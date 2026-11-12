# PC exports: the letter files and run logs

`pc-exports.zip` holds everything the Windows PC produced on the night of
11–12 November 2026 that is **not** already on another branch.

**Built 12 November 2026, 01:35 local.** Nothing here is needed to reconstruct
the work — every letter below can be regenerated from the cache branches with
`harvest.py --export-only`, which is the documented path in `PC-HANDOFF.md`.
These are published so the numbers can be checked without re-running anything,
and so the per-site run records survive.

| | |
| --- | --- |
| Zip | 2.1 MB |

```
115-118/letters-raw-115-118.jsonl    11.4 MB   28,017 letters
115-118/members-115-118.json         89 KB     385 entries, the roster as queried
115-118/harvest-115-118-pc.log       3.5 KB    pass boundaries and backoffs
106-110/letters-raw-106-110.jsonl    172 KB    514 letters
106-110/members-106-110.json         25 KB     111 entries
106-110/harvest-106-110-pc.log       10.8 KB
render-pc.log                        68 B
```

Both letter files were checked before packaging: line counts match what the
runner reported (28,017 and 514), and no line failed to parse.

| range | letters | hosts with letters | members |
| --- | --- | --- | --- |
| 115th–118th | 28,017 | 362 of 385 | 359 |
| 106th–110th | 514 | 57 of 111 | 57 |

The 106th–110th thinness is the path-keyed gap, not a harvest failure — see
that range's branch README for the 39 hostnames the index genuinely held
nothing under.

## What is deliberately not here

- **`requests.jsonl`** — already inside both cache zips, where it belongs
  beside the cache it describes.
- **Thumbnails, dates and first-page text** — on `pc-render-return`.
- **The PDFs** — 172 files, 84 MB, still on the PC as instructed. They are the
  only thing from this night that exists nowhere else, and they come over by
  USB or Drive rather than through the repository.
- **The bundles and scripts** — `harvest.py`, `run_pc.py`, `thumbs.py`,
  `letters-to-render.jsonl` and the three `pc-*.zip` bundles all came *from*
  `pc-bundle` and are unchanged. Nothing on the PC edited them, per the rule in
  `PC-CLAUDE.md`.

## The four branches from this night

| branch | holds |
| --- | --- |
| `pc-cache-115-118` | 385 of 385 sites, 102,126 CDX rows |
| `pc-cache-106-110` | 111 of 111 sites, 12,779 CDX rows |
| `pc-render-return` | 172 of 7,920 thumbnails, with dates and text |
| `pc-exports` | this: the letter files and run logs |
