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

# --- plots: one per metric ---
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
BG, INK, MUTED, GRID = "#141a24", "#e6e9ef", "#9aa3b2", "#2a3342"
OCEAN, SUNSET = "#7fb3d5", "#f4a582"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "text.color": INK,
                     "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": INK})
TITLES = {"papers": "Publication shortfall, 2021–2025", "trials": "Interventional trial shortfall, 2021–2025"}
for metric in ("papers", "trials"):
    rows = [r for r in out if r["metric"] == metric][::-1]
    fig, ax = plt.subplots(figsize=(8, 4.2), facecolor=BG)
    ax.axvline(1, color=MUTED, lw=1, ls="--", zorder=1)
    ax.text(1.04, len(rows) - 0.45, "on trend", color=MUTED, fontsize=8, va="center")
    for i, r in enumerate(rows):
        c = SUNSET if "ME/CFS" in r["group"] and "Long COVID" not in r["group"] else OCEAN
        ax.plot([r["shortfall_p5_burden_and_fit"], r["shortfall_p95_burden_and_fit"]], [i, i], color=c, lw=1.2, alpha=.5)
        ax.plot([r["shortfall_p5_burden"], r["shortfall_p95_burden"]], [i, i], color=c, lw=5, alpha=.8,
                solid_capstyle="round")
        ax.scatter(r["shortfall_median"], i, s=70, color=c, edgecolor=BG, linewidth=2, zorder=3)
        ax.text(r["shortfall_p95_burden_and_fit"] * 1.08, i, f'{r["shortfall_median"]:g}×', va="center",
                color=INK, fontsize=10, fontweight="bold")
        ax.text(r["shortfall_p95_burden_and_fit"] * 1.08, i - 0.28,
                f'{r["actual_per_year"]:{".0f" if metric == "papers" else ".1f"}} vs ~{r["expected_per_year"]:,} /yr', va="center", color=MUTED, fontsize=7.5)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([f'{r["group"]}\n{r["dalys_M"]:g}M DALYs' for r in rows], fontsize=9)
    ax.set_xscale("log"); ax.set_xlim(0.5, 80)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}×"))
    ax.set_xticks([0.5, 1, 2, 5, 10, 20, 50])
    ax.set_xlabel("Expected ÷ actual per year (log scale)")
    ax.set_ylim(-0.6, len(rows) - 0.3)
    ax.set_title(TITLES[metric], loc="left", color=INK, fontsize=12, pad=10)
    ax.set_facecolor(BG); ax.grid(True, axis="x", color=GRID, lw=.6)
    for s in ax.spines.values(): s.set_color(GRID)
    ax.tick_params(axis="y", length=0)
    fig.text(0.01, 0.01, "CCC burden, ME/CFS Burden model v11.2. Thick bar: 90% range from burden; "
             "thin: also trend-fit uncertainty.  v4", color=MUTED, fontsize=7.5)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(f"analysis/shortfall_{metric}_ccc_2021-2025.png", dpi=160, facecolor=BG)
