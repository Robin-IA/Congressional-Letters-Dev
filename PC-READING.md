# For Claude on the PC: where the reading work lives

**Updated 15 November 2026.** Read this first in any new session on the PC,
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
| `vocabulary/letters-reviewed.csv` | `digest,reviewed,title,date,topics,filing,note,date_audited` | One row per letter read. `date` is `yes` if you added a date row, otherwise `unchanged`. |
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
- **New subjects** are never added during reading. Hold the letter in
  `letters-vocabulary-needs/letters.csv` and comment on #221. Vocabulary
  changes go in their own PR to `build/topics.py`. Match words are plain
  lowercase words, never regex.

## 7. Before opening a PR

```bash
python3 -m unittest discover -s tests
python3 build/audit_dates.py
```

Both must pass. The PR title follows the existing pattern ("Letters review:
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
