#!/usr/bin/env python3
"""Turn the path harvest into a letter list the explorers read.

    python3 build/paths_letters.py
    python3 build/parse_urls.py --raw harvest/letters/letters-raw-paths.jsonl \\
        --members harvest/letters/members-paths.json \\
        --out harvest/letters/letters-parsed-paths.jsonl

``harvest_paths.py`` writes ``data/letters-paths.jsonl``: the letters found
under ``house.gov/<name>/``, where most representatives of the 2000s lived
instead of on a host of their own. It credits a path only by matching its name
to a later hostname (``house.gov/aderholt`` to ``aderholt.house.gov``), and
most of those members never had one: on 12 November 2026 that credited 138 of
1,616 letters.

The rosters do better, because they say which address each member had. The
106th-112th give ``www.house.gov/<name>/`` as the member's website at the
time, and ``address_holders.py`` already reads those, so a path letter goes to
whoever held the path when the letter was posted, the same rule as every other
letter. This writes the path letters in the shape ``harvest.py`` exports, with
that member's bioguide, so ``parse_urls.py`` can name the member and
``build_congress.py`` picks the parsed file up with the rest.

The bioguide here is from the first capture, because the letter's own date is
not known until the parse. ``build_congress.py`` attributes every letter again
from its parsed date, so this one only needs to be good enough for the parse
to know whose surname to look for.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "build"))
import address_holders as ah  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--paths", type=Path, default=ROOT / "data" / "letters-paths.jsonl")
    ap.add_argument("--out", type=Path,
                    default=ROOT / "harvest" / "letters" / "letters-raw-paths.jsonl")
    ap.add_argument("--members-out", type=Path,
                    default=ROOT / "harvest" / "letters" / "members-paths.json")
    args = ap.parse_args()

    idx = ah.index(ah.load())
    people: dict[str, dict] = {}
    for _, row in ah.roster_rows():
        name = row["name"].strip()
        people.setdefault(row["bioguide_id"], {
            "bioguide": row["bioguide_id"], "name": name,
            "last": name.split()[-1] if name else ""})

    stats: Counter = Counter()
    used: set[str] = set()
    with args.paths.open(encoding="utf-8") as src, \
            args.out.open("w", encoding="utf-8", newline="\n") as out:
        for line in src:
            row = json.loads(line)
            a = ah.attribute(idx, row["url"], "", row.get("timestamp") or "")
            stats[a.attribution] += 1
            if a.bioguide_id:
                used.add(a.bioguide_id)
            out.write(json.dumps({
                "bioguide": a.bioguide_id,
                "host": row["site"],
                **{k: row[k] for k in ("key", "url", "timestamp", "mimetype",
                                       "length", "digest") if k in row},
            }, ensure_ascii=False) + "\n")

    args.members_out.write_text(json.dumps(
        [people[b] for b in sorted(used) if b in people], indent=1),
        encoding="utf-8")
    total = sum(stats.values())
    print(f"{total:,} path letters", file=sys.stderr)
    for k, v in stats.most_common():
        print(f"  {k:>15}: {v:6,} ({v / max(1, total) * 100:5.1f}%)", file=sys.stderr)
    print(f"  {len(used)} members; wrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
