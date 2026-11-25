"""Charts: research vs burden, by how much a disease affects women. Run after analyse_sex.py.

Run from the repo root: python3 -I sex/plot_sex.py
Writes sex/sex_scatter.png (female share vs research) and sex/sex_groups.png (five sex groups).
Style matches analysis/sponsor_charts.py.
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, NullLocator

HERE = os.path.dirname(os.path.abspath(__file__))
BG, INK, MUTED, GRID, BAND = "#141a24", "#eef1f6", "#a3acba", "#262f3d", "#1d2533"
OCEAN, SUNSET, NEUTRAL = "#7fb3d5", "#f4a582", "#6b7585"   # mostly men, mostly women, balanced
plt.rcParams.update({"font.family": ["Inter", "DejaVu Sans"], "font.size": 13, "text.color": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelsize": 13, "ytick.labelsize": 13})
M = 0.055
FOOT = "Papers: PubMed. Trials: ClinicalTrials.gov. 2021–2025. Burden: GBD 2023."
SHORT = {"Rheumatic heart disease": "Rheumatic heart dis.", "Multiple sclerosis": "MS"}

d = pd.read_csv(os.path.join(HERE, "sex_by_disease_2021-2025.csv"))
d["side"] = d["sex_class"].map(lambda c: "f" if c.startswith("female") else "m" if c.startswith("male") else "b")
COL = {"f": SUNSET, "m": OCEAN, "b": NEUTRAL}
# ME/CFS: not one of the 120, so not in the trend line or group averages. Shown against the same
# 120-disease burden trend as the other dots. Burden: ME/CFS model v11.2 (CCC, central 17.5M DALYs);
# papers and trials: "All ME/CFS" from analysis/plot_data_2021-2025.csv. Female share about 70% (approximate).
ME_SHARE = 0.70
_all = pd.read_csv(os.path.join(HERE, "..", "expanded", "burden_vs_research_expanded_2021-2025.csv"))
_me = pd.read_csv(os.path.join(HERE, "..", "analysis", "plot_data_2021-2025.csv")).set_index("label").loc["All ME/CFS (classic + post-COVID)"]
ME = {}
for _m in ("papers", "trials"):
    _b, _a = np.polyfit(np.log10(_all["dalys"]), np.log10(_all[f"{_m}_per_year"]), 1)
    ME[_m] = float(_me[f"{_m}_per_year"]) / 10 ** (_a + _b * np.log10(float(_me["dalys"])))
ME_FOOT = "ME/CFS (about 70% women): not in trend or averages. Burden from a model."


def me_dot(ax, x, y, label_side="right"):
    ax.scatter([x], [y], s=150, color=SUNSET, edgecolor=INK, lw=2.2, zorder=6)
    dx, ha = (11, "left") if label_side == "right" else (-11, "right")
    ax.annotate("ME/CFS", (x, y), xytext=(dx, 0), textcoords="offset points", ha=ha, va="center",
                fontsize=12, fontweight="bold", color=INK, zorder=6)


YT = [0.03, 0.1, 0.3, 1, 3, 10]
YL = ["30× fewer", "10× fewer", "3× fewer", "As expected", "3× more", "10× more"]


def style(ax):
    ax.set_facecolor(BG)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    for s in ("left", "bottom"): ax.spines[s].set_color(MUTED); ax.spines[s].set_linewidth(1.2)
    ax.tick_params(length=6, width=1.2, color=MUTED, pad=5)


def header(fig, title, sub, legend, y0=0.955):
    fig.text(M, y0, title, fontsize=20, fontweight="bold", color=INK, va="baseline")
    fig.text(M, y0 - 0.038, sub, fontsize=12.5, color=MUTED, va="baseline")
    for (lab, col), x in zip(legend, (M, M + 0.33, M + 0.56)):
        fig.text(x, y0 - 0.075, "● " + lab, fontsize=12.5, color=col, va="baseline")


def scatter(version):
    fig = plt.figure(figsize=(6, 9.2), facecolor=BG)
    header(fig, "Research vs burden, by sex", "Each dot is a disease. Compared with what its burden predicts.",
           [("Mostly women", SUNSET), ("Balanced", NEUTRAL), ("Mostly men", OCEAN)])
    panels = [("Papers", "papers", 0.48), ("Trials", "trials", 0.118)]
    labels = {"papers": ["Breast cancer", "Multiple sclerosis", "Rheumatic heart disease", "Prostate cancer"],
              "trials": ["Breast cancer", "Multiple sclerosis", "Rheumatic heart disease", "Prostate cancer"]}
    for name, m, bottom in panels:
        ax = fig.add_axes([0.25, bottom, 0.70, 0.335])
        y = d[f"{m}_resid_fold"]
        for s in ("b", "m", "f"):
            k = d["side"] == s
            ax.scatter(d.loc[k, "female_share"] * 100, y[k], s=34, color=COL[s], lw=0.8, edgecolor=BG, zorder=3)
        ns = ~d["sex_class"].str.endswith("specific")
        b, a = np.polyfit(d.loc[ns, "female_share"] * 100, np.log10(y[ns]), 1)
        xs = np.array([d.loc[ns, "female_share"].min(), d.loc[ns, "female_share"].max()]) * 100
        ax.plot(xs, 10 ** (a + b * xs), color=INK, lw=2, zorder=4, solid_capstyle="round")
        ax.axhline(1, color=MUTED, lw=1.2, ls=(0, (3, 3)), zorder=1)
        me_dot(ax, ME_SHARE * 100, ME[m], "right")
        ax.set_yscale("log"); ax.set_ylim(0.025, 16)
        ax.yaxis.set_major_locator(FixedLocator(YT)); ax.set_yticklabels(YL)
        ax.yaxis.set_minor_locator(NullLocator())
        ax.set_xlim(-6, 106); ax.xaxis.set_major_locator(FixedLocator([0, 25, 50, 75, 100]))
        ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"] if m == "trials" else [])
        ax.grid(True, axis="y", color=GRID, lw=1, zorder=0)
        style(ax)
        ax.text(-4, 13, name, fontsize=15, fontweight="bold", color=INK, va="top")
        for lab in labels[m]:
            r = d[d["label"] == lab].iloc[0]
            x, yy = r["female_share"] * 100, r[f"{m}_resid_fold"]
            ha, dx = ("right", -7) if (x > 80 or lab == "Multiple sclerosis") else ("left", 7)
            if lab == "Rheumatic heart disease" and m == "papers":  # next to ME/CFS: label below the dot
                ax.annotate(SHORT[lab], (x, yy), xytext=(0, -9), textcoords="offset points",
                            ha="center", va="top", fontsize=10.5, color=MUTED)
                continue
            ax.annotate(SHORT.get(lab, lab), (x, yy), xytext=(dx, 0), textcoords="offset points",
                        ha=ha, va="center", fontsize=10.5, color=MUTED)
    fig.text(0.6, 0.062, "Share of patients who are women", fontsize=12.5, color=INK, ha="center", va="baseline")
    fig.text(M, 0.845, "White line: trend (one-sex diseases left out). It is flat.", fontsize=11.5, color=MUTED, va="baseline")
    fig.text(M, 0.034, ME_FOOT, fontsize=9.5, color=MUTED, va="baseline")
    fig.text(M, 0.016, FOOT, fontsize=9.5, color=MUTED, va="baseline")
    fig.text(1 - M, 0.016, version, fontsize=9, color=GRID, ha="right", va="baseline")
    fig.savefig(os.path.join(HERE, "sex_scatter.png"), dpi=300, facecolor=BG)


def groups(version):
    order = [("female-specific", "Women only", SUNSET), ("female-dominant", "Mostly women", SUNSET),
             ("balanced", "Balanced", NEUTRAL), ("male-dominant", "Mostly men", OCEAN),
             ("male-specific", "Men only", OCEAN)]
    rng = np.random.default_rng(46739079)  # seed drawn from a random number generator; jitter only
    fig = plt.figure(figsize=(6, 6.4), facecolor=BG)
    fig.text(M, 0.94, "Research by sex group", fontsize=20, fontweight="bold", color=INK, va="baseline")
    fig.text(M, 0.902, "Compared with what each disease's burden predicts", fontsize=12.5, color=MUTED, va="baseline")
    fig.text(M, 0.866, "Dots: diseases. White bar: group average.", fontsize=12.5, color=MUTED, va="baseline")
    top, bot = 0.76, 0.215
    axes = [fig.add_axes([0.355, bot, 0.29, top - bot]), fig.add_axes([0.675, bot, 0.29, top - bot])]
    n = len(order)
    for ax, m, title in zip(axes, ("papers", "trials"), ("Papers", "Trials")):
        for i, (cls, lab, col) in enumerate(order):
            yi = n - 1 - i
            v = d.loc[d["sex_class"] == cls, f"{m}_resid_fold"].to_numpy()
            ax.scatter(v, yi + rng.uniform(-0.22, 0.22, len(v)), s=22, color=col, alpha=0.75, lw=0, zorder=2)
            g = float(np.exp(np.log(v).mean()))
            ax.plot([g, g], [yi - 0.36, yi + 0.36], color=INK, lw=3, zorder=3, solid_capstyle="round")
            if cls == "female-dominant":
                me_dot(ax, ME[m], yi - 0.3, "left")
            if ax is axes[0]:
                fig.text(M, bot + (top - bot) * (yi + 0.5) / n, lab, fontsize=12.5, color=INK, va="center")
                fig.text(M, bot + (top - bot) * (yi + 0.5) / n - 0.026, f"{len(v)} diseases", fontsize=10.5,
                         color=MUTED, va="center")
        ax.axvline(1, color=MUTED, lw=1.2, ls=(0, (3, 3)), zorder=1)
        ax.set_xscale("log"); ax.set_xlim(0.025, 16); ax.set_ylim(-0.5, n - 0.5)
        ax.xaxis.set_major_locator(FixedLocator([0.1, 1, 10])); ax.set_xticklabels(["10×", "Expected", "10×"], fontsize=11.5)
        p = ax.get_position()
        fig.text(p.x0 + p.width * 0.36, bot - 0.075, "← fewer", fontsize=11, color=MUTED, ha="right", va="baseline")
        fig.text(p.x0 + p.width * 0.43, bot - 0.075, "more →", fontsize=11, color=MUTED, ha="left", va="baseline")
        ax.xaxis.set_minor_locator(NullLocator()); ax.yaxis.set_major_locator(NullLocator())
        ax.grid(True, axis="x", color=GRID, lw=1, zorder=0)
        style(ax); ax.spines["left"].set_visible(False)
        fig.text(ax.get_position().x0, top + 0.015, title, fontsize=13, fontweight="bold", color=INK, va="bottom")
    fig.text(M, 0.072, "Women-only and men-only groups include cancers, which get more research", fontsize=10.5, color=MUTED, va="baseline")
    fig.text(M, 0.045, ME_FOOT, fontsize=10.5, color=MUTED, va="baseline")
    fig.text(M, 0.018, FOOT, fontsize=9.5, color=MUTED, va="baseline")
    fig.text(1 - M, 0.018, version, fontsize=9, color=GRID, ha="right", va="baseline")
    fig.savefig(os.path.join(HERE, "sex_groups.png"), dpi=300, facecolor=BG)


scatter("v6")
groups("v4")
