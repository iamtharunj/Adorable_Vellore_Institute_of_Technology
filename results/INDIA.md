# Regional Indian synthetic cohorts

Six simulated cohorts, one per ICMR-INDIAB region, from `python -m twin.india`. **No real person; not an accuracy claim about Indians.** They test the twin on Indian regional diets and lifestyles where the true physiology is known. Plates come from the Indian Nutrient Databank and measured Indian glycaemic indices; populations from ICMR-INDIAB-21 (n = 18,090). Sources and assumptions: `research/DATASETS.md` section 4.

## 1. Generated cohort against its target (ICMR-INDIAB-21 regional median, in brackets)

| Diet, % of energy | North | South | East | West | Central | Northeast |
|---|---|---|---|---|---|---|
| Carbohydrate | 56.0 (60.3) | 60.2 (63.7) | 64.7 (64.8) | 60.9 (59.6) | 60.0 (62.6) | 68.2 (63.8) |
| Fat | 30.3 (27.7) | 27.1 (24.7) | 24.5 (24.0) | 27.7 (27.9) | 29.0 (25.6) | 19.3 (21.6) |
| Protein | 13.7 (12.1) | 12.7 (11.5) | 10.8 (11.3) | 11.4 (12.2) | 11.0 (11.5) | 12.4 (13.6) |
| Free / added sugar | 7.7 (7.9) | 7.6 (7.1) | 7.4 (6.3) | 8.1 (7.1) | 7.2 (7.0) | 3.8 (2.1) |
| White rice | 8.2 (8.1) | 29.9 (33.8) | 35.3 (31.1) | 24.6 (23.3) | 18.4 (17.1) | 51.9 (48.1) |
| Wheat | 22.6 (26.3) | 7.8 (10.9) | 10.8 (13.4) | 12.5 (10.0) | 25.5 (30.0) | 4.0 (7.6) |
| Millets | 1.5 (0.2) | 1.3 (0.4) | 0.0 (0.1) | 5.8 (5.1) | 0.0 (0.3) | 0.0 (0.1) |
| Animal protein | 0.2 (0.3) | 0.9 (1.0) | 0.9 (0.6) | 0.6 (1.4) | 0.2 (0.3) | 3.4 (2.9) |
| Energy, kcal/day (no target) | 1770 | 1616 | 1746 | 1554 | 1721 | 1541 |
| Carbohydrate-weighted meal GI | 58 | 66 | 68 | 66 | 63 | 69 |

| People | North | South | East | West | Central | Northeast |
|---|---|---|---|---|---|---|
| Median age | 40 (40) | 40 (41) | 44 (40) | 48 (42) | 38 (40) | 38 (39) |
| Median BMI | 23.1 (23.0) | 21.6 (23.0) | 21.2 (21.0) | 21.5 (22.0) | 22.4 (22.0) | 21.1 (22.0) |
| Male share | 0.42 (0.49) | 0.53 (0.45) | 0.58 (0.50) | 0.42 (0.48) | 0.53 (0.51) | 0.47 (0.50) |
| Physically inactive | 0.67 (0.67) | 0.53 (0.64) | 0.57 (0.55) | 0.67 (0.71) | 0.62 (0.61) | 0.62 (0.54) |
| Family history of T2D | 0.15 (0.10) | 0.18 (0.16) | 0.05 (0.07) | 0.08 (0.09) | 0.10 (0.05) | 0.07 (0.06) |
| Prediabetes share | 0.43 (0.43) | 0.47 (0.46) | 0.38 (0.39) | 0.42 (0.42) | 0.48 (0.49) | 0.33 (0.34) |
| Newly diagnosed T2D share | 0.12 (0.11) | 0.12 (0.11) | 0.07 (0.06) | 0.12 (0.12) | 0.08 (0.09) | 0.07 (0.06) |
| Median HbA1c, % | 5.6 | 5.7 | 5.5 | 5.5 | 5.7 | 5.2 |
| Median fasting glucose, mg/dL | 102 | 102 | 97 | 100 | 100 | 95 |
| Median triglycerides | 122 (114) | 128 (114) | 112 (101) | 110 (101) | 109 (104) | 118 (118) |
| Median HDL | 42 (41) | 40 (39) | 41 (38) | 42 (40) | 42 (39) | 40 (39) |

