# Changelog
All notable changes. Results quoted here are listed in `CLAIMS.md` with their status.

## Unreleased
- Due-diligence pass: October 2026 experiment re-run at the pinned commit and reproduced byte for byte; third-party notice for the mahgrs data, an AI-assistance disclosure, pinned dependencies, a reproduce script with a CI job that rebuilds every DEV result byte-identically, CONTRIBUTING rules, and a CITATION file.

## 31 Oct 2026
- **#16**: Fail-closed name and place check, which fixes a false accept in the old per-part check. Adds the regression gate (13,149 cases; CI fails on any false accept or false reject) and `CLAIMS.md`. DEV results only.
- **#15**: Fresh data split declared before use (DEV2 = buckets 3–4, TEST2 = 5–7), data commit pinned. Dev measurement of the product's record-based check.
- **#1**: The product uses the measured extractor (byte-identical, enforced in CI). Adds the roadmap and CI.
- Initial public release: the October 2026 pre-specified experiment (150,000 lines), frozen code with hashes, the prototype and tests.
