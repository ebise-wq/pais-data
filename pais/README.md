# PAIS disease burden and ME

Question: what share of people with a post-acute infection syndrome (PAIS) have ME, and what share
of the PAIS disease burden does ME account for?

This is an illustrative model, not a measurement. It was first made as a stand-alone page and then
moved into the catalog. Page: https://ebise-wq.github.io/pais-data/pais-burden.html

## Files

- `burden_me.html`: the interactive model. Numbers in the diagrams are hidden by default ("Hide numbers"). All inputs, defaults and sources are in this file (no
  data file). `tools/build_catalog.py` inserts it into the overview and the topic page. On the
  overview the assumption tables are left out and the defaults are used.

## Method

- Groups: Long COVID (house/bedbound and other), ME after another trigger, post-vaccination,
  post-Lyme (PTLDS), post-Q fever (QFS), post-Legionella, post-sepsis without ICU. Post-intensive
  care syndrome after sepsis is listed but left out by default.
- Prevalence is the share of the population in the Netherlands (population 18.0 million). These are
  guesses of absolute and relative prevalence based on reading the literature, not hard data.
  Starting point: the Dutch PAIS Alliance (paisalliantie.nl) figures, divided by 3 (post-Q fever
  unchanged). Post-Lyme is an own estimate (the earlier, doubled figure divided by 2).
- Each group has a share with ME. People with ME get an ME severity weight: 0.55 if house/bedbound,
  0.22 otherwise, and a mix of the two (weighted by the ME-other-trigger split) where housebound
  status is not known. People without ME get a group weight: 0.40 for housebound Long COVID, 0.07
  for the rest, 0.20 for post-ICU.
- Burden = prevalence × severity, in DALYs per person per year (years lived with disability only).
- Second view: dysautonomia (OI/POTS) and MCAS are laid over the Long COVID and ME groups, with
  assumed shares and extra severity, combined the GBD way: 1 − (1−a)(1−b)(1−c).
- The diagrams are area-proportional Euler diagrams. The 4-set view is fitted numerically, so its
  overlaps are approximate.

## Results (default assumptions)

- PAIS: 1.05% of the population. ME: 0.52% of the population, 49% of PAIS patients.
- Burden: 0.22 healthy life-years lost per 100 people each year, of which 0.18 (80%) is ME.
- On 2026-11-26 all prevalences were cut to a third (post-Lyme to half, post-Q fever unchanged). The
  shares barely moved: before, PAIS was 3.1% of the population, with the same 49% and 80%.

## Caveats

- Severity weights mix GBD disability weights and EQ-5D utility losses. These are not the same scale.
- The ME share after Lyme, Q fever, Legionella and sepsis has never been measured; those shares are guesses.
- MCAS shares are guesses: there are no criteria-based prevalence figures.
- The headline ratio depends mostly on the ME severity weights and the ME share in mild Long COVID.
  The sources and reasoning for each input are listed under the tables on the topic page.
