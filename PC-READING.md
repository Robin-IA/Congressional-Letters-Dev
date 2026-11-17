# For Claude on the PC: where the reading work lives

**Updated 17 November 2026.** Read this first in any new session on the PC,
whatever model it runs. A session that starts fresh does not remember this
setup. That includes switching models, for example to Sonnet.

**This is the contributor's guide** (QA-Analysis-methodology, "Roles"):
written for the PC, and meant to serve Internet Archive staff or public
contributors later.

**The rules for every step are the QA-Analysis-methodology** (`qa/`, Robin,
17 November 2026): letter determination, authorship, recipients, subject
analysis, dates and titles. The steps below are how the PC applies them; where
they differ, the `qa/` documents win.

**Do the batch by the steps below, in order, and nothing else.** Sections 1
to 9 are reference for the steps. If anything in them seems to disagree with
the steps, follow the steps and tell Robin which line disagrees. If a letter
fits none of the steps, do not invent a rule: hold it (step B7) and say why.

## What changed on 17 November 2026 (read before the next batch)

Robin decided these today. Each is in the steps below and in `qa/`:

1. **Recipients** (#349): a recipient is not a separate requirement. Members,
   committees and caucuses are "As recipient"; a committee with no member
   named goes under the committee. Every other recipient is a name, listed in
   `letter-topics.csv` (QA-analysis-recipients).
2. **Bundles** (#1226): several letters in one PDF are **one record** for the
   whole bundle, with a note beginning "Bundle:". Do not hold a bundle, and
   do not file it under its first letter (QA-analysis-text step 4).
3. **Drafts** (#183, #180): a letter missing its addressee or signers is kept,
   titled "— a draft", with a note beginning "Draft:". A blank date alone is
   not a draft (QA-analysis-letter-determination, "Drafts").
4. **Direction** (#175): a letter written *to* Congress, or with no member at
   either end, gets a row in `vocabulary/letter-direction.csv` (step B4).
5. **Older letters posted later** (#239, #1284): write the letter's true date
   even when it is older than the poster's holding of the address. The build
   places it by capture. Only correct a date that is wrong.
6. **Re-run the pick list before each part of a batch** (section 4). The Mac
   decided 47 letters the PC later read from an old list.
7. **What constitutes done** (#1308): it has OCR, is a letter, has
   authorship, a recipient (if applicable), a date (if determined), at least
   4 subjects with 2 topics, a title in our form, and is published and filed
   (section 5). **A discard is never done or Filed**: it falls under issues.
8. **Duplicates** (#1309): a letter the **same member** posted twice (a
   re-upload, an old and new address) is a duplicate, a type of discard. Note
   "copy of <digest>" on the second copy and list it on the batch's
   "Proposed discards" issue; the Mac runs the duplication check
   (DEDUPLICATION.md) and decides. The same letter on **different members'**
   sites is a shared letter, not a duplicate: read and file each posting.

## The batch, step by step

### A. Start the batch

1. `gh auth status` shows **Robin-IA**. If not, stop and tell Robin.
2. Update both repositories:

   ```bash
   cd letters-from-congress-OCR && git pull && cd ..
   cd Congressional-Letters-Dev && git fetch origin --prune
   git checkout harvest-member-letters && git pull
   ```

3. Check that your previous batch has been merged:
   `gh pr list --base harvest-member-letters --state open`.
   An open PR of yours is fine; the pick list skips its letters.
   Do **not** add to an old branch. Every batch starts a new branch.
4. Make the branch: `git checkout -b pc-read-<N> origin/harvest-member-letters`
   (N = the next batch number).
5. Make the pick list:

   ```bash
   python3 build/pc/pick_list.py --phase ocr --size 500 > batch-<N>.txt
   ```

   Use `--phase ocr` until it says 0 left, then `--phase text` (section 4a).
   It skips letters already read, held, discarded, or in an open PR. Keep
   `batch-<N>.txt` out of the commit.

### B. Each letter, one at a time

Do every step for one letter before starting the next. One pass, no
second visit (section 5).

1. **Get the text:** the letter's record in `text/<Congress>th.jsonl.gz`.
   If the text is garbled or cut off, render the page and read it.
2. **Is it a letter?** (section 5a)
   - Yes → go to 3.
   - Only part of a letter (a signature page, one middle page) → add it to
     #252 and go to the next letter. Write no rows.
   - Fails the **discard criteria** in `letters-discarded/README.md`: not a
     letter (a press release, resolution, newsletter, bill text, exhibit,
     "Dear Employer"), or a letter that is not by a member or congressional
     group, not to or about one, and not a supplement to a member's letter
     → add it to the batch's **"Proposed discards" issue**, hold it (one
     hold row with that issue's number) and go to the next letter. Do not
     write `letters-discarded/` yourself: the Mac decides, by the criteria,
     and records it.
     No text is **not** a reason to discard: it needs OCR.
   - Not sure → hold it (step 7) with the reason.
   - **A draft** (the addressee or the signers missing: "[ADDRESS BLOCK]",
     "[SIGNATURES]", blank signature lines): file it, with the title ending "— a draft" and the note
     beginning "Draft:"; name the sent version in the note if you know it, and
     the Mac links the two (qa/QA-analysis-letter-determination.md, "Drafts").
     A letter with only its day left blank is not a draft.
   - **A bundle** (several letters in one file): read and file it as **one
     record describing the whole bundle**, never under its first letter alone
     (qa/QA-analysis-text.md step 4; Robin, 17 November 2026, #1226). Title
     it for the bundle ("— NECA and others to …"), name every sender and
     recipient organization, and begin the note "Bundle:" with each letter
     inside listed (sender, recipient, date).
3. **Recipient** (qa/QA-analysis-recipients.md; Robin, 17 November 2026).
   Not a separate requirement: never hold a letter for want of one. Read the
   address block, then the salutation, then the body:
   - **Congress** (a member, several members, a committee or caucus): the
     letter is listed under them **"As recipient"**. Members named → each
     member (several: a `joint` row of Bioguide IDs). A committee or caucus
     with no member named → the committee or caucus. No addressee, written
     by others to the posting member → that member, "As recipient, from
     Rep./Sen. X's website". "Dear Colleague" to one chamber → `United States
     Senate` or `United States House of Representatives`.
   - **Everyone else is a name**: an official → the **office**, never the
     person ("to Secretary Austin" → Department of Defense); a company,
     organization or nonprofit (or its CEO) → the organization. Put **each**
     in `letter-topics.csv` with the other names (they count toward the 4
     subjects), and the first in `letter-recipients.csv`.
   - **No addressee, written by the member**, or a **private person** →
     `(no recipient)` in `letter-recipients.csv`; the name stays in the title.

   **Check the term exists** in `vocabulary/terms.csv` or `vocabulary/reviews.csv`.
   If it does not → hold the letter and list it under **Names** on the
   batch's vocabulary issue (step 7), as for any name. Never file it under a
   nearby term.
4. **Author.** The posting member signed it, or is among the signers. If not
   (an agency reply, a letter *to* the member), the title names the sender
   ("— CBO Director Elmendorf to Chairman Baucus …") and the note says so (#175).
   **Direction** (#175): a letter *to* Congress (to a member, committee,
   caucus or chamber, by someone else) gets a row `<digest>,to,<source>` in
   `vocabulary/letter-direction.csv`; one with no member at either end gets
   `<digest>,neither,<source>`. A letter from Congress, the usual case, gets no
   row.
5. **Date.** From the letter's own text: the letterhead or dateline. If it
   has none, in this order, and stop at the first that works:
   1. Read the scan again (Apple Vision text or re-OCR); a garbled dateline
      ("March 3I, 2023") still counts.
   2. The content: a dated event, an official in office, a fiscal year. Name it.
   3. The file name, if it carries a date, never later than the first capture.
      Source: "file name: <name>".
   4. A funding request naming fiscal year N → year N−1, precision `year`.
   5. None → **file it anyway** with no date row; the note says "date
      approximate (#488)". **Never hold a letter for its date.**

   Write a `letter-dates.csv` row only when your date differs from the
   published one.
6. **Title and subjects.**
   - Title: **"On Subject — to whom, D Month YYYY"**, the subject in title
     case; the "to whom" is the office or company, never a CEO's name.
   - Subjects: **at least 4, of which at least 2 are topics; no upper limit**
     (qa/QA-analysis-subject-analysis.md). Topics are only labels in `SUBJECTS` in `build/topics.py`,
     for what the letter is primarily about. Names count as subjects: every
     organization, company, nonprofit, committee, agency or office it names,
     and laws or bills in the vocabulary, written in `letter-topics.csv` by
     their exact vocabulary label. People go under their organization or
     office. Check every label.
   - If the letter's main subject is not in `SUBJECTS` → hold it (step 7).
     Never bend it onto a subject that does not fit.
7. **Hold** (for a missing term or subject, a letter you cannot place, or
   any letter you file an issue about; see "Issues and holds" below): one row in `letters-vocabulary-needs/letters.csv` with the title,
   date, subjects, the term or subject needed, and the reason. Write **none**
   of the other rows for it. Then:
   - **One vocabulary issue per batch**, titled "Reading batch N:
     vocabulary needed", label `vocabulary` (Robin, 17 November 2026), with
     two sections:
     - **Names** (organizations, companies, nonprofits, committees, agencies,
       offices, laws and bills, as recipients or subjects): one row per name,
       with its kind (organization or office), where it would file
       ("Executive branch › Department of Agriculture", "Companies"), and
       every held letter's digest, title and date.
     - **Subjects** (topics the subject list lacks): one row per subject, with
       where it would sit (a topic group, such as "Health" or "Security and
       foreign affairs"), one line from a letter showing why, and the held
       letters.

     If a name or subject is already requested on an open issue, add the
     letters there instead.
   - **Do not add the term yourself.** The Mac adds it, places it, files the
     held letters and closes the issue.
8. **Write the rows** for a letter that is not held, appended at the end of
   each file with `\n` line endings: `letter-titles.csv`, `letter-topics.csv`,
   `letter-recipients.csv`, `letter-dates.csv` (only if step 5 changed it),
   and always one `letters-reviewed.csv` row (section 5, the table).

### Issues and holds

**Whenever the PC files an issue about a letter, it holds the letter.** That
covers missing vocabulary, unreadable text, a posting credited to the
wrong member, a date or authorship it cannot settle, and anything else it
cannot resolve. It writes one row in `letters-vocabulary-needs/letters.csv`
with the issue number and the reason, and no other rows for that letter. **The
Mac resolves the issue and files the letter**, then closes the issue (Robin,
17 November 2026). The PC never files a held letter itself. A **proposed discard** is
held the same way, with the discards issue's number, so the pick list does not
choose it again; the Mac decides it and moves it to `letters-discarded/` or
files it.

### C. Finish the batch

1. Run both checks; both must pass:

   ```bash
   python3 -m unittest discover -s tests
   python3 build/audit_dates.py --ocr-repo ../letters-from-congress-OCR $(cat batch-<N>.txt)
   ```

   The tests must pass. The audit is a report on this batch's letters, not
   pass or fail: look again at each letter it flags, and fix the date row or
   say in the PR why it stands. It does not need `data/letters-parsed.jsonl`,
   which exists only on the Mac (say "holder check not run on the PC").

2. Commit only the CSV files. No code, no `batch-<N>.txt`.
3. Push the branch and open **one** PR:
   `gh pr create --base harvest-member-letters --label reading`.
   - If any letter was proposed as a discard: **one issue** titled
     "Reading batch N: proposed discards", labels `quality control` and
     `reading`, listing each digest, the posting member, what it is, and
     which test it fails. Link it from the PR.
   - Title: "Reading batch N: X of 500 letters filed, Y held".
   - Body: filed, held (with the term issues linked), the discards issue,
     #252 partials, and "holder check not run on the PC".
4. Tell Robin the PR number and the issue numbers (vocabulary, proposed
   discards, any others). **Never merge**, and never file a held letter: the
   Mac resolves each issue and files its letters.
5. Start the next batch at A1. The pick list skips this batch's letters
   while its PR is open.

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
| Mac | 106th–115th, most-posted first, 200 letters a batch; and the letters left on issues, in any Congress |

Stay in your own range, so the two machines never write rows for the same
letter. **Re-run the pick list before each part of a batch**, after pulling
both repositories: never read on from a list made earlier (17 November 2026:
the PC read 47 letters from a morning list that the Mac had decided that
afternoon, and their rows had to be dropped). The pick list leaves out
anything already read, held, discarded or in an open PR, but only as of the
moment it runs.

## 4a. The PC's work order (Robin, 17 November 2026)

Pull `letters-from-congress-OCR` before building a pick list: the Mac
pushes a fresh `progress.csv` after each publish. One row per scan
(distinct file); the first Congress is the lowest in `congresses`.

1. **Now: finish the OCR scans of the 116th–119th.** Pick list: `text=True`,
   `reviewed=False`, `ocr=True`, first Congress 116 or later
   (`pick_list.py --phase ocr`). About 2,100 were left on 17 November,
   counting newly harvested letters; the script prints the current count.
   Keep the 500-letter batches.
2. **Next: the text-layer letters of the 116th–119th**, newest Congress
   first (119th, then 118th, 117th, 116th). Pick list: `text=True`,
   `reviewed=False`, `ocr=False` (`pick_list.py --phase text`). About
   30,600 letters. Their text is
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
   body (qa/QA-analysis-recipients.md wins where this differs). File it by the kinds in section 6: Congress "As recipient",
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
     each one is filed; there is no limit on subjects (QA-analysis-subject-analysis).
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
        Hall") is not this case: hold it (step B7) and say so in the PR.
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
   An older letter posted later keeps its true date (posted later, #239,
   #1284; see "A date before the poster held the address" below).
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

A letter is done when (Robin, 17 November 2026; qa/QA-Analysis-methodology.md,
"Status values"):

- it has text (OCR or a text layer);
- it is a letter: not discarded, and not a true duplicate (one member's second
  copy, a potential discard needing review);
- its authorship is established;
- its recipient, if it has one, is a reviewed term (a letter with no addressee
  is `(no recipient)`);
- its date is settled, if it can be determined;
- it has **at least 4 subjects, at least 2 of them topics**, names included;
- its title is confirmed and in the established form;
- it is published and filed where it needs to be.

A discard or a duplicate is never done: it falls under issues.

Each batch is one PR, which appends rows to these files in the dev repository:

| File | Row | Rules |
| --- | --- | --- |
| `vocabulary/letter-titles.csv` | `digest,title,source` | Form: **"On Subject — to whom, D Month YYYY"**, e.g. "On Funding the Sea Grant Program in 2019 — to Chairman Moran and Ranking Member Shaheen, 11 April 2018". A letter to a company is filed under the company, with no CEO's name in the "to" part. |
| `vocabulary/letter-topics.csv` | `digest,topics,source` | `;`-separated, **at least 4, at least 2 of them topics**: topics from `SUBJECTS` in `build/topics.py`, plus the organizations, committees, agencies, offices, and laws or bills the letter names, by exact vocabulary label (qa/QA-analysis-subject-analysis.md). Check every label before writing it. |
| `vocabulary/letter-dates.csv` | `digest,date,precision,source` | Only when the letter's own date differs from the published date. The source says why, e.g. "the letterhead; was 2018-09-19 (captured-by)". |
| `vocabulary/letter-recipients.csv` | `digest,recipient,source` | One row per letter: the reviewed term from step 2 (an office, a committee, a member's name, or a company's label). Not for a private citizen. |
| `vocabulary/reviews.csv` | `candidate,letters,decision,…` | Only when step 2 needs a decision the vocabulary lacks: a `joint` row for several offices at once, or a `merge` row for a company not yet reviewed. |
| `vocabulary/letter-direction.csv` | `digest,direction,source` | Only for a letter not from Congress: `to` (written to Congress) or `neither` (no member at either end), #175. |
| `vocabulary/letters-reviewed.csv` | `digest,reviewed,title,date,topics,filing,note,date_audited` | One row per letter read. `date` is `yes` if you added a date row, otherwise `unchanged`; `filing` is `yes` if you added a recipient row. |
| `letters-vocabulary-needs/letters.csv` | `digest,title,date,topics,proposed_subjects,issue,note` | For a letter that needs a subject the vocabulary lacks. It stays here and goes in none of the files above. Also open a vocabulary-request issue for the term (§6). |
| `letters-discarded/letters.csv` | `digest,title,reason,issue,decided` | Written by the Mac, which decides discards by the criteria in `letters-discarded/README.md` (Robin, 17 November 2026). The PC proposes them in an issue (step B2) and never writes this file. |

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

**Not signed by a member?** It is still kept when it belongs to Congress
another way: written to a member or congressional group, naming one, or
supplementing a member's letter. A letter with none of these, and anything
that is not a letter, follows the **discard criteria** in
`letters-discarded/README.md` (Robin, 17 November 2026).

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
| 4 | Signed on behalf of a committee or caucus? | Go to 5 | Go to 4a |
| 4a | Written **to** a member or congressional group, or **names** one, or a **supplement** to a member's letter (enclosure, reply, a document the letter cites)? | Kept: titled with its sender (#175); a supplement is linked in `letter-related.csv` | Propose it as a discard (test 2 of `letters-discarded/README.md`) |
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

- **Date order** (#172): as in step B5: the letter's text, the content, the
  file name, the funding rule, then file it anyway.
- **A date before the poster held the address** (Robin, 17 November 2026,
  #239, #1284). If a member re-posted an older letter (a caucus site, a
  successor's site, another member's letter, a 1998 letter posted in 2001),
  write its **true date** anyway. The build places the posting by its first
  capture under whoever held the address then, flagged "Posted later" on the
  page. Only a date that is simply wrong (a misread year, a typo the content
  contradicts) is corrected instead.
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
  "Dear Employer" reference) goes on the batch's "Proposed discards" issue
  (step B2). The Mac decides and adds it to
  **`letters-discarded/letters.csv`**, and it is not read again.
- **Copies** (#224, #1309): note "copy of <digest>". Posted by the same
  member, it is a duplicate: propose it as a discard (the Mac decides by
  DEDUPLICATION.md, and every duplicate gets an issue for review). Posted by a
  different member, it is a shared letter: same title, same topics, filed.
- **Text that is only part of the letter** (#252), such as a signature page,
  footers or a middle page: skip the letter and add it to #252.
- **Recipients: three kinds, three ways to file** (Robin, 15 November 2026;
  #352, #357, #391). Read the address block, never guess, and sort the
  recipient into one of these. **Superseded in part on 17 November 2026**:
  the recipient is not a separate requirement, every recipient outside
  Congress is a name in `letter-topics.csv`, and a committee or caucus with no
  member named is itself "As recipient" (qa/QA-analysis-recipients.md wins).
  1. **A member or committee of Congress** (a chair and ranking member, the
     Speaker, a leader, a senator, a committee or caucus). File the letter **"As recipient"** (#352):
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
     or local office, State and local government › the state), and **under its
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
  CEO's name. Where the address block does not say who the recipient is,
  follow the no-addressee rows of step B3.

  **How kind 3 is recorded** (`build/filed_orgs.py`, from the Mac):
  - **One company:** put the company's reviewed label in
    `letter-recipients.csv`, for example `<digest>,Equifax,<source>`. The
    build then files the letter under the company **as a topic** and
    publishes it with **no recipient**, because only government officials
    are shown as recipients. A name in `reviews.csv` that resolves only to
    companies ("Mr. Bastian" → Delta Air Lines) is handled the same way.
  - **Several companies** (one letter to four airline CEOs): `letter-recipients.csv`
    takes one row per letter, so add **each company's label to the letter's
    row in `letter-topics.csv`**, after its subjects. There is no limit on
    subjects: four or more companies are all kept.
  - **A company the vocabulary lacks:** hold the letter and open a term
    issue (step B7). The Mac adds the company's `reviews.csv` row and files
    the letter.
  - **A member and a company together** ("Chairman Wicker and Mr.
    Zuckerberg"): the member stays the recipient (kind 1), and the company
    is added as a topic.
- **New subjects** are never added during reading, and a letter is **never
  bent onto a subject that does not fit** to avoid a hold. When the letter's
  subject is not in `SUBJECTS`:
  1. **Move the letter to the holds folder:** a row in
     `letters-vocabulary-needs/letters.csv`, with the proposed subject. A held
     letter goes in none of the other files until the subject exists.
  2. **Open an issue for the request**, one per term, titled "New
     vocabulary term needed: <term>" and labelled `vocabulary`: the term,
     where it would file, the held letters' digests, titles and dates, and
     one line from the text showing why. Not a comment on #221: Robin,
     16 November 2026, "It should file an issue with the vocabulary request
     and move a letter to folder for holds."

  **The PC recommends a term; the Mac adds it.** A term request says the
  term, the held letters, and *where it would file* (for example "State of
  Ohio › local government"). The Mac writes the term, places it in the
  hierarchy (`hierarchy.csv`, creating the state or group entries it needs),
  files the held letters and closes the request.

  The Mac makes the vocabulary PRs (`build/topics.py`, `reviews.csv`,
  `hierarchy.csv`). The same goes for a **recipient with no term** (a
  company, a state office, a foreign official): hold the letter and open its
  term issue (step B7), rather than filing it somewhere else. Between 15 and 16 November, ten PC batches (#369 to #415) filed no
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
vocabulary** and how many recipients have no term, with the term issues
linked. "0 held" is written out, not left blank. On the PC, `--ocr-repo` (or `LETTERS_OCR_REPO`) points the audit at the text repository; without it the audit sees only the PC's local text and reports most letters as unreadable (#332). The PR title follows the existing pattern ("Letters review:
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
| `vocabulary` | The batch's "Reading batch N: vocabulary needed" issue, holds, recipients, subjects, `reviews.csv` |
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
- **It does not query or fetch from the Wayback Machine.** Reading needs only
  the text repository. The Wayback rule (Robin) is **at most 2 workers in all,
  across every machine and job, each pausing 4–5 seconds between requests,
  and 1 after a 429 or 503**, and the Mac's harvests usually hold both. If a
  scan must be fetched, ask Robin first. `build/pc/fetch_for_ocr.py` is capped
  at 2 workers with a 4.5-second pause (#67), so it cannot break the rule.

## 9. Open issues to know

| Issue | About |
| --- | --- |
| #172 | The dating order |
| #175 | Letters written to Congress, not from it |
| #204 | The PC's agency letters |
| #221 | Proposed new subjects, with their held letters (history only; new requests are their own issues, step B7) |
| #224 | Duplicate letters |
| #242 / #243 | Letters in Word or HTML, not PDF (survey, then conversion) |
| #252 | Text layers that cover only part of a letter |
| #411 | What is a letter: the criteria in section 5a, in any format |
