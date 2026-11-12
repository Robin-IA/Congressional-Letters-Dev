# Security and accessibility checks

**Status: not passing.** 2 of 3 checks have open items. Each one below has a recommended fix. Make the fixes, then re-run the explorer-checks skill. This file is replaced on every run.

| | |
|---|---|
| Explorer | https://github.com/Robin-IA/Congressional-Letters-Dev (pages served from its builds: Explorer-Letters and Explorer-Congressional-Letters-<N>) |
| Commit | `f6a926f123` on `explorer-checks` |
| Date | 2026-11-12 |
| Pages checked | `Explorer-Letters/`, `Explorer-Letters/?q=veterans`, `Explorer-Congressional-Letters-119/`, `Explorer-Congressional-Letters-119/?view=recipients`, `Explorer-Congressional-Letters-119/?view=timeline`, `Explorer-Congressional-Letters-119/?view=search&q=opioid`, `Explorer-Congressional-Letters-119/?view=about`, `Explorer-Congressional-Letters-119/?member=W000817`, `Explorer-Congressional-Letters-110/` |
| Served from | http://127.0.0.1:8949/ |
| Live site (headers) | https://internetarchivecanada.github.io/congressional-letters/ |
| Standard | WCAG 2.2 Level AA |
| Security references | OWASP Top 10:2025 and ASVS 5.0.0 |
| Tools | axe-core 4.14.0, html5lib, ruff, bandit, pip-audit, headless Chromium |
| Reviewed by | Claude (claude-opus-5-5) via the explorer-checks skill |
| Skill version | 2026.11.05.9 |

## Summary

| Check | Result | Must fix | Needs review | Advisory |
|---|---|---:|---:|---:|
| Code validity | Pass | 0 | 0 | 12 |
| Code security | **Not passing** | 7 | 0 | 35 |
| Accessibility (WCAG 2.2 AA) | **Not passing** | 14 | 0 | 5 |

## What a pass means

Each check combines automated tools with a review of the code and pages against a written checklist. A pass means neither found anything open on the date and commit above. The standards are met as far as those checks can establish: it is a self-assessment, not third-party certification. Automated testing finds a minority of accessibility barriers. Testing with people who use assistive technology is still worth doing, and a change to the explorer needs a re-run.

## Code validity

No open items.

## Code security

### `S-47758c` Member website links are not checked for scheme

- **Must fix** · found by review · OWASP A05:2025 · ASVS V1
- **Where:** `app.js siteHref()/el('a', { href: siteHref(m) }) in the iac-119th template; build/build_site.py writes member['url'] into index.json as site`

```text
m.site comes from congress-legislators (and the departed rosters) and is written into an href unchecked. A javascript: URL would survive.
```

**Recommended fix:** In build/build_site.py write site only if it matches ^https?://, else omit it; app.js then shows the host without a link.

### `S-3e1881` Use of weak SHA1 hash for security. Consider usedforsecurity=False

- **Must fix** · found by bandit · OWASP A04:2025 · ASVS V11
- **Where:** `build/directory_urls.py:116`

```text
115     CACHE.mkdir(parents=True, exist_ok=True)
116     f = CACHE / (hashlib.sha1(f"{ts} {src}".encode()).hexdigest() + ".html")
117     if not f.exists():
```

**Recommended fix:** See https://bandit.readthedocs.io/en/1.9.4/plugins/b324_hashlib.html. If the flagged input can never come from outside (say why in the review), clear it.

### `S-bb0739` Use of weak SHA1 hash for security. Consider usedforsecurity=False

- **Must fix** · found by bandit · OWASP A04:2025 · ASVS V11
- **Where:** `build/resolve_wrappers.py:250`

```text
249                         "digest": base64.b32encode(
250                             hashlib.sha1(blob).digest()).decode("ascii"),
251                         "blob": blob}
```

**Recommended fix:** See https://bandit.readthedocs.io/en/1.9.4/plugins/b324_hashlib.html. If the flagged input can never come from outside (say why in the review), clear it.

### `S-11bd79` Use of weak SHA1 hash for security. Consider usedforsecurity=False

- **Must fix** · found by bandit · OWASP A04:2025 · ASVS V11
- **Where:** `build/wayback_lookup.py:101`

```text
100     CACHE.mkdir(parents=True, exist_ok=True)
101     f = CACHE / (hashlib.sha1(json.dumps(key, sort_keys=True).encode()).hexdigest() + ".json")
102     if f.exists():
```

**Recommended fix:** See https://bandit.readthedocs.io/en/1.9.4/plugins/b324_hashlib.html. If the flagged input can never come from outside (say why in the review), clear it.

### `S-fbe8a3` String rendered as markup or code (innerHTML)

- **Must fix** · found by explorer-checks · OWASP A05:2025 · ASVS V1
- **Where:** `federated/index.html:300`

```text
host.innerHTML = DATA.congresses.map(c => {

Review: drawCongresses: c.href goes into href="${c.href}" twice unescaped and unchecked, and c.status into class="congress ${c.status}", both from data.json. Today data.json is our own build (build/federated_mockup.py), but the rule is to escape data whatever its source. Fix: esc(c.href) after checking it starts with ../ or https://, and esc(c.status).
```

**Recommended fix:** Trace what reaches this sink. If any part comes from data (archive.org metadata, captured page text, the URL, user input), escape it or build nodes with textContent. Clear it only if every part is a literal or already escaped, and name the escaping function.

### `S-784cfb` String rendered as markup or code (innerHTML)

