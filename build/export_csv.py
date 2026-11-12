#!/usr/bin/env python3
"""Write one CSV of letters per Congress: the "Download data" file.

    python3 build/export_csv.py                 # every explorer under ../explorers/
    python3 build/export_csv.py 118 119         # just these

Run after build_congress.py and before build_hub.py, which links each file
from its Congress's card. Reads only the built explorers -- each one's
index.json and payload/member/*.json -- so the CSV says exactly what the
explorer shows, and a member's history is read across every explorer built.

Writes ``Explorer-Congressional-Letters-<N>/data/letters-from-congress-<N>th.csv``,
UTF-8 with a header row, one row per letter:

  congress            the Congress the letter falls in (each letter is in one)
  letter_date         ISO 8601, as precise as the source allows:
                      YYYY-MM-DD, or YYYY-MM when only the month is known
  date_basis          where the date came from (see DATE_BASIS)
  member_name, bioguide_id, chamber, state
  district            House only; "at-large" for a single-district state
  party               in this Congress; a switch reads
                      "Democrat -> Independent (2022-12-09)"
  party_history       every party, with the Congresses served under each
  seat_history        every seat (chamber, state, district), likewise
  congresses_served   each Congress, listed separately: "113; 114; 115"
  recipient           who the letter is to, where known
  topic_1..topic_3    the letter's first three topics from build/topics.py
  cosigners           other signers named in the file name (#41: a floor)
  subject             the description taken from the file name
  pdf_url             the PDF as the Wayback Machine serves it
  original_url        the address it was published at
  wayback_timestamp   the capture the link opens
  digest              the capture's CDX digest (SHA-1, base32)

The history columns cover only the Congresses built here, the 106th onwards:
a member who served before the 106th shows only from the 106th.

Written with a byte-order mark (utf-8-sig) so Excel reads the arrows and
accented names correctly; other tools ignore it. URLs are percent-encoded,
because file names on these sites carry spaces.
"""
from __future__ import annotations

import csv
import json
import re
import sys
import urllib.parse
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPLORERS = ROOT.parent / "explorers"

DATE_BASIS = {
    "day": "stated in the file name",
    "scanned": "stated in the PDF",
    "month": "month only, from the file name",
    "captured-by": "not stated; the letter is no later than this, its first archiving",
}

FIELDS = ["congress", "letter_date", "date_basis", "member_name", "bioguide_id",
          "chamber", "state", "district", "party", "party_history", "seat_history",
          "congresses_served", "recipient", "topic_1", "topic_2", "topic_3",
          "cosigners", "subject", "pdf_url", "original_url", "wayback_timestamp",
          "digest"]


def ordinal(n: int) -> str:
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def spans(numbers: list[int]) -> str:
    """[110, 111, 112, 115] -> '110th-112th, 115th'."""
    out, run = [], []
    for n in sorted(numbers):
        if run and n != run[-1] + 1:
            out.append(run)
            run = []
        run.append(n)
    if run:
        out.append(run)
    return ", ".join(ordinal(r[0]) if len(r) == 1 else f"{ordinal(r[0])}-{ordinal(r[-1])}"
                     for r in out)


def history(per_congress: dict[int, str]) -> str:
    """{113: 'A', 114: 'A', 116: 'B'} -> 'A: 113th-114th; B: 116th'."""
    by_value: dict[str, list[int]] = defaultdict(list)
    for n, value in sorted(per_congress.items()):
        by_value[value].append(n)
    order = sorted(by_value, key=lambda v: min(by_value[v]))
    return "; ".join(f"{v}: {spans(by_value[v])}" for v in order)


def district_of(m: dict) -> str:
    if m.get("chamber") != "rep":
        return ""
    d = m.get("district")
    return "at-large" if d in (0, "0") else ("" if d is None else str(d))


def seat_of(m: dict) -> str:
    if m.get("chamber") == "sen":
        return f"Senate {m.get('state', '')}"
    d = district_of(m)
    return f"House {m.get('state', '')}-{d}" if d else f"House {m.get('state', '')}"


