"""Figures and results/RESULTS.md, generated from the evaluation outputs so every number is traceable.

Colour follows the model in every figure: hybrid twin blue, population LightGBM orange, physics
twin alone aqua, Chronos yellow, persistence grey. Palette checked for colour-vision deficiency.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import core, hybrid
from .data import ROOT
from .hybrid import HORIZONS

RES, FIG = ROOT / "results", ROOT / "results" / "figures"
INK, SECOND, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
C = {"hybrid": "#2a78d6", "lgbm": "#eb6834", "twin": "#1baf7a", "chronos": "#eda100", "pers": MUTED, "c2ft": "#8a5cd1", "ens": "#104281"}
NAME = {"hybrid": "Hybrid twin", "lgbm": "LightGBM (population)", "twin": "Physics twin alone", "chronos": "Chronos-Bolt (zero-shot)", "pers": "Persistence",
        "c2": "Chronos-2 (zero-shot, CGM only)", "c2cov": "Chronos-2 (zero-shot, with covariates)", "c2ft": "Chronos-2 (fine-tuned)",
        "gru": "GRU", "lstm": "LSTM", "transformer": "Patch transformer", "ens": "Hybrid twin + Chronos-2", "ens_lgbm": "LightGBM + Chronos-2 (control)",
        "c2tw": "Chronos-2 (fine-tuned, twin states as covariates)", "ens_tw": "Hybrid twin + twin-informed Chronos-2",
        "moirai": "Moirai 1.1 (zero-shot, with covariates)", "moment": "MOMENT (forecasting head trained, CGM only)", "ts2vec": "TS2Vec (encoder trained + ridge)"}
FIG_MODELS = ("pers", "chronos", "lgbm", "twin", "hybrid", "c2ft", "ens")
EXTRA_ORDER = ("gru", "lstm", "transformer", "ts2vec", "moment", "moirai", "chronos", "c2", "c2cov", "c2ft", "c2tw", "ens_lgbm", "ens", "ens_tw")
ORDINAL = {"healthy": "#86b6ef", "prediabetes": "#2a78d6", "T2D": "#104281"}  # one hue, light to dark: the groups are ordered
plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Segoe UI", "Arial", "DejaVu Sans"], "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": AXIS, "axes.labelcolor": SECOND, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE, "legend.frameon": False,
    "axes.titlesize": 10.5, "axes.titleweight": "bold", "axes.titlelocation": "left", "lines.linewidth": 2, "figure.dpi": 150,
})
DOT = dict(s=42, edgecolor=SURFACE, linewidth=1.2, zorder=3)


def _save(fig, name):
    FIG.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIG / name, dpi=150)
    plt.close(fig)


def _bars(ax, acc, models, title):
    w = 0.8 / len(models)
    for j, m in enumerate(models):
        v = np.array([acc[h][m] for h in acc])
        x = np.arange(len(acc)) + (j - (len(models) - 1) / 2) * w
        ax.bar(x, v[:, 0], w * 0.86, color=C[m], label=NAME[m])
        ax.vlines(x, v[:, 1], v[:, 2], color=INK, linewidth=0.9)
        if m == ("ens" if "ens" in models else "hybrid"):
            for xi, vi in zip(x, v):
                ax.text(xi, vi[2] + 0.8, f"{vi[0]:.1f}", ha="center", va="bottom", fontsize=8.5, color=INK)
    ax.set_xticks(range(len(acc)), [f"{h} min ahead" for h in acc])
    ax.set_ylabel("RMSE (mg/dL)")
    ax.set_title(title)
    ax.grid(axis="x", visible=False)


def fig_accuracy(m):
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.4), sharey=True)
    for a, acc, title in ((ax[0], m["accuracy"], "Same cohort, unseen patients (CGMacros, 5-fold)"),
                          (ax[1], m["external_all_models"], "Unseen country, device and population (ShanghaiT2DM)")):
        _bars(a, {h: acc[h] for h in HORIZONS}, [k for k in FIG_MODELS if k in acc[30]], title)
    ax[1].set_ylabel("")
    ax[0].legend(loc="upper left", ncol=2, fontsize=8.5)
    _save(fig, "accuracy.png")


def fig_tournament(m):
    """60-min RMSE of every model at home and abroad, one bar per model with its 95% interval; the reported forecast in navy."""
    order = ("pers", "lgbm", "gru", "lstm", "transformer", "chronos", "c2", "c2cov", "twin", "hybrid", "c2ft", "ens")
    col = lambda k: C.get(k, {"gru": "#b9b7af", "lstm": "#b9b7af", "transformer": "#9a988f", "c2": "#cdbbea", "c2cov": "#b49ae0"}.get(k, MUTED))
    fig, ax = plt.subplots(1, 2, figsize=(12, 5.2), sharex=True)
    for a, acc, title in ((ax[0], m["accuracy"][60], "Same cohort, unseen patients (CGMacros)"), (ax[1], m["external_all_models"][60], "Unseen cohort (ShanghaiT2DM)")):
        ks = [k for k in order if k in acc][::-1]
        v = np.array([acc[k] for k in ks])
        a.barh(range(len(ks)), v[:, 0], 0.62, color=[col(k) for k in ks])
        a.hlines(range(len(ks)), v[:, 1], v[:, 2], color=INK, linewidth=0.9)
        for j, (k, x) in enumerate(zip(ks, v)):
            a.text(x[2] + 0.5, j, f"{x[0]:.1f}", va="center", fontsize=8.5, color=INK, fontweight="bold" if k == "ens" else "normal")
        a.set_yticks(range(len(ks)), [NAME[k] for k in ks], fontsize=9)
        a.set_title(title)
        a.grid(axis="y", visible=False)
        a.set_xlabel("RMSE 60 minutes ahead (mg/dL)")
    ax[0].set_xlim(0, max(max(m["accuracy"][60][k][2] for k in order if k in m["accuracy"][60]), max(m["external_all_models"][60][k][2] for k in order if k in m["external_all_models"][60])) * 1.12)
    _save(fig, "tournament.png")


def fig_recommendations(R):
    pol = {"nothing": "Do nothing", "walk15": "Always walk 15 min", "rule": "Carbohydrate rule", "twin": "Twin plans", "oracle": "Oracle (knows the truth)"}
    fig, ax = plt.subplots(figsize=(9, 3.8))
    ks = list(pol)[::-1]
    v = np.array([R["policies"][k]["excursions"] for k in ks]) * 100
    ax.barh(range(len(ks)), v[:, 0], 0.6, color=[C["hybrid"] if k == "twin" else AXIS for k in ks])
    ax.hlines(range(len(ks)), v[:, 1], v[:, 2], color=INK, linewidth=0.9)
    for j, k in enumerate(ks):
        ax.text(v[j, 2] + 0.8, j, f"{v[j, 0]:.0f}%   (acts on {R['policies'][k]['acts']:.0%} of meals)", va="center", fontsize=9, color=INK)
    ax.set_yticks(range(len(ks)), [pol[k] for k in ks])
    ax.set_xlim(0, v[:, 2].max() * 1.6)
    ax.set_xlabel("Meals with a true spike above 180 mg/dL for 15+ min (%)")
    ax.set_title(f"Choosing the action with the twin, {R['meals']} meals of {R['patients']} synthetic patients (true outcomes)")
    ax.grid(axis="y", visible=False)
    _save(fig, "recommendations.png")


def fig_twin_value(m):
    L = m["learning"]
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    names = {"generic": "Generic physiology\n(no labs, no learning)", "nolabs": "Learning twin,\npopulation prior", "full": "Learning twin,\nlab-informed prior"}
    for j, (k, lab) in enumerate(names.items()):
        v = L["day0_twin60"][k]
        ax[0].bar(j, v[0], 0.42, color=C["hybrid"] if k == "full" else AXIS)
        ax[0].vlines(j, v[1], v[2], color=INK, linewidth=0.9)
        ax[0].text(j, v[2] + 0.5, f"{v[0]:.1f}", ha="center", va="bottom", fontsize=9)
    ax[0].set_xticks(range(3), names.values())
    ax[0].set_ylabel("60-min RMSE in the first 24 h (mg/dL)")
    ax[0].set_title("First 24 h of a new patient, by how the twin starts")
    ax[0].grid(axis="x", visible=False)
    gain = np.array(L["by_day"]["frozen"]["twin"]) - np.array(L["by_day"]["full"]["twin"])
    ax[1].axhline(0, color=AXIS, linewidth=1)
    ax[1].plot(range(1, 11), gain, color=C["hybrid"])
    ax[1].scatter(range(1, 11), gain, color=C["hybrid"], **DOT)
    ax[1].text(10.15, gain[-1], f"{gain[-1]:+.1f}", va="center", fontsize=9)
    ax[1].set_xticks(range(1, 11))
    ax[1].set_xlabel("Day of twin life")
    ax[1].set_ylabel("60-min RMSE saved by updating (mg/dL)")
    ax[1].set_title("Updating twin vs. one frozen at its prior, by day")
    _save(fig, "twin_value.png")


def fig_calibration(roll):
    r = roll[(roll["variant"] == "full") & roll["evt2h"].notna() & (roll["g0"] <= 180)]
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    ax[0].plot([0, 1], [0, 1], color=AXIS, linewidth=1)
    for k in ("lgbm", "hybrid"):
        b = pd.qcut(r[f"p_{k}"], 10, duplicates="drop")
        g = r.groupby(b, observed=True).agg(p=(f"p_{k}", "mean"), y=("evt2h", "mean"))
        ax[0].plot(g["p"], g["y"], color=C[k], label=NAME[k])
        ax[0].scatter(g["p"], g["y"], color=C[k], **DOT)
    ax[0].set_xlabel("Predicted probability of an event within 2 h")
    ax[0].set_ylabel("Observed frequency")
    ax[0].set_title("Alert probabilities mean what they say (deciles)")
    ax[0].legend(loc="upper left")
    d = roll[(roll["variant"] == "full") & roll["y60"].notna()]
    rng = np.random.default_rng(0)
    cats = (("lgbm", "LightGBM,\ncalibrated once", "lgbm"), ("hybrid", "Hybrid twin,\ncalibrated once", "hybrid"), ("aci", "Hybrid twin,\nadapting per patient", "hybrid"))
    ax[1].axhspan(0.85, 0.95, color=GRID, alpha=0.6, linewidth=0)
    ax[1].axhline(0.9, color=MUTED, linewidth=1)
    for j, (k, lab, col) in enumerate(cats):
        pp = d["y60"].between(d[f"lo90_{k}60"], d[f"hi90_{k}60"]).groupby(d["id"]).mean()
        ax[1].scatter(j + rng.uniform(-0.16, 0.16, len(pp)), pp, color=C[col], **DOT)
    ax[1].text(2.45, 0.9, "target 90%", va="center", fontsize=8.5, color=SECOND)
    ax[1].set_xticks(range(3), [c[1] for c in cats])
    ax[1].set_xlim(-0.5, 2.9)
    ax[1].set_ylabel("Share of this patient's outcomes inside the 90% band")
    ax[1].set_title("Coverage per patient, 60 min ahead (one dot = one patient)")
    ax[1].grid(axis="x", visible=False)
    _save(fig, "calibration.png")


def fig_whatif(pairs):
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    titles = {"carbs": "More carbohydrate at the same kind of meal", "activity": "Active vs. sedentary hour after similar meals"}
    for a, (name, pr) in zip(ax, pairs.items()):
        lim = np.nanpercentile(np.abs(pr[["twin", "lgbm"]].to_numpy()), 98)
        a.plot([-lim, lim], [-lim, lim], color=AXIS, linewidth=1)
        a.axhline(0, color=AXIS, linewidth=1)
        for k in ("lgbm", "twin"):
            b = pd.qcut(pr[k], 6, duplicates="drop")
            g = pr.groupby(b, observed=True).agg(x=(k, "mean"), y=("obs", "mean"), se=("obs", "sem"))
            a.plot(g["x"], g["y"], color=C["hybrid" if k == "twin" else k], label="Twin what-if" if k == "twin" else NAME[k])
            a.vlines(g["x"], g["y"] - 1.96 * g["se"], g["y"] + 1.96 * g["se"], color=C["hybrid" if k == "twin" else k], linewidth=1)
            a.scatter(g["x"], g["y"], color=C["hybrid" if k == "twin" else k], **DOT)
        a.set_xlabel("Predicted difference in peak rise between the two meals (mg/dL)")
        a.set_ylabel("Observed difference (mg/dL)")
        a.set_title(f"{titles[name]} ({len(pr)} matched pairs)")
    ax[0].legend(loc="upper left")
    _save(fig, "whatif_validation.png")


def fig_construct(t):
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    for a, (x, y, xl, yl, title) in zip(ax, (("fpg", "gb", "Fasting plasma glucose from the lab (mg/dL)", "Basal glucose the twin learned (mg/dL)", "Basal glucose"),  # titles get the suffix below
                                            ("hba1c", "peak50", "HbA1c from the lab (%)", "Twin's peak glucose after a standard 50 g meal (mg/dL)", "Carbohydrate tolerance"))):
        for g, col in ORDINAL.items():
            d = t[t["group"] == g]
            a.scatter(d[x], np.exp(d[y]) if y == "gb" else d[y], color=col, label=g, **DOT)
        a.set_xlabel(xl)
        a.set_ylabel(yl)
        a.set_title(f"{title} (labs withheld from the twin)")
    ax[0].legend(loc="upper left", title="Lab-defined group")
    _save(fig, "construct_validity.png")


def fig_verification(ver):
    _, r, cf = ver
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    lim = [0, max(r["true_rise50"].max(), r["rise50"].max()) * 1.05]
    ax[0].plot(lim, lim, color=AXIS, linewidth=1)
    ax[0].scatter(r["true_rise50"], r["rise50"], color=C["hybrid"], **DOT)
    ax[0].set_xlabel("True peak rise after 50 g carbohydrate, reference simulator (mg/dL)")
    ax[0].set_ylabel("Twin's estimate (mg/dL)")
    ax[0].set_title("Synthetic patients: the twin recovers hidden physiology")
    lim = [min(cf["true"].min(), cf["twin"].min()) * 1.05, 2]
    ax[1].plot(lim, lim, color=AXIS, linewidth=1)
    for (name, d), col, lab in zip(cf.groupby("what"), (C["hybrid"], C["lgbm"]), ("40% less carbohydrate", "30-minute walk after the meal")):
        ax[1].scatter(d["true"], d["twin"], color=col, label=lab, **DOT)
    ax[1].set_xlabel("True change in 3-h peak when the day is re-simulated (mg/dL)")
    ax[1].set_ylabel("Twin's what-if answer (mg/dL)")
    ax[1].set_title("What-ifs against true counterfactuals")
    ax[1].legend(loc="upper left")
    _save(fig, "verification.png")


def fan(p, i, S, L, pop, M, H=36, record=None):
    """Everything needed to draw one forecast: twin trajectories (5/25/50/75/95th percentiles) plus the
    hybrid's corrected checkpoints with conformal 90% bands and the calibrated event probability.
    Pass record=core.scenario(...) to ask a what-if from the same twin state."""
    R = core.rollout(record if record is not None else p, [i], S, L, H, pop["slow"], conditioned=record is not None)[0]
    t = np.arange(1, H + 1) * p["dt"]
    out = {"t": t, "pct": np.percentile(R, [5, 25, 50, 75, 95], axis=0), "p_twin_raw": float(core.sustained(R, dt=p["dt"]).mean()),
           "peak": float(R.max(-1).mean())}
    if record is None:
        f = pd.DataFrame({"tw_p2h": [core.sustained(R[:, :hybrid.EVENT_MIN // p["dt"]], dt=p["dt"]).mean()], "tw_p3h": [out["p_twin_raw"]],
                          "tw_dpeak": [out["peak"] - p["g"][i]], "tw_X": [S[i, :, 1].mean()], "tw_D": [S[i, :, 3].mean()], "tw_innov": [0.0],
                          "tw_gb": [L[i, :, 0].mean()], "tw_phi": [L[i, :, 1].mean()], "tw_c": [L[i, :, 3].mean()]})
        for h in HORIZONS:
            f[f"tw_d{h}"], f[f"tw_sd{h}"] = R[:, h // p["dt"] - 1].mean() - p["g"][i], np.sqrt(R[:, h // p["dt"] - 1].var() + core.OBS_SD**2)
        d = hybrid.predict(M, pd.concat([f, hybrid.raw_features(p, np.array([i]))], axis=1).assign(**{f"y{h}": np.nan for h in HORIZONS}))
        out["hybrid"] = {h: (float(d[f"hybrid{h}"][0]), float(d[f"lo_hybrid{h}"][0] - hybrid.quantile(M["score", "hybrid", h], 0.9)),
                             float(d[f"hi_hybrid{h}"][0] + hybrid.quantile(M["score", "hybrid", h], 0.9))) for h in HORIZONS}
        out["p_alert"] = float(d["p_hybrid"][0])
    return out


def fig_example(P, models, roll):
    """One held-out meal, chosen by rule (not by eye): the T2D/prediabetes test patient with the median
    60-min hybrid error; their first lunch from day 4 on that starts at or below 180 mg/dL."""
    full = roll[(roll["variant"] == "full")]
    by = {p["id"]: p for p in P}
    e = full[full["id"].map(lambda i: by[i]["group"] != "healthy")].groupby("id").apply(lambda d: np.sqrt(((d["hybrid60"] - d["y60"]) ** 2).mean()), include_groups=False)
    pid = e.sort_values().index[len(e) // 2]
    p = by[pid]
    mod = next(m for m in models.values() if pid in m["test"])
    meals = p["meals"][(p["meals"]["kind"] == "lunch") & (p["meals"]["idx"] >= 3 * 288) & (p["meals"]["idx"] < len(p["g"]) - 40)]
    i = int(next(k for k in meals["idx"] if np.isfinite(p["g"][k]) and p["g"][k] <= 180))
    S, L, _ = core.assimilate(p, *core.prior(mod["pop"], p["static"]), mod["pop"]["slow"])
    f = fan(p, i, S, L, mod["pop"], mod["M"])
    w = fan(p, i, S, L, mod["pop"], mod["M"], record=core.scenario(p, i, carb_scale=0.7, walk_min=20))
    fig, ax = plt.subplots(figsize=(9.5, 4.4))
    past = np.arange(-36, 1) * 5
    ax.plot(past, p["g"][i - 36:i + 1], color=INK, linewidth=1.6, label="CGM so far")
    ax.fill_between(f["t"], f["pct"][0], f["pct"][4], color=C["hybrid"], alpha=0.10, linewidth=0)
    ax.fill_between(f["t"], f["pct"][1], f["pct"][3], color=C["hybrid"], alpha=0.16, linewidth=0)
    ax.plot(f["t"], f["pct"][2], color=C["hybrid"], label="Twin forecast (median, 50% and 90% of trajectories)")
    ax.plot(w["t"], w["pct"][2], color=C["twin"], label="What-if: 30% smaller portion and a 20-min walk")
    ax.scatter(f["t"], p["g"][i + 1:i + 37], s=12, color=MUTED, zorder=3, label="What happened next (hidden from the twin)")
    for h, (mid, lo, hi) in f["hybrid"].items():
        ax.vlines(h, lo, hi, color=INK, linewidth=1.1, zorder=4)
        ax.scatter([h], [mid], color=INK, **{**DOT, "s": 46, "zorder": 5})
    ax.scatter([], [], color=INK, **{**DOT, "s": 46}, label="Hybrid forecast with 90% conformal band")
    ax.axhline(180, color=MUTED, linewidth=1)
    ax.text(178, 183, "180 mg/dL", fontsize=8.5, color=SECOND, ha="right")
    ax.axvline(0, color=AXIS, linewidth=1)
    m = p["meals"].set_index("idx").loc[i]
    ax.set_title(f"{pid} ({p['group']}), day {i // 288 + 1} lunch, {m['carbs']:.0f} g carbohydrate: P(sustained >180 within 2 h) = {f['p_alert']:.0%}")
    ax.set_xlabel("Minutes from the meal")
    ax.set_ylabel("Glucose (mg/dL)")
    ax.legend(loc="upper left", fontsize=8.5)
    _save(fig, "example_forecast.png")
    return pid


# ---------------------------------------------------------------- RESULTS.md
def _ci(v, d=1):
    return f"{v[0]:.{d}f} ({v[1]:.{d}f} to {v[2]:.{d}f})"


def _table(head, rows):
    return "\n".join(["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]) + "\n"


def report(m, T):
    figs = [(fig_accuracy, (m,)), (fig_twin_value, (m,)), (fig_calibration, (T["roll"],)), (fig_whatif, (T["pairs"],)),
            (fig_construct, (T["cons"],)), (fig_verification, (T["ver"],))]
    if any(k in m["accuracy"][60] for k in ("gru", "c2ft")):
        figs.append((fig_tournament, (m,)))
    if m.get("recommendations"):
        figs.append((fig_recommendations, (m["recommendations"],)))
    for fn, args in figs:
        fn(*args)
    demo = fig_example(T["P"], T["models"], T["roll"])
    A, E, U, L, W, X, V, K = m["accuracy"], m["external"], m["uncertainty"], m["learning"], m["whatif"], m["construct_validity"], m["verification"], m["cohort"]
    models = [k for k in FIG_MODELS if k in A[30]]
    ens = [["Hybrid twin + Chronos-2 minus LightGBM"] + [_ci(A[h]["ens_minus_lgbm"], 2) for h in HORIZONS],
           ["Hybrid twin + Chronos-2 minus hybrid twin"] + [_ci(A[h]["ens_minus_hybrid"], 2) for h in HORIZONS]] if "ens" in A[30] else []
    ev = lambda e: [[NAME[k], f"{e[k]['auroc'][0]:.3f}", _ci(e[k]["auprc"], 3), e[k]["brier"], e[k]["ece"]] for k in ("lgbm", "twin", "hybrid")]
    s = [f"""# Results

