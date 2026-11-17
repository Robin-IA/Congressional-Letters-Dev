#!/bin/bash
# resolve_append.sh N -- merge the base into PR N's branch, keeping both sides of
# conflicts that are only rows appended to CSVs; test, push, then fold.sh N.
set -u
R=Robin-IA/Congressional-Letters-Dev; N=$1
cd ~/explorer-checks/Congressional-Letters-Dev || exit 1
B=$(gh pr view "$N" -R $R --json headRefName -q .headRefName) || exit 1
git fetch -q dev && git checkout -q -B "$B" "dev/$B" || exit 1
git merge -q dev/harvest-member-letters >/dev/null 2>&1
for f in $(git diff --name-only --diff-filter=U); do
  case "$f" in *.csv) ;; *) echo "#$N: conflict in $f is not a CSV -- stopping"; git merge --abort; exit 2;; esac
  python3 - "$f" <<'EOF' || { git merge --abort; exit 2; }
import sys, re
p = sys.argv[1]; t = open(p).read()
t2 = re.sub(r"<<<<<<< [^\n]*\n(.*?)=======\n(.*?)>>>>>>> [^\n]*\n", lambda m: m.group(1) + m.group(2), t, flags=re.S)
if "<<<<<<<" in t2 or ">>>>>>>" in t2: sys.exit("unresolved markers in " + p)
open(p, "w").write(t2)
EOF
  git add "$f"
done
for f in vocabulary/letter-titles.csv vocabulary/letter-topics.csv vocabulary/letters-reviewed.csv vocabulary/letter-dates.csv; do
  d=$(cut -d, -f1 "$f" | sort | uniq -d | wc -l | tr -d ' ')
  [ "$d" = 0 ] || { echo "#$N: $d duplicate digests in $f -- stopping"; git merge --abort; exit 3; }
done
python3 -m unittest discover -s tests 2>&1 | grep -q FAILED && { echo "#$N: tests fail after resolving"; git merge --abort; exit 4; }
git commit -qm "Merge harvest-member-letters: keep both sets of appended rows

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && git push -q dev "$B" && exec "$(dirname "$0")/fold.sh" "$N"
