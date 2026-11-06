# Deploying

A static page on GitHub Pages, serving the `harvest-member-letters` branch from
the repository root. No server, no database, and — for now — no archive.org
item: everything the page reads is in this repository.

It was built to run the way [internetarchivecanada/etd-viewer](https://github.com/internetarchivecanada/etd-viewer)
runs, with the bulk of the data in an archive.org item that the browser reads
directly. That works because item downloads carry
`Access-Control-Allow-Origin: *` — verified against
`archive.org/download/etd-catalog-cardinalscholar-bsu-edu/`. The item would
not take the files at the rate they were produced, so they moved here; see
below.

## What lives where

Measured from `git ls-files`, 6 November 2026.

| | | |
| --- | --- | --- |
| `index.html`, `app.js` | the repository, at the root | Pages serves from root, as etd-viewer does |
| `index.json` | the repository, 167 KB | members, counts, facets, year histogram — so the page paints at once |
| `payload/member/<id>.json`, `payload/search.json` | the repository, 19.6 MB | 514 member files, fetched one member at a time |
| `thumbs/<digest>.webp` | the repository, 854.2 MB | 47,688 rendered first pages, 18.3 KB on average |

`data_base` and `thumb_base` in `index.json` say where the page looks for the
last two. Both are relative paths today (`payload/member/`, `thumbs/`); each is
one field to change when the data moves back to an item.

## Why the item is not in the path

Every uploaded file queues an `archive.php` task and an item rations how many
may be queued:

```
Please reduce your request rate. - bucket_tasks_queued exceeds rationed amount
```

Measured here: 34 tasks draining at roughly five a minute. That is months for
48,000 thumbnails — the upload, not the rendering, becomes the thing that
cannot finish. Bundling into a zip is the documented way out, and is how the
North Korea explorer serves its screenshots, but a zip uploaded to this item
returns 200 from S3 and then never appears, twice, with the task queue empty.
**That is unexplained and is the thing to fix.**

## The Pages ceiling

Published sites "may be no larger than 1 GB", and a site that breaches it may
simply stop being served. The tracked tree is **874.9 MB**, nearly all of it
`thumbs/`. That leaves about 149 MB — roughly 8,000 more thumbnails at the
current average — and the backfill of departed members will want more than
that.

Thumbnails are WebP at quality 72, which is what made the corpus fit at all:
the same size as JPEG at quality 50, 21% smaller than the JPEGs they replaced.
`build/publish_thumbs.py` holds a 940 MB budget for thumbnails, a 64 MB margin
under the ceiling once everything else is counted.

If the budget runs out before the item works, re-compress rather than
re-render. The PDFs are not kept, so rendering again means pulling thousands of
multi-megabyte files off Wayback a second time.

## Publishing

The renderer writes straight into `thumbs/`, so there is no copy step:

```bash
python3 build/thumbs.py --thumbs thumbs --workers 2 --pause 1.5
python3 build/build_site.py --thumb-base thumbs/ --force
git add -A && git commit -m "Publish previews" && git push dev
```

`build_site.py` must run again after any thumbnail pass, because `index.json`
records which thumbnails existed when it was built. `--force` lets it proceed
when the corpus shrinks by more than a tenth, which it otherwise refuses.

**Push to `dev` only** — see `CLAUDE.md`. Pages allows **10 builds an hour**
from a branch and every push is one, so batch edits rather than pushing each.

`build/upload_item.py` and `build_site.py --item` remain for when the item is
back in the path: `--item` writes `data_base` as
`https://archive.org/download/<item>/…`. Neither is used today.

## Where it is published

All three sites serve the `harvest-member-letters` branch from its root — not
`main`, which is the initial scaffold and has never had the work merged into
it.

| Repository | Site | |
| --- | --- | --- |
| `Robin-IA/Congressional-Letters-Dev` | <https://robin-ia.github.io/Congressional-Letters-Dev/> | **development preview — this repository** |
| `internetarchivecanada/congressional-letters` | <https://internetarchivecanada.github.io/congressional-letters/> | published explorer, frozen |
| `Robin-IA/congressional-letters` | <https://robin-ia.github.io/congressional-letters/> | copy of the published explorer, frozen |

The two published sites stay at `ddaf0c9ac` (tag `pre-congress-restructure`)
until replacing them with this work is approved. That is a deliberate,
one-time push, not part of publishing.

`internetarchivecanada/letters-from-congress` is the private handover record
and has no Pages site — Pages from a private repository needs a paid plan,
which is why the published explorer was made as a separate public repository.

## The labs tile

`menu.tsv` and `cover.jpg` are for a tile on
[wayback-labs](https://wayback-labs.sf.archive.org/), the way the North Korea
explorer has one pointing at its GitHub Pages build and tagged SERVERLESS.
The tile is the only thing that would live on labs; the explorer itself does
not.

`meetings` references its cover at the web root
(`/community-meetings-cover.jpg`), so `cover.jpg` presumably needs copying
there as `letters-from-congress-cover.jpg`.

## Keeping it current

```bash
python3 build/harvest.py --workers 3      # resumable; CDX per member site
python3 build/parse_urls.py
python3 build/thumbs.py --thumbs thumbs --workers 2 --pause 1.5
python3 build/build_site.py --thumb-base thumbs/ --force
```

`harvest.py` writes the explorer's own `data/members.json` and
`data/letters-raw.jsonl`. The departed-member backfill must not — it runs with
its outputs redirected, and `BACKFILL.md` has the commands.