Generated by `python -m twin.evaluate`. Numbers in brackets are 95% intervals from resampling patients.
All CGMacros results are for patients the models never trained on (5-fold, patient-level, stratified
by glycaemic group); a test patient is only ever seen online, one reading at a time.

Cohort: {K['patients']} people ({', '.join(f'{v} {k}' for k, v in K['groups'].items())}), {K['rolling_forecasts']:,} rolling forecasts, {K['meals']:,} logged meals.

## 1. Forecast accuracy (RMSE, mg/dL)

![accuracy](figures/accuracy.png)

**CGMacros, unseen patients**

""" + _table(["Model"] + [f"{h} min" for h in HORIZONS], [[NAME[k]] + [_ci(A[h][k]) for h in HORIZONS] for k in models])
         + "\n" + _table(["Paired difference"] + [f"{h} min" for h in HORIZONS],
                         [["Hybrid minus LightGBM"] + [_ci(A[h]["hybrid_minus_lgbm"], 2) for h in HORIZONS],
                          ["Physics twin minus persistence"] + [_ci(A[h]["twin_minus_pers"], 2) for h in HORIZONS], *ens,
                          ["Share of the hybrid's predicted change supplied by physics"] + [A[h]["physics_share"] for h in HORIZONS]])
         + "\nWithout the nine patients used to set the filter's noise levels: hybrid "
         + ", ".join(f"{m['accuracy_excluding_dev'][h]['hybrid'][0]:.1f}" for h in HORIZONS) + " vs LightGBM "
         + ", ".join(f"{m['accuracy_excluding_dev'][h]['lgbm'][0]:.1f}" for h in HORIZONS) + " mg/dL.\n\n"
         + "**By glycaemic group (60 min)**\n\n" + _table(["Group"] + [NAME[k] for k in ("pers", "lgbm", "twin", "hybrid")],
                                                         [[g] + [v[60][k] for k in ("pers", "lgbm", "twin", "hybrid")] for g, v in m["accuracy_by_group"].items()])]
    for key, title in (("modality_matched_full", "trained on CGMacros degraded to the target modality (15-min CGM, no wearable)"), ("as_recorded_full", "trained on CGMacros as recorded")):
        e = E[key]
        s.append(f"\n**ShanghaiT2DM, external ({E['n_patients']} recordings, {E['share_on_insulin']:.0%} on insulin), {title}**\n\n"
                 + _table(["Model"] + [f"{h} min" for h in HORIZONS], [[NAME[k]] + [_ci(e[h][k]) for h in HORIZONS] for k in ("pers", "lgbm", "twin", "hybrid")]
                          + [["Hybrid minus LightGBM"] + [_ci(e[h]["hybrid_minus_lgbm"], 2) for h in HORIZONS],
                             ["Physics twin minus LightGBM"] + [_ci(e[h]["twin_minus_lgbm"], 2) for h in HORIZONS]]))
    s.append("\n## 2. The adverse event: glucose above 180 mg/dL for at least 15 minutes\n\nOnly forecasts made while glucose is still at or below 180 mg/dL count.\n\n"
             + f"**Rolling alert, event within 2 h** (CGMacros: n = {m['alert_event']['n']:,}, prevalence {m['alert_event']['prevalence']:.1%})\n\n"
             + _table(["Model", "AUROC", "AUPRC", "Brier", "ECE"], ev(m["alert_event"]))
             + f"\nAUPRC, hybrid minus LightGBM: {_ci(m['alert_event']['auprc_hybrid_minus_lgbm'], 3)}.\n\n"
             + f"**At meal time, event within 3 h** (n = {m['meal_event']['n']:,}, prevalence {m['meal_event']['prevalence']:.1%})\n\n"
             + _table(["Model", "AUROC", "AUPRC", "Brier", "ECE"], ev(m["meal_event"]))
             + f"\nAUPRC, hybrid minus LightGBM: {_ci(m['meal_event']['auprc_hybrid_minus_lgbm'], 3)}.\n\n"
             + "**Alert policy replayed on test patients** (threshold fixed on each fold's calibration patients for at most 1 false alert per patient-day; 60-min snooze)\n\n"
             + _table(["Model", "Events warned of before onset", "Median lead (min)", "False alerts per patient-day"],
                      [[NAME[k], f"{v['sensitivity']:.0%} of {v['events']}", v["median_lead_min"], v["false_per_day"]] for k, v in m["alerts"].items()])
             + "\n**ShanghaiT2DM, external** (modality-matched training)\n\n"
             + _table(["Task", "Model", "AUROC", "AUPRC", "Brier", "ECE"],
                      [[t] + r for t, e in (("2-h alert", E["modality_matched_full"]["alert_event"]), ("Meal, 3 h", E["modality_matched_full"]["meal_event"])) for r in ev(e)])
             + f"\nAUPRC, hybrid minus LightGBM: alert {_ci(E['modality_matched_full']['alert_event']['auprc_hybrid_minus_lgbm'], 3)}; meal {_ci(E['modality_matched_full']['meal_event']['auprc_hybrid_minus_lgbm'], 3)}.\n")
    un = lambda u: [[f"{h} min", n.replace("_", ", "), v["coverage"], v["width"], v["patient_median"], v["patient_min"], f"{v['patients_within_5pts']:.0%}"]
                    for h in HORIZONS for n, v in u[h].items() if isinstance(v, dict)]
    head = ["Horizon", "Band", "Coverage", "Mean width (mg/dL)", "Median patient", "Worst patient", "Patients within 5 points of 90%"]
    s.append("\n## 3. Uncertainty: 90% bands\n\n![calibration](figures/calibration.png)\n\n**CGMacros**\n\n" + _table(head, un(U))
             + "\nSpearman correlation between the hybrid band's width and its absolute error: " + ", ".join(f"{U[h]['spearman_width_vs_error']} ({h} min)" for h in HORIZONS) + ".\n\n"
             + "**ShanghaiT2DM, external** (calibrated on CGMacros only)\n\n" + _table(head, un(E["modality_matched_full"]["uncertainty"])))
    v4 = ("generic", "nolabs", "frozen", "full")
    lab = {"generic": "Generic physiology (no labs, no learning)", "nolabs": "Learning twin, population prior", "frozen": "Lab prior, never updated", "full": "Learning twin, lab prior"}
    s.append("\n## 4. What makes it a twin: labs as priors, and learning\n\n![twin value](figures/twin_value.png)\n\nPhysics twin alone, 60-min RMSE (mg/dL).\n\n"
             + _table(["Variant", "First 24 h", "Day 4 onward"], [[lab[k], _ci(L["day0_twin60"][k]), _ci(L["day3plus_twin60"][k])] for k in v4])
             + f"\n- Lab prior minus population prior, first 24 h: {_ci(L['day0_twin60_labs_minus_nolabs'], 2)} at 60 min; {_ci(L['day0_twin120_labs_minus_nolabs'], 2)} at 120 min.\n"
             + f"- Learning minus frozen, day 4 onward: {_ci(L['day3plus_learning_minus_frozen'], 2)}.\n"
             + f"- Personalised minus generic, day 4 onward: {_ci(L['day3plus_personalised_minus_generic'], 2)}.\n\n"
             + f"- The lab-to-prior map did not transfer: on ShanghaiT2DM the physics twin's 60-min RMSE was {E['modality_matched_full'][60]['twin'][0]:.1f} "
             + f"with the lab prior and {E['modality_matched_nolabs'][60]['twin'][0]:.1f} with the population prior.\n\n"
             + "By day of twin life (60-min RMSE): \n\n" + _table(["Variant"] + [f"d{k}" for k in range(1, 11)], [[lab[k]] + L["by_day"][k]["twin"] for k in v4]
                                                                   + [["LightGBM (population)"] + L["by_day"]["full"]["lgbm"]]))
    s.append("""
