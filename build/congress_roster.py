#!/usr/bin/env python3
"""Step 1 of the methodology: one roster per Congress.

    python3 build/congress_roster.py                 # add missing rosters, refresh the sitting Congress
    python3 build/congress_roster.py 120             # add the 120th
    python3 build/congress_roster.py --source-dir D  # read the legislators JSON from D

**Rosters are built once and then added to, not rebuilt.** A finished
Congress's roster is never rewritten: the script skips any closed Congress
whose file already exists, and says so. Only the Congress still sitting is
refreshed, because members still join and leave it. ``--rebuild`` overrides
that, for correcting a known error in a closed roster.

Writes ``data/rosters/congressNNN-roster.csv``: one row per member who served
**any part** of that Congress -- including those who joined, resigned, died or
were appointed partway through -- with party, state, chamber, district, the
website URL recorded for them at the time, and how long they served.

The URL is recorded in whatever form the source gives it. Through the 2000s
most representatives were at ``www.house.gov/<name>`` rather than on a
subdomain; that form is kept as-is, because the next step looks each URL up in
the Wayback Machine and needs it exactly as it was published.

Source: ``unitedstates/congress-legislators`` (current + historical), which
records each term's start and end date, party affiliations, and ``url``.
Stdlib only. See METHODOLOGY.md.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
import urllib.request
from collections import Counter
from datetime import date
from pathlib import Path

BASE = "https://unitedstates.github.io/congress-legislators/"
FILES = ("legislators-current.json", "legislators-historical.json")
UA = {"User-Agent": "ia-congressional-member-letters/0.1 "
                    "(Internet Archive; collections research)"}
OUT = Path(__file__).resolve().parent.parent / "data" / "rosters"

# Members the source records with no URL for a term, filled from Wayback evidence.
# Each says how it was established, and the note is carried into the row.
URL_OVERRIDES = {
    "Connie Conway": ("https://conway.house.gov",
                      "URL not in dataset; Wayback captures of conway.house.gov span "
                      "2022-06 to 2023-01, matching her tenure"),
    "Joseph Sempolinski": ("https://sempolinski.house.gov",
                           "URL not in dataset; Wayback captures span 2022-09 to 2022-12, "
                           "matching his tenure"),
    "Mayra Flores": ("https://flores.house.gov",
                     "URL not in dataset; inferred: flores.house.gov captures resume "
                     "2022-06-23, two days after she was sworn in (formerly Bill Flores's site)"),
    "Brenda Jones": ("https://brendajones.house.gov",
                     "URL not in dataset; Wayback captures of brendajones.house.gov date "
                     "from 2018-12, during her tenure"),
    "Erica Lee Carter": ("https://ericaleecarter.house.gov",
                         "URL not in dataset; Wayback captures span 2024-11 to 2024-12"),
}

# Source URLs that are wrong for a term, keyed (bioguide, Congress). The House's
# own member directory for that Congress is the evidence; the note is carried.
_W = "URL corrected: the dataset records {}; the House member directory lists {} for this seat"
URL_CORRECTIONS = {
    # the two Weldons: Dave (FL-15) was given Curt's (PA-7) site
    ("W000267", 108): ("https://www.house.gov/weldon",
                       _W.format("www.house.gov/curtweldon, Curt Weldon's site", "www.house.gov/weldon 2003-02–2005-01")),
    ("W000267", 109): ("https://www.house.gov/weldon | https://weldon.house.gov",
                       _W.format("www.house.gov/curtweldon, Curt Weldon's site",
                                 "www.house.gov/weldon 2005-01, then weldon.house.gov 2005-04–2006-12")),
    # curtweldon.house.gov is first listed in 2005-04
    ("W000268", 108): ("https://www.house.gov/curtweldon",
                       _W.format("curtweldon.house.gov, which it first lists in 2005", "www.house.gov/curtweldon 2003-02–2005-01")),
}

COLUMNS = ["name", "bioguide_id", "party", "state", "chamber", "district",
           "website_at_the_time", "served_this_congress", "days_this_congress",
           "full_or_partial", "service_notes", "years_in_office",
           "total_years_in_congress"]


def bounds(n: int) -> tuple[str, str]:
    """Constitutional start and end of the nth Congress (20th Amendment, 1935 on)."""
    return f"{2 * n + 1787}-01-03", f"{2 * n + 1789}-01-03"


def norm(u: str | None) -> str:
    return (u or "").rstrip("/").replace("http://", "https://")


def days(a: str, b: str) -> int:
    return (date.fromisoformat(b) - date.fromisoformat(a)).days


def chamber(t: str) -> str:
    return "Senate" if t == "sen" else "House"


def load(source_dir: Path | None) -> tuple[list, list]:
    out = []
    for f in FILES:
        if source_dir:
            out.append(json.loads((source_dir / f).read_text(encoding="utf-8")))
        else:
            req = urllib.request.Request(BASE + f, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as r:
                out.append(json.loads(r.read()))
    return out[0], out[1]


def periods(terms: list) -> list:
    """Merge contiguous terms into service periods per chamber (gap <= 120 days)."""
    out = []
    for t in terms:
        if (out and out[-1][0] == t["type"]
                and days(out[-1][2], t["start"]) <= 120):
            out[-1][2] = max(out[-1][2], t["end"])
        else:
            out.append([t["type"], t["start"], t["end"]])
    return out


def career_days(terms: list, today: str) -> int:
    iv = sorted((t["start"], min(t["end"], today)) for t in terms if t["start"] <= today)
    merged: list = []
    for a, b in iv:
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return sum(days(a, b) for a, b in merged)


def fold(s: str) -> str:
    return re.sub(r"[^a-z]", "", unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower())


def directory(n: int) -> list[dict]:
    """URLs the chambers listed during this Congress (build/directory_urls.py), if read."""
    f = OUT / f"directory-urls-{n}.tsv"
    return list(csv.DictReader(open(f, encoding="utf-8"), delimiter="\t")) if f.exists() else []


def seat_listings(listed: list[dict], p: dict, t: dict) -> dict[str, tuple[str, str]]:
    """{url: (first_seen, last_seen)} the directory listed for this member's seat and surname."""
    ch = chamber(t["type"])
    # any part of a compound surname: listed as "Mary Bono", recorded as "Bono Mack"
    parts = [fold(x) for x in re.split(r"[\s-]+", p["name"]["last"]) if len(fold(x)) >= 2]
    out: dict[str, tuple[str, str]] = {}
    for d in listed:
        if (d["chamber"] == ch and d["state"] == t["state"]
                and (ch == "Senate" or d["district"] == str(t.get("district", "")))
                and any(x in fold(d["name_listed"]) for x in parts)):
            a, b = out.get(d["url"], (d["first_seen"], d["last_seen"]))
            out[d["url"]] = (min(a, d["first_seen"]), max(b, d["last_seen"]))
    return out


