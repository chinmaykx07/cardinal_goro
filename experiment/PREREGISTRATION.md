# Pre-registration: fact-checker experiment on real Marathi government text

Written 30 Oct 2026, BEFORE any evaluation on the test split.

## Question
When a message contains numerals, dates and amounts, can a deterministic checker (a) accept every legitimate
rewriting of those facts and (b) reject every corrupted one? Measured on real Maharashtra GR text, not invented formats.

## Data
- Corpus: orgpedia/mahGRs (MIT), ~101,000 Marathi `.mr.txt` files, GRs of the Government of Maharashtra.
- Split by hash of file name (sha1 mod 10): DEV = 0,1,2 ; TEST = 8,9 ; the rest unused.
- Units: single lines (20 to 400 characters) containing at least one numeral.
- Rule: all design and tuning on DEV only. The checker is frozen (git-style hash recorded) before TEST is run once.

## Labels by construction (not by my judgment)
- VALID rewrites (checker must ACCEPT): digit script swap, comma regrouping (Indian/Western/none), date re-formatting
  (month-name / dd.mm.yyyy / dd/mm/yyyy), "रु." / "₹" prefix swap, magnitude re-expression (कोटी/लाख/हजार vs full digits), whitespace.
- CORRUPTIONS (checker must REJECT): one-digit substitution, adjacent transposition, digit deletion, digit insertion,
  month swap, year +/- 1, magnitude word swap, dropped numeral, extra numeral, swapped values between two different numerals.
- A corruption counts only if the numeric value of the affected numeral really changes (computed independently of the checker).

## Checkers compared
- v0: the checker logic shown in the first deck (month-name and dd/mm/yyyy dates, comma amounts), generalised minimally
  to compare all numerals as a multiset. No tuning.
- v2: designed on DEV only. Canonicalises numerals, dates and amounts; compares ordered facts (strict) and multisets (lenient).

## Pass criteria (set now)
- C1  Per corruption class (excluding value-swap), v2-strict detection: exact 95% lower confidence bound >= 99.5%.
- C2  Over all VALID rewrites, v2 false-reject rate: exact 95% upper confidence bound <= 5%.
- C3  Value-swap detection is reported for strict and lenient modes. No pass criterion; it is a known limitation of multiset comparison.
- Report: v0 on the same data, with confidence intervals. Report failures honestly, including any criterion missed.

## Extractor audit (independent signal)
For each GR in TEST, check that dates and amounts extracted from the Marathi text also appear (as ASCII digits)
in the English translation of the same GR. Reported as a corroboration rate. The English text is machine-translated,
so this is a proxy, not ground truth.

## What this does NOT test
- Any generator (NCM, ByT5, LLM). It tests the checker's canonicalisation only.
- Names and places. Those are copied through placeholders; they are not covered here.
- Citizen-notice style text. GR text is formal and long; this is a proxy for numeral formats used by this government.

## Amendment 1 (30 Oct 2026, made on DEV evidence, BEFORE any TEST evaluation)
Dev runs exposed three things; none used TEST data.
1. Harness bugs fixed (not checker changes): the "/-" rewrite could land inside a number; the month-change test hit "मे." (megawatt).
2. Checker fixes: dates after "दि." were not recognised; day+month without year (dates wrapped across lines) and month+year added;
   "रू."/"रूपये" recognised as rupee signs; money and plain integers share one canonical form; non-money decimals stay literal.
3. New corruption class added: "amount in words changed" (numbers written in words inside "(अक्षरी ... फक्त)").
   The v2 checker gains a fail-closed rule: the whole "अक्षरी ... फक्त" span is a literal fact.
   Criterion C1 now includes this class. No other criteria changed.
Dev numbers are NOT the result: they were used to tune. TEST is run once, after this file is saved, with the frozen code hash below.

## Frozen code (sha256), recorded before the TEST run
```
35728c75b8cb3310aa1b63e94a4b256d18356d50fee31f9e2df911c92e9fab43  factcheck.py
54e0f532dd176eaba528cb6ae70031def1d8bb78494caa553055c8c66b20421e  transforms.py
db95c114bee7eb46d91a90f09763cd10d9d5346cf04cc15b0222f2587cee64c1  run_eval.py
aeb7099dc98f7148fcaf8bd687d6f238f6f0cd422e1159dcf47beb672fbf0b4f  split.py
```
TEST run: 8 numeral lines per file, seed 20261030, executed once.

## RESULTS (TEST split, one completed run; the first launch died silently with no output, re-run with identical hashes)
150,000 numeral lines from ~20,000+ GRs in buckets 8-9, seed 20261030. Full output: test_run.txt, results_test.json.
- C2 PASS. v2 false-reject, worst class: 0.25% (5/2024, CI upper 0.58%) "crore/lakh in full". All others <=0.10%.
- C1 MISS on one class by sample size: "amount in words changed" 626/626 detected, exact lower bound 99.41% < 99.5%. Zero misses observed.
  All other 10 classes pass (tightest: lakh/crore/thousand swapped 2021/2024, lower bound 99.57%).
- C3: value swaps detected: strict 95542/95545 (100.00%), lenient multiset 17046/95545 (17.84%), v0 691/95545 (0.72%).
- v0 (first deck) on same data: false-rejects 63.9% of date separator changes, 100% of month-name dates, 99.95% of crore-in-full;
  detects 4.7% of month changes, 0% of magnitude swaps, 0% of words changes.
- Diagnosis of the remaining v2 wrong decisions (post-hoc, no code changed): mostly OCR-garbled table lines and harness artefacts
  (equal-valued "70" vs "70.00" swaps are not true corruptions). One genuine limitation: changing "रु." to "₹" INSIDE the
  "(अक्षरी ... फक्त)" span is rejected (fail-closed by design).
- Extractor audit (English translation, 3000 GRs): dates corroborated 20273/20990 = 96.6% [96.3, 96.8];
  rupee amounts 3828/5030 = 76.1% [74.9, 77.3]. The English side is machine-translated and often garbled
  (spaces inside numbers, "lakh" rendered as "Attention"), so this is a weak lower bound, not a measure of extractor error.
