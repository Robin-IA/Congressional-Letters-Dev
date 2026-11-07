# Methodology

How the corpus is assembled, step by step. **Revised 7 November 2026.** The
work now starts from who served in each Congress and works outward from there,
rather than from the websites the chambers happened to list.

Each step's output is the next step's input. Steps 2 and later are still being
designed and are listed so the order is clear, not because they are settled.

| Step | What | Output | State |
| --- | --- | --- | --- |
| 1 | Roster for each Congress | `data/rosters/congressNNN-roster.csv` | **done, 110th–119th** |
| 2 | Find each member's site in the Wayback Machine | | to design |
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

- **No URL recorded**: Five members' URLs come from Wayback evidence
  instead, and each row says how it was established. They are listed in
  `URL_OVERRIDES` in the script. Carte Goodwin (111th, appointed July to
  November 2010) has no URL at all.
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

## Steps 2–4: to design

Recorded so they are not lost; none is decided.

- **Wayback lookup (step 2).** For each roster row, look up
  `website_at_the_time` in CDX, **bounded to the member's own service dates**.
  An unbounded lookup can return a later member's site at the same address.
  `www.house.gov/<name>` URLs need a path-prefix query, not a host query
  (see `BACKFILL.md` §8). An earlier pass did this for the 113th–118th; its
  results are in git history at commit `b8c646b93`
  (`data/congressNNN-members.csv`).
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
