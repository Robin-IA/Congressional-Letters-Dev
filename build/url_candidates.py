#!/usr/bin/env python3
"""Candidate web addresses for every member of one Congress, for #111.

    python3 build/url_candidates.py 106
    python3 build/url_candidates.py 107 108 109

Writes ``data/url-candidates/congressNNN-url-candidates.csv``: one row per
(member, distinct address), so a member who used three addresses gets three
rows. ``is_congressional`` is left blank for the Wayback review to fill in.

Two sources are merged and named per row:

* ``unitedstates/congress-legislators`` -- every term's ``url``, for every term
  the member ever served, not only the ones inside this Congress. An address a
  member used in the next Congress may still hold letters from this one.
* that Congress's roster -- ``website_at_the_time``, which carries addresses
  derived from Wayback evidence that the dataset itself does not hold (the
  ``senate.gov/~name`` forms, for instance).

Addresses are normalised on host+path before being called distinct: scheme,
``www.`` and a trailing slash are not differences. The raw spellings are kept
in ``variants`` so nothing is lost.

A term that shares only its first or last day with the Congress is not counted
as service in it: a term ending on the day a Congress opens is the previous
Congress's.

Stdlib only.
"""
from __future__ import annotations

import csv
import json
import sys
import urllib.parse
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "cdx-cache"
OUT = ROOT / "data" / "url-candidates"

# A Congress runs from 3 January of an odd year for two years.
def span(n: int) -> tuple[str, str]:
    start = 1789 + (n - 1) * 2
    return f"{start}-01-03", f"{start + 2}-01-03"


def normalise(url: str) -> str:
    parts = urllib.parse.urlsplit(url if "://" in url else "http://" + url)
    return parts.netloc.lower().removeprefix("www.") + parts.path.rstrip("/")


def form(url: str) -> str:
    parts = urllib.parse.urlsplit(url if "://" in url else "http://" + url)
    host, path = parts.netloc.lower(), parts.path
    if "~" in path:
        return "tilde"
    if host in ("www.house.gov", "house.gov", "www.senate.gov", "senate.gov") and path.strip("/"):
        return "path"
    if host.endswith(".house.gov") or host.endswith(".senate.gov"):
        return "subdomain"
    if host.endswith(".gov"):
        return "other-gov"
    return "non-gov"


def explorer_hosts() -> set[str]:
    path = ROOT / "data" / "member-sites.tsv"
    if not path.exists():
        return set()
    with path.open(encoding="utf-8") as handle:
        return {(row.get("host") or "").strip().lower()
                for row in csv.DictReader(handle, delimiter="\t")
                if (row.get("in_explorer") or "").strip() == "yes"}


def people() -> list[dict]:
    out = []
    for name in ("legislators-historical.json", "legislators-current.json"):
        path = CACHE / name
        if path.exists():
            out += json.loads(path.read_text(encoding="utf-8"))
    if not out:
        sys.exit(f"no legislators JSON in {CACHE}")
    return out


def build(n: int) -> Path:
    start, end = span(n)
    served = lambda t: max(t.get("start") or "", start) < min(t.get("end") or "", end)

    candidates: dict[str, dict] = defaultdict(dict)
    info: dict[str, tuple] = {}
    for person in people():
        terms = person.get("terms", [])
        here = [t for t in terms if served(t)]
        if not here:
            continue
        bioguide = person["id"].get("bioguide", "")
        info[bioguide] = (
            f"{person['name'].get('first','')} {person['name'].get('last','')}".strip(),
            here[0].get("party", ""), here[0].get("state", ""),
            "House" if here[0].get("type") == "rep" else "Senate",
            f"{min(t.get('start','') for t in terms)[:4]}-{max(t.get('end','') for t in terms)[:4]}",
            person["id"].get("wikipedia", ""),
        )
        for term in terms:
            url = (term.get("url") or "").strip()
            if not url:
                continue
            entry = candidates[bioguide].setdefault(
                normalise(url), {"src": set(), "years": set(), "variants": set()})
            entry["src"].add("congress-legislators")
            entry["variants"].add(url)
            entry["years"].add(f"{term.get('start','')[:4]}-{term.get('end','')[:4]}")

    roster = ROOT / "data" / "rosters" / f"congress{n}-roster.csv"
    if roster.exists():
        with roster.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                bioguide = row["bioguide_id"]
                if not bioguide or bioguide not in info:
                    continue
                for url in [u.strip() for u in (row.get("website_at_the_time") or "").split("|") if u.strip()]:
                    entry = candidates[bioguide].setdefault(
                        normalise(url), {"src": set(), "years": set(), "variants": set()})
                    entry["src"].add(f"roster-{n}")
                    entry["variants"].add(url)
                    entry["years"].add(f"{start[:4]}-{end[:4]}")

    live = explorer_hosts()
    fields = ["name", "party", "state", "chamber", "years_active", "bioguide", "congress",
              "url", "url_form", "url_term_years", "source", "is_congressional",
              "in_explorer", "wikipedia", "variants", "notes"]
    rows = []
    for bioguide, (name, party, state, chamber, years, wiki) in sorted(
            info.items(), key=lambda kv: kv[1][0]):
        found = candidates.get(bioguide, {})
        if not found:
            rows.append(dict(zip(fields, [name, party, state, chamber, years, bioguide, n,
                                          "", "", "", "", "", "no", wiki, "",
                                          "NO URL IN ANY SOURCE - needs web research"])))
            continue
        for key, entry in sorted(found.items()):
            best = sorted(entry["variants"],
                          key=lambda u: (0 if u.startswith("https") else 1, len(u)))[0]
            rows.append(dict(zip(fields, [
                name, party, state, chamber, years, bioguide, n,
                best, form(best), "; ".join(sorted(entry["years"])),
                " + ".join(sorted(entry["src"])), "",
                "yes" if key.split("/")[0] in live else "no", wiki,
                " | ".join(sorted(entry["variants"])) if len(entry["variants"]) > 1 else "", ""])))

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"congress{n}-url-candidates.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    with_url = [r for r in rows if r["url"]]
    forms = defaultdict(int)
    for row in with_url:
        forms[row["url_form"]] += 1
    print(f"{n}th: {len(info)} members, {len(rows)} rows ({len(with_url)} with a URL), "
          f"{sum(1 for v in candidates.values() if len(v) > 1)} members with >1 address, "
          f"{sum(1 for r in with_url if r['in_explorer']=='no')} addresses not in the explorer")
    print(f"      forms: {dict(forms)}")
    print(f"      -> {path}")
    return path


if __name__ == "__main__":
    for arg in sys.argv[1:] or ["106"]:
        build(int(arg))
