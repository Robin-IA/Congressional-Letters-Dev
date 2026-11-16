# OCR-gap letters the PC could not read

398 digests the PC could not turn into OCR text, for the Mac to pick up (15 November 2026). `fetch-failures.csv`: `digest, congresses, why, cdx, url, timestamp`, where `url` and `timestamp` are the capture the PC tried. 230 are 116th-119th Congress, 168 are earlier.

The PC made two fetch passes, then asked CDX for every other `200` capture of each URL (`collapse=digest`). 18 letters were recovered that way (complete copies of the same URL, or a retry that worked) and are not in this file.

| `why` | meaning |
|---|---|
| `truncated-capture-N` | Fetched and the Wayback digest matched, but the capture is exactly N bytes (64,000, 1 MiB or 5 MiB). Wayback stored it cut off: no xref table, PDFium cannot open it. |
| `not-pdf` | The replay returned HTML or an error page, not a PDF. |
| `URLError`, `IncompleteRead` | Network failures on two attempts. |
| `http-404`, `http-403` | Replay not found, or forbidden. |
| `digest-mismatch` | The replay was a PDF whose Wayback digest differs from the key. |
| `no-url` | No url/timestamp in `letters-parsed.jsonl` or the PC's metadata; needs the Mac's per-harvest files. |

| `cdx` | meaning |
|---|---|
| `only-own-capture` | CDX lists no other PDF capture of that URL, so this digest's capture is all Wayback has. |
| `html-only` | CDX lists only `text/html` captures of that URL: it was never a PDF there. |
| `other-pdf-capture-tried-failed:...` | CDX listed another PDF capture, but fetching it failed too. |
| `no-url`, `cdx-error` | Not looked up. |

The OCR text itself is on `pc-ocr-return-106-115`. Filings of the 116th-119th OCRed letters are #367, #369, #371-#374, #380 and #397.
