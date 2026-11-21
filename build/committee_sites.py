#!/usr/bin/env python3
"""Committee websites, for harvesting committee letters (#23).

    python3 build/committee_sites.py          # -> data/committee-sites.csv

One row per committee website: chamber, committee, ``thomas_id``, the site
(a host, or a path on a chamber's host), the **party** that runs it, the
Congresses it is known for, where that came from, and whether a capture has
confirmed it.

**A site's side is not fixed; its party is.** ``republicans-agriculture.house.gov``
was the minority's site in the 116th-117th and, since 2023, redirects to the
majority's. congress-legislators' ``minority_url`` is still that 117th host for
18 of the 20 House committees that have one (checked on the live sites,
17 November 2026: every ``republicans-X`` answers 301 to the majority site and
``democrats-X`` answers 200; Oversight's minority is
``oversightdemocrats.house.gov``). So this records ``party`` -- ``R`` or ``D``
from the host (``republicans-``, ``gop-``, ``democrats-``, ``...democrats``),
blank for the committee's own site, which the majority runs -- and
``side_on(chamber, party, date)`` says which side that was on a letter's date.
The chair or ranking member on that date (``data/committee-chairs.csv``) is
the fallback signer.

Sources, merged:

1. ``data/legislators/committees-current.json`` (unitedstates/congress-legislators,
   gitignored): the 119th's sites.
2. ``data/rosters/committee-directory-NNN.tsv`` from ``committee_directories.py``:
   the chambers' own committee directories in Wayback, 106th-118th.
3. Party-prefixed House hosts for each committee host found by 1 or 2
   (``democrats-X``, ``republicans-X``), marked ``verified=no`` until the
   measurement's CDX query finds captures. A pattern is a guess, not a source.

Decided by Robin, 17 November 2026 (#23): joint committees and commissions are
included (congressional groups); committee letters are credited to every
member who signed them, carry the committee, and appear in each Congress's
explorer with a committee filter, as caucus letters do. Stdlib only.
"""
from __future__ import annotations

import csv
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "legislators"
ROSTERS = ROOT / "data" / "rosters"
OUT = ROOT / "data" / "committee-sites.csv"
CHAMBER = {"house": "House", "senate": "Senate", "joint": "Joint"}

# Majority party of each chamber, by Congress (Office of the Historian / Senate
# Historical Office party divisions). The 107th Senate changed hands twice.
HOUSE_MAJORITY = {**{n: "R" for n in range(106, 110)}, 110: "D", 111: "D",
                  **{n: "R" for n in range(112, 116)}, 116: "D", 117: "D", 118: "R", 119: "R"}
SENATE_MAJORITY = {106: "R", 108: "R", 109: "R", **{n: "D" for n in range(110, 114)},
                   114: "R", 115: "R", 116: "R", 117: "D", 118: "D", 119: "R"}
SENATE_107 = [(date(2001, 1, 3), "D"), (date(2001, 1, 20), "R"), (date(2001, 6, 6), "D")]


def congress_of(d: date) -> int:
    """The Congress sitting on d (terms begin 3 January of odd years)."""
    y = d.year - (1 if (d.month, d.day) < (1, 3) else 0)
    return (y - 1789) // 2 + 1


def majority_on(chamber: str, d: date) -> str:
    n = congress_of(d)
    if chamber == "Senate" and n == 107:
        return [p for start, p in SENATE_107 if d >= start][-1]
    return (SENATE_MAJORITY if chamber == "Senate" else HOUSE_MAJORITY).get(n, "")


def side_on(chamber: str, party: str, d: date) -> str:
    """'majority' or 'minority' for a site run by party on d; '' for a committee's own site."""
    if not party or chamber == "Joint":
        return "majority" if not party else ""
    m = majority_on(chamber, d)
    return "" if not m else ("majority" if party == m else "minority")


