# QA-analysis-letter-determination (step 1, REQUIRED)

Part of [QA-Analysis-methodology](QA-Analysis-methodology.md). **Every
posting gets this determination**, read from its OCR, never from its file
name or title. Robin's criteria (16–17 November 2026; #411, #496, #515,
#1207). The discard folder and its file are described in
[letters-discarded/README.md](../letters-discarded/README.md).

## Test 1: is it a letter?

A letter has **an addressee** (a person, office, company or organization:
an inside address, a salutation, "Dear Colleague") and **a signer** (a printed
name, or a signature standing in for it). A date and a named recipient are
preferred, not required. The addressee is where the recipient comes from
([QA-analysis-recipients](QA-analysis-recipients.md)).

**Not a letter, whoever posted it** → discard:
- a press or news release, even one quoting a member's letter in full;
- a resolution; a newsletter or report to constituents;
- bill text, a Federal Register page, floor remarks, a speech;
- an issue brief, report, research memorandum or instruction sheet;
- testimony or a statement for a hearing or roundtable, even headed "To:" a
  member; a sworn declaration;
- a ceremonial greeting with no addressee; a web page;
- a blank form or template with blank fields;
- vendor quotes, schedules or forms sent with a funding request;
- an exhibit (bank statement, check, e-mail printout, interview notes).

**A bundle** (several letters in one file) is decided as a whole: kept if any
letter in it passes test 2, and filed as one record (QA-analysis-text step 4;
Robin, 17 November 2026, #1226).

**Drafts** (Robin, 17 November 2026, #183, #180). A letter posted with its
template placeholders unfilled is still a letter, and kept:
- **Day left blank** ("July ___, 2018", "March XX, 2023") on a letter that is
  otherwise signed and addressed: an ordinary letter, dated to the month
  (QA-analysis-dates). Not a draft.
- **Unfinished draft**: the addressee or the signers are missing: a
  placeholder ("[ADDRESS BLOCK]", "[Company]", "[SIGNATURES]") or blank
  signature lines with no names. A missing date alone ("[DATE]" on a signed,
  addressed letter) is not a draft. Kept and **marked**: the title ends "— a draft"
  (QA-analysis-titles) and the note begins "Draft:". Search the posting
  member's letters for **the version that was sent**; when it is held, link
  the two in `vocabulary/letter-related.csv` with relation `draft_of` (draft
  first). The explorer then shows "Draft of: …" on the draft and "Sent
  version: …" on the letter. A draft is never discarded for being a draft.

**Still a letter**: a member's mail-merge or form letter to a class of people
("Dear Mayor/Chief", "Dear Recommender") is the member's correspondence; file
it with no recipient.

## Test 2: does it belong to Congress?

A letter is **kept** if any one holds:

1. **By a member or a congressional group** (committee, caucus, delegation,
   group of members).
2. **To a member or group, or naming one**: a letter written to a member
   (title it with the sender, #175), or naming a member, a member's district,
   or a congressional delegation ("Nevada's congressional delegation").
3. **A supplement to a member's letter**: an enclosure, a reply, a document
   the member's letter cites, or a letter on the same matter that the member
   posted with their own letter.

A letter for which **none** holds is discarded.

### The supplement search (required before any test-2 discard)

The letter alone cannot show point 3. Search the OCR of every letter by the
posting member for the letter's distinctive words (sender, subject, case
name), and **read each candidate**:

- A member's letter on the same matter, posted with it → **keep, file, and
  link** in `vocabulary/letter-related.csv` (relation `supports`). Examples:
  the USGS request cited by Cantwell (#1207); HHS's notice to Teaching and
  Mentoring Communities and Cuellar's letter on the grantee; Hua Qu's letter
  to President Trump and Smith's letter to Pompeo on her husband.
- No candidate refers to it → discard, recording in the note what was read
  (`"supplement_checked": true` for the Mac's writer).

`mac_read.py write` runs the search and holds any test-2 discard it finds
candidates for.

## Who decides

The Mac decides discards by these tests (Robin, 17 November 2026). The PC
proposes them in one issue per batch ("Reading batch N: proposed discards").
A discard takes a posting out of the reading, not out of the collection.
