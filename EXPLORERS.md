# Building the per-Congress explorers

Instructions for building one explorer per Congress, and the federated
explorer that sits over all of them. Written for whoever runs the build,
usually Claude Code. **Started 9 November 2026.** The methodology behind each
step is in `METHODOLOGY.md`. This file says how to run the steps and publish
the results.

## The repositories

| Repository | What it is |
| --- | --- |
| `Robin-IA/Congressional-Letters-Dev` | **The development repository.** Methodology, scripts, data, tests, decisions and issues all live here. Everything is tested here first, then published out to the explorers. |
| `Robin-IA/Explorer-Congressional-Letters-<N>` | **One explorer per Congress**, e.g. `Explorer-Congressional-Letters-119`. Built output only: never edited by hand, always published from dev by script. Public, because Pages needs it, and started with fresh history. |
| Federated explorer (name to be decided) | One explorer over all of them: lists the Congresses, searches across every explorer, has member pages spanning a career. Developed separately; requirements below. |

- **Everything is built under Robin-IA first, for testing.** Nothing goes to
  `internetarchivecanada` until Robin says so.
- **Creating a repository is Robin's call.** Ask before creating each new
  `Explorer-Congressional-Letters-<N>` repository. Publishing to one that
  already exists is routine.
- **Decisions and issues are recorded in Congressional-Letters-Dev.**
  Decisions go in the table below, with their date. Issues are filed there,
  never in an explorer repository.

## Decisions

