# Letters waiting on the vocabulary

Letters read in full whose decided topics include a subject not yet in `SUBJECTS`
(`build/topics.py`). The reading is done; they wait on the vocabulary, not on
review, so the picker skips them.

`letters.csv` holds one row per letter: the decided title, letterhead date,
topics (including the proposed subject), the proposed subject(s), and a note.
The running list of proposed subjects, with recommendations, is issue #221.

When a subject is accepted and added to `SUBJECTS`, apply that letter's row to
`vocabulary/letter-titles.csv`, `letter-dates.csv`, `letter-topics.csv` and
`letters-reviewed.csv`, then delete its row here.
