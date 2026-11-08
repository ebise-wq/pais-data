# PubMed publications per year by disease

Pulled from PubMed with `pubs_per_year.py` (NCBI E-utilities, count queries only).
Same 24 diseases as `../clinicaltrials/`.

## Files

- `pubs_per_year_<date>.csv`: one row per disease, one column per year (1996–2026). Main measure (`title`).
- `pubs_per_year_long_<date>.csv`: one row per disease and year, with all three counts.
- `queries_<date>.csv`: the exact PubMed search string for each disease.

## Columns

- `title`: papers with the disease named in the title, using a curated synonym list. Counted by
  the date the record was added to PubMed (`[edat]`), so each paper counts in exactly one year.
  This is the main measure.
- `title_dp`: the same search, counted by publication date (`[dp]`). PubMed matches `[dp]` against
  both the online and the print date, so a paper published online in December and in print in
  January counts in both years. For MS in 2022–2023 that added 504 papers to 7,041 (about 7%).
  Do not sum `title_dp` across years.
- `mesh`: papers with the disease as a MeSH major topic, by `[edat]`. Cross-check only.

## Why title search, not MeSH

For ME/CFS in 2021–2025, about half the papers that name the disease in the title or abstract have
no MeSH indexing at all (mostly journals outside MEDLINE, or papers not yet indexed). Where papers
are indexed, the ME/CFS tag is almost always present. So MeSH is accurate but misses many papers, and
the share it misses differs by field. Title search catches unindexed papers and skips papers that
mention a disease only in passing in the abstract.

## Choices and known problems

- **Long COVID** cannot use "post-COVID" alone: about half of those titles are about the
  "post-COVID era". The query uses specific phrases (long COVID, post-COVID-19 condition,
  post-acute sequelae, PASC, ...). It will miss some papers titled only "post-COVID fatigue" and
  similar. The MeSH term "Post-Acute COVID-19 Syndrome" only exists from 2022 and is rarely a
  major topic, so the `mesh` column badly undercounts long COVID.
- **ME/CFS** excludes the bare abbreviation "CFS", which mostly matches the Clinical Frailty Scale
  and engineering papers.
- **POTS** as a bare word matches flower pots and cooking pots, so it needs a clinical word in
  the title too.
- **ALS**, **SLE**, **IBS**, **T1D**, **HIV** abbreviations are included. A few false hits are
  likely (for example "et al's" for ALS).
- **Epilepsy** includes "seizure*", which also catches acute and febrile seizures (matches the
  trials regex).
- **Psoriasis** includes psoriatic arthritis (matches the trials regex).
- **Post-treatment Lyme** has no MeSH term, so `mesh` is blank.
- Papers mentioning two diseases in the title count under both, for example ME/CFS and long COVID.
- 2026 is a partial year (to the pull date). Recent years also grow a little after the pull,
  as late records are added.
- `[edat]` is the date added to PubMed, not the publication date. For most papers these are the
  same year. Journals added to PubMed later can have older papers loaded with a recent `[edat]`.