## 5. Does the learned physiology mean anything?

![construct validity](figures/construct_validity.png)

Twin run with labs withheld (population prior), parameters averaged from day 3; Spearman rho (p):

""" + _table(["Twin quantity", "Lab value", "rho (p)"], [
        ["Basal glucose", "Fasting plasma glucose", f"{X['gb_vs_fpg'][0]:.2f} ({X['gb_vs_fpg'][1]:.3g})"],
        ["Basal glucose", "HbA1c", f"{X['gb_vs_hba1c'][0]:.2f} ({X['gb_vs_hba1c'][1]:.3g})"],
        ["Peak after a standard 50 g meal", "HbA1c", f"{X['peak50_vs_hba1c'][0]:.2f} ({X['peak50_vs_hba1c'][1]:.3g})"],
        ["Peak after a standard 50 g meal", "HOMA-IR", f"{X['peak50_vs_homa_ir'][0]:.2f} ({X['peak50_vs_homa_ir'][1]:.3g})"],
        ["Rise above basal after a standard 50 g meal", "HbA1c", f"{X['rise50_vs_hba1c'][0]:.2f} ({X['rise50_vs_hba1c'][1]:.3g})"],
        ["Insulin-mediated disposal gain", "HbA1c", f"{X['phi_vs_hba1c'][0]:.2f} ({X['phi_vs_hba1c'][1]:.3g})"],
        ["Insulin-mediated disposal gain", "HOMA-IR", f"{X['phi_vs_homa_ir'][0]:.2f} ({X['phi_vs_homa_ir'][1]:.3g})"]])
             + f"\nGroup medians of the standard-meal peak: {X['peak50_group_median']}. Days 3-5 vs days 7+ of the standard-meal rise: rho = {X['rise50_test_retest'][0]:.2f}.\n"
             + "\nLeave-one-out R2 of the lab-to-prior map, per fold: " + "; ".join(f"fold {f}: " + ", ".join(f"{k} {v}" for k, v in p["lab_r2_loo"].items()) for f, p in m["population"].items()) + ".\n")
    wr = lambda o: [[n, f"{o[k]['sign_agreement'][0]:.1%} ({o[k]['sign_agreement'][1]:.1%} to {o[k]['sign_agreement'][2]:.1%})", _ci(o[k]["r"], 2), o[k]["predicted_mean_diff"]]
                    for k, n in (("twin", "Twin what-if"), ("lgbm", "LightGBM"))]
    s.append(f"""
