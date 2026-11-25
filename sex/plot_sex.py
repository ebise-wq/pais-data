"""Chart: research vs the burden trend, by female share of cases. Run after analyse_sex.py.
Run from the repo root: python3 -I sex/plot_sex.py  ->  sex/sex_residuals.png"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
VERSION = "v1"
d = pd.read_csv(os.path.join(HERE, "sex_by_disease_2021-2025.csv"))
BG, INK, MUTED, GRID = "#141a24", "#e6e9ee", "#9aa3ad", "#2a3240"
COL = {"female": "#E07E58", "balanced": "#7C8591", "male": "#4F9AD6"}
side = d["sex_class"].map(lambda c: "female" if c.startswith("female") else "male" if c.startswith("male") else "balanced")
spec = d["sex_class"].str.endswith("specific")

plt.rcParams.update({"font.size": 15, "text.color": INK, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "font.family": "DejaVu Sans"})
fig, axes = plt.subplots(1, 2, figsize=(14, 6.6), facecolor=BG, sharey=True)
for ax, metric, title in [(axes[0], "papers", "Papers"), (axes[1], "trials", "Trials")]:
    ax.set_facecolor(BG)
    y = d[f"{metric}_resid_fold"]
    for s in COL:
        m = (side == s)
        ax.scatter(d.loc[m & ~spec, "female_share"], y[m & ~spec], s=70, color=COL[s], edgecolor=BG, linewidth=1.5, zorder=3)
        ax.scatter(d.loc[m & spec, "female_share"], y[m & spec], s=90, marker="D", facecolor="none",
                   edgecolor=COL[s], linewidth=2, zorder=3)
    # OLS line for non-sex-specific diseases
    ns = ~spec
    b, a = np.polyfit(d.loc[ns, "female_share"], np.log10(y[ns]), 1)
    xs = np.linspace(d.loc[ns, "female_share"].min(), d.loc[ns, "female_share"].max(), 50)
    ax.plot(xs, 10 ** (a + b * xs), color=INK, linewidth=2, alpha=0.8, zorder=2)
    ax.axhline(1, color=MUTED, linewidth=1, linestyle=(0, (3, 3)), zorder=1)
    ax.set_yscale("log")
    ax.set_yticks([0.03, 0.1, 0.3, 1, 3, 10]); ax.set_yticklabels(["0.03×", "0.1×", "0.3×", "1×", "3×", "10×"]); ax.minorticks_off()
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1]); ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_xlim(-0.05, 1.05)
    ax.grid(axis="y", color=GRID, linewidth=1); ax.set_axisbelow(True)
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.set_title(title, loc="left", fontsize=18, fontweight="bold", color=INK)
    ax.set_xlabel("Female share of cases")
    for lab in ["Breast cancer", "Multiple sclerosis", "Endometriosis", "Pre-eclampsia & hypertensive disorders of pregnancy",
                "Gout", "Prostate cancer", "Rheumatic heart disease", "Migraine"]:
        r = d[d["label"] == lab].iloc[0]
        short = {"Pre-eclampsia & hypertensive disorders of pregnancy": "Pre-eclampsia"}.get(lab, lab)
        ax.annotate(short, (r["female_share"], r[f"{metric}_resid_fold"]), xytext=(6, 4), textcoords="offset points",
                    fontsize=11.5, color=MUTED)
axes[0].set_ylabel("Actual ÷ burden trend")
fig.suptitle("Research vs burden, by female share", x=0.06, ha="left", fontsize=21, fontweight="bold", y=0.99)
from matplotlib.lines import Line2D
h = [Line2D([], [], marker="o", ls="", color=COL["female"], ms=9, label="Mostly female (≥60%)"),
     Line2D([], [], marker="o", ls="", color=COL["balanced"], ms=9, label="Balanced"),
     Line2D([], [], marker="o", ls="", color=COL["male"], ms=9, label="Mostly male (≤40%)"),
     Line2D([], [], marker="D", ls="", mfc="none", mec=MUTED, mew=2, ms=9, label="One sex only")]
fig.legend(handles=h, loc="upper left", bbox_to_anchor=(0.06, 0.935), ncol=4, frameon=False, fontsize=13)
fig.text(0.995, 0.01, VERSION, ha="right", fontsize=9, color=GRID)
fig.tight_layout(rect=(0, 0.02, 1, 0.9))
fig.savefig(os.path.join(HERE, "sex_residuals.png"), dpi=150, facecolor=BG)
