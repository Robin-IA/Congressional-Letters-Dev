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
DATES = ROOT / "vocabulary" / "letter-dates.csv"
TOPICS_BY_HAND = ROOT / "vocabulary" / "letter-topics.csv"
RECIPIENTS_BY_HAND = ROOT / "vocabulary" / "letter-recipients.csv"
RELATED = ROOT / "vocabulary" / "letter-related.csv"
RULES = "2026-11-16a"  # change when the rules change, so the cache is redone

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


def related() -> list[tuple[str, str, str]]:
    """Letter-to-letter links made by hand: (digest, related, relation).

    vocabulary/letter-related.csv. "supports" says the first file is a
    supporting document for the second: the USGS's request to the FCC that
    Senator Cantwell posted beside her own letter citing it (#1207).
    """
    if not RELATED.exists():
        return []
    with RELATED.open(encoding="utf-8") as fh:
        return [(r["digest"], r["related"], r.get("relation") or "related")
                for r in csv.DictReader(fh) if r.get("digest") and r.get("related")]


# -------------------------------------------------------------- topics by hand

REVIEWS = ROOT / "vocabulary" / "reviews.csv"


def organizations_to_file_under() -> set[str]:
    """The reviewed organizations a letter can carry as a topic by hand.

    Robin, 15 November 2026: a letter to companies is filed under each company
    named in it (Delta, United, American and Southwest for one letter to four
    airline CEOs), and the company is the topic, never its chief executive.
    Only an organization reviews.csv accepts qualifies, so a misspelt name
    stops the build rather than publishing a stray term.

    There is no cap on these. tag() keeps at most 8 topics from a file name,
    but hand topics are added on top of whatever it finds; and a letter naming
    four or more companies carries every one of them (Robin, 15 November 2026).
    """
    with REVIEWS.open(encoding="utf-8") as fh:
        out = {r["target"].strip() for r in csv.DictReader(fh)
               if r.get("decision") == "merge" and r.get("kind") in ("organization", "office")
               and r.get("status") == "accepted" and (r.get("target") or "").strip()}
    # Names count as subjects (Robin, 17 November 2026; qa/QA-analysis-subject-
    # analysis.md): any committee, agency, office or organization the
    # vocabulary already holds, not only those added through reviews.csv.
    terms = ROOT / "vocabulary" / "terms.csv"
    if terms.exists():
        with terms.open(encoding="utf-8") as fh:
            out |= {r["label"] for r in csv.DictReader(fh)
                    if r.get("kind") in ("organization", "office") and r.get("status") == "preferred"}
    return out


SMALL_WORDS = {"a", "an", "the", "and", "but", "or", "nor", "for", "so", "yet",
               "at", "by", "in", "of", "on", "to", "up", "as", "via", "vs", "per",
               "from", "with", "into", "onto", "over"}


def title_form(title: str) -> str:
    """A hand title as a title (Robin, 16 November 2026): "On" and the subject
    in title case, then the rest unchanged.

        "Record-high fertilizer prices — to President Biden, 5 April 2022"
        -> "On Record-High Fertilizer Prices — to President Biden, 5 April 2022"

    Applied when the site is built, so the titles file needs no rewrite and a
    title already written this way is left as it is. A word with a capital or
    a digit after its first letter (H.R., COVID-19, K-12, iPhone) is kept.
    """
    if not title or " — " not in title:
        return title
    subject, rest = title.split(" — ", 1)
    words = subject.split()
    if not words:
        return title
    if words[0] == "On":
        return title
    if words[0] in ("The", "A", "An"):
        words[0] = words[0].lower()

    def cap(w: str, first: bool) -> str:
        def part(x: str) -> str:
            if not x or any(c.isupper() for c in x[1:]) or any(c.isdigit() for c in x):
                return x
            i = next((k for k, c in enumerate(x) if c.isalpha()), None)
            if i is None:
                return x
            return x[:i] + x[i].upper() + x[i + 1:]
        if not first and w in SMALL_WORDS:
            return w
        return "-".join(part(x) for x in w.split("-"))

    out = [w if k == 0 and w in ("the", "a", "an") else cap(w, k == 0)
           for k, w in enumerate(words)]
    return "On " + " ".join(out) + " — " + rest