## 6. Are the what-ifs right? Natural experiments in real data

![what-if validation](figures/whatif_validation.png)

Within one person, pairs of meals of the same kind that start from similar glucose and differ in
one input. The twin replays each meal from its own state at meal time with the real inputs.
These pairs are not randomised, so this is a consistency check, not causal proof; the same test
is applied to the LightGBM baseline.

**More carbohydrate** ({W['carbs']['pairs']} pairs, {W['carbs']['patients']} people, at least 25 g apart; observed mean difference in peak rise {_ci(W['carbs']['observed_mean_diff'])} mg/dL)

""" + _table(["Model", "Direction correct", "Correlation with observed", "Mean predicted difference"], wr(W["carbs"]))
             + f"\n**Active vs. sedentary after the meal** ({W['activity']['pairs']} pairs, {W['activity']['patients']} people; mean METs 15-75 min after: at least 2.2 vs at most 1.5; observed {_ci(W['activity']['observed_mean_diff'])} mg/dL)\n\n"
             + _table(["Model", "Direction correct", "Correlation with observed", "Mean predicted difference"], wr(W["activity"]))
             + f"\nEffect the twin attributes to the activity itself (same meals replayed at rest): {_ci(W['activity']['twin_attributed_effect'])} mg/dL.\n\n"
             + "Meal-level correlation of predicted and observed peak rise: "
             + "; ".join(f"{n} {_ci(W['meal_level_r'][k], 2)}" for k, n in (("twin", "twin (true inputs)"), ("twin_std", "twin (forecast)"), ("lgbm", "LightGBM"), ("carbs_only", "carbohydrate grams alone"))) + ".\n")
    s.append("\n## 7. Robustness on test patients\n\n" + _table(
        ["Input", "Hybrid RMSE 60", "Hybrid RMSE 120", "LightGBM RMSE 60", "Alert AUPRC (hybrid)", "90% band coverage / width, 60 min"],
        [[k.replace("_", " "), v["rmse60"]["hybrid"], v["rmse120"]["hybrid"], v["rmse60"]["lgbm"], v["alert_auprc"]["hybrid"], f"{v['coverage60']} / {v['width60']}"] for k, v in m["robustness"].items()]))
    s.append(f"""
