#!/usr/bin/env python3
"""Which letters were written as a caucus, read from the letter (#97).

Until now a caucus letter was found only by its address: a letter on
cpc.grijalva.house.gov is the Congressional Progressive Caucus's
(address_holders.CAUCUSES). Most caucuses have no website of their own, so
their letters sit on a member's site and only the letter says whose they are.

A caucus's name in the text is not enough. A letter is sent *to* a caucus,
mentions one in passing, or cites one ("such as the Congressional Black
Caucus Foundation"). So a letter counts only when it speaks as the caucus:

  - the opening sentence, read from the salutation on: "As members of the
    Congressional Hispanic Caucus, we write ...", "On behalf of the Blue Dog
    Coalition", "We, the undersigned Members of the ...", "The Congressional
    Steel Caucus is writing ...";
  - or the letterhead: the page opening with the caucus's name, a chair
    named, and nothing personal above the date (a district, a member's
    website, "Committee on"). A member's own letterhead lists the caucuses
    they chair ("CO-CHAIR, CONGRESSIONAL SHIPBUILDING CAUCUS"), and that
    says nothing about the letter.

Checked by hand 2026-11-13: of 25 sampled opening-sentence matches, 24 spoke
as the caucus (the 25th congratulated a new chair, which "your ... as" now
excludes); a second sample of 25 was 25 of 25; all 13 letterhead matches are
Congressional Hispanic Caucus stationery.

Most caucus letterheads are images the text does not include, which is why
the opening sentence carries most of the weight: measured 2026-11-13, about
530 openings speak as a group, against a few dozen readable letterheads.

The list below is made by hand from that measurement: every member caucus,
coalition or task force that two or more letters speak as, plus the ten
already found by address, under the labels those already use so the two
sources merge. Executive-branch task forces (the White House Coronavirus Task
Force) and outside coalitions (National Rural Housing Coalition) are not
caucuses of Congress and are left out. A caucus speaking in one letter only
is left out until a second turns up; the survey is in the commit that added
this file.

Run directly for counts:  python build/caucuses.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import committees  # noqa: E402  (DATE, SALUTE, OCRFIX, TEXTS: one reading of a letter)

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "letter-caucuses.json"
RULES = "2026-11-13d"  # change when the rules change, so the cache is redone

# pattern (case-insensitive), label. The first ten labels are
# address_holders.CAUCUSES's, so a letter found both ways is tagged once.
CAUCUSES = [
    (r"(?:congressional )?progressive caucus", "Congressional Progressive Caucus"),
    (r"(?:congressional )?black caucus(?! foundation| institute)", "Congressional Black Caucus"),
    (r"blue dog coalition", "Blue Dog Coalition"),
    (r"sustainable energy (?:and|&) (?:the )?environment(?:al)? coalition", "Sustainable Energy & Environment Coalition"),
    (r"(?:gop )?doctors?['’]?s? caucus", "GOP Doctors Caucus"),
    (r"(?<!senate )(?:congressional )?diabetes caucus", "Diabetes Caucus"),
    (r"(?<!senate )(?<!senate and )(?:congressional )?western caucus", "Congressional Western Caucus"),
    (r"new democrat coalition", "New Democrat Coalition"),
    (r"endangered species act (?:congressional )?working group", "Endangered Species Act Congressional Working Group"),
    (r"immigration reform caucus", "Immigration Reform Caucus"),

    (r"(?<!national )(?:congressional )?hispanic caucus(?! institute)", "Congressional Hispanic Caucus"),
    (r"(?:congressional )?asian pacific american caucus|\bCAPAC\b", "Congressional Asian Pacific American Caucus"),
    (r"democratic women['’]?s caucus", "Democratic Women's Caucus"),
    (r"(?:congressional )?steel caucus", "Congressional Steel Caucus"),
    (r"(?:congressional )?dads caucus", "Congressional Dads Caucus"),
    (r"monopoly busters caucus", "Monopoly Busters Caucus"),
    (r"senate western caucus", "Senate Western Caucus"),
    (r"safe climate caucus", "Safe Climate Caucus"),
    (r"americans abroad caucus", "Americans Abroad Caucus"),
    (r"(?:national guard (?:and|&) )?reserve components? caucus", "National Guard and Reserve Component Caucus"),
    (r"senate diabetes caucus", "Senate Diabetes Caucus"),
    (r"freethought caucus", "Congressional Freethought Caucus"),
    (r"(?:lgbt\w*\+? )?equality caucus", "Congressional Equality Caucus"),
    (r"biofuels caucus", "Congressional Biofuels Caucus"),
    (r"ukraine caucus", "Congressional Ukraine Caucus"),
    (r"pro-?choice caucus", "Pro-Choice Caucus"),
    (r"(?<!northern )border security caucus", "Congressional Border Security Caucus"),
    (r"northern border (?:security )?caucus", "Northern Border Caucus"),
    (r"great lakes task force", "Great Lakes Task Force"),
    (r"native american caucus", "Congressional Native American Caucus"),
    (r"quiet skies caucus", "Quiet Skies Caucus"),
    (r"heroin task force", "Bipartisan Heroin Task Force"),
    (r"democratic hispanic task force", "Senate Democratic Hispanic Task Force"),
    (r"high tech caucus", "Congressional High Tech Caucus"),
    (r"republican high tech task force", "Senate Republican High Tech Task Force"),
    (r"gaming caucus", "Congressional Gaming Caucus"),
    (r"protection of civilians in conflict caucus", "Protection of Civilians in Conflict Caucus"),
    (r"climate solutions caucus", "Climate Solutions Caucus"),
    (r"public broadcasting caucus", "Public Broadcasting Caucus"),
    (r"historic preservation caucus", "Congressional Historic Preservation Caucus"),
    (r"taiwan caucus", "Taiwan Caucus"),
    (r"populist caucus", "Populist Caucus"),
    (r"lyme (?:disease )?caucus", "Lyme Disease Caucus"),
    (r"sportsmen['’]?s caucus", "Congressional Sportsmen's Caucus"),
    (r"refugee caucus", "Congressional Refugee Caucus"),
    (r"cambodia caucus", "Congressional Cambodia Caucus"),
    (r"shipbuilding caucus", "Congressional Shipbuilding Caucus"),
    (r"caucus on black women", "Congressional Caucus on Black Women and Girls"),
    (r"caucus for women['’]?s issues", "Congressional Caucus for Women's Issues"),
    (r"caucus on foster youth", "Congressional Caucus on Foster Youth"),
    (r"caucus on hellenic issues|hellenic caucus", "Congressional Caucus on Hellenic Issues"),
    (r"caucus on international narcotics control", "Senate Caucus on International Narcotics Control"),
    (r"task force for combatt?ing anti-?semitism", "Task Force for Combating Antisemitism"),
    (r"brain injury task force", "Congressional Brain Injury Task Force"),
    (r"(?:congressional )?labor caucus", "Congressional Labor Caucus"),
    (r"house democratic caucus", "House Democratic Caucus"),
]
PATTERNS = [(re.compile(p, re.I), lab) for p, lab in CAUCUSES]

# The caucus's name with the words in front of it that make the letter speak
# as the caucus. ROLE covers "As co-chairs of", "We, the undersigned Members
# of", "On behalf of the bipartisan".
ROLE = (r"(?:(?:bi-?partisan|undersigned|newly formed)\s+)*"
        r"(?:(?:co-?\s?chairs?|chairs?|chairm[ae]n|chairwom[ae]n|vice[- ]chairs?|"
        r"co-?founders?|founders?|leaders?|leadership|members?|executive board)\s+"
        r"(?:(?:and|&)\s+(?:co-?\s?chairs?|members?|vice[- ]chairs?)\s+)?of\s+)?")
SPEAKS = re.compile(
    r"(?<!such )\b(?:as|we,?\s+the|we\s+are|on\s+behalf\s+of)\s+(?:the\s+)?" + ROLE
    + r"(?:the\s+)?(?:(?:bi-?partisan|u\.s\.)\s+)*(?=(?P<rest>.{0,240}))",
    re.I)
SUBJECT = re.compile(r"^\W*(?:the|our)\s+(?P<rest>.{0,80})", re.I)
VERB = re.compile(r"^\W*(?:is|are|writes?|requests?|urges?|would like|strongly|respectfully|"
                  r"has|have|was|were|calls?)\b", re.I)
PERSONAL = re.compile(r"district|\.(?:house|senate)\.gov|committee on|u\.s\. senator|"
                      r"united states senator|member of congress|congress(?:man|woman)\b", re.I)
CHAIRED = re.compile(r"\b(?:co-?\s?chair|chair(?:man|woman)?)\b", re.I)


def labels() -> list[str]:
    return list(dict.fromkeys(lab for _, lab in CAUCUSES))


LEAD = re.compile(r"(?:(?:u\.s\.\s+)?(?:house|senate|congressional)(?:\s+of\s+representatives['’]?)?\s+)+", re.I)


def _at_start(rest: str) -> list[tuple[str, int]]:
    """Caucuses named at the very start of ``rest``, with where each ends.

    The name as written first, so "Senate Western Caucus" is the Senate's;
    only when nothing matches is a leading House/Senate/Congressional set
    aside ("House Sustainable Energy and Environment Coalition")."""
    out = [(lab, m.end()) for p, lab in PATTERNS if (m := p.match(rest))]
    if not out and (lead := LEAD.match(rest)):
        out = [(lab, lead.end() + m.end()) for p, lab in PATTERNS
               if (m := p.match(rest[lead.end():]))]
    return out


def classify(text: str) -> tuple[list[str], str]:
    """([caucus labels], the rule that decided)."""
    text = committees.OCRFIX.sub(r"committee\1", text[:3500])
    found: list[str] = []
    s = committees.SALUTE.search(text[:3000])
    if s:
        opening = re.sub(r"\s+", " ", text[s.end(): s.end() + 350])
        first = re.split(r"(?<=[a-z0-9)])\.\s", opening, maxsplit=1)[0]
        for m in SPEAKS.finditer(first):
            # "your selection as the Chairman of ..." is written to the caucus.
            if re.search(r"\byour?\b", first[max(0, m.start() - 40): m.start()], re.I):
                continue
            rest = m.group("rest")
            # "the Congressional Hispanic Caucus, Congressional Black Caucus and ..."
            while True:
                hit = _at_start(rest)
                if not hit:
                    break
                lab, end = max(hit, key=lambda h: h[1])
                found.append(lab)
                nxt = re.match(r"\s*(?:,|and|&|,\s*and)\s+(?:the\s+)?(?:congressional\s+)?", rest[end:], re.I)
                if not nxt:
                    break
                rest = rest[end + nxt.end():]
        m = SUBJECT.match(first)
        if m:
            for lab, end in _at_start(m.group("rest")):
                if VERB.match(m.group("rest")[end:]):
                    found.append(lab)
        if found:
            return list(dict.fromkeys(found)), "opening sentence"
    # Caucus stationery opens with the caucus's name. A member's own
    # letterhead lists the caucuses they chair among their committees
    # ("CO-CHAIR, CONGRESSIONAL SHIPBUILDING CAUCUS" under the member's name
    # and district), which says nothing about this letter: 21 of 25 sampled
    # letterhead matches were that before this rule required the opening.
    d = committees.DATE.search(text)
    if d and d.start() >= 15:
        top = re.sub(r"\s+", " ", text[: d.start()])[:300]
        lead = re.match(r"\W{0,3}(?:the\s+)?", top).end()
        hit = _at_start(top[lead:])
        if hit and CHAIRED.search(top) and not PERSONAL.search(top) \
                and not re.search(r"honorable", top, re.I):
            return [max(hit, key=lambda h: h[1])[0]], "letterhead"
    return [], ""


def _stamp() -> list:
    return [RULES] + [[str(p), p.stat().st_size, int(p.stat().st_mtime)]
                      for p in committees.TEXTS if p.exists()]


def by_digest() -> dict[str, list]:
    """digest -> [[labels], rule] for every letter written as a caucus, cached in data/."""
    if CACHE.exists():
        try:
            cached = json.loads(CACHE.read_text(encoding="utf-8"))
            if cached.get("stamp") == _stamp():
                return cached["letters"]
        except (ValueError, KeyError):
            pass
    found: dict[str, list] = {}
    seen = set()
    for path in committees.TEXTS:
        if not path.exists():
            continue
        with path.open(encoding="utf-8-sig") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                d, t = r.get("digest"), r.get("text") or ""
                if not d or d in seen or len(t) < 50:
                    continue
                seen.add(d)
                labs, why = classify(t)
                if labs:
                    found[d] = [labs, why]
    tmp = CACHE.with_suffix(".tmp")
    tmp.write_text(json.dumps({"stamp": _stamp(), "letters": found}), encoding="utf-8")
    tmp.replace(CACHE)
    return found


if __name__ == "__main__":
    letters = by_digest()
    print(f"{len(letters)} letters written as a caucus", file=sys.stderr)
    print(Counter(e[1] for e in letters.values()), file=sys.stderr)
    for lab, n in Counter(lab for e in letters.values() for lab in e[0]).most_common():
        print(f"{n:6}  {lab}")
