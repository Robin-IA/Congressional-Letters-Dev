# Deduplication: when two files are the same letter

Draft, 16 November 2026. Robin asked for this after #139: "For duplication,
are you using checksum? Let's write a deduplication methodology." The checksum
is the first test, not the only one. This document sets out the five
relationships two files can have, how each is detected, and what is recorded.
Each level comes with worked examples from the corpus.

**What is decided and what is not.** Levels 1 and 5 describe current practice.
Levels 2–4, the comparison thresholds and `vocabulary/letter-duplicates.csv`
are **proposed**. So is how the explorers show a duplicate (§6), which is
Robin's call. Until it is decided, no letter is hidden or deleted.

## Why the checksum is not enough

Every letter's ID is its **digest**: the base32 SHA-1 of the file's bytes, as
the Wayback Machine records it. That deduplicates exact copies. Measured over
the whole corpus on 16 November 2026:

| | Count |
|---|---|
| Postings (one per URL a letter was captured at) | 113,815 |
| Distinct digests, i.e. letters as the explorers count them | 77,083 |
| Digests posted at more than one URL | 23,130 |

A checksum changes whenever one byte changes. Re-saving a PDF, re-exporting
it from Word, stamping new metadata, or rescanning it gives the same letter a
new digest. Comparing **text** finds those:

| Of the 76,590 digests with 300+ characters of text | Groups | Digests |
|---|---|---|
| Identical text after normalising (§3), different digests | 4,102 | 9,222 |
| The same first 300 normalised characters: candidates for levels 2–4 | 5,420 | 13,727 |

So about 5,100 digests are extra copies of letters already counted, which is
roughly 7% of the corpus. The checksum misses them all.

## 1. The five relationships

| Level | Relationship | Detected by | What happens |
|---|---|---|---|
| **0** | **One file, several URLs for it**: tracking parameters (`?utm_…`), `?download=`, and a site's download page wrapping the PDF | `harvest.canonical()` at harvest time; `resolve_wrappers.py` for wrappers | Collapsed before a digest is ever recorded, so the PDF stands in for its wrapper (#98) |
| **1** | **Byte-identical**: one file posted at several URLs | same digest | Already one letter. Its postings are listed under it, and each posting member is credited. |
| **2** | **Text-identical**: the same letter in different files | same normalised-text hash | Duplicates: one letter, one primary (§4) |
| **3** | **Near-identical**: the same letter, with differences only from OCR or extraction (noise, a dropped line, a missing page) | similarity ≥ 0.95 (§3), **and** the same date, addressee and signers | Duplicates, as level 2 |
| **4** | **Versions**: the same letter changed in substance (wording, signers, a draft and the sent letter) | same date and addressee, but a real difference in wording or signers | **Two letters.** Both are kept, titled to tell them apart, and linked as versions. |
| **5** | **Different letters** that happen to share a title or a file name | similarity < 0.90, or a different date, addressee or signers | Two letters. Each gets its own title. |

Something that looks like a duplicate but isn't: **the same text sent to
different addressees** (one letter each to EdFinancial, Nelnet, MOHELA…). Each
copy has its own recipient, so each is its own letter (level 5), even when the
bodies match word for word.

## 2. Worked examples (16 November 2026)

### From closed and open issues

| Level | Issue | What it shows |
|---|---|---|
| 0 | #98, download wrappers | 564 letters were first captured only as a site's download page. `resolve_wrappers.py` followed each page to its PDF, and `canonical()` keeps the PDF over the wrapper, so the page and the file are one letter. |
| 1 | #170, dates from a byte-identical sibling | One PDF posted by Shaheen and Baldwin (`ZHDSI6DF`), dated from the file name at one address and by capture at the others. **3,913 postings of 2,216 letters were dated worse than a byte-identical sibling** until the digest was used to share the best date. Level 1 dedup is also how a date travels. |
| 1 | #126 and #139, one file and two capture dates | Warren's site moved `/imo/media/doc/` to `/wp-content/uploads/`, so `7RKLT4QP` was captured in 2023 and again in 2026. One digest, so one letter; neither capture is its date. |
| 2 + 5 | #138, the Visa letters | One title covered three digests. `UP3TCZWK` and `ZHGVQVQD` are the same 5,198-character joint letter led by Stefanik (level 2). `5WAYSRG2` is Burchett's own 951-character letter, with the same date and addressee (level 5). Robin's rule from that case: **if the bodies differ, the titles must.** |
| 4 | #183, the TitleMax letter, draft and sent | `B3P2UUSH` (the draft: "March XX, 2023", "[ADDRESS BLOCK]") and `C3N75OU4` (the sent letter, 14 March 2023, to Director Chopra). Similarity 0.809, all of it from the unfilled template. **A version**: still open for Robin |
| 4 | #180, unfilled templates | 18 letters were published with placeholders ("XX", "[ADDRESS BLOCK]"). Each is checked for a sent version in the corpus; where one exists, the pair is level 4. |

