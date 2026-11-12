# OCR test: Apple Vision on the kept PDFs (12 November 2026)

Run 12 November 2026, 01:33–01:45, on the Mac, while the renderer worked.
Nothing here was written into the letter data. The OCR output itself is
not committed: it is the full text of 80 letters, some written *to* members
by outside organisations, and this repository is public.

## What was tested

- **Engine:** Apple's Vision framework (`VNRecognizeTextRequest`, accurate
  level, language correction on, en-US), through `build/ocr.swift`, compiled
  with `swiftc -O build/ocr.swift -o ocr`. It takes image paths and prints one
  JSON line per image. On-device; no service, nothing
  installed.
- **Input:** page 1 of each PDF, rendered at 300 dpi with pypdfium2.
- **Sample:** from the 2,647 PDFs kept in `data/pdfs/` at the time, chosen at
  random (seed 7; digests in `harvest/ocr-test-sample.json`):
  - 40 **controls** with a text layer of at least 800 characters, so OCR can be
    scored against the PDF's own text;
  - 40 **scans** with no text layer at all.

## Results

**Controls: 39 scored** (one had under 50 words on page 1).

| Word recall against the text layer | |
| --- | --- |
| Median | 96.1% |
| Mean | 91.0% |
| Pages under 90% | 7 of 39 |

Word recall is the share of the text layer's words OCR found, in order
(difflib over lowercased words). Precision: median 93.8%, mean 86.4%.

**The two worst scores are the text layer's fault, not OCR's.** One stores
the page's text reversed (`N O I T A N I M ON ...` for "NOMINATION"); the
other stores it in a broken font encoding (`aÉ~ê=oÉéêÉëÉåí~íáîÉ`). OCR read
both pages correctly. So a text layer is not proof of good text: some letters
that "have text" have unusable text, and OCR would fix them.

**Scans: 40.** Every page gave text: median 410 words a page, none under 20,
mean confidence 1.00 (Vision's own figure, which is not a measurement).
Checked by eye against two pages:

- A Kay Granger letter, 2015: letterhead, date and all addressee blocks
  exact.
- A 2004 Immigration Reform Caucus letter: the body exact, word for word. The
  only errors are in the blackletter "Congress of the United States"
  masthead: "Clashington, 29€" for "Washington, DC", and elsewhere
  "Representatibes".

**Speed:** 80 pages in 43 seconds, about half a second a page, alongside the
running renderer.

## What it suggests

- **Vision is good enough to use.** Typewritten and laser-printed letters read
  near-perfectly; the errors are in decorative mastheads, which search does
  not need.
- **More letters need it than thought.** 2,037 of the 2,647 kept PDFs (77%)
  have no text layer. The earlier 47–65% with text was measured on the 119th
  corpus; these are mostly older and departed members' letters.
- **Some text layers should be replaced.** Reversed or mis-encoded layers read
  as nonsense. A cheap check — the share of real dictionary words in the
  layer — would find them.
- **Cost:** about half a second a page. Page 1 of every scan in the corpus is
  a few hours; every page of every scan perhaps a day. Only PDFs on disk can
  be read, so it follows the renderer.

## Not yet decided

EXPLORERS.md step 5 leaves the engine open; this is the evidence for Vision.

- Whether to OCR every page or the first few (the text layer keeps six).
- How OCR text is stored: `source: ocr` beside `source: pdf` in
  `data/letter-text.jsonl`, as EXPLORERS.md step 5 proposes.
- The full-text index format, which this feeds.