def iso_date(date: str, precision: str) -> str:
    if not date:
        return ""
    return date[:7] if precision == "month" else date[:10]


def encoded(url: str) -> str:
    """Spaces and the like percent-encoded; existing %XX escapes kept."""
    return urllib.parse.quote(url, safe=":/?&=%#~+,;@!$'()*[]")


def split_list(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"[;,]", text or "") if p.strip()]


def main() -> int:
    wanted = {int(a) for a in sys.argv[1:] if a.isdigit()}
    explorers = {}
    for d in sorted(EXPLORERS.glob("Explorer-Congressional-Letters-*")):
        m = re.fullmatch(r"Explorer-Congressional-Letters-(\d+)", d.name)
        if m and (d / "index.json").exists():
            explorers[int(m.group(1))] = d
    if not explorers:
        sys.exit(f"no explorers under {EXPLORERS}")

    # Every member's party and seat in every Congress built, for the history
    # columns. Read from all explorers even when writing only some.
    parties: dict[str, dict[int, str]] = defaultdict(dict)
    seats: dict[str, dict[int, str]] = defaultdict(dict)
    indexes = {}
    for n, d in explorers.items():
        idx = json.loads((d / "index.json").read_text(encoding="utf-8"))
        indexes[n] = idx
        for m in idx["members"]:
            parties[m["id"]][n] = m.get("party") or ""
            seats[m["id"]][n] = seat_of(m)

    for n, d in sorted(explorers.items()):
        if wanted and n not in wanted:
            continue
        idx = indexes[n]
        col = {name: i for i, name in enumerate(idx["columns"])}
        rows = []
        for m in idx["members"]:
            path = d / idx.get("data_base", "payload/member/") / f"{m['id']}.json"
            if not m.get("letters") or not path.exists():
                continue
            common = {
                "congress": n, "member_name": m["name"], "bioguide_id": m["id"],
                "chamber": {"sen": "Senate", "rep": "House"}.get(m["chamber"], m["chamber"]),
                "state": m.get("state", ""), "district": district_of(m),
                "party": m.get("party", ""),
                "party_history": history(parties[m["id"]]),
                "seat_history": history(seats[m["id"]]),
                "congresses_served": "; ".join(str(c) for c in sorted(parties[m["id"]])),
            }
            for r in json.loads(path.read_text(encoding="utf-8")):
                topics = split_list(r[col["topics"]])[:3]
                key, ts, prec = r[col["key"]], r[col["timestamp"]], r[col["precision"]]
                rows.append({
                    **common,
                    "letter_date": iso_date(r[col["date"]], prec),
                    "date_basis": DATE_BASIS.get(prec, prec),
                    "recipient": r[col["recipient"]] or "",
                    "topic_1": topics[0] if topics else "",
                    "topic_2": topics[1] if len(topics) > 1 else "",
                    "topic_3": topics[2] if len(topics) > 2 else "",
                    "cosigners": "; ".join(split_list(r[col["cosigners"]])),
                    "subject": r[col["subject"]] or "",
                    "pdf_url": f"https://web.archive.org/web/{ts}id_/{encoded(key)}",
                    "original_url": encoded(key if "://" in key else f"https://{key}"),
                    "wayback_timestamp": ts,
                    "digest": r[col["digest"]] or "",
                })
        rows.sort(key=lambda r: (r["letter_date"], r["member_name"], r["original_url"]))
        out = d / "data" / f"letters-from-congress-{ordinal(n)}.csv"
        out.parent.mkdir(exist_ok=True)
        with out.open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
        if len(rows) != idx.get("letters"):
            print(f"  {ordinal(n)}: {len(rows):,} rows but index.json says "
                  f"{idx.get('letters'):,} letters", file=sys.stderr)
        print(f"{ordinal(n)}: {len(rows):,} letters, {out.stat().st_size / 1e6:.1f} MB -> {out}",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
