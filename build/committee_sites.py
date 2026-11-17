#!/usr/bin/env python3
"""Committee websites, for harvesting committee letters (#23).

    python3 build/committee_sites.py          # -> data/committee-sites.csv

Reads ``unitedstates/congress-legislators``'s committee files from
``data/legislators/`` (committees-current.json, committees-historical.json,
from https://unitedstates.github.io/congress-legislators/; gitignored like the
member files). Writes one row per committee website: the majority site
(``url``) and, where a committee has one, the minority's (``minority_url``).

Only the current committees carry websites in that source (47 of 49, as of
17 November 2026); the historical file names committees and the Congresses
they sat in, with no address. Earlier Congresses' committee addresses come
from the chambers' own committee directories in the Wayback Machine, like
``directory_urls.py`` for members -- a later step, under the Wayback rule.

Decided by Robin, 17 November 2026 (#23): joint committees and commissions are
included (congressional groups); committee letters are credited to every
member who signed them, carry the committee, and appear in each Congress's
explorer with a committee filter, as caucus letters do. Stdlib only.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "legislators"
OUT = ROOT / "data" / "committee-sites.csv"
CHAMBER = {"house": "House", "senate": "Senate", "joint": "Joint"}


def main() -> None:
    current = json.loads((SRC / "committees-current.json").read_text(encoding="utf-8"))
    rows = []
    for c in current:
        for side, key in (("majority", "url"), ("minority", "minority_url")):
            url = (c.get(key) or "").strip()
            if url:
                rows.append({"chamber": CHAMBER.get(c.get("type"), c.get("type")),
                             "committee": c["name"], "thomas_id": c.get("thomas_id", ""),
                             "side": side, "url": url, "congresses": "119",
                             "source": "congress-legislators committees-current"})
    rows.sort(key=lambda r: (r["chamber"], r["committee"], r["side"]))
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    by = {}
    for r in rows:
        by[(r["chamber"], r["side"])] = by.get((r["chamber"], r["side"]), 0) + 1
    print(f"{len(rows)} committee sites -> {OUT}: " + ", ".join(f"{c} {s} {n}" for (c, s), n in sorted(by.items())))


if __name__ == "__main__":
    main()
