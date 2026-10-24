"""The learned layer around the twin: causal features, the population LightGBM baseline (what a
standard pipeline would build), the capped residual corrector that turns twin rollouts into the
hybrid forecast, and conformal calibration. Everything here is fitted on training patients only."""
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression

from . import core

HORIZONS = (30, 60, 120)           # forecast horizons, minutes
EVENT_MIN, MEAL_MIN = 120, 180     # look-ahead of the rolling alert and of the meal-time forecast
CAP = {30: 20.0, 60: 30.0, 120: 40.0}  # largest correction (mg/dL) the residual model may apply to the physics
STATIC = ["hba1c", "fpg", "insulin", "bmi", "age"]
RAW = ["g0", "mean60", "sd120", "max180", "d15", "d30", "d60", "carbs30", "carbs60", "carbs120", "carbs240", "last_carbs",
       "last_min", "last_fat", "last_protein", "last_fiber", "mets30", "mets90", "hr30", "tod_sin", "tod_cos"]
TWIN = ["tw_d30", "tw_d60", "tw_d120", "tw_sd30", "tw_sd60", "tw_sd120", "tw_p2h", "tw_p3h", "tw_dpeak",
        "tw_X", "tw_D", "tw_innov", "tw_gb", "tw_phi", "tw_c"]
LGB = dict(n_estimators=300, learning_rate=0.03, num_leaves=15, min_child_samples=40, subsample=0.8,
           subsample_freq=1, colsample_bytree=0.8, verbose=-1, n_jobs=4, random_state=0)


