#!/usr/bin/env python3
"""Did 105th Congress members (1997-98) use <name>.house.gov sites? (#1386)

The 105th count in #1330 looked only under the shared paths,
``www.house.gov/<name>/`` and ``www.senate.gov/~<name>/``, and found captures
for 472 of 549 members. It could not check the ``<name>.house.gov`` subdomains:
``matchType=domain`` timed out on them. This asks CDX about each candidate
host with ``matchType=host``, which is cheaper, one request at a time.

Who is asked about, and why:

* **The members the paths missed** (79: the 77 of #1330, plus Pitts and Quinn,
  whose path queries failed with 504 and 503). For each, every host they might
  have used: the address the 1999 House and Senate directories give them
  (data/address-holders.csv), then ``<x>.house.gov`` and ``www-<x>.house.gov``
  (as Eshoo's) or ``<x>.senate.gov``, where ``<x>`` is the surname, the first
  name and surname run together (``davidbonior``), and the same for each other
  name the vocabulary has for them (``Curt Weldon`` for "W. Weldon"). Where the
  1999 directory gives a path other than the obvious one (``house.gov/
  curtweldon``), that path is asked about too.
* **Armey**, whose subdomain is the one #1330 saw answer (170 URLs), as a
  control: if it comes back empty, the run is not to be trusted.
* With ``--all``, every 105th member's ``<surname>.house.gov`` or
  ``<surname>.senate.gov``, once, to say whether the pattern was used at all.

Each host is asked for 1997 to 1999. Captures in 1997-98 mean the letters can
come from the Wayback Machine. Captures that begin only in 1999, or a 1999
directory that lists the subdomain, mean the site was probably there in 1998
before anyone captured it: those members are flagged for the 20thcenturyweb
collection of pre-2000 archives, per Robin's rule in #1386 ("First, search
Wayback - if none pass and it does look the subdomain was used, then note for
searching 20thcenturyweb").

Fetches from the Wayback Machine, so **do not run it beside the renderer or a
harvest**; they share one rate limit (CLAUDE.md). It is resumable: hosts
already in the output are skipped, so a stopped run picks up where it was.

    python3 build/check_105_subdomains.py --plan     # list the queries, fetch nothing
    python3 build/check_105_subdomains.py            # the 79, plus Armey
    python3 build/check_105_subdomains.py --all      # and every member's <surname> host

Writes data/rosters/subdomains-105.tsv (one row per host asked) and prints a
verdict per member.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import time
import unicodedata
import urllib.parse
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROSTER = ROOT / "data/rosters/congress105-roster.csv"
FOUND = ROOT / "data/rosters/cdx-urls-105.tsv"
HOLDERS = ROOT / "data/address-holders.csv"
RELATIONS = ROOT / "vocabulary/relations.csv"
OUT = ROOT / "data/rosters/subdomains-105.tsv"

CONTROL = "A000217"          # Richard Armey: armey.house.gov answered in #1330
LETTERISH = re.compile(r"(^|[^a-z])(letters?|ltrs?|let)([^a-z]|$)")
SUFFIX = {"jr", "sr", "ii", "iii", "iv"}
FIELDS = ["bioguide_id", "name", "chamber", "host", "why", "status",
          "captures_1997_98", "letterish_1997_98", "captures_1999",
          "first_capture", "verdict"]


def slug(text: str) -> str:
    """ "Gutiérrez" -> "gutierrez"; keeps hyphens ("ros-lehtinen")."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z-]", "", text.lower())


def name_words(name: str) -> list[str]:
    return [w for w in re.sub(r'["“”(),]', " ", name).split()
            if slug(w).strip("-") and slug(w) not in SUFFIX]


def stems_of(name: str) -> list[str]:
    """Host stems a name suggests: surname, first name + surname, and a two-word
    surname whole ("Carol Moseley Braun" -> braun, carolbraun, moseley-braun,
    moseleybraun, carolmoseleybraun)."""
    words = name_words(name)
    first, last = name_parts(name)
    out = [last]
    if len(words) >= 2 and first != last:
        out.append(first + last)
    if len(words) >= 3 and not words[-2].endswith(".") and slug(words[-2]) != first:
        two = slug(words[-2]) + "-" + last
        out += [two, two.replace("-", ""), first + two.replace("-", "")]
    if "-" in last:
        out.append(last.replace("-", ""))
    return [x for x in dict.fromkeys(out) if x]


