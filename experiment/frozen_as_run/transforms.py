"""Label-by-construction transforms. Valid rewrites keep the meaning of every numeral; corruptions change it.
The meaning test (`sem`) is deliberately independent of the checker's extractor."""
import random
import re
from decimal import Decimal

DEV = "०१२३४५६७८९"
ASC = "0123456789"
TO_ASC = str.maketrans(DEV, ASC)
TO_DEV = str.maketrans(ASC, DEV)
TOKEN = re.compile(r"[०-९0-9]+(?:[.,/\-][०-९0-9]+)*")
GROUPED = re.compile(r"\d{1,3}(?:,\d{2,3})+(?:\.\d+)?")
MONTHS_CANON = ["जानेवारी", "फेब्रुवारी", "मार्च", "एप्रिल", "मे", "जून", "जुलै", "ऑगस्ट",
                "सप्टेंबर", "ऑक्टोबर", "नोव्हेंबर", "डिसेंबर"]
MAGS = ["कोटी", "लाख", "हजार"]
MAG_VAL = {"कोटी": 10 ** 7, "लाख": 10 ** 5, "हजार": 10 ** 3}


def sem(tok):
    """Meaning of one numeral token, computed without the checker."""
    a = tok.translate(TO_ASC)
    if GROUPED.fullmatch(a):
        return ("n", Decimal(a.replace(",", "")))
    if re.fullmatch(r"\d+\.\d+", a):
        return ("n", Decimal(a))
    return ("r", tuple(int(x) for x in re.split(r"\D+", a) if x))


def tokens(line):
    return [(m.start(), m.end(), m.group(0)) for m in TOKEN.finditer(line)]


def _script(tok):
    return "dev" if re.search(r"[०-९]", tok) else "asc"


def _conv(s, script):
    return s.translate(TO_DEV) if script == "dev" else s


def _splice(line, a, b, new):
    return line[:a] + new + line[b:]


def _digit_positions(tok):
    return [i for i, c in enumerate(tok) if c in DEV or c in ASC]


def _other_digit(c, rnd):
    pool = DEV if c in DEV else ASC
    return rnd.choice([x for x in pool if x != c])


# --------------------------------------------------------------------------- corruptions (must be REJECTED)
def c_substitute(line, rnd):
    toks = tokens(line)
    if not toks:
        return None
    for _ in range(6):
        a, b, t = rnd.choice(toks)
        pos = rnd.choice(_digit_positions(t))
        new = t[:pos] + _other_digit(t[pos], rnd) + t[pos + 1:]
        if sem(new) != sem(t):
            return _splice(line, a, b, new)
    return None


def c_transpose(line, rnd):
    toks = tokens(line)
    rnd.shuffle(toks)
    for a, b, t in toks:
        ps = [i for i in range(len(t) - 1) if t[i] in DEV + ASC and t[i + 1] in DEV + ASC and t[i] != t[i + 1]]
        if not ps:
            continue
        i = rnd.choice(ps)
        new = t[:i] + t[i + 1] + t[i] + t[i + 2:]
        if sem(new) != sem(t):
            return _splice(line, a, b, new)
    return None


def c_delete(line, rnd):
    toks = tokens(line)
    rnd.shuffle(toks)
    for a, b, t in toks:
        pos = rnd.choice(_digit_positions(t))
        new = t[:pos] + t[pos + 1:]
        if new and TOKEN.fullmatch(new) and sem(new) != sem(t):
            return _splice(line, a, b, new)
    return None


def c_insert(line, rnd):
    toks = tokens(line)
    rnd.shuffle(toks)
    for a, b, t in toks:
        pos = rnd.randrange(len(t) + 1)
        d = rnd.choice(DEV if _script(t) == "dev" else ASC)
        new = t[:pos] + d + t[pos:]
        if TOKEN.fullmatch(new) and sem(new) != sem(t):
            return _splice(line, a, b, new)
    return None


def c_drop(line, rnd):
    toks = tokens(line)
    if not toks:
        return None
    a, b, t = rnd.choice(toks)
    return _splice(line, a, b, "")


