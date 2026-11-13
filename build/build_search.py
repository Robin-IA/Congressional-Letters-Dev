#!/usr/bin/env python3
"""Build each explorer's full-text search index with Pagefind.

    python3 build/build_search.py 119           # one Congress
    python3 build/build_search.py 106-119       # all of them

Run after build_congress.py: it reads the explorer as built, in
../explorers/Explorer-Congressional-Letters-<N>/, and writes the index into
its pagefind/ folder, which the explorer's search view loads.

The text is what the thumbnail pass took from each PDF's text layer
(data/letter-text.jsonl) and, for scans with no text layer, what OCR read
(data/letter-ocr.jsonl), keyed by the PDF's digest. A letter with neither is
not in the index, and is still found by its description as before.

One record per document, not per letter: a letter co-signed and posted by
several members shares one digest, and indexing it once per member would
show the same letter several times for one search. The record names every
member who posted it.

Pagefind itself runs from build/search/ (pinned in its package.json; run
`npm ci` there once). The browser needs nothing installed.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPLORERS = ROOT.parent / "explorers"
SEARCH = ROOT / "build" / "search"
MIN_CHARS = 40  # shorter than this is a stray header or a failed read, not a letter


def congresses(spec: str) -> list[int]:
    a, _, b = spec.partition("-")
    return list(range(int(a), int(b or a) + 1))


def load_text(path: Path, source: str, into: dict) -> None:
    """digest -> (text, source), keeping the longer text where both exist."""
    if not path.exists():
        return
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except ValueError:
                continue  # a half-written last line while OCR is still running
            digest, text = row.get("digest"), (row.get("text") or "").strip()
            if digest and len(text) >= MIN_CHARS and len(text) > len(into.get(digest, ("",))[0]):
                into[digest] = (text, source)


def records(explorer: Path, text: dict, congress: int) -> list[dict]:
    index = json.loads((explorer / "index.json").read_text(encoding="utf-8"))
    col = {name: i for i, name in enumerate(index["columns"])}
    names = {m["id"]: m["name"] for m in index["members"]}
    docs: dict[str, dict] = {}
    for path in sorted((explorer / "payload" / "member").glob("*.json")):
        bioguide = path.stem
        for row in json.loads(path.read_text(encoding="utf-8")):
            digest = row[col["digest"]]
            if not digest or digest not in text:
                continue
            doc = docs.setdefault(digest, {"row": row, "members": []})
            if bioguide not in doc["members"]:
                doc["members"].append(bioguide)
    out = []
    for digest, doc in docs.items():
        row, members = doc["row"], doc["members"]
        content, source = text[digest]
        subject = row[col["subject"]] or ""
        recipient = row[col["recipient"]] or ""
        title = subject or (f"Letter to {recipient}" if recipient else "Letter")
        out.append({
            # The result opens the letter itself, from the Wayback Machine,
            # the same link the explorer's own letter cards use.
            "url": f"https://web.archive.org/web/{row[col['timestamp']]}id_/{row[col['key']]}",
            "content": content,
            "language": "en",
            "meta": {
                "title": title,
                "recipient": recipient,
                "date": row[col["date"]] or "",
                "precision": row[col["precision"]] or "",
                "members": "; ".join(names.get(b, b) for b in members),
                "member_ids": ";".join(members),
                "digest": digest,
                # Which explorer the letter is in: the home page searches all
                # of them at once and links each result into its own.
                "congress": str(congress),
                # OCR text has misreadings; the page says which a match came from.
                "source": source,
            },
            "sort": {"date": row[col["date"]] or ""},
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("congresses", help="N or N-M, e.g. 119 or 106-119")
    ap.add_argument("--explorers", type=Path, default=EXPLORERS)
    args = ap.parse_args()

    if not (SEARCH / "node_modules" / "pagefind").exists():
        sys.exit(f"Pagefind is not installed: run `npm ci` in {SEARCH}")
    text: dict = {}
    load_text(ROOT / "data" / "letter-text.jsonl", "text", text)
    load_text(ROOT / "data" / "letter-ocr.jsonl", "ocr", text)
    print(f"{len(text):,} documents with text", file=sys.stderr)

    for n in congresses(args.congresses):
        explorer = args.explorers / f"Explorer-Congressional-Letters-{n}"
        if not (explorer / "index.json").exists():
            print(f"{n}th: no explorer built at {explorer}", file=sys.stderr)
            continue
        recs = records(explorer, text, n)
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as tmp:
            for r in recs:
                tmp.write(json.dumps(r, ensure_ascii=False) + "\n")
        # Into a fresh folder, swapped in only once it is complete. Pagefind
        # adds files and never removes a previous build's, so writing over
        # the old index doubled it at every build; and a failed build should
        # leave the last good index, not half of one.
        out, fresh = explorer / "pagefind", explorer / "pagefind.new"
        shutil.rmtree(fresh, ignore_errors=True)
        result = subprocess.run(["node", str(SEARCH / "index_records.mjs"), tmp.name, str(fresh)],
                                cwd=SEARCH, capture_output=True, text=True)
        Path(tmp.name).unlink()
        if result.returncode:
            shutil.rmtree(fresh, ignore_errors=True)
            print(f"{n}th: index FAILED\n{result.stderr.strip()}", file=sys.stderr)
            return 1
        shutil.rmtree(out, ignore_errors=True)
        fresh.rename(out)
        size = sum(f.stat().st_size for f in out.rglob("*") if f.is_file()) / 1048576
        ocr = sum(1 for r in recs if r["meta"]["source"] == "ocr")
        print(f"{n}th: {len(recs):,} documents indexed ({ocr:,} from OCR), {size:.1f} MB", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
