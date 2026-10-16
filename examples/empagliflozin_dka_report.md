# OpenPulse Signal Detection Report — Draft

Analysis definition version: `7d16320f72afede4134e9b50bb435ed61e4d52105531152820b5c5a4deef061f`

## Analysis definition

- Drug: empagliflozin
- Event: Diabetic ketoacidosis
- Years: 2022–2024
- Date field: `receivedate`
- Drug field: `patient.drug.openfda.generic_name`
- Event field: `patient.reaction.reactionmeddrapt.exact`
- Full filters and handling rules are preserved in cohort.yaml.

## FAERS contingency table

| | Target event matched | Target event not matched |
|---|---:|---:|
| Target drug matched | 974 | 27280 |
| Target drug not matched | 2878 | 4180210 |

Target-drug event reporting proportion: 3.447299%.
Background event reporting proportion: 0.068801%.

## Disproportionality statistics

Method: log-Wald; confidence level: 95.00%; no continuity correction.

| Metric | Estimate | CI lower | CI upper | SE(log) |
|---|---:|---:|---:|---:|
| PRR | 50.1055 | 46.6384 | 53.8303 | 0.036586 |
| ROR | 51.8587 | 48.1778 | 55.8208 | 0.037564 |

These are reporting disproportionality estimates, not incidence, patient risk ratios, or causal effects. No predefined signal-screening rule has been applied.

## DailyMed label evidence

- SETID: `faf3dd6a-9cd0-39c2-0d2e-232cb3f67565`
- Version: 31
- Label effectiveTime: 20260130 (not necessarily the publication date)
- Retrieved: 2026-10-15T05:03:05.318001+00:00
- Original label: https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=faf3dd6a-9cd0-39c2-0d2e-232cb3f67565
- Download source: https://dailymed.nlm.nih.gov/dailymed/downloadzipfile.cfm?setId=faf3dd6a-9cd0-39c2-0d2e-232cb3f67565
- Keyword: ketoacidosis; matching sections: 7.

The excerpts below are keyword matches, not independent evidence counts or an automated risk assessment. Clinical relevance and product scope still require human review.

Product identity check: SETID, product title, and active ingredients matched the configured reference.
Verified active ingredients: empagliflozin.

### Untitled section

> Limitations of Use 
>  
>  JARDIANCE is not recommended for use to improve glycemic control in patients with type 1 diabetes mellitus. It may increase the risk of diabetic ketoacidosis in these patients [see Warnings and Precautions (5.1) ] . 
>  JARDIANCE is not recommended for use to improve glycemic control in patients with type 2 diabetes mellitus with an eGFR less than 30 mL/min/1.73 m 2 . JARDIANCE is likely to be ineffective in this setting based upon its mechanism of action. 
>  JARDIANCE is not recommended for the treatment of chronic kidney disease in patients with polycystic kidney disease or patients requiring or with a recent history of intravenous immunosuppressive therapy or greater than 45 mg of prednisone or equivalent for kidney disease [see Clinical Studies (14.5) ] . JARDIANCE is not expected to be effective in these populations.

### 5.1  Diabetic Ketoacidosis in Patients with Type 1 Diabetes Mellitus and Other Ketoacidosis

> In patients with type 1 diabetes mellitus, JARDIANCE significantly increases the risk of diabetic ketoacidosis, a life-threatening event, beyond the background rate. In placebo-controlled trials of patients with type 1 diabetes mellitus, the risk of ketoacidosis was markedly increased in patients who received sodium glucose co-transporter 2 (SGLT2) inhibitors compared to patients who received placebo and fatal ketoacidosis has occurred with JARDIANCE. JARDIANCE is not indicated for glycemic control in patients with type 1 diabetes mellitus. 
>  Type 2 diabetes mellitus and pancreatic disorders (e.g., history of pancreatitis or pancreatic surgery) are also risk factors for ketoacidosis. There have been postmarketing reports of fatal events of ketoacidosis in patients with type 2 diabetes mellitus using SGLT2 inhibitors, including JARDIANCE. 
>  Precipitating conditions for diabetic ketoacidosis or other ketoacidosis include under-insulinization due to insulin dose reduction or missed insulin doses, acute febrile illness, reduced caloric intake, ketogenic diet, surgery, volume depletion, and alcohol abuse. 
>  Signs and symptoms are consistent with dehydration and severe metabolic acidosis and include nausea, vomiting, abdominal pain, generalized malaise, and shortness of breath. Blood glucose levels at presentation may be below those typically expected for diabetic ketoacidosis (e.g., less than 250 mg/dL). Ketoacidosis and glucosuria may persist longer than typically expected. Urinary glucose excretion persists for 3 days after discontinuing JARDIANCE [see Clinical Pharmacology (12.2) ] ; however, there have been postmarketing reports of ketoacidosis and/or glucosuria lasting greater than 6 days and some up to 2 weeks after discontinuation of SGLT2 inhibitors. 
>  Consider ketone monitoring in patients with type 1 diabetes mellitus and consider ketone monitoring in others at risk for ketoacidosis if indicated by the clinical situation. Assess for ketoacidosis regardless of presenting blood glucose levels in patients who present with signs and symptoms consistent with severe metabolic acidosis. If ketoacidosis is suspected, discontinue JARDIANCE, promptly evaluate, and treat ketoacidosis, if confirmed. Monitor patients for resolution of ketoacidosis before restarting JARDIANCE. 
>  Withhold JARDIANCE, if possible, in temporary clinical situations that could predispose patients to ketoacidosis. Resume JARDIANCE when the patient is clinically stable and has resumed oral intake [see Dosage and Administration (2.3) ] . 
>  Educate all patients on the signs and symptoms of ketoacidosis and instruct patients to discontinue JARDIANCE and seek medical attention immediately if signs and symptoms occur.

