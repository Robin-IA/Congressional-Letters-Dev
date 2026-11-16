#!/usr/bin/env python3
"""Companies and other non-government organizations are topics, not recipients.

Robin, 15 November 2026:

- "We do not care about recipients except for determining the subjects and
  topics."
- "Only government officials are listed as recipients."
- A letter to a company is filed under the company, never under its chief
  executive's name, and a letter to several companies' CEOs is filed under
  each company.

So a letter whose recipient, as reviews.csv resolves it, is only companies,
nonprofits or associations (anything under "Companies and organizations" in
the hierarchy) publishes with no recipient, and carries each of those
organizations as a topic. The organization's page then opens the letter by
that tag (build_vocabulary.py), and no CEO's name is shown anywhere.

A letter addressed to a company and a member at once ("Chairman Wicker and
Mr. Zuckerberg") keeps its recipient for the member, and gains the company as
a topic too.

Resolution reads reviews.csv and hierarchy.csv, the hand-made files, never
the built terms.csv: a recipient blanked here is no longer a candidate, so a
rule that read the built vocabulary would forget the decision on the next
build.
"""

from __future__ import annotations

import csv
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEWS = ROOT / "vocabulary" / "reviews.csv"
HIERARCHY = ROOT / "vocabulary" / "hierarchy.csv"
NONGOV_ROOT = "Companies and organizations"

_ABBREV = None


def _key(label: str) -> str:
    """build_vocabulary.name_key, imported late: that module is heavy."""
    global _ABBREV
    if _ABBREV is None:
        from build_vocabulary import name_key
        _ABBREV = name_key
    return _ABBREV(label)


def _accepted() -> list[dict]:
    if not REVIEWS.exists():
        return []
    with REVIEWS.open(encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh)
                if r.get("status") == "accepted" and r.get("decision") not in ("hold", "reject")]


def _parts(row: dict) -> list[tuple[str, str, int | None, int | None]]:
    """(kind, label, from year, to year) for each target of a review."""
    out = []
    for part in (row.get("target") or "").split(";"):
        part = part.strip()
        if not part:
            continue
        lo = hi = None
        if row["decision"] == "split":
            part, _, span = part.partition("@")
            a, _, b = span.partition("-")
            lo, hi = int(a), int(b or a)
        if re.fullmatch(r"[A-Z]\d{6}", part):
            out.append(("member", part, lo, hi))
            continue
        kind = row.get("kind") or "organization"
        if row["decision"] == "joint":
            # "organization:X", "person:Y", or a bare reviewed label ("Apple;
            # Google"), taken as an organization: nongov_labels() still has to
            # place it under Companies and organizations.
            kind, _, label = part.partition(":") if ":" in part else ("organization", "", part)
            part = label.strip()
        elif row["decision"] == "member":
            kind = "member"
        out.append((kind, part.strip(), lo, hi))
    return out


@lru_cache(maxsize=1)
def nongov_labels() -> frozenset[str]:
    """Every organization filed under "Companies and organizations"."""
    parent: dict[str, str] = {}
    if HIERARCHY.exists():
        with HIERARCHY.open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if r.get("term") and r.get("broader"):
                    parent.setdefault(r["term"], r["broader"])
    for r in _accepted():
        if r.get("broader"):
            for _kind, label, _lo, _hi in _parts(r):
                parent.setdefault(label, r["broader"])

    def under(label: str) -> bool:
        seen = set()
        while label and label not in seen:
            if label == NONGOV_ROOT:
                return True
            seen.add(label)
            label = parent.get(label, "")
        return False

    labels = {label for r in _accepted() for kind, label, _lo, _hi in _parts(r)
              if kind == "organization"}
    return frozenset(lab for lab in labels if lab != NONGOV_ROOT and under(lab))


@lru_cache(maxsize=1)
def _by_key() -> dict[str, list[tuple[str, str, int | None, int | None]]]:
    out: dict[str, list] = {}
    for r in _accepted():
        out.setdefault(_key(r["candidate"]), _parts(r))
    # A recipient already written as the organization's own name ("Equifax",
    # a hand recipient from letter-recipients.csv) is that organization.
    for label in nongov_labels():
        out.setdefault(_key(label), [("organization", label, None, None)])
    return out


def companies_for(recipient: str | None, year: int | None) -> tuple[list[str], bool]:
    """The non-government organizations a recipient resolves to, and whether
    it resolves to nothing else (so the recipient is not shown)."""
    if not (recipient or "").strip():
        return [], False
    parts = _by_key().get(_key(recipient))
    if not parts:
        return [], False
    live = [p for p in parts if p[2] is None or (year is not None and p[2] <= year <= p[3])]
    if not live:
        return [], False
    orgs = list(dict.fromkeys(label for kind, label, _lo, _hi in live
                              if kind == "organization" and label in nongov_labels()))
    return orgs, len(orgs) == len(live)


def tag_of(label: str) -> str:
    """The form a label takes in a letter's topics. Topics are separated by
    commas, so a comma in a name ("American Academy of Allergy, Asthma &
    Immunology") would split it in two; the tag drops the commas."""
    return label.replace(",", "")
