"""Regression gate: every labelled case must get the right decision.

Cases are in regression_cases.jsonl, built by experiment2/build_regression.py.
Their labels come from how each case was constructed, never from the checker.

  false accept = a message that should FAIL passed. Dangerous: a wrong fact
                 could reach a citizen.
  false reject = a message that should PASS failed. Safe but costly: the
                 template is used instead of the draft.

Any single wrong decision fails CI and prints its class and an example.
"""
import json
import pathlib
import sys
from collections import Counter

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "src"))
from verified import check  # noqa: E402

CASES = [json.loads(line) for line in (HERE / "regression_cases.jsonl").read_text(encoding="utf-8").splitlines()]


def _decide(case):
    rec = dict(case["record"])
    rec["date"] = tuple(rec["date"])
    return not check(case["message"], rec)


def _wrong(expect):
    bad = [c for c in CASES if c["expect"] == expect and _decide(c) != (expect == "pass")]
    by_class = Counter(f'{c["area"]}: {c["class"]}' for c in bad)
    example = bad[0]["message"] if bad else ""
    return len(bad), by_class, example


def test_case_file_is_not_empty_and_covers_both_directions():
    kinds = Counter((c["area"], c["expect"]) for c in CASES)
    for area in ("numbers", "names"):
        assert kinds[(area, "pass")] > 500 and kinds[(area, "fail")] > 500, kinds


def test_no_false_accepts():
    n, by_class, example = _wrong("fail")
    assert n == 0, f"{n} FALSE ACCEPTS (should have been rejected): {dict(by_class)}\nexample: {example}"


def test_no_false_rejects():
    n, by_class, example = _wrong("pass")
    assert n == 0, f"{n} FALSE REJECTS (should have passed): {dict(by_class)}\nexample: {example}"
