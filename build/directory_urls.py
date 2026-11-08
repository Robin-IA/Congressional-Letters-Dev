#!/usr/bin/env python3
"""Member URLs as the chambers themselves listed them, for Congresses the source leaves blank.

    python3 build/directory_urls.py 106 107      # writes data/rosters/directory-urls-NNN.tsv

Part of step 1 (see METHODOLOGY.md). ``unitedstates/congress-legislators``
records a ``url`` on few terms before 2003: 459 of the 106th's 544 members
have none. Both chambers published a directory of member websites throughout,
and the Wayback Machine holds it:

* House: ``www.house.gov/house/MemberWWW.html`` -- one ``<li>`` per member,
  "<a href=/name/>Name</a>, State, 3rd".
* Senate: ``www.senate.gov/senators/index.cfm`` -- "<a href=~name/>Last, First</a> (P - ST)".

This reads one capture of each per quarter across the Congress and writes
every listed URL with the dates it was seen. ``congress_roster.py`` uses the
file only for a member the source gives no URL for that term, matched by
chamber, state, district (House) and surname, and says so in
``service_notes``. Step 2 then confirms each one in Wayback inside the
member's own service.

Replayed captures are cached under ``harvest/directories/cache/`` (ignored
by git). Stdlib only.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import html
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "rosters"
CACHE = ROOT / "harvest" / "directories" / "cache"
CDX = "https://web.archive.org/cdx/search/cdx"
UA = {"User-Agent": "ia-congressional-member-letters/0.1 "
                    "(Internet Archive; collections research)"}

SOURCES = [
    ("House", "www.house.gov/house/MemberWWW.html"),
    ("House", "www.house.gov/house/MemberWWW.shtml"),
    ("Senate", "www.senate.gov/senators/index.cfm"),
]

STATES = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", "california": "CA",
    "colorado": "CO", "connecticut": "CT", "delaware": "DE", "florida": "FL", "georgia": "GA",
    "hawaii": "HI", "idaho": "ID", "illinois": "IL", "indiana": "IN", "iowa": "IA",
    "kansas": "KS", "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV", "new hampshire": "NH",
    "new jersey": "NJ", "new mexico": "NM", "new york": "NY", "north carolina": "NC",
    "north dakota": "ND", "ohio": "OH", "oklahoma": "OK", "oregon": "OR", "pennsylvania": "PA",
    "rhode island": "RI", "south carolina": "SC", "south dakota": "SD", "tennessee": "TN",
    "texas": "TX", "utah": "UT", "vermont": "VT", "virginia": "VA", "washington": "WA",
    "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY", "american samoa": "AS",
    "district of columbia": "DC", "guam": "GU", "puerto rico": "PR",
    "virgin islands": "VI", "u.s. virgin islands": "VI", "northern mariana islands": "MP",
}

HOUSE_RE = re.compile(
    r'<a\s+href="?([^"\s>]+)"?[^>]*>\s*([^<]+?)\s*</a>\s*(?:</b>)?\s*,\s*([^<\n]+)', re.I)
SENATE_RE = re.compile(
    r'<a\s+href="?([^"\s>]*senate\.gov[^"\s>]*)"?[^>]*>\s*([^<]+?)\s*</a>\s*(?:&nbsp;|\s)*\(\s*([A-Z]+)\s*-\s*([A-Z]{2})\s*\)',
    re.I)


def get(url: str, pause: float) -> bytes | None:
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                body = r.read()
            time.sleep(pause)
            return body
        except Exception as e:  # noqa: BLE001
            print(f"    retry {attempt + 1}: {e}", file=sys.stderr, flush=True)
            time.sleep(pause * 4 * (attempt + 1))
    return None


def decode(b: bytes) -> str:
    if b[:2] == b"\x1f\x8b":
        b = gzip.decompress(b)
    return b.decode("latin-1")


def captures(src: str, frm: str, to: str, pause: float) -> list[str]:
    q = urllib.parse.urlencode({"url": src, "from": frm, "to": to,
                                "fl": "timestamp,statuscode", "collapse": "timestamp:6"})
    body = get(f"{CDX}?{q}", pause)
    if body is None:
        return []
    ts = [ln.split()[0] for ln in body.decode().splitlines() if ln.endswith(" 200")]
    return ts[::3] + ([ts[-1]] if ts and ts[-1] not in ts[::3] else [])   # about one a quarter


def replay(ts: str, src: str, pause: float) -> str:
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / (hashlib.sha1(f"{ts} {src}".encode()).hexdigest() + ".html")
    if not f.exists():
        b = get(f"https://web.archive.org/web/{ts}id_/http://{src}", pause)
        if b is None:
            return ""
        f.write_bytes(b)
    return decode(f.read_bytes())


def absolute(href: str, src: str) -> str:
    """A member's site: their own host, or www.house.gov/<name> for path-keyed ones."""
    u = urllib.parse.urljoin(f"http://{src}", href.strip())
    p = urllib.parse.urlparse(u)
    host, path = p.netloc.lower(), p.path.strip("/")
    if host in ("www.house.gov", "house.gov") or (host.endswith("senate.gov") and path.startswith("~")):
        path = path.split("/")[0]                     # house.gov/towns/welcome.htm -> house.gov/towns
    return f"https://{host}/{path}".rstrip("/")


