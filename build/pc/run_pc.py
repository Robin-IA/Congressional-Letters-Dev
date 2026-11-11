"""Run one range of the letter harvest on a Windows PC until every site is done.

    py run_pc.py

The Windows stand-in for build/harvest_until_done.sh, which needs bash and
macOS's caffeinate. Same rules, so a run here behaves like a run on the Mac:

  1. wait until the Wayback Machine's CDX API answers;
  2. run build/harvest.py over the sites still to do, keeping Windows awake;
  3. count what is left. None: stop. Some: pause 5 minutes (30 if more than a
     quarter of the pass failed), then go again.

It gives up after 3 passes in a row that finish nothing and lists those sites.
Safe to stop with Ctrl-C and start again at any time: finished sites are kept
in harvest/letters/cache/ and skipped. Standard library only.
"""
from __future__ import annotations

import ctypes
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "build"))
import harvest  # noqa: E402

# The bundle carries one range's member list; its name says which range.
_lists = sorted((HERE / "harvest").glob("letters-*-members.json"))
if len(_lists) != 1:
    sys.exit(f"Expected one harvest/letters-*-members.json, found {len(_lists)}.")
RANGE = _lists[0].name[len("letters-"):-len("-members.json")]
MEMBERS_IN = HERE / "harvest" / f"letters-{RANGE}-members.json"
MEMBERS_OUT = HERE / "harvest" / "letters" / f"members-{RANGE}.json"
RAW = HERE / "harvest" / "letters" / f"letters-raw-{RANGE}.jsonl"
CACHE = HERE / "harvest" / "letters" / "cache"
LOG = HERE / "harvest" / "letters" / f"harvest-{RANGE}-pc.log"
PROBE = "https://web.archive.org/cdx/search/cdx?url=house.gov&limit=1"

PAUSE = 300
BACKOFF = 1800
MAX_STUCK = 3
WORKERS = os.environ.get("WORKERS", "2")
SITE_LINE = re.compile(r"^\s*\[\d+/\d+\]")


def say(text: str) -> None:
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S}  {text}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as log:
        log.write(line + "\n")


def keep_awake(on: bool) -> None:
    """Stop Windows sleeping while this runs (the display may still turn off)."""
    if os.name != "nt":
        return
    ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001
    flags = ES_CONTINUOUS | (ES_SYSTEM_REQUIRED if on else 0)
    ctypes.windll.kernel32.SetThreadExecutionState(flags)


def remaining() -> list[str]:
    members = json.loads(MEMBERS_IN.read_text(encoding="utf-8"))
    left = []
    for m in members:
        c = harvest.read_cache(CACHE / f"{m['host']}.json")
        if c is None or "error" in c or c.get("method") != harvest.CACHE_METHOD:
            left.append(m["host"])
    return left


def wait_for_wayback() -> None:
    waited = 0
    while True:
        try:
            with urllib.request.urlopen(PROBE, timeout=30) as r:
                if r.status == 200:
                    break
        except Exception:  # noqa: BLE001
            pass
        if waited == 0:
            say("Wayback not answering (hotspot?). Waiting.")
        time.sleep(60)
        waited += 60
    if waited:
        say(f"Wayback answering again after {waited}s.")


def run_pass() -> tuple[int, int]:
    """Run harvest.py once; echo its output; return (sites tried, failed)."""
    cmd = [sys.executable, str(HERE / "build" / "harvest.py"),
           "--members-in", str(MEMBERS_IN), "--members-out", str(MEMBERS_OUT),
           "--out", str(RAW), "--cache", str(CACHE), "--workers", WORKERS]
    tried = failed = 0
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, encoding="utf-8", errors="replace",
                          env=env) as proc, \
            LOG.open("a", encoding="utf-8") as log:
        for line in proc.stdout:
            print(line, end="", flush=True)
            log.write(line)
            if SITE_LINE.match(line):
                tried += 1
                failed += "FAILED" in line
    return tried, failed


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    keep_awake(True)
    try:
        before = len(remaining())
        say(f"=== harvest {RANGE} (PC): {before} sites to do ===")
        n = stuck = 0
        while before:
            n += 1
            wait_for_wayback()
            say(f"--- pass {n}: {before} to do ---")
            tried, failed = run_pass()
            after = len(remaining())
            say(f"pass {n} ended: {before - after} sites finished, {after} left")
            pause = PAUSE
            if tried and failed * 4 > tried:
                pause = BACKOFF
                say(f"{failed} of {tried} failed this pass: backing off for 30 minutes")
            stuck = stuck + 1 if after >= before else 0
            if stuck >= MAX_STUCK:
                say(f"Stopping: {MAX_STUCK} passes in a row finished nothing. Still failing:")
                for host in remaining():
                    say(f"    {host}")
                break
            before = after
            if after:
                time.sleep(pause)
        say(f"=== harvest {RANGE} (PC) finished: {len(remaining())} left. "
            "Zip harvest/letters/cache and bring it back to the Mac. ===")
    finally:
        keep_awake(False)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        keep_awake(False)
        print("\nStopped. Run it again to carry on; finished sites are kept.")
