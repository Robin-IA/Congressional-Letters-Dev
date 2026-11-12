"""Render letter thumbnails on a Windows PC until none are left.

    py -m pip install pypdfium2 pillow pypdf     # once
    py run_render.py

The PC's share of the thumbnail work, split off the Mac's so the two never
render the same letter. ``letters-to-render.jsonl`` lists only letters that
had no thumbnail when the bundle was built; the 52,000 already made stay on
the Mac.

Each run of build/thumbs.py downloads a letter's PDF from the Wayback Machine
once and keeps four things from it, all in this folder:

  thumbs/<digest>.webp   the 200 px thumbnail          -> back to the Mac
  pdf-dates.jsonl        the date the PDF states        -> back to the Mac
  letter-text.jsonl      the text of its first pages    -> back to the Mac
  pdfs/<digest>.pdf      the PDF itself                 -> stays here for now

Runs in batches of 400 and keeps going while a batch renders anything. It
stops when nothing is left, or after 3 batches in a row that render nothing
(what is left keeps failing). Ctrl-C is safe; run it again and finished
letters are skipped. Keeps Windows awake while it works.
"""
from __future__ import annotations

import ctypes
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
LETTERS = HERE / "letters-to-render.jsonl"
THUMBS = HERE / "thumbs"
LOG = HERE / "render-pc.log"
BATCH = os.environ.get("BATCH", "400")
WORKERS = os.environ.get("WORKERS", "2")
MAX_STUCK = 3
PAUSE = 300


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


def count_thumbs() -> int:
    return sum(1 for _ in THUMBS.glob("*.webp")) if THUMBS.exists() else 0


def main() -> int:
    try:
        import PIL, pypdf, pypdfium2  # noqa: F401,E401
    except ImportError as exc:
        sys.exit(f"{exc}. Install the PDF libraries first:\n"
                 "    py -m pip install pypdfium2 pillow pypdf")
    if not LETTERS.exists():
        sys.exit(f"{LETTERS.name} is missing: unzip the bundle into this folder.")

    say(f"=== render (PC): {WORKERS} workers, {BATCH} per batch ===")
    keep_awake(True)
    stuck = 0
    try:
        while True:
            before = count_thumbs()
            cmd = [sys.executable, str(HERE / "build" / "thumbs.py"),
                   "--parsed", str(LETTERS), "--thumbs", str(THUMBS),
                   "--pdfs", str(HERE / "pdfs"),
                   "--dates", str(HERE / "pdf-dates.jsonl"),
                   "--text", str(HERE / "letter-text.jsonl"),
                   "--failures", str(HERE / "thumb-failures.jsonl"),
                   "--workers", WORKERS, "--max", BATCH]
            out = subprocess.run(cmd, capture_output=True, text=True,
                                 encoding="utf-8", errors="replace")
            with LOG.open("a", encoding="utf-8") as log:
                log.write(out.stderr + out.stdout)
            m = re.search(r"([\d,]+) still to render", out.stderr)
            left = int(m.group(1).replace(",", "")) if m else -1
            made = count_thumbs() - before
            say(f"batch: {made} rendered; {left if left >= 0 else '?'} were still "
                f"to render at its start; {count_thumbs()} thumbnails in all")
            if out.returncode != 0:
                say(f"thumbs.py exited {out.returncode}; last lines:\n"
                    + "\n".join(out.stderr.strip().splitlines()[-5:]))
                return 1
            if left == 0:
                say("=== done: nothing left to render ===")
                return 0
            stuck = stuck + 1 if made == 0 else 0
            if stuck >= MAX_STUCK:
                say(f"=== stopping: {MAX_STUCK} batches in a row rendered nothing; "
                    "what is left keeps failing ===")
                return 0
            if made == 0:
                say(f"nothing rendered; waiting {PAUSE // 60} minutes")
                time.sleep(PAUSE)
    except KeyboardInterrupt:
        say("stopped with Ctrl-C; run again to carry on")
        return 130
    finally:
        keep_awake(False)


if __name__ == "__main__":
    raise SystemExit(main())
