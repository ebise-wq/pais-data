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
