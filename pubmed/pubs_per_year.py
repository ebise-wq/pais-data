"""PubMed publications per year per disease, 1996-2026.

Counts per disease and year:
  title    = disease named in the title (curated synonym list), by date added
             to PubMed [edat]. Main measure. Each paper counts in exactly one year.
  title_dp = same search by publication date [dp]. [dp] matches both the
             electronic and print date, so papers e-published in one year and
             printed the next count in both years (about 7% extra).
  mesh     = MeSH major topic, by [edat]. Cross-check only.
Uses NCBI E-utilities esearch with rettype=count. No API key needed (3 req/s).
"""
import csv, time, urllib.parse, urllib.request, re, datetime

YEARS = range(1996, 2027)
E = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

def ti(*phrases):
    return " OR ".join(f'"{p}"[ti]' for p in phrases)

# Same 24 diseases as clinicaltrials/fetch_counts.py.
# name: (title query, MeSH major-topic query or None)
D = {
 "ME/CFS": (ti("chronic fatigue syndrome", "myalgic encephalomyelitis", "myalgic encephalopathy",
               "ME/CFS", "CFS/ME", "systemic exertion intolerance"),
            '"Fatigue Syndrome, Chronic"[Majr]'),
 "Long COVID": (ti("long covid", "post-COVID-19 condition", "post-COVID condition", "post-COVID conditions",
                   "post-COVID syndrome", "post-COVID-19 syndrome", "post-acute COVID-19 syndrome",
                   "post-acute sequelae", "post-acute COVID", "persistent COVID", "chronic COVID",
                   "long-haul COVID", "COVID long haulers", "long-term sequelae of COVID")
                + " OR PASC[ti]",
                '"Post-Acute COVID-19 Syndrome"[Majr]'),
 "Celiac disease": (ti("celiac disease", "coeliac disease", "celiac sprue", "coeliac sprue",
                       "gluten-sensitive enteropathy", "gluten enteropathy", "dermatitis herpetiformis",
                       "refractory celiac", "refractory coeliac"),
                    '"Celiac Disease"[Majr]'),
 "Multiple sclerosis": (ti("multiple sclerosis", "clinically isolated syndrome"), '"Multiple Sclerosis"[Majr]'),
 "Rheumatoid arthritis": (ti("rheumatoid arthritis"), '"Arthritis, Rheumatoid"[Majr:noexp]'),
 "Crohn's disease": ("crohn*[ti]", '"Crohn Disease"[Majr]'),
 "Ulcerative colitis": (ti("ulcerative colitis"), '"Colitis, Ulcerative"[Majr]'),
 "IBD": ("crohn*[ti] OR " + ti("ulcerative colitis", "ulcerative proctitis", "inflammatory bowel disease",
                                             "inflammatory bowel diseases", "indeterminate colitis", "IBD-unclassified")
                        + ' OR pouchitis[ti] OR (IBD[ti] NOT "identity by descent"[tiab])',
                        '"Inflammatory Bowel Diseases"[Majr]'),  # MeSH tree includes Crohn and UC
 "Psoriasis": ("psoria*[ti]", '"Psoriasis"[Majr]'),
 "Systemic lupus": (ti("systemic lupus", "lupus nephritis") + " OR SLE[ti]", '"Lupus Erythematosus, Systemic"[Majr]'),
 "Type 1 diabetes": ("(" + ti("type 1 diabetes", "type I diabetes", "type 1 diabetic", "type I diabetic",
                              "insulin-dependent diabetes", "juvenile diabetes") + " OR T1D[ti] OR T1DM[ti])"
                     ' NOT "non-insulin-dependent"[ti]',
                     '"Diabetes Mellitus, Type 1"[Majr]'),
 "Epilepsy": ("epilep*[ti] OR seizure*[ti]", '"Epilepsy"[Majr]'),
 "Schizophrenia": ("schizophren*[ti]", '"Schizophrenia"[Majr]'),
 "Bipolar disorder": (ti("bipolar disorder", "bipolar disorders", "bipolar depression", "bipolar affective",
                         "bipolar I", "bipolar II", "bipolar spectrum", "bipolar mania", "bipolar patients",
                         "bipolar illness"),
                      '"Bipolar Disorder"[Majr]'),
 "Parkinson's disease": ("parkinson*[ti]", '"Parkinson Disease"[Majr]'),
 "Fibromyalgia": ("fibromyalg*[ti]", '"Fibromyalgia"[Majr]'),
 "POTS": (ti("postural orthostatic tachycardia", "postural tachycardia")
          + " OR (POTS[ti] AND (orthostatic[ti] OR tachycardia[ti] OR autonomic[ti] OR dysautonomia[ti]"
            " OR syncope[ti] OR patients[ti] OR syndrome[ti] OR COVID[ti]))",
          '"Postural Orthostatic Tachycardia Syndrome"[Majr]'),
 "Endometriosis": ("endometriosis[ti] OR endometrioma*[ti]", '"Endometriosis"[Majr]'),
 "Irritable bowel syndrome": (ti("irritable bowel") + " OR IBS[ti]", '"Irritable Bowel Syndrome"[Majr]'),
 "HIV": ("HIV[ti] OR " + ti("human immunodeficiency virus", "acquired immunodeficiency syndrome"),
         '"HIV Infections"[Majr]'),
 "Sjogren's": ("sjogren*[ti]", '"Sjogren\'s Syndrome"[Majr]'),
 "Gulf War illness": (ti("gulf war"), '"Persian Gulf Syndrome"[Majr]'),
 "Post-treatment Lyme": (ti("post-treatment lyme", "chronic lyme", "persistent lyme", "post-lyme",
                            "posttreatment lyme") + " OR PTLDS[ti] OR PTLD[ti]",
                         None),  # no specific MeSH term
 "ALS (rare ref.)": (ti("amyotrophic lateral sclerosis", "motor neuron disease", "motor neurone disease")
                     + " OR ALS[ti]", '"Amyotrophic Lateral Sclerosis"[Majr]'),
 "Cystic fibrosis (rare ref.)": (ti("cystic fibrosis"), '"Cystic Fibrosis"[Majr]'),
}

