# Backfill: the members who have left

Hand this file to Claude Code on the studio and say "run the backfill", or work
through it by hand. Everything it needs is here or in the clone.

**Prepared 5 November 2026**, commit `a8c728f4`, branch `harvest-member-letters`.

| | |
| --- | --- |
| Backfill queue | 1,215 member sites the explorer has never touched |
| **Queryable this pass** | **778 hostnames** |
| Deferred | 437 path-keyed `house.gov/<name>` sites — see §6 |
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
gh repo clone internetarchivecanada/letters-from-congress congressional-backfill -- -b harvest-member-letters
cd congressional-backfill
```

**`letters-from-congress`, not `congressional-letters`.** `PICKUP.md` sends you
to the latter, which is right for the explorer and wrong here: it is the public
Pages repository and does not have this work. The backfill code lives only on
`letters-from-congress`, which is private. Pushing it to the public repo would
publish `docs/keeping-it-current.md` at a public URL, so it has not been pushed
there. Clone this one and the question does not arise.

If you would rather work in an existing clone, add the remote:

```bash
git remote add lfc https://github.com/internetarchivecanada/letters-from-congress.git
git fetch lfc && git checkout -B harvest-member-letters lfc/harvest-member-letters
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
are the slow ones — more years, far more captures — and there are 141 of them
against 637 House hosts. Assume overnight rather than an afternoon.

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

Commit the output and push to `lfc`/`origin`. **Do not merge it into the
explorer yet** — see §6. Nothing in this run touches `index.json`, `payload/`
or `data/members.json`, so the live explorer is unaffected either way.

## 6. What this does not do

**It does not change the explorer.** The letters land in a separate file.
Folding them in means deciding what a departed member looks like on the page,
which is open: they have no current website to link to, and 89 of them have no
bioguide, so they cannot yet be attributed to a person. Attribution is fixable
by matching names against `legislators-historical.json`; it has not been done.

**It leaves 437 sites out.** Through the 2000s most representatives sat at
`house.gov/<name>/` rather than on a subdomain. Those are not hostnames:
`harvest_host` would build a cache filename containing a slash and enumerate the
wrong thing. Finding their letters needs a CDX query against a path prefix,
which is a second pass rather than a variation on this one. They are in
`data/member-sites.tsv`; `python build/backfill_roster.py --include-path-keyed`
lists them.

**Thumbnails are a downstream constraint.** `thumbs/` is already 854 MB across
47,688 files against a roughly 1 GB Pages budget. Every letter this backfill
finds is eventually a letter wanting a preview, and there is not room for all of
them where the thumbnails currently live.

## 7. If it goes wrong

The explorer as served before any of this is tagged, on all three remotes:

```bash
git checkout pre-congress-restructure -- index.html app.js index.json payload thumbs
```

`pre-congress-restructure` points at `ddaf0c9ac`, the commit both Pages sites
were serving on 5 November 2026. Nothing in this runbook writes to those paths,
so you should not need it — it exists so that rolling back is a checkout rather
than a reconstruction.
