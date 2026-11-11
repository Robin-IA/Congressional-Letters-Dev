# PC harvest bundle

This branch only carries the zip a Windows PC needs to run one range of the
letter harvest. Each rebuild replaces the zip in a new commit. Nothing here is served by GitHub Pages.

**`pc-harvest-115-118.zip`**: built 11 November 2026 at 18:05 from the Mac's
cache. 268 of 385 sites still to do. Queries CDX over https, not http,
which answered 503 under load. An earlier copy of this zip used http: if
the PC already unzipped it, replace `harvest.py` from this zip and keep
the `cache` folder.

On the PC: download the zip from this branch, unzip it into a folder of its
own (for example `C:\harvest`), then follow `PC-HANDOFF.md` on
`harvest-member-letters` from "Setting up the PC".

To rebuild on the Mac: `build/pc/make_bundle.sh 115-118`, then replace the zip
here.
