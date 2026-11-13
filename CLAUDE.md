# Letters from Congress — working notes

Letters that members of Congress published on their own websites, preserved by
the Wayback Machine, organised by Congress. Read `README.md` first for what the
thing is; this file is for the decisions that are not visible from the code.

**One explorer per Congress, 106th to 119th, and a home page over all of them.**
`EXPLORERS.md` has the build instructions, the decisions and what is still
open; `METHODOLOGY.md` has the method behind each step. This repository is the
development repository: everything is built and tested here, and the sites are
published from it by script. Nothing published is edited by hand.

## Where it is published

The same build goes to two accounts, every time (`build/publish_explorers.sh`,
then `build/publish_iac.sh`):

| | Robin-IA | Internet Archive Canada |
| --- | --- | --- |
| Home page | [`Explorer-Letters`](https://robin-ia.github.io/Explorer-Letters/) | [`congressional-letters`](https://internetarchivecanada.github.io/congressional-letters/) |
| Each Congress | `Explorer-Congressional-Letters-<N>` | `Explorer-Congressional-Letters-<N>` |

Each explorer's "All Congresses" link goes to its own account's home page, so
the IAC copies differ from Robin-IA's in two files: `index.html` (that link)
and `README.md` (its own address). `publish_iac.sh` makes that change on the
way across and never rewrites IAC history. The IAC home page lives at the
address the first explorer was published at, so it also keeps forwarding for
that explorer's old links (`?member=…`, `119th/`, `explorer.html`).

**Nothing is pushed to an explorer repository by hand.** Every one is built
output: rebuild, then publish with the scripts. Creating a repository, on
either account, is Robin's call.

**The Mac runs the pipeline unattended.** `build/auto_publish.sh` loops in
`~/ia/congressional-member-letters`: it merges the PC's return branches as
they arrive, and after a merge or 300 new thumbnails it rebuilds every
explorer and the home page and publishes to both accounts. Beside it run
`build/thumbs_loop.sh` (rendering) and `build/ocr_letters.py --watch` (OCR).
**That checkout builds from its own copy of the scripts and templates**, so a
change merged here reaches the sites only once those files there are brought
to main. On 12 November an out-of-date copy there twice republished an old
home page over a new one.

**This repository's own Pages site** serves `harvest-member-letters` at
<https://robin-ia.github.io/Congressional-Letters-Dev/>. Its `119th/` is the
explorer template every Congress is stamped from (see below), not a published
explorer.

Other repositories, kept as records:

| Repository | What it is |
| --- | --- |
| `internetarchivecanada/letters-from-congress` | Private. The original handover: PR #1, issue #2, and `docs/keeping-it-current.md`, which stays there. |
| `Robin-IA/congressional-letters` | The first single-Congress explorer. Superseded. |

## The explorer template

Every explorer is stamped from `119th/index.html` and `app.js` in this
repository by `build/build_congress.py`, which swaps in each Congress's name,
dates and links. A swap that no longer matches stops the build rather than
publishing a page that says the wrong Congress. Until 12 November the
template was read from `iac-119th`, a branch that existed on one laptop only;
it moved here so a fix to the explorers goes through a PR (#59).

**A change to either file reaches every explorer on the next build.** Bump
`app.js?v=` in `119th/index.html` whenever `app.js` changes.

## Accessibility and security

The home page and the explorers pass WCAG 2.2 Level AA, the security checks
and the code validity checks (`security-accessibility-checks.md`, checked 12
November 2026), and their footers say so. **The note is a claim**: a change to
the pages needs the explorer-checks skill re-run, and a run that stops
passing takes the note down. `--faint` is dark for a reason, the filter
controls are named and keep focus, and the counts are `role="status"`; the
report has the rest.

## The corpus rule

**Every letter here opens as a letter.** That is what the corpus is cut to, and
it cost 22.6% of what a search for "letter" appears to offer.

A URL containing "letter" is not the letter, twice over:

- **The announcement page** — `/oversight/letters/…`, `/statements/…`,
  `/media/in-the-news/…` — is a press release wearing the word. 7,220 dropped.
- **The download wrapper** is worse, because it is a page *instead of* the
  letter. The Senate CMS serves a ColdFusion interstitial carrying
  `x-archive-orig-refresh: 2; url=…&download=1`, so what the crawler archived is
  the member's page furniture and no document. 13,708 of these, 6,997 of which
  we already hold as a PDF at the real URL.

`build/resolve_wrappers.py` chases the remainder. It is parked at 113 of 6,711;
it competes with the renderer for the same Wayback budget, so run one at a time.

## Everything is served from the explorer repositories, not from an archive.org item

The ETD arrangement — bulk data on an item, streamed client-side — is what this
was built to do, and the item will not take it.

Every file uploaded queues an `archive.php` task and an item rations how many
may be queued at once: measured at 34 draining at roughly **five a minute**.
That is months for 48,113 thumbnails; the upload, not the rendering, becomes the
thing that cannot finish. Bundling into a zip is the documented way out and is
how the North Korea explorer serves its screenshots, but **a zip uploaded to
this item returns 200 from S3 and then never appears**, twice, with the queue
empty. That is unexplained and is the thing to fix if anyone wants the item back
in the path.

So each explorer repository tracks its own `thumbs/` and `payload/member/`,
and Pages serves them; each repository has its own 1 GB limit.
`thumb_base` and `data_base` in `index.json` are one field each when it moves
back.

**Thumbnails are WebP at quality 72.** Measured on 200 real files: 18.6 KB
against JPEG's 23.6 KB, the same size as JPEG quality 50 while still being
quality 72. That 21% is exactly what makes all 48,113 fit inside the 1 GB Pages
ceiling — 868 MB projected, against a 940 MB budget in `publish_thumbs.py` that
leaves a 64 MB margin. The ceiling is a hard limit; a site that breaches it may
simply stop being served.

## The long jobs

Both take days, both are resumable, **neither has to finish** for the explorer
to be correct.

```bash
build/thumbs_loop.sh 115-118 106-114 paths   # render behind the harvests, a cycle at a time
build/auto_publish.sh                        # merge the PC's returns, rebuild, publish both accounts
```

Run them from a terminal, not from inside a Claude session: anything a session
starts dies with it. And do not run anything else that fetches from the
Wayback Machine beside the renderer; they share one rate limit.

**The trap when moving machines.** `thumbs/` is tracked and arrives with a
clone; `payload/thumbs/` is gitignored and arrives empty. `thumbs.py` checks
`payload/thumbs/`, so a plain run on a fresh clone re-fetches every PDF already
done — thousands of multi-megabyte files asked of the Wayback Machine for
nothing. Pass `--thumbs thumbs` and check the first line it prints: `N still to
render` should be far below the total.

Ordering matters more than throughput, because they stop before they finish.
The renderer walks **across all members by position on each member's own page**,
so every member's opening screen fills together. Corpus order left 67 members
with nothing; fewest-first left Elizabeth Warren, who is top of the list and the
first page anyone opens, as a screen of placeholders.

## Measurement discipline

**Numbers in this project are measured, and the ones that were not have been
wrong.** Two that were published and false:

- "About a quarter of these PDFs carry extractable text," from 21 files checked
  by hand. Re-measured on 50 at random, one request at a time: **65%**, median
  2,852 characters. The live renderer across 9,178 letters reads 53%. Treat
  **47–65%** as the band. See issue #1 in `Robin-IA/congressional-letters`.
- "Press releases: 85" on the about page counted letters whose server sent the
  wrong content type. The real press releases were never in that number.

When a figure goes on the page, derive it from the data at build time rather
than typing it.

## Traps that have cost real time

**Caching, four times in one afternoon.** The Pages CDN served a stale `app.js`;
the browser served a stale `index.json`; archive.org's CDN served stale
per-member files; and the CDN served a stale `index.html`, so the `?v=` on the
script tag could not take effect. None of them looks broken — the page renders
cleanly and describes a build that is no longer there. Everything a build
rewrites now carries `index.json`'s `stamp`; thumbnails need no stamp, being
named by content digest. **Bump `app.js?v=` in `index.html` whenever `app.js`
changes.**

**`http://` CDX answers 503.** `harvest.py` names the http endpoint and works,
but in `thumbs.py` the same query over http returned *"Internet Archive:
Temporarily Offline"* in about five seconds every time — so the capture-retry
looked like "these letters have no other captures" when seven of eight lookups
were swallowed 503s. Use https.

**Captures can be truncated and the index will not say so.** Some payloads come
back at exactly 64,000 bytes — a crawl byte cap storing the first 64 KB of a
PDF, perfect `%PDF` header and no document. CDX's `length` is the WARC record
size; not one row in 69,360 reports 64000. Only the bytes show it. `thumbs.py`
treats a known cap size, and a PDF that will not render, as a bad capture and
asks CDX for the others: 4 of 12 rescued in the first measured batch. Rare in
the end — 6 in 9,178.

**A count from one source, a body from a narrower one.** The recipient page
chose which members to load with `MEMBERS.filter(m => m.top.includes(name))` —
the member card's top *three*. Nobody has Amazon in their top three, so the page
announced "37 letters" and listed none. **107 of the 200 recipients rendered
empty.** The same shape was in the year page (416 member files fetched for 2024)
and the search shortcuts. `search.json` carries a recipient for every letter and
is the thing that actually knows. If a view reports a number it did not compute,
check where each half came from.

## Conventions

- **Branch and open a PR; never commit to `main`.** Pushing a branch needs no
  permission. Merging is Robin's call.
- **Push branches to this repository only.** The sites are published by
  `publish_explorers.sh` and `publish_iac.sh`, never by pushing to them.
- **Fetch before branching.** The Mac pipeline and the PC both push here.
- Two-digit-year filename dates (`090501`) are ambiguous; `parse_urls.py`
  reads them the way that fits the capture and the member's first year, taken
  from `data/rosters/`, not the harvest rosters' `since` (#58, #60).
- GitHub Pages allows **10 builds an hour** from a branch and every push is one.
  Batch edits rather than pushing each.
- Tests: `python3 -m unittest discover -s tests`. 114 at the time of writing, and
  several of them assert that something which *looks* like debris survives —
  that is the half of the subject cleaning which is easy to get wrong.

## Open

- Rendering and OCR are running (see above); the PC handed back 7,920 path
  PDFs it did not render, and the Mac is working through them.
- The main 2000-2026 corpus has not been re-parsed with the date fix: its raw
  file, `data/letters-raw.jsonl`, is not on the Mac (issue #2).
- `resolve_wrappers.py` at 113 of 6,711 — worth perhaps 3,000 more letters.
- Full-text search: the text and OCR are there and nobody has built an index.
- The Mac's venv predates the pinned `requirements.txt` (Pillow 13, pypdf 7);
  reinstall it when the renderer is not running.
- Why the archive.org item swallows zips.
