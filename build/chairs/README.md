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

**Limits:**
- An edition shows the chair on its print date, so a mid-Congress change is missed when no edition falls after it. For example, Paul Ryan chaired Ways and Means in 2015; the 114th's only edition (February 2016) shows Kevin Brady.
- The 118th and 119th editions name the section differently, so they are not parsed yet.
- House Administration and Ethics are missing in some Congresses.
- Select committees (Intelligence) and subcommittees are not included.