def topics_by_hand() -> dict[str, list[str]]:
    """digest -> [topics], read from the letter and written by hand.

    topics_in() finds a topic when a letter says its distinctive words often
    enough, which is right for Medicare or Diabetes and silent about anything
    the rules do not name. A letter about the merchant category code for gun
    retailers is about firearms, payment processing and the Second Amendment,
    and no rule here knows that.

    These are added to whatever the rules find rather than replacing them, so
    a letter keeps the topics its text earns and gains the ones a reader saw.
    """
    if not TOPICS_BY_HAND.exists():
        return {}
    out: dict[str, list[str]] = {}
    with TOPICS_BY_HAND.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            tops = [t.strip() for t in (row.get("topics") or "").split(";") if t.strip()]
            if row.get("digest") and tops:
                out[row["digest"]] = tops
    return out


# --------------------------------------------------------------------- dates


# A reader's decision that a letter has no recipient: an open letter, a Dear
# Colleague handled by chamber elsewhere, a letter to a private person
# (Robin, 17 November 2026, #502). Written in letter-recipients.csv in place of
# a recipient, so the build neither shows one nor guesses one from the file
# name or the salutation, and progress counts the letter as filed.
NO_RECIPIENT = "(no recipient)"


def recipients_by_hand() -> dict[str, str]:
    """digest -> the recipient a reader found in the letter's address block (#357).

    vocabulary/letter-recipients.csv (digest, recipient, source). For names
    that mean a different person in each letter -- "Dear Mr. Smith" is
    Equifax's CEO in one and Chase's in another -- so ``reviews.csv``, which
    decides by name, cannot file them. The recipient is the office or the
    organization, never a private person (Robin, 15 November 2026). It wins
    over the file name and the salutation.
    """
    if not RECIPIENTS_BY_HAND.exists():
        return {}
    with RECIPIENTS_BY_HAND.open(encoding="utf-8", newline="") as fh:
        return {r["digest"]: r["recipient"].strip() for r in csv.DictReader(fh)
                if r.get("digest") and (r.get("recipient") or "").strip()}


def dates_by_hand() -> dict[str, tuple[str, str]]:
    """digest -> (date, precision), read from the letter and written by hand.

    The counterpart of by_hand() for dates. A letter puts its date on its
    letterhead; until the text was read we took the date from the file name,
    the PDF's metadata or the Wayback capture, and the first of those is not
    the letter's date -- it is when the file was posted or named. Measured
    against the letterhead, 768 letters given `day` precision from a file
    name are contradicted by the letter, and 8,996 dated by capture state a
    date of their own (#126).

    A date is a reader's job in the same way a title is: the letter can say
    "February 22, 2016" in its first paragraph while being dated 2 August
    2016, so the first date in the text is not always the letter's. Each row
    records in `source` where the date came from and what it replaced.
    """
    if not DATES.exists():
        return {}
    with DATES.open(encoding="utf-8") as fh:
        return {r["digest"]: (r["date"], r.get("precision") or "day")
                for r in csv.DictReader(fh) if r.get("date")}


# -------------------------------------------------------------------- cache

def _stamp() -> list:
    return [RULES] + [[str(p), p.stat().st_size, int(p.stat().st_mtime)]
                      for p in committees.TEXTS if p.exists()]


LETTERHEADS = ROOT / "data" / "letterhead-dates.json"


