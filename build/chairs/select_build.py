"""Select and special committee rows of data/committee-chairs.csv (select_parse.py, select_parse_txt.py)."""
import csv, re, glob, os, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.environ.get("LETTERS_ROOT") or os.path.dirname(os.path.dirname(HERE))
SUF = {"jr", "sr", "ii", "iii", "iv"}
def sn(n):
    n = unicodedata.normalize("NFKD", n).encode("ascii", "ignore").decode()
    w = [x for x in re.sub(r"[^\w\s'-]", " ", n.lower()).split() if x not in SUF]; return w[-1] if w else ""
ros = {}
for f in glob.glob(P + "/data/rosters/congress*-roster.csv"):
    n = int(re.search(r"congress(\d+)", f).group(1))
    for r in csv.DictReader(open(f)):
        ros.setdefault((n, r["chamber"], sn(r["name"])), set()).add((r["bioguide_id"], r["state"]))
KEEP = {"Select Committee on Ethics", "Select Committee on Intelligence", "Special Committee on Aging",
        "Permanent Select Committee on Intelligence", "Select Committee on the Climate Crisis",
        "Select Committee on Homeland Security", "Select Committee on the Modernization of Congress"}
ST = {"Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA","Colorado":"CO","Connecticut":"CT","Delaware":"DE","Florida":"FL","Georgia":"GA","Hawaii":"HI","Idaho":"ID","Illinois":"IL","Indiana":"IN","Iowa":"IA","Kansas":"KS","Kentucky":"KY","Louisiana":"LA","Maine":"ME","Maryland":"MD","Massachusetts":"MA","Michigan":"MI","Minnesota":"MN","Mississippi":"MS","Missouri":"MO","Montana":"MT","Nebraska":"NE","Nevada":"NV","New Hampshire":"NH","New Jersey":"NJ","New Mexico":"NM","New York":"NY","North Carolina":"NC","North Dakota":"ND","Ohio":"OH","Oklahoma":"OK","Oregon":"OR","Pennsylvania":"PA","Rhode Island":"RI","South Carolina":"SC","South Dakota":"SD","Tennessee":"TN","Texas":"TX","Utah":"UT","Vermont":"VT","Virginia":"VA","Washington":"WA","West Virginia":"WV","Wisconsin":"WI","Wyoming":"WY"}
seen, out, miss = set(), [], []
for f in ("select-raw.csv", "select-raw-txt.csv"):
    for r in csv.DictReader(open(os.path.join(HERE, f))):
        if r["committee"] not in KEEP: continue
        n, ch = int(r["congress"]), r["chamber"]
        com = f"{ch} {r['committee']}"
        chair = r["chair"].replace("``", '"').replace("''", '"')
        if (n, com, chair) in seen: continue
        seen.add((n, com, chair))
        opts = ros.get((n, ch, sn(chair)), set())
        st = r["state"] if len(r["state"]) == 2 else ST.get(r["state"], "")
        pick = [b for b, s in opts if s == st] or ([b for b, _ in opts] if len(opts) == 1 else [])
        if len(pick) != 1: miss.append((n, com, chair)); continue
        y0 = 1789 + 2 * (n - 1)
        out.append([ch, com, chair, pick[0], y0, y0 + 2, n,
                    f"Congressional Directory ({r['edition']}), select and special committees: the chair as printed"])
print(len(out), "rows; unmatched:", miss)
path = os.path.join(P, "data", "committee-chairs.csv")
rows = [x for x in csv.reader(open(path)) if x and not (len(x) > 1 and re.match(r"(Senate|House) (Select|Special|Permanent)", x[1]))]
with open(path, "w", newline="") as fh:
    csv.writer(fh, lineterminator="\n").writerows(rows + out)
