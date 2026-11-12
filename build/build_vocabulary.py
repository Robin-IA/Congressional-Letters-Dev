#!/usr/bin/env python3
"""Build the Letters from Congress vocabulary from what the letters already say.

    python3 build/build_vocabulary.py               # writes vocabulary/
    python3 build/build_vocabulary.py --no-wikidata # skip the Wikidata lookups

A controlled vocabulary of its own for these letters, in four kinds:

  member         every member of the 106th-119th Congresses, by Bioguide ID,
                 with the Wikidata item congress-legislators records for them
  organization   agencies, offices, companies and groups the letters are
                 written to
  person         people named as recipients who are not members
  topic          what the letters are about

WHERE EACH COMES FROM
  members        data/rosters/ (who served) and data/legislators/ (the
                 unitedstates/congress-legislators JSON: name forms, Wikidata)
  organizations  the hand-made tables in build/parse_urls.py (RECIPIENTS,
                 OFFICIALS, LEADERSHIP) and build/topics.py (AGENCIES)
  topics         build/topics.py (SUBJECTS)
  candidates     every other recipient the built explorers show three or more
                 times, sorted into organization, person or unclassified by
                 the words in the name. A candidate is a suggestion for a
                 person to accept, never a fact.

STATUS
  preferred      established: a member by Bioguide ID, or a term someone chose
                 by hand in the tables above (source "local")
  candidate      found in the data and not yet reviewed

Wikidata matches for organizations are looked up by name and recorded as
CANDIDATE exactMatch relations, never as the term's identity: a name search
is a lead, not evidence. Members' Wikidata IDs come from congress-legislators
and are recorded as established.

Counts are letters in the published explorers (../explorers/), so they agree
with what a visitor sees. Text-based terms -- organizations and people named
inside the letters -- come once the OCR is done (#40).

Writes vocabulary/terms.csv, relations.csv, sources.csv and vocabulary.json.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "build"))
import parse_urls  # noqa: E402
import topics  # noqa: E402

EXPLORERS = ROOT.parent / "explorers"
OUT = ROOT / "vocabulary"
WIKIDATA_CACHE = ROOT / "data" / "vocabulary-wikidata-cache.json"
UA = {"User-Agent": "ia-congressional-member-letters/0.1 (vocabulary build)"}
MIN_CANDIDATE = 3

ORG_WORDS = re.compile(
    r"\b(department|dept|agency|administration|commission|bureau|office|service|"
    r"board|council|committee|corporation|corp|inc|company|co|llc|ltd|association|"
    r"assn|bank|university|college|institute|foundation|authority|center|centers|"
    r"group|union|network|airlines?|hospital|fund|court|coalition|alliance|"
    r"society|federation|caucus|delegation|leadership|cabinet|county|city|state|"
    r"states|nations|organization|guard|army|navy|force|corps|council|services|"
    r"health|reserve|exchange|motors|energy|pharma|technologies|platforms|media|"
    r"news|times|post|school|schools|district|police|government|governors|"
    r"mayors|ceos|executives|companies|carriers|providers|manufacturers)\b", re.I)
PERSON_TITLES = re.compile(
    r"^(dr|mr|mrs|ms|miss|secretary|sec|general|gen|ltg|lt|admiral|adm|judge|"
    r"justice|ambassador|amb|governor|gov|mayor|senator|sen|rep|representative|"
    r"chairman|chairwoman|chair|commissioner|director|administrator|president|"
    r"ceo|attorney general|ag)\b\.?\s+\S", re.I)


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]


def ordinal(n: int) -> str:
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


# ------------------------------------------------------------------ the data

def explorer_counts() -> tuple[Counter, Counter, Counter]:
    """Letters per member, per recipient, per topic, as the explorers publish them."""
    per_member, per_recipient, per_topic = Counter(), Counter(), Counter()
    for d in sorted(EXPLORERS.glob("Explorer-Congressional-Letters-*")):
        idx_path = d / "index.json"
        if not idx_path.exists():
            continue
        idx = json.loads(idx_path.read_text(encoding="utf-8"))
        col = {c: i for i, c in enumerate(idx["columns"])}
        for m in idx["members"]:
            path = d / idx.get("data_base", "payload/member/") / f"{m['id']}.json"
            if not path.exists():
                continue
            for r in json.loads(path.read_text(encoding="utf-8")):
                per_member[m["id"]] += 1
                if r[col["recipient"]]:
                    per_recipient[r[col["recipient"]]] += 1
                for t in re.split(r"[;,]", r[col["topics"]] or ""):
                    if t.strip():
                        per_topic[t.strip()] += 1
    return per_member, per_recipient, per_topic


def rosters() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for f in sorted((ROOT / "data" / "rosters").glob("congress*-roster.csv")):
        n = int(re.search(r"congress(\d+)", f.name).group(1))
        for row in csv.DictReader(f.open(encoding="utf-8")):
            m = out.setdefault(row["bioguide_id"], {"name": row["name"], "congresses": [],
                                                     "parties": [], "chambers": []})
            m["congresses"].append(n)
            m["name"] = row["name"]          # the latest Congress's form wins
            for p in re.split(r"\s*→\s*|\s*\(\d{4}-\d\d-\d\d\)\s*", row["party"]):
                if p.strip() and p.strip() not in m["parties"]:
                    m["parties"].append(p.strip())
            if row["chamber"] not in m["chambers"]:
                m["chambers"].append(row["chamber"])
    return out


def legislators() -> dict[str, dict]:
    out = {}
    for name in ("legislators-current.json", "legislators-historical.json"):
        path = ROOT / "data" / "legislators" / name
        if path.exists():
            for leg in json.loads(path.read_text(encoding="utf-8")):
                if leg.get("id", {}).get("bioguide"):
                    out[leg["id"]["bioguide"]] = leg
    return out


ABBREV = {"gov": "governor", "amb": "ambassador", "sec": "secretary", "dept": "department",
          "admin": "administrator", "commr": "commissioner", "gen": "general",
          "ltg": "lieutenant general", "lt": "lieutenant", "adm": "admiral",
          "dr": "doctor", "ed": "education"}


def name_key(label: str) -> str:
    """One key for the spellings of one name: case, punctuation, abbreviations."""
    words = re.sub(r"[^a-z0-9 ]+", " ", label.lower()).split()
    return " ".join(ABBREV.get(w, w) for w in words if w not in ("the", "of", "us", "u", "s"))


# ------------------------------------------------------------- Wikidata leads

US_BODY = re.compile(r"united states|u\.s\.|\bus\b|federal|american", re.I)


def _search(text: str) -> list[dict]:
    q = urllib.parse.urlencode({"action": "wbsearchentities", "search": text,
                                "language": "en", "type": "item", "limit": 5,
                                "format": "json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(
                    f"https://www.wikidata.org/w/api.php?{q}", headers=UA), timeout=30) as r:
                return json.load(r).get("search", [])
        except urllib.error.HTTPError as exc:
            if exc.code != 429:
                raise
            time.sleep(20 * (attempt + 1))      # Wikidata asks clients to back off
    raise RuntimeError("rate-limited four times")


def wikidata_lead(label: str, cache: dict) -> dict | None:
    """A Wikidata item for a US federal body's name, as a lead only.

    "Department of Justice" alone finds the Philippines' department first, so
    the search is for the United States body ("United States Department of
    Justice"), and only a hit whose description says it is a US body counts.
    No US hit means no lead, rather than a foreign one.
    """
    if label in cache:
        return cache[label]
    probes = [label] if re.match(r"(united states|the president|u\.s\.)", label, re.I) \
        else [f"United States {label}", label]
    hit = None
    try:
        for probe in probes:
            us = [x for x in _search(probe) if US_BODY.search(x.get("description", ""))]
            time.sleep(1.0)
            if us:
                hit = {"id": us[0]["id"], "label": us[0].get("label", ""),
                       "description": us[0].get("description", "")}
                break
    except Exception as exc:  # noqa: BLE001 - a lead that fails is just no lead
        print(f"  wikidata: {label}: {type(exc).__name__}", file=sys.stderr)
        return None                              # not cached: tried again next build
    cache[label] = hit
    return hit


# -------------------------------------------------------------------- the build

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--no-wikidata", action="store_true")
    ap.add_argument("--apply-proposed", action="store_true",
                    help="preview: apply reviews.csv rows marked proposed as well as accepted")
    args = ap.parse_args()

    per_member, per_recipient, per_topic = explorer_counts()
    if not per_member:
        sys.exit(f"no built explorers under {EXPLORERS}; run build_congress.py first")
    terms: list[dict] = []
    relations: list[dict] = []
    ids: set[str] = set()

    def add(term_id, label, kind, facet, status, source, uri="", letters=0, note=""):
        if term_id in ids:
            raise SystemExit(f"duplicate term_id {term_id}")
        ids.add(term_id)
        terms.append({"term_id": term_id, "label": label, "kind": kind, "facet": facet,
                      "status": status, "source": source, "uri": uri,
                      "letters": letters, "note": note})

    def rel(term_id, relation, value, status="preferred", source="local"):
        relations.append({"term_id": term_id, "relation": relation, "value": value,
                          "status": status, "source": source})

    # Members ---------------------------------------------------------------
    legs = legislators()
    for bid, m in sorted(rosters().items(), key=lambda kv: kv[1]["name"].split()[-1]):
        tid = f"M-{bid}"
        cong = sorted(m["congresses"])
        note = (f"{', '.join(m['chambers'])}; {', '.join(m['parties'])}; "
                f"{ordinal(cong[0])}" + (f"-{ordinal(cong[-1])}" if len(cong) > 1 else "")
                + " Congress")
        add(tid, m["name"], "member", "person", "preferred", "Bioguide",
            f"https://bioguide.congress.gov/search/bio/{bid}", per_member.get(bid, 0), note)
        leg = legs.get(bid, {})
        if leg.get("id", {}).get("wikidata"):
            rel(tid, "exactMatch", f"http://www.wikidata.org/entity/{leg['id']['wikidata']}",
                "preferred", "congress-legislators")
        nm = leg.get("name", {})
        forms = {nm.get("official_full", ""),
                 " ".join(x for x in (nm.get("first"), nm.get("middle"), nm.get("last")) if x),
                 " ".join(x for x in (nm.get("nickname"), nm.get("last")) if x)}
        for form in sorted(f for f in forms if f and f != m["name"]):
            rel(tid, "altLabel", form, "preferred", "congress-legislators")
        for c in cong:
            rel(tid, "servedIn", f"{ordinal(c)} Congress", "preferred", "rosters")

    # Organizations: the hand-made tables ---------------------------------
    orgs: dict[str, str] = {}             # label -> term_id

    def org_kind(label: str) -> str:
        if label in ("The President", "The Speaker of the House", "The Vice President"):
            return "office"
        if label in parse_urls.LEADERSHIP or "leadership" in label.lower():
            return "group"
        return "government body"

    for table in (parse_urls.RECIPIENTS, parse_urls.LEADERSHIP, parse_urls.OFFICIALS):
        for label in table:
            if label in orgs:
                continue
            tid = f"O-{slug(label)}"
            orgs[label] = tid
            add(tid, label, "organization", org_kind(label), "preferred", "local", "",
                per_recipient.get(label, 0))
    for label, spellings in parse_urls.RECIPIENTS.items():
        for s in spellings:
            rel(orgs[label], "altLabel", s)
    for label, spellings in parse_urls.LEADERSHIP.items():
        for s in spellings:
            rel(orgs[label], "altLabel", s)
    # OFFICIALS spellings are the surnames of people who held the office:
    # how a letter names the office, not other names for the office.
    for label, names in parse_urls.OFFICIALS.items():
        for s in names:
            rel(orgs[label], "officeHolderName", s)

    # topics.AGENCIES: abbreviation -> words; link to an organization by name.
    for abbr, words in topics.AGENCIES.items():
        full = next((w for w in words if " " in w), "")
        match = next((lab for lab in orgs if lab.lower() == full.lower()), None)
        if not match:
            match = next((lab for lab in orgs if abbr.lower() in
                          [s.lower() for s in parse_urls.RECIPIENTS.get(lab, ())]), None)
        if match:
            tid = orgs[match]
        else:
            label = full.title().replace(" And ", " and ").replace(" Of ", " of ").replace(" The ", " the ") if full else abbr
            tid = f"O-{slug(label)}"
            orgs[label] = tid
            add(tid, label, "organization", "government body", "preferred", "local", "",
                per_recipient.get(label, 0))
        rel(tid, "abbreviation", abbr)
        rel(tid, "taggedAs", abbr, "preferred", "topics.py")

    # Topics ------------------------------------------------------------------
    for label, words in topics.SUBJECTS.items():
        tid = f"T-{slug(label)}"
        add(tid, label, "topic", "subject", "preferred", "local", "", per_topic.get(label, 0))
        for w in words:
            rel(tid, "matchWord", w, "preferred", "topics.py")

    # Candidates: recipients nobody has reviewed ------------------------------
    # Spellings of one name are grouped: "Gov Newsom", "Governor Newsom".
    known = {lab.lower() for lab in orgs}
    # A spelling whose key is a known organization's, or one of its spellings',
    # is another name for it ("Dept Of Ed" for the Department of Education):
    # recorded as a candidate altLabel there, not as a new term.
    org_keys = {}
    for lab, tid in orgs.items():
        org_keys.setdefault(name_key(lab), tid)
    for r in relations:
        if r["relation"] in ("altLabel", "abbreviation") and r["term_id"].startswith("O-"):
            v = r["value"]
            # A one-word abbreviation is never expanded for matching: "sec" is
            # the SEC's, and would otherwise claim every "Secretary".
            plain = [w for w in re.sub(r"[^a-z0-9 ]+", " ", v.lower()).split()
                     if w not in ("the", "of", "us", "u", "s")]
            if len(plain) == 1 and name_key(v) != plain[0]:     # "sec", "the sec"
                continue
            org_keys.setdefault(name_key(v), r["term_id"])
    groups: dict[str, Counter] = defaultdict(Counter)
    for label, n in per_recipient.items():
        if label.lower() in known:
            continue
        key = name_key(label)
        if key in org_keys and n >= 1:
            rel(org_keys[key], "altLabel", label, "candidate", f"letters ({n})")
            continue
        groups[key][label] += n
    surnames = defaultdict(set)
    for bid, m in rosters().items():
        surnames[m["name"].split()[-1].lower()].add(bid)
    cand = Counter()
    spellings = {}
    for key, forms in groups.items():
        total = sum(forms.values())
        if total >= MIN_CANDIDATE:
            label = forms.most_common(1)[0][0]
            cand[label] = total
            spellings[label] = [f for f in forms if f != label]
    for label, n in cand.most_common():
        if PERSON_TITLES.search(label):
            kind, facet = "person", "recipient"
        elif ORG_WORDS.search(label):
            kind, facet = "organization", "recipient"
        elif re.fullmatch(r"[A-Z]{2,6}s?", label):
            kind, facet = "organization", "abbreviation"
        else:
            kind, facet = "unclassified", "recipient"
        prefix = {"person": "P", "organization": "O"}.get(kind, "U")
        tid = f"{prefix}-{slug(label)}"
        if tid in ids:
            tid = f"{tid}-{n}"
        add(tid, label, kind, facet, "candidate", "letters", "", n,
            "a recipient as the file names give it; not reviewed")
        for form in spellings.get(label, []):
            rel(tid, "altLabel", form, "candidate", "letters")
        # A bare surname that exactly one member of these Congresses had.
        words = label.split()
        last = words[-1].lower() if words else ""
        if kind in ("unclassified", "person") and len(surnames.get(last, ())) == 1:
            (bid,) = surnames[last]
            rel(tid, "possibleMember", f"M-{bid}", "candidate", "rosters: the only member with this surname")

    # Wikidata leads for the hand-made organizations ------------------------------
    if not args.no_wikidata:
        cache = json.loads(WIKIDATA_CACHE.read_text()) if WIKIDATA_CACHE.exists() else {}
        for t in terms:
            if t["kind"] == "organization" and t["status"] == "preferred" \
                    and t["facet"] == "government body":
                hit = wikidata_lead(t["label"], cache)
                if hit:
                    rel(t["term_id"], "exactMatch",
                        f"http://www.wikidata.org/entity/{hit['id']}", "candidate",
                        f"Wikidata search: {hit['label']} — {hit['description']}"[:200])
        WIKIDATA_CACHE.write_text(json.dumps(cache, indent=1, ensure_ascii=False), encoding="utf-8")

    # Reviews ------------------------------------------------------------------
    # vocabulary/reviews.csv is made by hand: one row per reviewed candidate.
    # Only rows marked "accepted" are applied (or "proposed" too, with
    # --apply-proposed, to preview). A reviewed candidate stops being a term of
    # its own: it becomes another name, an abbreviation or an office holder's
    # name of the term it was decided to be, and its letters count there.
    extra_hier = []
    review_path = OUT / "reviews.csv"
    reviews = list(csv.DictReader(review_path.open(encoding="utf-8"))) if review_path.exists() else []
    wanted = {"accepted"} | ({"proposed"} if args.apply_proposed else set())
    cand_by_label = {t_["label"]: t_ for t_ in terms if t_["status"] == "candidate"}
    gone: set[str] = set()
    applied = Counter()
    for rv in reviews:
        if rv["status"] not in wanted or rv["decision"] == "hold":
            continue
        cand = cand_by_label.get(rv["candidate"])
        if not cand or cand["term_id"] in gone:
            continue                       # gone from the data, or folded in already
        gone.add(cand["term_id"])
        applied[rv["decision"]] += 1
        names = [cand["label"]] + [r["value"] for r in relations
                                   if r["term_id"] == cand["term_id"] and r["relation"] == "altLabel"]
        # Gone now, so a new term may take the same ID ("Census Bureau" the
        # candidate becomes "Census Bureau" the agency).
        terms.remove(cand)
        ids.discard(cand["term_id"])
        relations[:] = [r for r in relations if r["term_id"] != cand["term_id"]]
        if rv["decision"] == "reject":
            continue
        if rv["decision"] == "member":
            tid = f"M-{rv['target']}"
            for nm in names:
                rel(tid, "recipientName", nm, "preferred", "reviewed")
            continue
        target = next((t_ for t_ in terms if t_["label"] == rv["target"]
                       and t_["status"] == "preferred"), None)
        # An unreviewed term with the target's own name is the same thing:
        # fold it in ("Surface Transportation Board" under "Stb").
        twin = next((t_ for t_ in terms if t_["status"] == "candidate"
                     and t_["label"].lower() == rv["target"].lower()), None)
        twin_letters = 0
        if twin:
            names += [twin["label"]] + [r["value"] for r in relations
                                        if r["term_id"] == twin["term_id"] and r["relation"] == "altLabel"]
            twin_letters = int(twin["letters"] or 0)
            terms.remove(twin)
            ids.discard(twin["term_id"])
            relations[:] = [r for r in relations if r["term_id"] != twin["term_id"]]
            gone.add(twin["term_id"])
        if target is None:
            kind = rv["kind"] or "organization"
            prefix = {"person": "P", "organization": "O"}.get(kind, "O")
            add(f"{prefix}-{slug(rv['target'])}", rv["target"], kind,
                "person" if kind == "person" else "body", "preferred", "reviewed")
            target = terms[-1]
            if rv["broader"]:
                extra_hier.append({"term": rv["target"], "broader": rv["broader"]})
        target["letters"] = int(target["letters"] or 0) + int(cand["letters"] or 0) + twin_letters
        how = "officeHolderName" if rv["decision"] == "officeholder" else "altLabel"
        for nm in names:
            if nm != target["label"]:
                rel(target["term_id"], how, nm, "preferred", "reviewed")
        if rv["abbreviation"]:
            rel(target["term_id"], "abbreviation", rv["abbreviation"], "preferred", "reviewed")
    if gone:
        print(f"  reviews applied: {dict(applied)}", file=sys.stderr)

    # The hierarchy --------------------------------------------------------------
    # vocabulary/hierarchy.csv is made by hand: each row a term and the term it
    # sits under. A label there that is not a term yet becomes a category.
    # Members and unreviewed candidates are placed by rule, not by hand.
    by_label = {}
    for t_ in terms:
        if t_["status"] == "preferred":
            by_label.setdefault(t_["label"], t_["term_id"])
    roots = []
    hier = list(csv.DictReader((OUT / "hierarchy.csv").open(encoding="utf-8"))) + extra_hier
    for row in hier:
        for lab in (row["term"], row["broader"]):
            if lab and lab not in by_label:
                tid = f"C-{slug(lab)}"
                add(tid, lab, "category", "group", "preferred", "local")
                by_label[lab] = tid
        if row["broader"]:
            rel(by_label[row["term"]], "broader", by_label[row["broader"]])
        elif row["term"] not in roots:
            roots.append(row["term"])
    placed = {r["term_id"] for r in relations if r["relation"] == "broader"}
    unplaced = [t_["label"] for t_ in terms if t_["kind"] in ("topic", "organization")
                and t_["status"] == "preferred" and t_["term_id"] not in placed]
    if unplaced:
        print(f"  not in hierarchy.csv, placed at the top of their kind: {unplaced}", file=sys.stderr)
        for lab in unplaced:
            kind = next(x["kind"] for x in terms if x["label"] == lab)
            rel(by_label[lab], "broader", by_label["Topics" if kind == "topic" else "Organizations"])
    chamber_cat = {"Senate": by_label["Senators"], "House": by_label["Representatives"]}
    for b, m in rosters().items():
        for ch in m["chambers"]:
            if ch in chamber_cat:
                rel(f"M-{b}", "broader", chamber_cat[ch])
    cand_cat = {"organization": by_label["Organizations not yet reviewed"],
                "person": by_label["People not yet reviewed"],
                "unclassified": by_label["Recipients not yet sorted"]}
    for t_ in terms:
        if t_["status"] == "candidate":
            rel(t_["term_id"], "broader", cand_cat[t_["kind"]], "candidate", "rule: unreviewed")

    # A nested, alphabetical tree for browsing. Members sort by surname.
    legs_last = {b: (l.get("name", {}).get("last") or "") for b, l in legs.items()}
    term_by_id = {t_["term_id"]: t_ for t_ in terms}
    children = defaultdict(list)
    for r in relations:
        if r["relation"] == "broader":
            children[r["value"]].append(r["term_id"])

    def sort_key(tid):
        t_ = term_by_id[tid]
        if t_["kind"] == "member":
            last = legs_last.get(tid[2:]) or t_["label"].split()[-1]
            return (last.lower(), t_["label"].lower())
        return (re.sub(r"^the\s+", "", t_["label"], flags=re.I).lower(), "")

    def node(tid, seen=()):
        t_ = term_by_id[tid]
        kids = [node(c, seen + (tid,)) for c in sorted(set(children.get(tid, [])), key=sort_key)
                if c not in seen]
        n = {"id": tid, "label": t_["label"], "kind": t_["kind"]}
        if t_["status"] != "preferred":
            n["status"] = t_["status"]
        if int(t_["letters"] or 0):
            n["letters"] = int(t_["letters"])
        if kids:
            n["children"] = kids
        return n
    tree = [node(by_label[r]) for r in roots]

    seen_rel = set()
    deduped = []
    for r in relations:
        key = (r["term_id"], r["relation"], r["value"])
        if key not in seen_rel:
            seen_rel.add(key)
            deduped.append(r)
    relations[:] = deduped

    # Write ------------------------------------------------------------------------
    OUT.mkdir(exist_ok=True)
    with (OUT / "terms.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(terms[0]), lineterminator="\n")
        w.writeheader(); w.writerows(terms)
    with (OUT / "relations.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(relations[0]), lineterminator="\n")
        w.writeheader(); w.writerows(relations)
    sources = [
        {"source": "Bioguide", "full_name": "Biographical Directory of the United States Congress",
         "uri_pattern": "https://bioguide.congress.gov/search/bio/{id}", "license": "public domain (US government work)"},
        {"source": "congress-legislators", "full_name": "unitedstates/congress-legislators",
         "uri_pattern": "https://github.com/unitedstates/congress-legislators", "license": "CC0 1.0"},
        {"source": "Wikidata", "full_name": "Wikidata",
         "uri_pattern": "http://www.wikidata.org/entity/{id}", "license": "CC0 1.0"},
        {"source": "rosters", "full_name": "This repository's per-Congress rosters, data/rosters/",
         "uri_pattern": "", "license": "derived from congress-legislators"},
        {"source": "topics.py", "full_name": "This repository's topic tagger, build/topics.py",
         "uri_pattern": "", "license": "local"},
        {"source": "local", "full_name": "Chosen by hand in this repository, after checking",
         "uri_pattern": "", "license": "local"},
        {"source": "letters", "full_name": "Recipients as the letters' file names give them",
         "uri_pattern": "", "license": "local"},
    ]
    with (OUT / "sources.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(sources[0]), lineterminator="\n")
        w.writeheader(); w.writerows(sources)
    by_term = defaultdict(list)
    for r in relations:
        by_term[r["term_id"]].append({k: r[k] for k in ("relation", "value", "status", "source")})
    (OUT / "tree.json").write_text(json.dumps(tree, ensure_ascii=False, separators=(",", ":")),
                                   encoding="utf-8")
    (OUT / "vocabulary.json").write_text(json.dumps(
        {"terms": [{**t, "relations": by_term.get(t["term_id"], [])} for t in terms],
         "tree": tree},
        ensure_ascii=False, indent=1), encoding="utf-8")

    tally = Counter((t["kind"], t["status"]) for t in terms)
    for (kind, status), n in sorted(tally.items()):
        print(f"  {kind:13} {status:10} {n:6,}", file=sys.stderr)
    print(f"{len(terms):,} terms, {len(relations):,} relations -> {OUT}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
