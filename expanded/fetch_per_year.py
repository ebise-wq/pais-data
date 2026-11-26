"""PubMed papers and ClinicalTrials.gov interventional trials per year, 1996-2025, for the 111 causes in diseases.py.

Same searches and filters as fetch.py (title search by [edat]; query.cond, then keep studies whose listed
conditions match the disease regex; interventional; by start year), but for every year from 1996. The 13
original comparators and ME/CFS already have yearly counts in ../clinicaltrials/ and ../pubmed/.

Run from the repo root: python3 -I expanded/fetch_per_year.py
Writes expanded/per_year_<date>.csv (one row per disease and year). ClinicalTrials.gov pages are cached in
expanded/cache/all_*.json and PubMed counts in expanded/cache/pubmed_per_year.json (not committed), so an
interrupted run picks up where it stopped.
"""
import csv, datetime, json, os, re, sys, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diseases import D
from fetch import CACHE, CTG, FIELDS, get, keep, pubmed_count

YEARS = list(range(1996, 2026))
HERE = os.path.dirname(os.path.abspath(__file__))
PM_CACHE = os.path.join(CACHE, "pubmed_per_year.json")


def ctg_all(name, cond):
    """All interventional studies for the condition query, any start date."""
    fn = os.path.join(CACHE, "all_" + re.sub(r"\W+", "_", name) + ".json")
    if os.path.exists(fn):
        return json.load(open(fn))
    out, tok = [], None
    while True:
        p = {"query.cond": cond, "pageSize": 1000, "fields": FIELDS, "filter.advanced": "AREA[StudyType]INTERVENTIONAL"}
        if tok:
            p["pageToken"] = tok
        d = get(CTG + "?" + urllib.parse.urlencode(p), parse_json=True)
        out += d.get("studies", [])
        tok = d.get("nextPageToken")
        if not tok:
            break
    os.makedirs(CACHE, exist_ok=True)
    json.dump(out, open(fn, "w"))
    return out


def trials_by_year(name, spec):
    inc = re.compile(spec["inc"], re.I)
    exc = re.compile(spec["exc"], re.I) if spec["exc"] else None
    per = {y: 0 for y in YEARS}
    for s in ctg_all(name, spec["cond"]):
        ps = s["protocolSection"]
        if ps.get("designModule", {}).get("studyType") != "INTERVENTIONAL" or not keep(s, inc, exc):
            continue
        sd = ps.get("statusModule", {}).get("startDateStruct", {}).get("date")
        if sd and int(sd[:4]) in per:
            per[int(sd[:4])] += 1
    return per


if __name__ == "__main__":
    pm = json.load(open(PM_CACHE)) if os.path.exists(PM_CACHE) else {}
    rows = []
    for n, spec in D.items():
        got = pm.setdefault(n, {})
        for y in YEARS:
            if str(y) not in got:
                got[str(y)] = pubmed_count(f"({spec['pm']}) AND {y}[edat]")
        os.makedirs(CACHE, exist_ok=True)
        json.dump(pm, open(PM_CACHE, "w"))
        trials = trials_by_year(n, spec)
        rows += [{"disease": n, "year": y, "papers": got[str(y)], "trials": trials[y]} for y in YEARS]
        print(f"{n:45s} papers 2025 {got['2025']:6d}  trials 2025 {trials[2025]:4d}", flush=True)
    out = os.path.join(HERE, f"per_year_{datetime.date.today().isoformat()}.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["disease", "year", "papers", "trials"]); w.writeheader(); w.writerows(rows)
    print("Wrote", out)
