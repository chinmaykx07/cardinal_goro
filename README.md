# Verified Marathi decision messages

An open verification gate for AI-drafted messages to citizens. Facts (names, dates, amounts, reference numbers) are copied from the official record and never generated. A deterministic checker compares each draft with the record. If anything differs, the draft is replaced by an approved template, and if the template fails too, the system abstains. An officer approves every message before it is sent.

Status: research prototype. Not in production use.

## What has been measured
A pre-registered experiment on 150,000 real lines from Maharashtra government resolutions (orgpedia/mahGRs, MIT). The checker was tuned on 30% of documents, its code hashes were frozen, and then it was run once on a separate 20%. Errors were inserted by script, so the correct answers are known.

| | First checker (v0) | Rebuilt checker (v2, strict) |
|---|---|---|
| Valid date rewrites wrongly rejected | 63.9% | 0.0% |
| Month written in words, wrongly rejected | 100% | 0.0% |
| Crore/lakh written in full, wrongly rejected | 99.95% | 0.25% (95% upper bound 0.58%) |
| Month changed, caught | 4.7% | 99.99% |
| Lakh/crore/thousand swapped, caught | 0% | 99.85% |
| Two values swapped, caught | 0.7% | 100% |
| Amount in words changed, caught | 0% | 100% (626/626) |

Full output: `experiment/test_run.txt`, `experiment/results_test.json`. Design, pass criteria, amendment and results: `experiment/PREREGISTRATION.md`.

One pre-set criterion was missed: for "amount in words", 626 of 626 were caught, but that is too few cases to prove the 99.5% bar at 95% confidence.

## What is NOT tested (please do not cite these results for them)
- **Free rewording by a model.** The valid rewrites are changes of format (digit script, commas, date style, rupee sign, spacing), not paraphrase.
- **Changes to the order of facts.** The strict checker assumes the draft keeps the record's order of facts. An order-free comparison catches only 17.8% of swapped values.
- **Names and places**, and **any generator** (LLM, ByT5, NCM).
- **Citizen notices.** Government resolutions are used as a stand-in.
- **Errors beyond the 11 scripted classes.**
- **The English-translation cross-check** in `experiment/audit.py` is weak (dates 96.6%, rupee amounts 76.1%), because the translations are machine-made and often garbled.

## Layout
- `experiment/`: the measured checker (`factcheck.py`), scripted rewrites and corruptions (`transforms.py`), document split (`split.py`), harness (`run_eval.py`) and audit.
  - `frozen_as_run/` holds the exact files that were run; they match `code_hashes.txt`.
  - The top-level copies differ only in file paths.
- `src/verified.py`: the message flow (fill slots from the record, check, fall back to the template, abstain).
  - It reads numbers, dates and amounts with `src/factcheck.py`, which is byte-identical to the measured `experiment/frozen_as_run/factcheck.py`. A test enforces this.
  - The extractor is the measured one, but the comparison against a structured record is new and has not been run on the 150,000-line test. Re-measuring it on fresh data is on the roadmap.
  - Names and places are matched by exact spelling at the start of a word. A suffix is allowed for inflection, so a short name can still falsely match inside a longer one (for example राम inside रामचंद्र).
- `src/checker_prototype.py`: an earlier checker tested only on synthetic data. Kept for history.
- `tests/`: unit tests for `src/verified.py`.
- `ROADMAP.md`: the plan, with milestones.

## Run
```
pip install -r requirements.txt
python3 -m pytest tests
```
Reproduce the experiment (about 10 minutes):
```
git clone https://github.com/orgpedia/mahgrs
cd experiment
MAHGRS=<path-to-clone>/GRs PER_FILE=8 python3 -I run_eval.py test 150000 20261030 0
```
The exact mahgrs commit used on 30 Oct 2026 was not recorded. On 31 Oct 2026 its HEAD was `c96e88f731589e1284ecab60ff1a63d3b9c6bb82`. Later commits may change the sample.

The test split has now been used once. Comparisons on it are no longer a fair held-out test, so use fresh data or a new split for new work.

## Roadmap
See [ROADMAP.md](ROADMAP.md). In short: a tested gate with names and places, then open generators tested against the gate, then a pre-specified reviewer study (reviewer alone, reviewer helped by the checker, checker alone), then an open decision rule for when human review adds value.

## Licence
MIT. See `LICENSE`. Data: orgpedia/mahGRs (MIT).
