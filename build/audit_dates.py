"""Audit every date written by hand against the full text of its letter.

A letterhead date sits before the salutation. A date in the body does not.
Taking the first date in the text is right most of the time and wrong often
enough to matter, so this prints, for each letter, every date the text
contains, where it sits relative to "Dear ...", and what we recorded.

    py -I audit_dates.py [digest12 ...]
"""
import csv, json, re, sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "build"))
import committees  # noqa: E402

MONTHS = ("january february march april may june july august september "
          "october november december").split()
ABBR = {m[:3]: i + 1 for i, m in enumerate(MONTHS)}
FULL = {m: i + 1 for i, m in enumerate(MONTHS)}

# "January 12, 2024" / "Jan. 12, 2024" / "January 12 2024".
#
# The spaces are optional, not required. Tesseract runs words together often
# enough that requiring one loses real letterheads: this corpus contains
# "July17,2020" and "Aprill5,2019" (an April 15 whose "1" was read as an "l",
# which the month's trailing [a-z]* then absorbs). Both are letterhead dates
# and both were invisible to a \s+ pattern.
MDY = re.compile(r"\b(" + "|".join(m[:3] for m in MONTHS) +
                 r")[a-z]*\.?\s*(\d{1,2})(?:st|nd|rd|th)?\s*,?\s*(\d{4})\b", re.I)
# "12 January 2024"
DMY = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s*(" +
                 "|".join(m[:3] for m in MONTHS) + r")[a-z]*\.?\s*,?\s*(\d{4})\b", re.I)
# "11/26/2024" or "1/12/24"
SLASH = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b")
# Not every letter says "Dear". Several open "Leader Schumer:", "Speaker
# Pelosi," or "Madam Speaker:", and one opens with a Re: line and "To Whom It
# May Concern". A salutation we fail to find puts the whole body in front of
# the cut, which is what made three letters look as though their letterhead
# disagreed with itself.
SALUTE = re.compile(
    r"\bDear\b|\bTo [Ww]hom\b|\bMadam\b|\bMr\. President\b|"
    r"\b(?:Majority |Minority |Republican |Democratic )?"
    r"(?:Leader|Speaker|Senator|Chairman|Chairwoman|Chair|Congressman|"
    r"Congresswoman|Governor|Secretary|Administrator|Commissioner)"
    r"\s+[A-Z][A-Za-z'-]+\s*[,:]", re.I)
WEEKDAY = re.compile(r"\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s*,?\s*"
                     r"(" + "|".join(m[:3] for m in MONTHS) + r")[a-z]*\.?\s+"
                     r"(\d{1,2})(?:st|nd|rd|th)?\b", re.I)


def found(text):
    """[(pos, iso, raw)] for every date the text states."""
    out = []
    for m in MDY.finditer(text):
        mo, d, y = ABBR[m.group(1)[:3].lower()], int(m.group(2)), int(m.group(3))
        out.append((m.start(), f"{y:04d}-{mo:02d}-{d:02d}", m.group(0)))
    for m in DMY.finditer(text):
        d, mo, y = int(m.group(1)), ABBR[m.group(2)[:3].lower()], int(m.group(3))
        out.append((m.start(), f"{y:04d}-{mo:02d}-{d:02d}", m.group(0)))
    for m in SLASH.finditer(text):
        mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        y = y + 2000 if y < 100 else y
        if 1 <= mo <= 12 and 1 <= d <= 31 and 1990 <= y <= 2030:
            out.append((m.start(), f"{y:04d}-{mo:02d}-{d:02d}", m.group(0)))
    seen, uniq = set(), []
    for pos, iso, raw in sorted(out):
        try:
            date.fromisoformat(iso)
        except ValueError:
            continue
        if (pos, iso) in seen:
            continue
        seen.add((pos, iso))
        uniq.append((pos, iso, raw))
    return uniq


def weekdays(text):
    """[(weekday, month, day, raw)] the letter asserts, for cross-checking a year."""
    return [(m.group(1), ABBR[m.group(2)[:3].lower()], int(m.group(3)), m.group(0))
            for m in WEEKDAY.finditer(text)]


def letterhead_date(text: str) -> str | None:
    """The date on the letterhead, or None when it cannot be read with confidence.

    Source 1 of the dating order: what the letter says about itself. Used by
    build_site.py through letter_text.letterhead_by_digest(), which caches it.

    Conservative on purpose. It declines unless

    * a salutation is found, so there is somewhere for the letterhead to end;
    * at least one date sits before it;
    * and every date before it is the same date. Where they differ the letter
      is citing something above its own salutation -- a Re: line naming an
      inauguration, a footnote the OCR hoisted to the top -- and which one is
      the letterhead is a reader's judgement, not a rule's.

    It does not check that the date precedes the capture; build_site.py does
    that, because only it knows the capture.

    Scored against the 405 day-precision dates read by hand: it produced a
    date for 355 of them and agreed with 352, 99.2%. All three disagreements
    are letters whose letterhead states a year that cannot be right -- the
    Jackson confirmation, the Eaton fire, the Speaker-Designate -- and a hand
    date outranks this, so those three keep the year a reader gave them.
    """
    sal = SALUTE.search(text)
    if not sal:
        return None
    head = {iso for pos, iso, _ in found(text) if pos < sal.start()}
    if len(head) != 1:
        return None
    iso = head.pop()
    try:
        year = date.fromisoformat(iso).year
    except ValueError:
        return None
    # The corpus runs 2000-2026. A letterhead outside this is an OCR misread,
    # like the FCC letter whose 2013 came out as 2073.
    return iso if 1995 <= year <= 2027 else None