def name_parts(name: str) -> tuple[str, str]:
    """(first, surname) from "Robert C. \\"Bobby\\" Scott" or "Frank Pallone, Jr."."""
    words = name_words(name)
    first = next((w for w in words if not w.endswith(".")), words[0] if words else "")
    return slug(first), slug(words[-1]) if words else ""


def is_own_site(address: str) -> bool:
    """A host of the member's own, not a path on the shared house.gov or senate.gov."""
    return not re.match(r"^(www\.)?(house|senate)\.gov/", address)


def load(path: Path, delimiter: str = ",") -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter=delimiter))


def other_names() -> dict[str, list[str]]:
    out: dict[str, list[str]] = defaultdict(list)
    if RELATIONS.exists():
        for r in load(RELATIONS):
            if r["relation"] == "altLabel" and r["term_id"].startswith("M-"):
                out[r["term_id"][2:]].append(r["value"])
    return out


def candidates(member: dict, holders: list[dict], aka: list[str]) -> list[tuple[str, str]]:
    """(host or path prefix, why) for one member, most likely first."""
    senate = member["chamber"] == "Senate"
    out: list[tuple[str, str]] = []

    def add(target: str, why: str) -> None:
        if target and target not in [t for t, _ in out]:
            out.append((target, why))

    # Addresses from the House and Senate directories, which begin in 1999.
    # Only one seen by 1999 is evidence the member used it in 1997-98.
    for h in sorted(holders, key=lambda h: h["first_capture"] or "9999"):
        seen = f"directory, first seen {h['first_capture'][:7] or 'never'}"
        if is_own_site(h["address"]):
            add(h["address"], seen)
        else:
            add(h["address"].removeprefix("www.") + "/", seen + ", path")
    stems: list[str] = []
    for n in [member["name"], *aka]:
        stems += [x for x in stems_of(n) if x not in stems]
    for stem in stems:
        if senate:
            add(f"{stem}.senate.gov", "guess")
        else:
            add(f"{stem}.house.gov", "guess")
            add(f"www-{stem}.house.gov", "guess, as www-eshoo")
    return out


def query(target: str) -> str:
    params = [("url", target), ("from", "1997"), ("to", "1999"),
              ("filter", "statuscode:200"), ("collapse", "urlkey"),
              ("fl", "original,timestamp,mimetype"), ("limit", "5000")]
    if not target.endswith("/"):
        params.insert(1, ("matchType", "host"))
    else:
        # A path: prefix match, and no wildcard with it (harvest.cdx_rows).
        params.insert(1, ("matchType", "prefix"))
    return "https://web.archive.org/cdx/search/cdx?" + urllib.parse.urlencode(params)


def summarize(body: str) -> dict:
    rows = [line.split(" ") for line in body.splitlines() if line.count(" ") == 2]
    early = [r for r in rows if r[1][:4] in ("1997", "1998")]
    late = [r for r in rows if r[1][:4] == "1999"]
    return {
        "captures_1997_98": len(early),
        "letterish_1997_98": sum(1 for r in early
                                 if LETTERISH.search(urllib.parse.urlsplit(r[0]).path.lower())),
        "captures_1999": len(late),
        "first_capture": min((r[1] for r in rows), default=""),
    }


def verdict_for(rows: list[dict]) -> str:
    """One member's verdict from the hosts asked about (#1386's rule)."""
    if any(r["status"] != "ok" for r in rows) and not any(int(r["captures_1997_98"] or 0) for r in rows):
        return "retry: a query failed"
    early = [r for r in rows if int(r["captures_1997_98"] or 0)]
    if early:
        best = max(early, key=lambda r: int(r["captures_1997_98"]))
        kind = "subdomain" if not best["host"].endswith("/") else "path"
        return f"Wayback: {best['host']} ({best['captures_1997_98']} URLs in 1997-98, {best['letterish_1997_98']} letter-named; {kind})"
    used = [r for r in rows if not r["host"].endswith("/")
            and (int(r["captures_1999"] or 0) or "first seen 1999" in r["why"])]
    if used:
        return f"20thcenturyweb: {used[0]['host']} was in use by 1999, nothing captured in 1997-98"
    return "no site found in Wayback for 1997-98"