def c_extra(line, rnd):
    toks = tokens(line)
    if not toks:
        return None
    spots = [m.start() for m in re.finditer(r" ", line)]
    if not spots:
        return None
    s = _script(toks[0][2])
    ins = " " + _conv(str(rnd.randint(11, 99)), s) + " "
    p = rnd.choice(spots)
    return line[:p] + ins + line[p + 1:]


def c_year(line, rnd):
    ms = list(re.finditer(r"(?<!\d)(\d{4})(?!\d)", line.translate(TO_ASC)))
    ms = [m for m in ms if 1900 <= int(m.group(1)) <= 2100]
    if not ms:
        return None
    m = rnd.choice(ms)
    new = str(int(m.group(1)) + rnd.choice([-1, 1]))
    orig = line[m.start():m.end()]
    return _splice(line, m.start(), m.end(), _conv(new, _script(orig)))


def c_month(line, rnd):
    ms = list(re.finditer(r"(?<![\u0900-\u097F])(?:" + "|".join(MONTHS_CANON) + r")(?![\u0900-\u097F])", line))
    ms = [m for m in ms if re.search(r"(?<![०-९0-9])[०-९0-9]{1,2}\s*$", line[:m.start()])]
    if not ms:
        return None
    m = rnd.choice(ms)
    other = rnd.choice([x for x in MONTHS_CANON if x != m.group(0)])
    return _splice(line, m.start(), m.end(), other)


def c_mag(line, rnd):
    ms = list(re.finditer(r"(?<=[०-९0-9])\s*(कोटी|लाख|हजार)", line))
    if not ms:
        return None
    m = rnd.choice(ms)
    w = m.group(1)
    other = rnd.choice([x for x in MAGS if x != w])
    return _splice(line, m.start(1), m.end(1), other)


def c_swap(line, rnd):
    toks = tokens(line)
    pairs = [(i, j) for i in range(len(toks)) for j in range(i + 1, len(toks)) if sem(toks[i][2]) != sem(toks[j][2])]
    if not pairs:
        return None
    i, j = rnd.choice(pairs)
    (a1, b1, t1), (a2, b2, t2) = toks[i], toks[j]
    return line[:a1] + t2 + line[b1:a2] + t1 + line[b2:]


NUMWORDS = ["एक", "दोन", "तीन", "चार", "पाच", "सहा", "सात", "आठ", "नऊ", "दहा", "वीस", "तीस", "चाळीस",
            "पन्नास", "साठ", "सत्तर", "ऐंशी", "नव्वद", "शंभर", "हजार", "लाख", "कोटी"]


def c_words(line, rnd):
    m = re.search(r"अक्षरी[^)\n]{3,200}?फक्त", line)
    if not m:
        return None
    span = m.group(0)
    hits = [w for w in re.finditer(r"(?<![\u0900-\u097F])(" + "|".join(NUMWORDS) + r")(?![\u0900-\u097F])", span)]
    if not hits:
        return None
    h = rnd.choice(hits)
    other = rnd.choice([w for w in NUMWORDS if w != h.group(1)])
    new = span[:h.start()] + other + span[h.end():]
    return line[:m.start()] + new + line[m.end():]


CORRUPTIONS = {
    "digit substituted": c_substitute,
    "digits transposed": c_transpose,
    "digit deleted": c_delete,
    "digit inserted": c_insert,
    "numeral dropped": c_drop,
    "extra numeral added": c_extra,
    "year off by one": c_year,
    "month changed": c_month,
    "lakh/crore/thousand swapped": c_mag,
    "two values swapped": c_swap,
    "amount in words changed": c_words,
}


# --------------------------------------------------------------------------- valid rewrites (must be ACCEPTED)
def v_script(line, rnd):
    if not TOKEN.search(line):
        return None
    new = line.translate(TO_ASC) if re.search(r"[०-९]", line) else line.translate(TO_DEV)
    return new if new != line else None


def _western(digits):
    s = digits
    out = []
    while len(s) > 3:
        out.insert(0, s[-3:])
        s = s[:-3]
    out.insert(0, s)
    return ",".join(out)


