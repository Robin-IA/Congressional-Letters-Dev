#!/usr/bin/env python3
"""Where a harvest's time went, from the request log harvest.py writes.

    python3 build/timing_report.py harvest/letters/cache/requests.jsonl
    python3 build/timing_report.py harvest/letters/cache/requests.jsonl --hours 2

Every CDX request is one line in that log. This sums them by how they ended
(ok, timeout, http503, ConnectionResetError ...) and shows, for each, how many
there were and how much waiting they cost: the question being whether a slow
harvest is slow because each answer is slow, or because the failures are.

Seconds here are time spent inside requests. The deliberate pauses between
retries are not in the log; they are set in harvest.py's fetch() and
cdx_rows_paged(), and add 6-45 seconds after each failure.
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
from collections import defaultdict
from pathlib import Path


def load(path: Path, hours: float | None) -> list[dict]:
    since = time.time() - hours * 3600 if hours else 0
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if row.get("t", 0) >= since:
                rows.append(row)
    return rows


def report(rows: list[dict]) -> str:
    if not rows:
        return "No requests in the log for that period."
    out = []
    span = (max(r["t"] + r["s"] for r in rows) - min(r["t"] for r in rows)) / 3600
    total = sum(r["s"] for r in rows)
    out.append(f"{len(rows):,} requests over {span:.1f} hours, "
               f"{total / 3600:.1f} hours inside requests, "
               f"{len({r['pid'] for r in rows})} harvest process(es)\n")

    by = defaultdict(list)
    for r in rows:
        by[r["result"]].append(r["s"])
    out.append(f"{'result':<24}{'requests':>9}{'share':>8}"
               f"{'median s':>10}{'max s':>8}{'hours':>8}{'of time':>9}")
    for result, secs in sorted(by.items(), key=lambda kv: -sum(kv[1])):
        out.append(f"{result:<24}{len(secs):>9,}{len(secs) / len(rows):>8.0%}"
                   f"{statistics.median(secs):>10.1f}{max(secs):>8.0f}"
                   f"{sum(secs) / 3600:>8.2f}{sum(secs) / total:>9.0%}")

    kinds = defaultdict(lambda: [0, 0])
    for r in rows:
        k = "count" if r["kind"] == "count" else "page"
        kinds[k][0] += 1
        kinds[k][1] += r["result"] != "ok"
    out.append("")
    for k, (n, bad) in sorted(kinds.items()):
        out.append(f"{k} requests: {n:,}, failed {bad:,} ({bad / n:.0%})")

    # Is it getting better or worse? Failure share per hour, oldest first.
    hourly = defaultdict(lambda: [0, 0])
    for r in rows:
        h = time.strftime("%m-%d %H:00", time.localtime(r["t"]))
        hourly[h][0] += 1
        hourly[h][1] += r["result"] != "ok"
    out.append("\nby hour     requests  failed")
    for h, (n, bad) in sorted(hourly.items()):
        out.append(f"{h}  {n:>8,}  {bad / n:>6.0%}")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=Path)
    ap.add_argument("--hours", type=float, help="only the last N hours")
    a = ap.parse_args()
    print(report(load(a.log, a.hours)))


if __name__ == "__main__":
    main()
