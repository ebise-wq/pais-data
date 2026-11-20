# Trials in all registries (WHO ICTRP) vs ClinicalTrials.gov

ClinicalTrials.gov misses trials registered only in other registries (Pan African, India, China,
Iran, Australia/NZ, EU and others). WHO's ICTRP search portal combines them.

- `search_strings.txt`: the five ICTRP condition searches (registration date 2019–2026, all statuses).
  `search_strings_1_split.txt` splits search 1 in case an export is too large (not needed in the end).
- `raw/export<N>.xml.gz`: the XML exports, downloaded by hand from trialsearch.who.int (the export
  button did not work for automated access). Data: WHO International Clinical Trials Registry
  Platform (ICTRP), exported 2026-11-19. ICTRP terms: attribute WHO ICTRP, show the processing date,
  no commercial use.
- `analyse_ictrp.py` → `ictrp_vs_ctgov_2021-2025.csv`.

Method: interventional trials only; start year 2021–2025 (registration year if no usable start
date); a listed condition must match the same regex as the ClinicalTrials.gov counts; records that
cite an NCT number, or repeat a title already counted, are dropped as duplicates.

`ratio_all_to_ctgov` compares all registries with the ClinicalTrials.gov records *within the same
ICTRP export*, so both sides use the same search and dates. The ICTRP copy of ClinicalTrials.gov
gives somewhat fewer trials than the ClinicalTrials.gov API (different search and date fields),
so use the ratio rather than mixing the two sources.

## Caveats

- Some matches are off-target: a trial whose condition list mentions the disease but which is about
  something else (for ME/CFS: a cancer fatigue study, a POTS prevalence study). Not hand-cleaned.
- For ME/CFS, about 28 of the 58 extra trials are Chinese traditional-medicine trials (tuina,
  moxibustion, tai chi, herbal formulas) labelled "chronic fatigue syndrome". Diagnostic criteria
  in these trials are often unclear.
- Duplicates filed in two registries with different titles and no cross-reference are still counted twice.
