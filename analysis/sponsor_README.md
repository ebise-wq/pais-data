# Drug trials by sponsor type (commercial vs other)

Scripts: `clinicaltrials/sponsor_class.py` (fetch, one row per trial) → `analysis/sponsor_summary.py`
(tables) → `analysis/sponsor_charts.py` (charts). Pulled 25 Nov 2026 from the ClinicalTrials.gov API v2.

- **Commercial** = lead sponsor class `INDUSTRY`. **Other** = every other class (universities, hospitals,
  charities, NIH and other government, networks, individuals).
- **Trials**: interventional with a drug, biological or genetic arm, start year 2020–2026.
  Long COVID, ME/CFS, schizophrenia and epilepsy use the NCT IDs in `nct_ids_2026-11-08.json` (same as the
  drug-trial chart). The other 22 comparators use the queries in `expanded/diseases.py`.
- **Comparators**: the 24 causes in `expanded/burden_vs_research_expanded_2021-2025.csv` with 10–30M
  DALYs (GBD 2023). Long COVID (19.8M) and all ME/CFS (17.5M) are in the same range (ME/CFS model v11.2).
- `large_pharma_led`: commercial trials whose lead sponsor matches one of the ~20 largest drug companies
  (name regex in `sponsor_summary.py`; approximate).

Files: `clinicaltrials/sponsor_trials_2026-11-25.csv`, `sponsor_by_disease_2021-2025.csv`,
`sponsor_by_year_2020-2026.csv`, `drug_trials_per_year.png`, `sponsor_per_year.png`, `sponsor_comparison.png`.
`drug_trials_per_year.png` and `sponsor_per_year.png` are the same chart with the same layout, without and
with the sponsor split. `all_trials_per_year.png` uses the same layout for all interventional trials
(from `clinicaltrials/trials_per_year_2026-11-08.csv`), so the catalog page can switch between all three. Their long COVID and ME/CFS
counts for 2020–2026 match the earlier separate pull of 11 Nov 2026 year by year.

## Results, 2021–2025

| | Drug trials | Commercial | Share | Large pharma | Commercial / yr | Other / yr |
|---|---|---|---|---|---|---|
| Long COVID | 141 | 32 | 23% | 0 | 6.4 | 21.8 |
| ME/CFS | 13 | 1 | 8% | 0 | 0.2 | 2.4 |
| 24 comparators, median | | | 35% | | 23.0 | 19.2 |
| 16 non-cancer comparators, median | | | 41% | | 4.1 | 13.8 |

- Long COVID ranks 20th of 26 on commercial share. Below it: opioid and alcohol use disorders, neonatal
  sepsis, ME/CFS, congenital and rheumatic heart disease.
- ME/CFS has 1 commercial drug trial in 2021–2025 (a Chinese herbal granule, Heilongjiang Quanle, phase 4).
  Only neonatal sepsis (0.2/yr) and rheumatic heart disease (0) are as low.
- None of the 39 commercial long COVID drug trials (2020–2026) is led by a large drug company. Sponsors are
  small biotechs (e.g. argenx, Tonix, AIM ImmunoTech, Berlin Cures, ImmunityBio, Invivyd), stem-cell
  companies and supplement firms.
- Trend: the long COVID commercial share fell from 37% (17/46) in 2021–22 to 16% (15/95) in 2023–25
  (Fisher p = 0.009, but the split was chosen after looking at the data). Commercial counts fell from
  8–9 a year to 3–4. Pooled comparators stayed at 34–39% each year.

## Caveats

- Lead sponsor only. 10 long COVID trials led by universities list a company as collaborator (often drug
  supply, e.g. Pfizer for Paxlovid). Counting those would raise the share to about 30%.
- Lead sponsor can hide company funding. Cortene's CT38 ME/CFS trial (NCT03613129) lists the site PI as lead
  sponsor and no company. It is corrected to commercial in `OVERRIDES` in `sponsor_class.py`. It started in
  2018, so it falls outside 2020–2026 and changes no number here.
- "Commercial" covers very different firms, from large pharma to supplement makers and stem-cell clinics.
- Vaccine trials count as biologics. This pushes up pertussis, meningitis and hepatitis B.
- Many cancer trials are led by Chinese hospitals (class OTHER), which lowers cancer commercial shares.
- ClinicalTrials.gov only. ME/CFS counts are small, so its share is very uncertain (1 of 13).
