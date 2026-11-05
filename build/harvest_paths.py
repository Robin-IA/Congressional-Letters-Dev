#!/usr/bin/env python3
"""Harvest the members who lived at ``house.gov/<name>/`` instead of a host.

Why this is a second pass
-------------------------
Through the 2000s most representatives had no host of their own: they sat in a
directory on the chamber's site. 391 of the 440 members the House listed in
2003 look like that, and none do by 2016. ``build/chamber_rosters.py`` keys
them host + first path segment, which is why 435 rows of
``data/member-sites.tsv`` carry a slash.

Those rows cannot go through ``harvest.py``. It names its cache after the host,
so a slash would make a subdirectory, and it enumerates a *host* when the target
is a path prefix. Both differences are small; together they are a different
query, so they are a different script.

What this is worth
------------------
Less than the host-based backfill, and worth saying so. Surveyed unfiltered,
these sites hold ten to twenty letter-shaped URLs each -- 18 under
``house.gov/abercrombie``, 15 under ``house.gov/upton``, 2 under
``house.gov/waters`` -- against hundreds for a modern senate host. Across 435
sites that is still a few thousand letters, from the years the explorer is
thinnest: 2003 to 2008 together currently hold 562.

The 435 rows are also not 435 missing members. Matching each segment against the
subdomain sites in the same file, by label and chamber: 73 are an earlier URL
for a member already in the explorer, 193 for a member already in the host
backfill queue, and 171 have no subdomain counterpart at all. So much of this is
*earlier letters for members we already have a page for*, which is the easier
half to fold in.

Only the 73 yield a bioguide, though. The 193 directory matches point at House
hosts, and the House's own directory never stated an id -- so the match names a
site, not yet a person.

Attribution is inferred, and labelled as such
---------------------------------------------
A segment is matched to a subdomain site with the same label and chamber --
``house.gov/aderholt`` to ``aderholt.house.gov``. That is a guess, not a
statement: ``house.gov/alexander`` and ``alexander.senate.gov`` are Rodney and
Lamar, two different people, and the chamber check is what catches that one.
Every row records ``attribution`` so nothing downstream mistakes the guess for
the Senate directory's stated ``bioguide_id``.

The trap
--------
**Do not pass a wildcard and ``matchType=prefix`` together.** Either alone
enumerates the prefix; together they return nothing, and an empty answer is
indistinguishable from a member who wrote no letters. That cost an afternoon
and nearly cost this whole pass -- it looked like proof there was nothing here.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harvest  # noqa: E402  sibling script, not a package

# Segments that are the chamber's own plumbing rather than a member.
# ``chamber_rosters.py`` now drops these at the source, so a current TSV has
# none and this skips nothing. It stays because an older TSV still has them and
# because a plumbing prefix is a wildcard over the whole chamber site -- the one
# query here that could run for hours and return nothing that is a letter.
NOT_A_MEMBER = {"cgi-bin", "include_content", "bin", "cgi"}

RETRIES = 3
CACHE_METHOD = "prefix-v1"


def cache_name(site: str) -> str:
    """``house.gov/upton`` -> ``house.gov__upton.json``, a legal filename."""
    return site.replace("/", "__") + ".json"


def harvest_site(site: str, cache_dir: Path) -> dict:
    cache_path = cache_dir / cache_name(site)
    cached = harvest.read_cache(cache_path)
    if cached and "error" not in cached and cached.get("method") == CACHE_METHOD:
        return cached

    result: dict = {"site": site}
    last: Exception | None = None
    for attempt in range(RETRIES):
        try:
            # The wildcard, and no matchType. See the module docstring.
            rows = harvest.cdx_rows("%s/*" % site, match_type=None)
            result["method"] = CACHE_METHOD
            result["rows"] = rows
            harvest.write_cache(cache_path, result)
            return result
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(min(45, 5 * (2 ** attempt)))
    result["error"] = str(last)[:160]
    harvest.write_cache(cache_path, result)
    return result


def build_attribution(sites_file: Path, roster: Path) -> dict[str, dict]:
    """{path site: {bioguide, matched_host, attribution}} by label and chamber."""
    rows = list(csv.DictReader(sites_file.open(encoding="utf-8"), delimiter="\t"))
    hosts = {r["host"]: r for r in rows if "/" not in r["host"]}
    explorer = {m["host"].lower().removeprefix("www."): m
                for m in json.loads(roster.read_text(encoding="utf-8"))
                if m.get("host")}

    by_label: dict[tuple[str, str], str] = {}
    for host, r in hosts.items():
        by_label[(host.split(".", 1)[0], r["chamber"])] = host

    out: dict[str, dict] = {}
    for r in rows:
        if "/" not in r["host"]:
            continue
        seg = r["host"].split("/", 1)[1]
        match = by_label.get((seg, r["chamber"]))
        if not match:
            out[r["host"]] = {"bioguide": "", "matched_host": "",
                              "attribution": "none"}
            continue
        bioguide = (hosts[match]["bioguide"]
                    or explorer.get(match, {}).get("bioguide", ""))
        out[r["host"]] = {
            "bioguide": bioguide,
            "matched_host": match,
            # "explorer" means the member has a page already; "directory" means
            # they are in the host backfill queue under that name.
            "attribution": "inferred-label-%s" % (
                "explorer" if match in explorer else "directory"),
        }
    return out


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sites", type=Path, default=root / "data" / "member-sites.tsv")
    ap.add_argument("--roster", type=Path, default=root / "data" / "members.json")
    ap.add_argument("--cache", type=Path,
                    default=root / "data" / "cdx-cache" / "paths")
    ap.add_argument("--out", type=Path,
                    default=root / "data" / "letters-paths.jsonl")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--limit", type=int, default=0,
                    help="query only the first N sites; never limits the export")
    ap.add_argument("--export-only", action="store_true",
                    help="re-filter the cache without touching the network")
    ap.add_argument("--force", action="store_true",
                    help="overwrite the output even if it would shrink by more "
                         "than a tenth")
    args = ap.parse_args()

    args.cache.mkdir(parents=True, exist_ok=True)
    attribution = build_attribution(args.sites, args.roster)

    sites = sorted(s for s in attribution if s.split("/", 1)[1] not in NOT_A_MEMBER)
    skipped = len(attribution) - len(sites)
    print("%d path-keyed sites (%d skipped as chamber plumbing)"
          % (len(sites), skipped), file=sys.stderr)

    def needs_query(site: str) -> bool:
        cached = harvest.read_cache(args.cache / cache_name(site))
        if cached is None:
            return True
        return "error" in cached or cached.get("method") != CACHE_METHOD

    queryable = sites[: args.limit] if args.limit else sites
    outstanding = [s for s in queryable if needs_query(s)]
    todo = [] if args.export_only else outstanding
    # Report what is cached, not what is being skipped: with --export-only the
    # two differ, and "0 to query (435 already cached)" over an empty cache is
    # the kind of reassuring nonsense this project keeps having to delete.
    print("  %d to query (%d cached, %d outstanding)"
          % (len(todo), len(queryable) - len(outstanding), len(outstanding)),
          file=sys.stderr)

    done = failed = 0
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(harvest_site, s, args.cache): s for s in todo}
        for future in cf.as_completed(futures):
            site = futures[future]
            done += 1
            result = future.result()
            if "error" in result:
                failed += 1
                print("  [%d/%d] %-40s FAILED %s"
                      % (done, len(todo), site, result["error"][:60]), file=sys.stderr)
            else:
                rows = result.get("rows", [])
                kept = [r for r in rows if harvest.keep(r)]
                print("  [%d/%d] %-40s %4d letters (of %d rows)"
                      % (done, len(todo), site, len(kept), len(rows)), file=sys.stderr)

    # Export reads the cache, so it covers every site ever queried, not just
    # this run's. Same reason harvest.py separates the two.
    letters, sites_with = [], 0
    for site in sites:
        cached = harvest.read_cache(args.cache / cache_name(site))
        if not cached or "error" in cached:
            continue
        kept = harvest.clean([r for r in cached.get("rows", []) if harvest.keep(r)])
        if kept:
            sites_with += 1
        meta = attribution[site]
        for row in kept:
            letters.append({"site": site, **meta, **row})

    # REFUSE TO SHRINK WITHOUT BEING TOLD TO, the same guard build_site.py
    # carries. The export reads the cache, so a run against a cold or partly
    # cleared cache writes a handful of letters over a finished pass -- and a
    # two-site trial export wrote 9 letters where 435 sites belong while this
    # was being built. The explorer has lost records to exactly this shape of
    # overwrite before.
    if args.out.exists() and not args.force:
        was = sum(1 for _ in args.out.open(encoding="utf-8"))
        if was and len(letters) < was * 0.9:
            raise SystemExit(
                "refusing to shrink: this export has "
                "%d letters against %d already written (%+.0f%%). "
                "If the cache is genuinely smaller, pass --force. If it is "
                "not, the cache is incomplete -- run without --export-only."
                % (len(letters), was, (len(letters) - was) / was * 100))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="\n") as fh:
        for letter in letters:
            fh.write(json.dumps(letter, ensure_ascii=False) + "\n")

    named = sum(1 for l in letters if l["bioguide"])
    print("\n%d letters from %d of %d sites" % (len(letters), sites_with, len(sites)))
    print("  attributable to a bioguide : %d" % named)
    print("  no attribution yet         : %d" % (len(letters) - named))
    if failed:
        print("  hosts failed this run      : %d  (re-run to retry them)" % failed)
    print("\nwrote %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
