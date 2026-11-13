#!/usr/bin/env python3
"""Build one explorer per Congress (EXPLORERS.md step 7).

    python3 build/build_congress.py 110          # one Congress
    python3 build/build_congress.py 106-119      # a range
    python3 build/build_congress.py 106-119 --dry-run

For Congress N it writes a standalone explorer into
../explorers/Explorer-Congressional-Letters-N/ (index.html, app.js, index.json,
payload/), ready to become that repository's working copy.

Which letters (decided 2026-11-09): every letter whose date falls within N,
from 3 January of its first year to 3 January two years later, so each letter
appears in exactly one explorer. The date is the letter's own, then the PDF's,
then its first capture, the same order build_site.py uses.

Who gets each letter: address_holders.attribute(), at build time. Attributions
in address_holders.UNPUBLISHED (caucus) and "none" are left out, and so is a
letter credited to someone not on N's roster (EXPLORERS.md, open question:
former holders). Both are counted in index.json under "left_out".

Every member of N's roster is listed, with zero letters where none were found,
so an explorer exists and is correct before its harvest is: rebuilding it after
the harvest is what seeds it.

The page itself is build_site.py's, unchanged except that it reads which
Congress it is from index.json["congress"] instead of saying "119th".

Thumbnails are not copied. The page shows "preview coming soon" for each
missing one; --copy-thumbs copies the ones already rendered into the
explorer's thumbs/.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "build"))
import address_holders as ah  # noqa: E402

ROSTERS = ROOT / "data" / "rosters"
PARSED = [ROOT / "data" / "letters-parsed.jsonl",
          ROOT / "data" / "letters-119-departed-parsed.jsonl"]
PARSED_GLOB = "harvest/letters/letters-parsed-*.jsonl"
PDF_DATES = ROOT / "data" / "pdf-dates.jsonl"
THUMBS = ROOT / "thumbs"
# Beside the dev repository, not in it: each becomes a repository of its own.
OUT_ROOT = ROOT.parent / "explorers"
# The page and script every explorer is stamped from: 119th/index.html and app.js
# in this checkout. They were read from a local-only branch, iac-119th, which no PR
# could reach; on 12 November they moved onto the main line so fixes go through review.


def ordinal(n: int) -> str:
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def congress_of(day: str) -> int | None:
    """The Congress in session on an ISO date. Each begins 3 January."""
    if not day or len(day) < 4 or not day[:4].isdigit():
        return None
    year = int(day[:4])
    if day[5:10] and day[5:10] < "01-03":
        year -= 1
    return (year - 1787) // 2 if year >= 1789 else None


def bounds(n: int) -> tuple[str, str]:
    first = 2 * n + 1787
    return f"{first}-01-03", f"{first + 2}-01-03"


def human(day: str) -> str:
    y, m, d = day.split("-")
    months = ["January", "February", "March", "April", "May", "June", "July",
              "August", "September", "October", "November", "December"]
    return f"{months[int(m) - 1]} {int(d)}, {y}"


def roster_members(n: int) -> list[dict]:
    """N's roster in the shape build_site.py reads members.json in."""
    path = ROSTERS / f"congress{n}-roster.csv"
    start, end = bounds(n)
    out = []
    with path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            url = (row.get("website_at_the_time") or "").strip()
            host = re.sub(r"^https?://", "", url).split("/")[0] if url else ""
            served = row.get("served_this_congress") or ""
            m = re.findall(r"\d{4}-\d{2}-\d{2}", served)
            left = m[-1] if m and m[-1] < end else None
            in_office = (row.get("years_in_office") or "").strip()
            years = re.findall(r"\b(1[89]\d\d|20\d\d)\b", in_office)
            # WHEN THEIR SERVICE ENDED, NOT "present". A member who served to
            # the end of N and did not return has no "left" (that is for
            # leaving during N), so the page called Sherrod Brown "1993-present"
            # in the 118th. "years_in_office" ends in the last year or in
            # "present", and only a sitting member gets the second.
            until = (int(years[-1]) if years and not in_office.endswith("present")
                     else None)
            name = row["name"].strip()
            out.append({
                "bioguide": row["bioguide_id"],
                "name": name,
                "last": name.split()[-1] if name else "",
                "chamber": "sen" if row["chamber"].lower().startswith("sen") else "rep",
                "state": row["state"],
                "district": int(row["district"]) if (row.get("district") or "").isdigit() else None,
                "party": row.get("party") or "",
                "since": int(years[0]) if years else None,
                **({"left": left} if left else {}),
                **({"until": until} if until else {}),
                "host": host,
                "url": url,
            })
    # A member who served twice in one Congress appears twice; keep the first.
    seen, unique = set(), []
    for m in out:
        if m["bioguide"] not in seen:
            seen.add(m["bioguide"])
            unique.append(m)
    return unique


