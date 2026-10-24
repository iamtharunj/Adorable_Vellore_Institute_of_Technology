# Literature review

Scope: what a health digital twin has to be, how glucose is forecast today, what comparable
competitions rewarded, and what rival entries in this challenge have built. Compiled 1 to 10 October 2026.
Linked statements are published evidence; sentences marked *our reading* are judgement.
Full references: [BIBLIOGRAPHY.md](BIBLIOGRAPHY.md). Local copies: [papers/MANIFEST.md](papers/MANIFEST.md).

## 1. What counts as a digital twin

- NASEM (2023) defines a digital twin as a virtual representation that is **dynamically updated with data from its physical twin, has predictive capability, and informs decisions**, with verification, validation and uncertainty quantification (VVUQ) built in.
- Tudor et al. (npj Digital Medicine, 2025) screened 149 published health "digital twins": **18 (12%) met the NASEM definition and 2 (1.3%) mentioned VVUQ**. Most were static models or one-way "digital shadows".
- Sel et al. (npj Digital Medicine, 2025) make the same demand for medical twins: person-specific, continuously updated, with quantified uncertainty.
- *Our reading:* a jury with a clinician or a modelling researcher on it will ask three things. Does anything update? Is the uncertainty real? Was any claim tested? We designed for those three questions.

## 2. Why post-meal hyperglycaemia, and why India

| Evidence | Finding | Source |
|---|---|---|
| Burden | 11.4% diabetes, 15.3% prediabetes among 113,043 adults in 31 states | ICMR-INDIAB-17, Lancet Diabetes Endocrinol 2023 |
| Diet | 61.6% of energy from carbohydrate on average; modelled remission targets 49 to 54% | Anjana et al., Diabetes Care 2022 |
| Diet quality | Refined carbohydrate linked to T2D and prediabetes; replacing it with protein lowers risk (n = 18,090) | ICMR-INDIAB-21, Nature Medicine 2025 |
| Phenotype | Younger onset, lower BMI, more insulin resistance, faster beta-cell decline in South Asians | Mohan, Diabetes Care 2025 |
| CGM in Indian T2D | 649 first-sensor users: 40.8% time in range, 53.5% time above range | Gupta, Cureus 2025 |
| Twin-guided care in India | 4-hospital RCT (n = 319): CGM + wearable + twin-guided nutrition improved HbA1c and blood pressure | Shamanna et al., JACC Advances 2024 |
| The cheap intervention | Light walking after sitting lowers postprandial glucose versus continued sitting | Buffey et al., Sports Medicine 2022 (meta-analysis) |
| Target | Time in range 70 to 180 mg/dL above 70% | ADA Standards of Care, glycaemic goals |

*Our reading:* in Indian T2D the dominant, modifiable problem on a CGM report is time above range after
carbohydrate-heavy meals, and the two cheapest levers are portion and a walk. Both are inputs a twin can simulate.

## 3. How glucose is forecast: state of the art

