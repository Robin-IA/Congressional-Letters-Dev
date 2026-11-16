"""House standing-committee chairs from the Congressional Directory full text (the 118th and 119th
editions, whose layouts differ from the HTML sections): each committee heading is followed by its
'Room' line, and its chair is the first member listed after it."""
import re, sys, csv, os
HERE = os.path.dirname(os.path.abspath(__file__))
MEM = re.compile(r"^\s*(.+?) \(([A-Za-z]{2})-[0-9A-Za-z]+\)")
rows = []
for spec in sys.argv[1:]:
    path, cong, ed = spec.split(":"); cong = int(cong)
    t = open(path, encoding="utf-8", errors="replace").read().split("\n")
    a = max(i for i, l in enumerate(t) if l.strip() == "STANDING COMMITTEES OF THE HOUSE")
    b = next(i for i, l in enumerate(t) if i > a and l.strip().startswith("SELECT AND SPECIAL COMMITTEES"))
    for i in range(a, b):
        s = t[i].strip()
        if not s or len(s) > 70 or s.isupper() or ":" in s or s.endswith(".") or "Room" in s or MEM.match(t[i]) or s.startswith(("[", "http", "(")):
            continue
        if not any("Room" in t[k] for k in range(i + 1, min(i + 4, b))):
            continue
        for j in range(i + 1, min(i + 12, b)):
            m = MEM.match(t[j])
            if m:
                rows.append([cong, s.replace("\u2019", "'"), re.sub(r"\s+CHAIR(MAN)?$", "", m.group(1).strip()), m.group(2).upper(), ed]); break
with open(os.path.join(HERE, "house-raw-txt.csv"), "w", newline="") as fh:
    csv.writer(fh, lineterminator="\n").writerows([["congress", "committee", "chair", "state", "edition"]] + rows)
for r in rows: print(r[0], r[1], "|", r[2], r[3])
