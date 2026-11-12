# PC render return 2: the 106th–114th and path letters

Everything the PC rendered from `pc-render-106-114-paths.zip` (the 09:51
rebuild, 7,662 PDFs / 10,721 letters) before the job was **handed back to the
Mac**. The first run's 172 are on `pc-render-return` and are not repeated here.

**Final for the PC, 12 November 2026, 11:08 local. Partial by design — the Mac
takes the remainder.**

| | |
| --- | --- |
| Thumbnails | **392** of 7,662 (5.1%) |
| **OCR records** | **288** |
| Text records | 392 |
| Date records | 351 |
| Failures | 312 |

```
thumbs/<digest>.webp     392 files
letter-ocr.jsonl         288 lines   Tesseract 5.4.0.20240606
letter-text.jsonl        392 lines
pdf-dates.jsonl          351 lines
thumb-failures.jsonl     312 lines
```

The PDFs are on `pc-render-pdfs-2` in three zips. Nothing on the Mac waits for
them: OCR was done here.

## OCR worked, and was never the constraint

`ocr_tesseract.py` read **288 of the 392** PDFs — the ones whose text layer had
under 100 characters, which is the same rule the Mac applies with Apple Vision.
It ran at **40–62 PDFs a minute** against the renderer's 7–10, beside it, at no
bandwidth cost, and finished its last pass with nothing outstanding.

That ratio is the finding worth carrying: **about three quarters of these
letters are scans with no text layer.** On the first run it was 127 of 172; here
288 of 392. Without OCR, three quarters of this corpus is invisible to any text
search.

## The 312 failures, and what they mean

All but three are `URLError` — dropped connections, not anything Wayback
refused. They are not lost; `run_render.py` re-queues them on later batches, and
the Mac will reach them.

Two causes, both now measured:

1. **A throttled cellular hotspot** for the first 40 minutes, capped at about
   2.5 MB/min regardless of settings.
2. **Too many workers.** On Charter broadband at 12 workers the PC generated
   **8.4 failures a minute**; at 6 workers, **4.1**. Halving concurrency halved
   the connection errors.

## Worker counts, measured

| connection | workers | PDFs/min | MB/min | failures/min |
| --- | --- | --- | --- | --- |
| hotspot (throttled) | 6 | 7.3 | 2.74 | — |
| hotspot (throttled) | 2 | 4.7 | 2.24 | — |
| broadband | 12 | 7.4 | 5.2 | 8.4 |
| broadband | 6 | **9.8** | 3.4 | **4.1** |
| broadband | 4 | not reached — handed off | | |

**On the throttled link the worker count barely mattered**: 2.2–2.7 MB/min
whatever we set. Dropping 6 to 2 made it *worse*, which is the opposite of what
`PC-CLAUDE.md` advises on seeing connection errors — that advice assumes Wayback
refusing, not a capped pipe. Worth distinguishing the two cases there.

**On broadband, 6 beat 12** on completion rate and halved the failures. The link
was 287 Mbps and the job used under 1% of it, so Wayback's per-stream pace is the
limit, not bandwidth.

**Read PDFs/min, not MB/min.** The job is 7,662 documents. PDF sizes swung from
350 KB to 747 KB between stretches, so MB/min moves with what happened to be in
the queue and can rank the settings backwards.

One morning, one PC, with the connection changing underneath the measurement.
A reason to measure rather than a figure to copy.
