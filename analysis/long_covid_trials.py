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
row = next(r for r in csv.DictReader(open("clinicaltrials/trials_per_year_2026-11-08.csv")) if r["disease"] == "Long COVID")
vals = [int(row[str(y)]) for y in YEARS]

BG, INK, MUTED, GRID = "#141a24", "#eef1f6", "#a3acba", "#262f3d"
OCEAN = "#7fb3d5"
plt.rcParams.update({"font.family": ["Inter", "DejaVu Sans"], "font.size": 13, "text.color": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelsize": 13, "ytick.labelsize": 13})
M = 0.055
fig = plt.figure(figsize=(6, 6), facecolor=BG)
ax = fig.add_axes([0.11, 0.17, 0.845, 0.68])
for y, v in zip(YEARS, vals):
    partial = y == 2026
    ax.bar(y, v, width=0.68, color=OCEAN, alpha=0.45 if partial else 1, zorder=2,
           hatch="///" if partial else None, edgecolor=BG if not partial else OCEAN, linewidth=0)
    ax.annotate(f"{v}", (y, v), xytext=(0, 6), textcoords="offset points", ha="center", va="bottom",
                fontsize=13, color=INK if not partial else MUTED)
ax.annotate("to 8 Nov", (2026, vals[-1]), xytext=(0, 26), textcoords="offset points", ha="center",
            va="bottom", fontsize=11, color=MUTED)
ax.set_xlim(2019.4, 2026.6); ax.set_ylim(0, 180)
ax.set_xticks(YEARS); ax.set_xticklabels([str(y) for y in YEARS])
ax.yaxis.set_major_locator(MultipleLocator(50))
ax.set_facecolor(BG); ax.grid(True, axis="y", color=GRID, lw=1, zorder=0)
for side in ("top", "right"): ax.spines[side].set_visible(False)
for side in ("left", "bottom"): ax.spines[side].set_color(MUTED); ax.spines[side].set_linewidth(1.2)
ax.tick_params(length=7, width=1.2, color=MUTED, pad=6)
fig.text(M, 0.935, "Long COVID trials per year", fontsize=20, fontweight="bold", color=INK, va="baseline")
fig.text(M, 0.885, "Interventional trials, by start year", fontsize=13, color=MUTED, va="baseline")
fig.text(M, 0.040, f"Data: ClinicalTrials.gov, retrieved {PULL}.", fontsize=10.5, color=MUTED, va="baseline")
fig.text(1 - M, 0.040, "v1", fontsize=9, color=GRID, ha="right", va="baseline")
fig.savefig("analysis/long_covid_trials_per_year.png", dpi=300, facecolor=BG)
print(dict(zip(YEARS, vals)))
