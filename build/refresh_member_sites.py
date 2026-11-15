#!/usr/bin/env python3
"""Refresh the ``in_explorer`` column of data/member-sites.tsv.

``chamber_rosters.py`` sets ``in_explorer`` once, when it scrapes the archived
House and Senate directories: ``yes`` when our roster (data/members.json)
already knows the host. Sites harvested later -- the backfill, the
``house.gov/<name>`` paths harvest -- were never marked, so by 2026-11-15
1,213 rows said ``no`` while 842 of those sites had published letters.

This rewrites only that column, with no directory scraping: a site is ``yes``
when the roster knows it OR the published explorers hold a letter posted on
it (payload column 0, keyed with ``chamber_rosters.member_key``). Everything
else in the file is left as it is. ``backfill_roster.py`` reads ``no`` as its
queue, so after a refresh the queue is the sites with nothing published.

    python build/refresh_member_sites.py [--sites data/member-sites.tsv]
        [--roster data/members.json] [--payloads GLOB]
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chamber_rosters import member_key, norm  # noqa: E402

PAYLOADS = str(Path.home() / "ia/explorers/Explorer-Congressional-Letters-*/payload/member/*.json")


def published_sites(pattern: str) -> set[str]:
    """Every member site that has at least one published letter."""
    sites = set()
    for path in glob.glob(pattern):
        for row in json.loads(Path(path).read_text(encoding="utf-8")):
            key = member_key(row[0])
            if key:
                sites.add(key)
    return sites


def refresh(lines: list[str], known: set[str]) -> tuple[list[str], int]:
    """Rewrite the in_explorer column of the TSV's lines; return them and the count changed."""
    header = lines[0].rstrip("\n").split("\t")
    col, host_col = header.index("in_explorer"), header.index("host")
    out, changed = [lines[0]], 0
    for line in lines[1:]:
        cells = line.rstrip("\n").split("\t")
        value = "yes" if norm(cells[host_col]) in known else "no"
        changed += cells[col] != value
        cells[col] = value
        out.append("\t".join(cells) + "\n")
    return out, changed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sites", type=Path, default=Path("data/member-sites.tsv"))
    ap.add_argument("--roster", type=Path, default=Path("data/members.json"))
    ap.add_argument("--payloads", default=PAYLOADS,
                    help="glob of published member payloads (default: %(default)s)")
    args = ap.parse_args()

    roster = {norm(m["host"]) for m in json.loads(args.roster.read_text(encoding="utf-8"))
              if m.get("host")}
    published = published_sites(args.payloads)
    if not published:
        print("no published payloads matched %s -- nothing changed" % args.payloads)
        return 1
    lines = args.sites.read_text(encoding="utf-8").splitlines(keepends=True)
    out, changed = refresh(lines, roster | published)
    with args.sites.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("".join(out))
    yes = sum(1 for line in out[1:] if line.rstrip("\n").split("\t")[-1] == "yes")
    print("%d sites: %d in the explorer, %d not; %d rows changed"
          % (len(out) - 1, yes, len(out) - 1 - yes, changed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