| Date | Decision |
| --- | --- |
| 2026-11-09 | One explorer per Congress, plus a federated explorer that links them and searches across all of them. |
| 2026-11-09 | Congressional-Letters-Dev stays the development repository; the explorers are published from it. |
| 2026-11-09 | New explorer repositories start fresh, without the dev repository's history. |
| 2026-11-09 | Built under Robin-IA for testing, not internetarchivecanada. |
| 2026-11-09 | Repository names follow `Explorer-Congressional-Letters-<N>`, where N is the Congress number. |
| 2026-11-09 | Thumbnails are WebP, quality 72, **200 px wide** (PR #21). 340 px filled the 1 GB Pages limit; 200 px holds about 160,000. |
| 2026-11-09 | The letter PDFs are not hosted. Every letter opens from the Wayback Machine. |
| 2026-11-09 | A letter dated between two holders of an address goes to the earlier holder, flagged `after_service`, unless that member was still in office in the same chamber (step 3). |
| 2026-11-09 | The methodology is written before any new explorer is published. |
| 2026-11-09 | **Each letter appears in exactly one explorer: the Congress in session on the letter's date.** No letter or thumbnail is stored twice. The alternative, every letter of a Congress's members, would repeat a long-serving member's letters in every Congress they served. |

## The pipeline for Congress N

Steps 1–3 are done for the 106th–119th. Step 3 runs over every Congress at
once, because an address can pass between holders across Congresses. Its
output is then divided by Congress at step 7.

### 1. Roster

```bash
python3 build/congress_roster.py N
```

- Writes `data/rosters/congressN-roster.csv`, everyone who served any part of
  Congress N. A closed Congress's roster is built once and not rebuilt
  (`--rebuild` only to correct a known error, named in the commit).
- **Check:** 540–560 rows, and the script's count of members with no URL.
  Each member with no URL gets an issue to look for one in Wayback (rule in
  `METHODOLOGY.md` step 1).
- Before 2003 the source has few URLs. Run `build/directory_urls.py N` first
  so the roster can use the chambers' own member directories.

### 2. Find each member's site in the Wayback Machine

```bash
python3 build/wayback_lookup.py N
```

- One lookup per address, bounded to the member's own service. Writes
  `harvest/wayback/congressN-wayback.csv`.
- **Check:** every member confirmed at one address at least. Each one not
  confirmed gets an issue.
- Use `https://` for CDX. Over `http://` it has answered 503 for whole runs.

### 3. Who held each address, and when

```bash
python3 build/address_holders.py
python3 -m unittest discover -s tests
```

- Rebuilds `data/address-holders.csv` from every roster and lookup. It must
  report `0 overlaps`.

### 4. Find the letters at each address

**Not yet a script of its own.** Until it is, `build/harvest.py` does the
querying for hostnames:

```bash
python3 build/harvest.py --members-in harvest/letters-<range>-members.json \
  --members-out harvest/letters/members-<range>.json \
  --out harvest/letters/letters-raw-<range>.jsonl \
  --cache harvest/letters/cache --workers 2
```

- The members file lists the addresses to search, one per entry, built from
  `data/address-holders.csv`. Its `bioguide` is a placeholder only: who gets
  each letter is decided at step 7, not here.
- **Every address, not only those whose holder sits in Congress N.** A letter
  stays up after its author leaves, so one search per address covers every
  Congress at once.
- **Breadth first:** the newest Congresses first, and addresses with no
  letters at all before any re-run.
- **The cache holds raw CDX rows** (`harvest/letters/cache/`, not committed),
  so a change to the cleaning costs a re-filter, not a re-harvest.
- **Paths on shared hosts** (`www.house.gov/<name>`, `senate.gov/~name`) are
  not handled yet. `cdx_rows_paged` assumes a hostname. These are mostly
  before 2012.
- **One Wayback job at a time.** The harvest, the renderer and
  `resolve_wrappers.py` share the same budget.

Then reduce the raw rows to letters:

```bash
python3 build/parse_urls.py --raw harvest/letters/letters-raw-<range>.jsonl \
  --members harvest/letters/members-<range>.json \
  --out harvest/letters/letters-parsed-<range>.jsonl   # dates, recipients, subjects from the URL
python3 build/resolve_wrappers.py --cache harvest/letters/cache \
  --members harvest/letters/members-<range>.json     # Senate download wrappers; slow
```

Check each script's `--help` for the remaining options before a run; these are
the ones that keep a range's files apart from the explorer's own.

- **The corpus rule:** every letter opens as a letter. Announcement pages,
  press releases with "letter" in the URL, download wrappers and captures cut
  at 64,000 bytes are not letters (`CLAUDE.md`).

### 5. Text, for search

- **Where it comes from today:** `build/thumbs.py` downloads each PDF once, to
  render its thumbnail, and keeps the text layer of the first six pages in
  `data/letter-text.jsonl`.
  - As of 6 November: 39,830 PDFs read, 25,712 with text (65%), median 4,321
    characters, 139 MB in all.
  - It is not committed, and it is the only copy.
- **About a third are scans with no text layer.** For those, OCR is to be
  designed:
  - **Engine:** Apple's Vision framework runs on-device on the Mac and needs
    no service. Tesseract is the portable alternative.
  - **What it reads:** the renderer already holds the PDF. It would OCR a
    full-resolution render of each page, not the 200 px thumbnail.
  - **How it is recorded:** text from OCR is kept separately from text the
    PDF itself carried (`source: ocr` against `source: pdf`), because OCR
    makes errors and the text layer does not.
- **Full-text search is not built.** That is issue #1 in
  `Robin-IA/congressional-letters`. Today's search index (`payload/search.json`,
  4 MB) holds member, recipient, year and topics, but no text.
  - 139 MB of text cannot be one download.
  - Splitting by Congress helps. By the date each letter was written, today's
    text comes to 19 MB for the 116th, 30 MB for the 117th, 39 MB for the
    118th and 43 MB for the 119th, and under 5 MB for each earlier Congress.
    Those earlier figures will grow with the harvest.
  - Even that is too much to download whole. The index has to be split by
    term, so a query loads only the parts for its own words. To be designed.

### 6. Thumbnails

```bash
python3 build/thumbs.py --thumbs thumbs        # resumable; see the trap in CLAUDE.md
python3 build/publish_thumbs.py                # budget check
```

- **200 px wide, WebP quality 72.** About 6 KB each.
- Named by the PDF's digest, so a thumbnail is made once and shared. If a
  letter moves to another Congress's explorer, its thumbnail goes with it.
- **Order across members:** by position on each member's own page, so every
  member's first screen fills together.
- **Budget:** 940 MB per explorer. At 200 px the largest Congress so far, the
  118th, needs about 64 MB.

### 7. Build Congress N's explorer

**Needs changes to `build/build_site.py`.** Today it builds one explorer from
every letter on the sitting members' sites.

