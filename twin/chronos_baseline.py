"""Optional baselines: pretrained time-series foundation models. Needs `pip install -e .[chronos]`; a GPU makes it
about an hour. `python -m twin.chronos_baseline` writes data/processed/chronos.pkl (CGMacros, held-out folds) and
chronos_ext.pkl (ShanghaiT2DM), which twin.evaluate picks up:
- chronos: Chronos-Bolt, zero-shot, CGM history alone;
- c2, c2cov: Chronos-2, zero-shot, CGM alone and CGM + carbohydrate, METs and heart rate as past covariates;
- c2ft: Chronos-2 fine-tuned inside each patient-level fold (full fine-tune, learning rate and steps fixed in
  advance, checkpoint chosen on the fold's calibration patients), with the same covariates;
- ShanghaiT2DM: Chronos-2 zero-shot and fine-tuned on all of CGMacros degraded to 15-min CGM, with
  carbohydrate as the one covariate both sites share;
- c2tw: as c2ft, plus the twin's filtered states and parameters (TW, from `python -m twin.evaluate --twin-cov`)
  as further covariates: the twin-informed Chronos-2.
- india_<region>: Chronos-2 fine-tuned on half of one simulated Indian region, tested on the other half (c2ft).
The work is split into parts (zero, zero_ext, fold0..fold4, ext, india_<region>), each cached in
data/processed/chronos_parts/, so they can run on different machines: `python -m twin.chronos_baseline fold2 fold3`
runs just those; with no argument every missing part runs and the parts are merged into chronos.pkl, chronos_ext.pkl
and chronos_india.pkl; `merge` only merges the parts that are there. Fine-tuned models are kept in
data/processed/models/ and reused if present."""
import sys
from functools import cache

import numpy as np
import pandas as pd
import torch
from chronos import BaseChronosPipeline, Chronos2Pipeline

from .data import PROC, folds, load
from .evaluate import degrade_to
from .hybrid import HORIZONS, origins
from .india import REGIONS

DEV = "cuda" if torch.cuda.is_available() else "cpu"
FT = dict(learning_rate=1e-5, num_steps=1000, batch_size=64)
TW = ("tw_X", "tw_Z", "tw_D", "tw_gb", "tw_phi", "tw_c")


def covariates(p, keys):
    c, m = np.zeros(len(p["g"])), p["meals"]
    np.add.at(c, m["idx"].to_numpy(), np.nan_to_num(np.maximum(m["carbs"] - m["fiber"], 0).to_numpy(float)))  # net carbohydrate at its step
    cov = {"carbs": c, "mets": p["mets"].astype(float), "hr": p["hr"].astype(float), **p.get("tw", {})}
    return {k: np.asarray(cov[k], float) for k in keys}