def pdf_dates() -> dict[str, str]:
    dates = {}
    if PDF_DATES.exists():
        for line in PDF_DATES.open(encoding="utf-8"):
            try:
                row = json.loads(line)
            except Exception:  # noqa: BLE001
                continue
            if row.get("digest") and row.get("date"):
                dates[row["digest"]] = row["date"]
    return dates


def all_letters():
    """Every parsed letter once, by key, from every harvest so far."""
    seen = set()
    for path in [*PARSED, *sorted(ROOT.glob(PARSED_GLOB))]:
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                rec = json.loads(line)
                if rec["key"] in seen:
                    continue
                seen.add(rec["key"])
                yield rec


def sort_letters(congresses: set[int]):
    """Each letter's Congress and holder, for the Congresses asked for."""
    idx = ah.index(ah.load())
    dates = pdf_dates()
    by_congress: dict[int, list] = {n: [] for n in congresses}
    flags: dict[int, Counter] = {n: Counter() for n in congresses}
    total = 0
    rosters: dict[int, set] = {}

    def on_roster(n: int, bioguide: str) -> bool:
        if n not in rosters:
            try:
                rosters[n] = {m["bioguide"] for m in roster_members(n)}
            except Exception:  # noqa: BLE001 - a Congress with no roster file
                rosters[n] = set()
        return bioguide in rosters[n]

    for rec in all_letters():
        total += 1
        own = rec.get("date") or dates.get(rec.get("digest") or "")
        a = ah.attribute(idx, rec["url"], own or "", rec.get("first_seen") or "")
        if own and (a.attribution == "none"
                    or not on_roster(congress_of(own), a.bioguide_id)):
            # A date nobody holding the address could have written the
            # letter on. From the PDF's metadata it is a template's creation
            # date: Cotton's blinken_letter1.pdf says 2008, five years before
            # he entered Congress, first captured 2023. From the filename it
            # is a misread: "1.08.07.20 letter to doj" read as 2007-01-08,
            # "letter-zone-7-23.03.24" as 2003-07-23. Either way the capture
            # bounds it, so the letter is placed and shown by its capture,
            # as one with no date would be, and says so ("captured by").
            b = ah.attribute(idx, rec["url"], "", rec.get("first_seen") or "")
            if b.attribution != "none":
                own, a = "", b
                rec = {**rec, "date": None, "date_best": rec.get("first_seen"),
                       "date_precision": "captured-by", "date_rejected": True}
        best = own or rec.get("date_best")
        n = congress_of(best or "")
        if n not in congresses:
            continue
        flags[n][a.attribution] += 1
        if a.attribution == "none" or a.attribution in ah.UNPUBLISHED:
            continue
        by_congress[n].append((a.bioguide_id, a.attribution, rec))
    return by_congress, flags, total


def page_files(n: int, dest: Path) -> None:
    """index.html and app.js from the template, made to say which Congress."""
    def show(path):
        return (ROOT / path).read_text(encoding="utf-8")

    def swap(text, old, new, label):
        if text.count(old) != 1:
            raise SystemExit(f"template changed: {label} found {text.count(old)} times")
        return text.replace(old, new)

    ordn = ordinal(n)
    start, end = bounds(n)
    short = f"{ordn} Congress ({start[:4]}-{str(int(start[:4]) + 1)[2:]})"

    html = show("119th/index.html")
    html = swap(html, 'title="All Congresses">119th Congress (2025-26)</a>',
                f'title="All Congresses">{short}</a>', "crumb")
    html = html.replace('src="../app.js?v=', 'src="app.js?v=')
    # "All Congresses" goes to Letters from Congress, Explorer-Letters (build_hub.py), which is
    # published beside the explorers: robin-ia.github.io/<repo>/ for each.
    html = swap(html, 'class="home" href="../?view=topics"',
                'class="home" href="../Explorer-Letters/?view=topics"', "home link")
    html = swap(html, 'class="crumb" href="../"',
                'class="crumb" href="../Explorer-Letters/"', "crumb link")
    # The 119th's name for itself. Each Congress's own label already says
    # which years it covers, so the per-Congress page drops "(2007-present)".
    html = swap(html, "<title>Letters from Congress (2007-present) ·",
                "<title>Letters from Congress ·", "head title")
    html = swap(html, "<span>Letters from Congress (2007-present)</span>",
                "<span>Letters from Congress</span>", "masthead")
    (dest / "index.html").write_text(html, encoding="utf-8")

    js = show("app.js")
    js = swap(js, "el('h1', { class: 'hero' }, '119th Congress (2025-26)'),",
              "el('h1', { class: 'hero' }, (INDEX.congress || {}).label || '119th Congress (2025-26)'),",
              "hero")
    js = swap(js, "el('p', { class: 'dates' }, 'January 3, 2025 – January 3, 2027'),",
              "el('p', { class: 'dates' }, (INDEX.congress || {}).dates || 'January 3, 2025 – January 3, 2027'),",
              "dates")
    js = swap(js, "      : '119th Congress (2025-26) · Letters",
              "      : `${(INDEX.congress || {}).label || '119th Congress (2025-26)'} · Letters",
              "title")
    js = swap(js, " · Letters from Congress (2007-present)';",
              " · Letters from Congress (2007-present)`;", "title close")
    js = swap(js, "`Only members of the 119th Congress.${",
              "`Only letters written during the ${(INDEX.congress || {}).ordinal || '119th'} Congress, by its members.${",
              "about")
    js = swap(js, "the 119th began are in the archive too",
              "the ${(INDEX.congress || {}).ordinal || '119th'} began are in the archive too",
              "about 2")
    js = swap(js, "const service = m => `${m.since}–${m.left ? m.left.slice(0, 4) : 'present'}`;",
              "const service = m => `${m.since}–${m.left ? m.left.slice(0, 4) : (m.until || 'present')}`;",
              "service years")
    if js.count("Letters from Congress (2007-present)") != 3:
        raise SystemExit("template changed: page-title suffix")
    js = js.replace("Letters from Congress (2007-present)", "Letters from Congress")
    (dest / "app.js").write_text(js, encoding="utf-8")