def from_directory(listed: list[dict], p: dict, t: dict) -> tuple[str, str]:
    """The URL(s) a chamber directory listed for this member's seat and surname."""
    ch = chamber(t["type"])
    hits = {u: {"first_seen": a, "last_seen": b} for u, (a, b) in seat_listings(listed, p, t).items()}
    if not hits:
        return "", ""
    first = min(d["first_seen"] for d in hits.values())
    last_ = max(d["last_seen"] for d in hits.values())
    when = first if first == last_ else f"{first}–{last_}"
    urls = sorted(hits, key=lambda u: hits[u]["first_seen"])     # a site that moved: both, in order
    return " | ".join(urls), f"URL not in dataset; listed in the {ch} member directory as archived {when}"


def same_site(a: str, b: str) -> bool:
    """https://www.house.gov/pombo/pombo.htm and https://house.gov/pombo are one site."""
    k = lambda u: re.sub(r"^https?://(www\.)?", "", u.lower()).rstrip("/")
    a, b = k(a), k(b)
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def also_listed(listed: list[dict], p: dict, t: dict, urls: list) -> tuple[list, str]:
    """Directory URLs for this seat and surname that the source's URLs do not cover.

    A member's site often moved within a Congress -- www.house.gov/name to
    name.house.gov, www.senate.gov/~name to name.senate.gov -- and the source
    records one address. Letters were published at whichever was live, so both
    are kept and looked up (issue #16).
    """
    hits = seat_listings(listed, p, t)
    extra: list = []
    for x in sorted(hits, key=lambda x: hits[x][0]):       # hayes.house.gov = www.hayes.house.gov
        if not any(same_site(x, s) for s in urls + extra):
            extra.append(x)
    if not extra:
        return [], ""
    when = "; ".join(f"{x} as archived {a}" + (f"–{b}" if b != a else "")
                     for x in extra for a, b in [hits[x]])
    return extra, (f"URL changed during this Congress: the {chamber(t['type'])} member directory "
                   f"also lists {when}")


