# Progress log

Working title: **PrandialTwin**. Deadline 20 Oct 2026.

## 23 Oct 2026: script, notes and deck checked against the demo clips

| Piece | Where | State |
|---|---|---|
| Script rewritten in natural spoken language, content and order unchanged; no colons, semicolons or dashes in spoken lines; everyday analogies removed (the slides do not show them) | `docs/DEMO_SCRIPT.md` | About 24:33 with the four demo clips at their real lengths |
| Every spoken line has a code (`S09-L3-T`, `DB-L5-T`) so two audio recordings can be merged; table of all 65 files with start times; same codes in the speaker notes | `docs/DEMO_SCRIPT.md`, notes of `docs/PrandialTwin_Final.pptx` | Script and notes verified line for line identical |
| Demo lines fit the gaps between the cues of each silent clip | `docs/demo_videos/*.cues.txt` | Checked at 130 words a minute |
| Demo numbers checked on the settled screen of each clip (B: 74%, 122, +70, then 173 mg/dL and 21%; C: 65%, then 171 and 45% to 27%) | clips, script | An early check read a frame taken mid-update and briefly put 180 / 38% in the script; corrected, and the what-if panel and the suggestion line agree |
| Fixes: demo B "her" for INS-001 (a man); 23 slides in the header and README; slide titles 10 and 11 in the script; Lancet line worded as in the slide's headline; neutral pronouns on slide 6 and README; PDF re-exported | script, README, deck, PDF | Notes and slide 6 are the only parts of the deck that changed |

## 19 Oct 2026: checked against the brief

