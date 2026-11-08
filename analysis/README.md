# Research activity vs global disease burden

`burden_vs_research.py` plots average yearly PubMed papers and interventional trials (2021–2025)
against global DALYs from GBD 2023 (`../gbd/`, level-3 causes, global, both sexes, all ages, 2023).

- ME/CFS DALYs are set by hand to 25 million (including post-COVID ME/CFS). GBD has no ME/CFS cause.
- Only the 10 repo diseases with a matching GBD level-3 cause are shown: MS, RA, IBD (Crohn's + UC,
  counts summed), psoriasis, epilepsy (GBD "Idiopathic epilepsy"), schizophrenia, bipolar disorder,
  Parkinson's, HIV/AIDS, ALS (GBD "Motor neuron disease").
- Left out, no level-3 GBD cause: long COVID, celiac, SLE, type 1 diabetes, fibromyalgia, POTS,
  endometriosis, IBS, Sjögren's, Gulf War illness, post-treatment Lyme, cystic fibrosis.
- Dashed line: least-squares fit in log-log space, excluding ME/CFS. The fit is weak
  (R² 0.33 for papers, 0.17 for trials, n=10), so the "expected" values are rough.
- Whiskers: GBD 95% uncertainty interval.
