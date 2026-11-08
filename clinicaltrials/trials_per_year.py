import json,glob,re,csv,collections
ids=json.load(open("nct_ids.json"))
studies={}
for f in glob.glob("raw_*.json"):
    for s in json.load(open(f)):studies[s["protocolSection"]["identificationModule"]["nctId"]]=s
yrs=list(range(1996,2027))
rows=[];nodate={}
for d,L in ids.items():
    c=collections.Counter();nd=0
    for i in L:
        ps=studies[i]["protocolSection"]
        if ps.get("designModule",{}).get("studyType")!="INTERVENTIONAL":continue
        sd=ps.get("statusModule",{}).get("startDateStruct",{}).get("date")
        if not sd:nd+=1;continue
        c[int(sd[:4])]+=1
    nodate[d]=nd
    rows.append({"disease":d,"pre1996":sum(v for k,v in c.items() if k<1996),**{str(y):c[y] for y in yrs}})
with open("trials_per_year.csv","w") as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
R={r["disease"]:r for r in rows}
print("year",*["MECFS","LC","Celiac"],sep="\t")
for y in yrs:print(y,R["ME/CFS"][str(y)],R["Long COVID"][str(y)],R["Celiac disease"][str(y)],sep="\t")
print("pre1996",R["ME/CFS"]["pre1996"],R["Long COVID"]["pre1996"],R["Celiac disease"]["pre1996"])
print("nodate",nodate["ME/CFS"],nodate["Long COVID"],nodate["Celiac disease"])
bins=[(1996,2000),(2001,2005),(2006,2010),(2011,2015),(2016,2020),(2021,2025)]
print("\n5yr bins")
for d,r in R.items():print(d,[sum(r[str(y)] for y in range(a,b+1)) for a,b in bins])
