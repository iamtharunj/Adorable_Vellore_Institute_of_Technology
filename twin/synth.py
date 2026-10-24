"""Synthetic patients: linked EHR + wearable streams from a glucose simulator that is deliberately
RICHER than the twin (stomach emptying, explicit plasma insulin with first-phase secretion,
hepatic suppression, circadian insulin sensitivity, dawn effect, sensor lag and coloured noise).

Uses: (1) verification -- does the twin recover known physiology, and do its what-ifs match TRUE
counterfactuals; (2) a demo cohort that needs no download; (3) a privacy-safe test bed.
No performance claim in this repository rests on synthetic data. Every record is simulated; none
is, or is derived from, a real person.
"""
import math
from pathlib import Path

import numpy as np
import pandas as pd

from .india import REGIONS, menu, plate

# name, carbs, protein, fat, fibre (g per typical serving). Approximate, for plausibility only.
MEALS = {
    "breakfast": [("idli-sambar", 45, 8, 3, 5), ("poha", 50, 6, 9, 3), ("paratha-curd", 55, 11, 16, 5),
                  ("masala dosa", 48, 7, 9, 3), ("upma", 42, 7, 10, 4), ("oats-milk", 35, 9, 6, 6)],
    "lunch": [("rice-dal-sabzi", 85, 18, 12, 9), ("roti-sabzi-dal", 60, 16, 12, 11), ("curd rice", 70, 10, 9, 2),
              ("chicken biryani", 90, 28, 24, 5), ("rajma-chawal", 80, 18, 10, 12)],
    "dinner": [("roti-paneer", 50, 22, 22, 7), ("khichdi", 60, 14, 8, 6), ("rice-sambar", 75, 12, 8, 7),
               ("millet roti-sabzi", 45, 10, 8, 10)],
    "snack": [("chai-biscuits", 22, 3, 6, 1), ("fruit", 20, 1, 0, 3), ("samosa", 30, 5, 15, 2), ("mithai", 35, 3, 10, 0)],
}
MEAL_HOURS = {"breakfast": 8.2, "lunch": 13.2, "dinner": 20.3, "snack": 16.8}
S_MEAN, S_SD = 1.3 / 2.9, 0.252  # mean and SD of the Beta(1.3, 1.6) severity
REGION_CODE = {"north": "N", "south": "S", "east": "E", "west": "W", "central": "C", "northeast": "NE"}


def _spec(rng, pid, region=None):
    """One virtual person: latent metabolic severity -> physiology -> consistent EHR fields. With a region
    (twin.india), age, sex and BMI follow that region's ICMR-INDIAB-21 distribution and the person gets a home
    state, its plates and their own habits; the physiology itself is the same everywhere."""
    sev = REGIONS[region]["sev"] if region else 1.0                 # regional severity scale (india.calibrate)
    s = float(np.clip(rng.beta(1.3, 1.6) * sev, 0.02, 0.98))         # 0 healthy ... 1 advanced T2D
    alleles = int(rng.binomial(2, 0.30))                             # simulated TCF7L2 rs7903146 risk alleles
    if region:
        R, z = REGIONS[region], (s / sev - S_MEAN) / S_SD              # standardised within the region
        (bm, b1, b3), (am, a1, a3) = R["bmi"], R["age"]                # median, IQR; severity explains part of the spread
        bmi = float(np.clip(bm * math.exp(math.log(b3 / b1) / 1.349 * (0.6 * z + 0.8 * rng.standard_normal())), 15, 42))
        age = float(np.clip(am + (a3 - a1) / 1.349 * (0.5 * z + 0.87 * rng.standard_normal()), 20, 80))
        states = list(R["states"])
        state = states[rng.choice(len(states), p=np.array(list(R["states"].values())) / sum(R["states"].values()))]
        m = menu(region, state)
        extra = {"id": f"IN{REGION_CODE[region]}-{pid:03d}", "region": region, "state": state, "sex": "M" if rng.random() < R["male"] else "F",
                 "active": bool(rng.random() > R["inactive"]), "menu": m,
                 "habit": {k: rng.gamma(2.0, 1.0, len(v)) * [w for _, _, w in v] for k, v in m.items()},  # own favourites
                 "appetite": float(math.exp(rng.normal(0, 0.12)))}
    else:
        bmi = float(np.clip(rng.normal(23.5 + 4.5 * s, 3.3), 17, 42))
    height = float(rng.normal(1.62, 0.08))
    si = 8e-4 * math.exp(-1.9 * s + rng.normal(0, 0.25) - 0.03 * (bmi - 24))    # insulin sensitivity
    beta = 0.22 * math.exp(-1.7 * s + rng.normal(0, 0.25) - 0.16 * alleles)     # beta-cell response
    gb = float(86 + 75 * s**1.5 + rng.normal(0, 5))
    sp = {
        "id": f"SYN-{pid:03d}", "severity": s, "alleles": alleles, "bmi": bmi, "height": height, "bw": bmi * height**2,
        "age": float(np.clip(rng.normal(42 + 16 * s, 11), 22, 78)), "sex": "F" if rng.random() < 0.48 else "M",
        "si": si, "beta": beta, "beta_d": 6 * beta * math.exp(rng.normal(0, 0.3)), "gb": gb,
        "ib": 6.5 * (8e-4 / si) ** 0.6 * (beta / 0.22) ** 0.3,       # fasting insulin: resistance raises it, beta-cell loss lowers it
        "kemp": 0.045 * math.exp(rng.normal(0, 0.2)), "kabs": 0.055, "bex": 9e-4 * math.exp(rng.normal(0, 0.35)),
        "circ": float(rng.uniform(0.08, 0.25)), "dawn": float(rng.uniform(0.0, 0.25) * (0.5 + s)),
        "lag": float(rng.uniform(7, 12)), "hr_rest": float(rng.normal(68 + 6 * s, 5)),
    }
    return {**sp, **extra, "age": age} if region else sp


