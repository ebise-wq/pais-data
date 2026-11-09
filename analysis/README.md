# Research activity vs global disease burden

`burden_vs_research.py` plots average yearly PubMed papers and interventional trials (2021–2025)
against global DALYs from GBD 2023 (`../gbd/`, level-3 causes, global, both sexes, all ages, 2023).

- ME/CFS DALYs are set by hand to 25 million (including post-COVID ME/CFS). GBD has no ME/CFS cause.
- Only the 10 repo diseases with a matching GBD level-3 cause are shown: MS, RA, IBD (its own category, see below), psoriasis, epilepsy (GBD "Idiopathic epilepsy"), schizophrenia, bipolar disorder,
  Parkinson's, HIV/AIDS, ALS (GBD "Motor neuron disease").
- Left out, no level-3 GBD cause: long COVID, celiac, SLE, type 1 diabetes, fibromyalgia, POTS,
  endometriosis, IBS, Sjögren's, Gulf War illness, post-treatment Lyme, cystic fibrosis.
- Dashed line: least-squares fit in log-log space, excluding ME/CFS. The fit is weak
  (R² 0.20 for papers, 0.15 for trials, n=10), so the "expected" values are rough.
- Whiskers: GBD 95% uncertainty interval.

## IBD

IBD is its own category in both data sets, not Crohn's + UC added together. Each trial or paper
counts once, even if it names both. It also includes trials and papers that name only
"inflammatory bowel disease" / "IBD", because the GBD cause covers all IBD.

- Trials (all registered studies): Crohn's 1,930 + UC 1,519, with 527 listed under both. Union 2,922.
  Another 855 name only IBD in general. IBD total 3,777.
- Papers, 2021–2025: 350 titles name both Crohn's and UC. About 13,600 name only IBD in general.
  IBD averages 5,590 papers a year, against 2,904 a year from the old Crohn's + UC sum.
- The IBD trials row was pulled on 2026-11-09, one day after the other rows. The IBD PubMed rows
  were also pulled on 2026-11-09 but are stored in the 2026-11-08 files.
