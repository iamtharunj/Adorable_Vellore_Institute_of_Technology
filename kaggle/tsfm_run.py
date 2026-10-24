"""PrandialTwin: three more forecasting baselines, run on Kaggle (kaggle/run_tsfm.ipynb). Standalone, so each model can
bring its own dependencies. Reads series.npz (from `python -m twin.tsfm export`) and writes out/<model>_<part>.csv: the
point forecast at 30, 60 and 120 min from every rolling origin, keyed by (id, i) like twin.chronos_baseline, with
the same patient folds, one day of context and the same covariates.
  moirai  Moirai 1.1-R large, zero-shot, CGM + covariates as past inputs; patch size chosen by Moirai ("auto")
  moment  MOMENT-1-large, encoder frozen, linear forecasting head trained per fold (CGM only: it models each channel alone)
  ts2vec  TS2Vec encoder trained per fold on CGM + covariates, ridge from its causal embedding to future glucose
Parts: fold0..fold4 (CGMacros: train on the other four folds, test on this one), ext (train on all of CGMacros at 15 min,
test on ShanghaiT2DM), india_<region> (simulated: train on half of the region, test on the other half). Settings are
fixed in advance; each fold's every fourth training patient is its calibration
patient, as for Chronos-2. TSFM_SMOKE=1 runs a tiny version on the CPU to check the code.
Usage: python tsfm_run.py <model> <part> [<part> ...]"""
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

HERE = Path(__file__).resolve().parent
SMOKE = os.environ.get("TSFM_SMOKE") == "1"
OUT = HERE / ("out_smoke" if SMOKE else "out")
SIZE = "small" if SMOKE else "large"
DEV = "cuda" if torch.cuda.is_available() else "cpu"
HORIZONS = (30, 60, 120)
KEYS = {"home": ("carbs", "mets", "hr"), "ext": ("carbs",)}  # Shanghai has no wearable: carbohydrate is the shared covariate


def cohort(z, c):
    n, m = np.cumsum(np.r_[0, z[f"{c}_len"]]), np.cumsum(np.r_[0, z[f"{c}_olen"]])
    P = [{"id": str(pid), "dt": int(z[f"{c}_dt"]), "o": z[f"{c}_o"][m[k]:m[k + 1]],
          **{v: z[f"{c}_{v}"][n[k]:n[k + 1]].astype(np.float32) for v in ("g", "carbs", "mets", "hr")}} for k, pid in enumerate(z[f"{c}_ids"])]
    return [dict(p, o=p["o"][::40]) for p in P[:4]] if SMOKE else P


def split(z, part):
    """(train, test, covariates), exactly as twin.chronos_baseline splits them."""
    if part == "ext":
        return cohort(z, "home15"), cohort(z, "ext"), KEYS["ext"]
    if part.startswith("india_"):  # one simulated region: half its people to train, the other half to test, as twin.india
        P = cohort(z, part)
        return P[::2], P[1::2], KEYS["home"]
    P, f, k = cohort(z, "home"), z["home_fold"], int(part[4:])
    if SMOKE:
        return P[:3], P[3:], KEYS["home"]
    return [p for p, x in zip(P, f) if x != k], [p for p, x in zip(P, f) if x == k], KEYS["home"]


def windows(p, keys, ctx):
    """The last ctx steps before every origin (origin included): (n, ctx, 1 + covariates), CGM first, NaN where
    missing; and the mask of steps before the record starts."""
    X = np.stack([p["g"]] + [p[k] for k in keys], 1)
    X = np.concatenate([np.full((ctx, X.shape[1]), np.nan, np.float32), X])
    return np.stack([X[i + 1:i + 1 + ctx] for i in p["o"]]), np.arange(ctx)[None] < (ctx - 1 - p["o"])[:, None]


def future(p, H):
    g = np.r_[p["g"], np.full(H, np.nan, np.float32)]
    return np.stack([g[i + 1:i + 1 + H] for i in p["o"]])


