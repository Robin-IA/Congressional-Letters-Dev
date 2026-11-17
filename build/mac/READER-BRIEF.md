# Reading brief: Letters from Congress, 106th–115th (the Mac)

The rules behind each step are the QA-Analysis-methodology (`qa/`). This brief
is how a reader applies them.

You read letters that members of Congress posted on their websites, and you
write one JSON line per letter. Read each letter's `text` (OCR or PDF text
layer) **against the letter itself, never the file name alone**. Do every step
for one letter before going on to the next.

Input: a JSON file of letters. Long texts keep the beginning and the end (signers), with "[... middle omitted ...]" between. Each has `digest`, `congresses`, `postings`
(member, bioguide, file, capture, date_now, precision_now) and `text`.

Output: write a JSONL file (one object per line, **one line for every letter**)
to the path you are given. Fields:

```
{"digest": "<full digest>",
 "status": "file" | "partial" | "notletter" | "unsure",
 "title": "On Subject in Title Case — to whom, D Month YYYY",
 "recipient": "<exact vocabulary label>",
 "recipient_source": "short: where you read it (address block / salutation / ...)",
 "joint": null or ["<bioguide id or exact label>", ...],
 "new_term": null or {"label": "...", "kind": "organization"|"office", "broader": "<exact hierarchy node>"},
 "topics": ["<exact subject>", ...],
 "names": ["<exact organization, committee, agency or office label>", ...],
 "date": "YYYY-MM-DD" or "",
 "precision": "day" | "month" | "year",
 "date_source": "the letterhead" | "the dateline" | "content: ..." | "file name: ..." | ...,
 "note": "one line: anything a checker should know"}
```

## Read only your own file

