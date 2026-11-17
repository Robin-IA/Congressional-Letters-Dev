#!/usr/bin/env python3
"""QA status CSVs: one per Congress, one row per posting (QA-Analysis-methodology).

    python3 build/qa_status.py [--out DIR] [--congress 106-119]

Run after build_congress.py, which writes the explorers this reads. Writes
<DIR>/<N>th.csv (default: the letters-from-congress-OCR checkout's qa-status/)
with the columns Robin set on 17 November 2026:

  Congress, Letter URL, Letter name (original), Discarded, Letter Name Fix,
  Authors, Subjects, Dates, Recipients, OCR, Filed?, Issue

Filed? is one of (Robin, 17 November 2026: what constitutes done):
  Filed         done: has OCR, is a letter, has authorship, a recipient if
                applicable, a date if determined, at least 4 subjects with 2
                topics, a title in the established form, and is published and
                filed. Filed here is exactly "done" in progress.py.
  Hold          held for a term or a decision (letters-vocabulary-needs)
  Needs Review  read but short of a requirement (subjects, title, recipient
                term), set aside as partial or unreadable (build/mac/skip.txt),
                DISCARDED (Discarded=Y, Issue=Y), or a TRUE DUPLICATE, one
                member's second copy of a letter, a potential discard needing
                further review (Issue=Y). Neither is ever Filed until taken
                out of that status and the rest of the work is complete.
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
    ap.add_argument("--progress", type=Path, default=OCR_REPO / "progress.csv",
                    help="progress.py's progress.csv, whose done column Filed follows")
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
    import sys
    sys.path.insert(0, str(ROOT / "build"))
    import topics as topics_mod  # noqa: E402
    subject_list = set(topics_mod.SUBJECTS)
    terms = rows_of(ROOT / "vocabulary/terms.csv")
    org_labels = {r["label"] for r in terms if r.get("kind") in ("organization", "office")
                  and r.get("status") == "preferred"}
    known = ({r["label"] for r in terms if r.get("status") == "preferred"}
             | {r["candidate"] for r in rows_of(ROOT / "vocabulary/reviews.csv") if r.get("status") == "accepted"})
    prog = rows_of(args.progress)
    done = {r["digest"]: r.get("done") == "True" for r in prog}
    # progress.py's "letter" step is false for a discard and for a true
    # duplicate (a potential discard, Robin, 17 November 2026): both are under
    # issues.
    not_letter = {r["digest"] for r in prog if r.get("letter") == "False"}
    direction = {r["digest"]: r["direction"] for r in rows_of(ROOT / "vocabulary/letter-direction.csv")}

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
                if row[11:12] == ["received"]:  # a copy on a recipient's page (#352)
                    continue
                key, ts, _kind, date, _prec, recipient, _subject, tops, cosigners, digest, url = row[:11]
                authors = [names.get(mid, mid)] + [c for c in (cosigners or "").split(",") if c]
                if direction.get(digest) in ("to", "neither"):
                    # Written to Congress, or no member at either end (#175): the
                    # author is the sender the title names ("— AARP to Senator
                    # Collins"), never the member who posted it.
                    m = re.search(r" — (.+?) to ", titles.get(digest, ""))
                    authors = [m.group(1)] if m else []
                subj = list(dict.fromkeys([t for t in (tops or "").split(",") if t] + topics.get(digest, [])))
                rec = recipients.get(digest) or recipient or ""
                if digest in discarded:
                    status = "Needs Review"   # a discard is not done (17 November 2026)
                elif digest in held:
                    status = "Hold"
                elif digest in skip:
                    status = "Needs Review"
                elif digest in reviewed:
                    # Filed is exactly progress.py's "done" (Robin's definition,
                    # 17 November 2026), read from progress.csv, so the two
                    # never disagree.
                    status = "Filed" if done.get(digest) else "Needs Review"
                else:
                    status = "Unprocessed"
                note = (reviewed.get(digest) or {}).get("note", "")
                issue = bool(digest in discarded or digest in not_letter or (held.get(digest) or {}).get("issue")
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
