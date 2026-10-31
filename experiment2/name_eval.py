"""P0-4: measure name and place checking in src/verified.py.

Synthetic data: common Marathi first names, surnames and place names, combined at
random (no real person intended). Each case is a full message from the three
provisional templates, with a fixed date and amount, and only the name or place
changed. Every case's correct answer is known by construction:

  must PASS  exact name; name + allowed case ending; extra spaces; punctuation after
  must FAIL  letter substituted / deleted / inserted inside a word; vowel sign changed;
             a different person's name; surname replaced; name inside a longer word;
             first name kept but the surname moved elsewhere
  FAIL BY DESIGN (fail-closed, reported separately, not errors):
             oblique vowel + ending (रामाला), name parts in another order

Insertions are only made strictly inside a word, so they can never form
"name + allowed ending", which would be correct Marathi.

Usage: python3 -I name_eval.py <n_per_class> <seed>
"""
import os
import random
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from verified import check, SUFFIXES  # noqa: E402

try:
    from scipy.stats import beta

    def cp(k, n, a=0.05):
        lo = 0.0 if k == 0 else beta.ppf(a / 2, k, n - k + 1)
        hi = 1.0 if k == n else beta.ppf(1 - a / 2, k + 1, n - k)
        return lo, hi
except ImportError:  # pragma: no cover
    def cp(k, n, a=0.05):
        return float("nan"), float("nan")

FIRST = ["सुनीता", "रमेश", "अनिता", "विजय", "मीना", "संजय", "कविता", "प्रकाश", "स्वाती", "दीपक",
         "सुरेश", "आशा", "महेश", "वैशाली", "गणेश", "रेखा", "अमोल", "प्रिया", "नितीन", "सविता",
         "राहुल", "पूजा", "सचिन", "शुभांगी", "अजय", "मनीषा", "किरण", "उषा", "विनोद", "सुवर्णा",
         "राम", "राज", "शंकर", "लता", "मोहन", "छाया", "अनिल", "संगीता", "योगेश", "ज्योती"]
LAST = ["पाटील", "जाधव", "कुलकर्णी", "शिंदे", "देशमुख", "पवार", "गायकवाड", "मोरे", "चव्हाण", "भोसले",
        "जोशी", "देशपांडे", "कदम", "सावंत", "शेख", "काळे", "माने", "गोखले", "राऊत", "शिर्के",
        "थोरात", "वाघ", "नाईक", "लोखंडे", "बनसोडे", "खरात", "घुले", "ढोले", "वाकचौरे", "इंगळे"]
PLACES = ["नाशिक", "पुणे", "सातारा", "कोल्हापूर", "नागपूर", "सोलापूर", "जळगाव", "लातूर", "बीड",
          "अहमदनगर", "सांगली", "रत्नागिरी", "धुळे", "अकोला", "अमरावती", "नांदेड", "परभणी", "वर्धा",
          "नवी मुंबई", "ठाणे", "पालघर", "रायगड", "उस्मानाबाद", "यवतमाळ", "भंडारा"]
TEMPLATES = [
    "{NAME}, {PLACE}: आपला अर्ज क्र. RTS/2026/04521 दिनांक ३० नोव्हेंबर २०२६ रोजी मंजूर झाला असून ₹१,५०० इतकी रक्कम खात्यात जमा केली जाईल.",
    "{NAME} ({PLACE}) यांचा अर्ज क्र. RTS/2026/04521 नामंजूर झाला आहे. कारण: उत्पन्न दाखला जोडलेला नाही. शुल्क ₹१,५०० भरून ३० नोव्हेंबर २०२६ पर्यंत पुन्हा अर्ज करा.",
    "अर्ज क्र. RTS/2026/04521: {NAME}, रा. {PLACE}, यांनी ३० नोव्हेंबर २०२६ पर्यंत ₹१,५०० भरावे.",
]
CONSONANTS = [chr(c) for c in range(0x0915, 0x093A)]
VOWEL_SWAPS = {"ि": "ी", "ी": "ि", "ु": "ू", "ू": "ु", "े": "ै", "ै": "े", "ो": "ौ", "ौ": "ो"}
LONGER = ["चंद्र", "कर", "राव", "नाथ", "दास", "कांत"]   # continuations that make a different, longer word


def rec_for(name, place):
    return {"name": name, "place": place, "ref": "RTS/2026/04521", "date": (30, 11, 2026), "amount": 1500}


def message(tpl, name_text, place_text):
    return tpl.replace("{NAME}", name_text).replace("{PLACE}", place_text)


# ---- word-level corruptions, each guaranteed to change the word -----------------
def sub_letter(w, rnd):
    pos = [i for i, c in enumerate(w) if c in CONSONANTS]
    if not pos:
        return None
    i = rnd.choice(pos)
    return w[:i] + rnd.choice([c for c in CONSONANTS if c != w[i]]) + w[i + 1:]


