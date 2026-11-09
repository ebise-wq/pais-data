# Research activity vs global disease burden

`burden_vs_research.py` plots average yearly PubMed papers and interventional trials (2021–2025)
against global DALYs from GBD 2023 (`../gbd/`: one level-3 and one level-4 cause file; global, both sexes, all ages, 2023).

- ME/CFS DALYs are set by hand to 25 million (including post-COVID ME/CFS). GBD has no ME/CFS cause.
- Only the 13 repo diseases with a matching GBD cause are shown: MS, RA, Crohn's, UC, psoriasis,
  epilepsy (GBD "Idiopathic epilepsy"), schizophrenia, bipolar disorder, Parkinson's, HIV/AIDS,
  ALS (GBD "Motor neuron disease"), endometriosis, type 1 diabetes (level 4).
- Type 1 diabetes uses GBD "Diabetes mellitus type 1" (3.14M). GBD counts "Chronic kidney disease
  due to diabetes mellitus type 1" (3.06M) under CKD, so it is not included.
- Left out, no GBD cause at level 3 or 4: long COVID, celiac, SLE, fibromyalgia, POTS, IBS,
  Sjögren's, Gulf War illness, post-treatment Lyme, cystic fibrosis.
- Dashed line: least-squares fit in log-log space, excluding ME/CFS. The fit is weak
  (R² 0.50 for papers, 0.30 for trials, n=13), so the "expected" values are rough.
- Whiskers: GBD 95% uncertainty interval.

## Shortfall with CCC burden estimates

`shortfall_ccc.py` gives the shortfall (expected / actual papers or trials per year, 2021–2025) for four
ways of grouping ME/CFS and long COVID, using the CCC column of the Global ME/CFS Burden model v11.2
(Monte Carlo, 300,000 draws, year 2026). Output: `shortfall_ccc_2021-2025.csv`.

- Expected = the log-log trend through the 13 GBD comparison diseases, read off at the group's DALYs.
- Both ME/CFS rows use the same ME/CFS counts. Long COVID uses the long COVID counts. The combined row
  uses ME/CFS + long COVID minus items counted under both (2021–2025: 150 papers, 19 trials).
- `p5/p95_burden`: 90% range from the burden estimate alone. The trend is monotonic, so the DALY
  percentiles map straight onto shortfall percentiles.
- `p5/p95_burden_and_fit`: also includes uncertainty in the trend line (4,000 bootstrap resamples of the
  13 diseases, with lognormal DALY draws fitted to the median and 90% range).
- The trend is shallow (slope 0.34 for papers, 0.23 for trials in log-log), so the expected count changes
  little with burden. Comparator DALYs are GBD 2023; the ME/CFS model is for 2026.
