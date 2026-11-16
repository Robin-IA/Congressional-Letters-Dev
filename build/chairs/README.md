# Committee chairs by Congress (#364)

`data/committee-chairs.csv`: one row per chair per Congress, 106th–119th.

**Senate:** from the Senate Historical Office's *Chairmen of Senate Standing Committees, 1789–present* (Table 5-3).

1. Download the PDF from https://www.senate.gov/artandhistory/history/resources/pdf/CommitteeChairs.pdf
2. Extract its text to `senate.txt` with pypdf.
3. Run `senate_parse.py`, then `senate_build.py`.

The years are the table's. A Congress lists every chair who served in it, so a mid-Congress change gives two rows. Bioguide IDs come from `data/rosters`. Three names are corrected and noted in the `source` column.

**House:** from the *Congressional Directory* (GovInfo collection `CDIR`), the section `STANDING COMMITTEES OF THE HOUSE`. It covers 20 editions, the 106th through the 117th.

1. Download each edition's `https://www.govinfo.gov/content/pkg/<package>/html/<package>-HOUSECOMMITTEES.htm` into `build/chairs/cdir/`. These public URLs need no API key; the API's `DEMO_KEY` runs out after a few requests.
2. Run `house_parse.py` (which writes `house-raw.csv`), then `house_build.py`.

**118th and 119th:** the HTML section isn't published for these editions. Download the whole edition from `https://www.govinfo.gov/content/pkg/<package>.zip` and run `house_parse_txt.py <text file>:<congress>:<package> ...` on its full text, which writes `house-raw-txt.csv`. `house_build.py` reads both raw files. Three layouts are handled: 'Name, of State, Chair' up to the 117th, a first-listed chair in 2024, and 'Name (st-nn) chairman' in 2026.

**Limits:**
- 118th: the only edition (April 2024) shows Tom Cole chairing Appropriations and Rules. Kay Granger chaired Appropriations until April 2024, and Virginia Foxx took Rules then. Neither change appears.
- An edition shows the chair on its print date, so a mid-Congress change is missed when no edition falls after it. For example, Paul Ryan chaired Ways and Means in 2015; the 114th's only edition (February 2016) shows Kevin Brady.
- House Administration and Ethics are missing in some Congresses.
- Select committees (Intelligence) and subcommittees are not included.
