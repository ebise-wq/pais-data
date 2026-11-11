# Burden vs research with 124 diseases

This extends `../analysis/` from 13 comparator diseases to 124. The 111 new ones are GBD 2023 causes
(level 3 or 4) with a name a title search can find. Papers and trials use the same method as before.

## Files

- `diseases.py`: the 111 new causes. Each has its GBD cause name(s), a PubMed title query, a
  ClinicalTrials.gov condition query, and a regex that a listed condition must match.
- `fetch.py`: pulls papers per year (PubMed, title search, by `[edat]`) and interventional trials per
  start year (ClinicalTrials.gov), 2021–2025. Writes `counts_<date>.csv` and `queries_<date>.csv`.
  Raw API pages go to `cache/` (not committed).
- `analyse.py`: joins counts to GBD DALYs, adds the 13 original comparators and ME/CFS from
  `../analysis/plot_data_2021-2025.csv`, fits trends and draws the plots.
- `burden_vs_research_expanded_2021-2025.csv`: one row per disease. `*_trend` is the value of the
  124-disease trend at that disease's DALYs. `*_shortfall` = trend ÷ actual; above 1 means fewer
  papers or trials than the trend predicts. Sorted by paper shortfall.
- `fits_2021-2025.csv`: log-log fits for several subsets, with the ME/CFS shortfall under each.
- `papers_vs_dalys_expanded.png`, `trials_vs_dalys_expanded.png`.

Run from the repo root: `python3 -I expanded/fetch.py`, then `python3 -I expanded/analyse.py`.

## Check against the old pipeline

The new code reproduces the old MS counts: 16,435 papers 2021–2025 (the same number) and 737 trials
(734 three days earlier).

## Results (pulled 2026-11-11)

| Set | n | Papers slope | Papers R² | ME/CFS papers shortfall | Trials slope | Trials R² | ME/CFS trials shortfall |
|---|---|---|---|---|---|---|---|
| Original 13 | 13 | 0.34 | 0.50 | 20.3× (12.4–29.8) | 0.23 | 0.30 | 13.4× (8.9–18.9) |
| All | 124 | 0.44 | 0.34 | 9.4× (6.9–13.1) | 0.60 | 0.39 | 7.5× (4.9–11.4) |
| All except cancers | 104 | 0.40 | 0.33 | 7.3× (5.4–10.2) | 0.56 | 0.38 | 5.5× (3.7–8.2) |
| Non-cancer chronic (NCD) | 65 | 0.32 | 0.21 | 8.9× (6.4–12.2) | 0.38 | 0.32 | 8.9× (6.4–12.2) |

Ranges: 90% interval from ME/CFS burden uncertainty (CCC, model v11.2) and trend uncertainty
(4,000 bootstrap resamples). The two "non-cancer" ME/CFS rows match by chance (8.94 and 8.88).

- The 13 original diseases sit above the broader trend. Most are well-funded chronic diseases (MS,
  Parkinson's, Crohn's, HIV). So the old 20× and 13× were measured against a high bar. Against all
  124 diseases ME/CFS is about 9× below on papers and 7.5× below on trials.
- The scatter is much wider: residual SD 0.48 log10 for papers (a factor of 3), against 0.21 for the
  13. One trend line is a rough summary.
- Rank is a steadier measure than the multiple. On papers, ME/CFS falls further below the trend than
  121 of the 124 diseases. Only tension-type headache, conduct disorder and neonatal encephalopathy
  (birth asphyxia) fall further. On trials, 13 of 124 fall further below.

### Diseases far below the trend

Papers: tension-type headache (21×), conduct disorder (17×), neonatal encephalopathy (11×),
rheumatic heart disease (9×), neonatal sepsis (9×), ascariasis, scabies, neck pain, lymphatic
filariasis, onchocerciasis, typhoid, pertussis (6–8×).

Trials: lymphatic filariasis (29×), cysticercosis (25×), measles (24×), food-borne trematodes (23×),
neonatal sepsis (18×), ascariasis, rheumatic heart disease, typhoid, neonatal encephalopathy (13–15×).

**Malaria is not far below.** For papers it sits close to the trend (51.6M DALYs, 2,766 papers a year,
trend 3,267, 1.2×, rank 49 of 124). For trials it is 3.3× below (45 a year against 147; rank 27).
TB is above the trend for papers (0.5×) and 2.4× below for trials. The big-name infections
(HIV, TB, malaria) get far more attention than the smaller neglected tropical diseases, newborn
conditions and childhood vaccine-preventable infections.

Far above the trend: breast cancer, melanoma, liver and brain cancer, fatty liver disease, MS,
Crohn's, glaucoma and lymphomas.

## Caveats

- **ClinicalTrials.gov only.** Trials in LMICs are often registered only in PACTR, CTRI, ISRCTN or
  ChiCTR. So trial counts for tropical, newborn and maternal conditions are likely too low, and their
  trial shortfalls too high.
- **Title searches are not equally sensitive.** Depression uses `depression OR depressive` (broad).
  Anxiety uses named anxiety disorders only (narrow), which probably explains part of its 3.8× paper
  shortfall. Type 2 diabetes misses papers that say only "diabetes". Lower respiratory infections
  leave out influenza and COVID-19 pneumonia. Non-Hodgkin lymphoma uses `lymphoma*`, so it includes
  Hodgkin papers (about 10%). African trypanosomiasis includes *T. brucei* lab biology. Queries are
  in `queries_2026-11-11.csv`, and spot checks of sampled titles looked on-topic.
- **Neck pain and low back pain trials** are inflated by many small physiotherapy trials.
- **Choice of causes shapes the trend.** Left out: injuries, "other …" residual causes, risk factors,
  COVID-19 (its 2021–2025 research volume reflects the pandemic), and causes with tiny burden (Ebola,
  Zika, guinea worm). Parent and child causes are never both used.
- Hepatitis B and C each sum chronic and acute GBD causes. Liver cancer due to hepatitis is not
  included. Summed uncertainty bounds are approximate.
- Comparator DALYs are global GBD 2023. Most research is funded in high-income countries, so diseases
  that mostly affect poor countries will sit low for reasons that have nothing to do with ME/CFS.
- ME/CFS burden is from the ME/CFS model (2026, CCC), not GBD. ME/CFS papers and trials are the
  "All ME/CFS" counts from `../analysis/`.
