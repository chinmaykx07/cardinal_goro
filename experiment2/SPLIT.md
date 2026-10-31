# Fresh data split (declared 31 Oct 2026, before any file in it was opened)

## Why
The pre-registered October 2026 run (`experiment/`) used hash buckets 0–2 for design and 8–9 for its one final test. Re-using bucket 8–9 for new claims would no longer be a fair held-out test. Buckets 3–7, half of the corpus, were never read.

## Declaration
- Corpus: orgpedia/mahgrs, **commit `c96e88f731589e1284ecab60ff1a63d3b9c6bb82`** (main branch HEAD on 31 Oct 2026). Only `GRs/*/*.mr.txt` is used.
- Bucket = `sha1(file name) mod 10`, the same function as `experiment/split.py`.
- **DEV2 = buckets 3, 4.** Design, tuning and debugging. Results from DEV2 are labelled as dev results and never presented as final.
- **TEST2 = buckets 5, 6, 7.** Final numbers only. Each frozen design (code hashes recorded beforehand, in a dated commit) is run once. A crashed run may be repeated with identical hashes, and the crash is reported.
- Buckets 0–2 and 8–9 are not used for new claims.

## Statement
This file and `split2.py` were committed and pushed before any file in buckets 3–7 was opened in this work. The git history of this repository shows the order. The October 2026 harness read only buckets 0–2 and 8–9 (see `experiment/split.py`). Its earlier development sessions are not part of this repository's history, so this cannot be proved independently, but nothing in the code reads buckets 3–7.

## Note on the October run
The exact mahgrs commit used on 30 Oct 2026 was not recorded. The commit above is the HEAD one day later. If the corpus changed in between, the October sample may not be exactly reproducible. Everything from now on is pinned.
