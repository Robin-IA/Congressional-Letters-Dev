#!/usr/bin/env python3
"""Step 3: who held each address, and when.

    python3 build/address_holders.py        # writes data/address-holders.csv

An address identifies a member only for a span of time: ``murphy.house.gov``
was Tim Murphy's, then Stephanie Murphy's, then Greg Murphy's. This builds,
from the rosters (step 1) and the Wayback lookups (step 2) alone, one row per
address per member who held it, and ``attribute()`` -- the rule step 4 applies
to every letter -- reads that table. See METHODOLOGY.md, step 3.

No network. Stdlib only.
"""

from __future__ import annotations

import csv
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
ROSTERS = ROOT / "data" / "rosters"
WAYBACK = ROOT / "harvest" / "wayback"
OUT = ROOT / "data" / "address-holders.csv"
CONGRESSES = range(106, 120)

# Hosts several members used at once: the member's own path is the address.
SHARED_HOSTS = {"house.gov", "wwwc.house.gov", "senate.gov"}

COLUMNS = ["address", "urls", "bioguide_id", "name", "state", "chamber", "district",
           "held_from", "held_to", "congresses", "first_capture", "last_capture",
           "holders", "before", "after"]


def address_key(url: str) -> str:
    """Rule 1. The host without ``www.``; on a shared host, the host plus the
    member's own path segment (``senate.gov/senators/<file>`` for the holding
    pages the Senate posted in January 2001).

    Works on a letter's URL as well as a site's, so step 4 keys letters the
    same way: ``https://www.house.gov/matsui/pr/letter.pdf`` -> ``house.gov/matsui``.
    """
    u = url.strip()
    if "://" not in u:
        u = "https://" + u
    p = urlparse(u)
    host = p.netloc.lower().split(":")[0]
    host = host[4:] if host.startswith("www.") else host
    if host not in SHARED_HOSTS:
        return host
    parts = [s for s in p.path.split("/") if s]
    if not parts:
        return host
    if parts[0].lower() == "senators" and len(parts) > 1:
        return f"{host}/senators/{parts[1].lower()}"
    seg = parts[0].lower()
    if "." in seg:                       # a page at the host's root, not a member's folder
        return host
    return f"{host}/{seg}"


@dataclass
class Holding:
    address: str
    bioguide_id: str
    name: str
    state: str
    chamber: str
    district: str
    held_from: str
    held_to: str
    congresses: list[int] = field(default_factory=list)
    urls: set[str] = field(default_factory=set)
    first_capture: str = ""
    last_capture: str = ""
    holders: int = 1
    before: str = ""
    after: str = ""

    def row(self) -> dict:
        return {"address": self.address, "urls": " | ".join(sorted(self.urls)),
                "bioguide_id": self.bioguide_id, "name": self.name, "state": self.state,
                "chamber": self.chamber, "district": self.district,
                "held_from": self.held_from, "held_to": self.held_to,
                "congresses": " ".join(str(n) for n in self.congresses),
                "first_capture": self.first_capture, "last_capture": self.last_capture,
                "holders": self.holders, "before": self.before, "after": self.after}


def roster_rows(congresses=CONGRESSES, rosters: Path = ROSTERS):
    for n in congresses:
        f = rosters / f"congress{n}-roster.csv"
        if not f.exists():
            continue
        with open(f, newline="", encoding="utf-8") as h:
            for r in csv.DictReader(h):
                yield n, r


def url_chamber(url: str) -> str:
    host = urlparse(url if "://" in url else "https://" + url).netloc.lower()
    return "House" if host.endswith("house.gov") else "Senate" if host.endswith("senate.gov") else ""


def span(served: str) -> tuple[str, str]:
    a, b = served.split(" to ")
    return a.strip(), b.strip()


