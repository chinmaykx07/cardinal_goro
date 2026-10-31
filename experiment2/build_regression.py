"""Build tests/regression_cases.jsonl: a fixed set of labelled messages for CI.

Every label comes from HOW the case was built (the frozen scripted transforms for
numbers, dates and amounts; the construction rules in name_eval.py for names and
places). The checker is never consulted here, so the set cannot quietly freeze a
checker bug in place.

Sources:
  * numbers/dates/amounts: DEV2 records from record_eval.py (real spans), every
    valid rewrite and corruption class
  * names/places: name_eval.py constructions, every class including the
    "rejected by design" ones

Usage: MAHGRS=<mahgrs>/GRs python3 -I build_regression.py <n_records> <n_name_records> <seed>
"""
import hashlib
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import record_eval as RE   # noqa: E402
import name_eval as NE     # noqa: E402

OUT = os.path.join(HERE, "..", "tests", "regression_cases.jsonl")


def number_cases(n, seed):
    recs, _, _ = RE.build_records(os.environ["MAHGRS"], "dev2", n, seed)
    out = []
    for rec, msg in recs:
        out.append(("base message (real formats, unchanged)", "pass", rec, msg))
        for expect, table in (("pass", RE.transforms.VALIDS), ("fail", RE.transforms.CORRUPTIONS)):
            for name, fn in table.items():
                rnd = random.Random(int(hashlib.sha1((name + msg).encode()).hexdigest()[:12], 16) ^ seed)
                cand = fn(msg, rnd)
                if cand is None or cand == msg:
                    continue
                out.append((name, expect, rec, cand))
    return out


def name_cases(n, seed):
    # "design" cases are correct Marathi that the fail-closed rule must reject
    return [(cls, "pass" if kind == "pass" else "fail", rec, msg) for cls, kind, rec, msg in NE.generate(n, seed)]


def main(n_rec, n_names, seed):
    rows = [("numbers", *c) for c in number_cases(n_rec, seed)] + [("names", *c) for c in name_cases(n_names, seed)]
    with open(OUT, "w", encoding="utf-8") as f:
        for area, cls, expect, rec, msg in rows:
            r = dict(rec)
            r["date"] = list(r["date"])
            f.write(json.dumps({"area": area, "class": cls, "expect": expect, "record": r, "message": msg},
                               ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} cases to {os.path.relpath(OUT)}")


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
