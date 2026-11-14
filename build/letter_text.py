#!/usr/bin/env python3
"""A letter's topics read from its text, and titles written by hand.

**Health topics from the text** (Robin, 2026-11-13): a letter that mentions
Medicare, Medicaid or the Affordable Care Act carries that topic. The
agency's name is taken out first, or every letter addressed to the Centers
for Medicare & Medicaid Services would be about both programs. Diabetes
needs two mentions: a single one is nearly always a disease in a list
("cancer, heart disease, diabetes, Alzheimer's"), checked on ten of them
2026-11-13, and those letters are not about diabetes. About a third of the
Medicare, Medicaid and ACA letters mention the program once; tighten the
same way if those read as passing.

**Titles by hand** (vocabulary/letter-titles.csv: digest, title, source).
Titles were built from the file name before the letters' text was read, and
some file names say nothing: Chuck Grassley's "2011-05-04-ceg-letter-to-..."
gave the title "Ceg". Robin gave permission to override the file-name
title, in the form: briefly, the subject or concern, and to whom the letter
is written ("Industry funding — to American Diabetes Association").

Titles from the text by rule were tried and not kept: a "Re:" line is on
2 to 4 per cent of letters, and the letter's stated purpose ("We write to
urge ...") gave a title for 654 of 5,477 untitled letters, many unreadable
("Urging reject measures", "Ask for your assistance"). A title is a reader's
job, so the file holds titles written from the text by a reader.

Run directly for counts:  python build/letter_text.py
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import committees  # noqa: E402  (TEXTS, SALUTE, OCRFIX: one reading of a letter)

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "letter-text-info.json"
TITLES = ROOT / "vocabulary" / "letter-titles.csv"
RULES = "2026-11-13d"  # change when the rules change, so the cache is redone

# -------------------------------------------------------------------- topics

AGENCY = re.compile(r"cent(?:er|re)s? for medicare\s*(?:&|and)\s*medicaid(?: services)?|"
                    r"\bcms\b|medicare payment advisory commission|"
                    r"medicaid and chip payment and access commission", re.I)
TEXT_TOPICS = {
    "Medicare": re.compile(r"\bmedicare\b", re.I),
    "Medicaid": re.compile(r"\bmedicaid\b", re.I),
    "Affordable Care Act": re.compile(r"affordable care act|\bobamacare\b|\bACA\b"),
    "Diabetes": re.compile(r"\bdiabet(?:es|ic)\b|\binsulin\b|\bprediabetes\b", re.I),
}

# More topics from the text (Robin, 2026-11-13: "read more topics from the
# text and add them to the vocabulary"). Each needs three mentions of its own
# distinctive words; samples read at exactly three were on the topic. The
# broad words in topics.py ("gas", "school", "labor") are left out here, as
# they turn up in ordinary prose.
#
# Not tagged from the text, because names and boilerplate set them off at
# three mentions: Taxes ("taxpayer funds"), Housing and Agriculture (the
# THUD subcommittee and the Department), Veterans (the VA's name), Postal
# Service (post office boxes), Israel and Gaza (Rep. Steve Israel), Social
# Security (citations of the Social Security Act), Tobacco (the ATF's name),
# Tariffs ("Section 301" of the INA), and passing mentions for Russia,
# China, Ukraine, Afghanistan, Guns, Prisons, Elections and Aviation. Those
# want names taken out first, as AGENCY does for CMS.
_W = lambda body: re.compile(r"\b(?:" + body + r")\b", re.I)
TEXT_TOPICS.update({
    "COVID-19": _W(r"covid(?:-?19)?|coronavirus|sars-cov-2"),
    "Vaccines": _W(r"vaccines?|vaccinations?|immuni[sz]ations?"),
    "Opioids": _W(r"opioids?|fentanyl|naloxone|oxycontin|opiates?"),
    "Mental health": _W(r"mental health|behavioral health|suicides?"),
    "Abortion": _W(r"abortions?|mifepristone"),
    "Wildfires": _W(r"wildfires?|forest fires?"),
    "PFAS": _W(r"pfas|pfoa|pfos|forever chemicals?"),
    "Nuclear": _W(r"nuclear|uranium|radioactive"),
    "Climate": _W(r"climate change|global warming|greenhouse gas(?:es)?|climate crisis"),
    "Student loans": _W(r"student loans?|student debt|pell grants?"),
    "Crypto": _W(r"crypto(?:currency|currencies)?|bitcoin|stablecoins?|digital assets?"),
    "Immigration": _W(r"immigration|immigrants?|asylum|daca|deportations?|undocumented"),
    "Iran": _W(r"iran|iranian|tehran"),
    "Broadband": _W(r"broadband|digital divide"),
    "Railroads": _W(r"railroads?|railways?|amtrak|freight rail|passenger rail"),
    "Childcare": _W(r"child ?care|head start"),
})

MIN_MENTIONS = {"Diabetes": 2}
MIN_MENTIONS.update({lab: 3 for lab in TEXT_TOPICS
                     if lab not in ("Medicare", "Medicaid", "Affordable Care Act", "Diabetes")})


def topics_in(text: str) -> list[str]:
    flat = AGENCY.sub(" ", text)
    return [lab for lab, p in TEXT_TOPICS.items()
            if len(p.findall(flat)) >= MIN_MENTIONS.get(lab, 1)]


# -------------------------------------------------------------------- titles

def by_hand() -> dict[str, str]:
    if not TITLES.exists():
        return {}
    with TITLES.open(encoding="utf-8") as fh:
        return {r["digest"]: r["title"] for r in csv.DictReader(fh) if r.get("title")}


# -------------------------------------------------------------------- cache

def _stamp() -> list:
    return [RULES] + [[str(p), p.stat().st_size, int(p.stat().st_mtime)]
                      for p in committees.TEXTS if p.exists()]


def by_digest() -> dict[str, list[str]]:
    """digest -> [topics] for every letter whose text names one."""
    if CACHE.exists():
        try:
            cached = json.loads(CACHE.read_text(encoding="utf-8"))
            if cached.get("stamp") == _stamp():
                return cached["letters"]
        except (ValueError, KeyError):
            pass
    found: dict[str, list[str]] = {}
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
                tops = topics_in(t)
                if tops:
                    found[d] = tops
    tmp = CACHE.with_suffix(".tmp")
    tmp.write_text(json.dumps({"stamp": _stamp(), "letters": found}), encoding="utf-8")
    tmp.replace(CACHE)
    return found


if __name__ == "__main__":
    info = by_digest()
    print(f"{len(info)} letters with a topic from their text", file=sys.stderr)
    for lab, n in Counter(t for e in info.values() for t in e).most_common():
        print(f"{n:7}  {lab}")
    print(f"{len(by_hand())} titles written by hand", file=sys.stderr)
