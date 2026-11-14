#!/usr/bin/env python3
"""Write every letter's text to the letters-from-congress-OCR repository.

    .venv/bin/python build/export_text.py                       # ~/ia/letters-from-congress-OCR
    .venv/bin/python build/export_text.py --out /some/checkout

One store for the text, so that "is this letter's text missing?" has one
answer, measured one way (#116). Before this, the text lived in two large
files on the Mac (data/letter-text.jsonl, 192 MB, and data/letter-ocr.jsonl,
138 MB), too big for GitHub, with partial copies on the PC; a count taken on
either machine disagreed with the other (30,560 letters without text on the
PC, 20,386 on the Mac, 14 November 2026).

WHAT IS WRITTEN, in OUT:

  text/<N>th.jsonl.gz   one record per scan (PDF digest) published in the
                        Nth Congress's explorer, sorted by digest:
                        digest, congresses, source, engine, chars,
                        confidence, text
  text/unpublished.jsonl.gz
                        scans with text that no explorer publishes (caucus
                        letters kept back, letters with no holder)
  coverage.json         every published letter in one bucket (below), per
                        Congress and in all, as letters and distinct scans
  COVERAGE.md           the same, as tables

THE TEXT FOR A SCAN is its text layer when that is at least MIN_CHARS (100)
characters, the longest if read more than once; otherwise its OCR, the
longest of Apple Vision's and the PC's Tesseract. ``source`` says which
("text-layer" or "ocr") and ``engine`` which OCR. A scan with neither has no
record; coverage.json says why.

The files are gzipped with no timestamp, so a Congress whose text did not
change writes the same bytes and adds nothing to the repository's history.
Nothing here commits or pushes: that is done in the OCR repository, by
branch and pull request like any other change.
"""
from __future__ import annotations

import argparse
import collections
import datetime
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "build"))
import build_congress as bc  # noqa: E402

MIN_CHARS = 100
CONGRESSES = range(106, 120)

# The buckets of #116, in the order COVERAGE.md lists them.
BUCKETS = [
    ("text_layer", "Text layer of at least 100 characters"),
    ("ocr", "OCR of at least 100 characters"),
    ("ocr_short", "OCR'd, but under 100 characters"),
    ("scan_pdf_pending", "A scan, its PDF on the Mac, OCR pending"),
    ("scan_fetch_failed", "A scan, its PDF fetch failed"),
    ("scan_not_fetched", "A scan, its PDF not fetched yet"),
    ("never_read", "Never read: a thumbnail but no text record"),
    ("render_failed", "Never read: the render failed"),
    ("not_rendered", "Never read: not rendered yet"),
    ("no_digest", "No PDF digest"),
]
USABLE = {"text_layer", "ocr"}


def jsonl(path: Path):
    if path.exists():
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                try:
                    yield json.loads(line)
                except Exception:  # noqa: BLE001 - a half-written last line
                    continue


def best_texts() -> tuple[dict, dict, dict]:
    """digest -> its best text record; and each digest's longest layer and
    OCR character counts, for the buckets."""
    layer_chars: dict[str, int] = collections.defaultdict(int)
    best: dict[str, dict] = {}
    for r in jsonl(ROOT / "data" / "letter-text.jsonl"):
        d, chars = r.get("digest"), r.get("chars") or 0
        if not d:
            continue
        layer_chars[d] = max(layer_chars[d], chars)
        if chars >= MIN_CHARS and chars > best.get(d, {}).get("chars", -1):
            best[d] = {"digest": d, "source": "text-layer", "engine": None,
                       "chars": chars, "confidence": None, "text": r.get("text") or ""}
    ocr_chars: dict[str, int] = collections.defaultdict(int)
    for r in jsonl(ROOT / "data" / "letter-ocr.jsonl"):
        d, chars = r.get("digest"), r.get("chars") or 0
        if not d:
            continue
        ocr_chars[d] = max(ocr_chars[d], chars)
        have = best.get(d)
        if have and have["source"] == "text-layer":
            continue
        if chars >= MIN_CHARS and chars > (have or {}).get("chars", -1):
            best[d] = {"digest": d, "source": "ocr", "engine": r.get("engine"),
                       "chars": chars, "confidence": r.get("confidence"),
                       "text": r.get("text") or ""}
    return best, layer_chars, ocr_chars


def bucket(d: str, layer_chars, ocr_chars, pdfs, fetch_failed, rendered, render_failed) -> str:
    if not d:
        return "no_digest"
    if layer_chars.get(d, 0) >= MIN_CHARS:
        return "text_layer"
    if ocr_chars.get(d, 0) >= MIN_CHARS:
        return "ocr"
    if d in ocr_chars:
        return "ocr_short"
    if d in layer_chars:
        if d in pdfs:
            return "scan_pdf_pending"
        return "scan_fetch_failed" if d in fetch_failed else "scan_not_fetched"
    if d in rendered:
        return "never_read"
    return "render_failed" if d in render_failed else "not_rendered"


