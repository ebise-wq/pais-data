"""Shortfall (expected / actual) in papers and trials per year, 2021-2025, using CCC burden estimates.

Burden: Global ME/CFS Burden model v11.2 (Monte Carlo, 300,000 draws, year 2026), CCC criteria.
Expected = log-log trend fitted to the 13 GBD comparison diseases in burden_vs_research.py.
Run from repo root: python3 -I analysis/shortfall_ccc.py
"""
import csv, math, random

YEARS = [str(y) for y in range(2021, 2026)]
# 2021-2025 papers / trials counted under BOTH the ME/CFS and long COVID searches
# (PubMed title queries ANDed by [edat] year; ClinicalTrials.gov NCT IDs in both lists, by start year).
OVERLAP_PAPERS = [8, 29, 31, 40, 42]
OVERLAP_TRIALS = [1, 4, 7, 3, 4]

# CCC column: median, 5th, 95th percentile, millions of DALYs per year
GROUPS = [
    ("Non-COVID (classic) ME/CFS", (7.7, 3.2, 18.7), "classic"),
    ("All ME/CFS (classic + post-COVID)", (17.5, 9.9, 31.7), "ME/CFS"),
    ("Long COVID, incl. post-COVID ME", (19.8, 12.4, 31.7), "Long COVID"),
    ("Long COVID + non-COVID ME/CFS", (28.3, 18.3, 44.7), "union"),
]

def avg(path):
    with open(path) as f:
        return {r["disease"]: sum(int(r[y]) for y in YEARS) / len(YEARS) for r in csv.DictReader(f)}

pubs, trials = avg("pubmed/pubs_per_year_2026-11-08.csv"), avg("clinicaltrials/trials_per_year_2026-11-08.csv")
# classic ME/CFS = ME/CFS papers/trials that do not also name long COVID
pubs["classic"] = pubs["ME/CFS"] - sum(OVERLAP_PAPERS) / 5
trials["classic"] = trials["ME/CFS"] - sum(OVERLAP_TRIALS) / 5
pubs["union"] = pubs["ME/CFS"] + pubs["Long COVID"] - sum(OVERLAP_PAPERS) / 5
trials["union"] = trials["ME/CFS"] + trials["Long COVID"] - sum(OVERLAP_TRIALS) / 5

comp = [r for r in csv.DictReader(open("analysis/burden_vs_research_2021-2025.csv")) if r["label"] != "ME/CFS"]

def fit(pts):
    n = len(pts); mx = sum(x for x, _ in pts) / n; my = sum(y for _, y in pts) / n
    b = sum((x - mx) * (y - my) for x, y in pts) / sum((x - mx) ** 2 for x, _ in pts)
    return my - b * mx, b

def pct(v, p):
    v = sorted(v); k = (len(v) - 1) * p; f = int(k)
    return v[f] + (v[min(f + 1, len(v) - 1)] - v[f]) * (k - f)

random.seed(20261109)
out = []
for metric, actual in (("papers", pubs), ("trials", trials)):
    key = "pubs_per_year" if metric == "papers" else "trials_per_year"
    pts = [(math.log10(float(r["dalys"])), math.log10(float(r[key]))) for r in comp]
    a, b = fit(pts)
    boots = [fit([random.choice(pts) for _ in pts]) for _ in range(4000)]
    for name, (med, lo, hi), src in GROUPS:
        act = actual[src]
        exp = lambda d, a=a, b=b: 10 ** (a + b * math.log10(d * 1e6))
        # Range 1: burden uncertainty only. expected() is monotonic in DALYs, so the 5th/95th percentile
        # of DALYs maps straight onto the 5th/95th percentile of the shortfall.
        # Range 2: also trend-line uncertainty: lognormal DALYs (from median and 90% range) x bootstrap fit.
        sig = math.log(hi / lo) / (2 * 1.6449)
        sims = []
        for ab, bb in boots:
            d = med * math.exp(random.gauss(0, sig))
            sims.append(10 ** (ab + bb * math.log10(d * 1e6)) / act)
        out.append({"metric": metric, "group": name, "dalys_M": med, "actual_per_year": round(act, 1),
                    "expected_per_year": round(exp(med)),
                    "shortfall_median": round(exp(med) / act, 1),
                    "shortfall_p5_burden": round(exp(lo) / act, 1), "shortfall_p95_burden": round(exp(hi) / act, 1),
                    "shortfall_p5_burden_and_fit": round(pct(sims, .05), 1),
                    "shortfall_p95_burden_and_fit": round(pct(sims, .95), 1)})

