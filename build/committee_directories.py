#!/usr/bin/env python3
"""Committee websites as the chambers listed them, Congress by Congress (#23).

    python3 build/committee_directories.py 106 107 ...   # -> data/rosters/committee-directory-NNN.tsv

congress-legislators gives addresses for current committees only
(``committee_sites.py``). For the 106th-118th the addresses come from the
chambers' own committee directories, read in the Wayback Machine one capture
a quarter across each Congress, as ``directory_urls.py`` does for members:

* House: ``www.house.gov/house/CommitteeWWW.html`` (.shtml) until 2011, then
  ``www.house.gov/committees/``.
* Senate: ``www.senate.gov/committees/committees_home.htm`` and the CMS
  layout ``www.senate.gov/pagelayout/committees/d_three_sections_with_teasers/committees_home.htm``.

Every link from a directory to a committee-looking site is kept with the name
it was listed under and the dates it was seen. A link is kept when it leaves
the directory for a committee host (``<x>.house.gov``, ``<x>.senate.gov``,
``jec.senate.gov``, ``csce.gov``, ``jct.gov``) or a committee path on
``www.house.gov`` / ``www.senate.gov``, and its anchor names a committee,
commission or caucus, or matches a committee name congress-legislators gives
for that Congress. ``committee_sites.py`` merges the result.

**This touches Wayback.** The Wayback rule (MAC-READING.md) applies: it runs
as one worker, pausing 4.5 s between requests by default, and doubles the
pause after a 429 or 503. Check nothing else holds the two workers first.
Replays are cached under ``harvest/directories/cache/`` (shared with
``directory_urls.py``; ignored by git), so a re-run costs only CDX listings.
Stdlib only.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
import urllib.parse
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import directory_urls as du  # noqa: E402  get(), captures(), replay() and the UA

ROOT = du.ROOT
OUT = ROOT / "data" / "rosters"
LEG = ROOT / "data" / "legislators"

SOURCES = [
    ("House", "www.house.gov/house/CommitteeWWW.html"),
    ("House", "www.house.gov/house/CommitteeWWW.shtml"),
    ("House", "www.house.gov/committees/"),
    ("Senate", "www.senate.gov/committees/committees_home.htm"),
    ("Senate", "www.senate.gov/pagelayout/committees/d_three_sections_with_teasers/committees_home.htm"),
]

A_RE = re.compile(r'<a\s[^>]*?href\s*=\s*["\']?([^"\'\s>]+)["\']?[^>]*>(.*?)</a>', re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")
WORD_RE = re.compile(r"committee|commission|caucus|subcommittee|select|joint", re.I)
JOINT_HOSTS = ("jec.senate.gov", "www.jec.senate.gov", "csce.gov", "www.csce.gov", "jct.gov", "www.jct.gov")
# paths on the chambers' own hosts that are navigation, never a committee's site
NAV = re.compile(r"^(house|committees?|senators?|legislative|reference|art_history|pagelayout|"
                 r"general|visiting|index|search|representatives|leadership|"
                 r"[^/]+\.(?:htm|html|shtml|cfm|asp|pdf))(/|$)", re.I)
MEMBER_HOST = re.compile(r"^(www\.)?(house|senate)\.gov$", re.I)


def norm(s: str) -> str:
    s = re.sub(r"\b(house|senate|committee|on|the|of|and|select|permanent|special|u\.?s\.?)\b", " ", s.lower())
    return " ".join(re.findall(r"[a-z]+", s))


def known_names(n: int) -> dict[str, tuple[str, str, str]]:
    """normalized name -> (chamber, name, thomas_id) for committees sitting in Congress n."""
    out = {}
    for fn in ("committees-historical.json", "committees-current.json"):
        p = LEG / fn
        if not p.exists():
            continue
        for c in json.loads(p.read_text(encoding="utf-8")):
            cong = [int(x) for x in c.get("congresses", [])]
            if fn.endswith("current.json") or n in cong:
                chamber = {"house": "House", "senate": "Senate", "joint": "Joint"}.get(c["type"], c["type"])
                for nm in [c["name"], *(c.get("names") or {}).values()]:
                    out.setdefault(norm(nm), (chamber, c["name"], c.get("thomas_id", "")))
    return out


def site(href: str, src: str) -> str | None:
    """The committee site a directory link points to, or None when it is not one."""
    u = urllib.parse.urljoin(f"http://{src}", html.unescape(href.strip()))
    p = urllib.parse.urlparse(u)
    host, path = p.netloc.lower().split(":")[0], p.path.strip("/")
    if p.scheme not in ("http", "https") or not host:
        return None
    if host in JOINT_HOSTS:
        return f"https://{host}"
    if MEMBER_HOST.match(host):                       # www.house.gov/<committee>/
        first = path.split("/")[0]
        if not first or NAV.match(path) or first.startswith("~"):
            return None
        return f"https://{host}/{first}"
    if host.endswith(".house.gov") or host.endswith(".senate.gov"):
        if host.split(".")[0] in ("clerk", "www", "majorityleader", "democraticleader", "republicanleader",
                                  "speaker", "kids", "bioguide", "thomas", "democrats", "republicans",
                                  "gop", "dems", "chaplain", "history", "oig", "cao", "uscode", "docs",
                                  "legcounsel", "lrc", "pressgallery", "periodicalpress"):
            return None
        return f"https://{host}"
    return None


def parse(src: str, page: str, names: dict) -> list[tuple[str, str, str, str]]:
    rows = []
    for href, inner in A_RE.findall(page):
        url = site(href, src)
        if not url:
            continue
        text = re.sub(r"\s+", " ", html.unescape(TAG_RE.sub(" ", inner))).strip()
        hit = names.get(norm(text))
        if not (hit or WORD_RE.search(text)):
            continue
        rows.append((text, url, hit[2] if hit else "", hit[1] if hit else ""))
    return rows


def run(n: int, pause: float) -> None:
    frm, to = f"{2 * n + 1787}0103", min(f"{2 * n + 1789}0103", date.today().strftime("%Y%m%d"))
    names = known_names(n)
    seen: dict[tuple, list[str]] = {}
    for chamber, src in SOURCES:
        for ts in du.captures(src, frm, to, pause):
            rows = parse(src, du.replay(ts, src, pause), names)
            print(f"{n}th {chamber} {ts[:8]} {src}: {len(rows)} committee links", flush=True)
            for text, url, tid, cname in rows:
                seen.setdefault((chamber, tid, cname, text, url), []).append(ts[:8])
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"committee-directory-{n}.tsv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["listed_in", "thomas_id", "committee", "name_listed", "url", "first_seen", "last_seen", "captures"])
        for (ch, tid, cname, text, url), ts in sorted(seen.items()):
            w.writerow([ch, tid, cname, text, url, min(ts), max(ts), len(ts)])
    print(f"{n}th: {len(seen)} listed committee links -> {out}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("congress", nargs="+", type=int)
    ap.add_argument("--pause", type=float, default=4.5, help="seconds between Wayback requests (rule: 4-5)")
    a = ap.parse_args()
    for n in a.congress:
        if not 106 <= n <= 119:
            ap.error(f"{n}: the project covers the 106th-119th")
        run(n, a.pause)


if __name__ == "__main__":
    main()
