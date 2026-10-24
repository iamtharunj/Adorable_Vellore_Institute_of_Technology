"""Experiments. `python -m twin.evaluate` writes results/: metrics.json, RESULTS.md, figures, and the
fitted models the dashboard replays. Every learned component is refit inside each patient-level
fold; a test patient is only ever seen online, one reading at a time."""
import gzip
import json
import pickle
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from . import core, hybrid, synth
from .data import PROC, ROOT, folds, load
from .hybrid import HORIZONS

RES = ROOT / "results"
# Filter noise settings were chosen on these nine patients; results are also reported without them.
DEV_IDS = ["CGM-002", "CGM-007", "CGM-012", "CGM-017", "CGM-022", "CGM-029", "CGM-034", "CGM-041", "CGM-046"]
VARIANTS = (("full", True, True), ("nolabs", False, True), ("frozen", True, False), ("generic", False, False))
# Optional baselines (twin.chronos_baseline, twin.neural_baselines) and blends, scored when their predictions exist.
# ens = the forecast we report: hybrid twin and fine-tuned Chronos-2 averaged; ens_lgbm = the same blend with LightGBM, a control;
# c2tw, ens_tw = twin-informed Chronos-2 (the twin's states as covariates) and its average with the hybrid.
EXTRA = ("chronos", "c2", "c2cov", "c2ft", "c2tw", "gru", "lstm", "transformer", "moirai", "moment", "ts2vec", "ens", "ens_lgbm", "ens_tw")


# ---------------------------------------------------------------- running twins
def _task(a):
    return hybrid.twin_task(*a)


def twins(pool, patients, pop, labs=True, learn=True):
    return list(pool.map(_task, [(p, *core.prior(pop, p["static"], labs), pop["slow"], learn, True) for p in patients]))


def cat(outs, key):
    return pd.concat([o[key] for o in outs], ignore_index=True)


def _states(a):
    """The twin's filtered states and parameters after every step (ensemble means), exactly as twin_task runs it.
    Causal: the filter at step t has seen readings up to t only."""
    p, pop = a
    S, L, _ = core.assimilate(p, *core.prior(pop, p["static"]), pop["slow"])
    return {"tw_X": S[:, :, 1].mean(1), "tw_Z": S[:, :, 2].mean(1), "tw_D": S[:, :, 3].mean(1),
            **{f"tw_{k}": L[:, :, core.PARAMS.index(k)].mean(1) for k in ("gb", "phi", "c")}}


def twin_covariates(pool):
    """data/processed/twin_cov.pkl, {(fold, id): states} for twin.chronos_baseline's twin-informed Chronos-2: every
    CGMacros patient under each fold's population (the twin the hybrid uses there), and degraded CGMacros plus
    ShanghaiT2DM under the modality-matched one (fold "ext")."""
    with gzip.open(PROC / "fold_models.pkl.gz") as f:
        fm = pickle.load(f)
    with gzip.open(RES / "models.pkl.gz") as f:
        ext = pickle.load(f)["matched"]["pop"]
    P = load("cgmacros")
    assert all(fm[k]["test"] == [P[i]["id"] for i in ti] for k, ti in enumerate(folds(P, 5)))
    jobs = [(k, p, fm[k]["pop"]) for k in range(5) for p in P] + [("ext", p, ext) for p in [degrade_to(p) for p in P] + load("shanghai")]
    out = dict(zip([(k, p["id"]) for k, p, _ in jobs], pool.map(_states, [(p, pop) for _, p, pop in jobs], chunksize=4)))
    pd.to_pickle(out, PROC / "twin_cov.pkl")