### From the shared-title audit (#139)

| Level | Example | Digests | Evidence |
|---|---|---|---|
| 1 | Schatz and others to the credit bureaus, v2 | `ELW4RO46` | One file posted on menendez.senate.gov, schatz.senate.gov and tester.senate.gov (twice), so four postings and one letter |
| 2 | Bair Island restoration, to Secretary Norton, 21 Nov 2005 | `JAJZYXCW`, `P5RQOG7V` | Text similarity 1.0. Stark's site moved from `house.gov/stark/` to `stark.house.gov`, and the PDF was re-saved |
| 2 | SFRC Democrats to Chairman Risch, 9 Oct 2019 | `PB4ZPI2V`, `JLCQAKCX` | 1.0. Cardin's `/imo/media/doc/` file, re-uploaded under `/wp-content/uploads/` |
| 2 | Resuming student loan payments, 18 Jul 2023 | `BUIQJ4BV`, `7RKLT4QP` | 1.0. Menendez's and Warren's copies of one joint letter |
| 3 | The 14 pairs on #224 | e.g. `427NWMXS` / `FXGUTS52` | Ratio 0.99 or above, found while reading |
| 4 | Grassley to the American Heart Association, 4 May 2011 | `LPGAN4HK`, `D5AXGHTA` (file name `-2`) | 0.917. Same date and addressee, but the request changed: the first says nothing was posted and asks whether the AHA supports disclosure; the `-2` revision says the AHA has begun listing sponsors and asks about the funding's purpose |
| 4 | Schatz and others to Equifax, Experian and TransUnion, 29 Jan 2019 | `I55JMZ3U`, `ELW4RO46` (`v2`) | 0.953. v2 adds Cortez Masto and Menendez as signers, and two sentences |
| 4 | The TitleMax letter, draft and sent (#183) | | A draft and the sent version |
| 3 | Waxman to the FAA on Santa Monica Airport, 26 May 2000 | `BFKGU4XF`, `WJU74CF2` | 0.569, yet the same letter: one copy also carries the FAA's reply of 19 July 2000. **An enclosure or a reply drags the score down.** Compare the letter portion. The fuller copy is the primary. |
| 3 | Bomb threats against Jewish community centers, 7 Mar 2017 | `TXBNL3SV`, `XYNTT3DA` | 0.802. The same signed letter, but OCR reads the two-column signature pages in a different order and one copy stops early |
| 4 or 3 | Ebola, to President Obama, 8 Oct 2014 | `JIU3SNAV` (unsigned, typed), `VEBRFFDK` (signed, on letterhead) | The same body and the same 26 signers. **A signed copy and an unsigned or typed one**: a version until Robin decides (§6) |
| 5 | Barbara Lee for Democratic Caucus chair, 27 Nov 2018 | `M4VIBMRI`, `Z4XS7BXJ` | 0.182. Two Dear Colleagues on one day: one from three former CBC chairs, one from Adam Smith |
| 5 | Withholding a member's pay in the shutdown, 1 Oct 2025 | `2MOPPHCQ` (Bilirakis), `EVUSVOYY` (Estes) | 0.578, and nearly word for word. **The same wording from different senders makes different letters**: each member's own letter about their own pay |
| 5 | The UN Arms Trade Treaty, 15 Oct 2013 | `2ZUWDJJH` (Senate), `LTMFZ7GE` (House) | 0.743. Companion letters from each chamber: the same date and addressee, different signers and wording |
| — | The mercury rule, to Administrator Leavitt, June 2004 | `5LG7T4HP` (the letter), `QLAN4KHE` (its co-signer list) | 0.029. The second file is the letter's signer list, posted separately. It is not a letter (§5a), so it goes to Robin, not dedup. |

## 3. How to compare two texts

1. **Text:** take each digest's longest text, from the text layer or the
   OCR (`data/letter-text.jsonl`, `data/letter-ocr.jsonl`).
2. **Normalise:** lowercase, and keep only letters and digits. This is the
   hash for level 2 (SHA-1 of the normalised string).
3. **Similarity:** compare word sequences with `difflib.SequenceMatcher`
   (`autojunk=False`) over the first 1,500 words. Characters are not compared,
   because OCR splits words ("Associa tion"). Thresholds:
   - **≥ 0.99:** the same letter (level 2 or 3), unless the signers differ.
   - **0.90–0.99:** read the differences. If they are only OCR noise, a dropped
     line or a missing page, it is level 3. If wording or signers change, it
     is level 4.
   - **< 0.90:** read both. Of the 28 shared titles in this band (#139), 19
     were the same letter, 4 were versions and only 5 were different letters.
     The low scores came from:
     - an enclosure or the agency's reply in one copy;
     - signature pages read in a different column order;
     - a letterhead or footer present in one copy only;
     - a signed copy against a typed one.

     So compare the **letter portion** (from the date through the close),
     not the whole file.
4. **Check the letter's facts, not only its words:** the date (the letter's
   own, §5 of PC-READING), the addressee and the signature block. A different
   date or addressee makes a different letter, whatever the similarity.
   Different signers make a version.
5. **Use the file name as a clue:** `v2`, `-2`, `final`, `revised`, `draft`
   and `.docx.pdf` point to versions, not duplicates. #411 lets the file name
   help decide, but it never decides on its own.

## 4. Choosing the primary copy (levels 2 and 3)

In this order:

1. The **more complete text**: all pages and the signature block present
   (#123), and the most characters of readable text.
2. A **text layer** over OCR, then the higher OCR confidence.
3. The copy posted by the **lead signer** (the first signature, or the member
   whose letterhead it is).
4. The **earliest capture**, which is the most likely to still replay.

The other copies keep their own rows (title, date, recipient, subjects) and
are linked to the primary. Nothing is deleted: each one is still a posting at
its own URL, and a member who posted only a duplicate still posted the letter.

## 5. What is recorded

Proposed: `vocabulary/letter-duplicates.csv`, one row per non-primary digest.

```
digest,same_as,level,similarity,evidence,source
P5RQOG7VL4Q2OKEBM3MGNG6J6YEY45PD,JAJZYXCWLXVQXLS3UISJSCJ2O7MMHVQA,2,1.0,"one letter at Stark's old and new addresses",#139
ELW4RO46NLTGGYZKWY62X3QACR2OD6WH,I55JMZ3ULS5O5RNEZO5T5BTFW4LM73CP,4,0.953,"v2 adds Cortez Masto and Menendez",#139
```

- `level` is 2, 3 or 4. Level 4 rows record a **version**, not a duplicate, so
  they link two letters that both stay.
- Rules for the tests:
  - every `same_as` exists;
  - no chains (the primary is never itself a duplicate);
  - one row per digest;
  - a level 2 or 3 pair has the same date in `letter-dates.csv`, or no hand
    date on either side.
- A level 2 or 3 duplicate shares its primary's title. A level 4 version
  takes a distinguishing title ("… (Version 2, with Senators Cortez Masto and
  Menendez) …").

## 6. In the explorers (Robin's decision; nothing changes until then)

The options:
- **(a)** Show one letter, with "Also posted as" listing the other files and
  postings.
- **(b)** Keep every file as a letter, with a "Duplicate of" note.
- **(c)** Show one letter in counts and search, and every copy on its
  members' pages.

The counts already show the stakes. 9,222 digests in text-identical groups
means the explorers count about 5,100 letters twice.

## 7. In the monthly harvest (#542)

For each new digest:
1. Is it already in the corpus? (level 1)
2. Normalised-text hash against the corpus. (level 2)
3. Its opening 300 normalised characters against the corpus, then
   similarity on those candidates. (levels 3–4)

A level 2 or 3 match gets a row in `letter-duplicates.csv` and is not read
again. A level 4 match, or anything between 0.90 and 0.99 that a reader has
not settled, goes on a **"Duplicate letter"** issue, as #542 asks.

## Related

#98 (download wrappers), #126 and #170 (dates through level 1), #138 (Visa), #139 (the shared titles these examples came from), #224 (14 near-identical
pairs), #183 (draft and sent), #180 (unfilled templates, a kind of version),
#41 (a cosigned letter credited to each signer), #411 (the file name as
evidence), #542 (the monthly harvest).