def _plan(rng, sp, days, dt, p_unlogged, p_walk, wear_dropout):
    """What the person does: sleep, meals, activity. Returned at 1-minute resolution."""
    T = days * 1440
    mets, sleep, meals = np.full(T, 1.25), np.zeros(T, int), []
    for d in range(days):
        bed, wake = int(d * 1440 + rng.normal(23.3, 0.6) * 60), int((d + 1) * 1440 + rng.normal(6.6, 0.5) * 60)
        t = bed
        while t < min(wake, T):                                       # 0 awake, 1 light, 2 deep, 3 REM
            st, ln = rng.choice([1, 2, 3, 0], p=[0.5, 0.2, 0.22, 0.08]), int(rng.integers(10, 40))
            sleep[t:min(t + ln, wake, T)] = st if st else 0
            mets[t:min(t + ln, wake, T)] = 0.95 if st else 1.1
            t += ln
        for kind in ("breakfast", "lunch", "dinner", "snack"):
            if kind == "snack" and rng.random() < 0.35:
                continue
            t = int(d * 1440 + rng.normal(21.0 if "menu" in sp and kind == "dinner" else MEAL_HOURS[kind], 0.5) * 60)
            if "menu" in sp:  # a regional plate, picked by this person's habits; carries its GI
                opts, w = sp["menu"][kind], sp["habit"][kind]
                name, items, _ = opts[rng.choice(len(opts), p=w / w.sum())]
                m = plate(items, sp["appetite"])
            else:
                name, *mac = MEALS[kind][rng.integers(len(MEALS[kind]))]
                m = dict(zip(("carbs", "protein", "fat", "fiber"), mac))
            size = math.exp(rng.normal(0, 0.25))
            walk = rng.random() < p_walk and kind != "snack"
            if 0 <= t < T - 200:
                meals.append({"t": t, "kind": kind, "name": name, **{k: v if k == "gi" else v * size for k, v in m.items()},
                              "logged": rng.random() > p_unlogged * (2.5 if kind == "snack" else 1), "walk": walk})
                if walk:
                    w0 = t + int(rng.integers(10, 30))
                    mets[w0:w0 + int(rng.integers(12, 25))] = rng.uniform(3.0, 4.0)
        busy = sp.get("active", False)  # regional: physically active (PAL >= 1.7) people move more through the day
        for _ in range(rng.poisson(4.0 if busy else 1.5)):              # incidental activity
            a = int(d * 1440 + rng.uniform(7.5, 21) * 60)
            mets[a:a + int(rng.integers(20, 60) if busy else rng.integers(8, 45))] = rng.uniform(2.5, 5.0) if busy else rng.uniform(2.0, 5.5)
    worn = np.ones(T, bool)
    for _ in range(rng.poisson(days * wear_dropout * 3)):
        a = int(rng.integers(0, T))
        worn[a:a + int(rng.integers(30, 400))] = False
    return {"T": T, "mets": mets[:T], "sleep": sleep[:T], "worn": worn, "meals": meals,
            "noise": rng.standard_normal(T // dt + 1), "bias": float(rng.normal(0, 0.03))}


def simulate(sp, plan, dt=5):
    """Run the reference physiology for one person and plan. Deterministic given (sp, plan), so a
    modified plan gives a true counterfactual. Returns (plasma glucose per minute, CGM per dt)."""
    T, mets = plan["T"], plan["mets"]
    speed = any("gi" in m for m in plan["meals"])  # regional plates: stomach empties in proportion to GI / 70 (our assumption)
    inp = np.zeros((T, 4))
    for m in plan["meals"]:
        inp[m["t"]] += (m["carbs"] - m["fiber"], m["fat"], m["fiber"], (m["carbs"] - m["fiber"]) * m.get("gi", 70) / 70)
    G = Gi = sp["gb"]
    I, X, Qs, Qg, Qr, E, B, fat, fib, dG = sp["ib"], 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    sg, p2, n, cbw = 0.012, 0.025, 0.15, 0.8 * 1000 / (2.2 * sp["bw"])  # bioavailability / distribution volume
    out, cgm, e = np.empty(T), [], 0.0
    for t in range(T):
        h = (t % 1440) / 60.0
        Qs += inp[t, 0]; Qr += inp[t, 3]; fat = fat * 0.992 + inp[t, 1]; fib = fib * 0.992 + inp[t, 2]
        kemp = sp["kemp"] / (1 + fat / 35 + fib / 12) * (0.6 + 0.4 / (1 + (Qs / 50) ** 2))
        if speed and Qs > 1e-6:
            kemp *= Qr / Qs                                            # GI-weighted mix of what is in the stomach
        ra = cbw * sp["kabs"] * Qg
        Qs, Qg, Qr = Qs - kemp * Qs, Qg + kemp * Qs - sp["kabs"] * Qg, Qr - kemp * Qr
        act = max(mets[t] - 1.5, 0.0)
        E += (act - E) / 15; B += (0.15 * E - B) / 180                # acute uptake and slower sensitisation
        si = sp["si"] * (1 + sp["circ"] * math.cos(2 * math.pi * (h - 13) / 24)) * (1 + B)
        I += -n * (I - sp["ib"]) + sp["beta"] * max(G - sp["gb"], 0) + sp["beta_d"] * max(dG, 0)
        X += -p2 * X + p2 * si * (I - sp["ib"])
        egp = sg * sp["gb"] / (1 + max(I - sp["ib"], 0) / (1.5 * sp["ib"]))  # insulin suppresses liver output
        dawn = sp["dawn"] * sg * sp["gb"] * math.exp(-((h - 6) / 1.5) ** 2)
        dG = -(sg + X + sp["bex"] * E) * G + egp + ra + dawn
        G = max(G + dG, 40.0)
        Gi += (G - Gi) / sp["lag"]
        out[t] = G
        if t % dt == dt - 1:
            e = 0.8 * e + 0.6 * 3.0 * plan["noise"][t // dt]            # AR(1) sensor noise, SD 3 mg/dL
            cgm.append(Gi * (1 + plan["bias"]) + e)
    return out, np.array(cgm)


def true_standard_rise(sp):
    """Ground truth for the twin's carb-tolerance summary: peak rise after 50 g carbohydrate at noon."""
    plan = {"T": 1440, "mets": np.full(1440, 1.25), "meals": [{"t": 720, "carbs": 50.0, "fat": 0.0, "fiber": 0.0}],
            "noise": np.zeros(289), "bias": 0.0}
    g, _ = simulate(sp, plan)
    return float(g[720:900].max() - g[719])


def _record(sp, plan, cgm, rng, dt, cgm_dropout):
    T = plan["T"] // dt
    g = cgm.copy()
    for _ in range(rng.poisson(T * cgm_dropout / 12)):
        a = int(rng.integers(0, T))
        g[a:a + int(rng.integers(3, 30))] = np.nan
    b = lambda v: v.reshape(T, dt)
    worn = b(plan["worn"]).all(1)
    mets = np.where(worn, b(plan["mets"]).mean(1), np.nan)
    hr = np.where(worn, sp["hr_rest"] + 13 * (b(plan["mets"]).mean(1) - 1) + rng.normal(0, 3, T), np.nan)
    steps = np.where(worn, np.maximum(b(plan["mets"]).mean(1) - 1.6, 0) * 55 * dt, np.nan).round()
    a1c = (np.nanmean(g) + 46.7) / 28.7 + rng.normal(0, 0.15)            # ADAG relation + assay noise
    fpg = sp["gb"] + rng.normal(0, 4)
    homa_ir = fpg * sp["ib"] / 405
    static = {"age": round(sp["age"]), "sex": sp["sex"], "bmi": round(sp["bmi"], 1), "weight_kg": round(sp["bw"], 1),
              "hba1c": round(a1c, 1), "fpg": round(fpg), "insulin": round(sp["ib"] * math.exp(rng.normal(0, 0.15)), 1),
              "tg": round(95 * math.exp(0.35 * math.log(max(homa_ir, 0.3)) + rng.normal(0, 0.3))),
              "hdl": round(54 - 4 * math.log(max(homa_ir, 0.3)) + rng.normal(0, 7)),
              "tcf7l2_risk_alleles": sp["alleles"], "family_history": bool(rng.random() < 0.25 + 0.4 * sp["severity"]),
              "hypertension": bool(rng.random() < 0.15 + 0.35 * sp["severity"] + 0.004 * (sp["age"] - 40))}
    grp = "healthy" if a1c < 5.7 else "prediabetes" if a1c < 6.5 else "T2D"
    if "region" in sp:  # ICMR-INDIAB's rule: HbA1c or fasting glucose (no OGTT here)
        grp = "T2D" if a1c >= 6.5 or fpg >= 126 else "prediabetes" if a1c >= 5.7 or fpg >= 100 else "healthy"
    static["medications"] = {"healthy": "none", "prediabetes": "none"}.get(grp, "metformin" + (", glimepiride" if sp["severity"] > 0.75 else ""))
    if "region" in sp:  # ICMR-INDIAB-21 regional medians and shares; its type 2 diabetes is newly diagnosed, so untreated
        R = REGIONS[sp["region"]]
        static.update(tg=round(static["tg"] * R["tg"] / 111), hdl=round(static["hdl"] + R["hdl"] - 50), medications="none",
                      family_history=bool(rng.random() < R["family"] * (1 + sp["severity"]) / (1 + S_MEAN)),
                      region=sp["region"], state=sp["state"], physically_active=sp["active"],
                      tobacco=bool(rng.random() < R["tobacco"]), alcohol=bool(rng.random() < R["alcohol"]))
    lg = [m for m in plan["meals"] if m["logged"]]
    le = lambda k: [m[k] * math.exp(rng.normal(0, 0.12)) for m in lg]    # logging error on portions
    meals = pd.DataFrame({"idx": [m["t"] // dt for m in lg], "kind": [m["kind"] for m in lg], "name": [m["name"] for m in lg],
                          "carbs": le("carbs"), "protein": le("protein"), "fat": le("fat"), "fiber": le("fiber")})
    return {"id": sp["id"], "cohort": f"india_{sp['region']}" if "region" in sp else "synthetic", "group": grp, "dt": dt, "static": static, "g": g, "hr": hr, "mets": mets,
            "steps": steps, "sleep": b(plan["sleep"])[:, -1], "tod": ((np.arange(T) + 1) * dt / 60) % 24,
            "meals": meals.drop_duplicates("idx").sort_values("idx").reset_index(drop=True), "truth": sp, "plan": plan}


def generate(n=60, days=14, seed=7, dt=5, p_unlogged=0.10, p_walk=0.30, cgm_dropout=0.03, wear_dropout=0.08, region=None):
    """A cohort of virtual patients. Every knob that shapes data quality is an argument. With a region (twin.india),
    people are drawn until the region's ICMR-INDIAB-21 shares of normal glucose, prediabetes and newly diagnosed
    type 2 diabetes (by HbA1c) are filled."""
    if region is None:
        rng, out = np.random.default_rng(seed), []
        for i in range(n):
            sp = _spec(rng, i + 1)
            plan = _plan(rng, sp, days, dt, p_unlogged, p_walk, wear_dropout)
            out.append(_record(sp, plan, simulate(sp, plan, dt)[1], rng, dt, cgm_dropout))
        return out
    R, rng, out = REGIONS[region], np.random.default_rng([seed, list(REGIONS).index(region)]), []
    left = {"T2D": round(n * R["t2d"]), "prediabetes": round(n * R["prediabetes"])}
    left["healthy"] = n - sum(left.values())
    for _ in range(40 * n):
        sp = _spec(rng, len(out) + 1, region)
        plan = _plan(rng, sp, days, dt, p_unlogged, p_walk, wear_dropout)
        rec = _record(sp, plan, simulate(sp, plan, dt)[1], rng, dt, cgm_dropout)
        if left[rec["group"]] > 0:
            left[rec["group"]] -= 1
            out.append(rec)
        if len(out) == n:
            return out
    raise RuntimeError(f"{region}: could not fill {left}")


def export(patients, outdir):
    """Write the cohort as Synthea-style EHR tables plus one wearable CSV per patient."""
    out = Path(outdir)
    (out / "wearables").mkdir(parents=True, exist_ok=True)
    start = pd.Timestamp("2026-01-05")
    loinc = {"hba1c": ("4548-4", "Hemoglobin A1c", "%"), "fpg": ("1558-6", "Fasting glucose", "mg/dL"),
             "insulin": ("20448-7", "Insulin, fasting", "uU/mL"), "tg": ("2571-8", "Triglycerides", "mg/dL"),
             "hdl": ("2085-9", "HDL cholesterol", "mg/dL"), "bmi": ("39156-5", "Body mass index", "kg/m2"),
             "weight_kg": ("29463-7", "Body weight", "kg")}
    snomed = {"T2D": (44054006, "Type 2 diabetes mellitus"), "prediabetes": (15777000, "Prediabetes")}
    pat, obs, cond, med, meals = [], [], [], [], []
    for p in patients:
        s = p["static"]
        pat.append({"Id": p["id"], "BIRTHYEAR": 2026 - s["age"], "GENDER": s["sex"], "SYNTHETIC": True,
                    "TCF7L2_RS7903146_RISK_ALLELES": s.get("tcf7l2_risk_alleles"), "FAMILY_HISTORY_DIABETES": s.get("family_history"),
                    **({k.upper(): s[k] for k in ("region", "state", "physically_active", "tobacco", "alcohol")} if "region" in s else {})})
        obs += [{"PATIENT": p["id"], "DATE": start.date(), "CODE": c, "DESCRIPTION": d, "VALUE": s[k], "UNITS": u} for k, (c, d, u) in loinc.items()]
        if p["group"] in snomed:
            cond.append({"PATIENT": p["id"], "START": start.date(), "CODE": snomed[p["group"]][0], "DESCRIPTION": snomed[p["group"]][1]})
        if s.get("hypertension"):
            cond.append({"PATIENT": p["id"], "START": start.date(), "CODE": 59621000, "DESCRIPTION": "Essential hypertension"})
        med += [{"PATIENT": p["id"], "START": start.date(), "DESCRIPTION": m.strip()} for m in str(s.get("medications", "none")).split(",") if m.strip() != "none"]
        ts = start + pd.to_timedelta((np.arange(len(p["g"])) + 1) * p["dt"], "min")
        pd.DataFrame({"timestamp": ts, "cgm_mgdl": np.round(p["g"], 1), "heart_rate_bpm": np.round(p["hr"]), "steps": p.get("steps"),
                      "mets": np.round(p["mets"], 2), "sleep_stage": p.get("sleep")}).to_csv(out / "wearables" / f"{p['id']}.csv", index=False)
        m = p["meals"].copy()
        m.insert(0, "PATIENT", p["id"]); m.insert(1, "timestamp", ts[m["idx"].to_numpy()])
        meals.append(m.drop(columns="idx").round(1))
    for name, rows in [("patients", pat), ("observations", obs), ("conditions", cond), ("medications", med)]:
        pd.DataFrame(rows).to_csv(out / f"{name}.csv", index=False)
    pd.concat(meals).to_csv(out / "meals.csv", index=False)


if __name__ == "__main__":
    from .data import ROOT, load
    cohort = load("synthetic")
    export(cohort, ROOT / "data" / "synthetic")
    print(len(cohort), "synthetic patients ->", ROOT / "data" / "synthetic", pd.Series([p["group"] for p in cohort]).value_counts().to_dict())