- **Must fix** · found by explorer-checks · OWASP A05:2025 · ASVS V1
- **Where:** `federated/index.html:366`

```text
$('#groups').innerHTML = [...groups.keys()].sort((a, b) => b - a).map(n => {

Review: #groups: c.href is put in an href unescaped; m.state and the year r[2] (from search.json) are interpolated without esc(). r[4], m.name and rec are escaped. Fix: esc(m.state), Number(r[2]), and esc(c.href) with the same prefix check.
```

**Recommended fix:** Trace what reaches this sink. If any part comes from data (archive.org metadata, captured page text, the URL, user input), escape it or build nodes with textContent. Clear it only if every part is a literal or already escaped, and name the escaping function.

### `S-4e8008` String rendered as markup or code (innerHTML)

- **Must fix** · found by explorer-checks · OWASP A05:2025 · ASVS V1
- **Where:** `federated/index.html:391`

```text
$('#careerHead').innerHTML = `<a href="../119th/?member=${m.id}">${esc(m.name)}</a>`;

Review: #careerHead: href="../119th/?member=${m.id}" puts m.id from 119th/index.json into an attribute unescaped (m.name is escaped). Fix: encodeURIComponent(m.id).
```

**Recommended fix:** Trace what reaches this sink. If any part comes from data (archive.org metadata, captured page text, the URL, user input), escape it or build nodes with textContent. Clear it only if every part is a literal or already escaped, and name the escaping function.

<details><summary>Manual checklist (6 pass, 4 fail, 10 n/a)</summary>

| Item | Result | Note |
|---|---|---|
| No secrets | pass | No secret findings from the scanner; no keys or tokens in the build scripts, which read only public endpoints. |
| Untrusted data is escaped | fail | Explorers and the home page are clean (no innerHTML of data). The federated/ mockup has three sinks with unescaped data fields: S-fbe8a3, S-784cfb, S-4e8008. |
| URLs from data are safe | fail | Letter and thumbnail links use a fixed https://web.archive.org prefix. Member site links (m.site) are not scheme-checked: see manual:url-scheme. |
| Harvested data is validated | fail | Issue #58 (filed today): 13 letters carry impossible dates (one after its own first capture), so the build does not check parsed dates against the capture or the member's service. Same fix family as manual:url-scheme. |
| Third-party code is pinned | pass | No CDN scripts: the pages load only their own app.js / hub.js. |
| No mixed content | pass | Everything the pages load is same-origin over https; outbound links to web.archive.org are https. |
| Dependencies are pinned and maintained | fail | requirements.txt names pypdfium2, pillow, pypdf, internetarchive without versions (S-c8f77d). Build-time only, nothing served. Fix: pin exact versions. |
| Dependencies have no known vulnerabilities | pass | pip-audit raised no dep: findings; no package.json; no vendored front-end libraries. |
| Third parties a visitor's browser contacts | pass | None on load. web.archive.org is contacted only when a reader opens a letter, which is the point of the site. |
| What Pages publishes | pass | The explorer repos publish only built output. Congressional-Letters-Dev is public and serves its whole tree on Pages (scripts, data/, docs): all intended to be public; checked that no notes or credentials are among them. |
| Server input is validated | n/a | Static site, no server. |
| Configuration is safe to serve | n/a | Static site, no server. |
| Errors are handled and do not leak | n/a | Static site, no server. |
| Commands built from data | n/a | Not served. Build scripts' subprocess calls use argument lists (bandit B603 advisories), with no shell=True. |
| Who can write | n/a | No contributions or uploads. |
| Fetches of submitted URLs | n/a | No contributions or uploads. |
| Scope of writes | n/a | No contributions or uploads. |
| Limits | n/a | No public queue. |
| Model output is untrusted | n/a | No AI components on the site; OCR text is not shown. |
| Models are pinned | n/a | No models. |

</details>

<details><summary>Cleared on review (20)</summary>

