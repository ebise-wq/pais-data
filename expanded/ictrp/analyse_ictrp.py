"""Trials in all WHO ICTRP registries vs ClinicalTrials.gov only, 2021-2025.

Input: XML exports from the ICTRP search portal (trialsearch.who.int), one per search in
search_strings.txt, saved gzipped in raw/. Run from the repo root:
    python3 -I expanded/ictrp/analyse_ictrp.py

For each disease whose search terms were in an export:
- keep interventional trials (study type contains "interven", or ChiCTR "Prevention"/"Treatment study")
- year = first 4-digit year in the start date (Date_enrollement); if missing or implausible,
  the registration year
- a listed condition must match the same regex used for ClinicalTrials.gov
  (../diseases.py, or ../../clinicaltrials/fetch_counts.py for the original comparators);
  for ME/CFS the title may match too, as in the ClinicalTrials.gov method
- a non-ClinicalTrials.gov record whose secondary IDs include an NCT number is dropped as a
  duplicate of that ClinicalTrials.gov record, and records with the same public title are counted
  once (ClinicalTrials.gov first), which merges trials filed in two registries without a link
Output: ictrp_vs_ctgov_2021-2025.csv and mecfs_shortfall_adjusted.csv (ME/CFS trial shortfall
from ../fits_2021-2025.csv, scaled by comparator ratio / ME/CFS ratio)
Data: WHO International Clinical Trials Registry Platform (ICTRP), exported 2026-11-19.
"""
import collections, csv, glob, gzip, os, re, sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from diseases import D

YEARS = range(2021, 2026)
CT_INC = {  # same regex as ../../clinicaltrials/fetch_counts.py
    "ME/CFS": (r"chronic fatigue syndrome|myalgic|ME/CFS|\bCFS\b|systemic exertion intolerance", None, True),
    "Multiple sclerosis": (r"multiple sclerosis|\bMS\b|clinically isolated syndrome", r"tuberous|amyotrophic|systemic sclerosis", False),
    "Rheumatoid arthritis": (r"rheumatoid arthritis", r"juvenile", False),
    "Crohn's disease": (r"crohn", None, False),
    "Bipolar disorder": (r"bipolar", None, False),
    "Endometriosis": (r"endometrio", None, False),
    "ALS / motor neuron disease": (r"amyotrophic|\bALS\b|motor neuron", None, False),
}
# which diseases each export covers (export file stem -> diseases)
EXPORTS = {
    "export1": ["ME/CFS", "Lymphatic filariasis", "Cysticercosis", "Measles", "Food-borne trematodiases", "Neonatal sepsis",
                "Ascariasis", "Rheumatic heart disease", "Typhoid & paratyphoid", "Neonatal encephalopathy", "Meningitis",
                "Cystic echinococcosis", "Pertussis", "Scabies", "Leprosy", "Chagas disease", "Dengue", "Schistosomiasis",
                "Malaria"],
    "export2": ["Tuberculosis", "Hepatitis C", "Sickle cell disease", "Gout", "Polycystic ovary syndrome"],
    "export3": ["Multiple sclerosis", "Crohn's disease", "ALS / motor neuron disease"],
    "export4": ["Rheumatoid arthritis", "Bipolar disorder"],
    "export5": ["Endometriosis", "Glaucoma"],
}


def spec(name):
    if name in CT_INC:
        inc, exc, title_ok = CT_INC[name]
    else:
        inc, exc, title_ok = D[name]["inc"], D[name]["exc"], False
    return re.compile(inc, re.I), (re.compile(exc, re.I) if exc else None), title_ok


def txt(t, k):
    return (t.findtext(k) or "").strip()


def interventional(st):
    st = st.lower()
    return "interven" in st or st in ("prevention", "treatment study")


def year(t):
    for k in ("Date_enrollement",):
        m = re.search(r"(19|20)\d\d", txt(t, k))
        if m and 1990 <= int(m.group(0)) <= 2030:
            return int(m.group(0))
    r = txt(t, "Date_registration3")[:4]
    return int(r) if r.isdigit() else None


def matches(t, inc, exc, title_ok):
    conds = [c for c in re.split(r"[;\n]", txt(t, "Condition")) if c.strip()]
    hits = [c for c in conds if inc.search(c)]
    title = txt(t, "Public_title") + " " + txt(t, "Scientific_title")
    if not hits:
        return bool(title_ok and inc.search(title))
    if exc and all(exc.search(c) for c in hits) and not inc.search(title):
        return False
    return True


trials = {}
covered = []
for path in sorted(glob.glob(os.path.join(HERE, "raw", "export*.xml.gz"))):
    stem = os.path.basename(path).split(".")[0]
    covered += EXPORTS[stem]
    for t in ET.parse(gzip.open(path)).getroot().findall("Trial"):
        trials[txt(t, "TrialID")] = t

