import json,re,os,urllib.parse,urllib.request,csv,time
B="https://clinicaltrials.gov/api/v2/studies"
F="NCTId,BriefTitle,Condition,StudyType,Phase,DesignAllocation,InterventionType,OverallStatus,StartDate,EnrollmentCount,LeadSponsorClass,DesignPrimaryPurpose"
# name: (API cond query, regex that must match a listed condition (or title if title_ok), exclusion regex)
D={
 "ME/CFS":("chronic fatigue syndrome OR myalgic encephalomyelitis", r"chronic fatigue syndrome|myalgic|ME/CFS|\bCFS\b|systemic exertion intolerance",None,True),
 "Long COVID":("long covid OR post-acute COVID-19 syndrome OR post-COVID condition OR PASC OR post COVID-19 condition", r"long.?covid|post.?acute (sequelae|covid)|\bPASC\b|post.?covid|post.?acute.{0,20}(sars|covid)|long.?haul|persistent covid|chronic covid|sequelae of (covid|sars)|covid.?19 sequelae|post.?sars.?cov",None,True),
 "Celiac disease":("celiac disease OR coeliac disease", r"c(o)?eliac (disease|sprue)|gluten.?sensitive enteropathy|^c(o)?eliac$|refractory c(o)?eliac|dermatitis herpetiformis",r"non.?c(o)?eliac|not.?celiac|plexus|ganglia|block|neurolysis|artery",True),
 "Multiple sclerosis":("multiple sclerosis", r"multiple sclerosis|\bMS\b|clinically isolated syndrome",r"tuberous|amyotrophic|systemic sclerosis",False),
 "Rheumatoid arthritis":("rheumatoid arthritis", r"rheumatoid arthritis",r"juvenile",False),
 "Crohn's disease":("crohn disease", r"crohn",None,False),
 "Ulcerative colitis":("ulcerative colitis", r"ulcerative colitis",None,False),
 "Psoriasis":("psoriasis", r"psoria",r"psoriatic arthritis$",False),
 "Systemic lupus":("systemic lupus erythematosus", r"lupus",r"cutaneous lupus$|discoid",False),
 "Type 1 diabetes":("type 1 diabetes", r"type ?(1|i)\b.{0,10}diabet|diabet.{0,25}type ?(1|i)\b|T1D|insulin.?dependent|juvenile diabet",r"type ?(2|ii)",False),
 "Epilepsy":("epilepsy", r"epileps|seizure",None,False),
 "Schizophrenia":("schizophrenia", r"schizo",None,False),
 "Bipolar disorder":("bipolar disorder", r"bipolar",None,False),
 "Parkinson's disease":("parkinson disease", r"parkinson",None,False),
 "Fibromyalgia":("fibromyalgia", r"fibromyalg",None,False),
 "POTS":("postural orthostatic tachycardia syndrome", r"postural (orthostatic )?tachycardia|\bPOTS\b",None,True),
 "Endometriosis":("endometriosis", r"endometrio",None,False),
 "Irritable bowel syndrome":("irritable bowel syndrome", r"irritable bowel|\bIBS\b",None,False),
 "HIV":("HIV", r"\bHIV\b|human immunodeficiency|AIDS\b",None,False),
 "Sjogren's":("Sjogren's Syndrome", r"sj(o|ö)gren",None,False),
 "Gulf War illness":("gulf war illness", r"gulf war",None,True),
 "Post-treatment Lyme":("lyme disease", r"post.?treatment lyme|chronic lyme|PTLD|persistent lyme|lyme.{0,30}(syndrome|persistent|chronic)",None,True),
 "ALS (rare ref.)":("amyotrophic lateral sclerosis", r"amyotrophic|\bALS\b|motor neuron",None,False),
 "Cystic fibrosis (rare ref.)":("cystic fibrosis", r"cystic fibrosis",None,False),
}
def get(p):
    for i in range(5):
        try:return json.load(urllib.request.urlopen(B+"?"+urllib.parse.urlencode(p),timeout=120))
        except Exception as e: time.sleep(2**i); err=e
    raise err
def fetch(q,fn):
    if os.path.exists(fn):return json.load(open(fn))
    out=[];tok=None
    while True:
        p={"query.cond":q,"pageSize":1000,"fields":F}
        if tok:p["pageToken"]=tok
        d=get(p);out+=d["studies"];tok=d.get("nextPageToken")
        if not tok:break
    json.dump(out,open(fn,"w"));return out
rows=[];allkept={}
for name,(q,inc,exc,title_ok) in D.items():
    S=fetch(q,"raw_"+re.sub(r"\W+","_",name)+".json")
    I=re.compile(inc,re.I);E=re.compile(exc,re.I) if exc else None
    K=[]
    for s in S:
        ps=s["protocolSection"];c=ps.get("conditionsModule",{}).get("conditions",[]);t=ps["identificationModule"]["briefTitle"]
        hit=any(I.search(x) for x in c) or (title_ok and I.search(t))
        if name=="Celiac disease" and E and E.search(" ".join(c)+" "+t) and not re.search(r"c(o)?eliac disease",t+" ".join(c),re.I): hit=False
        elif name!="Celiac disease" and E and all(E.search(x) for x in c if I.search(x)) and not I.search(t): hit=False
        if hit:K.append(s)
    allkept[name]={s["protocolSection"]["identificationModule"]["nctId"] for s in K}
    def dm(s):return s["protocolSection"].get("designModule",{})
    inter=[s for s in K if dm(s).get("studyType")=="INTERVENTIONAL"]
    rct=[s for s in inter if dm(s).get("designInfo",{}).get("allocation")=="RANDOMIZED"]
    itypes=lambda s:{i.get("type") for i in s["protocolSection"].get("armsInterventionsModule",{}).get("interventions",[])}
    drug=[s for s in inter if itypes(s)&{"DRUG","BIOLOGICAL","GENETIC"}]
    ph=lambda s:set(dm(s).get("phases",[]))
    p2=[s for s in drug if ph(s)&{"PHASE2","PHASE3"}]
    p3=[s for s in drug if ph(s)&{"PHASE3"}]
    ind=[s for s in inter if s["protocolSection"].get("sponsorCollaboratorsModule",{}).get("leadSponsor",{}).get("class")=="INDUSTRY"]
    rows.append(dict(disease=name,raw_hits=len(S),studies=len(K),interventional=len(inter),randomized=len(rct),drug_or_biologic=len(drug),phase2_or_3_drug=len(p2),phase3_drug=len(p3),industry_led=len(ind)))
    print(rows[-1],flush=True)
with open("counts.csv","w") as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
json.dump({k:sorted(v) for k,v in allkept.items()},open("nct_ids.json","w"))
a=allkept
print("ME/CFS ∩ Long COVID:",len(a["ME/CFS"]&a["Long COVID"]))
