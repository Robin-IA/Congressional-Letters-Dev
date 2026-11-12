# PC handoff: running a letter harvest on a Windows PC

**Prepared 11 November 2026** for the 115th–118th Congresses. The steps work
for any range that has a `harvest/letters-<range>-members.json`.

## What this is

A Windows PC, on a phone's hotspot, harvests one range of Congresses' letters
from the Wayback Machine. The Mac stays on its broadband connection and keeps
the other range. Results come back to the Mac when the PC is done.

The point is a second IP address. On 11 November both ranges were failing on
Wayback 503s and dropped connections while they shared one connection. The
limit is most likely per IP, so a PC on the same broadband connection would not
help.

The PC needs no clone of the repository. A small bundle carries the member
list, the harvester and every site already done. The harvester uses only
Python's standard library.

| File | Runs on | What it does |
| --- | --- | --- |
| `build/pc/make_bundle.sh` | Mac | Builds the zip for the PC |
| `build/pc/run_pc.py` | PC | The Windows version of `build/harvest_until_done.sh` |
| `build/pc/merge_pc_cache.py` | Mac | Copies the PC's finished sites into the Mac's cache |

## Before you start, on the Mac

1. **Stop the Mac's run of the same range**, or both machines will fetch the
   same sites. Press Ctrl-C in its terminal window. Leave the other range
   running.
2. Build the bundle:

   ```bash
   build/pc/make_bundle.sh 115-118
   ```

   It prints how many sites are still to do and writes
   `~/Desktop/pc-harvest-115-118/pc-harvest-115-118.zip`. The current build is
   from 18:05 on 11 November: about 2 MB, with 268 of 385 sites to do.
3. Put the zip on the `pc-bundle` branch of `Robin-IA/Congressional-Letters-Dev`
   so the PC can download it. That branch holds only the zip and a README.

If the Mac finishes a few more sites after the bundle is built, the PC simply
repeats them. Nothing is lost either way.

## What goes to the PC

One file, the zip. The easiest way is to download it on the PC from GitHub:

<https://github.com/Robin-IA/Congressional-Letters-Dev/raw/pc-bundle/pc-harvest-115-118.zip>

Google Drive, a USB stick or email work too.

**If the PC unzipped an earlier copy.** Bundles built before 18:05 on 11
November query the Wayback index over `http://`, which answered 503 to about a
fifth of requests under load. The current one uses `https://`. Copy the new
zip's `build\harvest.py` over the old one and keep the PC's
`harvest\letters\cache` folder, which holds what the PC has already done.
`run_pc.py` picks it up at the start of its next pass.

| In the zip | What it is |
| --- | --- |
| `run_pc.py` | The runner |
| `build/harvest.py` | The harvester: queries over https, keeps each CDX page as it arrives, and logs every request's time |
| `build/timing_report.py` | Reads the request log |
| `harvest/letters-<range>-members.json` | The sites to harvest |
| `harvest/letters/cache/` | Every cache file the Mac has for those sites, finished or not |

## Setting up the PC

1. Turn on the phone's hotspot and connect the PC to it, not to the home
   network. The whole point is a different IP address.
