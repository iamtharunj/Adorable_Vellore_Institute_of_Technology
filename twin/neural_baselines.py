"""Optional baselines: sequence neural networks (GRU, LSTM, a patch transformer) trained on exactly the folds
and forecasts the twin is scored on. Needs `pip install -e .[chronos]` (for torch); a GPU makes it minutes.
`python -m twin.neural_baselines` writes data/processed/neural.pkl (CGMacros, held-out folds) and
neural_ext.pkl (ShanghaiT2DM, trained on all of CGMacros degraded to 15-min CGM, no wearable), which
twin.evaluate picks up. Settings were fixed once, before any test result, and not tuned. Trained weights are
kept in data/processed/models/neural_<fold>.pt."""
import time

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from .data import PROC, folds, load
from .evaluate import degrade_to
from .hybrid import HORIZONS, STATIC, origins

KINDS, SEEDS = ("gru", "lstm", "transformer"), 5
DEV = "cuda" if torch.cuda.is_available() else "cpu"
shape = lambda dt: (240 // dt, 30 // dt, [h // dt for h in HORIZONS])  # 4 h of history, 30-min patches, horizons in steps


def channels(p):
    """Per-step inputs, all known at the time: glucose (gaps filled forward) and its mask, meal macros at the step
    they were logged, METs, heart rate against the person's running median, wearable mask, time of day."""
    g, L = p["g"].astype(float), shape(p["dt"])[0]
    gf = pd.Series(g).ffill().bfill().to_numpy()  # bfill only reaches the gap before the first reading, ahead of any origin
    meal, m = np.zeros((len(g), 4)), p["meals"]
    for j, n in enumerate(("carbs", "fat", "protein", "fiber")):
        v = np.maximum(m["carbs"] - m["fiber"], 0) if n == "carbs" else m[n]
        np.add.at(meal[:, j], m["idx"].to_numpy(), np.nan_to_num(v.to_numpy(float)))
    hr = pd.Series(p["hr"])
    hrd, w = (hr - hr.expanding(min_periods=1).median()).to_numpy(), np.isfinite(p["mets"])
    X = np.column_stack([(gf - 140) / 50, np.isfinite(g), meal / [50, 30, 30, 10], np.nan_to_num((p["mets"] - 1.2) / 2) * w,
                         np.nan_to_num(hrd / 20), w, np.sin(2 * np.pi * p["tod"] / 24), np.cos(2 * np.pi * p["tod"] / 24)])
    return np.vstack([np.zeros((L, X.shape[1])), X]).astype(np.float32), g


def windows(p, o):
    (X, g), (L, _, H) = channels(p), shape(p["dt"])
    y = np.stack([(g[np.minimum(o + k, len(g) - 1)] - g[o]) / 50 for k in H], 1)  # target: change from now, scaled
    return X[o[:, None] + np.arange(1, L + 1)[None, :]], y.astype(np.float32)  # padded row i + L is origin i


def dense(p):
    """Training windows: every reading after the 1-h warm-up that leaves room for the 3-h look-ahead."""
    dt = p["dt"]
    return np.array([i for i in range(60 // dt, len(p["g"]) - 180 // dt - 2) if np.isfinite(p["g"][i])])


def static(P, mu=None, sd=None):
    Z = np.array([[p["static"].get(s, np.nan) for s in STATIC] for p in P], float)
    mu, sd = (np.nanmean(Z, 0), np.nanstd(Z, 0) + 1e-6) if mu is None else (mu, sd)
    return np.nan_to_num((Z - mu) / sd).astype(np.float32), mu, sd


def build(P, origins_of, Z):
    xs, ys, zs = zip(*[(*windows(p, origins_of(p)), np.repeat(z[None], len(origins_of(p)), 0)) for p, z in zip(P, Z)])
    return [torch.tensor(np.concatenate(a)).to(DEV) for a in (xs, ys, zs)]


class Seq(nn.Module):
    def __init__(s, kind, c, ns, L, patch, d=64):
        super().__init__()
        s.kind, s.n = kind, L // patch
        if kind == "transformer":  # 30-min patches mixing all channels, learned positions
            s.patch, s.pos = nn.Linear(c * patch, d), nn.Parameter(torch.zeros(s.n, d))
            s.enc = nn.TransformerEncoder(nn.TransformerEncoderLayer(d, 4, 128, 0.2, batch_first=True), 2)
        else:
            s.enc = getattr(nn, kind.upper())(c, d, 2, batch_first=True, dropout=0.2)
        s.head = nn.Sequential(nn.Linear(d + ns, 64), nn.ReLU(), nn.Linear(64, len(HORIZONS)))  # + the static record

    def forward(s, x, z):
        h = s.enc(s.patch(x.reshape(x.shape[0], s.n, -1)) + s.pos)[:, -1] if s.kind == "transformer" else s.enc(x)[0][:, -1]
        return s.head(torch.cat([h, z], 1))


@torch.no_grad()
def predict(net, x, z, bs=4096):
    net.eval()
    return torch.cat([net(x[a:a + bs], z[a:a + bs]) for a in range(0, len(x), bs)]).cpu().numpy()


def train(kind, tr, va, seed, patch, epochs=40, patience=5, bs=512):
    """AdamW, early stopping on the held-back training patients (`va`)."""
    torch.manual_seed(seed)
    net = Seq(kind, tr[0].shape[2], tr[2].shape[1], tr[0].shape[1], patch).to(DEV)
    opt = torch.optim.AdamW(net.parameters(), 1e-3, weight_decay=1e-4)
    best, state, bad = np.inf, None, 0
    for _ in range(epochs):
        net.train()
        perm = torch.randperm(len(tr[0]), device=DEV)
        for a in range(0, len(perm), bs):
            b = perm[a:a + bs]
            ok = torch.isfinite(tr[1][b])
            opt.zero_grad()
            (((net(tr[0][b], tr[2][b]) - torch.nan_to_num(tr[1][b])) ** 2 * ok).sum() / ok.sum()).backward()
            nn.utils.clip_grad_norm_(net.parameters(), 1.0)
            opt.step()
        v = np.sqrt(np.nanmean((predict(net, va[0], va[2]) - va[1].cpu().numpy()) ** 2))
        if v < best - 1e-4:
            best, state, bad = v, {k: t.clone() for k, t in net.state_dict().items()}, 0
        elif (bad := bad + 1) >= patience:
            break
    net.load_state_dict(state)
    return net


def fit_predict(train_, test, tag):
    """Train each kind (SEEDS seeds, averaged) on train_, with every fourth patient held back for early stopping as
    in the twin's learned layer; forecast the test patients' rolling origins."""
    cal = np.arange(len(train_)) % 4 == 3
    fit, val = [p for p, c in zip(train_, cal) if not c], [p for p, c in zip(train_, cal) if c]
    Zf, mu, sd = static(fit)
    tr, va = build(fit, dense, Zf), build(val, dense, static(val, mu, sd)[0])
    te = build(test, origins, static(test, mu, sd)[0])
    rows = pd.concat([pd.DataFrame({"id": p["id"], "i": origins(p)}) for p in test], ignore_index=True)
    g0 = np.concatenate([p["g"][origins(p)] for p in test])
    saved = {"static_mu": mu, "static_sd": sd, "dt": train_[0]["dt"]}
    for kind in KINDS:
        t0 = time.time()
        nets = [train(kind, tr, va, seed, shape(train_[0]["dt"])[1]) for seed in range(SEEDS)]
        pr = np.mean([predict(net, te[0], te[2]) for net in nets], 0)
        saved[kind] = [{k: t.cpu() for k, t in net.state_dict().items()} for net in nets]
        for k, h in enumerate(HORIZONS):
            rows[f"{kind}{h}"] = g0 + 50 * pr[:, k]
        print(tag, kind, f"{time.time() - t0:.0f} s", flush=True)
    (PROC / "models").mkdir(parents=True, exist_ok=True)
    torch.save(saved, PROC / "models" / f"neural_{tag.replace(' ', '')}.pt")  # every seed's weights, a few MB
    return rows


def main():
    P = load("cgmacros")
    home = [fit_predict([p for i, p in enumerate(P) if i not in set(ti)], [P[i] for i in ti], f"fold {f}") for f, ti in enumerate(folds(P, 5))]
    pd.concat(home, ignore_index=True).to_pickle(PROC / "neural.pkl")
    fit_predict([degrade_to(p) for p in P], load("shanghai"), "ShanghaiT2DM").to_pickle(PROC / "neural_ext.pkl")


if __name__ == "__main__":
    main()
