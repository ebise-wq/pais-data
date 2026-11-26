# Global ME/CFS burden

Question: how many people worldwide have ME/CFS, and how much disease burden (DALYs) does it cause?
Nobody has counted this, so it is a model. It also estimates all long COVID, a 2040 projection and
figures for 21 rich countries.

The model was built as a stand-alone page in a separate session (v11.2) and then moved into the
catalog. The Monte Carlo code that made the numbers is not in the repo; only its output is.
Page: https://ebise-wq.github.io/pais-data/global-burden.html

The ME/CFS burden in the research-vs-burden charts (`analysis/`, `expanded/`) comes from this model
(v11.2, CCC, 2026).

## Files

- `burden_interactive.html`: the interactive page (v11.3). Tabs: distribution, by age, countries;
  "How it's built" follows below them rather than as a tab. `tools/build_catalog.py` inserts it into
  `docs/global-burden.html` only, because its data are large (about 380 KB). Ids start with `gme-` and all styles sit under `.gme`. Text, sources and reasoning for every step
  are in this file.
- `overview.html`: the snapshot on the catalog overview: the two distribution charts (people and
  DALYs, CCC, both routes, now). The build gives it only those four parts of the model output.
- `model_output_2026-11-26.json`: the model output the page reads: ranges for people and DALYs by
  criteria, post-COVID route, age group, year and country, and the inputs of each step.

## Method

- Classic ME (started before or without COVID): starts from the Chicago community study (Jason 1999,
  0.42% of adults, doctor-confirmed), converted between definitions with ratios from English primary
  care (Nacul 2011) and Dutch patients (MECVS Nederland 2023), then adjusted by age and from rich
  countries to the world.
- Post-COVID ME, two routes from different studies:
  1. US study: extra ME after infection in RECOVER (Vernon 2025), using only people who joined soon
     after infection, corrected for doctor confirmation, criteria, variant and vaccination, recovery,
     reinfections and the rich-to-world step.
  2. UK survey: all long COVID from the ONS survey (winter 2023–24), then the share that meets
     ME/CFS criteria.
  The page averages the two on a multiplying scale (the geometric mean, in each draw).
- All long COVID: a separate route from the ONS survey, corrected for symptoms not caused by infection.
- Burden: people × disability weight, plus an addition for early death (7%, range 2–25%, from
  Roberts 2016). ME/CFS weights are GBD 2010 weights of states with similar loss of function, averaged
  over a severity mix based on DecodeME and the European ME Alliance survey. The CCC average is 0.36
  (0.28–0.45).
- Each step is a range. The model draws from all ranges 300,000 times (seed 20260821).
- Criteria: ICC, CCC, IOM and Fukuda. No population study has applied ICC, so ICC rests on ratios
  from patient samples.
- Reference diseases: people from GBD 2021 studies and WHO; DALYs from GBD 2023. Population by age:
  UN World Population Prospects 2024.

## Results (now, medians with 90% ranges)

| Criteria | People with ME/CFS | DALYs per year |
|---|---|---|
| ICC | 27.3M (15.2–50.2M) | 11.3M (6.0–21.9M) |
| CCC (default) | 45.1M (27.0–76.9M) | 17.5M (9.9–31.7M) |
| IOM | 64.8M (40.5–106M) | 24.5M (14.4–42.8M) |
| Fukuda | 80.1M (49.8–130M) | 28.6M (16.7–49.5M) |

- CCC: classic ME 19.7M (8.5–46.1M), post-COVID ME 23.4M (12.7–43.2M). Medians of parts do not add
  up to the median of the total. 0.54% of the world population; 210 DALYs per 100,000 people.
- The two post-COVID routes differ 2.4-fold for CCC: US study 36.0M, UK survey 15.2M.
- All long COVID: 87.8M people (56.3–137M), 19.8M DALYs (12.4–31.7M).
- 2040 (CCC): 48.7M people (26.8–92.7M), 18.9M DALYs (9.9–37.9M), with a 25% chance of another
  pandemic built in.
- Compared with multiple sclerosis (1.9M people, 1.1M DALYs): 24× as many people and 16× the DALYs.

## Caveats

- Four steps explain 90% of the spread in post-COVID ME: extra ME after infection in RECOVER, the
  share a doctor would confirm, the share meeting CCC, and recovery. Two are judgement and two rest
  on a single study.
- The US route probably runs high (questionnaire answers overstate ME); the UK route may run low
  (the survey misses the sickest and people who no longer link their illness to COVID).
- No step has been measured in a low- or middle-income country.
- The disability weights are borrowed from other conditions, not measured for ME/CFS. Compare with
  other diseases loosely.
- The 2040 inputs about new infections are judgement.
