# Methodology comparison

How the design was chosen, what it was compared against, and what was tried and dropped.

## 1. Three candidate architectures

| Stage | A. Population ML with static columns | **B. Hybrid physiological twin with data assimilation (built)** | C. Latent neural state-space twin |
|---|---|---|---|
| Static record | Labs as feature columns | Labs become priors on physiological parameters | Embedding conditions the dynamics |
| Patient representation | Feature vector | Posterior over 5 named parameters + 4 states | Latent vector |
| Stream | Windowed features | Each CGM reading assimilated; meals and activity drive the model | Neural CDE / Mamba encoder |
| State estimation | Implicit | Ensemble Kalman filter, states and parameters jointly | Amortised variational filter |
| Forecast | Regressor / classifier per horizon | Ensemble rollout + capped LightGBM residual, averaged with fine-tuned Chronos-2 (since 17 Oct) | Decoder rollout |
| Uncertainty | Quantiles, then conformal | Ensemble, conformalized quantiles, per-patient adaptive conformal | Variational posterior |
| What-if | Perturbs correlated features | Re-run the same state with an edited input | Unconstrained |
| Data need | Moderate | Low | High (45 people is far too few to train one from scratch) |
| Twin by the NASEM definition | No | Yes | Partly |
| Role here | **Baseline** | **Chosen** | Not built |

## 2. Component choices

| Component | Chosen | Alternatives weighed | Why |
|---|---|---|---|
| Physiology | 4 states (glucose, insulin action, insulin drive, disturbance), 5 patient parameters, closed-form two-compartment gut | UVA/Padova (about 30 parameters), oral minimal model with measured insulin | CGMacros has no insulin measurements: only the product of secretion and sensitivity is identifiable from CGM, so that product is the parameter. Fewer parameters than a patient has days |
| Integration | Exponential integrator per sub-system | Euler / RK4 | Exact for each linear part, stable at 5 and 15 min, so one code path serves both cohorts |
| Assimilation | Stochastic ensemble Kalman filter, 128 members | EKF/UKF, particle filter, nightly MAP refit, Luenberger observer (rival) | Gives state, parameter and forecast uncertainty from one mechanism; no Jacobians; 1 s per patient. An observer gives a point estimate only |
| Population learning | Joint robust least squares over training patients' meal windows (sparse Jacobian) | Hierarchical Bayes (NumPyro) | 15 s per fold, no new dependency. Empirical Bayes is enough for 36 training patients |
| Lab-to-prior map | Ridge, strength by exact leave-one-out | Gaussian process, gradient boosting | Four features, 36 patients: anything richer overfits |
| Residual model | LightGBM on twin outputs + raw features, correction capped | LSTM / transformer | Same learner as the baseline, so the comparison isolates the twin. Cap keeps physics in charge. (Still holds after 17 Oct: the networks were tested as baselines, not as the residual) |
| Baselines | Persistence, population LightGBM (what most entries built), Chronos-Bolt zero-shot; from 17 Oct GRU, LSTM, patch transformer (`twin/neural_baselines.py`) and Chronos-2 zero-shot and fine-tuned (`twin/chronos_baseline.py`) | (nothing left out) | A twin must be compared with the strongest fair rival. We first wrote "fine-tuning needs more than 45 people"; that was untested and wrong (section 4) |
| Forecast partner (17 Oct) | Hybrid twin and fine-tuned Chronos-2 averaged, equal weights fixed in advance | Chronos-2 alone; fitted blend weights | Best of every model at 30 and 60 min at home and abroad; Chronos-2 alone has no state, mechanism or what-if. Fitted weights would need another held-out split |
| Recommendations (17 Oct) | Exhaustive search over 8 lifestyle actions on the twin's own state; least effort with P(event) under 30% (`core.recommend`) | Q-learning; offline RL from the logged data | One choice per meal, outcome within 3 h: a contextual bandit the twin solves exactly. No randomised actions in the data for offline RL; Q-learning in the twin would converge to the same answer with approximation error |
| Intervals | Conformalized quantile regression, then adaptive conformal inference per patient | Ensemble spread scaled by a conformal factor | See "tried and dropped" |
| Dashboard | Streamlit + Plotly | React front end | One file, runs from a clean clone |