| Family | Representative work | Strength | Gap we use |
|---|---|---|---|
| Deep forecasters and benchmarks | GlucoBench (ICLR 2024); BGLP Challenge 2018/2020 on OhioT1DM | Strong point forecasts on standard splits | One model for all; no "what if"; type 1 with known insulin |
| Time-series foundation models | Chronos-Bolt fine-tuned on 8 public CGM sets: zero-shot did not consistently beat Elastic Net or PatchTST, light fine-tuning cut RMSE 8.6 to 18.2% (Zhang et al., 2026); Chronos-2 with covariates (Ansari et al., 2025); on CGMacros, multimodal context moved Chronos-2 from 23.8 to 23.5 mg/dL (GlucoAgent, NeurIPS 2026); GluFormer (Nature 2026, 10,812 people) | Transfer, scale, in-context covariates | Not interventional; no patient state; no what-if mechanism. *Tested 17 Oct:* fine-tuned Chronos-2 is the most accurate single forecaster here, at home and abroad, so it is averaged into our reported forecast; the twin keeps state, what-ifs and advice |
| Deep sequence models on small CGM sets | GlucoBench (ICLR 2024): on small datasets ARIMA and linear regression were best; deep models excelled only on larger ones. Tree ensembles beat deep nets on medium tabular data (Grinsztajn et al., NeurIPS 2022) | Flexible, end to end | *Tested 17 Oct:* GRU, LSTM and a patch transformer tie LightGBM at home and fail on the external cohort (one population's mapping, nothing adapts per person) |
| Reinforcement learning for diabetes decisions | Lifestyle prescriptions as an offline single-step contextual bandit (arXiv 2510.26807); insulin dosing in type 1 with offline RL on UVA/Padova (arXiv 2204.03376, 2310.10312); RL insulin dosing for meals and exercise (Nature Communications 2024) | Sequential optimisation | Mostly type 1 insulin dosing, simulator-evaluated. *Our reading:* the meal-time lifestyle choice is a contextual bandit; with a twin as the model it is solved exactly by enumeration (`core.recommend`) and was tested against true counterfactuals |
| Personalised meal response | Zeevi et al. (Cell 2015, 800 people); Berry et al. (Nat Med 2020, r = 0.77); Kondratyeva et al. (2026) on CGMacros | Responses are personal and predictable | A per-meal score: no continuous state, no uncertainty |
| Mechanistic and hybrid twins | Bergman minimal model (1979); oral minimal model (Dalla Man 2002); exercise extension (Breton 2008); ReplayBG (TBME 2023); Wang & Fox (ML4H 2023); PhysioSeq2Seq (2026) | Few parameters with meaning; replay with altered inputs | Mostly type 1; fitted offline; labs not used as priors; uncertainty rarely calibrated |
| Counterfactual CGM models | GlyTwin (2025); SSM-CGM (NeurIPS TS4H 2025) | What-if forecasts | What-ifs not checked against observed behaviour |
| Irregular multivariate series | Raindrop (ICLR 2022), mTAN (ICLR 2021) | Missing and asynchronous sensors | Black box. A state-space twin handles a gap by integrating forward |
| Uncertainty | Conformalized quantile regression (Romano et al. 2019); adaptive conformal inference (Gibbs & Candès 2021) | Distribution-free coverage; online adaptation | Coverage per patient is almost never reported |

What the model constants rest on: glucose effectiveness, insulin-action and insulin-clearance rates are
fixed at minimal-model scale values (Bergman 1979; Dalla Man 2002) and act only as the model's time
constants; every patient-level quantity is estimated from data. The 15-minute persistence rule for an
event follows the convention CGM consensus statements use for glycaemic events (Battelino et al.);
applying it to the 180 mg/dL target is our definition, not a guideline outcome.

## 4. Comparable competitions: what won, and what we could verify

| Competition | Winner and method | Evidence | Lesson taken |
|---|---|---|---|
| BGLP Challenge 2020 (OhioT1DM, KDH@ECAI) | Rubin-Falcone, Fox, Wiens: deep residual forecasting (N-BEATS style), personalised. RMSE **18.22 / 31.66 mg/dL** at 30 / 60 min; 2nd Hameed & Kleinberg 19.21 / 31.77; 3rd Zhu et al. (GAN) 18.34 / 32.21 | **Verified** from the organisers' official ranking table (8 ranked systems) | A 60-min RMSE near 30 mg/dL is the realistic frontier even with insulin data. Top entries were all personalised |
| PhysioNet/CinC Challenge 2019 (sepsis, 6 h early) | "Can I get your signature?" (Morrill et al.): signature features + gradient boosting, utility 0.360; then Sepsyd 0.345, Separatrix 0.339 | **Verified** via the organisers' analysis (arXiv 2012.11013; 104 teams) | On the hospital with no training data the winner scored **-0.123**; rank correlation of utility between seen and unseen hospitals was about zero. External validation decides credibility |
| BrisT1D Kaggle (2024-25, T1D + smartwatch) | Not established | **Unavailable**: leaderboard and write-ups are script-rendered; no primary source retrieved | None claimed |
| Epic Sepsis Model (deployed, not a competition) | External AUROC 0.63, PPV 12% (Wong et al., JAMA Intern Med 2021) | Published | Silent failure outside home data; alert burden matters |
| This challenge, previous editions | None found | **Unavailable**: no prior edition or published rubric located | We rely on the brief only |

## 5. Rival entries in this challenge (public GitHub, as of 10 Oct 2026)

Self-reported numbers, not reproduced by us.

| Entry | Event | Data | Method | Reported | Gap |
|---|---|---|---|---|---|
| GlucoTwin India (Team Vicimus) | Glucose excursion up to 2 h | 80 synthetic patients; CGMacros as "external validation" | Oral minimal model, MAP calibration from EHR-informed literature priors, Luenberger observer, LightGBM, conformalized quantile regression, what-if, FHIR/ABDM | Synthetic: RMSE 17.5 at 60 min, AUROC 0.959. CGMacros: RMSE 22.5 at 60 min; 71% of excursions flagged, 46 min lead, 1.2 false alerts/day; "labs add no measurable accuracy" | Closest to ours. Twins calibrated on the first 60% of each real recording; what-ifs untested; no second real cohort; coverage not per patient |
| MetaTwin | Glucose event + "should this forecast be trusted" | Synthetic headline; CGMacros pipeline optional | Forecaster + failure detector + abstention | Synthetic RMSE 13.6; failure-detector AUROC 0.67 | States itself that results are synthetic |
| VitalTwin | T2D and CVD risk, 24-week projection | 20,000 synthetic people | Bergman ODE + risk models + effect-size projection | Synthetic only | Outcomes sampled from the risk equations the model then learns |
| GlucoTwin (AlgoAura) | >180 in 120 min | 200 synthetic | GBDT + Platt | AUROC 0.981 | Model learns its own generator |
| GlucoTwin (RUSHI-KOLLA) | >180, about 60 min | CGMacros + Synthea | LightGBM | AUROC 0.951 | Synthea chart is not the same person as the CGM trace |
| HealthJEPA, GlycoTwin AI, glycotwin, GlucoTwin prototype | Glucose excursions | Synthetic | Deep or boosted models | AUROC 0.93+ | Synthetic only |
| ThermoTwin, TwinCare, CardioTwin, asthma, sepsis, warfarin twins | Other conditions | Synthetic or trial context | Rules, RF, PK/PD | Mostly none | Different lanes |

*Our reading:* "glucose above 180, boosted trees, what-if slider, synthetic data" is the crowded lane, and one
team has already added physiology and conformal bands. Nobody has (a) made real linked data the primary
evidence, (b) tested what-ifs against real behaviour, (c) reported coverage per patient, or (d) run a
second real cohort from another country without refitting. Those four are where this project puts its effort.

## 6. Gaps this project addresses

1. **Labs as physiology, not columns.** Rivals concatenate EHR fields; one reports no benefit. We map labs to priors on the twin's parameters and measure the cold-start effect.
2. **Something must update.** We assimilate every reading with an ensemble Kalman filter and compare against a frozen twin and a generic one.
3. **What-ifs must be checked.** Natural experiments inside the real data, and true counterfactuals from a richer simulator.
4. **Coverage per patient.** Conformal bands adapted online, reported for every patient, including on the external cohort.
5. **Transfer.** Train on one country's data, test on another's, with the baseline given the same modality.
6. **The strongest rivals, tested rather than assumed away (17 Oct).** GRU, LSTM, a patch transformer and Chronos-2 (zero-shot and fine-tuned) on the same folds and the same external cohort.
7. **Advice that is tested.** The twin picks the least-effort lifestyle change at each meal; the choice is scored against true counterfactuals on synthetic patients, alongside fixed rules and an oracle.
