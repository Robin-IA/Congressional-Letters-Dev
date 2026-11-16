"""data/subcommittee-chairs.csv from sub-raw.csv and sub-raw-txt.csv (#364)."""
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
HL = {"Banking and Financial Services": "Financial Services", "Commerce": "Energy and Commerce",
      "Education and Labor": "Education and the Workforce", "Education and Workforce": "Education and the Workforce",
      "Government Reform": "Oversight", "Oversight and Government Reform": "Oversight", "Oversight and Reform": "Oversight",
      "Oversight and Accountability": "Oversight", "International Relations": "Foreign Affairs", "Resources": "Natural Resources",
      "Science": "Science, Space, and Technology", "Science and Technology": "Science, Space, and Technology",
      "Standards of Official Conduct": "Ethics", "Budget": "the Budget", "Judiciary": "the Judiciary"}
SL = {"Budget": "the Budget", "Judiciary": "the Judiciary", "Governmental Affairs": "Homeland Security and Governmental Affairs",
      "Health, Education, Labor, and Pensions": "Health, Education, Labor, and Pensions", "Small Business and Entrepreneurship": "Small Business",
      "Banking, Housing and Urban Affairs": "Banking, Housing, and Urban Affairs", "Agriculture, Nutrition and Forestry": "Agriculture, Nutrition, and Forestry",
      "Health, Education, Labor and Pensions": "Health, Education, Labor, and Pensions"}
def label(ch, c):
    c = c.replace("’", "'")
    if ch == "House":
        c = HL.get(c, c); return "Committee on House Administration" if c == "House Administration" else "House Committee on " + c
    return "Senate Committee on " + SL.get(c, c)
ST = {"Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA","Colorado":"CO","Connecticut":"CT","Delaware":"DE","Florida":"FL","Georgia":"GA","Hawaii":"HI","Idaho":"ID","Illinois":"IL","Indiana":"IN","Iowa":"IA","Kansas":"KS","Kentucky":"KY","Louisiana":"LA","Maine":"ME","Maryland":"MD","Massachusetts":"MA","Michigan":"MI","Minnesota":"MN","Mississippi":"MS","Missouri":"MO","Montana":"MT","Nebraska":"NE","Nevada":"NV","New Hampshire":"NH","New Jersey":"NJ","New Mexico":"NM","New York":"NY","North Carolina":"NC","North Dakota":"ND","Ohio":"OH","Oklahoma":"OK","Oregon":"OR","Pennsylvania":"PA","Rhode Island":"RI","South Carolina":"SC","South Dakota":"SD","Tennessee":"TN","Texas":"TX","Utah":"UT","Vermont":"VT","Virginia":"VA","Washington":"WA","West Virginia":"WV","Wisconsin":"WI","Wyoming":"WY"}
seen, out, miss = set(), [], []
for f in ("sub-raw.csv", "sub-raw-txt.csv"):
    for r in csv.DictReader(open(os.path.join(HERE, f))):
        chair = r["chair"].split(" (")[0].rstrip(".").replace("``", '"').replace("''", '"').strip()
        if not chair: continue
        n, ch = int(r["congress"]), r["chamber"]
        if "Committees of the" in r["committee"]: continue
        com = label(ch, r["committee"])
        sub = re.sub(r"\s+", " ", r["subcommittee"]).strip().rstrip(",")
        key = (n, com, sub.lower()[:40], chair)
        if key in seen: continue
        seen.add(key)
        opts = ros.get((n, ch, sn(chair)), set())
        st = r["state"] if len(r["state"]) == 2 else ST.get(r["state"], "")
        pick = [b for b, s in opts if s == st] or ([b for b, _ in opts] if len(opts) == 1 else [])
        if len(pick) != 1: miss.append((n, ch, chair)); continue
        out.append([ch, com, sub, chair, pick[0], n, f"Congressional Directory ({r['edition']}): the subcommittee chair as printed"])
print(len(out), "rows; unmatched:", len(miss), miss[:12])
with open(os.path.join(P, "data", "subcommittee-chairs.csv"), "w", newline="") as fh:
    csv.writer(fh, lineterminator="\n").writerows([["chamber", "committee", "subcommittee", "chair", "bioguide", "congress", "source"]] + out)
