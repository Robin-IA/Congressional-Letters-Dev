# Discarded postings

Postings that are **not letters**, and are not to be filed as letters: an
employer reference ("Dear Employer"), a resolution, a newsletter, bill text,
an issue brief, a bank statement or other exhibit. Robin, 16 November 2026:
"This will be the place to put letters that aren't letters."

`letters.csv`, one row per posting:

| Column | |
| --- | --- |
| `digest` | the scan's digest |
| `title` | what the posting is, in a few words |
| `reason` | why it is not a letter |
| `issue` | the issue where it was decided |
| `decided` | who decided, and when |

A digest here is not read again: the reading pick skips it, as it skips the
holds in `letters-vocabulary-needs/letters.csv`. Rows are added, never
reordered.
