# Congressional rosters, 106th–119th Congresses

One CSV per Congress, one row per member who served **any part** of it.
That includes members who joined, resigned, died or were appointed partway through.
Source: [`unitedstates/congress-legislators`](https://github.com/unitedstates/congress-legislators)
(current and historical), downloaded 2026-11-06 (110th–119th) and 2026-11-08 (106th–109th).
For the 106th–109th, where the source records few URLs, `website_at_the_time` is filled from the
House and Senate member directories as archived in Wayback (`directory-urls-NNN.tsv`, written by
`build/directory_urls.py`), and `service_notes` says so.

| Column | Meaning |
| --- | --- |
| `name`, `bioguide_id` | Member, and the Biographical Directory ID (the only reliable key; several members share names) |
| `party` | Party during this Congress. A switch is shown as `A → B (date)` |
| `state`, `chamber`, `district` | `district` is House only; `0` is at-large or a delegate |
| `website_at_the_time` | The URL recorded on the member's term(s) in this Congress. Several are joined with `\|` |
| `served_this_congress` | First and last day of service within this Congress |
| `days_this_congress` | Length of that span. For the sitting 119th, it is counted to the build date |
| `full_or_partial` | `partial` = joined after the Congress convened, or left before it ended |
| `service_notes` | `joined <date>`, `left <date> (during this Congress)`, and later career events |
| `years_in_office` | Career periods by chamber, e.g. `House 1991–2007; Senate 2007–present` |
| `total_years_in_congress` | Total career service, both chambers, overlaps merged |

## Known limits

- **Career totals can be up to about two years high** for members who first entered by special election
  long ago. The source dates those first terms from the day that Congress convened:
  Pelosi's starts 1987-01-06, but she was sworn in in June 1987. Dates *within* the 106th–119th carry
  real start dates and are exact.
- The source records **when** someone left, not **why** (retired, resigned, died, appointed elsewhere).
- 119th Congress: Ashley Moody and Jon Husted were appointed until the 2026-11-03 special elections.
  The source does not yet record the results.
- The 111th's Carte Goodwin (appointed July–November 2010) has no website recorded. Checking Wayback for one is [issue #10](https://github.com/Robin-IA/Congressional-Letters-Dev/issues/10), to do after the initial explorer is built.
- Three members of the 106th–107th have no URL anywhere: Joel Hefley (106th, [#12](https://github.com/Robin-IA/Congressional-Letters-Dev/issues/12)), Jesse Jackson Jr. (106th, [#13](https://github.com/Robin-IA/Congressional-Letters-Dev/issues/13)) and Dean Barkley (107th, [#14](https://github.com/Robin-IA/Congressional-Letters-Dev/issues/14)). Each issue is to do after the initial explorer is built.
- Bishop, Regula and Reyes (110th–112th) carry `wwwc.house.gov/...` URLs as the source gives them.

Built by `build/congress_roster.py`. This is step 1 of [`METHODOLOGY.md`](../../METHODOLOGY.md).
URLs are recorded in whatever form the source gives, for lookup in the Wayback Machine in step 2.
