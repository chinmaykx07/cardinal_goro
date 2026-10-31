"""Placeholder fill + strict checker for Marathi decision messages.

Facts (name, place, ref, date, amount) are never generated: the drafter emits
{NAME} {PLACE} {REF} {DATE} {AMOUNT} slots and fill() copies from the record.
check() then verifies the final text with the measured v2 extractor; anything
doubtful returns reasons, and the caller falls back to the approved template,
or abstains if the template fails too.
"""
import os
import re
from collections import Counter

from factcheck import facts_v2

D = str.maketrans("०१२३४५६७८९", "0123456789")
MONTHS = ["जानेवारी", "फेब्रुवारी", "मार्च", "एप्रिल", "मे", "जून", "जुलै",
          "ऑगस्ट", "सप्टेंबर", "ऑक्टोबर", "नोव्हेंबर", "डिसेंबर"]
SLOTS = ("NAME", "PLACE", "REF", "DATE", "AMOUNT")
_DEV = str.maketrans("0123456789", "०१२३४५६७८९")


def indian_group(n: int) -> str:
    """12,50,000 style grouping (last three digits, then pairs)."""
    s = str(n)
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    pairs = []
    while len(head) > 2:
        pairs.insert(0, head[-2:])
        head = head[:-2]
    return ",".join([head] + pairs + [tail])

_SUFFIX_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "marathi_suffixes.txt")
SUFFIXES = tuple(l.strip() for l in open(_SUFFIX_FILE, encoding="utf-8")
                 if l.strip() and not l.lstrip().startswith("#"))
_LETTER = r"[\u0900-\u097F\u200c\u200d]"   # any Devanagari letter, sign or joiner
_SUFFIX_ALT = "|".join(sorted(map(re.escape, SUFFIXES), key=len, reverse=True))


def name_present(name: str, text: str) -> bool:
    """True if the whole `name` appears in one piece: its words in the record's
    order, separated only by spaces, starting a word, with at most one allowed
    case ending after the LAST word. Fail-closed: anything else (stem changes,
    the oblique vowel, a longer name that starts with it, words in another order,
    or the parts scattered across the message) counts as absent."""
    words = name.split()
    if not words:
        return False
    body = r"\s+".join(map(re.escape, words))
    pat = (r"(?<!" + _LETTER + r")" + body
           + r"(?:" + _SUFFIX_ALT + r")?" + r"(?!" + _LETTER + r")")
    return re.search(pat, text) is not None


def fill(draft: str, rec: dict) -> str:
    """Substitute slots from the record. Unknown or missing slots raise."""
    d, m, y = rec["date"]
    vals = {
        "NAME": rec["name"], "PLACE": rec["place"], "REF": rec["ref"],
        "DATE": f"{str(d).translate(_DEV)} {MONTHS[m - 1]} {str(y).translate(_DEV)}",
        "AMOUNT": "₹" + indian_group(rec["amount"]).translate(_DEV),
    }
    found = re.findall(r"\{([A-Z]+)\}", draft)
    bad = [s for s in found if s not in vals]
    if bad:
        raise ValueError(f"unknown slot(s): {bad}")
    out = draft
    for k, v in vals.items():
        out = out.replace("{" + k + "}", v)
    return out


def _expected_facts(rec: dict) -> Counter:
    d, m, y = rec["date"]
    return Counter([("D", int(y), int(m), int(d)), ("N", str(int(rec["amount"])))])


def check(text: str, rec: dict) -> list:
    """Return a list of failure reasons; empty list means the text passed.

    Numbers, dates and amounts are read by the measured v2 extractor
    (src/factcheck.py, byte-identical to experiment/frozen_as_run/factcheck.py).
    The record has exactly one date and one amount, which are different fact
    types, so comparing them without regard to order cannot hide a swap.
    Any extra numeral, or a date missing its year, fails.
    """
    fails, t = [], text.translate(D)
    refs = re.findall(r"RTS/\d{4}/\d+", t)
    if refs != [rec["ref"]]:
        fails.append("ref")
    rest = re.sub(r"RTS/\d{4}/\d+", " ", t)
    got, want = Counter(facts_v2(rest)), _expected_facts(rec)

    def split(c):
        dates = Counter({f: n for f, n in c.items() if f[0] == "D"})
        return dates, c - dates

    got_dates, got_other = split(got)
    want_dates, want_other = split(want)
    if got_dates != want_dates:
        fails.append("date")
    if got_other != want_other:  # includes partial dates (no year) and extra numerals
        fails.append("amount_or_extra_number")
    for whole in (rec["name"], rec["place"]):
        if not name_present(whole, text):
            fails.append(f"missing:{whole}")
    return fails


def render_or_fallback(draft: str, template: str, rec: dict):
    """Return (text, source).

    Tries the draft, then the approved template. Both are checked. If neither
    passes, returns (None, "abstain") so a person writes the message by hand.
    """
    for source, body in (("draft", draft), ("template", template)):
        try:
            text = fill(body, rec)
        except ValueError:
            continue
        if not check(text, rec):
            return text, source
    return None, "abstain"
