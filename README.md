# PC render PDFs 2: the source PDFs from the second run

`pc-render-pdfs-2.zip` holds the source PDFs the PC downloaded from the Wayback
Machine during the second render run. Their thumbnails, OCR, text and dates are
on `pc-render-return-2`. The first run's 172 PDFs are on `pc-render-pdfs`.

**Partial — the run is still going. Batch 1 built 10:35, batch 2 at 11:00.**

| | |
| --- | --- |
| `pc-render-pdfs-2.zip` | **154** PDFs, 65.8 MB |
| `pc-render-pdfs-3.zip` | **123** PDFs, 66.6 MB |
| Total so far | **277** of 7,662 (3.6%) |

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

One zip per batch, sized by bytes rather than file count: each holds up to
85 MB of PDFs, which is 120-190 files depending on how big they run. Sizing by
count would not be safe -- PDFs have averaged anywhere from 350 KB to 747 KB
across stretches of this run, so 190 files can be 87 MB or 142 MB, and GitHub
refuses any single file over 100 MB.

Pushed with git, not the contents API: the REST blob endpoint refuses anything
much over 50 MB, answering HTTP 422. Built in a fresh local repository rather
than a clone of this 1.3 GB one. `core.autocrlf` is set system-wide on that PC,
so this repo disables it and carries `* -text` — a line-ending rewrite would
corrupt a zip silently.
