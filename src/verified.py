"""Placeholder fill + strict checker for Marathi decision messages.

Facts (name, place, ref, date, amount) are never generated: the drafter emits
{NAME} {PLACE} {REF} {DATE} {AMOUNT} slots and fill() copies from the record.
check() then verifies the final text; anything doubtful returns reasons, and the
caller falls back to the approved template.
"""
import re

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


def check(text: str, rec: dict) -> list:
    """Return a list of failure reasons; empty list means the text passed."""
    fails, t = [], text.translate(D)
    refs = re.findall(r"RTS/\d{4}/\d+", t)
    if refs != [rec["ref"]]:
        fails.append("ref")
    t = re.sub(r"RTS/\d{4}/\d+", " ", t)
    pat = r"(\d{1,2})\s+(" + "|".join(MONTHS) + r")\s+(\d{4})"
    dates = [(int(a), MONTHS.index(b) + 1, int(c)) for a, b, c in re.findall(pat, t)]
    t = re.sub(pat, " ", t)
    dates += [(int(a), int(b), int(c)) for a, b, c in re.findall(r"(\d{1,2})/(\d{1,2})/(\d{4})", t)]
    t = re.sub(r"(\d{1,2})/(\d{1,2})/(\d{4})", " ", t)
    if dates != [tuple(rec["date"])]:
        fails.append("date")
    nums = [int(x.replace(",", "")) for x in re.findall(r"\d[\d,]*", t)]
    if nums != [rec["amount"]]:
        fails.append("amount_or_extra_number")
    for part in rec["name"].split() + [rec["place"]]:
        if part not in text:  # strict, exact; inflected forms still contain the stem
            fails.append(f"missing:{part}")
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