## 3. Against the closest rival entry (method level)

| | GlucoTwin India (Team Vicimus) | This project |
|---|---|---|
| Primary evidence | 80 synthetic patients; CGMacros as a second table | 45 real people, patient-level 5-fold; synthetic used only for verification |
| Twin fitted to a test patient | MAP calibration on the first 60% of the recording | Never fitted: prior from labs, then online updates only |
| Updating | State observer (point estimate), parameters fixed after calibration | Ensemble filter updates states and parameters at every reading |
| Labs | Literature priors; reported "no measurable accuracy" from labs | Lab-to-prior map learned from real people; cold-start effect measured |
| Intervals | Conformalized quantile regression on held-out patients | Same, plus per-patient online adaptation; coverage reported per patient |
| What-if | Simulator, not validated | Tested on matched real meal pairs and on true counterfactuals |
| Second real cohort | None | ShanghaiT2DM, no refit, baseline trained at matched modality |
| Interoperability | FHIR R4, ABHA identifiers | Synthea-style CSV export only (their strength, not ours) |

## 4. Tried and dropped

| Idea | What happened | Decision |
|---|---|---|
| Move persistent disturbance into basal glucose (integral action) | Unstable without extra clipping and 2 to 4% worse RMSE on the development patients | Reverted. Plain filter kept |
| Intervals from the ensemble spread times a conformal factor | Spread barely varied (Spearman with absolute error about 0), so bands were constant-width in disguise | Replaced by conformalized quantile regression with the twin's outputs as features |
| "Rise above basal after a standard meal" as the tolerance index | No relation to HbA1c (rho about 0) because basal glucose and carbohydrate sensitivity trade off | Report the absolute standard-meal peak instead, and say why |
| Carbohydrate yield fixed at the textbook value | A third of patients hit the lower bound | Parameter reinterpreted as acute carbohydrate sensitivity with a wider prior; documented in `twin/core.py` |
| Total carbohydrate as the meal input | Fibre coefficient ran to its bound | Use carbohydrate minus fibre |
| No time-of-day term | Breakfast responses under-predicted | Population 24-h harmonic on carbohydrate sensitivity, fitted per fold |
| Zero-shot use only of foundation models ("fine-tuning needs more than 45 people") | Tested 17 Oct: fine-tuned on about 27 patients per fold, Chronos-2 became the most accurate single model at home and on ShanghaiT2DM | Claim withdrawn; fine-tuned Chronos-2 averaged into the reported forecast |
| Sequence networks trained from scratch (GRU, LSTM, patch transformer) | Tied LightGBM at home; on ShanghaiT2DM over-predicted at every hour (mean error +13 to +20 mg/dL, worst on insulin) | Kept as reported baselines only |

Model structure was iterated twice using cross-validated results on CGMacros, and filter noise levels were set on
nine development patients. Both are stated wherever results appear, and results are also given without those nine.
ShanghaiT2DM was run at each of the two iterations; it was never used to choose anything.

## 5. What is established and what is ours

| Established methods we use | Ours |
|---|---|
| Minimal-model physiology; ensemble Kalman filter; gradient boosting; conformalized quantile regression; adaptive conformal inference; HOMA; GRU, LSTM and transformer networks; Chronos-2 fine-tuning; model-based planning for a contextual bandit | Labs mapped to priors over twin parameters and tested for cold-start value on real data |
| | A T2D/prediabetes meal twin that is never fitted to its patient, only updated online, evaluated as such |
| | What-if answers scored against within-person natural experiments, with the same test applied to the ML baseline |
| | Per-patient interval coverage as the unit of reporting, internally and on an external cohort |
| | Cross-country, cross-device transfer test with a modality-matched baseline |
| | The strongest rivals tested on the same folds and external cohort, including the one that beat the twin abroad |
| | Twin-planned lifestyle advice scored against true counterfactuals, with fixed rules and an oracle |
| | A reference simulator richer than the twin, used to check what-ifs against true counterfactuals |

The claim is the combination and the fact that each twin property has a test, not a new model family.
