"""Deterministic fact checkers for Marathi numerals, dates and amounts.

v0: the logic shown in the first deck, generalised to compare all numerals as a multiset.
v2: canonicalising checker, developed on the DEV split only.
"""
import re
from collections import Counter
from decimal import Decimal, InvalidOperation

DEVDIG = str.maketrans("०१२३४५६७८९", "0123456789")

# ---------------------------------------------------------------- v0 (as in the first deck)
V0_MONTHS = ["जानेवारी", "फेब्रुवारी", "मार्च", "एप्रिल", "मे", "जून", "जुलै",
             "ऑगस्ट", "सप्टेंबर", "ऑक्टोबर", "नोव्हेंबर", "डिसेंबर"]


def facts_v0(text):
    t = text.translate(DEVDIG)
    facts = []
    pat = r"(\d{1,2})\s+(" + "|".join(V0_MONTHS) + r")\s+(\d{4})"
    for a, b, c in re.findall(pat, t):
        facts.append(("D", int(c), V0_MONTHS.index(b) + 1, int(a)))
    t = re.sub(pat, " ", t)
    for a, b, c in re.findall(r"(\d{1,2})/(\d{1,2})/(\d{4})", t):
        facts.append(("D", int(c), int(b), int(a)))
    t = re.sub(r"(\d{1,2})/(\d{1,2})/(\d{4})", " ", t)
    for x in re.findall(r"\d[\d,]*", t):
        facts.append(("N", int(x.replace(",", "") or 0) if x.replace(",", "") else 0))
    return facts


# ---------------------------------------------------------------- v2
# Month spellings attested in the DEV split (nukta removed before matching).
MONTH_VARIANTS = {
    1: ["जानेवारी", "जानवारी", "जानेवारि"],
    2: ["फेब्रुवारी", "फेब्रवारी", "फेब्रुअरी"],
    3: ["मार्च"],
    4: ["एप्रिल", "अप्रिल"],
    5: ["मे"],
    6: ["जून", "जुन"],
    7: ["जुलै", "जुले", "जूलै", "जुलाई"],
    8: ["ऑगस्ट", "ऑगष्ट", "ऑगष्ट्ट", "आगस्ट", "ऑगस्ट्ट"],
    9: ["सप्टेंबर", "सप्टेबर", "सप्टेम्बर"],
    10: ["ऑक्टोबर", "ऑक्टोंबर", "आक्टोबर", "ऑक्टोम्बर"],
    11: ["नोव्हेंबर", "नोव्हेबर", "नोव्हेम्बर"],
    12: ["डिसेंबर", "डिसेम्बर"],
}
MONTH_LOOKUP = {w: m for m, ws in MONTH_VARIANTS.items() for w in ws}
MONTH_ALT = "|".join(sorted(MONTH_LOOKUP, key=len, reverse=True))
MAG = {"कोटी": Decimal(10) ** 7, "कोटि": Decimal(10) ** 7, "लाख": Decimal(10) ** 5,
       "लक्ष": Decimal(10) ** 5, "हजार": Decimal(10) ** 3, "सहस्र": Decimal(10) ** 3}
MAG_ALT = "|".join(sorted(MAG, key=len, reverse=True))
NUM = r"\d{1,3}(?:,\d{2,3})+(?:\.\d+)?|\d+(?:\.\d+)?"
DV = r"[\u0900-\u097F]"
MW = r"(?<!" + DV + r")(?:" + MONTH_ALT + r")(?!" + DV + r")"
RS = r"(?:रुपये|रूपये|रु\.?|रू\.?|₹)"
V2_RE = re.compile(
    # 0 amount written in words: the whole span is one literal fact
    r"(?P<words>अक्षरी[^)\n]{3,200}?फक्त)"
    r"|"
    # 1 day + month name + year          e.g. 09 ऑक्टोबर, 2020
    r"(?P<dn>(?<!\d)(?P<dn_d>\d{1,2})\s*(?P<dn_m>" + MW + r")\s*[,.]?\s*(?P<dn_y>\d{4})(?!\d))"
    # 2 numeric date                     e.g. 22.9.2020  15/06/2023  (also right after "दि.")
    r"|(?P<ds>(?<!\d)(?<!\d[./\-,])(?P<ds_d>\d{1,2})\s*[./\-]\s*(?P<ds_m>\d{1,2})\s*[./\-]\s*(?P<ds_y>\d{4})(?!\d))"
    # 3 day + month name, year missing   (dates that wrap across lines)
    r"|(?P<dm>(?<!\d)(?P<dm_d>\d{1,2})\s*(?P<dm_m>" + MW + r"))"
    # 4 month name + year
    r"|(?P<my>(?P<my_m>" + MW + r")\s*[,.]?\s*(?P<my_y>\d{4})(?!\d))"
    # 5 money: rupee sign + number [+ magnitude], or number + magnitude
    r"|(?P<money>(?:" + RS + r"\s*(?P<mn>" + NUM + r")(?:\s*(?P<mg>" + MAG_ALT + r"))?)|(?:(?P<mn2>" + NUM + r")\s*(?P<mg2>" + MAG_ALT + r")))"
    # 6 any other numeral
    r"|(?P<num>" + NUM + r")"
)


def normalise(text):
    t = text.translate(DEVDIG).replace("\u093c", "")  # digits to ASCII, drop nukta
    return t.replace("\u200c", "").replace("\u200d", "")


def _dec(s):
    return Decimal(s.replace(",", ""))


def facts_v2(text):
    t = normalise(text)
    out = []
    for m in V2_RE.finditer(t):
        if m.group("words"):
            out.append(("W", re.sub(r"\s+", " ", m.group("words")).strip()))
        elif m.group("dn"):
            out.append(("D", int(m.group("dn_y")), MONTH_LOOKUP[m.group("dn_m")], int(m.group("dn_d"))))
        elif m.group("ds"):
            out.append(("D", int(m.group("ds_y")), int(m.group("ds_m")), int(m.group("ds_d"))))
        elif m.group("dm"):
            out.append(("DM", MONTH_LOOKUP[m.group("dm_m")], int(m.group("dm_d"))))
        elif m.group("my"):
            out.append(("MY", int(m.group("my_y")), MONTH_LOOKUP[m.group("my_m")]))
        elif m.group("money"):
            n = m.group("mn") or m.group("mn2")
            mag = m.group("mg") or m.group("mg2")
            v = _dec(n) * (MAG[mag] if mag else 1)
            out.append(("N", format(v.normalize(), "f")))
        else:
            n = m.group("num")
            if "." in n:
                out.append(("L", n.replace(",", "")))   # non-money decimals keep trailing zeros: 2.0 is not 2
            elif "," in n:
                out.append(("N", n.replace(",", "")))
            elif len(n) > 1 and n.startswith("0"):
                out.append(("Z", n))                    # leading-zero codes like 08 stay literal
            else:
                out.append(("N", n))
    return out


def facts_v0_norm(text):  # v0 facts made comparable (strings) so one comparer works
    return [tuple(map(str, f)) for f in facts_v0(text)]


def check(candidate, record_text, version="v2", mode="strict"):
    """Return True if `candidate` carries the same facts as `record_text` (the reference text)."""
    f = facts_v2 if version == "v2" else facts_v0_norm
    a, b = f(candidate), f(record_text)
    return a == b if mode == "strict" else Counter(a) == Counter(b)
