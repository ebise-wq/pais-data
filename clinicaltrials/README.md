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

`IBD` is a separate row: any study whose listed conditions name Crohn's, ulcerative colitis or
inflammatory bowel disease in general, counted once. It is not the sum of the Crohn's and UC rows
(527 studies are listed under both). Pulled 2026-11-09.
