"""P0-3: measure the product's record-based check (src/verified.py) on DEV2.

For each record:
  * the date and the amount are REAL values, copied together with their exact
    surface form (digits, separators, month names, commas, lakh/crore words)
    from a DEV2 line of the Maharashtra GR corpus;
  * the name, place and reference number are synthetic;
  * the message is one of three provisional templates (not yet reviewed by a
    native speaker), with the real date and amount spans pasted in.

The base message must pass. Then each scripted rewrite (must pass) and each
corruption (must fail) from experiment/transforms.py is applied. Those
transforms label cases by construction, independently of the checker.

Usage:  MAHGRS=<mahgrs>/GRs python3 -I record_eval.py dev2 <n_records> <seed>
TEST2 is refused unless FINAL=1 is set (one frozen run only; see SPLIT.md).
"""
import hashlib
import json
import os
import random
import re
import sys
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "experiment"))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
sys.path.insert(0, HERE)
import split2                      # noqa: E402
import transforms                  # noqa: E402  (experiment/transforms.py, frozen hash)
from verified import check         # noqa: E402

try:
    from scipy.stats import beta

    def cp(k, n, a=0.05):
        lo = 0.0 if k == 0 else beta.ppf(a / 2, k, n - k + 1)
        hi = 1.0 if k == n else beta.ppf(1 - a / 2, k + 1, n - k)
        return lo, hi
except ImportError:  # pragma: no cover
    def cp(k, n, a=0.05):
        return float("nan"), float("nan")

TO_ASC = str.maketrans("०१२३४५६७८९", "0123456789")
MONTHS = transforms.MONTHS_CANON
MAG = {"कोटी": 10 ** 7, "लाख": 10 ** 5, "हजार": 10 ** 3}

# ---- value spans, parsed here independently of src/factcheck.py -------------------------
D = r"[०-९0-9]"
NUMERIC_DATE = re.compile(r"(?<![०-९0-9.,/\-])(" + D + r"{1,2})([./\-])(" + D + r"{1,2})\2(" + D + r"{4})(?![०-९0-9])")
NAMED_DATE = re.compile(r"(?<![०-९0-9])(" + D + r"{1,2})\s+(" + "|".join(MONTHS) + r")(?![ऀ-ॿ]),?\s+(" + D + r"{4})(?![०-९0-9])")
AMOUNT = re.compile(r"(?:रु\.|₹)\s*(" + D + r"{1,3}(?:," + D + r"{2,3})+(?:\." + D + r"+)?|" + D + r"+(?:\." + D + r"+)?)(?:\s*(कोटी|लाख|हजार)(?![ऀ-ॿ]))?(?![०-९0-9,.])")


def _valid_date(d, m, y):
    return 1 <= d <= 31 and 1 <= m <= 12 and 1950 <= y <= 2035


def date_spans(line):
    out = []
    for m in NUMERIC_DATE.finditer(line):
        d, mo, y = (int(x.translate(TO_ASC)) for x in (m.group(1), m.group(3), m.group(4)))
        if _valid_date(d, mo, y):
            out.append((m.group(0), (d, mo, y)))
    for m in NAMED_DATE.finditer(line):
        d, y = int(m.group(1).translate(TO_ASC)), int(m.group(3).translate(TO_ASC))
        mo = MONTHS.index(m.group(2)) + 1
        if _valid_date(d, mo, y):
            out.append((m.group(0), (d, mo, y)))
    return out


def amount_spans(line):
    out = []
    for m in AMOUNT.finditer(line):
        try:
            v = Decimal(m.group(1).translate(TO_ASC).replace(",", ""))
        except InvalidOperation:
            continue
        if m.group(2):
            v *= MAG[m.group(2)]
        if v > 0 and v == v.to_integral_value() and v < 10 ** 13:
            out.append((m.group(0), int(v)))
    return out


# ---- synthetic parts (invented; no real person) ---------------------------------------
NAMES = ["सुनीता पाटील", "रमेश जाधव", "अनिता कुलकर्णी", "विजय शिंदे", "मीना देशमुख",
         "संजय पवार", "कविता गायकवाड", "प्रकाश मोरे", "स्वाती चव्हाण", "दीपक भोसले"]
PLACES = ["नाशिक", "पुणे", "सातारा", "कोल्हापूर", "नागपूर", "औरंगाबाद", "सोलापूर", "जळगाव"]
# Provisional wording, digit-free, pending native review (issue #9).
TEMPLATES = [
    "{NAME}, {PLACE}: आपला अर्ज क्र. {REF} दिनांक {DATE} रोजी मंजूर झाला असून {AMOUNT} इतकी रक्कम खात्यात जमा केली जाईल.",
    "{NAME} ({PLACE}) यांचा अर्ज क्र. {REF} नामंजूर झाला आहे. कारण: उत्पन्न दाखला जोडलेला नाही. शुल्क {AMOUNT} भरून {DATE} पर्यंत पुन्हा अर्ज करा.",
    "अर्ज क्र. {REF}: {NAME}, रा. {PLACE}, यांनी {DATE} पर्यंत {AMOUNT} भरावे.",
]


