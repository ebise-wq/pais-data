"""Drug/biologic trials by sponsor type: long COVID, ME/CFS and diseases with 10-30M DALYs.

Sponsor type comes from ClinicalTrials.gov's lead sponsor class. INDUSTRY = commercial.
Every other class (OTHER = universities, hospitals, charities; NIH; FED; OTHER_GOV; NETWORK;
INDIV; UNKNOWN) = non-commercial. We also record whether a non-commercial trial lists an
industry collaborator (often a company that supplies the drug or money).

Trial selection matches the earlier work:
- Long COVID, ME/CFS, schizophrenia, epilepsy: the NCT IDs in nct_ids_2026-11-08.json
  (same selection as drug_trials_per_year.py and the long COVID chart).
- The other 22 comparators: expanded/diseases.py query and condition regex, as in expanded/fetch.py.
- Drug/biologic = interventional with a DRUG, BIOLOGICAL or GENETIC intervention. Start years 2020-2026.

Comparators = causes in expanded/burden_vs_research_expanded_2021-2025.csv with 10-30M DALYs (GBD 2023).
Run from repo root: python3 -I clinicaltrials/sponsor_class.py
Writes clinicaltrials/sponsor_trials_<date>.csv (one row per trial per disease).
"""
import csv, datetime, json, os, re, sys, time, urllib.parse, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "expanded"))
from diseases import D

API = "https://clinicaltrials.gov/api/v2/studies"
FIELDS = ("NCTId,BriefTitle,Condition,StudyType,StartDate,InterventionType,Phase,"
          "LeadSponsorName,LeadSponsorClass,CollaboratorName,CollaboratorClass")
DRUG = {"DRUG", "BIOLOGICAL", "GENETIC"}
YEARS = range(2020, 2027)
CACHE = os.path.join(ROOT, "clinicaltrials", "cache_sponsor")
# Manual corrections where the registry's lead sponsor hides the company that runs and funds the trial.
OVERRIDES = {
    # CT38 (Cortene Inc.). Registry lead sponsor is the site PI (Lucinda Bateman, class OTHER), no company
    # listed. Cortene developed CT38 and funded the trial (Health Rising, 3 Sep 2021). Started 2018.
    "NCT03613129": {"lead_sponsor": "Cortene Inc. (registry: Lucinda Bateman, MD)", "lead_class": "INDUSTRY"},
}


def get(params):
    err = None
    for i in range(6):
        try:
            return json.load(urllib.request.urlopen(API + "?" + urllib.parse.urlencode(params), timeout=120))
        except Exception as e:
            err = e; time.sleep(2 ** i)
    raise err


def cached(name, fn):
    path = os.path.join(CACHE, re.sub(r"\W+", "_", name) + ".json")
    if os.path.exists(path):
        return json.load(open(path))
    out = fn()
    os.makedirs(CACHE, exist_ok=True)
    json.dump(out, open(path, "w"))
    return out


def by_ids(ids):
    out = []
    for i in range(0, len(ids), 100):
        out += get({"filter.ids": ",".join(ids[i:i + 100]), "fields": FIELDS, "pageSize": 100})["studies"]
        time.sleep(0.2)
    return out


def by_query(cond):
    out, tok = [], None
    while True:
        p = {"query.cond": cond, "pageSize": 1000, "fields": FIELDS,
             "filter.advanced": "AREA[StudyType]INTERVENTIONAL AND AREA[StartDate]RANGE[2020-01-01,2026-12-31]"}
        if tok:
            p["pageToken"] = tok
        d = get(p); out += d.get("studies", []); tok = d.get("nextPageToken")
        if not tok:
            return out


def keep(ps, spec):  # same rule as expanded/fetch.py
    inc = re.compile(spec["inc"], re.I); exc = re.compile(spec["exc"], re.I) if spec["exc"] else None
    hits = [c for c in ps.get("conditionsModule", {}).get("conditions", []) if inc.search(c)]
    if not hits:
        return False
    title = ps["identificationModule"].get("briefTitle", "")
    return not (exc and all(exc.search(c) for c in hits) and not inc.search(title))


def row(disease, group, dalys, ps):
    sp = ps.get("sponsorCollaboratorsModule", {})
    lead = dict(sp.get("leadSponsor", {}))
    nct = ps["identificationModule"]["nctId"]
    if nct in OVERRIDES:
        lead.update(name=OVERRIDES[nct]["lead_sponsor"], **{"class": OVERRIDES[nct]["lead_class"]})
    collab = sp.get("collaborators", [])
    return {"disease": disease, "group": group, "dalys": dalys,
            "nct_id": ps["identificationModule"]["nctId"],
            "start_year": int(ps["statusModule"]["startDateStruct"]["date"][:4]),
            "lead_sponsor": lead.get("name", ""), "lead_class": lead.get("class", ""),
            "commercial": int(lead.get("class") == "INDUSTRY"),
            "industry_collaborator": int(any(c.get("class") == "INDUSTRY" for c in collab)),
            "phases": "|".join(ps.get("designModule", {}).get("phases", [])),
            "title": ps["identificationModule"].get("briefTitle", "")}


def is_drug(ps):
    if ps.get("designModule", {}).get("studyType") != "INTERVENTIONAL":
        return False
    it = {x.get("type") for x in ps.get("armsInterventionsModule", {}).get("interventions", [])}
    sd = ps.get("statusModule", {}).get("startDateStruct", {}).get("date", "")
    return bool(it & DRUG) and sd and int(sd[:4]) in YEARS


if __name__ == "__main__":
    ids = json.load(open(os.path.join(ROOT, "clinicaltrials", "nct_ids_2026-11-08.json")))
    burden = {r["label"]: r for r in csv.DictReader(open(os.path.join(ROOT, "expanded",
              "burden_vs_research_expanded_2021-2025.csv")))}
    model = {r["label"]: r for r in csv.DictReader(open(os.path.join(ROOT, "analysis", "plot_data_2021-2025.csv")))}
    comps = [r for r in burden.values() if 10e6 <= float(r["dalys"]) <= 30e6]
    jobs = [("Long COVID", "Long COVID", model["Long COVID, incl. post-COVID ME"]["dalys"], "ids", "Long COVID"),
            ("ME/CFS", "ME/CFS", model["All ME/CFS (classic + post-COVID)"]["dalys"], "ids", "ME/CFS")]
    for r in comps:
        src = ("ids", r["label"]) if r["label"] in ids else ("query", r["label"])
        jobs.append((r["label"], r["group"], r["dalys"], *src))
    rows = []
    for name, group, dalys, how, key in jobs:
        if how == "ids":
            S = cached(name, lambda: by_ids(ids[key]))
            K = [s["protocolSection"] for s in S]
        else:
            S = cached(name, lambda: by_query(D[key]["cond"]))
            K = [s["protocolSection"] for s in S if keep(s["protocolSection"], D[key])]
        R = [row(name, group, dalys, ps) for ps in K if is_drug(ps)]
        rows += R
        n = [r for r in R if 2021 <= r["start_year"] <= 2025]
        print(f"{name:32s} drug trials 2021-25: {len(n):5d}  commercial {sum(r['commercial'] for r in n):5d}", flush=True)
    out = os.path.join(ROOT, "clinicaltrials", f"sponsor_trials_{datetime.date.today()}.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    print("wrote", out, len(rows))
