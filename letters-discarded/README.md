# Discarded postings

The discard folder: every posting taken out of the reading, with a link to find
it again (`wayback_url`). Robin, 17 November 2026: "move them to the discards
folder so we can find them later."

The full step is [QA-analysis-letter-determination](../qa/QA-analysis-letter-determination.md),
part of the QA-Analysis-methodology; this README keeps the summary and the
file's format.

A posting goes here when it fails either test below. **The criteria are
Robin's, 17 November 2026** (#496, #515). They build on "This will be the
place to put letters that aren't letters" (16 November) and the Fried letter
(#1207).


**Duplicates are a type of discard** (Robin, 17 November 2026, #1308; reviewed on #1309). A
member's second copy of a letter they already posted, found clearly by the
duplication check (DEDUPLICATION.md), is recorded here with a reason
beginning "duplicate:" and the primary copy it repeats. Like every discard, it
is not done and falls under issues.

## The discard criteria

Ask the two questions in order. A posting that passes both is kept and read.

### 1. Is it a letter?

By the test in PC-READING.md §5a: an addressee, and a signer. **Discard** a
posting that is not a letter, whoever posted it:

- a **press or news release**, even one that quotes a member's letter in
  full (the letter is filed where it is posted as a letter; #515);
- a **resolution** (a town board, a legislative conference; #496);
- a **newsletter** or report to constituents;
- **bill text**, a Federal Register page, a floor statement or remarks;
- an **issue brief**, a report, a research memorandum or an instruction sheet;
- **testimony or a statement** submitted for a hearing or roundtable, even when
  headed "To:" a member, and a sworn **declaration** (PC batch 60, #1238);
- a **ceremonial greeting** with no addressee ("I send my warmest greetings
  to all those celebrating …") and a **web page** such as a welcome message;
- a **template** or sample letter with blank fields;
- **vendor quotes**, schedules and forms sent with a funding request;
- an **exhibit**: a bank statement, a check, a wire record, e-mail printouts,
  interview notes, a deposition, interrogatory answers, database printouts
  (the Government Reform files on #515);
- a "**Dear Employer**" reference (#498).

### 2. Does it belong to Congress?

A letter is **kept** if any one of these holds:

1. **It is by a member of Congress, or by a congressional group**: a
   committee, a caucus, a delegation or another group of members.
2. **It is to a member or congressional group, or names one**: a letter
   written to a member (#175), or one that refers to a member or a member's
   district.
3. **It is a supplement to a member's letter**: an enclosure, a reply, or a
   document the member's letter cites. It is linked to that letter in
   `vocabulary/letter-related.csv` (the USGS letter Cantwell cited; #1207).

**Both tests are decided by reading the letter's OCR**, not its file name or
title (Robin, 17 November 2026). Test 2's third point needs more than the
letter itself: before a letter is discarded under test 2, the posting
members' own letters are searched (their OCR) for any that cite it, as the
Cantwell letter cited the USGS request. `mac_read.py write` does this search
and leaves the letter out, for a closer reading, if anything turns up.

A letter for which **none** holds is **discarded**: correspondence between
other parties that a member happened to post (the Florida agriculture
department's letter to the Army Corps; #1207).

**A discard found to support a letter is restored** (Robin, #1289: "Doublecheck
discards for connection to a letter. If found, connect the discard to the
letter and process the discard, filing it."). It is linked to the letter in
`vocabulary/letter-related.csv` and its row here is taken out, so the reading
picks it up and files it. `build/mac/find_linked_letters.py discards` proposes
candidates from the test-2 discards made before the citation search above; a
reader confirms each, and `find_linked_letters.py apply` writes both changes.
This is the one case in which a row leaves this file.


**Campaign letters** (Robin, 17 November 2026, #411): **discard** a campaign
letter (campaign letterhead or site, "paid for by", fundraising) written
**outside** its author's service in Congress, before they took office or after
they left, with the reason "campaign letter outside congressional service".
A campaign letter written **while** they served is kept and read, its note
saying "campaign letter". A campaign letter whose date cannot be settled is
held for review, not discarded.
### Not reasons to discard

- **No text, or text too damaged to read.** The posting needs a fetch and
  OCR (#122, #559), not a decision. Discard it only once it has been read.
- **Only part of a letter** (a signature page, a middle page). It goes on
  #252.
- **A duplicate.** It follows DEDUPLICATION.md.
- **No date, or no named recipient.** It is filed anyway (PC-READING step B5,
  #498, #502).

## Who decides

**The Mac decides, by these criteria** (Robin, 17 November 2026: "You make
the discard decision"). The PC **proposes** a discard in an issue, one per
reading batch ("Reading batch N: proposed discards"); the Mac reads it,
decides each posting by the two tests, writes the rows here, comments its
decision on the issue and closes it. The Mac's own readers' not-letters are
decided and written in the same batch PR. A case the criteria do not settle
goes to Robin in an issue.

A row takes the posting out of the reading, not out of the collection:
nothing is removed or hidden from the explorers by a row here.

## The file

`letters.csv`, one row per posting:

| Column | |
| --- | --- |
| `digest` | the scan's digest |
| `title` | what the posting is, in a few words |
| `reason` | which test it fails, and why |
| `issue` | the issue where it was decided |
| `decided` | who decided, and when |
| `posted_by` | the member whose site posted it (the first posting found) |
| `wayback_url` | where to find it: the posting's capture on the Wayback Machine |

A digest here is not read again: the reading pick skips it, as it skips the
holds in `letters-vocabulary-needs/letters.csv`. Rows are added, never
reordered.
