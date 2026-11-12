#!/bin/bash
# Publish the built explorers and home page to Internet Archive Canada, after
# publish_explorers.sh has published them to Robin-IA. Run by that script at
# its end, so auto_publish.sh keeps both in step; PUBLISH_IAC=0 skips it.
#
#   build/publish_iac.sh
#
# Internet Archive Canada holds the same sites under the same names, except the
# home page: internetarchivecanada/congressional-letters, the address the first
# explorer was published at, not Explorer-Letters. So two links change on the
# way across: each explorer's "All Congresses" goes to ../congressional-letters/
# and its README names its own address.
#
# Explorers: a commit made from main's tree with those two files rewritten,
# on top of the last IAC commit, so every push is a fast-forward and the IAC
# history is never rewritten. Built with a temporary index, because the
# explorer folders are publish_explorers.sh's working copies and a branch
# switch there would land its next commit on the wrong branch.
#
# Home page: a clone of congressional-letters kept beside the explorers.
# Its old links, from when it was the 119th explorer (?member=, 119th/,
# explorer.html), forward to the 119th explorer, so those stay.
#
# Never creates a repository: making one in the organization is Robin's call.
# Checks every remote before pushing, and that the remote ends at the commit
# just made. A failure is logged and the rest carry on.
set -u
ORG=internetarchivecanada
EXPLORERS=~/ia/explorers
HOME_CLONE=~/ia/explorers-iac/congressional-letters
HOME_REPO="https://github.com/$ORG/congressional-letters.git"
HOME_BRANCH=harvest-member-letters
LOG="$EXPLORERS/publish.log"
say() { echo "$(date '+%H:%M:%S')  IAC $*" | tee -a "$LOG"; }

publish_explorer() {   # $1 = repository name
  local name="$1" url="https://github.com/$ORG/$1.git"
  cd "$EXPLORERS/$name" || { say "$name: no folder"; return 1; }
  if ! gh repo view "$ORG/$name" >/dev/null 2>&1; then
    say "$name: no such repository on $ORG; not creating one"; return 1
  fi
  if git remote get-url iac >/dev/null 2>&1; then
    [ "$(git remote get-url iac)" = "$url" ] || { say "$name: remote iac is not $url; not pushing"; return 1; }
  else
    git remote add iac "$url"
  fi
  git fetch -q iac main || { say "$name: fetch failed"; return 1; }
  local base main idx html readme tree c
  base=$(git rev-parse iac/main); main=$(git rev-parse main)
  idx=$(mktemp)
  GIT_INDEX_FILE="$idx" git read-tree "$main"
  html=$(git show "$main:index.html" \
    | sed 's|class="crumb" href="\.\./Explorer-Letters/"|class="crumb" href="../congressional-letters/"|' \
    | git hash-object -w --stdin)
  readme=$(git show "$main:README.md" \
    | sed "s|https://robin-ia.github.io/$name/|https://$ORG.github.io/$name/|g" \
    | git hash-object -w --stdin)
  GIT_INDEX_FILE="$idx" git update-index --cacheinfo 100644,"$html",index.html \
    --cacheinfo 100644,"$readme",README.md
  tree=$(GIT_INDEX_FILE="$idx" git write-tree); rm -f "$idx"
  if ! git show "$tree:index.html" | grep -q 'href="../congressional-letters/"'; then
    say "$name: All Congresses link not found to rewrite; not pushing"; return 1
  fi
  if [ "$tree" = "$(git rev-parse "$base^{tree}")" ]; then
    say "$name: already current"; return 0
  fi
  c=$(git commit-tree "$tree" -p "$base" \
    -m "Internet Archive Canada copy of $(git log -1 --format=%s "$main") ($(git rev-parse --short "$main"))")
  git push -q iac "$c:refs/heads/main" 2>&1 | tail -2
  git update-ref refs/heads/iac-main "$c"
  if [ "$(git ls-remote iac refs/heads/main | cut -f1)" = "$c" ]; then
    say "$name: pushed $(git rev-parse --short "$c")"
  else
    say "$name: PUSH FAILED"; return 1
  fi
}

publish_home() {
  if [ ! -d "$HOME_CLONE/.git" ]; then
    mkdir -p "$(dirname "$HOME_CLONE")"
    git clone -q --depth 1 --filter=blob:none -b "$HOME_BRANCH" "$HOME_REPO" "$HOME_CLONE" \
      || { say "congressional-letters: clone failed"; return 1; }
  fi
  cd "$HOME_CLONE" || { say "congressional-letters: no clone"; return 1; }
  [ "$(git remote get-url origin)" = "$HOME_REPO" ] \
    || { say "congressional-letters: clone's origin is not $HOME_REPO; not pushing"; return 1; }
  git fetch -q --depth 1 origin "$HOME_BRANCH" || { say "congressional-letters: fetch failed"; return 1; }
  git reset -q --hard FETCH_HEAD
  # The home page's files, never the README or the forwarding pages this
  # address keeps from when it was the 119th explorer.
  rsync -a --delete --exclude .git --exclude README.md --exclude 119th --exclude explorer.html \
    "$EXPLORERS/Explorer-Letters/" ./
  python3 - <<'PY' || { say "congressional-letters: could not add the old-link forwarding; not pushing"; return 1; }
from pathlib import Path
p = Path("index.html"); s = p.read_text(encoding="utf-8")
fwd = """<head>
<script>
// This address used to be the 119th Congress explorer, and every view of it was
// a link with its state in the query string (?member=W000817, ?to=..., ?year=...).
// Those links are out in the world: send them to the 119th explorer, which reads
// the same parameters. The home page's own links use ?q= and ?term= only.
(function () {
  var p = new URLSearchParams(location.search);
  var old = ['member', 'to', 'year', 'view', 'chamber', 'party', 'as', 'sort'];
  if (old.some(function (k) { return p.has(k); })) {
    location.replace('../Explorer-Congressional-Letters-119/' + location.search + location.hash);
  }
})();
</script>"""
assert s.count("<head>") == 1
p.write_text(s.replace("<head>", fwd, 1), encoding="utf-8")
PY
  git add -A
  if git diff --cached --quiet; then say "congressional-letters: already current"; return 0; fi
  git -c user.name=Robin-IA commit -q -m "Home page: build of $(date '+%Y-%m-%d %H:%M')"
  git push -q origin "HEAD:$HOME_BRANCH" 2>&1 | tail -2
  if [ "$(git ls-remote origin "refs/heads/$HOME_BRANCH" | cut -f1)" = "$(git rev-parse HEAD)" ]; then
    say "congressional-letters: pushed $(git rev-parse --short HEAD)"
  else
    say "congressional-letters: PUSH FAILED"; return 1
  fi
}

say "=== publishing to $ORG ==="
for n in $(seq 106 119); do publish_explorer "Explorer-Congressional-Letters-$n"; done
publish_home
say "=== $ORG done ==="