| Id | Item | Where | Why cleared |
|---|---|---|---|
| `S-9c80d3` | String rendered as markup or code (innerHTML) | `app.js:45` | el() (app.js:40-53) writes innerHTML only for an attribute named 'html'. No caller passes one: grep for 'html:' finds no use in app.js or in the built explorers' app.js (copied from the iac-119th template). Every value reaches the DOM through setAttribute or createTextNode. |
| `S-1d9bee` | String rendered as markup or code (innerHTML) | `federated/index.html:253` | federated/index.html bars(): every interpolated value is a computed number (x, y, widths), fmt(d.value), or esc(d.label / d.sub / d.aria / opts.aria). esc() (line 222) escapes & < > " and every attribute is double-quoted. |
| `S-fffc65` | String rendered as markup or code (innerHTML) | `federated/index.html:260` | tip.innerHTML = d.tip. Every tip is built from ord(n), fmt(...), long(date) (Date.toLocaleDateString output) and esc(c.detail) / esc(m.name): drawTimeline (line 295), search hits (line 365), careers (line 396). |
| `S-3a7181` | String rendered as markup or code (innerHTML) | `federated/index.html:356` | #summary: fmt(total), groups.size (a number) and esc(q). The ?q= value from the URL is escaped here, encodeURIComponent'd in hrefs (line 369) and esc'd in the chart aria-label: no reflected route. |
| `S-6273f5` | String rendered as markup or code (innerHTML) | `federated/index.html:414` | <option value="${esc(m.name)}">: esc() escapes the double quote, and the attribute is double-quoted. |
| `S-7d1cf4` | String rendered as markup or code (insertAdjacentHTML) | `federated/index.html:404` | insertAdjacentHTML of fmt(DATA.total), a number; the rest is a literal. |
| `S-7c973f` | String rendered as markup or code (innerHTML) | `index.html:152` | Dev repo root page. Only fmt(index.letters), fmt(index.members_with_letters) (fmt = Number(n).toLocaleString) and index.span, an [int, int] that build_site.py writes from Counter keys of years. No string from data reaches it. Recommend Number() around span too. |
| `S-08fe87` | Audit url open for permitted schemes. Allowing use of file:/ or custom schemes is often unexpected. | `build/backfill_roster.py:75` | Every urlopen fetches a fixed https:// prefix written in the source: web.archive.org (cdx and id_ replay), archive.org (advancedsearch, scrape), unitedstates.github.io/congress-legislators, bioguide.congress.gov or www.wikidata.org/w/api.php. Data only fills the host or path after that fixed scheme  |
| `S-4de3ea` | Audit url open for permitted schemes. Allowing use of file:/ or custom schemes is often unexpected. | `build/build_vocabulary.py:173` | Every urlopen fetches a fixed https:// prefix written in the source: web.archive.org (cdx and id_ replay), archive.org (advancedsearch, scrape), unitedstates.github.io/congress-legislators, bioguide.congress.gov or www.wikidata.org/w/api.php. Data only fills the host or path after that fixed scheme  |
| `S-c81aa3` | Audit url open for permitted schemes. Allowing use of file:/ or custom schemes is often unexpected. | `build/chamber_rosters.py:138` | Every urlopen fetches a fixed https:// prefix written in the source: web.archive.org (cdx and id_ replay), archive.org (advancedsearch, scrape), unitedstates.github.io/congress-legislators, bioguide.congress.gov or www.wikidata.org/w/api.php. Data only fills the host or path after that fixed scheme  |
| `S-752549` | Audit url open for permitted schemes. Allowing use of file:/ or custom schemes is often unexpected. | `build/congress_roster.py:114` | Every urlopen fetches a fixed https:// prefix written in the source: web.archive.org (cdx and id_ replay), archive.org (advancedsearch, scrape), unitedstates.github.io/congress-legislators, bioguide.congress.gov or www.wikidata.org/w/api.php. Data only fills the host or path after that fixed scheme  |
| `S-6655f9` | Audit url open for permitted schemes. Allowing use of file:/ or custom schemes is often unexpected. | `build/directory_urls.py:88` | Every urlopen fetches a fixed https:// prefix written in the source: web.archive.org (cdx and id_ replay), archive.org (advancedsearch, scrape), unitedstates.github.io/congress-legislators, bioguide.congress.gov or www.wikidata.org/w/api.php. Data only fills the host or path after that fixed scheme  |
| `S-ea0a74` | Audit url open for permitted schemes. Allowing use of file:/ or custom schemes is often unexpected. | `build/fetch_pdfs.py:100` | Every urlopen fetches a fixed https:// prefix written in the source: web.archive.org (cdx and id_ replay), archive.org (advancedsearch, scrape), unitedstates.github.io/congress-legislators, bioguide.congress.gov or www.wikidata.org/w/api.php. Data only fills the host or path after that fixed scheme  |
| `S-d202c3` | Audit url open for permitted schemes. Allowing use of file:/ or custom schemes is often unexpected. | `build/harvest.py:266` | Every urlopen fetches a fixed https:// prefix written in the source: web.archive.org (cdx and id_ replay), archive.org (advancedsearch, scrape), unitedstates.github.io/congress-legislators, bioguide.congress.gov or www.wikidata.org/w/api.php. Data only fills the host or path after that fixed scheme  |
| `S-4c3430` | Audit url open for permitted schemes. Allowing use of file:/ or custom schemes is often unexpected. | `build/ia_search.py:122` | Every urlopen fetches a fixed https:// prefix written in the source: web.archive.org (cdx and id_ replay), archive.org (advancedsearch, scrape), unitedstates.github.io/congress-legislators, bioguide.congress.gov or www.wikidata.org/w/api.php. Data only fills the host or path after that fixed scheme  |
| `S-15e590` | Audit url open for permitted schemes. Allowing use of file:/ or custom schemes is often unexpected. | `build/pc/fetch_for_ocr.py:69` | Every urlopen fetches a fixed https:// prefix written in the source: web.archive.org (cdx and id_ replay), archive.org (advancedsearch, scrape), unitedstates.github.io/congress-legislators, bioguide.congress.gov or www.wikidata.org/w/api.php. Data only fills the host or path after that fixed scheme  |
| `S-b40f11` | Audit url open for permitted schemes. Allowing use of file:/ or custom schemes is often unexpected. | `build/pc/run_pc.py:83` | Every urlopen fetches a fixed https:// prefix written in the source: web.archive.org (cdx and id_ replay), archive.org (advancedsearch, scrape), unitedstates.github.io/congress-legislators, bioguide.congress.gov or www.wikidata.org/w/api.php. Data only fills the host or path after that fixed scheme  |
| `S-b0e2de` | Audit url open for permitted schemes. Allowing use of file:/ or custom schemes is often unexpected. | `build/thumbs.py:222` | Every urlopen fetches a fixed https:// prefix written in the source: web.archive.org (cdx and id_ replay), archive.org (advancedsearch, scrape), unitedstates.github.io/congress-legislators, bioguide.congress.gov or www.wikidata.org/w/api.php. Data only fills the host or path after that fixed scheme  |
| `S-3105cc` | Audit url open for permitted schemes. Allowing use of file:/ or custom schemes is often unexpected. | `build/thumbs.py:334` | Every urlopen fetches a fixed https:// prefix written in the source: web.archive.org (cdx and id_ replay), archive.org (advancedsearch, scrape), unitedstates.github.io/congress-legislators, bioguide.congress.gov or www.wikidata.org/w/api.php. Data only fills the host or path after that fixed scheme  |
| `S-5818c2` | Audit url open for permitted schemes. Allowing use of file:/ or custom schemes is often unexpected. | `build/wayback_lookup.py:86` | Every urlopen fetches a fixed https:// prefix written in the source: web.archive.org (cdx and id_ replay), archive.org (advancedsearch, scrape), unitedstates.github.io/congress-legislators, bioguide.congress.gov or www.wikidata.org/w/api.php. Data only fills the host or path after that fixed scheme  |