def v_commas(line, rnd):
    toks = [(a, b, t) for a, b, t in tokens(line) if GROUPED.fullmatch(t.translate(TO_ASC))]
    if not toks:
        return None
    a, b, t = rnd.choice(toks)
    s = t.translate(TO_ASC)
    ip, _, fp = s.partition(".")
    digits = ip.replace(",", "")
    new = rnd.choice([_western(digits), digits]) + ("." + fp if fp else "")
    if new == s:
        return None
    return _splice(line, a, b, _conv(new, _script(t)))


def v_date_format(line, rnd):
    ms = [m for m in re.finditer(r"(?<![\d.,/\-])(\d{1,2})([./\-])(\d{1,2})\2(\d{4})(?!\d)", line.translate(TO_ASC))]
    if not ms:
        return None
    m = rnd.choice(ms)
    d, sep, mo, y = m.group(1), m.group(2), m.group(3), m.group(4)
    sep2 = rnd.choice([x for x in "./-" if x != sep])
    pad = rnd.choice([True, False])
    d2, mo2 = (d.zfill(2), mo.zfill(2)) if pad else (str(int(d)), str(int(mo)))
    new = f"{d2}{sep2}{mo2}{sep2}{y}"
    orig = line[m.start():m.end()]
    if new == orig.translate(TO_ASC):
        return None
    return _splice(line, m.start(), m.end(), _conv(new, _script(orig)))


def v_date_name(line, rnd):
    """numeric date -> 'dd <month>, yyyy' with the canonical month spelling."""
    ms = [m for m in re.finditer(r"(?<![\d.,/\-])(\d{1,2})[./\-](\d{1,2})[./\-](\d{4})(?!\d)", line.translate(TO_ASC))]
    ms = [m for m in ms if 1 <= int(m.group(2)) <= 12 and 1 <= int(m.group(1)) <= 31]
    if not ms:
        return None
    m = rnd.choice(ms)
    orig = line[m.start():m.end()]
    new = f"{int(m.group(1))} {MONTHS_CANON[int(m.group(2)) - 1]}, {m.group(3)}"
    return _splice(line, m.start(), m.end(), _conv(new, _script(orig)))


def v_magnitude(line, rnd):
    ms = list(re.finditer(r"((?:\d{1,3}(?:,\d{2,3})+|\d+)(?:\.\d+)?)\s*(कोटी|लाख|हजार)", line.translate(TO_ASC)))
    if not ms:
        return None
    m = rnd.choice(ms)
    val = Decimal(m.group(1).replace(",", "")) * MAG_VAL[m.group(2)]
    if val != val.to_integral_value():
        return None
    digits = str(int(val))
    new = rnd.choice([digits, _western(digits)])
    orig = line[m.start():m.end()]
    return _splice(line, m.start(), m.end(), _conv(new, _script(orig)))


def v_rupee(line, rnd):
    if "रु." in line and re.search(r"रु\.\s*[०-९0-9]", line):
        return line.replace("रु.", "₹", 1)
    if "₹" in line:
        return line.replace("₹", "रु.", 1)
    return None


def v_suffix(line, rnd):
    for m in re.finditer(r"रु\.\s*([०-९0-9]{1,3}(?:,[०-९0-9]{2,3})+(?:\.[०-९0-9]+)?|[०-९0-9]+(?:\.[०-९0-9]+)?)", line):
        rest = line[m.end():]
        if re.match(r"\s*(?:कोटी|कोटि|लाख|लक्ष|हजार|सहस्र|/-)", rest) or re.match(r"[०-९0-9.,]", rest):
            continue
        return line[:m.end()] + "/-" + line[m.end():]
    return None


def v_space(line, rnd):
    spots = [m.start() for m in re.finditer(r" ", line)]
    if not spots:
        return None
    p = rnd.choice(spots)
    return line[:p] + "  " + line[p + 1:]


VALIDS = {
    "digit script swapped (Devanagari/Latin)": v_script,
    "comma grouping changed": v_commas,
    "date separator or padding changed": v_date_format,
    "date written with month name": v_date_name,
    "crore/lakh written out in full": v_magnitude,
    "rupee sign changed (रु./₹)": v_rupee,
    "trailing /- added": v_suffix,
    "extra spaces": v_space,
}