def origins(p, stride_min=15, warm_min=60):
    """Rolling forecast origins: every 15 min after a 1-h warm-up, where a CGM reading exists."""
    dt = p["dt"]
    o = np.arange(warm_min // dt, len(p["g"]) - MEAL_MIN // dt - 1, max(stride_min // dt, 1))
    return o[np.isfinite(p["g"][o])]


def meal_origins(p, warm_min=60):
    g, H = p["g"], MEAL_MIN // p["dt"]
    return np.array([i for i in p["meals"]["idx"] if warm_min // p["dt"] <= i < len(g) - H - 1 and np.isfinite(g[i])
                     and np.isfinite(g[i + 1:i + 1 + H]).mean() >= 0.8], int)


def raw_features(p, o):
    """Features a standard pipeline would use. Every value is known at the origin (see tests)."""
    dt, g = p["dt"], p["g"]
    gs, ms, hs = pd.Series(g), pd.Series(p["mets"]), pd.Series(p["hr"])
    roll = lambda s, m, fn, mp=1: getattr(s.rolling(m // dt, min_periods=mp), fn)().to_numpy()[o]
    f = {"g0": g[o], "mean60": roll(gs, 60, "mean"), "sd120": roll(gs, 120, "std", 2), "max180": roll(gs, 180, "max") - g[o]}
    for m in (15, 30, 60):
        f[f"d{m}"] = g[o] - g[np.maximum(o - m // dt, 0)]
    carbs, mac, age = core.meal_ctx(p, o)  # most recent meal first
    for w in (30, 60, 120, 240):
        f[f"carbs{w}"] = (carbs * (age * dt < w)).sum(1)
    has = carbs[:, 0] > 0
    f["last_carbs"], f["last_min"] = carbs[:, 0], np.where(has, age[:, 0] * dt, core.MEAL_WINDOW)
    for j, n in enumerate(("fat", "protein", "fiber")):
        f[f"last_{n}"] = mac[:, 0, j] * has
    f["mets30"], f["mets90"] = roll(ms, 30, "mean"), roll(ms, 90, "mean")
    f["hr30"] = roll(hs, 30, "mean") - hs.expanding(min_periods=1).median().to_numpy()[o]  # vs own running baseline
    f["tod_sin"], f["tod_cos"] = np.sin(2 * np.pi * p["tod"][o] / 24), np.cos(2 * np.pi * p["tod"][o] / 24)
    for s in STATIC:
        f[s] = p["static"].get(s, np.nan)
    return pd.DataFrame(f)


def targets(p, o):
    dt, g = p["dt"], p["g"]
    y = {f"y{h}": g[o + h // dt] for h in HORIZONS}
    for name, mins in (("evt2h", EVENT_MIN), ("evt3h", MEAL_MIN)):
        w = np.stack([g[i + 1:i + 1 + mins // dt] for i in o]) if len(o) else np.empty((0, mins // dt))
        first = core.first_sustained(w, dt=dt)
        y[name] = np.where(np.isfinite(w).mean(1) >= 0.8, (first >= 0).astype(float), np.nan)
        if mins == EVENT_MIN:
            y["lead"] = np.where(first >= 0, (first + 1) * dt, np.nan)  # minutes from origin to event onset
    peak = np.where(np.isfinite(w), w, -np.inf).max(1) if len(o) else np.empty(0)  # over the 3-h window
    y["peak"] = np.where(np.isfinite(peak), peak, np.nan)
    return pd.DataFrame(y)


def twin_task(p, mu, sd, slow, learn=True, with_meals=False, seed=0):
    """Run one patient's twin end to end and summarise its forecasts at every origin.
    Returns {'roll': DataFrame, 'meal': DataFrame or None, 'par': daily parameter trajectory}."""
    S, L, innov = core.assimilate(p, mu, sd, slow, learn=learn, seed=seed)
    dt, g = p["dt"], p["g"]
    H = MEAL_MIN // dt
    noise = np.random.default_rng(seed + 1)

    def summarise(o, conditioned=False, active=None):
        R = core.rollout(p, o, S, L, H, slow, conditioned=conditioned, active=active, seed=seed)
        Rn = R + core.OBS_SD * noise.standard_normal(R.shape).astype(np.float32)
        f = {"tw_p2h": core.sustained(Rn[..., :EVENT_MIN // dt], dt=dt).mean(1), "tw_p3h": core.sustained(Rn, dt=dt).mean(1),
             "tw_dpeak": R.max(-1).mean(1) - g[o]}
        for h in HORIZONS:
            f[f"tw_d{h}"], f[f"tw_sd{h}"] = R[..., h // dt - 1].mean(1) - g[o], np.sqrt(R[..., h // dt - 1].var(1) + core.OBS_SD**2)
        return f

    def table(o):
        f = summarise(o)
        f.update({"tw_X": S[o, :, 1].mean(1), "tw_D": S[o, :, 3].mean(1), "tw_innov": np.nan_to_num(innov[o]),
                  "tw_gb": L[o, :, 0].mean(1), "tw_phi": L[o, :, 1].mean(1), "tw_c": L[o, :, 3].mean(1)})
        d = pd.concat([pd.DataFrame(f), raw_features(p, o), targets(p, o)], axis=1)
        d.insert(0, "id", p["id"]); d.insert(1, "i", o); d.insert(2, "day", o * dt // 1440); d.insert(3, "t", o * dt)
        return d

    out = {"roll": table(origins(p)), "meal": None}
    if with_meals:
        mo = meal_origins(p)
        m = table(mo)
        # what-if fidelity: the same meals replayed with the true future supplied, with and without the activity
        m["tw_cond_dpeak"] = summarise(mo, conditioned=True)["tw_dpeak"]
        m["tw_rest_dpeak"] = summarise(mo, conditioned=True, active=False)["tw_dpeak"]
        m["mets_post"] = [np.nanmean(p["mets"][i + 15 // dt:i + 75 // dt + 1]) if np.isfinite(p["mets"][i + 15 // dt:i + 75 // dt + 1]).any() else np.nan for i in mo]
        m["kind"] = p["meals"].set_index("idx").loc[mo, "kind"].to_numpy() if len(mo) else []
        out["meal"] = m
    day = np.arange(len(g)) * dt // 1440
    out["par"] = pd.DataFrame({"id": p["id"], "day": np.unique(day),
                               **{k: [L[day == d, :, j].mean() for d in np.unique(day)] for j, k in enumerate(core.PARAMS)},
                               "rise50": [core.standard_meal_rise(L[day == d].mean(0), p["static"]["weight_kg"], slow).mean() for d in np.unique(day)]})
    return out


def _cols(kind):
    return {"lgbm": RAW + STATIC, "hybrid": RAW + TWIN}[kind]  # labs never enter the hybrid as columns: they act through the prior


def fit_layer(fit, cal, meal_fit, meal_cal):
    """Fit the baseline and hybrid models on `fit` patients; calibrate on `cal` patients."""
    M = {}
    for kind in ("lgbm", "hybrid"):
        X = fit[_cols(kind)]
        for h in HORIZONS:
            base = fit["g0"] if kind == "lgbm" else fit["g0"] + fit[f"tw_d{h}"]  # hybrid learns what physics missed
            ok = fit[f"y{h}"].notna()
            M[kind, h] = lgb.LGBMRegressor(**LGB).fit(X[ok], (fit[f"y{h}"] - base)[ok])
            for q, a in (("lo", 0.05), ("hi", 0.95)):  # quantile models: interval width follows the situation
                M[kind, h, q] = lgb.LGBMRegressor(**LGB, objective="quantile", alpha=a).fit(X[ok], (fit[f"y{h}"] - base)[ok])
        for name, d, y in (("evt2h", fit, "evt2h"), ("meal", meal_fit, "evt3h")):
            ok = d[y].notna() & (d["g0"] <= 180)
            M[kind, name] = lgb.LGBMClassifier(**LGB).fit(d.loc[ok, _cols(kind)], d.loc[ok, y])
    ok = meal_fit["peak"].notna()
    M["lgbm", "rise"] = lgb.LGBMRegressor(**LGB).fit(meal_fit.loc[ok, _cols("lgbm") + ["mets_post"]], (meal_fit["peak"] - meal_fit["g0"])[ok])
    # calibration on patients none of the models above saw
    pc, mc = predict(M, cal), predict(M, meal_cal)
    for name, d, y, col in (("evt2h", pc, "evt2h", "tw_p2h"), ("meal", mc, "evt3h", "tw_p3h")):
        ok = d[y].notna() & (d["g0"] <= 180)
        M["iso", name] = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(d.loc[ok, col], d.loc[ok, y])
    for h in HORIZONS:
        for kind in ("lgbm", "hybrid"):  # conformalized quantile regression (Romano et al., 2019)
            M["score", kind, h] = np.sort(score(pc, kind, h).dropna().to_numpy())
    M["alert_thr"] = {m: alert_threshold(pc, f"p_{m}") for m in ("lgbm", "twin", "hybrid")}
    return M


def predict(M, d):
    """Add every model's forecasts to a table produced by twin_task."""
    d = d.copy()
    for h in HORIZONS:
        d[f"pers{h}"] = d["g0"]
        d[f"twin{h}"] = d["g0"] + d[f"tw_d{h}"]
        d[f"lgbm{h}"] = d["g0"] + M["lgbm", h].predict(d[_cols("lgbm")])
        d[f"res{h}"] = np.clip(M["hybrid", h].predict(d[_cols("hybrid")]), -CAP[h], CAP[h])
        d[f"hybrid{h}"] = d[f"twin{h}"] + d[f"res{h}"]
        for kind, base in (("lgbm", d["g0"]), ("hybrid", d[f"twin{h}"])):
            lo, hi = (base + M[kind, h, q].predict(d[_cols(kind)]) for q in ("lo", "hi"))
            d[f"lo_{kind}{h}"], d[f"hi_{kind}{h}"] = np.minimum(lo, hi), np.maximum(lo, hi)
    name = "meal" if "tw_cond_dpeak" in d else "evt2h"
    col = "tw_p3h" if name == "meal" else "tw_p2h"
    for kind in ("lgbm", "hybrid"):
        d[f"p_{kind}"] = M[kind, name].predict_proba(d[_cols(kind)])[:, 1]
    d["p_twin"] = M["iso", name].predict(d[col]) if ("iso", name) in M else d[col]
    if name == "meal":
        d["rise_lgbm"] = M["lgbm", "rise"].predict(d[_cols("lgbm") + ["mets_post"]])
    return d


def score(d, kind, h):
    """Conformal score: how far the outcome fell outside the raw quantile band (negative = inside)."""
    return np.maximum(d[f"lo_{kind}{h}"] - d[f"y{h}"], d[f"y{h}"] - d[f"hi_{kind}{h}"])


def quantile(sorted_scores, level):
    """Conformal quantile of calibration scores with the finite-sample correction."""
    n = len(sorted_scores)
    return sorted_scores[min(int(np.ceil(np.clip(level, 0, 1) * (n + 1))) - 1, n - 1)]


def aci(sorted_scores, r, alpha=0.1, gamma=0.01, delay=1):
    """Adaptive conformal inference (Gibbs & Candes, 2021) along one patient's timeline.
    r: that patient's scores in time order. Returns the margin used at each step; the interval
    covered when r[t] <= q[t]. Feedback only arrives `delay` steps later, as in live use."""
    a, q = alpha, np.empty(len(r))
    for t in range(len(r)):
        q[t] = quantile(sorted_scores, 1 - a)
        if t >= delay and np.isfinite(r[t - delay]):
            a += gamma * (alpha - (r[t - delay] > q[t - delay]))
    return q


def alerts(d, col, thr, snooze=60):
    """Replay an alert policy over rolling forecasts: alert when P(event within 2 h) >= thr while
    glucose is still <= 180, then stay quiet for `snooze` minutes. Returns sensitivity (events
    warned of before onset), median lead time (min) and false alerts per patient-day."""
    caught, events, false, leads, days = 0, 0, 0, [], 0.0
    for _, g in d[d["evt2h"].notna()].groupby("id"):
        t, p, ok, y, lead = (g[c].to_numpy() for c in ("t", col, "g0", "evt2h", "lead"))
        ok, last, hit = ok <= 180, -np.inf, {}
        onset = np.where(y == 1, t + np.nan_to_num(lead), np.nan)
        for j in range(len(t)):
            if ok[j] and p[j] >= thr and t[j] - last >= snooze:
                last = t[j]
                if y[j] == 1:
                    hit[onset[j]] = max(hit.get(onset[j], 0), lead[j])
                else:
                    false += 1
        ev = np.unique(onset[ok & (y == 1)])
        events += len(ev); caught += len(hit); leads += list(hit.values())
        days += (t[-1] - t[0]) / 1440 if len(t) > 1 else 0
    return {"sensitivity": caught / max(events, 1), "median_lead_min": float(np.median(leads)) if leads else float("nan"),
            "false_per_day": false / max(days, 1e-9), "events": events}


def alert_threshold(d, col, max_false_per_day=1.0):
    """Lowest threshold that keeps false alerts at or under the budget (chosen on calibration patients)."""
    for thr in np.arange(0.05, 1.0, 0.025):
        if alerts(d, col, thr)["false_per_day"] <= max_false_per_day:
            return float(thr)
    return 0.975