</details>

## Accessibility (WCAG 2.2 AA)

### `A-2942b7` Links must be distinguishable without relying on color

- **Must fix** · found by axe-core 4.14.0 · WCAG 1.4.1
- **Where:** `/Explorer-Congressional-Letters-110/ link-in-text-block`

```text
1 element(s): a[href="?view=about"]
Fix any of the following:
  The link has insufficient color contrast of 1.04:1 with the surrounding text. (Minimum contrast is 3:1, link text: #2f6bbd, surrounding text: #6e6e73)
  The link has no styling (such as underline) to distinguish it from the surrounding text
```

**Recommended fix:** Ensure links are distinguished from surrounding text in a way that does not rely on color See https://dequeuniversity.com/rules/axe/4.14/link-in-text-block?application=axeAPI

### `A-cf4f4f` Select element must have an accessible name

- **Must fix** · found by axe-core 4.14.0 · WCAG 4.1.2
- **Where:** `/Explorer-Congressional-Letters-110/ select-name`

```text
3 element(s): select:nth-child(2); select:nth-child(3); select:nth-child(4)
Fix any of the following:
  Element does not have an implicit (wrapped) <label>
  Element does not have an explicit <label>
  aria-label attribute does not exist or is empty
  aria-labelledby attribute does not exist, references elements that do not exist or references elements that are empty
  Element has no title attribute
  Element's default semantics were not overridden with role="none" or role="presentation"
```

**Recommended fix:** Ensure select element has an accessible name See https://dequeuniversity.com/rules/axe/4.14/select-name?application=axeAPI

### `A-bac58d` Page scrolls sideways at 320 px wide

- **Must fix** · found by explorer-checks · WCAG 1.4.10
- **Where:** `/Explorer-Congressional-Letters-119/`

```text
219px wider than the viewport
```

**Recommended fix:** Let content wrap at narrow widths: max-width:100% on media and tables in a scrolling container, no fixed widths over 320px. Data tables may scroll inside their own container.

### `A-4a24ac` Elements must meet minimum color contrast ratio thresholds

- **Must fix** · found by axe-core 4.14.0 · WCAG 1.4.3
- **Where:** `/Explorer-Congressional-Letters-119/ color-contrast`

```text
5 element(s): .sub > .faint; tr:nth-child(1) > .who:nth-child(3) > .faint; tr:nth-child(2) > .who:nth-child(3) > .faint; tr:nth-child(3) > .who:nth-child(3) > .faint; tr:nth-child(5) > .who:nth-child(3) > .faint
Fix any of the following:
  Element has insufficient color contrast of 2.84 (foreground color: #96969b, background color: #fbfbfd, font size: 10.9pt (14.5px), font weight: normal). Expected contrast ratio of 4.5:1
```

**Recommended fix:** Ensure the contrast between foreground and background colors meets WCAG 2 AA minimum contrast ratio thresholds See https://dequeuniversity.com/rules/axe/4.14/color-contrast?application=axeAPI

### `A-3e6bb7` Links must be distinguishable without relying on color

- **Must fix** · found by axe-core 4.14.0 · WCAG 1.4.1
- **Where:** `/Explorer-Congressional-Letters-119/ link-in-text-block`

```text
1 element(s): a[href="?view=about"]
Fix any of the following:
  The link has insufficient color contrast of 1.04:1 with the surrounding text. (Minimum contrast is 3:1, link text: #2f6bbd, surrounding text: #6e6e73)
  The link has no styling (such as underline) to distinguish it from the surrounding text
```

**Recommended fix:** Ensure links are distinguished from surrounding text in a way that does not rely on color See https://dequeuniversity.com/rules/axe/4.14/link-in-text-block?application=axeAPI

### `A-ccd44e` Select element must have an accessible name

- **Must fix** · found by axe-core 4.14.0 · WCAG 4.1.2
- **Where:** `/Explorer-Congressional-Letters-119/ select-name`

```text
3 element(s): select:nth-child(2); select:nth-child(3); select:nth-child(4)
Fix any of the following:
  Element does not have an implicit (wrapped) <label>
  Element does not have an explicit <label>
  aria-label attribute does not exist or is empty
  aria-labelledby attribute does not exist, references elements that do not exist or references elements that are empty
  Element has no title attribute
  Element's default semantics were not overridden with role="none" or role="presentation"
```

**Recommended fix:** Ensure select element has an accessible name See https://dequeuniversity.com/rules/axe/4.14/select-name?application=axeAPI

### `A-f3579e` All touch targets must be 24px large, or leave sufficient space

- **Must fix** · found by axe-core 4.14.0 · WCAG 2.5.8
- **Where:** `/Explorer-Congressional-Letters-119/ target-size`