def letterhead_by_digest() -> dict[str, str]:
    """digest -> the date the letter puts on its own letterhead.

    Source 1 of the dating order, applied to every letter whose text we hold
    rather than only to the ones a reader has got to. The reading is
    audit_dates.letterhead_date(); this caches it, because it scans every
    letter's text and the result only changes when the text does.

    Robin, 15 November 2026: "Let's go with letterhead FIRST as that is the
    intent." A file name can be the date a draft was generated or filed --
    Quill names are wrong 54.2% of the time against the letterhead (#182) --
    and the date a reader searches for is the one printed on the letter.

    The caller applies the rule that a letter cannot postdate its own
    capture; this function does not know the capture.
    """
    stamp = _stamp()
    if LETTERHEADS.exists():
        try:
            cached = json.loads(LETTERHEADS.read_text(encoding="utf-8"))
            if cached.get("stamp") == stamp:
                return cached["dates"]
        except (ValueError, KeyError):
            pass
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import audit_dates  # noqa: PLC0415 - imported here to keep the module light

    out: dict[str, str] = {}
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
                if not d or d in seen or len(t) < 200:
                    continue
                seen.add(d)
                iso = audit_dates.letterhead_date(re.sub(r"\s+", " ", t).strip())
                if iso:
                    out[d] = iso
    tmp = LETTERHEADS.with_suffix(".tmp")
    tmp.write_text(json.dumps({"stamp": stamp, "dates": out}), encoding="utf-8")
    tmp.replace(LETTERHEADS)
    return out



# Recipients from the salutation (#97) -----------------------------------------
# A file name names its recipient on 44% of letters; the salutation names one
# on nine in ten that have text. Used only where the file name gave none
# (build_site.py). Checked 15 November 2026 on 30 random letters with no
# recipient: 27 named one and every one was the letter's addressee; one was
# cut at a comma ("Dear Chairman Cole, Ranking Member DeLauro"); the other 3
# were greetings ("Dear Sirs", "Dear Mr. Secretary") and are left blank,
# because they name no one. A letter written TO a member ("Dear
# Representative Young") is recorded as such (#175).
GENERIC = {"colleague", "colleagues", "friend", "friends", "sir", "sirs", "madam", "sir or madam",
           "madam or sir", "sir/madam", "sir and madam", "representative", "senator", "member",
           "members", "mr. secretary", "madam secretary", "mr. chairman", "madam chair",
           "madam chairwoman", "mr. chair", "chairman", "chair", "chairwoman", "secretary",
           "administrator", "commissioner", "director", "mr. speaker", "madam speaker",
           "ranking member", "leader", "governor", "mayor", "ambassador", "general",
           "attorney general", "judge", "colleague and friend", "all", "team", "reader",
           "editor", "supporter", "neighbor", "constituent", "fellow", "fellow american",
           "fellow americans", "mr", "mrs", "ms", "dr", "senators", "representatives",
           "chairmen", "chairs", "conferees", "leaders", "members of congress"}
SALUTATION = re.compile(r"\bdear\b\s*([^:,\n;]{2,80})[:,;]", re.I)


def salutation_recipient(text: str) -> str:
    """The recipient a letter's salutation names, or ''."""
    m = SALUTATION.search(text[:3000])
    if not m:
        return ""
    v = re.sub(r"\s+", " ", m.group(1)).strip(" .-")
    v = re.sub(r"^(?:the\s+)?(?:honorable|hon\.?)\s+", "", v, flags=re.I)
    if not re.match(r"[A-Za-z]", v) or len(v) > 70 or v.lower().rstrip(".") in GENERIC:
        return ""
    if re.search(r"\d|@|http|www\.", v):
        return ""
    return v


SALUTATIONS = ROOT / "data" / "letter-salutations.json"
SALUTATION_RULES = "2026-11-15a"


def salutation_by_digest() -> dict[str, str]:
    """digest -> the recipient the letter's salutation names; cached like the letterheads."""
    stamp = [SALUTATION_RULES] + _stamp()[1:]
    if SALUTATIONS.exists():
        try:
            cached = json.loads(SALUTATIONS.read_text(encoding="utf-8"))
            if cached.get("stamp") == stamp:
                return cached["recipients"]
        except (ValueError, KeyError):
            pass
    out: dict[str, str] = {}
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
                if not d or d in out or len(t) < 200:
                    continue
                who = salutation_recipient(t)
                if who:
                    out[d] = who
    tmp = SALUTATIONS.with_suffix(".tmp")
    tmp.write_text(json.dumps({"stamp": stamp, "recipients": out}), encoding="utf-8")
    tmp.replace(SALUTATIONS)
    return out


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
