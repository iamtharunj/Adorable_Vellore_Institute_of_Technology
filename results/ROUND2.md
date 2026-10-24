# Round 2 (19 Oct 2026): more models, three datasets

Trained on Kaggle T4 GPUs (`kaggle/run_chronos.ipynb`, `kaggle/run_tsfm.ipynb`), merged with `python -m twin.tsfm merge`.
Same patient folds, the same forecast moments and one day of history for every model; RMSE in mg/dL; brackets are 95%
intervals from resampling patients. The reported forecast (hybrid twin + fine-tuned Chronos-2, 17 Oct) was fixed
before these runs.

- **MOMENT** (MOMENT-1-large): encoder frozen, forecasting head trained per fold; glucose only (it takes no covariates).
- **TS2Vec**: self-supervised encoder trained per fold on glucose + carbohydrate, METs and heart rate; ridge to the horizon.
- **Twin-informed Chronos-2**: fine-tuned Chronos-2 with the twin's filtered states and parameters as extra inputs.
- **Chronos-2 re-trained**: the 17 Oct recipe run again on Kaggle (fp32), to check reproducibility. Its models are kept in `data/processed/models/`.
- Moirai (zero-shot) was also queued; see the note at the end.

## 60 minutes ahead

| Model | CGMacros (45 adults, held out) | ShanghaiT2DM (109 recordings, unseen) | Indian regions (180 simulated adults) |
|---|---|---|---|
| **Hybrid twin + Chronos-2 (reported)** | **23.62** | **23.97** | 15.51 |
| Hybrid twin + Chronos-2, re-trained | 23.67 | 23.95 | |
| Hybrid twin + twin-informed Chronos-2 | 23.75 | 24.11 | |
| Hybrid twin + MOMENT | 24.48 | 26.06 | 15.56 |
| Hybrid twin + TS2Vec | 24.51 | 25.61 | 17.02 |
| Chronos-2 fine-tuned, reported / re-trained | 24.36 / 24.40 | 24.18 / 23.66 | 17.63 |
| Twin-informed Chronos-2 | 24.67 | 24.34 | |
| Hybrid twin | 24.93 | 26.38 | **15.26** |
| LightGBM | 24.95 | 28.37 | 15.74 |
| TS2Vec | 25.91 | 26.75 | 20.97 |
| MOMENT | 26.80 | 29.18 | 18.56 |
| Physics twin alone | 26.61 | 25.55 | 20.36 |
| Persistence | 30.06 | 29.39 | 31.50 |

Differences at 60 minutes:

| Comparison | CGMacros | ShanghaiT2DM |
|---|---|---|
| Re-trained blend minus reported blend | +0.04 (-0.13 to 0.19) | -0.02 (-0.10 to 0.06) |
| Twin-informed blend minus reported blend | +0.12 (-0.02 to 0.27) | +0.15 (0.06 to 0.22) |
| MOMENT minus hybrid | +1.86 (0.85 to 2.89) | +2.80 (2.08 to 3.54) |
| TS2Vec minus hybrid | +0.98 (0.27 to 1.80) | +0.37 (-0.09 to 0.84) |
| Hybrid + TS2Vec minus reported blend | +0.89 (0.59 to 1.12) | +1.64 (1.43 to 1.82) |
| Hybrid + MOMENT minus reported blend | +0.85 (0.51 to 1.27) | +2.09 (1.80 to 2.43) |

Indian regions, minus hybrid twin at 60 min: hybrid + Chronos-2 +0.25 (0.16 to 0.34), LightGBM +0.48 (0.17 to 0.79),
Chronos-2 +2.37 (2.20 to 2.53), MOMENT +3.31 (3.01 to 3.68), TS2Vec +5.71 (5.34 to 6.19).

## 30 and 120 minutes

| Model | CGMacros 30 / 120 | ShanghaiT2DM 30 / 120 | Indian 30 / 120 |
|---|---|---|---|
| Hybrid twin + Chronos-2 (reported) | 16.51 / 29.38 | 14.60 / 33.11 | 7.82 / 18.99 |
| Hybrid twin + Chronos-2, re-trained | 16.60 / 29.35 | 14.23 / 34.17 | |
| Hybrid twin + twin-informed Chronos-2 | 16.65 / 29.38 | 14.55 / 33.65 | |
| Hybrid twin | 17.19 / 31.21 | 15.56 / 37.64 | 7.57 / 19.71 |
| LightGBM | 17.24 / 31.71 | 17.13 / 42.53 | 8.86 / 18.75 |
| TS2Vec | 18.54 / 31.55 | 16.42 / 37.64 | 12.79 / 23.23 |
| MOMENT | 20.59 / 30.99 | 20.55 / 37.86 | 13.78 / 20.00 |

## What this means

1. The reported forecast holds. None of the new models, alone or averaged with the twin, beats hybrid twin + Chronos-2
   on either real cohort.
2. It reproduces. Re-training Chronos-2 from scratch moves the 60-minute blend by 0.04 and -0.02 mg/dL (intervals
   cross zero). Individual Chronos-2 forecasts change by a median of 1 to 3 mg/dL between runs, and the 120-minute
   Shanghai blend by 1.1, so Chronos-2 differences under about 1 mg/dL are run-to-run noise.
3. Giving Chronos-2 the twin's states does not help (blend +0.12 at home, +0.15 abroad).
4. MOMENT is no better than persistence at 30 minutes and is out. It models each channel alone (no meals) and reads a
   fixed 512-step window, of which one day of history fills 56% at 5-minute and 19% at 15-minute sampling.
5. TS2Vec is weaker than the twin at home and ties it abroad; as a blend partner it is worse than Chronos-2 everywhere.
6. On the Indian simulations the hybrid twin alone is best at 30 and 60 minutes; LightGBM and the blends are better at
   120. The simulator shares the twin's physiology family, so this is a check of the method on Indian food, not a
   claim about real Indians.

Moirai: the Kaggle run had not returned when this file was written. If it lands, it is scored the same way
(`python -m twin.tsfm merge`, then `context/scripts/score_new.py`).
