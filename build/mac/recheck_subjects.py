#!/usr/bin/env python3
"""Re-check filed letters for subjects (#1266): at least 4, at least 2 topics.

    python3 build/mac/recheck_subjects.py pick N OUT.json      # N letters short of the rule
    python3 build/mac/recheck_subjects.py write OUT.json ROWS.jsonl

Run ``write`` in a dev-clone worktree on a fresh branch, as mac_read.py write.

pick: filed letters (letters-reviewed.csv), not discarded, not set aside
(build/mac/skip.txt), whose subjects fall short of Robin's rule of
17 November 2026 (qa/QA-analysis-subject-analysis.md): the letter's own
topics and names (letter-topics.csv) plus its recipient when that is an
organization or office. Nearest to done first (3 subjects, then 2, ...), so
each batch moves the done count most. Each item carries the title, the current
subjects and recipient, and the text (head and tail of a long letter).

ROWS.jsonl, one object per letter:
  {"digest", "topics": [subject-list labels, the FULL list],
   "names": [organization/office/law labels, the FULL list],
   "new_term": {label, kind, broader} | [..] | null,
   "direction": "from" | "to" | "neither", "note"}

write: checks every topic is in SUBJECTS and every name is a term (or a
placed new_term), replaces the letter's letter-topics.csv row with topics +
names, records a direction row for "to"/"neither", and adds "subjects
re-checked (#1266)" to its letters-reviewed note. A letter still short says
why in its note and stays Needs Review.
"""
from __future__ import annotations

import csv
import gzip
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIPE = Path.home() / "ia" / "congressional-member-letters"
OCR = Path.home() / "ia" / "letters-from-congress-OCR"
sys.path.insert(0, str(PIPE / "build"))
import topics as topics_mod  # noqa: E402

SUBJECTS = set(topics_mod.SUBJECTS)


def rows_of(path: Path) -> list[dict]:
    return list(csv.DictReader(path.open(encoding="utf-8", newline=""))) if path.exists() else []


def vocab(base: Path):
    terms = rows_of(base / "vocabulary/terms.csv")
    org = {r["label"] for r in terms if r["kind"] in ("organization", "office") and r["status"] == "preferred"}
    pref = {r["label"] for r in terms if r["status"] == "preferred"}
    acc = {r["candidate"] for r in rows_of(base / "vocabulary/reviews.csv") if r["status"] == "accepted"}
    nodes = {r["term"] for r in rows_of(base / "vocabulary/hierarchy.csv")} | {
        r["broader"] for r in rows_of(base / "vocabulary/hierarchy.csv")}
    return org, pref | acc, nodes


def short(base: Path) -> list[tuple[str, int, int]]:
    org, _, _ = vocab(base)
    dis = {r["digest"] for r in rows_of(base / "letters-discarded/letters.csv")}
    skip = set((base / "build/mac/skip.txt").read_text().split()) if (base / "build/mac/skip.txt").exists() else set()
    tp = {r["digest"]: [t for t in r["topics"].split(";") if t] for r in rows_of(base / "vocabulary/letter-topics.csv")}
    rc = {r["digest"]: r["recipient"] for r in rows_of(base / "vocabulary/letter-recipients.csv")}
    out = []
    for r in rows_of(base / "vocabulary/letters-reviewed.csv"):
        d = r["digest"]
        if d in dis or d in skip:
            continue
        h = tp.get(d, [])
        n = len(set(h) | ({rc[d]} if rc.get(d) in org else set()))
        t = sum(1 for x in h if x in SUBJECTS)
        if n < 4 or t < 2:
            out.append((d, n, t))
    return out


def pick(n: int, out: Path) -> None:
    cand = sorted(short(PIPE), key=lambda x: (-min(x[1], 4), -x[2], x[0]))[:n]
    want = {d for d, _, _ in cand}
    texts = {}
    for f in sorted((OCR / "text").glob("*.jsonl.gz")):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                if r["digest"] in want and len(r["text"]) > len(texts.get(r["digest"], "")):
                    texts[r["digest"]] = r["text"]
    titles = {r["digest"]: r["title"] for r in rows_of(PIPE / "vocabulary/letter-titles.csv")}
    tp = {r["digest"]: r["topics"] for r in rows_of(PIPE / "vocabulary/letter-topics.csv")}
    rc = {r["digest"]: r["recipient"] for r in rows_of(PIPE / "vocabulary/letter-recipients.csv")}
    rows = []
    for d, nsub, ntop in cand:
        t = re.sub(r"[ \t]+", " ", texts.get(d, "")).strip()
        body = t if len(t) <= 6000 else t[:4500] + "\n[... middle omitted ...]\n" + t[-1500:]
        rows.append({"digest": d, "title": titles.get(d, ""), "subjects_now": tp.get(d, ""),
                     "recipient_now": rc.get(d, ""), "n_subjects": nsub, "n_topics": ntop, "text": body})
    json.dump(rows, out.open("w"), indent=1, ensure_ascii=False)
    print(f"{len(short(PIPE)):,} letters short; picked {len(rows)} -> {out}")


