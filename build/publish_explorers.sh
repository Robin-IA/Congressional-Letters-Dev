#!/bin/bash
# Publish the built explorers and the home page to GitHub Pages under Robin-IA.
#
#   python3 build/build_congress.py 106-119 --copy-thumbs
#   python3 build/export_csv.py
#   python3 build/build_hub.py
#   build/publish_explorers.sh
#
# Creates a repository only if it does not exist (creating one is Robin's call:
# run this only when asked). Refuses to push to a name that forwards to another
# repository, and checks the remote main is the commit just made.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"   # before the cd below, for publish_iac.sh
cd ~/ia/explorers || exit 1
OWNER=Robin-IA
LOG=~/ia/explorers/publish.log
say() { echo "$(date '+%H:%M:%S')  $*" | tee -a "$LOG"; }

publish() {   # $1 = folder name, $2 = description
  local name="$1" desc="$2"
  cd ~/ia/explorers/"$name" || { say "$name: no folder"; return 1; }
  touch .nojekyll
  if [ ! -f README.md ]; then
    cat > README.md <<EOF
# $name

$desc

Built output, published with GitHub Pages at <https://robin-ia.github.io/$name/>.
Never edited by hand: it is built from
[Congressional-Letters-Dev](https://github.com/Robin-IA/Congressional-Letters-Dev)
(\`build/build_congress.py\`, \`build/export_csv.py\`, \`build/build_hub.py\`) and
pushed from there. The letters themselves are not stored here: every one opens
from the Wayback Machine.
EOF
  fi
  if [ ! -d .git ]; then
    git init -q -b main
    git config core.autocrlf false
  fi
  git add -A
  git commit -q -m "Build of $(date '+%Y-%m-%d %H:%M')" || say "$name: nothing new to commit"
  if ! gh repo view "$OWNER/$name" >/dev/null 2>&1; then
    # --homepage puts the Pages address in the repository's About panel, so
    # the live site is one click from the code.
    gh repo create "$OWNER/$name" --public --description "$desc" \
      --homepage "https://robin-ia.github.io/$name/" >/dev/null || { say "$name: create failed"; return 1; }
    say "$name: repository created"
  fi
  local real; real=$(gh api "repos/$OWNER/$name" --jq .full_name 2>/dev/null)
  if [ "$real" != "$OWNER/$name" ]; then say "$name: resolves to $real, not $OWNER/$name; not pushing"; return 1; fi
  git remote get-url origin >/dev/null 2>&1 || git remote add origin "https://github.com/$OWNER/$name.git"
  git push -q -u origin main 2>&1 | tail -2 || true
  # The remote's main must now BE this commit. A push to a forwarded name
  # (a moved repository) is refused, and "main exists" would not notice.
  if [ "$(git ls-remote origin refs/heads/main | cut -f1)" = "$(git rev-parse HEAD)" ]; then
    say "$name: pushed ($(du -sh . | cut -f1))"
  else
    say "$name: PUSH FAILED"; return 1
  fi
  gh api -X POST "repos/$OWNER/$name/pages" -f "source[branch]=main" -f "source[path]=/" >/dev/null 2>&1 \
    && say "$name: Pages turned on" \
    || say "$name: Pages already on, or could not be turned on (check)"
}

for n in $(seq 106 119); do
  ord="${n}th"
  # The home page is the starting point, so every explorer's description names it.
  publish "Explorer-Congressional-Letters-$n" \
    "Letters from Congress: letters members of the $ord Congress published on their own websites, preserved by the Wayback Machine. Start at the Letters from Congress home page, all letters from every Congress: https://robin-ia.github.io/Explorer-Letters/"
done
publish "Explorer-Letters" \
  "Letters from Congress: start here. All letters from every Congress, 106th to 119th, that members published on their own websites, preserved by the Wayback Machine. Search across all of them, then open any Congress's explorer."
say "=== all done ==="

# The same build to Internet Archive Canada, so the two never drift apart:
# auto_publish.sh calls this script every round and gets both. PUBLISH_IAC=0
# publishes to Robin-IA only.
if [ "${PUBLISH_IAC:-1}" != 0 ]; then
  bash "$HERE/publish_iac.sh"
fi
