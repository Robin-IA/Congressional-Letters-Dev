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

## 5. What "done" means, and the files a PR touches

### One pass per letter (Robin, 15 November 2026)

Reading is **one process**. Each letter is taken all the way through, in this
order, in the same batch and the same PR. The recipient is **not** a separate
pass or a separate PR (the earlier recipient-only PRs, #405 and #408, are the
last of that kind).

1. **Read the text** (OCR or text layer) against the letter, not the file name.
2. **Find the recipient** in the address block, then the salutation, then the
   body. File it by the three kinds in section 6: Congress "As recipient",
   an official under the office, a company or organization as a topic, and a
   private citizen under no name. One row in `letter-recipients.csv`;
   several offices at once is a `joint` row in `reviews.csv`; several
   companies go in `letter-topics.csv`.
3. **Find who wrote it, and where it files.** Check that the posting member
   signed it or is among its signers. A letter written *to* the member is
   titled with its sender (#175). The Congress follows from the letter's date
   and who held the posting address then (the holder check). Say in the note
   when the signers and the posting member differ.
4. **Write the title** in our form, "Subject — to whom, D Month YYYY", with
   the recipient from step 2 (an office or company, never a CEO's name).
5. **Settle the date** by the dating order (#172): the letterhead, then the
   file name, then the PDF metadata, then review. Refuse a date that leaves the
   posting with no holder (#239).
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
| `vocabulary/letter-titles.csv` | `digest,title,source` | Form: **"Subject — to whom, D Month YYYY"**, e.g. "Funding the Sea Grant program in 2019 — to Chairman Moran and Ranking Member Shaheen, 11 April 2018". A letter to a company is filed under the company, with no CEO's name in the "to" part. |
| `vocabulary/letter-topics.csv` | `digest,topics,source` | `;`-separated, **only labels already in `SUBJECTS`** in `build/topics.py`. Check every label before writing it. |
| `vocabulary/letter-dates.csv` | `digest,date,precision,source` | Only when the letter's own date differs from the published date. The source says why, e.g. "the letterhead; was 2018-09-19 (captured-by)". |
| `vocabulary/letter-recipients.csv` | `digest,recipient,source` | One row per letter: the reviewed term from step 2 (an office, a committee, a member's name, or a company's label). Not for a private citizen. |
| `vocabulary/reviews.csv` | `candidate,letters,decision,…` | Only when step 2 needs a decision the vocabulary lacks: a `joint` row for several offices at once, or a `merge` row for a company not yet reviewed. |
| `vocabulary/letters-reviewed.csv` | `digest,reviewed,title,date,topics,filing,note,date_audited` | One row per letter read. `date` is `yes` if you added a date row, otherwise `unchanged`; `filing` is `yes` if you added a recipient row. |
| `letters-vocabulary-needs/letters.csv` | `digest,title,date,topics,proposed_subjects,issue,note` | For a letter that needs a subject the vocabulary lacks. It stays here and goes in none of the files above. Also comment on #221. |

Write CSV rows with `\n` line endings and append only, never reorder.
`source` is "read from the text of the letter (the PC)".

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
- **Not every PDF is a member's letter.** An agency reply, an association's
  letter to a member, a CBO letter or a newspaper page is titled with its
  sender ("— CBO Director Elmendorf to Chairman Baucus …") and noted (#175).
  A page that is not a letter at all (a draft resolution, a newsletter) is
  skipped and listed in the PR for a filing decision.
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
     **under the official's office** in the matching area of the topic list
     (Government officials: Executive Office of the President, a department or
     agency, Judicial branch, State and local government), and **under its
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
- **New subjects** are never added during reading. Hold the letter in
  `letters-vocabulary-needs/letters.csv` and comment on #221. Vocabulary
  changes go in their own PR to `build/topics.py`. Match words are plain
  lowercase words, never regex.

## 7. Before opening a PR

```bash
python3 -m unittest discover -s tests
python3 build/audit_dates.py --ocr-repo ../letters-from-congress-OCR
```

Both must pass. On the PC, `--ocr-repo` (or `LETTERS_OCR_REPO`) points the audit at the text repository; without it the audit sees only the PC's local text and reports most letters as unreadable (#332). The PR title follows the existing pattern ("Letters review:
agency letters, round N (25 read from full text)"). The body lists copies,
holds and gaps. If rows from a Mac batch land at the same time, the conflict
is only appended rows, and the Mac resolves it by keeping both sets.

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
