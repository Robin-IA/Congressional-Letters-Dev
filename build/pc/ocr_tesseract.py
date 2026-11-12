#!/usr/bin/env python3
"""OCR the PC's kept PDFs that have no usable text layer, with Tesseract.

    py ocr_tesseract.py            # one pass over what is here now
    py ocr_tesseract.py --watch    # keep going beside run_render.py

The PC's counterpart to build/ocr_letters.py, which does the same on the Mac
with Apple Vision. Run it from the render folder (C:\\render2): it reads
``pdfs\\<digest>.pdf`` and ``letter-text.jsonl`` as run_render.py leaves them,
and writes ``letter-ocr.jsonl`` beside them, one line per PDF:

    {"digest", "source": "ocr", "engine": "tesseract-5.4.0", "pages",
     "chars", "confidence", "text"}

the same shape as the Mac's ``data/letter-ocr.jsonl``. ``engine`` carries the
Tesseract version, because the two engines make different mistakes and a
reader of the text should be able to tell which made it. merge_render.py
brings these lines back to the Mac, where ocr_letters.py then skips them.

WHICH PDFs, WHICH PAGES -- the same rules as the Mac, so the two halves agree:
a PDF whose text layer has fewer than ``--min-chars`` (100) characters, its
first ``--pages`` (6) pages, rendered at 300 dpi.

``confidence`` is Tesseract's mean word confidence over 0-1. It is not on the
same scale as Apple Vision's and should not be compared with it.

Tesseract is found on PATH or in C:\\Program Files\\Tesseract-OCR; ``--tesseract``
names it otherwise. Each worker runs one single-threaded Tesseract; the default
is half the cores, leaving the rest for the renderer.

With --watch it re-reads the folder every 10 minutes and stops by itself once
render-pc.log says rendering is over and nothing is left to read. Ctrl-C is
safe; run it again and PDFs already read are skipped.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
WINDOWS_DEFAULT = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")


def find_tesseract(given: str | None) -> str:
    for cand in (given, shutil.which("tesseract"),
                 str(WINDOWS_DEFAULT) if WINDOWS_DEFAULT.exists() else None):
        if cand:
            return cand
    sys.exit("Tesseract not found: install it, or pass --tesseract PATH")


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


def tsv_to_text(tsv: str) -> tuple[str, list[float]]:
    """Rebuild a page's text from Tesseract's TSV, with its word confidences.

    Words on one line are joined by spaces, lines by newlines, and paragraphs
    and blocks by a blank line, which is what Tesseract's own text output does.
    """
    lines: dict[tuple, list[str]] = {}
    confs: list[float] = []
    for row in csv.DictReader(io.StringIO(tsv), delimiter="\t",
                              quoting=csv.QUOTE_NONE):
        if row.get("level") != "5":
            continue
        word = (row.get("text") or "").strip()
        conf = float(row.get("conf") or -1)
        if not word or conf < 0:
            continue
        key = (int(row["block_num"]), int(row["par_num"]), int(row["line_num"]))
        lines.setdefault(key, []).append(word)
        confs.append(conf)
    out: list[str] = []
    prev = None
    for key in sorted(lines):
        if prev is not None and key[:2] != prev[:2]:
            out.append("")
        out.append(" ".join(lines[key]))
        prev = key
    return "\n".join(out), confs


def ocr_pdf(pdf_path: str, tess: str, pages: int, dpi: int, lang: str) -> dict:
    import pypdfium2 as pdfium
    env = dict(os.environ, OMP_THREAD_LIMIT="1")
    texts: list[str] = []
    confs: list[float] = []
    with tempfile.TemporaryDirectory() as tmp:
        doc = pdfium.PdfDocument(pdf_path)
        n = min(pages, len(doc))
        for i in range(n):
            img = doc[i].render(scale=dpi / 72).to_pil()
            p = Path(tmp) / f"p{i:02d}.png"
            img.save(p)
            res = subprocess.run([tess, str(p), "stdout", "--dpi", str(dpi),
                                  "-l", lang, "tsv"],
                                 capture_output=True, text=True, encoding="utf-8",
                                 errors="replace", timeout=300, env=env)
            if res.returncode != 0:
                raise RuntimeError(res.stderr.strip()[-200:])
            text, c = tsv_to_text(res.stdout)
            texts.append(text)
            confs.extend(c)
        doc.close()
    text = "\n\f\n".join(texts)    # form feed between pages, as on the Mac
    return {"pages": n, "chars": len(text),
            "confidence": round(sum(confs) / len(confs) / 100, 3) if confs else 0.0,
            "text": text[:60000]}


def rendering_over(log: Path) -> bool:
    if not log.exists():
        return False
    marks = [l for l in log.read_text(encoding="utf-8", errors="replace").splitlines()
             if "===" in l]
    return bool(marks) and ("=== done" in marks[-1] or "=== stopping" in marks[-1])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pdfs", type=Path, default=HERE / "pdfs")
    ap.add_argument("--text", type=Path, default=HERE / "letter-text.jsonl")
    ap.add_argument("--out", type=Path, default=HERE / "letter-ocr.jsonl")
    ap.add_argument("--tesseract", help="path to tesseract(.exe)")
    ap.add_argument("--lang", default="eng")
    ap.add_argument("--min-chars", type=int, default=100)
    ap.add_argument("--pages", type=int, default=6)
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) // 2))
    ap.add_argument("--max", type=int, default=0, help="stop after N PDFs")
    ap.add_argument("--watch", action="store_true",
                    help="keep going while run_render.py keeps PDFs")
    args = ap.parse_args()

    try:
        import pypdfium2  # noqa: F401
    except ImportError:
        sys.exit("pypdfium2 is missing: py -m pip install pypdfium2 pillow pypdf")
    tess = find_tesseract(args.tesseract)
    ver = subprocess.run([tess, "--version"], capture_output=True, text=True)
    first = (ver.stdout or ver.stderr).split()
    engine = f"tesseract-{first[1].lstrip('v')}" if len(first) > 1 else "tesseract"

    total = 0
    while True:
        chars = text_chars(args.text)
        done = done_digests(args.out)
        todo = sorted(p for p in args.pdfs.glob("*.pdf")
                      if p.stem not in done and p.stem in chars
                      and chars[p.stem] < args.min_chars)
        if args.max:
            todo = todo[: max(0, args.max - total)]
        print(f"{time.strftime('%H:%M:%S')}  {engine}, {args.workers} workers: "
              f"{len(todo):,} PDFs to read ({len(done):,} already read)",
              file=sys.stderr, flush=True)
        started = time.time()
        with ProcessPoolExecutor(args.workers) as pool:
            futs = {pool.submit(ocr_pdf, str(p), tess, args.pages, args.dpi,
                                args.lang): p for p in todo}
            for i, fut in enumerate(as_completed(futs), 1):
                pdf = futs[fut]
                try:
                    rec = fut.result()
                except Exception as exc:  # noqa: BLE001 - one bad PDF is not the run
                    print(f"  {pdf.stem}: {type(exc).__name__}: {str(exc)[:80]}",
                          file=sys.stderr)
                    continue
                line = json.dumps({"digest": pdf.stem, "source": "ocr",
                                   "engine": engine, **rec}, ensure_ascii=False)
                with args.out.open("a", encoding="utf-8", newline="\n") as fh:
                    fh.write(line + "\n")
                total += 1
                if i % 50 == 0 or i == len(todo):
                    rate = i / max(1e-9, time.time() - started) * 60
                    print(f"  {i:,}/{len(todo):,}  {rate:.0f} PDFs/min",
                          file=sys.stderr, flush=True)
        if not args.watch or (args.max and total >= args.max):
            return 0
        if not todo and rendering_over(HERE / "render-pc.log"):
            print("rendering is over and every PDF is read: done", file=sys.stderr)
            return 0
        time.sleep(600)


if __name__ == "__main__":
    raise SystemExit(main())
