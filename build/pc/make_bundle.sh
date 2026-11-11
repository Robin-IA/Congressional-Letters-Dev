#!/bin/bash
# Build the zip that carries one range's harvest to a Windows PC.
#
#   build/pc/make_bundle.sh                 # 115-118, into ~/Desktop/pc-harvest-115-118
#   build/pc/make_bundle.sh 115-118 /some/dir
#
# The PC needs no clone. The zip holds run_pc.py, build/harvest.py,
# build/timing_report.py, the range's member list and a snapshot of every
# cache file for its sites, finished or not, so the PC skips what is done.
# Stop the Mac's run of the same range first, or both will fetch the same
# sites. See PC-HANDOFF.md.
set -eu
RANGE="${1:-115-118}"
OUT="${2:-$HOME/Desktop/pc-harvest-$RANGE}"
REPO="${REPO:-$(cd "$(dirname "$0")/../.." && pwd)}"
MEMBERS="$REPO/harvest/letters-$RANGE-members.json"
[ -f "$MEMBERS" ] || { echo "No $MEMBERS" >&2; exit 1; }

B="$OUT/bundle"
rm -rf "$B"
mkdir -p "$B/build" "$B/harvest/letters/cache"
cp "$REPO/build/harvest.py" "$REPO/build/timing_report.py" "$B/build/"
cp "$REPO/build/pc/run_pc.py" "$B/"
cp "$MEMBERS" "$B/harvest/"

python3 - "$MEMBERS" "$REPO/harvest/letters/cache" "$B/harvest/letters/cache" <<'PY'
import json, shutil, sys
from pathlib import Path
members, src, dst = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
n = 0
for m in json.load(open(members)):
    for name in (f"{m['host']}.json", f"{m['host']}.partial.json"):
        if (src / name).exists():
            shutil.copy2(src / name, dst / name)
            n += 1
print(f"{n} cache files copied")
PY

(cd "$B" && python3 -c "
import sys; sys.path.insert(0, '.'); import run_pc
print(len(run_pc.remaining()), 'sites to do')")
find "$B" -name __pycache__ -type d -prune -exec rm -rf {} +
rm -f "$OUT/pc-harvest-$RANGE.zip"
(cd "$B" && zip -qr "../pc-harvest-$RANGE.zip" .)
echo "Wrote $OUT/pc-harvest-$RANGE.zip"
