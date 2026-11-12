#!/usr/bin/env python3
"""Build Letters from Congress, the page over every per-Congress explorer.

    python3 build/export_csv.py           # the Download data files, first
    python3 build/build_hub.py            # into ../explorers/Explorer-Letters/
    python3 build/build_hub.py --out DIR

Lists the Congresses and searches across them (EXPLORERS.md, "The federated
explorer"). It is three files: ``index.html`` and ``hub.js`` from
``build/hub/``, and ``hub.json``, which says only which explorers exist and
where. Every count on the page is computed in the browser from each
explorer's own ``index.json``, so nothing here needs rebuilding when an
explorer is rebuilt -- only when one is added.

The explorers are found as ``Explorer-Congressional-Letters-<N>/index.json``
beside the output folder, and linked as ``../Explorer-Congressional-Letters-<N>/``.
That is the layout GitHub Pages gives repositories of one account
(``robin-ia.github.io/<repo>/``), so the same relative links work when served
locally from the explorers folder and when published, and the page can read
every explorer's data because it is all one origin.

Search covers what the explorers' own search covers -- subject, recipient,
topics -- plus member names. Full-text search waits for the OCR and an index.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPLORERS = ROOT.parent / "explorers"
NAME = "Explorer-Letters"   # the page is titled "Letters from Congress"


PER_CONGRESS = 4   # letters pictured on each Congress's card


def samples(explorer: Path, n: int) -> list[dict]:
    """A few real letters from one explorer, to show as pictures.

    One letter each from the members with the most letters, taking the first
    of theirs that has a thumbnail and says who it was to, so the pictures are
    of different people and every caption has something to say. Chosen at
    build time, the same way every build, from what the explorer holds.
    """
    idx = json.loads((explorer / "index.json").read_text(encoding="utf-8"))
    col = {c: i for i, c in enumerate(idx["columns"])}
    thumbs = explorer / "thumbs"
    out = []
    for m in sorted(idx["members"], key=lambda m: -(m.get("letters") or 0)):
        path = explorer / idx.get("data_base", "payload/member/") / f"{m['id']}.json"
        if not m.get("letters") or not path.exists():
            continue
        for r in json.loads(path.read_text(encoding="utf-8")):
            digest = r[col["digest"]]
            if (digest and r[col["recipient"]] and r[col["kind"]] == "pdf"
                    and (thumbs / f"{digest}.webp").exists()):
                out.append({"thumb": f"thumbs/{digest}.webp", "member": m["name"],
                            "member_id": m["id"], "to": r[col["recipient"]],
                            "subject": r[col["subject"]] or "",
                            "date": r[col["date"]] or "",
                            "url": f"https://web.archive.org/web/{r[col['timestamp']]}id_/"
                                   + urllib.parse.quote(r[col["key"]], safe=":/?&=%#~+,;@!$'()*[]")})
                break
        if len(out) >= n:
            break
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--explorers", type=Path, default=EXPLORERS)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    out = args.out or args.explorers / NAME

    congresses = []
    for d in sorted(args.explorers.glob("Explorer-Congressional-Letters-*")):
        m = re.fullmatch(r"Explorer-Congressional-Letters-(\d+)", d.name)
        idx = d / "index.json"
        if not m or not idx.exists():
            continue
        k = json.loads(idx.read_text(encoding="utf-8")).get("congress") or {}
        if k.get("number") != int(m.group(1)):
            sys.exit(f"{idx} says Congress {k.get('number')}, not {m.group(1)}")
        entry = {"number": int(m.group(1)),
                 "label": f"{k.get('ordinal', m.group(1))} Congress",
                 "path": f"../{d.name}/",
                 "samples": samples(d, PER_CONGRESS)}
        # The Download data file, from export_csv.py. Linked only when it
        # exists; without it the card says "coming soon".
        csvs = sorted((d / "data").glob("letters-from-congress-*.csv"))
        if csvs:
            entry["download"] = f"../{d.name}/data/{csvs[-1].name}"
        congresses.append(entry)
    if not congresses:
        sys.exit(f"no explorers under {args.explorers}")
    congresses.sort(key=lambda c: c["number"])

    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    out.mkdir(parents=True, exist_ok=True)
    src = ROOT / "build" / "hub"
    html = (src / "index.html").read_text(encoding="utf-8")
    if html.count("hub.js?v=STAMP") != 1:
        sys.exit("build/hub/index.html: expected one hub.js?v=STAMP")
    (out / "index.html").write_text(html.replace("hub.js?v=STAMP", f"hub.js?v={stamp}"),
                                    encoding="utf-8")
    shutil.copy2(src / "hub.js", out / "hub.js")
    (out / "hub.json").write_text(json.dumps(
        {"built": stamp, "congresses": congresses}, indent=1), encoding="utf-8")
    print(f"{len(congresses)} Congresses "
          f"({congresses[0]['number']}th-{congresses[-1]['number']}th) -> {out}",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
