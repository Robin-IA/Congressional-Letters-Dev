"""House rows of data/committee-chairs.csv from house-raw.csv (house_parse.py)."""
import csv, re, glob, os, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.environ.get("LETTERS_ROOT") or os.path.dirname(os.path.dirname(HERE))
LAB = {"Banking and Financial Services": "Financial Services", "Commerce": "Energy and Commerce",
       "Education and Labor": "Education and the Workforce", "Government Reform": "Oversight",
       "Oversight and Government Reform": "Oversight", "Oversight and Reform": "Oversight",
       "International Relations": "Foreign Affairs", "Resources": "Natural Resources",
       "Science": "Science, Space, and Technology", "Science and Technology": "Science, Space, and Technology",
       "Standards of Official Conduct": "Ethics", "Education and Workforce": "Education and the Workforce",
       "Oversight and Accountability": "Oversight", "Budget": "the Budget", "Judiciary": "the Judiciary"}
ST = {"Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA","Colorado":"CO","Connecticut":"CT","Delaware":"DE","Florida":"FL","Georgia":"GA","Hawaii":"HI","Idaho":"ID","Illinois":"IL","Indiana":"IN","Iowa":"IA","Kansas":"KS","Kentucky":"KY","Louisiana":"LA","Maine":"ME","Maryland":"MD","Massachusetts":"MA","Michigan":"MI","Minnesota":"MN","Mississippi":"MS","Missouri":"MO","Montana":"MT","Nebraska":"NE","Nevada":"NV","New Hampshire":"NH","New Jersey":"NJ","New Mexico":"NM","New York":"NY","North Carolina":"NC","North Dakota":"ND","Ohio":"OH","Oklahoma":"OK","Oregon":"OR","Pennsylvania":"PA","Rhode Island":"RI","South Carolina":"SC","South Dakota":"SD","Tennessee":"TN","Texas":"TX","Utah":"UT","Vermont":"VT","Virginia":"VA","Washington":"WA","West Virginia":"WV","Wisconsin":"WI","Wyoming":"WY"}
SUF = {"jr", "sr", "ii", "iii", "iv"}
def sn(n):
    n = unicodedata.normalize("NFKD", n).encode("ascii", "ignore").decode()
    w = [x for x in re.sub(r"[^\w\s'-]", " ", n.lower()).split() if x not in SUF]; return w[-1] if w else ""
ros = {}
for f in glob.glob(P + "/data/rosters/congress*-roster.csv"):
    n = int(re.search(r"congress(\d+)", f).group(1))
    for r in csv.DictReader(open(f)):
        if r["chamber"] == "House": ros.setdefault((n, sn(r["name"]), r["state"]), r["bioguide_id"])
seen, out, miss = set(), [], []
for r in [x for f in ("house-raw.csv", "house-raw-txt.csv") if os.path.exists(os.path.join(HERE, f))
          for x in csv.DictReader(open(os.path.join(HERE, f)))]:
    name = LAB.get(r["committee"], r["committee"])
    com = "Committee on House Administration" if name == "House Administration" else "House Committee on " + name
    n = int(r["congress"]); chair = r["chair"].replace("``", '"').replace("''", '"')
    note = ""
    if chair == "David Drier": chair, note = "David Dreier", "; the Directory prints 'Drier'"
    key = (n, com, chair)
    if key in seen: continue
    seen.add(key)
    b = ros.get((n, sn(chair), (r["state"] if len(r["state"]) == 2 else ST.get(r["state"], ""))), "")
    if not b: miss.append((n, chair)); continue
    y0 = 1789 + 2 * (n - 1)
    out.append(["House", com, chair, b, y0, y0 + 2, n,
                f"Congressional Directory ({r['edition']}): the chair as printed; a change between editions is not dated" + note])
print(len(out), "rows; unmatched:", miss)
path = os.path.join(P, "data", "committee-chairs.csv")
rows = [x for x in csv.reader(open(path)) if x and x[0] != "House"]
with open(path, "w", newline="") as fh:
    csv.writer(fh, lineterminator="\n").writerows(rows + out)