def vacancy(url: str) -> bool:
    """The Clerk's page for a vacant seat, listed in place of a member who has left."""
    p = urllib.parse.urlparse(url)
    return ("clerk" in p.netloc or "vacantoffice" in url
            or (p.netloc in ("www.house.gov", "house.gov")
                and p.path.strip("/") in ("house", "")))   # a link back into the directory, not a site


def seat(rest: str) -> tuple[str, str] | None:
    """'Texas, 30th' / 'Arkansas 2nd' / 'American Samoa' -> (state, district); 0 = at large."""
    low = rest.strip().lower()
    names = [n for n in STATES if low.startswith(n)]
    if not names:
        return None
    name = max(names, key=len)
    m = re.match(r"[\s,]*(\d+)", low[len(name):])
    return STATES[name], (m.group(1) if m else "0")


def parse(chamber: str, src: str, page: str) -> list[tuple]:
    rows = []
    if chamber == "House":
        for href, name, rest in HOUSE_RE.findall(page):
            where, url = seat(html.unescape(rest)), absolute(href, src)
            if where and "house.gov" in url and not vacancy(url):
                rows.append((chamber, *where, html.unescape(name).strip(), url))
    else:
        for href, name, _party, st in SENATE_RE.findall(page):
            nm = re.sub(r"\s+", " ", html.unescape(name).replace("\xa0", " ")).strip()
            rows.append((chamber, st.upper(), "", nm, absolute(href, src)))
    return rows


def run(n: int, pause: float) -> None:
    frm, to = f"{2 * n + 1787}0103", min(f"{2 * n + 1789}0103", date.today().strftime("%Y%m%d"))
    seen: dict[tuple, list[str]] = {}
    for chamber, src in SOURCES:
        for ts in captures(src, frm, to, pause):
            rows = parse(chamber, src, replay(ts, src, pause))
            print(f"{n}th {chamber} {ts[:8]} {src}: {len(rows)} members", flush=True)
            for r in rows:
                seen.setdefault(r, []).append(ts[:8])
    out = OUT / f"directory-urls-{n}.tsv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["chamber", "state", "district", "name_listed", "url", "first_seen", "last_seen", "captures"])
        for (ch, st, d, nm, u), ts in sorted(seen.items()):
            w.writerow([ch, st, d, nm, u, min(ts), max(ts), len(ts)])
    print(f"{n}th: {len(seen)} listed URLs -> {out}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("congress", nargs="+", type=int)
    ap.add_argument("--pause", type=float, default=3.0)
    a = ap.parse_args()
    for n in a.congress:
        run(n, a.pause)


if __name__ == "__main__":
    main()
