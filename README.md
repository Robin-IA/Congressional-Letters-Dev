# Letters from Congress

### → **[Letters from Congress](https://internetarchivecanada.github.io/congressional-letters/)** · [Robin-IA copy](https://robin-ia.github.io/Explorer-Letters/)

*Picking this up on another machine? → [PICKUP.md](PICKUP.md) · Working notes → [CLAUDE.md](CLAUDE.md) · Building the explorers → [EXPLORERS.md](EXPLORERS.md)*

Letters that members of Congress published on their own websites, preserved by
the Wayback Machine, organised by Congress: a home page that searches across
every Congress from the 106th (1999) to the 119th, and one explorer per
Congress below it, showing who each member wrote to, and when. Each letter
appears in exactly one explorer, the Congress in session on its date, and
opens from the Wayback Machine.

**This is the development repository.** The methodology, scripts, data,
templates, tests, decisions and issues live here; the sites are built from it
and published by script. Nothing published is edited by hand.

## Where it is published

The same build is published to two accounts, every time:

| | Internet Archive Canada | Robin-IA |
| --- | --- | --- |
| Home page | <https://internetarchivecanada.github.io/congressional-letters/> | <https://robin-ia.github.io/Explorer-Letters/> |
| One Congress | `internetarchivecanada.github.io/Explorer-Congressional-Letters-<N>/` | `robin-ia.github.io/Explorer-Congressional-Letters-<N>/` |

Each is its own GitHub repository serving Pages from `main`, tagged
`explorers`, `democracys-library`, `congress` and `letters-from-congress`.
Every explorer's description and "All Congresses" link lead back to its
account's home page.

**Checked 12 November 2026:** the home page and the explorers meet WCAG 2.2
Level AA and pass the security and code validity checks
([report](security-accessibility-checks.md)).

## What is in this repository

| Path | What it is |
| --- | --- |
| `build/hub/` | The home page: `index.html`, `hub.js`, images. Built by `build/build_hub.py`. |
| `119th/index.html`, `app.js` | **The explorer template.** Every Congress's explorer is stamped from these by `build/build_congress.py`, which swaps in its name, dates and links. `119th/` is also this repository's own Pages preview. |
| `build/` | The pipeline: harvesting, parsing, rendering, OCR, building and publishing. |
| `data/rosters/` | Who served in each Congress, 106th to 119th, with their dates. |
| `harvest/` | Per-Congress harvest inputs and logs; the letter files themselves are not tracked. |
| `vocabulary/` | The Letters from Congress vocabulary of subjects. |
| `METHODOLOGY.md`, `EXPLORERS.md` | The method behind each step, and how to run and publish it. |

The built sites are not here: each lives in its own repository.

## Building and publishing

`EXPLORERS.md` has every step and its checks. In short, from a checkout with
the harvest data in place:

```bash
python3 build/build_congress.py 106-119 --copy-thumbs   # one explorer per Congress, into ../explorers/
python3 build/export_csv.py                             # each explorer's Download data CSV
python3 build/build_hub.py                              # the home page
build/publish_explorers.sh                              # publish to Robin-IA, then build/publish_iac.sh to IAC
```

On the Mac this runs unattended: `build/auto_publish.sh` merges the PC's
returns as they arrive and republishes both accounts after each merge or 300
new thumbnails, beside `build/thumbs_loop.sh` (rendering) and
`build/ocr_letters.py --watch` (OCR). `CLAUDE.md` has what that means for
changes merged here.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # pinned; pypdfium2 and pillow render, pypdf reads dates and text
python3 -m unittest discover -s tests
```

### Members who left during the Congress

`harvest.py` builds its roster from `legislators-current.json`, so a member who
resigned, died or moved to another post during the Congress is not in it.
They are harvested from a roster of their own:

```bash
python3 build/harvest.py --members-in data/congress119-departed.json \
  --out data/letters-119-departed.jsonl \
  --members-out data/congress119-departed-queried.json --workers 3
python3 build/parse_urls.py --raw data/letters-119-departed.jsonl \
  --members data/congress119-departed.json \
  --out data/letters-119-departed-parsed.jsonl
```

`build_congress.py` reads `data/letters-119-departed-parsed.jsonl` beside the
other harvests. The roster carries each member's `left` date: the explorer
shows them as "Left office", gives an end year rather than "present", and
links their site to the Wayback Machine's copy from the day they left,
because the address usually belongs to someone else by now.

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

They are WebP at quality 72, named by capture digest, and each explorer serves
its own from its repository's `thumbs/`, under that repository's 1 GB Pages
limit. A letter's thumbnail is stored once, in the one explorer that holds the
letter. Moving them to an archive.org item would be the way past that limit,
and is blocked on an unexplained fault: a zip uploaded to the item returns
200 and never appears. See `CLAUDE.md`.

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
- **Each letter is in one explorer**, the Congress in session on its date. A
  letter dated before a member's first Congress, or from an address another
  member held, is credited by the rules in `EXPLORERS.md` and `METHODOLOGY.md`,
  and flagged where it is an inference.

`build/ia_search.py` is vendored from `collection-analysis` and carries that
project's notes on these endpoints.
