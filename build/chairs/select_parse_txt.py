"""Select/special committee chairs from the full text of the 118th and 119th Directory editions."""
import re, sys, csv, os
HERE = os.path.dirname(os.path.abspath(__file__))
WANT = {"Select Committee on Ethics": "Senate", "Select Committee on Intelligence": "Senate",
        "Special Committee on Aging": "Senate", "Permanent Select Committee on Intelligence": "House"}
MEM = re.compile(r"^\s*(.+?) \(([A-Za-z]{2})(?:-[0-9A-Za-z]+)?\)")
rows = []
for spec in sys.argv[1:]:
    path, cong, ed = spec.split(":"); cong = int(cong)
    t = open(path, encoding="utf-8", errors="replace").read().split("\n")
    for i, l in enumerate(t):
        s = l.strip()
        if s in WANT and any(("Room" in t[k] or "(ph)" in t[k]) for k in range(i + 1, min(i + 5, len(t)))):
            for j in range(i + 1, min(i + 14, len(t))):
                m = MEM.match(t[j])
                if m and "Room" not in t[j] and "(ph)" not in t[j]:
                    rows.append([cong, WANT[s], s, re.sub(r"\s+CHAIR(MAN)?$", "", m.group(1).strip()), m.group(2).upper(), ed]); break
with open(os.path.join(HERE, "select-raw-txt.csv"), "w", newline="") as fh:
    csv.writer(fh, lineterminator="\n").writerows([["congress", "chamber", "committee", "chair", "state", "edition"]] + rows)
for r in rows: print(r)