```text
27 element(s): a[href="?view=search&q=FTC"]; a[href="?view=search&q=Nominations"]; a[href="?view=search&q=Tariffs"]; .shot[target="_blank"][rel="noopener"]:nth-child(21) > .topics > .topic[href="?view=search&q=Ethics"]; .shot[target="_blank"][rel="noopener"]:nth-child(21) > .topics > .topic[href="?view=search&q=DOD"]
Fix any of the following:
  Target has insufficient size (29.7px by 18px, should be at least 24px by 24px)
  Target has insufficient space to its closest neighbors. Safe clickable space has a diameter of 18px instead of at least 24px.
```

**Recommended fix:** Ensure touch targets have sufficient size and space See https://dequeuniversity.com/rules/axe/4.14/target-size?application=axeAPI

### `A-6500b2` Page scrolls sideways at 320 px wide

- **Must fix** · found by explorer-checks · WCAG 1.4.10
- **Where:** `/Explorer-Letters/`

```text
21px wider than the viewport
```

**Recommended fix:** Let content wrap at narrow widths: max-width:100% on media and tables in a scrolling container, no fixed widths over 320px. Data tables may scroll inside their own container.

### `A-251e8d` Elements must meet minimum color contrast ratio thresholds

- **Must fix** · found by axe-core 4.14.0 · WCAG 1.4.3
- **Where:** `/Explorer-Letters/ color-contrast`

```text
7 element(s): figcaption; .kicker; h1; #lede; .herotext > .note
Fix any of the following:
  Element's background color could not be determined because element contains an image node

Review: Measured by hand. The hero text sits on a gradient (#f6e9ea to #faf7f2), not the image, and passes: kicker 8.5:1, h1 11.3:1, lede 13:1, note 5.1:1. The photo credit (figcaption) is white 11.5px on rgba(20,20,24,.55) over the photograph: over the photo's lightest pixels that composites to about rgb(126,126,128), 4.0:1, under 4.5:1. Fix in build/hub/index.html: raise the figcaption background to rgba(20,20,24,.72) (worst case about 6.4:1).
```

**Recommended fix:** Ensure the contrast between foreground and background colors meets WCAG 2 AA minimum contrast ratio thresholds See https://dequeuniversity.com/rules/axe/4.14/color-contrast?application=axeAPI

### `A-4c1f2b` Explorer filter count is not announced

- **Must fix** · found by review · WCAG 4.1.3
- **Where:** `app.js (iac-119th template), .count in the members and recipients views`

```text
Changing Chamber to Senate changes '555 of 555 members' to '104 of 555 members' with no live region on the page.
```

**Recommended fix:** Add role: 'status' to the el('span', { class: 'count' }, ...) that renders 'N of M members'. The explorer pages are generated: build_congress.py copies index.html and app.js from the git ref iac-119th (TEMPLATE_REF) and rewrites them, so a fix to the explorers goes into that template (and from there into each explorer on the next build), not into the published repos.

### `A-dd0005` Changing a filter sends keyboard focus to the top of the page

- **Must fix** · found by review · WCAG 2.4.3
- **Where:** `app.js (iac-119th template), setParam()/go() rebuilding the view`

```text
Focus the Chamber select and change it to Senate: the view is rebuilt and document.activeElement becomes <body>, so a keyboard user starts again from the top.
```

**Recommended fix:** In go() (or setParam), remember which control had focus (e.g. its name or a data-key) before rebuilding, and focus the new control with the same key after render. The explorer pages are generated: build_congress.py copies index.html and app.js from the git ref iac-119th (TEMPLATE_REF) and rewrites them, so a fix to the explorers goes into that template (and from there into each explorer on the next build), not into the published repos.

### `A-4cd8bb` Explorer views have no headings: the page title is a styled paragraph

- **Must fix** · found by review · WCAG 1.3.1
- **Where:** `app.js (iac-119th template), the 'hero' line in the members view; Explorer-Congressional-Letters-119/`

```text
On Explorer-Congressional-Letters-119/ document.querySelectorAll('h1,h2,h3') is empty. '119th Congress (2025-26)' is <p class="hero">; member names are an <h2> only on the member view.
```

**Recommended fix:** In app.js change el('p', { class: 'hero' }, ...) to el('h1', { class: 'hero' }, ...) (h1 is already reset to inherit size in the page CSS). The explorer pages are generated: build_congress.py copies index.html and app.js from the git ref iac-119th (TEMPLATE_REF) and rewrites them, so a fix to the explorers goes into that template (and from there into each explorer on the next build), not into the published repos.

### `A-8bd0c2` Home page search results are not announced

- **Must fix** · found by review · WCAG 4.1.3
- **Where:** `build/hub/index.html (#results) and build/hub/hub.js; Explorer-Letters/?q=veterans`

```text
After a search, '1,418 letters across 14 Congresses' is written into #results, which has no aria-live or role=status. The only live region is #stats (the fixed totals).
```

**Recommended fix:** Give the results summary line its own element with role="status" (e.g. <p id="resultsSummary" role="status">) in build/hub/index.html and write the count there in hub.js, keeping the result list outside the live region.

### `A-155de5` Explorer search box and filter dropdowns have borders too faint to see

- **Must fix** · found by review · WCAG 1.4.11
- **Where:** `explorer index.html (iac-119th template) CSS: .controls input[type=search] and .controls select, border 1px solid var(--hair)`

```text
Border #e4e4e8 on #fbfbfd, about 1.2:1; 3:1 is needed for the edge of a control.
```

