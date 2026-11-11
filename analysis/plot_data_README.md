# plot_data_2021-2025.csv

Data behind the "Papers vs disease burden" and "Trials vs disease burden" scatterplots.
Made by `shortfall_ccc.py` (pais-data repo, `analysis/`). One row per disease or group.

## Rows

- 13 `comparator` rows: diseases with a GBD 2023 cause (global, both sexes, all ages, 2023).
  These define the trend line.
- 4 `ME/CFS or long COVID group` rows: burden from the ME/CFS Burden model v11.2, CCC criteria,
  year 2026 (median and 90% range). Not used in the trend. The plots show only
  "All ME/CFS (classic + post-COVID)".

## Columns

| Column | Meaning |
|---|---|
| `label` | Disease or group |
| `kind` | `comparator` or `ME/CFS or long COVID group` |
| `burden_source` | Where the DALYs come from (GBD cause name, or the model) |
| `interval` | `95% UI` (GBD) or `90% range` (model) |
| `dalys`, `dalys_low`, `dalys_high` | DALYs per year: point estimate and interval |
| `papers_per_year` | PubMed papers with the disease in the title, by date added to PubMed, 2021–2025 average |
| `trials_per_year` | Interventional ClinicalTrials.gov studies by start year, 2021–2025 average |
| `papers_trend`, `trials_trend` | Value of the trend line at this row's `dalys` |
| `papers_shortfall`, `trials_shortfall` | trend ÷ actual. Above 1 = fewer than the trend predicts |
| `*_shortfall_p5`, `*_shortfall_p95` | Groups only: 90% range of the shortfall, combining burden uncertainty (lognormal fitted to the 90% range) and trend-fit uncertainty (4,000 bootstrap resamples of the 13 comparators) |

## Trend line

Least squares on log10 values, fitted to the 13 comparators:
`log10(count) = a + b × log10(DALYs)`

| | a | b | R² |
|---|---|---|---|
| Papers | 1.1716 | 0.3412 | 0.500 |
| Trials | 0.4624 | 0.2309 | 0.299 |

## How the ME/CFS and long COVID counts are built

- All ME/CFS: every paper or trial with ME/CFS in the title (includes ones that also name long COVID).
- Classic ME/CFS: All ME/CFS minus papers or trials that also name long COVID
  (2021–2025: 150 papers, 19 trials).
- Long COVID: the long COVID search.
- Long COVID + classic ME/CFS: long COVID + classic ME/CFS (overlap counted once).

## Caveats

- Comparator DALYs are for 2023 (GBD); the ME/CFS model is for 2026.
- Post-COVID ME/CFS papers titled only "long COVID" are not in the ME/CFS count, so All ME/CFS
  papers are a slight undercount (shortfall slightly overstated).
- Epilepsy search includes "seizure*", so its counts run high.
- ClinicalTrials.gov only; no other trial registries.
- With 13 points and R² of 0.50 (papers) and 0.30 (trials), the trend is rough.

Plot settings used (v15): both axes log10; x 3×10⁵ to 6×10⁷ DALYs; y 70 to 14,000 (papers),
5 to 420 (trials).
