#!/bin/bash
# Merge the PC's returns and republish the explorers, every so often, until stopped.
#
#   build/auto_publish.sh                 # every 15 minutes
#   EVERY=1800 MIN_NEW=500 build/auto_publish.sh
#
# Each round:
#   1. fetches the PC's return branches from the dev remote, and merges any
#      that moved since the last round (merge_render.py --apply, which adds
#      only what the Mac lacks);
#   2. if anything was merged, or the Mac's own renderer has made MIN_NEW more
#      thumbnails since the last publish, rebuilds every explorer
#      (build_congress.py --copy-thumbs), the Download data CSVs and the home
#      page, and runs publish_explorers.sh.
#
# Robin asked for this on 12 November 2026: share the explorers as complete as
# possible while rendering and OCR continue, accepting repeat uploads. GitHub
# Pages allows 10 builds an hour per repository; at most one publish a round
# keeps every repository well inside that.
#
# Remembers which commit of each branch it merged in harvest/letters/
# auto-publish-state, so a restart does not merge twice (and a second merge
# would add nothing anyway). Logs to harvest/letters/auto-publish.log.
set -u
cd "$(dirname "$0")/.." || exit 1
EVERY="${EVERY:-900}"
MIN_NEW="${MIN_NEW:-300}"
REMOTE="${REMOTE:-dev}"
BRANCHES=(pc-render-return-2 pc-render-return-3 pc-ocr-return-106-115)
STATE=harvest/letters/auto-publish-state
LOG=harvest/letters/auto-publish.log
mkdir -p "$(dirname "$STATE")"; touch "$STATE"

say() { echo "$(date '+%Y-%m-%d %H:%M:%S')  $*" | tee -a "$LOG"; }
count_thumbs() { find thumbs -name '*.webp' | wc -l | tr -d ' '; }
last_of() { grep "^$1 " "$STATE" | tail -1 | cut -d' ' -f2; }
remember() { grep -v "^$1 " "$STATE" > "$STATE.tmp"; echo "$1 $2" >> "$STATE.tmp"; mv "$STATE.tmp" "$STATE"; }

say "=== auto publish: every ${EVERY}s; republish on a PC merge or ${MIN_NEW} new thumbnails ==="
while true; do
  merged=0
  git fetch -q "$REMOTE" 2>>"$LOG" || say "fetch failed; trying again next round"
  for b in "${BRANCHES[@]}"; do
    sha=$(git rev-parse -q --verify "$REMOTE/$b" 2>/dev/null) || continue
    [ "$sha" = "$(last_of "$b")" ] && continue
    tmp=$(mktemp -d)
    if git archive "$REMOTE/$b" | tar -x -C "$tmp" \
       && python3 build/pc/merge_render.py "$tmp" --apply >>"$LOG" 2>&1; then
      remember "$b" "$sha"; merged=1
      say "$b: merged ${sha:0:9}"
    else
      say "$b: merge FAILED for ${sha:0:9}; see $LOG"
    fi
    rm -rf "$tmp"
  done

  now=$(count_thumbs)
  last=$(last_of thumbs-at-publish); last=${last:-0}
  if [ "$merged" = 1 ] || [ $((now - last)) -ge "$MIN_NEW" ]; then
    say "publishing: $now thumbnails ($((now - last)) since the last publish)"
    if python3 build/build_congress.py 106-119 --copy-thumbs >>"$LOG" 2>&1 \
       && python3 build/export_csv.py >>"$LOG" 2>&1 \
       && python3 build/build_hub.py >>"$LOG" 2>&1 \
       && bash build/publish_explorers.sh >>"$LOG" 2>&1; then
      remember thumbs-at-publish "$now"
      failed=$(grep -c "PUSH FAILED\|not pushing" <(tail -40 "$LOG"))
      say "published$( [ "$failed" -gt 0 ] && echo "; $failed push problem(s), see the log")"
    else
      say "publish FAILED; see $LOG"
    fi
  fi
  sleep "$EVERY"
done