def load_text():
    out = {}
    for p in committees.TEXTS:
        if not p.exists():
            continue
        with p.open(encoding="utf-8-sig") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                d, t = r.get("digest"), r.get("text") or ""
                if d and len(t) > 200 and d not in out:
                    out[d] = re.sub(r"\s+", " ", t).strip()
    return out


def main(only):
    texts = load_text()
    recorded = {r["digest"]: (r["date"], r.get("precision") or "day", r.get("source") or "")
                for r in csv.DictReader(
                    (ROOT / "vocabulary" / "letter-dates.csv").open(encoding="utf-8"))}
    reviewed, settled = {}, set()
    with (ROOT / "vocabulary" / "letters-reviewed.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            reviewed[r["digest"]] = r.get("note") or ""
            if (r.get("date_audited") or "").strip().lower() == "yes":
                settled.add(r["digest"])
    short = {d[:12]: d for d in reviewed}
    stored = {}
    for line in (ROOT / "data" / "letters-parsed.jsonl").open(encoding="utf-8"):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        stored.setdefault(r["digest"],
                          ((r.get("date_best") or "")[:10], r.get("date_precision") or ""))
    targets = [short[k] for k in (only or sorted(short)) if k in short]

    clean = flagged = quiet = 0
    notext = []
    for full in targets:
        t = texts.get(full)
        if not t:
            # Counted and named, never dropped. A check that skips what it
            # cannot read, and reports the same number either way, is how
            # #168 wasted two hours.
            notext.append(full[:12])
            continue
        dates = found(t)
        sal = SALUTE.search(t)
        cut = sal.start() if sal else len(t)
        head = [x for x in dates if x[0] < cut]
        body = [x for x in dates if x[0] >= cut]
        rec = recorded.get(full, (None, None, ""))[0]
        was, wasprec = stored.get(full, ("", ""))
        effective = rec or was
        wd = weekdays(t)

        why = []
        heads = {x[1] for x in head}
        if not dates:
            why.append(f"NO DATE IN TEXT (standing on {effective}, {wasprec or 'hand'})")
        elif not head:
            why.append(f"no date before the salutation (standing on {effective})")
        elif effective not in heads:
            why.append(f"standing on {effective} but the letterhead reads "
                       f"{sorted(heads)}")
        elif len(heads) > 1:
            why.append(f"{len(heads)} different dates before the salutation, "
                       f"{effective} among them")
        if wd:
            for name, mo, dd, raw in wd:
                yr = int((effective or "0000-01-01")[:4])
                for cand in (yr - 1, yr, yr + 1):
                    try:
                        if date(cand, mo, dd).strftime("%A").lower() == name.lower():
                            if cand != yr:
                                why.append(f"weekday {raw!r} fits {cand}, not {yr}")
                            break
                    except ValueError:
                        pass
        if not why:
            clean += 1
            continue
        # date_audited=yes in letters-reviewed.csv means a reader has already
        # read this letter whole and settled the question. Those letters keep
        # tripping the heuristics -- an undated letter stays undated, a letter
        # whose letterhead is wrong goes on being wrong -- so a settled case is
        # counted and not reprinted. Clear the column to make one speak again.
        if full in settled and not only:
            quiet += 1
            continue
        flagged += 1
        print(f"\n=== {full[:12]}  recorded={rec or '(none)'}")
        print(f"    note: {reviewed[full][:150]}")
        for w in why:
            print(f"    !! {w}")
        print(f"    before salutation: {[(x[1], x[2]) for x in head][:6]}")
        print(f"    after  salutation: {[(x[1], x[2]) for x in body][:6]}")
        if wd:
            print(f"    weekdays asserted: {[x[3] for x in wd][:4]}")
    if notext:
        print(f"\n{len(notext)} reviewed letters have no OCR text here, so their "
              f"dates cannot be checked:")
        for i in range(0, len(notext), 6):
            print("    " + "  ".join(notext[i:i + 6]))
    print(f"\n{clean} agree with their letterhead, {quiet} settled by an earlier "
          f"reading, {flagged} to look at, {len(notext)} unreadable, "
          f"of {len(targets)} reviewed letters")


if __name__ == "__main__":
    main(sys.argv[1:])
