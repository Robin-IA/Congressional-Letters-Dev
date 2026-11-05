#!/usr/bin/env python3
"""Turn the backfill queue into a roster ``harvest.py`` can read.

``build/chamber_rosters.py`` writes ``data/member-sites.tsv``: every member
website the chambers listed, 2003 to 2026, flagged for whether our own roster
knows about it. The rows flagged ``no`` are members who have left, and they are
the material the README calls most at risk. This script shapes those rows the
way ``harvest.py`` expects a member, so the same harvest can run over them.

Why it needs a step of its own
------------------------------
``harvest.py`` builds its roster from ``legislators-current.json`` and then
*writes* it to ``data/members.json``, which the explorer reads. Pointing it at
a different set of people would therefore replace the explorer's member list
with departed members -- the failure its own ``--limit`` comment records, where
a three-host trial run "quietly rewrote the dataset as three members and the
explorer rebuilt around it". So the backfill roster is built here, written
somewhere else, and passed in with ``--members-in``.

What is left out, and why
-------------------------
**Path-keyed sites are skipped.** Through the 2000s most representatives sat
at ``house.gov/<name>/`` rather than on a subdomain, and 437 of the queue look
like that. They are not hosts: ``harvest_host`` would make a cache filename
containing a slash and enumerate the wrong thing. Finding their letters needs a
CDX query against a path prefix rather than a host, which is a second pass and
not a variation on this one. They stay in the TSV; ``--include-path-keyed``
lists them without pretending they are ready.

Identity is partial, and that is recorded rather than guessed. The Senate's own
directory states a ``bioguide_id``; the House's does not, so a House row gets
whatever ``legislators-historical.json`` can supply by matching its hostname,
and an empty string when nothing matches. ``harvest.py`` only needs ``host``,
but it copies ``bioguide`` into every row it emits, so a blank there means a
letter that cannot yet be attributed to a person -- fixable later by name, not
by inventing an id now.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

HISTORICAL = ("https://unitedstates.github.io/congress-legislators/"
              "legislators-historical.json")

UA = {"User-Agent": "ia-congressional-member-letters/0.1 "
                    "(Internet Archive; collections research)"}


def norm(host: str) -> str:
    host = host.lower().strip().rstrip(".")
    return host[4:] if host.startswith("www.") else host


def host_of(url: str) -> str:
    if not url:
        return ""
    if not url.startswith("http"):
        url = "http://" + url
    return norm(urlparse(url).hostname or "")


def load_historical(cache: Path) -> dict[str, dict]:
    """{hostname: {bioguide, name, chamber, state, since}} for departed members."""
    path = cache / "legislators-historical.json"
    if not path.exists() or not path.stat().st_size:
        path.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(HISTORICAL, headers=UA)
        with urllib.request.urlopen(req, timeout=180) as r:
            path.write_bytes(r.read())

    by_host: dict[str, dict] = {}
    for person in json.loads(path.read_text(encoding="utf-8")):
        terms = person.get("terms", [])
        years = [int(t["start"][:4]) for t in terms
                 if (t.get("start") or "")[:4].isdigit()]
        name = person.get("name", {})
        ident = {
            "bioguide": (person.get("id", {}) or {}).get("bioguide", ""),
            "name": name.get("official_full")
                    or ("%s %s" % (name.get("first", ""), name.get("last", ""))).strip(),
            "last": name.get("last", ""),
            "since": min(years) if years else None,
        }
        for term in terms:
            host = host_of(term.get("url") or "")
            if not host:
                continue
            # A later term wins: the same host can outlive one member only by
            # being reassigned, and the most recent holder is the useful one.
            by_host[host] = {**ident,
                             "chamber": "sen" if term.get("type") == "sen" else "rep",
                             "state": term.get("state", "")}
    return by_host


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sites", type=Path, default=root / "data" / "member-sites.tsv")
    ap.add_argument("--cache", type=Path, default=root / "data" / "cdx-cache")
    ap.add_argument("--out", type=Path,
                    default=root / "data" / "backfill-members.json")
    ap.add_argument("--include-path-keyed", action="store_true",
                    help="also list the house.gov/<name> rows, which this "
                         "pipeline cannot query yet")
    args = ap.parse_args()

    rows = [r for r in csv.DictReader(args.sites.open(encoding="utf-8"), delimiter="\t")
            if r["in_explorer"] == "no"]
    hosts = [r for r in rows if "/" not in r["host"]]
    path_keyed = [r for r in rows if "/" in r["host"]]

    historical = load_historical(args.cache)

    members, unidentified = [], 0
    for r in hosts:
        ident = historical.get(r["host"], {})
        bioguide = r["bioguide"] or ident.get("bioguide", "")
        if not bioguide:
            unidentified += 1
        members.append({
            "since": ident.get("since"),
            "bioguide": bioguide,
            "name": ident.get("name", ""),
            "last": ident.get("last", ""),
            "host": r["host"],
            "url": "https://%s" % r["host"],
            "chamber": "sen" if r["chamber"] == "senate" else "rep",
            "state": ident.get("state", ""),
            "district": None,
            "party": "",
            # Provenance, so a later pass can tell these from the sitting roster.
            "source": "chamber-directory",
            "listed": "%s-%s" % (r["first_year"], r["last_year"]),
        })

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(members, ensure_ascii=False), encoding="utf-8")

    print("backfill queue           : %d" % len(rows))
    print("  queryable hostnames    : %d  -> %s" % (len(members), args.out))
    print("  path-keyed, not yet    : %d  (house.gov/<name>; needs a prefix query)"
          % len(path_keyed))
    print("  named from legislators : %d" % (len(members) - unidentified))
    print("  no identity yet        : %d  (letters will carry an empty bioguide)"
          % unidentified)

    if args.include_path_keyed:
        print("\npath-keyed rows:")
        for r in path_keyed:
            print("  %-40s %s-%s" % (r["host"], r["first_year"], r["last_year"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
