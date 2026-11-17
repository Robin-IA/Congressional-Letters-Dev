# For Claude on the Mac: reading the 106th–115th, step by step

**The rules are the QA-Analysis-methodology** (`qa/QA-Analysis-methodology.md`
and its step documents); this file is how the Mac applies them. Subjects: at
least 4 per letter, no upper limit, names counting (Robin, 17 November 2026).

**Written 17 November 2026.** This is the Mac's reading work. The PC's is
[PC-READING.md](PC-READING.md), whose rules for recipients, dates, titles and
subjects apply here too. Read this first in a new session, or after the
tokens reset (Robin: 12:45 AM and ; commit the rebuilt
 with the next batch PR (the tests check name subjects
against it, and a stale copy refuses new committees and agencies);5:45 AM EST).

**What and why.** Robin, 17 November 2026: "Let's do the 106-115th letters of
unfiled letters in the Mac's range" and "Just file issues for anything you can
not resolve." On that day about 27,850 letters in the 106th–115th were not
done: about 23,000 OCR scans and about 5,100 text-layer letters. The PC reads
the 116th–119th; the Mac never picks a letter whose first Congress is past
the 115th.

**The difference from the PC:** the Mac **adds missing terms itself** and
files the letter in the same PR. It holds nothing for vocabulary. It opens an
issue only for what it cannot resolve.

## Where things are

| What | Where |
| --- | --- |
| Pipeline (the built vocabulary, the explorers) | `~/ia/congressional-member-letters` |
| Dev clone that `fold.sh` merges in | `~/explorer-checks/Congressional-Letters-Dev` (remote `dev`) |
| Worktree for writing a batch | `~/explorer-checks/wt-vocab` (remote `dev`) |
| Text and `progress.csv` | `~/ia/letters-from-congress-OCR` |
| The tools | `build/mac/` in this repository: `mac_read.py`, `fold.sh`, `resolve_append.sh` |
| The readers' instructions | `build/mac/READER-BRIEF.md` |
| Postings set aside as not letters | `build/mac/skip.txt` (one digest a line), listed on #1222 |
| Working folder for batch files | `W=~/explorer-checks/mac-read` (`subjects.txt`, `skip.txt`, `bN*.json*`) |

Run the tools from the copies in the pipeline (`~/ia/congressional-member-letters/build/mac/`).
They are synced there like any merged file.

## Before the first batch of a session

1. `gh auth status` shows **Robin-IA**.
2. Pull the text: `cd ~/ia/letters-from-congress-OCR && git pull`.
3. Update the vocabulary build, so the writer checks against today's terms:
   `cd ~/ia/congressional-member-letters && python3 build/build_vocabulary.py`.
4. Make the working folder and the subject list:

   ```bash
   W=~/explorer-checks/mac-read; mkdir -p $W
   M=~/ia/congressional-member-letters/build/mac
   python3 $M/mac_read.py subjects $W/subjects.txt
   cp $M/skip.txt $W/skip.txt   # if $W/skip.txt has newer lines, keep those
   ```

5. Check no Mac batch PR is open and unmerged:
   `gh pr list -R Robin-IA/Congressional-Letters-Dev --state open`. Fold or
   close it first, so its letters are not picked twice.

## One batch (200 letters)

N is the next batch number: one more than the last "Mac reading, 106th–115th,
batch N" PR.

1. **Pick and split** (in the pipeline):

   ```bash
   cd ~/ia/congressional-member-letters
   python3 build/mac/mac_read.py pick 200 $W/bN.json $W/skip.txt
   python3 build/mac/mac_read.py split $W/bN.json 4
   ```

   `pick` takes the most-posted letters first and skips anything read, held,
   discarded or in `skip.txt`. It prints how many are left.

