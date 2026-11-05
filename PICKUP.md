# Pick this up on another machine

Hand this file to Claude Code and say "continue the work". Everything it needs
is here or in the clone.

**State as of 5 November 2026**, branch `harvest-member-letters` on `dev`
(`git log -1` for the commit — a sha written here goes stale the next push):

| | |
| --- | --- |
| Letters | 69,650, from 514 of 539 sitting members, 2000–2026 |
| Thumbnails rendered | **47,674 of 48,028 documents — 99%** |
| Letters showing a preview | 69,120 of 69,565 PDF letters — 99% |
| Still to render | **239** |
| Given up on | 115 documents, recorded and skipped automatically |
| Disk | **854 MB** of a 940 MB budget |

Live now, both serving `ddaf0c9ac` on the `harvest-member-letters` branch:
<https://internetarchivecanada.github.io/congressional-letters/> ·
<https://robin-ia.github.io/congressional-letters/>

**The explorer is finished and working**, and the thumbnail render has all but
finished too — 239 documents left of 48,028. Every letter without a picture
shows "preview coming soon" and still opens, so that remainder has never had to
finish for the site to be correct.

The open work is no longer the render. It is the **backfill** — the members who
have left, who the explorer has never seen — and the **per-Congress
restructure**. Both are in [`BACKFILL.md`](BACKFILL.md) and section 8 below.

