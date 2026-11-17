# QA-analysis-dates (step 5, REQUIRED)

Part of [QA-Analysis-methodology](QA-Analysis-methodology.md). The dating
order (#172, #488, #506, #652; Robin, 15–17 November 2026), with the tiers
in [METHODOLOGY.md](../METHODOLOGY.md) "Dating".

## The order: stop at the first that works

1. **The letter's own text**: letterhead or dateline. Read through OCR damage
   ("March 3I, 2023" is 31 March 2023). Check the year against the content:
   a dateline that predates what the letter cites is a typo (a 2018 dateline
   on a letter about COVID-19 is 2020; Zinke "Secretary" in January 2017 is
   2018). Say so in `date_source`.
2. **OCR first, if there is no dateline**: a missing date is often the OCR's
   fault. Re-read or re-OCR (QA-analysis-text) before going on.
3. **The content**, when it pins the date: a dated event, an official in
   office, a fiscal year, "the 116th Congress", a letter it replies to. Name
   the evidence.
4. **The file name**, when it carries a date, at the precision it gives,
   never later than the first capture. `date_source`: "file name: <name>".
5. **A received stamp** gives a date no earlier than the letter; mark it
   approximate.
6. **A funding request naming fiscal year N**: year N−1, precision `year`.
7. **Nothing works**: file it anyway, with no date row; the note says
   "date approximate" (#488). **Never hold a letter for its date.**

## How dates are stored

- A full ISO date with a precision: `day`; `month` as YYYY-MM-01; `year` as
  YYYY-06-30 (or the first capture that year).
- Never later than the file's first capture (#652).
- The date must leave the posting with a member who held the address then
  (the holder check at merge). Since 17 November 2026 the true date is still recorded: when a date finds no holder because an
  older letter was posted later (another member's letter, a caucus's earlier
  letters, an agency letter a member re-posted), the build places the posting
  by its first capture, flagged `posted_later` (Robin, 17 November 2026,
  #239, #1284; QA-analysis-authorship step 5, case 4). A date that is simply
  wrong (a misread year) is corrected from the content, never forced.
- Write a `letter-dates.csv` row only when the date differs from the published
  one.