def add_intervals(M, r, alpha=0.1):
    """90% intervals: conformalized quantile bands calibrated once on held-out patients (split), and
    the hybrid's band re-calibrated online for each patient as their outcomes arrive (ACI)."""
    for h in HORIZONS:
        for kind in ("hybrid", "lgbm"):
            q = hybrid.quantile(M["score", kind, h], 1 - alpha)
            r[f"lo90_{kind}{h}"], r[f"hi90_{kind}{h}"] = r[f"lo_{kind}{h}"] - q, r[f"hi_{kind}{h}"] + q
        s = hybrid.score(r, "hybrid", h)
        q = np.concatenate([hybrid.aci(M["score", "hybrid", h], x.to_numpy(), alpha, delay=h // 15) for _, x in s.groupby(r["id"], sort=False)])
        r[f"lo90_aci{h}"], r[f"hi90_aci{h}"] = r[f"lo_hybrid{h}"] - q, r[f"hi_hybrid{h}"] + q
    return r


def fit_all(pool, train):
    """Population components + learned layer from a set of training patients."""
    pop = core.fit_population(train)
    tr = twins(pool, train, pop)
    is_cal = np.arange(len(train)) % 4 == 3  # every fourth training patient calibrates, never fits
    fit, cal = [o for o, c in zip(tr, is_cal) if not c], [o for o, c in zip(tr, is_cal) if c]
    return pop, hybrid.fit_layer(cat(fit, "roll"), cat(cal, "roll"), cat(fit, "meal"), cat(cal, "meal"))


def cross_validate(P, pool, k=5):
    roll, meal, par, models = [], [], [], {}
    for f, ti in enumerate(folds(P, k)):
        t0 = time.time()
        test, train = [P[i] for i in ti], [p for i, p in enumerate(P) if i not in set(ti)]
        pop, M = fit_all(pool, train)
        for variant, labs, learn in VARIANTS:
            te = twins(pool, test, pop, labs, learn)
            r, m, pr = hybrid.predict(M, cat(te, "roll")), hybrid.predict(M, cat(te, "meal")), cat(te, "par")
            if variant == "full":
                r = add_intervals(M, r)
            for d, acc in ((r, roll), (m, meal), (pr, par)):
                d["variant"], d["fold"] = variant, f
                acc.append(d)
        models[f] = {"pop": pop, "M": M, "test": [p["id"] for p in test]}
        print(f"fold {f}: {len(train)} train / {len(test)} test, {time.time() - t0:.0f} s", flush=True)
    return pd.concat(roll, ignore_index=True), pd.concat(meal, ignore_index=True), pd.concat(par, ignore_index=True), models


# ---------------------------------------------------------------- metrics
def rmse(d, col, h):
    return float(np.sqrt(np.nanmean((d[f"{col}{h}"] - d[f"y{h}"]) ** 2)))


def boot(d, fn, n=300, seed=0):
    """95% CI of fn(table) by resampling patients (not rows): readings within a patient are not independent."""
    rng, groups = np.random.default_rng(seed), [g for _, g in d.groupby("id").indices.items()]
    vals = []
    for _ in range(n):
        idx = np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))])
        vals.append(fn(d.iloc[idx]))
    lo, hi = np.nanpercentile(np.array(vals, float), [2.5, 97.5], axis=0)
    return [round(float(fn(d)), 4), round(float(lo), 4), round(float(hi), 4)]


def ece(y, p, bins=10):
    b = np.minimum((p * bins).astype(int), bins - 1)
    return float(sum(abs(y[b == k].mean() - p[b == k].mean()) * (b == k).mean() for k in range(bins) if (b == k).any()))


def accuracy(r):
    out, models = {}, ["pers", "lgbm", "twin", "hybrid"] + [m for m in EXTRA if f"{m}60" in r]
    for h in HORIZONS:
        d = r[["id", f"y{h}"] + [f"{m}{h}" for m in models]].dropna()
        out[h] = {m: boot(d, lambda x, m=m: rmse(x, m, h)) for m in models}
        out[h]["mae"] = {m: round(float((d[f"{m}{h}"] - d[f"y{h}"]).abs().mean()), 2) for m in models}
        out[h]["bias"] = {m: round(float((d[f"{m}{h}"] - d[f"y{h}"]).mean()), 2) for m in models}  # mean error: + = forecasts too high
        out[h]["hybrid_minus_lgbm"] = boot(d, lambda x: rmse(x, "hybrid", h) - rmse(x, "lgbm", h))
        out[h]["twin_minus_pers"] = boot(d, lambda x: rmse(x, "twin", h) - rmse(x, "pers", h))
        for m in models[4:]:
            out[h][f"{m}_minus_lgbm"] = boot(d, lambda x, m=m: rmse(x, m, h) - rmse(x, "lgbm", h))
            out[h][f"{m}_minus_hybrid"] = boot(d, lambda x, m=m: rmse(x, m, h) - rmse(x, "hybrid", h))
        # how much of the hybrid's predicted change the physics supplies before the residual model corrects it
        out[h]["physics_share"] = round(float(1 - ((r[f"hybrid{h}"] - r[f"twin{h}"]) ** 2).mean() / ((r[f"hybrid{h}"] - r["g0"]) ** 2).mean()), 3)
    return out