def write(batch: Path, rows_path: Path) -> None:
    base = Path.cwd()
    org, known, nodes = vocab(base)
    want = {r["digest"] for r in json.load(batch.open())}
    rc = {r["digest"]: r["recipient"] for r in rows_of(base / "vocabulary/letter-recipients.csv")}
    newr, newh, topics, dirs, notes, bad, still = [], [], {}, {}, {}, [], []
    import letter_text  # noqa: E402  (the pipeline's, reading its vocabulary)
    file_under = set(letter_text.organizations_to_file_under())
    added: set[str] = set()
    for line in rows_path.open(encoding="utf-8"):
        if not line.strip():
            continue
        o = json.loads(line)
        d = o["digest"]
        if d not in want:
            bad.append((d, "not in this batch")); continue
        nts = o.get("new_term") or []
        nts = [nts] if isinstance(nts, dict) else nts
        for nt in nts:
            lab = re.sub(r"\s*\([^)]*\)$", "", (nt.get("label") or "").strip())
            if not lab or lab in known:
                continue
            if nt.get("broader") not in nodes:
                bad.append((d, f"new term {lab!r}: no node {nt.get('broader')!r}")); continue
            newr.append({"candidate": lab, "letters": "1", "decision": "merge", "target": lab, "abbreviation": "",
                         "kind": nt.get("kind") or "organization", "broader": nt["broader"],
                         "reason": "a name read from the letter (#1266 re-check, the Mac)", "status": "accepted"})
            newh.append({"term": lab, "broader": nt["broader"]})
            known.add(lab); nodes.add(lab); added.add(lab)
        tops = list(dict.fromkeys(t for t in o.get("topics", []) if t))
        # A proposed new term is one of the letter's names, whether or not the
        # reader repeated it in `names` (batch 1).
        placed = [re.sub(r"\s*\([^)]*\)$", "", (nt.get("label") or "").strip()) for nt in nts]
        names = list(dict.fromkeys([n for n in o.get("names", []) if n] + [p for p in placed if p in known]))
        # A subject-list topic put under names belongs with the topics; a
        # category that is neither (a state, a caucus group) is dropped and
        # logged, and the rule check below decides if the letter is short.
        tops += [n for n in names if n in SUBJECTS and n not in tops]
        dropped = [n for n in names if n not in SUBJECTS and n not in file_under and n not in added]
        names = [n for n in names if n not in SUBJECTS and n not in dropped]
        if dropped:
            print("  dropped (not a name term):", d[:12], dropped)
        badt = [t for t in tops if t not in SUBJECTS]
        # Names must be what the build files letters under (the same test as
        # tests/test_vocabulary_by_hand): an organization or office term, or
        # one added in this batch -- not a category such as "State of Nevada".
        badn = [n for n in names if n not in file_under and n not in added]
        if badt or badn:
            bad.append((d, f"not in vocabulary: topics {badt} names {badn}")); continue
        topics[d] = ";".join(dict.fromkeys(tops + names))
        if o.get("direction") in ("to", "neither"):
            dirs[d] = o["direction"]
        n = len(set(tops + names) | ({rc[d]} if rc.get(d) in org else set()))
        mark = "subjects re-checked (#1266)"
        if n < 4 or len(tops) < 2:
            still.append(d); mark = "subjects re-checked (#1266), still short: " + (o.get("note") or "")[:200]
        notes[d] = mark

    def upsert(path: Path, key_rows: dict, make) -> None:
        rows = rows_of(path)
        fields = next(csv.reader(path.open(encoding="utf-8"))) if path.exists() else []
        seen = set()
        for r in rows:
            if r["digest"] in key_rows:
                make(r, key_rows[r["digest"]]); seen.add(r["digest"])
        extra = [r for d, v in key_rows.items() if d not in seen for r in [make({"digest": d}, v)] if r]
        with path.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
            w.writeheader(); w.writerows(rows + extra)

    def set_topics(r, v):
        r["topics"] = v; r.setdefault("source", "read from the text of the letter (the Mac, #1266 re-check)"); return r

    def set_dir(r, v):
        r["direction"] = v; r.setdefault("source", "read from the letter (the Mac, #1266 re-check)"); return r

    def set_note(r, v):
        if "note" in r and v not in (r.get("note") or ""):
            r["note"] = ((r.get("note") or "") + " " + v).strip()
        return r if "reviewed" in r else None

    upsert(base / "vocabulary/letter-topics.csv", topics, set_topics)
    upsert(base / "vocabulary/letter-direction.csv", dirs, set_dir)
    upsert(base / "vocabulary/letters-reviewed.csv", notes, set_note)
    for name, rows in (("vocabulary/reviews.csv", newr), ("vocabulary/hierarchy.csv", newh)):
        if rows:
            p = base / name
            fields = next(csv.reader(p.open(encoding="utf-8")))
            with p.open("a", encoding="utf-8", newline="") as fh:
                csv.DictWriter(fh, fieldnames=fields, lineterminator="\n").writerows(
                    [{f: r.get(f, "") for f in fields} for r in rows])
    print(json.dumps({"rechecked": len(topics), "now_meet_rule": len(topics) - len(still),
                      "still_short": len(still), "new_terms": len(newr), "direction_rows": len(dirs),
                      "unresolved": len(bad)}))
    for d, why in bad:
        print("  UNRESOLVED", d[:12], why)


if __name__ == "__main__":
    if sys.argv[1] == "pick":
        pick(int(sys.argv[2]), Path(sys.argv[3]))
    elif sys.argv[1] == "write":
        write(Path(sys.argv[2]), Path(sys.argv[3]))