## 8. Verification on synthetic patients with known physiology

![verification](figures/verification.png)

{V['n_train']} synthetic patients set the population components, {V['n_test']} others are twinned. The simulator is
structurally richer than the twin, so recovery is not guaranteed by construction.

- Standard-meal rise, twin vs truth: Spearman {V['rise50_spearman']}. Basal glucose: Spearman {V['gb_spearman']}, mean absolute error {V['gb_mae_mgdl']} mg/dL.
""" + "".join(f"- What-if '{k.replace('_', ' ')}' ({V[k]['n']} meals): true mean change {V[k]['true_mean']} mg/dL, twin {V[k]['twin_mean']} mg/dL; correlation {V[k]['r']}; direction correct {V[k]['sign_agreement']:.0%}; mean absolute error {V[k]['mae']} mg/dL.\n"
              for k in ("carbs_minus_40pct", "walk_30min")))
    s.append(f"\n## 9. Example forecast\n\n![example](figures/example_forecast.png)\n\nPatient and meal picked by a fixed rule (median-error non-healthy test patient, {demo}; first eligible lunch from day 4), not by appearance.\n")
    XA = m["external_all_models"]
    tour = lambda acc: [[NAME[k]] + [f"{acc[h][k][0]:.2f}" for h in HORIZONS]
                        + [_ci(acc[60][f"{k}_minus_{r}"], 2) if f"{k}_minus_{r}" in acc[60] else "–" for r in ("lgbm", "hybrid")] + [acc[60]["bias"][k]]
                        for k in ("pers", "lgbm", "twin", "hybrid") + EXTRA_ORDER if k in acc[30]]
    head = ["Model", "30 min", "60 min", "120 min", "60 min: minus LightGBM", "60 min: minus hybrid", "Mean error at 60 min"]
    if any(k in A[30] for k in ("gru", "c2", "c2ft")):  # optional baselines present
        s.append("""
