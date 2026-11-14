#!/usr/bin/env python3
"""Fetch again the PDFs that were rendered but not kept, so they can be OCRed.

    .venv/bin/python build/fetch_pdfs.py --dry-run     # count only
    .venv/bin/python build/fetch_pdfs.py               # fetch, 2 at a time
    .venv/bin/python build/fetch_pdfs.py --workers 1 --max 50
    .venv/bin/python build/fetch_pdfs.py --congresses 116-119   # a share of them

Before 11 November 2026 the renderer read each PDF and threw it away. For a
PDF with a text layer that lost nothing: the text was taken on the way past.
For a scan it lost the only way to its words, because ocr_letters.py reads
``data/pdfs/``. This fetches exactly those -- a text layer under
``--min-chars``, no OCR yet, no local copy -- and puts them in ``data/pdfs/``,
where ``ocr_letters.py --watch`` picks them up on its next pass.

WHICH CAPTURE. The one the renderer read: the ``captured`` timestamp in
``data/letter-text.jsonl``, at the URL the Wayback Machine holds -- the
``url`` the harvest observed, from ``data/letters-parsed.jsonl``. Not the
explorers' ``key``: that is the letter's identity, lowercased and with any
cache-busting hex prefix stripped from the file name, and the archive has
never held that spelling of a prefixed file. Asking for it is a 404 (#102:
4 of 4 failed scans that answered were a 404 by key and a PDF by url).
The key is used only where no observed url is known. The bytes are checked against the ``sha256`` the renderer recorded,
so what is kept is the very file the thumbnail was made from; a mismatch is
logged and not kept. Letters in no explorer (unpublished: caucus, or no
holder) are skipped.

Newest Congress first, the same order people search in. Resumable: a PDF
already in ``data/pdfs/`` is skipped. Failures go to
``harvest/letters/fetch-pdfs-failures.jsonl`` and are retried on the next run.
It shares the Wayback budget with the renderer, so it defaults to 2 workers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPLORERS = ROOT.parent / "explorers"
PARSED = [ROOT / "data" / "letters-parsed.jsonl",
          ROOT / "data" / "letters-119-departed-parsed.jsonl"]
PARSED_GLOB = "harvest/letters/letters-parsed-*.jsonl"
UA = {"User-Agent": "ia-congressional-member-letters/0.1 (fetch for OCR)"}


def jsonl(path: Path):
    if path.exists():
        for line in path.open(encoding="utf-8"):
            try:
                yield json.loads(line)
            except Exception:  # noqa: BLE001 - a half-written last line
                continue


def congress_set(spec: str) -> set[int]:
    """'116-119' or '106-110,115' -> the Congress numbers."""
    out: set[int] = set()
    for part in (spec or "").split(","):
        if "-" in part:
            a, b = part.split("-")
            out |= set(range(int(a), int(b) + 1))
        elif part.strip():
            out.add(int(part))
    return out


def observed_urls(digests: set[str]) -> dict[str, str]:
    """digest -> a URL the harvest saw the Wayback Machine hold it under (#102)."""
    out: dict[str, str] = {}
    # Every parsed-letter file the explorers are built from, as
    # build_congress.all_letters() reads them: the per-harvest files hold
    # about 27,000 digests found nowhere else.
    for path in [*PARSED, *sorted(ROOT.glob(PARSED_GLOB))]:
        for r in jsonl(path):
            d = r.get("digest")
            if d in digests and d not in out and r.get("url"):
                out[d] = r["url"]
    return out


def replay(ts: str, url: str) -> str:
    return (f"https://web.archive.org/web/{ts}id_/"
            + urllib.parse.quote(url, safe=":/?&=%#~+,;@!$'()*[]"))


def targets(args) -> list[tuple[int, str, str, str, str, str]]:
    text = {r["digest"]: r for r in jsonl(args.text) if r.get("digest")}
    ocr = {r["digest"] for r in jsonl(args.ocr) if r.get("digest")}
    have = {p.stem for p in args.pdfs.glob("*.pdf")}
    need = {d for d, r in text.items()
            if int(r.get("chars") or 0) < args.min_chars and d not in ocr and d not in have}
    where: dict[str, tuple[int, str]] = {}
    for f in EXPLORERS.glob("Explorer-Congressional-Letters-*/payload/member/*.json"):
        n = int(f.parts[-4].rsplit("-", 1)[1])
        for row in json.loads(f.read_text(encoding="utf-8")):
            key, digest = row[0], row[9]
            if digest in need and (digest not in where or n > where[digest][0]):
                where[digest] = (n, key)
    seen = observed_urls(set(where))
    out = [(n, d, key, text[d].get("captured") or "", text[d].get("sha256") or "",
            seen.get(d) or key)
           for d, (n, key) in where.items()]
    out.sort(key=lambda t: (-t[0], t[1]))
    print(f"{len(need):,} scans with no text and no local PDF; "
          f"{len(out):,} are in an explorer, {len(need) - len(out):,} are not (skipped)",
          file=sys.stderr)
    only = congress_set(getattr(args, "congresses", ""))
    if only:
        out = [t for t in out if t[0] in only]
        print(f"  {len(out):,} of them in the {args.congresses} share", file=sys.stderr)
    return out


def fetch(item, pdfs: Path, tries: int = 3) -> tuple[str, str]:
    n, digest, key, ts, sha, observed = item
    url = replay(ts, observed)
    last = ""
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                        timeout=120) as r:
                blob = r.read()
            if not blob.startswith(b"%PDF"):
                return digest, "not-pdf"
            if sha and hashlib.sha256(blob).hexdigest() != sha:
                return digest, "sha256-mismatch"
            part = pdfs / f"{digest}.pdf.part"
            part.write_bytes(blob)
            part.replace(pdfs / f"{digest}.pdf")
            return digest, "ok"
        except urllib.error.HTTPError as exc:
            last = f"http-{exc.code}"
            if exc.code in (403, 404, 410):
                break
        except Exception as exc:  # noqa: BLE001 - connection trouble is retried
            last = type(exc).__name__
        time.sleep(10 * (attempt + 1))
    return digest, last or "failed"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pdfs", type=Path, default=ROOT / "data" / "pdfs")
    ap.add_argument("--text", type=Path, default=ROOT / "data" / "letter-text.jsonl")
    ap.add_argument("--ocr", type=Path, default=ROOT / "data" / "letter-ocr.jsonl")
    ap.add_argument("--failures", type=Path,
                    default=ROOT / "harvest" / "letters" / "fetch-pdfs-failures.jsonl")
    ap.add_argument("--min-chars", type=int, default=100)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--max", type=int, default=0)
    ap.add_argument("--congresses", default="",
                    help="only these Congresses, e.g. 116-119; the PC takes the rest")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    todo = targets(args)
    if args.max:
        todo = todo[: args.max]
    if args.dry_run or not todo:
        return 0
    args.pdfs.mkdir(parents=True, exist_ok=True)
    started, done, ok = time.time(), 0, 0
    with ThreadPoolExecutor(args.workers) as pool:
        futs = [pool.submit(fetch, item, args.pdfs) for item in todo]
        for fut in as_completed(futs):
            digest, status = fut.result()
            done += 1
            if status == "ok":
                ok += 1
            else:
                with args.failures.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"digest": digest, "why": status,
                                         "at": time.strftime("%Y-%m-%dT%H:%M:%S")}) + "\n")
            if done % 50 == 0 or done == len(todo):
                rate = done / max(1e-9, time.time() - started) * 3600
                print(f"{time.strftime('%H:%M:%S')}  {done:,}/{len(todo):,}  "
                      f"{ok:,} kept  {rate:,.0f}/hour", file=sys.stderr, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
