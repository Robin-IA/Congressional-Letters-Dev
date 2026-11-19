# Letters from Congress: history and plan

Written 19 November 2026, after the work had been running for seven weeks. It
builds the project plan backwards: what was built, when, and why; where the
work stands; and what is left to finish it and to keep it going into the
120th Congress. Dates and counts come from the repository's commits, its pull
requests and issues, and the measurements named beside each figure.

## In one paragraph

Letters from Congress collects the letters that members of Congress publish
on their own websites, as the Wayback Machine archived them, and makes them
searchable by member, recipient, topic and Congress. It began on
30 September 2026 as one explorer of the current (119th) Congress. It is now
fifteen explorers, one for each Congress from the 105th (1997–98) to the 119th,
plus a home page that searches across them. The fifteen explorers publish
114,891 letters. 99.6% have readable text, and 21,314 (18.6%) are fully
reviewed and filed. One Mac and one Windows PC, working mostly unattended,
did the work through 597 pull requests and 782 issues.

## Timeline

### Phase 1: one explorer of the current Congress (30 September – 22 October)

| Date | What happened |
| --- | --- |
| 30 Sep | Repository started ("Initial scaffold"). |
| 1 Oct | First harvest of member-site letters from the Wayback Machine's CDX index, the URL parser and the first explorer. It is named **Letters from Congress**. |
| 2 Oct | Deployment directory for Wayback Labs (the Mac Studio). The private `internetarchivecanada/letters-from-congress` repository is created. |
| 5–6 Oct | The page reads its data from an archive.org item. Search works, dates come from the letters themselves, and a host is not counted as harvested until every CDX page comes back. The public `congressional-letters` repository is created on 6 Oct. |
| 7 Oct | First controlled vocabulary of subjects and agencies. Rebuilt from a harvest that could be trusted. |
| 13 Oct | Only files that open as letters are kept: **89,891 → 69,650**. Text is captured while the PDF bytes are in hand. Thumbnails are served from the repository. |
| 13–22 Oct | The first unattended loop renders previews and publishes them as it goes, from 7,996 to 47,688. |

### Phase 2: back in time, one Congress at a time (4–11 November)

