#!/usr/bin/env bash
# Reproduce every DEV result and the regression set from the pinned data.
# Fetches ONLY the DEV2 files (buckets 3-4). TEST2 (buckets 5-7) is never fetched.
# Usage: scripts/reproduce_dev.sh [workdir]      (needs git >= 2.29, python3, requirements.txt)
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
WORK="${1:-$REPO/../mahgrs-dev2}"
COMMIT=$(python3 -I -c "import sys; sys.path.insert(0,'$REPO/experiment2'); import split2; print(split2.DATA_COMMIT)")

if [ ! -d "$WORK/.git" ]; then
  git clone -q --filter=blob:none --no-checkout https://github.com/orgpedia/mahgrs "$WORK"
fi
cd "$WORK"
git fetch -q origin "$COMMIT" 2>/dev/null || true
git -c advice.detachedHead=false checkout -q "$COMMIT" -- 2>/dev/null || true
test "$(git rev-parse "$COMMIT^{commit}")" = "$COMMIT"

# DEV2 file list and blob ids, chosen by the same bucket rule as split2.py
git ls-tree -r "$COMMIT" GRs | awk '$4 ~ /\.mr\.txt$/ {print $3, $4}' > .all
python3 -I - "$REPO/experiment2" <<'PY'
import sys; sys.path.insert(0, sys.argv[1]); import split2
rows = [l.split(maxsplit=1) for l in open(".all")]
dev = [(o, p.strip()) for o, p in rows if split2.bucket(p.strip()) in split2.SPLITS["dev2"]]
open(".dev2_oids", "w").write("\n".join(o for o, _ in dev) + "\n")
open(".dev2_paths", "w").write("\n".join(p for _, p in dev) + "\n")
print(f"DEV2: {len(dev)} files")
PY
split -l 1000 .dev2_oids .chunk_
for f in .chunk_*; do git fetch -q --no-tags --no-write-fetch-head origin $(cat "$f"); done
rm -f .chunk_*
git checkout -q "$COMMIT" --pathspec-from-file=.dev2_paths

cd "$REPO/experiment2"
export MAHGRS="$WORK/GRs"
python3 -I record_eval.py dev2 20000 20261031 > /tmp/dev2_run.txt
python3 -I name_eval.py 10000 20261031 > /tmp/name_run.txt
cp "$REPO/tests/regression_cases.jsonl" /tmp/regression_committed.jsonl
python3 -I build_regression.py 500 300 7

status=0
diff -q /tmp/dev2_run.txt dev2_run.txt        && echo "OK  dev2_run.txt reproduced"   || { echo "DIFF dev2_run.txt"; status=1; }
diff -q /tmp/name_run.txt name_run.txt        && echo "OK  name_run.txt reproduced"   || { echo "DIFF name_run.txt"; status=1; }
cmp -s /tmp/regression_committed.jsonl "$REPO/tests/regression_cases.jsonl" \
  && echo "OK  regression_cases.jsonl rebuilt byte-identically" || { echo "DIFF regression_cases.jsonl"; status=1; }
exit $status
