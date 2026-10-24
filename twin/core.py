"""The twin: a compact glucose physiology model, an ensemble Kalman filter that keeps it
synchronised with one patient, forecast / what-if rollouts, and the population components
(lab-to-physiology prior map, meal-composition effects) learned across training patients.

Units: glucose mg/dL, time minutes, carbohydrate grams, activity METs.
"""
import numpy as np
from scipy.optimize import least_squares
from scipy.signal import lfilter
from scipy.sparse import lil_matrix

# Per-patient parameters, all estimated in log space.
#   gb   basal glucose (mg/dL)
#   phi  insulin-mediated disposal gain (1/min per mg/dL above basal). CGM cannot separate beta-cell
#        response from insulin sensitivity, only their product -- the disposition index -- so that
#        product is the parameter.
#   k    gut absorption rate (1/min)
#   c    carbohydrate sensitivity: acute glucose appearance per g available carbohydrate per kg body
#        weight (mg/dL kg/g). Below the textbook f/V_G because fast hepatic and first-phase insulin
#        effects, which this model does not resolve, are folded into it.
#   bex  activity-driven glucose uptake (1/min per MET above light activity)
PARAMS = ["gb", "phi", "k", "c", "bex"]
PRIOR_MU = np.log([110.0, 1e-4, 0.03, 150.0, 5e-4])  # weak, literature-scale regulariser (research/LITERATURE_REVIEW.md)
PRIOR_SD = np.array([0.20, 1.2, 0.4, 0.7, 0.8])
SG, P2, N_INS = 0.014, 0.03, 0.14   # glucose effectiveness, insulin-action and insulin-clearance rates (1/min)
TAU_A, TAU_D = 20.0, 45.0           # activity and unmodelled-disturbance time constants (min)
# Meal coefficients shared by everyone: absorption slowing per 30 g fat, 30 g protein, 10 g fibre, then
# the 24-h cosine and sine of carbohydrate sensitivity (glucose tolerance varies over the day).
SLOW0 = np.array([0.3, 0.2, 0.3, 0.0, 0.0])
MEAL_WINDOW, M = 360, 8             # minutes a meal keeps contributing; meals tracked at once
# Filter noise: CGM noise (mg/dL), glucose process noise per 5 min, disturbance SD (mg/dL/min).
# Chosen once on the 9-patient development subset listed in research/DECISION_REPORT.md, then frozen.
OBS_SD, Q_G, SD_D = 2.0, 2.5, 0.5
Q_PAR = np.array([0.003, 0.003, 0.002, 0.002, 0.002])  # parameter random walk per 5 min (log units)
LAB_FEATURES = ["hba1c", "fpg", "insulin", "bmi"]


def activity(mets, dt):
    """Causal low-pass of METs above light activity. An unworn watch (NaN) counts as rest."""
    w = np.exp(-dt / TAU_A)
    return lfilter([1 - w], [1, -w], np.nan_to_num(np.maximum(mets - 1.5, 0.0)))


