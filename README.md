# PC render PDFs 2: the source PDFs from the second run

`pc-render-pdfs-2.zip` holds the source PDFs the PC downloaded from the Wayback
Machine during the second render run. Their thumbnails, OCR, text and dates are
on `pc-render-return-2`. The first run's 172 PDFs are on `pc-render-pdfs`.

**Built 12 November 2026, 10:35 local. Partial — the run is still going.**

| | |
| --- | --- |
| PDFs | **154** of 7,662 (2.0%) |
| Zipped | 65.8 MB |
| Average | 456 KB each |

Every file is named for its CDX digest and matches a thumbnail of the same name
on `pc-render-return-2`. All were checked to begin with `%PDF`.

## These do not need to come back

`run_render.py` marks the PDFs as staying on the PC, and Robin confirmed they
need not travel for OCR's sake, because `ocr_tesseract.py` reads them here. They
are pushed anyway because a branch is less trouble than a USB stick and the
volume is manageable — but nothing on the Mac is waiting for them.

**At full size this stops being true.** 7,662 PDFs at 456 KB is about 3.5 GB,
which is roughly 40 parts under GitHub's 100 MB file limit. If the whole run
lands here, that is worth a deliberate decision rather than a default.

## Batching

Pushed as one zip at 154 files. Going forward the plan is batches of 500 PDFs,
each split into 3 parts under 90 MB, since 500 at 456 KB is about 234 MB and
GitHub refuses any single file over 100 MB.

Pushed with git, not the contents API: the REST blob endpoint refuses anything
much over 50 MB, answering HTTP 422. Built in a fresh local repository rather
than a clone of this 1.3 GB one. `core.autocrlf` is set system-wide on that PC,
so this repo disables it and carries `* -text` — a line-ending rewrite would
corrupt a zip silently.