def build_records(root, split, n, seed):
    rnd = random.Random(seed)
    dates, amounts = [], []
    for _, line in split2.lines(root, split, 10 ** 9, seed, per_file=40):
        dates += date_spans(line)
        amounts += amount_spans(line)
        if len(dates) >= 3 * n and len(amounts) >= 3 * n:
            break
    rnd.shuffle(dates)
    rnd.shuffle(amounts)
    recs = []
    for i in range(min(n, len(dates), len(amounts))):
        (dspan, dval), (aspan, aval) = dates[i], amounts[i]
        y = rnd.choice([2025, 2026, 2027])
        ref = f"RTS/{y}/{rnd.randint(1, 99999):05d}"
        rec = {"name": rnd.choice(NAMES), "place": rnd.choice(PLACES), "ref": ref,
               "date": dval, "amount": aval}
        tpl = rnd.choice(TEMPLATES)
        msg = (tpl.replace("{NAME}", rec["name"]).replace("{PLACE}", rec["place"])
               .replace("{REF}", ref).replace("{DATE}", dspan).replace("{AMOUNT}", aspan))
        recs.append((rec, msg))
    return recs, len(dates), len(amounts)


def main(split, n, seed):
    if split == "test2" and os.environ.get("FINAL") != "1":
        sys.exit("TEST2 is for one frozen final run only. Set FINAL=1 deliberately (see SPLIT.md).")
    root = os.environ["MAHGRS"]
    recs, nd, na = build_records(root, split, n, seed)
    res = defaultdict(lambda: [0, 0])          # name -> [n, wrong]
    res_fact = defaultdict(lambda: [0, 0])     # corruptions that left the ref intact, so hit date/amount
    reasons = defaultdict(Counter)
    examples = defaultdict(list)

    def record(kind, name, rec, msg, must_pass):
        fails = check(msg, rec)
        wrong = bool(fails) if must_pass else not fails
        res[(kind, name)][0] += 1
        res[(kind, name)][1] += wrong
        if kind == "corrupt" and rec["ref"] in msg.translate(TO_ASC):
            res_fact[name][0] += 1
            res_fact[name][1] += wrong
        if wrong:
            reasons[(kind, name)].update(fails or ["accepted"])
            if len(examples[(kind, name)]) < 3:
                examples[(kind, name)].append(msg)

    for rec, msg in recs:
        record("valid", "base message (real formats, unchanged)", rec, msg, True)
        for kind, table, must_pass in (("valid", transforms.VALIDS, True), ("corrupt", transforms.CORRUPTIONS, False)):
            for name, fn in table.items():
                rnd = random.Random(int(hashlib.sha1((name + msg).encode()).hexdigest()[:12], 16) ^ seed)
                cand = fn(msg, rnd)
                if cand is None or cand == msg:
                    continue
                record(kind, name, rec, cand, must_pass)

    print(f"=== split={split} records={len(recs)} seed={seed} data={split2.DATA_COMMIT[:12]} "
          f"(date spans seen {nd}, amount spans seen {na}) ===")
    out = {}
    for (kind, name), (cnt, wrong) in res.items():
        lo, hi = cp(wrong, cnt)
        label = "false-reject" if kind == "valid" else "missed     "
        print(f"[{kind:7s}] {name:42s} n={cnt:6d}  {label} {wrong:5d} = {100*wrong/cnt:6.2f}%  95% CI [{100*lo:.2f}, {100*hi:.2f}]")
        out[f"{kind}|{name}"] = {"n": cnt, "wrong": wrong, "reasons": dict(reasons[(kind, name)])}
    print("\n---- corruptions that hit the real date or amount (reference number left intact) ----")
    for name, (cnt, wrong) in res_fact.items():
        lo, hi = cp(wrong, cnt)
        print(f"[corrupt] {name:42s} n={cnt:6d}  missed      {wrong:5d} = {100*wrong/cnt:6.2f}%  95% CI [{100*lo:.2f}, {100*hi:.2f}]")
        out[f"corrupt_fact|{name}"] = {"n": cnt, "wrong": wrong}
    json.dump(out, open(os.path.join(HERE, f"results_record_{split}.json"), "w"), ensure_ascii=False, indent=1)
    print("\n---- wrong decisions: reasons and examples ----")
    for key, ex in examples.items():
        print(f"\n{key}: {dict(reasons[key])}")
        for e in ex:
            print("   ", e)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
