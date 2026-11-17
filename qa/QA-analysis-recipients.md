# QA-analysis-recipients (step 3, REQUIRED)

Part of [QA-Analysis-methodology](QA-Analysis-methodology.md). Read the
address block, then the salutation, then the body. Write **one**
`letter-recipients.csv` row. Robin's recipient policy (15–17 November 2026;
#352, #357, #498, #502).

| What you find | Recipient |
| --- | --- |
| A member, or several | the member's term; several: a `joint` row of Bioguide IDs |
| A committee, or its chair and ranking member | the committee (subcommittees: the full committee) |
| The congressional leaders together | "Congressional leadership" |
| A federal, state, local or foreign official | the **office**, never the person: "to Secretary Austin" → Department of Defense; Governor of Ohio; Mayor of Denver |
| Several offices | a `joint` row of their labels |
| A company, organization or nonprofit, or its CEO or staff | the organization, never the person; several: the first as recipient, the others as name subjects (step 4) |
| "Dear Colleague" to one chamber | United States Senate / United States House of Representatives |
| No addressee, written by the member (open letter, notice) | `(no recipient)` |
| No addressee, plainly directed at the posting member by others (a support letter for their bill) | the posting member, "As recipient, from Sen. X's website" |
| A private person (including a former official writing after leaving office) | `(no recipient)`; the name stays in the title |

- The recipient term must exist. The Mac adds a missing one (kind
  `organization` or `office`, a `broader` node in the house form: "Florida
  Attorney General", "Governor of X", "Embassy of X", "U.S. Embassy in X",
  "Mayor of X", "X state government agencies", "X local government and
  agencies"); the PC holds the letter and lists the name on the batch's "names needed"
  issue.
- A label never ends in a parenthetical ("Mayor of Chicago", not "Mayor of
  Chicago (Illinois)"): the matcher strips it.
- An official's name is kept searchable as an `officeholder` row on the office,
  and in the title.