Read **only** the input file you are given. The folder holds other readers'
files (the whole batch, other parts, their outputs); never open them. Each
output line's `digest` must be the digest of the letter whose text you read
for that line. Before writing, check that the words of each title appear in
that same letter's text: the writer refuses a title that does not match
(batch 3: two readers wrote another part's letters over their own digests).

**Keep any helper script in a folder of your own**, named for your part
(e.g. `/tmp/reader-b4-2/`), never a shared name such as `/tmp/show.py`:
in batch 3 readers overwrote each other's helper and printed the wrong
letters.

## Steps for each letter

1. **Is it a letter?** It needs an addressee (person, office, company,
   organization; a salutation or inside address shows it) and a signer.
   - Only part of a letter (a signature page, a middle page, footers): `status: "partial"`.
   - **Several letters in one file** (a bundle: support packets, replies, a
     letter with a press release or memo): `status: "file"`, ONE row for the
     whole bundle. Title it for the bundle ("On Support for X — NECA and
     others to Speaker Ryan and Representative Newhouse, <first letter's
     date>"); put every sender and recipient organization in `names`; begin
     `note` with "Bundle:" and list each letter (sender, recipient, date) and
     any non-letter part. Discard only if no letter in it passes test 2
     (qa/QA-analysis-text.md step 4).
   - Not a letter at all (a resolution, Senate Journal page, newsletter, bill
     text, press release — even one quoting a letter in full — report,
     exhibit, form): `status: "notletter"`, with a short `title` saying what
     it is and the reason in `note`.
   - A letter that is **not by** a member or congressional group (committee,
     caucus, delegation), **not to or about** one (names no member or
     district), and **not a supplement** to a member's letter (enclosure,
     reply, or a document the member's letter cites): `status: "notletter"`,
     `note` beginning "no relation to Congress:". The full criteria are in
     `letters-discarded/README.md`.
   - Unreadable text is **not** "notletter": use `unsure` with "needs OCR".
   - A letter **to** the member from someone else (agency reply, association,
     constituent group) IS kept: title it with the sender ("— Secretary
     Chu to Senator Boxer, 3 May 2010") and say so in `note`.
   - Cannot tell: `status: "unsure"` with the reason in `note`.
2. **Recipient** — address block, then salutation, then body
   (qa/QA-analysis-recipients.md). Members, committees and caucuses are
   "As recipient"; everyone else is also a name. Pick ONE:
   - A member of Congress: their full name as in `vocabulary/terms.csv`
     (kind `member`). Several members: `joint` = their bioguide IDs (from
     terms.csv `term_id` "M-<id>"; give the id without "M-"), `recipient` "".
   - A committee's members named (a chair and ranking member): `joint` = their
     bioguide IDs, and the committee's label in `names`. A committee or caucus
     with no member named: the committee's label as `recipient`.
   - A federal, state, local or foreign **official**: the **office** label
     (Secretary Austin → "Department of Defense"; Governor of Ohio → the governor
     term), never the person. Several offices: `joint` with their labels.
     Also list every office in `names` (a recipient outside Congress is a name).
   - A company or organization, or its CEO: the organization's label, never
     the person. Several companies: `recipient` the first, and **every** one
     (the first too) in `names`.
   - "Dear Colleague" to one chamber: "United States Senate" or "United States
     House of Representatives".
   - No addressee and the member wrote it (open letter, notice to constituents),
     or a private person: "(no recipient)".
   - Subcommittees file under the full committee ("Senate Committee on
     Appropriations"); say the subcommittee in the title.
   - Find the label with `grep -i "<name>" vocabulary/terms.csv` (columns:
     term_id,label,kind,...; use only rows with status `preferred`) and
     `grep -i "<name>" vocabulary/reviews.csv` (candidate column, status
     `accepted`). Copy the label exactly.
   - **Not in the vocabulary:** propose it in `new_term`: the office's or
     organization's proper name as `label`, `kind`, and `broader` = an existing
     node of `vocabulary/hierarchy.csv` (column `term`; e.g. "Federal agencies",
     "Companies", "Associations and other organizations", "Nonprofits",
     "Colleges and universities", "Ohio state government agencies",
     "Foreign governments"). Check the node exists with grep. Then set
     `recipient` to the same label. If you cannot place it, `status: "unsure"`.
3. **Author.** Check the posting member signed it or is among the signers. If
   not, say who did in `note` and title it with the sender.
4. **Date** — from the letter's own text: letterhead or dateline. Read through
   OCR damage ("March 3I, 2009" is 2009-03-31). If none:
   content that pins it (a dated event, "the 111th Congress", a fiscal year;
   name it in `date_source`); then the file name if it carries a date
   (`date_source: "file name: <name>"`), never later than the capture
   (capture is YYYYMMDDhhmmss); a funding request naming fiscal year N →
   year N−1, precision `year`, date N−1-06-30. If nothing works, `date: ""`
   and `note` says "date approximate". **Never invent a date.** The date must
   not be after the first posting's capture.
5. **Title** "On Subject — to whom, D Month YYYY", subject in title case. The
   "to whom" names an official as addressed ("to Secretary Hagel", "to
   Governor Brown", "to Chairman Moran"), even though the recipient term is
   the office; a company letter names the company, never a CEO ("to
   Equifax"). Example:
   "On Funding the Sea Grant Program — to Chairman Moran and Ranking Member
   Shaheen, 11 April 2018". No date known: end at the recipient.
6. **Subjects: at least 4, of which at least 2 are `topics`; no upper limit**
   (Robin, 17 November 2026;
   `qa/QA-analysis-subject-analysis.md`). Two kinds:
   - `topics`: what the letter is **primarily about**, only exact lines of
     `subjects.txt`. Keep to its main matters. If nothing fits, use the
     nearest and say so in `note`; do not invent one.
   - `names`: every organization, company, nonprofit, committee, agency or
     office the letter names as a party or subject, and laws or bills that are
     vocabulary terms, as exact labels from `terms.csv` (kind organization or
     office, status preferred) or `reviews.csv`. A person is never a name: a
     CEO or staff member goes under the organization, an official under the
     office. A name not in the vocabulary goes in `new_term` (a list is
     allowed) and in `names`.
   - A recipient outside Congress is a name: list it in `names` too (it counts
     toward the 4). A member, committee or caucus recipient does not count.
     Names never count toward the 2 topics.
     Short of 4, or of 2 topics, after a second look: say why in `note`.

Be accurate rather than fast. Do not fetch anything from the web. Write the
output file, then reply with only: the count of each status and any letters
you were unsure about, one line each.
