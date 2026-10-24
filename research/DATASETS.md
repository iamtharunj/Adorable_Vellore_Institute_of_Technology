# Dataset catalogue

As of 10 October 2026, updated 18 October. Three datasets are used, plus six simulated regional Indian cohorts (section 4);
the rest were evaluated and set aside, with the reason. No real Indian cohort is used: no open Indian CGM dataset with
linked labs was found, so the Indian cohorts are simulated from Indian surveys and food tables and are labelled as such.

**Re-checked 17 October 2026: still none to download.** Indian CGM data exists, but only on request or not at all:

| Lead | What it holds | Access |
|---|---|---|
| Pune-2021 + Joshi-2018 ([Frontiers in Endocrinology 2023](https://www.frontiersin.org/journals/endocrinology/articles/10.3389/fendo.2023.1264072/full)) | 128 CGM traces (FreeStyle Libre Pro), HbA1c; no meal logs | "Will be made available by the authors, without undue reservation": email the authors |
| Chennai food-response studies ([medRxiv 2024](https://www.medrxiv.org/content/10.1101/2024.10.20.24315560v1.full)) | Adults with T2D, Libre, meals | Not shareable: participants did not consent to third-party sharing |
| Ultrahuman M1 study ([medRxiv 2023](https://www.medrxiv.org/content/10.1101/2023.09.20.23295642.full.pdf)) | Non- and pre-diabetic Indians | Availability not confirmed (page blocked to automated access) |
| Retrospective clinic cohorts ([Primary Care Diabetes 2025](https://www.sciencedirect.com/science/article/pii/S1751991825001111), [Cureus 2025](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12066881/)) | 248 and 649 adults with T2D | Summary statistics only |

GluFormer ([code](https://github.com/Guylu/GluFormer), Apache-2.0), a CGM-specific foundation model, publishes no weights, and its
pretraining cohort is private, so it cannot be fine-tuned here.

`python -m twin.data` downloads the two real datasets from their official hosts, verifies integrity
and writes `data/raw/SOURCES.json` (URL, byte count and SHA-256 of every file). Raw data is never committed.

## Used

### 1. CGMacros v1.0.0: development and internal validation

| | |
|---|---|
| Source | PhysioNet, <https://physionet.org/content/cgmacros/1.0.0/>, DOI 10.13026/3z8q-x658 |
| Licence | **CC BY-NC-SA 4.0** (attribution, non-commercial, share-alike). Open access, no credentialing |
| Ethics | Advarra IRB Pro00049227; ClinicalTrials.gov NCT04991142; written consent (per the PhysioNet page) |
| Population | 45 adults in the USA: 15 without diabetes, 16 prediabetes, 14 type 2 diabetes (by HbA1c); 34 Hispanic/Latino; BMI 21 to 49 |
| Duration | About 10 days each (7 to 19) |
| Static record (`bio.csv`) | Age, sex, BMI, weight, height, self-identified ethnicity, HbA1c, fasting glucose, fasting insulin, triglycerides, total/HDL/LDL cholesterol, three fingerstick glucose values on day 1 |
| Streams (per-minute CSV) | Dexcom G6 Pro and FreeStyle Libre Pro glucose, Fitbit heart rate, activity calories, METs (11 files give a 0 to 3 intensity instead), meal type, calories, carbohydrate, protein, fat, fibre, amount consumed, photo path |
| Protocol | Breakfasts were protein shakes and lunches came from one restaurant chain, both with deliberately varied macronutrients; dinners were free choice |
| Download | 657 MB archive, mostly meal photos. We read only the 48 CSVs (6.6 MB compressed) from the remote zip with HTTP range requests and check each file's CRC. Downloaded 10 Oct 2026 |
| What we use | Dexcom as the target; Fitbit METs as activity (calories / resting calories where METs are missing: identical quantity in every file that has both); meals; six lab and demographic fields |

Handling decisions that matter:

- **Dexcom is stored interpolated to one minute.** We keep only native readings (integer values), one per 5-minute bin, so no value on our grid was computed from a later sample.
- **Libre is never an input.** It is a near-copy of the target (and reads 20 to 60 mg/dL lower in several participants).
- **"Amount consumed" and photos are recorded after eating.** Not used. Meals are assumed fully eaten at decision time.
- **Total carbohydrate includes fibre** on food labels; the twin uses carbohydrate minus fibre.
- **Dates are shifted by whole days**, so clock time is intact and time-of-day effects are usable.
- Limitations: small (45), one country, short, standardised breakfasts and lunches, no medication record, no sleep or HRV, no outcomes beyond CGM.

### 2. ShanghaiT2DM: external validation, never used for fitting

| | |
|---|---|
| Source | figshare collection 6310860, file `diabetes_datasets.zip` (<https://figshare.com/articles/dataset/diabetes_datasets_zip/21600933>); paper: Zhao et al., *Scientific Data* 2023 |
| Licence | **CC BY 4.0** |
| Population | 100 Chinese adults with type 2 diabetes, 109 recordings; mean age 60, BMI 24, HbA1c 9.0%; about half on insulin; many recorded in hospital |
| Duration | 3 to 14 days per recording |
| Static record | Age, sex, height, weight, BMI, smoking, alcohol, diabetes duration, complications, comorbidities, glucose-lowering and other drugs, fasting and 2-h glucose, C-peptide and insulin, HbA1c (mmol/mol), glycated albumin, lipids, creatinine, eGFR, uric acid, urea |
| Streams (Excel per recording) | FreeStyle Libre H glucose every 15 min, capillary glucose, ketones, meals as free text with weights (English and Chinese), insulin doses, oral agents, pump rates |
| Download | 3.7 MB; MD5 checked against the value figshare publishes. Downloaded 10 Oct 2026 |
| What we use | CGM, meal times and text, six static fields. HbA1c converted from IFCC to %, insulin from pmol/L to µU/mL |

Handling decisions that matter:

- **Meals are free text** ("Rice 100 g, Beef 15 g"). `twin.data.meal_macros` turns them into grams of each macronutrient with a 12-row keyword table of approximate food-composition values. This is crude; whether weights are raw or cooked is not stated. The twin's per-patient carbohydrate-sensitivity parameter absorbs a consistent scale error, a fixed-feature model cannot.
- **Insulin and drug doses are not modelled.** Their effect lands in the twin's disturbance state. Results are reported separately for recordings with and without insulin.
- **No wearable.** Activity is treated as rest; this is the missing-modality test.
- Limitations: treated, older, partly inpatient population; 15-minute sampling; approximate meal content.

### 3. Synthetic cohort (generated here): verification and demo only

| | |
|---|---|
| Source | `python -m twin.synth` (seeded, fully reproducible). Writes Synthea-style tables and per-patient wearable CSVs to `data/synthetic/` |
| Licence | Same as the code (MIT). Contains no real person and is derived from none |
| Content | 60 virtual adults, 14 days. EHR: demographics, HbA1c, fasting glucose and insulin, lipids, BMI, diagnoses (SNOMED CT), medications, family history, a simulated TCF7L2 risk-allele count. Streams: 5-min CGM, heart rate, steps, METs, sleep stage, meals from 19 Indian dishes with macros |
| Configurable | Cohort size, days, seed, share of unlogged meals, post-meal walk frequency, CGM and wearable dropout |
| Generator | A reference simulator that is structurally richer than the twin: nonlinear stomach emptying, explicit plasma insulin with first-phase secretion, hepatic suppression, circadian insulin sensitivity, dawn effect, exercise sensitisation, sensor lag, AR(1) sensor noise and bias, logging error |
| Use | (1) Does the twin recover hidden physiology? (2) Do what-ifs match true counterfactuals (the simulator can replay a day with one input changed)? (3) A demo that runs with no download |
| Not used for | Any accuracy claim. Effect sizes inside the generator (for example the allele effect) are assumptions chosen for plausibility, not estimates |

### 4. Regional Indian synthetic cohorts (generated here, 18 Oct 2026): verification and demo only

No open Indian CGM data exists (above), so `python -m twin.india` simulates it, region by region, from published
Indian surveys and food tables. Same reference simulator as cohort 3; what changes is who the people are and what they eat.

| | |
|---|---|
| Source | `twin/india.py` (data and checks) and `twin/synth.py` (simulator). Six cohorts of 60 adults, 14 days: North, South, East, West, Central and Northeast, the regions of ICMR-INDIAB with its state grouping. Five were asked for; the Northeast is added because INDIAB reports it separately and its diet differs most (white rice 99%, most animal protein, least sugar) |
| Licence | Same as the code (MIT). No real person; derived from none |
| Written to | `data/synthetic/india_<region>/` (the Synthea-style tables, wearables, and meals with dish names) and `data/processed/india_<region>.pkl`; `load("india_south")` |
| Check | `results/INDIA.md`: each generated cohort next to its INDIAB target, then the twin fitted and tested inside each region |
| Not used for | Any accuracy claim about Indians |

Where each regional number comes from:

| Element | Source |
|---|---|
| States in each region | ICMR-INDIAB-21, Anjana et al., *Nat Med* 2025 ([PMC12618255](https://pmc.ncbi.nlm.nih.gov/articles/PMC12618255/)), Extended Data Table 1 |
| A person's home state | Census of India 2011 populations |
| Age and BMI (median, IQR), sex, physically inactive, family history, tobacco, alcohol, hypertension, triglycerides, HDL | ICMR-INDIAB-21 Table 2 (n = 18,090) |
| Shares of prediabetes and newly diagnosed type 2 diabetes | ICMR-INDIAB-21 Table 2; INDIAB's rule (HbA1c or fasting glucose). Each region's severity distribution is scaled (`india.calibrate`, once) so its share of normal glucose arises by itself, then a quota trims the sampling noise. Known diabetes is outside INDIAB's diet sample, so T2D here is untreated |
| Diet targets: % energy from carbohydrate, fat, protein, added sugar, white rice, wheat, millets, animal protein | ICMR-INDIAB-21 Extended Data Table 2 |
| Staples by state (Karnataka ragi and jowar, Gujarat bajra, Maharashtra jowar and bajra, Chhattisgarh and Bihar rice, Punjab wheat) | ICMR-INDIAB-21 Extended Data Table 1 and text |
| Dish composition, per serving unit | Indian Nutrient Databank (INDB), Vijayakumar et al., *Curr Dev Nutr* 2024 ([GitHub](https://github.com/lindsayjaacks/Indian-Nutrient-Databank-INDB-), commit fbdb62b), 68 recipes; Shobana et al., *Indian J Med Res* 2022 ([PMC9552392](https://pmc.ncbi.nlm.nih.gov/articles/PMC9552392/)) cooked composition for ragi mudde, jowar bhakri, bajra rotla, adai, chickpea sundal; USDA FoodData Central 09040 for banana |
| Glycaemic index, measured in India | Shobana 2022: ragi mudde 98, jowar roti 84, maize roti 75, bajra roti 70, adai 66, methi paratha 60, chickpea sundal 24. NIN, *J Food Sci Technol* (South Indian breakfasts, [summary](https://thesouthfirst.com/health/which-of-these-south-indian-breakfast-foods-can-increase-your-blood-sugar-levels/)): plain dosa 79, lemon rice 79, vegetable biryani 75, chapati 62, parota 62, pesarattu 61, vada sambar 37. Rice idli 78 ([PSG CAS](https://ir.psgcas.ac.in/1647/1/2022-D~1.PDF)). Upma 71 ([Asian breakfast GI study](https://dro.deakin.edu.au/articles/journal_contribution/The_glycaemic_index_and_insulinaemic_index_of_commercially_available_breakfast_and_snack_foods_in_an_Asian_population/20802640)) |
| Glycaemic index, otherwise | Atkinson et al., *Diabetes Care* 2008, Table 1 ([PMC2584181](https://pmc.ncbi.nlm.nih.gov/articles/PMC2584181/)): white rice 73, wheat roti 62, white bread 75, boiled potato 78, lentils 32, chickpeas 28, kidney beans 24, full-fat milk 39, banana 51, sucrose 65. A plate's GI is the carbohydrate-weighted mean; free sugars count at 65 |

Our assumptions (no data found, or a choice we made):

- The stomach empties in proportion to the meal's GI / 70. The twin never sees GI; it sees grams, as from a food log.
- INDB counts all frying oil as eaten in deep-fried recipes (60 to 80 g fat in one samosa or vada). For samosa, medu vada and
  kachori we keep INDB's carbohydrate, protein and fibre and set fat to half the energy.
- INDB carbohydrate is treated as available carbohydrate, the IFCT 2017 convention (its energy fits 17 kJ/g carbohydrate and
  protein and 37 kJ/g fat with no fibre term), so a label's total carbohydrate is carbohydrate + fibre.
- GI with no measurement: flattened rice 70, puffed rice 80 (between boiled rice 73 and rice crackers 87), dhokla 35, dal dhokli 47,
  non-starchy vegetables and gravies 50, khichdi 59 (rice and lentils 2:1).
- Proxies, named as such in `twin/india.py`: luchi as INDB plain paratha, pakhala as boiled rice, dal bafla as paratha with
  panchmel dal, pork as INDB mutton yakhni, pitha as rice puttu, pongal as khichdi with ghee.
- Dinner at 21:00 ± 30 min in every region. The only data found is a wellness-app report (54% of 30,000 users ate their last large
  meal after 21:00; [EYVA India Wellness Index 2026](https://thesouthfirst.com/health/are-you-eating-dinner-at-the-wrong-time-study-reveals-best-time-for-last-meal-to-fight-insulin-resistance)). Other meal times are the base generator's. No regional meal-time survey was found.
- Physically active people (INDIAB PAL ≥ 1.70) get about four 20-to-60-minute bouts a day at 2.5 to 5 METs; inactive people the
  base generator's 1.5 shorter bouts.
- Physiology (insulin sensitivity, beta-cell function, liver) is the same in every region. Regions differ by plates, GI, body size,
  prevalence and activity. Each person has their own favourite plates (gamma-weighted) among those of their state.
- Plate weights were tuned once, by hand, so each region's diet lands near its INDIAB targets; `results/INDIA.md` shows what is
  left over. Height follows the base generator (no verified Indian adult height by sex was found).

## Considered and not used

| Dataset | What it offers | Access | Why not used |
|---|---|---|---|
| BIG IDEAs Glycemic Variability (PhysioNet) | 16 adults at prediabetes range; Dexcom G6, Empatica E4 (HR, IBI for HRV, EDA, temperature), food logs | Open; about 34 GB raw | Size against a slow PhysioNet link (18 KB/s observed) and a 10-day deadline. Next external set to add: `twin.data` needs one more loader |
| AI-READI v3 | 2,280 adults, Dexcom G6, Garmin, labs, retinal images | Controlled access, ethics attestation, about 2 weeks | Access time; no meal logs, so no meal what-if |
| HUPA-UCM (Mendeley Data) | 25 adults with type 1 diabetes, Libre 2, Fitbit, insulin, carbs | Open, CC BY-NC-ND | Type 1; the twin has no exogenous-insulin model |
| OhioT1DM | 12 adults with type 1 diabetes, 8 weeks | Data-use agreement signed by an institution | Access time; type 1 |
| T1DEXI (Vivli) | 497 adults with type 1 diabetes | Request and review | Access time; type 1 |
| MIMIC-IV | ICU and hospital EHR | Credentialed (training + DUA) | Inpatient monitors, not wearables; no CGM |
| Synthea | Synthetic longitudinal EHR | Open (Apache 2.0) | Its records carry no physiology that a glucose stream could be consistent with. Joining a random Synthea chart to a real CGM trace would be fake fusion. Our generator emits Synthea-style tables whose labs come from the same latent physiology as the streams |
| simglucose (UVA/Padova re-implementation) | Type 1 simulator, 30 virtual patients | Open (MIT) | Type 1 with insulin pump; no endogenous secretion, labs or lifestyle streams |

## Fusion check

In CGMacros and ShanghaiT2DM the static record and the stream share a participant ID and a study window: the labs
and the glucose trace belong to the same person. That is the fusion the brief asks for. In the synthetic cohort the
same holds by construction, because one latent physiology produces both.