def build(rows, lookups) -> list[Holding]:
    """Rule 2: a member holds an address during the Congresses whose roster
    gives it to them, and within those only during their service. A member who
    held it in Congresses that do not follow one another gets a row per run.

    ``rows`` yields (congress, roster row); ``lookups`` yields step 2 rows,
    each carrying a ``congress`` key.
    """
    # (address, bioguide) -> {congress: (from, to, row, urls)}
    terms: dict[tuple[str, str], dict[int, list]] = defaultdict(dict)
    for n, r in rows:
        urls = [u.strip() for u in r["website_at_the_time"].split("|") if u.strip()]
        a, b = span(r["served_this_congress"])
        moved = re.search(r"switched chamber (\d{4}-\d{2}-\d{2})", r.get("service_notes", ""))
        for u in urls:
            key = (address_key(u), r["bioguide_id"])
            ua, ub, ur = a, b, r
            if moved:
                # one row covers both chambers; each address only its own part
                was = "House" if r["chamber"] == "Senate" else "Senate"
                if url_chamber(u) == was:
                    ub, ur = moved.group(1), {**r, "chamber": was}
                elif url_chamber(u) == r["chamber"]:
                    ua = moved.group(1)
            t = terms[key].get(n)
            if t is None:
                terms[key][n] = [ua, ub, ur, {u}]
            else:                       # two rows in one Congress (changed chamber): widen
                t[0], t[1] = min(t[0], ua), max(t[1], ub)
                t[3].add(u)

    caps: dict[tuple[str, str, int], list[str]] = defaultdict(list)
    for w in lookups:
        if w.get("lookup") != "found":
            continue
        k = (address_key(w["url"]), w["bioguide_id"], int(w["congress"]))
        caps[k] += [c for c in (w["first_capture"], w["last_capture"]) if c]

    out: list[Holding] = []
    for (addr, bid), by_n in terms.items():
        run: list[int] = []
        for n in sorted(by_n) + [None]:
            if run and (n is None or n != run[-1] + 1):
                first, last = by_n[run[0]], by_n[run[-1]]
                r = last[2]
                h = Holding(addr, bid, r["name"], r["state"], r["chamber"], r["district"],
                            min(by_n[m][0] for m in run), max(by_n[m][1] for m in run),
                            list(run), set().union(*(by_n[m][3] for m in run)))
                cs = sorted(c for m in run for c in caps.get((addr, bid, m), []))
                if cs:
                    h.first_capture, h.last_capture = cs[0], cs[-1]
                out.append(h)
                run = []
            if n is not None:
                run.append(n)

    by_addr: dict[str, list[Holding]] = defaultdict(list)
    for h in out:
        by_addr[h.address].append(h)
    for hs in by_addr.values():
        hs.sort(key=lambda h: (h.held_from, h.held_to))
        people = len({h.bioguide_id for h in hs})
        for i, h in enumerate(hs):
            h.holders = people
            prev = next((x.bioguide_id for x in reversed(hs[:i]) if x.bioguide_id != h.bioguide_id), "")
            nxt = next((x.bioguide_id for x in hs[i + 1:] if x.bioguide_id != h.bioguide_id), "")
            h.before, h.after = prev, nxt
    out.sort(key=lambda h: (h.address, h.held_from))
    return out


def overlaps(holdings: list[Holding]) -> list[tuple[Holding, Holding]]:
    """Two different members holding one address on the same day (beyond the
    shared 3 January a Congress changes hands on)."""
    by_addr: dict[str, list[Holding]] = defaultdict(list)
    for h in holdings:
        by_addr[h.address].append(h)
    bad = []
    for hs in by_addr.values():
        for i, a in enumerate(hs):
            for b in hs[i + 1:]:
                if a.bioguide_id != b.bioguide_id and a.held_from < b.held_to and b.held_from < a.held_to:
                    bad.append((a, b))
    return bad


@dataclass
class Attribution:
    bioguide_id: str          # "" when attribution is none
    attribution: str          # "holder", "after_service", "earlier_office" or "none"
    by_capture: bool = False  # dated by capture on an address with more than one holder


class Index(dict):
    """address -> its holdings in order, plus each member's service spans
    across every address, so a gap can tell "left office" from "the roster gave
    this member another address that Congress"."""
    service: dict[str, list[tuple[str, str, str]]]


def index(holdings: list[Holding]) -> Index:
    idx = Index()
    idx.service = defaultdict(list)
    for h in holdings:
        idx.setdefault(h.address, []).append(h)
        idx.service[h.bioguide_id].append((h.held_from, h.held_to, h.chamber))
    for hs in idx.values():
        hs.sort(key=lambda h: (h.held_from, h.held_to))
    return idx