with open("analysis/shortfall_ccc_2021-2025.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=out[0].keys()); w.writeheader(); w.writerows(out)
for r in out:
    print(f'{r["metric"]:7s} {r["group"]:36s} act {r["actual_per_year"]:7.1f} exp {r["expected_per_year"]:5d}  '
          f'{r["shortfall_median"]:5.1f}x ({r["shortfall_p5_burden"]}-{r["shortfall_p95_burden"]})  '
          f'[+fit: {r["shortfall_p5_burden_and_fit"]}-{r["shortfall_p95_burden_and_fit"]}]')

# --- plots: All ME/CFS on a scatter with the 13 GBD comparison diseases, designed for phone screens ---
# 6x6 in at 300 dpi = 1800 px. Shown ~380 px wide on a phone, so 1 pt is about 0.9 screen px: keep text >= 12 pt.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator
BG, INK, MUTED, FAINT, GRID = "#141a24", "#eef1f6", "#a3acba", "#5c7a94", "#262f3d"
OCEAN, SUNSET = "#7fb3d5", "#f4a582"
plt.rcParams.update({"font.family": ["Inter", "DejaVu Sans"], "font.size": 13, "text.color": INK,
                     "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
                     "xtick.labelsize": 13, "ytick.labelsize": 13, "axes.labelsize": 14})
COMP_NAME = {"Multiple sclerosis": "MS", "Rheumatoid arthritis": "RA", "Type 1 diabetes": "T1D",
             "ALS / motor neuron disease": "ALS", "Ulcerative colitis": "UC", "HIV/AIDS": "HIV",
             "Parkinson's disease": "Parkinson's", "Bipolar disorder": "Bipolar", "Crohn's disease": "Crohn's",
             "Endometriosis": "Endometr.", "Schizophrenia": "Schizophr."}
UP, DOWN = (0, 12, "center"), (0, -14, "center")
COMP_OFF = {  # (dx, dy, ha) in points; labels above or below so they clear the range bars
    "papers": {"Parkinson's": (-12, 0, "right"), "Epilepsy": UP, "Schizophr.": UP, "HIV": UP, "MS": UP, "RA": UP,
               "Psoriasis": (-12, -4, "right"), "T1D": DOWN, "UC": UP, "Crohn's": UP, "ALS": (-10, -14, "right"),
               "Endometr.": (8, -14, "left"), "Bipolar": DOWN},
    "trials": {"Parkinson's": UP, "HIV": UP, "MS": UP, "T1D": UP, "Schizophr.": UP, "Epilepsy": DOWN,
               "Psoriasis": UP, "RA": DOWN, "Crohn's": UP, "UC": UP, "ALS": (-14, 0, "right"),
               "Endometr.": DOWN, "Bipolar": DOWN},
}
PLOT_GROUPS = ["All ME/CFS (classic + post-COVID)"]
SPEC = {  # title, y label, y ticks
    "papers": ("Papers vs disease burden", "Papers per year", [100, 300, 1000, 3000, 10000]),
    "trials": ("Trials vs disease burden", "Trials per year", [3, 10, 30, 100, 300]),
}
XS = [3e5, 6e7]
for metric in ("papers", "trials"):
    key = "pubs_per_year" if metric == "papers" else "trials_per_year"
    pts = [(math.log10(float(r["dalys"])), math.log10(float(r[key]))) for r in comp]
    a, b = fit(pts)
    trend = lambda x: 10 ** (a + b * math.log10(x))
    title, ylab, yticks = SPEC[metric]
    fig, ax = plt.subplots(figsize=(6, 6), facecolor=BG)
    ax.plot(XS, [trend(x) for x in XS], color=MUTED, lw=1.5, ls=(0, (4, 3)), zorder=1)
    for r in comp:
        x, y = float(r["dalys"]), float(r[key])
        ax.plot([float(r["dalys_lower"]), float(r["dalys_upper"])], [y, y], color=FAINT, lw=1.3, alpha=.6, zorder=2)
        ax.scatter(x, y, s=55, color=OCEAN, edgecolor=BG, linewidth=1.5, zorder=3)
        n = COMP_NAME.get(r["label"], r["label"])
        dx, dy, ha = COMP_OFF[metric].get(n, UP)
        ax.annotate(n, (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center",
                    fontsize=12, color=MUTED)
    for (name, (med, lo, hi), _), r in zip(GROUPS, [o for o in out if o["metric"] == metric]):
        if name not in PLOT_GROUPS: continue
        x, y = med * 1e6, r["actual_per_year"]
        ax.plot([lo * 1e6, hi * 1e6], [y, y], color=SUNSET, lw=3, alpha=.55, zorder=3, solid_capstyle="round")
        ax.scatter(x, y, s=150, color=SUNSET, edgecolor=BG, linewidth=2, zorder=4)
        ax.annotate("ME/CFS", (x, y), xytext=(0, 22), textcoords="offset points", ha="center", va="bottom",
                    fontsize=16, fontweight="bold", color=SUNSET)
        ax.annotate(f'{r["shortfall_median"]:g}× shortfall\n({r["shortfall_p5_burden_and_fit"]:g}–'
                    f'{r["shortfall_p95_burden_and_fit"]:g}×)', (x, y), xytext=(0, -20), textcoords="offset points",
                    ha="center", va="top", fontsize=14, fontweight="semibold", color=SUNSET, linespacing=1.25)
    lo_y = min(o["actual_per_year"] for o in out if o["metric"] == metric)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(*XS)
    ax.set_ylim(yticks[0] * 0.75, yticks[-1] * 1.25) if metric == "papers" else ax.set_ylim(lo_y / 3.2, 400)
    ax.xaxis.set_major_locator(FixedLocator([1e6, 3e6, 1e7, 3e7]))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v/1e6:g}M"))
    ax.yaxis.set_major_locator(FixedLocator(yticks))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    for axis in (ax.xaxis, ax.yaxis): axis.set_minor_locator(NullLocator())
    ax.set_xlabel("Disease burden (DALYs per year)", labelpad=8)
    ax.set_ylabel(ylab, labelpad=8)
    ax.set_title(title, loc="left", color=INK, fontsize=20, fontweight="bold", pad=14)
    ax.set_facecolor(BG); ax.grid(True, color=GRID, lw=1)
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.tick_params(length=0, pad=6)
    fig.text(0.03, 0.02, "2021–25 average. ME/CFS: CCC burden, 90% range (model v11.2).\nOthers: GBD 2023.",
             color=MUTED, fontsize=10.5, va="bottom", linespacing=1.3)
    fig.text(0.97, 0.02, "v9", color=GRID, fontsize=9, ha="right", va="bottom")
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    # "trend" label rotated to follow the dashed line (angle measured on screen, after layout)
    tx = XS[1] / 1.7
    (x1, y1), (x2, y2) = ax.transData.transform([(tx, trend(tx)), (tx * 2, trend(tx * 2))])
    ax.annotate("trend", (tx, trend(tx)), xytext=(0, 6), textcoords="offset points",
                rotation=math.degrees(math.atan2(y2 - y1, x2 - x1)), rotation_mode="anchor",
                ha="center", va="bottom", color=MUTED, fontsize=12)
    fig.savefig(f"analysis/{metric}_vs_dalys_ccc_2021-2025.png", dpi=300, facecolor=BG)
