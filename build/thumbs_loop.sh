#!/bin/bash
# Render thumbnails behind a running harvest, a cycle at a time.
#
#   build/thumbs_loop.sh                        # 115-118, 106-114, then paths
#   build/thumbs_loop.sh 115-118 106-114 paths  # the same, said explicitly
#   BATCH=200 build/thumbs_loop.sh        # renders per cycle (default 400)
#
# Each cycle turns every site the harvest has finished so far into a letter
# list -- export from the cache, then parse_urls.py, both local and quick --
# and then renders up to BATCH thumbnails from it. thumbs.py names a thumbnail
# by the PDF's digest and skips any it already has, so a cycle only ever
# renders letters that are new since the last one.
#
# WHY IT IS NOT PART OF THE HARVEST. The harvest reads the index: one request
# lists hundreds of a site's URLs. A thumbnail downloads the PDF itself, one
# request per letter. And which URLs are letters at all is only decided by the
# parse, which drops announcement pages, download wrappers and press releases.
# Both share one Wayback budget, so combining them would add nothing.
#
# Ranges are done in the order given: a later range gets a cycle only once the
# earlier ones have nothing left to render. The lists are written to
# harvest/letters/loop/, never over the harvest's own letters-raw-<range>.jsonl,
# which the running harvest rewrites at the end of every pass.
#
# Stops by itself once nothing is left to render and no harvest is running.
# One renderer at a time: two would both append to data/letter-text.jsonl.
set -u
cd "$(dirname "$0")/.." || exit 1

RANGES=("$@")
[ ${#RANGES[@]} -eq 0 ] && RANGES=(115-118 106-114 paths)
BATCH="${BATCH:-400}"
# The renderer needs pypdfium2, pillow and pypdf; the harvest needs nothing.
PY="${PY:-.venv/bin/python}"
PAUSE="${PAUSE:-300}"
DIR=harvest/letters/loop
LOG=harvest/letters/thumbs-loop.log
mkdir -p "$DIR"
"$PY" -c "import PIL, pypdf, pypdfium2" 2>/dev/null || {
    echo "$PY cannot render (needs requirements.txt); set PY=..." >&2; exit 1; }

say() { echo "$(date '+%Y-%m-%d %H:%M:%S')  $*" | tee -a "$LOG"; }

refresh() {   # $1 = range; writes $DIR/letters-parsed-$1.jsonl
    local r="$1"
    # A list with no member file is not a CDX range: the house.gov/<name>/
    # paths (harvest_paths.py, then paths_letters.py and parse_urls.py) are
    # one finished list, harvest/letters/letters-parsed-paths.jsonl. Render
    # from it as it stands; it changes only when the path harvest is re-run.
    if [ ! -f "harvest/letters-$r-members.json" ]; then
        [ -f "harvest/letters/letters-parsed-$r.jsonl" ] || return 1
        cp "harvest/letters/letters-parsed-$r.jsonl" "$DIR/letters-parsed-$r.jsonl"
        return 0
    fi
    python3 build/harvest.py --export-only --no-timing \
        --members-in "harvest/letters-$r-members.json" \
        --members-out "$DIR/members-$r.json" \
        --out "$DIR/letters-raw-$r.jsonl" \
        --cache harvest/letters/cache >>"$LOG" 2>&1 &&
    python3 build/parse_urls.py --raw "$DIR/letters-raw-$r.jsonl" \
        --members "$DIR/members-$r.json" \
        --out "$DIR/letters-parsed-$r.jsonl" >>"$LOG" 2>&1
}

say "=== thumbs loop: ${RANGES[*]}, $BATCH per cycle ==="
while true; do
    rendered_any=0
    for r in "${RANGES[@]}"; do
        if ! refresh "$r"; then
            say "$r: could not build the letter list; see $LOG"
            continue
        fi
        before=$(find thumbs -name '*.webp' | wc -l)
        out=$(caffeinate -i "$PY" build/thumbs.py \
                --parsed "$DIR/letters-parsed-$r.jsonl" --thumbs thumbs \
                --workers 1 --max "$BATCH" 2>&1 | tee -a "$LOG")
        left=$(echo "$out" | sed -n 's/.*, \([0-9,]*\) still to render.*/\1/p' \
                | head -1 | tr -d ,)
        made=$(( $(find thumbs -name '*.webp' | wc -l) - before ))
        say "$r: $made rendered; ${left:-?} were still to render at the start"
        # Stay on this range while it has work AND the cycle made progress.
        # A cycle that renders nothing means what is left keeps failing for
        # now (Wayback refusing, not the PDF), so let the next range have a go.
        if [ "${left:-1}" != "0" ] && [ "$made" -gt 0 ]; then
            rendered_any=1
            break    # stay on this range until it is empty
        fi
    done
    if [ "$rendered_any" = 0 ] && ! pgrep -f "build/harvest.py" >/dev/null; then
        say "=== nothing left to render and no harvest running: done ==="
        exit 0
    fi
    [ "$rendered_any" = 0 ] && { say "caught up; waiting ${PAUSE}s"; sleep "$PAUSE"; }
done
