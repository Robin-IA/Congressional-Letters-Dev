# OCR-gap fetch failures

Digests the PC could not turn into OCR text, for the Mac to pick up. `fetch-failures.csv` has one row per digest: `digest, congresses, why, url, timestamp` (the capture the PC tried). 416 rows, from the PC's two fetch passes (15 November 2026).

| `why` | rows | meaning |
|---|---|---|
| `truncated-capture-64000` | 182 | Fetched and the Wayback digest matched, but the capture is exactly 64,000 bytes: Wayback stored it cut off, so there is no xref table and PDFium cannot open it. |
| `truncated-capture-1048576` | 27 | Same, cut at exactly 1 MiB. |
| `truncated-capture-5242880` | 11 | Same, cut at exactly 5 MiB. |
| `not-pdf` | 110 | The replay did not return a PDF (HTML or an error page). |
| `URLError` | 37 | Network error twice; worth another try. |
| `http-404` | 26 | Replay not found. |
| `IncompleteRead` | 10 | Connection dropped mid-body; worth another try. |
| `no-url` | 8 | No url/timestamp in `letters-parsed.jsonl` or the PC's metadata; needs the Mac's per-harvest files. |
| `digest-mismatch` | 3 | Replay returned a PDF whose Wayback digest differs from the key. |
| `http-403` | 2 | Forbidden. |

The truncated captures are the likeliest to repay a look: another capture of the same URL may be complete (check CDX for the same `url` with a larger `length`). A complete copy has a different digest, so it would be a new row, not a replacement.

The OCR text itself is on `pc-ocr-return-106-115`. Filings of the 116th-119th OCRed letters are #367, #369, #371-#374 and #380.
