# PC render return 2: the 106th–114th and path letters

First partial return from the second render run (`C:\render2`), built from
`pc-render-106-114-paths.zip` (the 09:51 rebuild, 7,662 PDFs / 10,721 letters).
The first run's 172 are on `pc-render-return`; this branch is separate and does
not repeat them.

**Built 12 November 2026, 10:35 local. Partial — more will follow on this
branch.** The run is still going.

| | |
| --- | --- |
| Thumbnails | **154** of 7,662 (2.0%) |
| OCR records | **82** |
| Text records | 154 |
| Date records | 144 |
| Failures so far | 62 |

```
thumbs/<digest>.webp     154 files
letter-ocr.jsonl          82 lines   Tesseract 5.4.0
letter-text.jsonl        154 lines
pdf-dates.jsonl          144 lines
thumb-failures.jsonl      62 lines
```

The PDFs are on `pc-render-pdfs-2` and stay on the PC as well; nothing on the
Mac waits for them, since OCR happens here.

## OCR is working, and keeping ahead easily

`ocr_tesseract.py --watch` has been running beside the renderer since 10:07.
It reads 46–62 PDFs a minute against the renderer's 9, so it is never the
constraint, and it costs no bandwidth. Every line carries
`"engine": "tesseract-5.4.0.20240606"`.

## The failure count needs reading carefully

62 failures against 154 successes looks alarming and is mostly an artifact of
where the run started. The first 40 minutes were on a Verizon cellular hotspot
that turned out to be throttled to about 2.5 MB/min; **26 of the failures are
`URLError`**, which is a dropped connection rather than anything Wayback did.
The run moved to Charter broadband at 10:29.

Failures are not lost: `run_render.py` retries them on later batches.

## Worker counts, measured here

Nothing from the CDX harvest transferred, and the reason is worth recording.

| where | workers | MB/min | PDFs/min |
| --- | --- | --- | --- |
| hotspot (throttled) | 6 | 2.74 | 7.3 |
| hotspot (throttled) | 2 | 2.24 | 4.7 |
| broadband | 6 | 6.6 | 9.4 |
| broadband | 12 | measuring | measuring |

On the throttled hotspot the worker count barely mattered: throughput sat at
2.2–2.7 MB/min whatever we did, because the pipe was the ceiling. Dropping from
6 to 2 made it *worse*, which is the opposite of what `PC-CLAUDE.md` suggests
for connection errors — that advice assumes refusals, not a capped link.

On broadband the link is 287 Mbps and we were using about 880 kbit/s, so
Wayback's per-stream pace became the limit and concurrency is worth something
again. The PC has 8 logical cores and OCR holds 4 of them, so beyond about 12
workers local CPU may bind before Wayback does.

One morning, one connection, two of them changing underneath the measurement.
A reason to measure rather than a figure to copy.
