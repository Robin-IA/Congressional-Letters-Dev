# For Claude on the PC

> **Overnight, 13 November 2026, 00:30, from the Mac. This comes first.**
>
> - **Job 3 is the Mac's now.** The Mac started rendering
>   `pc-render-all-missing` itself at 00:30. **Before shutting down:** stop
>   `C:\render4`, and if it rendered anything, pack and push one last return
>   to `pc-render-return-3`; the Mac merges it and skips what it already
>   has. **Do not restart Job 3** in the morning.
> - **Job 2 stays the PC's.** Push one last OCR return to
>   `pc-ocr-return-106-115` before shutting down, and in the morning carry on
>   with `C:\ocr` from where it stopped (it resumes; nothing to unzip again).
>   Same rules as before: on the hotspot, and push a return about once an hour.
> - Job 4 stays the Mac's, as below.

> **New jobs as of 12 November 2026, 21:50, from the Mac.** Read this, then the
> rules below, which still apply. Nothing in them is changed here.
>
> - **Job 3 replaces Job 1.** `pc-render-all-missing.zip` holds every PDF
>   letter in the fourteen explorers that still has no preview: **6,860 PDFs**
>   (9,814 letters), including whatever Job 1 did not finish, with the 934
>   failures already recorded so they are not retried. Unzip it into
>   `C:\render4` and run it the way Job 1 ran (`run_render.py`). If Job 1 is
>   still running, push its last return and stop it first, or the two render
>   the same letters.
> - **Job 4 (the 116th–119th scans' OCR) is the Mac's, not the PC's.**
>   Decided 12 November, 22:00: the Mac fetches and OCRs those 7,198 scans
>   itself. **Do not run `pc-ocr-116-119.zip`**; it stays on this branch only
>   as a record. The PC's jobs are Job 2 (the 106th–115th scans) and Job 3.
> - **Size.** At about 465 KB a PDF, Job 3 is about 3.2 GB of downloads. That
>   is past the 3 GB alert and a third of the hotspot's 10 GB, so check with
>   Robin which connection it runs on.
> - **The Mac is downloading again** from 22:00, fetching Job 4's scans on
>   Charter. If Job 3 runs on Charter too, the two share one IP and one
>   Wayback allowance: keep the PC to `--workers 2` there, or run it on the
>   hotspot.
> - **Results come back as before**, packed by `pack_return.py`, on these
>   branches exactly: **Job 3 on `pc-render-return-3`**, Job 2 on
>   `pc-ocr-return-106-115` as before. The Mac's auto-publish job merges only
>   branches it knows by name, and watches both. It publishes what it
>   merges, and every publish rebuilds full-text search, so new OCR becomes
>   searchable on its own.

> **Rules as of 12 November 2026, 11:55. These replace anything older below.**
>
> 1. **Do not push PDFs to GitHub.** Stop pushing to `pc-render-pdfs-2`, and
>    do not start any other PDF branch. The PDFs stay on the PC. Nothing on the
>    Mac uses them: the OCR is done on the PC, and every letter opens from
>    the Wayback Machine.
> 2. **Push what the Mac does need, about once an hour:** the thumbnails and
>    the `.jsonl` files, packed by `pack_return.py`. See "Sending results back,
>    step by step" below. Until those arrive, the Mac has nothing to merge.
> 3. **Job 2 (the scans' OCR, `C:\ocr`) runs only while the PC is on the
>    hotspot** (from 13:40, 12 November). On the hotspot it has its own IP and
>    takes nothing from the Mac, which has paused its own OCR downloads so its
>    rendering has Charter's Wayback allowance to itself. **If the PC moves back
>    to Charter, pause Job 2**: push one last OCR return, then Ctrl-C both
>    `C:\ocr` windows; Job 1 keeps rendering. The 3 GB data alert (rule above
>    and under Job 1) covers both jobs together: the scans are about 465 KB
>    each, so Job 2's 6,400 remaining are about 3 GB on their own.

Written 11 November 2026, 22:15, by the Claude session on the Mac. This is
what a Claude session on the Windows PC needs to know to help run the letter
harvest. Robin is the person you are working with.

## Current jobs: read this first (12 November 2026, 11:45)

Everything below this section is history: how the harvests and the first two
render runs were set up. These are the PC's jobs now. **Run them on the
Charter broadband, not the hotspot**: the hotspot measured as throttled to about
2.5 MB a minute, and on broadband 6 workers did 9.8 PDFs a minute.

The Mac meanwhile renders only the 115th–118th and fetches only the
116th–119th scans, so nothing below overlaps with it.

**Wayback is refusing some connections** from this household's IP today:
dropped connections (`URLError`) come and go. Both tools retry them, so a burst
of failures is not a reason to stop. If more than half of a pass fails for an
hour, lower `WORKERS` and tell Robin.

### Job 1: render the 106th–114th and the path letters (7,260 PDFs)

The same job as `C:\render2`, rebuilt at 11:34 to leave out everything already
rendered, including the PC's own 564.

**If `C:\render2` is still running, keep it running and skip steps 1–2.** It is
the same set of letters and skips what it has done; switching folders gains
nothing. What matters is that its **thumbnails and `.jsonl` files come back**
on `pc-render-return-2` (update that branch), not its PDFs: at 11:47 the PC had
pushed 598 PDFs but the Mac had thumbnails for only 392 of them.

1. Download
   <https://github.com/Robin-IA/Congressional-Letters-Dev/raw/pc-bundle/pc-render-106-114-paths.zip>
   and unzip it into a **new** folder, `C:\render3`. Do not resume `C:\render2`.
2. Copy `ocr_tesseract.py` from `C:\render2` into `C:\render3`. It is unchanged
   for this job.
3. Window 1: `cd C:\render3`, `$env:WORKERS=6`, `py run_render.py`.
4. Window 2: `cd C:\render3`, `py ocr_tesseract.py --watch`.

### Job 2: OCR the 106th–115th scans that have no text (7,025 PDFs)

These letters already have thumbnails, but they were rendered before PDFs were
kept, so their scans were never OCRed. Each is downloaded again from the exact
capture the thumbnail came from, checked against the sha256 recorded then, and
read with Tesseract. Nothing is rendered.

1. Download
   <https://github.com/Robin-IA/Congressional-Letters-Dev/raw/pc-bundle/pc-ocr-106-115.zip>
   and unzip it into its own folder, `C:\ocr`. It holds `fetch_for_ocr.py`, a new
   `ocr_tesseract.py` (it also stops when the fetch is done), `fetch-list.jsonl`
   and a small `letter-text.jsonl`.
2. Window 3: `cd C:\ocr`, `$env:WORKERS=4`, `py fetch_for_ocr.py`. Standard
   library only; nothing to install.
3. Window 4: `cd C:\ocr`, `py ocr_tesseract.py --watch`.

`fetch_for_ocr.py` works in passes and retries failures on the next pass, after
5 minutes. A 404, a non-PDF or a sha256 mismatch is final and not retried. It
stops when everything is kept, or after 3 passes in a row that keep nothing, and
writes `=== done` to `fetch-pc.log`; `ocr_tesseract.py` then finishes the last
PDFs and stops too.

Tested on the Mac before sending: two scans downloaded, matched their sha256
and were read (3,324 and 7,260 characters), and the OCR stopped by itself once
the fetch log said done.

**Run both jobs at once if the CPU keeps up**, 10 download workers in all.
If the OCR in either folder falls behind its downloads, give `ocr_tesseract.py`
`--workers 2` in each folder, or run Job 2 after Job 1.

### Sending results back, step by step

`pack_return.py` packs a work folder for GitHub: the thumbnails it has not sent
before, in zips under 85 MB, plus one `data.zip` of every `.jsonl` and log as
they stand. Never the PDFs. Download it once into each work folder:
<https://github.com/Robin-IA/Congressional-Letters-Dev/raw/pc-bundle/pack_return.py>

| Work folder | Push folder | Branch |
| --- | --- | --- |
| `C:\render2` (or `C:\render3`) | `C:\push\render` | `pc-render-return-2` |
| `C:\ocr` | `C:\push\ocr` | `pc-ocr-return-106-115` |

**Once per push folder** (PowerShell). The `fetch` and `reset` lines are only
for `pc-render-return-2`, which already exists; skip them for the OCR branch.

```
mkdir C:\push\render; cd C:\push\render
git init -b pc-render-return-2
git config core.autocrlf false
Set-Content .gitattributes "* -text"
git remote add origin https://github.com/Robin-IA/Congressional-Letters-Dev.git
git fetch origin pc-render-return-2
git reset --hard origin/pc-render-return-2
```

`core.autocrlf false` and `* -text` matter: a line-ending rewrite corrupts a
zip without any error.

**Every hour or so, for each job:**

```
py C:\render2\pack_return.py C:\render2 C:\push\render
cd C:\push\render
git add -A
git commit -m "render return: N new thumbnails"
git push origin pc-render-return-2
```

and for the OCR job:

```
py C:\ocr\pack_return.py C:\ocr C:\push\ocr
cd C:\push\ocr
git add -A
git commit -m "OCR return: N records"
git push origin pc-ocr-return-106-115
```

It prints the counts and writes them into `README.md`. It remembers what it
sent in `packed-thumbs.txt`, so each push carries only new thumbnails, about
9 MB per 500, and never reuses a zip name. Once both jobs are done, push one
last time. The Mac merges straight from the branch with `merge_render.py`,
which adds only what it lacks, so a thumbnail sent twice does no harm.

## What the PC is for

The PC harvests letters from the Wayback Machine's CDX index for two ranges of
Congresses, from a phone hotspot. The hotspot gives it a second IP address,
which is the whole point: Wayback refuses (503) more from the Mac's IP as load
goes up, and the PC has measured more room on its own.

| Range | Folder | Sites | State at 22:05 |
| --- | --- | --- | --- |
| 115th–118th | `C:\harvest` | 385 | Running since this evening. 220 finished, returned once already |
| 106th–110th | `C:\harvest-106-110` | 111 | New. Not started; empty cache |

The Mac harvests the 111th–114th (28 sites left) and renders thumbnails. The
member lists do not overlap, so neither machine fetches a site the other has.

## Starting the 106th–110th

1. Download
   <https://github.com/Robin-IA/Congressional-Letters-Dev/raw/pc-bundle/pc-harvest-106-110.zip>.
2. Unzip it into `C:\harvest-106-110`. **Not** into `C:\harvest`: `run_pc.py`
   takes its range from the single `harvest\letters-<range>-members.json`
   beside it, so two ranges cannot share a folder.
3. In PowerShell:

   ```
   cd C:\harvest-106-110
   $env:WORKERS=6; py run_pc.py
   ```

   The first line should say `=== harvest 106-110 (PC): 111 sites to do ===`.

It can run at the same time as the 115th–118th run, in its own window. Watch
the refusal share once both are running (below): the two runs share the
hotspot's IP, so 6 + 6 workers is twice the load measured as fine.

## How the runner behaves

- One line per site. `FAILED` lines are normal: Wayback's gateway gives up at
  about 60 s (504) or refuses (503). Failed sites are retried on the next pass.
- Pages of a big site are saved as they arrive (`<host>.partial.json`), so a
  retry asks only for the pages still missing.
- 5 minutes between passes, 30 if more than a quarter of a pass failed. It
  stops by itself when every site is done, or after 3 passes in a row that
  finish nothing.
- Ctrl-C is safe at any time. `py run_pc.py` again resumes; finished sites are
  skipped.
- Log: `harvest\letters\harvest-<range>-pc.log` in each folder.

Timing, per folder:

```
py build\timing_report.py harvest\letters\cache\requests.jsonl --hours 1
```

Look at the 503 share and pages per hour. If 503s climb well past half of all
requests, lower `WORKERS` for one of the runs.

## Expect the 106th–110th to fail more

These are 1999–2009. Many members then had no host of their own: their site
was a path such as `house.gov/<name>/` or `senate.gov/~name`. `harvest.py`'s
paged enumeration assumes a hostname, so those come back empty or fail on
every pass. That is a known gap (EXPLORERS.md, "Paths on shared hosts"), not
something to fix on the PC. When the runner stops with sites still failing,
report the list; do not change `harvest.py` to get round it.

## Sending results back

The same for both ranges, and safe to repeat as often as you like:

1. Zip the folder's `harvest\letters\cache` (all of it, including
   `requests.jsonl`).
2. Push it as the only file on a branch of `Robin-IA/Congressional-Letters-Dev`
   named `pc-cache-<range>` (the 115th–118th already uses
   `pc-cache-115-118`), with a short README saying when it was built and how
   many sites are finished, failed and untouched.
3. Tell Robin. The Mac merges it with `build/pc/merge_pc_cache.py`, which
   copies a site only when the PC finished it and the Mac has not. Partial
   returns are fine; nothing finished on the Mac is ever replaced.

## Rules

- `Robin-IA/Congressional-Letters-Dev` is **public**. Push only data branches
  (`pc-cache-*`) from the PC. Never push to `main` or `harvest-member-letters`,
  and never merge anything: merging is Robin's call.
- Do not edit `harvest.py`, `run_pc.py` or `timing_report.py` on the PC. If
  something needs changing, say what and why; the Mac side changes it through
  a pull request and rebuilds the bundle.
- Report numbers you measured, and say how you measured them. Two numbers in
  this project were published and turned out wrong because they were not.

## Rendering (rebuilt 12 November 2026, 09:51 — the second run)

Both harvests are done and merged. The PC's job is thumbnails for the
106th–114th and the `house.gov/<name>/` path letters: **7,662 PDFs** (10,721
letters). The Mac renders only the 115th–118th meanwhile, so the two never
render the same letter.

**This replaces the 01:06 bundle.** The first run rendered 172 before it was
stopped; that return (`pc-render-return`, `pc-render-pdfs`) is merged on the
Mac, and this bundle leaves out those and everything else that already has a
thumbnail. Do not resume the old `C:\render` folder — its letter list is stale.

**The network: the phone's hotspot, capped at 10 GB.** The run is about
3.5 GB of PDF downloads, call it 4 GB with retries. The hotspot also gives the
PC its own IP, so it does not compete with the Mac for Wayback's allowance.
Two things must reach Robin straight away, in this session:

- **The hotspot drops.** Downloads then fail as connection errors, and a batch
  line in `render-pc.log` shows few or none rendered. Tell Robin before the
  runner gives up after three empty batches.
- **3 GB used.** Before starting, note the PC's counters with
  `Get-NetAdapterStatistics | Select Name, ReceivedBytes, SentBytes` in
  PowerShell, and check every half hour or so. When received plus sent has
  grown by 3 GB, tell Robin and wait: Robin decides whether to carry on or move
  the PC to the Charter Wi-Fi. The size of `C:\render2\pdfs` is a cross-check,
  since the PDFs are nearly all of the traffic. The phone's own counter may
  read a little higher.

Moving networks loses nothing: Ctrl-C both windows, connect to the other
network, run both commands again; finished letters are skipped. The return to
GitHub (about 150 MB) can wait for Charter.

1. Once, if not already done: `py -m pip install pypdfium2 pillow pypdf`.
2. Download
   <https://github.com/Robin-IA/Congressional-Letters-Dev/raw/pc-bundle/pc-render-106-114-paths.zip>
   and unzip it into a new folder, `C:\render2`.
3. In PowerShell: `cd C:\render2`, then `$env:WORKERS=4`, then `py run_render.py`.

It works in batches of 400 and logs one line per batch to `render-pc.log`. The
first run measured 20 PDFs a minute, so a batch is about 20 minutes and the
whole bundle about 6½ hours. The Mac, at 4 workers, does ~1,000 an hour; if the
log shows many 503s or connection errors, drop to `$env:WORKERS=2`. It stops by
itself when nothing is left, or after 3 batches in a row that render nothing.
Ctrl-C is safe; run it again to carry on.

Each letter's PDF is downloaded once and gives four things, all in `C:\render2`:

| What | Where | Back to the Mac |
| --- | --- | --- |
| Thumbnail | `thumbs\<digest>.webp` | yes |
| Date the PDF states | `pdf-dates.jsonl` | yes |
| Text of its first pages | `letter-text.jsonl` | yes |
| The PDF | `pdfs\<digest>.pdf` | no — keep on the PC |
| OCR of PDFs with no text layer | `letter-ocr.jsonl` | yes |
| Attempts that failed | `thumb-failures.jsonl` | yes |

**Sending results back.** Push to a **new** branch, `pc-render-return-2`
(`pc-render-return` already holds the first run): `thumbs` zipped in parts
under 90 MB each (GitHub refuses a file over 100 MB; 7,662 thumbnails are about
140 MB), and one zip of the four `.jsonl` files, `letter-ocr.jsonl` included. Partial returns are fine.
The Mac merges with `build/pc/merge_render.py`, which copies only thumbnails
it lacks, adds dates and text only for letters it has none for, and never
replaces anything.

### OCR on the PC, with Tesseract (added 12 November 2026, 10:10)

About two thirds of these PDFs are scans with no text layer. The PC reads
them itself with Tesseract, so the PDFs (about 3.5 GB) do **not** need to come
back to the Mac. Keep them on the PC; nothing on the Mac waits for them.

1. Once: install Tesseract 5 (the UB Mannheim Windows build, which puts it in
   `C:\Program Files\Tesseract-OCR`), with English. `tesseract --version`
   should answer.
2. Download
   <https://github.com/Robin-IA/Congressional-Letters-Dev/raw/pc-bundle/ocr_tesseract.py>
   into `C:\render2`, beside `run_render.py`.
3. In a **second** PowerShell window, while rendering runs:
   `cd C:\render2`, then `py ocr_tesseract.py --watch`.

It reads only PDFs the renderer has already kept whose text layer is under 100
characters: the first six pages at 300 dpi, the same rules the Mac uses with
Apple Vision. It writes `letter-ocr.jsonl` beside the other files, one line per
PDF, with `"engine": "tesseract-<version>"` so its text is never mistaken for
the Mac's. With `--watch` it checks for new PDFs every 10 minutes and stops by
itself once `render-pc.log` says rendering is over and every PDF is read.
Ctrl-C is safe; run it again to carry on.

**Workers.** It defaults to half the PC's cores, one Tesseract each, leaving
the rest for the renderer, which mostly waits on downloads anyway.
`--workers N` changes it. On the Mac, 4 workers read 47 PDFs a minute; the
renderer keeps about 14 a minute, so OCR should keep up easily.

**Checked on the Mac before sending:** 8 PDFs already read with Apple Vision,
read again with this script. The words agreed 82–100%, median about 95%.
Tesseract's `confidence` is on its own scale and is not comparable with
Vision's.

**Do not edit the script on the PC.** If it fails, say so in the return's
README with the error, as with every other tool here.
