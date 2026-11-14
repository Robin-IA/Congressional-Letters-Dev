#!/bin/bash
# Merge the PC's returns and republish the explorers, every so often, until stopped.
#
#   build/auto_publish.sh                 # every 15 minutes
#   EVERY=1800 MIN_NEW=500 MAX_AGE=3600 build/auto_publish.sh
#
# Each round:
#   1. fetches the PC's return branches from the dev remote, and merges any
#      that moved since the last round (merge_render.py --apply, which adds
#      only what the Mac lacks);
#   2. if anything was merged, or the Mac's own renderer has made MIN_NEW more
#      thumbnails since the last publish, or MAX_AGE seconds (2 hours) have
#      passed and any letter, text, OCR, thumbnail or vocabulary file changed
#      since the last publish, rebuilds every explorer
#      (build_congress.py --copy-thumbs), the Download data CSVs, the
#      vocabulary and the home page, and runs publish_explorers.sh.
#
# The vocabulary is rebuilt because its counts come from the explorers just
# built: new OCR can give a committee or caucus its first letter
# (committees.py, caucuses.py), and without this the letter is tagged but the
# term is missing from By topic until the next manual rebuild.
#
# Robin asked for this on 12 November 2026: share the explorers as complete as
# possible while rendering and OCR continue, accepting repeat uploads. GitHub
# Pages allows 10 builds an hour per repository; at most one publish a round
# keeps every repository well inside that.
#
# The 2-hour rebuild (Robin, 14 November 2026): the Mac's OCR and its PDF
# fetch add text all day, which changes topics, search and the pages'
# numbers, but neither triggers a merge or new thumbnails. Nothing changed,
# nothing is published: an idle pipeline makes no empty commits.
#
# Remembers which commit of each branch it merged in harvest/letters/
# auto-publish-state, so a restart does not merge twice (and a second merge
# would add nothing anyway). Logs to harvest/letters/auto-publish.log.
set -u
cd "$(dirname "$0")/.." || exit 1
EVERY="${EVERY:-900}"
MIN_NEW="${MIN_NEW:-300}"
MAX_AGE="${MAX_AGE:-7200}"
REMOTE="${REMOTE:-dev}"
# The PC's return branches, by name: a branch not listed here is never merged.
# PC_BRANCHES (space-separated) replaces the list without editing this file.
read -r -a BRANCHES <<< "${PC_BRANCHES:-pc-render-return-2 pc-render-return-3 pc-ocr-return-106-115 pc-ocr-return-116-119}"
STATE=harvest/letters/auto-publish-state
LOG=harvest/letters/auto-publish.log
# Touched as each publish starts: a file newer than this changed since then.
SINCE=harvest/letters/auto-publish-since
# What a rebuild reads. A change to any of them is worth a timed rebuild.
# Not what a rebuild writes (vocabulary/terms, relations and sources.csv,
# from build_vocabulary.py), or every rebuild would schedule the next.
INPUTS=(data/letter-text.jsonl data/letter-ocr.jsonl data/letters-parsed.jsonl
        data/letters-119-departed-parsed.jsonl data/address-holders.csv data/rosters
        harvest/letters vocabulary thumbs)
mkdir -p "$(dirname "$STATE")"; touch "$STATE"

say() { echo "$(date '+%Y-%m-%d %H:%M:%S')  $*" | tee -a "$LOG"; }
changed_since() {   # any input newer than the last publish (or no record of one)
  [ -f "$SINCE" ] || return 0
  [ -n "$(find "${INPUTS[@]}" -newer "$SINCE" \( -name '*.jsonl' -o -name '*.csv' -o -name '*.webp' \) \
          ! -name 'auto-publish*' ! -name 'fetch-pdfs-failures.jsonl' \
          ! -path 'vocabulary/terms.csv' ! -path 'vocabulary/relations.csv' \
          ! -path 'vocabulary/sources.csv' -print -quit 2>/dev/null)" ]
}
age() { [ -f "$SINCE" ] && echo $(( $(date +%s) - $(stat -f %m "$SINCE") )) || echo 999999; }
count_thumbs() { find thumbs -name '*.webp' | wc -l | tr -d ' '; }
last_of() { grep "^$1 " "$STATE" | tail -1 | cut -d' ' -f2; }
remember() { grep -v "^$1 " "$STATE" > "$STATE.tmp"; echo "$1 $2" >> "$STATE.tmp"; mv "$STATE.tmp" "$STATE"; }

say "=== auto publish: every ${EVERY}s; republish on a PC merge, ${MIN_NEW} new thumbnails, or every ${MAX_AGE}s if anything changed ==="
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
  why=""
  if [ "$merged" = 1 ]; then why="a PC merge"
  elif [ $((now - last)) -ge "$MIN_NEW" ]; then why="$((now - last)) new thumbnails"
  elif [ "$(age)" -ge "$MAX_AGE" ] && changed_since; then why="$(( $(age) / 60 )) minutes since the last publish, and the data changed"
  fi
  if [ -n "$why" ]; then
    touch "$SINCE"
    say "publishing ($why): $now thumbnails ($((now - last)) since the last publish)"
    if python3 build/build_congress.py 106-119 --copy-thumbs >>"$LOG" 2>&1 \
       && python3 build/export_csv.py >>"$LOG" 2>&1 \
       && python3 build/build_vocabulary.py >>"$LOG" 2>&1 \
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