def median(pipe, p, keys, ctx_steps, name):
    """Median forecast from every rolling origin of p, using one day of history (and covariates, if keys)."""
    o, g, cov = origins(p), p["g"].astype(float), covariates(p, keys)
    sl = [slice(max(i + 1 - ctx_steps, 0), i + 1) for i in o]
    inp = [{"target": g[s], "past_covariates": {k: v[s] for k, v in cov.items()}} for s in sl] if keys else [g[s] for s in sl]
    q, _ = pipe.predict_quantiles(inp, prediction_length=max(HORIZONS) // p["dt"], quantile_levels=[0.5], batch_size=256)
    med = np.stack([np.asarray(x.squeeze(0)[:, 0].cpu()) for x in q])
    return pd.DataFrame({"id": p["id"], "i": o, **{f"{name}{h}": med[:, h // p["dt"] - 1] for h in HORIZONS}})


def bolt(p, pipe, ctx_steps):
    o, g = origins(p), pd.Series(p["g"]).ffill().to_numpy()  # Chronos-Bolt takes no gaps: causal forward fill
    ctx = np.stack([np.concatenate([np.full(max(ctx_steps - i - 1, 0), np.nan), g[max(i + 1 - ctx_steps, 0):i + 1]]) for i in o])
    med = np.concatenate([pipe.predict_quantiles(torch.tensor(ctx[a:a + 512], dtype=torch.float32), prediction_length=max(HORIZONS) // p["dt"],
                                                 quantile_levels=[0.5])[0][:, :, 0].cpu().numpy() for a in range(0, len(o), 512)])
    return pd.DataFrame({"id": p["id"], "i": o, **{f"chronos{h}": med[:, h // p["dt"] - 1] for h in HORIZONS}})


def finetune(base, train_, keys, ctx_steps, tag):
    """Chronos-2 fine-tuned on train_; every fourth patient held back to pick the checkpoint. Kept in
    data/processed/models/chronos2_<tag>/finetuned-ckpt (about 0.5 GB) and reloaded from there on the next run."""
    out = PROC / "models" / f"chronos2_{tag}"
    if (out / "finetuned-ckpt").exists():
        return Chronos2Pipeline.from_pretrained(str(out / "finetuned-ckpt"), device_map=DEV)
    cal = np.arange(len(train_)) % 4 == 3
    series = lambda Q: [{"target": p["g"].astype(float), "past_covariates": covariates(p, keys)} for p in Q]
    return base.fit(series([p for p, c in zip(train_, cal) if not c]), prediction_length=max(HORIZONS) // train_[0]["dt"],
                    validation_inputs=series([p for p, c in zip(train_, cal) if c]), context_length=ctx_steps, output_dir=out,
                    save_total_limit=1, **FT)


@cache
def pipe(name):
    return (BaseChronosPipeline if "bolt" in name else Chronos2Pipeline).from_pretrained(name, device_map=DEV)


def part(name, make):
    f = PROC / "chronos_parts" / f"{name}.pkl"
    if not f.exists():
        f.parent.mkdir(parents=True, exist_ok=True)
        make().to_pickle(f)
        print(name, "done", flush=True)
    return pd.read_pickle(f)


def main(only=()):
    P, sh = load("cgmacros"), load("shanghai")
    tw = pd.read_pickle(PROC / "twin_cov.pkl")
    with_tw = lambda Q, k: [dict(p, tw=tw[(k, p["id"])]) for p in Q]
    wear, day, c2 = ("carbs", "mets", "hr"), 288, "amazon/chronos-2"
    merge = lambda parts: parts[0].join([x.drop(columns=["id", "i"]) for x in parts[1:]])

    def fold(f, ti):
        train, test = [p for i, p in enumerate(P) if i not in set(ti)], [P[i] for i in ti]
        ft = finetune(pipe(c2), train, wear, day, f"fold{f}")
        a = pd.concat([median(ft, p, wear, day, "c2ft") for p in test], ignore_index=True)
        ft = finetune(pipe(c2), with_tw(train, f), wear + TW, day, f"tw_fold{f}")
        return a.join(pd.concat([median(ft, p, wear + TW, day, "c2tw") for p in with_tw(test, f)], ignore_index=True).drop(columns=["id", "i"]))

    def india(r):  # one simulated region: train on half its people, test on the other half, the split of twin.india.check
        Q = load(f"india_{r}")
        ft = finetune(pipe(c2), Q[::2], wear, day, f"india_{r}")
        return pd.concat([median(ft, p, wear, day, "c2ft") for p in Q[1::2]], ignore_index=True)

    def ext():
        D = [degrade_to(p) for p in P]
        ft = finetune(pipe(c2), D, ("carbs",), 96, "all15min")
        a = pd.concat([median(ft, p, ("carbs",), 96, "c2ft") for p in sh], ignore_index=True)
        ft = finetune(pipe(c2), with_tw(D, "ext"), ("carbs",) + TW, 96, "tw_all15min")
        return a.join(pd.concat([median(ft, p, ("carbs",) + TW, 96, "c2tw") for p in with_tw(sh, "ext")], ignore_index=True).drop(columns=["id", "i"]))

    jobs = {"zero": lambda: pd.concat([merge([bolt(p, pipe("amazon/chronos-bolt-small"), day), median(pipe(c2), p, (), day, "c2"),
                                              median(pipe(c2), p, wear, day, "c2cov")]) for p in P], ignore_index=True),
            "zero_ext": lambda: pd.concat([median(pipe(c2), p, ("carbs",), 96, "c2cov") for p in sh], ignore_index=True),
            **{f"fold{f}": (lambda f=f, ti=ti: fold(f, ti)) for f, ti in enumerate(folds(P, 5))}, "ext": ext,
            **{f"india_{r}": (lambda r=r: india(r)) for r in REGIONS}}
    if list(only) == ["merge"]:  # combine the parts already there (e.g. unzipped from Kaggle); trains nothing
        out = {k: pd.read_pickle(f) for k in jobs if (f := PROC / "chronos_parts" / f"{k}.pkl").exists()}
    else:
        out = {k: part(k, v) for k, v in jobs.items() if not only or k in only}
    if not only or list(only) == ["merge"]:
        if all(f"fold{f}" in out for f in range(5)):
            out["zero"].merge(pd.concat([out[f"fold{f}"] for f in range(5)], ignore_index=True), on=["id", "i"]).to_pickle(PROC / "chronos.pkl")
        if "ext" in out:
            out["zero_ext"].merge(out["ext"], on=["id", "i"]).to_pickle(PROC / "chronos_ext.pkl")
        if all(f"india_{r}" in out for r in REGIONS):
            pd.concat([out[f"india_{r}"] for r in REGIONS], ignore_index=True).to_pickle(PROC / "chronos_india.pkl")


if __name__ == "__main__":
    main(sys.argv[1:])
