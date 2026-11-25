"""Charts: commercial vs other sponsors of drug/biologic trials.

Run from repo root: python3 -I analysis/sponsor_charts.py
Needs analysis/sponsor_by_year_2020-2026.csv and analysis/sponsor_by_disease_2021-2025.csv
(from sponsor_summary.py), and clinicaltrials/trials_per_year_2026-11-08.csv for all trial types.
Writes three per-year charts in one layout, so the catalog page can switch between them:
analysis/drug_trials_per_year.png (drug or biologic trials), analysis/sponsor_per_year.png (the same,
split by sponsor type) and analysis/all_trials_per_year.png (all interventional trials). Also writes
analysis/sponsor_comparison.png.
"""
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, FixedLocator, NullLocator

PULL = "25 Nov 2026"
BG, INK, MUTED, GRID, BAND = "#141a24", "#eef1f6", "#a3acba", "#262f3d", "#1d2533"
OCEAN, SUNSET = "#7fb3d5", "#f4a582"   # other sponsors, commercial sponsors
plt.rcParams.update({"font.family": ["Inter", "DejaVu Sans"], "font.size": 13, "text.color": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelsize": 13, "ytick.labelsize": 13})
M = 0.055


def style(ax):
    ax.set_facecolor(BG)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    for s in ("left", "bottom"): ax.spines[s].set_color(MUTED); ax.spines[s].set_linewidth(1.2)
    ax.tick_params(length=6, width=1.2, color=MUTED, pad=5)


def per_year(version, mode):
    """mode: "drug" (drug or biologic trials), "sponsor" (the same, split by sponsor type), "all" (all
    interventional trials). Panels sit in the same place in every mode; only the y scale changes."""
    split = mode == "sponsor"
    if mode == "all":
        tpy = {r["disease"]: r for r in csv.DictReader(open("clinicaltrials/trials_per_year_2026-11-08.csv"))}
        get = lambda d: [(y, 0, int(tpy[d][str(y)])) for y in range(2020, 2027)]
        lc_max, me_max, step = 170, 51, 50
    else:
        rows = list(csv.DictReader(open("analysis/sponsor_by_year_2020-2026.csv")))
        get = lambda d: [(int(r["year"]), int(r["commercial"]), int(r["drug_trials"]) - int(r["commercial"]))
                         for r in rows if r["disease"] == d]
        lc_max, me_max, step = 50, 15, 10
    fig = plt.figure(figsize=(6, 7.2), facecolor=BG)
    unit = 0.525 / lc_max          # figure height per trial, same in both panels
    panels = [("Long COVID", lc_max, 0.30), ("ME/CFS", me_max, 0.115)]
    for name, ymax, bottom in panels:
        ax = fig.add_axes([0.11, bottom, 0.845, ymax * unit])
        data = get(name)
        for y, c, o in data:
            part = y == 2026
            kw = dict(width=0.62, zorder=2, linewidth=0, alpha=0.5 if part else 1)
            low = SUNSET if split else OCEAN
            ax.bar(y, c, color=low, hatch="///" if part else None, edgecolor=low if part else BG, **kw)
            ax.bar(y, o, bottom=c, color=OCEAN, hatch="///" if part else None, edgecolor=OCEAN if part else BG, **kw)
            if c + o:
                ax.annotate(f"{c}/{c + o}" if split else f"{c + o}", (y, c + o), xytext=(0, 4), textcoords="offset points", ha="center",
                            va="bottom", fontsize=11.5, color=MUTED if part else INK)
        ax.set_xlim(2019.4, 2026.6); ax.set_ylim(0, ymax)
        ax.yaxis.set_major_locator(MultipleLocator(step)); ax.grid(True, axis="y", color=GRID, lw=1, zorder=0)
        ax.set_xticks(range(2020, 2027))
        ax.set_xticklabels([str(y) for y in range(2020, 2027)] if name == "ME/CFS" else [])
        style(ax)
        ax.text(2019.55, ymax * 0.95, name, fontsize=15, fontweight="bold", color=INK, va="top")
    title = "Long COVID and ME/CFS trials" if mode == "all" else "Long COVID and ME/CFS drug trials"
    fig.text(M, 0.945, title, fontsize=20, fontweight="bold", color=INK, va="baseline")
    if mode == "all":
        fig.text(M, 0.905, "All interventional trials by start year", fontsize=12, color=MUTED, va="baseline")
        fig.text(M, 0.865, "■ All trial types", fontsize=13, color=OCEAN, va="baseline")
    elif split:
        fig.text(M, 0.905, "Drug or biologic trials by start year. Label: commercial / all", fontsize=12, color=MUTED, va="baseline")
        fig.text(M, 0.865, "■ Commercial sponsor", fontsize=13, color=SUNSET, va="baseline")
        fig.text(M + 0.45, 0.865, "■ Other sponsor", fontsize=13, color=OCEAN, va="baseline")
    else:
        fig.text(M, 0.905, "Drug or biologic trials by start year", fontsize=12, color=MUTED, va="baseline")
        fig.text(M, 0.865, "■ All sponsors", fontsize=13, color=OCEAN, va="baseline")
    foot = {"sponsor": "ClinicalTrials.gov lead sponsor class. 2026 to 8 Nov.",
            "drug": "ClinicalTrials.gov. 2026 to 8 Nov.",
            "all": "ClinicalTrials.gov. 2026 to 8 Nov. Trials naming both count in both."}[mode]
    fig.text(M, 0.035, foot, fontsize=10.5, color=MUTED, va="baseline")
    fig.text(1 - M, 0.035, version, fontsize=9, color=GRID, ha="right", va="baseline")
    out = {"sponsor": "analysis/sponsor_per_year.png", "drug": "analysis/drug_trials_per_year.png",
           "all": "analysis/all_trials_per_year.png"}[mode]
    fig.savefig(out, dpi=300, facecolor=BG)
    plt.close(fig)


def comparison(version):
    rows = list(csv.DictReader(open("analysis/sponsor_by_disease_2021-2025.csv")))
    rows.sort(key=lambda r: float(r["commercial_share"]))
    n = len(rows)
    short = {"Cardiomyopathy & myocarditis": "Cardiomyopathy", "Congenital heart disease": "Congenital heart dis.",
             "Rheumatic heart disease": "Rheumatic heart dis.", "Alcohol use disorders": "Alcohol use disorder",
             "Opioid use disorders": "Opioid use disorder"}
    fig = plt.figure(figsize=(6, 9.6), facecolor=BG)
    top, bot = 0.835, 0.085
    a1 = fig.add_axes([0.385, bot, 0.27, top - bot])
    a2 = fig.add_axes([0.70, bot, 0.255, top - bot])
    for i, r in enumerate(rows):
        hi = r["disease"] in ("Long COVID", "ME/CFS")
        if hi:
            for a in (a1, a2):
                a.axhspan(i - 0.5, i + 0.5, color=BAND, zorder=0, lw=0)
        sh = float(r["commercial_share"])
        a1.barh(i, sh * 100, height=0.62, color=SUNSET, zorder=2, lw=0)
        a1.text(sh * 100 + 2, i, f"{sh:.0%}", va="center", fontsize=10.5, color=INK if hi else MUTED)
        c, o = float(r["commercial_per_year"]), float(r["non_commercial_per_year"])
        lo = 0.1
        a2.plot([max(c, lo), max(o, lo)], [i, i], color=GRID, lw=2, zorder=1)
        a2.scatter([max(o, lo)], [i], s=46, color=OCEAN, zorder=3, lw=0)
        a2.scatter([max(c, lo)], [i], s=46, color=SUNSET, zorder=4, lw=0)
        lab = short.get(r["disease"], r["disease"])
        fig.text(M, bot + (top - bot) * (i + 0.5) / n, lab, fontsize=12 if hi else 11.5,
                 fontweight="bold" if hi else "normal", color=INK if hi else MUTED, va="center")
    for a in (a1, a2):
        a.set_ylim(-0.5, n - 0.5); a.yaxis.set_major_locator(NullLocator()); style(a)
        a.spines["left"].set_visible(False); a.tick_params(axis="y", length=0)
    a1.set_xlim(0, 100); a1.xaxis.set_major_locator(FixedLocator([0, 50, 100]))
    a1.set_xticklabels(["0", "50", "100"]); a1.grid(True, axis="x", color=GRID, lw=1, zorder=0)
    a2.set_xscale("log"); a2.set_xlim(0.08, 400)
    a2.xaxis.set_major_locator(FixedLocator([0.1, 1, 10, 100])); a2.set_xticklabels(["0", "1", "10", "100"])
    a2.xaxis.set_minor_locator(NullLocator()); a2.grid(True, axis="x", color=GRID, lw=1, zorder=0)
    fig.text(0.385, top + 0.012, "Commercial %", fontsize=12, color=INK, va="bottom")
    fig.text(0.70, top + 0.012, "Trials per year", fontsize=12, color=INK, va="bottom")
    fig.text(M, 0.962, "Commercial drug trials vs", fontsize=20, fontweight="bold", color=INK, va="baseline")
    fig.text(M, 0.932, "diseases with 10–30M DALYs", fontsize=20, fontweight="bold", color=INK, va="baseline")
    fig.text(M, 0.902, "Drug or biologic trials, 2021–2025", fontsize=12.5, color=MUTED, va="baseline")
    fig.text(M, 0.875, "● Commercial sponsor", fontsize=12.5, color=SUNSET, va="baseline")
    fig.text(M + 0.42, 0.875, "● Other sponsor", fontsize=12.5, color=OCEAN, va="baseline")
    fig.text(M, 0.03, "ClinicalTrials.gov, Nov 2026. DALYs: GBD 2023; ME/CFS, long COVID: model.",
             fontsize=9.5, color=MUTED, va="baseline")
    fig.text(1 - M, 0.012, version, fontsize=9, color=GRID, ha="right", va="baseline")
    fig.savefig("analysis/sponsor_comparison.png", dpi=300, facecolor=BG)


per_year("v2", "drug")
per_year("v2", "sponsor")
per_year("v1", "all")
comparison("v1")
