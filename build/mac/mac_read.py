#!/usr/bin/env python3
"""Mac reading batches for the 106th-115th (Robin, 17 November 2026).

  mac_read.py pick N OUT.json [SKIP.txt]   -- next N unread letters, with text and posting
  mac_read.py split OUT.json K              -- OUT-1.json .. OUT-K.json, one per reader
  mac_read.py subjects FILE                 -- the SUBJECTS list readers must choose from
  mac_read.py write OUT.json ROWS.jsonl     -- validate readers' rows and append them

The whole procedure is in MAC-READING.md.

Run `pick` from the pipeline (~/ia/congressional-member-letters) and `write` from
a dev-clone worktree on a fresh branch. ROWS.jsonl: one JSON object per letter:

  {"digest", "status": "file"|"partial"|"notletter"|"unsure",
   "title", "recipient", "topics": [...], "companies": [...],
   "date": "YYYY-MM-DD" or "", "precision": "day"|"month"|"year", "date_source",
   "note", "new_term": {"label", "kind": "organization"|"office", "broader"} or null,
   "joint": [labels or bioguide ids] or null}

`write` files what it can and lists the rest as UNRESOLVED (for issues).
"""
from __future__ import annotations

import csv
import glob
import gzip
import json
import re
import sys
from pathlib import Path

HOME = Path.home()
PIPE = HOME / "ia/congressional-member-letters"
OCR = HOME / "ia/letters-from-congress-OCR"
TODAY = "2026-11-17"
SRC = "read from the text of the letter (the Mac)"
FILES = ("vocabulary/letters-reviewed.csv", "letters-vocabulary-needs/letters.csv",
         "letters-discarded/letters.csv")