def events(d, y):
    d = d[d[y].notna() & (d["g0"] <= 180)][["id", y, "p_lgbm", "p_twin", "p_hybrid"]]
    safe = lambda fn: (lambda x, c: fn(x[y], x[c]) if 0 < x[y].sum() < len(x) else np.nan)
    out = {"n": len(d), "patients": int(d["id"].nunique()), "prevalence": round(float(d[y].mean()), 4)}
    for m in ("lgbm", "twin", "hybrid"):
        c = f"p_{m}"
        out[m] = {"auprc": boot(d, lambda x: safe(average_precision_score)(x, c)), "auroc": boot(d, lambda x: safe(roc_auc_score)(x, c)),
                  "brier": round(float(brier_score_loss(d[y], d[c])), 4), "ece": round(ece(d[y].to_numpy(), d[c].to_numpy()), 4)}
    for a, b in (("hybrid", "lgbm"), ("twin", "lgbm")):
        out[f"auprc_{a}_minus_{b}"] = boot(d, lambda x: safe(average_precision_score)(x, f"p_{a}") - safe(average_precision_score)(x, f"p_{b}"))
    return out


def alert_metrics(r, models):
    """Alert thresholds come from each fold's calibration patients, then run unchanged on its test patients."""
    out = {}
    for m in ("lgbm", "twin", "hybrid"):
        parts = [hybrid.alerts(r[r["fold"] == f], f"p_{m}", mod["M"]["alert_thr"][m]) for f, mod in models.items()]
        ev = sum(p["events"] for p in parts)
        out[m] = {"events": ev, "sensitivity": round(sum(p["sensitivity"] * p["events"] for p in parts) / max(ev, 1), 3),
                  "median_lead_min": round(float(np.nanmedian([p["median_lead_min"] for p in parts])), 1),
                  "false_per_day": round(float(np.mean([p["false_per_day"] for p in parts])), 2)}
    return out


def uncertainty(r):
    out = {}
    for h in HORIZONS:
        d = r[r[f"y{h}"].notna()]
        o = {}
        for name, k in (("hybrid_split", "hybrid"), ("hybrid_aci", "aci"), ("lgbm_split", "lgbm")):
            cov = d[f"y{h}"].between(d[f"lo90_{k}{h}"], d[f"hi90_{k}{h}"])
            pp = cov.groupby(d["id"]).mean()
            o[name] = {"coverage": round(float(cov.mean()), 3), "width": round(float((d[f"hi90_{k}{h}"] - d[f"lo90_{k}{h}"]).mean()), 1),
                       "patient_median": round(float(pp.median()), 3), "patient_min": round(float(pp.min()), 3),
                       "patients_within_5pts": round(float(((pp - 0.9).abs() <= 0.05).mean()), 3)}
        o["spearman_width_vs_error"] = round(float(spearmanr(d[f"hi90_hybrid{h}"] - d[f"lo90_hybrid{h}"], (d[f"y{h}"] - d[f"hybrid{h}"]).abs())[0]), 3)
        out[h] = o
    return out


def learning(roll):
    """Forecast error by day of twin life, per variant: cold start and learning curve."""
    out = {"by_day": {}}
    for v in [v[0] for v in VARIANTS]:
        d = roll[(roll["variant"] == v) & (roll["day"] < 10)]
        out["by_day"][v] = {m: [round(rmse(d[d["day"] == k], m, 60), 2) for k in range(10)] for m in ("twin", "hybrid", "lgbm", "pers")}
    w = roll[roll["day"] == 0].pivot_table(index=["id", "i"], columns="variant", values=["twin60", "twin120", "y60", "y120"]).dropna()
    w.columns = [f"{a}_{b}" for a, b in w.columns]
    w = w.reset_index()
    for h in (60, 120):
        e = lambda x, v: float(np.sqrt(((x[f"twin{h}_{v}"] - x[f"y{h}_full"]) ** 2).mean()))
        out[f"day0_twin{h}"] = {v: boot(w, lambda x, v=v: e(x, v)) for v in ("full", "nolabs", "frozen", "generic")}
        out[f"day0_twin{h}_labs_minus_nolabs"] = boot(w, lambda x: e(x, "full") - e(x, "nolabs"))
    late = roll[roll["day"] >= 3].pivot_table(index=["id", "i"], columns="variant", values=["twin60", "y60"]).dropna()
    late.columns = [f"{a}_{b}" for a, b in late.columns]
    late = late.reset_index()
    e = lambda x, v: float(np.sqrt(((x[f"twin60_{v}"] - x["y60_full"]) ** 2).mean()))
    out["day3plus_twin60"] = {v: boot(late, lambda x, v=v: e(x, v)) for v in ("full", "nolabs", "frozen", "generic")}
    out["day3plus_learning_minus_frozen"] = boot(late, lambda x: e(x, "full") - e(x, "frozen"))
    out["day3plus_personalised_minus_generic"] = boot(late, lambda x: e(x, "full") - e(x, "generic"))
    return out