**Recommended fix:** Give .controls input and .controls select a border of #8a8a90 (3.4:1 on #fbfbfd) instead of var(--hair). The explorer pages are generated: build_congress.py copies index.html and app.js from the git ref iac-119th (TEMPLATE_REF) and rewrites them, so a fix to the explorers goes into that template (and from there into each explorer on the next build), not into the published repos.

<details><summary>Manual checklist (13 pass, 7 fail, 2 n/a)</summary>

| Item | Result | Note |
|---|---|---|
| 1.1.1 Non-text content | pass | Letter images have alt text naming member, recipient and year; the home page chart is a list of 14 links each named with the Congress, dates and count. |
| 1.3.1 Info and relationships | fail | Home page headings are correct (h1, h2). Explorer views have no headings: manual:headings. |
| 1.3.2 Meaningful sequence | pass | DOM order matches reading order on the home page (text column, then letters) and in the explorers. |
| 1.4.1 Use of color | pass | Selected explorer tab has an underline and aria-current; the chart uses a single colour with labels. In-text links fail separately (axe link-in-text-block). |
| 1.4.11 Non-text contrast | fail | Explorer filter controls' borders 1.2:1: manual:non-text-contrast. Home page search border (#2c5aa0, 2px) and focus rings pass. |
| 1.4.4 Resize text / 1.4.12 Text spacing | pass | At 640 px (200% of 1280) neither the home page nor the explorer member view scrolls sideways or clips. 320 px reflow fails separately (reflow:320). |
| 2.4.4 Link purpose | pass | Member cards are named by member, chart links by Congress and count, site links by host. |
| 2.4.6 Headings and labels | fail | The explorer's three filter dropdowns have no label (axe select-name), and the explorer has no headings (manual:headings). |
| 3.1.1 Language of page | pass | lang="en" on the home page and every explorer. |
| 2.1.1 Keyboard | pass | Every control is a native link, button, input or select; the chart bars are links. |
| 2.1.2 No keyboard trap | pass | No modals or embeds; tabbing moves through and out of every widget. |
| 2.4.1 Bypass blocks | pass | No skip link, but header, nav, search, main and footer landmarks on both page types. |
| 2.4.3 Focus order | fail | Order follows reading order, but changing an explorer filter drops focus to the top: manual:focus-after-filter. |
| 2.4.7 Focus visible | pass | Home page: 3px outline on every link and button, ring shadow on the search box. Explorer: the browser's focus ring (outline auto) on every control, checked by tabbing. |
| 2.4.11 Focus not obscured | pass | A card focused further down the explorer page lands at 401 px, clear of the sticky tab bar (bottom at 47 px). |
| 2.5.8 Target size | fail | Topic chips and suggestion links in the explorer are 18 px high (axe target-size). |
| 2.2.2 Pause, stop, hide | n/a | Nothing moves or auto-updates. |
| 3.2.2 On input | pass | Changing a select filters in place (history.replaceState); it does not navigate away. The lost focus is recorded under 2.4.3. |
| 3.3.2 Labels or instructions | fail | Search boxes have an accessible name and an adjacent Search button (G167), but the explorer's dropdowns have no visible or programmatic label (axe select-name). |
| 4.1.2 Name, role, value | pass | View tabs are buttons carrying aria-current on the selected one; the letters/list toggle uses aria-pressed. |
| 4.1.3 Status messages | fail | Neither the home page search count nor the explorer filter count is announced: manual:status-messages (two findings). |
| 1.2.2 Captions | n/a | No audio or video. |

</details>

## Advisory (52)

Optional. These items never block a pass.

