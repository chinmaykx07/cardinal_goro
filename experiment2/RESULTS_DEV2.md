# P0-3 dev result: the product's record-based check on DEV2

**Status: a dev result, not a final one.** It was run on DEV2 (buckets 3–4), where tuning is allowed. The final number will come from one frozen run on TEST2 (buckets 5–7), after the name and place work in P0-4 changes `verified.py`. Re-measuring after every change is the point of keeping TEST2 untouched.

Run: 31 Oct 2026. Data: orgpedia/mahgrs `c96e88f731589e1284ecab60ff1a63d3b9c6bb82`. Command:
```
MAHGRS=<mahgrs>/GRs python3 -I record_eval.py dev2 20000 20261031
```
Full output: `dev2_run.txt`, `results_record_dev2.json`.

## What was measured
`src/verified.py: check(message, record)` decides whether a message carries exactly the record's facts. Each test case is built as follows:
- **The date and the amount are real.** Each is copied with its exact surface form from a DEV2 line: Devanagari or Latin digits, `/ . -` separators, month names, odd comma groupings such as `६५२,५८,१४,०८२`, decimals such as `रु.४४.००`, and lakh/crore words. The record value is parsed by `record_eval.py`'s own code, not by the checker.
- **The name, place and reference number are synthetic.**
- **The surrounding wording comes from one of three provisional templates**, not yet reviewed by a native speaker.

Each base message must pass. Then each scripted rewrite (must pass) and each corruption (must fail) from the frozen `experiment/transforms.py` is applied. Those transforms label cases by construction.

**Records: 15,995**, which is every usable रु./₹ amount found in the 20,176 DEV2 files.

## Result
| Class | n | Wrong | 95% CI upper bound |
|---|---|---|---|
| Base message (real formats, unchanged), must pass | 15,995 | 0 | 0.02% |
| 8 valid rewrite types, must pass | 5,037 to 15,995 each | 0 | 0.02% to 0.07% |
| 10 corruption types, must fail | 5,037 to 15,995 each | 0 | 0.02% to 0.07% |
| Same corruptions, restricted to those that hit the real date or amount (reference number intact) | 5,037 to 15,995 each | 0 | 0.02% to 0.07% |

All 15,995 base messages passing also means the checker's extractor and this harness's independent parser agreed on every real date and amount span.

A control shows the harness can detect failures: a deliberately weakened check that ignores amounts missed 44 of 300 digit substitutions.

## What this does NOT show
- **Real generated text.** Only the date and amount spans are real; the wording is from fixed templates. A model's draft may phrase things in ways not covered.
- **Harder records.** Each message has one date and one amount, which are different fact types, so their order cannot matter. Records with several amounts or several dates will be harder.
- **Amounts without a rupee sign** (for example `१२ लाख` alone) were not sampled, and **amounts in words** (`अक्षरी … फक्त`) do not occur in these templates.
- **Names and places.** They are synthetic and not corrupted here. That is P0-4.
- **Errors beyond the scripted classes.** The corruptions are the ones we designed.
- **Shared blind spots.** If the harness parser and the checker had the same blind spot for some format, cases in that format would be left out silently rather than counted as errors. Their agreement on 15,995 real spans lowers this risk but does not rule it out.