def rmse(e):
    return float(np.sqrt(np.nanmean(e ** 2)))


def moirai(train, test, keys, ctx, H, dt, part):
    """Zero-shot (train is unused). Patch size "auto": Moirai picks it for each window by its own loss on the window's
    last H steps, so each window carries ctx + H steps and the forecast reads the last ctx."""
    from uni2ts.model.moirai import MoiraiForecast, MoiraiModule
    f = MoiraiForecast(module=MoiraiModule.from_pretrained(f"Salesforce/moirai-1.1-R-{SIZE}"), prediction_length=H, context_length=ctx,
                       patch_size="auto", num_samples=100, target_dim=1, feat_dynamic_real_dim=0, past_feat_dynamic_real_dim=len(keys)).to(DEV).eval()
    out = []
    for p in test:
        W, pad = windows(p, keys, ctx + H)
        for a in range(0, len(W), 128):
            w = W[a:a + 128]
            x, obs = torch.tensor(np.nan_to_num(w), device=DEV), torch.tensor(np.isfinite(w), device=DEV)
            with torch.no_grad():
                s = f(past_target=x[..., :1], past_observed_target=obs[..., :1], past_is_pad=torch.tensor(pad[a:a + 128], device=DEV),
                      past_feat_dynamic_real=x[..., 1:], past_observed_feat_dynamic_real=obs[..., 1:])
            out.append(s.reshape(len(w), -1, H).median(1).values.cpu().numpy())
    return np.concatenate(out)


