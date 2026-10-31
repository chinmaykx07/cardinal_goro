# Claims ledger

Every claim we make in public (the README, the Foresight application, talks, posts) should have a row here, with its evidence and status. **If a claim is not in this table, don't make it.** If a result changes, update the row first, then everything that quotes it.

## Words we use
- **False accept**: a message with a wrong fact **passed** the checker. *This is the dangerous error*, because a wrong amount, date or name could reach a citizen. Target: zero.
- **False reject**: a correct message was **blocked**. Safe but costly, because the template is used instead of the draft. It is kept low and measured.
- **Rejected by design**: correct Marathi that the fail-closed rule refuses on purpose (for example रामाला, or पाटील सुनीता). These are counted as false rejects we accept, and reported separately.

## Status levels
- **FINAL**: a held-out set used once, with the design and code frozen beforehand.
- **DEV**: measured on development data that we are allowed to tune on. Never quote it as final.
- **FACT**: a checkable fact about what we did or about a source.
- **UNTESTED**: not measured. Only ever say it as "not yet tested".

## Ledger (as of 31 Oct 2026)
| # | Claim | Status | Evidence |
|---|---|---|---|
| 1 | The checker experiment used 150,000 real lines from Maharashtra government resolutions, tuned on 30% of documents (buckets 0–2), with the final run on a separate 20% (buckets 8–9) and the code frozen by hash | FINAL | `experiment/PREREGISTRATION.md`, `experiment/code_hashes.txt`, `experiment/split.py` |
| 2 | The first checker (v0) wrongly rejected 63.9% of valid date-format changes (9,171/14,355) and caught 0 of 2,024 lakh/crore/thousand swaps | FINAL | `experiment/test_run.txt` |
| 3 | The rebuilt checker (v2, strict) wrongly rejected at most 0.25% of valid rewrites in any rewrite type (5/2,024; 95% upper bound 0.58%) | FINAL | `experiment/test_run.txt` |
| 4 | v2 strict caught at least 99.85% of corruptions in each of the 11 error types (lowest: 2,021/2,024) | FINAL | `experiment/test_run.txt` |
| 5 | One pre-set criterion was missed: amount in words, 626/626 caught, but the 95% lower bound of 99.41% is below the 99.5% bar | FINAL | `experiment/PREREGISTRATION.md` |
| 6 | The first test launch crashed with no output and was re-run with identical hashes | FACT | `experiment/PREREGISTRATION.md` |
| 7 | The October test plan was written down before the final run, in the repo; it was **not** on an external registry | FACT | `experiment/PREREGISTRATION.md` |
| 8 | The exact data commit for the October run was not recorded | FACT | `README.md` |
| 9 | The fresh split (DEV2 = buckets 3–4, TEST2 = 5–7) and the data commit were declared and pushed before any file in buckets 3–7 was opened | FACT | git history: commit d5d8e15 precedes all use; `experiment2/SPLIT.md` |
| 10 | The product's record-based check made 0 wrong decisions on 15,995 DEV2 records with real date and amount formats (95% upper bounds 0.02%–0.07% per class) | **DEV** | `experiment2/RESULTS_DEV2.md`, `dev2_run.txt` |
| 11 | Name and place checking made 0 wrong decisions across 17 classes, 10,000 synthetic records each (95% upper bounds 0.04%–0.05%) | **DEV** (synthetic names, draft endings list) | `experiment2/RESULTS_NAMES_DEV.md`, `name_run.txt` |
| 12 | The previous per-part name check accepted 500/500 messages naming the wrong person when the first name appeared elsewhere | DEV (control) | `experiment2/RESULTS_NAMES_DEV.md` |
| 13 | The shipped extractor `src/factcheck.py` is byte-identical to the measured one | FACT, enforced in CI | `tests/test_verified.py` |
| 14 | No known wrong decision on the 13,149-case regression set; CI fails on any false accept or false reject | FACT, enforced in CI | `tests/test_regression.py` |
| 15 | The data (orgpedia/mahgrs) is MIT licensed | FACT | the LICENSE file in that repo |
| 16 | Any AI text generator against the gate | UNTESTED | milestone M2 |
| 17 | The reviewer study (catch rates, complacency) | UNTESTED | milestone M3 |
| 18 | Real citizen notices (government resolutions are a stand-in) | UNTESTED | |
| 19 | Real-world names, initials, transliterated names, and a native-reviewed endings list | UNTESTED | issues #4, #9 |
| 20 | The final (TEST2) number for the record-based check | UNTESTED | issue #3; run once after the native review |

## Things we must not say
- "Zero errors" or "error-free": every zero above is "0 observed in n", with an upper bound.
- "Pre-registered" for the October run: say "pre-specified in the repository".
- "Tested on names" without "synthetic, dev, draft endings list".
- "Never measured" about human oversight in general: say "rarely measured".

## Note on the Foresight application (submitted 31 Oct 2026)
At submission it said names and places were not yet tested, which was true then. Rows 10–12 came later the same day and are DEV results. They do not change anything the application claimed.
