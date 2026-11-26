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

`per_year_interactive.html`: the interactive chart on the catalog page ("Papers and trials per year,
131 diseases"). It reads `trials_per_year_*.csv` and `../pubmed/pubs_per_year_long_*.csv` (the `title`
column) for these 24 diseases, `../expanded/per_year_*.csv` for the other 107 of the 120 diseases
(it skips the 4 causes left out of that comparison), and
DALYs from `../expanded/burden_interactive_2021-2025.json` (GBD 2023; ME/CFS 17.5M and long COVID
19.8M from the ME/CFS model, as in the 120-disease comparison). Fibromyalgia, POTS, Gulf War illness,
Sjögren's, lupus, celiac disease, IBS, post-treatment Lyme and cystic fibrosis are not GBD causes, so
they have no DALYs. It shows 1996–2025, since 2026 is a partial year. The two sources were pulled on
different dates (8 and 26 Nov 2026) with their own searches, so the 24 and the 111 are comparable in
method but not identical in query style. The chart opens on a linear scale (v3, at the user's request); log is a
button away.

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
