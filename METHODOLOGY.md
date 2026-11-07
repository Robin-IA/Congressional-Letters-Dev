# Methodology

How the corpus is assembled, step by step. **Revised 7 November 2026.** The
work now starts from who served in each Congress and works outward from there,
rather than from the websites the chambers happened to list.

Each step's output is the next step's input. Steps 3 and 4 are still to be
designed. They are listed so the order is clear, not because they are settled.

| Step | What | Output | State |
| --- | --- | --- | --- |
| 1 | Roster for each Congress | `data/rosters/congressNNN-roster.csv` | **done, 110th–119th** |
| 2 | Find each member's site in the Wayback Machine | `harvest/wayback/congressNNN-wayback.csv` | **running, 110th–119th** |
| 3 | Flag URLs used by more than one member | | to design |
| 4 | Find the letters on each site | | to design |

---

## Step 1: the roster

**The first step is always the same: build the roster for the Congress, one CSV
per Congress, including everyone who served any part of it.**

```bash
python3 build/congress_roster.py          # add any missing roster; refresh the sitting Congress
python3 build/congress_roster.py 120      # add the 120th when it convenes
```

**Rosters are built once and then added to; they are not rebuilt.** Once a
Congress has ended, its roster is fixed. The script skips any closed Congress
whose file already exists, and says so. Going forward the work is adding:

- the sitting Congress is refreshed as members join and leave it
- each new Congress gets its own roster when it convenes
- later steps add their results alongside a roster, never by regenerating it

`--rebuild` rewrites a closed roster. Use it only to correct a known error, and
say what was corrected in the commit.

A fixed roster is a record of who served in that Congress, which does not
change. Three columns describe a member's career beyond it, and they are only
true as of the day the roster was built: `years_in_office` ("…present"),
`total_years_in_congress`, and `service_notes` such as "left Congress 2025-01-03".
The 110th–118th rosters were built on 7 November 2026.

Stdlib only. It downloads `legislators-current.json` and
`legislators-historical.json` from
[`unitedstates/congress-legislators`](https://github.com/unitedstates/congress-legislators)
each run (`--source-dir` reads saved copies instead).

### Who is on it

Everyone with a term that overlaps the Congress's dates (3 January to
3 January). That includes:

- members who served the whole Congress
- **members who served part of it**: those who joined by special election or
  appointment, and those who resigned, died, were appointed elsewhere or
  switched chamber partway through

A partial term is marked `partial` and dated in `service_notes`, for example
`left 2008-11-16 (during this Congress)`. A member who switched chamber
mid-Congress appears once, under the chamber they ended in.

### What it records

| Column | |
| --- | --- |
| `name`, `bioguide_id` | The bioguide ID is the key. Names repeat: two Mike Rogers, two Patrick Murphys, two Robert Menendezes |
| `party` | Party during this Congress, with any switch dated |
| `state`, `chamber`, `district` | |
| `website_at_the_time` | The URL recorded on the member's terms in this Congress |
| `served_this_congress`, `days_this_congress` | First and last day served, and the length of that span |
| `full_or_partial` | |
| `service_notes` | Joined/left dates, and later career events |
| `years_in_office` | Career periods by chamber |
| `total_years_in_congress` | Whole career, both chambers |

**The URL is recorded exactly as published, in whatever form.** Through the
2000s most representatives were at `www.house.gov/<name>`, not on a subdomain.
Those are kept as they are, because step 2 looks each one up in the Wayback
Machine and needs the URL as it was at the time. A member whose URL changed
during the Congress has both, separated by `|`.

### Where the source falls short

