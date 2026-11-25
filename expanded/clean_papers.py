"""Cleaner PubMed counts (2021-2025, title search by [edat], same queries as before) with two fixes.

1. Veterinary filter, applied to every disease: drop titles naming livestock or pet animals
   (cattle, sheep, goats, pigs, dogs, cats, horses, poultry, ...). Lab-animal models (mice, rats)
   are kept, since that is research on the human disease. Mainly affects zoonotic and parasitic
   diseases whose literature includes animal-health work (Fasciola, Echinococcus, Taenia, ...).
2. Abbreviation fixes, from sampled abbreviation-only titles (seed 968592, 15 per term):
   ALS: "et al's" is indexed as ALS (4/15 off-topic) -> NOT "et al"[ti]
   TB: terbium chemistry (3/15) -> NOT (terbium, luminescence, doped, coordination polymer terms)
   AMD: acid mine drainage (2/15) -> NOT ("acid mine"[ti] OR drainage[ti])
   IBS: metallurgy symposium, a device name (2/15); IBS is not in the comparison (no GBD cause)
   SLE, COPD, HCV: 0/15 off-topic, unchanged.
Output: the papers_* columns of cleaned_counts_2021-2025.csv. Run from repo root: python3 -I expanded/clean_papers.py
"""
import csv, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from diseases import D
from fetch import pubmed_count, save_cleaned

VET = ("cattle OR cow OR cows OR bovine OR calves OR sheep OR ovine OR lamb OR lambs OR goat OR goats OR caprine OR "
       "swine OR pig OR pigs OR piglets OR porcine OR boar OR dog OR dogs OR canine OR puppies OR cat OR cats OR feline OR "
       "horse OR horses OR equine OR donkey* OR camel* OR buffalo* OR ruminant* OR livestock OR poultry OR chicken* OR "
       "broiler* OR duck* OR wildlife OR veterinary OR herd OR herds OR farm OR farms OR slaughter*")
VET_NOT = "(" + " OR ".join(f"{w}[ti]" for w in VET.split(" OR ")) + ")"
FIX = {
    "ALS / motor neuron disease": ' NOT "et al"[ti]',
    "Tuberculosis": " NOT (terbium[ti] OR luminescen*[ti] OR doped[ti] OR phosphor*[ti] OR \"coordination polymer\"[ti])",
    "Macular degeneration": ' NOT ("acid mine"[ti] OR drainage[ti])',
}
ORIG_Q = {}  # original comparators and ME/CFS: queries from ../pubmed
for r in csv.DictReader(open(os.path.join(HERE, "..", "pubmed", "queries_2026-11-08.csv"))):
    ORIG_Q[r["disease"]] = r["title_query"]
ORIG = {"ME/CFS": "ME/CFS", "Multiple sclerosis": "Multiple sclerosis", "Rheumatoid arthritis": "Rheumatoid arthritis",
        "Crohn's disease": "Crohn's disease", "Ulcerative colitis": "Ulcerative colitis", "Psoriasis": "Psoriasis",
        "Type 1 diabetes": "Type 1 diabetes", "Epilepsy": "Epilepsy", "Schizophrenia": "Schizophrenia",
        "Bipolar disorder": "Bipolar disorder", "Parkinson's disease": "Parkinson's disease", "Endometriosis": "Endometriosis",
        "HIV/AIDS": "HIV", "ALS / motor neuron disease": "ALS (rare ref.)"}

queries = {label: ORIG_Q[src] for label, src in ORIG.items()}
queries.update({k: v["pm"] for k, v in D.items()})
rows = []
for name, q in queries.items():
    q2 = f"(({q}){FIX.get(name, '')}) NOT {VET_NOT}"
    before = pubmed_count(f"({q}) AND 2021:2025[edat]") / 5
    after = pubmed_count(f"({q2}) AND 2021:2025[edat]") / 5
    rows.append({"disease": name, "papers_per_year": before, "papers_cleaned_per_year": after,
                 "papers_kept_share": round(after / before, 3) if before else ""})
    print(f"{name:45s} {before:8.1f} -> {after:8.1f}", flush=True)
save_cleaned(rows)  # papers_* columns of cleaned_counts_2021-2025.csv
