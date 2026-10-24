# Bibliography

Grouped by use. "Local" marks a PDF fetched by `research/fetch_papers.py` (see `papers/MANIFEST.md`).
Entries dated 2026 with arXiv numbers were retrieved from arXiv during this project.

## Digital twins: definition and review
- National Academies of Sciences, Engineering, and Medicine (2023). *Foundational Research Gaps and Future Directions for Digital Twins.* <https://nap.nationalacademies.org/resource/26894/RH-digital-twins.pdf> (Local)
- Tudor BH, et al. (2025). A scoping review of human digital twins in healthcare applications and usage patterns. *npj Digital Medicine.* <https://pmc.ncbi.nlm.nih.gov/articles/PMC12484800/> (Local)
- Sel K, et al. (2025). On verification, validation and uncertainty quantification of digital twins for precision medicine. *npj Digital Medicine.* <https://www.nature.com/articles/s41746-025-01447-y> (title paraphrased; not held locally)
- Shamanna P, et al. (2024). Randomised trial of digital-twin-guided care in type 2 diabetes, four Indian hospitals. *JACC: Advances.* <https://pmc.ncbi.nlm.nih.gov/articles/PMC11450914/> (title paraphrased; not held locally)

## India: burden, diet, phenotype
- Anjana RM, et al. (2023). Metabolic non-communicable disease health report of India (ICMR-INDIAB-17). *Lancet Diabetes Endocrinol.* <https://doi.org/10.1016/S2213-8587(23)00119-5>
- Anjana RM, et al. (2022). Macronutrient recommendations for remission and prevention of T2D in Asian Indians. *Diabetes Care.* <https://diabetesjournals.org/care/article/45/12/2883/147462/>
- Anjana RM, et al. (2025). Dietary profiles and metabolic risk in India (ICMR-INDIAB-21). *Nature Medicine.* <https://doi.org/10.1038/s41591-025-03949-4> (open access: <https://pmc.ncbi.nlm.nih.gov/articles/PMC12618255/>; regional tables used for `twin/india.py`)
- Vijayakumar A, Dubasi HB, Awasthi A, Jaacks LM (2024). Development of an Indian Food Composition Database (INDB). *Curr Dev Nutr* 8:103790. <https://doi.org/10.1016/j.cdnut.2024.103790>; data <https://github.com/lindsayjaacks/Indian-Nutrient-Databank-INDB->
- Shobana S, et al. (2022). Carbohydrate profiling and glycaemic indices of selected traditional Indian foods. *Indian J Med Res* 155:56-65. <https://pmc.ncbi.nlm.nih.gov/articles/PMC9552392/>
- National Institute of Nutrition (ICMR). Glycaemic index of 23 South Indian breakfast foods. *J Food Sci Technol.* <https://link.springer.com/article/10.1007/s13197-022-05368-6>
- Atkinson FS, Foster-Powell K, Brand-Miller JC (2008). International tables of glycemic index and glycemic load values. *Diabetes Care* 31:2281-2283. <https://pmc.ncbi.nlm.nih.gov/articles/PMC2584181/>
- Mohan V (2025). The South Asian phenotype of type 2 diabetes. *Diabetes Care.* <https://doi.org/10.2337/dci24-0046>
- Gupta (2025). CGM metrics in 649 Indian patients with T2D on a first sensor. *Cureus.* <https://pmc.ncbi.nlm.nih.gov/articles/PMC12066881/>
- Buffey AJ, et al. (2022). The acute effects of interrupting prolonged sitting time in adults with standing and light-intensity walking on biomarkers of cardiometabolic health: systematic review and meta-analysis. *Sports Medicine* 52:1765-1787. <https://doi.org/10.1007/s40279-022-01649-4> (Local)
- American Diabetes Association. *Standards of Care in Diabetes*, Section 6: glycemic goals. <https://diabetesjournals.org/care/article/49/Supplement_1/S132/163927/>
- Battelino T, et al. (2023). Continuous glucose monitoring and metrics for clinical trials: international consensus. *Lancet Diabetes Endocrinol.* <https://doi.org/10.1016/S2213-8587(22)00319-9>
- Nathan DM, et al. (2008). Translating the A1C assay into estimated average glucose values (ADAG). *Diabetes Care* 31(8):1473-1478. (HbA1c of the synthetic patients, `twin/synth.py`)

