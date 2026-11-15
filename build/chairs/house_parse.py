"""House standing-committee chairs from Congressional Directory text (CDIR *-HOUSECOMMITTEES)."""
import re, glob, os, csv, html
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cdir")
CHAIR = re.compile(r"^\s{4,}(.+?), of ([A-Za-z .]+?),\s*(Chair|Chairman|Chairwoman)\s*\.?\s*$")
out = []
for f in sorted(glob.glob(D + "/CDIR-*.htm")):
    t = html.unescape(re.sub(r"<[^>]*>", "", open(f, encoding="utf-8", errors="replace").read()))
    if "STANDING COMMITTEES OF THE HOUSE" not in t: continue
    m = re.search(r"Congressional Directory for the (\d+)", t); cong = int(m.group(1))
    lines = t.split("\n"); heading = None; sub = False
    for i, l in enumerate(lines):
        s = l.strip()
        # a committee heading: a centred line followed (within 3 lines) by a room/phone line
        if s and l.startswith(" " * 10) and not CHAIR.match(l) and len(s) < 70:
            nxt = " ".join(x.strip() for x in lines[i + 1:i + 4])
            if re.search(r"House Office Building|phone \d|, The Capitol|\bH-\d", nxt) and not s.startswith(("[", "http")):
                heading, sub = s, False
                continue
        if re.match(r"^\s*SUBCOMMITTEES?\s*$", l) or re.match(r"^\s*Subcommittees?\s*$", l):
            sub = True
        m = CHAIR.match(l)
        if m and heading and not sub:
            out.append([cong, heading, m.group(1).strip(), m.group(2).strip(), os.path.basename(f)[:-4]])
            sub = True  # the next chair lines in this committee are subcommittees
csv.writer(open(os.path.join(os.path.dirname(D), "house-raw.csv"), "w", newline=""), lineterminator="\n").writerows(
    [["congress", "committee", "chair", "state", "edition"]] + out)
from collections import Counter
print(len(out)); print(sorted(Counter(r[0] for r in out).items()))
for r in out:
    if r[0] in (115, 117): print(r)