ctg = {r["disease"]: sum(int(r[str(y)]) for y in YEARS) / 5
       for r in csv.DictReader(open(os.path.join(HERE, "..", "..", "clinicaltrials", "trials_per_year_2026-11-08.csv")))}
exp_rows = {r["disease"]: r for r in csv.DictReader(open(glob.glob(os.path.join(HERE, "..", "counts_*.csv"))[0]))}
CTG_NAME = {"ME/CFS": "ME/CFS", "Multiple sclerosis": "Multiple sclerosis", "Rheumatoid arthritis": "Rheumatoid arthritis",
            "Crohn's disease": "Crohn's disease", "Bipolar disorder": "Bipolar disorder", "Endometriosis": "Endometriosis",
            "ALS / motor neuron disease": "ALS (rare ref.)"}

out = []
for name in covered:
    inc, exc, title_ok = spec(name)
    by_reg = collections.Counter()
    seen = {}
    kept = [t for t in trials.values() if interventional(txt(t, "Study_type")) and year(t) in YEARS and matches(t, inc, exc, title_ok)]
    kept.sort(key=lambda t: txt(t, "Source_Register") != "ClinicalTrials.gov")  # ClinicalTrials.gov records win ties
    for t in kept:
        reg = txt(t, "Source_Register")
        if reg != "ClinicalTrials.gov" and re.search(r"NCT\d{8}", txt(t, "Secondary_ID")):
            continue  # duplicate of a ClinicalTrials.gov record
        key = re.sub(r"[^a-z0-9]", "", txt(t, "Public_title").lower())[:80]
        if key and key in seen:
            continue  # same title already counted (e.g. a trial filed in both ChiCTR and ITMCTR)
        seen[key] = reg
        by_reg["ClinicalTrials.gov" if reg == "ClinicalTrials.gov" else reg] += 1
    n_ct = by_reg["ClinicalTrials.gov"]
    n_all = sum(by_reg.values())
    if name in CTG_NAME:
        ctgov_api = ctg[CTG_NAME[name]]
    else:
        ctgov_api = sum(int(exp_rows[name][f"trials_{y}"]) for y in YEARS) / 5
    no_cn = n_all - by_reg["ChiCTR"] - by_reg["ITMCTR"]
    others = ", ".join(f"{k} {v}" for k, v in by_reg.most_common() if k != "ClinicalTrials.gov")
    out.append({"disease": name, "ictrp_ctgov_records": n_ct, "ictrp_other_registries": n_all - n_ct, "ictrp_all": n_all,
                "ratio_all_to_ctgov": round(n_all / n_ct, 2) if n_ct else "",
                "ratio_excl_chictr_itmctr": round(no_cn / n_ct, 2) if n_ct else "",
                "ctgov_api_per_year": ctgov_api, "ictrp_all_per_year": round(n_all / 5, 1),
                "other_registries": others})

out.sort(key=lambda r: -(r["ratio_all_to_ctgov"] or 99))
with open(os.path.join(HERE, "ictrp_vs_ctgov_2021-2025.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=out[0].keys()); w.writeheader(); w.writerows(out)
# ---- effect on the ME/CFS trial shortfall ----
import statistics
base = float(next(r for r in csv.DictReader(open(os.path.join(HERE, "..", "fits_2021-2025.csv")))
                  if r["metric"] == "trials" and r["set"] == "All")["mecfs_shortfall"])
me = next(r for r in out if r["disease"] == "ME/CFS")
ref = [r for r in out if r["disease"] != "ME/CFS" and r["ictrp_ctgov_records"] >= 20]
orig = [r for r in out if r["disease"] in CT_INC and r["disease"] != "ME/CFS"]
summary = []
for col, label in (("ratio_all_to_ctgov", "all registries"), ("ratio_excl_chictr_itmctr", "excluding ChiCTR and ITMCTR")):
    for name, grp in ((f"median of {len(ref)} diseases with >=20 ClinicalTrials.gov trials", ref),
                      (f"median of the {len(orig)} original comparators covered", orig)):
        m = statistics.median(r[col] for r in grp)
        summary.append({"registries": label, "comparison": name, "comparator_ratio": round(m, 2),
                        "mecfs_ratio": me[col], "mecfs_trials_shortfall_ctgov": base,
                        "mecfs_trials_shortfall_adjusted": round(base * m / me[col], 1)})
with open(os.path.join(HERE, "mecfs_shortfall_adjusted.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=summary[0].keys()); w.writeheader(); w.writerows(summary)
for r in summary:
    print(r)
for r in out:
    print(f'{r["disease"]:28s} ctgov(ictrp) {r["ictrp_ctgov_records"]:4d}  other {r["ictrp_other_registries"]:4d}  '
          f'ratio {r["ratio_all_to_ctgov"]!s:5s}  ctgov API/yr {r["ctgov_api_per_year"]:6.1f}  all/yr {r["ictrp_all_per_year"]:6.1f}  | {r["other_registries"][:70]}')