def roster(n: int, cur: list, hist: list, today: str) -> list[dict]:
    S, E = bounds(n)
    listed = directory(n)
    curids = {p["id"]["bioguide"] for p in cur}
    # The day this Congress actually convened: the most common term start in it.
    convened = Counter(t["start"] for p in cur + hist for t in p["terms"]
                       if S <= t["start"] < E).most_common(1)[0][0]
    rows = []
    for p in cur + hist:
        ts = [t for t in p["terms"] if t["start"] < E and t["end"] > S]
        if not ts:
            continue
        bid = p["id"]["bioguide"]
        first, tl = ts[0], ts[-1]
        later = [t for t in p["terms"] if t["start"] >= E]
        last = p["terms"][-1]
        nm = p["name"].get("official_full") or f"{p['name']['first']} {p['name']['last']}"

        # party within this Congress, with any switch dated
        parties: list = []
        for t in ts:
            for a in t.get("party_affiliations",
                           [{"start": t["start"], "end": t["end"], "party": t.get("party", "")}]):
                if a["start"] < E and a["end"] > S and (not parties or parties[-1][0] != a["party"]):
                    parties.append((a["party"], max(a["start"], S)))
        party = parties[0][0] + "".join(f" → {pa} ({d})" for pa, d in parties[1:])

        per = periods(p["terms"])
        yrs = "; ".join(
            f"{chamber(t)} {s[:4]}–{'present' if (bid in curids and [t, s, e] == per[-1]) else e[:4]}"
            for t, s, e in per)

        # the URL(s) recorded on this Congress's terms, in source form
        urls: list = []
        for t in ts:
            u = norm(t.get("url"))
            if u and u not in urls:
                urls.append(u)
        src = ""
        if (bid, n) in URL_CORRECTIONS:
            u, src = URL_CORRECTIONS[(bid, n)]
            urls = u.split(" | ")
        if not urls and nm in URL_OVERRIDES:
            urls, src = [URL_OVERRIDES[nm][0]], URL_OVERRIDES[nm][1]
        if not urls and listed:
            u, why = from_directory(listed, p, tl)
            if u:
                urls, src = u.split(" | "), why
        if not urls and later and later[0].get("url"):
            urls, src = [norm(later[0]["url"])], "URL not in dataset for this term; taken from next term"
        if urls and listed:
            extra, why = also_listed(listed, p, tl, urls)
            if extra:
                urls += extra
                src = "; ".join(x for x in (src, why) if x)

        st, en = max(first["start"], S), min(tl["end"], E)
        svc = []
        if days(convened, st) > 2:
            svc.append(f"joined {st}")
        if len({t["type"] for t in ts}) > 1:
            svc.append(f"switched chamber {tl['start']}")
        appointed_pending = en < E and bid in curids and tl.get("how") == "appointment"
        if appointed_pending:
            svc.append(f"appointed; appointment ran to {en} (special election), "
                       "result not yet in source data")
        elif en < E:
            svc.append(f"left {en} (during this Congress)")
        elif tl["end"] > E:          # senator mid-term
            if bid not in curids:
                svc.append(f"left Congress {last['end']}")
        elif not later:
            if E <= today:           # nothing to say while this Congress is sitting
                svc.append("did not return in next Congress")
        elif bid not in curids:
            svc.append(f"left Congress {last['end']}")
        if (later and tl["type"] == "rep" and later[0]["type"] == "rep"
                and later[0].get("district") != tl.get("district")):
            svc.append(f"district {tl.get('district')}→{later[0].get('district')} in next Congress")
        if src:
            svc.append(src)

        partial = days(convened, st) > 2 or en < E
        rows.append({
            "name": nm, "bioguide_id": bid, "party": party, "state": tl["state"],
            "chamber": chamber(tl["type"]),
            "district": tl.get("district") if tl["type"] == "rep" else "",
            "website_at_the_time": " | ".join(urls),
            "served_this_congress": f"{st} to {en}",
            "days_this_congress": days(st, min(en, today)),
            "full_or_partial": "partial" if partial else ("full" if en <= today else "full (in progress)"),
            "service_notes": "; ".join(svc),
            "years_in_office": yrs,
            "total_years_in_congress": f"{career_days(p['terms'], today) / 365.25:.1f}",
        })
    rows.sort(key=lambda r: (r["chamber"] != "Senate", r["state"], int(r["district"] or 0), r["name"]))
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("congress", nargs="*", type=int,
                    help="Congress numbers; default: 110th to the sitting Congress")
    ap.add_argument("--source-dir", type=Path, help="read the two legislators JSON files from here")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--rebuild", action="store_true",
                    help="rewrite closed Congresses' rosters that already exist")
    a = ap.parse_args()
    today = date.today().isoformat()
    sitting = next(n for n in range(110, 200) if bounds(n)[0] <= today < bounds(n)[1])
    todo = []
    for n in a.congress or range(110, sitting + 1):
        path = a.out / f"congress{n}-roster.csv"
        if path.exists() and bounds(n)[1] <= today and not a.rebuild:
            print(f"{n}th: closed, roster exists; left as is (--rebuild to rewrite)")
        else:
            todo.append(n)
    if not todo:
        return
    cur, hist = load(a.source_dir)
    a.out.mkdir(parents=True, exist_ok=True)
    for n in todo:
        rows = roster(n, cur, hist, today)
        with open(a.out / f"congress{n}-roster.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, COLUMNS, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
        c = Counter(r["chamber"] for r in rows)
        print(f"{n}th: {len(rows)} members (Senate {c['Senate']}, House {c['House']}), "
              f"{sum(r['full_or_partial'] == 'partial' for r in rows)} partial, "
              f"{sum(not r['website_at_the_time'] for r in rows)} with no URL")


if __name__ == "__main__":
    main()
