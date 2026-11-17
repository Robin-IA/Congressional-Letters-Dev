# For Claude on the PC: where the reading work lives

**Updated 15 November 2026** (reading is one pass per letter, section 5). Read this first in any new session on the PC,
whatever model it runs. A session that starts fresh does not remember this
setup. That includes switching models, for example to Sonnet.

The older [`PC-HANDOFF.md`](PC-HANDOFF.md) covers the November harvest bundle.
This file covers the work the PC does now: reading letters from their text and
recording titles, dates and topics.

## 1. Accounts and access

- `gh` and `git` must be signed in as **Robin-IA**. Check with
  `gh auth status`. The text repository is private and has no other
  collaborator, so any other account gets "not found".
- Robin's email address is private. Never put it in a commit, a PR or an issue.

## 2. The repositories

| Repository | Visibility | What it holds | The PC's use |
| --- | --- | --- | --- |
| [`Robin-IA/Congressional-Letters-Dev`](https://github.com/Robin-IA/Congressional-Letters-Dev) | public | Code, tests, and the hand-made vocabulary files the explorers are built from | Branch and open PRs; never merge |
| [`Robin-IA/letters-from-congress-OCR`](https://github.com/Robin-IA/letters-from-congress-OCR) | **private** | The text of every letter: PDF text layer, or OCR | Read only |
| `Robin-IA/Explorer-*` and `internetarchivecanada/Explorer-*` | public | The built explorers | Never touch. The Mac builds and publishes them with its scripts |

The working branch of the dev repository is **`harvest-member-letters`**.
Branch from its latest commit, and open every PR against it:

```bash
git fetch origin && git checkout -b <topic-branch> origin/harvest-member-letters
gh pr create --base harvest-member-letters
```

Never push to `main` or to `harvest-member-letters`. The Mac merges PC PRs
once the tests pass and every hand date still has a holder; Robin has
authorized that. The PC never merges.

## 3. Where the text is

```bash
gh repo clone Robin-IA/letters-from-congress-OCR
gzip -dc letters-from-congress-OCR/text/116th.jsonl.gz | head -1
```

- `text/<N>th.jsonl.gz` holds one record per scan, filed under the first
  Congress whose explorer publishes it. A record has `digest`, `congresses`,
  `source` (`text-layer` or `ocr`), `engine`, `chars` and `text`.
- `progress.csv` and `PROGRESS.md` say what is done. The Mac rewrites them at
  every publish, so `git pull` before choosing letters.
- `COVERAGE.md` shows which letters have no text and why.

The `digest` is the Wayback Machine's base-32 SHA-1 of the PDF. It is the key
everywhere: the vocabulary files, the explorers and this repository.

## 4. Who reads what

| Machine | Reads |
| --- | --- |
| PC | 116th–119th, plus the agency letters of #204 |
| Mac | 106th–115th, most-posted first, 25 letters a batch |

Stay in your own range, so the two machines never write rows for the same
letter.

## 4a. The PC's work order (Robin, 17 November 2026)

Pull `letters-from-congress-OCR` before building a pick list: the Mac
pushes a fresh `progress.csv` after each publish. One row per scan
(distinct file); the first Congress is the lowest in `congresses`.

1. **Now: finish the OCR scans of the 116th–119th.** Pick list: `text=True`,
   `reviewed=False`, `ocr=True`, first Congress 116 or later. About 1,800 are
   left after batch 59 (2,305 before it). Keep the 500-letter batches.
2. **Next: the text-layer letters of the 116th–119th**, newest Congress
   first (119th, then 118th, 117th, 116th). Pick list: `text=True`,
   `reviewed=False`, `ocr=False`. About 30,800 letters. Their text is
   clean, so batches go faster.
3. **Then:** whatever Robin assigns. The other large pile is the
   106th–115th OCR scans (about 23,000), which are in the Mac's range
   (section 4).

**Do not hold letters for a date or a missing addressee any more.**
- Undated letters follow step 5: OCR first, then the content, then the
  file name, then file the letter anyway.
- A member's letter with no addressee gets `(no recipient)`, and a Dear
  Colleague letter goes to its chamber (section 6, #502).
- Hold a letter only for a missing vocabulary term or subject, as before,
  with its issue.

**Harvesting is the Mac's.**
- The PC does not query Wayback for new letters.
- The Mac is running the 2025–2026 catch-up and will run the monthly
  harvest (#542) and the year-by-year re-check (#1054).
- New letters reach the PC through `progress.csv` after the Mac publishes.
  They are new rows with `reviewed=False`, picked up by the lists above.

## 5. What "done" means, and the files a PR touches

### One pass per letter (Robin, 15 November 2026)

Reading is **one process**. Each letter is taken all the way through, in this
order, in the same batch and the same PR. The recipient is **not** a separate
pass or a separate PR (the earlier recipient-only PRs, #405 and #408, are the
last of that kind).

1. **Read the text** (OCR or text layer) against the letter, not the file name.
2. **Find the recipient** in the address block, then the salutation, then the
   body. File it by the three kinds in section 6: Congress "As recipient",
   an official under the office (with the official's name kept searchable:
   in the title, and as an `officeholder` name on the office term; no person
   term, Robin, 16 November 2026), a company or organization as a topic, and a
   private citizen under no name. One row in `letter-recipients.csv`;
   several offices at once is a `joint` row in `reviews.csv`; several
   companies go in `letter-topics.csv`.
   - **A member of Congress as recipient:** marked "As recipient", and filed
     under the recipient's name **in addition to** the authors (#352).
   - **Any other personal name** (a CEO, a staff member, a private citizen):
     never the person; file under the company or organization.
   - **Many companies or organizations named** (a letter to ten insurers):
     each one is filed, and the 8-subject limit does not apply.
   - **No addressee** (no address block or salutation, or only "To Whom It
     May Concern"; Robin, 16 November 2026, #498). Do not guess and do not
     hold it. In order:
     1. The **author** is the letterhead, or the signer when they differ
        (then the letterhead is the organization).
     2. Read the recipient from the address block, the salutation, then the
        body, as above.
     3. If none can be read and the letter sits on a **member's website**
        whose member is **not the author**, that member is the recipient:
        "As recipient, from Rep./Sen. X's website" (#352). The `source` in
        `letter-recipients.csv` says "from Rep. X's website (the posting
        member); the author is Y", and the title names the sender ("… —
        Mayor of Gilman to Representative Emmer, 10 March 2025").
     4. If the **member is the author** (an open letter, a notice to
        constituents, students or "stakeholders"), write the recipient as
        **`(no recipient)`** in `letter-recipients.csv`: the letter files
        under its author, shows no recipient, and counts as filed. The title
        still says whom it addresses ("— to high school students").
        Confirmed by Robin, 17 November 2026 (#502). A letter to a
        **private person** is written the same way.
     4a. A **Dear Colleague** letter to the members of one chamber files under
        the chamber: **United States Senate** or **United States House of
        Representatives** (Robin, 17 November 2026, #502). A letter to
        "the conferees" or to named chairs and ranking members files under
        their committees (a joint row when there are several).
     5. **Omit** letters to unnamed employers ("Dear Employer"), which are
        references or personnel letters, not correspondence to file.
     6. A **named** addressee whose office cannot be established ("Dear Mr.
        Hall") is not this case: hold it with an issue.
3. **Find who wrote it, and where it files.** Check that the posting member
   signed it or is among its signers. A letter written *to* the member is
   titled with its sender (#175). The Congress follows from the letter's date
   and who held the posting address then (the holder check). Say in the note
   when the signers and the posting member differ.
4. **Write the title as a title** (Robin, 16 November 2026): **"On Subject —
   to whom, D Month YYYY"**, the subject in title case, for example "On
   Additional Nashville Flights for the NCAA Division I Football Championship —
   to airline CEOs, 18 December 2025". The recipient comes from step 2 (an
   office or company, never a CEO's name). Titles written in the older form
   ("Subject — …") are converted when the site is built
   (`letter_text.title_form`), so either is accepted, but write new ones this way.
5. **Settle the date** by the dating order (#172). **Always take the date
   from the letter's own text (the OCR)**: the letterhead or dateline first.
   Refuse a date that leaves the posting with no holder (#239).
   **If the text gives no date** (Robin, 17 November 2026), in this order:
   1. **OCR first.** A garbled or missing dateline is often the OCR's fault:
      read the scan's Apple Vision text (or re-OCR it) before giving up.
      Read a dateline whose remaining digits are clear ("March 3I, 2023").
   2. **The content**, when it pins the year: a dated event, an official in
      office, a fiscal year, "the 116th Congress". Name the evidence.
   3. **The file name**, when it carries a date ("2019-03-12", "03.12.19",
      "March 12 2019"), at the precision it gives, and never later than the
      posting's first capture. Write `source` as "file name: <name>".
   4. The funding-request rule (a fiscal year N gives year N−1, below).
   5. Otherwise **file the letter anyway**: no `letter-dates.csv` row, so
      the weak published date stands, and the `letters-reviewed.csv` note
      says it is approximate (#488). Do not hold it.
6. **Choose the subjects** from the recipient where it implies them (a letter
   to an airline is about Airlines; `recipient-topics.csv`) and from what the
   letter discusses. Only labels in `SUBJECTS`, plus reviewed organizations.

A letter is done when all of these hold:

- it has text;
- it has been read against that text;
- its title is confirmed and written in our form;
- its date is settled;
- it has subjects;
- it is **filed**, meaning its recipient is a reviewed term. A letter still in
  "Not yet reviewed" is not done.

Each batch is one PR, which appends rows to these files in the dev repository:

| File | Row | Rules |
| --- | --- | --- |
| `vocabulary/letter-titles.csv` | `digest,title,source` | Form: **"On Subject — to whom, D Month YYYY"**, e.g. "On Funding the Sea Grant Program in 2019 — to Chairman Moran and Ranking Member Shaheen, 11 April 2018". A letter to a company is filed under the company, with no CEO's name in the "to" part. |
| `vocabulary/letter-topics.csv` | `digest,topics,source` | `;`-separated, **only labels already in `SUBJECTS`** in `build/topics.py`. Check every label before writing it. |
| `vocabulary/letter-dates.csv` | `digest,date,precision,source` | Only when the letter's own date differs from the published date. The source says why, e.g. "the letterhead; was 2018-09-19 (captured-by)". |
| `vocabulary/letter-recipients.csv` | `digest,recipient,source` | One row per letter: the reviewed term from step 2 (an office, a committee, a member's name, or a company's label). Not for a private citizen. |
| `vocabulary/reviews.csv` | `candidate,letters,decision,…` | Only when step 2 needs a decision the vocabulary lacks: a `joint` row for several offices at once, or a `merge` row for a company not yet reviewed. |
| `vocabulary/letters-reviewed.csv` | `digest,reviewed,title,date,topics,filing,note,date_audited` | One row per letter read. `date` is `yes` if you added a date row, otherwise `unchanged`; `filing` is `yes` if you added a recipient row. |
| `letters-vocabulary-needs/letters.csv` | `digest,title,date,topics,proposed_subjects,issue,note` | For a letter that needs a subject the vocabulary lacks. It stays here and goes in none of the files above. Also comment on #221. |
| `letters-discarded/letters.csv` | `digest,title,reason,issue,decided` | A posting that is **not a letter** (resolution, newsletter, exhibit, "Dear Employer" reference), once Robin has decided it. It goes in none of the other files and is not read again. |

Write CSV rows with `\n` line endings and append only, never reorder.
`source` is "read from the text of the letter (the PC)".

## 5a. What is a letter (Robin, 16 November 2026; #411)

Decide this **before** titling, dating or filing. It applies to every format.

**A letter must have:**

1. **An addressee**: a person, a company or an organization. A salutation, an
   inside address or "Dear Colleague" shows it.
2. **A member of Congress as signer.** A **printed name is enough**. If there
   is **no printed name, there must be a signature**, which stands in for the
   name. If the signer is not a member, is it signed **on behalf of a
   committee or caucus**? If so, **are the members listed?**

**Preferred, not required:** a date in the letter (undated: #506, never from
metadata, harvest or file name alone) and a named recipient (a letter plainly
directed at someone but naming no one follows #498).

**The file name is evidence**, a hint about letter, date, author and subject to
check against the text, never the whole test.

| # | Question | Yes | No |
|---|---|---|---|
| 1 | Is it a PDF? | Go to 2 | Open an issue (#242, #243) |
| 2 | Addressed to a person, company or organization? | Go to 3 | Open an issue, or #498 for a member's letter with no addressee |
| 3 | Signed, by printed name or by signature, by a member? | A letter. Go to 6 | Go to 4 |
| 4 | Signed on behalf of a committee or caucus? | Go to 5 | Written to Congress (#175), or not a letter (`letters-discarded/`) |
| 5 | Are the members listed? | A letter, filed with the members listed | Open an issue |
| 6 | Does the text give a date and a named recipient? | Fill both in | Still a letter: #506 or #498 |

- **OCR text shows a printed name, a signer title and a close. It never shows
  a signature.** Where the text has none of these, the signature question
  needs the rendered page: render it and read it.
- **Non-PDF items and any that fail or half meet a criterion get an issue**
  (label `quality control`) listing the digest or URL, the format, the
  criterion and what was read. Nothing is filed until it is resolved, and
  nothing is silently dropped.
- **Screening.** The signals (salutation, date, signer title, inside address,
  close, letterhead, committee or caucus named) are measured on #411. A
  salutation plus a close or signer title passes (91.4% of held scans). A scan
  that fails is **read or rendered by a person**, never discarded by the
  pattern, because most sampled failures were real letters.
- **File-name check.** Compare what a file name suggests with what the text
  says. The text stays the rule for date and author.

## 6. The rules that matter most

- **Date order** (#172): the letterhead first, then the file name, then the PDF
  metadata, then review.
- **A date can be refused.** A hand date also moves the letter to the right
  Congress and holder. If a member re-posted an older letter (a caucus site, a
  successor's site), a posting can have no holder on the letter's date. When
  the holder check fails, drop the date row, keep the date in the
  `letters-reviewed.csv` note, and cite #239. Never force a date.
- **The letterhead year can be a typo.** If the letter cites later events (a
  hearing, a bill, a fiscal year), date it from the content and say so in the
  source.
- **An undated funding request is dated to a year** (Robin, 16 November
  2026). A community project funding (earmark) request that prints no date but
  names fiscal year N was written in the spring of year N−1: of 57 dated
  requests naming their year, every fiscal year from FY2023 to FY2027 fell in
  March–May of the year before. Record precision `year`, marked approximate:
  the date column holds the letter's first capture in year N−1 (or 30 June),
  so it sorts and places correctly; the explorers show only "about N−1".
  Check the text first: many "undated" requests have a dateline the OCR
  garbled ("March 3I, 2023"), and those take the day.
- **Not every PDF is a member's letter.** An agency reply, an association's
  letter to a member, a CBO letter or a newspaper page is titled with its
  sender ("— CBO Director Elmendorf to Chairman Baucus …") and noted (#175).
  A page that is not a letter at all (a draft resolution, a newsletter, a
  "Dear Employer" reference) goes in **`letters-discarded/letters.csv`**
  (digest, title, reason, issue, decided; Robin, 16 November 2026) once
  Robin has decided it, and is listed in the PR. It is not read again.
- **Copies** (#224): note "another scan of <digest>". Same title, same topics.
- **Text that is only part of the letter** (#252), such as a signature page,
  footers or a middle page: skip the letter and add it to #252.
- **Recipients: three kinds, three ways to file** (Robin, 15 November 2026;
  #352, #357, #391). Read the address block, never guess, and sort the
  recipient into one of these. A letter is filed only when its recipient is a
  reviewed term, so this decides what goes in `vocabulary/letter-recipients.csv`
  (`digest,recipient,source`) and `vocabulary/reviews.csv`.
  1. **A member or committee of Congress** (a chair and ranking member, the
     Speaker, a leader, a senator). File the letter **"As recipient"** (#352):
     in that Congress's session **under the author** (the member who wrote or
     posted it), **under the recipient** member, marked "As recipient", and
     under that Congress on the **topics page**. A letter to several members is
     a `joint` decision in `reviews.csv` (target = Bioguide IDs separated by
     `;`). The two groups, wrote and received, are kept apart.
  2. **A government official** (a Secretary, an Administrator, the President,
     a governor, a judge). File it **under the member or members who wrote it**,
     **under the official's office** in the matching area of the browse
     (Executive branch: the Executive Office of the President or a federal
     agency; Legislative branch; Judicial branch; or, for a governor or a state
     or local office, Topics › State and local government › the state), and **under its
     subjects**. The official gets **no person term of their own** (Robin,
     15 November 2026): the name is recorded on the office as an
     `officeholder` decision in `reviews.csv` ("Hagel" → Department of
     Defense), or as a `split` by year where one name held several offices.
     The title still names the official: "to Secretary Hagel".
  3. **A CEO, or anyone writing for a company or organization.** Never file a
     personal name. File under the **member or members who wrote it**, then the
     **company or organization**, then the **topics**. A private citizen gets
     no person term either; the name stays searchable in the text (#357).

  The title follows: "to Secretary Austin" for an official, "to the chief
  executive of United Airlines" or the company's name for a CEO, never the
  CEO's name. Where the address block does not say who the recipient is, list
  the letter in the PR and leave it.

  **How kind 3 is recorded** (`build/filed_orgs.py`, from the Mac):
  - **One company:** put the company's reviewed label in
    `letter-recipients.csv`, for example `<digest>,Equifax,<source>`. The
    build then files the letter under the company **as a topic** and
    publishes it with **no recipient**, because only government officials
    are shown as recipients. A name in `reviews.csv` that resolves only to
    companies ("Mr. Bastian" → Delta Air Lines) is handled the same way.
  - **Several companies** (one letter to four airline CEOs): `letter-recipients.csv`
    takes one row per letter, so add **each company's label to the letter's
    row in `letter-topics.csv`**, after its subjects. The 8-subject cap does
    not apply to these: four or more companies are all kept.
  - **A company the vocabulary lacks:** add a `reviews.csv` row first:
    `merge`, kind `organization`, broader `Companies`, `Nonprofits` or
    `Associations and other organizations`. Without one, the build stops on
    the unknown label in `letter-topics.csv`, and a `letter-recipients.csv`
    row is shown as a recipient and not filed under the company. This is a
    vocabulary change, so it goes in its own PR, as with subjects.
  - **A member and a company together** ("Chairman Wicker and Mr.
    Zuckerberg"): the member stays the recipient (kind 1), and the company
    is added as a topic.
- **New subjects** are never added during reading, and a letter is **never
  bent onto a subject that does not fit** to avoid a hold. When the letter's
  subject is not in `SUBJECTS`:
  1. **Move the letter to the holds folder:** a row in
     `letters-vocabulary-needs/letters.csv`, with the proposed subject. A held
     letter goes in none of the other files until the subject exists.
  2. **File the request** as a comment on #221 (the vocabulary-request
     issue): the proposed subject, the held letters' digests and titles, and
     one line from the text showing why.

  **The PC recommends a term; the Mac adds it.** A term request says the
  term, the held letters, and *where it would file* (for example "State of
  Ohio › local government"). The Mac writes the term, places it in the
  hierarchy (`hierarchy.csv`, creating the state or group entries it needs),
  files the held letters and closes the request.

  Vocabulary changes go in their own PR to `build/topics.py`. Match words are
  plain lowercase words, never regex. The same goes for a **recipient with no
  term** (a company, a state office, a foreign official): list it in the PR
  and on #357, and leave the letter unfiled rather than filing it somewhere
  else. Between 15 and 16 November, ten PC batches (#369 to #415) filed no
  holds at all, and their letters had to be read again for subjects and
  recipients.

## 7. Before opening a PR

```bash
python3 -m unittest discover -s tests
python3 build/audit_dates.py --ocr-repo ../letters-from-congress-OCR
```

On the PC, `audit_dates.py` cannot run the **holder check** for letters whose
postings are not in the PC's checkout (the 119th, for example). That is
expected: **the Mac runs the holder check on every PC PR as it merges it**
(`fold.sh`), and refuses the merge if a date leaves a posting with no holder.
Say "holder check not run on the PC" in the PR and go on; nothing else is
needed.

**The PC never rebuilds the vocabulary** (`build_vocabulary.py`). It writes
the hand files (`letter-*.csv`, `reviews.csv`, the holds file), and the Mac
rebuilds the vocabulary and explorers when it publishes. A new term exists
once its `reviews.csv` row is merged, whether or not the vocabulary has been
rebuilt; check `reviews.csv` and `vocabulary/terms.csv` before asking for one.

Both must pass, and the PR body must say **how many letters were held for
vocabulary** and how many recipients have no term, with the #221 and #357
comments linked. "0 held" is written out, not left blank. On the PC, `--ocr-repo` (or `LETTERS_OCR_REPO`) points the audit at the text repository; without it the audit sees only the PC's local text and reports most letters as unreadable (#332). The PR title follows the existing pattern ("Letters review:
agency letters, round N (25 read from full text)"). The body lists copies,
holds and gaps. If rows from a Mac batch land at the same time, the conflict
is only appended rows, and the Mac resolves it by keeping both sets.

## 7a. Label every issue and PR (Robin, 16 November 2026)

Every issue and every PR the PC opens gets **at least one topic label**, set
when it is created: `gh issue create … --label "reading,vocabulary"` or
`gh pr create … --label reading`. Use as many as fit. Labels are only added,
never removed. Use only these (`gh label list` shows them):

| Label | Use it for |
| --- | --- |
| `reading` | A reading batch PR; a letter that needs to be read again |
| `vocabulary` | A term request ("New vocabulary term needed"), holds, recipients, subjects, `reviews.csv` |
| `dates` | Letters with no date in their text (the #191 issues), refused dates, holder-check problems |
| `OCR` | Text missing, cut off or unreadable; OCR batches and returns |
| `harvest` | Member sites, URLs, captures, letters not found or not in PDF |
| `quality control` | Checking, reconciling, duplicates, letters that are not letters |
| `methodologies` | A rule or criterion that needs deciding |
| `process documentation` | Changes to this file or to how the work is handed over |
| `search` / `explorer` | How letters are found; the published pages |
| `bug` / `enhancement` | Code that is wrong / a new feature |

Typical sets: a reading batch PR is `reading` (plus `vocabulary` if it adds
`reviews.csv` rows); a term request is `vocabulary`; an index of term
requests is `vocabulary`; an undated-letters issue is `dates` and `reading`;
an OCR-gap issue is `OCR`. Do not use `important`; that is Robin's.

## 8. What the PC does not do

- It does not publish or build explorers. The Mac's publish loop does that
  every 2 hours if the data changed, on a PC merge, or after 300 new
  thumbnails.
- It does not edit code (`build/`, `app.js`, `tests/`) in a reading PR. Code
  changes are separate PRs, and Robin reads them.
- It does not push the text repository, which the Mac rewrites at each
  publish.

## 9. Open issues to know

| Issue | About |
| --- | --- |
| #172 | The dating order |
| #175 | Letters written to Congress, not from it |
| #204 | The PC's agency letters |
| #221 | Proposed new subjects, with their held letters |
| #224 | Duplicate letters |
| #239 | Older letters re-posted later, and refused dates |
| #242 / #243 | Letters in Word or HTML, not PDF (survey, then conversion) |
| #252 | Text layers that cover only part of a letter |
| #411 | What is a letter: the criteria in section 5a, in any format |
