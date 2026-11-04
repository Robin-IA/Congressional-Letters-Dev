#!/usr/bin/env python3
"""Every member website the House and Senate listed, year by year, from Wayback.

Why this exists
---------------
The explorer harvests the *sitting* roster, which is why Lindsey Graham is not
in it: he left mid-term, a successor took the South Carolina seat in 2026, and
``legislators-current.json`` only ever describes today. Members who have left
are the material the README calls most at risk and least replaceable, and
mapping them to websites they no longer have was the thing that made it hard.

Both chambers did that mapping themselves, every year, and published it: a
directory of members linking to their official sites. Those pages are in the
Wayback Machine. Reading one capture per year turns them into dated rosters --
the union this project would otherwise have had to accumulate one October at a
time -- from the same archive the captures themselves come from.

Two other sources were considered and are not enough on their own.
``legislators-historical.json`` carries a term ``url`` for only 903 of its
12,231 members, giving 743 hostnames. The Congress.gov API has authoritative
per-Congress rosters but drops ``officialWebsiteUrl`` once a member leaves --
verified absent for Graham, Flake and Deal -- so it answers who served, never
where they published. The Clerk's ``MemberData.xml`` has bioguide IDs and
districts but no per-member site.

What this script is for
-----------------------
It writes ``data/member-sites.tsv``: one row per member website, the years it
was listed, and whether our own roster knows about it. The rows where
``in_explorer`` is ``no`` are the backfill queue.

Feed those hosts to ``harvest.py``. This script establishes the roster; the
captures come from the CDX API, which is what the rest of the pipeline reads.

The sources
-----------
The Senate publishes a structured file, which is the better source on both
counts: it is unambiguous, and it carries ``bioguide_id`` so a row joins to our
roster without matching on names. The House has no equivalent -- the Clerk's
XML omits websites -- so its directories are parsed as HTML, across three
addresses that overlap into one run. Each chamber is continuous from 2003.

Traps
-----
**Wayback serves some captures gzipped and urllib does not unwrap them.**
Decoding those bytes as text destroys the page silently: gzip's 0x8b magic byte
becomes U+FFFD and every link is lost, which reads exactly like a format
change. ``decode`` sniffs the magic as well as trusting the header.

**Many House members have no host of their own.** Through the 2000s most sat at
``house.gov/<name>/`` rather than on a subdomain -- 391 of 440 in 2003, still
75 in 2015, none by 2016. Keying on the bare host would collapse hundreds of
them into one, so those are keyed host + first path segment.

**A directory page is full of chamber furniture**, and a retired one is a "Page
Not Found" stub that parses to nothing. Neither is a failure: the guard runs
per chamber-year over every source combined, so a dead address costs nothing
while another still covers that year.

Coverage before 2003 is genuinely thin -- 5 hosts in 1999, 26 in 2002 --
because few members had a site to link to yet. That is a fact about 1999, not a
parsing failure, so those years are reported and not guarded.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

# (chamber, url, kind). Oldest first per chamber; they overlap by design.
SOURCES = [
    ("senate", "senate.gov/general/contact_information/senators_cfm.cfm", "html"),
    ("senate", "www.senate.gov/general/contact_information/senators_cfm.xml", "xml"),
    ("house", "house.gov/house/MemberWWW.html", "html"),
    ("house", "www.house.gov/house/MemberWWW.shtml", "html"),
    ("house", "www.house.gov/representatives", "html"),
]

CDX = ("https://web.archive.org/cdx/search/cdx?url=%s&output=json&fl=timestamp"
       "&filter=statuscode:200&collapse=timestamp:4&limit=60")
REPLAY = "https://web.archive.org/web/%sid_/http://%s"

UA = {"User-Agent": "ia-congressional-member-letters/0.1 "
                    "(Internet Archive; collections research)"}

TIMEOUT = 120
RETRIES = 3
PAUSE = 1.5

# The chamber's own sections, which sit in the same markup as the members.
FURNITURE = {
    "representatives", "senators", "leadership", "committees", "committee",
    "clerk", "clerkweb", "house", "senate", "writerep", "daily", "schedule",
    "learn", "evs", "legislative", "artandhistory", "reference", "visitors",
    "pagfoundation", "educate", "galleries", "general", "about", "contact",
    "search", "index", "home", "media", "news", "jobs", "doc", "docs",
}

# Before this, a directory listed a handful of sites because a handful existed.
GUARD_FROM = 2003
EXPECTED = {"senate": 100, "house": 440}

LINK = re.compile(r'href="([^"]+)"', re.I)
WEBSITE = re.compile(r"<website>\s*([^<\s]+)\s*</website>", re.I)
MEMBER_XML = re.compile(r"<member>(.*?)</member>", re.I | re.S)
BIOGUIDE = re.compile(r"<bioguide_id>\s*([^<\s]+)\s*</bioguide_id>", re.I)
# Wayback rewrites in-page links to point back at itself; strip that prefix so
# the original target is what gets parsed.
WB_PREFIX = re.compile(r'https?://web\.archive\.org/web/\d+(?:id_)?/', re.I)


def decode(raw: bytes, encoding: str | None) -> str:
    if (encoding or "").lower() == "gzip" or raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return raw.decode("utf-8", "replace")


def fetch(url: str, cache: Path) -> str:
    if cache.exists() and cache.stat().st_size:
        return decode(cache.read_bytes(), None)
    last: Exception | None = None
    for attempt in range(RETRIES):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                body = decode(r.read(), r.headers.get("Content-Encoding"))
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(body, encoding="utf-8")
            time.sleep(PAUSE)
            return body
        except (urllib.error.URLError, OSError) as e:
            last = e
            time.sleep(2 + attempt * 3)
    raise RuntimeError("%s: %s" % (url, last))


def norm(host: str) -> str:
    host = host.lower().strip().rstrip(".")
    return host[4:] if host.startswith("www.") else host


def member_key(raw: str) -> str | None:
    """A member's site: their own host, or house.gov/<name> for path-keyed ones."""
    if not raw or raw.startswith(("#", "mailto:", "javascript:")):
        return None
    parsed = urlparse(raw if raw.startswith("http") else "http://" + raw.lstrip("/"))
    host = norm(parsed.hostname or "")
    if not host.endswith(("house.gov", "senate.gov")):
        return None

    if host.count(".") >= 2:
        return None if host.split(".")[0] in FURNITURE else host

    seg = parsed.path.strip("/").split("/")[0].lower() if parsed.path else ""
    if not seg or seg in FURNITURE or "." in seg:
        return None
    return "%s/%s" % (host, seg)


