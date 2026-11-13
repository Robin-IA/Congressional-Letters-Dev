# Pick this up on another machine

Hand this file to Claude Code and say "continue the work". Everything it needs
is here, in `CLAUDE.md` and `EXPLORERS.md`, or in the clone.

**State as of 12 November 2026**, branch `harvest-member-letters` on `dev`
(`git log -1` for the commit; a sha written here goes stale the next push):

- **Published:** a home page and one explorer per Congress, 106th to 119th, on
  two accounts (below). The home page computes its own totals; read them
  there rather than from here.
- **Checked:** WCAG 2.2 Level AA, security and code validity all pass
  (`security-accessibility-checks.md`), and the pages' footers say so.
- **Running on the Mac:** rendering, OCR, and an auto-publish loop that keeps
  both accounts up to date (section 4).
- **The PC** has handed its work back: harvest caches, renders and OCR come
  back on `pc-*` branches, which the Mac merges automatically. `PC-HANDOFF.md`
  has the PC's side.

---

## 0. The repositories

| Repository | What it is |
| --- | --- |
| **`Robin-IA/Congressional-Letters-Dev`** | **Develop here.** Methodology, scripts, data, templates, tests, decisions, issues. Remote `dev` in a clone. |
| `Robin-IA/Explorer-Letters` · `internetarchivecanada/congressional-letters` | The home page, on each account. Built output. |
| `Robin-IA/Explorer-Congressional-Letters-<N>` · `internetarchivecanada/Explorer-Congressional-Letters-<N>` | One explorer per Congress, on each account. Built output. |
| `internetarchivecanada/letters-from-congress` | Private record of the original handover. Do not push to it. |
| `Robin-IA/congressional-letters` | The first single-Congress explorer. Superseded. |

**Never push to a built repository by hand.** Rebuild, then publish with
`build/publish_explorers.sh`, which publishes to Robin-IA and then runs
`build/publish_iac.sh` for Internet Archive Canada. Creating a repository is
Robin's call.

## 1. Clone

```bash
mkdir -p ~/ia && cd ~/ia
gh repo clone Robin-IA/Congressional-Letters-Dev congressional-member-letters -- -b harvest-member-letters
cd congressional-member-letters && git remote rename origin dev
```

`harvest-member-letters` is the working branch, not `main`; every PR targets
it. **Fetch before branching**: the Mac pipeline and the PC both push here.

The build writes the sites to `../explorers/` beside the clone, one folder per
repository, and `publish_iac.sh` keeps a clone of the IAC home page at
`~/ia/explorers-iac/`.

## 2. Install

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 -m unittest discover -s tests
```

`requirements.txt` pins exact versions (Pillow 13, pypdf 7) because the
versions in use on 12 November carried 54 known vulnerabilities. The Mac's own
venv predates the pins: reinstall it when the renderer is not running.

## 3. Copy the data git does not carry

The letters, text and thumbnails are not all tracked. Copy these across
whole, from the machine that has them:

| Path | What it is |
| --- | --- |
| `harvest/letters/letters-raw-*.jsonl`, `letters-parsed-*.jsonl` | Each harvest's letters, raw from CDX and parsed. The parsed files are rebuilt from the raw ones with `parse_urls.py`, which needs no network. |
| `data/letters-parsed.jsonl` | The original 2000–2026 corpus, parsed. **Its raw file, `data/letters-raw.jsonl`, is not on the Mac** (issue #2), so it cannot be re-parsed there. |
| `data/letters-119-departed-parsed.jsonl` | The 119th's departed members, parsed. |
| `data/pdf-dates.jsonl`, `data/letter-text.jsonl`, `data/letter-ocr.jsonl` | Dates, text and OCR read from the PDFs. Expensive to recreate: each meant a Wayback download. |
| `data/thumb-failures.jsonl` | Renders that failed; without it the renderer retries the slow ones. |
| `thumbs/` | Every rendered preview. Many are untracked. |
| `data/cdx-cache/`, `harvest/*/cache/` | CDX answers, so a re-export runs offline. |

**Copy in one direction only, and check which side is newer first.** A stale
copy carried over a newer one has already lost records in a sister repository,
and on 12 November the Mac's `letter-text.jsonl` held twice the records the
documentation expected.

## 4. The jobs on the Mac

Three run unattended in `~/ia/congressional-member-letters`. Start each from a
**terminal**, not from inside a Claude session (anything a session starts dies
with it), and keep the machine awake (`caffeinate`; the renderer already wraps
itself).

| Job | What it does | Log |
| --- | --- | --- |
| `build/thumbs_loop.sh 115-118 106-114 paths` | Renders previews behind the harvests, a cycle at a time | `harvest/letters/thumbs-loop.log` |
| `python3 build/ocr_letters.py --watch` | OCRs scanned letters into `data/letter-ocr.jsonl` | `harvest/letters/ocr.log` |
| `build/auto_publish.sh` | Every 15 minutes: merges the PC's return branches, and after a merge or 300 new thumbnails rebuilds every explorer and the home page and publishes to both accounts | `harvest/letters/auto-publish.log`, `~/ia/explorers/publish.log` |

**This checkout builds from its own copy of the scripts and templates.** A
change merged on GitHub reaches the sites only after the changed files here
are brought to main (`git fetch dev` and check out those paths). Do it while
`auto_publish.sh` is between rounds: no `build_congress`, `build_hub` or
`publish_` process running.

**Nothing else that fetches from the Wayback Machine should run beside the
renderer.** They share one rate limit.

## 5. Is it working?

- **Render rate:** 15–20 a minute is healthy. The loop prints it; or count
  `thumbs/` two minutes apart. Below that, look at the newest lines of
  `data/thumb-failures.jsonl`: `truncated-by-the-crawl`, `unreadable-…`,
  `not-pdf` and `http-404` are bad captures, nothing to fix; `URLError`,
  `ConnectionResetError` and `http-429` are the network, so slow down rather
  than retry harder. A `ModuleNotFoundError` means the wrong Python: use the
  venv.
- **Publishing:** each round ends with `=== all done ===` (Robin-IA) and
  `IAC === internetarchivecanada done ===` in `~/ia/explorers/publish.log`.
  A `PUSH FAILED` or `not pushing` line there says which repository.
- **Live:** a site's `index.json` from Pages carries the new `stamp`. A Pages
  build can sit queued for hours on GitHub's side; re-request it with
  `gh api -X POST repos/<owner>/<repo>/pages/builds`.

## 6. Still open

`CLAUDE.md` keeps the list, under "Open". The issues on
`Robin-IA/Congressional-Letters-Dev` have the detail.
