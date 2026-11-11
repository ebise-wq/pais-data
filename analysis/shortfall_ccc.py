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
# Layout: title, axis description, x-axis title and footnote all start at the same left margin (M).
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FuncFormatter, LogLocator, NullFormatter
BG, INK, MUTED, GRID = "#141a24", "#eef1f6", "#a3acba", "#262f3d"
OCEAN, SUNSET = "#7fb3d5", "#f4a582"
plt.rcParams.update({"font.family": ["Inter", "DejaVu Sans"], "font.size": 13, "text.color": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelsize": 13, "ytick.labelsize": 13})
COMP_NAME = {"Multiple sclerosis": "MS", "Rheumatoid arthritis": "RA", "Type 1 diabetes": "T1D",
             "ALS / motor neuron disease": "ALS", "Ulcerative colitis": "UC", "HIV/AIDS": "HIV",
             "Parkinson's disease": "Parkinson's", "Bipolar disorder": "Bipolar", "Crohn's disease": "Crohn's"}
LEFT, ABOVE = (-9, 0, "right"), (0, 13, "center")   # default: right of the dot, (9, 0, "left")
COMP_OFF = {
    "papers": {"Parkinson's": LEFT, "Epilepsy": ABOVE, "Psoriasis": LEFT, "HIV": LEFT, "ALS": (0, -14, "center"), "Crohn's": (-6, 13, "left")},
    "trials": {"Psoriasis": ABOVE, "HIV": LEFT, "Crohn's": (-6, 13, "left"), "Schizophrenia": (9, 3, "left")},
}
PLOT_GROUPS = ["All ME/CFS (classic + post-COVID)"]
SPEC = {  # title, axis description, y ticks, y limits
    "papers": ("Papers vs disease burden", "Papers per year (2021–25 average)", [100, 1000, 10000], (70, 14000)),
    "trials": ("Trials vs disease burden", "Trials started per year (2021–25 average)", [10, 100], (5, 420)),
}
XS = [3e5, 6e7]
M = 0.055  # shared left margin, figure fraction
for metric in ("papers", "trials"):
    key = "pubs_per_year" if metric == "papers" else "trials_per_year"
    pts = [(math.log10(float(r["dalys"])), math.log10(float(r[key]))) for r in comp]
    a, b = fit(pts)
    my = sum(y for _, y in pts) / len(pts)
    r2 = 1 - sum((y - a - b * x) ** 2 for x, y in pts) / sum((y - my) ** 2 for _, y in pts)
    trend = lambda x: 10 ** (a + b * math.log10(x))
    title, desc, yticks, ylim = SPEC[metric]

    fig = plt.figure(figsize=(6, 6), facecolor=BG)
    ax = fig.add_axes([0.155, 0.20, 0.80, 0.65])
    ax.plot(XS, [trend(x) for x in XS], color=MUTED, lw=1.5, ls=(0, (4, 3)), zorder=1)
    for r in comp:
        x, y = float(r["dalys"]), float(r[key])
        ax.scatter(x, y, s=60, color=OCEAN, edgecolor=BG, linewidth=1.5, zorder=3)
        n = COMP_NAME.get(r["label"], r["label"])
        dx, dy, ha = COMP_OFF[metric].get(n, (9, 0, "left"))
        ax.annotate(n, (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center",
                    fontsize=12, color=MUTED)
    for (name, (med, lo, hi), _), r in zip(GROUPS, [o for o in out if o["metric"] == metric]):
        if name not in PLOT_GROUPS: continue
        x, y = med * 1e6, r["actual_per_year"]
        ax.plot([lo * 1e6, hi * 1e6], [y, y], color=SUNSET, lw=3, alpha=.5, zorder=3, solid_capstyle="round")
        ax.scatter(x, y, s=160, color=SUNSET, edgecolor=BG, linewidth=2, zorder=4)
        # three stacked lines with equal gaps: name, shortfall, range
        for dy, txt, fs, fw in ((52, "ME/CFS", 16, "bold"),
                                (32, f'{r["shortfall_median"]:g}× shortfall', 13.5, "normal"),
                                (13, f'({r["shortfall_p5_burden_and_fit"]:g}–{r["shortfall_p95_burden_and_fit"]:g}×)', 13.5, "normal")):
            ax.annotate(txt, (x, y), xytext=(0, dy), textcoords="offset points", ha="center", va="bottom",
                        fontsize=fs, fontweight=fw, color=SUNSET)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(*XS); ax.set_ylim(*ylim)
    ax.xaxis.set_major_locator(FixedLocator([1e6, 1e7]))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v/1e6:g}M"))
    ax.yaxis.set_major_locator(FixedLocator(yticks))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    for axis in (ax.xaxis, ax.yaxis):
        axis.set_minor_locator(LogLocator(base=10, subs=range(2, 10)))
        axis.set_minor_formatter(NullFormatter())
    ax.set_facecolor(BG); ax.grid(True, which="major", color=GRID, lw=1)
    for side in ("top", "right"): ax.spines[side].set_visible(False)
    for side in ("left", "bottom"): ax.spines[side].set_color(MUTED); ax.spines[side].set_linewidth(1.2)
    ax.tick_params(which="major", length=7, width=1.2, color=MUTED, pad=6)
    ax.tick_params(which="minor", length=4, width=1, color=MUTED)

    fig.text(M, 0.935, title, fontsize=20, fontweight="bold", color=INK, va="baseline")
    fig.text(M, 0.885, desc, fontsize=13, color=MUTED, va="baseline")
    fig.text(M, 0.105, "Disease burden (DALYs per year)", fontsize=13, color=MUTED, va="baseline")
    fig.text(M, 0.040, "ME/CFS: CCC burden, 90% range (model v11.2). Others: GBD 2023.",
             fontsize=10.5, color=MUTED, va="baseline")
    fig.text(1 - M, 0.040, "v14", fontsize=9, color=GRID, ha="right", va="baseline")
    # key for the trend line, in the empty lower-left corner of the plot
    ky = 0.15 if metric == "papers" else 0.06   # between gridlines
    ax.plot([0.03, 0.11], [ky, ky], transform=ax.transAxes, color=MUTED, lw=1.5, ls=(0, (4, 3)))
    ax.text(0.135, ky, f"trend, 13 diseases (R² = {r2:.2f})", transform=ax.transAxes,
            va="center", fontsize=12, color=MUTED)
    fig.savefig(f"analysis/{metric}_vs_dalys_ccc_2021-2025.png", dpi=300, facecolor=BG)

# --- one self-contained dataset with everything the two scatterplots need ---
fits = {}
for key in ("pubs_per_year", "trials_per_year"):
    pts = [(math.log10(float(r["dalys"])), math.log10(float(r[key]))) for r in comp]
    a_, b_ = fit(pts)
    my_ = sum(y for _, y in pts) / len(pts)
    fits[key] = (a_, b_, 1 - sum((y - a_ - b_ * x) ** 2 for x, y in pts) / sum((y - my_) ** 2 for _, y in pts))
rows_out = []
for r in comp:
    d = float(r["dalys"]); row = {"label": r["label"], "kind": "comparator", "burden_source": f'GBD 2023: {r["gbd_cause"]}',
        "interval": "95% UI", "dalys": round(d), "dalys_low": round(float(r["dalys_lower"])), "dalys_high": round(float(r["dalys_upper"])),
        "papers_per_year": float(r["pubs_per_year"]), "trials_per_year": float(r["trials_per_year"])}
    rows_out.append(row)
for (name, (med, lo, hi), src) in GROUPS:
    rows_out.append({"label": name, "kind": "ME/CFS or long COVID group",
                     "burden_source": "ME/CFS Burden model v11.2, CCC, year 2026", "interval": "90% range",
                     "dalys": round(med * 1e6), "dalys_low": round(lo * 1e6), "dalys_high": round(hi * 1e6),
                     "papers_per_year": round(pubs[src], 1), "trials_per_year": round(trials[src], 1)})
for row in rows_out:
    for key, short in (("pubs_per_year", "papers"), ("trials_per_year", "trials")):
        a_, b_, _ = fits[key]
        exp_ = 10 ** (a_ + b_ * math.log10(row["dalys"]))
        row[f"{short}_trend"] = round(exp_, 1)
        row[f"{short}_shortfall"] = round(exp_ / row[f"{short}_per_year"], 2)
        o = next((o for o in out if o["group"] == row["label"] and o["metric"] == short), None)
        row[f"{short}_shortfall_p5"] = o["shortfall_p5_burden_and_fit"] if o else ""
        row[f"{short}_shortfall_p95"] = o["shortfall_p95_burden_and_fit"] if o else ""
with open("analysis/plot_data_2021-2025.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows_out[0].keys()); w.writeheader(); w.writerows(rows_out)
print("trend fits (log10 papers or trials = a + b * log10 DALYs), 13 comparators:")
for k, (a_, b_, r2_) in fits.items(): print(f"  {k}: a={a_:.4f} b={b_:.4f} R2={r2_:.3f}")
