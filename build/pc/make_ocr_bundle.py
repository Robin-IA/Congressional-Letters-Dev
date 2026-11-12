#!/usr/bin/env python3
"""Build the zip that carries a share of the scans' OCR to a PC.

    python3 build/pc/make_ocr_bundle.py 106-115

Writes ~/Desktop/pc-ocr-<SHARE>/pc-ocr-<SHARE>.zip holding:

  fetch_for_ocr.py    downloads each scan from Wayback (standard library only)
  ocr_tesseract.py    reads each one with Tesseract
  fetch-list.jsonl    the scans in this share: digest, key, timestamp, sha256
  letter-text.jsonl   digest and text-layer length only, which is how
                      ocr_tesseract.py picks the PDFs that need reading

The scans are the ones fetch_pdfs.py would fetch for these Congresses: a
thumbnail but no text layer, no OCR and no local PDF. Give the Mac's
fetch_pdfs.py the OTHER Congresses (--congresses) while the PC works, or both
machines fetch the same letters. Bring the OCR back with merge_render.py; it
reads letter-ocr.jsonl from the returned folder.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "build"))
import fetch_pdfs  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    share = sys.argv[1]
    args = argparse.Namespace(
        text=REPO / "data" / "letter-text.jsonl", ocr=REPO / "data" / "letter-ocr.jsonl",
        pdfs=REPO / "data" / "pdfs", min_chars=100, congresses=share)
    items = fetch_pdfs.targets(args)

    out_dir = Path.home() / "Desktop" / f"pc-ocr-{share}"
    bundle = out_dir / "bundle"
    shutil.rmtree(bundle, ignore_errors=True)
    bundle.mkdir(parents=True)
    for name in ("fetch_for_ocr.py", "ocr_tesseract.py"):
        shutil.copy2(REPO / "build" / "pc" / name, bundle / name)
    with (bundle / "fetch-list.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for n, digest, key, ts, sha in items:
            fh.write(json.dumps({"digest": digest, "key": key, "timestamp": ts,
                                 "sha256": sha, "congress": n}) + "\n")
    with (bundle / "letter-text.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for _, digest, *_ in items:
            fh.write(json.dumps({"digest": digest, "chars": 0}) + "\n")

    zpath = out_dir / f"pc-ocr-{share}.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(bundle.iterdir()):
            z.write(f, f.name)
    print(f"{len(items):,} scans in the {share} share\n"
          f"Wrote {zpath} ({zpath.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
