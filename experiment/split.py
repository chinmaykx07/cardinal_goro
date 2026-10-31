import hashlib, os, sys, re, random, json
ROOT=os.environ.get("MAHGRS","/home/claude/orgpedia/mahgrs/GRs")  # set MAHGRS to the GRs folder of a clone of github.com/orgpedia/mahgrs
DEV=set(range(0,3)); TEST={8,9}
def bucket(path):
    return int(hashlib.sha1(os.path.basename(path).encode()).hexdigest(),16)%10
def files(split):
    want = DEV if split=="dev" else TEST
    out=[]
    for d in sorted(os.listdir(ROOT)):
        for f in sorted(os.listdir(os.path.join(ROOT,d))):
            if f.endswith(".mr.txt") and bucket(f) in want:
                out.append(os.path.join(ROOT,d,f))
    return out
DIG=re.compile(r"[०-९0-9]")
def lines(split, n, seed):
    rnd=random.Random(seed); fs=files(split); rnd.shuffle(fs); out=[]
    for p in fs:
        try: txt=open(p,encoding="utf-8").read()
        except Exception: continue
        ls=[l.strip() for l in txt.split("\n")]
        cand=[l for l in ls if 20<=len(l)<=400 and re.search(r"[०-९]",l) and not l.startswith("# Page")]
        rnd.shuffle(cand)
        out+= [(p,l) for l in cand[:int(os.environ.get("PER_FILE","3"))]]
        if len(out)>=n: break
    return out[:n]
if __name__=="__main__":
    for s in ("dev","test"): print(s,len(files(s)))
