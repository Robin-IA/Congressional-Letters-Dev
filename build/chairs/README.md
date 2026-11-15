# Committee chairs by Congress (#364)

`data/committee-chairs.csv`: one row per chair per Congress, 106th–119th.

**Senate:** from the Senate Historical Office's *Chairmen of Senate Standing Committees, 1789–present* (Table 5-3).

1. Download the PDF from https://www.senate.gov/artandhistory/history/resources/pdf/CommitteeChairs.pdf
2. Extract its text to `senate.txt` with pypdf.
3. Run `senate_parse.py`, then `senate_build.py`.

The years are the table's. A Congress lists every chair who served in it, so a mid-Congress change gives two rows. Bioguide IDs come from `data/rosters`. Three names are corrected and noted in the `source` column.

**House:** to follow, from the *Congressional Directory* (GovInfo `CDIR`).
