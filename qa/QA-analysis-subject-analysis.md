# QA-analysis-subject-analysis (step 4, REQUIRED)

Part of [QA-Analysis-methodology](QA-Analysis-methodology.md). Robin,
17 November 2026: **at least 4 subjects per letter, of which at least 2 are
topics** (subjects from the subject list, in addition to names); **no upper
limit**, because names count as subjects. The old limit of 8 is removed.

## What counts as a subject

Two kinds, both recorded in `letter-topics.csv` (`;`-separated):

1. **Topics**: what the letter is **primarily about**, from the subject list
   (`build/topics.py` `SUBJECTS`). Keep to the letter's main matters; a passing
   mention is not a topic.
2. **Names**: every **organization, company, nonprofit, committee, agency or
   office** the letter names as a party or subject, and **laws and bills** it
   names (the Affordable Care Act, the Jones Act, H.R. 2201). A person is never
   a name subject: a CEO or staff member is filed under their organization;
   an official under the office.

The recipient (step 3) counts toward the 4 when it is an organization or
office. Authors do not.

## Steps

1. List the letter's main matters; choose a topic for each from the subject
   list. Do not bend a letter onto a subject that does not fit.
2. List the organizations, companies, nonprofits, committees, agencies,
   offices, and laws and bills it names. Consult
   [QA-analysis-authorship](QA-analysis-authorship.md) and
   [QA-analysis-recipients](QA-analysis-recipients.md) for which names are
   authors and recipients.
3. **Count.** At least 4 in all, and at least 2 of them topics. Short of
   either: read again for the matters and names you passed over. A letter
   that truly falls short (a one-line acknowledgment) says so in its note and
   is marked **Needs Review**.
4. **Check every label** against the vocabulary (`terms.csv` preferred rows,
   `reviews.csv` accepted rows, the subject list).
5. **Missing term or subject**:
   - **Mac**: add it. A topic goes in `build/topics.py` with its place in the
     hierarchy; a name goes in `reviews.csv` (merge, kind, broader) and
     `hierarchy.csv`. File the letter in the same PR.
   - **PC**: hold the letter (`letters-vocabulary-needs/letters.csv`). Missing
     names go in one issue per batch ("Reading batch N: names needed"); a
     missing topic subject gets its own issue ("New subject needed:
     <subject>"). Label `vocabulary`.
   - Subjects asked for repeatedly are proposed together (Puerto Rico, North
     Korea, NATO and others, #1250).

## Re-check of letters already filed

Most letters filed before 17 November 2026 fall short of these rules
(#1266 has the counts). They are re-read under these rules on **#1266**.