def moment(train, test, keys, ctx, H, dt, part):
    from momentfm import MOMENTPipeline
    m = MOMENTPipeline.from_pretrained(f"AutonLab/MOMENT-1-{SIZE}", model_kwargs={
        "task_name": "forecasting", "forecast_horizon": H, "head_dropout": 0.1, "weight_decay": 0,
        "freeze_encoder": True, "freeze_embedder": True, "freeze_head": False})
    m.init()
    m.to(DEV)
    T = lambda a: torch.tensor(a, device=DEV)

    def inputs(P):  # MOMENT reads 512 steps: one day of CGM at the right, gaps filled forward (causal), mask = real steps
        W = pd.DataFrame(np.concatenate([windows(p, (), ctx)[0][..., 0] for p in P])).ffill(axis=1).to_numpy(np.float32)
        x, mask = np.zeros((len(W), 512), np.float32), np.zeros((len(W), 512), np.float32)
        x[:, -ctx:], mask[:, -ctx:] = np.nan_to_num(W), np.isfinite(W)
        return x, mask

    def predict(x, mask):
        m.eval()
        with torch.no_grad():
            return np.concatenate([m(x_enc=T(x[a:a + 256])[:, None], input_mask=T(mask[a:a + 256])).forecast[:, 0].cpu().numpy()
                                   for a in range(0, len(x), 256)])

    cal = np.arange(len(train)) % 4 == 3
    fit, val = [p for p, c in zip(train, cal) if not c], [p for p, c in zip(train, cal) if c] or train[-1:]
    (xf, mf), yf = inputs(fit), np.concatenate([future(p, H) for p in fit])
    (xv, mv), yv = inputs(val), np.concatenate([future(p, H) for p in val])
    opt, rng, best = torch.optim.Adam(m.head.parameters(), lr=1e-4), np.random.default_rng(0), (np.inf, None)
    for epoch in range(1 if SMOKE else 3):
        m.train()
        for b in np.array_split(rng.permutation(len(xf)), max(len(xf) // 64, 1)):
            y = T(yf[b])
            loss = ((m(x_enc=T(xf[b])[:, None], input_mask=T(mf[b])).forecast[:, 0] - torch.nan_to_num(y))[torch.isfinite(y)] ** 2).mean()
            opt.zero_grad()
            loss.backward()
            opt.step()
        e = rmse(predict(xv, mv) - yv)
        print("epoch", epoch, "calibration RMSE (all horizons)", round(e, 2), flush=True)
        if e < best[0]:
            best = (e, {k: v.clone() for k, v in m.head.state_dict().items()})
    m.head.load_state_dict(best[1])
    torch.save(best[1], OUT / f"moment_{part}_head.pt")  # the trained part; the encoder is the public checkpoint
    return predict(*inputs(test))


def ts2vec(train, test, keys, ctx, H, dt, part):
    sys.path.insert(0, str(HERE / "ts2vec"))
    from sklearn.linear_model import Ridge
    from ts2vec import TS2Vec
    cal = np.arange(len(train)) % 4 == 3
    fit, val = [p for p, c in zip(train, cal) if not c], [p for p, c in zip(train, cal) if c] or train[-1:]
    A = lambda p: np.stack([p["g"]] + [p[k] for k in keys], 1)
    mu, sd = np.nanmean(np.concatenate([A(p) for p in fit]), 0), np.nanstd(np.concatenate([A(p) for p in fit]), 0) + 1e-6

    def arr(P):  # (patients, longest record, channels), standardised; missing covariates read as their mean, CGM gaps stay missing
        out = np.full((len(P), max(len(p["g"]) for p in P), 1 + len(keys)), np.nan, np.float32)
        for k, p in enumerate(P):
            x = (A(p) - mu) / sd
            x[:, 1:] = np.nan_to_num(x[:, 1:])
            out[k, :len(x)] = x
        return out

    model = TS2Vec(input_dims=1 + len(keys), device=DEV, output_dims=320, max_train_length=3000)  # as in the authors' train.py
    model.fit(arr(fit), n_iters=5 if SMOKE else None, verbose=False)
    model.save(str(OUT / f"ts2vec_{part}.pt"))

    def feats(P):  # the embedding at the origin from a causal window of one day, plus current glucose
        R = model.encode(arr(P), causal=True, sliding_length=1, sliding_padding=ctx, batch_size=256)
        return np.concatenate([np.c_[R[k, p["o"]], (p["g"][p["o"]] - mu[0]) / sd[0]] for k, p in enumerate(P)])

    Xf, Xv, Xt = feats(fit), feats(val), feats(test)
    Yf, Yv = (np.concatenate([future(p, H) for p in Q]) for Q in (fit, val))
    med = np.full((len(Xt), H), np.nan, np.float32)
    for h in HORIZONS:
        j = h // dt - 1
        f, v = np.isfinite(Yf[:, j]), np.isfinite(Yv[:, j])
        err = {a: rmse(Ridge(alpha=a).fit(Xf[f], Yf[f, j]).predict(Xv[v]) - Yv[v, j]) for a in (0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000)}
        med[:, j] = Ridge(alpha=min(err, key=err.get)).fit(Xf[f], Yf[f, j]).predict(Xt)
    return med


def main(model, parts):
    z = np.load(HERE / "series.npz")
    OUT.mkdir(exist_ok=True)
    for part in parts:
        f = OUT / f"{model}_{part}.csv"
        if f.exists():
            print(part, "already done", flush=True)
            continue
        train, test, keys = split(z, part)
        dt, t = test[0]["dt"], time.time()
        torch.manual_seed(0)
        med = {"moirai": moirai, "moment": moment, "ts2vec": ts2vec}[model](train, test, keys, 1440 // dt, 120 // dt, dt, part)
        o = np.concatenate([p["o"] for p in test])
        d = pd.DataFrame({"id": np.concatenate([[p["id"]] * len(p["o"]) for p in test]), "i": o, **{f"{model}{h}": med[:, h // dt - 1] for h in HORIZONS}})
        y = np.concatenate([future(p, 120 // dt) for p in test])
        print(part, f"{time.time() - t:.0f} s | test RMSE", {h: round(rmse(d[f"{model}{h}"].to_numpy() - y[:, h // dt - 1]), 2) for h in HORIZONS}, flush=True)
        d.to_csv(f, index=False)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