def count(term):
    url = E + "?" + urllib.parse.urlencode({"db": "pubmed", "rettype": "count", "term": term})
    for i in range(6):
        try:
            time.sleep(0.36)
            txt = urllib.request.urlopen(url, timeout=60).read().decode()
            m = re.search(r"<Count>(\d+)</Count>", txt)
            if m:
                return int(m.group(1))
            raise ValueError(txt[:200])
        except Exception as e:
            err = e
            time.sleep(2 ** i)
    raise err

if __name__ == "__main__":
    # Default: pull every disease into new files dated today.
    # --only NAME [NAME ...] --date YYYY-MM-DD: pull only these diseases and merge them into the
    # existing files of that date, leaving the other rows as they were.
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="+"); ap.add_argument("--date")
    args = ap.parse_args()
    today = args.date or datetime.date.today().isoformat()
    todo = args.only or list(D)
    old = []
    if args.only:
        with open(f"pubs_per_year_long_{today}.csv") as f:
            old = [r for r in csv.DictReader(f) if r["disease"] not in todo]
    with open(f"queries_{today}.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["disease", "title_query", "mesh_query"])
        for d, (t, m) in D.items():
            w.writerow([d, t, m or ""])
    rows = []
    for d in todo:
        t, m = D[d]
        for y in YEARS:
            rows.append({"disease": d, "year": y, "title": count(f"({t}) AND {y}[edat]"),
                         "title_dp": count(f"({t}) AND {y}[dp]"),
                         "mesh": count(f"({m}) AND {y}[edat]") if m else ""})
        print(d, sum(r["title"] for r in rows if r["disease"] == d and 2021 <= r["year"] <= 2025), flush=True)
    rows = sorted(old + rows, key=lambda r: (list(D).index(r["disease"]), int(r["year"])))
    with open(f"pubs_per_year_long_{today}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["disease", "year", "title", "title_dp", "mesh"]); w.writeheader(); w.writerows(rows)
    # wide format matching clinicaltrials/trials_per_year_*.csv (title counts)
    with open(f"pubs_per_year_{today}.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["disease"] + [str(y) for y in YEARS])
        for d in D:
            w.writerow([d] + [r["title"] for r in rows if r["disease"] == d])
