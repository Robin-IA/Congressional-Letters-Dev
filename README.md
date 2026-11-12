# PC render return: a partial, and the job handed back

`pc-render-return.zip` holds what the Windows PC rendered from
`pc-render-106-114-paths.zip` before the work was handed back to the Mac.

**Built 12 November 2026, 01:25 local. This is a small partial — 172 of 7,920
PDFs, 2.2%.** The rest was not attempted. **The Mac should render the remainder;
the PC is not continuing.**

| | |
| --- | --- |
| Distinct PDFs in the bundle | 7,920 |
| **Rendered here** | **172 (2.2%)** |
| Letter records covered | 197 of 11,043 |
| Failures recorded | 7 |
| Zip | 3.2 MB, 175 entries |

## What is in it

```
thumbs/<digest>.webp     172 files, 3.3 MB, averaging 18.0 KB
pdf-dates.jsonl          155 lines
letter-text.jsonl        172 lines, 0.21 MB
thumb-failures.jsonl       7 lines
```

**No PDFs.** `pdfs/` stayed on the PC as instructed — 172 files, 47.7 MB — and
will come over by USB or Drive if they are wanted. The zip was checked to
contain no `.pdf` entries before pushing.

The three returned files are exactly the ones `run_render.py` marks as going
back to the Mac. Merging should skip any digest the Mac has already rendered;
nothing here is newer than the Mac's own work, it is simply a different 2.2%.

## Why it stopped

Measured over the first five minutes, then extrapolated:

| | |
| --- | --- |
| Rate | 20 PDFs/min → **~6.6 hours** for 7,920 |
| **Download volume** | 465 KB per PDF → **~3.7 GB** |

3.7 GB over a phone hotspot, against the roughly 5 MB the whole night's CDX
harvesting used. The hotspot existed to give the harvest a second IP, because
Wayback refuses *index queries* from a busy address. These are ordinary file
downloads and gain nothing from a second IP, so the cellular link was pure cost.

The 18.0 KB average thumbnail matches the 18.8 KB figure in `BACKFILL.md` §6,
so the Pages-budget arithmetic there still holds.

## Still open

`BACKFILL.md` §6 puts the published site at 874.9 MB of Pages' 1,024 MB —
roughly 8,000 previews of headroom. The two harvests returned tonight exported
**28,531 letters** between them (`pc-cache-115-118`, `pc-cache-106-110`), and
this render bundle alone wants 7,920 previews. Where the thumbnails live is
issue #2 step 6, and it is now the binding constraint rather than a tidiness
question.
