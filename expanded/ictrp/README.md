# Trials in all registries (WHO ICTRP) vs ClinicalTrials.gov

ClinicalTrials.gov misses trials registered only in other registries (Pan African, India, China,
Iran, Australia/NZ, EU and others). WHO's ICTRP search portal combines them.

- `search_strings.txt`: the five ICTRP condition searches (search 4 is saved as `raw/export4`) (registration date 2019–2026, all statuses).
  `search_strings_1_split.txt` splits search 1 in case an export is too large (not needed in the end).
- `raw/export<N>.xml.gz`: the XML exports, downloaded by hand from trialsearch.who.int (the export
  button did not work for automated access). Data: WHO International Clinical Trials Registry
  Platform (ICTRP), exported 2026-11-19. ICTRP terms: attribute WHO ICTRP, show the processing date,
  no commercial use.
- `analyse_ictrp.py` → `ictrp_vs_ctgov_2021-2025.csv` (31 diseases) and `mecfs_shortfall_adjusted.csv`.

Method: interventional trials only; start year 2021–2025 (registration year if no usable start
date); a listed condition must match the same regex as the ClinicalTrials.gov counts; records that
cite an NCT number, or repeat a title already counted, are dropped as duplicates.

`ratio_all_to_ctgov` compares all registries with the ClinicalTrials.gov records *within the same
ICTRP export*, so both sides use the same search and dates. The ICTRP copy of ClinicalTrials.gov
gives somewhat fewer trials than the ClinicalTrials.gov API (different search and date fields),
so use the ratio rather than mixing the two sources.

## Results

How many more trials all registries hold than ClinicalTrials.gov (interventional, started 2021–2025):

| Disease | All registries ÷ ClinicalTrials.gov | Without ChiCTR and ITMCTR |
|---|---|---|
| Crohn's disease | 1.2× | 1.2× |
| Sickle cell disease | 1.3× | 1.3× |
| Hepatitis C | 1.4× | 1.3× |
| MS | 1.6× | 1.6× |
| ALS | 1.6× | 1.4× |
| Malaria | 1.8× | 1.8× |
| Glaucoma | 1.9× | 1.7× |
| Bipolar disorder | 2.2× | 2.0× |
| Tuberculosis | 2.4× | 1.9× |
| **ME/CFS** | **2.5×** | **1.8×** |
| Endometriosis | 2.6× | 2.3× |
| Polycystic ovary syndrome | 2.8× | 1.9× |
| Rheumatoid arthritis | 3.0× | 2.6× |
| Gout | 3.2× | 2.6× |
| Leprosy | 5.4× | 5.4× |

Median of the 18 diseases with at least 20 ClinicalTrials.gov trials: 1.9× (1.8× without the two
Chinese registries).

Effect on ME/CFS: the trial shortfall from `../fits_2021-2025.csv` (7.7× below the 120-disease trend)
is scaled by (comparator ratio ÷ ME/CFS ratio), assuming the 120 diseases gain like these 30.

- All registries: about **5.8×** below the trend (5.9× against the 6 original comparators covered).
- Without ChiCTR and ITMCTR for every disease: about **7.7×** (7.9×).

ME/CFS gains more than most diseases only because of the two Chinese registries, which hold many
traditional-medicine trials labelled "chronic fatigue syndrome". So the trial shortfall is about
6–8× whichever way it is counted, against 7.7× from ClinicalTrials.gov alone.

## Caveats

- Some matches are off-target: a trial whose condition list mentions the disease but which is about
  something else (for ME/CFS: a cancer fatigue study, a POTS prevalence study). Not hand-cleaned.
- For ME/CFS, 28 of the 58 extra trials are Chinese traditional-medicine trials (tuina,
  moxibustion, tai chi, herbal formulas) labelled "chronic fatigue syndrome". Diagnostic criteria
  in these trials are often unclear.
- Duplicates filed in two registries with different titles and no cross-reference are still counted twice.

## Diagnostic criteria in ME/CFS trials

`mecfs_trial_criteria.csv`: every interventional "ME/CFS" trial (start 2021–2025) counted above,
classified by the inclusion criteria (automatic tagging, then corrected by hand after reading each
entry). Unique trials (duplicates across registries removed):

| Criteria | ClinicalTrials.gov | Other registries | Chinese registries |
|---|---|---|---|
| PEM required (CCC, ICC, IOM 2015, NICE 2021) | 23 | 10 | 1 |
| Fukuda / CDC (PEM optional) | 3 | 0 | 6 |
| Oxford (fatigue only) | 1 | 0 | 0 |
| Other definition (questionnaire, bodily distress) | 2 | 1 | 0 |
| ME/CFS diagnosis, criteria not named | 9 | 6 | 20 |
| Not public yet | 0 | 1 | 0 |
| Not an ME/CFS population | 13 | 11 | 0 |
| Total | 51 | 29 | 27 |

"Not an ME/CFS population": the condition list names chronic fatigue syndrome, but the trial
enrols someone else (cancer or ICU fatigue, fibromyalgia, long COVID by WHO or NICE definitions,
POTS, tick-attributed illness, soldiers, football players). 8 Chinese-registry trials and 2 on
ClinicalTrials.gov also required a traditional Chinese medicine syndrome diagnosis.

The comparison diseases were not checked this way, so the off-target share elsewhere is unknown.

### Comparison with MS and rheumatoid arthritis

`ms_ra_trial_sample.csv`: a random sample of 60 ClinicalTrials.gov trials each for MS (of 734) and
rheumatoid arthritis (of 393), interventional, start 2021–2025 (random seed 261455), read and
classified by hand. The 51 ME/CFS trials were sorted into the same three groups (the mixed
group includes ME/CFS + fibromyalgia trials and long COVID trials that also take ME/CFS patients).

| | ME/CFS (all 51) | MS (sample of 60) | RA (sample of 60) |
|---|---|---|---|
| Mainly patients with the disease | 36 (71%) | 50 (83%) | 37 (62%) |
| Mixed population, disease one of several | 6 | 9 | 18 |
| Not the disease (healthy volunteers, other fatigue, etc.) | 9 | 1 | 5 |
| Not mainly the disease, % (95% CI) | 29% (19–43) | 17% (9–28) | 38% (27–51) |
| Named diagnostic criteria, among trials mainly in the disease | 27 of 36 (75%)¹ | 18 of 50 (36%) | 27 of 37 (73%) |

¹ 23 used criteria that require PEM; the rest Fukuda or Oxford.

ME/CFS sits between MS and RA. Off-target trials inflate the comparison diseases' counts about as
much as ME/CFS's, so removing them would not change the ME/CFS shortfall much. MS trials name their
diagnostic criteria (McDonald) less often than ME/CFS trials do; many say only "diagnosed by a
neurologist". The Chinese-registry ME/CFS trials (1 of 27 requiring PEM, 20 naming no criteria)
are the outlier, not ME/CFS trials in general.
