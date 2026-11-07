#!/usr/bin/env python3
"""Step 2 of the methodology: find each roster member's website in the Wayback Machine.

    python3 build/wayback_lookup.py 118          # one Congress
    python3 build/wayback_lookup.py              # every roster in data/rosters/
    python3 build/wayback_lookup.py 118 --limit 20   # trial -> congress118-wayback.trial.csv

Reads ``data/rosters/congressNNN-roster.csv`` and writes
``harvest/wayback/congressNNN-wayback.csv``: one row per member per URL, saying
whether the Wayback Machine holds that URL's home page **during the member's
own service in that Congress**, and if so the first and last capture.

Why the window matters
----------------------
Member hostnames are reused: ``jones.house.gov`` was Walter Jones's, then
Mondaire Jones's. An unbounded "last capture" lookup returned the later
member's site for the earlier one (issue #8). Every query here is bounded with
``from``/``to`` to the dates in ``served_this_congress``.

Two query shapes
----------------
* Host sites (``pelosi.house.gov``) are queried as the exact home page.
* Path sites (``www.house.gov/pelosi``), the usual House form through the
  2000s, are queried as that path's home page too. If the home page has no
  successful capture in the window, the lookup falls back to a prefix query
  over the path or host, which finds sites whose front page sat at
  ``index.html`` or similar. ``query`` in the output says which answered.

What it does not do
-------------------
No ``filter=`` and no negative ``limit`` are sent to CDX. Together they
returned captures years older than the true last one (Conaway's 2012 against a
real December 2020). Every row in the window comes back, collapsed to one per
day, and success is decided here: status 200 and an HTML MIME type.

Resumable: each answer is cached under ``harvest/wayback/cache/`` (ignored by
git), so a re-run asks Wayback only for what it does not already have. A query
that errors is not cached and is retried next run. Stdlib only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROSTERS = ROOT / "data" / "rosters"
OUT = ROOT / "harvest" / "wayback"
CACHE = OUT / "cache"
CDX = "https://web.archive.org/cdx/search/cdx"
UA = {"User-Agent": "ia-congressional-member-letters/0.1 "
                    "(Internet Archive; collections research)"}

COLUMNS = ["bioguide_id", "name", "chamber", "state", "district", "url",
           "window_from", "window_to", "query", "days_captured",
           "first_capture", "last_capture", "wayback_first", "wayback_last",
           "lookup", "checked_on"]


def target(url: str) -> tuple[str, bool]:
    """CDX target for a URL's home page, and whether the site is path-keyed."""
    p = urllib.parse.urlparse(url if "://" in url else "https://" + url)
    host = p.netloc.lower()
    path = p.path.strip("/")
    return (f"{host}/{path}/" if path else f"{host}/"), bool(path)


def cdx(params: dict, pause: float) -> list[list[str]] | None:
    """Rows of (timestamp, statuscode, mimetype), or None after repeated failure."""
    url = CDX + "?" + urllib.parse.urlencode(params)
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as r:
                body = r.read().decode("utf-8", "replace")
            time.sleep(pause)
            if "<html" in body[:500].lower():   # "Temporarily Offline" and friends
                raise RuntimeError("HTML in place of CDX")
            return [ln.split(" ") for ln in body.splitlines() if ln.strip()]
        except Exception as e:  # noqa: BLE001 -- any failure is a retry
            wait = pause * 4 * (attempt + 1)
            print(f"    retry {attempt + 1} in {wait:.0f}s: {e}", file=sys.stderr, flush=True)
            time.sleep(wait)
    return None


def cached(key: dict, pause: float) -> list | None:
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / (hashlib.sha1(json.dumps(key, sort_keys=True).encode()).hexdigest() + ".json")
    if f.exists():
        return json.loads(f.read_text())["rows"]
    rows = cdx(key, pause)
    if rows is not None:
        f.write_text(json.dumps({"query": key, "rows": rows}))
    return rows


def good(rows: list) -> list[str]:
    return sorted({r[0] for r in rows if len(r) >= 3 and r[1] == "200" and "html" in r[2]})


def lookup(url: str, start: str, end: str, pause: float) -> dict:
    tgt, path_keyed = target(url)
    frm, to = start.replace("-", ""), end.replace("-", "")
    base = {"fl": "timestamp,statuscode,mimetype", "from": frm, "to": to,
            "collapse": "timestamp:8"}
    rows = cached({**base, "url": tgt}, pause)
    if rows is None:
        return {"query": "home page", "lookup": "error"}
    ok, how = good(rows), "home page"
    if not ok:
        rows = cached({**base, "url": tgt, "matchType": "prefix", "limit": "5000"}, pause)
        if rows is None:
            return {"query": "prefix", "lookup": "error"}
        ok, how = good(rows), "prefix"
    if not ok:
        return {"query": how, "days_captured": 0, "lookup": "none in window"}
    days = sorted({t[:8] for t in ok})
    live = tgt.rstrip("/") + "/"
    return {"query": how, "days_captured": len(days),
            "first_capture": ok[0], "last_capture": ok[-1],
            "wayback_first": f"https://web.archive.org/web/{ok[0]}/{live}",
            "wayback_last": f"https://web.archive.org/web/{ok[-1]}/{live}",
            "lookup": "found"}


def run(n: int, limit: int | None, pause: float, only: set | None = None) -> None:
    src = ROSTERS / f"congress{n}-roster.csv"
    if not src.exists():
        print(f"{n}th: no roster at {src}; build it first (step 1)")
        return
    trial = bool(limit or only)
    out = OUT / f"congress{n}-wayback{'.trial' if trial else ''}.csv"
    rows = list(csv.DictReader(open(src, encoding="utf-8")))
    if only:
        rows = [r for r in rows if r["bioguide_id"] in only]
    rows = rows[:limit]
    today = date.today().isoformat()
    result, found = [], 0
    for i, r in enumerate(rows, 1):
        start, end = r["served_this_congress"].split(" to ")
        end = min(end, today)
        for url in [u.strip() for u in r["website_at_the_time"].split("|") if u.strip()] or [""]:
            rec = {k: r.get(k, "") for k in ("bioguide_id", "name", "chamber", "state", "district")}
            rec.update(url=url, window_from=start, window_to=end, checked_on=today)
            if not url:
                rec.update(lookup="no URL in roster")
            else:
                rec.update(lookup(url, start, end, pause))
            found += rec["lookup"] == "found"
            result.append(rec)
            print(f"[{n} {i}/{len(rows)}] {rec['lookup']:<15} {rec.get('days_captured', ''):>4} "
                  f"{url}  {rec['name']}", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(result)
    errors = sum(x["lookup"] == "error" for x in result)
    print(f"{n}th: {found} of {len(result)} found in window; {errors} errors -> {out}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("congress", nargs="*", type=int)
    ap.add_argument("--limit", type=int, help="first N roster rows only (trial)")
    ap.add_argument("--only", help="comma-separated bioguide IDs (trial)")
    ap.add_argument("--pause", type=float, default=3.0, help="seconds between CDX requests")
    a = ap.parse_args()
    ns = a.congress or sorted(int(re.search(r"\d+", p.name).group()) for p in ROSTERS.glob("congress*-roster.csv"))
    for n in ns:
        run(n, a.limit, a.pause, set(a.only.split(",")) if a.only else None)


if __name__ == "__main__":
    main()
