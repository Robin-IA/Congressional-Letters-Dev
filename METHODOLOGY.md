# Methodology

How the corpus is assembled, step by step. **Revised 7 November 2026.** The
work now starts from who served in each Congress and works outward from there,
rather than from the websites the chambers happened to list.

Each step's output is the next step's input. Step 4 is designed but not built.

| Step | What | Output | State |
| --- | --- | --- | --- |
| 1 | Roster for each Congress | `data/rosters/congressNNN-roster.csv` | **done, 106th–119th** |
| 2 | Find each member's site in the Wayback Machine | `harvest/wayback/congressNNN-wayback.csv` | **done, 106th–119th** |
| 3 | Who held each address, and when | `data/address-holders.csv` | done, 106th–119th |
| 4 | Find the letters at each address | `data/letters-parsed.jsonl` | designed, not built |

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
The 110th–118th rosters were built on 7 November 2026, and the 106th–109th on
8 November 2026, which takes the rosters back to 1999 and so covers the year 2000.

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

- **Before 2003 the source records almost no URLs.** In the 106th Congress
  (1999–2001), 459 of 544 members have none. For those Congresses the roster
  uses what the chambers themselves published at the time:
  - `build/directory_urls.py` reads the House member directory
    (`www.house.gov/house/MemberWWW.html`, later `.shtml`, which is 404 from
    2012; from 2011 `www.house.gov/representatives/`, a table per state that
    files American Samoa as `state_aq`) and the Senate's
    (`www.senate.gov/senators/index.cfm`, which redirects from November 2002,
    so there are no Senate listings from the 108th on), one Wayback capture a quarter
    across each Congress. It writes `data/rosters/directory-urls-NNN.tsv`:
    every listed URL, with the dates it was seen.
  - A member with no URL in the source takes the URL listed for their seat
    (chamber, state, district) under their surname. The note reads "listed in
    the House member directory as archived 19990219–20001206". A site that
    moved during the Congress gives both URLs, in order, joined by `|`.
  - This comes before borrowing the next term's URL, because a listing from
    the time is better evidence than a later term.
  - **Sources by row:**

    | Congress | From the source | From the directory | From the next term | None |
    | --- | ---: | ---: | ---: | ---: |
    | 106th | 33 | 509 | 0 | 2 |
    | 107th | 66 | 481 | 2 | 1 |
    | 108th | 544 | 0 | 0 | 0 |
    | 109th | 500 | 45 | 0 | 0 |

    The directory is read for the 106th–112th. In the 110th–112th it supplies
    no member's only URL, just the second addresses below; the 113th–119th do
    not use it.
  - The directory has its own traps. A member with no site was linked back
    into the directory itself (`Member.htm#il02`), and a seat left vacant was
    linked to the Clerk's vacancy page. Neither is taken as a member's URL.
    Step 2 checks every directory URL inside the member's own service.
  - **Where the source and the directory disagree, both are kept.** A
    member's site often moved within a Congress (`www.house.gov/name` to
    `name.house.gov`, `www.senate.gov/~name` to `name.senate.gov`), and the
    source records one address. Letters were published at whichever was live,
    so every address the directory lists for the seat and surname is added
    after the source's, and step 2 looks up each
    ([#16](https://github.com/Robin-IA/Congressional-Letters-Dev/issues/16)).
    The note reads "URL changed during this Congress: the House member
    directory also lists https://bonner.house.gov as archived
    20050103–20061201". `same_site()` keeps `www.` and path variants of one
    address from being added twice. This added 457 URLs for 452 members:

    | Congress | Members | URLs added | Shape |
    | --- | ---: | ---: | --- |
    | 106th | 32 | 32 | senators: `~name` beside `name.senate.gov` |
    | 107th | 59 | 59 | 54 senators, 5 House |
    | 108th | 76 | 77 | House, mostly `name.house.gov`; 9 on `wwwc.house.gov` |
    | 109th | 119 | 123 | the same; 8 on `wwwc.house.gov` |
    | 110th | 36 | 36 | House: 34 `name.house.gov`, 2 `www.house.gov/name` |
    | 111th | 56 | 56 | House: 43 and 13 |
    | 112th | 74 | 74 | House: 66 and 8 |

    `wwwc.house.gov` was a second House web server the directory linked some
    members to from 2003. Wayback holds it; all 17 in the 108th–109th were
    found, and of the 110th's, only Marilyn Musgrave's
    `wwwc.house.gov/musgrave` was not (her `musgrave.house.gov` was).
  - **A relative's listing is not the member's.** The directory is matched by
    seat and surname, and relatives share both: Julia and André Carson
    (IN-7), Michael and Gus Bilirakis (FL-9), and Lincoln and Mario
    Diaz-Balart, whose seats were renumbered around each other. Matched on
    surname alone, each was given the other's site. `someone_else()` drops a
    listing whose given names belong to another legislator with the same
    surname and state, unless the listing also carries a name this member
    goes by. That keeps Lacy Clay, listed as `Clay Jr., William "Lacy"` while
    his father was William. In the 106th–109th it changed no URL, only the
    listing dates in the notes for five rows (the Chafees, the Shusters and
    Doris Matsui), which had included the relative's. One case it cannot
    separate: Donald Payne and Donald Payne Jr. are both listed as "Payne,
    Donald", so Payne Jr.'s note carries dates from his father's listing too.
  - **Source URLs are stripped of whitespace.** Three carried a trailing
    space (Kuhl and Goode in the 110th, Paul Kirk in the 111th), which made
    Kuhl's and Goode's directory address look like a second one.
  - **The directory also catches the source being wrong.** Two source URLs
    were wrong, and `URL_CORRECTIONS` in the script replaces them, keyed by
    bioguide and Congress, with a note in the row: Dave Weldon (FL-15) was
    given Curt Weldon's `www.house.gov/curtweldon` in the 108th and 109th;
    and Curt Weldon's 108th URL, `curtweldon.house.gov`, is not listed until
    April 2005, so nothing was captured in his window.
- **No URL recorded.** Across the 110th–119th, 17 rows have no URL for that
  term in the source. Each row's `service_notes` says how its URL was
  filled:
  - **11 special-election members** take the URL from their next term
    ("URL not in dataset for this term; taken from next term").
  - **6 come from Wayback evidence** ("URL not in dataset; …"), listed in
    `URL_OVERRIDES` in the script. Mayra Flores's is inferred. Carte Goodwin
    (111th, appointed July to November 2010) had none at first;
    `goodwin.senate.gov` is captured from 2010-07-21, his second day, to
    2010-11-08, and was added on 9 November.

  **Rule: every member with no URL gets an issue to check Wayback for one,
  worked after the initial explorer is built.** Goodwin's was
  [#10](https://github.com/Robin-IA/Congressional-Letters-Dev/issues/10),
  now closed. The 17 filled URLs are checked by step 2, which looks each one up within
  that member's own service. Any that step 2 cannot confirm get an issue of
  their own.
  The 106th–107th add three: Joel Hefley and Jesse Jackson Jr. in the 106th
  ([#12](https://github.com/Robin-IA/Congressional-Letters-Dev/issues/12),
  [#13](https://github.com/Robin-IA/Congressional-Letters-Dev/issues/13)), and
  Dean Barkley in the 107th
  ([#14](https://github.com/Robin-IA/Congressional-Letters-Dev/issues/14)).
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
| 106th | 544 | 9 | 2 |
| 107th | 550 | 25 | 1 |
| 108th | 544 | 10 | 0 |
| 109th | 545 | 13 | 0 |
| 110th | 554 | 30 | 0 |
| 111th | 559 | 36 | 0 |
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

### Results (run 7–8 November 2026)

**5,716 of 5,717 lookups found the site within the member's own service.** The
one that did not is Marilyn Musgrave's second address in the 110th; her first
was found, so every member of the 110th–119th is confirmed. The 110th–112th
were re-run on 8–9 November with the 166 added addresses and Carte Goodwin's
URL (step 1). Three lookups failed
on the network in the first run (Hinchey, McCaskill, Wicker) and were found on
the re-run. No home page needed the prefix fallback.

| Congress | Lookups | Found | Median days captured | Found only as redirects |
| --- | ---: | ---: | ---: | ---: |
| 110th | 591 | 590 | 94 | 39 |
| 111th | 616 | 616 | 86 | 130 |
| 112th | 629 | 629 | 69 | 166 |
| 113th | 555 | 555 | 88 | 16 |
| 114th | 547 | 547 | 72 | 1 |
| 115th | 561 | 561 | 100 | 3 |
| 116th | 550 | 550 | 111 | 3 |
| 117th | 557 | 557 | 100 | 1 |
| 118th | 556 | 556 | 99 | 0 |
| 119th | 555 | 555 | 220 | 0 |

"Found only as redirects" means not one capture of the home page in the window
was a 200; counting 200s alone would have reported those 359 addresses as missing,
almost all of them in the 110th–112th. The 119th's median runs to the build
date and is not comparable.

**The 17 filled URLs are all confirmed.** Carte Goodwin's, added later, was
found on 8 days of his 117. Each was found inside the member's
own window. The five taken from Wayback evidence, plus Tom Reed, Tony Wied and
Donald Payne Jr. (`payne.house.gov` was his father's first), were opened and
read: every capture names the member it is credited to. Mayra Flores's
`flores.house.gov`, which had been inferred, reads "Congresswoman Mayra Flores"
in June 2022 and on 3 January 2023. No issue was needed beyond #10. All 166 addresses added to the 110th–112th
were found but Musgrave's (median 73, 96 and 77 days).

**24 members have fewer than 5 days captured, and none is a gap.** Every one
served only weeks of that Congress: members sworn in after a November election
(Massie, DelBene, Wild, Hern), or members who left in its first weeks for
another office (Biden, Clinton, Harris, Becerra, Pompeo, Sasse, Vance).

### Results for the 106th–109th (run 8 November 2026)

**2,560 of 2,567 lookups found the site within the member's own service.**
That includes the 291 addresses added where a site moved (see step 1), looked
up on 8–9 November.

| Congress | Lookups | Found | Median days captured | Found only as redirects |
| --- | ---: | ---: | ---: | ---: |
| 106th | 580 | 577 | 14 | 7 |
| 107th | 684 | 682 | 94 | 20 |
| 108th | 621 | 620 | 93 | 37 |
| 109th | 682 | 681 | 192 | 103 |

- **Every URL taken from a chamber directory is confirmed**: 509 in the
  106th, 481 in the 107th, 45 in the 109th.
- **289 of the 291 added addresses were found.** Median days captured:
  18, 91, 49 and 150 for the 106th–109th.
- **The seven that were not found:**
  - Three members with no URL: Hefley, Jackson Jr. (#12, #13) and Barkley
    (#14).
  - John Cornyn, 107th, 34 days as an early-sworn senator. His URL is borrowed
    from his next term. The exact query finds nothing, and the prefix query
    for the whole host answers 504 every time, including split into three
    date ranges: CDX reads the host's whole index before filtering by date.
    Read instead page by page (`showNumPages`: 1,102 pages, 9 November),
    with a control query on the same pages returning his 2003 captures, it
    holds **no capture of `cornyn.senate.gov` in his window**. His first
    capture at all is 2003-03-26. The row is now `none in window`.
    [#15](https://github.com/Robin-IA/Congressional-Letters-Dev/issues/15).
  - Denny Hastert's `dennyhastert.house.gov`, listed once by the 106th
    directory in February 1999. His other listed URL, `www.house.gov/hastert`,
    was found, so he is confirmed.
  - Todd Akin's `akin.house.gov`, 108th and 109th: one of the added
    addresses. The directory lists it from August 2003 to December 2006, but
    Wayback has no capture of its home page between 2001 and 2007-01-19. The
    108th's prefix query found nothing; the 109th's timed out, so that row is
    `error`. His other address, `www.house.gov/akin`, was found in both, so
    he is confirmed.
- **The 106th is thinly captured: median 14 days in two years**, against
  roughly 95 from the 107th on. Twelve members found have fewer than 5 days,
  several of them serving the whole Congress (Dreier, Obey, Mollohan). That is
  how often the Wayback Machine crawled in 1999–2000, not a gap in the
  rosters. Expect fewer letters per member there.

## Step 3: who held each address, and when

**An address identifies a member only for a span of time.** `murphy.house.gov`
was Tim Murphy's, then Stephanie Murphy's, then Greg Murphy's. Step 2 is safe
from this, because every lookup is bounded to the member's own service. Step 4
is not: a letter found on a reused address has to go to whoever held the
address on the letter's date. Step 3 writes the table that makes that possible.
It is the fix for
[#8](https://github.com/Robin-IA/Congressional-Letters-Dev/issues/8), and step 4
uses it to fix the misattribution in
[#7](https://github.com/Robin-IA/Congressional-Letters-Dev/issues/7).

### What it writes

`data/address-holders.csv`, written by `build/address_holders.py` from the
rosters and step 2 alone, with no new Wayback queries. One row per address per
member per unbroken run of Congresses: a member who left and came back to the
same address has a row for each stay. `attribute()` in the same script is the
rule below, for step 4 to call.

| Column | |
| --- | --- |
| `address` | the key below |
| `urls` | every URL in the rosters that reduces to this address |
| `bioguide_id`, `name`, `state`, `chamber`, `district` | the holder |
| `held_from`, `held_to` | the span (rule 2) |
| `congresses` | the Congresses whose roster gives this member this address |
| `first_capture`, `last_capture` | from step 2, inside that span |
| `holders` | how many members held this address; 1 for most |
| `before`, `after` | the previous and next holder's bioguide, if any |

### Rules

1. **The address is the host**, without `www.`, so `kennedy.senate.gov` and
   `www.kennedy.senate.gov/public` are one address. On the hosts several
   members shared at once, it is the host plus the member's own path:
   `house.gov/matsui`, `wwwc.house.gov/regula`, `senate.gov/~chafee`, and
   `senate.gov/senators/carper.html` (the holding pages the Senate posted for
   senators arriving in January 2001, before their own sites were up).
2. **A member holds an address only during the Congresses whose roster gives
   it to them**, and within those, only during their service: never their
   whole career. Greg Murphy has served since 2019 but was at
   `gregmurphy.house.gov` until 2023, so his span on `murphy.house.gov` starts
   in 2023. Where a member's site moved within a Congress, both addresses
   carry that member's service in that Congress; step 2's capture dates show
   when each was live, but are recorded, not used to cut the span, because
   captures are too sparse to mark an edge. **The one cut made is a change of
   chamber**: a roster row covering both chambers (Menendez, Wicker,
   Gillibrand, Heller, Markey, Kirk, Schiff, Kim) gives the House address the
   service up to the switch date and the Senate address the service after.
3. **A letter goes to whoever held its address on the letter's date.** That is
   the date read from the letter where there is one, and otherwise the
   **earliest capture of the letter's own URL**: a letter cannot be captured
   before it was posted, so that capture bounds the posting date from above.
   - In a holder's span: that holder.
   - After a holder's span and before the next holder's: the holder before,
     flagged `after_service`. Decided 9 November 2026 (Robin), over the
     alternative of crediting no one: these letters stay in the explorer,
     under the member whose site they were on, and the flag lets them be
     shown or reviewed apart. **Except where the earlier holder was still in
     office in the same chamber**, and the roster had recorded another
     address for them in those Congresses: Ed Pastor, Jim Matheson and John
     Boehner each served throughout, but the source gives a different URL in
     some Congresses. Those letters are the holder's outright. The other 24
     members with a gap at their own address really had left and come back
     (Shea-Porter, Titus, Issa, Kyl, Zinke …), and stay `after_service`. A
     House site left up after its member moved to the Senate is after service. A site left up after a member died or resigned
     still shows that member's letters (Matsui, 2005-01-03 to 2005-03-10;
     Payne, 2012-03-06 to 2012-11-15).
   - Before the first holder in the rosters, or after the last: no holder.
     `attribution: none`, kept out of the explorer, as letters-from-congress#2
     sets for the backfill. That covers holders from before 1999, whom the
     rosters do not record.
   - Dated by capture rather than by the letter, on an address with more than
     one holder: flagged `by_capture`, for review.
4. **A letter belongs to the address it was captured at**, not to wherever that
   address redirects. `dingell.house.gov` redirects to `debbiedingell.house.gov`,
   a different member's site.

### Built, 9 November 2026

**2,043 addresses in 2,120 rows; 49 held by more than one member**, 100 rows
between them. No two members hold one address on the same day; the script
checks this on every build and the tests assert it. (The design's ad hoc
count, 2,038, keyed a few addresses differently. These are from the table.)

- **33 are a surname reused in another seat**, often years apart:
  `jones.house.gov` (Walter Jones, then Mondaire Jones), `menendez.house.gov`
  (Robert Menendez 1999–2007, Rob Menendez from 2023), `mikerogers.house.gov`
  (two different Mike Rogers, Michigan then Alabama), `kennedy.senate.gov`,
  `kirk.senate.gov`.
- **16 stayed in one state and chamber**: relatives or successors of the
  same name (the Chafees, Clays, Hunters, Lipinskis, Matsuis, Shusters,
  Fitzpatricks, Grijalvas, Murkowskis, Paynes, Warners, Menendezes) and
  surnames reused in the same state (`cox`, `flores`, `gonzalez`,
  `house.gov/campbell`). The design's count of 11 judged by seat, not state.
- **`murphy.house.gov` is the only address with three holders.**

### Tests

`tests/test_address_holders.py`, 19 cases on the real data:
`murphy.house.gov` (three holders), `mikerogers.house.gov` (same name, two
people), `menendez.house.gov` (father and son, sixteen years apart, and the
cut at the father's move to the Senate), `payne.house.gov` and
`house.gov/matsui` (same seat, a gap between holders), a letter on
`dingell.house.gov` (a redirect to another member, not followed), Pastor
and Shea-Porter (a gap in office and out of it), the `by_capture` flag, and
the address key itself.

### Open

- `payne.house.gov` is listed under "Payne, Donald" for both father and son,
  so the directory cannot separate them. Their spans separate them instead.

## Step 4: find the letters at each address (designed, not built)

**Query every address in `data/address-holders.csv`, keep what opens as a
letter, and credit each letter with step 3's `attribute()` when the site is
built, not when it is harvested.** The harvest is the expensive half and is
done once per address; who gets a letter depends on the rosters, the dates and
the rules, all of which can change, so it is worked out afresh on every build.
This is the principle `build/harvest.py` already follows for cleaning (cache
raw rows, filter on the way out), extended to attribution.

### Measured against today's explorer (9 November 2026)

`attribute()` run over the 73,354 letters the explorer now holds
(`letters-parsed.jsonl` and the 119th's departed members), with the date read
from the URL where there is one and the first capture otherwise:

| Outcome | Letters |
| --- | ---: |
| Same member as now | 71,545 |
| **A different member** | **1,058** |
| No holder | 495 |
| Address not in the table (caucus subdomains) | 256 |

- **The 1,058 are #7, fixed.** `grijalva.house.gov` 404, `murphy.house.gov`
  269, `levin.house.gov` 140, `kennedy.house.gov` 53, `gallagher.house.gov`
  45, `fitzpatrick.house.gov` 32, `conaway.house.gov` 25, then
  `kennedy.senate.gov`, `owens`, `moran`, `hurd`, `ross`. #7 measured 874 plus
  242 with no holder from the legislators file alone; the rosters and the
  directories place most of those 242.
- **2,219 letters are dated only by capture on a shared address**
  (`by_capture`). They are attributed, and listed for review.
- **The explorer covers 527 of the 2,043 addresses and 555 of the 1,571
  members** who served in the 106th–119th. The other 1,516 addresses are the
  harvest: 674 House hosts, 151 Senate hosts, 576 `www.house.gov/<name>`
  paths, 105 `senate.gov` paths, 9 on `wwwc.house.gov`, and
  `jessejacksonjr.org`. Most were first held before 2010 (1,117 of them).

### Harvest, per address

- **One CDX query per address, unbounded in time.** A letter stays up after
  its author leaves, and a reused address can carry the previous holder's
  letters for years. The date decides who gets it, and step 3 already knows
  who held the address when. Bounding the query to the holder's span would
  drop exactly the letters `after_service` exists for.
- **Hosts** take `matchType=domain`, as `harvest.py` does now; **paths on a
  shared host** take `url=www.house.gov/<name>/&matchType=prefix`, and the
  `senate.gov/~name` and `senators/<file>.html` forms likewise. This is the
  second pass `BACKFILL.md` §8 left open.
- **The same filters as now**: `statuscode:200`, `urlkey:.*letter.*`,
  `!urlkey:.*newsletter.*`, one row per `urlkey`. Raw rows are cached per
  address under `harvest/letters/cache/`, so a cleaning change costs a
  re-filter, not a re-harvest.
- **Over https, and paged when the whole-host query times out.** Cornyn's
  host (step 2) and the large sites `harvest.py` warns of answer 504 because
  CDX reads the whole index before filtering; `showNumPages` with `&page=N`
  answers inside the gateway limit and is resumable. `http://` CDX answered
  503 to the renderer and is not used.
- **Order by breadth, as the renderer does**: every address's first query
  before any address's retry, members with no letters at all first. The run
  takes days and will be stopped before it finishes; what it has done by then
  should be spread across members, not deep in a few.
- **It competes with the renderer and `resolve_wrappers.py` for the same
  Wayback budget.** Run one at a time.

### What counts as a letter

Unchanged from the corpus rule in `CLAUDE.md`: **every letter opens as a
letter.** Announcement pages and press releases wearing the word are dropped;
the Senate CMS's download wrappers go to `resolve_wrappers.py`; captures cut
at the crawl's 64,000-byte cap are bad captures. These filters live in
`harvest.py` and `parse_urls.py` and are reused, not rewritten.

### Dating

The date `attribute()` is given, in order:

1. **The letter's own date**, read from its URL or path (`parse_urls.py`:
   31,081 letters today).
2. **The date the PDF says it was made** (`data/pdf-dates.jsonl`, written by
   the renderer: 715 more today, and it grows as rendering continues).
3. **The first capture of the letter's URL**, which bounds the posting date
   from above. Flagged `by_capture` on a shared address.

Because the renderer adds PDF dates after the harvest, attributing at build
time means a letter first credited by capture is re-credited by its own date
as soon as one is known.

### Written

`data/letters-parsed.jsonl` keeps its shape, with `bioguide` now the holder on
the letter's date rather than whoever holds the host today, and four fields
added: `address`, `attribution` (`holder`, `after_service` or `none`),
`dated_by` (`letter`, `pdf` or `capture`) and `by_capture`. `none` stays out
of the explorer, as letters-from-congress#2 set for the backfill. The 119th's
departed file merges into it; it existed only because the harvest started
from the sitting roster.

### Tests to write with it

The 1,058 above are the acceptance test: no letter credited to a member
outside that member's holding of its address (#7's own criterion). Pinned
cases: a Grijalva letter from 2020 on `grijalva.house.gov` goes to Raúl, not
Adelita; Greg Murphy has no `murphy.house.gov` letter before 2023; a
`by_capture` letter re-credited once a PDF date arrives.

### Open

- **A letter dated before an address's first holder, by that same member's
  earlier office.** 428 of the 495 with no holder are this: Tammy Baldwin's
  and Bernie Sanders's House letters reposted on their Senate sites, and
  Tom Cole's `cole.house.gov`, live from 2007 while the rosters record
  `www.house.gov/cole` until 2011. The member wrote them. The design as built
  says `none`; crediting the first holder when they were in Congress on that
  date, flagged `earlier_office`, would keep them. The other 67 are dated
  before anyone held the address, some by a misread date (`090206` read as
  2006 on Michael Bennet's site, posted in 2009).
- **Caucus subdomains.** `cpc.grijalva.house.gov` (108 letters),
  `rsc.jordan.house.gov` (76), `rsc.scalise.house.gov` (62),
  `diabetes.degette.house.gov`, `doctorscaucus.murphy.house.gov`: the
  Progressive Caucus, the Republican Study Committee and others, hosted on a
  chair's address. Credit the parent address's holder, flagged `caucus`, or
  leave them out. They are the caucus's letters more than the member's.

## How this relates to the earlier approach

`BACKFILL.md` and `build/chamber_rosters.py` start from the House and Senate
member directories as archived each year (`data/member-sites.tsv`): a list of
websites, with people attached where possible. The House directory never
stated a bioguide ID, so many of those rows name a site rather than a person.
Starting from the roster turns that around. Every row is a person with a
bioguide ID and service dates, and the website is an attribute of that person
for a span of time. `member-sites.tsv` remains useful as a second source of
URLs in step 2.
