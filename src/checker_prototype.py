# Test B: deterministic checker for Marathi notices. Synthetic records; mock outputs; tests the CHECKER only.
import re, random
random.seed(11)
D=str.maketrans("०१२३४५६७८९","0123456789")
MONTHS=["जानेवारी","फेब्रुवारी","मार्च","एप्रिल","मे","जून","जुलै","ऑगस्ट","सप्टेंबर","ऑक्टोबर","नोव्हेंबर","डिसेंबर"]
SUF=["","ला","ने","चा","ची","चे","च्या","ना","त","पासून","साठी","कडे","मध्ये","वर","चं","स","तून","ाला","ांना","ास","ाचा","ाची","ाचे","ाच्या"]
def to_dev(n): return str(n).translate(str.maketrans("0123456789","०१२३४५६७८९"))
def canon(w):  # lenient: collapse short/long vowel signs and nasal variants
    return (w.replace("ि","ी").replace("ु","ू").replace("इ","ई").replace("उ","ऊ").replace("ं","न्").replace("ँ","न्")
             .replace("़",""))
def check(text, rec, lenient=False):
    t=text.translate(D)
    ok=True
    # reference id
    refs=re.findall(r'RTS/\d{4}/\d+',t)
    if refs!=[rec["ref"]]: return False
    t=re.sub(r'RTS/\d{4}/\d+',' ',t)
    # dates
    dates=[]
    for m in re.finditer(r'(\d{1,2})\s+('+"|".join(MONTHS)+r')\s+(\d{4})',t): dates.append((int(m[1]),MONTHS.index(m[2])+1,int(m[3])))
    t=re.sub(r'(\d{1,2})\s+('+"|".join(MONTHS)+r')\s+(\d{4})',' ',t)
    for m in re.finditer(r'(\d{1,2})/(\d{1,2})/(\d{4})',t): dates.append((int(m[1]),int(m[2]),int(m[3])))
    t=re.sub(r'(\d{1,2})/(\d{1,2})/(\d{4})',' ',t)
    if dates!=[rec["date"]]: return False
    nums=[int(x.replace(",","")) for x in re.findall(r'\d[\d,]*',t)]
    if nums!=[rec["amount"]]: return False   # any extra/hallucinated number rejects
    toks=re.findall(r'[ऀ-ॿ]+',text)
    def has(word):
        w=canon(word) if lenient else word
        for tk in toks:
            x=canon(tk) if lenient else tk
            if x.startswith(w) and x[len(w):] in (SUF if not lenient else [canon(s) for s in SUF]): return True
        return False
    for part in rec["name"].split():
        if not has(part): return False
    if not has(rec["place"]): return False
    return True
FIRST=["सुनीता","रमेश","अनिता","सविता","गणेश","कविता","मीना","विजय","प्रिया","दीपक"]
LAST=["पाटील","जाधव","शिंदे","पवार","देशमुख","कुलकर्णी","भोसले","चव्हाण"]
PLACE=["नाशिक","पुणे","नागपूर","अमरावती","सातारा","कोल्हापूर","लातूर","जळगाव"]
def fmt_date(d,style):
    if style==0: return f"{to_dev(d[0])} {MONTHS[d[1]-1]} {to_dev(d[2])}"
    if style==1: return f"{d[0]} {MONTHS[d[1]-1]} {d[2]}"
    return f"{to_dev(d[0])}/{to_dev(d[1])}/{to_dev(d[2])}"
def render(rec, over=None):
    r=dict(rec); r.update(over or {})
    dn=random.choice([True,False])
    amt=f"{r['amount']:,}"; amt=to_dev(amt) if dn else amt
    refs=r["ref"] if random.random()<.5 else r["ref"]
    pl=r["place"]+random.choice(["ला","मध्ये","हून","च्या"]) if False else r["place"]+random.choice(["ला","मध्ये","च्या"])
    nm=r["name"]+random.choice([" यांना"," यांच्या"," यांचे"])
    d=fmt_date(r["date"],random.choice([0,1,2]))
    return random.choice([
      f"{nm} अर्ज क्र. {refs}: {pl} केंद्रात {d} रोजी ₹{amt} जमा करावे.",
      f"{pl} येथील {nm} प्रकरण {refs}. रक्कम ₹{amt}, अंतिम तारीख {d}.",
    ])
def recs(n):
    out=[]
    for _ in range(n):
        out.append(dict(name=random.choice(FIRST)+" "+random.choice(LAST), place=random.choice(PLACE),
                        amount=random.choice([500,1000,1500,2100,2500,3000,4500,12000]),
                        date=(random.randint(1,28),random.randint(1,12),2026),
                        ref=f"RTS/2026/{random.randint(1000,99999):05d}"))
    return out
R=recs(3000)
# 1) false rejects on VALID variants
for lenient in (False,True):
    fr=sum(not check(render(r),r,lenient) for r in R)
    print(f"valid-variant false-reject, lenient_names={lenient}: {fr/len(R)*100:.2f}%")
# 2) detection of corruptions
def swap_digits(n):
    s=list(str(n)); 
    if len(s)<2: return n+1
    i=random.randrange(len(s)-1); s[i],s[i+1]=s[i+1],s[i]
    v=int("".join(s)); return v if v!=n else n+10
def corrupt(r,kind):
    o={}
    if kind=="year+/-1": o["date"]=(r["date"][0],r["date"][1],2026+random.choice([-1,1]))
    elif kind=="day+/-1": o["date"]=((r["date"][0]%28)+1,r["date"][1],2026)
    elif kind=="amount digit swap": o["amount"]=swap_digits(r["amount"])
    elif kind=="amount drop zero": o["amount"]=r["amount"]//10
    elif kind=="ref digit change":
        x=list(r["ref"]); i=-random.randint(1,4); x[i]=str((int(x[i])+random.randint(1,8))%10); o["ref"]="".join(x)
    elif kind=="other person (same surname)": o["name"]=random.choice([f for f in FIRST if f!=r["name"].split()[0]])+" "+r["name"].split()[1]
    elif kind=="matra variant (सुनीता->सुनिता)":
        f,l=r["name"].split(); o["name"]=f.replace("ी","ि",1).replace("ू","ु",1)+" "+l
        if o["name"]==r["name"]: o["name"]=f.replace("ा","")+" "+l
    elif kind=="wrong place": o["place"]=random.choice([p for p in PLACE if p!=r["place"]])
    return o
print("\ndetection rate by corruption type (higher is better)")
print(f"{'corruption':38s} strict-names  lenient-names")
for kind in ["year+/-1","day+/-1","amount digit swap","amount drop zero","ref digit change","other person (same surname)","matra variant (सुनीता->सुनिता)","wrong place"]:
    res=[]
    for lenient in (False,True):
        det=0
        for r in R:
            ov=corrupt(r,kind)
            # render with corrupted values but check against TRUE record
            bad=render(r,ov)
            det+= (not check(bad,r,lenient))
        res.append(det/len(R)*100)
    print(f"{kind:38s} {res[0]:8.1f}%     {res[1]:8.1f}%")