def party_of(url: str) -> str:
    host, _, path = re.sub(r"^https?://", "", url.lower()).partition("/")
    if re.match(r"(republicans|gop)-", host) or re.search(r"republican|gop", path):
        return "R"
    if re.match(r"(democrats|dems)-", host) or re.search(r"democrats\.", host) or "democrat" in path:
        return "D"
    return ""


def site_of(url: str) -> str:
    """https://agriculture.house.gov/ -> agriculture.house.gov; www.house.gov/judiciary stays a path."""
    s = re.sub(r"^https?://", "", url.strip()).rstrip("/").lower()
    host, _, path = s.partition("/")
    if path and host in ("www.house.gov", "house.gov", "www.senate.gov"):
        return f"{host}/{path.split('/')[0]}"
    return s if "jointcommittees/" in path else host   # the Library and Printing pages on cha.house.gov


def main() -> None:
    rows: dict[tuple, dict] = {}

    def add(chamber, committee, tid, url, congresses, source, verified):
        s = site_of(url)
        key = (tid or committee, s)
        r = rows.setdefault(key, {"chamber": chamber, "committee": committee, "thomas_id": tid,
                                  "site": s, "party": party_of(url), "congresses": set(),
                                  "source": set(), "verified": verified})
        r["congresses"] |= set(congresses)
        r["source"].add(source)
        if verified == "yes":
            r["verified"] = "yes"

    current = json.loads((SRC / "committees-current.json").read_text(encoding="utf-8"))
    for c in current:
        ch = CHAMBER.get(c.get("type"), c.get("type"))
        for key in ("url", "minority_url"):
            url = (c.get(key) or "").strip()
            if not url:
                continue
            # the source's minority_url is a party's host; which Congresses it served is for CDX to say
            cong = {119} if key == "url" else set()
            add(ch, c["name"], c.get("thomas_id", ""), url, cong,
                "congress-legislators committees-current" + ("" if key == "url" else " (minority_url)"), "listed")

    # seen on the live sites, 17 November 2026: hosts the source and the patterns miss
    for tid, name, url in (("HSGO", "House Committee on Oversight and Government Reform",
                            "https://oversightdemocrats.house.gov/"),
                           ("HSED", "House Committee on Education and Workforce",
                            "https://edworkforce.house.gov/")):
        add("House", name, tid, url, {119}, "live site, 17 November 2026", "yes")

    for tsv in sorted(ROSTERS.glob("committee-directory-*.tsv")):
        n = int(tsv.stem.rsplit("-", 1)[1])
        with tsv.open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh, delimiter="\t"):
                add(r["listed_in"], r["committee"] or r["name_listed"], r["thomas_id"], r["url"], {n},
                    f"{r['listed_in']} committee directory (Wayback)", "listed")

    # party-prefixed hosts for each House committee host, to be confirmed by CDX
    for (tid, s), r in list(rows.items()):
        host = s.split("/")[0]
        if r["chamber"] != "House" or "/" in s or r["party"] or not host.endswith(".house.gov"):
            continue
        base = host[: -len(".house.gov")]
        for pre in ("democrats-", "republicans-"):
            if (tid, f"{pre}{base}.house.gov") not in rows:
                add("House", r["committee"], r["thomas_id"], f"https://{pre}{base}.house.gov", set(),
                    "pattern from the committee's host", "no")

    out = sorted(rows.values(), key=lambda r: (r["chamber"], r["committee"], r["party"], r["site"]))
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["chamber", "committee", "thomas_id", "site", "party",
                                           "congresses", "source", "verified"], lineterminator="\n")
        w.writeheader()
        for r in out:
            w.writerow({**r, "congresses": " ".join(map(str, sorted(r["congresses"]))),
                        "source": "; ".join(sorted(r["source"]))})
    by: dict[str, int] = {}
    for r in out:
        by[f"{r['chamber']} {r['verified']}"] = by.get(f"{r['chamber']} {r['verified']}", 0) + 1
    print(f"{len(out)} committee sites -> {OUT}: " + ", ".join(f"{k} {v}" for k, v in sorted(by.items())))


if __name__ == "__main__":
    main()
