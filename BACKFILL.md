# Backfill: the members who have left

Hand this file to Claude Code on the studio and say "run the backfill", or work
through it by hand. Everything it needs is here or in the clone.

**Prepared 5 November 2026**, branch `harvest-member-letters` on `dev`
(`Robin-IA/Congressional-Letters-Dev` — the private working copy).

**This file is the mechanics. The sequence and the acceptance criteria are
[issue #2](https://github.com/internetarchivecanada/letters-from-congress/issues/2)** — what each pass is for,
how to tell it worked, and the two decisions that cannot be made by running
something.

| | |
| --- | --- |
| Backfill queue | 1,213 member sites the explorer has never touched |
| **Queryable this pass** | **778 hostnames** |
| **Second pass** | **435 path-keyed `house.gov/<name>` sites** — see §8 |
| Identified | 689 of 778 carry a bioguide; 89 do not |
| Verified on | 2 hosts, 5 November — see §4 |
| Expected runtime | **many hours. Run it detached.** |

## Why

The explorer harvests the *sitting* roster, so everyone who has left is absent,
and their sites are the material the README calls most at risk and least
replaceable. `data/member-sites.tsv` is the historical map that fixes it: every
member website the House and Senate listed in their own directories, 2003 to
2026, read one capture per year out of the Wayback Machine.

Lindsey Graham is the case that made this concrete. He left mid-term, a
successor took the seat, and he fell off `legislators-current.json` — so the
explorer has none of him. The trial run in §4 recovered 44 letters.

---

## 1. Clone

```bash
mkdir -p ~/ia && cd ~/ia
gh repo clone Robin-IA/Congressional-Letters-Dev congressional-backfill -- -b harvest-member-letters
cd congressional-backfill
```

**`Congressional-Letters-Dev`, not either `congressional-letters`.** The two
repos with that name are public, serve GitHub Pages, are under review by other
people, and do not have this work. `Congressional-Letters-Dev` is private,
carries everything, and is where development happens. Clone it and the question
does not arise.

`internetarchivecanada/letters-from-congress` also has this work and is also
private, but it is frozen as the record of what was handed over. Do not push to
it.

If you would rather work in an existing clone, add the remote:

```bash
git remote add dev https://github.com/Robin-IA/Congressional-Letters-Dev.git
git fetch dev && git checkout -B harvest-member-letters dev/harvest-member-letters
```

## 2. Install

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Run

```bash
# Only if data/member-sites.tsv is missing -- it is committed, so normally skip.
# Re-reads 20 archived directory pages; about 3 minutes.
python build/chamber_rosters.py

# Shapes the queue into a roster harvest.py can read. Seconds.
python build/backfill_roster.py

# The harvest itself. Detached, because it runs for hours.
nohup python build/harvest.py \
  --members-in  data/backfill-members.json \
  --out         data/letters-backfill.jsonl \
  --members-out data/backfill-members-queried.json \
  --workers 3 > backfill.log 2>&1 &

tail -f backfill.log
```

**All three paths must be given.** `harvest.py` normally writes its roster to
`data/members.json` and its letters to `data/letters-raw.jsonl`, which are the
explorer's own files. `--members-in` refuses to run unless both are redirected:

```
harvest.py: error: --members-in needs --members-out and --out set to
something other than the explorer's own file
```

That guard exists because this has gone wrong before. The `--limit` comment in
`harvest.py` records a three-host trial run that "quietly rewrote the dataset as
three members and the explorer rebuilt around it".

**Leave `--workers` at 3.** Wayback throttles, and the enumeration treats a
failed page as a failed host specifically so throttling cannot turn into silent
short reads. More workers buys less than it costs.

## 4. What to expect

Measured on 5 November, two hosts, nothing else running:

```
[1/2] adler.house.gov          0 letters (of 0 rows)    2m
[2/2] lgraham.senate.gov      44 letters (of 76 rows)  17m
```

That is two hosts of evidence and it does not extrapolate to 778. Senate hosts
are the slow ones — more years, far more captures — and there are 138 of them
against 640 House hosts. Assume overnight rather than an afternoon.

**A zero is usually a true zero.** `adler.house.gov` has 20 captures in Wayback
and rows that match `urlkey:.*letter.*`, but all of them are `enewsletter-signup`
pages, which the third filter `!urlkey:.*newsletter.*` removes. Verified by
running the query by hand. Do not treat zeros as a fault without checking one.

**The run is resumable and re-running is cheap.** Every host is cached to
`data/cdx-cache/<host>.json`. A host that succeeded is skipped; a host that
failed is re-queried. So if the run dies, start it again with the same command.

**Wayback CDX was intermittently offline on 5 November**, answering an HTML
"Internet Archive: Temporarily Offline" page where JSON was expected. The
enumeration handles that — the host is retried three times, then recorded as an
error and picked up by the next run — but expect some failures in the log and
plan on a second pass to clear them.

## 5. When it finishes

```bash
wc -l data/letters-backfill.jsonl
python - <<'PY'
import json, collections
rows = [json.loads(l) for l in open("data/letters-backfill.jsonl", encoding="utf-8")]
print("letters:", len(rows))
print("hosts with letters:", len({r["host"] for r in rows}))
print("no bioguide:", sum(1 for r in rows if not r.get("bioguide")))
PY
```

Commit the output and push to `dev`. **Do not merge it into the
explorer yet** — see §6. Nothing in this run touches `index.json`, `payload/`
or `data/members.json`, so the live explorer is unaffected either way.

## 6. What this does not do

**It does not change the explorer.** The letters land in a separate file.
Folding them in means deciding what a departed member looks like on the page,
which is open: they have no current website to link to, and 89 of them have no
bioguide, so they cannot yet be attributed to a person. Attribution is fixable
by matching names against `legislators-historical.json`; it has not been done.

**It leaves the path-keyed sites to a second pass**, which now exists — §8.

**Thumbnails are a downstream constraint, and a near one.** The published site
is 874.9 MB against GitHub Pages' 1,024 MB limit — `thumbs/` is 854.2 MB of it,
across 47,688 files. About 149 MB is left, and a preview averages 18.8 KB, so
there is room for roughly **8,000 more thumbnails**. This backfill expects more
letters than that, so deciding where the previews live stops being optional
somewhere in the middle of it.

## 7. If it goes wrong

The explorer as served before any of this is tagged, on all four remotes:

```bash
git checkout pre-congress-restructure -- index.html app.js index.json payload thumbs
```

`pre-congress-restructure` points at `ddaf0c9ac`, the commit both Pages sites
were serving on 5 November 2026. Nothing in this runbook writes to those paths,
so you should not need it — it exists so that rolling back is a checkout rather
than a reconstruction.

---

## 8. Second pass: the path-keyed sites

Through the 2000s most representatives had no host of their own but a directory
on the chamber's site — 391 of the 440 the House listed in 2003, none by 2016.
Those 435 rows of `data/member-sites.tsv` carry a slash, and `harvest.py` cannot
take them: it names its cache after the host, so a slash makes a subdirectory,
and it enumerates a host where the target is a path prefix.

```bash
nohup python build/harvest_paths.py --workers 3 > paths.log 2>&1 &
tail -f paths.log
```

Defaults are safe here — it writes `data/letters-paths.jsonl` and
`data/cdx-cache/paths/`, neither of which the explorer reads. It prints
`435 path-keyed sites (0 skipped as chamber plumbing)` — the two that were
plumbing, `senate.gov/cgi-bin` and `house.gov/include_content`, are now dropped
where the roster is built rather than here.

**It refuses to shrink its own output by more than a tenth.** The export reads
the cache, so a run against a cold cache writes a handful of letters over a
finished pass. If you see

```
refusing to shrink: this export has 9 letters against 2,400 already written
```

the cache is incomplete, not the corpus — run it again without `--export-only`.
`--force` overrides, and should be needed roughly never.

**Expect less than the host pass.** These sites hold ten to twenty letter-shaped
URLs each, not hundreds: `house.gov/abercrombie` gave 8 letters from 17 rows on
5 November, against 18 letter-shaped URLs found by hand. Across 435 sites that
is plausibly a few thousand, concentrated in the years the explorer is thinnest
— 2003 to 2008 together hold 562 letters today.

**They are not 435 missing members.** Matched by label and chamber: 73 are an
earlier URL for a member already in the explorer, 193 for a member already in
the host queue above, and 171 have no subdomain counterpart at all. Only the 73
resolve to a bioguide — the House's own directory never stated one — so for the
other 362 the row names a site, not yet a person. Every row carries an
`attribution` field saying which case it is. Nothing here should be folded into
the explorer on the strength of an inferred match alone.

**If you change the query, do not pass a wildcard and `matchType=prefix`
together.** Either alone enumerates the prefix; together they return nothing,
and an empty CDX answer is indistinguishable from a member who wrote no letters.
That is written at the top of both `harvest_paths.py` and `cdx_rows`.