def attribute(idx: Index, url: str, date: str = "",
              first_capture: str = "") -> Attribution:
    """Rule 3: the letter goes to whoever held its address on its date.

    ``url`` is the URL the letter was captured at -- never where it redirects
    (rule 4). ``date`` is the date read from the letter (YYYY-MM-DD, or
    YYYYMMDD...), and failing that ``first_capture``, the earliest capture of
    the letter's own URL, which bounds the posting date from above.

    In a span: that holder. Between two holders: the earlier, flagged
    ``after_service`` (decided 2026-11-09) unless that member was still in
    office then, in the same chamber, at another address. Before the first
    holder: that holder, flagged ``earlier_office`` (decided 2026-11-09), if
    they were in Congress then in any chamber; otherwise ``none``. After the
    last: ``none``. On the day a seat changes hands both spans include it; the
    incoming holder wins, since a new term begins at noon.
    """
    key = address_key(url)
    hs = idx.get(key, [])
    by_capture = not date
    d = _iso(date or first_capture)
    if not hs and d:
        parent = caucus_parent(idx, key)
        if parent:
            # A caucus site on a member's subdomain (cpc.grijalva.house.gov,
            # rsc.jordan.house.gov): whoever the parent address gives, flagged
            # ``caucus``. Kept in the data, not published (decided 2026-11-09):
            # about half the RSC's are letters *to* the caucus from outside
            # groups, and the RSC site carries earlier chairs' files with it.
            a = attribute(idx, "https://" + parent + "/", date, first_capture)
            return Attribution(a.bioguide_id, "caucus" if a.bioguide_id else "none", a.by_capture)
    if not hs or not d:
        return Attribution("", "none")
    flag = by_capture and len({h.bioguide_id for h in hs}) > 1
    inside = [h for h in hs if h.held_from <= d <= h.held_to]
    if inside:
        return Attribution(max(inside, key=lambda h: h.held_from).bioguide_id, "holder", flag)
    earlier = [h for h in hs if h.held_to < d]
    later = [h for h in hs if h.held_from > d]
    if earlier and later:
        last = max(earlier, key=lambda h: h.held_to)
        # Still in the same chamber, at an address the roster recorded instead
        # for those Congresses (Ed Pastor, Jim Matheson): theirs outright. A
        # House site left up after its member went to the Senate (Menendez)
        # is after service.
        serving = any(a <= d <= b and ch == last.chamber
                      for a, b, ch in getattr(idx, "service", {}).get(last.bioguide_id, []))
        return Attribution(last.bioguide_id, "holder" if serving else "after_service", flag)
    if later and not earlier:
        # Before the address's first holder, but written by that member in an
        # earlier office and reposted here: Baldwin's and Sanders's House
        # letters on their Senate sites, Cole's cole.house.gov while the roster
        # records www.house.gov/cole. Theirs, flagged (decided 2026-11-09).
        first = min(later, key=lambda h: h.held_from)
        if any(a <= d <= b for a, b, _ in getattr(idx, "service", {}).get(first.bioguide_id, [])):
            return Attribution(first.bioguide_id, "earlier_office", flag)
    return Attribution("", "none", flag)


# Attributions kept in the data but left out of every published explorer.
UNPUBLISHED = {"caucus"}


def caucus_parent(idx: Index, key: str) -> str:
    """The member address a caucus subdomain sits on, or "" if it is not one.

    ``cpc.grijalva.house.gov`` -> ``grijalva.house.gov``, only when the
    subdomain is not itself an address in the table and its parent is.
    """
    if "/" in key or key in idx:
        return ""
    parent = key.split(".", 1)[1] if key.count(".") > 2 else ""
    return parent if parent in idx else ""


def _iso(s: str) -> str:
    s = (s or "").strip()
    m = re.match(r"(\d{4})-?(\d{2})-?(\d{2})", s)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""


def lookup_rows(congresses=CONGRESSES, wayback: Path = WAYBACK):
    for n in congresses:
        f = wayback / f"congress{n}-wayback.csv"
        if not f.exists():
            continue
        with open(f, newline="", encoding="utf-8") as h:
            for r in csv.DictReader(h):
                r["congress"] = n
                r["first_capture"] = _iso(r["first_capture"])
                r["last_capture"] = _iso(r["last_capture"])
                yield r


def load(path: Path = OUT) -> list[Holding]:
    """Read data/address-holders.csv back, for step 4."""
    out = []
    with open(path, newline="", encoding="utf-8") as h:
        for r in csv.DictReader(h):
            out.append(Holding(r["address"], r["bioguide_id"], r["name"], r["state"],
                               r["chamber"], r["district"], r["held_from"], r["held_to"],
                               [int(n) for n in r["congresses"].split()],
                               set(r["urls"].split(" | ")), r["first_capture"],
                               r["last_capture"], int(r["holders"]), r["before"], r["after"]))
    return out


def main() -> None:
    holdings = build(roster_rows(), lookup_rows())
    bad = overlaps(holdings)
    for a, b in bad:
        print(f"OVERLAP {a.address}: {a.name} {a.held_from}–{a.held_to} / "
              f"{b.name} {b.held_from}–{b.held_to}", file=sys.stderr)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        for h in holdings:
            w.writerow(h.row())
    addrs = index(holdings)
    shared = {a: hs for a, hs in addrs.items() if len({h.bioguide_id for h in hs}) > 1}
    print(f"{len(addrs):,} addresses, {len(shared)} held by more than one member, "
          f"{sum(len(hs) for hs in shared.values())} holder rows between them; "
          f"{len(bad)} overlaps -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
