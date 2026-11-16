"""Subcommittee chairs from the full text of the 118th and 119th Directory editions."""
import re, sys, csv, os
HERE = os.path.dirname(os.path.abspath(__file__))
MARK = re.compile(r"^\s*(.+?) \(([A-Za-z]{2})(?:-[0-9A-Za-z]+)?\)\s+(?:CHAIRMAN|chairman|CHAIR|chair)\b")
rows = []
for spec in sys.argv[1:]:
    path, cong, ed = spec.split(":"); cong = int(cong)
    t = open(path, encoding="utf-8", errors="replace").read().split("\n")
    for chamber in ("HOUSE", "SENATE"):
        try:
            a = max(i for i, l in enumerate(t) if l.strip() == f"STANDING COMMITTEES OF THE {chamber}")
        except ValueError: continue
        b = next((i for i, l in enumerate(t) if i > a and l.strip().startswith("SELECT AND SPECIAL COMMITTEES")), len(t))
        committee, sub = None, False
        for i in range(a, b):
            s = t[i].strip()
            if s and len(s) < 70 and not s.isupper() and ":" not in s and not s.endswith(".") and "(" not in s and not s.startswith(("[", "http")) \
               and any(("Room" in t[k] or "(ph)" in t[k]) for k in range(i + 1, min(i + 4, b))):
                committee, sub = s.replace("’", "'"), False; continue
            if s.upper().startswith("SUBCOMMITTEES"): sub = True; continue
            m = MARK.match(t[i])
            if m and committee and sub:
                k = i - 1
                while k > a and (not t[k].strip() or "(" in t[k]): k -= 1
                name = re.sub(r"\s+", " ", t[k].strip())
                rows.append([cong, chamber.title(), committee, name, re.sub(r"\s+CHAIR(MAN)?$", "", m.group(1).strip()), m.group(2).upper(), ed])
with open(os.path.join(HERE, "sub-raw-txt.csv"), "w", newline="") as fh:
    csv.writer(fh, lineterminator="\n").writerows([["congress", "chamber", "committee", "subcommittee", "chair", "state", "edition"]] + rows)
from collections import Counter
print(len(rows), sorted(Counter((r[0], r[1]) for r in rows).items()))
for r in rows:
    if r[2] == "Appropriations": print(r[0], r[1], r[3][:55], "|", r[4])
