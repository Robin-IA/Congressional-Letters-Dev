"""senate.py -- Senate standing-committee chairs 1999-present from the Senate Historical Office table."""
import re, csv, glob, os
lines = open(os.path.join(os.path.dirname(__file__), "senate.txt")).read().split("\n")
CH = re.compile(r"^\s*(\d{4})\s*(?:[–-]\s*(\d{4})?)?\s*:\s*(.+?)\s*\(\s*([A-Z/]+)\s*-\s*([A-Z]{2})\s*\)")
def heading(i):
    s = lines[i].strip()
    if not s or len(s) > 70 or re.match(r"^\d", s) or CH.match(lines[i]) or s.startswith(("Established", "See ", "Formerly")): return False
    for j in range(i + 1, min(i + 4, len(lines))):
        t = lines[j].strip()
        if t: return t.startswith("Established") and ":" not in s and not s.endswith((".", ")"))
    return False
cur, out = None, []
for i, l in enumerate(lines):
    if heading(i): cur = l.strip(); continue
    m = CH.match(l)
    if m and cur:
        s, e, name, party, st = m.groups()
        e = e or ("" if re.search(r"[–-]\s*:", l) else s)
        if (e == "" or int(e) >= 1999) and int(s) <= 2026:
            out.append([cur, re.sub(r"\d+$", "", name).strip(), party, st, s, e])
csv.writer(open(os.path.join(os.path.dirname(__file__), "senate-raw.csv"), "w", newline=""), lineterminator="\n").writerows(
    [["committee", "chair", "party", "state", "start", "end"]] + out)
print(len(out)); from collections import Counter; print(Counter(r[0] for r in out).most_common(40))