### 6	ADVERSE REACTIONS

> The following important adverse reactions are described below and elsewhere in the labeling: 
>  
>  Diabetic Ketoacidosis in Patients with Type 1 Diabetes Mellitus and Other Ketoacidosis [see Warnings and Precautions (5.1) ] 
>  
>  Volume Depletion [see Warnings and Precautions (5.2) ] 
>  
>  Genitourinary Infections, including Urosepsis, Pyelonephritis, Necrotizing Fasciitis of the Perineum (Fournier's Gangrene), and Genital Mycotic Infections [see Warnings and Precautions (5.3) ] 
>  
>  Hypoglycemia [see Warnings and Precautions (5.4) ] 
>  
>  Hypersensitivity Reactions [see Warnings and Precautions (5.6) ]

### 6.2  Postmarketing Experience

> Additional adverse reactions have been identified during postapproval use of JARDIANCE. Because these reactions are reported voluntarily from a population of uncertain size, it is generally not possible to reliably estimate their frequency or establish a causal relationship to drug exposure. 
>  
>  Gastrointestinal Disorders: Constipation 
>  Infections: Necrotizing fasciitis of the perineum (Fournier's gangrene), urosepsis and pyelonephritis 
>  Metabolism and Nutrition Disorders: Ketoacidosis 
>  Renal and Urinary Disorders: Acute kidney injury 
>  Skin and Subcutaneous Tissue Disorders: Angioedema, skin reactions (e.g., rash, urticaria)

### Untitled section

> Disease-associated maternal and/or embryo/fetal risk 
>  
>  Poorly controlled diabetes in pregnancy increases the maternal risk for diabetic ketoacidosis, pre-eclampsia, spontaneous abortions, preterm delivery, and delivery complications. Poorly controlled diabetes increases the fetal risk for major birth defects, stillbirth, and macrosomia related morbidity.

### Untitled section

> Diabetic Ketoacidosis in Patients with Type 1 Diabetes Mellitus and Other Ketoacidosis 
>  
>  In patients with type 1 diabetes mellitus, inform them that using JARDIANCE can increase their risk of life-threatening diabetic ketoacidosis and that fatal ketoacidosis has occurred. For all other patients, inform them that JARDIANCE can cause potentially fatal ketoacidosis and that type 2 diabetes mellitus and pancreatic disorders (e.g., history of pancreatitis or pancreatic surgery) are risk factors. 
>  Educate all patients on precipitating factors (such as insulin dose reduction or missed insulin doses, infection, reduced caloric intake, ketogenic diet, surgery, dehydration, and alcohol abuse) and symptoms of ketoacidosis (including nausea, vomiting, abdominal pain, tiredness, and labored breathing). Inform patients that blood glucose may be normal even in the presence of ketoacidosis. 
>  Advise patients that they may be asked to monitor ketones. If symptoms of ketoacidosis occur, instruct patients to discontinue JARDIANCE and seek medical attention immediately [see Warnings and Precautions (5.1) ] .

### Untitled section

> This Medication Guide has been approved by the U.S. Food and Drug Administration. 
>  Revised: January 2026 
>  
>  
>  
>  
>  
>  MEDICATION GUIDE JARDIANCE ® (jar DEE ans) (empagliflozin tablets) for oral use 
>  
>  
>  
>  
>  What is the most important information I should know about JARDIANCE? 
>  JARDIANCE can cause serious side effects, including: 
>  
>  Diabetic ketoacidosis (increased ketones in your blood or urine) in people with type 1 and other ketoacidosis. JARDIANCE can cause ketoacidosis that can be life-threatening and may lead to death. Ketoacidosis is a serious condition which needs to be treated in a hospital. People with type 1 diabetes have a high risk of getting ketoacidosis. People with type 2 diabetes or pancreas problems also have an increased risk of getting ketoacidosis. Ketoacidosis can also happen in people who: are sick, cannot eat or drink as usual, skip meals, are on a diet high in fat and low in carbohydrates (ketogenic diet), take less than the usual amount of insulin or miss insulin doses, drink too much alcohol, have a loss of too much fluid from the body (volume depletion), or who have surgery. Ketoacidosis can happen even if your blood sugar is less than 250 mg/dL. Your healthcare provider may ask you to periodically check ketones in your urine or blood. 
>  Stop taking JARDIANCE and call your healthcare provider or get medical help right away if you get any of the following. If possible, check for ketones in your urine or blood, even if your blood sugar is less than 250 mg/dL: 
>  
>  
>  
>  
>  
>  
>  
>  
>  nausea 
>  vomiting 
>  stomach-area (abdominal) pain 
>  
>  
>  
>  
>  tiredness 
>  trouble breathing 
>  ketones in your urine or blood 
>  
>  
>  
>  
>  
>  
>  
>  
>  Dehydration. JARDIANCE can cause some people to become dehydrated (the loss of body water and salt). Dehydration may cause you to feel dizzy, faint, light-headed, or weak, especially when you stand up (orthostatic hypotension). There have been reports of sudden worsening of kidney function in people who are taking JARDIANCE. You may be at higher risk of dehydration if you: 
>  take medicines to lower your blood pressure, including diuretics (water pills) 
>  are on low sodium (salt) diet 
>  have kidney problems 
>  are 65 years of age or older 
>  Talk to your healthcare provider about what you can do to prevent dehydration including how much fluid you should drink on a daily basis. Call your healthcare provider right away if you reduce the amount of food or liquid you drink, for example if you are sick or you cannot eat, or start to lose liquids from your body, for example from vomiting, diarrhea or being in the sun too long. 
>  
>  
>  
>  
>  
>  What is JARDIANCE? 
>  JARDIANCE is a prescription medicine used to: 
>  reduce the risk of cardiovascular death and hospitalization for heart failure in adults with heart failure, when the heart cannot pump enough blood to the rest of your body. 
>  reduce the risk of further worsening of kidney disease, end-stage kidney disease (ESKD), death due to cardiovascular disease, and hospitalization in adults with chronic kidney disease. 
>  reduce the risk of cardiovascular death in adults with type 2 diabetes and who also have known cardiovascular disease. 
>  lower blood sugar (glucose) along with diet and exercise in adults and children who are 10 years of age and older with type 2 diabetes. 
>  JARDIANCE is not for use to lower blood sugar (glucose) in people with type 1 diabetes. It may increase their risk of diabetic ketoacidosis (increased ketones in blood or urine). JARDIANCE is not for use to lower blood sugar (glucose) in people with type 2 diabetes who have severe kidney problems, because it may not work. JARDIANCE is not for people with polycystic kidney disease, or who are taking or have recently received certain types of immunosuppressive therapy to treat kidney disease. JARDIANCE is not expected to work if you have these conditions. It is not known if JARDIANCE is safe and effective in children under 10 years of age. 
>  
>  
>  
>  Who should not take JARDIANCE? Do not take JARDIANCE if you: 
>  
>  are allergic to empagliflozin or any of the ingredients in JARDIANCE. See the end of this Medication Guide for a complete list of ingredients in JARDIANCE. Symptoms of a serious allergic reaction to JARDIANCE may include: 
>  rash 
>  raised, red areas on your skin (hives) 
>  swelling of your face, lips, mouth, and throat that may cause difficulty in breathing or swallowing 
>  If you have any of these symptoms, stop taking JARDIANCE and call your healthcare provider right away or go to the nearest hospital emergency room. 
>  
>  
>  
>  
>  
>  What should I tell my healthcare provider before taking JARDIANCE? Before taking JARDIANCE, tell your healthcare provider about all of your medical conditions, including if you: 
>  
>  have type 1 diabetes or have had diabetic ketoacidosis. 
>  have a decrease in your insulin dose. 
>  have a serious infection. 
>  have a history of infection of the vagina or penis. 
>  have a history of amputation. 
>  have kidney problems. 
>  have liver problems. 
>  have a history of urinary tract infections or problems with urination. 
>  are on a low sodium (salt) diet. Your healthcare provider may change your diet or your dose. 
>  are going to have surgery. Your healthcare provider may stop your JARDIANCE before you have surgery. Talk to your healthcare provider if you are having surgery about when to stop taking JARDIANCE and when to start it again. 
>  are eating less, or there is a change in your diet. 
>  are dehydrated. 
>  have or have had problems with your pancreas, including pancreatitis or surgery on your pancreas. 
>  drink alcohol very often or drink a lot of alcohol in the short term ("binge" drinking). 
>  have ever had an allergic reaction to JARDIANCE. 
>  are pregnant or plan to become pregnant. JARDIANCE may harm your unborn baby. If you become pregnant while taking JARDIANCE, tell your healthcare provider as soon as possible. Talk with your healthcare provider about the best way to control your blood sugar while you are pregnant. 
>  are breastfeeding or plan to breastfeed. JARDIANCE may pass into your breast milk and may harm your baby. Talk with your healthcare provider about the best way to feed your baby if you are taking JARDIANCE. Do not breastfeed while taking JARDIANCE. 
>  
>  Tell your healthcare provider about all the medicines you take, including prescription and over-the-counter medicines, vitamins, and herbal supplements. JARDIANCE may affect the way other medicines work, and other medicines may affect how JARDIANCE works. Know the medicines you take. Keep a list of them to show your healthcare provider and pharmacist when you get a new medicine. 
>  
>  
>  
>  How should I take JARDIANCE? 
>  
>  Take JARDIANCE exactly as your healthcare provider tells you to take it. 
>  Take JARDIANCE by mouth 1 time in the morning each day, with or without food. 
>  Your healthcare provider will tell you how much JARDIANCE to take and when to take it. Your healthcare provider may change your dose if needed. 
>  Your healthcare provider may tell you to take JARDIANCE along with other diabetes medicines. Low blood sugar can happen more often when JARDIANCE is taken with certain other diabetes medicines. See " What are the possible side effects of JARDIANCE? " 
>  
>  If you miss a dose, take it as soon as you remember. If it is almost time for your next dose, skip the missed dose and take the medicine at the next regularly scheduled time. Do not take two doses of JARDIANCE at the same time. Talk with your healthcare provider if you have questions about a missed dose. 
>  If you take too much JARDIANCE, call your healthcare provider or Poison Help line at 1-800-222-1222, or go to the nearest hospital emergency room right away. 
>  When taking JARDIANCE, you may have sugar in your urine, which will show up on a urine test. 
>  When your body is under some types of stress, such as fever, trauma (such as a car accident), infection, or surgery, the amount of diabetes medicine you need may change. Tell your healthcare provider right away if you have any of these conditions and follow your healthcare provider's instructions. 
>  Your healthcare provider may do certain blood tests before you start JARDIANCE and during treatment as needed. 
>  
>  
>  
>  
>  
>  What are the possible side effects of JARDIANCE? 
>  
>  JARDIANCE may cause serious side effects, including: 
>  
>  See " What is the most important information I should know about JARDIANCE? " 
>  
>  
>  Genital and urinary tract infections. JARDIANCE can cause serious infections in your genital area or urinary tract that could require hospitalization. A rare but serious bacterial infection called necrotizing fasciitis can cause damage to the tissue under the skin in the area between and around the anus and genitals (perineum). This infection may require hospitalization, multiple surgeries, and could lead to death. Seek medical attention immediately if you have a fever or you are feeling very weak, tired or uncomfortable (malaise), and you develop any of the following symptoms in the area between and around your anus and genitals: 
>  
>  
>  
>  
>  
>  
>  
>  
>  pain or tenderness 
>  
>  
>  
>  
>  swelling 
>  
>  
>  
>  
>  redness of skin (erythema) 
>  
>  
>  
>  
>  
>  Also tell your healthcare provider if you have any of these signs or symptoms of urinary tract infections or yeast infections: 
>  
>  
>  
>  
>  
>  
>  Urinary tract infection: 
>  
>  burning feeling when you urinate 
>  need to urinate often or right away 
>  pain in the lower part of your stomach (pelvis) 
>  blood in your urine 
>  You may also have a fever, back pain, nausea, or vomiting. 
>  
>  Vaginal yeast infection : 
>  vaginal odor 
>  white or yellowish vaginal discharge (may be lumpy or look like cottage cheese) 
>  vaginal itching 
>  
>  
>  
>  Yeast infection of the skin around the penis (balanitis or balanoposthitis): If you are uncircumcised, swelling may make it difficult to pull back the skin around the tip of your penis. Other symptoms include: 
>  
>  
>  
>  
>  
>  
>  
>  
>  redness, itching, or swelling of the penis 
>  bad smelling discharge from the penis 
>  
>  
>  
>  
>  rash on the penis 
>  pain in the skin around the penis 
>  
>  
>  
>  
>  
>  
>  Talk to your healthcare provider about what to do if you get symptoms of a yeast infection. They may suggest you use an over-the-counter antifungal medicine. Contact your healthcare provider right away if your symptoms do not improve after using an over-the-counter antifungal medicine. 
>  
>  
>  
>  
>  
>  Low blood sugar (hypoglycemia). In adults, if you take JARDIANCE with another medicine that can cause low blood sugar, such as a sulfonylurea or insulin, your risk of getting low blood sugar is higher. In children 10 years of age and older, the risk for low blood sugar is higher with JARDIANCE even if you do not use another medicine that can also lower blood sugar. The dose of your sulfonylurea medicine or insulin may need to be lowered while you take JARDIANCE. Signs and symptoms of low blood sugar may include: 
>  
>  
>  
>  
>  
>  
>  
>  headache 
>  drowsiness 
>  weakness 
>  
>  
>  
>  
>  irritability 
>  hunger 
>  fast heartbeat 
>  
>  
>  
>  
>  confusion 
>  shaking or feeling jittery 
>  
>  
>  
>  
>  dizziness 
>  sweating 
>  
>  
>  
>  
>  
>  
>  
>  Amputations. SGLT2 inhibitors may increase your risk of lower limb amputations. 
>  You may be at a higher risk of lower limb amputation if you: 
>  have a history of amputation 
>  have had blocked or narrowed blood vessels, usually in your leg 
>  have had diabetic foot infection, ulcers or sores 
>  
>  Call your healthcare provider right away if you have new pain or tenderness, any sores, ulcers, or infections in your leg or foot. Talk to your healthcare provider about proper foot care. 
>  
>  Serious allergic reactions. If you have any symptoms of a serious allergic reaction, stop taking JARDIANCE and call your healthcare provider right away or go to the nearest hospital emergency room. See " Who should not take JARDIANCE? " . 
>  
>  The most common side effects of JARDIANCE include: 
>  
>  urinary tract infections 
>  yeast infections in females 
>  These are not all the possible side effects of JARDIANCE. For more information, ask your healthcare provider or pharmacist. Call your doctor for medical advice about side effects. You may report side effects to FDA at 1-800-FDA-1088. 
>  
>  
>  
>  How should I store JARDIANCE? 
>  
>  Store JARDIANCE at room temperature between 68°F to 77°F (20°C to 25°C). 
>  
>  Keep JARDIANCE and all medicines out of the reach of children. 
>  
>  
>  
>  
>  
>  
>  General information about the safe and effective use of JARDIANCE. 
>  Medicines are sometimes prescribed for purposes other than those listed in a Medication Guide. Do not use JARDIANCE for a condition for which it is not prescribed. Do not give JARDIANCE to other people, even if they have the same symptoms you have. It may harm them. You can ask your pharmacist or healthcare provider for information about JARDIANCE that is written for health professionals. 
>  
>  
>  
>  What are the ingredients in JARDIANCE? 
>  
>  Active Ingredient: empagliflozin 
>  Inactive Ingredients: colloidal silicon dioxide, croscarmellose sodium, hydroxypropyl cellulose, lactose monohydrate, magnesium stearate, and microcrystalline cellulose. In addition, the film coating contains the following inactive ingredients: ferric oxide yellow, hypromellose, polyethylene glycol, talc, and titanium dioxide. Distributed by: Boehringer Ingelheim Pharmaceuticals, Inc., Ridgefield, CT 06877 USA Licensed from: Boehringer Ingelheim International GmbH, Ingelheim, Germany JARDIANCE is a registered trademark of and used under license from Boehringer Ingelheim International GmbH. Boehringer Ingelheim Pharmaceuticals, Inc. either owns or uses the EMPA-REG OUTCOME ® , EMPEROR-Reduced ® , EMPEROR-Preserved ® , and EMPA-KIDNEY ® trademarks under license. The other brands listed are trademarks of their respective owners and are not trademarks of Boehringer Ingelheim Pharmaceuticals, Inc. Copyright © 2026 Boehringer Ingelheim International GmbH ALL RIGHTS RESERVED COL8914QA062026 For more information about JARDIANCE, including current prescribing information and Medication Guide, go to www.jardiance.com , scan the code, or call Boehringer Ingelheim Pharmaceuticals, Inc. at 1-800-542-6257.

## Limitations and pending checks

- Standardized generic-name fields may be missing. Phrase matching does not guarantee complete or accurate drug identification.
- Only the selected event term is queried; a complete synonym or related-term set is not included.
- openFDA documentation states that only the latest version of a report is returned. Duplicate cases across different report identifiers have not been independently addressed.
- receivedate is the first FDA receipt date, not event onset. Current report contents may include updates after the selected years; this is not a historical frozen snapshot.
- Separate API requests are not an atomic snapshot; database updates may affect consistency.
- Confidence intervals depend on the independent-count, large-sample approximation and do not capture systematic reporting biases.
- Current labeling does not establish historical label content during the analysis years.
- Keyword absence does not establish risk absence. XML extraction may lose table formatting; check the original label.
- Complete event harmonization remains pending. Auxiliary source availability is reported below when evidence is supplied.
- Primary results use a fixed template. Any separately included model synthesis requires human review.
- Saved count responses permit statistical recalculation, but are not a snapshot of all FAERS reports. A future API query may yield different counts.
- Original source-specific notes and definitions are preserved verbatim in the input JSON copies, including their original language.

## Auxiliary evidence

These sources provide context and do not change the FAERS contingency table. Search results require relevance review.

| Source | Status |
|---|---|
| clinical_trials | completed |
| drugsfda | completed |
| sider | completed |

### clinical_trials

Status: **completed**.

Source: https://clinicaltrials.gov/api/v2/studies?query.intr=empagliflozin&pageSize=5&format=json&countTotal=true

Retrieved studies: 5. Only the first search page was requested; this is not a systematic review.

Eligibility criteria describe permitted enrollment, not observed participant characteristics. Enrollment counts retain their registry type (for example, ESTIMATED or ACTUAL).

| NCT ID | Study | Age range | Sex | Healthy volunteers | Enrollment / type |
|---|---|---|---|---|---|
| NCT06933355 | Acute Effects of SGLT2 Inhibitor on Kidney Allograft Oxygen Tension | 18 Years to Not reported | ALL | No | 8 / ESTIMATED |
| NCT06308679 | A Bioequivalence Study of Two Formulations of 10-mg Empagliflozin Tablets in Healthy Thai Volunteers Under Fasting Conditions | 18 Years to 55 Years | ALL | Yes | 28 / ESTIMATED |
| NCT05879276 | Effect at 3 Months of Early Empagliflozin Initiation in Cardiogenic Shock Patients on Mortality, Rehospitalization, Left Ventricular Ejection Fraction and Renal Function. | 18 Years to Not reported | ALL | No | 164 / ESTIMATED |
| NCT01001962 | Double Blind Placebo Study of JARDIANCE® (Empagliflozin) in Prehypertensives Type II Diabetics | 45 Years to 65 Years | ALL | No | 1054 / ESTIMATED |
| NCT06065280 | Sodium-glucose Transport 2 Inhibitors (SGLT2i) in HFrEF Patients | 18 Years to 80 Years | ALL | No | 80 / ACTUAL |

**NCT06933355: intervention and eligibility excerpts**

- Interventions: JARDIANCE 25mg; Placebo
- Eligibility excerpt: Inclusion Criteria: * Male or female patients, age ≥ 18 years. * Non-diabetic kidney transplant recipients * \&gt; 6 months post-transplant * Stable eGFR\&gt; 20 ml/min (defined as eGFR 20 ml/min ± 5 ml/min variation in the last 3 months) * Immunosuppressive: Tacrolimus (Adport) and Mycophenolatmofetil (Myfenax/Cellcept/Mycophenolatmofetil) * Capable of lying in a MR-scanner * Capable of providing a signed informed consent and comply with study requirements. * Negativ pregnancy test Exclusion Criteria: * Diabetic kidney disease type 1 or 2 (World Health Organization (WHO) criteria) * Hemogl [Excerpt truncated; see evidence.json.]

**NCT06308679: intervention and eligibility excerpts**

- Interventions: Empagliflozin 10 mg tablets; JARDIANCE®
- Eligibility excerpt: Inclusion Criteria: 1. Thai male and/or female age between 18-55 years 2. Has body mass index (BMI) between 18.0-30.0 kg/m2 3. Has been determined healthy by physical examination, assessment of medical history, and vital signs (blood pressure (systolic blood pressure not lower than 90 or not over 139 mmHg, diastolic blood pressure not lower than 60 or not over 89 mmHg), body temperature, pulse rate, respiratory rate) or showing no clinically significant abnormalities in the opinion of principal investigator or designated physicians 4. Has normal or acceptable results (being assessed as not cl [Excerpt truncated; see evidence.json.]

**NCT05879276: intervention and eligibility excerpts**

- Interventions: Empagliflozin 10 MG
- Eligibility excerpt: Inclusion Criteria: * Adult patients hospitalized in critical cardiac unit care or Intensive care unit for a cardiogenic shock * "Who must have been or is on catecholamines for at least 12 hours for the treatment of cardiogenic shock. * Patients who are able to take oral tablets Exclusion Criteria: * GFR\&lt; 20 ml/min/1.73m2. * Chronic dialysis. * Patient on SGLT2 inhibitors prior to admission to ICU or CCU. * Known allergy to SGLT2 inhibitors or to any of its excipients (in particular, patients with hereditary disorders of galactose intolerance, total lactase deficiency or glucose or galacto [Excerpt truncated; see evidence.json.]

**NCT01001962: intervention and eligibility excerpts**

- Interventions: empagliflozin; Metformin
- Eligibility excerpt: Inclusion criteria 1. Age between 45 and 65 years. 2. All patients are going to give their informed consent to participate in the study. 3. Patients who are not receiving antihypertensive or diabetes treatment (newly diagnosed diabetics) 4. BP between 130 to 140 mmHg for systolic BP (prehypertensives) 5. Type II diabetes (HbA1c 7.0-8.0) Exclusion criteria 1. Known oversensitiveness 2. chronic renal disease (GFR\&lt;60 ml/min) or ESRD 3. heart or respiratory failure, recent MI, shock 4. pregnancy or lactation.

**NCT06065280: intervention and eligibility excerpts**

- Interventions: Empagliflozin 10 MG; Dapagliflozin 10 MG
- Eligibility excerpt: Inclusion criteria: * Patients with HFrEF, on optimal medical therapy according to European Society of Cardiology guidelines, * an age of at least 18 years, * an ejection fraction of 40% or less, with New York Heart Association (NYHA) class II - IV symptoms will be eligible for the study. Exclusion criteria: * Recent treatment with or unacceptable side effects associated with an SGLT2i * Type-I diabetes mellitus, * Symptoms of hypotension or a systolic blood pressure of less than 95 mm Hg, * Severe CKD and an estimated glomerular filtration rate (eGFR) below 30 ml per minute per 1.73 m2 of [Excerpt truncated; see evidence.json.]

- Only the first 5 search results are retrieved, not a systematic review. Verify intervention relevance. Eligibility criteria do not describe the actual enrolled population.

### drugsfda

Status: **completed**.

Source: https://api.fda.gov/drug/drugsfda.json?search=products.active_ingredients.name%3A%22empagliflozin%22&limit=5

Retrieved application records: 5. These may contain multiple products and combination formulations; this is not a complete approval history.

| Application | Sponsor | Product number | Brand | Active ingredients / strengths | Dosage form / route | Marketing status (as returned) |
|---|---|---|---|---|---|---|
| ANDA212138 | ZYDUS PHARMS | 002 | EMPAGLIFLOZIN | EMPAGLIFLOZIN (25MG) | TABLET | Discontinued |
| ANDA212138 | ZYDUS PHARMS | 001 | EMPAGLIFLOZIN | EMPAGLIFLOZIN (10MG) | TABLET | Discontinued |
| ANDA212198 | ZYDUS PHARMS | 004 | EMPAGLIFLOZIN AND METFORMIN HYDROCHLORIDE | EMPAGLIFLOZIN (12.5MG); METFORMIN HYDROCHLORIDE (1GM) | TABLET | Discontinued |
| ANDA212198 | ZYDUS PHARMS | 002 | EMPAGLIFLOZIN AND METFORMIN HYDROCHLORIDE | EMPAGLIFLOZIN (5MG); METFORMIN HYDROCHLORIDE (1GM) | TABLET | Discontinued |
| ANDA212198 | ZYDUS PHARMS | 003 | EMPAGLIFLOZIN AND METFORMIN HYDROCHLORIDE | EMPAGLIFLOZIN (12.5MG); METFORMIN HYDROCHLORIDE (500MG) | TABLET | Discontinued |
| ANDA212198 | ZYDUS PHARMS | 001 | EMPAGLIFLOZIN AND METFORMIN HYDROCHLORIDE | EMPAGLIFLOZIN (5MG); METFORMIN HYDROCHLORIDE (500MG) | TABLET | Discontinued |
| ANDA213654 | LUPIN LTD | 003 | EMPAGLIFLOZIN;METFORMIN HYDROCHLORIDE | EMPAGLIFLOZIN (12.5MG); METFORMIN HYDROCHLORIDE (1GM) | TABLET, EXTENDED RELEASE | None (Tentative Approval) |
| ANDA213654 | LUPIN LTD | 001 | EMPAGLIFLOZIN;METFORMIN HYDROCHLORIDE | EMPAGLIFLOZIN (5MG); METFORMIN HYDROCHLORIDE (1GM) | TABLET, EXTENDED RELEASE | None (Tentative Approval) |
| ANDA213654 | LUPIN LTD | 004 | EMPAGLIFLOZIN;METFORMIN HYDROCHLORIDE | EMPAGLIFLOZIN (25MG); METFORMIN HYDROCHLORIDE (1GM) | TABLET, EXTENDED RELEASE | None (Tentative Approval) |
| ANDA213654 | LUPIN LTD | 002 | EMPAGLIFLOZIN;METFORMIN HYDROCHLORIDE | EMPAGLIFLOZIN (10MG); METFORMIN HYDROCHLORIDE (1GM) | TABLET, EXTENDED RELEASE | None (Tentative Approval) |
| ANDA220511 | AJANTA PHARMA LTD | 004 | EMPAGLIFLOZIN AND METFORMIN HYDROCHLORIDE | EMPAGLIFLOZIN, METFORMIN HYDROCHLORIDE (25MG/1000MG) | TABLET, EXTENDED RELEASE | None (Tentative Approval) |
| ANDA220511 | AJANTA PHARMA LTD | 002 | EMPAGLIFLOZIN AND METFORMIN HYDROCHLORIDE | EMPAGLIFLOZIN, METFORMIN HYDROCHLORIDE (10MG/1000MG) | TABLET, EXTENDED RELEASE | None (Tentative Approval) |
| ANDA220511 | AJANTA PHARMA LTD | 003 | EMPAGLIFLOZIN AND METFORMIN HYDROCHLORIDE | EMPAGLIFLOZIN, METFORMIN HYDROCHLORIDE (12.5MG/1000MG) | TABLET, EXTENDED RELEASE | None (Tentative Approval) |
| ANDA220511 | AJANTA PHARMA LTD | 001 | EMPAGLIFLOZIN AND METFORMIN HYDROCHLORIDE | EMPAGLIFLOZIN, METFORMIN HYDROCHLORIDE (5MG/1000MG) | TABLET, EXTENDED RELEASE | None (Tentative Approval) |
| NDA206111 | BOEHRINGER INGELHEIM | 004 | SYNJARDY | EMPAGLIFLOZIN (12.5MG); METFORMIN HYDROCHLORIDE (1GM) | TABLET | Prescription |
| NDA206111 | BOEHRINGER INGELHEIM | 002 | SYNJARDY | EMPAGLIFLOZIN (5MG); METFORMIN HYDROCHLORIDE (1GM) | TABLET | Prescription |
| NDA206111 | BOEHRINGER INGELHEIM | 003 | SYNJARDY | EMPAGLIFLOZIN (12.5MG); METFORMIN HYDROCHLORIDE (500MG) | TABLET | Prescription |
| NDA206111 | BOEHRINGER INGELHEIM | 001 | SYNJARDY | EMPAGLIFLOZIN (5MG); METFORMIN HYDROCHLORIDE (500MG) | TABLET | Prescription |

Application and product fields are reproduced from Drugs@FDA; they do not independently establish current availability or a complete regulatory timeline.

- Only the first 5 application records are retrieved. Results may include combination products and are not a complete approval history or full prescribing label.

### sider

Status: **completed**.

Drug matching: matched.
Matching event records: 0.

SIDER is label-derived evidence. An unmatched drug or an absent event match is not proof of no risk.

**Identifier coverage and event-term diagnostic**

| Check | Result |
|---|---|
| Compound IDs matched by drug name | CID111949646 |
| Side-effect rows for these IDs | 95 |
| Flat-ID matched rows | 95 |
| Stereo-ID matched rows | 0 |
| PT rows for these IDs | 52 |
| Distinct PT terms for these IDs | 50 |
| Requested event term | Diabetic ketoacidosis |
| Exact event rows for this drug | 0 |
| Dataset-wide exact event rows (vocabulary check only) | 13 |
| Candidate-search keywords | ketoacidosis, ketoacid, ketosis |
| Candidate PT terms for this drug | 0 |
| Diagnostic finding | exact_event_unmatched_no_keyword_candidates |

Counts are database rows or distinct terms, not patients. Flat-ID and stereo-ID counts may overlap. Dataset-wide event rows are not a comparator for risk.

The drug has PT records in these files, but neither the exact event nor the specified keyword candidates matched. This is a dataset-specific lookup result, not evidence that the clinical risk is absent.



Dataset version: unverified_release.
Dataset source: https://sideeffects.embl.de/download/

- Exact generic-name and specified PT matching is used. No match does not establish absence of risk.
- Keyword candidates are diagnostic only, not validated synonyms; they do not change the formal event definition.
- SIDER is label-derived evidence, not independent confirmation of causality.
- Dataset release remains as recorded in the manifest; local hashes do not independently verify a publisher release.

Full source responses, including unabridged eligibility criteria and application products, are retained in evidence.json.


## Reproduction

The analysis directory preserves source JSON files and provenance.json. Label evidence is stored as label.json in standalone reports, or label_result.json in workflow runs.
Re-run faers_stats.py using the copied audit.json. cohort.yaml preserves the versioned analysis definition.
Software: Python standard library; build_report.py and faers_stats.py.

## Gemini auxiliary synthesis

Status:skipped. The fixed-template report and statistics are retained.
