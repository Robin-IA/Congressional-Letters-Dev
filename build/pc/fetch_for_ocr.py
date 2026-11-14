"""Fetch scanned letters from the Wayback Machine on a Windows PC, for OCR.

    py fetch_for_ocr.py                 # in C:\\ocr, beside fetch-list.jsonl
    $env:WORKERS=4; py fetch_for_ocr.py

The PC's share of the scans that were rendered before PDFs were kept, so they
have a thumbnail but no text. ``fetch-list.jsonl`` lists them, one per line:
{digest, key, url, timestamp, sha256, congress}. Each PDF is downloaded once from
the exact capture the thumbnail was made from, checked against the sha256 the
renderer recorded, and kept in ``pdfs\\<digest>.pdf``. ``ocr_tesseract.py
--watch``, running beside it in a second window, reads each one and writes
``letter-ocr.jsonl``.

Only the standard library: nothing to install for this half.

Runs in passes. A pass tries everything not yet kept; failures are logged to
``fetch-failures.jsonl`` and tried again on the next pass, after a pause. It
stops when everything is kept, or after 3 passes in a row that keep nothing,
and then writes ``=== done`` to ``fetch-pc.log`` so ocr_tesseract.py knows to
finish once it has read the last PDF. Ctrl-C is safe; run it again to carry on.
Keeps Windows awake while it works.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIST = HERE / "fetch-list.jsonl"
PDFS = HERE / "pdfs"
LOG = HERE / "fetch-pc.log"
FAILURES = HERE / "fetch-failures.jsonl"
WORKERS = int(os.environ.get("WORKERS", "6"))
MAX_STUCK = 3
PAUSE = 300
UA = {"User-Agent": "ia-congressional-member-letters/0.1 (fetch for OCR)"}


def say(text: str) -> None:
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S}  {text}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as log:
        log.write(line + "\n")


def keep_awake(on: bool) -> None:
    if os.name != "nt":
        return
    ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001
    ctypes.windll.kernel32.SetThreadExecutionState(
        ES_CONTINUOUS | (ES_SYSTEM_REQUIRED if on else 0))


def asked(item: dict) -> str:
    """The URL to ask for: the one the archive holds (``url``), not ``key``.

    ``key`` is the letter's identity, with any hex prefix stripped from the
    file name; the archive never held that spelling, so asking for it was a
    404 for most of the scans once marked dead (#102). Older lists have no
    ``url`` and fall back to ``key``.
    """
    return item.get("url") or item["key"]


def fetch(item: dict) -> tuple[str, str]:
    digest = item["digest"]
    url = (f"https://web.archive.org/web/{item['timestamp']}id_/"
           + urllib.parse.quote(asked(item), safe=":/?&=%#~+,;@!$'()*[]"))
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                    timeout=120) as r:
            blob = r.read()
    except urllib.error.HTTPError as exc:
        return digest, f"http-{exc.code}"
    except Exception as exc:  # noqa: BLE001 - connection trouble: next pass
        return digest, type(exc).__name__
    if not blob.startswith(b"%PDF"):
        return digest, "not-pdf"
    if item.get("sha256") and hashlib.sha256(blob).hexdigest() != item["sha256"]:
        return digest, "sha256-mismatch"
    part = PDFS / f"{digest}.pdf.part"
    part.write_bytes(blob)
    part.replace(PDFS / f"{digest}.pdf")
    return digest, "ok"


def main() -> int:
    if not LIST.exists():
        sys.exit(f"{LIST.name} is missing: unzip the bundle into this folder.")
    items = [json.loads(line) for line in LIST.open(encoding="utf-8") if line.strip()]
    PDFS.mkdir(exist_ok=True)
    # A 404 or 410 will not change on a retry of the same URL; everything
    # else might. A failure is final only for the URL that was asked: rows
    # written before the list carried ``url`` asked for ``key`` and record no
    # URL, so those letters are tried again at the address the archive holds.
    now = {i["digest"]: asked(i) for i in items}
    final = set()
    if FAILURES.exists():
        for line in FAILURES.open(encoding="utf-8"):
            try:
                row = json.loads(line)
            except Exception:  # noqa: BLE001
                continue
            if (row.get("why") in ("http-404", "http-410", "not-pdf", "sha256-mismatch")
                    and row.get("asked") and row.get("asked") == now.get(row["digest"])):
                final.add(row["digest"])

    say(f"=== fetch for OCR (PC): {len(items):,} scans, {WORKERS} workers ===")
    keep_awake(True)
    stuck = 0
    try:
        while True:
            todo = [i for i in items
                    if not (PDFS / f"{i['digest']}.pdf").exists() and i["digest"] not in final]
            if not todo:
                say("=== done: every PDF that can be fetched is here ===")
                return 0
            say(f"pass: {len(todo):,} to fetch")
            kept = 0
            started = time.time()
            with ThreadPoolExecutor(WORKERS) as pool:
                for n, fut in enumerate(as_completed(pool.submit(fetch, i) for i in todo), 1):
                    digest, status = fut.result()
                    if status == "ok":
                        kept += 1
                    else:
                        if status in ("http-404", "http-410", "not-pdf", "sha256-mismatch"):
                            final.add(digest)
                        with FAILURES.open("a", encoding="utf-8") as fh:
                            fh.write(json.dumps({"digest": digest, "why": status,
                                                 "asked": now.get(digest)}) + "\n")
                    if n % 100 == 0:
                        rate = n / max(1e-9, time.time() - started) * 3600
                        say(f"  {n:,}/{len(todo):,}  {kept:,} kept  {rate:,.0f}/hour")
            say(f"pass ended: {kept:,} kept of {len(todo):,}")
            stuck = stuck + 1 if kept == 0 else 0
            if stuck >= MAX_STUCK:
                say(f"=== done: {MAX_STUCK} passes in a row kept nothing; "
                    "what is left keeps failing ===")
                return 0
            time.sleep(PAUSE)
    except KeyboardInterrupt:
        say("stopped with Ctrl-C; run again to carry on")
        return 130
    finally:
        keep_awake(False)


if __name__ == "__main__":
    raise SystemExit(main())
