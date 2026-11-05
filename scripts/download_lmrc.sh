#!/usr/bin/env bash
# Download the LMRC 2021 training inputs (Amazon Last Mile Routing Research Challenge).
# Public HTTPS endpoint of the AWS Open Data bucket: no AWS account or CLI needed.
# Total size ~2.3 GB (travel_times.json alone is ~1.8 GB). Re-running resumes partial files.
#
# Usage (from the repository root):   bash scripts/download_lmrc.sh [target_dir]
set -euo pipefail

BASE="https://amazon-last-mile-challenges.s3.amazonaws.com/almrrc2021/almrrc2021-data-training/model_build_inputs"
DEST="${1:-data/raw/lmrc}"
FILES=(route_data.json actual_sequences.json invalid_sequence_scores.json package_data.json travel_times.json)

mkdir -p "$DEST"

remote_size() {
  curl -sfI "$BASE/$1" | tr -d '\r' | awk 'tolower($1)=="content-length:" {print $2}'
}

local_size() {
  if [[ -f "$1" ]]; then stat -c %s "$1"; else echo 0; fi
}

total=0
for f in "${FILES[@]}"; do
  s=$(remote_size "$f")
  total=$((total + s))
done
echo "Total to download: $((total / 1000000)) MB into $DEST"
avail_kb=$(df -Pk "$DEST" | awk 'NR==2 {print $4}')
if (( avail_kb * 1024 < total * 2 )); then
  echo "Not enough free disk space (need about 2x the download size)." >&2
  exit 1
fi

for f in "${FILES[@]}"; do
  want=$(remote_size "$f")
  have=$(local_size "$DEST/$f")
  if [[ "$have" == "$want" ]]; then
    echo "[skip] $f already complete ($((want / 1000000)) MB)"
    continue
  fi
  echo "[get ] $f ($((want / 1000000)) MB)"
  curl -f --retry 5 --retry-delay 5 -C - -o "$DEST/$f" "$BASE/$f"
  have=$(local_size "$DEST/$f")
  if [[ "$have" != "$want" ]]; then
    echo "Size mismatch for $f: got $have bytes, expected $want. Re-run to resume." >&2
    exit 1
  fi
done

echo "Done. Files in $DEST:"
ls -lh "$DEST"
