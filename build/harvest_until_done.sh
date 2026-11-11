#!/bin/bash
# Run the letter harvest for one range until every site is done, restarting
# it by itself after a crash, a dropped connection or the Mac waking up.
#
#   build/harvest_until_done.sh 115-118
#
# Start it from a terminal (not from a Claude session) and leave the window
# open. It is safe to stop with Ctrl-C and start again at any time: harvest.py
# skips every site already in the cache and retries only the ones that failed
# or were never reached.
#
# Each pass:
#   1. waits until the Wayback Machine's CDX API answers;
#   2. runs harvest.py under caffeinate, so the Mac does not sleep mid-run;
#   3. counts the sites still to do. None left: parse the letters and stop.
#      Some left: pause, then go again.
# It gives up after 3 passes in a row that finish nothing, because those
# sites are failing for a reason a retry will not fix. They are listed at
# the end, so they can get an issue each.
#
# Two ranges can run side by side, in two terminals (tried 11 November; the
# project's earlier rule was one Wayback job at a time). Each range has its
# own log and touches only its own sites. WORKERS=1 halves one job's load.
# If both start backing off, stop one.

set -u
RANGE="${1:-115-118}"
cd "$(dirname "$0")/.." || exit 1

MEMBERS_IN="harvest/letters-${RANGE}-members.json"
MEMBERS_OUT="harvest/letters/members-${RANGE}.json"
RAW="harvest/letters/letters-raw-${RANGE}.jsonl"
PARSED="harvest/letters/letters-parsed-${RANGE}.jsonl"
CACHE="harvest/letters/cache"
LOG="harvest/letters/harvest-${RANGE}.log"
PROBE="https://web.archive.org/cdx/search/cdx?url=house.gov&limit=1"

PAUSE_BETWEEN_PASSES=300   # seconds
MAX_STUCK_PASSES=3

[ -f "$MEMBERS_IN" ] || { echo "No $MEMBERS_IN; nothing to harvest." >&2; exit 1; }

say() { echo "$(date '+%Y-%m-%d %H:%M:%S')  $*" | tee -a "$LOG"; }

# Sites with no good cache entry, by the same rule harvest.py uses.
remaining() {
  python3 - "$MEMBERS_IN" "$CACHE" <<'PY'
import json, sys
sys.path.insert(0, "build")
from pathlib import Path
import harvest
members = json.load(open(sys.argv[1]))
cache = Path(sys.argv[2])
left = []
for m in members:
    c = harvest.read_cache(cache / f"{m['host']}.json")
    if c is None or "error" in c or c.get("method") != harvest.CACHE_METHOD:
        left.append(m["host"])
print(len(left))
for h in left:
    print(h, file=sys.stderr)
PY
}

wait_for_wayback() {
  local waited=0
  until curl -fsS -o /dev/null -m 30 "$PROBE"; do
    if [ $waited -eq 0 ]; then say "Wayback not answering (wifi?). Waiting."; fi
    sleep 60; waited=$((waited + 60))
  done
  if [ $waited -gt 0 ]; then say "Wayback answering again after ${waited}s."; fi
}

pass=0
stuck=0
before=$(remaining 2>/dev/null)
say "=== harvest $RANGE: $before sites to do ==="

while :; do
  if [ "$before" -eq 0 ]; then break; fi
  pass=$((pass + 1))
  wait_for_wayback
  say "--- pass $pass: $before to do ---"
  mark=$(wc -l < "$LOG")
  caffeinate -i python3 build/harvest.py \
    --members-in "$MEMBERS_IN" --members-out "$MEMBERS_OUT" \
    --out "$RAW" --cache "$CACHE" --workers "${WORKERS:-2}" >>"$LOG" 2>&1
  status=$?
  after=$(remaining 2>/dev/null)
  say "pass $pass ended (exit $status): $((before - after)) sites finished, $after left"

  # Refused rather than unlucky? If more than a quarter of this pass's sites
  # failed, the Wayback Machine is likely pushing back (another job running
  # alongside, or plain throttling). Wait half an hour instead of five minutes.
  tried=$(tail -n +"$((mark + 1))" "$LOG" | grep -cE '^\s*\[[0-9]+/[0-9]+\]')
  failed=$(tail -n +"$((mark + 1))" "$LOG" | grep -cE '^\s*\[[0-9]+/[0-9]+\].*FAILED')
  pause=$PAUSE_BETWEEN_PASSES
  if [ "$tried" -gt 0 ] && [ $((failed * 4)) -gt "$tried" ]; then
    pause=1800
    say "$failed of $tried failed this pass: backing off for 30 minutes"
  fi

  if [ "$after" -ge "$before" ]; then
    stuck=$((stuck + 1))
    if [ $stuck -ge $MAX_STUCK_PASSES ]; then
      say "Stopping: $MAX_STUCK_PASSES passes in a row finished nothing. Still failing:"
      remaining 2>&1 >/dev/null | sed 's/^/    /' | tee -a "$LOG"
      break
    fi
  else
    stuck=0
  fi
  before=$after
  [ "$after" -eq 0 ] && break
  sleep "$pause"
done

# Reduce the raw rows to letters. No network; seconds, not hours.
if [ -s "$RAW" ]; then
  say "Parsing letters into $PARSED"
  python3 build/parse_urls.py --raw "$RAW" --members "$MEMBERS_OUT" \
    --out "$PARSED" >>"$LOG" 2>&1 && say "Parsed: $(wc -l < "$PARSED" | tr -d ' ') letters"
fi
say "=== harvest $RANGE finished ==="