2. **Read.** Start four Agent subagents **in one message**, model `sonnet`,
   one per part, each with this prompt (k = 1 to 4):

   > Follow the reading brief at
   > /Users/robinfay/ia/congressional-member-letters/build/mac/READER-BRIEF.md
   > exactly. Read it first. Working directory for vocabulary lookups:
   > /Users/robinfay/ia/congressional-member-letters. Subjects list:
   > /Users/robinfay/explorer-checks/mac-read/subjects.txt. Input letters:
   > /Users/robinfay/explorer-checks/mac-read/bN-k.json (50 letters). Write
   > your output to: /Users/robinfay/explorer-checks/mac-read/bN-k.jsonl. Do
   > not modify any other file. Do not use git. Do not fetch from the web.

   Wait for all four to report. Each takes about 3 minutes and about 150,000
   tokens.

3. **Check what they flag.** Read their reports. Then
   `cat $W/bN-?.jsonl > $W/bN.jsonl` and look for these:
   - **A letter to several offices** where only one proposed term was given
     (batch 1: Faso to five state agencies). Edit that line so `new_term` is
     a list of every missing office and `joint` names all of them.
   - **A proposed term that already exists under another name.** Compare
     each `new_term` with `vocabulary/terms.csv` (`grep -i`). Follow the house
     forms: "Florida Attorney General", "Governor of Ohio", "Embassy of
     France", "U.S. Embassy in Beijing".
   - **A date the reader doubted.** The writer rejects nothing on dates; the
     holder check at merge catches a date that leaves a posting with no holder.

4. **Write** (in the worktree, on a new branch):

   ```bash
   cd ~/explorer-checks/wt-vocab && git fetch -q dev
   git checkout -q -B mac-read-106-115-bN dev/harvest-member-letters
   python3 ~/ia/congressional-member-letters/build/mac/mac_read.py write $W/bN.json $W/bN.jsonl
   ```

   It prints `filed`, `dates`, `new_terms`, `joint`, `notletter` and
   `unresolved`. It checks every recipient, company and subject against the
   **pipeline's** built vocabulary. A proposed term goes into `reviews.csv` (a
   `merge` row) and `hierarchy.csv`. A missing state chain is built up to
   State and local government. A letter with an older row is replaced, not
   duplicated.
   - **Unresolved**: fix the line in `bN.jsonl` (the right label, a subject
     from `subjects.txt`) and run it again from step 4's `git checkout`. If you
     cannot fix it, leave it out and open an issue (see below).

5. **Test and open the PR:**

   ```bash
   python3 -m unittest discover -s tests          # must say OK; read it, do not
                                                  # chain on it (grep succeeds either way)
   git add vocabulary && git commit -m "Mac reading, 106th-115th, batch N: X letters filed"
   git push -q dev mac-read-106-115-bN
   gh pr create -R Robin-IA/Congressional-Letters-Dev --base harvest-member-letters \
     --head mac-read-106-115-bN --label "reading,vocabulary" \
     --title "Mac reading, 106th–115th, batch N: X letters filed" --body-file <body>
   ```

   The body gives the counts, the new terms, the dates changed and what was
   left out. It ends with the Claude Code line. Never Robin's email.

6. **Fold:** `bash ~/ia/congressional-member-letters/build/mac/fold.sh <PR>`.
   It runs the tests and the holder check, merges, and syncs the files into
   the pipeline. Expect "merged + synced … 0 without a holder". On CONFLICT
   run `resolve_append.sh <PR>`. On anything else, read the message and fix
   the branch. Never force a merge.

7. **Not letters** (the discard criteria in `letters-discarded/README.md`): the writer records each
   `notletter` in `letters-discarded/letters.csv` itself, in the batch PR:
   **the Mac decides discards** (Robin, 17 November 2026). Check each one
   against the two tests before writing: unreadable text is `unsure` (OCR),
   not a discard. A test-2 discard that the search holds back: read each
   candidate it names. If none cites the letter, set `"supplement_checked":
   true` on its line, with what was read in `note`, and write again. If one
   does, file the letter and link it in `letter-related.csv`. Partials (`status: partial`) go on #252 and into
   `skip.txt`. Also decide any open "Reading batch N: proposed discards"
   issue from the PC the same way, then comment and close it.

8. Go back to 1 with N+1.

## What comes from the PC (the contributor), and what the Mac does

The PC reads the 116th–119th by PC-READING and never merges or files a held
letter. For each batch it sends a PR and up to two issues; Robin passes on
their numbers. **Handle them in this order**, every time, from the OCR:

