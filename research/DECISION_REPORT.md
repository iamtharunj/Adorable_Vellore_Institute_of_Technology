# Decision report

Written 10 to 11 October 2026. Builds on the research strategy report of 1 October.
Evidence behind each statement: [LITERATURE_REVIEW.md](LITERATURE_REVIEW.md), [DATASETS.md](DATASETS.md),
[METHODS_COMPARISON.md](METHODS_COMPARISON.md), [BIBLIOGRAPHY.md](BIBLIOGRAPHY.md). Results: [../results/RESULTS.md](../results/RESULTS.md).

## 1. Decision

**Build a physiological digital twin that forecasts sustained post-meal hyperglycaemia (CGM above 180 mg/dL for
15+ minutes) in type 2 diabetes and prediabetes, developed on real linked data (CGMacros) and tested unchanged
on a second real cohort (ShanghaiT2DM).**

It is the only candidate where the static record and the wearable stream of the *same real person* can be
downloaded today, the event has a guideline threshold, and a what-if can be checked against what actually happened.
The topic is crowded in this challenge; the evidence standard is not.

## 2. What the brief requires

| Requirement (from `Digi_Twin_Problem.txt`) | How it is met |
|---|---|
| One chronic or lifestyle condition prevalent in India | Type 2 diabetes and prediabetes |
| Fuse static/historical EHR data with dynamic wearable/IoT time series | Labs set the prior on the twin's parameters; CGM, meals and activity update it. Same person in both streams |
| A working model that predicts an adverse event (example given: a glucose spike 2 hours ahead) | Probability of glucose above 180 mg/dL for 15+ min within 2 h (rolling) and within 3 h of a meal |
| Conceptual doctor-facing dashboard | `app.py`: record, twin state, forecast, drivers, what-if |
| Anonymised, open-source or synthetic data only | CGMacros (PhysioNet, de-identified), ShanghaiT2DM (figshare, de-identified), own synthetic cohort |
| Public GitHub with README fields, architecture PDF, presentation, 20+ minute video, licence | README sections 1 to 11; video to be recorded by the team |

The brief publishes no scoring rubric. *Our reading:* a "technical and expert panel" will weigh whether the
fusion is real, whether the event is clinically meaningful, whether the model is a twin or a classifier, and
whether claims are backed.

## 3. Candidate problems

Scores are 1 (weak) to 5 (strong). The total is the weighted sum scaled to 100. This is a structured
judgement, not a measurement; the reasons are in the last column.

| # | Candidate | India impact (15) | Feasibility (15) | Data today (20) | Horizon fit (10) | Novelty (10) | Validation (15) | Deployment (5) | Differentiation (10) | **Total** | Deciding facts |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A | **Post-meal hyperglycaemia in T2D/prediabetes, 2 to 3 h** | 5 | 4 | 5 | 5 | 2 | 5 | 4 | 3 | **86** | Open, linked, same-person data; known mechanism; natural experiments in the data. At least six rival entries on the topic |
| B | Nocturnal hypoglycaemia on insulin or sulfonylurea, 30 to 60 min | 4 | 3 | 3 | 4 | 3 | 3 | 3 | 4 | 67 | Open data is mostly type 1; needs an insulin model; events are rare in T2D sets |
| E | Next-day glycaemic deterioration from sleep and activity | 4 | 3 | 2 | 3 | 4 | 3 | 4 | 4 | 64 | Best data (AI-READI) is access-controlled, about 2 weeks; threshold is arbitrary |
| C | Hypertensive episode in 24 to 48 h | 5 | 2 | 1 | 3 | 4 | 1 | 3 | 4 | 53 | 35.5% prevalence, but no open set aligns ambulatory BP, wearable and EHR. Would be synthetic end to end |
| G | Sepsis or inpatient deterioration | 3 | 3 | 3 | 4 | 1 | 3 | 2 | 1 | 53 | Hospital monitors, not wearables; credentialed data; a deployed model failed externally |
| D | Cardiovascular anomaly (for example AF) from a week of sleep and heart rate | 4 | 2 | 2 | 2 | 3 | 2 | 3 | 3 | 51 | Open ECG sets have no EHR; outcome labels are years away or absent |
| F | Asthma/COPD exacerbation from wearable and air quality | 4 | 2 | 1 | 3 | 4 | 1 | 3 | 4 | 50 | No open linked dataset |

Sensitivity: A stays first unless novelty and differentiation together carry more than half the weight. We did
not choose A because it is fashionable or easy. We chose it because it is the only one whose claims can be tested
on real people within the deadline, and then spent the effort on the tests.

## 4. The selected problem

