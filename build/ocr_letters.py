#!/usr/bin/env python3
"""OCR the kept PDFs that have no usable text layer, with Apple Vision.

    swiftc -O build/ocr.swift -o build/ocr        # once; the binary is not committed
    .venv/bin/python build/ocr_letters.py         # resumable; Ctrl-C is safe
    .venv/bin/python build/ocr_letters.py --watch # keep going as the renderer keeps PDFs

Reads ``data/pdfs/<digest>.pdf``, which the renderer keeps, so it costs the
Wayback Machine nothing. Writes ``data/letter-ocr.jsonl``, one line per PDF:

    {"digest", "source": "ocr", "engine": "apple-vision", "pages", "chars",
     "confidence", "text"}

KEPT APART FROM THE PDF'S OWN TEXT. ``data/letter-text.jsonl`` holds the text
layer the PDF carried; OCR makes errors that a text layer does not, so its
text goes in its own file and says where it came from (EXPLORERS.md step 5).

WHICH PDFs. Those whose text layer, as the renderer recorded it, has fewer
than ``--min-chars`` characters: scans, mostly. 77% of the kept PDFs on 12
November 2026 had none at all (OCR-TEST.md). A layer that is present but
unusable -- reversed, or in a broken encoding -- is not caught by this yet.

WHICH PAGES. The first ``--pages`` (six), the same depth as the text layer, at
300 dpi. Measured at about half a second a page (OCR-TEST.md).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text_chars(path: Path) -> dict[str, int]:
    """digest -> characters of text layer the renderer found (last line wins)."""
    out: dict[str, int] = {}
    if path.exists():
        for line in path.open(encoding="utf-8"):
            try:
                row = json.loads(line)
            except Exception:  # noqa: BLE001 - a half-written last line
                continue
            if row.get("digest"):
                out[row["digest"]] = int(row.get("chars") or 0)
    return out


def done_digests(path: Path) -> set[str]:
    out: set[str] = set()
    if path.exists():
        for line in path.open(encoding="utf-8"):
            try:
                out.add(json.loads(line)["digest"])
            except Exception:  # noqa: BLE001
                continue
    return out


def ocr_pdf(pdf_path: Path, ocr_bin: Path, pages: int, dpi: int) -> dict:
    import pypdfium2 as pdfium
    with tempfile.TemporaryDirectory() as tmp:
        doc = pdfium.PdfDocument(str(pdf_path))
        n = min(pages, len(doc))
        images = []
        for i in range(n):
            img = doc[i].render(scale=dpi / 72).to_pil()
            p = Path(tmp) / f"p{i:02d}.png"
            img.save(p)
            images.append(str(p))
        doc.close()
        if not images:
            return {"pages": 0, "chars": 0, "confidence": 0.0, "text": ""}
        res = subprocess.run([str(ocr_bin), *images], capture_output=True,
                             text=True, timeout=600)
    texts, confs = [], []
    for line in res.stdout.splitlines():
        row = json.loads(line)
        if "error" in row:
            continue
        texts.append(row["text"])
        if row.get("lines"):
            confs.append(row["confidence"])
    text = "\n\f\n".join(texts)    # form feed between pages
    return {"pages": len(images), "chars": len(text),
            "confidence": round(sum(confs) / len(confs), 3) if confs else 0.0,
            "text": text[:60000]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pdfs", type=Path, default=ROOT / "data" / "pdfs")
    ap.add_argument("--text", type=Path, default=ROOT / "data" / "letter-text.jsonl")
    ap.add_argument("--out", type=Path, default=ROOT / "data" / "letter-ocr.jsonl")
    ap.add_argument("--ocr", type=Path, default=ROOT / "build" / "ocr",
                    help="the compiled build/ocr.swift")
    ap.add_argument("--min-chars", type=int, default=100,
                    help="OCR a PDF whose text layer is shorter than this")
    ap.add_argument("--pages", type=int, default=6)
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--max", type=int, default=0, help="stop after N PDFs")
    ap.add_argument("--watch", action="store_true",
                    help="when caught up, wait for the renderer to keep more")
    args = ap.parse_args()

    if not args.ocr.exists():
        sys.exit(f"{args.ocr} is missing: swiftc -O build/ocr.swift -o {args.ocr}")

    total = 0
    while True:
        chars = text_chars(args.text)
        done = done_digests(args.out)
        todo = sorted(p for p in args.pdfs.glob("*.pdf")
                      if p.stem not in done and chars.get(p.stem, 0) < args.min_chars)
        if args.max:
            todo = todo[: max(0, args.max - total)]
        print(f"{time.strftime('%H:%M:%S')}  {len(todo):,} PDFs to read "
              f"({len(done):,} already read)", file=sys.stderr, flush=True)
        started = time.time()
        for i, pdf in enumerate(todo, 1):
            try:
                rec = ocr_pdf(pdf, args.ocr, args.pages, args.dpi)
            except Exception as exc:  # noqa: BLE001 - one bad PDF is not the run
                print(f"  {pdf.stem}: {type(exc).__name__}: {str(exc)[:80]}",
                      file=sys.stderr)
                continue
            line = json.dumps({"digest": pdf.stem, "source": "ocr",
                               "engine": "apple-vision", **rec},
                              ensure_ascii=False)
            with args.out.open("a", encoding="utf-8", newline="\n") as fh:
                fh.write(line + "\n")
            total += 1
            if i % 50 == 0 or i == len(todo):
                rate = i / max(1e-9, time.time() - started) * 60
                print(f"  {i:,}/{len(todo):,}  {rate:.0f} PDFs/min",
                      file=sys.stderr, flush=True)
        if not args.watch or (args.max and total >= args.max):
            return 0
        time.sleep(600)


if __name__ == "__main__":
    raise SystemExit(main())
