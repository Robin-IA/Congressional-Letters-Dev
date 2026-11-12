# PC cache return: 115th–118th Congresses

`pc-cache-115-118.zip` is the Windows PC's harvest cache, coming **back** to the
Mac. The outbound direction is the `pc-bundle` branch; this is the return leg.

**Built 11 November 2026, 21:41 local**, from a PC on a Verizon cellular
hotspot. This branch holds only the zip and this README.

| | |
| --- | --- |
| Sites finished | **220 of 385** |
| Failed, cached and retryable | 98 |
| Never attempted | 67 |
| Still to do | **165** |
| CDX rows held | **84,444** across 219 hosts |
| Files in the zip | 323 (flat at the root) |

The PC completed **100 sites** in an evening; the bundle arrived with 268 to do.

## Merging it

Per `PC-HANDOFF.md`, "Bringing results back to the Mac". The zip unpacks flat,
so the site files land directly in the target folder:

```bash
unzip pc-cache-115-118.zip -d ~/Downloads/pc-cache
python3 build/pc/merge_pc_cache.py ~/Downloads/pc-cache          # dry run
python3 build/pc/merge_pc_cache.py ~/Downloads/pc-cache --apply
```

A site is copied only when the PC finished it and the Mac has not. A finished
site on the Mac is never replaced and nothing is deleted, so merging an
incomplete cache is safe — the 98 failed and 67 untouched sites simply stay
with whatever the Mac already has.

`requests.jsonl` is in the zip as well. It is the PC's per-request timing log,
not cache data; `merge_pc_cache.py` ignores it, and it is kept because it is
the evidence behind the worker-count note below.

## Worker counts on Windows, measured

`PC-HANDOFF.md` describes the default as two workers and offers `WORKERS=1` to
go gentler. It also says the runner had not yet been run on Windows. It has
now, and on this connection more workers was substantially better:

| `WORKERS` | sites/min |
| --- | --- |
| 1 | 0.00 over 19 min |
| 2 | 0.22–0.32 |
| 4 | 0.54 |
| **6** | **1.5** |

Refusals did not scale with concurrency the way we expected: 503s sat at
18% at two workers and 20–22% at four, while request volume doubled at an
unchanged success rate. The pile of cached failures *fell* throughout — 162 to
98 — so the extra workers cleared retries faster than they created them. The
ceiling was never found; we stopped at six.

Caveat: measured on one cellular connection over one evening, against a Wayback
index whose own load was changing. It is a reason to try more workers, not a
settled figure.

Two endpoint notes, both already in the current bundle: queries go over
`https://` because `http://` answered 503 to about a fifth of requests under
load, and Wayback's gateway abandons an expensive filtered scan at about 60
seconds with a 504 while its backend keeps computing — which is why a retry
often succeeds immediately against a warm cache.
