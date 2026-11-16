"""Subcommittee chairs from the Congressional Directory's standing-committee sections (HTML editions):
inside each committee, after 'SUBCOMMITTEES', a subcommittee heading (one or two lines) and then
'Name, of State, Chair'."""
import re, glob, os, csv, html
HERE = os.path.dirname(os.path.abspath(__file__))
CHAIR = re.compile(r"^\s{4,}(.+?), of ([A-Za-z .]+?),\s*(Chair|Chairman|Chairwoman)\s*\.?\s*$")
out = []
for chamber, pattern in (("House", "cdir/CDIR-*.htm"), ("Senate", "sen/CDIR-*-SENATECOMMITTEES.htm")):
    for f in sorted(glob.glob(os.path.join(HERE, pattern))):
        t = html.unescape(re.sub(r"<[^>]*>", "", open(f, encoding="utf-8", errors="replace").read()))
        m = re.search(r"Congressional Directory for the (\d+)", t)
        if not m or "STANDING COMMITTEES OF THE" not in t: continue
        cong = int(m.group(1)); lines = t.split("\n"); committee = None; sub = False
        for i, l in enumerate(lines):
            s = l.strip()
            if s and l.startswith(" " * 10) and not CHAIR.match(l) and len(s) < 70 and not s.startswith(("[", "http")) \
                    and not re.search(r"\d|phone|http|Office Building|Committees of the", s):
                nxt = " ".join(x.strip() for x in lines[i + 1:i + 4])
                if re.search(r"House Office Building|Senate Office Building|phone \d|, The Capitol|\bH-\d|\bS[DHR]-\d", nxt) and "Subcommittee" not in s:
                    committee, sub = s, False; continue
            if re.match(r"^\s*SUBCOMMITTEES?\s*$", l): sub = True; continue
            c = CHAIR.match(l)
            if c and committee and sub:
                head, k = [], i - 1
                while k > 0 and not lines[k].strip(): k -= 1
                while k > 0 and lines[k].strip() and ", of " not in lines[k] and not CHAIR.match(lines[k]) and len(head) < 3:
                    head.insert(0, lines[k].strip()); k -= 1
                name = re.sub(r"\s+", " ", " ".join(head)).strip()
                if name and not name.startswith("["):
                    out.append([cong, chamber, committee, name, c.group(1).strip(), c.group(2).strip(), os.path.basename(f)[:15]])
with open(os.path.join(HERE, "sub-raw.csv"), "w", newline="") as fh:
    csv.writer(fh, lineterminator="\n").writerows([["congress", "chamber", "committee", "subcommittee", "chair", "state", "edition"]] + out)
from collections import Counter
print(len(out)); print(sorted(Counter((r[0], r[1]) for r in out).items()))
for r in out:
    if r[0] == 115 and r[2] == "Appropriations": print(r[1], r[3][:60], "|", r[4])
