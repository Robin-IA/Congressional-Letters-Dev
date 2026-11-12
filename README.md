# PC render return: the PDFs

`pc-render-pdfs.zip` holds the 172 source PDFs the Windows PC downloaded from
the Wayback Machine while rendering thumbnails on the night of 11–12 November
2026. Their thumbnails, dates and first-page text are on `pc-render-return`;
this is the other half of that return.

**Built 12 November 2026, 01:45 local.**

| | |
| --- | --- |
| PDFs | **172** |
| Raw size | 83.1 MB |
| Zipped | **72.8 MB** |
| Average | 465 KB each |

Each file is named for its CDX digest, matching the thumbnail of the same name
on `pc-render-return` — all 172 digests line up across the two branches. Every
file was checked to begin with `%PDF` before packaging.

These are 172 of the 7,920 PDFs in `pc-render-106-114-paths.zip`, which is 2.2%.
The remaining 7,748 are the Mac's to fetch: at the rate measured here, 20 PDFs a
minute and 465 KB each, the whole bundle is about 6.6 hours and 3.7 GB, which is
why the job moved off the PC's cellular hotspot.

## Why this is on GitHub at all

`run_render.py` keeps the PDF beside each thumbnail and marks it as staying on
the PC, with transfer by USB or Drive. That guidance assumes the PDFs are bulky.
At 172 files they are not, and a branch is less trouble than a stick. If a later
run renders the full 7,920, the PDFs would be roughly 3.4 GB and the advice
would be right again — this branch is not a precedent for that case.

## It was pushed with git, not the API

The contents API refuses a blob this size: a 72.8 MB zip is 101.8 MB once
base64-encoded, and the REST endpoint answers HTTP 422 with "your input was too
large to process. Consider creating the blob in a local clone." The other four
branches from this night were all built through the API, which works up to
roughly 50 MB of file.

This branch was pushed from a fresh local repository rather than a clone of this
one, which is 1.3 GB. `core.autocrlf` is set system-wide on that PC, so the
local repo disabled it and carries `* -text`, since a line-ending rewrite would
corrupt a zip silently.
