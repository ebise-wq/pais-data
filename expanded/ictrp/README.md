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