## Datasets
- Gutierrez-Osuna R, Kerr D, Mortazavi B, Das A (2025). CGMacros: a scientific dataset for personalized nutrition and diet monitoring (v1.0.0). PhysioNet. <https://doi.org/10.13026/3z8q-x658>; data descriptor: Das A, Kerr D, Glantz N, Bevier W, Santiago R, Gutierrez-Osuna R, Mortazavi BJ (2025). CGMacros: a pilot scientific dataset for personalized nutrition and diet monitoring. *Scientific Data* 12:1557. <https://doi.org/10.1038/s41597-025-05851-7> (Local)
- Zhao Q, et al. (2023). Chinese diabetes datasets for data-driven machine learning (ShanghaiT1DM, ShanghaiT2DM). *Scientific Data* 10:35. <https://doi.org/10.1038/s41597-023-01940-7> (Local)
- Goldberger AL, et al. (2000). PhysioBank, PhysioToolkit, and PhysioNet. *Circulation* 101(23):e215-e220.
- Prioleau T, et al. (2025). Glucose-ML: a collection of longitudinal diabetes datasets for development of robust AI solutions. arXiv:2507.14077 (Local)
- James SG, et al. (2025). BrisT1D dataset: young adults with type 1 diabetes in the UK using smartwatches. arXiv:2507.17757 (Local)
- Hidalgo JI, et al. (2024). HUPA-UCM diabetes dataset. *Data in Brief.* <https://pmc.ncbi.nlm.nih.gov/articles/PMC11214197/>
- AI-READI Consortium (2025). Protocol. *BMJ Open.* <https://pmc.ncbi.nlm.nih.gov/articles/PMC11800295/>
- Walonoski J, et al. (2018). Synthea: synthetic patient generator. *JAMIA* 25(3):230-238.

## Glucose physiology models
- Bergman RN, Ider YZ, Bowden CR, Cobelli C (1979). Quantitative estimation of insulin sensitivity. *Am J Physiol* 236(6):E667-E677. (minimal model)
- Dalla Man C, Caumo A, Cobelli C (2002). The oral glucose minimal model. *IEEE Trans Biomed Eng* 49(5):419-429.
- Breton MD (2008). Physical activity: the major unaccounted impediment to closed loop control. *J Diabetes Sci Technol* 2(1):169-174. doi:10.1177/193229680800200127
- Matthews DR, et al. (1985). Homeostasis model assessment (HOMA). *Diabetologia* 28:412-419.
- Evensen G (1994). Sequential data assimilation with a nonlinear quasi-geostrophic model using Monte Carlo methods (ensemble Kalman filter). *J Geophys Res* 99(C5).
- Cappon G, et al. (2023). ReplayBG. *IEEE Trans Biomed Eng.* <https://github.com/gcappon/replay-bg>
- Wang KA, Fox EB (2023). Interpretable mechanistic representations for meal-level glycemic control. *ML4H, PMLR 225.* (Local)
- Tran P, et al. (2026). PhysioSeq2Seq: a hybrid physiological digital twin and sequence-to-sequence LSTM for long-horizon glucose forecasting in type 1 diabetes. arXiv:2605.16860 (Local)
- Arefeen A, et al. (2025). GlyTwin: digital twin for glucose control in type 1 diabetes through optimal behavioral modifications using patient-centric counterfactuals. arXiv:2504.09846 (Local)

## Forecasting, foundation models, meal response
- Sergazinov R, et al. (2024). GlucoBench: curated list of continuous glucose monitoring datasets with prediction benchmarks. *ICLR.* (Local)
- Zhang B, et al. (2026). Evaluating time-series foundation models and multimodal dietary context for CGM forecasting. arXiv:2609.11872 (Local)
- Ansari AF, et al. (2024). Chronos: learning the language of time series. *TMLR*; Chronos-Bolt weights: <https://huggingface.co/amazon/chronos-bolt-small>
- Lutsker G, et al. (2026). GluFormer. *Nature.* <https://www.nature.com/articles/s41586-025-09925-9>
- Zeevi D, et al. (2015). Personalized nutrition by prediction of glycemic responses. *Cell* 163:1079-1094. (Local)
- Berry SE, et al. (2020). Human postprandial responses to food (PREDICT 1). *Nature Medicine.* <https://www.nature.com/articles/s41591-020-0934-0>
- Kondratyeva V, et al. (2026). Predicting postprandial glycemic response from meal images, clinical variables, and gut microbiome information. arXiv:2609.24453 (Local)
- Brügger V, Kowatsch T, Jovanova M (2025). Predicting postprandial glucose excursions to personalize dietary interventions for type-2 diabetes management. *Scientific Reports.* <https://pmc.ncbi.nlm.nih.gov/articles/PMC12271334/> (Local)
- Zhang X, Zeman M, Tsiligkaridis T, Zitnik M (2022). Graph-guided network for irregularly sampled multivariate time series (Raindrop). *ICLR.* arXiv:2110.05357 (Local)
- Ke G, et al. (2017). LightGBM. *NeurIPS.*

