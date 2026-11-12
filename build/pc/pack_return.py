"""Pack what the PC has made so it can go back to the Mac through GitHub.

    py pack_return.py C:\\render2 C:\\push\\render2
    py pack_return.py C:\\ocr     C:\\push\\ocr

The first folder is a work folder (run_render.py's, or fetch_for_ocr.py's).
The second is a git working copy of the return branch, made once as
PC-CLAUDE.md describes. Run this, then commit and push the second folder.

What it writes there, every time:

  data.zip                 every .jsonl and .log in the work folder, as they
                           stand: pdf-dates, letter-text, letter-ocr,
                           thumb-failures, fetch-failures, render-pc.log,
                           fetch-pc.log. Replaced each time; small.
  thumbs-NNNN.zip          only the thumbnails not packed before, in parts
                           under 85 MB. Earlier parts stay; nothing is sent
                           twice. packed-thumbs.txt remembers what was sent.
  README.md                counts, so the Mac can see what arrived.

Never the PDFs: they stay on the PC. Nothing on the Mac needs them.

Standard library only.
"""
from __future__ import annotations

import json
import sys
import zipfile
from datetime import datetime
from pathlib import Path

PART_BYTES = 85 * 1024 * 1024
DATA = ("pdf-dates.jsonl", "letter-text.jsonl", "letter-ocr.jsonl",
        "thumb-failures.jsonl", "fetch-failures.jsonl", "render-pc.log", "fetch-pc.log")


def lines(path: Path) -> int:
    return sum(1 for _ in path.open(encoding="utf-8", errors="replace")) if path.exists() else 0


def main() -> int:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    work, out = Path(sys.argv[1]), Path(sys.argv[2])
    if not work.is_dir():
        sys.exit(f"{work} is not a folder")
    if not (out / ".git").exists():
        sys.exit(f"{out} is not a git working copy; set it up as PC-CLAUDE.md says")

    # The data files: whole, every time.
    present = [work / n for n in DATA if (work / n).exists()]
    with zipfile.ZipFile(out / "data.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for f in present:
            z.write(f, f.name)

    # Thumbnails: only those not sent before, in parts under 85 MB.
    sent_file = out / "packed-thumbs.txt"
    sent = set(sent_file.read_text(encoding="utf-8").split()) if sent_file.exists() else set()
    thumbs = sorted((work / "thumbs").glob("*.webp")) if (work / "thumbs").exists() else []
    new = [t for t in thumbs if t.stem not in sent]
    parts, part, size = [], [], 0
    for t in new:
        if part and size + t.stat().st_size > PART_BYTES:
            parts.append(part)
            part, size = [], 0
        part.append(t)
        size += t.stat().st_size
    if part:
        parts.append(part)
    # Numbered on from the parts already there, so a name is never reused and
    # an earlier part is never overwritten.
    start = len(list(out.glob("thumbs-*.zip")))
    for i, group in enumerate(parts, start + 1):
        name = out / f"thumbs-{i:04d}.zip"
        with zipfile.ZipFile(name, "w", zipfile.ZIP_STORED) as z:   # WebP is compressed
            for t in group:
                z.write(t, f"thumbs/{t.name}")
    with sent_file.open("a", encoding="utf-8") as fh:
        for t in new:
            fh.write(t.stem + "\n")

    counts = {
        "thumbnails in the work folder": len(thumbs),
        "thumbnails sent in all": len(sent) + len(new),
        "thumbnails new in this push": len(new),
        **{f.name: lines(f) for f in present if f.suffix == ".jsonl"},
        "PDFs on the PC (not sent)": len(list((work / "pdfs").glob("*.pdf")))
                                     if (work / "pdfs").exists() else 0,
    }
    (out / "README.md").write_text(
        f"# Return from {work}\n\nPacked {datetime.now():%Y-%m-%d %H:%M} by pack_return.py.\n\n"
        "| | |\n| --- | --- |\n"
        + "".join(f"| {k} | {v:,} |\n" for k, v in counts.items())
        + "\n`data.zip` holds every .jsonl and log as they stood; `thumbs-*.zip` hold the "
          "thumbnails, each sent once. No PDFs.\n", encoding="utf-8")
    print(json.dumps(counts, indent=1))
    print(f"\n{len(parts)} new thumbnail zip(s). Now: cd {out}; git add -A; "
          "git commit -m \"...\"; git push")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
