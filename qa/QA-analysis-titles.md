# QA-analysis-titles (step 6, REQUIRED)

Part of [QA-Analysis-methodology](QA-Analysis-methodology.md). The
standardized title is the **Letter Name Fix** of the QA status CSVs; the
original is the file's own name.

## The form

**"On Subject — to whom, D Month YYYY"**, the subject in title case.

- **To whom**: as the letter addresses them. An official by title and name
  ("to Secretary Hagel", "to Governor Brown", "to Chairman Moran and Ranking
  Member Shaheen"), even though the recipient term is the office. A company by
  its name ("to Equifax"), never a CEO's name.
- **Sent by someone other than the posting member**: name the sender:
  "On … — Secretary Chao to Senator Rounds, 3 May 2018"; "— the Fraternal
  Order of Police to Senators Markey and Brown".
- **No date**: end at the recipient.
- **A discard**: a few words saying what it is ("Senate resolution text
  objecting to UN Security Council Resolution 2334").

## Drafts

An unfinished draft (QA-analysis-letter-determination, "Drafts") is titled in
the usual form with "— a draft" at the end: "On the True Cost of a Title
Loan — to Director Chopra, March 2023 — a draft". A letter whose day alone
was left blank is not a draft and takes no marker.

## Checks

- Every word of substance in the title appears in the letter's own text
  (stems, not exact words). The writer refuses a title that does not match
  (the title guard), because a mismatch means the reading belongs to another
  letter. A true match the guard cannot see (words in the middle of a long
  text, OCR without word spaces) is confirmed from the full OCR and marked
  `"title_checked": true`.
- Titles in the older form ("Subject — …") are converted at build time, but
  new titles use this form.