def build(n: int, letters: list, flags: Counter, args) -> dict:
    dest = OUT_ROOT / f"Explorer-Congressional-Letters-{n}"
    work = OUT_ROOT / ".work"
    work.mkdir(parents=True, exist_ok=True)
    members = roster_members(n)
    on_roster = {m["bioguide"] for m in members}

    kept, former = [], Counter()
    for bioguide, attribution, rec in letters:
        if bioguide not in on_roster:
            former[bioguide] += 1
            continue
        rec = dict(rec, bioguide=bioguide, attribution=attribution)
        kept.append(rec)

    start, end = bounds(n)
    summary = {"congress": n, "members": len(members), "letters": len(kept),
               "members_with_letters": len({r["bioguide"] for r in kept}),
               "former_holder_letters": sum(former.values()),
               "attributions": dict(flags)}
    if args.dry_run:
        return summary

    dest.mkdir(parents=True, exist_ok=True)
    (dest / "thumbs").mkdir(exist_ok=True)
    members_path = work / f"members-{n}.json"
    parsed_path = work / f"parsed-{n}.jsonl"
    members_path.write_text(json.dumps(members, ensure_ascii=False), encoding="utf-8")
    with parsed_path.open("w", encoding="utf-8") as sink:
        for rec in kept:
            sink.write(json.dumps(rec, ensure_ascii=False) + "\n")

    result = subprocess.run(
        [sys.executable, str(ROOT / "build" / "build_site.py"),
         "--parsed", str(parsed_path), "--members", str(members_path),
         "--out", str(dest), "--payload", str(dest / "payload"),
         "--thumbs", str(dest / "thumbs"), "--thumb-base", "thumbs/", "--force"],
        cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"build_site.py failed for {n}:\n{result.stderr[-2000:]}")

    index_path = dest / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    ordn = ordinal(n)
    index["congress"] = {
        "number": n, "ordinal": ordn,
        "label": f"{ordn} Congress ({start[:4]}-{str(int(start[:4]) + 1)[2:]})",
        "start": start, "end": end,
        "dates": f"{human(start)} – {human(end)}",
    }
    index["attributions"] = dict(Counter(r["attribution"] for r in kept))
    index["left_out"] = {"former_holders": sum(former.values()),
                         **{k: v for k, v in flags.items()
                            if k == "none" or k in ah.UNPUBLISHED}}
    index_path.write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")),
                          encoding="utf-8")
    page_files(n, dest)

    if args.copy_thumbs:
        (dest / "thumbs").mkdir(exist_ok=True)
        for rec in kept:
            src = THUMBS / f"{rec.get('digest')}.webp"
            if rec.get("digest") and src.exists():
                shutil.copy2(src, dest / "thumbs" / src.name)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("congresses", help="N or N-M, e.g. 110 or 106-119")
    parser.add_argument("--dry-run", action="store_true", help="count only, write nothing")
    parser.add_argument("--copy-thumbs", action="store_true",
                        help="copy already-rendered thumbnails into each explorer")
    args = parser.parse_args()
    a, _, b = args.congresses.partition("-")
    wanted = set(range(int(a), int(b or a) + 1))
    missing = [n for n in wanted if not (ROSTERS / f"congress{n}-roster.csv").exists()]
    if missing:
        raise SystemExit(f"no roster for {missing}; run build/congress_roster.py first")

    by_congress, flags, total = sort_letters(wanted)
    print(f"{total:,} letters read from every harvest so far", file=sys.stderr)
    print(f"{'Congress':<10}{'members':>8}{'with':>7}{'letters':>9}{'former':>8}",
          file=sys.stderr)
    for n in sorted(wanted):
        s = build(n, by_congress[n], flags[n], args)
        print(f"{ordinal(n):<10}{s['members']:>8}{s['members_with_letters']:>7}"
              f"{s['letters']:>9,}{s['former_holder_letters']:>8,}", file=sys.stderr)


if __name__ == "__main__":
    main()