| Id | Check | Item | Where | Reference | Suggestion |
|---|---|---|---|---|---|
| `V-f5b37c` | validity | Local variable `first` is assigned to but never used | `build/address_holders.py:157` |  | Remove assignment to unused variable `first` |
| `V-b46868` | validity | `sys` imported but unused | `build/backfill_roster.py:44` |  | Remove unused import: `sys` |
| `V-6387e6` | validity | Ambiguous variable name: `l` | `build/build_vocabulary.py:524` |  | See https://docs.astral.sh/ruff/rules/ for this rule. |
| `V-857ea8` | validity | Multiple statements on one line (semicolon) | `build/build_vocabulary.py:591` |  | See https://docs.astral.sh/ruff/rules/ for this rule. |
| `V-9e61c7` | validity | Multiple statements on one line (semicolon) | `build/build_vocabulary.py:594` |  | See https://docs.astral.sh/ruff/rules/ for this rule. |
| `V-301d38` | validity | Multiple statements on one line (semicolon) | `build/build_vocabulary.py:613` |  | See https://docs.astral.sh/ruff/rules/ for this rule. |
| `V-2a2c6f` | validity | Do not assign a `lambda` expression, use a `def` | `build/congress_roster.py:221` |  | Rewrite `k` as a `def` |
| `V-fca0cc` | validity | Ambiguous variable name: `l` | `build/harvest_paths.py:237` |  | See https://docs.astral.sh/ruff/rules/ for this rule. |
| `V-a95a69` | validity | `sys` imported but unused | `build/ia_search.py:33` |  | Remove unused import: `sys` |
| `V-c7efa8` | validity | Ambiguous variable name: `l` | `build/pc/ocr_tesseract.py:153` |  | See https://docs.astral.sh/ruff/rules/ for this rule. |
| `V-92f2f6` | validity | f-string without any placeholders | `build/thumbs.py:558` |  | Remove extraneous `f` prefix |
| `V-3dc06e` | validity | f-string without any placeholders | `build/thumbs.py:559` |  | Remove extraneous `f` prefix |
| `S-e84315` | security | Consider possible security implications associated with the subprocess module. | `build/build_congress.py:40` |  | See https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_imports.html#b404-import-subprocess. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-515964` | security | Try, Except, Continue detected. | `build/build_congress.py:138` |  | See https://bandit.readthedocs.io/en/1.9.4/plugins/b112_try_except_continue.html. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-60fa54` | security | Starting a process with a partial executable path | `build/build_congress.py:185` | A05:2025 · ASVS V1 | See https://bandit.readthedocs.io/en/1.9.4/plugins/b607_start_process_with_partial_path.html. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-3995d8` | security | subprocess call - check for execution of untrusted input. | `build/build_congress.py:185` | A05:2025 · ASVS V1 | See https://bandit.readthedocs.io/en/1.9.4/plugins/b603_subprocess_without_shell_equals_true.html. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-989200` | security | subprocess call - check for execution of untrusted input. | `build/build_congress.py:272` | A05:2025 · ASVS V1 | See https://bandit.readthedocs.io/en/1.9.4/plugins/b603_subprocess_without_shell_equals_true.html. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-badfac` | security | Try, Except, Continue detected. | `build/build_site.py:328` |  | See https://bandit.readthedocs.io/en/1.9.4/plugins/b112_try_except_continue.html. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-118168` | security | Try, Except, Continue detected. | `build/fetch_pdfs.py:51` |  | See https://bandit.readthedocs.io/en/1.9.4/plugins/b112_try_except_continue.html. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-011e18` | security | Try, Except, Continue detected. | `build/harvest.py:815` |  | See https://bandit.readthedocs.io/en/1.9.4/plugins/b112_try_except_continue.html. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-04a316` | security | Consider possible security implications associated with the subprocess module. | `build/ocr_letters.py:30` |  | See https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_imports.html#b404-import-subprocess. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-233055` | security | Try, Except, Continue detected. | `build/ocr_letters.py:46` |  | See https://bandit.readthedocs.io/en/1.9.4/plugins/b112_try_except_continue.html. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-fdd90c` | security | Try, Except, Continue detected. | `build/ocr_letters.py:59` |  | See https://bandit.readthedocs.io/en/1.9.4/plugins/b112_try_except_continue.html. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-7f90d9` | security | subprocess call - check for execution of untrusted input. | `build/ocr_letters.py:78` | A05:2025 · ASVS V1 | See https://bandit.readthedocs.io/en/1.9.4/plugins/b603_subprocess_without_shell_equals_true.html. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-e239ec` | security | Try, Except, Continue detected. | `build/pc/fetch_for_ocr.py:97` |  | See https://bandit.readthedocs.io/en/1.9.4/plugins/b112_try_except_continue.html. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-599955` | security | Try, Except, Continue detected. | `build/pc/make_render_bundle.py:70` |  | See https://bandit.readthedocs.io/en/1.9.4/plugins/b112_try_except_continue.html. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-a2d9a7` | security | Try, Except, Continue detected. | `build/pc/merge_render.py:42` |  | See https://bandit.readthedocs.io/en/1.9.4/plugins/b112_try_except_continue.html. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-5098dd` | security | Try, Except, Continue detected. | `build/pc/merge_render.py:55` |  | See https://bandit.readthedocs.io/en/1.9.4/plugins/b112_try_except_continue.html. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-ac13f2` | security | Try, Except, Continue detected. | `build/pc/merge_render.py:111` |  | See https://bandit.readthedocs.io/en/1.9.4/plugins/b112_try_except_continue.html. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-94fcc6` | security | Consider possible security implications associated with the subprocess module. | `build/pc/ocr_tesseract.py:45` |  | See https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_imports.html#b404-import-subprocess. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-2b11f3` | security | Try, Except, Continue detected. | `build/pc/ocr_tesseract.py:71` |  | See https://bandit.readthedocs.io/en/1.9.4/plugins/b112_try_except_continue.html. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-e1918b` | security | Try, Except, Continue detected. | `build/pc/ocr_tesseract.py:84` |  | See https://bandit.readthedocs.io/en/1.9.4/plugins/b112_try_except_continue.html. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-3e4c48` | security | subprocess call - check for execution of untrusted input. | `build/pc/ocr_tesseract.py:130` | A05:2025 · ASVS V1 | See https://bandit.readthedocs.io/en/1.9.4/plugins/b603_subprocess_without_shell_equals_true.html. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-dd02d2` | security | subprocess call - check for execution of untrusted input. | `build/pc/ocr_tesseract.py:181` | A05:2025 · ASVS V1 | See https://bandit.readthedocs.io/en/1.9.4/plugins/b603_subprocess_without_shell_equals_true.html. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-9325ed` | security | Consider possible security implications associated with the subprocess module. | `build/pc/run_pc.py:23` |  | See https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_imports.html#b404-import-subprocess. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-c2eb49` | security | Try, Except, Pass detected. | `build/pc/run_pc.py:86` |  | See https://bandit.readthedocs.io/en/1.9.4/plugins/b110_try_except_pass.html. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-8df66b` | security | subprocess call - check for execution of untrusted input. | `build/pc/run_pc.py:103` | A05:2025 · ASVS V1 | See https://bandit.readthedocs.io/en/1.9.4/plugins/b603_subprocess_without_shell_equals_true.html. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-4b7563` | security | Consider possible security implications associated with the subprocess module. | `build/pc/run_render.py:29` |  | See https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_imports.html#b404-import-subprocess. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-bf91b2` | security | subprocess call - check for execution of untrusted input. | `build/pc/run_render.py:86` | A05:2025 · ASVS V1 | See https://bandit.readthedocs.io/en/1.9.4/plugins/b603_subprocess_without_shell_equals_true.html. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-87c64f` | security | Try, Except, Pass detected. | `build/resolve_wrappers.py:322` |  | See https://bandit.readthedocs.io/en/1.9.4/plugins/b110_try_except_pass.html. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-a4d1d5` | security | Try, Except, Pass detected. | `build/resolve_wrappers.py:331` |  | See https://bandit.readthedocs.io/en/1.9.4/plugins/b110_try_except_pass.html. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-1a0d6b` | security | Try, Except, Continue detected. | `build/resolve_wrappers.py:345` |  | See https://bandit.readthedocs.io/en/1.9.4/plugins/b112_try_except_continue.html. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-43b01e` | security | Try, Except, Continue detected. | `build/thumbs.py:201` |  | See https://bandit.readthedocs.io/en/1.9.4/plugins/b112_try_except_continue.html. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-79a121` | security | Try, Except, Continue detected. | `build/thumbs.py:279` |  | See https://bandit.readthedocs.io/en/1.9.4/plugins/b112_try_except_continue.html. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-c8f77d` | security | 4 requirement(s) without an exact version in requirements.txt | `requirements.txt` | A03:2025 · ASVS V15 | Pin each to the version tested (name==1.2.3), for example from `pip freeze`, so the audit and the deployment install the same thing. |
| `S-df2a6c` | security | No content-security-policy header | `https://internetarchivecanada.github.io/congressional-letters/` | A02:2025 · ASVS V3 | Set it; it limits the damage of any XSS that gets through; a <meta http-equiv> CSP works on static hosts. |
| `S-2e624e` | security | No x-content-type-options header | `https://internetarchivecanada.github.io/congressional-letters/` | A02:2025 · ASVS V3 | Set it; it stops browsers guessing content types. It has no <meta> form, so on a host that cannot set headers (GitHub Pages) it stays open; the explorer's owners decide whether that matters enough to change host. |
| `A-a23f29` | accessibility | ARIA role should be appropriate for the element | `/Explorer-Letters/ aria-allowed-role` |  | Ensure role attribute has an appropriate value for the element See https://dequeuniversity.com/rules/axe/4.14/aria-allowed-role?application=axeAPI |
| `A-f78bb9` | accessibility | All page content should be contained by landmarks | `/Explorer-Letters/ region` |  | Ensure all page content is contained by landmarks See https://dequeuniversity.com/rules/axe/4.14/region?application=axeAPI |
| `A-077c9d` | accessibility | Table header text should not be empty | `/Explorer-Congressional-Letters-119/ empty-table-header` |  | Ensure table headers have discernible text See https://dequeuniversity.com/rules/axe/4.14/empty-table-header?application=axeAPI |
| `A-d11ce6` | accessibility | Page should contain a level-one heading | `/Explorer-Congressional-Letters-119/ page-has-heading-one` |  | Ensure that the page, or at least one of its frames contains a level-one heading See https://dequeuniversity.com/rules/axe/4.14/page-has-heading-one?application=axeAPI |
| `A-a48dc0` | accessibility | Page should contain a level-one heading | `/Explorer-Congressional-Letters-110/ page-has-heading-one` |  | Ensure that the page, or at least one of its frames contains a level-one heading See https://dequeuniversity.com/rules/axe/4.14/page-has-heading-one?application=axeAPI |

