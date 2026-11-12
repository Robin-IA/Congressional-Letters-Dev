#!/usr/bin/env python3
"""Build the zip that carries a share of the thumbnail rendering to a PC.

    python3 build/pc/make_render_bundle.py NAME LIST.jsonl [LIST.jsonl ...]
    python3 build/pc/make_render_bundle.py 106-114-paths \\
        harvest/letters/letters-parsed-106-110.jsonl \\
        harvest/letters/letters-parsed-111-114.jsonl \\
        harvest/letters/letters-parsed-paths.jsonl

Writes ~/Desktop/pc-render-NAME/pc-render-NAME.zip holding build/thumbs.py,
run_render.py, and letters-to-render.jsonl: every PDF letter in the given lists
that has no thumbnail in thumbs/ yet, so none of the ones already made travel.
The failures already recorded for those letters go too, so the PC does not
retry what the Mac has given up on.

Give the Mac's own loop the OTHER ranges while the PC works, or both machines
render the same letters. Bring results back with merge_render.py.
"""
from __future__ import annotations

import json
import shutil
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def main() -> int:
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    name, lists = sys.argv[1], [Path(p) for p in sys.argv[2:]]
    have = {p.stem for p in (REPO / "thumbs").glob("*.webp")}

    out_dir = Path.home() / "Desktop" / f"pc-render-{name}"
    bundle = out_dir / "bundle"
    shutil.rmtree(bundle, ignore_errors=True)
    (bundle / "build").mkdir(parents=True)
    shutil.copy2(REPO / "build" / "thumbs.py", bundle / "build" / "thumbs.py")
    shutil.copy2(REPO / "build" / "pc" / "run_render.py", bundle / "run_render.py")

    digests: set[str] = set()
    seen_keys: set[str] = set()
    letters = 0
    with (bundle / "letters-to-render.jsonl").open("w", encoding="utf-8",
                                                   newline="\n") as out:
        for path in lists:
            for line in path.open(encoding="utf-8"):
                rec = json.loads(line)
                d = rec.get("digest") or ""
                if ("pdf" not in (rec.get("mimetype") or "") or not d
                        or d in have or rec["key"] in seen_keys):
                    continue
                seen_keys.add(rec["key"])
                digests.add(d)
                letters += 1
                out.write(line if line.endswith("\n") else line + "\n")

    failures = REPO / "data" / "thumb-failures.jsonl"
    kept = 0
    with (bundle / "thumb-failures.jsonl").open("w", encoding="utf-8",
                                                newline="\n") as out:
        if failures.exists():
            for line in failures.open(encoding="utf-8"):
                try:
                    if json.loads(line).get("digest") in digests:
                        out.write(line)
                        kept += 1
                except Exception:  # noqa: BLE001
                    continue

    zpath = out_dir / f"pc-render-{name}.zip"
    zpath.unlink(missing_ok=True)
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(bundle.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(bundle).as_posix())
    print(f"{len(digests):,} PDFs to render ({letters:,} letters), "
          f"{kept} earlier failures carried")
    print(f"Wrote {zpath} ({zpath.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
