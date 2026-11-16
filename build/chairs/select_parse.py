"""Select and special committee chairs from the Congressional Directory's *-SENATECOMMITTEES-2 and
*-HOUSECOMMITTEES-2 sections: a 'Select/Special/Permanent Select Committee on X' heading, then
'Name, of State, Chair'."""
import re, glob, os, csv, html
HERE = os.path.dirname(os.path.abspath(__file__))
HEAD = re.compile(r"^\s{6,}((?:Permanent )?(?:Select|Special) Committee on [A-Za-z ,'&-]+?)\s*$")
CHAIR = re.compile(r"^\s{4,}(.+?), of ([A-Za-z .]+?),\s*(Chair|Chairman|Chairwoman)\s*\.?\s*$")
out = []
for f in sorted(glob.glob(os.path.join(HERE, "sel", "*.htm"))):
    t = html.unescape(re.sub(r"<[^>]*>", "", open(f, encoding="utf-8", errors="replace").read()))
    m = re.search(r"Congressional Directory for the (\d+)", t)
    if not m: continue
    cong = int(m.group(1)); chamber = "Senate" if "SENATE" in f else "House"
    head = None
    for l in t.split("\n"):
        h = HEAD.match(l)
        if h: head = re.sub(r"\s+", " ", h.group(1)); continue
        c = CHAIR.match(l)
        if c and head:
            out.append([cong, chamber, head, c.group(1).strip(), c.group(2).strip(), os.path.basename(f)[:15]]); head = None
with open(os.path.join(HERE, "select-raw.csv"), "w", newline="") as fh:
    csv.writer(fh, lineterminator="\n").writerows([["congress", "chamber", "committee", "chair", "state", "edition"]] + out)
from collections import Counter
print(len(out)); print(sorted(Counter((r[1], r[2]) for r in out).items()))
