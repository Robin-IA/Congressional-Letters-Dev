"""Merge the PC's harvest cache back into the Mac's. Run on the Mac.

    python3 build/pc/merge_pc_cache.py ~/Downloads/pc-cache
    python3 build/pc/merge_pc_cache.py ~/Downloads/pc-cache --apply

First form only reports. With --apply it copies. One file per site, and a
site's file is copied from the PC only when the PC's is a finished result and
the Mac's is missing or failed. A finished result on the Mac is never
replaced. Nothing is deleted on either side.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "build"))
import harvest  # noqa: E402


def good(entry: dict | None) -> bool:
    return (entry is not None and "error" not in entry
            and entry.get("method") == harvest.CACHE_METHOD)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("pc_cache", type=Path)
    ap.add_argument("--mac-cache", type=Path,
                    default=REPO / "harvest" / "letters" / "cache")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    files = sorted(a.pc_cache.glob("*.json"))
    if not files:
        sys.exit(f"No .json files in {a.pc_cache}. Point at the cache folder itself.")
    copy, mac_kept, pc_not_done = [], 0, 0
    for f in files:
        pc = harvest.read_cache(f)
        if not good(pc):
            pc_not_done += 1
            continue
        if good(harvest.read_cache(a.mac_cache / f.name)):
            mac_kept += 1
            continue
        copy.append(f)

    print(f"{len(files)} files from the PC")
    print(f"  {len(copy)} finished on the PC, missing or failed on the Mac -> copy")
    print(f"  {mac_kept} already finished on the Mac -> keep the Mac's")
    print(f"  {pc_not_done} not finished on the PC -> skip")
    if not a.apply:
        print("\nNothing copied. Run again with --apply to copy.")
        return
    for f in copy:
        shutil.copy2(f, a.mac_cache / f.name)
    print(f"\nCopied {len(copy)} into {a.mac_cache}")


if __name__ == "__main__":
    main()