Read [`CLAUDE.md`](CLAUDE.md) for why the project is built the way it is, and
[issue #2](https://github.com/internetarchivecanada/letters-from-congress/issues/2)
for what to do next and in what order. This file is only about resuming.

---

## 0. Four repositories. Develop in one of them.

| Remote | Repository | What it is |
| --- | --- | --- |
| **`dev`** | **`Robin-IA/Congressional-Letters-Dev`** | **public, Pages — the working copy. Develop here.** |
| `origin` | `internetarchivecanada/letters-from-congress` | private, no Pages. The handover record: PR #1, issue #2, and the internal decisions doc. **Frozen** |
| `iac` | `internetarchivecanada/congressional-letters` | public, Pages. The live explorer, under review. **Frozen** |
| `mine` | `Robin-IA/congressional-letters` | public, Pages. Your copy of the live explorer. **Frozen** |

**`iac` and `mine` are being reviewed by other people and must not change.**
Development happens on `dev` and reaches them only when it is finished, as a
deliberate push, once.

**`origin` is frozen as the record of what was handed over.** It is the only
repository that still holds `docs/keeping-it-current.md` and its generator
`build/make_decisions_doc.py` — an internal decisions document. It is private,
and that is where that document stays.

**`dev` does not have those files, by construction.** It was made public on
5 November so it could serve a Pages preview during development, and the three
paths carrying that document were removed from **every commit** first, not
merely deleted in a new one. A public repository publishes its history, so
deleting a file forward would have published it anyway.

So: **all new work goes to `dev`.** Before adding anything under `docs/`, or
anything else not meant to be read by strangers, remember that this repository
is now public and serves its own branch root over HTTP.

## 1. Clone

```bash
mkdir -p ~/ia && cd ~/ia
gh repo clone Robin-IA/Congressional-Letters-Dev congressional-member-letters -- -b harvest-member-letters
cd congressional-member-letters
```

**`Congressional-Letters-Dev`**, and **not `main`**. `main` is the initial
scaffold; the work has never been merged into it, and both Pages sites serve
the branch.

The other three repositories are frozen — see section 0. Of the names, the one
that sounds like the main repository, `congressional-letters`, is the published
mirror and the furthest behind. Clone the dev repo and the question does not
arise.

The clone brings all 47,688 thumbnail files, all 514 member files and the page
itself. (47,674 of those match a document still in the corpus; 14 are leftovers
from documents the harvest no longer lists, which cost nothing.) Open `index.html` and the explorer works immediately.

## 2. Install

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Copy the data git does not carry

Five files under `data/`, all gitignored. **The first is required** — the
renderer reads it and will not start without it.

| File | Size | What it is |
| --- | --- | --- |
| `letters-parsed.jsonl` | 51 MB | **Required.** One record per letter: URL, capture, digest, and the date, recipient and subject parsed from the filename |
| `thumb-failures.jsonl` | 16 KB | **Copy this.** 202 recorded failures over 183 documents; 115 have hit the give-up threshold. Without it they are all retried, and they are the slow ones |
| `pdf-dates.jsonl` | 1.5 MB | Dates read out of the PDFs so far |
| `letter-text.jsonl` | 53 MB | Extracted text and a sha256 for 19,437 letters. Nothing reads it yet; see issue #1 |
| `wrapper-targets.jsonl` | 40 KB | Progress of the download-wrapper chase, 113 of 6,711 |

Copy the whole `data/` directory across. `data/cdx-cache/` is bigger than it
was — it now holds the chamber directory pages (90 files) and
`legislators-historical.json` as well — and **carrying it across is worth it**:
with that cache, `build/chamber_rosters.py` and `build/backfill_roster.py` both
run offline in seconds instead of re-reading 20 archived pages.

## 4. Resume the render

Only 239 documents are left, so this is now a short job rather than the main
event. Skip to section 8 if the backfill is what you came for.

```bash
caffeinate -i python3 build/thumbs.py --thumbs thumbs --workers 2 --pause 1.5
```

Four things in that line, each of which has gone wrong at least once:

- **`--thumbs thumbs`.** The finished work arrives as `thumbs/` (tracked); the
  script defaults to `payload/thumbs/` (gitignored, so empty on a fresh clone).
  Without this flag it re-fetches all 47,688 PDFs it already has.
- **`caffeinate -i`.** A sleeping machine freezes the job. On the Windows box
  this cost five hours one night and about twenty-two another.
- **`--workers 2 --pause 1.5`.** Two workers is what runs stably. Three bought
  3/min and took network refusals from 29% of failures to 68%. Earlier, two
  workers at a 0.75s pause for five days straight earned an outright HTTP 403
  on the replay endpoint that took hours to clear.
- Run it from a **terminal**, not from inside a Claude session. Anything
  started from a session dies with it, which has happened three times.

**Check the first line before walking away:**

```
48,028 distinct PDFs, 239 still to render
  skipping 115 that have failed 3+ times
```

If that second number is near 48,000, stop it — `--thumbs` did not take and it
is about to redo everything.

## 5. Publish what it renders

The renderer writes straight into `thumbs/`, so there is no copy step.

```bash
python3 build/build_site.py --thumb-base thumbs/ --force
git add -A && git commit -m "Publish previews" && git push dev harvest-member-letters
```

`--force` because the build refuses to shrink the corpus by more than a tenth
without being told to, which is a guard worth keeping.

Every 20–30 minutes is plenty. **GitHub Pages allows 10 builds an hour from a
branch and every push is one**, so do not loop tighter than that.

**Push `dev`, and nothing else.** That is what section 0 is about: the two
public repos are under review by other people, and they serve Pages from the
branch root where an internal document now sits. With 239 documents left there
is no publishing loop to run anyway — one final build into `dev`, and the public
repos get brought forward deliberately, once, by whoever decides what the public
branch should contain and what happens to `docs/`.

## 6. How to tell whether it is actually working

`build/pending.py` counts and renders nothing:

```bash
python3 build/pending.py thumbs
```

Measure the live rate rather than reading the renderer's own progress line —
that line is cumulative and divides by elapsed time including every hour the
machine spent asleep, so it reports 2/min for a job doing 15/min.

```bash
a=$(find thumbs -name '*.webp' | wc -l); sleep 120
echo $(( ($(find thumbs -name '*.webp' | wc -l) - a) / 2 ))/min
```

**15–20/min is healthy.** Below that, check whether the failures are about the
network or about the letters:

```bash
tail -30 data/thumb-failures.jsonl
```

`truncated-by-the-crawl`, `unreadable-PdfiumError`, `not-pdf` and `http-404`
are bad captures — a patch of poor data, nothing to fix. `URLError`,
`ConnectionResetError` and `http-429` are the network, and if they dominate,
slow down rather than retrying harder.

Across the whole render the documents won: of 202 recorded failures, 84 are
the network (`URLError` 77, `ConnectionResetError` 6, `http-403` 1) and 118 are
the documents themselves (`truncated-by-the-crawl` 68, `unreadable-PdfiumError`
26, `http-404` 16, `not-pdf` 7, `too-big` 1). So most of what is left is bad
data rather than a throttle to wait out.

To check whether the Wayback replay endpoint is refusing us, fetch eight real
PDFs in a row. **A single request proves nothing** — after the 403 lifted, six
single fetches returned five good PDFs while the renderer sat doing nothing for
nine minutes, because the endpoint had stopped refusing and started stalling
connections instead.

## 7. The render, as good as finished

It will not reach 48,028. 115 documents have been given up on and 239 remain to
try, so the ceiling is about 47,900 of 48,028 — **99.7%**, against the 4–8%
unrenderable this file once expected. The early estimate was pessimistic
because the first 1,400 attempts were not a representative sample.

"Finished" means the queue is empty. That is close enough that it is no longer
what the project is waiting on.

## 8. Still open, in rough order of value

- **The backfill — [`BACKFILL.md`](BACKFILL.md).** 1,213 member sites the
  explorer has never touched, from the chambers' own archived directories,
  2003–2026. 778 are queryable hostnames and 435 are path-keyed
  `house.gov/<name>` sites with a harvester of their own. Both passes are
  written, guarded and trialled; neither has been run at scale. This is the
  work. Expect overnight.
- **The per-Congress restructure.** A front page with search, then one page per
  Congress — 111th through 119th, reverse chronological back to 2010, each
  labelled with its years (119th Congress, 2025–2026). Not started. It depends
  on the backfill for honesty: a Congress-shaped page implies a completeness
  the sitting roster alone cannot deliver, so either run the backfill first or
  label each tab with what it actually covers.
- **The download-wrapper chase**, `build/resolve_wrappers.py`, is parked at 113
  of 6,711. Worth roughly 3,000 more letters. It competes with the backfill for
  the same Wayback budget, so do not run them together.
- **Full-text search.** About half these PDFs carry a usable text layer and
  `data/letter-text.jsonl` already holds the text for 19,437 of them, taken from
  the same download as the thumbnail. Nobody has built an index. See issue #1 in
  `Robin-IA/congressional-letters`. NARA's own crawl items carry extracted-text
  files beside the WARCs — the same index, already built — but they are
  access-restricted. The reasoning is in `docs/keeping-it-current.md`, which
  lives only on the private `origin` repository — not in this one.
- **Thumbnails are at 854 MB of a ~940 MB budget.** Every letter the backfill
  finds is eventually a letter wanting a preview, and there is not room for all
  of them where the thumbnails currently live.
- **Why the archive.org item swallows zips.** A zip uploaded there returns 200
  from S3 and then never appears, twice, with the task queue empty. Solving it
  would let the thumbnails move off the Pages repository, which is where they do
  not really belong — and that is now a constraint, not a tidiness complaint.
