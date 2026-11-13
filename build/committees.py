#!/usr/bin/env python3
"""Which letters were written on a committee's behalf, read from the letter.

Nothing in a letter's address says so: Henry Waxman's letters to the FDA's
Commissioner von Eschenbach are on waxman.house.gov whether he wrote them as
the member for Los Angeles or as Chairman of the Committee on Oversight and
Government Reform. The letterhead says which.

A committee's name in the text is not enough. A member's own letterhead
lists the committees they sit on ("COMMITTEES: FINANCE, BUDGET …"), and
the address block names the committee the letter is sent *to*. Measured
2026-11-13, about 6,900 letters name a committee above the address and
fewer than one in six of those is committee stationery. So a letter counts
only on positive evidence that a member's stationery does not carry, read
from the text above the letter's date:

  - the majority and minority telephone lines a House committee prints;
  - the committee's roster: five or more "NAME, STATE" pairs;
  - the page opening with the committee's own name, and nothing personal
    (a district, a "COMMITTEES:" list, a member's website) above the date;
  - a chairman and a ranking member named together, with nothing personal;

or, when the letterhead was an image the text does not include, the first
sentence after the salutation speaking as the committee ("The Committee on
Oversight and Government Reform ... will be conducting oversight", "As
Chairman of the Committee on ...").

Checked by hand 2026-11-13: 65 of 65 sampled letterhead matches, across
every rule, were committee stationery. What it misses is letters whose text
has no letterhead and does not open as the committee.

The chamber is the letterhead's own (a Senate office building, "House of
Representatives"), and only when that is silent the website's. Committees
that renamed (Government Reform; Oversight and Government Reform; Oversight
and Accountability) are one committee, under one name.

Run directly for counts:  python build/committees.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXTS = [ROOT / "data" / "letter-text.jsonl", ROOT / "data" / "letter-ocr.jsonl"]
CACHE = ROOT / "data" / "letter-committees.json"
RULES = "2026-11-13a"  # change when the rules change, so the cache is redone

# pattern, chamber ("any" = the letterhead's chamber), label ({C} = that chamber)
COMMITTEES = [
    (r"committee on agriculture, nutrition,? (?:and|&) forestry", "Senate", "Senate Committee on Agriculture, Nutrition, and Forestry"),
    (r"committee on agriculture\b(?!,)", "House", "House Committee on Agriculture"),
    (r"committee on appropriations", "any", "{C} Committee on Appropriations"),
    (r"committee on armed services", "any", "{C} Committee on Armed Services"),
    (r"committee on (?:the )?budget", "any", "{C} Committee on the Budget"),
    (r"committee on banking, housing,? (?:and|&) urban affairs", "Senate", "Senate Committee on Banking, Housing, and Urban Affairs"),
    (r"committee on (?:banking and )?financial services", "House", "House Committee on Financial Services"),
    (r"committee on commerce, science,? (?:and|&) transportation", "Senate", "Senate Committee on Commerce, Science, and Transportation"),
    (r"committee on energy (?:and|&) commerce", "House", "House Committee on Energy and Commerce"),
    (r"committee on energy (?:and|&) natural resources", "Senate", "Senate Committee on Energy and Natural Resources"),
    (r"committee on environment (?:and|&) public works", "Senate", "Senate Committee on Environment and Public Works"),
    (r"committee on finance\b", "Senate", "Senate Committee on Finance"),
    (r"committee on foreign relations", "Senate", "Senate Committee on Foreign Relations"),
    (r"committee on (?:foreign affairs|international relations)", "House", "House Committee on Foreign Affairs"),
    (r"committee on health, education, labor,? (?:and|&) pensions", "Senate", "Senate Committee on Health, Education, Labor, and Pensions"),
    (r"committee on homeland security (?:and|&) governmental affairs|committee on governmental affairs", "Senate", "Senate Committee on Homeland Security and Governmental Affairs"),
    (r"committee on homeland security\b(?! (?:and|&))", "House", "House Committee on Homeland Security"),
    (r"committee on indian affairs", "Senate", "Senate Committee on Indian Affairs"),
    (r"committee on (?:the )?judiciary", "any", "{C} Committee on the Judiciary"),
    (r"committee on rules (?:and|&) administration", "Senate", "Senate Committee on Rules and Administration"),
    (r"committee on rules\b(?! (?:and|&|of))", "House", "House Committee on Rules"),
    (r"committee on small business", "any", "{C} Committee on Small Business"),
    (r"committee on veterans'? ?affairs", "any", "{C} Committee on Veterans' Affairs"),
    (r"committee on ways (?:and|&) means", "House", "House Committee on Ways and Means"),
    (r"committee on (?:education (?:and|&) (?:the )?workforce|education (?:and|&) labor)", "House", "House Committee on Education and the Workforce"),
    (r"committee on (?:the )?(?:natural )?resources\b", "House", "House Committee on Natural Resources"),
    (r"committee on (?:oversight (?:and|&) (?:government )?reform|oversight (?:and|&) accountability|government reform)", "House", "House Committee on Oversight"),
    (r"committee on science(?:, space,? (?:and|&) technology| (?:and|&) technology)?\b", "House", "House Committee on Science, Space, and Technology"),
    (r"committee on transportation (?:and|&) infrastructure", "House", "House Committee on Transportation and Infrastructure"),
    (r"committee on house administration", "House", "Committee on House Administration"),
    (r"(?<!select )committee on (?:ethics|standards of official conduct)", "House", "House Committee on Ethics"),
    (r"select committee on ethics", "Senate", "Senate Select Committee on Ethics"),
    (r"(?<!permanent )select committee on intelligence", "Senate", "Senate Select Committee on Intelligence"),
    (r"permanent select committee on intelligence", "House", "House Permanent Select Committee on Intelligence"),
    (r"special committee on aging", "Senate", "Senate Special Committee on Aging"),
    (r"select committee on the climate crisis", "House", "House Select Committee on the Climate Crisis"),
    (r"select committee on (?:energy independence (?:and|&) )?global warming", "House", "House Select Committee on Energy Independence and Global Warming"),
    (r"select committee on the modernization of congress", "House", "House Select Committee on the Modernization of Congress"),
    (r"select subcommittee on the coronavirus", "House", "House Select Subcommittee on the Coronavirus Crisis"),
    (r"select committee on (?:the )?(?:strategic competition|chinese communist party|ccp)", "House", "House Select Committee on the Chinese Communist Party"),
    (r"joint economic committee", "Joint", "Joint Economic Committee"),
    (r"joint committee on taxation", "Joint", "Joint Committee on Taxation"),
]
PATTERNS = [(re.compile(p, re.I), ch, lab) for p, ch, lab in COMMITTEES]


def labels() -> list[str]:
    """Every committee this can name, House and Senate both for a shared name."""
    out = []
    for _, ch, lab in COMMITTEES:
        for c in (("House", "Senate") if ch == "any" else (ch,)):
            out.append(lab.replace("{C}", c))
    return list(dict.fromkeys(out))


def chamber(label: str) -> str:
    """House, Senate or Joint, for placing a committee."""
    if label == "Committee on House Administration":
        return "House"
    return label.split()[0] if label.split()[0] in ("House", "Senate", "Joint") else ""


def informal(label: str) -> str:
    """'House Committee on Ways and Means' -> 'House Ways and Means Committee'."""
    m = re.fullmatch(r"(House|Senate) Committee on (?:the )?(.+)", label)
    return f"{m.group(1)} {m.group(2)} Committee" if m else ""


MONTH = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?"
DATE = re.compile(rf"\b{MONTH}\s+\d{{1,2}}\s*,?\s*(?:19|20)\d\s?\d\b"
                  r"|\b\d{1,2}/\d{1,2}/(?:19|20)?\d\d\b", re.I)
STATES = ("alabama|alaska|arizona|arkansas|california|colorado|connecticut|delaware|"
          "florida|georgia|hawaii|idaho|illinois|indiana|iowa|kansas|kentucky|louisiana|"
          "maine|maryland|massachusetts|michigan|minnesota|mississippi|missouri|montana|"
          "nebraska|nevada|new hampshire|new jersey|new mexico|new york|north carolina|"
          "north dakota|ohio|oklahoma|oregon|pennsylvania|rhode island|south carolina|"
          "south dakota|tennessee|texas|utah|vermont|virginia|washington|west virginia|"
          "wisconsin|wyoming")
ROSTER = re.compile(rf"[A-Z][A-Za-z.'\- ]{{3,40}}[,.]\s+(?:{STATES})\b", re.I)
PHONES = re.compile(r"(?:majority|minority)\s*[:\-]?\s*\(?202", re.I)
PERSONAL = re.compile(
    r"committees?\s*:|comm\w*ees\b|district|at-large|subcommittee|u\.s\. senator|"
    r"united states senator|member of congress|\.(?:house|senate)\.gov|website|office\s*:", re.I)
CHAIR = re.compile(r"\bchair(?:man|woman)?\b", re.I)
RANK = re.compile(r"\branking (?:minority |republican |democratic )?member\b", re.I)
OPENS = re.compile(r"\W{0,3}(?:u\.s\. |united states )?(?:house |senate )?"
                   r"(?:permanent |special |select )?(?:joint )?committee", re.I)
# OCR's spellings of the word: "COMMllTEE", "COMMITIEE", "C0MMITTEE".
OCRFIX = re.compile(r"\bc[o0]m{1,2}[il1!|t]{1,4}e{1,2}(s?)\b", re.I)
SALUTE = re.compile(r"\bdear\b[^:,\n]{0,60}[:,;]", re.I)
BODY = re.compile(
    r"^\W*(?:the|our) (?:(?:house|senate) )?(?:permanent |special |select )?committee on "
    r"[^.]{0,120}?\b(?:is|are|will|has (?!(?:exclusive )?jurisdiction)\w+|have \w+|"
    r"requests?|writes?|seeks?)\b"
    r"|^\W*(?:as|in my capacity as) (?:the )?(?:chair(?:man|woman)?|ranking (?:minority )?member|"
    r"vice chair(?:man)?) of the (?:(?:house|senate) )?(?:permanent |special |select )?committee on",
    re.I)


def _chamber_of(flat: str, host: str) -> str:
    s = len(re.findall(r"united states senate|dirksen|russell|hart senate|\bsenate\b", flat, re.I))
    h = len(re.findall(r"house of representatives|rayburn|longworth|cannon|ford house", flat, re.I))
    if s != h:
        return "Senate" if s > h else "House"
    return "Senate" if "senate" in host else "House" if "house" in host else ""


def _named(flat: str, ch: str) -> list[str]:
    """The committees named, in the order they appear."""
    hits = sorted((m.start(), lab) for p, c, lab in PATTERNS
                  if c in ("any", ch, "Joint") and (m := p.search(flat)))
    out = [lab.replace("{C}", ch) for _, lab in hits]
    return [lab for lab in dict.fromkeys(out) if not lab.startswith(" ") and "{C}" not in lab]


def classify(text: str, host: str = "") -> tuple[str | None, str]:
    """(committee label or None, the rule that decided)."""
    text = OCRFIX.sub(r"committee\1", text[:3500])
    m = DATE.search(text)
    if m and m.start() >= 15:
        flat = re.sub(r"\s+", " ", text[: m.start()])
        labs = _named(flat, _chamber_of(flat, host))
        if labs:
            roster = len(ROSTER.findall(flat))
            personal = PERSONAL.search(flat)
            why = ("majority/minority phones" if PHONES.search(flat)
                   else "roster" if roster >= 5
                   else "opens with committee name" if OPENS.match(flat) and not personal
                   else "chair and ranking member" if CHAIR.search(flat) and RANK.search(flat)
                   and not personal and roster >= 2
                   else "")
            if why and not (len(labs) > 1 and why in ("opens with committee name",
                                                      "chair and ranking member")):
                return labs[0], why
    s = SALUTE.search(text[:3000])
    if s:
        opening = re.sub(r"\s+", " ", text[s.end(): s.end() + 400])
        if BODY.search(opening):
            labs = _named(opening[:200], _chamber_of(opening, host))
            if labs:
                return labs[0], "opening sentence"
    return None, ""


def _stamp() -> list:
    return [RULES] + [[str(p), p.stat().st_size, int(p.stat().st_mtime)] for p in TEXTS if p.exists()]


def by_digest() -> dict[str, list[str]]:
    """digest -> [label, rule] for every committee letter, cached in data/.

    A letter on more than one site is classified once, by its text alone
    where the letterhead names its chamber; the website's chamber decides
    only the rest, so the cache keeps both answers for those."""
    if CACHE.exists():
        try:
            cached = json.loads(CACHE.read_text(encoding="utf-8"))
            if cached.get("stamp") == _stamp():
                return cached["letters"]
        except (ValueError, KeyError):
            pass
    found: dict[str, list[str]] = {}
    seen = set()
    for path in TEXTS:
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                d, t = r.get("digest"), r.get("text") or ""
                if not d or d in seen or len(t) < 50:
                    continue
                seen.add(d)
                house, why_h = classify(t, "house.gov")
                senate, why_s = classify(t, "senate.gov")
                why = why_h or why_s
                if house or senate:
                    found[d] = [house or "", senate or "", why]
    tmp = CACHE.with_suffix(".tmp")
    tmp.write_text(json.dumps({"stamp": _stamp(), "letters": found}), encoding="utf-8")
    tmp.replace(CACHE)
    return found


def committee_for(entry: list[str] | None, host: str) -> str:
    if not entry:
        return ""
    house, senate, _ = entry
    return (senate if "senate" in (host or "") else house) or house or senate


if __name__ == "__main__":
    letters = by_digest()
    print(f"{len(letters)} letters written on a committee's behalf", file=sys.stderr)
    for (lab, n) in Counter(e[0] or e[1] for e in letters.values()).most_common():
        print(f"{n:6}  {lab}")
    print(Counter(e[2] for e in letters.values()), file=sys.stderr)
