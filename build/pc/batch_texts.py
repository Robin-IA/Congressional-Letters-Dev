#!/usr/bin/env python3
"""The texts of a reading batch, cut to the reading rule (build/reading_view.py).

    python3 build/pc/batch_texts.py batch-68.txt > batch-68-texts.jsonl

One JSON line per digest in the batch file: digest, congresses, source,
pages, chars, read_chars, cut and text. A letter of 1-2 pages is whole; a
longer one has its first and last pages whole and the middle up to 75% of
the letter. "cut": true means part of the middle is left out. When the
letter cannot be decided from what is given, read the full record in
letters-from-congress-OCR and note "read in full: <why>".
"""
import argparse
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "build"))
from reading_view import reading_view  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("batch", type=Path, help="one digest per line (pick_list.py's output)")
    ap.add_argument("--ocr-repo", type=Path, default=ROOT.parent / "letters-from-congress-OCR")
    args = ap.parse_args()
    want = [line.split()[0] for line in args.batch.read_text(encoding="utf-8").splitlines() if line.strip()]
    wanted = set(want)
    found = {}
    for f in sorted((args.ocr_repo / "text").glob("*th.jsonl.gz")):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                if r["digest"] in wanted:
                    found[r["digest"]] = r
    out = sys.stdout
    cut = 0
    for d in want:
        r = found.get(d)
        if not r:
            out.write(json.dumps({"digest": d, "text": None, "note": "no text: needs OCR"}) + "\n")
            continue
        v = reading_view(r["text"])
        cut += v["cut"]
        out.write(json.dumps({"digest": d, "congresses": r.get("congresses"), "source": r.get("source"),
                              **v}, ensure_ascii=False) + "\n")
    print(f"{len(want):,} letters, {len(found):,} with text, {cut:,} cut to 75%", file=sys.stderr)


if __name__ == "__main__":
    main()
