# For Claude on the PC

Written 11 November 2026, 22:15, by the Claude session on the Mac. This is
what a Claude session on the Windows PC needs to know to help run the letter
harvest. Robin is the person you are working with.

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
