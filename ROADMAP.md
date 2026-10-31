# Roadmap

The question: **when does a human approving AI output actually catch errors, and when is it a rubber stamp?**
The testbed is AI-drafted Marathi government messages, with a deterministic fact checker as one of the conditions.

Dates follow the Foresight application submitted on 31 Oct 2026, which proposed 1 Feb 2027 to 31 Jan 2028. A decision is expected around the end of January 2027. Phase 0 is work worth doing whether or not the grant comes through.

Status key: ✅ done · 🔄 in progress · ⬜ not started

---

## Phase 0: before the decision (Nov 2026 to Jan 2027, unfunded)
Goal: arrive at 1 Feb 2027 with the gate solid and the study design ready, so funded months go on new results.

| # | Task | Done when | Status |
|---|---|---|---|
| P0-1 | The product uses the measured extractor | `src/factcheck.py` byte-identical to the frozen file, with a test enforcing it; `verified.check` built on it | ✅ |
| P0-2 | Fresh data split for all future tests | The pre-registered split used hash buckets 0–2 (dev) and 8–9 (test). Buckets 3–7 were never used. Reserve 3–4 as DEV2 and 5–7 as TEST2, write this down before touching them, and pin the mahgrs commit (`experiment2/SPLIT.md`) | ✅ |
| P0-3 | Re-measure the product's record-based check | Run `verified.check` against scripted rewrites and corruptions on DEV2. Report false rejects and catches with intervals. TEST2 stays untouched. Dev result: 0 wrong decisions in 15,995 records (`experiment2/RESULTS_DEV2.md`); the final TEST2 run waits for P0-4 | 🔄 |
| P0-4 | Name and place matching | A list of Marathi case suffixes; a test set of name variants (inflections, spelling variants, a name inside a longer name); fix the known राम/रामचंद्र gap | ⬜ |
| P0-5 | Record schema and three notice types | A JSON schema for a record (name, place, ref, date, amount, decision, reason code), plus approved templates for three notice types, e.g. RTS application rejected, approved, documents missing | ⬜ |
| P0-6 | Error taxonomy for the study | Two lists: errors the checker can see (digits, dates, amounts, refs, names) and errors it cannot (decision flipped, wrong reason, wrong deadline written in words, wrong office). Each has a script that plants it | ⬜ |
| P0-7 | Draft study protocol | Conditions (reviewer alone / reviewer + checker / checker alone), outcomes (catch rate by error type, time, approvals without opening facts), hypothesis H1 (a passing check lowers catch rate for errors the checker cannot see), a power calculation that sets the number of reviewers and items, and an analysis plan | ⬜ |
| P0-8 | Review interface prototype | A minimal web page that shows a draft and the record, records approve or reject, time taken and whether the facts panel was opened, and writes an append-only log | ⬜ |
| P0-9 | Continuous integration | A GitHub Actions workflow runs `pytest` and checks the frozen hashes on every push | ✅ |
| P0-10 | A native-speaker reading | A native Marathi speaker reads the sample message and the three templates, and the corrections are committed | ⬜ |

Not code, but start now:
- **Passport and visa** (needed for the Berlin stay, May–June 2027). A passport can take weeks, so apply in November.
- **Line up annotators and reviewers.** Find 2 Marathi annotators and a pool of about 20 possible reviewers, and ask one or two department offices whether officers could take part.

## M1: tested gate (Feb to Apr 2027)
- Close out P0-3 and P0-4 if they are not finished.
- Publish the study protocol (P0-7) **before** any study data is collected: a dated commit, plus an external registry such as OSF so the date can be checked independently.
- Tag release `v0.1` under MIT.

## M2: generators against the gate (May to Jul 2027; Berlin stay 1 May to 12 June)
- Two or three open generators, including a small open Marathi model, produce 1,000+ drafts from records in the held-out set.
- Measure coverage (drafts that pass), false rejects and false accepts, with intervals. Facts inside a model draft are checked against the record.
- An optional LoRA fine-tune of one small model, using about 25% of the ~250 requested GPU-hours.
- Build the study item bank: drafts with planted errors from both lists in P0-6.
- Pilot the study with Node members in Berlin, and fix the protocol before the main run. Record every change as a dated amendment.

## M3: main study (Aug to Nov 2027)
- 12 reviewers, government officers if access allows, otherwise other Marathi readers. All three conditions, with condition order balanced across reviewers.
- Report catch rate by error type and condition, time taken, approvals without checking, and the H1 complacency effect, all with intervals and exactly as pre-specified. Any extra analysis is labelled exploratory.

## M4: publish (Dec 2027 to Jan 2028)
- The decision rule: when review adds value and when it is hollow, by error type and checker result.
- The open dataset (records, drafts, planted errors, anonymised reviewer decisions), the rerunnable method, and a short report.
- Tag release `v1.0`.

---

## Rules we keep
- Facts are copied from the record, never generated.
- No result is reported for something not yet tested. The README's "not tested" list is kept up to date.
- Every held-out set is used once for a final number. Tuning happens only on dev data.
- Changes to a frozen design are written down as dated amendments, before the data they affect is used.

## Known gaps (tracked)
- Names: a short name can match inside a longer one (राम / रामचंद्र).
- The strict line-comparison mode requires the record's fact order. The product check does not need it, because a record has one date and one amount of different types, but records with several amounts will.
- The checker checks facts, not the meaning of the wording around them. This is by design, and it is what the study measures.
- The exact mahgrs commit used for the October 2026 run was not recorded.
