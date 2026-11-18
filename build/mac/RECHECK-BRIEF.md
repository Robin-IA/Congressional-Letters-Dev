# Re-check brief: subjects for filed letters (#1266)

You re-check letters that are already filed but fall short of the subject
rule (read `qa/QA-analysis-subject-analysis.md` first): **at least 4
subjects, at least 2 of them topics.**

- **Topics**: exact lines of `~/explorer-checks/mac-read/subjects.txt`, for
  what the letter is primarily about. Never bend a letter onto a topic that
  does not fit.
- **Names** count as subjects: every organization, company, nonprofit,
  committee, agency or office the letter names as a party or subject, by
  exact label: a `preferred` row of `vocabulary/terms.csv` whose kind is
  organization or office, or an accepted candidate of `vocabulary/reviews.csv`.
  A state or category node ("State of Nevada") is not a name. A missing
  organization or office goes in `new_term` {label, kind:
  "organization"|"office", broader: an existing `term` of
  `vocabulary/hierarchy.csv`}; no parenthetical at the end of a label.
- **People are never names**: a CEO or official files under their
  organization or office. A member of Congress is never a name.
- **An organization that sent the letter** (a company, county, association
  or agency writing to Congress) **is a name**: it is a party to the letter.
  "Authors do not count" means members, who are authors, not subjects.
- **Laws and bills** are topics: a named law the letter is about (181 were
  added on 17 November 2026, #1324) is an exact line of `subjects.txt` like
  any other topic. A law it only cites in passing is not a subject. A law the
  list lacks goes in `new_term` as {label, kind: "law", broader: its parent
  topic from `subjects.txt`}; it is collected for the Mac to add, not filed
  yet, so do not count it toward the rule. Bills cited only by number are left
  out (say so in `note`).

Each input item has `title`, `subjects_now` (`;`-separated), `recipient_now`
and `text` (head and tail of a long letter). Keep the existing subjects that
are right; drop any that are not what the letter is about; add until the
rule is met. Read enough of the text to find the names it carries, not only
the opening. If a letter truly cannot reach 4, say why in `note`.

Also give `direction`: "from" (a member or congressional group wrote it),
"to" (written to Congress by others), or "neither" (no member at either end).

Write exactly one JSON line per letter to your output file:
`{"digest", "topics": [FULL list], "names": [FULL list, including any new_term
labels], "new_term": null | {..} | [..], "direction", "note"}`.

Read only your own input file; write no other output file; keep helper
scripts in `/tmp/reader-<your part>/`. Report counts and anything uncertain,
briefly.
