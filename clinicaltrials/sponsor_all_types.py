"""Lead sponsor class for every interventional long COVID and ME/CFS trial started 2020-2026, of any type.

sponsor_class.py covers drug or biologic trials only. This adds the other interventional trials
(behavioural, device, dietary supplement, procedure, ...) for long COVID and ME/CFS, so the trials chart
can split all trial types by sponsor too. Same trial selection (the NCT IDs in nct_ids_2026-11-08.json),
same sponsor rule (INDUSTRY = commercial) and the same manual override as sponsor_class.py.

Run from repo root: python3 -I clinicaltrials/sponsor_all_types.py
Writes clinicaltrials/sponsor_all_types_<date>.csv (one row per trial per disease).
"""
import csv, datetime, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python3 -I leaves the script folder off the path
from sponsor_class import ROOT, DRUG, YEARS, by_ids, cached, row

ids = json.load(open(os.path.join(ROOT, "clinicaltrials", "nct_ids_2026-11-08.json")))
rows = []
for name in ("Long COVID", "ME/CFS"):
    S = cached(f"all_types_{name}", lambda: by_ids(ids[name]))
    for s in S:
        ps = s["protocolSection"]
        if ps.get("designModule", {}).get("studyType") != "INTERVENTIONAL":
            continue
        sd = ps.get("statusModule", {}).get("startDateStruct", {}).get("date", "")
        if not sd or int(sd[:4]) not in YEARS:
            continue
        types = sorted({x.get("type", "") for x in ps.get("armsInterventionsModule", {}).get("interventions", [])})
        r = row(name, name, "", ps)
        rows.append({"disease": name, "nct_id": r["nct_id"], "start_year": r["start_year"],
                     "drug_or_biologic": int(bool(set(types) & DRUG)), "intervention_types": "|".join(types),
                     "lead_sponsor": r["lead_sponsor"], "lead_class": r["lead_class"], "commercial": r["commercial"],
                     "title": r["title"]})
    R = [r for r in rows if r["disease"] == name]
    print(f"{name}: {len(R)} interventional trials 2020-2026, {sum(r['commercial'] for r in R)} commercial")
out = os.path.join(ROOT, "clinicaltrials", f"sponsor_all_types_{datetime.date.today()}.csv")
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
print("wrote", out, len(rows))