1. **The batch PR** ("Reading batch N: …"): `bash build/mac/fold.sh <PR>`
   (tests, holder check, merge, sync). On CONFLICT, `resolve_append.sh <PR>`.
   It refuses a PR that touches code; read such a PR before merging it.
   Check the PR says how many letters were held and lists its issues.
2. **"Reading batch N: vocabulary needed"** (names and subjects):
   - **Names**: add each as a `reviews.csv` merge row (kind, `broader` in the
     house form, QA-analysis-recipients) and a `hierarchy.csv` row, building a
     state chain where needed. A name that already exists under another label:
     use that label.
   - **Subjects**: add each to `build/topics.py` (hand-filed, no match words)
     with its place in `hierarchy.csv`; if it is better served by an existing
     subject or a name, say so on the issue.
   - **File the held letters** from `letters-vocabulary-needs/letters.csv`
     (their title, date and subjects are already read): recipient and topic
     rows, a reviewed row, the hold row removed. One vocabulary PR for the
     batch; comment what was added and where; close the issue.
3. **"Reading batch N: proposed discards"**: decide each from its OCR by both
   tests of QA-analysis-letter-determination, with the supplement search for
   test 2. Discard: a `letters-discarded/` row with its Wayback link; kept:
   file it like any held letter. Remove its hold row. One PR; comment each
   decision; close the issue.
4. **Any other issue the PC files about a letter** (unreadable text, a bundle,
   wrong attribution, an unsettled date or author): resolve it (re-OCR, a
   rule, a date from the content), file the letter, remove its hold, close
   the issue.
