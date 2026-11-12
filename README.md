# PC cache return: 115th–118th Congresses

`pc-cache-115-118.zip` is the Windows PC's harvest cache, coming **back** to the
Mac. The outbound direction is the `pc-bundle` branch; this is the return leg.

**Updated 11 November 2026, 23:15 local.** The first push here was a 21:41
snapshot at 220 sites; this one is the finished harvest.

| | |
| --- | --- |
| Sites finished | **371 of 385** |
| Still failing | 13 |
| Never attempted | 1 (`royce.house.gov`, in flight when this was built) |
| CDX rows held | **99,437** across 365 hosts |
| Files in the zip | 392 (flat at the root) |

The bundle arrived with 268 sites to do. The PC finished **251 of them** in one
evening.

## Merging it

Per `PC-HANDOFF.md`, "Bringing results back to the Mac". The zip unpacks flat,
so the site files land directly in the target folder:

```bash
unzip pc-cache-115-118.zip -d ~/Downloads/pc-cache
python3 build/pc/merge_pc_cache.py ~/Downloads/pc-cache          # dry run
python3 build/pc/merge_pc_cache.py ~/Downloads/pc-cache --apply
```

A site is copied only when the PC finished it and the Mac has not. A finished
site on the Mac is never replaced and nothing is deleted.

`requests.jsonl` is in the zip as well. It is the PC's per-request timing log,
not cache data; `merge_pc_cache.py` ignores it, and it is kept because it is the
evidence behind the worker-count note below.

**Check whether `thumbs_loop.sh` is running before `--apply`.** Its next cycle
rebuilds the letter list from the merged cache and renders every new letter
without asking. `BACKFILL.md` §6 puts the published site at 874.9 MB of Pages'
1,024 MB — roughly 8,000 previews of headroom. This range alone looks like
~22,500 letters (6,493 counted across 111 finished sites, 58 per site, 56% of
CDX rows surviving the filter), which is about three times the room left.
Where the previews live is issue #2 step 6, and merging turns it from a
question into a deadline.

## The 13 that still fail

Six are plain Wayback 503s, five kept most of their pages and lost one, one is
a hotspot DNS failure. None look permanent, but they survived repeated retries
across an evening:

```
lowey.house.gov            HTTP 503        lipinski.house.gov   1 of 2 pages kept
sensenbrenner.house.gov    HTTP 503        marino.house.gov     1 of 2 pages kept
torressmall.house.gov      HTTP 503        olson.house.gov      2 of 3 pages kept
cochran.senate.gov         HTTP 503        tipton.house.gov     2 of 3 pages kept
costello.house.gov         HTTP 503        hatch.senate.gov     3 of 4 pages kept
goodlatte.house.gov        HTTP 503        blackburn.house.gov  0 of 1 pages kept
cramer.house.gov           getaddrinfo failed
```

`blackburn.house.gov` is the only one holding nothing at all.

## Worker counts on Windows, measured

`PC-HANDOFF.md` describes the default as two workers and offers `WORKERS=1` to
go gentler. It also says the runner had not yet been run on Windows. It has now,
and on this connection more workers was substantially better:

| `WORKERS` | sites/min |
| --- | --- |
| 1 | 0.00 over 19 min |
| 2 | 0.22–0.32 |
| 4 | 0.54 |
| **6** | **1.95 sustained over 78 min** |

Refusals did not scale with concurrency the way we expected: 503s sat at 18% at
two workers and 20–22% at four, while request volume doubled at an unchanged
success rate. The pile of cached failures *fell* throughout — 162 to 13 — so the
extra workers cleared retries faster than they created them. Connection-level
errors (`URLError`, `timeout`) appeared at six but stayed at 4–6%, never
becoming the constraint. The ceiling was never found; six was simply the last
number tried.

Caveat: one cellular connection, one evening, against a Wayback index whose own
load was changing. A reason to try more workers, not a settled figure.

Two endpoint notes, both already in the current bundle: queries go over
`https://` because `http://` answered 503 to about a fifth of requests under
load, and Wayback's gateway abandons an expensive filtered scan at about 60
seconds with a 504 while its backend keeps computing — which is why a third
attempt often succeeds against a warm index. That pattern is visible in the tail
of `requests.jsonl`:

```
23:08:50  cramer.house.gov  page 15  try1  60.5s  http504
23:09:52  royce.house.gov   page 5   try3  49.1s  ok
```
