# Contributing

This project's value is that its claims can be checked. Every contribution has to keep it that way.

## The rules
1. **Facts are copied from the record, never generated.** No code path may let a model write a name, date, amount or reference number into a message.
2. **Fail closed.** When the checker is unsure, it rejects, and the template is used. A change that lets more messages through can only add false accepts, so it needs:
   - the relevant evaluation re-run (`experiment2/record_eval.py`, `experiment2/name_eval.py`) with zero observed false accepts;
   - for Marathi language rules (for example `src/marathi_suffixes.txt`), sign-off from a native speaker, named in the PR.
3. **The regression gate must pass.** `python3 -m pytest tests` runs 13,149 labelled cases, and CI fails on any false accept or false reject.
   - Labels come from how the cases were built (`experiment2/build_regression.py`), **never from the checker's output**. Do not "fix" a failing case by changing its label to match the checker. Find out which one is wrong.
   - If the case really is mislabelled, fix the construction rule, rebuild, and explain it in the PR.
4. **Held-out data is used once.** DEV2 (buckets 3–4) is for development. TEST2 (buckets 5–7) is for one frozen final run per design: record the code hashes in a dated commit first. See `experiment2/SPLIT.md`.
5. **Frozen files stay frozen.** `experiment/frozen_as_run/` must keep matching `experiment/code_hashes.txt`. CI checks this, and `src/factcheck.py` must stay byte-identical to the frozen extractor.
6. **Every public claim goes in `CLAIMS.md`**, with evidence and a status (FINAL / DEV / FACT / UNTESTED). Write "0 observed in n (95% upper bound x%)", never "zero errors".
7. **Report what failed.** A missed target or a crashed run is reported, not hidden.

## Pull requests
- Describe what changed, what was measured, and what is *not* claimed.
- Include the evaluation output, or the relevant lines of it, if behaviour changed.
- AI-assisted contributions are welcome and must be disclosed (for example with a `Co-Authored-By` line).

## Reproducing
`scripts/reproduce_dev.sh` fetches the pinned DEV2 data, re-runs both dev evaluations and rebuilds the regression set, then checks that the rebuilt set is byte-identical to the committed one.