def vowel_sign(w, rnd):
    pos = [i for i, c in enumerate(w) if c in VOWEL_SWAPS]
    if pos:
        i = rnd.choice(pos)
        return w[:i] + VOWEL_SWAPS[w[i]] + w[i + 1:]
    if "ं" in w:
        return w.replace("ं", "", 1)
    return None


def del_char(w, rnd):
    if len(w) < 3:
        return None
    i = rnd.randrange(len(w))
    return w[:i] + w[i + 1:]


def ins_inside(w, rnd):
    if len(w) < 2:
        return None
    i = rnd.randrange(1, len(w))          # strictly inside: never at the end
    return w[:i] + rnd.choice(CONSONANTS) + w[i:]


def corrupt_one_word(text, fn, rnd):
    words = text.split()
    k = rnd.randrange(len(words))
    new = fn(words[k], rnd)
    if not new or new == words[k]:
        return None
    words[k] = new
    return " ".join(words)


def generate(n, seed):
    """Yield (class, kind, record, message); kind is "pass", "fail" or "design".
    "design" cases are correct Marathi that the fail-closed rule must reject."""
    rnd = random.Random(seed)
    for _ in range(n):
        name = f"{rnd.choice(FIRST)} {rnd.choice(LAST)}"
        place = rnd.choice(PLACES)
        rec = rec_for(name, place)
        tpl = rnd.choice(TEMPLATES)
        other = f"{rnd.choice([f for f in FIRST if f != name.split()[0]])} {rnd.choice(LAST)}"
        first, last = name.split()

        yield "exact name and place", "pass", rec, message(tpl, name, place)
        yield "name + allowed ending", "pass", rec, message(tpl, name + rnd.choice(SUFFIXES), place)
        yield "place + allowed ending", "pass", rec, message(tpl, name, place + rnd.choice(SUFFIXES))
        yield "extra spaces inside name", "pass", rec, message(tpl, first + "  " + last, place)

        for label, fn in (("letter substituted", sub_letter), ("vowel sign changed", vowel_sign),
                          ("letter deleted", del_char), ("letter inserted inside a word", ins_inside)):
            bad = corrupt_one_word(name, fn, rnd)
            if bad and bad != name:
                yield f"name: {label}", "fail", rec, message(tpl, bad, place)
            bad = corrupt_one_word(place, fn, rnd)
            if bad and bad != place:
                yield f"place: {label}", "fail", rec, message(tpl, name, bad)

        if other != name:
            yield "different person's name", "fail", rec, message(tpl, other, place)
        new_last = rnd.choice([s for s in LAST if s != last])
        yield "surname replaced", "fail", rec, message(tpl, f"{first} {new_last}", place)
        yield "name inside a longer word", "fail", rec, message(tpl, f"{first} {last}{rnd.choice(LONGER)}", place)
        yield ("surname belongs to someone else, first name elsewhere", "fail", rec,
               message(tpl, f"{rnd.choice([f for f in FIRST if f != first])} {last}", place) + f" पत्ता: {first} नगर.")
        other_place = rnd.choice([p for p in PLACES if p != place])
        yield "different place", "fail", rec, message(tpl, name, other_place)

        yield ("oblique vowel + ending (correct Marathi, rejected by design)", "design", rec,
               message(tpl, name + "ा" + rnd.choice(["ला", "ने", "चा", "ना"]), place))
        yield "name parts in another order (rejected by design)", "design", rec, message(tpl, f"{last} {first}", place)


def main(n, seed):
    res = defaultdict(lambda: [0, 0])
    examples = defaultdict(list)
    for cls, kind, rec, msg in generate(n, seed):
        passed = not check(msg, rec)
        wrong = (not passed) if kind == "pass" else passed
        res[(cls, kind)][0] += 1
        res[(cls, kind)][1] += wrong
        if wrong and len(examples[cls]) < 3:
            examples[cls].append(msg)

    print(f"=== name/place evaluation: {n} records per class, seed={seed}, {len(SUFFIXES)} allowed endings ===")
    for kind, title in (("pass", "MUST PASS  (a wrong decision = false reject)"),
                        ("fail", "MUST FAIL  (a wrong decision = false accept, the dangerous kind)"),
                        ("design", "REJECTED BY DESIGN (correct Marathi that the fail-closed rule refuses)")):
        print(f"\n{title}")
        for (cls, k), (cnt, wrong) in res.items():
            if k != kind:
                continue
            lo, hi = cp(wrong, cnt)
            if kind == "design":
                print(f"  {cls:60s} n={cnt:6d}  rejected {cnt - wrong:6d} = {100*(cnt-wrong)/cnt:6.2f}%")
            else:
                print(f"  {cls:60s} n={cnt:6d}  wrong {wrong:5d} = {100*wrong/cnt:6.2f}%  95% CI [{100*lo:.2f}, {100*hi:.2f}]")
    if examples:
        print("\n---- examples of wrong decisions ----")
        for cls, ex in examples.items():
            print(f"\n{cls}:")
            for e in ex:
                print("   ", e)


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]))
