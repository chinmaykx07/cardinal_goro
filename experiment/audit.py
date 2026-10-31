"""Extractor audit: do dates and amounts found in the Marathi text also appear in the English translation (same GR)?"""
import os, random, re, sys, json
from decimal import Decimal
import os as _os; sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import split, factcheck as F
from scipy.stats import beta

EN_MONTHS = {m: i + 1 for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july",
                                             "august", "september", "october", "november", "december"])}
EN_MONTHS.update({k[:3]: v for k, v in list(EN_MONTHS.items())})
EN_MONTHS["sept"] = 9
MAGV = {"crore": 10 ** 7, "crores": 10 ** 7, "lakh": 10 ** 5, "lakhs": 10 ** 5, "lac": 10 ** 5, "thousand": 10 ** 3}


def cp(k, n, a=0.05):
    lo = 0.0 if k == 0 else beta.ppf(a / 2, k, n - k + 1)
    hi = 1.0 if k == n else beta.ppf(1 - a / 2, k + 1, n - k)
    return lo, hi


def en_dates(t):
    t = t.lower()
    out = set()
    mon = "|".join(sorted(EN_MONTHS, key=len, reverse=True))
    for d, m, y in re.findall(r"(\d{1,2})(?:st|nd|rd|th)?\s*(" + mon + r")\.?,?\s*(\d{4})", t):
        out.add((int(y), EN_MONTHS[m], int(d)))
    for m, d, y in re.findall(r"(" + mon + r")\.?\s*(\d{1,2})(?:st|nd|rd|th)?,?\s*(\d{4})", t):
        out.add((int(y), EN_MONTHS[m], int(d)))
    for d, m, y in re.findall(r"(?<!\d)(\d{1,2})\s*[./\-]\s*(\d{1,2})\s*[./\-]\s*(\d{4})(?!\d)", t):
        out.add((int(y), int(m), int(d)))
    return out


def en_money(t):
    t = t.lower()
    vals = set()
    for num, mag in re.findall(r"((?:\d{1,3}(?:,\d{2,3})+|\d+)(?:\.\d+)?)\s*(crores?|lakhs?|lac|thousand)?", t):
        try:
            v = Decimal(num.replace(",", ""))
        except Exception:
            continue
        vals.add(format((v * (MAGV[mag] if mag else 1)).normalize(), "f"))
    return vals


def mr_items(text):
    t = F.normalise(text)
    dates, money = [], []
    for m in F.V2_RE.finditer(t):
        if m.group("dn"):
            dates.append((int(m.group("dn_y")), F.MONTH_LOOKUP[m.group("dn_m")], int(m.group("dn_d"))))
        elif m.group("ds"):
            dates.append((int(m.group("ds_y")), int(m.group("ds_m")), int(m.group("ds_d"))))
        elif m.group("money") and (m.group("mn") is not None):  # amounts introduced by a rupee sign
            n = m.group("mn")
            mag = m.group("mg")
            v = Decimal(n.replace(",", "")) * (F.MAG[mag] if mag else 1)
            money.append((format(v.normalize(), "f"), m.group(0)))
    return dates, money


def main(ndocs, seed):
    fs = [p for p in split.files("test")]
    random.Random(seed).shuffle(fs)
    dd = dm = cd = cm = used = 0
    miss_d, miss_m = [], []
    for p in fs:
        en = p.replace(".mr.txt", ".en.txt")
        if not os.path.exists(en):
            continue
        try:
            mr_t = open(p, encoding="utf-8").read()
            en_t = open(en, encoding="utf-8").read()
        except Exception:
            continue
        dates, money = mr_items(mr_t)
        if not dates and not money:
            continue
        used += 1
        E_d, E_m = en_dates(en_t), en_money(en_t)
        for d in set(dates):
            dd += 1
            if d in E_d:
                cd += 1
            elif len(miss_d) < 400:
                miss_d.append((os.path.basename(p), d))
        for v, raw in set(money):
            dm += 1
            if v in E_m:
                cm += 1
            elif len(miss_m) < 400:
                miss_m.append((os.path.basename(p), v, raw))
        if used >= ndocs:
            break
    print(f"docs audited: {used}")
    for name, k, n in (("dates", cd, dd), ("rupee amounts", cm, dm)):
        lo, hi = cp(k, n)
        print(f"{name:14s} corroborated in the English translation: {k}/{n} = {100*k/n:.1f}%   95% CI [{100*lo:.1f}, {100*hi:.1f}]")
    json.dump({"miss_dates": miss_d[:60], "miss_money": miss_m[:60]}, open("audit_misses.json", "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]))
