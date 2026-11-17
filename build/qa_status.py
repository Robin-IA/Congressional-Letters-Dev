#!/usr/bin/env python3
"""QA status CSVs: one per Congress, one row per posting (QA-Analysis-methodology).

    python3 build/qa_status.py [--out DIR] [--congress 106-119]

Run after build_congress.py, which writes the explorers this reads. Writes
<DIR>/<N>th.csv (default: the letters-from-congress-OCR checkout's qa-status/)
with the columns Robin set on 17 November 2026:

  Congress, Letter URL, Letter name (original), Discarded, Letter Name Fix,
  Authors, Subjects, Dates, Recipients, OCR, Filed?, Issue

Filed? is one of:
  Filed         read and recorded (a discarded posting is Filed with Discarded=Y)
  Hold          waiting on a vocabulary term (letters-vocabulary-needs)
  Needs Review  read but short of a requirement (fewer than 4 subjects), or set
                aside as partial, bundled or unreadable (build/mac/skip.txt)
  Unprocessed   not yet read
Issue is Y when an issue is recorded against the letter: a hold's issue, a
discard's issue, a set-aside (#252, #1226), or an issue number in its reviewed
note.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPLORERS = ROOT.parent / "explorers"
OCR_REPO = ROOT.parent / "letters-from-congress-OCR"
COLUMNS = ["Congress", "Letter URL", "Letter name (original)", "Discarded", "Letter Name Fix",
           "Authors", "Subjects", "Dates", "Recipients", "OCR", "Filed?", "Issue"]


def rows_of(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, default=OCR_REPO / "qa-status")
    ap.add_argument("--congress", default="106-119")
    args = ap.parse_args()
    lo, _, hi = args.congress.partition("-")
    congresses = range(int(lo), int(hi or lo) + 1)

    titles = {r["digest"]: r["title"] for r in rows_of(ROOT / "vocabulary/letter-titles.csv")}
    reviewed = {r["digest"]: r for r in rows_of(ROOT / "vocabulary/letters-reviewed.csv")}
    topics = {r["digest"]: [t for t in r["topics"].split(";") if t]
              for r in rows_of(ROOT / "vocabulary/letter-topics.csv")}
    recipients = {r["digest"]: r["recipient"] for r in rows_of(ROOT / "vocabulary/letter-recipients.csv")}
    discarded = {r["digest"]: r for r in rows_of(ROOT / "letters-discarded/letters.csv")}
    held = {r["digest"]: r for r in rows_of(ROOT / "letters-vocabulary-needs/letters.csv")}
    skip = set((ROOT / "build/mac/skip.txt").read_text().split()) if (ROOT / "build/mac/skip.txt").exists() else set()
    ocr = {r["digest"]: r["ocr"] == "True" for r in rows_of(OCR_REPO / "progress.csv")}

    args.out.mkdir(parents=True, exist_ok=True)
    totals = {}
    for n in congresses:
        ex = EXPLORERS / f"Explorer-Congressional-Letters-{n}"
        if not (ex / "index.json").exists():
            continue
        names = {m["id"]: m.get("name", m["id"]) for m in json.load(open(ex / "index.json")).get("members", [])}
        out_rows = []
        for f in sorted(glob.glob(str(ex / "payload/member/*.json"))):
            mid = Path(f).stem
            for row in json.load(open(f)):
                key, ts, _kind, date, _prec, recipient, _subject, tops, cosigners, digest, url = row[:11]
                authors = [names.get(mid, mid)] + [c for c in (cosigners or "").split(",") if c]
                subj = list(dict.fromkeys([t for t in (tops or "").split(",") if t] + topics.get(digest, [])))
                rec = recipients.get(digest) or recipient or ""
                if digest in discarded:
                    status = "Filed"
                elif digest in held:
                    status = "Hold"
                elif digest in skip:
                    status = "Needs Review"
                elif digest in reviewed:
                    n_subj = len(set(topics.get(digest, [])) | ({rec} if rec and rec != "(no recipient)" else set()))
                    status = "Filed" if n_subj >= 4 else "Needs Review"
                else:
                    status = "Unprocessed"
                note = (reviewed.get(digest) or {}).get("note", "")
                issue = bool((held.get(digest) or {}).get("issue") or (discarded.get(digest) or {}).get("issue")
                             or digest in skip or re.search(r"#\d{2,}", note))
                out_rows.append({
                    "Congress": n,
                    "Letter URL": f"https://web.archive.org/web/{ts}id_/{url or key}",
                    "Letter name (original)": (url or key).rstrip("/").split("/")[-1],
                    "Discarded": "Y" if digest in discarded else "N",
                    "Letter Name Fix": titles.get(digest, ""),
                    "Authors": ";".join(dict.fromkeys(authors)),
                    "Subjects": ";".join(subj),
                    "Dates": date or "",
                    "Recipients": rec,
                    "OCR": "Y" if ocr.get(digest) else "N",
                    "Filed?": status,
                    "Issue": "Y" if issue else "N",
                })
        with (args.out / f"{n}th.csv").open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n")
            w.writeheader()
            w.writerows(out_rows)
        counts = {}
        for r in out_rows:
            counts[r["Filed?"]] = counts.get(r["Filed?"], 0) + 1
        totals[n] = (len(out_rows), counts)
        print(f"{n}th: {len(out_rows):,} postings  " + "  ".join(f"{k} {v:,}" for k, v in sorted(counts.items())))


if __name__ == "__main__":
    main()