| Fix | Why |
|---|---|
| `.gitignore`: Kaggle kit, `out_*.zip`, regional wearables (one sample per region kept) | `git add .` would have committed 1.04 GB, including a 915 MB file GitHub rejects, and CGMacros-derived records inside the kit. Now 94 files, 15 MB |
| Dashboard lists the six regional cohorts from a fresh clone (generated on first open, about 45 s) | They were hidden until the 45-min `twin.india` run |
| Deck page numbers on slides 10 to 19; PDF re-exported | Stale after slides were inserted (slide 13 said 11) |
| More baselines for Kaggle: Moirai (zero-shot, covariates), MOMENT (head trained per fold), TS2Vec (encoder per fold + ridge), on CGMacros folds, ShanghaiT2DM and the six Indian regions (half train, half test, the split of `twin.india`); Chronos-2 gets the Indian parts too. `python -m twin.tsfm export` -> `kaggle/prandialtwin_kit.zip` (one dataset for both notebooks); `kaggle/run_tsfm.ipynb`, one model per account; `python -m twin.tsfm merge`, `python -m twin.chronos_baseline merge` | The question "why not MOMENT, Moirai, TS2Vec?". UniTS and Ti-MAE skipped (no maintained forecasting code); a PatchTST-style patch transformer (channels mixed, so meals count) is already reported |
| Kaggle results in: Chronos-2 on the six Indian regions (models in `data/processed/models/chronos2_india_*`), MOMENT on all 12 parts (`kaggle/tsfm_out/`). All points match the kit. MOMENT 60-min: 26.8 home (hybrid 24.9), 29.2 Shanghai (hybrid 26.4); no better than persistence at 30 min; out. Chronos-2 India 60-min 17.6 vs persistence 31.5. Same moments, all six regions, 60 min: hybrid twin 15.3, LightGBM 15.7, hybrid + Chronos-2 15.5, Chronos-2 17.6, MOMENT 18.6, physics twin 20.4 | Not yet in RESULTS |
| Business proposal deck, 23 slides, non-technical: problem, world and India burden, deaths, why T2D, who it serves, how it works, dashboard on a simulated Karnataka patient, evidence, Indian regions, market, business model, illustrative sizing, roadmap, risks, ask | `docs/PrandialTwin_Business.pptx` / `.pdf`; every statistic carries its source on the slide; speaker notes on every slide. To be combined with the technical results |
| Round 2 results in (all outputs verified: points, folds, model reload exact): MOMENT, TS2Vec, twin-informed Chronos-2, Chronos-2 re-trained. Reported forecast holds and reproduces (+0.04 / -0.02 mg/dL) | `results/ROUND2.md`; Moirai still out |
| Final presentation rebuilt (20 Oct) on the user's "Dark Gradient" template: 44 slides, 6 Wikimedia photos, 4 news cutouts with highlighted numbers, 4 part dividers; two-speaker narration (Tharun 48%, Gargi 52%) in every slide's notes | `docs/PrandialTwin_Final.pptx` / `.pdf`, `docs/IMAGE_CREDITS.md`; stranger-proof recording guide, demo click-steps, chapters and jury Q&A in `docs/DEMO_SCRIPT.md` (about 30 min) |
| Final presentation cut to 29 slides (20 Oct, v4): business part dropped; new architecture diagram (slide 12, also `docs/architecture.pdf` / `.png`, replacing the `make_architecture.py` render); slides on the maths of the twin, EnKF, hybrid cap, conformal bands, why the 50/50 average wins (RMSE of an average and error correlation per partner), why the neural nets and MOMENT lost; how the synthetic data is made; why CGMacros and ShanghaiT2DM can be trusted; four demos (synthetic record files, Karnataka patient what-if, CGMacros alert + Shanghai switch, tests); 27 numbered references on slides 28-29. Script rewritten non-redundant, 50/50 Tharun/Gargi, planned 20:24 (the brief asks for a minimum of 20 min). v3 (44 slides) kept in the session scratchpad | `docs/PrandialTwin_Final.pptx` / `.pdf`, `docs/DEMO_SCRIPT.md`, `docs/IMAGE_CREDITS.md`, `research/BIBLIOGRAPHY.md` (+ MOMENT, TS2Vec, ADAG) |
| Final presentation v5 (20 Oct): 23 slides. Dropped "why type 2 diabetes" (now one sentence in slide 5), "where we fit", both dividers and the roadmap (now one line on the closing slide); references on one slide, every listed reference checked as cited. Every formula keeps its symbols on screen with a plain-words caption (bathtub, 128 guesses like a GPS, two people guessing a cow's weight); architecture slide (9) builds in four clicks with a longer, simpler walk-through; demo B adds the learning chart and the evidence panel. Colleges added: Tharun J (leader, VIT Vellore), Gargi Sharma (ABES Institute of Technology, Ghaziabad). Script 49/51, planned 21:38 at 130 words a minute | `docs/PrandialTwin_Final.pptx` / `.pdf`, `docs/architecture.pdf` / `.png`, `docs/DEMO_SCRIPT.md`, README section 1. v4 (29 slides) kept in the session scratchpad |
| Fresh-clone copy: 15 tests pass; dashboard opens on synthetic and India West with no exception. Real cohorts need `python -I -m twin.data` first (checked in the working copy at the demo moment: 65% alert, what-if 45% to 27%, as the demo script says) | |

## 18 Oct 2026: regional Indian synthetic cohorts; models kept; Kaggle

| Piece | Where | State |
|---|---|---|
| Six simulated regional Indian cohorts (North, South, East, West, Central, Northeast), 60 adults x 14 days each | `twin/india.py`, `twin/synth.py`, `load("india_<region>")`, `data/synthetic/india_<region>/` | Generated and exported. Populations from ICMR-INDIAB-21, 120 plates from the Indian Nutrient Databank (68 recipes) and Shobana 2022, measured Indian GIs |
| Validation against ICMR-INDIAB-21 | `results/INDIA.md` section 1 | Every diet within 4.5 points of energy of its regional median; prevalence matched by construction; age and BMI within sampling noise after a per-region severity scale |
| The twin tested inside each region | `results/INDIA.md` sections 2-4 | Re-run on the current cohorts on 19 Oct (about 30 min); every forecast now saved as `data/processed/india_<r>_roll.pkl` so other models are scored at the same moments |
| Technical report on how the synthetic data is generated | Claude Doc: https://claude.ai/code/artifact/b9e098ed-45aa-49d0-bb39-f78b4e88289b | Written |
| Dashboard lists the six regional cohorts | `app.py` | Checked headless on a South India patient |
| Trained models are kept, never deleted | `data/processed/models/` | Neural nets (all folds), Chronos-2 fold 0-1 (laptop) and the two 15-min models (Kaggle) |
| Twin-informed Chronos-2 (twin states as covariates), on Kaggle | `twin/chronos_baseline.py`, `kaggle/` | ShanghaiT2DM done: no better than plain fine-tuned Chronos-2 at 60 min (+0.68, 0.54 to 0.84). Re-training plain Chronos-2 moved its 60-min RMSE by 0.5 and 120-min by 1.7: run-to-run noise. Home folds pending |
| Tests | `tests/test_twin.py` | 15 pass (new: regional prevalence, plates, GI) |

## 17 Oct 2026: alternatives tested, Chronos-2 added, advice added

Prompted by the question "why always LightGBM?". Every model family we had ruled out was tested on the same folds and the same external cohort.

| Piece | Where | State |
|---|---|---|
| GRU, LSTM, patch transformer baselines | `twin/neural_baselines.py` -> `data/processed/neural*.pkl` | Run (about 15 min on the laptop GPU) |
| Chronos-Bolt and Chronos-2 zero-shot, Chronos-2 fine-tuned per fold and abroad | `twin/chronos_baseline.py` -> `data/processed/chronos*.pkl` | Run (about 1.5 h) |
| Reported forecast = hybrid twin + fine-tuned Chronos-2, averaged | `evaluate.with_baselines` | In RESULTS sections 1 and 10 |
| Twin-planned advice (least-effort action under 30% risk) | `core.recommend`, dashboard "Suggested change", `evaluate.recommendations` | Tested on synthetic patients; RESULTS section 11 |
| Dashboard draws the reported twin + Chronos-2 forecast (diamonds) from the cached held-out forecasts; new `docs/dashboard.png`, deck slide 8 | `app.py` | Done; on the 15-min grid only (not at off-grid meal moments), no band yet |
| Tests | `tests/test_twin.py` | 14 pass (new: recommendation logic; dashboard suggestion) |
| Report, deck (20 slides), architecture, README, research files, demo script | | Updated |
| A-to-Z explainer with sources and video links | Claude Doc: https://claude.ai/code/artifact/ec7b4fd4-a5f6-4d83-aabe-e0ef65fe9e43 | Written |

Headline (60-min RMSE, home / ShanghaiT2DM): LightGBM 25.0 / 28.4; hybrid 24.9 / 26.4; GRU 25.1 / 43.2; LSTM 25.3 / 40.0; patch transformer 24.7 / 34.1; Chronos-2 zero-shot with covariates 26.9 / 26.6; Chronos-2 fine-tuned 24.4 / 24.2; **hybrid + Chronos-2 23.6 / 24.0**.
Chronos-2 fine-tuned minus hybrid abroad: -2.20 (-2.60 to -1.80). Advice on synthetic patients: spikes 34.7% -> 18.1% (oracle 11.0%).
Withdrawn: "fine-tuning needs more than 45 people". Kept: LightGBM as the residual learner (same learner as the baseline isolates the twin).

## 11 Oct 2026: build complete

| Piece | Where | State |
|---|---|---|
| Data download + loaders (CGMacros, ShanghaiT2DM) | `twin/data.py` | Run. 45 + 109 records; checksums in `data/raw/SOURCES.json` |
| Synthetic EHR + wearable generator, Synthea-style export | `twin/synth.py` | Run. 60 patients in `data/synthetic/` |
| Twin: physiology, ensemble Kalman filter, rollout, what-if, population fit, lab-to-prior map | `twin/core.py` | Run |
| Baseline + hybrid layer, conformal bands, alert replay | `twin/hybrid.py` | Run |
| Chronos-Bolt zero-shot baseline (GPU) | `twin/chronos_baseline.py` | Run |
| Evaluation: 5-fold CV, ablations, robustness, external cohort, synthetic verification | `twin/evaluate.py` | Run end to end (about 25 min) |
| Figures and tables | `twin/report.py`, `results/` | Generated; all seven figures inspected |
| Tests | `tests/test_twin.py` | 13 pass, including a headless dashboard test |
| Dashboard | `app.py` | Launched, screenshotted, driven headless on all three cohorts |
| Architecture diagram | `docs/architecture.pdf`, `.png` | Done |
| Presentation | `docs/PrandialTwin.pptx`, `.pdf` | 17 slides with speaker notes; validated; every slide inspected |
| Video script | `docs/DEMO_SCRIPT.md` | Done |
| README, licence | `README.md`, `LICENSE` | Done, except team fields |
| Research | `research/` | Decision report, literature review, methods comparison, dataset catalogue, bibliography; 20 of 25 papers downloaded (5 need a browser, listed in `papers/MANIFEST.md`) |

## Left for the team

1. Fill the `TODO` fields: team, college, video link, repository link (README sections 1 and 11; slides 1 and 20).
2. Record the 20+ minute video with `docs/DEMO_SCRIPT.md`.
3. Create the public repository named `TeamName_CollegeName`, commit, and test the README commands on a fresh clone.
4. Confirm that CGMacros' non-commercial licence (CC BY-NC-SA 4.0) is acceptable for a prize competition.
5. Optional: BIG IDEAs as a third cohort; rename the project.

## Timeline of decisions

| When | What |
|---|---|
| 1 Oct | Research strategy report: hybrid glucose twin recommended |
| 10 Oct | Brief re-read; six new rival entries found, one with physiology + conformal + what-if. Differentiation moved to evidence: real data first, external cohort, per-patient coverage, tested what-ifs |
| 10 Oct | PhysioNet served the CGMacros archive at 18 KB/s; switched to HTTP range requests for the CSVs only (6.6 MB of 657 MB) |
| 10 Oct | Gate G1 passed: 489 events in 1,550 eligible meals; 2,015 + 324 matched meal pairs |
| 10 Oct | Filter noise levels set on nine development patients, then frozen |
| 10 Oct | First full run. Found: hybrid ties LightGBM at home, wins on ShanghaiT2DM; ensemble-spread bands uninformative; "rise above basal" index invalid |
| 10 Oct | Changes: net carbohydrate, time-of-day term, conformalized quantile bands, modality-matched external baseline. Tried and reverted: drift-to-basal transfer |
| 10 Oct | Final run. Numbers in `results/RESULTS.md` |
| 11 Oct | Figures and dashboard inspected and fixed; README, decision report, deck, demo script written |
| 17 Oct | Tested GRU, LSTM, patch transformer, Chronos-2 zero-shot and fine-tuned; Chronos-2 averaged into the forecast; twin-planned advice added and tested; every document updated |

## Headline results (held-out patients; 95% intervals by resampling patients)

- CGMacros, 60-min RMSE: hybrid 24.9, LightGBM 25.0, physics twin 26.6, Chronos-Bolt 28.7, persistence 30.1 mg/dL. Hybrid minus LightGBM -0.02 (-0.71 to 0.57): a tie.
- ShanghaiT2DM (unseen), modality-matched baseline: hybrid 26.4, LightGBM 28.4, physics twin 25.5, persistence 29.4. Hybrid minus LightGBM -1.99 (-2.64 to -1.39).
- Alerts at about one false alert per patient-day: hybrid warns of 61% of 693 events (median lead 30 min); LightGBM 52%.
- 90% bands, worst patient: 89% adapted per patient vs 78% calibrated once. ShanghaiT2DM: 88% vs 64%.
- Not significant: lab prior in the first 24 h (-0.46, -1.01 to 0.10); updating vs frozen twin from day 4 (-0.87, -2.14 to 0.26).
- What-if direction on matched real pairs: 66% carbohydrate, 61% activity (LightGBM 68%, 63%). Active hour: observed -10.7, twin -9.1 mg/dL.

## Commands

```
python -m venv .venv && .venv/Scripts/python -m pip install -e ".[dev,chronos]"
python -I -m twin.data        # download + build records (about 2 min)
python -I -m twin.synth       # synthetic cohort as CSV
python -I -m twin.neural_baselines   # optional, GPU: GRU, LSTM, transformer
python -I -m twin.chronos_baseline   # optional, GPU: Chronos-Bolt and Chronos-2
python -I -m twin.evaluate    # everything; add --reuse to rebuild the report from cache
python -I -m pytest -q
streamlit run app.py
```
