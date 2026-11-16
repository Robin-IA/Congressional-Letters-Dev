import csv, re, glob, os
P = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LAB = {"Budget": "the Budget", "Judiciary": "the Judiciary", "Governmental Affairs": "Homeland Security and Governmental Affairs",
       "Labor and Human Resources": "Health, Education, Labor, and Pensions", "INDIAN AFFAIRS—2ND": "Indian Affairs"}
SUF = {"jr", "sr", "ii", "iii", "iv"}
def sn(n): w = [x for x in re.sub(r"[^\w\s'-]", " ", n.lower()).split() if x not in SUF]; return w[-1] if w else ""
ros = {}
for f in glob.glob(P + "/data/rosters/congress*-roster.csv"):
    n = int(re.search(r"congress(\d+)", f).group(1))
    for r in csv.DictReader(open(f)):
        if r["chamber"] == "Senate": ros.setdefault((n, sn(r["name"]), r["state"]), r["bioguide_id"])
anyc = {(k[1], k[2]): v for k, v in sorted(ros.items())}
vocab = {r["label"] for r in csv.DictReader(open(P + "/vocabulary/terms.csv"))}
out, miss = [], []
FIX = {"Debbie Stabennow": "Debbie Stabenow", "Lott, Trent": "Trent Lott", "Robert C. Smit h": "Robert C. Smith"}  # PDF spelling; text extraction
for r in csv.DictReader(open(os.path.join(os.path.dirname(__file__), "senate-raw.csv"))):
    note = "; name corrected from the table's '%s'" % r["chair"] if r["chair"] in FIX else ""
    r["chair"] = FIX.get(r["chair"], r["chair"])
    com = "Senate Committee on " + LAB.get(r["committee"], r["committee"])
    if com not in vocab: miss.append(com)
    s = int(r["start"]); e = int(r["end"]) if r["end"] else 2026
    for n in range(106, 120):
        y0 = 1789 + 2 * (n - 1)
        if s <= y0 + 1 and (e > y0 or s == e == y0):
            out.append(["Senate", com, r["chair"], ros.get((n, sn(r["chair"]), r["state"])) or anyc.get((sn(r["chair"]), r["state"]), ""), r["start"], r["end"], n,
                        "Senate Historical Office, Chairmen of Senate Standing Committees (Table 5-3)" + note])
csv.writer(open(os.path.join(P, "data", "committee-chairs.csv"), "w", newline=""), lineterminator="\n").writerows(
    [["chamber", "committee", "chair", "bioguide", "start", "end", "congress", "source"]] + out)
print(len(out), "rows; no bioguide:", sorted({(r[2], r[6]) for r in out if not r[3]})[:10]); print("labels not in vocabulary:", sorted(set(miss)))
