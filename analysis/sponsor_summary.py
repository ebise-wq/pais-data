"""Summarise clinicaltrials/sponsor_trials_<date>.csv: commercial vs non-commercial drug trials.

Run from repo root: python3 -I analysis/sponsor_summary.py clinicaltrials/sponsor_trials_2026-11-25.csv
Writes analysis/sponsor_by_disease_2021-2025.csv and analysis/sponsor_by_year_2020-2026.csv.
"""
import csv, re, statistics, sys, collections
src = sys.argv[1]
R = list(csv.DictReader(open(src)))
for r in R:
    r["start_year"] = int(r["start_year"]); r["commercial"] = int(r["commercial"])
    r["industry_collaborator"] = int(r["industry_collaborator"])
# Large pharma: top 20 drug companies by 2024 revenue, matched on lead sponsor name (incl. main subsidiaries).
BIG = re.compile(r"Pfizer|Johnson ?& ?Johnson|Janssen|Roche|Genentech|Chugai|Merck Sharp|\bMSD\b|AbbVie|Allergan|"
                 r"AstraZeneca|MedImmune|Alexion|Novartis|Sandoz|Bristol|Celgene|Eli Lilly|Lilly|Sanofi|Genzyme|"
                 r"Novo Nordisk|GlaxoSmithKline|\bGSK\b|ViiV|Amgen|Takeda|Shire|Boehringer|Gilead|Kite|Bayer|"
                 r"Teva|Regeneron|Vertex|Moderna|Astellas|Daiichi", re.I)
for r in R:
    r["large_pharma"] = int(r["commercial"] and bool(BIG.search(r["lead_sponsor"])))

diseases = list(dict.fromkeys(r["disease"] for r in R))
out = []
for d in diseases:
    x = [r for r in R if r["disease"] == d and 2021 <= r["start_year"] <= 2025]
    n = len(x); c = sum(r["commercial"] for r in x)
    out.append({"disease": d, "group": x[0]["group"] if x else "", "dalys": R[[r["disease"] for r in R].index(d)]["dalys"],
                "drug_trials_2021_2025": n, "commercial": c, "non_commercial": n - c,
                "commercial_share": round(c / n, 3) if n else "",
                "non_commercial_with_industry_collaborator": sum(1 for r in x if not r["commercial"] and r["industry_collaborator"]),
                "large_pharma_led": sum(r["large_pharma"] for r in x),
                "commercial_per_year": c / 5, "non_commercial_per_year": (n - c) / 5})
with open("analysis/sponsor_by_disease_2021-2025.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=out[0].keys()); w.writeheader(); w.writerows(out)

yr = []
for d in diseases:
    for y in range(2020, 2027):
        x = [r for r in R if r["disease"] == d and r["start_year"] == y]
        yr.append({"disease": d, "year": y, "drug_trials": len(x), "commercial": sum(r["commercial"] for r in x)})
with open("analysis/sponsor_by_year_2020-2026.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=yr[0].keys()); w.writeheader(); w.writerows(yr)

print(f"{'disease':30s} {'grp':10s} {'DALYs':>5s} {'n':>5s} {'comm':>5s} {'share':>6s} {'big':>4s} {'comm/yr':>8s} {'non/yr':>7s}")
for o in sorted(out, key=lambda o: -(o["commercial_share"] or 0)):
    print(f"{o['disease'][:30]:30s} {o['group'][:10]:10s} {float(o['dalys'])/1e6:5.1f} {o['drug_trials_2021_2025']:5d} {o['commercial']:5d} "
          f"{o['commercial_share']:6.0%} {o['large_pharma_led']:4d} {o['commercial_per_year']:8.1f} {o['non_commercial_per_year']:7.1f}")
comp = [o for o in out if o["disease"] not in ("Long COVID", "ME/CFS")]
for lab, sub in [("all 24", comp), ("non-cancer 16", [o for o in comp if o["group"] != "Cancer"]),
                 ("NCD non-cancer", [o for o in comp if o["group"] == "NCD"])]:
    print(lab, "median share", round(statistics.median(o["commercial_share"] for o in sub), 2),
          "median comm/yr", statistics.median(o["commercial_per_year"] for o in sub),
          "median noncomm/yr", statistics.median(o["non_commercial_per_year"] for o in sub),
          "pooled share", round(sum(o["commercial"] for o in sub) / sum(o["drug_trials_2021_2025"] for o in sub), 2))
# Year trend in commercial share, pooled comparators
for lab, keep in [("comparators", lambda d: d not in ("Long COVID", "ME/CFS")),
                  ("non-cancer comps", lambda d: d not in ("Long COVID", "ME/CFS") and [o for o in out if o["disease"] == d][0]["group"] != "Cancer")]:
    print(lab, [(y, round(sum(r["commercial"] for r in R if keep(r["disease"]) and r["start_year"] == y) /
                       max(1, sum(1 for r in R if keep(r["disease"]) and r["start_year"] == y)), 2)) for y in range(2020, 2027)])
