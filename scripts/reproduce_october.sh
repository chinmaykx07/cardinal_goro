#!/usr/bin/env bash
# Re-run the October 2026 experiment (buckets 8-9, already spent as a held-out test)
# from the pinned data, and check the output matches experiment/test_run.txt exactly.
# Takes about 10-15 minutes. Usage: scripts/reproduce_october.sh [workdir]
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
WORK="${1:-$REPO/../mahgrs-october}"
COMMIT=c96e88f731589e1284ecab60ff1a63d3b9c6bb82
[ -d "$WORK/.git" ] || git clone -q --filter=blob:none --no-checkout https://github.com/orgpedia/mahgrs "$WORK"
cd "$WORK"
git ls-tree -r "$COMMIT" GRs | awk '$4 ~ /\.mr\.txt$/ {print $3, $4}' > .all
python3 -I - <<'PY'
import hashlib, os
rows = [l.split(maxsplit=1) for l in open(".all")]
b = lambda p: int(hashlib.sha1(os.path.basename(p).encode()).hexdigest(), 16) % 10
t = [(o, p.strip()) for o, p in rows if b(p.strip()) in (8, 9)]
open(".t_oids", "w").write("\n".join(o for o, _ in t) + "\n")
open(".t_paths", "w").write("\n".join(p for _, p in t) + "\n")
print(f"buckets 8-9: {len(t)} files")
PY
split -l 1000 .t_oids .tchunk_
for f in .tchunk_*; do git fetch -q --no-tags --no-write-fetch-head origin $(cat "$f"); done
rm -f .tchunk_*
git checkout -q "$COMMIT" --pathspec-from-file=.t_paths
OUT="$(mktemp -d)"
cp "$REPO"/experiment/{run_eval.py,split.py,transforms.py,factcheck.py} "$OUT"/   # run in a scratch dir so committed results are not overwritten
cd "$OUT"
MAHGRS="$WORK/GRs" PER_FILE=8 python3 -I run_eval.py test 150000 20261030 0 > test_run.txt
diff -q test_run.txt "$REPO/experiment/test_run.txt" && echo "OK  October test_run.txt reproduced exactly"
