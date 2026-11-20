"""How much of a letter a reader is given (Robin, 20 November 2026; PC batch 68 on).

The rule:
- A letter of 1 or 2 pages is read whole.
- A longer letter is read to 75% of its characters. The first page and the
  last page are always read whole, because they carry the letterhead, date,
  address block and signers. The rest of the 75% goes to the middle pages, in
  order from page 2. If the first and last pages alone pass 75%, both are
  still read whole.
- If that is not enough to decide the letter, the reader opens the full
  record, notes "read in full: <why>", and says so in the PR. Robin raises the
  share if this happens often.

Pages: OCR text separates pages with a form feed. A text layer has no page
breaks, so every 2,500 characters counts as a page (an OCR page's median is
about 2,400), cut at a line break where there is one.
"""
from __future__ import annotations

SHARE = 0.75
PAGE_CHARS = 2500


def pages(text: str) -> list[str]:
    """The letter's pages: by form feed if it has them, else 2,500-character runs."""
    if "\f" in text:
        return [p for p in text.split("\f") if p.strip()]
    out, rest = [], text
    while len(rest) > PAGE_CHARS:
        cut = rest.rfind("\n", PAGE_CHARS // 2, PAGE_CHARS)
        cut = cut + 1 if cut > 0 else PAGE_CHARS
        out.append(rest[:cut])
        rest = rest[cut:]
    if rest.strip() or not out:
        out.append(rest)
    return out


def reading_view(text: str) -> dict:
    """What the reader is given: {"text", "pages", "read_chars", "chars", "cut"}."""
    ps = pages(text)
    total = sum(len(p) for p in ps)
    if len(ps) <= 2:
        return {"text": "\n\f\n".join(ps), "pages": len(ps), "read_chars": total, "chars": total, "cut": False}
    budget = int(total * SHARE) - len(ps[0]) - len(ps[-1])
    parts, read = [ps[0]], len(ps[0]) + len(ps[-1])
    for i, p in enumerate(ps[1:-1], start=2):
        if budget <= 0:
            omitted = ps[i - 1:-1]
            parts.append(f"[... pages {i}-{len(ps) - 1} omitted, "
                         f"{sum(len(x) for x in omitted):,} characters ...]")
            break
        take = p[:budget]
        parts.append(take if len(take) == len(p) else
                     take + f"\n[... rest of page {i} and any pages to {len(ps) - 1} omitted ...]")
        read += len(take)
        budget -= len(take)
        if len(take) < len(p):
            break
    parts.append(ps[-1])
    return {"text": "\n\f\n".join(parts), "pages": len(ps), "read_chars": read, "chars": total,
            "cut": read < total}