def construct(par, P):
    """Does physiology the twin learned WITHOUT labs agree with the labs it never saw?"""
    s = pd.DataFrame([{"id": p["id"], "group": p["group"], **{k: p["static"][k] for k in ("hba1c", "fpg", "insulin")}} for p in P])
    s["homa_ir"] = s["fpg"] * s["insulin"] / 405
    t = par[(par["variant"] == "nolabs") & (par["day"] >= 2)].groupby("id")[["gb", "phi", "c", "rise50"]].mean().reset_index().merge(s, on="id")
    t["peak50"] = np.exp(t["gb"]) + t["rise50"]  # glucose the twin expects at the peak of a standard 50 g meal
    sp = lambda a, b: [round(float(v), 4) for v in spearmanr(t[a], t[b])]
    out = {"n": len(t), "peak50_vs_hba1c": sp("peak50", "hba1c"), "peak50_vs_homa_ir": sp("peak50", "homa_ir"),
           "rise50_vs_hba1c": sp("rise50", "hba1c"), "gb_vs_fpg": sp("gb", "fpg"), "gb_vs_hba1c": sp("gb", "hba1c"),
           "phi_vs_homa_ir": sp("phi", "homa_ir"), "phi_vs_hba1c": sp("phi", "hba1c"),
           "peak50_group_median": t.groupby("group")["peak50"].median().round(0).to_dict(),
           "gb_group_median": np.exp(t.groupby("group")["gb"].median()).round(0).to_dict()}
    a = par[par["variant"] == "nolabs"]
    early, late = a[a["day"].between(2, 4)].groupby("id")["rise50"].mean(), a[a["day"] >= 6].groupby("id")["rise50"].mean()
    j = pd.concat([early, late], axis=1).dropna()
    out["rise50_test_retest"] = [round(float(v), 4) for v in spearmanr(j.iloc[:, 0], j.iloc[:, 1])]
    return out, t


def pairs(m, pred, by, lo, hi, tol):
    """Within-person matched meal pairs that differ in `by` (>= hi vs <= lo) but agree on `tol` columns."""
    rows = []
    for pid, d in m.groupby("id"):
        a, b = d[d[by] >= hi], d[d[by] <= lo]
        for _, x in a.iterrows():
            c = b[(b["kind"] == x["kind"]) & np.all([(b[k] - x[k]).abs() <= v for k, v in tol.items()], axis=0)]
            if by == "last_carbs":
                c = c[x[by] - c[by] >= 25]
            for _, z in c.iterrows():
                rows.append({"id": pid, "obs": x["rise"] - z["rise"], **{p: x[p] - z[p] for p in pred}})
    return pd.DataFrame(rows)


def whatif(meal):
    """Check what-if answers against what really happened when the same person did the other thing."""
    m = meal[(meal["variant"] == "full") & meal["peak"].notna()].copy()
    m["rise"], m["twin"], m["twin_std"], m["lgbm"] = m["peak"] - m["g0"], m["tw_cond_dpeak"], m["tw_dpeak"], m["rise_lgbm"]
    m["carbs_only"] = m["last_carbs"]
    out = {"n_meals": len(m), "meal_level_r": {}, "meal_level_r_within_person": {}}
    dm = m[["rise", "twin", "twin_std", "lgbm", "carbs_only"]] - m.groupby("id")[["rise", "twin", "twin_std", "lgbm", "carbs_only"]].transform("mean")
    for c in ("twin", "twin_std", "lgbm", "carbs_only"):
        out["meal_level_r"][c] = boot(m[["id", "rise", c]], lambda x: np.corrcoef(x["rise"], x[c])[0, 1])
        out["meal_level_r_within_person"][c] = round(float(np.corrcoef(dm["rise"], dm[c])[0, 1]), 3)
    tabs = {}
    for name, by, lo, hi, tol in (("carbs", "last_carbs", 1e9, 0, {"g0": 15}), ("activity", "mets_post", 1.5, 2.2, {"g0": 20, "last_carbs": 15})):
        pr = pairs(m.dropna(subset=[by]), ["twin", "lgbm"], by, lo, hi, tol)
        tabs[name] = pr
        o = {"pairs": len(pr), "patients": int(pr["id"].nunique()), "observed_mean_diff": boot(pr, lambda x: x["obs"].mean())}
        for c in ("twin", "lgbm"):
            o[c] = {"sign_agreement": boot(pr, lambda x: (np.sign(x["obs"]) == np.sign(x[c])).mean()),
                    "r": boot(pr, lambda x: np.corrcoef(x["obs"], x[c])[0, 1]), "predicted_mean_diff": round(float(pr[c].mean()), 1)}
        o["sign_twin_minus_lgbm"] = boot(pr, lambda x: (np.sign(x["obs"]) == np.sign(x["twin"])).mean() - (np.sign(x["obs"]) == np.sign(x["lgbm"])).mean())
        out[name] = o
    act = m[m["mets_post"] >= 2.2]
    out["activity"]["twin_attributed_effect"] = boot(act[["id", "tw_cond_dpeak", "tw_rest_dpeak"]], lambda x: (x["tw_cond_dpeak"] - x["tw_rest_dpeak"]).mean())
    return out, tabs, m


