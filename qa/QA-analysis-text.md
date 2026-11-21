# QA-analysis-text (step 0, REQUIRED)

Part of [QA-Analysis-methodology](QA-Analysis-methodology.md). Before any
judgment about a letter, make sure you are reading the whole of it.

1. **Get the text** from `letters-from-congress-OCR/text/<N>th.jsonl.gz`
   (`source`: `text-layer` or `ocr`). How much a reader is given:
   - **The PC, from batch 68** (Robin, 20 November 2026; a trial,
     `build/reading_view.py`, given by `build/pc/batch_texts.py`):
     - a letter of **1 or 2 pages is read whole**;
     - a letter of **3 or more pages is read to 75% of its characters**: the
       **first and last pages whole**, because they carry the letterhead,
       date, address block and signers, then the middle pages in order from
       page 2 until the 75% is used. If the first and last pages alone pass
       75%, both are still read whole.
     - A page is an OCR page break. A text layer has none, so every 2,500
       characters counts as a page (an OCR page's median is about 2,400).
     - Why: the PC's batches stopped on usage limits. Bigger batches (3,000)
       read the instructions once; the cap reads less of each long letter.
       On the first 3,000 letters of the 109th–114th, 996 were over 2 pages
       and the batch reads 87% of its characters.
     - If it proves not enough, Robin raises the share.
   - **The Mac's readers** (`build/mac/mac_read.py`, `recheck_subjects.py`)
     still see the first 4,500 and last 1,500 characters of a letter over
     6,000, so the signers are not lost.
   - Either way, **open the full record when a decision depends on the part
     left out**, and say so in the note ("read in full: <why>").
2. **Is it readable?**
   - Garbled text (foreign-script noise, no word spaces, fragments) or a scan
     upside down: fetch the PDF once from the Wayback Machine (one worker,
     the project User-Agent), rotate if needed, and OCR it (Apple Vision,
     `build/ocr`). Store the result in `data/letter-ocr.jsonl`. Example:
     Cassidy's `B766OFXY` was upside down; rotated, it read cleanly (Mac
     batch 8).
   - If it still cannot be read: file an issue (`OCR`, #122 or #559). **No
     text is never a reason to discard.**
3. **Is it the whole letter?**
   - Only part (a signature page, a middle page, a letter starting mid-text):
     note it on **#252** and leave it unfiled until the full PDF is read.
   - Complete except the signature block (OCR stops at "Sincerely"): it is
     whole; file it, noting that the signers could not be checked.
4. **Is it one letter?** A file holding several letters (a packet of support
   letters, a set of replies, letters with a press release, memo, cost
   estimates or petition pages) is a **bundle**. Robin, 17 November 2026
   (#1226): **a bundle is read and filed as one record, describing the whole
   bundle**:
   - **Title** names the bundle: "On Support for H.R. 3144 — NECA and others
     to Speaker Ryan and Representative Newhouse, 12 June 2017", dated by its
     first letter.
   - **Authors and recipients**: the posting member and any member who signed
     or received a letter in it, as for any letter (QA-analysis-authorship,
     QA-analysis-recipients).
   - **Names**: every sender and recipient organization or office in it, with
     the topics (QA-analysis-subject-analysis).
   - **Note** begins "Bundle:" and lists each letter inside (sender, recipient,
     date) and any non-letter part.
   - **Letter determination** applies to the bundle as a whole: a press
     release, memo, estimate or petition inside does not disqualify it; it is
     discarded only when no letter in it passes test 2.
   A bundle is not split into one record per letter.
5. **Is the digest sound?** A 40-character hex digest is not a Wayback digest;
   such rows are skipped and listed on #1226.
6. **Duplicates.** If the same letter is in another file, follow
   [DEDUPLICATION.md](../DEDUPLICATION.md): one member's repeats are
   duplicates; the same letter on several members' sites is one shared letter.