<!-- explorer-checks:state {"passing": false, "date": "2026-11-12", "commit": "f6a926f123549749b5750b8623a0775913124f5e", "open": ["A-155de5", "A-251e8d", "A-2942b7", "A-3e6bb7", "A-4a24ac", "A-4c1f2b", "A-4cd8bb", "A-6500b2", "A-8bd0c2", "A-bac58d", "A-ccd44e", "A-cf4f4f", "A-dd0005", "A-f3579e", "S-11bd79", "S-3e1881", "S-47758c", "S-4e8008", "S-784cfb", "S-bb0739", "S-fbe8a3"], "titles": {"S-fbe8a3": "String rendered as markup or code (innerHTML)", "S-784cfb": "String rendered as markup or code (innerHTML)", "S-4e8008": "String rendered as markup or code (innerHTML)", "S-3e1881": "Use of weak SHA1 hash for security. Consider usedforsecurity=False", "S-bb0739": "Use of weak SHA1 hash for security. Consider usedforsecurity=False", "S-11bd79": "Use of weak SHA1 hash for security. Consider usedforsecurity=False", "A-251e8d": "Elements must meet minimum color contrast ratio thresholds", "A-6500b2": "Page scrolls sideways at 320 px wide", "A-ccd44e": "Select element must have an accessible name", "A-4a24ac": "Elements must meet minimum color contrast ratio thresholds", "A-3e6bb7": "Links must be distinguishable without relying on color", "A-f3579e": "All touch targets must be 24px large, or leave sufficient space", "A-bac58d": "Page scrolls sideways at 320 px wide", "A-2942b7": "Links must be distinguishable without relying on color", "A-cf4f4f": "Select element must have an accessible name", "A-4cd8bb": "Explorer views have no headings: the page title is a styled paragraph", "A-8bd0c2": "Home page search results are not announced", "A-4c1f2b": "Explorer filter count is not announced", "A-dd0005": "Changing a filter sends keyboard focus to the top of the page", "A-155de5": "Explorer search box and filter dropdowns have borders too faint to see", "S-47758c": "Member website links are not checked for scheme"}} -->
