"""Figures for the federated explorer mockup (federated/), derived at build time.

    python3 build/federated_mockup.py

Writes federated/data.json: one entry per Congress from the 106th, with its
dates, roster size, today's letters by the Congress in session on each
letter's date, the members those letters came from, the most written-to
recipients, and how far the pipeline has got for that Congress.

"Today's letters" are the explorer's corpus -- letters on the websites of the
119th Congress's members, including those who left during it. Each earlier
Congress gains the letters of members who had left by 2025 as its own harvest
(EXPLORERS.md step 4) is run; until then its count is a floor, and the page
says so.
"""

import collections
import csv
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LETTERS = [ROOT / "data/letters-parsed.jsonl", ROOT / "data/letters-119-departed-parsed.jsonl"]
ROSTERS = ROOT / "data/rosters"
HARVEST = ROOT / "harvest/letters-115-118-members.json"
CACHE = ROOT / "harvest/letters/cache"
OUT = ROOT / "federated/data.json"

FIRST, LAST = 106, 119
PUBLISHED = {119: "../119th/"}
HARVESTING = {115, 116, 117, 118}


def congress_of(iso: str) -> int:
    """The Congress in session on a YYYY-MM-DD date (terms begin 3 January of odd years)."""
    y, m, d = int(iso[:4]), int(iso[5:7]), int(iso[8:10])
    if y % 2 == 1 and (m, d) < (1, 3):
        y -= 1
    return (y - 1787) // 2


def dates(n: int) -> tuple[str, str]:
    start = 1787 + 2 * n
    return f"{start}-01-03", f"{start + 2}-01-03"


def main() -> None:
    seen = set()
    letters = collections.Counter()
    members = collections.defaultdict(set)
    recipients = collections.defaultdict(collections.Counter)
    for f in LETTERS:
        for line in open(f, encoding="utf-8"):
            r = json.loads(line)
            if r["url"] in seen:
                continue
            seen.add(r["url"])
            d = r.get("date_best") or ""
            if not re.match(r"\d{4}-\d\d-\d\d", d):
                continue
            n = congress_of(d)
            letters[n] += 1
            if r.get("bioguide"):
                members[n].add(r["bioguide"])
            if r.get("recipient_canonical"):
                recipients[n][r["recipient_canonical"]] += 1

    hosts = len(json.load(open(HARVEST))) if HARVEST.exists() else 0
    # harvest.py's own test for a host it will not query again
    done = 0
    for f in CACHE.glob("*.json") if CACHE.exists() else []:
        try:
            e = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            continue
        done += "error" not in e and e.get("method") == "paged-v2"

    out = []
    for n in range(LAST, FIRST - 1, -1):
        roster = ROSTERS / f"congress{n}-roster.csv"
        size = sum(1 for _ in csv.DictReader(open(roster, encoding="utf-8"))) if roster.exists() else 0
        start, end = dates(n)
        if n in PUBLISHED:
            status, detail = "published", "Explorer published"
        elif n in HARVESTING:
            status, detail = "harvesting", f"Harvesting departed members' sites: {done} of {hosts} addresses"
        else:
            status, detail = "planned", "Roster and Wayback lookups done; harvest not started"
        out.append({
            "n": n, "start": start, "end": end, "roster": size,
            "letters": letters.get(n, 0), "members": len(members.get(n, ())),
            "top": recipients[n].most_common(3),
            "status": status, "detail": detail, "href": PUBLISHED.get(n),
        })

    OUT.parent.mkdir(exist_ok=True)
    json.dump({"built": date.today().isoformat(), "total": len(seen), "congresses": out},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{OUT.relative_to(ROOT)}: {len(seen):,} letters, {len(out)} Congresses")


if __name__ == "__main__":
    main()