| Date | What happened |
| --- | --- |
| 4 Nov | A historical member roster, built from the House and Senate's own directories. |
| 5 Nov | **`Robin-IA/Congressional-Letters-Dev` becomes the working repository.** Its numbering starts at #1, so every PR and issue cited here is from 5 November on. The GitHub Pages size budget is measured. |
| 6 Nov | Each Congress gets its own folder, and the 119th moves into `119th/`. Members who left during the 119th are added. Rosters with websites for the 113th–118th. |
| 7 Nov | `METHODOLOGY.md` starts. Step 1 is the per-Congress roster (built once, then added to). Step 2 is a lookup of each member's site in Wayback, bounded by their service (#9, #11). |
| 8 Nov | Rosters for the 106th–109th, back to 1999 (#17). |
| 8–9 Nov | Step 3: **who held each web address, and when.** A letter is credited to the member who held the address on its date. The same address passes between members, and a gap between holders goes to the earlier one, flagged. |
| 9 Nov | **Decision: one explorer per Congress, with a home page across them** (#20, #22, #25), each letter in the explorer of its date. Thumbnails shrink to 200 px, from 925 MB to 294 MB (#21). Committee letters (#23) and caucus letters (#24) are opened as questions. |
| 11 Nov | **The PC joins** (#29, PC-HANDOFF.md). It renders thumbnails and runs OCR on its own ranges, and returns its work as branches the Mac merges. |

### Phase 3: fourteen explorers and a home page (12–14 November)

| Date | What happened |
| --- | --- |
| 12 Nov | **The explorers for the 106th–119th Congresses are published**, one GitHub repository each, with the home page `Explorer-Letters` (#39). Pages builds hold up because each repository is small. OCR starts: Apple Vision on the Mac (#37) and Tesseract on the PC (#38). The controlled vocabulary for subjects is opened (#40). The accessibility check (WCAG 2.2 AA) passes and is noted on the pages. |
| 13 Nov | Full-text search with Pagefind, in each explorer and across all of them (#65). **`auto_publish.sh`** merges the PC's returns and republishes on its own (#66). Caucus letters are published under the chair (#77). |
| 14 Nov | `letters-from-congress-OCR`: one store for every letter's text (#119). Publishing rebuilds the vocabulary too (#100). Every member site the rosters name is searched (#110). |

### Phase 4: reading every letter (15–19 November)

The busiest stretch: 208 PRs and issues on the 15th, 485 on the 16th and 460 on the 17th.

| Date | What happened |
| --- | --- |
| 15 Nov | Subjects read from the letters' text (#165, #188). **Dating rule:** the letter's own date, then the file name, then the PDF metadata, then review (#172). A progress report runs in every publish (#178). 40% of postings were found to have no date better than a scan or harvest timestamp (#191). The format survey for non-PDF letters opens (#242). |
| 16 Nov | The OCR gap: the letters the PC's Tesseract could not read are read by the Mac (#383–#386). The maintainer harvest for new letters is planned (#542). The **2025 catch-up harvest** of every current member's site starts. |
| 17 Nov | **The QA analysis: what "done" means** (#1308). Every member in a letter is represented, officials are filed under their office, and companies are names. **Robin's subject rule:** every filed letter has at least 4 subjects, at least 2 of them topics (#1266; 17,990 letters were short). The reading surfaced so many missing names that 519 "new vocabulary term needed" issues were filed on the 16th and 17th. The harvest before 2025 is to be re-checked one year at a time (#1054). |
| 18 Nov | Campaign letters are kept only while the member is in office (#1317). The first subject re-check batches run (#1319–#1325). 181 named laws become subjects (#1326). **The 105th Congress (1997–98)**: a roster, 34 hand-read HTML letters, and an explorer (#1330, #1334). |
| 19 Nov | **The 105th takes every letter of 1997–98** (option A, #1364), and goes from 34 letters to 137. The "Not yet reviewed" names are filed letter by letter (#1365). The OCR phase closes with the PC's batch 65 (#1360). Batch 66, the first 600 text-layer letters of the 119th, is read (#1366). "Unfiled letters" headings (#1367), footer disclaimers (#1339), and About-page notes on letters *to* members and on co-signed letters (#1372). |

## Decisions that shaped it

- **Credit by address holder, not by name** (Step 3, 8–9 Nov). The same web
  address passes from one member to the next, so a letter goes to whoever held
  its address on its date.
- **One explorer per Congress, with a home page across them** (9 Nov, #22).
  Each letter appears in one explorer only, the one for its date. This keeps
  each repository within GitHub Pages' limits and each page fast.
- **The letter decides.** Its date, recipient and subjects are read from its
  text, not from its file name or capture date (#172, #191). Where it cannot
  be read, the page says so.
- **What "done" means** (#1308, 17 Nov). A letter is done when it has text,
  has been reviewed against that text, has a title in the house form, has a
  settled date, carries subjects, and is filed under a reviewed recipient.
  Officials are filed under the office, and companies and organizations are
  names. Every member in a letter is represented.
- **The subject rule** (#1266, 17 Nov): at least 4 subjects, at least 2 of
  them topics. Named laws count as topics (#1324).
- **The PC proposes, the Mac decides.** The PC reads letters and proposes
  new terms and discards. The Mac adds terms, decides discards and merges.
- **Discards are decided, never assumed.** A form, a press release, or a
  letter with no member at either end is discarded only after a search for the
  member letter it supports; when found, it is kept as a supplement.
- **The 105th takes all of 1997–98** (option A, 19 Nov). Before, those letters
  sat in later explorers only because the 105th had none.
- **Wayback is shared and treated gently.** At most two workers at a time in
  all, a 4–5 second pause, one worker after any 429 or 503, and a file is kept
  only when its bytes match the CDX digest.

## Automation and unattended work

- **Rendering loop** (13–22 Oct). Previews were rendered and published
  continuously, with no one watching. 47,688 previews were made.
- **The PC** (from 11 Nov). It renders and runs OCR on its own Congress ranges.
  It reads batches of letters under `PC-READING.md` and returns each as a PR
  with an issue for the terms it needs and one for proposed discards.
- **`auto_publish.sh`** (from 13 Nov). Every 15 minutes it merges the PC's
  returns. When something changed, it rebuilds every explorer, the CSV
  downloads, the vocabulary and the home page, writes the progress report,
  and publishes to both GitHub organizations.
- **`fold.sh`** merges a reading PR only after the tests pass and every
  dated letter still has an address holder.
- **The OCR watcher** (`ocr_letters.py --watch`). Apple Vision OCRs each
  scan as its PDF arrives.
- **Scheduled overnight runs and parallel sessions.** Reading batches,
  subject re-checks, harvests and the 105th each ran in their own session,
  reporting by PR and issue comment. The rules in each run's instructions held
  them to the same standard as the day's work.

## From one repository to many

| | Robin-IA | internetarchivecanada |
| --- | --- | --- |
| Original explorer | `congressional-letters` (6 Oct) | `letters-from-congress` (2 Oct, private), `congressional-letters` (13 Oct, now the home page) |
| Working repository | `Congressional-Letters-Dev` (5 Nov) | — |
| Per-Congress explorers | `Explorer-Congressional-Letters-106` … `-119` (12 Nov), `-105` (18 Nov) | the same fifteen (12 Nov; the 105th on 19 Nov) |
| Home page | `Explorer-Letters` (12 Nov) | `congressional-letters` |
| Text store | `letters-from-congress-OCR` (14 Nov, private) | — |

In all: one working repository, fifteen explorers and a home page, published
twice (Robin-IA and internetarchivecanada), plus a text store. One publish
script pushes all of them.

## Where it stands (19 November 2026)

From `PROGRESS.md` (19 Nov, 2:55 PM) and `COVERAGE.md` (17 Nov), in
letters-from-congress-OCR:

| Measure | Count |
| --- | ---: |
| Letters published, 105th–119th | 114,891 |
| With readable text (text layer or OCR, at least 100 characters) | 114,388 (99.6%) |
| Of those, text from OCR | 56,427 |
| Reviewed against the text | 38,368 |
| Filed under a reviewed recipient | 98,685 |
| Carrying subjects | 21,518 |
| **Done** | **21,314 (18.6%)** |
| Recipient has no vocabulary term | 10,699 |
| No recipient read yet | 5,474 |
| Still short of the subject rule (at the 19 Nov pick) | 10,476 |

The 2025 catch-up harvest has staged 1,379 letters new to the corpus, not
yet published. The 106 largest current member sites time out at the CDX
index. A page-by-page retry is running on one worker.

## The plan to finish

### 1. Text (nearly done)

- **503 published letters lack readable text** (19 Nov). On 17 Nov most
  were scans not fetched yet (376 scans), with a few awaiting OCR, failed
  fetches, and OCR that read under 100 characters. Fetch, OCR, read.
- **Partial text** (#252): PDFs whose text layer covers only part of the
  letter, such as the signature page. Six held letters are waiting on this.
  OCR the whole document.
- **The 2025 catch-up**: 1,350 staged letters, 1,329 with readable text, 15
  scans queued for OCR. Publish them once read.
- **The 105th's welcome-page letters** (#1332): OCR and review before they
  stay discarded.

### 2. Reading and filing (most of the remaining work)

- **Review the ~76,500 letters not yet read against their text.** The 109th–114th
  are the furthest behind: under 15% reviewed. The 115th and 116th are past
  half.
- **Subjects**: about 10,500 letters short of the 4-subject rule, in
  300-letter batches (#1266). The 15 that cannot honestly reach it say why.
- **Recipients**: 10,699 with no term and 5,474 with none read. These are
  filed by reading the address block (#97).
- **Titles** in the house form for every letter (#1337), links between
  related letters (#1289), and duplicates (#1309).

### 3. Finding what the harvest missed

- **Non-PDF letters** (#242): 190 Word and 6 text files are listed. 25,124
  HTML pages are named "letter", and a sample of about 100 is planned. Letters
  that exist only as web pages are to be saved as PDFs, so they read and
  display like the rest.
- **Letters whose address doesn't say "letter"** (#546): GUID-named PDFs
  and the like. The plan is a CDX pass by file type: first "letter" and
  "letters", then "ltr" or "let" as a word, then everything else by format.
- **Completeness before the 110th** (#1295) and **the 105th's floor**
  (#1331): `<name>.house.gov` sites that time out, and files not named
  "letter".
- **The harvest before 2025, one year at a time** (#1054). 2024 is next, after
  the large-site retry.
- **Committee sites** (#23), credited to the chair. The roster work is in
  #1313.

### 4. The 120th Congress and after

The 120th convenes on 3 January 2027. To carry the project past it without a
rebuild:

- **The monthly maintainer harvest** (#542). Each current member's site is
  queried for new captures, which are fetched, rendered, OCR'd and staged
  for reading. It needs an S3 key for Save Page Now (#545), to capture pages
  the Wayback Machine has not.
- **A 120th roster and explorer.** Members, websites, and the address
  holders updated as seats change hands. The 119th closes, and its departed
  members' last captures are kept.
- **One repository per Congress continues.** `publish_explorers.sh` creates
  the next repository and its Pages link, and `auto_publish.sh` takes the new
  range.
- **The vocabulary keeps growing by decision, not automatically.** Readers
  propose terms, and a reviewed decision adds each one.
- **Documentation for whoever runs it next** (#1347, #1348): how to
  contribute, the infrastructure, and the process end to end.

### Open decisions for Robin

- Does the committee a letter is addressed to count toward its 4 subjects?
  Readers have split on it.
- In what order: finish reading the published letters, or widen the harvest
  (non-PDF, GUID-named, committee sites) first?
- When to publish the 1,379 letters from the 2025 catch-up: as they're read,
  or as one batch?
