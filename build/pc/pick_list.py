#!/usr/bin/env python3
"""The PC's next reading batch: one digest per line, ready to read.

    python3 build/pc/pick_list.py --phase ocr  --size 500 > batch.txt
    python3 build/pc/pick_list.py --phase text --size 500 > batch.txt

Run it from the dev repository, on an up-to-date harvest-member-letters, after
pulling letters-from-congress-OCR (PC-READING.md, step A).

--phase ocr   the 116th-119th scans whose text is OCR (PC-READING 4a, item 1)
--phase text  the 116th-119th text-layer letters, newest Congress first (item 2)

A digest is left out when it is already:
- read (vocabulary/letters-reviewed.csv),
- held (letters-vocabulary-needs/letters.csv),
- discarded (letters-discarded/letters.csv),
- in an open PR against harvest-member-letters (fetched with git), so a batch
  that has not been merged yet is never picked twice.

The counts go to stderr; stdout is only the digests.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILES = ("vocabulary/letters-reviewed.csv",
         "letters-vocabulary-needs/letters.csv",
         "letters-discarded/letters.csv")


def digests(text: str) -> set[str]:
    return {r["digest"] for r in csv.DictReader(text.splitlines()) if r.get("digest")}


def taken_here() -> set[str]:
    out: set[str] = set()
    for f in FILES:
        p = ROOT / f
        if p.exists():
            out |= digests(p.read_text(encoding="utf-8"))
    return out


# Named, not taken from a remote: on the PC `origin` is internetarchivecanada/
# letters-from-congress, whose PR numbers are unrelated, and the dev repository
# is the remote `dev` (#1341).
REPO = "Robin-IA/Congressional-Letters-Dev"
REPO_URL = f"https://github.com/{REPO}.git"


def taken_in_open_prs() -> tuple[set[str], list[int]]:
    """Digests in the CSVs of every open PR against harvest-member-letters."""
    try:
        listing = subprocess.run(
            ["gh", "pr", "list", "--repo", REPO, "--base", "harvest-member-letters", "--state", "open",
             "--json", "number,headRefName", "--limit", "100"],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        sys.exit(f"could not list open PRs ({exc}); is gh signed in as Robin-IA?")
    out: set[str] = set()
    numbers = []
    for pr in json.loads(listing):
        ref = f"refs/pick/{pr['number']}"
        # A PR that cannot be fetched stops the run: skipping it silently is
        # what lets two batches be handed the same letters (#1341).
        got = subprocess.run(["git", "fetch", "-q", REPO_URL, f"+pull/{pr['number']}/head:{ref}"],
                             cwd=ROOT, capture_output=True, text=True,
                             encoding="utf-8", errors="replace")
        if got.returncode != 0:
            sys.exit(f"could not fetch PR #{pr['number']} from {REPO}: {got.stderr.strip()}")
        numbers.append(pr["number"])
        for f in FILES:
            # encoding="utf-8": the CSVs hold accented names, and text=True
            # alone decodes with the locale encoding, which is cp1252 on
            # Windows and stops the run on the first such name.
            shown = subprocess.run(["git", "show", f"{ref}:{f}"], cwd=ROOT,
                                   capture_output=True, text=True, encoding="utf-8")
            if shown.returncode == 0:
                out |= digests(shown.stdout)
    return out, numbers


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--phase", choices=("ocr", "text"), required=True)
    ap.add_argument("--size", type=int, default=500)
    ap.add_argument("--ocr-repo", type=Path, default=ROOT.parent / "letters-from-congress-OCR")
    args = ap.parse_args()

    progress = args.ocr_repo / "progress.csv"
    if not progress.exists():
        sys.exit(f"no {progress}; clone or pull letters-from-congress-OCR first")
    taken = taken_here()
    in_prs, prs = taken_in_open_prs()
    taken |= in_prs

    picks = []
    with progress.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            first = min(int(c) for c in r["congresses"].replace(";", " ").split() if c.isdigit())
            if first < 116 or r["text"] != "True" or r["reviewed"] != "False":
                continue
            if (r["ocr"] == "True") != (args.phase == "ocr"):
                continue
            if r["digest"] in taken:
                continue
            picks.append((-first, r["digest"]))
    picks.sort()  # newest Congress first; digest order within one
    left = len(picks)
    for _, d in picks[:args.size]:
        print(d)
    print(f"{args.phase}: {left:,} left to read; picked {min(left, args.size):,}. "
          f"Skipped {len(taken):,} already read, held, discarded or in open PRs "
          f"({', '.join(f'#{n}' for n in prs) or 'none open'}).", file=sys.stderr)


if __name__ == "__main__":
    main()
