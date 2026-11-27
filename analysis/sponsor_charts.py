"""Charts: commercial vs other sponsors of long COVID and ME/CFS trials.

Run from repo root: python3 -I analysis/sponsor_charts.py
Needs analysis/sponsor_by_year_2020-2026.csv and analysis/sponsor_by_disease_2021-2025.csv
(from sponsor_summary.py), and clinicaltrials/sponsor_all_types_2026-11-26.csv (from
clinicaltrials/sponsor_all_types.py) for all trial types.
Writes four per-year charts in one layout, so the catalog page can switch between them with two switches
(drug or all trial types; commercial sponsors shown or not): analysis/drug_trials_per_year.png,
analysis/sponsor_per_year.png, analysis/all_trials_per_year.png and analysis/all_trials_sponsor_per_year.png.
Also writes analysis/sponsor_comparison.png. Every chart is saved twice: transparent (for the page) and on
solid green in analysis/solid/ (for sharing on white backgrounds).
"""
import csv, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, FixedLocator, NullLocator

PULL = "25 Nov 2026"
# Forest glass: transparent background (the page shows deep green through it). BG is only used for edges.
BG, INK, MUTED, GRID, BAND = "#0e2a22", "#e9efe9", "#a7bdb2", "#ffffff1f", "#ffffff0d"
OCEAN, SUNSET = "#9fd8b5", "#f2b880"   # other sponsors, commercial sponsors
plt.rcParams.update({"font.family": ["Inter", "DejaVu Sans"], "font.size": 13, "text.color": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelsize": 13, "ytick.labelsize": 13})
M = 0.055


def style(ax):
    ax.set_facecolor("none")
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    for s in ("left", "bottom"): ax.spines[s].set_color(MUTED); ax.spines[s].set_linewidth(1.2)
    ax.tick_params(length=6, width=1.2, color=MUTED, pad=5)


def glow(fig):
    """The page's background as an image behind the figure: light from the top left, as in the CSS
    radial-gradient(120% 80% at 10% 0%, #1f4d3e 0%, #12342a 38%, #0e2a22 62%, #0b231c 100%)."""
    w, h = fig.get_size_inches()
    ny = 400; nx = max(2, int(ny * w / h))
    u, v = np.meshgrid(np.linspace(0, 1, nx), np.linspace(0, 1, ny))
    d = np.clip(np.hypot((u - 0.1) / 1.2, v / 0.8), 0, 1)
    stops = [0, 0.38, 0.62, 1]
    cols = np.array([matplotlib.colors.to_rgb(c) for c in ("#1f4d3e", "#12342a", "#0e2a22", "#0b231c")])
    img = np.stack([np.interp(d, stops, cols[:, k]) for k in range(3)], axis=-1)
    ax = fig.add_axes([0, 0, 1, 1], zorder=-100); ax.set_axis_off()
    ax.imshow(img, extent=[0, 1, 0, 1], aspect="auto", origin="upper")
    return ax


def save(fig, path):
    """Transparent PNG for the page, plus a copy on solid green in <folder>/solid/ for sharing on white pages, with the page's glow."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, dpi=300, transparent=True)
    solid = os.path.join(os.path.dirname(path), "solid", os.path.basename(path))
    os.makedirs(os.path.dirname(solid), exist_ok=True)
    bg = glow(fig)
    fig.savefig(solid, dpi=300, facecolor=BG)
    bg.remove()
    plt.close(fig)


ALL_TYPES = "clinicaltrials/sponsor_all_types_2026-11-26.csv"


def per_year(version, kind, split, wide=False):
    """kind: "drug" (drug or biologic trials) or "all" (all interventional trials); split: commercial sponsors
    in their own colour. The four views share one layout, so the page can switch between them; only the y
    scale differs between drug and all. wide=True: a landscape copy in analysis/wide/ for desktop topic pages."""
    if kind == "all":
        rows = list(csv.DictReader(open(ALL_TYPES)))
        def get(d):
            out = []
            for y in range(2020, 2027):
                R = [r for r in rows if r["disease"] == d and int(r["start_year"]) == y]
                c = sum(int(r["commercial"]) for r in R)
                out.append((y, c if split else 0, len(R) - c if split else len(R)))
            return out
        lc_max, me_max, step = 170, 51, 50
    else:
        rows = list(csv.DictReader(open("analysis/sponsor_by_year_2020-2026.csv")))
        def get(d):
            out = []
            for r in rows:
                if r["disease"] != d:
                    continue
                n, c = int(r["drug_trials"]), int(r["commercial"])
                out.append((int(r["year"]), c if split else 0, n - c if split else n))
            return out
        lc_max, me_max, step = 50, 15, 10
    W, H = (10, 5.8) if wide else (6, 7.2)
    fig = plt.figure(figsize=(W, H), facecolor="none")
    X, Yt, Yb = (lambda i: i / W), (lambda i: 1 - i / H), (lambda i: i / H)  # inches to figure fractions
    me_bot, gap, lc_top = 0.828, 0.198, 1.26     # inches; same in both shapes
    h_lc = (H - lc_top - me_bot - gap) / (1 + me_max / lc_max)   # same height per trial in both panels
    panels = [("Long COVID", lc_max, me_bot + gap + h_lc * me_max / lc_max), ("ME/CFS", me_max, me_bot)]
    for name, ymax, bottom in panels:
        ax = fig.add_axes([X(0.66), Yb(bottom), X(W - 0.93), Yb(h_lc * ymax / lc_max)])
        data = get(name)
        for y, c, o in data:
            part = y == 2026
            kw = dict(width=0.62, zorder=2, linewidth=0, alpha=0.5 if part else 1)
            ax.bar(y, c, color=SUNSET, hatch="///" if part else None, edgecolor=SUNSET if part else BG, **kw)
            ax.bar(y, o, bottom=c, color=OCEAN, hatch="///" if part else None, edgecolor=OCEAN if part else BG, **kw)
            if c + o:
                ax.annotate(f"{c}/{c + o}" if split else f"{c + o}", (y, c + o), xytext=(0, 4), textcoords="offset points", ha="center",
                            va="bottom", fontsize=11.5 if not (split and kind == "all") else 10.5, color=MUTED if part else INK)
        ax.set_xlim(2019.4, 2026.6); ax.set_ylim(0, ymax)
        ax.yaxis.set_major_locator(MultipleLocator(step)); ax.grid(True, axis="y", color=GRID, lw=1, zorder=0)
        ax.set_xticks(range(2020, 2027))
        ax.set_xticklabels([str(y) for y in range(2020, 2027)] if name == "ME/CFS" else [])
        style(ax)
        ax.text(2019.55, ymax * 0.95, name, fontsize=15, fontweight="bold", color=INK, va="top")
    title = "Long COVID and ME/CFS trials" if kind == "all" else "Long COVID and ME/CFS drug trials"
    L = X(0.33)
    fig.text(L, Yt(0.396), title, fontsize=20, fontweight="bold", color=INK, va="baseline")
    what = "All interventional trials by start year" if kind == "all" else "Drug or biologic trials by start year"
    fig.text(L, Yt(0.684), what, fontsize=12, color=MUTED, va="baseline")
    if split:
        fig.text(L, Yt(0.972), "■ Commercial sponsor", fontsize=13, color=SUNSET, va="baseline")
        fig.text(X(3.03), Yt(0.972), "■ Other sponsor", fontsize=13, color=OCEAN, va="baseline")
    else:
        fig.text(L, Yt(0.972), "■ All sponsors", fontsize=13, color=OCEAN, va="baseline")
    foot = "ClinicalTrials.gov" + (" lead sponsor class" if split else "") + ". 2026 to " + \
           ("26 Nov." if kind == "all" else "8 Nov.") + (" Trials naming both count in both." if kind == "all" else "")
    foot = foot.replace(" lead sponsor class. ", ", lead sponsor. ") if kind == "all" and split else foot
    fig.text(L, Yb(0.252), foot, fontsize=10.5 if (wide or len(foot) < 70) else 9.5, color=MUTED, va="baseline")
    fig.text(1 - L, Yb(0.252), version, fontsize=9, color=MUTED, alpha=0.6, ha="right", va="baseline")
    out = {("drug", False): "analysis/drug_trials_per_year.png", ("drug", True): "analysis/sponsor_per_year.png",
           ("all", False): "analysis/all_trials_per_year.png", ("all", True): "analysis/all_trials_sponsor_per_year.png"}
    path = out[(kind, split)]
    save(fig, os.path.join(os.path.dirname(path), "wide", os.path.basename(path)) if wide else path)


def comparison(version):
    rows = list(csv.DictReader(open("analysis/sponsor_by_disease_2021-2025.csv")))
    rows.sort(key=lambda r: float(r["commercial_share"]))
    n = len(rows)
    short = {"Cardiomyopathy & myocarditis": "Cardiomyopathy", "Congenital heart disease": "Congenital heart dis.",
             "Rheumatic heart disease": "Rheumatic heart dis.", "Alcohol use disorders": "Alcohol use disorder",
             "Opioid use disorders": "Opioid use disorder"}
    fig = plt.figure(figsize=(6, 9.6), facecolor="none")
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
    fig.text(1 - M, 0.012, version, fontsize=9, color=MUTED, alpha=0.6, ha="right", va="baseline")
    save(fig, "analysis/sponsor_comparison.png")


for wide in (False, True):
    per_year("v6", "drug", False, wide)
    per_year("v7", "drug", True, wide)
    per_year("v5", "all", False, wide)
    per_year("v4", "all", True, wide)
comparison("v4")