## 10. Model tournament: neural networks and foundation models

Same patient-level folds and the same rolling forecasts as above (RMSE, mg/dL; mean error: + = forecasts too high).
GRU, LSTM and patch transformer: 4 h of history plus the static record, 5 seeds averaged, settings fixed once before
any test result (`twin/neural_baselines.py`). Chronos: one day of history; Chronos-2 fine-tuned inside each fold
(`twin/chronos_baseline.py`). Hybrid twin + Chronos-2 = the two forecasts averaged with equal weight, fixed in advance;
LightGBM + Chronos-2 is the same blend without the twin, as a control.
""" + ("""Moirai, MOMENT and TS2Vec: same folds, origins and one-day context, run on Kaggle (`kaggle/tsfm_run.py`); settings fixed
in advance. Moirai is zero-shot and picks its own patch size per window; MOMENT's epoch and TS2Vec's ridge penalty are chosen on
each fold's calibration patients.
""" if any(k in A[30] for k in ("moirai", "moment", "ts2vec")) else "") + """
**CGMacros, unseen patients**

""" + _table(head, tour(A)) + f"""
![tournament](figures/tournament.png)

**ShanghaiT2DM, external** (everything trained on CGMacros degraded to 15-min CGM, no wearable; Chronos-2's only covariate there is carbohydrate)

""" + _table(head, tour(XA)))
    R = m.get("recommendations")
    if R:
        pct = lambda v: f"{v[0]:.1%} ({v[1]:.1%} to {v[2]:.1%})"
        pol = {"nothing": "Do nothing", "walk15": "Always walk 15 min", "rule": "Rule: 60 g carbohydrate or more → 3/4 portion and a 15-min walk",
               "twin": f"Twin plans: least effort that brings its P(event) under {R['risk']:.0%}", "oracle": "Oracle: knows the true outcome"}
        s.append(f"""
## 11. Recommendations: twin-planned actions against true counterfactuals

At every eligible meal of {R['patients']} synthetic patients ({R['meals']} meals, day 4 on), each of {len(R['actions'])} actions (portion 100/75/50%,
walk 0/15/30 min) is replayed in the reference simulator, so the true outcome of every choice is known. The twin
picks by trying every action on its own state (`core.recommend`): one choice per meal with its outcome within 3 h is a
contextual bandit, which this solves exactly. Event = above 180 mg/dL for 15+ minutes within 3 h.

![recommendations](figures/recommendations.png)

""" + _table(["Policy", "Meals with a true event", "Mean true peak (mg/dL)", "Acts on", "Mean effort"],
             [[pol[k], pct(v["excursions"]), v["mean_peak"], f"{v['acts']:.0%}", v["effort"]] for k, v in R["policies"].items()])
                 + f"""
- Twin minus doing nothing: {pct(R['twin_minus_nothing'])} of meals; twin minus the rule: {pct(R['twin_minus_rule'])}.
- The twin acts on {R['twin_acts_when_spike']:.0%} of meals that would truly spike and {R['twin_acts_when_no_spike']:.0%} of those that would not.
- Synthetic patients from our own simulator (richer than the twin, same family of model): an upper bound on real-world benefit, not a trial.
""")
    (RES / "RESULTS.md").write_text("".join(s), encoding="utf-8")
