# Burden vs research with 120 diseases

This extends `../analysis/` from 13 comparator diseases to 120. The 107 new ones are GBD 2023 causes
(level 3 or 4) with a name a title search can find. Papers and trials use the same method as before.

Four more causes were fetched but are left out (`EXCLUDE` in `analyse.py`): conduct disorder,
tension-type headache, low back pain and neck pain. Their diagnoses are loosely bounded, and research on
them is spread across many labels, so a title search misses most of it. For example, wider searches
raised conduct disorder from 68 to 159–296 papers a year, and tension-type headache from 53 to 121–695.
Including them made ME/CFS look closer to the bottom of the ranking than it is.

## Files

- `diseases.py`: the 111 fetched causes (107 used). Each has its GBD cause name(s), a PubMed title query, a
  ClinicalTrials.gov condition query, and a regex that a listed condition must match.
- `fetch.py`: pulls papers per year (PubMed, title search, by `[edat]`) and interventional trials per
  start year (ClinicalTrials.gov), 2021–2025. Writes `counts_<date>.csv` and `queries_<date>.csv`.
  Raw API pages go to `cache/` (not committed).
- `analyse.py`: joins counts to GBD DALYs, adds the 13 original comparators and ME/CFS from
  `../analysis/plot_data_2021-2025.csv`, fits trends and draws the plots.
- `burden_vs_research_expanded_2021-2025.csv`: one row per disease. `*_trend` is the value of the
  120-disease trend at that disease's DALYs. `*_shortfall` = trend ÷ actual; above 1 means fewer
  papers or trials than the trend predicts. Sorted by paper shortfall.
- `fits_2021-2025.csv`: log-log fits for several subsets, with the ME/CFS shortfall under each.
- `papers_vs_dalys_expanded.png`, `trials_vs_dalys_expanded.png`.

Run from the repo root: `python3 -I expanded/fetch.py`, then `python3 -I expanded/analyse.py`.

## Check against the old pipeline

The new code reproduces the old MS counts: 16,435 papers 2021–2025 (the same number) and 737 trials
(734 three days earlier).

## Results (pulled 2026-11-11, 120 diseases)

| Set | n | Papers slope | Papers R² | ME/CFS papers shortfall | Trials slope | Trials R² | ME/CFS trials shortfall |
|---|---|---|---|---|---|---|---|
| Original 13 | 13 | 0.34 | 0.50 | 20.3× (12.4–29.8) | 0.23 | 0.30 | 13.4× (8.9–18.9) |
| All | 120 | 0.45 | 0.39 | 10.3× (7.5–14.5) | 0.60 | 0.38 | 7.7× (5.0–11.7) |
| All except cancers | 100 | 0.41 | 0.38 | 8.1× (5.9–11.2) | 0.55 | 0.37 | 5.6× (3.7–8.5) |
| Non-cancer chronic (NCD) | 61 | 0.34 | 0.31 | 10.6× (7.8–14.3) | 0.38 | 0.33 | 9.3× (6.8–12.7) |

Ranges: 90% interval from ME/CFS burden uncertainty (CCC, model v11.2) and trend uncertainty
(4,000 bootstrap resamples).

- The 13 original diseases sit above the broader trend. Most are well-funded chronic diseases (MS,
  Parkinson's, Crohn's, HIV). So the old 20× and 13× were measured against a high bar. Against all
  120 diseases ME/CFS is about 10× below on papers and 7.7× below on trials.
- The scatter is much wider: residual SD 0.45 log10 for papers (a factor of about 3), against 0.21 for the
  13. One trend line is a rough summary.
- Rank is a steadier measure than the multiple. On papers, ME/CFS falls further below the trend than
  119 of the 120 diseases. Only neonatal encephalopathy (birth asphyxia) falls further. Among the 61
  non-cancer chronic diseases, none falls further. On trials, 13 of 120 fall further below, mostly
  tropical, childhood and newborn infections.

### Diseases far below the trend

Papers: neonatal encephalopathy (12×), rheumatic heart disease (10×), neonatal sepsis (9×),
ascariasis, scabies, lymphatic filariasis, onchocerciasis, typhoid, pertussis (7–9×).

Trials: lymphatic filariasis (30×), cysticercosis (26×), measles (25×), food-borne trematodes (24×),
neonatal sepsis (18×), ascariasis, rheumatic heart disease, typhoid, neonatal encephalopathy (13–15×).

**Malaria is not far below.** For papers it sits close to the trend (51.6M DALYs, 2,766 papers a year,
trend 3,652, 1.3×, rank 44 of 120). For trials it is 3.3× below (45 a year against 150; rank 25).
TB is above the trend for papers (0.6×) and 2.5× below for trials. The big-name infections
(HIV, TB, malaria) get far more attention than the smaller neglected tropical diseases, newborn
conditions and childhood vaccine-preventable infections.

Far above the trend: breast cancer, melanoma, liver and brain cancer, fatty liver disease, MS,
Crohn's, glaucoma and lymphomas.

## Caveats

- **ClinicalTrials.gov only.** Trials in LMICs are often registered only in PACTR, CTRI, ISRCTN or
  ChiCTR. So trial counts for tropical, newborn and maternal conditions are likely too low, and their
  trial shortfalls too high.
- **Title searches are not equally sensitive.** Depression uses `depression OR depressive` (broad).
  Anxiety uses named anxiety disorders only (narrow), which probably explains part of its 4.2× paper
  shortfall. It is kept because the diagnosis is well defined; the search could be widened. Type 2 diabetes misses papers that say only "diabetes". Lower respiratory infections
  leave out influenza and COVID-19 pneumonia. Non-Hodgkin lymphoma uses `lymphoma*`, so it includes
  Hodgkin papers (about 10%). African trypanosomiasis includes *T. brucei* lab biology. Queries are
  in `queries_2026-11-11.csv`, and spot checks of sampled titles looked on-topic.
- **Choice of causes shapes the trend.** Left out: the four vague causes above, injuries, "other …" residual causes, risk factors,
  COVID-19 (its 2021–2025 research volume reflects the pandemic), and causes with tiny burden (Ebola,
  Zika, guinea worm). Parent and child causes are never both used.
- Hepatitis B and C each sum chronic and acute GBD causes. Liver cancer due to hepatitis is not
  included. Summed uncertainty bounds are approximate.
- Comparator DALYs are global GBD 2023. Most research is funded in high-income countries, so diseases
  that mostly affect poor countries will sit low for reasons that have nothing to do with ME/CFS.
- ME/CFS burden is from the ME/CFS model (2026, CCC), not GBD. ME/CFS papers and trials are the
  "All ME/CFS" counts from `../analysis/`.
