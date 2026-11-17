# QA-analysis-authorship (step 2, REQUIRED)

Part of [QA-Analysis-methodology](QA-Analysis-methodology.md). Establish who
wrote the letter, and file it under its congressional authors.

1. **Read the signers** in the signature block, then the letterhead. A
   printed name is enough; a signature stands in for a missing name. The
   reader sees the end of every long letter, where signers usually are.
2. **The posting member** is the member whose site posted the file. Check that
   they signed or are among the signers.
   - **Among the signers, or the letterhead is theirs and the signers are
     illegible or cut**: the posting member is an author. Note "signers could
     not be checked" when so.
   - **Not among the signers**: title the letter with its real senders and say
     so in the note. Example: Bobby Scott's Dear Colleague endorsing Barbara
     Lee, posted by Lee.
3. **Several members signed**: every legible member signer is an author. A
   letter on a committee's or caucus's behalf files under the committee or
   caucus too, with its members listed when the letter lists them.
4. **Not by a member** (an agency reply, an organization, a constituent): the
   author is the sender, named in the title ("— Secretary Chao to Senator
   Rounds"); the letter is kept only through letter determination test 2.
5. **Check that each author held office on the letter's date.** Required
   for every letter. Compare the date (step 5) with the author's service:
   - **In Congress?** The member's term at the posting address
     (`data/address-holders.csv`) and their congressional career
     (congress-legislators terms, in `address_holders.career_terms()`).
   - **In the post the letter claims?** A letter signed as a committee's
     chair or ranking member, or as a leader, must fall within that service:
     `data/committee-chairs.csv` (#364; see `build/chairs/README.md` for its
     limits: some mid-Congress changes are missed) and the leadership terms.

   When the date falls **after the author left Congress, the address or the
   post**, or **before they arrived**, one of four things is true. Find
   which, from the OCR:
   1. **The date is wrong**: a misread year, a file-name or upload date.
      Re-date it (QA-analysis-dates); the holder check at merge refuses a date
      that leaves the posting with no holder.
   2. **Another member wrote it and re-posted it** on an address they took
      over. The build credits a later holder's letter to them when the file
      was first captured in their span, they were in Congress on its date, and
      its OCR names them and not the earlier holder, or names neither and the
      earlier holder had already left before the capture
      (`address_holders.later_holder` / `reposted_by`, #1249: Stephanie
      Murphy's letters on `murphy.house.gov` had been credited to Tim Murphy,
      who had resigned). The 12 November 2026 rule does the same when the date
      falls between two holders (Mike Levin at `levin.house.gov`).
   3. **The member's own letter from an earlier office**, re-posted on a
      later site (a House letter on a senator's site): credited to them,
      flagged `earlier_office`.

   4. **An older letter, posted later**: another member's letter, a
      caucus's earlier letters carried from chair to chair, or an agency's or
      company's letter, posted by a member who did not yet hold the address
      on its date (Carter's copy of the 2014 Royce–McCaul–Duncan letter;
      Bonior's of Waxman's 1998 letters). **Record its true date** (Robin,
      17 November 2026, #239, #1284). The build places the posting by the
      file's first capture, under whoever held the address then, flagged
      `posted_later` (`address_holders.place`), and the explorer says
      "Posted later". Title it with its real senders (step 2).

   If none fits, title the letter with its real author, say why in the note,
   and file an issue (label `harvest` for a posting, `dates` for a date).
6. **Names in the record.** Authors are members' vocabulary terms (by
   Bioguide ID). A signer who is not a member (a staff director, a CEO) is not
   an author term; their organization is a subject (step 4).
7. **Consult** [QA-analysis-subject-analysis](QA-analysis-subject-analysis.md)
   for organization names, and [DEDUPLICATION.md](../DEDUPLICATION.md) when the
   same letter is on several members' sites (a shared, multi-author letter).
