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
