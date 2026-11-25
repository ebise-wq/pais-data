# Research volume vs which sex a disease mostly affects

Question: once burden (DALYs) is taken into account, do diseases that mostly affect women get fewer
papers or trials than diseases that mostly affect men? Uses the 120 diseases in `../expanded/`
(papers and ClinicalTrials.gov trials per year, 2021–2025; GBD 2023 DALYs).

## Files

- `sex_labels.csv`: female share of cases for each disease, a confidence rating, and a one-line basis.
  **Coded by hand from standard epidemiology, not taken from a dataset.** See caveats.
- `analyse_sex.py` → `sex_results_2021-2025.csv` and `sex_by_disease_2021-2025.csv`.
  `sex_results` holds every model, robustness check and sex-class average in one table. Its `table`
  column says which: `model`, `robustness` or `sex class`. `multiplier` is the effect per +10 pp
  female (or, for `sex class`, the geometric mean of actual ÷ trend), with `ci_low`–`ci_high`.
- `plot_sex.py` → `sex_scatter.png` (female share vs research, each dot a disease) and
  `sex_groups.png` (the five sex groups, with group averages).

Run from the repo root: `python3 -I sex/analyse_sex.py`, then `python3 -I sex/plot_sex.py`.
Needs pandas, numpy, statsmodels, matplotlib.

## Classes

Female-specific (≥95% female, n=8, includes breast cancer at 99%), female-dominant (≥60%, n=15),
balanced (n=68), male-dominant (≤40%, n=26), male-specific (n=3: prostate cancer, testicular cancer, BPH).

## Methods

- Outcome: log10 papers (or trials) per year. Every main model adjusts for log10 DALYs, because
  research volume tracks burden.
- Main exposure: female share of cases as a continuous variable, in the 109 diseases that are not
  sex-specific. Effects are reported as a multiplier on papers or trials per +10 percentage points
  female. OLS with HC3 (heteroskedasticity-robust) standard errors.
- Second model adds disease group (cancer, other NCD, infectious, NTD, maternal/neonatal). Group is
  partly a confounder (NTDs are poor-country diseases) and partly could be on the path, so both are shown.
- Also: the five classes as categories (all 120, balanced as reference); female-dominant minus
  male-dominant directly; negative binomial on 5-year counts; permutation tests (10,000 shuffles,
  within group for the group model); Huber robust regression; cleaned counts; dropping each group;
  dropping the 13 originally hand-picked comparators; only high-confidence labels; and 2,000 runs with
  random error added to each female share (SD 0.03 / 0.07 / 0.12 for high / medium / low confidence).

## Results

| Outcome | Model | Multiplier per +10 pp female | 95% CI | p | Permutation p |
|---|---|---|---|---|---|
| Papers | DALYs | 0.94 | 0.79–1.11 | 0.45 | 0.48 |
| Papers | DALYs + group | 0.98 | 0.84–1.14 | 0.80 | 0.78 |
| Trials | DALYs | 0.99 | 0.81–1.21 | 0.92 | 0.93 |
| Trials | DALYs + group | 1.04 | 0.89–1.22 | 0.65 | 0.64 |

Female-dominant vs male-dominant (DALYs adjusted): papers 0.76× (0.36–1.60), trials 1.09× (0.47–2.53).

**No detectable association.** Point estimates are close to 1 in every model. The intervals rule out
large effects per 10 pp (beyond about −20% / +20%), but the class contrasts are wide: a 2× gap between
female-dominant and male-dominant diseases cannot be ruled out with 15 and 26 diseases.

Robustness (papers, DALYs model): cleaned counts 0.94; without the original 13 comparators 0.87
(0.73–1.05, p=0.14); only high-confidence labels 0.98; Huber 0.93; NB 1.00. Trials: all between 0.91
and 1.15, none significant. The original 13 included well-funded female-leaning diseases (MS, RA,
endometriosis), so dropping them tilts papers slightly toward fewer for female diseases, but not significantly.

Sex-specific female conditions sit *above* the trend on trials (2.9×, p=0.001, all 120, DALYs
only). That disappears when disease group is added (1.3×, p=0.40): it comes from breast, ovarian and
cervical cancer, and cancers in general sit high. Maternal hemorrhage sits low (0.38× on papers).

Female-dominant diseases are split. Far above trend: MS, depression, dementia, RA, thyroid cancer.
Far below: rheumatic heart disease (0.10×), trachoma, genital herpes, anxiety, urticaria, gallstones,
migraine. The low ones are mostly poor-country, non-fatal or "common" conditions, which also describes
many low balanced and male-dominant diseases.

## Caveats

- **Labels are hand-coded approximations.** They reflect typical published sex ratios of cases
  (prevalence or incidence), not GBD sex-specific DALYs. 36 of 120 are rated low confidence, mostly
  infections with roughly equal ratios. The label-noise test says modest errors don't change the result,
  but a systematic bias in the labels would not be caught. A better version would use GBD 2023 DALYs
  by sex (the GBD Results tool, sex = Male and Female, same causes) and define female share of DALYs.
- **Range is narrow.** Outside sex-specific conditions, only 15 diseases are ≥60% female and
  none is above 75%. Most of the variation is between 40% and 60%, which limits power.
- **DALYs are the yardstick.** If disability weights undervalue conditions common in women (often
  non-fatal, chronic), the adjustment itself hides a bias. This analysis cannot test that.
- ME/CFS is not in the 120 and is not used in any model or group average. The charts show it as a
  highlighted dot against the same 120-disease burden trend: about 10× fewer papers (0.097×) and 7.7×
  fewer trials (0.13×) than its burden predicts (ME/CFS model v11.2, CCC, 17.5M DALYs). Its female share
  is set at about 70%, an approximation.
- Observational, 120 diseases chosen for searchability. Many other things differ between diseases.
- Same count caveats as `../expanded/README.md` (title searches, ClinicalTrials.gov only).
