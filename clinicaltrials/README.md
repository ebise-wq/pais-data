# ClinicalTrials.gov study counts by condition

Pulled 2026-11-08 from the ClinicalTrials.gov API v2 with `fetch_counts.py`.

Method: query `query.cond` for each disease, then keep only studies where a listed
condition (or, for ME/CFS, long COVID, celiac, POTS, Gulf War illness and Lyme, the title)
matches a disease regex. This drops loose matches such as cancer fatigue tagged with the
MeSH term "Fatigue Syndrome, Chronic", acute COVID studies, and celiac plexus nerve blocks.

Columns: `studies` = all registered studies (any type); `interventional` = trials;
`randomized`; `drug_or_biologic` = interventional with a drug, biological or genetic arm;
`phase2_or_3_drug` / `phase3_drug`; `industry_led` = lead sponsor class INDUSTRY.

Limits: ClinicalTrials.gov only (no EU CTR, ISRCTN, ChiCTR etc.). Regex filtering is
imperfect in both directions. 35 studies are counted under both ME/CFS and long COVID.

`trials_per_year_*.csv` (from `trials_per_year.py`): interventional studies per start year,
1996–2026. Registration only became expected in 2005 (ICMJE) and required for many US trials
from 2007 (FDAAA), so years before about 2005–2008 are badly undercounted. 2026 is a partial year.

## Check of the ME/CFS drug-trial counts (11 Nov 2026)

ME/CFS drug or biologic trials look low (13 starting in 2021–2025), so they were checked:
- A broad full-text search (all fields, interventional, start 2021–2025) found no ME/CFS drug trial
  that the selection missed. The missed drug trials were on other conditions, or were labelled
  "post-viral" or "post-COVID fatigue" rather than ME/CFS.
- The filter does not match the inverted MeSH form "Fatigue Syndrome, Chronic" when the title has no
  ME/CFS term. That drops 43 studies (all years). Almost none are ME/CFS: they use the term for general
  fatigue in cancer, MS, iron deficiency and similar. The only drug trials among them (testosterone in
  cancer survivors, iron therapy) are not ME/CFS, so the filter was left as it is.
- If anything, "drug or biologic" is generous for ME/CFS. The 13 include a PET tracer imaging study,
  a probiotic, vitamin B1, a stellate ganglion block and two herbal products. Supplement and medical-food
  trials (oxaloacetate, melatonin + zinc, hydrogen water) are registered as dietary supplement or
  other, so they are not counted.
