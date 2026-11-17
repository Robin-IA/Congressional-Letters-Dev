# Deduplication: when two files are the same letter

16 November 2026. Robin asked for this after #139: "For duplication, are you
using checksum? Let's write a deduplication methodology." The checksum is the
first test, not the only one.

## The rule (Robin, 16 November 2026)

> Same letter on different members' sites is one multi-author letter and
> stays; only repeats by the same member are true duplicates.

So whether a copy counts as a duplicate depends on **who posted it**, not only
on whether the text matches:

| The same letter, posted… | Is | What happens |
|---|---|---|
| by **different members** | a **shared letter**: one multi-author letter | Every posting stays, credited to its member, and **references the others** ("Also posted by …", #41). Not a duplicate. |
| **more than once by one member** (a site moved, a file re-uploaded, the old and new address both captured) | a **true duplicate** | One copy is that member's primary (§4). The others are linked to it and shown once. |

A letter with **the same wording, signed and sent by different members as
their own letters** is neither. Example: Bilirakis and Estes each asking the
CAO to withhold their own pay, 1 October 2025. Each member wrote their own
letter, so these are separate letters, titled with the member (#586). *Robin
to confirm.*

## Why the checksum is not enough

Every letter's ID is its **digest**: the base32 SHA-1 of the file's bytes, as
the Wayback Machine records it. A checksum changes whenever one byte changes.
Re-saving a PDF, re-exporting it from Word, stamping new metadata or
rescanning it gives the same letter a new digest. Measured over the whole
corpus, 16 November 2026:

| | Count |
|---|---|
| Postings (one per URL a letter was captured at) | 113,815 |
| Distinct digests | 77,083 |
| Digests posted by two or more **different members**: shared letters already joined by the checksum | 7,109 |

Comparing **normalised text** (§3) finds the copies the checksum misses: 4,083
groups of digests with identical text but different checksums. Split by who
posted them:

| Identical-text groups | Groups | What they are |
|---|---|---|
| Each file posted by a different member | 2,086 | **Shared letters** to link, not duplicates |
| One member posted it more than once | 565 (591 extra copies) | **True duplicates** |
| Mixed: shared across members, and some member posted it twice | 1,432 | Both. Link across members; within a member, a duplicate. |

So the checksum's real gap is less about letters counted twice than about
**shared letters whose postings don't know about each other**. A letter
co-signed by nine senators and posted by each (`ZHDSI6DF`, #170) is one file.
The same letter re-saved by each office is nine files that nothing connects.

## 1. The levels: how alike two files are

These levels say **how alike** two files are. The rule above then says, from
**who posted them**, whether a pair is a duplicate or a shared letter.

| Level | How alike | Detected by | Same member | Different members |
|---|---|---|---|---|
| **0** | One file, several URLs for it: tracking parameters (`?utm_…`), `?download=`, a download page wrapping the PDF | `harvest.canonical()`; `resolve_wrappers.py` (#98) | Collapsed at harvest | Collapsed at harvest |
| **1** | Byte-identical | the same digest | Already one letter | **Shared**: already one digest, posted by each |
| **2** | Text-identical, different files | the same normalised-text hash | **Duplicate** | **Shared** |
| **3** | Near-identical: OCR or extraction noise, a dropped line, a missing page, an enclosure or reply in one copy | similarity ≥ 0.95 on the letter portion (§3), **and** the same date, addressee and signers | **Duplicate** | **Shared** |
| **4** | Versions: changed wording or signers, a draft and the sent letter | the same date and addressee, a real difference | **Two letters**, linked as versions | Two letters, linked as versions |
| **5** | Different letters that share a title or a file name | similarity < 0.90, or a different date, addressee or signers | Two letters | Two letters |

**The same text sent to different addressees** (one letter each to
EdFinancial, Nelnet, MOHELA…) is level 5. Each copy has its own recipient, so
each is its own letter.

## 2. Worked examples

### From issues

| Level | Issue | What it shows |
|---|---|---|
| 0 | #98, download wrappers | 564 letters were captured only as a site's download page. `resolve_wrappers.py` followed each page to its PDF, and `canonical()` keeps the PDF over the wrapper. |
| 1, shared | #170, dates from a byte-identical sibling | `ZHDSI6DF` (EPA's PFAS plan), one PDF posted by nine senators. It was dated from the file name at one address and by capture at the others. **3,913 postings of 2,216 shared letters were dated worse than a byte-identical sibling** until the digest carried the best date across. Linking a shared letter's postings is also how its date travels. |
| 1, one member | #126 and #139 | Warren's site moved `/imo/media/doc/` to `/wp-content/uploads/`, so `7RKLT4QP` was captured in 2023 and 2026. One digest, one member: one letter, and neither capture is its date. |
| 2 shared + 5 | #138, the Visa letters | `UP3TCZWK` (posted by Hern, Lamborn, Stefanik and Womack) and `ZHGVQVQD` (Tenney) are the same 5,198-character joint letter in two files: **one shared letter of five postings**. `5WAYSRG2` is Burchett's own 951-character letter with the same date and addressee: **a different letter**. Robin's rule: **if the bodies differ, the titles must.** |
| 4, one member | #183, TitleMax | `B3P2UUSH` (the draft: "March XX, 2023", "[ADDRESS BLOCK]") and `C3N75OU4` (the sent letter, 14 March 2023), both from the same member. Similarity 0.809, all from the unfilled template. A version: **open for Robin.** |
| 4 | #180, unfilled templates | 18 letters were published with placeholders. Where a sent version is in the corpus, the pair is level 4. |

### From the shared-title audit (#139)

| Verdict | Example | Digests (posted by) | Evidence |
|---|---|---|---|
| **Duplicate** (level 2) | Bair Island, to Secretary Norton, 21 Nov 2005 | `JAJZYXCW`, `P5RQOG7V` (both Stark) | 1.0. Stark's site moved from `house.gov/stark/` to `stark.house.gov`, and the PDF was re-saved |
| **Duplicate** (level 2) | SFRC Democrats to Chairman Risch, 9 Oct 2019 | `PB4ZPI2V`, `JLCQAKCX` (both Cardin) | 1.0. Cardin's file, re-uploaded under `/wp-content/uploads/` |
| **Duplicate** (level 3) | Waxman to the FAA on Santa Monica Airport, 26 May 2000 | `BFKGU4XF`, `WJU74CF2` (both Waxman) | 0.569 overall, but the same letter: one copy also carries the FAA's reply. **An enclosure or reply drags the score down; compare the letter portion.** The fuller copy is the primary. |
| **Shared** (level 2) | Resuming student loan payments, 18 Jul 2023 | `BUIQJ4BV` (Menendez), `7RKLT4QP` (Warren) | 1.0. One joint letter, two offices' files |
| **Shared** (level 1) | The credit bureaus, v2, 29 Jan 2019 | `ELW4RO46` (Menendez, Schatz, Tester) | One file, three members |
| **Shared** (level 3) | Bomb threats against Jewish community centers, 7 Mar 2017 | `TXBNL3SV` (5 senators), `XYNTT3DA` (3 more) | 0.802 from OCR of two-column signature pages; one letter, eight postings |
| **Shared** (level 3) | #224, `427NWMXS` / `FXGUTS52` | (4 members) / (King) | 0.99 or above |
| **Shared**; signed or typed open | Ebola, to President Obama, 8 Oct 2014 | `JIU3SNAV` (Pittenger, Stivers: unsigned, typed), `VEBRFFDK` (Marchant, Salmon: signed) | The same body and 26 signers. Whether a typed copy is a version: **Robin to confirm** |
| **Versions**, one member | Grassley to the AHA, 4 May 2011 | `LPGAN4HK`, `D5AXGHTA` (`-2`) | 0.917. The request changed between the two |
| **Versions** | The credit bureaus, 29 Jan 2019 | `I55JMZ3U` (v1), `ELW4RO46` (v2) | v2 adds Cortez Masto and Menendez, and two sentences |
| **Different letters** | Barbara Lee for caucus chair, 27 Nov 2018 | `M4VIBMRI`, `Z4XS7BXJ` | Former CBC chairs; Adam Smith |
| **Different letters** | The UN Arms Trade Treaty, 15 Oct 2013 | `2ZUWDJJH` (Senate), `LTMFZ7GE` (House) | Companion letters from each chamber |
| **Separate letters, same wording** | Withholding a member's pay, 1 Oct 2025 | `2MOPPHCQ` (Bilirakis), `EVUSVOYY` (Estes) | Each member's own letter about their own pay (see the rule) |
| **Not a letter** | The mercury rule, June 2004 | `QLAN4KHE` | The co-signer list of `5LG7T4HP`, posted separately (§5a). Goes to Robin. |

## 3. How to compare two texts

1. **Text:** each digest's longest text, from the text layer or the OCR
   (`data/letter-text.jsonl`, `data/letter-ocr.jsonl`).
2. **Normalise:** lowercase, and keep only letters and digits. The SHA-1 of the
   result is the level 2 hash.
3. **Similarity:** compare word sequences with `difflib.SequenceMatcher`
   (`autojunk=False`) over the first 1,500 words. OCR splits words
   ("Associa tion"), so characters are not compared. Compare the **letter
   portion**, from the date through the close.
   - **≥ 0.99:** the same letter, unless the signers differ.
   - **0.90–0.99:** read the differences. OCR noise, a dropped line or a
     missing page makes it level 3. Changed wording or signers makes it level 4.
   - **< 0.90:** read both. Of the 28 shared titles in this band (#139), 19 were
     the same letter, 4 were versions and 5 were different letters. The low
     scores came from an enclosure or reply in one copy, signature pages read
     in a different column order, a letterhead in one copy only, and signed
     copies against typed ones.
4. **Check the facts, not only the words:** the letter's own date, the
   addressee and the signature block. A different date or addressee makes a
   different letter. Different signers make a version.
5. **The file name is a clue:** `v2`, `-2`, `final`, `revised` and `draft`
   point to versions. #411 lets the file name help decide, never decide.
6. **Then the posters:** look up who posted each file
   (`build_congress.all_letters()`, `bioguide`). Different members means a
   shared letter, and one member means a duplicate.

## 4. A member's primary copy (true duplicates only)

When one member posted the same letter more than once, in this order:

1. The **more complete text**: all pages and the signature block present
   (#123), and the most readable characters.
2. A **text layer** over OCR, then the higher OCR confidence.
3. The **earliest capture**, which is the most likely to still replay.

The other copies keep their postings, since each is still a capture at its
own URL, and point to the primary. A shared letter has no primary: every
member's posting is the letter, from that member.

## 5. What is recorded

**A clear duplicate is a type of discard** (Robin, 17 November 2026, #1308; reviewed on #1309).
When the check above clearly finds a true duplicate (the same member posted
both files; similarity at least 0.99, or at least 0.95 with the same title,
date and addressee), the non-primary copy is recorded in
`letters-discarded/letters.csv` with a reason beginning "duplicate:" and the
primary it repeats, and in `vocabulary/letter-duplicates.csv`. The primary
stays. A pair the check cannot settle (under 0.95, or a different title) is a
**potential discard**: not done, Needs Review, with an issue, until it is
read. First run, 17 November 2026: of 230 copies noted by readers, 145 were
shared letters (different members, kept), 48 were clear duplicates
(discarded), and 16 wait on a reading.


- **`vocabulary/letter-duplicates.csv`**: one row per non-primary copy of a
  **true duplicate**, plus the version links (level 4).

  ```
  digest,same_as,level,similarity,evidence,source
  P5RQOG7VL4Q2OKEBM3MGNG6J6YEY45PD,JAJZYXCWLXVQXLS3UISJSCJ2O7MMHVQA,2,1.0,"Stark's old and new addresses",#139
  D5AXGHTAQH2G2XYPMIR5BMDBRYUE3VZ2,LPGAN4HK443UR4QFDXZZR572PLUUKCG4,4,0.917,"the -2 revision",#139
  ```

  Test rules:
  - every `same_as` exists;
  - no chains;
  - one row per digest;
  - at levels 2 and 3, both digests come from the same member (otherwise the
    pair is a shared letter, not a duplicate).
- **Shared letters: `vocabulary/letter-shared.csv`**, one row per group: a
  `group` id and the digests in it. Level 1 needs no row, because one digest
  posted by several members already joins them. The explorers read it to show
  "Also posted by …" on each posting, and to credit every posting member (#41).
- **Titles:** a duplicate shares its primary's title. A shared letter's files
  share one title. A version takes a distinguishing title ("… (Version 2, with
  Senators Cortez Masto and Menendez) …").

## 6. In the explorers

- **Shared letters (decided):** every posting stays, on every posting member's
  page, with "Also posted by" linking the others.
- **True duplicates:** shown once on the member's page, with its other files
  listed under it.
- **Open for Robin:**
  - how collection-wide totals count a shared letter: once, or once per
    member;
  - whether a typed or unsigned copy of a signed letter is a version or the
    same letter (Ebola).

## 7. In the monthly harvest (#542)

For each new digest:
1. Already in the corpus? (level 1)
2. Normalised-text hash against the corpus. (level 2)
3. Opening 300 normalised characters, then similarity on the candidates.
   (levels 3–4)

Then the posters decide:
- A match from **another member** joins that letter's shared group, and the
  new posting is read only for what differs (its member).
- A match from the **same member** is a duplicate row.
- A level 4 match, or anything between 0.90 and 0.99 not yet settled, goes on
  a **"Duplicate letter"** issue, as #542 asks.

## Related

#41 (multi-member letters credited to each signer), #98 (download wrappers),
#126 and #170 (dates through shared files), #138 (Visa), #139 (the shared-title
audit), #180 and #183 (drafts and templates), #224 (near-identical pairs),
#411 (the file name as evidence), #542 (the monthly harvest).
