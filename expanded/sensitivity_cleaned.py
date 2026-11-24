"""Refit the burden-vs-research trend with cleaned counts and compare with the main analysis.

Papers: papers_cleaned_2021-2025.csv (veterinary filter, abbreviation fixes).
Trials: trials_title_filtered_2021-2025.csv, weighted count (title names the disease = 1, else share of
listed conditions that match). Same 120 diseases as analyse.py; ME/CFS as "All ME/CFS" (CCC model DALYs).
Output: sensitivity_cleaned_2021-2025.csv. Run from repo root: python3 -I expanded/sensitivity_cleaned.py
"""
import csv, math, os
HERE = os.path.dirname(os.path.abspath(__file__))
base = list(csv.DictReader(open(os.path.join(HERE, "burden_vs_research_expanded_2021-2025.csv"))))
pc = {r["disease"]: float(r["papers_cleaned_per_year"]) for r in csv.DictReader(open(os.path.join(HERE, "papers_cleaned_2021-2025.csv")))}
tc = {r["disease"]: float(r["trials_weighted_per_year"]) for r in csv.DictReader(open(os.path.join(HERE, "trials_title_filtered_2021-2025.csv")))}
ME = {"dalys": 17.5e6, "papers": 216.8, "trials": 10.2, "papers_clean": pc["ME/CFS"], "trials_clean": tc["ME/CFS"]}


def fit(P):
    n = len(P); mx = sum(x for x, _ in P) / n; my = sum(y for _, y in P) / n
    b = sum((x - mx) * (y - my) for x, y in P) / sum((x - mx) ** 2 for x, _ in P); a = my - b * mx
    r2 = 1 - sum((y - a - b * x) ** 2 for x, y in P) / sum((y - my) ** 2 for _, y in P)
    return a, b, r2


out = []
for metric, rawk in (("papers", "papers_per_year"), ("trials", "trials_per_year")):
    clean = pc if metric == "papers" else tc
    for version in ("main", "cleaned"):
        vals = {r["label"]: (float(r["dalys"]), float(r[rawk]) if version == "main" else clean[r["label"]]) for r in base}
        P = [(math.log10(d), math.log10(v)) for d, v in vals.values() if v > 0]
        a, b, r2 = fit(P)
        me_v = ME[metric] if version == "main" else ME[metric + "_clean"]
        resid = {k: math.log10(v) - (a + b * math.log10(d)) for k, (d, v) in vals.items() if v > 0}
        me_r = math.log10(me_v) - (a + b * math.log10(ME["dalys"]))
        lower = sorted((k for k, e in resid.items() if e < me_r), key=lambda k: resid[k])
        out.append({"metric": metric, "version": version, "n": len(P), "slope": round(b, 3), "r2": round(r2, 3),
                    "mecfs_per_year": me_v, "mecfs_shortfall": round(10 ** -me_r, 1), "n_below_mecfs": len(lower),
                    "below_mecfs": "; ".join(lower)})
with open(os.path.join(HERE, "sensitivity_cleaned_2021-2025.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=out[0].keys()); w.writeheader(); w.writerows(out)
for r in out:
    print({k: v for k, v in r.items() if k != "below_mecfs"}); print("   below:", r["below_mecfs"][:300])