- Ansari AF, et al. (2025). Chronos-2: from univariate to universal forecasting. arXiv:2510.15821; weights: <https://huggingface.co/amazon/chronos-2>
- GlucoAgent: personalized glucose forecasting from multimodal personal context (2026). *NeurIPS.* <https://neurips.cc/virtual/2026/177194>
- SSM-CGM: interpretable state-space forecasting model of CGM (2025). arXiv:2510.04386
- Friedman JH (2001). Greedy function approximation: a gradient boosting machine. *Annals of Statistics* 29(5). doi:10.1214/aos/1013203451
- Grinsztajn L, Oyallon E, Varoquaux G (2022). Why do tree-based models still outperform deep learning on typical tabular data? *NeurIPS.* arXiv:2207.08815
- Hochreiter S, Schmidhuber J (1997). Long short-term memory. *Neural Computation* 9(8). doi:10.1162/neco.1997.9.8.1735
- Cho K, et al. (2014). Learning phrase representations using RNN encoder-decoder for statistical machine translation (GRU). arXiv:1406.1078
- Vaswani A, et al. (2017). Attention is all you need. *NeurIPS.* arXiv:1706.03762
- Nie Y, et al. (2023). A time series is worth 64 words: long-term forecasting with transformers (PatchTST). *ICLR.* arXiv:2211.14730
- Goswami M, et al. (2024). MOMENT: a family of open time-series foundation models. *ICML.* arXiv:2402.03885 (round 2 baseline, `kaggle/tsfm_run.py`)
- Yue Z, et al. (2022). TS2Vec: towards universal representation of time series. *AAAI.* arXiv:2106.10466 (round 2 baseline)

## Decisions and reinforcement learning
- Watkins CJCH, Dayan P (1992). Q-learning. *Machine Learning* 8:279-292. doi:10.1007/BF00992698
- Sutton RS, Barto AG (2018). *Reinforcement Learning: An Introduction*, 2nd ed. <http://incompleteideas.net/book/the-book-2nd.html>
- Li L, Chu W, Langford J, Schapire RE (2010). A contextual-bandit approach to personalized news article recommendation. arXiv:1003.0146
- Levine S, Kumar A, Tucker G, Fu J (2020). Offline reinforcement learning: tutorial, review, and perspectives. arXiv:2005.01643
- Yu T, et al. (2020). MOPO: model-based offline policy optimization. arXiv:2005.13239
- Diabetes lifestyle medicine treatment assistance using reinforcement learning (2025). arXiv:2510.26807
- Offline reinforcement learning for safer blood glucose control in people with type 1 diabetes (2022). arXiv:2204.03376
- End-to-end offline reinforcement learning for glycemia control (2023). arXiv:2310.10312
- Personalized insulin dosing using reinforcement learning for high-fat meals and aerobic exercises in type 1 diabetes (2024). *Nature Communications.* <https://www.nature.com/articles/s41467-024-50764-5>

## Uncertainty
- Romano Y, Patterson E, Candès E (2019). Conformalized quantile regression. *NeurIPS.* arXiv:1905.03222 (Local)
- Gibbs I, Candès E (2021). Adaptive conformal inference under distribution shift. *NeurIPS.* arXiv:2106.00170 (Local)
- Angelopoulos AN, Bates S (2021). A gentle introduction to conformal prediction and distribution-free uncertainty quantification. arXiv:2107.07511
- Koenker R, Bassett G (1978). Regression quantiles. *Econometrica* 46(1):33-50. doi:10.2307/1913643

## Competitions and deployment failures
- Marling C, Bunescu R (2020). The OhioT1DM dataset for blood glucose level prediction: update 2020; BGLP Challenge official results: <https://webpages.charlotte.edu/rbunescu/data/ohiot1dm/bglp/bglp-results.html>; proceedings (Local)
- Rubin-Falcone H, Fox I, Wiens J (2020). Deep residual time-series forecasting: application to blood glucose prediction. *KDH@ECAI*, CEUR-WS 2675.
- Reyna MA, et al. (2020). Early prediction of sepsis from clinical data: the PhysioNet/Computing in Cardiology Challenge 2019. *Crit Care Med.* <https://pmc.ncbi.nlm.nih.gov/articles/PMC6964870/>
- Reyna MA, Clifford GD (2020). Voting of predictive models for clinical outcomes: analysis of the PhysioNet/CinC Challenge 2019. arXiv:2012.11013 (Local)
- Morrill J, et al. (2019). The signature-based model for early detection of sepsis from electronic health records in the ICU. *Computing in Cardiology.*
- Wong A, et al. (2021). External validation of a widely implemented proprietary sepsis prediction model. *JAMA Intern Med.* <https://jamanetwork.com/journals/jamainternalmedicine/fullarticle/2781307>

## Rival entries (public repositories, read 1 and 10 Oct 2026)
- GlucoTwin India, Team Vicimus: <https://github.com/Physics0070/Vicimus_Vishwakarma-Institute-of-Technology>
- MetaTwin: <https://github.com/riyasojitra27-ux/MetaTwin>
- VitalTwin: <https://github.com/AnushreeKasturi/health-digital-twin>
- GlucoTwin (AlgoAura): <https://github.com/Nishu15205/AlgoAura_MERI-College-of-Engineering-and-Technology>
- GlucoTwin (RUSHI-KOLLA): <https://github.com/RUSHI-KOLLA/Digital-Twin-Challenge>
- HealthJEPA: <https://github.com/THENDRALRAJA006/Digital-Twin-Challenge>
- GlycoTwin AI: <https://github.com/shivamrajsr07/GlycoTwin-AI>
- BioTwin Omni: <https://github.com/deepshekhar555/HappiestHealth-DigitalTwin-2026>
- WarfarinTwin: <https://github.com/legallyananyar-dev/digital-twin-challenge->
- ThermoTwin: <https://github.com/Purvee25/ThermoTwin>