def write_gz(path: Path, records: list[dict]) -> int:
    raw = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in records)
    data = gzip.compress(raw.encode("utf-8"), compresslevel=9, mtime=0)
    if not path.exists() or path.read_bytes() != data:
        path.write_bytes(data)
    return len(data)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=Path.home() / "ia" / "letters-from-congress-OCR")
    args = ap.parse_args()
    if not args.out.is_dir():
        sys.exit(f"{args.out}: not a folder; clone Robin-IA/letters-from-congress-OCR there first")
    (args.out / "text").mkdir(exist_ok=True)

    best, layer_chars, ocr_chars = best_texts()
    pdfs = {p.stem for p in (ROOT / "data" / "pdfs").glob("*.pdf")}
    rendered = {p.stem for p in (ROOT / "thumbs").rglob("*.webp")}
    render_failed = {r.get("digest") for r in jsonl(ROOT / "data" / "thumb-failures.jsonl")}
    fetch_failed = {r.get("digest") for r in
                    jsonl(ROOT / "harvest" / "letters" / "fetch-pdfs-failures.jsonl")}

    by, _, _ = bc.sort_letters(set(CONGRESSES))
    congresses_of: dict[str, list[int]] = collections.defaultdict(list)
    letters = {n: collections.Counter() for n in CONGRESSES}
    scans = {n: collections.defaultdict(set) for n in CONGRESSES}
    for n, rows in by.items():
        for _, _, rec in rows:
            d = rec.get("digest") or ""
            b = bucket(d, layer_chars, ocr_chars, pdfs, fetch_failed, rendered, render_failed)
            letters[n][b] += 1
            scans[n][b].add(d)
            if d and n not in congresses_of[d]:
                congresses_of[d].append(n)

    sizes = {}
    for n in CONGRESSES:
        recs = [{**best[d], "congresses": sorted(congresses_of[d])}
                for d in sorted(best) if congresses_of.get(d) and min(congresses_of[d]) == n]
        sizes[f"{n}th"] = (len(recs), write_gz(args.out / "text" / f"{n}th.jsonl.gz", recs))
    rest = [{**best[d], "congresses": []} for d in sorted(best) if d not in congresses_of]
    sizes["unpublished"] = (len(rest), write_gz(args.out / "text" / "unpublished.jsonl.gz", rest))

    def tally(counter_of, sets_of):
        return {k: {"letters": counter_of.get(k, 0), "scans": len(sets_of.get(k, ()))}
                for k, _ in BUCKETS}
    all_letters = sum((letters[n] for n in CONGRESSES), collections.Counter())
    all_scans: dict[str, set] = collections.defaultdict(set)
    for n in CONGRESSES:
        for k, v in scans[n].items():
            all_scans[k] |= v
    total = sum(all_letters.values())
    usable = sum(all_letters[k] for k in USABLE)
    coverage = {
        "measured": datetime.datetime.now().astimezone().isoformat(timespec="minutes"),
        "min_chars": MIN_CHARS,
        "published_letters": total,
        "usable_letters": usable,
        "usable_share": round(usable / total, 4) if total else 0,
        "buckets": dict(BUCKETS),
        "all": tally(all_letters, all_scans),
        "by_congress": {f"{n}th": tally(letters[n], scans[n]) for n in CONGRESSES},
        "files": {k: {"records": c, "bytes": b} for k, (c, b) in sizes.items()},
    }
    (args.out / "coverage.json").write_text(json.dumps(coverage, indent=1) + "\n", encoding="utf-8")

    lines = ["# Text coverage", "",
             f"Measured {coverage['measured']} by `build/export_text.py` in "
             "Congressional-Letters-Dev, over every letter the explorers publish. "
             f"A letter has usable text when its text layer or its OCR is at least "
             f"{MIN_CHARS} characters.", "",
             f"**{usable:,} of {total:,} published letters ({100 * usable / total:.1f}%) "
             "have usable text.**", "",
             "| | letters | scans |", "| --- | ---: | ---: |"]
    for k, label in BUCKETS:
        lines.append(f"| {label} | {all_letters.get(k, 0):,} | {len(all_scans.get(k, ())):,} |")
    lines += ["", "## By Congress, letters", "",
              "| Congress | usable | " + " | ".join(label for k, label in BUCKETS if k not in USABLE) + " |",
              "| --- | ---: | " + " | ".join("---:" for k, _ in BUCKETS if k not in USABLE) + " |"]
    for n in CONGRESSES:
        c = letters[n]
        lines.append(f"| {n}th | {sum(c[k] for k in USABLE):,} | "
                     + " | ".join(f"{c.get(k, 0):,}" for k, _ in BUCKETS if k not in USABLE) + " |")
    lines += ["", "## Files", "", "| file | records | MB |", "| --- | ---: | ---: |"]
    for k, (c, b) in sizes.items():
        lines.append(f"| `text/{k}.jsonl.gz` | {c:,} | {b / 1e6:.1f} |")
    (args.out / "COVERAGE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"{usable:,} of {total:,} published letters have usable text "
          f"({100 * usable / total:.1f}%); "
          f"{sum(c for c, _ in sizes.values()):,} texts, "
          f"{sum(b for _, b in sizes.values()) / 1e6:.1f} MB -> {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
