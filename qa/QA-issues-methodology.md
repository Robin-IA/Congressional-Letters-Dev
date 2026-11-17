# What counts as an issue (subject)

Part of [QA-Analysis-methodology](QA-Analysis-methodology.md). Answers #81,
decided by Robin on 17 November 2026. An **issue** is a subject that letters
are grouped under and followed across members and Congresses. In this
project an issue is a **subject** of the controlled vocabulary: a topic from
the subject list or a name (an organization, office, law or bill).

## The rules

| Question | Answer |
| --- | --- |
| **Threshold.** When does a subject become an issue? | **One letter is enough.** A subject exists as soon as one letter needs it; there is no minimum count of letters, members or Congresses (Robin). |
| **Subjects per letter** | **At least 4, at least 2 of them topics, no upper limit** ([QA-analysis-subject-analysis](QA-analysis-subject-analysis.md)). |
| **Members** | **Every member of Congress in the letter is represented** (Robin): each member who signed it is an author, and each member it is addressed to is listed "As recipient", each under their own term by Bioguide ID ([QA-analysis-authorship](QA-analysis-authorship.md), [QA-analysis-recipients](QA-analysis-recipients.md)). A name read from a page is checked against the roster first (#120). |
| **Scope.** A broad area or a specific matter? | Both, at two levels. Topics are grouped in a hierarchy ("U.S. territories" › Puerto Rico; topic groups such as Health). Specific matters are names: a law, a bill, an agency, a company. |
| **Sources** | The project's own vocabulary (`vocabulary/terms.csv`, `build/topics.py`). Every term names a source, and terms are reconciled to FAST, LCSH and Wikidata where a match exists. |
| **Evidence.** What places a letter under a subject? | The letter's own text, read in full: never the file name ([QA-analysis-text](QA-analysis-text.md), step 4 of the analysis). A subject is what the letter is primarily about, or a party or law it names; a passing mention is not a topic. |
| **Boundaries.** Overlaps, splits and merges | A letter carries every subject it is about. A subject that is asked for under several names is merged by a `reviews.csv` row; a new subject is placed in the hierarchy when it is added. |
| **Review.** Who confirms, and where it is recorded | The contributor (the PC) proposes missing subjects and names on the batch's "vocabulary needed" issue; the maintainer (the Mac) adds them to `build/topics.py` or `reviews.csv` and `hierarchy.csv`, and files the letters. |
| **Reporting.** What a page may say | A count of letters on a subject says how many letters were found, **never how much a member cared**: what a member posted, and what the Wayback Machine kept, shape it. Every number on a page links to the letters behind it. Only letters a member wrote count as theirs (#175). |

## Worked examples, three Congresses

**107th: a Government Reform minority letter on Karl Rove's stock holdings**
(`ARIF5YQUOAFW`, posted by Waxman, to the White House Counsel, 25 June 2001).
Subjects: Ethics, Oversight, Energy (topics); Intel, Enron, Pfizer, Johnson &
Johnson (names), with the White House Counsel as recipient. Seven subjects,
three topics. Each company is a subject because the letter names it as a
party, not because it is in the file name.

**115th: the Dolores County commissioners to Congress on the West Fork Fire
Station Act** (`LROT2JYNNZCK`, posted by Bennet). Subjects: Firefighters,
Public lands (topics); Forest Service, Dolores County Board of County
Commissioners, Dolores Fire Protection District (names), to the Senate and the
House. A letter **to** Congress: direction `to`, listed under Bennet's
"Letters received" and not counted as written by him.

**119th: support letters for the Lowndes County Sheriff's Department's
Community Project Funding request** (`WM6MXK5GWQ2N`, a bundle of five letters
to Representative Kelly). Subjects: Policing, Appropriations, Technology,
School safety (topics); the Lowndes County Board of Supervisors, the Sheriff's
Department, the Mississippi State Senate, the school district, Golden Triangle
Development LINK and Steel Dynamics (names). One record for the whole bundle
(#1226), with Kelly "As recipient".

## Features that rely on this

- The subject browse and the topics page in each explorer, and the hub.
- Members' positions on an issue (#43) and tracing an issue from letter to
  response to legislation (#46), both still open: they will use these
  subjects, and the reporting rule above applies to them.