def fetch(url: str) -> str:
    sys.path.insert(0, str(ROOT / "build"))
    from harvest import fetch as harvest_fetch  # https, retries, HTML-as-outage
    return harvest_fetch(url, timeout=120)


def plan(everyone: bool) -> list[tuple[dict, str, str]]:
    roster = load(ROSTER)
    found = {r["bioguide_id"] for r in load(FOUND, "\t")}
    holders: dict[str, list[dict]] = defaultdict(list)
    for h in load(HOLDERS):
        holders[h["bioguide_id"]].append(h)
    aka = other_names()
    out = []
    for m in roster:
        if m["bioguide_id"] not in found or m["bioguide_id"] == CONTROL:
            for target, why in candidates(m, holders[m["bioguide_id"]], aka[m["bioguide_id"]]):
                out.append((m, target, why))
        elif everyone:
            _, last = name_parts(m["name"])
            out.append((m, f"{last}.{'senate' if m['chamber'] == 'Senate' else 'house'}.gov", "--all"))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--plan", action="store_true", help="list the queries; fetch nothing")
    ap.add_argument("--all", action="store_true", help="also every member's <surname> host")
    ap.add_argument("--pause", type=float, default=2.0, help="seconds between requests")
    args = ap.parse_args()

    todo = plan(args.all)
    if args.plan:
        for m, target, why in todo:
            print(f"{m['name'][:26]:26} {target:40} {why}")
        print(f"{len(todo)} queries for {len({m['bioguide_id'] for m, _, _ in todo})} members")
        return

    done = {(r["bioguide_id"], r["host"]): r for r in load(OUT, "\t")} if OUT.exists() else {}
    print(f"{len(todo)} queries; {sum(1 for m, t, _ in todo if (m['bioguide_id'], t) in done)} already done",
          flush=True)
    for m, target, why in todo:
        key = (m["bioguide_id"], target)
        if key in done and done[key]["status"] == "ok":
            continue
        row = {"bioguide_id": m["bioguide_id"], "name": m["name"], "chamber": m["chamber"],
               "host": target, "why": why, "status": "ok", "captures_1997_98": 0,
               "letterish_1997_98": 0, "captures_1999": 0, "first_capture": "", "verdict": ""}
        try:
            row.update(summarize(fetch(query(target))))
        except Exception as exc:  # noqa: BLE001 - recorded, and retried on the next run
            row["status"] = f"error: {str(exc)[:80]}"
        done[key] = row
        print(f"  {m['name'][:26]:26} {target:40} {row['status']:6} "
              f"{row['captures_1997_98']:>5} in 1997-98, {row['captures_1999']:>5} in 1999", flush=True)
        write(done)
        time.sleep(args.pause)

    by_member: dict[str, list[dict]] = defaultdict(list)
    for r in done.values():
        by_member[r["bioguide_id"]].append(r)
    for rows in by_member.values():
        v = verdict_for(rows)
        for r in rows:
            r["verdict"] = v
    write(done)
    control = by_member.get(CONTROL, [])
    if control and not any(int(r["captures_1997_98"] or 0) for r in control):
        print("WARNING: armey.house.gov, the control, came back empty; do not trust this run")
    tally: dict[str, int] = defaultdict(int)
    for rows in by_member.values():
        tally[rows[0]["verdict"].split(":")[0]] += 1
        print(f"{rows[0]['name'][:28]:28} {rows[0]['verdict']}")
    print(dict(tally))


def write(done: dict) -> None:
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        for r in sorted(done.values(), key=lambda r: (r["name"], r["host"])):
            w.writerow(r)


if __name__ == "__main__":
    main()
