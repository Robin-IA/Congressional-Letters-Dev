# QA-Analysis-methodology

**The step-by-step analysis every letter gets, from its OCR text to its filing,
for anyone doing the work: the PC, the Mac, a person, or any model.** Written
17 November 2026 from Robin's instructions and from the reading done so far
(PC batches 1–60, Mac 106th–115th batches 1–19).

Each step has its own document. Follow them **in order, for one letter at a
time, all the way through**: one pass, no second visit. Steps 0–2 and 4–6 are
REQUIRED for every letter. Step 3 is not a separate requirement: the
recipient is a criterion of step 1 and, except for Congress, a name in step 4
(Robin, 17 November 2026).

| Step | Document | Decides |
| --- | --- | --- |
| 0 | [QA-analysis-text](QA-analysis-text.md) | Is the text good enough to read? Partial, garbled, upside-down, bundled? |
| 1 | [QA-analysis-letter-determination](QA-analysis-letter-determination.md) | Is it a letter? Is it congressional, to a member, or a supplement to a member's letter? Otherwise it is discarded. |
| 2 | [QA-analysis-authorship](QA-analysis-authorship.md) | Who wrote it; which members it files under. |
| 3 | [QA-analysis-recipients](QA-analysis-recipients.md) | Whom it is to: members, committees and caucuses "As recipient"; everyone else a name under its organization or office. |
| 4 | [QA-analysis-subject-analysis](QA-analysis-subject-analysis.md) | **At least 4 subjects, at least 2 of them topics**: topics, plus the organizations, companies, committees, laws and bills it names. |
| 5 | [QA-analysis-dates](QA-analysis-dates.md) | Its date, and how sure. |
| 6 | [QA-analysis-titles](QA-analysis-titles.md) | Its standardized title ("Letter Name Fix"). |
| 7 | this document, below | Record it; hold it or file an issue if needed; run the QA checks. |

The procedures that carry this out are [PC-READING.md](../PC-READING.md) (the
PC, 116th–119th) and [MAC-READING.md](../MAC-READING.md) (the Mac,
106th–115th). Where they and these documents differ, **these documents win**,
and the procedure is corrected.

Related: [DEDUPLICATION.md](../DEDUPLICATION.md) (the same letter in several
files), [letters-discarded/README.md](../letters-discarded/README.md) (the
discard folder), [METHODOLOGY.md](../METHODOLOGY.md) (harvest, roster,
holders).

## Roles

The methodology is the same for everyone; what differs is what each role may
change. Today the **PC** is the contributor and the **Mac** the maintainer.
After this project the contributor role may be opened to Internet Archive staff
or, with permission, the public (Robin, 17 November 2026), so the roles are
defined by what they do, not by machine:

| | Contributor (today: the PC; [PC-READING](../PC-READING.md)) | Maintainer (today: the Mac; [MAC-READING](../MAC-READING.md)) |
| --- | --- | --- |
| Reads letters by steps 0–6 | yes | yes |
| Writes rows for letters it can file | yes, in a PR | yes |
| Missing vocabulary | holds the letter; lists it on the batch's "vocabulary needed" issue | adds the term or subject and its place in the hierarchy |
| Discards | proposes (holds the letter, lists it on the batch's discards issue) | decides by the criteria and records it |
| Any other issue about a letter | holds the letter and files the issue | resolves the issue, files the letter, closes the issue |
| Merges | never | after the tests and the holder check pass |

A contributor needs only these documents, the text repository and the
vocabulary files; everything that changes the vocabulary, the rules or the
published explorers belongs to the maintainer.

## The vocabulary rule

Every recipient and subject is a term of the controlled vocabulary. When a
letter needs a term that does not exist:

- **The Mac adds it**: a `reviews.csv` merge row with its kind and `broader`
  node, and a `hierarchy.csv` row (building a state chain if needed), then
  files the letter in the same PR (Robin, 17 November 2026).
- **The PC holds the letter**: a row in `letters-vocabulary-needs/letters.csv`.
  Missing **names and subjects** go in **one issue per batch**, "Reading batch
  N: vocabulary needed", label `vocabulary`, in two sections (Robin,
  17 November 2026). The Mac adds them in one vocabulary PR, files the held
  letters and closes the issue.

A letter is never filed under a nearby term to avoid a hold.

## Step 7: record, hold, issue, check

**Record** one row per letter in each file (CSV, appended, `\n` line endings):
`letter-titles.csv`, `letter-topics.csv`, `letter-recipients.csv`,
`letter-dates.csv` (only when the date changes), `letters-reviewed.csv`
(always), and `letter-related.csv` for a supplement or reply linked to a
member's letter. A discarded posting gets a row in `letters-discarded/` with
its Wayback link, written by the Mac.

**Hold** a letter only for a missing term (PC) or a decision the rules do not
cover. Never hold it for a date or a missing addressee: those have rules.

**File an issue** for anything that cannot be resolved: a missing term (PC),
unreadable text needing OCR, a bundle, a rule that does not exist, or a
posting credited to the wrong member. Name the digest, the posting member and
file, and what was read.

**An issue holds its letter** (Robin, 17 November 2026). A reader who files an
issue about a letter writes only its hold row (`letters-vocabulary-needs/
letters.csv`, with the issue number) and no other rows. **The Mac resolves the
issue, files the letter, and closes the issue.** A held letter is never filed
by the reader who held it.

**QA checks**, all of which must pass before a batch is merged:

1. Every row's title matches its own letter's text (the writer's title
   guard). A reader writing one letter's reading under another's digest is the
   failure this catches (Mac batch 3).
2. Every recipient and subject is a vocabulary term or is added in the same PR.
3. Every letter has **at least 4 subjects, at least 2 of them topics** (step 4).
4. Every date is a full ISO date with a precision, and no later than the
   file's first capture.
5. The tests pass: `python3 -m unittest discover -s tests` must say OK.
6. The holder check passes at merge (`fold.sh`): every date leaves the posting
   with a member who held the address, and each author held office (and any
   committee post the letter claims) on its date (QA-analysis-authorship
   step 5).
7. Every discard was decided from the OCR, by both tests, with the supplement
   search for test 2.

## Status values (the QA status CSVs)

`qa-status/<N>th.csv` in the **letters-from-congress-OCR** repository, one
per Congress, one row per posting, rebuilt at each publish by
`build/qa_status.py`. Columns: Congress, Letter URL, Letter name (original),
Discarded (Y/N), Letter Name Fix, Authors (`;`), Subjects (`;`), Dates,
Recipients, OCR (Y/N), Filed? (Filed / Hold / Unprocessed / Needs Review),
Issue (Y/N). A discarded posting is Filed with Discarded = Y.

- **Filed**: read, every step done, recorded.
- **Hold**: waiting on a vocabulary term or a decision.
- **Unprocessed**: not yet read.
- **Needs Review**: read, but short of a requirement (fewer than 4 subjects or
  fewer than 2 topics,
  #1266), or set aside as partial, bundled or unreadable (#252, #1226).