def meal_ctx(p, origins, future=0):
    """For each origin bin, the meals that matter there: up to M meals logged within the last
    MEAL_WINDOW minutes (plus the next `future` bins when the true future is supplied).
    Returns carbs (O, M), meal descriptors (O, M, 5) = fat, protein, fibre, cos and sin of the meal's
    clock time, and age (O, M) in bins since the meal."""
    m = p["meals"]
    idx = np.concatenate([m["idx"].to_numpy(), np.full(M, -10**9)])
    # food labels count fibre inside total carbohydrate; only the rest reaches the blood as glucose
    carbs = np.concatenate([np.maximum(m["carbs"].to_numpy(float) - m["fiber"].to_numpy(float), 0), np.zeros(M)])
    hour = 2 * np.pi * p["tod"][np.clip(m["idx"].to_numpy(int), 0, len(p["tod"]) - 1)] / 24
    mac = np.concatenate([np.c_[m[["fat", "protein", "fiber"]].to_numpy(float), np.cos(hour), np.sin(hour)], np.zeros((M, 5))])
    age = np.asarray(origins)[:, None] - idx[None, :]
    ok = (age < MEAL_WINDOW // p["dt"]) & (age >= -future)
    pick = np.argsort(np.where(ok, age, 10**9), axis=1, kind="stable")[:, :M]  # most recent first
    ok = np.take_along_axis(ok, pick, 1)
    return carbs[pick] * ok, mac[pick], np.where(ok, np.take_along_axis(age, pick, 1), 0).astype(float)


def meal_ra(k, cbw, ctx, slow, j, dt):
    """Mean glucose appearance (mg/dL/min) during bin `origin + j` from the meals in ctx.
    Two equal-rate gut compartments have a closed form, so every gram is accounted for exactly."""
    carbs, mac, age = ctx
    km = k[..., None] / (1 + mac[..., :3] @ (slow[:3] / np.array([30.0, 30.0, 10.0])))
    F = lambda t: -np.exp(-km * t) * (1 + km * t)  # minus the unabsorbed fraction
    grams = carbs * np.exp(mac[..., 3:] @ slow[3:])  # time-of-day effect on carbohydrate sensitivity
    return cbw * (grams * (F(np.maximum((age + j + 1) * dt, 0)) - F(np.maximum((age + j) * dt, 0)))).sum(-1) / dt


def step(G, X, Z, D, gb, phi, bex, ra, A, dt):
    """Advance glucose G, insulin action X, insulin drive Z and disturbance D by dt minutes.
    Exponential integrator: each linear sub-system is advanced exactly, so any dt is stable."""
    en, ep = np.exp(-N_INS * dt), np.exp(-P2 * dt)
    Z1 = Z * en + phi * np.maximum(G - gb, 0) * (1 - en)  # insulin responds to glucose above basal
    X1 = X * ep + 0.5 * (Z + Z1) * (1 - ep)               # and acts with a delay
    a = SG + 0.5 * (X + X1) + bex * A                     # fractional clearance (1/min)
    b = SG * gb + ra + D                                  # appearance (mg/dL/min)
    return b / a + (G - b / a) * np.exp(-a * dt), X1, Z1, D * np.exp(-dt / TAU_D)


# ---------------------------------------------------------------- online: the twin itself
def assimilate(p, mu, sd, slow=SLOW0, n=128, seed=0, learn=True):
    """Run the twin through a patient's record, updating it at every CGM reading.

    mu, sd: log-normal prior over PARAMS (from labs or population). learn=False freezes the
    parameters at their prior (state-only filter, the 'frozen twin' ablation).
    Returns the filtered ensemble after each bin: states (T, n, 4) = G, X, Z, D and
    log-parameters (T, n, 5), plus the one-step-ahead innovation (T,).
    """
    rng, dt, g = np.random.default_rng(seed), p["dt"], p["g"]
    T, s = len(g), np.sqrt(p["dt"] / 5.0)
    A, ctx, bw = activity(p["mets"], dt), meal_ctx(p, np.arange(T)), p["static"]["weight_kg"]
    L = mu + sd * rng.standard_normal((n, 5))
    lo, hi = PRIOR_MU - 3 * PRIOR_SD, PRIOR_MU + 3 * PRIOR_SD
    S = np.zeros((n, 4))
    S[:, 0] = g[np.isfinite(g)][0] + OBS_SD * rng.standard_normal(n)
    S[:, 1] = S[:, 2] = np.exp(L[:, 1]) * np.maximum(S[:, 0] - np.exp(L[:, 0]), 0)
    out_S, out_L, innov = np.empty((T, n, 4), np.float32), np.empty((T, n, 5), np.float32), np.full(T, np.nan)
    wd = np.exp(-dt / TAU_D)
    for i in range(T):
        P = np.exp(L)
        ra = meal_ra(P[:, 2], P[:, 3] / bw, tuple(c[i] for c in ctx), slow, 0, dt)
        S[:, 0], S[:, 1], S[:, 2], S[:, 3] = step(*S.T, P[:, 0], P[:, 1], P[:, 4], ra, A[i], dt)
        S[:, 0] += Q_G * s * rng.standard_normal(n)
        S[:, 3] += SD_D * np.sqrt(1 - wd**2) * rng.standard_normal(n)
        if learn:
            L += Q_PAR * s * rng.standard_normal((n, 5))
        if np.isfinite(g[i]):  # no reading -> the twin simply coasts on its model
            hx = S[:, 0].copy()
            innov[i] = g[i] - hx.mean()
            Xa = np.concatenate([S, L], 1)
            h = hx - hx.mean()
            K = (Xa - Xa.mean(0)).T @ h / (h @ h + (n - 1) * OBS_SD**2)
            if not learn:
                K[4:] = 0
            Xa += np.outer(g[i] + OBS_SD * rng.standard_normal(n) - hx, K)
            S, L = Xa[:, :4], Xa[:, 4:]
            S[:, 0] = np.clip(S[:, 0], 40, 400)
            S[:, 1:3] = np.maximum(S[:, 1:3], 0)
            L = np.clip(L, lo, hi)
        out_S[i], out_L[i] = S, L
    return out_S, out_L, innov


def rollout(p, origins, S, L, H, slow=SLOW0, conditioned=False, active=None, seed=0):
    """Forecast H bins ahead from the filtered ensembles at `origins`. Returns glucose (O, n, H).

    Standard forecast: only meals logged up to the origin are known and activity relaxes to rest.
    conditioned=True supplies the meals that follow the origin in the record; active (default: same
    as conditioned) supplies the activity that follows. A what-if is a conditioned rollout on a
    record whose future has been edited (see `scenario`).
    """
    rng, dt, bw = np.random.default_rng(seed), p["dt"], p["static"]["weight_kg"]
    origins = np.asarray(origins, int)
    active = conditioned if active is None else active
    A = activity(p["mets"], dt)
    ctx = tuple(c[:, None] for c in meal_ctx(p, origins, future=H if conditioned else 0))
    P = np.exp(L[origins].astype(float))
    G, X, Z, D = (S[origins, :, i].astype(float) for i in range(4))
    out, s, wd = np.empty(G.shape + (H,), np.float32), np.sqrt(dt / 5.0), np.exp(-dt / TAU_D)
    for j in range(1, H + 1):
        Aj = A[np.minimum(origins + j, len(A) - 1)] if active else A[origins] * np.exp(-j * dt / TAU_A)
        ra = meal_ra(P[..., 2], P[..., 3] / bw, ctx, slow, j, dt)
        G, X, Z, D = step(G, X, Z, D, P[..., 0], P[..., 1], P[..., 4], ra, Aj[:, None], dt)
        G = G + Q_G * s * rng.standard_normal(G.shape)
        D = D + SD_D * np.sqrt(1 - wd**2) * rng.standard_normal(G.shape)
        out[..., j - 1] = G
    return out


def scenario(p, i, carb_scale=1.0, add_meal=None, walk_min=0, walk_start=15, walk_mets=3.5):
    """The record as known at bin i with a hypothetical future, for `rollout(..., conditioned=True)`:
    the meal logged at i resized, an optional extra meal (carbs, protein, fat, fibre) eaten now, an
    optional walk. Everything recorded after i is removed, so only the stated inputs differ."""
    q, dt = dict(p), p["dt"]
    m = p["meals"][p["meals"]["idx"] <= i].copy()
    m.loc[m["idx"] == i, ["carbs", "protein", "fat", "fiber"]] *= carb_scale
    if add_meal is not None:
        m.loc[len(m)] = {"idx": i + 1, "kind": "what-if", **dict(zip(["carbs", "protein", "fat", "fiber"], add_meal))}
    q["meals"] = m
    q["mets"] = np.where(np.arange(len(p["mets"])) <= i, p["mets"], 1.2)
    if walk_min:
        q["mets"][i + 1 + walk_start // dt:i + 1 + (walk_start + walk_min) // dt] = walk_mets
    return q


# Lifestyle actions at a meal: (share of the logged meal eaten, minutes of walking from 15 min after it).
ACTIONS = ((1.0, 0), (1.0, 15), (1.0, 30), (0.75, 0), (0.75, 15), (0.75, 30), (0.5, 0), (0.5, 30))
EFFORT = np.array([(1 - a) * 4 + w / 15 for a, w in ACTIONS])  # leaving a quarter of the meal counts like one 15-min walk


def recommend(p, i, S, L, slow=SLOW0, risk=0.3):
    """The least-effort action that brings the twin's P(15+ min above 180 within 3 h) under `risk`.
    One choice per meal, outcome within 3 h: a contextual bandit, which the twin solves exactly by
    trying every action on its own state (what Q-learning would only approximate from trial and error).
    Returns (index into ACTIONS, P for every action); index 0 = no change needed or possible."""
    H = 180 // p["dt"]
    pr = np.array([sustained(rollout(scenario(p, i, carb_scale=a, walk_min=w), [i], S, L, H, slow, conditioned=True)[0], dt=p["dt"]).mean()
                   for a, w in ACTIONS])
    ok = np.flatnonzero(pr < risk)
    k = 0 if pr[0] < risk else int(ok[EFFORT[ok].argmin()]) if len(ok) else int(pr.argmin())
    return k, pr


def standard_meal_rise(L, bw, slow=SLOW0, carbs=50.0, dt=5, H=36):
    """Peak glucose rise (mg/dL) after a standard carbohydrate load taken at basal glucose.
    One identifiable, clinically readable summary of a parameter set: the twin's carb tolerance."""
    gb, phi, k, c, bex = np.exp(np.asarray(L, float)).T
    G, X, Z, D, peak = gb.copy(), 0 * gb, 0 * gb, 0 * gb, gb.copy()
    ctx = (np.array([carbs]), np.zeros((1, 5)), np.array([-1.0]))  # no macros, time-of-day neutral
    for j in range(1, H + 1):
        G, X, Z, D = step(G, X, Z, D, gb, phi, bex, meal_ra(k, c / bw, ctx, slow, j, dt), 0.0, dt)
        peak = np.maximum(peak, G)
    return peak - gb


def first_sustained(traj, thr=180.0, dt=5):
    """Index (last axis = time) where a trajectory first starts a run of at least 15 consecutive
    minutes above thr; -1 if it never does. This is the adverse event the twin forecasts."""
    n = 15 // dt + 1
    above = np.nan_to_num(np.asarray(traj), nan=-np.inf) > thr
    run = np.stack([above[..., i:above.shape[-1] - n + 1 + i] for i in range(n)]).all(0)
    return np.where(run.any(-1), run.argmax(-1), -1)


def sustained(traj, thr=180.0, dt=5):
    return first_sustained(traj, thr, dt) >= 0


# ---------------------------------------------------------------- offline: population components
def meal_windows(patients, H_min=180):
    """Every logged meal with a usable CGM trace after it, as arrays for batched simulation."""
    W = {k: [] for k in ("pid", "i", "g0", "y", "A", "carbs", "mac", "age", "bw")}
    for n, p in enumerate(patients):
        g, H = p["g"], H_min // p["dt"]
        idx = np.array([i for i in p["meals"]["idx"] if i + H < len(g) and np.isfinite(g[i]) and np.isfinite(g[i + 1:i + 1 + H]).mean() >= 0.8], int)
        if not len(idx):
            continue
        c, m, a = meal_ctx(p, idx, future=H)
        A = activity(p["mets"], p["dt"])
        W["pid"].append(np.full(len(idx), n)); W["i"].append(idx); W["g0"].append(g[idx])
        W["y"].append(np.stack([g[i + 1:i + 1 + H] for i in idx])); W["A"].append(np.stack([A[i + 1:i + 1 + H] for i in idx]))
        W["carbs"].append(c); W["mac"].append(m); W["age"].append(a)
        W["bw"].append(np.full(len(idx), p["static"]["weight_kg"]))
    return {k: np.concatenate(v) for k, v in W.items()}


def simulate_windows(W, logtheta, slow, dt):
    """Open-loop simulation of each meal window from its pre-meal glucose, true inputs supplied."""
    gb, phi, k, c, bex = np.exp(logtheta[W["pid"]]).T
    G = W["g0"].copy()
    X = Z = phi * np.maximum(G - gb, 0)
    D, out = np.zeros_like(G), np.empty_like(W["y"])
    for j in range(1, out.shape[1] + 1):
        ra = meal_ra(k, c / W["bw"], (W["carbs"], W["mac"], W["age"]), slow, j, dt)
        G, X, Z, D = step(G, X, Z, D, gb, phi, bex, ra, W["A"][:, j - 1], dt)
        out[:, j - 1] = G
    return out


def fit_traits(patients, slow=None, sigma=15.0):
    """Joint robust fit of every patient's parameters (their 'trait') and, if slow is None, the shared
    meal-composition coefficients. No lab value is used here, so traits can later be compared with labs."""
    W, dt, P = meal_windows(patients), patients[0]["dt"], len(patients)
    mask = np.isfinite(W["y"])
    fit_slow = slow is None

    def res(x):
        th = x[5:].reshape(P, 5)
        r = (simulate_windows(W, th, x[:5] if fit_slow else slow, dt) - np.nan_to_num(W["y"])) / sigma
        return np.concatenate([(r * mask).ravel(), ((th - PRIOR_MU) / PRIOR_SD).ravel()])

    nW, H = W["y"].shape
    J = lil_matrix((nW * H + 5 * P, 5 + 5 * P), dtype=int)
    if fit_slow:
        J[:nW * H, :5] = 1
    rows = np.arange(nW * H).reshape(nW, H)
    for n in range(P):
        J[rows[W["pid"] == n].ravel()[:, None], 5 + 5 * n + np.arange(5)] = 1
    J[nW * H + np.arange(5 * P), 5 + np.arange(5 * P)] = 1
    x0 = np.concatenate([SLOW0, np.tile(PRIOR_MU, P)])
    lb = np.concatenate([[0, 0, 0, -1, -1], np.tile(PRIOR_MU - 3 * PRIOR_SD, P)])
    ub = np.concatenate([[2, 2, 2, 1, 1], np.tile(PRIOR_MU + 3 * PRIOR_SD, P)])
    sol = least_squares(res, x0, jac_sparsity=J, bounds=(lb, ub), loss="soft_l1", max_nfev=60)
    return sol.x[5:].reshape(P, 5), (sol.x[:5] if fit_slow else np.asarray(slow))


def _lab_x(static):
    v = np.array([static.get(f, np.nan) for f in LAB_FEATURES], float)
    v[1:3] = np.log(np.maximum(v[1:3], 1e-3))  # fasting glucose and insulin enter as logs (HOMA is their product)
    return v


def fit_population(patients, slow=None):
    """Everything the twin learns across patients: meal-composition effects, the population prior
    and the ridge map from lab values to each patient's prior. Fit on training patients only."""
    traits, slow = fit_traits(patients, slow)
    X = np.array([_lab_x(p["static"]) for p in patients])
    xm, xs = np.nanmean(X, 0), np.nanstd(X, 0) + 1e-9
    Xs = np.nan_to_num((X - xm) / xs)
    mu, Y = traits.mean(0), traits - traits.mean(0)
    best = None
    for lam in (1.0, 3.0, 10.0, 30.0):  # ridge strength by exact leave-one-out error
        Hm = Xs @ np.linalg.solve(Xs.T @ Xs + lam * np.eye(Xs.shape[1]), Xs.T)
        loo = (Y - Hm @ Y) / (1 - np.diag(Hm))[:, None]
        if best is None or (loo**2).sum() < best[0]:
            best = ((loo**2).sum(), lam, np.sqrt((loo**2).mean(0)))
    _, lam, sd_lab = best
    Wt = np.linalg.solve(Xs.T @ Xs + lam * np.eye(Xs.shape[1]), Xs.T @ Y)
    sd_pop = traits.std(0)
    return {"slow": slow, "mu": mu, "sd": np.maximum(sd_pop, 0.05), "W": Wt, "xm": xm, "xs": xs, "lam": lam,
            "sd_lab": np.maximum(np.minimum(sd_lab, sd_pop), 0.05), "traits": traits, "r2_loo": 1 - sd_lab**2 / np.maximum(sd_pop**2, 1e-12)}


def prior(pop, static, labs=True):
    """Log-normal prior (mean, sd) over PARAMS for a new patient: from their labs, or the population."""
    if not labs:
        return pop["mu"], pop["sd"]
    return pop["mu"] + np.nan_to_num((_lab_x(static) - pop["xm"]) / pop["xs"]) @ pop["W"], pop["sd_lab"]
