#!/usr/bin/env python3
"""Bring a PC's rendering back into this repository.

    python3 build/pc/merge_render.py ~/Downloads/pc-render          # dry run
    python3 build/pc/merge_render.py ~/Downloads/pc-render --apply

FOLDER is what came back from the PC, laid out as run_render.py left it:
thumbs/*.webp, pdf-dates.jsonl, letter-text.jsonl, thumb-failures.jsonl, and
optionally pdfs/*.pdf and letter-ocr.jsonl (ocr_tesseract.py). Any of them may
be missing; a thumbnails-only return is fine.

Nothing here is ever replaced or removed:
  - a thumbnail or PDF is copied only if the Mac has none of that digest;
  - a date, text or OCR line is appended only if the Mac has none for that
    digest. OCR lines go into data/letter-ocr.jsonl beside Apple Vision's and
    keep their own "engine", so ocr_letters.py skips the PDFs they cover;
  - failure lines are appended for digests that still have no thumbnail, since
    each records a real attempt and thumbs.py counts them.
Safe to run again on a later, larger return.
"""
from __future__ import annotations

import json
import shutil
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def digests_in(path: Path) -> set[str]:
    out: set[str] = set()
    if path.exists():
        for line in path.open(encoding="utf-8"):
            try:
                d = json.loads(line).get("digest")
            except Exception:  # noqa: BLE001 - a half-written last line
                continue
            if d:
                out.add(d)
    return out


def new_lines(src: Path, skip: set[str]) -> list[str]:
    lines: list[str] = []
    if src.exists():
        for line in src.open(encoding="utf-8"):
            try:
                d = json.loads(line).get("digest")
            except Exception:  # noqa: BLE001
                continue
            if d and d not in skip:
                lines.append(line if line.endswith("\n") else line + "\n")
                skip.add(d)
    return lines


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    apply = "--apply" in sys.argv
    if len(args) != 1:
        sys.exit(__doc__)
    src = Path(args[0]).expanduser()

    plan = []
    for sub, suffix, dest in (("thumbs", ".webp", REPO / "thumbs"),
                              ("pdfs", ".pdf", REPO / "data" / "pdfs")):
        files = sorted((src / sub).glob(f"*{suffix}")) if (src / sub).exists() else []
        fresh = [f for f in files if not (dest / f.name).exists()]
        print(f"{sub}: {len(files):,} from the PC, {len(fresh):,} new")
        plan.append((fresh, dest))

    data = REPO / "data"
    have_thumb = {p.stem for p in (REPO / "thumbs").glob("*.webp")}
    have_thumb |= {f.stem for f in plan[0][0]}
    appends = []
    for name in ("pdf-dates.jsonl", "letter-text.jsonl", "letter-ocr.jsonl"):
        lines = new_lines(src / name, digests_in(data / name))
        print(f"{name}: {len(lines):,} new lines")
        appends.append((data / name, lines))
    # Failure lines, repeats included, since thumbs.py counts them per digest.
    # The bundle carried the Mac's own lines for these letters to the PC, so
    # only the PC's extra attempts come back: per (digest, why), the PC's
    # count less the Mac's.
    def tally(path: Path) -> Counter:
        c: Counter = Counter()
        if path.exists():
            for line in path.open(encoding="utf-8"):
                try:
                    row = json.loads(line)
                except Exception:  # noqa: BLE001
                    continue
                if row.get("digest"):
                    c[(row["digest"], row.get("why", ""))] += 1
        return c
    mac, pc = tally(data / "thumb-failures.jsonl"), tally(src / "thumb-failures.jsonl")
    fails = [json.dumps({"digest": d, "why": why}) + "\n"
             for (d, why), n in pc.items() if d not in have_thumb
             for _ in range(max(0, n - mac[(d, why)]))]
    print(f"thumb-failures.jsonl: {len(fails):,} lines for letters still without a thumbnail")
    appends.append((data / "thumb-failures.jsonl", fails))

    if not apply:
        print("\nNothing copied. Run again with --apply to copy.")
        return 0
    for fresh, dest in plan:
        dest.mkdir(parents=True, exist_ok=True)
        for f in fresh:
            part = dest / (f.name + ".part")
            shutil.copy2(f, part)
            part.replace(dest / f.name)
    for path, lines in appends:
        if lines:
            with path.open("a", encoding="utf-8", newline="\n") as fh:
                fh.writelines(lines)
    print("\nMerged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