def parse_html(page: str) -> dict[str, str]:
    """{host: ''} -- HTML directories give no usable identifier beyond the link."""
    found = {}
    for href in LINK.findall(WB_PREFIX.sub("", page)):
        key = member_key(href)
        if key:
            found.setdefault(key, "")
    return found


def parse_xml(page: str) -> dict[str, str]:
    """{host: bioguide} -- the Senate file states the id, so no name matching."""
    found = {}
    for block in MEMBER_XML.findall(page):
        site = WEBSITE.search(block)
        if not site:
            continue
        key = member_key(site.group(1))
        if not key:
            continue
        bio = BIOGUIDE.search(block)
        found[key] = bio.group(1) if bio else ""
    return found


def captures(url: str, cache: Path) -> list[str]:
    rows = json.loads(fetch(CDX % url, cache))
    return [r[0] for r in rows[1:]] if len(rows) > 1 else []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cache", type=Path,
                    default=Path("data/cdx-cache/chamber-directories"))
    ap.add_argument("--roster", type=Path, default=Path("data/members.json"))
    ap.add_argument("--out", type=Path, default=Path("data/member-sites.tsv"))
    args = ap.parse_args()

    chamber_of: dict[str, str] = {}
    bioguide_of: dict[str, str] = {}
    years_of: dict[str, set[int]] = defaultdict(set)
    # (chamber, year) -> hosts, so the guard sees every source at once.
    per_year: dict[tuple[str, int], set[str]] = defaultdict(set)

    for chamber, url, kind in SOURCES:
        slug = re.sub(r"[^a-z0-9]+", "-", url.lower()).strip("-")
        print("\n%-6s %s" % (chamber, url), file=sys.stderr)
        for ts in captures(url, args.cache / ("cdx-%s.json" % slug)):
            year = int(ts[:4])
            page = fetch(REPLAY % (ts, url), args.cache / ("%s-%s.html" % (slug, ts)))
            found = parse_xml(page) if kind == "xml" else parse_html(page)

            for host, bio in found.items():
                chamber_of.setdefault(host, chamber)
                years_of[host].add(year)
                if bio:
                    bioguide_of.setdefault(host, bio)
            per_year[(chamber, year)] |= set(found)
            print("  %d  %4d members%s" % (
                year, len(found), "" if found else "   (nothing here)"), file=sys.stderr)

    short, thin = [], []
    for (chamber, year), hosts in sorted(per_year.items()):
        if len(hosts) >= EXPECTED[chamber] * 0.9:
            continue
        line = "%d %s: %d members, expected ~%d" % (
            year, chamber, len(hosts), EXPECTED[chamber])
        (short if year >= GUARD_FROM else thin).append(line)

    if short:
        print("\nPARSE LOOKS WRONG -- a chamber-year is not this small:", file=sys.stderr)
        for s in short:
            print("  " + s, file=sys.stderr)
        return 1

    explorer = {norm(m["host"])
                for m in json.loads(args.roster.read_text(encoding="utf-8"))
                if m.get("host")}

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("host\tchamber\tbioguide\tfirst_year\tlast_year"
                 "\tyears_listed\tin_explorer\n")
        for host in sorted(years_of):
            ys = sorted(years_of[host])
            fh.write("%s\t%s\t%s\t%d\t%d\t%d\t%s\n" % (
                host, chamber_of[host], bioguide_of.get(host, ""),
                ys[0], ys[-1], len(ys), "yes" if host in explorer else "no"))

    backfill = sum(1 for h in years_of if h not in explorer)
    covered = sorted({y for (_, y) in per_year if y >= GUARD_FROM})
    print("\n%d distinct member sites, %d-%d" % (len(years_of), covered[0], covered[-1]))
    print("  in the explorer already    : %d" % (len(years_of) - backfill))
    print("  backfill queue             : %d" % backfill)
    print("  with a bioguide id         : %d" % len(bioguide_of))
    print("  explorer sites never listed: %d" % len(explorer - set(years_of)))
    if thin:
        print("\n  thin early years, as expected: %s"
              % "; ".join(t.split(",")[0] for t in thin))
    print("\nwrote %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
