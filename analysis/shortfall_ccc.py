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