| | |
|---|---|
| Unmet need | Indian T2D on CGM spends most time above range after carbohydrate-heavy meals. A professional CGM report shows this afterwards; nobody tells doctor or patient before the meal |
| Target patient | Adult with type 2 diabetes or prediabetes, not on a pump, wearing a 10 to 14 day CGM, logging meals; smartwatch optional |
| Prediction target | CGM above 180 mg/dL for at least 15 consecutive minutes, starting from at or below 180. Rolling: within 2 h, every 15 min. At a logged meal: within 3 h |
| Intervention window | Median alert lead 30 min at about one false alert per patient-day; at meal time the whole meal is still ahead. Enough for a smaller portion or a walk, both of which the twin simulates |
| Why existing solutions fall short | Population models have no patient state and no what-if. Published hybrid twins are mostly type 1, fitted offline, without calibrated uncertainty. Rival entries validate on their own simulator or fit the twin to part of the test recording, and do not test what-ifs |
| Measurable innovation | (1) cold-start value of labs as priors; (2) learning curve against a frozen twin; (3) coverage per patient; (4) what-if agreement with natural experiments; (5) transfer to an unseen cohort. Each has a number in section 7 |

## 5. Architecture

Labs become a prior over five physiological parameters. An ensemble Kalman filter (128 members) corrects
four states and those parameters at every CGM reading. A three-hour rollout of the ensemble gives the physics
forecast; a capped LightGBM model corrects it; since 17 October the reported forecast averages that hybrid with a
fine-tuned Chronos-2. Conformalized quantile bands are re-calibrated per patient online. A what-if edits the future of
the record and re-runs from the same state, and at a meal the twin suggests the least-effort change that keeps its risk
under 30%.
Diagram: [../docs/architecture.pdf](../docs/architecture.pdf). Alternatives considered: [METHODS_COMPARISON.md](METHODS_COMPARISON.md).

Left out on purpose: LLM or agent layers (no measured benefit), microbiome features, food-image recognition, a
separate survival head, federated learning. Transformers and recurrent networks trained on 45 people were first left
out untested; on 17 October we tested them (section 7b): they tie at home and fail abroad, while a fine-tuned
foundation model (Chronos-2) does not fail and is now part of the forecast.

## 6. Novelty

Established and used as tools: minimal-model physiology, ensemble Kalman filter, gradient boosting, conformal
prediction, HOMA. New here, by combination and by test: a T2D/prediabetes meal twin that is never fitted to its
patient; labs mapped to parameter priors and tested for cold-start value; what-ifs scored against natural
experiments with the same test applied to the baseline; coverage reported per patient on two cohorts; a
cross-country transfer test with a modality-matched baseline; a richer-than-the-twin simulator for
counterfactual verification. We found no single paper or entry that does all of these; that is a statement
about our search, not proof of absence.

## 7. Pre-stated claims and what happened

The 1 October plan named five results that would show twin value over ordinary ML. Outcome of each:

| Claim | Result | Verdict |
|---|---|---|
| Better cold start from labs | First 24 h, lab prior minus population prior: -0.46 mg/dL (-1.01 to 0.10). On ShanghaiT2DM the lab prior was slightly worse (25.5 vs 25.2) | **Not shown** |
| A falling learning curve | Updating minus frozen from day 4: -0.87 (-2.14 to 0.26); worse in the first three days. Personalised minus generic: -5.6 (-9.4 to -2.1) | **Partly**: personalisation yes, continued learning not significant |
| Per-patient coverage near nominal | All 45 patients within 5 points of 90% with online adaptation; worst 89% (78% without). ShanghaiT2DM: worst 88% (64% without) | **Shown** |
| What-ifs match natural experiments better than the baseline | Direction right 66% (carbohydrate), 61% (activity), both above chance; LightGBM 68% and 63%. Mean activity effect: observed -10.7, twin -9.1 mg/dL | **Partly**: consistent, not better than the baseline |
| Smaller drop on an external cohort | ShanghaiT2DM 60-min RMSE: hybrid 26.4 vs LightGBM 28.4, difference -2.0 (-2.6 to -1.4); alert AUPRC 0.450 vs 0.356 | **Shown** |
| (Steady-state accuracy within 5% of the best baseline) | CGMacros 60-min RMSE: hybrid 24.9 vs LightGBM 25.0 | **Met (tie)** |

### 7b. Added 17 October: the alternatives we had ruled out, and reinforcement learning

