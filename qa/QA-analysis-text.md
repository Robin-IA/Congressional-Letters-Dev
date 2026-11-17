# QA-analysis-text (step 0, REQUIRED)

Part of [QA-Analysis-methodology](QA-Analysis-methodology.md). Before any
judgment about a letter, make sure you are reading the whole of it.

1. **Get the text** from `letters-from-congress-OCR/text/<N>th.jsonl.gz`
   (`source`: `text-layer` or `ocr`). A reader sees the first 4,500 and last
   1,500 characters of a long letter, so the signers are not lost; open the
   full record when a decision depends on the middle.
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
