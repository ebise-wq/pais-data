"""PubMed papers and ClinicalTrials.gov interventional trials per year, 2021-2025, for the causes in diseases.py.

Same method as ../pubmed/pubs_per_year.py (title search, [edat]) and ../clinicaltrials/fetch_counts.py
(query.cond, then keep studies whose listed conditions match a regex; interventional; by start year).
Here the API is asked only for interventional studies starting 2021-2025, to keep downloads small.

Run from the repo root: python3 -I expanded/fetch.py [--only "Name,Name"]
Writes expanded/counts_<date>.csv and expanded/queries_<date>.csv. Raw API pages are cached in
expanded/cache/ (not committed).
"""
import csv, datetime, json, os, re, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diseases import D

YEARS = list(range(2021, 2026))
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache")
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
CTG = "https://clinicaltrials.gov/api/v2/studies"
FIELDS = "NCTId,BriefTitle,Condition,StudyType,StartDate"


def get(url, parse_json=False):
    err = None
    for i in range(6):
        try:
            txt = urllib.request.urlopen(url, timeout=120).read().decode()
            return json.loads(txt) if parse_json else txt
        except Exception as e:  # network hiccups, 429s
            err = e
            time.sleep(2 ** i)
    raise err


def pubmed_count(term):
    time.sleep(0.36)  # 3 requests/s without an API key
    txt = get(EUTILS + "?" + urllib.parse.urlencode({"db": "pubmed", "rettype": "count", "term": term}))
    m = re.search(r"<Count>(\d+)</Count>", txt)
    if not m:
        raise ValueError(txt[:300])
    return int(m.group(1))


def ctg_studies(name, cond):
    fn = os.path.join(CACHE, re.sub(r"\W+", "_", name) + ".json")
    if os.path.exists(fn):
        return json.load(open(fn))
    out, tok = [], None
    while True:
        p = {"query.cond": cond, "pageSize": 1000, "fields": FIELDS,
             "filter.advanced": "AREA[StudyType]INTERVENTIONAL AND AREA[StartDate]RANGE[2021-01-01,2025-12-31]"}
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


def keep(study, inc, exc):
    ps = study["protocolSection"]
    conds = ps.get("conditionsModule", {}).get("conditions", [])
    title = ps["identificationModule"].get("briefTitle", "")
    hits = [c for c in conds if inc.search(c)]
    if not hits:
        return False
    if exc and all(exc.search(c) for c in hits) and not inc.search(title):
        return False
    return True


def trials_per_year(name, spec):
    inc = re.compile(spec["inc"], re.I)
    exc = re.compile(spec["exc"], re.I) if spec["exc"] else None
    S = ctg_studies(name, spec["cond"])
    per = {y: 0 for y in YEARS}
    for s in S:
        ps = s["protocolSection"]
        if ps.get("designModule", {}).get("studyType") != "INTERVENTIONAL" or not keep(s, inc, exc):
            continue
        sd = ps.get("statusModule", {}).get("startDateStruct", {}).get("date")
        if sd and int(sd[:4]) in per:
            per[int(sd[:4])] += 1
    return len(S), per


if __name__ == "__main__":
    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
    today = datetime.date.today().isoformat()
    names = [n for n in D if not only or n in only]
    rows = []
    for n in names:
        spec = D[n]
        papers = {y: pubmed_count(f"({spec['pm']}) AND {y}[edat]") for y in YEARS}
        raw, trials = trials_per_year(n, spec)
        row = {"disease": n, "group": spec["group"], "gbd_causes": "; ".join(spec["gbd"]),
               **{f"papers_{y}": papers[y] for y in YEARS}, **{f"trials_{y}": trials[y] for y in YEARS},
               "ctg_raw_hits_2021_2025": raw}
        rows.append(row)
        print(f"{n:45s} papers/yr {sum(papers.values())/5:8.1f}  trials/yr {sum(trials.values())/5:6.1f}  (raw {raw})",
              flush=True)
    suffix = "" if not only else "_partial"
    with open(os.path.join(HERE, f"counts_{today}{suffix}.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    if not only:
        with open(os.path.join(HERE, f"queries_{today}.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["disease", "group", "gbd_causes", "pubmed_title_query", "ctg_query_cond", "ctg_condition_regex",
                        "ctg_exclude_regex"])
            for n, s in D.items():
                w.writerow([n, s["group"], "; ".join(s["gbd"]), s["pm"], s["cond"], s["inc"], s["exc"] or ""])
