# Letters from Congress (2007-present)

### → **[Development preview](https://robin-ia.github.io/Congressional-Letters-Dev/)**

*Picking this up on another machine? → [PICKUP.md](PICKUP.md) · Working notes → [CLAUDE.md](CLAUDE.md)*

Letters that members of Congress published on their own websites, preserved by
the Wayback Machine, and organised by Congress: a home page listing every
Congress from the 110th (2007) forward, and below it, one explorer per
Congress — who each member wrote to, and when.

**This repository is where it is being built.** The preview above is its only
site. There is no published copy or mirror yet; one will come when the work is
ready and has been approved. Push to this repository only — see `CLAUDE.md`.

## Where it stands

| Congress | State |
| --- | --- |
| **119th (2024-26)** | **Built** — 69,650 letters from 514 of 539 members. The members who left office during it are being added |
| 110th – 118th | Placeholders on the home page, not yet built |

The 119th explorer is the work that began as
[congressional-letters](https://internetarchivecanada.github.io/congressional-letters/),
which covered the members sitting in 2026. That explorer is unchanged and stays
as it is; this repository builds on it.

## How the site is laid out

One static site on GitHub Pages, serving the `harvest-member-letters` branch
from the repository root. No server, no database.

| Path | What it is |
| --- | --- |
| `index.html` | The home page: the list of Congresses |
| `119th/` | The 119th Congress explorer — `index.html`, `index.json` and `payload/` |
| `119th/index.json` | Members, counts, facets, year histogram, and a cache stamp |
| `119th/payload/member/<bioguide>.json` | One member's letters, fetched when that member is opened |
| `119th/payload/search.json` | Every letter's description, so search works from a cold load |
| `app.js` | The explorer, shared by every Congress's folder |
| `thumbs/<digest>.webp` | Rendered first pages, shared by every Congress |
| `explorer.html` | Forwards to `119th/` — the 119th lived here for a day |

Each future Congress gets a folder of its own beside `119th/`, with its own
`index.json` and `payload/`, reading the same `app.js` and `thumbs/`. A letter
captured once is rendered once, however many Congresses it appears in.

Every explorer view is a link, because the URL is the whole state:
`119th/?member=W000817`, `?to=Department%20of%20Justice`, `?year=2020`,
`?view=recipients`, `?view=search&q=opioid`. A query sent to the home page is
forwarded to `119th/`, so links made before the home page existed still work.

To run it locally, serve the repository root:

```bash
python3 -m http.server 8947
```

## Building the 119th

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

`pypdfium2` and `pillow` do the rendering, `pypdf` reads dates and text.
`internetarchive` is only needed by `build/upload_item.py`, which is not in the
serving path.

```bash
python3 build/harvest.py --workers 5      # CDX per member site; resumable
python3 build/resolve_wrappers.py         # chase download pages to the file
python3 build/parse_urls.py               # URLs -> date, recipient, subject
python3 build/thumbs.py --thumbs thumbs   # render first pages into thumbs/
python3 build/build_site.py --thumb-base ../thumbs/ --force
python3 -m unittest discover -s tests
```

- **`--thumbs thumbs`** — without it the renderer looks in `payload/thumbs/`,
  which is gitignored and empty on a fresh clone, and re-fetches every PDF
  already rendered.
- **`--thumb-base ../thumbs/`** — relative to the page in `119th/`, which is
  how the browser resolves it.
- **`--force`** — the build otherwise refuses to shrink the corpus by more than
  a tenth, a guard worth keeping.

`build_site.py` writes into `119th/` by default. It must run again after any
thumbnail pass, because `index.json` records which thumbnails existed.

`harvest.py` caches **raw** CDX rows and cleans on the way out, so a newly
discovered kind of junk costs a re-filter rather than another pass over every
host. Querying is hours; filtering is seconds.

`thumbs.py` and `resolve_wrappers.py` take days, are resumable, and neither has
to finish for the explorer to be correct. Both are deliberately slow — two
workers and a pause, because four earned a rate limit that outlasted the run
that earned it. The renderer walks across all members by position on each
member's own page, so every member's opening screen fills together.

### Members who left during the Congress

`harvest.py` builds its roster from `legislators-current.json`, so a member who
resigned, died or moved to another post during the Congress is not in it.
They are harvested from a roster of their own and built in beside the rest:

```bash
python3 build/harvest.py --members-in data/congress119-departed.json \
  --out data/letters-119-departed.jsonl \
  --members-out data/congress119-departed-queried.json --workers 3
python3 build/parse_urls.py --raw data/letters-119-departed.jsonl \
  --members data/congress119-departed.json \
  --out data/letters-119-departed-parsed.jsonl
python3 build/build_site.py --thumb-base ../thumbs/ --force \
  --also-members data/congress119-departed.json \
  --also-parsed  data/letters-119-departed-parsed.jsonl
```

The roster carries each member's `left` date. The explorer shows them as
"Left office", gives their years of service as an end year rather than
"present", and links their site to the Wayback Machine's copy from the day they
left, because the address usually belongs to someone else by now.

The departed are kept out of `data/members.json` on purpose: `harvest.py`
rewrites that file from the current roster, and would drop them.

For members who left **before** a Congress began — the material for the 110th to
118th — see [BACKFILL.md](BACKFILL.md).

## Why this material needs an archive

A member's website is replaced wholesale when the seat changes hands — the
address survives, the content does not. Checked while building this:
`portman.senate.gov` and `braun.senate.gov` no longer resolve at all. Their
letters are still in the Wayback Machine.

So this is not a convenience copy of a live website. For a growing share of it,
the archive is the only copy.

## Where the letters come from

Wayback's CDX index, queried per member site, for URLs containing "letter".
The roster of members and their official websites is
`unitedstates/congress-legislators`.

**Archive-It is not a source for this.** Its "Congress" collection (6848)
returned zero captures for `warren.senate.gov` and `grassley.senate.gov`: it
archives political campaigns and `senate.gov`'s own homepage, not official
member sites.

**Nor, for now, is NARA's end-of-Congress harvest**, which the Internet Archive
crawls under contract and [webharvest.gov](https://webharvest.gov/) presents —
the model for this site's home page. Its items are access-restricted.

## Every letter here opens as a letter

That is the rule the corpus is cut to, and it costs 22.6% of what the index
appears to offer. A URL containing "letter" is not the letter twice over:

**The announcement page.** `/oversight/letters/…`, `/statements/…`,
`/media/in-the-news/…` — a press release wearing the word. 7,220 of them, and
none is a letter.

**The download wrapper.** The Senate CMS links a page, not a file, and the page
meta-refreshes to the file two seconds later:

```
GET /download/20181109-letter-to-commerce-daeo-re-ross-conflict-of-interest
    x-archive-orig-refresh: 2; url=//…-of-interest&download=1
```

What the crawler archived is the interstitial. Replay it and you get the
member's page furniture and no letter. 13,708 of these; 6,997 we already hold
as a PDF at the real URL. `build/resolve_wrappers.py` recovers the remainder,
chasing `&download=1` to whatever finally has a body and believing only its
first five bytes.

## Why the filename is the description

The description beside each letter is cut from the file name, because that is
what the harvest gives you for nothing: a URL per letter and no text. The
people publishing these files named them for people:

```
012622_-wh-hhs-fda---covid-therapeutics-letter
4-5-20---minnesota-delegation-letter-to-president-trump---disaster-declaration
pressley-warren-markey-letter-to-hhs-re-racial-disparities-in-vaccine-distribution
```

Date, co-signers, the member's role, the recipient and the subject, all in the
slug. Named officials are folded into the office they held, so one
correspondent is not split in two; a surname held by two office-holders is left
unresolved rather than guessed.

Somewhere between 47% and 65% of these PDFs carry a usable text layer — the
first published estimate, "about a quarter", was from 21 files and said the
opposite of what is true. The text is already extracted for many of them, and
nothing yet indexes it. Search covers descriptions, not contents.

## The thumbnails are the point

A first page rendered at about 18 KB shows the letterhead, the date, the
salutation and the opening argument. It is legible, and a visitor learns more
from it than from anything a parser could write, which is why a member's
letters are shown as a wall of documents before they are shown as a table.

They are WebP at quality 72, named by capture digest, and served from `thumbs/`
in this repository — 854 MB across 47,688 files, most of GitHub Pages' 1 GB
limit. That leaves room for roughly 8,000 more, fewer than the earlier
Congresses will need. Moving them to an archive.org item is the way out, and is
blocked on an unexplained fault: a zip uploaded to the item returns 200 and
never appears. See `CLAUDE.md`.

## Four traps in this pipeline

**A section called "letters" is not a letter.** Wayback has crawled an endless
JavaScript-library path space beneath some `/media/letters/` folders.
Unfiltered, that made John Larson the most prolific correspondent in Congress
with 43,357 letters. A letter is now identified by its own name or the folder it
sits directly in.

**"newsletter" contains "letter".** For `murkowski.senate.gov`, 65% of matching
URLs were newsletters. Excluded in the query, where it is free.

**A site's 404 page carries the letter's path.** `404error.html?request=...`
looks exactly like the document it failed to serve.

**`showNumPages` ignores filters.** It returned 1,261 for `grassley.senate.gov`
with and without a urlkey filter. Rows are counted instead.

And one about measurement: a short read must be recorded as a failure, never as
a number. `warren.senate.gov` measured 7 PDFs at one timeout and 5,897 at
another. Results are cached per host and a re-run retries only what failed.

## Caveats

- **Only what was archived.** This is what the Wayback Machine holds of what
  Congress published, not a complete record of what Congress sent.
- **Only letters whose URL says "letter".** One published as an untitled
  attachment, or named by topic alone, is not reached.
- **Recipients are named in about a fifth of filenames.** Where a site names
  files by topic, there is no recipient to extract and none is invented.
- **Most dates are upper bounds.** Where neither the filename nor the PDF
  states a date, a letter is placed at the first Wayback capture that saw it,
  and shown as "by March 2016" rather than as a day.
- **The 119th explorer holds everything on its members' sites**, back to 2000 —
  the way an end-of-Congress harvest captures a whole site, old pages included.
  A letter from 2012 by a member still sitting in 2025 appears there.

`build/ia_search.py` is vendored from `collection-analysis` and carries that
project's notes on these endpoints.
