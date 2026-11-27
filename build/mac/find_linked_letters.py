#!/usr/bin/env python3
"""Letters that belong together, found for a reader to confirm (#1289).

Robin, #1289: "Doublecheck discards for connection to a letter. If found,
connect the discard to the letter and process the discard, filing it. Check
all letters to see if they reference other letters. If a relationship is
found, connect it to other letters."

  find_linked_letters.py discards   [--out DIR] [--all]   discards a member's letter may cite
  find_linked_letters.py references [--out DIR]           letters that name another letter
  find_linked_letters.py apply CONFIRMED.csv              write what a reader confirmed

Run `discards` and `references` from the pipeline machine, where the OCR
(~/ia/letters-from-congress-OCR) and the built explorers (~/ia/explorers) are.
They only propose: each writes a CSV of candidates with the evidence, and a
reader reads both letters and marks `confirm` yes or no. Run `apply` from a
dev-clone branch on the reader's CSV; it writes vocabulary/letter-related.csv
and, for a confirmed discard, takes the discard's row out of
letters-discarded/letters.csv so the reading picks it up and files it.

**Discards.** The discard criteria keep a letter that is a supplement to a
member's letter: an enclosure, a reply, or a document the letter cites
(letters-discarded/README.md, test 2, point 3). Since batch 4, `mac_read.py
write` searches the posting members' letters for a citation before it
discards one under test 2, and says so in the reason ("No letter by the
posting members cites it"). Of the 195 test-2 discards, 153 were made
without that search (26 November 2026); those are the ones checked (with
--all, every test-2 discard). A
candidate is one of the posting members' letters that

* names the discard's distinctive words (its sender, its subject), as
  mac_read.citing_letters does;
* mentions the discard's date, written any common way; or
* was posted beside it: the same folder on the member's site, captured within
  60 days (Cantwell's letter and the USGS request she cited; #1207).

**References.** A letter that names another letter by its date: "my letter
of March 3, 2019", "our letter dated 3/3/19", "in response to your letter of
June 5", "On June 5, 2018, I wrote to you". Each reference is matched to the
letters the same members posted, dated within three days of the date named.
"my/our letter" proposes `follows_up` (this letter follows up the earlier
one); "your letter" proposes `supports` (this letter, the reply, supports the
one it answers, as State's reply supports the Royce letter in
vocabulary/letter-related.csv).

The candidate files say why each was proposed. Nothing here decides: a
date in common is a lead, not a link.
"""
from __future__ import annotations

import argparse
import csv
import glob
import gzip
import json
import re
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

HOME = Path.home()
ROOT = Path(__file__).resolve().parents[2]
OCR = HOME / "ia/letters-from-congress-OCR"
EXPLORERS = HOME / "ia/explorers"
DISCARDS = ROOT / "letters-discarded/letters.csv"
RELATED = ROOT / "vocabulary/letter-related.csv"
DATES = ROOT / "vocabulary/letter-dates.csv"
OUT = HOME / "ia/linked-letters"

SEARCHED = "No letter by the posting members cites it"
RELATIONS = {"supports", "draft_of", "part_of", "follows_up"}

