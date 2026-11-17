# QA-analysis-recipients (step 3)

Part of [QA-Analysis-methodology](QA-Analysis-methodology.md).

**A recipient is not a separate requirement of the analysis** (Robin,
17 November 2026). It does two jobs:

1. **Letter determination** (step 1): an addressee is part of what makes a
   letter (test 1), and a letter *to* a member or congressional group belongs
   to Congress (test 2).
2. **A name**: every other recipient is a name subject (step 4), filed under
   its organization, company, nonprofit, government agency or government
   office, like any other name the letter carries.

**The exception is Congress.** A letter to members of Congress, or to a
congressional committee or caucus, is listed under the recipient's name,
marked **"As recipient"** (#352), in addition to its authors.

Read the address block, then the salutation, then the body. A letter is never
held for want of a recipient.

## Congress: "As recipient"

| What you find | Record |
| --- | --- |
| A member, or several, named | each member, "As recipient" (several: a `joint` row of Bioguide IDs) |
| A committee's or caucus's members named (a chair and ranking member) | those members, "As recipient"; the committee is also a name (step 4) |
| A committee or caucus, no member named ("To the Committee on Finance") | the committee or caucus, "As recipient" (Robin, 17 November 2026) |
| No addressee, plainly directed at the posting member by others (a support letter for their bill) | the posting member, "As recipient, from Sen. X's website" |
| "Dear Colleague" to one chamber | United States Senate / United States House of Representatives |

## Everyone else: a name

| What you find | Record |
| --- | --- |
| A federal, state, local or foreign official | the **office**, never the person: "to Secretary Austin" → Department of Defense; Governor of Ohio; Mayor of Denver |
| A company, organization or nonprofit, or its CEO or staff | the organization, never the person |
| Several of these | each one |
| No addressee, written by the member (open letter, notice) | none: `(no recipient)` |
| A private person (including a former official writing after leaving office) | none: `(no recipient)`; the name stays in the title |

Each of these is **listed among the letter's names** in `letter-topics.csv`
and counts toward the 4 subjects (step 4). One `letter-recipients.csv` row
still records the first one (or a `joint` row of several offices), because
the explorer shows a government office as the letter's "to" line.

## Terms

- The term must exist. The Mac adds a missing one (kind `organization` or
  `office`, a `broader` node in the house form: "Florida Attorney General",
  "Governor of X", "Embassy of X", "U.S. Embassy in X", "Mayor of X",
  "X state government agencies", "X local government and agencies"); the PC
  holds the letter and lists the name in the **Names** section of the batch's
  "vocabulary needed" issue, as for any other name.
- A label never ends in a parenthetical ("Mayor of Chicago", not "Mayor of
  Chicago (Illinois)"): the matcher strips it.
- An official's name is kept searchable as an `officeholder` row on the office,
  and in the title.
