"""More forecasting baselines, run on Kaggle by kaggle/tsfm_run.py outside this package, because each brings its
own pinned dependencies: Moirai (zero-shot, with covariates), MOMENT (frozen encoder, forecasting head trained per
fold) and TS2Vec (self-supervised encoder per fold + ridge). Same folds, origins, one-day context and covariates as
twin.chronos_baseline, on the same three datasets: CGMacros folds, ShanghaiT2DM, and the six simulated Indian regions.
  python -m twin.tsfm export   kaggle/prandialtwin_kit.zip, the one Kaggle dataset for both notebooks: this package
                               and the records for twin.chronos_baseline, plus series.npz (plain arrays, readable by
                               any numpy) and the runner for kaggle/run_tsfm.ipynb
  python -m twin.tsfm merge    kaggle/tsfm_out/<model>_<part>.csv -> data/processed/tsfm.pkl, tsfm_ext.pkl and
                               tsfm_india.pkl"""
import pickle
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from .data import PROC, folds, load
from .evaluate import degrade_to
from .hybrid import origins
from .india import REGIONS

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "kaggle"
PARTS = {"tsfm.pkl": [f"fold{k}" for k in range(5)], "tsfm_ext.pkl": ["ext"], "tsfm_india.pkl": [f"india_{r}" for r in REGIONS]}
SLIM = ("id", "cohort", "dt", "g", "group", "hr", "meals", "mets", "tod", "static")  # what the Kaggle runs read of a simulated record


def export():
    from .chronos_baseline import covariates
    P, sh, IN = load("cgmacros"), load("shanghai"), {r: load(f"india_{r}") for r in REGIONS}
    fold = np.zeros(len(P), int)
    for f, ti in enumerate(folds(P, 5)):
        fold[ti] = f
    z = {"home_fold": fold}
    for c, Q in (("home", P), ("home15", [degrade_to(p) for p in P]), ("ext", sh), *((f"india_{r}", Q) for r, Q in IN.items())):
        cov, o = [covariates(p, ("carbs", "mets", "hr")) for p in Q], [origins(p) for p in Q]
        z |= {f"{c}_ids": np.array([p["id"] for p in Q]), f"{c}_dt": Q[0]["dt"], f"{c}_len": [len(p["g"]) for p in Q],
              f"{c}_g": np.concatenate([p["g"] for p in Q]).astype(float), f"{c}_olen": [len(x) for x in o], f"{c}_o": np.concatenate(o),
              **{f"{c}_{k}": np.concatenate([v[k] for v in cov]) for k in ("carbs", "mets", "hr")}}
    np.savez_compressed(PROC / "series.npz", **z)
    with zipfile.ZipFile(KIT / "prandialtwin_kit.zip", "w", zipfile.ZIP_DEFLATED) as f:  # CGMacros-derived: a PRIVATE Kaggle dataset
        for s in sorted((ROOT / "twin").glob("*.py")):
            f.write(s, f"prandialtwin/twin/{s.name}")
        for s in ("cgmacros.pkl", "shanghai.pkl", "twin_cov.pkl", "chronos_parts/zero.pkl", "chronos_parts/zero_ext.pkl"):
            f.write(PROC / s, f"prandialtwin/data/processed/{s}")
        for r, Q in IN.items():
            f.writestr(f"prandialtwin/data/processed/india_{r}.pkl", pickle.dumps([{k: p[k] for k in SLIM} for p in Q]))
        f.write(PROC / "series.npz", "tsfm/series.npz")
        f.write(KIT / "tsfm_run.py", "tsfm/tsfm_run.py")
    print("wrote", KIT / "prandialtwin_kit.zip")


def merge():
    """Each output file gets every model that has all of its parts; models with only some parts are listed, not merged."""
    got = {}
    for f in sorted((KIT / "tsfm_out").glob("*_*.csv")):
        model, part = f.stem.split("_", 1)
        got.setdefault(model, {})[part] = pd.read_csv(f).set_index(["id", "i"])
    for name, parts in PARTS.items():
        done = [m for m in got if all(k in got[m] for k in parts)]
        print(name, done, "| incomplete:", [m for m in got if m not in done and any(k in got[m] for k in parts)])
        if done:
            pd.concat([pd.concat([got[m][k] for k in parts]) for m in done], axis=1).reset_index().to_pickle(PROC / name)


if __name__ == "__main__":
    {"export": export, "merge": merge}[sys.argv[1]]()
