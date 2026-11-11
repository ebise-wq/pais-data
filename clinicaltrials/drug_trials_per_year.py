"""Drug/biologic trials per start year for ME/CFS and long COVID.

Uses the NCT IDs already selected in nct_ids_2026-11-08.json and re-fetches study type,
intervention types and start date from the ClinicalTrials.gov API v2.
Definition matches fetch_counts.py: interventional, with a DRUG, BIOLOGICAL or GENETIC intervention.
Run from repo root: python3 -I clinicaltrials/drug_trials_per_year.py
"""
import csv, json, time, urllib.parse, urllib.request, collections, datetime

ids = json.load(open("clinicaltrials/nct_ids_2026-11-08.json"))
API = "https://clinicaltrials.gov/api/v2/studies"
FIELDS = "NCTId,StudyType,StartDate,InterventionType"
info = {}
want = sorted(set(ids["ME/CFS"]) | set(ids["Long COVID"]))
for i in range(0, len(want), 100):
    batch = want[i:i + 100]
    q = urllib.parse.urlencode({"filter.ids": ",".join(batch), "fields": FIELDS, "pageSize": 100})
    for s in json.load(urllib.request.urlopen(f"{API}?{q}"))["studies"]:
        ps = s["protocolSection"]
        info[ps["identificationModule"]["nctId"]] = {
            "type": ps.get("designModule", {}).get("studyType"),
            "start": ps.get("statusModule", {}).get("startDateStruct", {}).get("date", ""),
            "itypes": {x.get("type") for x in ps.get("armsInterventionsModule", {}).get("interventions", [])}}
    time.sleep(0.3)
missing = [n for n in want if n not in info]
print("fetched", len(info), "of", len(want), "missing", missing[:5])

years = list(range(2015, 2027))
rows = []
for d in ("ME/CFS", "Long COVID"):
    c, total = collections.Counter(), 0
    for n in ids[d]:
        s = info.get(n)
        if not s or s["type"] != "INTERVENTIONAL" or not s["itypes"] & {"DRUG", "BIOLOGICAL", "GENETIC"}: continue
        total += 1
        if s["start"]: c[int(s["start"][:4])] += 1
    rows.append({"disease": d, "total_drug_or_biologic": total, **{str(y): c[y] for y in years}})
    print(d, "total", total, {y: c[y] for y in years})
out = f"clinicaltrials/drug_trials_per_year_{datetime.date.today()}.csv"
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
print("wrote", out)
