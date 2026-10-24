"""Run from the repo root: python context/scripts/score_new.py (needs data/processed/cv.pkl from twin.evaluate).
Score the new Kaggle forecasts the way twin.evaluate does (same rows, patient bootstrap), without writing results."""
import pickle

import numpy as np
import pandas as pd

from twin import evaluate as ev
from twin.data import PROC, load
from twin.hybrid import HORIZONS
from twin.india import REGIONS

roll, meal, par, models, rob, ext, ext_model, ext_rows, ver, rec = pickle.loads((PROC / "cv.pkl").read_bytes())
f = lambda c, h: f"{c[0]:.2f} ({c[1]:.2f} to {c[2]:.2f})"

for name, d, files in (("CGMacros, held-out patients", roll[roll["variant"] == "full"], ("chronos.pkl", "neural.pkl", "tsfm.pkl")),
                       ("ShanghaiT2DM, external", ext_rows, ("chronos_ext.pkl", "neural_ext.pkl", "tsfm_ext.pkl"))):
    d = ev.with_baselines(d, files)
    for h in HORIZONS:
        d[f"ensm{h}"] = (d[f"hybrid{h}"] + d[f"moment{h}"]) / 2
    print(f"\n== {name}: RMSE mg/dL (95% CI by patient) ==")
    for h in HORIZONS:
        x = d[["id", f"y{h}"] + [f"{m}{h}" for m in ("pers", "lgbm", "hybrid", "c2ft", "ens", "moment", "ensm")]].dropna()
        row = {m: ev.rmse(x, m, h) for m in ("pers", "lgbm", "hybrid", "c2ft", "ens", "moment", "ensm")}
        print(f"{h:3d} min  n={len(x)}  " + "  ".join(f"{m} {v:.2f}" for m, v in row.items()))
        for a, b in (("moment", "hybrid"), ("moment", "c2ft"), ("moment", "lgbm"), ("ensm", "ens")):
            print(f"         {a} minus {b}: {f(ev.boot(x, lambda q: ev.rmse(q, a, h) - ev.rmse(q, b, h)), h)}")
        print(f"         moment mean error (+ = too high): {(x[f'moment{h}'] - x[f'y{h}']).mean():+.2f}")

print("\n== Simulated Indian regions (test half of each region): RMSE mg/dL ==")
C, M = pd.read_pickle(PROC / "chronos_india.pkl"), pd.read_pickle(PROC / "tsfm_india.pkl")
allr = []
for r in REGIONS:
    Q = {p["id"]: p for p in load(f"india_{r}")[1::2]}
    d = C[C["id"].isin(Q)].merge(M, on=["id", "i"])
    for h in HORIZONS:
        k = h // 5
        d[f"y{h}"] = [Q[a]["g"][i + k] if i + k < len(Q[a]["g"]) else np.nan for a, i in zip(d["id"], d["i"])]
        d[f"pers{h}"] = [Q[a]["g"][i] for a, i in zip(d["id"], d["i"])]
    d["region"] = r
    allr.append(d)
    out = []
    for h in HORIZONS:
        x = d.dropna(subset=[f"y{h}"])
        out.append(f"{h}m: pers {ev.rmse(x, 'pers', h):.2f} chronos {ev.rmse(x, 'c2ft', h):.2f} moment {ev.rmse(x, 'moment', h):.2f}")
    print(f"{r:10s} " + " | ".join(out))
d = pd.concat(allr, ignore_index=True)
for h in HORIZONS:
    x = d.dropna(subset=[f"y{h}"])
    print(f"all six, {h:3d} min: pers {ev.rmse(x, 'pers', h):.2f} chronos {ev.rmse(x, 'c2ft', h):.2f} moment {ev.rmse(x, 'moment', h):.2f}  "
          f"moment minus chronos {f(ev.boot(x, lambda q: ev.rmse(q, 'moment', h) - ev.rmse(q, 'c2ft', h)), h)}")
