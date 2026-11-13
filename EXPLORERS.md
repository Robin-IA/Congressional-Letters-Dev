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
| `Robin-IA/Explorer-Letters` | **Letters from Congress, the home page** over all of them: lists the Congresses, searches across every explorer. Built by `build/build_hub.py`; requirements below. |
| `internetarchivecanada/Explorer-Congressional-Letters-<N>`, `internetarchivecanada/congressional-letters` | **The same sites on Internet Archive Canada**, published from the same build every time (`build/publish_iac.sh`). The home page there is `congressional-letters`, the address the first explorer was published at. |

- **Everything is built under Robin-IA first, then published to
  `internetarchivecanada` from the same build.** Robin approved publishing to
  Internet Archive Canada on 12 November 2026.
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
| 2026-11-09 | A letter dated before an address's first holder goes to that holder, flagged `earlier_office`, when they were already in Congress. That keeps 428 of today's letters; 67 still have no holder. |
| 2026-11-09 | Letters on a caucus subdomain (`cpc.grijalva.house.gov`, `rsc.jordan.house.gov`) go to the parent address's holder, flagged `caucus`, and are **kept in the data but not published** (`UNPUBLISHED` in `build/address_holders.py`) until #24 is done. 255 rows, 126 distinct documents. About half the RSC's are letters to the caucus from outside groups. |
| 2026-11-09 | Committee letters are wanted, credited to the chair as of the letter's date. Not yet harvested (#23). |
| 2026-11-09 | **Each letter appears in exactly one explorer: the Congress in session on the letter's date.** No letter or thumbnail is stored twice. The alternative, every letter of a Congress's members, would repeat a long-serving member's letters in every Congress they served. |
| 2026-11-12 | The federated explorer is **Letters from Congress**, repository and folder **`Explorer-Letters`**, published beside the explorers so `../Explorer-Congressional-Letters-<N>/` reaches each one. Each explorer's "All Congresses" link goes to `../Explorer-Letters/`. Built by `build/build_hub.py`. Not `Letters-from-Congress`: under Robin-IA that name still forwards to the private `internetarchivecanada/letters-from-congress`, which it was moved to, and reusing it would break that forwarding. |
| 2026-11-12 | **Images are public domain, from Wikidata or Wikimedia Commons**, or our own thumbnails of the letters. Before one is used: its license is read on its Commons page (public domain or CC0), its credit line is shown as the source asks, and the page and the commit name the file. Self-hosted, never hot-linked. The first is the home page's banner, *East Front of the U.S. Capitol at Sunrise* (Architect of the Capitol, public domain; their terms ask for the credit "Architect of the Capitol" and no implied endorsement). Wikidata's own image for the Capitol (Q54109, P18) is a different public-domain photograph of the West Front. |
| 2026-11-12 | Letter subjects use **a controlled vocabulary of their own, the Letters from Congress vocabulary** (`vocabulary/`, built by `build/build_vocabulary.py`): members by Bioguide ID with Wikidata, the organizations and people letters are written to, and topics. Started from what the letters already carry; the words inside the letters are added once the OCR is done. Not LCSH, which is not robust enough for letters. Unreviewed terms and every searched-for Wikidata match are `candidate`, never fact (#40). |
| 2026-11-12 | **Published to Internet Archive Canada** as well as Robin-IA, at Robin's request: 14 explorer repositories under `internetarchivecanada`, and `congressional-letters` replaced by the home page as a new commit on its history, keeping forwarding for its old links. Every publish now goes to both (`publish_iac.sh`, PR #61). |
| 2026-11-12 | **The explorer template moved onto the main line** (`119th/index.html`, `app.js`), from `iac-119th`, a branch on one laptop, so fixes to the explorers go through review (PR #59). |
| 2026-11-12 | Ambiguous two-digit-year filename dates are read the way that fits the capture and the member's first year (PR #60, fixing #58). |
| 2026-11-12 | **Every explorer says it covers only its own Congress**, and sends readers to the home page's search and By topic list for all of a member's letters. Asked for on every explorer, not explained on the 119th alone. |
| 2026-11-12 | **A date nobody holding the address could have written on is set aside for the capture.** If a letter's date (from its filename or its PDF's metadata) finds no holder of the address, or a holder not in that Congress, and its capture does, it is placed and shown by its capture ("captured by"). This covers PDF dates that are a template's creation date and filename dates that were misread. Checked against the original 72,897 letters: 72,655 are now in an explorer. The other 242 are the 201 caucus letters (unpublished, #24) and 41 from 2008–2012 House sites missing from the address-holders table (taylor, miller, bean, jackson, barrett). |
| 2026-11-12 | **Hosts a roster does not name come from `data/website-aliases.csv`**, hand-kept, each row with the capture that shows who held the host, and only for the Congresses that evidence covers. The rosters gave `www.house.gov/<name>` for members whose letters sit on `<name>.house.gov`. The first five (Gene Taylor, Melissa Bean, Jesse Jackson Jr., Gresham Barrett, Gary Miller) placed 40 more original letters: 72,695 of 72,897 are in an explorer. What is left is the 201 caucus letters and one letter dated after its holder left. |
| 2026-11-12 | **Caucus letters are credited to the chair and tagged with the caucus** (Robin), for every caucus whose name its own site or letters confirm: `CAUCUSES` in `build/address_holders.py`, 10 caucuses, 124 letter rows. **The RSC is held** (#76): its host is not the letter's chair (rsc.scalise carries letters from before Scalise), and many of its letters are to it, not from it. Also held: five small hosts not yet named or not caucuses. 310 letters in all. |
| 2026-11-12 | **A letter re-posted by a later holder of the same address is theirs.** When the date falls between two holders and the earlier one was not serving, but the next holder was serving on the date and the letter was captured during their tenure, it is the next holder's `earlier_office` letter, not the earlier holder's `after_service` one. Found on levin.house.gov: Mike Levin's letters, dated in 2019, were being attributed to Sander Levin. |
| 2026-11-13 | **Every member is listed, letters or not, and each links to their website as the Wayback Machine archived it during that Congress** (#79). The link and the day count come from the home-page lookup in `harvest/wayback/congress<N>-wayback.csv`. A member page says the site was **searched** only when a harvest queried its address (`searched_addresses()` in `build_congress.py`, from the harvest caches); otherwise it says the site was archived but not yet searched. On 13 November that is 192 of the 524 members with no letters in the 106th and 56 of the 474 in the 107th (three more in the 110th and 119th), whose `house.gov/<name>` and `senate.gov/~name` paths no harvest has reached. |
| 2026-11-13 | The home page's menu is **Home · By topic · By member · By Congress**; the Wayback Machine link is gone from it (the page still credits and links the Wayback Machine in its text). **By member** (`?view=by-member`) lists every member of every Congress the explorers cover, letters or not, with years served, party, state and letters, gathered from the explorers' `index.json`; a member opens to their Congresses, each linking to that explorer's member page. Not `?view=members` or `?member=`: on the Internet Archive Canada address those are old 119th-explorer links and are forwarded there (`publish_iac.sh`). By topic links to it from its note and from the Members of Congress branch. |
| 2026-11-13 | The home page's vocabulary view is headed **By topic or Congress Member**, and its categories carry **no count of terms**; a term still shows its letters. Roster parties are corrected at the source script, not by hand: `congress_roster.py` has `PARTY_CORRECTIONS`, keyed by Bioguide ID and term start, each with the Biographical Directory's wording as evidence. The first: Aníbal Acevedo-Vilá (A000359), 107th, where congress-legislators gives "AL" and Bioguide says "elected as a Popular Democrat to the One Hundred Seventh Congress". |

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
- **Paths on shared hosts** (`www.house.gov/<name>`) go through their own
  harvest, because `cdx_rows_paged` assumes a hostname. Mostly before 2012.
  - `build/harvest_paths.py` queries the 435 House paths in
    `data/member-sites.tsv` into `data/letters-paths.jsonl`. Run on 12
    November 2026: 1,616 letters from 174 of the 435.
  - `build/paths_letters.py`, then `parse_urls.py`, turns them into
    `harvest/letters/letters-parsed-paths.jsonl`, which `build_congress.py`
    reads with the rest. Each is credited to whoever held the path on its
    date, from the rosters: 1,561 credited, 55 to no one. The name match in
    `harvest_paths.py` itself had credited 138.
  - **Still missing:** Senate paths (`senate.gov/~name`). `member-sites.tsv`
    has none, and the five tried by hand, Thurmond and Helms among them,
    returned nothing.
  - **Expect few.** Sites of that era rarely put "letter" in a URL. Hastert's
    `house.gov/hastert` has 842 captures and no letter: its 24 PDFs are forms
    and flyers.
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
- **Left out:** attribution `none`, and `caucus` letters on a caucus not in
  `CAUCUSES` (`build/address_holders.py`; #76). They stay in the data, so a
  decision to publish them is a rebuild, not a harvest.
- **Caucus letters** on a named caucus are published under the chair whose
  site hosts them, with the caucus as a topic.
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

1. Build: `build_congress.py N --copy-thumbs`, `export_csv.py`, `build_hub.py`.
   Each explorer is built into its working copy in `../explorers/`; its
   `thumb_base` is `thumbs/` and it carries its own `app.js`, stamped from
   the template.
2. **Bump `app.js?v=` in `119th/index.html`** whenever `app.js` changes.
   Every file a build rewrites carries `index.json`'s `stamp`. These are the
   caching traps in `CLAUDE.md`.
3. Publish: `build/publish_explorers.sh` commits and pushes each explorer and
   the home page to Robin-IA, then runs `build/publish_iac.sh`, which
   publishes the same build to Internet Archive Canada. On the Mac,
   `build/auto_publish.sh` runs all of this unattended.
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

## Published

**Since 12 November every publish goes to both accounts**, Robin-IA and
Internet Archive Canada, from the same build; `~/ia/explorers/publish.log`
records each one. The table below is the first publish, kept as a record.

**12 November 2026, first publish**, under Robin-IA, from the build of 11:59.
Every repository is public, with Pages serving `main` from its root. They
include the thumbnails rendered so far; rendering continues, and each is
republished as it fills in: rebuild, `export_csv.py`, `build_hub.py`, push.

Home page: <https://robin-ia.github.io/Explorer-Letters/>, 112,201 letters
from 1,244 members across 14 Congresses, as the page computes it.

| Congress | Repository | Stamp | Letters | Members with letters | Thumbnails |
| --- | --- | --- | ---: | ---: | ---: |
| 106th | [`Explorer-Congressional-Letters-106`](https://robin-ia.github.io/Explorer-Congressional-Letters-106/) | 20261112115906 | 41 | 17 of 544 | 21 |
| 107th | [`Explorer-Congressional-Letters-107`](https://robin-ia.github.io/Explorer-Congressional-Letters-107/) | 20261112115906 | 408 | 74 of 550 | 85 |
| 108th | [`Explorer-Congressional-Letters-108`](https://robin-ia.github.io/Explorer-Congressional-Letters-108/) | 20261112115906 | 1,010 | 166 of 544 | 333 |
| 109th | [`Explorer-Congressional-Letters-109`](https://robin-ia.github.io/Explorer-Congressional-Letters-109/) | 20261112115907 | 2,583 | 224 of 545 | 436 |
| 110th | [`Explorer-Congressional-Letters-110`](https://robin-ia.github.io/Explorer-Congressional-Letters-110/) | 20261112115907 | 2,292 | 258 of 554 | 787 |
| 111th | [`Explorer-Congressional-Letters-111`](https://robin-ia.github.io/Explorer-Congressional-Letters-111/) | 20261112115907 | 5,220 | 379 of 559 | 1,717 |
| 112th | [`Explorer-Congressional-Letters-112`](https://robin-ia.github.io/Explorer-Congressional-Letters-112/) | 20261112115908 | 5,926 | 399 of 552 | 2,457 |
| 113th | [`Explorer-Congressional-Letters-113`](https://robin-ia.github.io/Explorer-Congressional-Letters-113/) | 20261112115909 | 6,932 | 448 of 554 | 3,735 |
| 114th | [`Explorer-Congressional-Letters-114`](https://robin-ia.github.io/Explorer-Congressional-Letters-114/) | 20261112115911 | 7,926 | 467 of 547 | 4,795 |
| 115th | [`Explorer-Congressional-Letters-115`](https://robin-ia.github.io/Explorer-Congressional-Letters-115/) | 20261112115913 | 11,506 | 468 of 561 | 6,817 |
| 116th | [`Explorer-Congressional-Letters-116`](https://robin-ia.github.io/Explorer-Congressional-Letters-116/) | 20261112115915 | 20,014 | 502 of 550 | 10,633 |
| 117th | [`Explorer-Congressional-Letters-117`](https://robin-ia.github.io/Explorer-Congressional-Letters-117/) | 20261112115919 | 20,601 | 523 of 557 | 11,712 |
| 118th | [`Explorer-Congressional-Letters-118`](https://robin-ia.github.io/Explorer-Congressional-Letters-118/) | 20261112115924 | 16,324 | 486 of 554 | 11,931 |
| 119th | [`Explorer-Congressional-Letters-119`](https://robin-ia.github.io/Explorer-Congressional-Letters-119/) | 20261112115927 | 11,418 | 484 of 555 | 9,725 |

Checked live: each `index.json` carries its build's stamp; five member pages
and the 118th's CSV load; thumbnails return 200 in five explorers sampled;
Elizabeth Warren's 118th page shows her 727 letters and opens each from
Wayback; the home page's search for "FEMA" finds 866 letters across 14
Congresses, linking into the right explorer.

## The federated explorer: requirements so far

What it has to do, as discussed on 9 November. **The first version was built
on 12 November** (`build/build_hub.py`, page in `build/hub/`): it lists every
Congress and searches across them, loading each explorer's `search.json`
newest first, and gathers a member's Congresses into one card. Search matches
subject, recipient, topics and member names, as the explorers' own search
does; full text waits for the OCR and an index. Career pages and the
cross-Congress views below are not built yet. PR #25 is an earlier mockup of
the same page, from the 119th's data alone.

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

- **Caucus letters** (#24, #76): the RSC and five small hosts are still held. What it takes to publish the RSC: Drop outside groups' letters to the RSC, dedupe it across its two hosts, and credit the chair on the letter's date.
- **Committee letters** (#23): rosters of committee sites and of their chairs and ranking members, then a harvest.
- **A letter credited `after_service` to someone not on Congress N's
  roster**: list them in N's explorer as a former holder, or only in the
  federated explorer.
- **One shared `app.js` or a copy per explorer.**
  - Shared: a fix lands everywhere, but it also changes closed Congresses.
  - Copied: copies drift apart, and the caching trap repeats per repository.
- **OCR engine and the full-text index format** (step 5).
- **Senate paths on shared hosts** (`senate.gov/~name`, step 4). The House paths are done.