INDIAB-21 reports median HbA1c 5.2 to 5.5% and fasting capillary glucose 92 to 98 mg/dL by region; our fasting value is plasma-like. Prevalence is matched exactly by construction (people are drawn until each region's shares are filled, by INDIAB's HbA1c-or-fasting-glucose rule); BMI and activity are then outcomes, and drift where the diet pushes glucose up.

## 2. After meals (test half, every eligible meal)

|  | North | South | East | West | Central | Northeast |
|---|---|---|---|---|---|---|
| Meals | 1158 | 1165 | 1182 | 1201 | 1185 | 1194 |
| Meals followed by glucose > 180 mg/dL for 15+ min | 24.4% | 31.6% | 42.4% | 32.1% | 28.9% | 37.1% |
| Mean 3-h peak rise, mg/dL | 57.8 | 66.0 | 83.7 | 69.0 | 64.2 | 77.0 |

## 3. The twin inside each region (in-simulator; fitted on half the people, scored on the other half)

| RMSE, mg/dL | North | South | East | West | Central | Northeast |
|---|---|---|---|---|---|---|
| Persistence, 30 min | 14.9 | 18.0 | 23.3 | 19.7 | 17.8 | 22.1 |
| LightGBM, 30 min | 6.9 | 8.8 | 10.0 | 9.5 | 8.4 | 9.2 |
| Physics twin, 30 min | 7.6 | 8.9 | 10.9 | 9.3 | 8.8 | 10.2 |
| Hybrid twin, 30 min | 6.2 | 7.3 | 8.7 | 7.6 | 7.3 | 8.2 |
| Persistence, 60 min | 24.7 | 29.1 | 37.3 | 32.3 | 28.6 | 35.2 |
| LightGBM, 60 min | 12.3 | 15.0 | 18.2 | 16.9 | 14.8 | 16.6 |
| Physics twin, 60 min | 15.8 | 18.8 | 24.4 | 20.6 | 18.8 | 22.6 |
| Hybrid twin, 60 min | 11.6 | 14.0 | 18.5 | 15.5 | 14.1 | 16.9 |
| Persistence, 120 min | 32.9 | 37.5 | 46.8 | 41.4 | 36.5 | 44.0 |
| LightGBM, 120 min | 15.3 | 17.9 | 21.6 | 19.7 | 17.4 | 19.9 |
| Physics twin, 120 min | 25.1 | 28.2 | 35.2 | 31.3 | 27.8 | 32.3 |
| Hybrid twin, 120 min | 15.3 | 18.3 | 23.7 | 20.6 | 17.6 | 21.7 |
| Hybrid minus LightGBM, 60 min | -0.71 (-1.11 to -0.34) | -1.03 (-2.00 to -0.22) | 0.30 (-0.52 to 1.01) | -1.36 (-2.15 to -0.67) | -0.66 (-1.27 to -0.14) | 0.31 (-0.12 to 0.72) |

## 4. Does the twin recover the truth? (simulator ground truth)

|  | North | South | East | West | Central | Northeast |
|---|---|---|---|---|---|---|
| Carb tolerance vs truth, Spearman | 0.84 | 0.80 | 0.88 | 0.93 | 0.91 | 0.93 |
| Basal glucose error, mg/dL | 4.7 | 6.2 | 5.0 | 3.8 | 5.2 | 4.3 |
| What-if 40% less food: correlation with true effect | 0.79 | 0.75 | 0.83 | 0.88 | 0.82 | 0.88 |
| What-if 40% less food: direction right | 100% | 100% | 100% | 100% | 100% | 100% |
| What-if 30-min walk: correlation with true effect | 0.20 | 0.06 | -0.01 | 0.42 | -0.19 | 0.13 |
| What-if 30-min walk: direction right | 98% | 95% | 97% | 98% | 99% | 98% |

**Limits.** Physiology is the same in every region; regions differ by plates, glycaemic index, body size, prevalence and activity. Stomach emptying scaled by GI is our assumption. Meal clock times are national (dinner 21:00, the only data found being a wellness-app report), not regional. Several dishes are INDB proxies (named so in `twin/india.py`).
