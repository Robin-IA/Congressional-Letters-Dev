#!/usr/bin/env python3
"""Match unreviewed recipient names to reviewed ones by rule (#97).

The salutation gives a recipient for most letters (letter_text.py), and the
common names are decided by hand in vocabulary/reviews.csv. What is left is a
long tail -- 2,600 names of under eight letters each -- most of which are a
name already decided under another title or spelling: "Dr. Redfield" when
"Director Redfield" is decided, "Charwoman Granger and Ranking Member
DeLauro" when the correctly spelled pair is. This proposes a decision for
each such name, from positive evidence only:

1. **Same title, same surname.** A decided name with the same office title
   ("secretary", "administrator", "chair" ...) and surname gives its target,
   if every such decided name agrees on one.
2. **An honorific and the surname.** "Mr."/"Ms."/"Dr." and a surname every
   decided name agrees on, and no member of Congress had. A bare surname
   never matches.
3. **The same people in another order or spelling.** A name of several
   people ("Chairman X and Ranking Member Y") takes the target of a decided
   name with the same surnames.
4. **Each part resolved.** Otherwise each person in it is resolved by 1-2;
   if all are, the letter goes to each target ("joint"), or to the one
   target they share.
5. **A member by title.** "Senator X", "Congressman X", "Representative X":
   the one member of that chamber, in the 106th-119th rosters, with that
   surname. Two members with one surname is no match.

Anything else is left for a reader. The rows say which rule matched and on
what, so each can be checked.

    python build/match_recipients.py              # counts and a sample
    python build/match_recipients.py --write      # append the rows to reviews.csv
"""
from __future__ import annotations

import argparse
import csv
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_vocabulary import rosters  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
VOCAB = ROOT / "vocabulary"

# One office title for its spellings; the last title before the surname
# names the office ("Assistant Secretary" is "secretary").
TITLE = {"chair": "chair", "chairman": "chair", "chairwoman": "chair", "charman": "chair", "chainnan": "chair",
         "charwoman": "chair", "secretary": "secretary", "secretaries": "secretary", "administrator": "administrator",
         "director": "director", "commissioner": "commissioner", "general": "general", "ambassador": "ambassador",
         "chief": "chief", "postmaster": "postmaster", "comptroller": "comptroller", "governor": "governor",
         "mayor": "mayor", "leader": "leader", "leaders": "leader", "speaker": "speaker", "president": "president",
         "judge": "judge", "senator": "senator", "senators": "senator", "congressman": "representative",
         "congresswoman": "representative", "congressinan": "representative", "representative": "representative",
         "representatives": "representative", "rep": "representative", "sen": "senator", "member": "member"}
PLAIN = {"mr", "mrs", "ms", "dr", "drs", "messrs", "honorable", "hon", "the", "acting", "deputy", "assistant",
         "under", "vice", "ranking", "minority", "majority", "attorney", "inspector", "lieutenant", "major",
         "admiral", "colonel", "col", "gen", "lt", "dear", "madam", "madame", "democratic", "republican", "senate",
         "house", "emerita", "elect", "president-elect", "governor-elect", "minority", "secretary-general",
         "director-general", "us", "u", "s"}
MEMBER_TITLES = {"senator": "Senate", "representative": "House"}
SUFFIX = {"jr", "sr", "ii", "iii", "iv"}
HONORIFIC = {"mr", "mrs", "ms", "dr", "drs", "messrs"}


def people(label: str) -> list[tuple[str, str]]:
    """(title, surname) for each person a name holds: "Chairman Cole and
    Ranking Member DeLauro" -> [("chair", "cole"), ("member", "delauro")]."""
    parts = re.split(r"\s*(?:,|\band\b|&)\s*", label, flags=re.I)
    out, last_title = [], ""
    for part in parts:
        words = [w for w in re.sub(r"[^a-z\-' ]+", " ", part.lower()).split() if w not in SUFFIX]
        if not words:
            continue
        title = ""
        for w in words[:-1]:
            if w in TITLE:
                title = TITLE[w]
            elif w in HONORIFIC and not title:
                title = "hon"
        surname = words[-1]
        if surname in TITLE or surname in PLAIN:
            return []                      # a title with no name: "Dear Mr. Chairman"
        out.append((title or last_title, surname))
        last_title = title or last_title if len(words) == 1 else title
    return out


