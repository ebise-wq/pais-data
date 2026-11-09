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

# --- plots: scatter of the 13 comparison diseases plus the four CCC groups (sized for phones) ---
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
BG, INK, MUTED, GRID = "#141a24", "#e6e9ef", "#8b94a3", "#252d3a"
OCEAN, SUNSET, ROSE = "#7fb3d5", "#f4a582", "#e8a0bf"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "text.color": INK,
                     "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED})
SHORT = {"Non-COVID (classic) ME/CFS": "Classic ME/CFS", "All ME/CFS (classic + post-COVID)": "All ME/CFS",
         "Long COVID, incl. post-COVID ME": "Long COVID", "Long COVID + non-COVID ME/CFS": "Long COVID\n+ classic ME/CFS"}
COMP_NAME = {"Multiple sclerosis": "MS", "Rheumatoid arthritis": "RA", "Type 1 diabetes": "T1D",
             "ALS / motor neuron disease": "ALS", "Ulcerative colitis": "UC", "HIV/AIDS": "HIV",
             "Parkinson's disease": "Parkinson's", "Bipolar disorder": "Bipolar", "Crohn's disease": "Crohn's"}
GROUP_OFF = {  # (dx, dy, ha) in points
    "papers": {"Classic ME/CFS": (-12, 0, "right"), "All ME/CFS": (0, -34, "center"),
               "Long COVID": (14, -60, "left"), "Long COVID\n+ classic ME/CFS": (12, 6, "left")},
    "trials": {"Classic ME/CFS": (-12, 0, "right"), "All ME/CFS": (0, -34, "center"),
               "Long COVID": (14, -60, "left"), "Long COVID\n+ classic ME/CFS": (12, 6, "left")},
}
COMP_OFF = {  # labels sit above or below the dot so they clear the range bar
    "papers": {"Parkinson's": (0, 11, "center"), "Epilepsy": (0, 11, "center"), "Schizophrenia": (0, 11, "center"),
               "HIV": (0, 11, "center"), "MS": (0, 11, "center"), "RA": (0, 11, "center"),
               "Psoriasis": (-4, 11, "right"), "T1D": (0, -13, "center"), "UC": (0, 11, "center"),
               "Crohn's": (0, 11, "center"), "ALS": (-6, -13, "center"), "Endometriosis": (8, -13, "center"),
               "Bipolar": (0, -13, "center")},
    "trials": {"Parkinson's": (0, 11, "center"), "HIV": (0, 11, "center"), "MS": (0, 11, "center"),
               "T1D": (0, 11, "center"), "Schizophrenia": (0, 11, "center"), "Epilepsy": (0, -13, "center"),
               "Psoriasis": (0, 11, "center"), "RA": (0, -13, "center"), "Crohn's": (0, 11, "center"),
               "UC": (0, 11, "center"), "ALS": (-24, 0, "right"), "Endometriosis": (0, -13, "center"),
               "Bipolar": (0, -13, "center")},
}
PLOT_GROUPS = ["All ME/CFS (classic + post-COVID)"]
TITLES = {"papers": ("Papers per year vs disease burden", "Papers per year (2021–2025 avg)"),
          "trials": ("Trials per year vs disease burden", "Interventional trials per year (2021–2025 avg)")}
for metric in ("papers", "trials"):
    key = "pubs_per_year" if metric == "papers" else "trials_per_year"
    pts = [(math.log10(float(r["dalys"])), math.log10(float(r[key]))) for r in comp]
    a, b = fit(pts)
    fig, ax = plt.subplots(figsize=(7, 7), facecolor=BG)
    xs = [3e5, 6e7]
    ax.plot(xs, [10 ** (a + b * math.log10(x)) for x in xs], color=MUTED, lw=1.2, ls="--", zorder=1)
    for r in comp:
        x, y = float(r["dalys"]), float(r[key])
        ax.plot([float(r["dalys_lower"]), float(r["dalys_upper"])], [y, y], color=OCEAN, lw=1, alpha=.35, zorder=2)
        ax.scatter(x, y, s=45, color=OCEAN, edgecolor=BG, linewidth=1.5, zorder=3)
        n = COMP_NAME.get(r["label"], r["label"])
        dx, dy, ha = COMP_OFF[metric].get(n, (7, 3, "left"))
        ax.annotate(n, (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center", fontsize=10, color=MUTED)
    for (name, (med, lo, hi), _), r in zip(GROUPS, [o for o in out if o["metric"] == metric]):
        if name not in PLOT_GROUPS: continue
        c = ROSE if "Long COVID" in name else SUNSET
        x, y = med * 1e6, r["actual_per_year"]
        ax.plot([lo * 1e6, hi * 1e6], [y, y], color=c, lw=2.5, alpha=.6, zorder=3, solid_capstyle="round")
        ax.scatter(x, y, s=110, color=c, edgecolor=BG, linewidth=2, zorder=4)
        lab = SHORT[name]
        dx, dy, ha = GROUP_OFF[metric][lab]
        ax.annotate(f'{lab}\n{r["shortfall_median"]:g}× shortfall\n({r["shortfall_p5_burden_and_fit"]:g}–{r["shortfall_p95_burden_and_fit"]:g}×)', (x, y), xytext=(dx, dy), textcoords="offset points",
                    ha=ha, va="center", fontsize=11.5, color=c, fontweight="bold", linespacing=1.1,
                    arrowprops=None)
    lo_y = min(o["actual_per_year"] for o in out if o["metric"] == metric)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(*xs)
    _, hi_y = ax.get_ylim(); ax.set_ylim(lo_y / 3, hi_y * 1.15)
    t, yl = TITLES[metric]
    ax.set_title(t, loc="left", color=INK, fontsize=15, pad=12)
    ax.set_xlabel("Global DALYs per year"); ax.set_ylabel(yl)
    ax.set_facecolor(BG); ax.grid(True, which="major", color=GRID, lw=.8)
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.tick_params(length=0)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v/1e6:g}M"))
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    fig.text(0.02, 0.012, "ME/CFS: CCC burden, median and 90% range (ME/CFS Burden model v11.2). Shortfall range\n"
             "includes trend-fit uncertainty. Others: GBD 2023, 95% UI. Shortfall = trend ÷ actual.  v8", color=MUTED, fontsize=8.5, va="bottom")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    # "trend" label rotated to follow the dashed line (angle measured on screen, after layout)
    tx = xs[1] / 1.6
    (x1, y1), (x2, y2) = ax.transData.transform([(tx, 10 ** (a + b * math.log10(tx))),
                                                 (tx * 2, 10 ** (a + b * math.log10(tx * 2)))])
    ax.annotate("trend", (tx, 10 ** (a + b * math.log10(tx))), xytext=(0, 5), textcoords="offset points",
                rotation=math.degrees(math.atan2(y2 - y1, x2 - x1)), rotation_mode="anchor",
                ha="center", va="bottom", color=MUTED, fontsize=10)
    fig.savefig(f"analysis/{metric}_vs_dalys_ccc_2021-2025.png", dpi=200, facecolor=BG)