def digests(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {r["digest"] for r in csv.DictReader(path.open(encoding="utf-8")) if r.get("digest")}


def pick(n: int, out: Path, skip_file: str | None) -> None:
    taken = set().union(*(digests(PIPE / f) for f in FILES))
    if skip_file:
        taken |= {l.strip() for l in open(skip_file) if l.strip()}
    cand = []
    for r in csv.DictReader((OCR / "progress.csv").open(encoding="utf-8")):
        cs = [int(c) for c in r["congresses"].replace(";", " ").split() if c.isdigit()]
        if not cs or min(cs) > 115 or r["text"] != "True" or r["reviewed"] != "False":
            continue
        if r["digest"] in taken:
            continue
        cand.append((-len(r["members"].split(";")), -max(cs), r["digest"], min(cs), r))
    cand.sort()
    chosen = {c[2]: c for c in cand[:n]}
    # text
    texts = {}
    for c in sorted({c[3] for c in chosen.values()}):
        with gzip.open(OCR / f"text/{c}th.jsonl.gz", "rt", encoding="utf-8") as fh:
            for line in fh:
                if '"digest"' not in line:
                    continue
                r = json.loads(line)
                if r["digest"] in chosen:
                    texts[r["digest"]] = r["text"]
    # postings
    posts: dict[str, list] = {}
    for ex in sorted(glob.glob(str(HOME / "ia/explorers/Explorer-Congressional-Letters-1*"))):
        idx = json.load(open(Path(ex) / "index.json"))
        names = {m["id"]: m.get("name", m["id"]) for m in idx.get("members", [])}
        cong = ex.rsplit("-", 1)[1]
        for f in glob.glob(f"{ex}/payload/member/*.json"):
            mid = Path(f).stem
            for row in json.load(open(f)):
                if row[9] in chosen:
                    posts.setdefault(row[9], []).append({
                        "congress": cong, "member": names.get(mid, mid), "bioguide": mid,
                        "file": row[10] or row[0], "capture": row[1], "date_now": row[3],
                        "precision_now": row[4], "recipient_now": row[5], "subject_now": row[6]})
    rows = []
    for d, c in chosen.items():
        t = re.sub(r"[ \t]+", " ", texts.get(d, "")).strip()
        # The head carries the letterhead, date and address; the tail carries
        # the signers, which a plain cut at 4,500 characters lost (batch 1).
        body = t if len(t) <= 6000 else t[:4500] + "\n[... middle omitted ...]\n" + t[-1500:]
        rows.append({"digest": d, "congresses": c[4]["congresses"], "postings": posts.get(d, [])[:6],
                     "text": body, "text_cut": len(t) > 6000})
    json.dump(rows, open(out, "w"), indent=1, ensure_ascii=False)
    print(f"{len(cand):,} left in 106-115; picked {len(rows)} -> {out}")


# ------------------------------------------------------------------ write

STATE_NODE = re.compile(r"^(.+?) (state officials|state government agencies|local government and agencies|organizations)$")


def ensure(node: str, nodes: set, newh: list) -> bool:
    """Build a missing state chain up to State and local government (as add_terms.ensure)."""
    m = STATE_NODE.match(node or "")
    if not m:
        return False
    st, kind = m.groups()
    up = f"State of {st}" if kind == "state officials" else f"{st} agencies and organizations"
    newh.append({"term": node, "broader": up}); nodes.add(node)
    if up not in nodes:
        if up.startswith("State of "):
            newh.append({"term": up, "broader": "State and local government"}); nodes.add(up)
        else:
            sof = f"State of {st}"
            newh.append({"term": up, "broader": sof}); nodes.add(up)
            if sof not in nodes:
                newh.append({"term": sof, "broader": "State and local government"}); nodes.add(sof)
    return True


def write(batch: Path, rows_path: Path) -> None:
    sys.path.insert(0, str(Path("build").resolve()))
    import progress  # noqa: E402
    import topics  # noqa: E402
    subjects = set(topics.SUBJECTS) if not isinstance(topics.SUBJECTS, dict) else set(topics.SUBJECTS)
    # The built vocabulary in a dev clone lags; the pipeline's is current.
    progress.VOCAB = PIPE / "vocabulary"
    known_terms = progress.recipient_terms()
    key = progress.name_key
    reviews = list(csv.DictReader(open("vocabulary/reviews.csv", encoding="utf-8")))
    accepted = {key(r["candidate"]) for r in reviews if r.get("status") == "accepted"}
    hier = list(csv.DictReader(open("vocabulary/hierarchy.csv", encoding="utf-8")))
    nodes = {h["term"] for h in hier} | {h["broader"] for h in hier if h["broader"]}
    labels_kind = {}
    for r in csv.DictReader(open(PIPE / "vocabulary/terms.csv", encoding="utf-8")):
        labels_kind[r["label"]] = r["kind"]
    members = {r["term_id"][2:]: r["label"] for r in csv.DictReader(open(PIPE / "vocabulary/terms.csv", encoding="utf-8"))
               if r["term_id"].startswith("M-")}
    org_labels = {lab for lab, k in labels_kind.items() if k == "organization"}

    def known(label: str) -> bool:
        return label == "(no recipient)" or known_terms.get(key(label)) == "preferred" or key(label) in accepted

    batch_d = {o["digest"]: o for o in json.load(open(batch))}
    T, P, R, D, V, NEWR, NEWH, unresolved, partial, notletter = ([] for _ in range(10))
    for line in open(rows_path, encoding="utf-8"):
        if not line.strip():
            continue
        o = json.loads(line)
        d = o["digest"]
        if d not in batch_d:
            unresolved.append((d, "digest not in this batch")); continue
        st = o.get("status", "file")
        if st == "partial":
            partial.append(d); continue
        if st == "notletter":
            notletter.append((d, o.get("title", ""), o.get("note", ""))); continue
        if st == "unsure":
            unresolved.append((d, o.get("note") or "reader unsure")); continue
        rec = (o.get("recipient") or "").strip()
        nts = o.get("new_term") or []
        nts = [nts] if isinstance(nts, dict) else nts
        placed = True
        for nt in nts:
            lab = (nt.get("label") or "").strip()
            if not lab or known(lab):
                continue
            b = nt.get("broader") or ""
            if b not in nodes and not ensure(b, nodes, NEWH):
                placed = False; break
            NEWR.append({"candidate": lab, "letters": "1", "decision": "merge", "target": lab, "abbreviation": "",
                         "kind": nt.get("kind") or "organization", "broader": b,
                         "reason": "a recipient read from the letter's address block (Mac reading, 106th-115th)",
                         "status": "accepted"})
            NEWH.append({"term": lab, "broader": b})
            accepted.add(key(lab)); nodes.add(lab)
        if not placed:
            unresolved.append((d, f"new term: no place {b!r} in the hierarchy")); continue
        if not rec and len(nts) == 1 and not o.get("joint"):
            rec = nts[0]["label"]
        if o.get("joint"):
            ids = []
            for j in o["joint"]:
                if j in members:
                    ids.append(j)
                elif known(j):
                    ids.append(j)
                else:
                    ids = None; break
            if ids is None:
                unresolved.append((d, f"joint addressee not a term: {o['joint']}")); continue
            kind = "member" if all(i in members for i in ids) else ""
            if not rec or rec.endswith(")"):
                rec = ", ".join(members.get(i, i) for i in ids[:-1]) + " and " + members.get(ids[-1], ids[-1])
            if not known(rec):
                NEWR.append({"candidate": rec, "letters": "1", "decision": "joint", "target": ";".join(ids),
                             "abbreviation": "", "kind": kind, "broader": "",
                             "reason": "checked: the addressees named in the letter (Mac reading, 106th-115th)",
                             "status": "accepted"})
                accepted.add(key(rec))
        if not known(rec):
            unresolved.append((d, f"recipient {rec!r} is not a term")); continue
        tops = [t for t in o.get("topics", []) if t]
        bad = [t for t in tops if t not in subjects]
        if bad:
            unresolved.append((d, f"subjects not in SUBJECTS: {bad}")); continue
        if not tops:
            unresolved.append((d, "no subject")); continue
        comps = [c for c in o.get("companies", []) if c]
        badc = [c for c in comps if not known(c)]
        if badc:
            unresolved.append((d, f"companies not terms: {badc}")); continue
        post = (batch_d[d]["postings"] or [{}])[0]
        T.append({"digest": d, "title": o["title"], "source": SRC})
        P.append({"digest": d, "topics": ";".join(tops[:8] + comps), "source": SRC})
        R.append({"digest": d, "recipient": rec, "source": (o.get("recipient_source") or "read from the letter's address block (the Mac)")})
        date = o.get("date") or ""
        changed = bool(date) and date != post.get("date_now")
        if changed:
            D.append({"digest": d, "date": date, "precision": o.get("precision") or "day",
                      "source": f"{o.get('date_source') or 'the letterhead'}; was {post.get('date_now')} ({post.get('precision_now')})"})
        V.append({"digest": d, "reviewed": TODAY, "title": "yes", "date": "yes" if changed else "unchanged",
                  "topics": "yes", "filing": "yes", "note": (o.get("note") or "")[:400], "date_audited": "yes"})

    def add(path, rows):
        if not rows:
            return
        with open(path, encoding="utf-8") as fh:
            fields = next(csv.reader(fh))
        if "digest" in fields:
            # A fresh read replaces an older row for the same letter (an early
            # hand title, a recipient filed before the letter was read), so
            # every file keeps one row per digest.
            mine = {r["digest"] for r in rows}
            with open(path, encoding="utf-8", newline="") as fh:
                old = list(csv.DictReader(fh))
            kept = [r for r in old if r["digest"] not in mine]
            if len(kept) != len(old):
                with open(path, "w", encoding="utf-8", newline="") as fh:
                    w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
                    w.writeheader(); w.writerows(kept)
        with open(path, "a", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
            for r in rows:
                w.writerow({f: r.get(f, "") for f in fields})

    add("vocabulary/reviews.csv", NEWR)
    add("vocabulary/hierarchy.csv", NEWH)
    add("vocabulary/letter-titles.csv", T)
    add("vocabulary/letter-topics.csv", P)
    add("vocabulary/letter-recipients.csv", R)
    add("vocabulary/letter-dates.csv", D)
    add("vocabulary/letters-reviewed.csv", V)
    report = {"filed": len(T), "dates": len(D), "new_terms": [r["candidate"] for r in NEWR if r["decision"] == "merge"],
              "joint": len([r for r in NEWR if r["decision"] == "joint"]),
              "partial": partial, "notletter": notletter, "unresolved": unresolved}
    json.dump(report, open(str(rows_path) + ".report.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps({k: (v if not isinstance(v, list) else len(v)) for k, v in report.items()}))
    for d, why in unresolved:
        print("  UNRESOLVED", d[:12], why)


def split(batch: Path, k: int) -> None:
    rows = json.load(open(batch))
    size = -(-len(rows) // k)
    for i in range(k):
        part = rows[i * size:(i + 1) * size]
        out = batch.with_name(f"{batch.stem}-{i + 1}.json")
        json.dump(part, open(out, "w"), ensure_ascii=False, indent=1)
        print(out, len(part))


def subjects(out: Path) -> None:
    sys.path.insert(0, str(PIPE / "build"))
    import topics  # noqa: E402
    out.write_text("\n".join(sorted(topics.SUBJECTS)) + "\n", encoding="utf-8")
    print(out, len(topics.SUBJECTS))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "pick":
        pick(int(sys.argv[2]), Path(sys.argv[3]), sys.argv[4] if len(sys.argv) > 4 else None)
    elif cmd == "split":
        split(Path(sys.argv[2]), int(sys.argv[3]))
    elif cmd == "subjects":
        subjects(Path(sys.argv[2]))
    else:
        write(Path(sys.argv[2]), Path(sys.argv[3]))