# ---------------------------------------------------------------- further experiments
def robustness(P, models, pool):
    """Degrade the inputs of test patients and see whether the twin fails gracefully."""
    rng = np.random.default_rng(0)

    def degrade(p, kind):
        q = dict(p)
        if kind == "no_wearable":
            q["mets"], q["hr"] = np.full(len(p["g"]), np.nan), np.full(len(p["g"]), np.nan)
        elif kind == "no_meal_log":
            q["meals"] = p["meals"].iloc[:0]
        elif kind == "carb_error_30pct":
            q["meals"] = p["meals"].assign(carbs=p["meals"]["carbs"] * np.exp(rng.normal(0, 0.3, len(p["meals"]))))
        return q

    out, by_id = {}, {p["id"]: p for p in P}
    for kind in ("intact", "no_wearable", "carb_error_30pct", "no_meal_log"):
        rs, ms = [], []
        for f, mod in models.items():
            te = twins(pool, [degrade(by_id[i], kind) for i in mod["test"]], mod["pop"])
            rs.append(add_intervals(mod["M"], hybrid.predict(mod["M"], cat(te, "roll"))))
            if kind != "no_meal_log":
                ms.append(hybrid.predict(mod["M"], cat(te, "meal")))
        r = pd.concat(rs, ignore_index=True)
        o = {f"rmse{h}": {m: round(rmse(r, m, h), 2) for m in ("lgbm", "twin", "hybrid")} for h in (60, 120)}
        d = r[r["y60"].notna()]
        o["coverage60"] = round(float(d["y60"].between(d["lo90_hybrid60"], d["hi90_hybrid60"]).mean()), 3)
        o["width60"] = round(float((d["hi90_hybrid60"] - d["lo90_hybrid60"]).mean()), 1)
        e = r[r["evt2h"].notna() & (r["g0"] <= 180)]
        o["alert_auprc"] = {m: round(float(average_precision_score(e["evt2h"], e[f"p_{m}"])), 3) for m in ("lgbm", "twin", "hybrid")}
        if ms:
            e = pd.concat(ms, ignore_index=True)
            e = e[e["evt3h"].notna() & (e["g0"] <= 180)]
            o["meal_auprc"] = {m: round(float(average_precision_score(e["evt3h"], e[f"p_{m}"])), 3) for m in ("lgbm", "twin", "hybrid")}
        out[kind] = o
        print("robustness", kind, o["rmse60"], flush=True)
    return out


