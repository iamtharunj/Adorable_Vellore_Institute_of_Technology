"""Run from the repo root: python context/scripts/score_india.py (needs india_<r>_roll.pkl from twin.india).
Indian regions: the twin's own forecasts (twin.india.check, saved as india_<r>_roll.pkl) next to every Kaggle model,
at the same moments, plus each model averaged with the hybrid twin. Patient-bootstrap intervals. Writes nothing."""
import numpy as np
import pandas as pd

from twin import evaluate as ev
from twin.data import PROC
from twin.hybrid import HORIZONS
from twin.india import REGIONS

new = [pd.read_pickle(PROC / f) for f in ("chronos_india.pkl", "tsfm_india.pkl") if (PROC / f).exists()]
rows = []
for r in REGIONS:
    d = pd.read_pickle(PROC / f"india_{r}_roll.pkl")
    for x in new:
        d = d.merge(x, on=["id", "i"], how="inner")
    d["region"] = r
    rows.append(d)
d = pd.concat(rows, ignore_index=True)
extra = [m for m in ("c2ft", "moment", "moirai", "ts2vec") if f"{m}60" in d]
for m in extra:
    for h in HORIZONS:
        d[f"hyb+{m}{h}"] = (d[f"hybrid{h}"] + d[f"{m}{h}"]) / 2
models = ["pers", "lgbm", "twin", "hybrid"] + extra + [f"hyb+{m}" for m in extra]
ci = lambda c: f"{c[0]:+.2f} ({c[1]:+.2f} to {c[2]:+.2f})"

print("RMSE mg/dL at 60 min by region (same moments for every model)")
print(f"{'':10s}" + "".join(f"{m:>12s}" for m in models))
for r, x in d.groupby("region", sort=False):
    x = x.dropna(subset=["y60"])
    print(f"{r:10s}" + "".join(f"{ev.rmse(x, m, 60):12.2f}" for m in models))
for h in HORIZONS:
    x = d[["id", f"y{h}"] + [f"{m}{h}" for m in models]].dropna()
    print(f"\nAll six regions, {h} min, n={len(x)}, {x['id'].nunique()} people: " + ", ".join(f"{m} {ev.rmse(x, m, h):.2f}" for m in models))
    for m in models:
        if m != "hybrid":
            print(f"   {m} minus hybrid: {ci(ev.boot(x, lambda q, m=m: ev.rmse(q, m, h) - ev.rmse(q, 'hybrid', h)))}")