- **No URL recorded.** Across the 110th–119th, 17 rows have no URL for that
  term in the source. Each row's `service_notes` says how its URL was
  filled:
  - **11 special-election members** take the URL from their next term
    ("URL not in dataset for this term; taken from next term").
  - **5 come from Wayback evidence** ("URL not in dataset; …"), listed in
    `URL_OVERRIDES` in the script. Mayra Flores's is inferred.
  - **1 has no URL at all**: Carte Goodwin (111th, appointed July to
    November 2010).

  **Rule: every member with no URL gets an issue to check Wayback for one,
  worked after the initial explorer is built.** Goodwin's is
  [#10](https://github.com/Robin-IA/Congressional-Letters-Dev/issues/10).
  The 16 filled URLs are checked by step 2, which looks each one up within
  that member's own service. Any that step 2 cannot confirm get an issue of
  their own.
- **Why someone left is not recorded**, only when.
- **Career totals can run up to about two years high** for members who first
  entered by special election long ago. The source dates those first terms from
  the day that Congress convened. Dates within the 110th–119th are exact.
- **The sitting Congress is a snapshot.** Day counts run to the build date, and
  results the source has not yet recorded are said to be pending. In the
  119th, the results of Moody's and Husted's 3 November 2026 special elections
  are still pending.

### Check before using a roster

Each Congress should come to roughly 540–560 rows: 535 seats, plus delegates,
plus anyone who replaced someone mid-session. The script prints the count, the
number of partial terms and the number with no URL. On 7 November 2026:

| Congress | Members | Partial | No URL |
| --- | ---: | ---: | ---: |
| 110th | 554 | 30 | 0 |
| 111th | 559 | 36 | 1 |
| 112th | 552 | 27 | 0 |
| 113th | 554 | 26 | 0 |
| 114th | 547 | 15 | 0 |
| 115th | 561 | 43 | 0 |
| 116th | 550 | 25 | 0 |
| 117th | 557 | 40 | 0 |
| 118th | 554 | 31 | 0 |
| 119th | 555 | 32 | 0 |

---

## Step 2: find each site in the Wayback Machine

```bash
python3 build/wayback_lookup.py          # every roster in data/rosters/
python3 build/wayback_lookup.py 118      # one Congress
```

For each roster row, this asks the Wayback Machine whether it holds the home
page of `website_at_the_time` **during that member's own service in that
Congress**. It writes `harvest/wayback/congressNNN-wayback.csv`: one row per
member per URL, with the number of days captured, the first and last capture,
and a Wayback link to each.

**Everything harvested goes under `harvest/`**, beside the rosters, never into
them. The raw CDX answers are cached in `harvest/wayback/cache/`, which git
ignores. A re-run asks Wayback only for what it does not have, so an
interrupted run is resumed by running it again.

### Why every lookup is bounded

Surname hostnames are reused. An unbounded "last capture" of `jones.house.gov`
is Mondaire Jones's 2023 site, not Walter Jones's. Every query carries `from`
and `to` set to `served_this_congress`, so a capture can only come from the
member's own time in office.

### How a capture is counted

- The home page is queried first: `pelosi.house.gov/`, or `www.house.gov/pelosi/`
  for the older path-style sites. If that has no successful capture in the
  window, a prefix query over the whole site follows. The `query` column says
  which one answered.
- **No `filter=` and no negative `limit` are sent to CDX.** Used together, they
  returned captures years older than the true last one: Conaway's came back as
  2012 against a real December 2020. Every capture in the window is fetched,
  collapsed to one per day, and success (status 200, HTML) is decided locally.
- **A redirect capture of the home page counts.** Many home pages only ever
  answered 302 into the site. Shelby's did on 154 of 155 captured days in the
  110th, so a count of 200s alone reported one day. Wayback follows the
  redirect inside the archive (that capture opens "United States Senator
  Richard Shelby : Home"). `days_200` and `days_redirect_only` keep the two
  apart.
- `lookup` is `found`, `none in window`, `no URL in roster` or `error`.
  Errors are not cached, so the next run retries them.

### Checked before the full run (7 November 2026)

A trial of eight members whose answers were known landed every capture inside
the member's window. Three were opened by page title:

- Walter Jones: `jones.house.gov`, last capture 2019-01-02, titled "Congressman Walter Jones"
- Nancy Pelosi: `www.house.gov/pelosi`, 2009-01-02, "Congresswoman Nancy Pelosi, California, 8th District"
- Stephanie Murphy: `murphy.house.gov`, 2020-12-31, "Stephanie Murphy"

The first two are cases the unbounded lookup got wrong or could not express.

## Steps 3–4: to design

Recorded so they are not lost; neither is decided.

- **Reused URLs (step 3).** Surname hostnames are reassigned: `jones.house.gov`
  was Walter Jones, then Mondaire Jones. Across Congresses, the rosters show
  who held each URL and when. See issues
  [#7](https://github.com/Robin-IA/Congressional-Letters-Dev/issues/7) (letters
  credited to the wrong member) and
  [#8](https://github.com/Robin-IA/Congressional-Letters-Dev/issues/8) (the URLs
  themselves).
- **Letters (step 4).** The harvest in `BACKFILL.md` and `build/harvest.py`,
  driven by roster rows rather than by the chambers' website directories.

## How this relates to the earlier approach

`BACKFILL.md` and `build/chamber_rosters.py` start from the House and Senate
member directories as archived each year (`data/member-sites.tsv`): a list of
websites, with people attached where possible. The House directory never
stated a bioguide ID, so many of those rows name a site rather than a person.
Starting from the roster turns that around. Every row is a person with a
bioguide ID and service dates, and the website is an attribute of that person
for a span of time. `member-sites.tsv` remains useful as a second source of
URLs in step 2.