- **Which letters:** every letter whose date falls within Congress N, from 3
  January of its first year to 3 January two years later. Each appears in
  exactly one explorer, so no letter or thumbnail is stored twice.
  - The date is the letter's own if it has one, then the PDF's, then its first
    capture (`METHODOLOGY.md` step 4).
- **Credited by** `address_holders.attribute()`, at build time, never at
  harvest. A rebuild picks up new dates and roster fixes without a new harvest.
- **Members:** everyone on Congress N's roster, with a count of zero where no
  letters were found. A member credited only with `after_service` letters is
  listed separately as a former holder (open, below).
- **Output:** `index.json`, `payload/member/<id>.json`,
  `payload/search.json`, and the thumbnails for the letters in N, written into
  a working copy of `Explorer-Congressional-Letters-<N>`.
- **Totals are derived from the data at build time**, never typed in.

**What the page looks like:** the live Letters from Congress explorer, with:

- **The Congress named in the header:** "119th Congress", with its dates,
  "January 3, 2025 – January 3, 2027". The live page's crumb reads "119th
  Congress (2024-26)", which is wrong: the 119th began in 2025.
- **Links to the previous and next Congress**, and one to the federated
  explorer, in place of the crumb's current `../` link.
- **A line saying what the explorer holds**, from `index.json`: letters
  written during this Congress, by the members who held each site at the time.
  Until the earlier Congresses are built, the 119th's explorer holds every
  letter from 2000 on, and must say so.
- Nothing else changes. Same app, same cards, same member pages. A click still
  opens the letter in Wayback.

### 8. Publish

1. Build into a working copy of `Explorer-Congressional-Letters-<N>`. Its
   `thumb_base` is `thumbs/` and the page loads `app.js` from the same
   repository, until the shared-app question below is settled.
2. **Bump `app.js?v=` in `index.html`** whenever `app.js` changes. Every file
   a build rewrites carries `index.json`'s `stamp`. These are the
   caching traps in `CLAUDE.md`.
3. Commit and push. That publishes it on Pages.
4. **Check the live site, not the working copy:**
   - `index.json` from Pages has the new `stamp`.
   - Five member pages open and list letters.
   - Twenty thumbnails return 200 and are 200 px wide.
   - One letter opens in Wayback.
5. Record the publish in this repository: the date, the Congress, the stamp,
   and the counts.

## Issues

- **Filed in Congressional-Letters-Dev.** An issue that goes with a PR is
  opened without asking. One that needs investigating, or that only Robin can
  fix, is filed and the work moves on, as agreed on 8 November.
- **Each step's checks name what gets an issue:**
  - a member with no URL (step 1);
  - a member not confirmed in Wayback (step 2);
  - an overlap in the holders table (step 3);
  - an address that will not enumerate (step 4).
- **Issues are worked after the explorer they affect is built**, unless they
  block it.

## The federated explorer: requirements so far

To be developed separately. What it has to do, as discussed on 9 November:

- **List every Congress** with its dates and counts, read from each
  explorer's `index.json`. Counts are computed by the federated explorer from
  what it loads, never typed or added up from another source.
- **Search across every explorer.**
  - It loads each Congress's search index and shows results as they arrive,
    newest Congress first, each linking into its own explorer.
  - When the number of Congresses makes that heavy, it switches to one
    combined index built at publish time.
- **Member pages that span a career.** A member who served several Congresses
  appears in each of their explorers. The federated explorer gathers them on
  one page.
- **Views that cross Congresses** live only here: a recipient over 25 years,
  topics over time, the year pages.
- **The same origin:** all of it is served from `robin-ia.github.io`, so it
  can read every explorer's data and images directly.

## Open

- **Letters from a member's earlier office**: 428 letters dated before their
  address's first holder (`METHODOLOGY.md` step 4).
- **Caucus subdomains**: 256 letters on sites like `rsc.jordan.house.gov`.
- **A letter credited `after_service` to someone not on Congress N's
  roster**: list them in N's explorer as a former holder, or only in the
  federated explorer.
- **One shared `app.js` or a copy per explorer.**
  - Shared: a fix lands everywhere, but it also changes closed Congresses.
  - Copied: copies drift apart, and the caching trap repeats per repository.
- **OCR engine and the full-text index format** (step 5).
- **Harvesting paths on shared hosts** (step 4).
- **The federated explorer's repository name.**
