"""Long COVID interventional trials per start year (ClinicalTrials.gov), designed for phone screens.

Run from repo root: python3 -I analysis/long_covid_trials.py
Data: clinicaltrials/trials_per_year_2026-11-08.csv (pulled 2026-11-08).
Two studies with start years 2016 and 2018 are left out: they started before COVID-19
(older studies that later added long COVID), so they are not long COVID trials in the usual sense.
"""
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

YEARS = list(range(2020, 2027))
PULL = "8 Nov 2026"
rows = {r["disease"]: r for r in csv.DictReader(open("clinicaltrials/trials_per_year_2026-11-08.csv"))}
SERIES = [("Long COVID", [int(rows["Long COVID"][str(y)]) for y in YEARS]),
          ("ME/CFS", [int(rows["ME/CFS"][str(y)]) for y in YEARS])]

BG, INK, MUTED, GRID = "#141a24", "#eef1f6", "#a3acba", "#262f3d"
OCEAN, SUNSET = "#7fb3d5", "#f4a582"
COLORS = {"Long COVID": OCEAN, "ME/CFS": SUNSET}
plt.rcParams.update({"font.family": ["Inter", "DejaVu Sans"], "font.size": 13, "text.color": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelsize": 13, "ytick.labelsize": 13})
M = 0.055
fig = plt.figure(figsize=(6, 6), facecolor=BG)
ax = fig.add_axes([0.11, 0.17, 0.845, 0.63])
W = 0.36                      # bar width; pairs sit side by side with a small gap
for k, (name, vals) in enumerate(SERIES):
    c = COLORS[name]
    for y, v in zip(YEARS, vals):
        partial = y == 2026
        x = y + (k - 0.5) * (W + 0.03)
        ax.bar(x, v, width=W, color=c, alpha=0.45 if partial else 1, zorder=2,
               hatch="///" if partial else None, edgecolor=c if partial else BG, linewidth=0)
        ax.annotate(f"{v}", (x, v), xytext=(0, 5), textcoords="offset points", ha="center", va="bottom",
                    fontsize=11.5, color=MUTED if partial else INK)
ax.annotate("to 8 Nov", (2026, SERIES[0][1][-1]), xytext=(0, 26), textcoords="offset points", ha="center",
            va="bottom", fontsize=11, color=MUTED)
# legend as coloured words under the subtitle
fig.text(M, 0.835, "■ Long COVID", fontsize=13, color=OCEAN, va="baseline")
fig.text(M + 0.24, 0.835, "■ ME/CFS", fontsize=13, color=SUNSET, va="baseline")
ax.set_xlim(2019.4, 2026.6); ax.set_ylim(0, 180)
ax.set_xticks(YEARS); ax.set_xticklabels([str(y) for y in YEARS])
ax.yaxis.set_major_locator(MultipleLocator(50))
ax.set_facecolor(BG); ax.grid(True, axis="y", color=GRID, lw=1, zorder=0)
for side in ("top", "right"): ax.spines[side].set_visible(False)
for side in ("left", "bottom"): ax.spines[side].set_color(MUTED); ax.spines[side].set_linewidth(1.2)
ax.tick_params(length=7, width=1.2, color=MUTED, pad=6)
fig.text(M, 0.935, "Long COVID and ME/CFS trials", fontsize=20, fontweight="bold", color=INK, va="baseline")
fig.text(M, 0.885, "Interventional trials, by start year", fontsize=13, color=MUTED, va="baseline")
fig.text(M, 0.040, f"ClinicalTrials.gov, {PULL}. Trials naming both count in both.", fontsize=10.5, color=MUTED, va="baseline")
fig.text(1 - M, 0.040, "v2", fontsize=9, color=GRID, ha="right", va="baseline")
fig.savefig("analysis/long_covid_trials_per_year.png", dpi=300, facecolor=BG)
for name, vals in SERIES: print(name, dict(zip(YEARS, vals)))
