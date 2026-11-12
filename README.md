# PC cache return: 115th–118th Congresses

`pc-cache-115-118.zip` is the Windows PC's harvest cache, coming **back** to the
Mac. The outbound bundle is on `pc-bundle`; this is the return leg. The
106th–110th returns separately on `pc-cache-106-110`.

**Final, 12 November 2026, 00:18 local. The range finished clean — 385 of 385,
nothing left.** Two earlier pushes on this branch were partial snapshots (220
sites at 21:41, 371 at 23:15); this supersedes both.

| | |
| --- | --- |
| Sites finished | **385 of 385** |
| Still failing | 0 |
| Never attempted | 0 |
| CDX rows held | **102,126** across 379 hosts |
| Letters exported | **28,017** |
| Files in the zip | 386 (flat at the root, including `requests.jsonl`) |

The bundle arrived with 268 sites to do. The PC finished all of them in one
evening, 18:34 to 00:16.

## Merging it

Per `PC-HANDOFF.md`, "Bringing results back to the Mac". The zip unpacks flat:

```bash
unzip pc-cache-115-118.zip -d ~/Downloads/pc-cache
python3 build/pc/merge_pc_cache.py ~/Downloads/pc-cache          # dry run
python3 build/pc/merge_pc_cache.py ~/Downloads/pc-cache --apply
```

A site is copied only when the PC finished it and the Mac has not. A finished
site on the Mac is never replaced and nothing is deleted.

`requests.jsonl` is in the zip as well — the PC's per-request timing log, not
cache data. `merge_pc_cache.py` ignores it; it is kept as the evidence behind
the worker-count note below.

**Check whether `thumbs_loop.sh` is running before `--apply`.** Its next cycle
rebuilds the letter list from the merged cache and renders every new letter
without asking. `BACKFILL.md` §6 puts the published site at 874.9 MB of Pages'
1,024 MB — roughly 8,000 previews of headroom. **This range alone exported
28,017 letters**, about three and a half times that. Where the previews live is
issue #2 step 6, and merging turns it from a question into a deadline.

## Every straggler came back

Thirteen sites were still failing at 23:15 and all thirteen were recovered on
later passes, including the two that looked worst:

```
hatch.senate.gov     156 letters (of 231 rows)   -- had 3 of 4 pages banked
olson.house.gov       42 letters (of 50 rows)    -- plain 503
blackburn.house.gov                              -- recovered; had held nothing
cramer.house.gov                                 -- 18+ index pages, the largest site
```

The partial-page mechanism is why: pages that arrived were kept in
`<host>.partial.json`, so each retry asked only for what was missing. Nothing
was re-fetched and nothing was lost across three restarts at different worker
counts.

## Worker counts on Windows, measured

`PC-HANDOFF.md` describes the default as two workers and offers `WORKERS=1` to
go gentler, and notes the runner had not yet been run on Windows. It has now,
and on this connection more workers was substantially better:

| `WORKERS` | sites/min |
| --- | --- |
| 1 | 0.00 over 19 min |
| 2 | 0.22–0.32 |
| 4 | 0.54 |
| **6** | **1.95 sustained over 78 min** |

Refusals did not scale with concurrency as expected: 503s sat at 18% at two
workers and 20–22% at four while request volume doubled at an unchanged success
rate. The pile of cached failures *fell* throughout — 162 to 13 to 0 — so the
extra workers cleared retries faster than they created them. The ceiling was
never found; six was simply the last number tried.

Connection-level failures (`URLError`, `timeout`) stayed at 4–6% here, but
reached **24%** once the 106th–110th ran alongside this range on the same
hotspot IP. See that branch's README: the driver looked like request *rate*
rather than worker count.

Caveat: one cellular connection, one evening, against a Wayback index whose own
load was changing. A reason to try more workers, not a settled figure.

## Two endpoint notes

Both already in the current bundle. Queries go over `https://` because `http://`
answered 503 to about a fifth of requests under load. And Wayback's gateway
abandons an expensive filtered scan at about 60 seconds with a 504 while its
backend keeps computing, which is why a third attempt often succeeds against a
warm index:

```
23:08:50  cramer.house.gov  page 15  try1  60.5s  http504
23:09:52  royce.house.gov   page 5   try3  49.1s  ok
```
