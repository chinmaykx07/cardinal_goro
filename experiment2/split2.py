"""Fresh split for all work after the October 2026 pre-registered run.

The October run used hash buckets 0-2 (DEV) and 8-9 (TEST); see experiment/.
Buckets 3-7 were never read. They are declared here, in SPLIT.md, BEFORE any
file in them is opened:
    DEV2  = buckets 3, 4   (design and tuning)
    TEST2 = buckets 5, 6, 7 (final numbers only, each frozen design run once)
The bucket function is identical to experiment/split.py: sha1(file name) mod 10.
"""
import hashlib
import os
import random
import re

DATA_COMMIT = "c96e88f731589e1284ecab60ff1a63d3b9c6bb82"  # orgpedia/mahgrs, pinned 31 Oct 2026
SPLITS = {"dev2": {3, 4}, "test2": {5, 6, 7}}
USED_BEFORE = {0, 1, 2, 8, 9}


def bucket(name):
    return int(hashlib.sha1(os.path.basename(name).encode()).hexdigest(), 16) % 10


def files(root, split):
    want = SPLITS[split]
    out = []
    for d in sorted(os.listdir(root)):
        p = os.path.join(root, d)
        if not os.path.isdir(p):
            continue
        for f in sorted(os.listdir(p)):
            if f.endswith(".mr.txt") and bucket(f) in want:
                out.append(os.path.join(p, f))
    return out


DEV_DIGIT = re.compile(r"[०-९]")


def lines(root, split, n, seed, per_file=8):
    """Same line filter as experiment/split.py: 20-400 chars, a Devanagari digit, not a page marker."""
    rnd = random.Random(seed)
    fs = files(root, split)
    rnd.shuffle(fs)
    out = []
    for p in fs:
        try:
            txt = open(p, encoding="utf-8").read()
        except Exception:
            continue
        cand = [l.strip() for l in txt.split("\n")]
        cand = [l for l in cand if 20 <= len(l) <= 400 and DEV_DIGIT.search(l) and not l.startswith("# Page")]
        rnd.shuffle(cand)
        out += [(p, l) for l in cand[:per_file]]
        if len(out) >= n:
            break
    return out[:n]