MONTHS = {m: i + 1 for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"])}
MONTHS.update({m[:3]: i for m, i in list(MONTHS.items())})
MONTHS["sept"] = 9
MON = r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|sept?(?:ember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?"
DATE = (rf"(?:{MON}\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+\d{{4}}"    # March 3, 2019
        rf"|\d{{1,2}}\s+{MON}\s+\d{{4}}"                         # 3 March 2019
        rf"|\d{{1,2}}/\d{{1,2}}/\d{{2,4}})")                     # 3/3/19

# A letter named by its date, and whose it is.
REFERENCES = [
    ("own", re.compile(rf"\b(?:my|our)\s+(?:previous\s+|prior\s+|earlier\s+|initial\s+|original\s+)?"
                       rf"letters?\s+(?:to\s+you\s+|to\s+[A-Z][\w.]*(?:\s+[A-Z][\w.]*){{0,3}}\s+)?"
                       rf"(?:of|dated|on|from|sent(?:\s+on)?)\s+({DATE})", re.I)),
    ("own", re.compile(rf"\bon\s+({DATE}),?\s+(?:I|we)\s+(?:wrote|sent\s+(?:you\s+)?a\s+letter)", re.I)),
    ("theirs", re.compile(rf"\byour\s+(?:recent\s+)?letter\s+(?:to\s+me\s+|to\s+us\s+)?"
                          rf"(?:of|dated|on|from|received)\s+({DATE})", re.I)),
]
STOP = {"letter", "letters", "senator", "secretary", "administrator", "chairman",
        "representative", "members", "department", "ranking", "member", "committee",
        "leader", "congress", "january", "february", "august", "september", "october",
        "november", "december", "director", "regarding", "concerning", "request"}


# ----------------------------------------------------------------- reading

def parse_date(text: str) -> date | None:
    """ "March 3, 2019", "3 March 2019", "Mar. 3rd 2019", "3/3/19" -> a date."""
    t = text.strip().lower().replace(",", " ")
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", t)
    if m:
        mo, d, y = (int(x) for x in m.groups())
        y += 2000 if y < 50 else 1900 if y < 100 else 0
    else:
        words = re.findall(r"[a-z]+|\d+", t)
        mo = next((MONTHS.get(w) for w in words if w in MONTHS), None)
        nums = [int(w) for w in words if w.isdigit()]
        if not mo or len(nums) < 2:
            return None
        d, y = (nums[0], nums[1]) if nums[1] > 31 else (nums[1], nums[0])
    try:
        return date(y, mo, d)
    except ValueError:
        return None


def references(text: str) -> list[tuple[str, date, str]]:
    """(whose, date named, the words around it) for each letter the text names."""
    out = []
    flat = re.sub(r"\s+", " ", text)
    for whose, pattern in REFERENCES:
        for m in pattern.finditer(flat):
            when = parse_date(m.group(1))
            if when:
                start, end = max(0, m.start() - 80), min(len(flat), m.end() + 120)
                out.append((whose, when, flat[start:end].strip()))
    seen, unique = set(), []
    for r in out:
        if (r[0], r[1]) not in seen:
            seen.add((r[0], r[1]))
            unique.append(r)
    return unique


def date_forms(d: date) -> list[str]:
    """The ways a letter might write a date, lower-cased, for a text search."""
    month = [k for k, v in MONTHS.items() if v == d.month and len(k) > 3][0]
    return [f"{month} {d.day}, {d.year}", f"{month} {d.day} {d.year}", f"{d.day} {month} {d.year}",
            f"{d.month}/{d.day}/{d.year}", f"{d.month}/{d.day}/{d.year % 100:02d}"]


def keys_of(title: str) -> list[str]:
    """A discard's distinctive words, as mac_read.citing_letters takes them."""
    return [w.lower() for w in re.findall(r"[A-Za-z][A-Za-z'-]{6,}", title)
            if w.lower() not in STOP][:5]


def date_in(title: str) -> date | None:
    m = re.search(DATE, title, re.I)
    return parse_date(m.group(0)) if m else None


# --------------------------------------------------------------- the corpus

class Corpus:
    """What the Mac knows about every letter: who posted it, where, when."""

    def __init__(self, ocr: Path = OCR, explorers: Path = EXPLORERS):
        self.members: dict[str, set[str]] = defaultdict(set)      # digest -> bioguides
        self.posts: dict[str, list[dict]] = defaultdict(list)     # digest -> postings
        self.dates: dict[str, date] = {}
        self.text: dict[str, str] = {}
        self.by_member: dict[str, set[str]] = defaultdict(set)    # bioguide -> digests
        for ex in sorted(glob.glob(str(explorers / "Explorer-Congressional-Letters-1*"))):
            for f in glob.glob(f"{ex}/payload/member/*.json"):
                mid = Path(f).stem
                for row in json.load(open(f, encoding="utf-8")):
                    if row[11:12] == ["received"]:      # a copy on a recipient's page (#352)
                        continue
                    self.add_post(row[9], mid, {"file": row[10] or row[0], "capture": row[1],
                                                 "date": row[3], "recipient": row[5], "subject": row[6]})
        if DATES.exists():
            for r in csv.DictReader(DATES.open(encoding="utf-8")):
                when = iso(r["date"]) if r.get("precision") == "day" else None
                if when:
                    self.dates[r["digest"]] = when
        for f in sorted((ocr / "text").glob("*.jsonl.gz")):
            with gzip.open(f, "rt", encoding="utf-8") as fh:
                for line in fh:
                    r = json.loads(line)
                    self.text[r["digest"]] = r["text"]

    def add_post(self, digest: str, member: str, post: dict) -> None:
        if not digest:
            return
        self.members[digest].add(member)
        self.by_member[member].add(digest)
        post = {**post, "member": member}
        self.posts[digest].append(post)
        when = iso(post.get("date") or "")
        if when and digest not in self.dates:
            self.dates[digest] = when

    def title(self, digest: str) -> str:
        p = self.posts.get(digest) or [{}]
        return f"{p[0].get('subject') or '?'} — to {p[0].get('recipient') or '?'}, {p[0].get('date') or '?'}"


def iso(s: str) -> date | None:
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        return None


def folder(file: str) -> str:
    return file.rsplit("/", 1)[0].lower() if "/" in file else ""


def capture_day(ts: str) -> date | None:
    try:
        return date(int(ts[:4]), int(ts[4:6]), int(ts[6:8]))
    except (ValueError, IndexError):
        return None


# -------------------------------------------------------------- the checks

def discard_candidates(discard: dict, corpus: Corpus, skip: set[str]) -> list[dict]:
    """The posting members' letters that may cite or sit beside one discard."""
    d = discard["digest"]
    keys = keys_of(discard["title"])
    when = date_in(discard["title"])
    forms = date_forms(when) if when else []
    beside = {(p["member"], folder(p["file"])): capture_day(p["capture"]) for p in corpus.posts.get(d, [])}
    out = []
    for member in sorted(corpus.members.get(d, set())):
        for other in sorted(corpus.by_member[member]):
            if other == d or other in skip:
                continue
            text = corpus.text.get(other, "").lower()
            why = []
            hit = [k for k in keys if k in text]
            if keys and len(hit) >= max(2, len(keys) // 2 + 1):
                why.append(f"names {', '.join(hit)}")
            if forms and any(f in text for f in forms):
                why.append(f"mentions {when.isoformat()}")
            for p in corpus.posts[other]:
                there = beside.get((member, folder(p["file"])))
                cap = capture_day(p["capture"])
                if folder(p["file"]) and there and cap and abs((cap - there).days) <= 60:
                    why.append(f"posted beside it ({folder(p['file'])})")
                    break
            if why:
                out.append({"discard": d, "discard_title": discard["title"], "letter": other,
                            "letter_title": corpus.title(other), "member": member,
                            "evidence": "; ".join(why), "score": len(why),
                            "relation": "supports", "confirm": ""})
    return sorted(out, key=lambda r: -r["score"])


def reference_candidates(digest: str, corpus: Corpus, skip: set[str], linked: set[tuple[str, str]],
                         window: int = 3) -> list[dict]:
    """Letters by the same members dated near a date this letter names."""
    out = []
    for whose, when, context in references(corpus.text.get(digest, "")):
        for member in sorted(corpus.members.get(digest, set())):
            for other in sorted(corpus.by_member[member]):
                od = corpus.dates.get(other)
                if other == digest or other in skip or not od or abs((od - when).days) > window:
                    continue
                if whose == "own":
                    pair, relation = (digest, other), "follows_up"
                else:
                    pair, relation = (digest, other), "supports"   # the reply first
                if pair in linked or pair[::-1] in linked:
                    continue
                out.append({"letter": digest, "letter_title": corpus.title(digest), "names": when.isoformat(),
                            "whose": whose, "context": context, "candidate": other,
                            "candidate_title": corpus.title(other), "candidate_date": od.isoformat(),
                            "member": member, "days_off": abs((od - when).days),
                            "digest": pair[0], "related": pair[1], "relation": relation, "confirm": ""})
    return sorted(out, key=lambda r: r["days_off"])


# ---------------------------------------------------------------- commands

def load_csv(path: Path) -> list[dict]:
    return list(csv.DictReader(path.open(encoding="utf-8", newline=""))) if path.exists() else []


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = list(rows[0]) if rows else ["none"]
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


TEST2 = re.compile(r"test 2|no relation|between other parties|not a letter by, to", re.I)
# A posting that is not a letter fails test 1 whatever it relates to, and a
# duplicate is a second copy; neither is a supplement to restore. The reasons
# are free text, so "not a letter by, to, or about a member" (test 2) is kept.
NOT_A_LETTER = re.compile(r"\bnot a letter\b(?!\s+by)|^duplicate", re.I)


def unsearched_test2(discards: list[dict], everyone: bool = False) -> list[dict]:
    """Test-2 discards whose reason does not say the citation search was done."""
    return [r for r in discards
            if TEST2.search(r["reason"]) and not NOT_A_LETTER.search(r["reason"])
            and (everyone or SEARCHED.lower() not in r["reason"].lower())]


def cmd_discards(out: Path, everyone: bool) -> None:
    discards = load_csv(DISCARDS)
    todo = unsearched_test2(discards, everyone)
    corpus = Corpus()
    skip = {r["digest"] for r in discards}
    rows = [c for r in todo for c in discard_candidates(r, corpus, skip)]
    write_csv(out / "discard-candidates.csv", rows)
    print(f"{len(todo)} test-2 discards checked; {len({r['discard'] for r in rows})} have candidates; "
          f"{len(rows)} candidate links -> {out / 'discard-candidates.csv'}")


def cmd_references(out: Path) -> None:
    discards = {r["digest"] for r in load_csv(DISCARDS)}
    linked = {(r["digest"], r["related"]) for r in load_csv(RELATED)}
    corpus = Corpus()
    rows = []
    for digest in sorted(corpus.text):
        if digest in discards or digest not in corpus.members:
            continue
        rows += reference_candidates(digest, corpus, discards, linked)
    write_csv(out / "reference-candidates.csv", rows)
    print(f"{len({r['letter'] for r in rows})} letters name another letter that may be in the collection; "
          f"{len(rows)} candidate links -> {out / 'reference-candidates.csv'}")


def cmd_apply(confirmed: Path, issue: str) -> None:
    """Write a reader's confirmed rows: letter-related.csv, and the discard file."""
    rows = [r for r in load_csv(confirmed) if (r.get("confirm") or "").strip().lower() in ("yes", "y")]
    links, refile = [], set()
    for r in rows:
        if "discard" in r:                     # from discard-candidates.csv
            first, second = r["discard"], r["letter"]
            refile.add(r["discard"])
            note = (f"{r['discard_title']}; {r['evidence']}; was discarded, found to support "
                    f"{r['letter_title']} (#{issue})")
        else:                                  # from reference-candidates.csv
            first, second = r["digest"], r["related"]
            note = f"named by date ({r['names']}) in the letter's text: \"{r['context'][:160]}\" (#{issue})"
        relation = (r.get("relation") or "supports").strip()
        if relation not in RELATIONS:
            raise SystemExit(f"{confirmed}: unknown relation {relation!r}; one of {sorted(RELATIONS)}")
        links.append({"digest": first, "related": second, "relation": relation, "note": note})
    have = load_csv(RELATED)
    known = {(r["digest"], r["related"]) for r in have}
    new = [l for l in links if (l["digest"], l["related"]) not in known]
    with RELATED.open("a", encoding="utf-8", newline="") as fh:
        csv.DictWriter(fh, fieldnames=["digest", "related", "relation", "note"]).writerows(new)
    if refile:
        lines = DISCARDS.read_text(encoding="utf-8").splitlines(keepends=True)
        kept = [lines[0]] + [l for l in lines[1:] if l.split(",", 1)[0] not in refile]
        DISCARDS.write_text("".join(kept), encoding="utf-8")
    print(f"{len(new)} links added to {RELATED.name}; {len(refile)} discards returned to the reading")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("discards")
    d.add_argument("--out", type=Path, default=OUT)
    d.add_argument("--all", action="store_true", help="every test-2 discard, searched or not")
    r = sub.add_parser("references")
    r.add_argument("--out", type=Path, default=OUT)
    a = sub.add_parser("apply")
    a.add_argument("confirmed", type=Path)
    a.add_argument("--issue", default="1289")
    args = ap.parse_args()
    if args.cmd == "discards":
        cmd_discards(args.out, args.all)
    elif args.cmd == "references":
        cmd_references(args.out)
    else:
        cmd_apply(args.confirmed, args.issue)


if __name__ == "__main__":
    main()
