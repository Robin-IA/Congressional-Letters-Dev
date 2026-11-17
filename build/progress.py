#!/usr/bin/env python3
"""How far each Congress is from done: the running view of the reading.

    .venv/bin/python build/progress.py                  # -> ~/ia/letters-from-congress-OCR
    .venv/bin/python build/progress.py --out /some/dir

Writes PROGRESS.md (one table, by Congress) and progress.csv (one row per
scan, so the next batch can be picked from what is not done).

WHAT "DONE" MEANS (Robin, 14 November 2026). A letter is done when all of
these hold:

  text            its text layer or its OCR is at least MIN_CHARS (100)
                  characters, so there is something to read
  reviewed        a reader has read it against that text
                  (vocabulary/letters-reviewed.csv)
  title confirmed the reader confirmed or wrote its title (reviewed: title=yes)
  title process   its title is a hand title in the project's form, "subject
                  — to whom" (vocabulary/letter-titles.csv, with " — " between
                  the two halves)
  date settled    its date was read from the letter (vocabulary/letter-dates.csv)
                  or the reader confirmed the date it had (reviewed: date=yes or
                  unchanged) -- the dating rule of #172
  subjects        it carries at least one topic as published
  filed           its recipient is a reviewed term of the vocabulary -- not
                  in Not yet reviewed (a candidate), not missing a term, and
                  not missing a recipient (Robin: anything in Not yet reviewed
                  is not complete)

The counts are of letters as the explorers publish them, so a scan posted by
two members counts twice, as a reader would find it twice. Whether a letter
is done is decided by its scan (its digest): reading a scan once settles
every posting of it. Nothing here reads the Wayback Machine.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "build"))
from build_vocabulary import name_key  # noqa: E402
import filed_orgs  # noqa: E402
import letter_text  # noqa: E402
EXPLORERS = ROOT.parent / "explorers"
VOCAB = ROOT / "vocabulary"
MIN_CHARS = 100
CONGRESSES = range(106, 120)

# The columns of PROGRESS.md, in order, with what each counts.
STEPS = [
    ("text", "Text", "text layer or OCR of at least 100 characters"),
    ("ocr", "of which OCR", "the text came from OCR (a scan), not the PDF's own text layer"),
    ("reviewed", "Reviewed", "read by a reader against the text (letters-reviewed.csv)"),
    ("title_confirmed", "Title confirmed", "the reader confirmed or wrote the title"),
    ("title_process", "Title in our form", "a hand title in the form \"subject — to whom\" (letter-titles.csv)"),
    ("date_settled", "Date settled", "read from the letter (letter-dates.csv) or confirmed by the reader"),
    ("subjects", "Subjects", "at least one topic as published"),
    ("filed", "Filed", "its recipient is a reviewed term, not in Not yet reviewed"),
    ("done", "Done", "all of the above"),
]


def title_in_form(title: str) -> bool:
    """'Industry funding — to American Diabetes Association': a subject, an
    em dash, and who it is to (or 'X to Y' for a letter written to a member)."""
    if " — " not in (title or ""):
        return False
    subject, whom = title.split(" — ", 1)
    return bool(subject.strip()) and bool(whom.strip())


def filing(recipient: str, terms: dict) -> str:
    """'filed', 'not yet reviewed', 'no term' or 'no recipient'."""
    if not (recipient or "").strip():
        return "no recipient"
    state = terms.get(name_key(recipient))
    if state is None:
        return "no term"
    return "filed" if state == "preferred" else "not yet reviewed"


REVIEWED_NAMES = ("officeHolderName", "recipientName")


def recipient_terms() -> dict:
    """name_key of every term's label and alternate spellings -> its status,
    the reviewed one winning where a spelling belongs to two terms."""
    out: dict[str, str] = {}
    status_of: dict[str, str] = {}
    for r in read_csv("terms.csv"):
        status_of[r["term_id"]] = r["status"]
        k = name_key(r["label"])
        if out.get(k) != "preferred":
            out[k] = r["status"]
    for r in read_csv("relations.csv"):
        if r["term_id"] not in status_of:
            continue
        if r["relation"] == "altLabel":
            k = name_key(r["value"])
        elif r["relation"] in REVIEWED_NAMES:
            # A reviews.csv decision files the name under a reviewed term
            # without making it an altLabel: "Hagel" an office holder's name
            # of the Department of Defense, "Grassley" a recipientName of
            # his member term. A split carries its years: "Wheeler (2014-2017)".
            k = name_key(re.sub(r"\s*\([^)]*\)$", "", r["value"]))
        else:
            continue
        if out.get(k) != "preferred":
            out[k] = status_of[r["term_id"]]
    return out


def status(digest: str, topics: str, chars: dict, ocr: set, reviewed: dict,
           titles: dict, dates: set, filed: str = "filed") -> dict:
    """The steps one published letter has passed."""
    r = reviewed.get(digest) or {}
    s = {
        "text": chars.get(digest, 0) >= MIN_CHARS,
        "ocr": digest in ocr,
        "reviewed": bool(r),
        "title_confirmed": (r.get("title") or "").lower() == "yes",
        "title_process": title_in_form(titles.get(digest, "")),
        "date_settled": digest in dates or (r.get("date") or "").lower() in ("yes", "unchanged"),
        "subjects": bool((topics or "").strip()),
        "filed": filed == "filed",
    }
    s["done"] = all(s[k] for k in ("text", "reviewed", "title_confirmed", "title_process",
                                   "date_settled", "subjects", "filed"))
    return s


def text_chars() -> tuple[dict, set]:
    """digest -> the most characters any read gave it, and the digests whose
    usable text came from OCR (the text layer fell short)."""
    layer: dict[str, int] = defaultdict(int)
    ocr: dict[str, int] = defaultdict(int)
    for path, into in ((ROOT / "data" / "letter-text.jsonl", layer),
                       (ROOT / "data" / "letter-ocr.jsonl", ocr)):
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if r.get("digest"):
                    into[r["digest"]] = max(into[r["digest"]], int(r.get("chars") or 0))
    best = {d: max(layer.get(d, 0), ocr.get(d, 0)) for d in set(layer) | set(ocr)}
    from_ocr = {d for d, n in ocr.items() if n >= MIN_CHARS and layer.get(d, 0) < MIN_CHARS}
    return best, from_ocr


def read_csv(name: str) -> list[dict]:
    path = VOCAB / name
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def published(explorers: Path):
    """(congress, member, digest, subject, topics, recipient) for every published letter."""
    for n in CONGRESSES:
        d = explorers / f"Explorer-Congressional-Letters-{n}"
        index = d / "index.json"
        if not index.exists():
            continue
        cols = json.loads(index.read_text(encoding="utf-8"))["columns"]
        at = {c: i for i, c in enumerate(cols)}
        for f in sorted((d / "payload" / "member").glob("*.json")):
            for row in json.loads(f.read_text(encoding="utf-8")):
                yield (n, f.stem, row[at["digest"]], row[at["subject"]], row[at["topics"]],
                       row[at["recipient"]])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=Path.home() / "ia" / "letters-from-congress-OCR")
    ap.add_argument("--explorers", type=Path, default=EXPLORERS)
    args = ap.parse_args()
    if not args.out.is_dir():
        sys.exit(f"{args.out}: not a folder")

    chars, ocr = text_chars()
    reviewed = {r["digest"]: r for r in read_csv("letters-reviewed.csv")}
    titles = {r["digest"]: r["title"] for r in read_csv("letter-titles.csv")}
    dates = {r["digest"] for r in read_csv("letter-dates.csv")}
    terms = recipient_terms()
    # A reader's decision that a letter has no recipient files it (#502).
    no_recipient = {d for d, r in letter_text.recipients_by_hand().items()
                    if r == letter_text.NO_RECIPIENT}
    company_tags = {filed_orgs.tag_of(lab) for lab in filed_orgs.nongov_labels()}
    filings = {n: Counter() for n in CONGRESSES}

    per = {n: Counter() for n in CONGRESSES}
    scans: dict[str, dict] = {}
    for n, member, digest, subject, topics, recipient in published(args.explorers):
        # A letter filed under a company by topic is filed (filed_orgs.py).
        if any(t.strip() in company_tags for t in re.split(r"[;,]", topics or "")):
            f = "filed"
        elif digest in no_recipient:
            f = "filed"
        else:
            f = filing(recipient, terms)
        filings[n][f] += 1
        s = status(digest, topics, chars, ocr, reviewed, titles, dates, f)
        per[n]["letters"] += 1
        for k, v in s.items():
            per[n][k] += v
        row = scans.setdefault(digest, {"digest": digest, "congresses": set(), "members": set(),
                                        "title": subject, **s})
        row["congresses"].add(n)
        row["members"].add(member)

    total = sum((per[n] for n in CONGRESSES), Counter())
    when = datetime.datetime.now().astimezone()

    def pct(a, b):
        return f"{100 * a / b:.1f}%" if b else "—"

    lines = [
        "# Progress", "",
        f"Measured {when:%B} {when.day}, {when.year}, {when:%I:%M %p %Z}".replace(" 0", " ")
        + " by `build/progress.py` in Congressional-Letters-Dev, over every letter the"
        " explorers publish. A letter is **done** when it has text, has been reviewed"
        " against it, its title is confirmed and in our form, its date is settled, it"
        " carries subjects, and it is filed (its recipient is a reviewed term). It counts"
        " what is published, so it reflects the last publish.", "",
        f"**{total['done']:,} of {total['letters']:,} published letters are done"
        f" ({pct(total['done'], total['letters'])}).**", "",
        "| Congress | Letters | " + " | ".join(label for _, label, _ in STEPS) + " |",
        "| --- | ---: | " + " | ".join("---:" for _ in STEPS) + " |",
    ]
    for n in CONGRESSES:
        c = per[n]
        lines.append(f"| {n}th | {c['letters']:,} | " +
                     " | ".join(f"{c[k]:,}" for k, _, _ in STEPS) + " |")
    lines.append(f"| **All** | **{total['letters']:,}** | " +
                 " | ".join(f"**{total[k]:,}**" for k, _, _ in STEPS) + " |")
    ftot = sum((filings[n] for n in CONGRESSES), Counter())
    kinds = ["filed", "not yet reviewed", "no term", "no recipient"]
    lines += ["", "## Filing", "",
              "Where each letter's recipient stands. Only **filed** counts toward done.", "",
              "| Congress | " + " | ".join(kinds) + " |", "| --- | " + " | ".join("---:" for _ in kinds) + " |"]
    lines += [f"| {n}th | " + " | ".join(f"{filings[n][k]:,}" for k in kinds) + " |" for n in CONGRESSES]
    lines += [f"| **All** | " + " | ".join(f"**{ftot[k]:,}**" for k in kinds) + " |"]
    lines += ["", "- **not yet reviewed**: the recipient is a candidate in Not yet reviewed;"
              " a `reviews.csv` decision files it.",
              "- **no term**: the recipient has no vocabulary term (named too rarely to be a"
              " candidate); file it by a `reviews.csv` decision or a corrected recipient.",
              "- **no recipient**: none was read from the file name; the letter's salutation"
              " names one (#97)."]
    lines += ["", "## What each column counts", ""]
    lines += [f"- **{label}**: {what}." for _, label, what in STEPS]
    off_form = sorted(t for d, t in titles.items() if not title_in_form(t))
    if off_form:
        lines += ["", f"## Hand titles not in our form ({len(off_form)})", ""]
        lines += [f"- {t}" for t in off_form]
    # For the PC, which does the reading: how a letter becomes done, and what
    # to read next -- scans with text that are not done, most-published first
    # (a scan posted by several members is found by more readers), then newest.
    todo = sorted((r for r in scans.values() if r["text"] and not r["done"]),
                  key=lambda r: (-len(r["members"]), -max(r["congresses"]), r["digest"]))
    missing = Counter()
    for r in todo:
        for k in ("reviewed", "title_confirmed", "title_process", "date_settled", "subjects", "filed"):
            if not r[k]:
                missing[k] += 1
    label = {k: lab for k, lab, _ in STEPS}
    lines += [
        "", "## For the PC", "",
        "**To make a letter done**, in one PR from a fresh branch off the latest"
        " `harvest-member-letters`:", "",
        "1. Read it against its text (`text/<N>th.jsonl.gz` in this repository).",
        "2. `vocabulary/letters-reviewed.csv`: one row, `title=yes`, and `date=yes`"
        " (corrected) or `unchanged` (already right).",
        "3. `vocabulary/letter-titles.csv`: the title, as \"subject — to whom\".",
        "4. `vocabulary/letter-dates.csv`: the date, if read from the letter and different;"
        " the order is the letter, then the file name, then the PDF's metadata, then review (#172).",
        "5. `vocabulary/letter-topics.csv`: topics, if it has none or lacks one it should"
        " carry. New topics go in `build/topics.py` first, in their own PR.",
        "6. Filed: its recipient must be a reviewed term. If it is in Not yet reviewed,"
        " add the decision to `vocabulary/reviews.csv`; if it has no recipient or no term,"
        " that is #97's recipients-from-the-text work.",
        "7. Run `python3 -m unittest discover -s tests` before opening the PR.", "",
        f"**{len(todo):,} scans have text and are not done.** What they lack:", "",
    ]
    lines += [f"- {label[k]}: {v:,}" for k, v in missing.most_common()]
    lines += ["", "**Next 25 to read** (most published first, then newest Congress;"
              " the full list is `progress.csv`, filter `text=True, done=False`):", "",
              "| digest | Congress | postings | title now |", "| --- | --- | ---: | --- |"]
    lines += [f"| `{r['digest'][:12]}` | {', '.join(f'{c}th' for c in sorted(r['congresses']))}"
              f" | {len(r['members'])} | {(r['title'] or '').replace('|', '/')[:70]} |"
              for r in todo[:25]]
    lines += ["", "Letters are counted as published, so a scan posted by two members counts"
              " twice. Whether a letter is done is decided by its scan, so reading a scan once"
              " settles every posting of it. `progress.csv` has one row per scan.", ""]
    (args.out / "PROGRESS.md").write_text("\n".join(lines), encoding="utf-8")

    keys = ["digest", "congresses", "members", "title"] + [k for k, _, _ in STEPS]
    with (args.out / "progress.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for d in sorted(scans):
            r = scans[d]
            w.writerow({**{k: r[k] for k in keys if k not in ("congresses", "members")},
                        "congresses": ";".join(str(x) for x in sorted(r["congresses"])),
                        "members": ";".join(sorted(r["members"]))})

    print(f"{total['done']:,} of {total['letters']:,} published letters done; "
          f"{len(scans):,} scans -> {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