def load():
    terms = list(csv.DictReader((VOCAB / "terms.csv").open(encoding="utf-8")))
    cand = {r["label"]: int(r["letters"] or 0) for r in terms if r["status"] == "candidate"}
    members = {r["term_id"][2:] for r in terms if r["term_id"].startswith("M-")}
    reviews = list(csv.DictReader((VOCAB / "reviews.csv").open(encoding="utf-8")))
    return cand, members, reviews


def index(reviews):
    """What decided names say: (title, surname) -> targets, surname -> targets,
    and frozenset(surnames) -> the decision of a several-person name."""
    by_title, by_surname, by_group = defaultdict(set), defaultdict(set), defaultdict(set)
    decided = set()
    for r in reviews:
        if r["status"] != "accepted":
            continue
        decided.add(r["candidate"])
        if r["decision"] in ("reject", "hold", "split"):
            continue
        who = people(r["candidate"])
        if not who:
            continue
        decision = (r["decision"], r["target"], r["kind"], r["broader"])
        if len(who) > 1:
            by_group[frozenset(s for _, s in who)].add(decision)
        elif r["decision"] in ("merge", "officeholder", "member", "person"):
            t, s = who[0]
            by_surname[s].add(decision)
            if t:
                by_title[(t, s)].add(decision)
    return by_title, by_surname, by_group, decided


def roster_surnames():
    out = defaultdict(set)
    for bid, m in rosters().items():
        words = [w for w in re.sub(r"[^a-z\-' ]+", " ", m["name"].lower()).split() if w not in SUFFIX]
        if words:
            for ch in m["chambers"]:
                out[(ch, words[-1])].add(bid)
    return out


def resolve_one(t, s, idx, members, roster):
    by_title, by_surname, _, _ = idx
    if t and (t, s) in by_title and len(by_title[(t, s)]) == 1:
        return next(iter(by_title[(t, s)])), f"rule 1: {t} {s}"
    if t in MEMBER_TITLES:
        ids = roster.get((MEMBER_TITLES[t], s), set()) & members
        if len(ids) == 1:
            return ("member", ids.pop(), "", ""), f"rule 5: the one {MEMBER_TITLES[t]} member named {s}"
        return None, ""
    # A bare surname ("Thompson") is never enough, and neither is one a
    # member of Congress also had ("Dr. Sullivan" is not only Jake Sullivan).
    if t == "hon" and len(by_surname.get(s, ())) == 1 and not any(k[1] == s for k in roster):
        return next(iter(by_surname[s])), f"rule 2: {s}"
    return None, ""


def match(label, idx, members, roster):
    who = people(label)
    if not who:
        return None
    if len(who) == 1:
        dec, why = resolve_one(*who[0], idx, members, roster)
        return (dec, why) if dec else None
    group = idx[2].get(frozenset(s for _, s in who))
    if group and len(group) == 1:
        return next(iter(group)), "rule 3: the same people as a decided name"
    targets, whys = [], []
    for t, s in who:
        dec, why = resolve_one(t, s, idx, members, roster)
        if not dec or dec[0] == "person":
            return None
        targets.append(dec[1])
        whys.append(why)
    targets = list(dict.fromkeys(targets))
    if len(targets) == 1:
        return ("merge" if not re.fullmatch(r"[A-Z]\d{6}", targets[0]) else "member", targets[0], "", ""), \
               "rule 4: " + "; ".join(whys)
    return ("joint", ";".join(targets), "", ""), "rule 4: " + "; ".join(whys)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true", help="append the rows to vocabulary/reviews.csv")
    ap.add_argument("--sample", type=int, default=25)
    args = ap.parse_args()
    cand, members, reviews = load()
    idx = index(reviews)
    roster = roster_surnames()
    rows = []
    for label, n in sorted(cand.items(), key=lambda kv: -kv[1]):
        if label in idx[3]:
            continue
        m = match(label, idx, members, roster)
        if m:
            (dec, tgt, kind, broader), why = m
            rows.append([label, n, dec, tgt, "", kind, broader, "matched by rule (match_recipients.py): " + why, "accepted"])
    print(f"{len(rows)} of {len(cand)} unreviewed names matched, {sum(r[1] for r in rows):,} "
          f"of {sum(cand.values()):,} letters")
    random.seed(97)
    for r in random.sample(rows, min(args.sample, len(rows))):
        print(f"  {r[1]:>3}  {r[0]!r} -> {r[2]} {r[3]}   [{r[7][37:]}]")
    if args.write:
        with (VOCAB / "reviews.csv").open("a", encoding="utf-8", newline="") as fh:
            csv.writer(fh, lineterminator="\n").writerows(rows)
        print(f"appended {len(rows)} rows to vocabulary/reviews.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
