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
    ("Non-COVID (classic) ME/CFS", (7.7, 3.2, 18.7), "ME/CFS"),
    ("All ME/CFS (classic + post-COVID)", (17.5, 9.9, 31.7), "ME/CFS"),
    ("Long COVID, incl. post-COVID ME", (19.8, 12.4, 31.7), "Long COVID"),
    ("Long COVID + non-COVID ME/CFS", (28.3, 18.3, 44.7), "union"),
]

def avg(path):
    with open(path) as f:
        return {r["disease"]: sum(int(r[y]) for y in YEARS) / len(YEARS) for r in csv.DictReader(f)}

pubs, trials = avg("pubmed/pubs_per_year_2026-11-08.csv"), avg("clinicaltrials/trials_per_year_2026-11-08.csv")
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

# --- plots: scatter of the 13 comparison diseases plus the four CCC groups ---
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
BG, INK, MUTED, GRID = "#141a24", "#e6e9ef", "#9aa3b2", "#2a3342"
OCEAN, SUNSET, ROSE = "#7fb3d5", "#f4a582", "#e8a0bf"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "text.color": INK,
                     "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED})
SHORT = {"Non-COVID (classic) ME/CFS": "Classic ME/CFS", "All ME/CFS (classic + post-COVID)": "All ME/CFS",
         "Long COVID, incl. post-COVID ME": "Long COVID", "Long COVID + non-COVID ME/CFS": "Long COVID +\nclassic ME/CFS"}
# label offsets in points (dx, dy, ha) per metric
GROUP_OFF = {
    "papers": {"Classic ME/CFS": (-10, 0, "right"), "All ME/CFS": (10, 0, "left"),
               "Long COVID": (-30, -60, "right"), "Long COVID +\nclassic ME/CFS": (12, 4, "left")},
    "trials": {"Classic ME/CFS": (-10, 0, "right"), "All ME/CFS": (10, 0, "left"),
               "Long COVID": (20, -75, "left"), "Long COVID +\nclassic ME/CFS": (12, 4, "left")},
}
COMP_OFF = {
    "papers": {"Epilepsy": (0, 9, "center"), "Parkinson's disease": (-8, 6, "right"),
               "Rheumatoid arthritis": (8, 6, "left"), "Psoriasis": (-9, -3, "right"),
               "Type 1 diabetes": (9, -4, "left"), "Schizophrenia": (0, 9, "center"),
               "Bipolar disorder": (0, -14, "center"), "Crohn's disease": (0, 9, "center"),
               "Ulcerative colitis": (-8, 6, "right"), "ALS / motor neuron disease": (-4, -14, "right"),
               "Endometriosis": (9, -4, "left")},
    "trials": {"Schizophrenia": (0, 9, "center"), "Epilepsy": (-9, -3, "right"),
               "Bipolar disorder": (0, 9, "center"), "Multiple sclerosis": (-9, -3, "right"),
               "Crohn's disease": (-6, 9, "left")},
}
# small vertical shift of the range bars only, so overlapping ranges stay readable
WHISKER_SHIFT = {"Classic ME/CFS": 0.93, "All ME/CFS": 1.07, "Long COVID": 0.96, "Long COVID +\nclassic ME/CFS": 1.04}
TITLES = {"papers": ("PubMed publications per year", "Papers per year, 2021–2025 average (title search)"),
          "trials": ("Interventional trials per year", "Trials started per year, 2021–2025 average")}
for metric in ("papers", "trials"):
    key = "pubs_per_year" if metric == "papers" else "trials_per_year"
    pts = [(math.log10(float(r["dalys"])), math.log10(float(r[key]))) for r in comp]
    a, b = fit(pts)
    r2 = 1 - sum((y - a - b * x) ** 2 for x, y in pts) / sum((y - sum(q for _, q in pts) / len(pts)) ** 2 for _, y in pts)
    fig, ax = plt.subplots(figsize=(8.5, 6.4), facecolor=BG)
    xs = [2.5e5, 1e8]
    ax.plot(xs, [10 ** (a + b * math.log10(x)) for x in xs], color=MUTED, lw=1, ls="--", zorder=1)
    for r in comp:
        x, y = float(r["dalys"]), float(r[key])
        ax.plot([float(r["dalys_lower"]), float(r["dalys_upper"])], [y, y], color=OCEAN, lw=1, alpha=.4, zorder=2)
        ax.scatter(x, y, s=50, color=OCEAN, edgecolor=BG, linewidth=2, zorder=3)
        dx, dy, ha = COMP_OFF[metric].get(r["label"], (7, 5, "left"))
        ax.annotate(r["label"], (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, fontsize=8, color=MUTED)
    for (name, (med, lo, hi), _), r in zip(GROUPS, [o for o in out if o["metric"] == metric]):
        c = ROSE if "Long COVID" in name else SUNSET
        x, y, e = med * 1e6, r["actual_per_year"], r["expected_per_year"]
        ax.plot([x, x], [y, e], color=c, lw=1, ls=":", alpha=.8, zorder=2)
        wy = y * WHISKER_SHIFT[SHORT[name]]
        ax.plot([lo * 1e6, hi * 1e6], [wy, wy], color=c, lw=2, alpha=.55, zorder=2, solid_capstyle="round")
        ax.scatter(x, y, s=85, color=c, edgecolor=BG, linewidth=2, zorder=4)
        lab = SHORT[name]
        dx, dy, ha = GROUP_OFF[metric][lab]
        ax.annotate(f'{lab}\n{r["shortfall_median"]:g}× short ({r["shortfall_p5_burden"]:g}–{r["shortfall_p95_burden"]:g})',
                    (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center",
                    arrowprops=dict(arrowstyle="-", color=c, lw=.8, alpha=.7) if abs(dy) > 20 else None,
                    fontsize=8.5, color=INK, fontweight="bold", linespacing=1.15)
    lo_y = min(o["actual_per_year"] for o in out if o["metric"] == metric)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(*xs)
    _, hi_y = ax.get_ylim(); ax.set_ylim(lo_y / 2, hi_y * 1.3)
    t, yl = TITLES[metric]
    ax.set_title(t, loc="left", color=INK, fontsize=12, pad=10)
    ax.set_xlabel("Global DALYs per year"); ax.set_ylabel(yl)
    ax.text(0.01, 0.98, f"dashed: log-log fit to the 13 other diseases, R²={r2:.2f}", transform=ax.transAxes,
            ha="left", va="top", fontsize=7.5, color=MUTED)
    ax.set_facecolor(BG); ax.grid(True, which="major", color=GRID, lw=.6)
    for sp in ax.spines.values(): sp.set_color(GRID)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v/1e6:g}M"))
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    fig.text(0.01, 0.01, "ME/CFS and long COVID: CCC burden, ME/CFS Burden model v11.2 (2026), median and 90% range.\n"
             "Other diseases: GBD 2023, 95% UI. Shortfall = trend ÷ actual.  v5", color=MUTED, fontsize=7.5, va="bottom")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(f"analysis/{metric}_vs_dalys_ccc_2021-2025.png", dpi=160, facecolor=BG)