| Question | Result | Verdict |
|---|---|---|
| Do GRU, LSTM or a transformer beat LightGBM? | Home 60-min RMSE 25.1, 25.3, 24.7 vs 25.0: ties. Abroad 43.2, 40.0, 34.1 vs 28.4: much worse (mean error +13 to +19, largest on insulin) | **No** |
| Does a foundation model beat the twin? | Zero-shot Chronos-2 loses at home (26.9); fine-tuned it ties at home (24.4) and beats the hybrid abroad: minus hybrid -2.2 (-2.6 to -1.8) | **Yes, abroad.** Our written claim that fine-tuning needs more than 45 people was wrong |
| Is twin + Chronos-2 the best forecast? | 23.6 at home (minus LightGBM -1.3 (-2.2 to -0.7)), 24.0 abroad (minus hybrid -2.4 (-2.7 to -2.1)); abroad the twin is a better partner than LightGBM | **Yes**, at 30 and 60 min in both cohorts |
| Does twin-planned advice prevent spikes? | Synthetic patients, true outcomes: 34.7% of meals spike with no action, 28.5% with a carbohydrate rule, 18.1% when the twin chooses, 11.0% for an oracle | **Shown on synthetic patients only** (an upper bound) |
| Is Q-learning the right tool? | The meal choice is a one-step contextual bandit; exhaustive search over the twin's what-ifs gives its exact solution | **No**; planning with the twin instead |

Gates: G1 (enough events and pairs) passed with 489 events in 1,550 eligible meals and 2,015 + 324 matched pairs.
G3 (physics twin within 10% of LightGBM at 60 min) passed at +6.6%.

How to present this: lead with transfer, per-patient uncertainty and alert yield. Say plainly that the home-cohort
accuracy is a tie, and that the lab prior and continued learning did not reach significance with 45 people.
A stated negative is stronger in front of an expert jury than an untested claim.

## 8. Risks

| Risk | Status | Response |
|---|---|---|
| A rival (GlucoTwin India) already has physiology + conformal + what-if | Real | Compete on evidence: real-data primary results, external cohort, per-patient coverage, tested what-ifs. Do not compete on FHIR/ABDM polish |
| "45 people, everything is noise" | Real | Intervals by resampling patients everywhere; two cohorts; negatives reported |
| "Tie with LightGBM, so why a twin?" | Expected question | External transfer, alert yield, per-patient coverage, state and what-if. The table in section 7 is the answer |
| "A foundation model beats your twin abroad" | Found (17 Oct) | Said first, not discovered by a judge. Chronos-2 is averaged into the forecast; the twin keeps state, bands, what-ifs and advice, and is the better blend partner abroad |
| Advice evaluated only in simulation | Inherent | Labelled as an upper bound everywhere; lifestyle actions only |
| Lab-to-prior map does not transfer | Found | Reported. Population prior is the safer default outside the training population |
| Natural experiments are confounded | Inherent | Matched within person on meal kind, carbohydrate and pre-meal glucose; called a consistency check; same test on the baseline |
| Parameters not separately identifiable | Found | Product parameter for insulin response; dashboard shows identifiable summaries; failed index documented |
| CGMacros is non-commercial (CC BY-NC-SA) and the challenge has cash prizes | Open | Student research use is the intended case, but the team should confirm with the organisers or the dataset authors |
| Not validated in Indians | Inherent | Stated on the dashboard, in the README and on a slide. India argument is problem fit only |
| Demo cherry-picking | Guarded | Demo patient and meal chosen by a written rule; the example shown under-predicts the peak and we show it anyway |

## 9. Plan to the deadline (20 October 2026)

| When | What | Owner |
|---|---|---|
| Done | Data, twin, baselines, evaluation, report, tests, dashboard, research files, architecture, slides, demo script | built |
| 11 to 12 Oct | Team reads `results/RESULTS.md` and section 7; fills team details in the README; decides the project name | all |
| 12 to 14 Oct | Rehearse the demo with `docs/DEMO_SCRIPT.md`; one outsider reads the dashboard for 30 seconds and says what they understood | all |
| 14 to 16 Oct | Record the 20+ minute video; upload unlisted; add the link | presenter |
| Optional, 13 to 15 Oct | Add BIG IDEAs as a third cohort (one loader in `twin/data.py`); confirm the CGMacros licence question | data lead |
| 17 Oct | Create the public repository named `TeamName_CollegeName`; fresh-clone test of the README commands | repo lead |
| 18 to 19 Oct | Buffer; submit leader name, phone, email and repository link on Unstop | leader |

## 10. Disclosures

- Filter noise levels were chosen on nine CGMacros patients (IDs in `twin/evaluate.py`). Headline results are also given without them: hybrid 25.4 vs LightGBM 25.4 mg/dL at 60 min.
- The model structure was revised twice after cross-validated results on CGMacros (net carbohydrate; a time-of-day term). ShanghaiT2DM was run at both versions and never used to choose anything.
- Rival results quoted here are self-reported and were not reproduced.
- 17 October baselines: network settings fixed once and not tuned; five-seed averaging chosen after a one-seed run had been seen; Chronos-2 fine-tuned once per fold with settings fixed in advance; its pretraining corpus may include public CGM data.
- Winner claims for comparable competitions were verified where a primary source could be retrieved (BGLP 2020, PhysioNet 2019) and marked unavailable where not (BrisT1D).