def degrade_to(p, dt=15):
    """The record as a site with 15-minute CGM and no wearable would have stored it."""
    k = dt // p["dt"]
    T = len(p["g"]) // k
    m = p["meals"].assign(idx=p["meals"]["idx"] // k)
    m = m[m["idx"] < T].groupby("idx", as_index=False).agg({"kind": "first", **{n: "sum" for n in ("carbs", "protein", "fat", "fiber")}})
    return dict(p, dt=dt, g=pd.DataFrame(p["g"][:T * k].reshape(T, k)).ffill(axis=1).iloc[:, -1].to_numpy(), tod=p["tod"][:T * k].reshape(T, k)[:, -1],
                mets=np.full(T, np.nan), hr=np.full(T, np.nan), meals=m)


def external(P, pool):
    """Fit everything on CGMacros, then run ShanghaiT2DM untouched: other country, device (15-min
    Libre), treated T2D inpatients, no wearable, meals as free text. Nothing is refitted there.
    Two training set-ups, so the baseline gets its fairest shot: CGMacros as recorded, and CGMacros
    degraded to the target site's modality (15-minute CGM, no wearable)."""
    sh = load("shanghai")
    words = "insulin|novolin|humulin|gansulin|glargine|aspart|lispro|detemir|degludec|novorapid|lantus|humalog|scilin"
    insulin = {p["id"]: bool(pd.Series([p["static"]["agents"]]).str.contains(words, case=False)[0]) for p in sh}
    out, keep, rows = {"n_patients": len(sh), "share_on_insulin": round(float(np.mean(list(insulin.values()))), 3)}, {}, None
    for name, train in (("as_recorded", P), ("modality_matched", [degrade_to(p) for p in P])):
        pop, M = fit_all(pool, train)
        keep["all" if name == "as_recorded" else "matched"] = {"pop": pop, "M": M}
        for variant, labs in (("full", True), ("nolabs", False)):
            te = twins(pool, sh, pop, labs)
            r = add_intervals(M, hybrid.predict(M, cat(te, "roll")))
            o = {h: {m: boot(r[["id", f"y{h}", f"{m}{h}"]].dropna(), lambda x, m=m, h=h: rmse(x, m, h), n=200) for m in ("pers", "lgbm", "twin", "hybrid")} for h in HORIZONS}
            for h in HORIZONS:
                d = r[["id", f"y{h}", f"lgbm{h}", f"twin{h}", f"hybrid{h}"]].dropna()
                o[h]["hybrid_minus_lgbm"] = boot(d, lambda x, h=h: rmse(x, "hybrid", h) - rmse(x, "lgbm", h), n=200)
                o[h]["twin_minus_lgbm"] = boot(d, lambda x, h=h: rmse(x, "twin", h) - rmse(x, "lgbm", h), n=200)
            o["alert_event"], o["meal_event"] = events(r, "evt2h"), events(hybrid.predict(M, cat(te, "meal")), "evt3h")
            o["uncertainty"] = uncertainty(r)
            o["rmse60_by_insulin"] = {str(k): {m: round(rmse(g, m, 60), 2) for m in ("pers", "lgbm", "twin", "hybrid")} for k, g in r.groupby(r["id"].map(insulin))}
            out[f"{name}_{variant}"] = o
            if (name, variant) == ("modality_matched", "full"):  # kept per forecast, to score other models on the same rows
                rows = r[["id", "i", "g0"] + [f"{m}{h}" for m in ("y", "pers", "lgbm", "twin", "hybrid") for h in HORIZONS]]
            print("external", name, variant, {h: (o[h]["lgbm"][0], o[h]["twin"][0], o[h]["hybrid"][0]) for h in HORIZONS}, flush=True)
    return out, keep, rows


def verification(pool, cohort="synthetic"):
    """Synthetic patients with known physiology: does the twin recover it, and do its what-ifs match
    TRUE counterfactuals from a simulator that is structurally richer than the twin?"""
    S = load(cohort)
    train, test = S[::2], S[1::2]
    pop = core.fit_population(train)
    out = {"n_train": len(train), "n_test": len(test)}
    rows, cf = [], []
    for p in test:
        mu, sd = core.prior(pop, p["static"])
        St, L, _ = core.assimilate(p, mu, sd, pop["slow"])
        last = L[-2 * 288:].mean(0)
        rows.append({"rise50": core.standard_meal_rise(last, p["static"]["weight_kg"], pop["slow"]).mean(), "true_rise50": synth.true_standard_rise(p["truth"]),
                     "gb": float(np.exp(last[:, 0].mean())), "true_gb": p["truth"]["gb"]})
        H, plan = 36, p["plan"]
        cand = [m for m in plan["meals"] if m["logged"] and not m["walk"] and m["kind"] in ("lunch", "dinner") and 3 * 1440 < m["t"] < plan["T"] - 400][:4]
        base = synth.simulate(p["truth"], plan)[0]
        for m in cand:
            i = m["t"] // 5
            if i not in set(p["meals"]["idx"]):
                continue
            sl = slice(m["t"], m["t"] + 180)
            tw0 = core.rollout(core.scenario(p, i), [i], St, L, H, pop["slow"], conditioned=True).max(-1).mean()
            for name, kw, edit in (("carbs_minus_40pct", {"carb_scale": 0.6}, lambda x: {**x, **{k: x[k] * 0.6 for k in ("carbs", "protein", "fat", "fiber")}}),
                                   ("walk_30min", {"walk_min": 30}, None)):
                plan2 = dict(plan)
                if edit:
                    plan2["meals"] = [edit(x) if x is m else x for x in plan["meals"]]
                else:
                    plan2["mets"] = plan["mets"].copy()
                    plan2["mets"][m["t"] + 20:m["t"] + 50] = 3.5
                # truth: same day replayed with one input changed. twin: same filtered state, same edit.
                true = synth.simulate(p["truth"], plan2)[0][sl].max() - base[sl].max()
                tw = core.rollout(core.scenario(p, i, **kw), [i], St, L, H, pop["slow"], conditioned=True).max(-1).mean() - tw0
                cf.append({"what": name, "true": true, "twin": float(tw)})
    r, cf = pd.DataFrame(rows), pd.DataFrame(cf)
    out["rise50_spearman"] = round(float(spearmanr(r["rise50"], r["true_rise50"])[0]), 3)
    out["gb_spearman"] = round(float(spearmanr(r["gb"], r["true_gb"])[0]), 3)
    out["gb_mae_mgdl"] = round(float((r["gb"] - r["true_gb"]).abs().mean()), 1)
    for name, d in cf.groupby("what"):
        out[name] = {"n": len(d), "true_mean": round(float(d["true"].mean()), 1), "twin_mean": round(float(d["twin"].mean()), 1),
                     "r": round(float(np.corrcoef(d["true"], d["twin"])[0, 1]), 3), "sign_agreement": round(float((np.sign(d["true"]) == np.sign(d["twin"])).mean()), 3),
                     "mae": round(float((d["true"] - d["twin"]).abs().mean()), 1)}
    return out, r, cf


def _policy_task(a):
    """One synthetic patient: the twin's choice at every eligible meal, and the TRUE outcome of every action."""
    p, pop = a
    S, L, _ = core.assimilate(p, *core.prior(pop, p["static"]), pop["slow"])
    plan, idx, rows = p["plan"], set(p["meals"]["idx"]), []
    for m in [m for m in plan["meals"] if m["logged"] and not m["walk"] and 3 * 1440 < m["t"] < plan["T"] - 400 and m["t"] // 5 in idx]:
        k, pr = core.recommend(p, m["t"] // 5, S, L, pop["slow"])
        for a_, (portion, walk) in enumerate(core.ACTIONS):
            plan2 = dict(plan, meals=[{**x, **{n: x[n] * portion for n in ("carbs", "protein", "fat", "fiber")}} if x is m else x for x in plan["meals"]])
            if walk:  # the walk scenario() gives the twin: 3.5 METs from 20 min after the meal (minute resolution here)
                plan2["mets"] = plan["mets"].copy()
                plan2["mets"][m["t"] + 20:m["t"] + 20 + walk] = 3.5
            true = synth.simulate(p["truth"], plan2)[0][m["t"]:m["t"] + 180]
            rows.append({"id": p["id"], "t": m["t"], "carbs": m["carbs"], "a": a_, "chosen": k, "tw_p": pr[a_],
                         "true_peak": float(true.max()), "true_evt": float(core.sustained(true, dt=1))})
    return pd.DataFrame(rows)


def recommendations(pool):
    """Is there a decision worth learning, and does the twin make it well? On synthetic patients every action's TRUE
    outcome is known. Policies: do nothing; always walk 15 min; a carbohydrate rule; the twin choosing by exhaustive
    search over its own what-ifs (core.recommend); an oracle that knows the truth."""
    S = load("synthetic")
    pop = core.fit_population(S[::2])
    d = pd.concat(pool.map(_policy_task, [(p, pop) for p in S[1::2]]), ignore_index=True)
    rows = []
    for (pid, t), g in d.groupby(["id", "t"]):
        g = g.set_index("a")
        safe = [k for k in g.index if not g.loc[k, "true_evt"]]
        pick = {"nothing": 0, "walk15": 1, "rule": 4 if g["carbs"].iloc[0] >= 60 else 0, "twin": int(g["chosen"].iloc[0]),
                "oracle": min(safe, key=lambda k: core.EFFORT[k]) if safe else int(g["true_peak"].idxmin())}
        rows.append({"id": pid, **{f"{n}_{c}": v for n, k in pick.items()
                                   for c, v in (("evt", g.loc[k, "true_evt"]), ("peak", g.loc[k, "true_peak"]), ("acts", float(k > 0)), ("effort", core.EFFORT[k]))}})
    r = pd.DataFrame(rows)
    out = {"meals": len(r), "patients": int(r["id"].nunique()), "risk": 0.3, "actions": [list(a) for a in core.ACTIONS],
           "policies": {n: {"excursions": boot(r, lambda x, n=n: x[f"{n}_evt"].mean()), "mean_peak": round(float(r[f"{n}_peak"].mean()), 1),
                            "acts": round(float(r[f"{n}_acts"].mean()), 3), "effort": round(float(r[f"{n}_effort"].mean()), 2)}
                        for n in ("nothing", "walk15", "rule", "twin", "oracle")},
           "twin_minus_nothing": boot(r, lambda x: x["twin_evt"].mean() - x["nothing_evt"].mean()),
           "twin_minus_rule": boot(r, lambda x: x["twin_evt"].mean() - x["rule_evt"].mean()),
           "twin_acts_when_spike": round(float(r.loc[r["nothing_evt"] == 1, "twin_acts"].mean()), 3),
           "twin_acts_when_no_spike": round(float(r.loc[r["nothing_evt"] == 0, "twin_acts"].mean()), 3)}
    print("recommendations", {n: v["excursions"][0] for n, v in out["policies"].items()}, flush=True)
    return out, d


def with_baselines(d, files):
    """Merge optional baseline forecasts, and form the reported forecast: hybrid twin and fine-tuned Chronos-2 averaged."""
    for f in files:
        if (PROC / f).exists():
            d = d.merge(pd.read_pickle(PROC / f), on=["id", "i"], how="left")
    if "c2ft60" in d:
        for h in HORIZONS:
            d[f"ens{h}"], d[f"ens_lgbm{h}"] = (d[f"hybrid{h}"] + d[f"c2ft{h}"]) / 2, (d[f"lgbm{h}"] + d[f"c2ft{h}"]) / 2
            if f"c2tw{h}" in d:
                d[f"ens_tw{h}"] = (d[f"hybrid{h}"] + d[f"c2tw{h}"]) / 2
    return d


def save_models(folds_, final):
    """What the dashboard replays with. The final models (fitted on all of CGMacros) ship with the
    repository; the per-fold ones, which let real patients be replayed held-out, stay local."""
    for path, obj in ((RES / "models.pkl.gz", final), (PROC / "fold_models.pkl.gz", folds_)):
        with gzip.open(path, "wb") as f:
            pickle.dump(obj, f)


def main(reuse=False):
    RES.mkdir(exist_ok=True)
    P = load("cgmacros")
    cache = PROC / "cv.pkl"
    with ProcessPoolExecutor(8) as pool:
        if reuse and cache.exists():
            roll, meal, par, models, rob, ext, ext_model, ext_rows, ver, rec = pickle.loads(cache.read_bytes())
        else:
            roll, meal, par, models = cross_validate(P, pool)
            rob = robustness(P, models, pool)
            ext, ext_model, ext_rows = external(P, pool)
            ver = verification(pool)
            rec = recommendations(pool)
            cache.write_bytes(pickle.dumps((roll, meal, par, models, rob, ext, ext_model, ext_rows, ver, rec)))
        save_models(models, ext_model)
    roll = with_baselines(roll, ("chronos.pkl", "neural.pkl", "tsfm.pkl"))
    ext_rows = with_baselines(ext_rows, ("chronos_ext.pkl", "neural_ext.pkl", "tsfm_ext.pkl"))
    full = roll[roll["variant"] == "full"]
    mfull = meal[meal["variant"] == "full"]
    grp = full["id"].map({p["id"]: p["group"] for p in P})
    cons, cons_tab = construct(par, P)
    wi, wi_tabs, wi_meals = whatif(meal)
    metrics = {
        "cohort": {"patients": len(P), "groups": pd.Series([p["group"] for p in P]).value_counts().to_dict(),
                   "rolling_forecasts": len(full), "meals": len(mfull), "dev_ids": DEV_IDS},
        "accuracy": accuracy(full),
        "accuracy_excluding_dev": accuracy(full[~full["id"].isin(DEV_IDS)]),
        "accuracy_by_group": {g: {h: {m: round(rmse(d, m, h), 2) for m in ("pers", "lgbm", "twin", "hybrid")} for h in HORIZONS} for g, d in full.groupby(grp)},
        "alert_event": events(full, "evt2h"), "meal_event": events(mfull, "evt3h"),
        "meal_event_by_group": {g: events(d, "evt3h") for g, d in mfull.groupby(mfull["id"].map({p["id"]: p["group"] for p in P}))},
        "alerts": alert_metrics(full, models), "uncertainty": uncertainty(full), "learning": learning(roll),
        "construct_validity": cons, "whatif": wi, "robustness": rob, "external": ext, "external_all_models": accuracy(ext_rows),
        "verification": ver[0], "recommendations": rec[0],
        "population": {f: {"slow": mod["pop"]["slow"].round(3).tolist(), "lab_r2_loo": dict(zip(core.PARAMS, mod["pop"]["r2_loo"].round(2).tolist())),
                           "alert_thr": mod["M"]["alert_thr"]} for f, mod in models.items()},
    }
    (RES / "metrics.json").write_text(json.dumps(metrics, indent=1, default=float))
    from .report import report
    report(metrics, {"roll": roll, "meal": meal, "par": par, "cons": cons_tab, "pairs": wi_tabs, "meals": wi_meals, "ver": ver, "P": P, "models": models})


if __name__ == "__main__":
    if "--twin-cov" in sys.argv:
        with ProcessPoolExecutor(4) as pool:
            twin_covariates(pool)
    else:
        main(reuse="--reuse" in sys.argv)