2. Check for Python. In PowerShell, run `py --version`. Any 3.9 or later works.
   If it is missing, install it from
   [python.org](https://www.python.org/downloads/windows/); nothing else needs
   installing.
3. Unzip the bundle into a folder of its own, for example `C:\harvest`. Unzip
   it fully; Windows can show a zip's contents without extracting them.
4. Plug the PC in. The runner keeps Windows from sleeping while it works, but a
   laptop on battery may still stop.

Phone data should be small. The first 105 finished sites took 9 MB in the
cache, about 85 KB a site, so 270 sites are roughly 25 MB, more with retries.
That is an estimate from the cache, not a measurement of the traffic.

## Running it

In PowerShell, from the unzipped folder:

```
cd C:\harvest
py run_pc.py
```

It should start with `=== harvest 115-118 (PC): N sites to do ===`, where N is
the number `make_bundle.sh` printed. A much bigger number means the cache
folder did not unzip into place; stop and check before it re-fetches finished
sites.

Each site prints one line. `243 letters (of 361 rows)  20m` is a success; the
minutes are the time since the pass began, not that site's time. `FAILED` lines
are expected: the runner retries them on the next pass, after 5 minutes, or 30
if more than a quarter of the pass failed. Pages that did answer are kept, so a
retry asks only for the ones that failed.

Leave the window open. To stop, press Ctrl-C; to carry on, run `py run_pc.py`
again, and finished sites are skipped. It stops by itself when every site is
done, or after 3 passes in a row that finish nothing, listing the sites still
failing. Everything it prints also goes to
`harvest\letters\harvest-<range>-pc.log`.

To go easier on the connection, run `$env:WORKERS=1; py run_pc.py` instead.
That fetches one site at a time instead of two.

Every request is also logged to `harvest\letters\cache\requests.jsonl`. To see
where the time is going:

```
py build\timing_report.py harvest\letters\cache\requests.jsonl --hours 2
```

## Bringing results back to the Mac

Only the cache comes back. It is one file per site, so merging is copying
files.

1. On the PC, right-click `C:\harvest\harvest\letters\cache` and choose Send to
   → Compressed (zipped) folder. Move `cache.zip` to the Mac.
2. On the Mac, unzip it into `~/Downloads/pc-cache`, so the site files sit
   directly in that folder.
3. See what would change. Nothing is copied yet:

   ```bash
   python3 build/pc/merge_pc_cache.py ~/Downloads/pc-cache
   ```

4. If the numbers look right, run the same command with `--apply` on the end. A
   site is copied only when the PC finished it and the Mac has not; a finished
   site on the Mac is never replaced, and nothing is deleted.
5. Rebuild the letters from the merged cache, without touching the network,
   and parse them:

   ```bash
   python3 build/harvest.py --members-in harvest/letters-115-118-members.json --members-out harvest/letters/members-115-118.json --out harvest/letters/letters-raw-115-118.jsonl --cache harvest/letters/cache --export-only
   ```

   ```bash
   python3 build/parse_urls.py --raw harvest/letters/letters-raw-115-118.jsonl --members harvest/letters/members-115-118.json --out harvest/letters/letters-parsed-115-118.jsonl
   ```

Or hand steps 2–5 to Claude Code in a session in this repository.

**Thumbnails need nothing more.** If `build/thumbs_loop.sh` is running on the
Mac, its next cycle rebuilds the letter list from the merged cache and renders
the PC's letters along with the rest. The PC only harvests; it never renders.
The loop writes its own lists to `harvest/letters/loop/`, so steps 5 and 6 are
still what produce the range's own `letters-parsed-<range>.jsonl`.

## If something goes wrong

| What you see | What to do |
| --- | --- |
| `py` is not recognized | Python is not installed, or not on the PATH. Reinstall from python.org and tick "Add python.exe to PATH". |
| `Expected one harvest/letters-*-members.json` | The zip was not fully extracted, or `run_pc.py` was moved out of its folder. Unzip again and run it from that folder. |
| Far more sites to do than `make_bundle.sh` printed | The cache did not land in `harvest\letters\cache`. Stop and check before it re-fetches. |
| `Wayback not answering` | The hotspot dropped. It waits and carries on by itself. |
| `backing off for 30 minutes` again and again | Wayback is refusing this connection too. Try `$env:WORKERS=1`, or stop and pick it up later. |
| `Stopping: 3 passes in a row finished nothing` | Those sites fail for a reason a retry will not fix. Bring the cache back anyway; the list goes into issues. |
| The PC slept or restarted | Run `py run_pc.py` again. Finished sites are skipped. |

The runner and the bundle were tested on the Mac. They have not yet been run on
Windows.
