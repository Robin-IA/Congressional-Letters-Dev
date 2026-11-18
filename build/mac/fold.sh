#!/bin/bash
# fold.sh N -- test-merge PR N onto the base, run the tests and the holder
# check, merge it, and sync its files into the pipeline. One line out.
# Stops (no merge) on a conflict, a failing test, a lost holder, or a PR that
# touches code (build/, app.js, tests/ other than data) -- those need a read.
set -u
R=Robin-IA/Congressional-Letters-Dev
N=$1
DEV=~/explorer-checks/Congressional-Letters-Dev
PIPE=~/ia/congressional-member-letters
cd "$DEV" || exit 1
git fetch -q dev
B=$(gh pr view "$N" -R $R --json headRefName -q .headRefName) || { echo "#$N: not found"; exit 1; }
FILES=$(gh pr view "$N" -R $R --json files -q '.files[].path')
CODE=$(echo "$FILES" | grep -E '^(build/|app\.js|119th/|tests/)' | tr '\n' ' ')
git checkout -q -B "t-$B" dev/harvest-member-letters
git merge -q --no-edit "dev/$B" >/dev/null 2>&1 || { git merge --abort; echo "#$N: CONFLICT ($(echo $FILES | tr '\n' ' '))"; exit 2; }
T=$(python3 -m unittest discover -s tests 2>&1 | grep -E "^Ran|FAILED" | tr '\n' ' ')
echo "$T" | grep -q FAILED && { echo "#$N: TESTS FAIL: $T"; exit 3; }
H=$(cd "$PIPE" && .venv/bin/python - "$DEV/vocabulary/letter-dates.csv" <<'EOF'
import sys, collections
from pathlib import Path
sys.path.insert(0, "build")
import build_congress as bc, address_holders as ah, letter_text as lt
lt.DATES = Path(sys.argv[1]); hand = lt.dates_by_hand(); idx = ah.index(ah.load()); bad = 0
for rec in bc.all_letters():
    d = rec.get("digest")
    # A hand-read non-PDF letter (data/letters-nonpdf.jsonl, #1330) is credited
    # to the author read from it, checked against the roster at build time.
    if d in hand and not rec.get("format"):
        a = ah.place(idx, rec["url"], hand[d][0], ah._iso(rec.get("first_seen") or ""))
        # A caucus copy is published under its chair when the caucus is named
        # (address_holders.CAUCUSES); only an unnamed caucus host has no holder.
        bad += a.attribution == "none" or (a.attribution in ah.UNPUBLISHED
                                           and not ah.caucus_name(rec["url"]))
print(f"{len(hand)} dates, {bad} without a holder")
EOF
)
echo "$H" | grep -q ", 0 without" || { echo "#$N: HOLDER CHECK: $H"; exit 4; }
if [ -n "$CODE" ]; then echo "#$N: touches code ($CODE) -- tests pass, $H; needs a read before merging"; exit 5; fi
gh pr merge "$N" -R $R --merge >/dev/null || { echo "#$N: merge refused"; exit 6; }
cd "$PIPE" && git fetch -q dev && git checkout dev/harvest-member-letters -- $FILES && git reset -q
for f in $FILES; do git show "dev/harvest-member-letters:$f" | cmp -s - "$f" || { echo "#$N: merged, but $f did not sync"; exit 7; }; done
echo "#$N merged + synced: $(echo "$FILES" | wc -l | tr -d ' ') files; ${T% }; $H"
