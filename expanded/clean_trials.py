"""Cleaner trial counts: keep only trials whose brief title names the disease.

Why: a trial counts for a disease if one of its listed conditions matches. Many such trials are
mixed (several diseases, healthy volunteers) or about something else (cancer fatigue tagged
"chronic fatigue syndrome", hip replacement tagged "rheumatoid arthritis"). Tested on 171
hand-labelled trials (51 ME/CFS, 60 MS, 60 RA; ictrp/mecfs_trial_criteria.csv and
ictrp/ms_ra_trial_sample.csv), the title rule kept 92-96% of trials that are mainly in the disease
for all three, against raw counts that overstate by 1.2x (MS) to 1.6x (RA). Same idea as the
PubMed title search.

Two cleaned counts (both start from trials whose listed condition matches, as before):
- title: the brief title also names the disease (and does not match the exclusion regex).
  Drops many genuine surgical, device and vaccine trials whose titles name the procedure, so it is
  NOT used for the main analysis.
- weighted (used): a trial whose title names the disease counts 1; otherwise it counts the share
  of its listed conditions that match the disease (a trial listing only the disease counts 1;
  "hearing loss; dementia; cognitive impairment" counts 1/3). On the 171 labelled trials this cut
  the overcount from 1.20-1.62x (raw) to 1.06-1.33x, keeping 89-99% of genuine trials.
Inputs: cache/ (ClinicalTrials.gov pages saved by fetch.py) for the 111 newer causes;
the original comparators are re-fetched by NCT ID from ../clinicaltrials/nct_ids_2026-11-08.json.
Output: the trials_* columns of cleaned_counts_2021-2025.csv. Run from repo root: python3 -I expanded/clean_trials.py
"""
import csv, json, os, re, sys, time, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from diseases import D
from fetch import keep, YEARS, save_cleaned

ORIG = {  # name in ../clinicaltrials -> (label used in analyse.py, regex, exclusion)
    "ME/CFS": ("ME/CFS", r"chronic fatigue syndrome|myalgic|ME/CFS|\bCFS\b|systemic exertion intolerance", None),
    "Multiple sclerosis": ("Multiple sclerosis", r"multiple sclerosis|\bMS\b|clinically isolated syndrome", r"tuberous|amyotrophic|systemic sclerosis"),
    "Rheumatoid arthritis": ("Rheumatoid arthritis", r"rheumatoid arthritis", r"juvenile"),
    "Crohn's disease": ("Crohn's disease", r"crohn", None),
    "Ulcerative colitis": ("Ulcerative colitis", r"ulcerative colitis", None),
    "Psoriasis": ("Psoriasis", r"psoria", r"psoriatic arthritis$"),
    "Type 1 diabetes": ("Type 1 diabetes", r"type ?(1|i)\b.{0,10}diabet|diabet.{0,25}type ?(1|i)\b|T1D|insulin.?dependent|juvenile diabet", r"type ?(2|ii)"),
    "Epilepsy": ("Epilepsy", r"epileps|seizure", None),
    "Schizophrenia": ("Schizophrenia", r"schizo", None),
    "Bipolar disorder": ("Bipolar disorder", r"bipolar", None),
    "Parkinson's disease": ("Parkinson's disease", r"parkinson", None),
    "Endometriosis": ("Endometriosis", r"endometrio", None),
    "HIV": ("HIV/AIDS", r"\bHIV\b|human immunodeficiency|AIDS\b", None),
    "ALS (rare ref.)": ("ALS / motor neuron disease", r"amyotrophic|\bALS\b|motor neuron", None),
}


def get(url):
    for i in range(6):
        try:
            return json.load(urllib.request.urlopen(url, timeout=120))
        except Exception as e:
            err = e; time.sleep(2 ** i)
    raise err


def by_year(studies, inc, exc, title_ok=False):
    raw = {y: 0 for y in YEARS}; clean = {y: 0 for y in YEARS}; wt = {y: 0.0 for y in YEARS}
    for s in studies:
        ps = s["protocolSection"]
        if ps.get("designModule", {}).get("studyType") != "INTERVENTIONAL":
            continue
        sd = ps.get("statusModule", {}).get("startDateStruct", {}).get("date")
        if not sd or int(sd[:4]) not in raw:
            continue
        title = ps["identificationModule"].get("briefTitle", "")
        conds = ps.get("conditionsModule", {}).get("conditions", [])
        if not (keep(s, inc, exc) or (title_ok and inc.search(title))):
            continue
        y = int(sd[:4]); raw[y] += 1
        if inc.search(title) and not (exc and exc.search(title)):
            clean[y] += 1; wt[y] += 1
        elif conds:
            wt[y] += sum(1 for c in conds if inc.search(c)) / len(conds)
    return raw, clean, wt


rows = []
ids = json.load(open(os.path.join(HERE, "..", "clinicaltrials", "nct_ids_2026-11-08.json")))
for src, (label, inc, exc) in ORIG.items():
    L = ids[src]; studies = []
    for i in range(0, len(L), 100):
        q = {"filter.ids": ",".join(L[i:i + 100]), "pageSize": 100,
             "fields": "NCTId,BriefTitle,Condition,StudyType,StartDate"}
        studies += get("https://clinicaltrials.gov/api/v2/studies?" + urllib.parse.urlencode(q))["studies"]
        time.sleep(0.3)
    # ids were already filtered by condition (or title for ME/CFS), so accept them all at the condition step
    raw, clean, wt = by_year(studies, re.compile(inc, re.I), re.compile(exc, re.I) if exc else None, title_ok=True)
    rows.append({"disease": label, "trials_source": "original", "trials_raw_per_year": sum(raw.values()) / 5,
                 "trials_title_per_year": sum(clean.values()) / 5, "trials_weighted_per_year": round(sum(wt.values()) / 5, 2)})
    print(label, rows[-1]["trials_raw_per_year"], rows[-1]["trials_title_per_year"], flush=True)

for name, spec in D.items():
    fn = os.path.join(HERE, "cache", re.sub(r"\W+", "_", name) + ".json")
    inc = re.compile(spec["inc"], re.I); exc = re.compile(spec["exc"], re.I) if spec["exc"] else None
    raw, clean, wt = by_year(json.load(open(fn)), inc, exc)
    rows.append({"disease": name, "trials_source": "expanded", "trials_raw_per_year": sum(raw.values()) / 5,
                 "trials_title_per_year": sum(clean.values()) / 5, "trials_weighted_per_year": round(sum(wt.values()) / 5, 2)})

for r in rows:
    r["trials_title_share"] = round(r["trials_title_per_year"] / r["trials_raw_per_year"], 2) if r["trials_raw_per_year"] else ""
    r["trials_weighted_share"] = round(r["trials_weighted_per_year"] / r["trials_raw_per_year"], 2) if r["trials_raw_per_year"] else ""
save_cleaned(rows)  # trials_* columns of cleaned_counts_2021-2025.csv