5. **Ask Robin only** when the rules do not settle it: a new kind of case, a
   change to a rule, or a judgment the criteria leave open (bundled PDFs,
   #1226). Say on the issue that it waits on Robin.
6. After the next publish, the PC's pick list sees the batch as done.

## Issues: only for what cannot be resolved

Open one with label `reading` (plus `vocabulary`, `dates` or `quality control`
as fits) when:
- a recipient cannot be identified or placed, even after reading the scan;
- a letter needs a rule that does not exist yet (Robin decides rules);
- the text is too damaged to read, and the PDF needs fetching and OCR
  (`OCR` label; #122, #559).

Name the digest, the posting member and file, and what was read.

## Publishing

Not after every batch. Publish after every 5 batches or so, or when Robin asks,
with the command in the handoff (build_congress 106-119, export_csv,
build_vocabulary, build_hub, progress, publish_explorers). Then run
`export_text.py` and `build/qa_status.py` (the per-Congress QA status CSVs).
Commit the rebuilt `vocabulary/terms.csv` with the next batch PR,
and push `progress.csv` and `qa-status/` to `letters-from-congress-OCR` by
branch and PR, so the PC's pick list and the QA status stay current.

## Rules learned in batch 1 (PR 1221)

- Readers must see a letter's end as well as its beginning: `pick` keeps the
  first 4,500 and last 1,500 characters of a long letter.
- Titles name the official as addressed ("to Secretary Hagel"); the
  recipient term is the office.
- Subcommittees file under the full committee.
- A letter *to* a member from someone else is kept, filed with the member
  "As recipient" (a `joint` of Bioguide IDs for several), and titled with
  the sender.
- **Readers can read the wrong file.** In batch 3, two of four readers wrote
  another part's letters over their own digests. The writer now refuses a
  title whose words are mostly absent from the letter's text, and the prompt
  says to read only its own file. If many are refused, re-run that part.
- The writer reads the pipeline's built `vocabulary/terms.csv`. **Commit the
  rebuilt `terms.csv` with the first batch after each publish**: the subjects
  test checks name subjects against the committed copy, and a stale one refuses
  new committees and agencies (batch 20; the PC's readers check it too).

## Where it stands

| Batch | PR | Filed | Notes |
| --- | --- | --- | --- |
| 1 | 1221 | 198 | 17 new terms, 14 joint, 9 dates; 2 not letters to #1222 |
| 2 | 1225 | 190 | 9 new terms, 10 joint, 5 dates; 3 not letters to #1222; 3 partial to #252; 3 unresolved (issues); 1 hex digest dropped |
| 3 | 1241 | 195 | read twice (two readers mixed parts; caught by the title guard); 17 new terms; a supplement found by the search (HHS to TMC, linked to Cuellar's letter); 3 discarded |
| 4 | 1245 | 196 | 7 new terms, 9 joint; 3 discarded (the Smith statement, and two test-2 letters after the supplement search was checked by hand); 1 partial to #252 |
| 5 | 1248 | 199 | 10 new terms (incl. Prime Minister of Israel), 14 joint, 4 dates; 1 discarded (a hearing opening statement); 1 title hand-checked past the guard |
| 6 | 1251 | 195 | 11 new terms, 8 joint, 4 dates; 4 discarded (a speech, a news release, Baldwin's guidelines sheet, a USDA letter by test 2); 1 partial to #252 |
| 7 | 1252 | 199 | 12 new terms (Oregon state officers for a four-office joint letter), 11 joint, 6 dates; 1 discarded (a sign-on statement) |
| 8 | 1253 | 194 | 13 new terms, 11 joint, 4 dates; 6 discarded (a floor statement, blank forms and instruction sheets, an EPA letter by test 2); an upside-down scan rotated and OCR'd |
| 9 | 1254 | 197 | 11 new terms, 15 joint, 3 dates; 1 discarded (hearing talking points); 2 partial to #252; published after batch 8 (25.5% done) |
| 10 | 1255 | 199 | 16 new terms, 11 joint, 4 dates; 1 discarded (an amicus brief); an open letter to Texas college presidents filed with no recipient |
| 11 | 1256 | 196 | 9 new terms, 15 joint, 4 dates; 2 supplements kept and linked after the search (Hua Qu to Trump; governors on 1332 waivers); 3 discarded; 1 partial |
| 12 | 1257 | 200 | 8 new terms, 15 joint, 6 dates; a supplement found by the search (AFL-CIO to the SEC on Navient, linked to Warren's letter); no discards |
| 13 | 1258 | 196 | 8 new terms, 8 joint, 4 dates; 3 discarded (a blank form; EPA's 2016 Bay-Delta comment and a UMWA Funds notice, both test 2 after the search was read by hand); 1 bundle to #1226 |
| 14 | 1259 | 198 | 14 new terms (a Colorado local-government group built for Denver), 7 joint, 5 dates; 1 discarded; 1 partial; published after batch 13 (26.7% done) |
| 15 | 1260 | 199 | 6 new terms, 10 joint, 2 dates; 1 discarded (Treasury's response to a SIGTARP draft, test 2 after the search was read by hand) |
| 16 | 1261 | 194 | 11 new terms, 10 joint, 3 dates; 5 discarded (2 not letters; 3 test-2 letters after the search was read by hand); a tribal letter naming the Nevada delegation kept; 1 partial |
| 17 | 1262 | 198 | 14 new terms, 6 joint, 4 dates; 2 discarded (floor remarks; asylum attorneys' letter to Kelly by test 2) |
| 18 | 1263 | 194 | 7 new terms, 10 joint, 6 dates; 3 discarded by test 2 after the search was read by hand; 2 bundles to #1226; 1 partial |
| 19 | 1265 | 196 | 4 new terms, 7 joint, 1 date; 4 discarded (a press release, a booklet, a form; FEMA's letter to North Dakota by test 2) |
| 20 | 1272 | 198 | first batch under QA-Analysis-methodology: 190 with 4+ subjects, 8 under 4 (noted for review); 57 new terms (names count); 15 joint, 4 dates; 1 discarded; 1 partial |
| 21 | 1281 | 196 | under the 2-topic rule: 193 meet it, 5 short (noted); 52 new terms, 7 joint, 4 dates; 3 discarded (draft bill text; two letters by test 2 after the search was read by hand); 1 partial |
| 22 | (this PR) | 196 | 6 short of 4 subjects or 2 topics (noted); 75 new terms, 9 joint, 7 dates; 4 discarded (a Warren report, a forwarded email, a blank grant-request form, and FEMA to North Dakota on Drayton by test 2 after the search was read by hand); the service organizations' Military Lending Act letter linked to McCaskill's |
