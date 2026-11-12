# PC cache return: 106th–110th Congresses

`pc-cache-106-110.zip` is the Windows PC's harvest cache for the 106th–110th,
coming **back** to the Mac. The outbound bundle is on `pc-bundle`; this is the
return leg. The 115th–118th returns separately on `pc-cache-115-118`.

**Built 12 November 2026, 00:05 local.** The range ran from 23:30 to 00:02 and
**finished clean** — two passes, no stragglers.

| | |
| --- | --- |
| Sites finished | **111 of 111** |
| Still failing | 0 |
| Never attempted | 0 |
| CDX rows held | **12,779** across 72 hosts |
| Letters exported | **514** |
| Files in the zip | 112 (flat at the root, including `requests.jsonl`) |

```
pass 1 ended: 100 sites finished, 11 left
pass 2 ended:  11 sites finished,  0 left
```

## Merging it

Per `PC-HANDOFF.md`, "Bringing results back to the Mac". The zip unpacks flat:

```bash
unzip pc-cache-106-110.zip -d ~/Downloads/pc-cache-106-110
python3 build/pc/merge_pc_cache.py ~/Downloads/pc-cache-106-110          # dry run
python3 build/pc/merge_pc_cache.py ~/Downloads/pc-cache-106-110 --apply
```

The Mac had reached none of this range, so the bundle started with an empty
cache and every site here is new. Nothing on the Mac can be overwritten.

## 39 hosts returned nothing

Reported rather than worked around, as `PC-CLAUDE.md` asks. These are the known
gap — 1999–2009, when many members had no host of their own and sat at a path
such as `house.gov/<name>/`, which the paged enumeration cannot see
(EXPLORERS.md, "Paths on shared hosts"). They are not harvest failures: each
was queried successfully and the index genuinely held no letter-shaped URL
under that hostname.

```
armey.house.gov          boyda.house.gov          cleland.senate.gov
daviddavis.house.gov     dayton.senate.gov        dennyhastert.house.gov
dewine.senate.gov        everett.house.gov        graham.senate.gov
gramm.senate.gov         hart.house.gov           helms.senate.gov
hoeffel.house.gov        houghton.house.gov       isakson.house.gov
jessejacksonjr.org       joeskeen.house.gov       johnthune.house.gov
juliacarson.house.gov    leach.house.gov          mahoney.house.gov
mccarthy.house.gov       mccrery.house.gov        millender-mcdonald.house.gov
ney.house.gov            northup.house.gov        nussle.house.gov
otter.house.gov          oxley.house.gov          pombo.house.gov
portergoss.house.gov     quinn.house.gov          regula.house.gov
reynolds.house.gov       schrock.house.gov        schwarz.house.gov
shaw.house.gov           thurmond.senate.gov      vitter.house.gov
```

Worth noting `graham.senate.gov` is in that list. Lindsey Graham is the case
that motivated the whole backfill, and `lgraham.senate.gov` gave 44 letters in
the 5 November trial — so the zero here is the *older* hostname, not the member.

Only 72 of 111 hosts carried any rows at all, which is why 111 sites produced
514 letters where 385 sites in the 115th–118th produced 27,680.

## What this run cost

It ran alongside the 115th–118th on one hotspot IP, six workers here and three
there. Finishing 111 sites in 32 minutes is about 3.5 sites a minute, the
fastest rate measured on this PC — these sites are small, one or two index
pages each.

That speed came with a cost worth recording: **connection-level failures
(`URLError`, `timeout`) rose to 24% of requests**, against 4–6% all evening on
the 115th–118th at six workers. They were spread thinly across many hosts
rather than concentrated, and every request goes to `web.archive.org` — the
host in `requests.jsonl` is only the site being asked *about* — so these are
failed connections to Wayback, not dead congressional domains.

The driver appears to be request *rate* rather than worker count: small sites
complete fast, so six workers produced about 92 requests per five minutes here
against roughly 50 on the larger 115th–118th hosts. Wayback's own failures went
the other way, 504s falling from 20% to 4%.

Measured from `requests.jsonl` over 5- and 15-minute windows while both runs
were live. One connection, one night — a thing to watch on the next cellular
run, not a settled figure.
