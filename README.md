# PC harvest bundles

This branch only carries the zips a Windows PC needs to run a range of the
letter harvest, one zip per range. Each rebuild replaces its zip in a new
commit. Nothing here is served by GitHub Pages.

| Zip | Built | Sites to do | Unzip into |
| --- | --- | --- | --- |
| `pc-harvest-115-118.zip` | 11 November 2026, 18:05 | 268 of 385 | `C:\harvest` |
| `pc-harvest-106-110.zip` | 11 November 2026, 22:05 | 111 of 111 | `C:\harvest-106-110` |
| `pc-render-106-114-paths.zip` | 12 November 2026, 11:34 | 7,260 PDFs to render | `C:\render3` |
| `pack_return.py` | 12 November 2026, 11:55 | packs thumbnails and data for the return; never PDFs | each work folder |
| `pc-ocr-106-115.zip` | 12 November 2026, 11:34 | 7,025 scans to fetch and OCR | `C:\ocr` |
| `pc-render-all-missing.zip` | 12 November 2026, 21:44 | 6,860 PDFs to render (every letter in the explorers still without a preview; replaces `pc-render-106-114-paths.zip`) | `C:\render4` |
| `pc-ocr-116-119.zip` | 12 November 2026, 21:45 | 7,198 scans to fetch and OCR (the 116th–119th; the 106th–115th stay with `pc-ocr-106-115.zip`) | `C:\ocr2` |

Both harvests are finished and returned. The render bundle is the PC's
current job, rebuilt at 09:51 on 12 November for a second run, with
`ocr_tesseract.py` beside it to OCR the scans on the PC; see "Rendering" in
`PC-CLAUDE.md`.

**One folder per range.** `run_pc.py` works out its range from the single
`harvest/letters-<range>-members.json` beside it, so two ranges must not share
a folder. Each folder keeps its own cache, and both can run at once.

**The 106th–110th is split off the 106th–114th.** The Mac kept the 111th–114th
(28 sites left at the split), so the two machines never harvest the same site.
Both bundles query CDX over https. The 106th–110th starts with an empty cache:
the Mac had not reached any of those sites.

On the PC: download the zip, unzip it into its own folder, open PowerShell in
that folder and run `py run_pc.py`. `PC-HANDOFF.md` on `harvest-member-letters`
has the rest, from "Setting up the PC". Results come back the same way for
both: zip that folder's `harvest\letters\cache`, and merge on the Mac with
`build/pc/merge_pc_cache.py`.

A Claude session on the PC should read `PC-CLAUDE.md` first.

To rebuild on the Mac: `build/pc/make_bundle.sh <range>`, then replace that
zip here.
