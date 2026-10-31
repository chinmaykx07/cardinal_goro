import hashlib, json, random, sys
sys.path.insert(0, "/tmp/claude-0/-home-claude/9c9bede2-6e1a-50e6-8e32-801745dafdd5/scratchpad/exp")
import split, factcheck, transforms
from scipy.stats import beta

def cp(k, n, alpha=0.05):
    lo = 0.0 if k == 0 else beta.ppf(alpha / 2, k, n - k + 1)
    hi = 1.0 if k == n else beta.ppf(1 - alpha / 2, k + 1, n - k)
    return lo, hi

CHECKERS = [("v0 (first deck, multiset)", "v0", "lenient"),
            ("v2 strict (ordered)", "v2", "strict"),
            ("v2 lenient (multiset)", "v2", "lenient")]

def main(which, nlines, seed, show):
    lines = split.lines(which, nlines, seed)
    res = {}
    fails = {}
    for kind, table in (("valid", transforms.VALIDS), ("corrupt", transforms.CORRUPTIONS)):
        for name, fn in table.items():
            key = (kind, name)
            res[key] = {c[0]: [0, 0] for c in CHECKERS}  # [accepted, rejected]
            for path, line in lines:
                rnd = random.Random(int(hashlib.sha1((name + line).encode()).hexdigest()[:12], 16) ^ seed)
                cand = fn(line, rnd)
                if cand is None or cand == line:
                    continue
                for label, ver, mode in CHECKERS:
                    ok = factcheck.check(cand, line, ver, mode)
                    res[key][label][0 if ok else 1] += 1
                    wrong = (not ok) if kind == "valid" else ok
                    if wrong and label.startswith("v2 strict") and len(fails.setdefault(key, [])) < show:
                        fails[key].append((line[:200], cand[:200]))
    out = {}
    print(f"\n=== split={which} lines={len(lines)} seed={seed} ===")
    for (kind, name), per in res.items():
        n = sum(per[CHECKERS[0][0]])
        if n == 0:
            continue
        print(f"\n[{kind.upper()}] {name}   (n={n})")
        for label, _, _ in CHECKERS:
            acc, rej = per[label]
            if kind == "valid":
                lo, hi = cp(rej, n)
                print(f"   {label:28s} false-reject {rej:5d}/{n}  = {100*rej/n:6.2f}%   95% CI [{100*lo:.2f}, {100*hi:.2f}]")
            else:
                lo, hi = cp(rej, n)
                print(f"   {label:28s} detected     {rej:5d}/{n}  = {100*rej/n:6.2f}%   95% CI [{100*lo:.2f}, {100*hi:.2f}]")
        out[f"{kind}|{name}"] = {"n": n, **{lbl: per[lbl] for lbl, _, _ in CHECKERS}}
    json.dump(out, open(f"/tmp/claude-0/-home-claude/9c9bede2-6e1a-50e6-8e32-801745dafdd5/scratchpad/exp/results_{which}.json", "w"), ensure_ascii=False, indent=1)
    if show:
        print("\n---- v2-strict wrong decisions (examples) ----")
        for (kind, name), ex in fails.items():
            print(f"\n[{kind}] {name}")
            for a, b in ex:
                print("   ORIG:", a)
                print("   CAND:", b)

if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
