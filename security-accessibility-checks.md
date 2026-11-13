# Security and accessibility checks

**Status: passing.** All three checks passed on 2026-11-12 at commit `d428dfdc05`. Nothing is open. Advisory items below are optional.

> The checkout had uncommitted changes when this ran, so it describes a working tree, not a commit.

| | |
|---|---|
| Explorer | https://github.com/Robin-IA/Congressional-Letters-Dev (pages served from its builds: Explorer-Letters and Explorer-Congressional-Letters-<N>) |
| Commit | `d428dfdc05` on `explorer-checks` |
| Date | 2026-11-12 |
| Pages checked | `Explorer-Letters/`, `Explorer-Letters/?q=veterans`, `Explorer-Congressional-Letters-119/`, `Explorer-Congressional-Letters-119/?view=recipients`, `Explorer-Congressional-Letters-119/?view=timeline`, `Explorer-Congressional-Letters-119/?view=search&q=opioid`, `Explorer-Congressional-Letters-119/?view=about`, `Explorer-Congressional-Letters-119/?member=W000817`, `Explorer-Congressional-Letters-110/` |
| Served from | http://127.0.0.1:8950/ |
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
| Code security | Pass | 0 | 0 | 32 |
| Accessibility (WCAG 2.2 AA) | Pass | 0 | 0 | 5 |

## Standards met

Checked 12 November 2026 at commit `d428dfdc05`, on the pages listed above:

- **WCAG 2.2 Level AA**: every Level A and AA success criterion, by automated tests and a manual review of each criterion (checklists under each check below).
- **WCAG 2.1 Level AA** and **WCAG 2.0 Level AA**, which WCAG 2.2 includes. 4.1.1 Parsing, dropped from 2.2 but still in 2.0 and 2.1, is covered by the code validity check (no HTML parse errors, no duplicate ids).
- These are the web content requirements of **Section 508** (US federal; WCAG 2.0 AA) and **EN 301 549** clause 9 (WCAG 2.1 AA).
- Security was checked against the OWASP Top 10:2025 risks and ASVS 5.0.0 chapters that apply to an explorer; each finding and checklist item names its category. That is not an ASVS verification at any level.

## What a pass means

Each check combines automated tools with a review of the code and pages against a written checklist. A pass means neither found anything open on the date and commit above. The standards are met as far as those checks can establish: it is a self-assessment, not third-party certification. Automated testing finds a minority of accessibility barriers. Testing with people who use assistive technology is still worth doing, and a change to the explorer needs a re-run.

## Code validity

No open items.

## Code security

No open items.

<details><summary>Manual checklist (10 pass, 0 fail, 10 n/a)</summary>

| Item | Result | Note |
|---|---|---|
| No secrets | pass | No secret findings from the scanner; the build scripts read only public endpoints and carry no keys or tokens. |
| Untrusted data is escaped | pass | Explorers and the home page build every node with createTextNode or setAttribute (no innerHTML of data). The federated/ mockup's three unescaped sinks are fixed (744c4b789); all ten sinks resolved above. |
| URLs from data are safe | pass | Letter and thumbnail links use a fixed https://web.archive.org prefix. Member site links are written only if they start http(s) (build_site.py, 744c4b789); the mockup's links pass safeHref(). |
| Harvested data is validated | pass | Parsed letter dates are checked: a two-digit-year date is read the way that is not after the file's first capture and not before the member first served (parse_urls.py, PR #60, fixing #58), and a date after its own capture with no reading that fits is dropped for the capture date. Member site URLs a |
| Third-party code is pinned | pass | No CDN scripts: the pages load only their own app.js / hub.js. |
| No mixed content | pass | Everything the pages load is same-origin over https; outbound links to web.archive.org are https. |
| Dependencies are pinned and maintained | pass | requirements.txt pins exact versions (744c4b789). Python 3.15 is current. |
| Dependencies have no known vulnerabilities | pass | pip-audit finds none in the pinned versions (pillow 13.0.0, pypdf 7.0.1, pypdfium2 5.15.2, internetarchive 5.12.1). The versions previously installed carried 54; the working venv on the Mac still has them until it is reinstalled from requirements.txt. |
| Third parties a visitor's browser contacts | pass | None on load. web.archive.org is contacted only when a reader opens a letter, which is the point of the site. |
| What Pages publishes | pass | The explorer repos publish only built output. Congressional-Letters-Dev is public and serves its whole tree on Pages (scripts, data/, docs): all meant to be public; no notes or credentials among them. |
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

<details><summary>Cleared on review (23)</summary>

| Id | Item | Where | Why cleared |
|---|---|---|---|
| `S-9c80d3` | String rendered as markup or code (innerHTML) | `app.js:45` | el() (app.js:40-53) writes innerHTML only for an attribute named 'html'. No caller passes one: grep finds no 'html:' anywhere in app.js, which is now the template every explorer is stamped from. Every value reaches the DOM through setAttribute or createTextNode. |
| `S-1d9bee` | String rendered as markup or code (innerHTML) | `federated/index.html:255` | bars(): every interpolated value is a computed number, fmt(d.value), or esc(d.label / d.sub / d.aria / opts.aria); esc() (federated/index.html:222) escapes & < > " ' and every attribute is double-quoted. |
| `S-fffc65` | String rendered as markup or code (innerHTML) | `federated/index.html:262` | tip.innerHTML = d.tip. Every tip is built from ord(n), fmt(...), long(date) (Date.toLocaleDateString output) and esc(c.detail) / esc(m.name). |
| `S-fbe8a3` | String rendered as markup or code (innerHTML) | `federated/index.html:302` | Fixed in 744c4b789. drawCongresses now writes href="${esc(safeHref(c.href))}" (safeHref admits only relative paths or http(s)), class="congress ${esc(c.status)}"; the rest is esc(), fmt(), long() or literals. esc() (federated/index.html:222) escapes & < > " ' and every attribute is double-quoted. |
| `S-3a7181` | String rendered as markup or code (innerHTML) | `federated/index.html:358` | #summary: fmt(total), groups.size (a number) and esc(q). The ?q= value from the URL is escaped here, encodeURIComponent'd in hrefs and esc'd in the chart aria-label: no reflected route. |
| `S-784cfb` | String rendered as markup or code (innerHTML) | `federated/index.html:368` | Fixed in 744c4b789. #groups: href="${esc(safeHref(c.href))}?view=search&q=${encodeURIComponent(q)}", Number(r[2]) for the year, esc(m.state), esc(m.name), esc(rec), esc(r[4]), and encodeURIComponent(id) in the member link. |
| `S-e34383` | String rendered as markup or code (innerHTML) | `federated/index.html:393` | Fixed in 744c4b789 (was S-4e8008). #careerHead: href="../119th/?member=${encodeURIComponent(m.id)}" and ${esc(m.name)}. |
| `S-6273f5` | String rendered as markup or code (innerHTML) | `federated/index.html:416` | <option value="${esc(m.name)}">: esc() escapes both quotes, and the attribute is double-quoted. |
| `S-7d1cf4` | String rendered as markup or code (insertAdjacentHTML) | `federated/index.html:406` | insertAdjacentHTML of fmt(DATA.total), a number; the rest is a literal. |
| `S-7c973f` | String rendered as markup or code (innerHTML) | `index.html:152` | Dev repo root page. Only fmt(index.letters), fmt(index.members_with_letters) (fmt = Number(n).toLocaleString) and index.span, an [int, int] that build_site.py writes from Counter keys of years. No string from data reaches it. |
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

No open items.

<details><summary>Manual checklist (20 pass, 0 fail, 2 n/a)</summary>

| Item | Result | Note |
|---|---|---|
| 1.1.1 Non-text content | pass | Letter images have alt text naming member, recipient and year; the home page chart is a list of 14 links each named with the Congress, dates and count. |
| 1.3.1 Info and relationships | pass | Home page: h1 then h2s. Explorer: each view's title is now an h1 (ed2bffbbb); the member view's name is an h2 under the page's landmarks. |
| 1.3.2 Meaningful sequence | pass | DOM order matches reading order on the home page (text column, then letters) and in the explorers. |
| 1.4.1 Use of color | pass | Selected explorer tab has an underline and aria-current; links in running text are now underlined; the chart uses one colour with labels. |
| 1.4.11 Non-text contrast | pass | Explorer filter borders now #8a8a90, 3.4:1 (ed2bffbbb). Home page search border (#2c5aa0, 2px) and focus rings pass. |
| 1.4.4 Resize text / 1.4.12 Text spacing | pass | At 640 px (200% of 1280) neither page scrolls sideways or clips, and at 320 px every checked view fits (measured in headless Chromium). Re-checked on the build at d428dfdc0. |
| 2.4.4 Link purpose | pass | Member cards are named by member, chart links by Congress and count, site links by host. |
| 2.4.6 Headings and labels | pass | Views have h1 titles, and the three dropdowns are named Chamber, Party and Sort by. |
| 3.1.1 Language of page | pass | lang="en" on the home page and every explorer. |
| 2.1.1 Keyboard | pass | Every control is a native link, button, input or select; the chart bars are links. |
| 2.1.2 No keyboard trap | pass | No modals or embeds; tabbing moves through and out of every widget. |
| 2.4.1 Bypass blocks | pass | No skip link, but header, nav, search, main and footer landmarks on both page types. |
| 2.4.3 Focus order | pass | Order follows reading order, and changing a filter now returns focus to that control (verified: Chamber to Senate, focus stays on the Chamber dropdown). Re-checked on the build at d428dfdc0. |
| 2.4.7 Focus visible | pass | Home page: 3px outline on every link and button, ring shadow on the search box. Explorer: the browser focus ring on every control, checked by tabbing. |
| 2.4.11 Focus not obscured | pass | A card focused further down the explorer lands at 401 px, clear of the sticky tab bar (bottom at 47 px). |
| 2.5.8 Target size | pass | Topic links are now at least 24 px tall (ed2bffbbb); axe finds no target-size issue on any checked page. |
| 2.2.2 Pause, stop, hide | n/a | Nothing moves or auto-updates. |
| 3.2.2 On input | pass | Changing a select filters in place (history.replaceState); it does not navigate away. |
| 3.3.2 Labels or instructions | pass | Search boxes have an accessible name and an adjacent Search button (G167); the dropdowns are named, and each shows its current choice (Both chambers, Any party, Most letters) as its visible text. |
| 4.1.2 Name, role, value | pass | View tabs are buttons carrying aria-current on the selected one; the letters/list toggle uses aria-pressed. |
| 4.1.3 Status messages | pass | Home page search status and the explorer's members and recipients counts are role="status" (ed2bffbbb); verified they update in place. Re-checked on the build at d428dfdc0. |
| 1.2.2 Captions | n/a | No audio or video. |

</details>

<details><summary>Cleared on review (1)</summary>

| Id | Item | Where | Why cleared |
|---|---|---|---|
| `A-251e8d` | Elements must meet minimum color contrast ratio thresholds | `/Explorer-Letters/ color-contrast` | Measured by hand (unchanged since ed2bffbbb). The hero text sits on a gradient (#f6e9ea to #faf7f2), not the image: kicker 8.5:1, h1 11.3:1, lede 13:1, note 5.1:1. The photo credit (figcaption) is white 11.5px on rgba(20,20,24,.72) (fixed in ed2bffbbb, was .55): over the photograph's lightest pixels |

</details>

## Advisory (49)

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
| `S-515964` | security | Try, Except, Continue detected. | `build/build_congress.py:140` |  | See https://bandit.readthedocs.io/en/1.9.4/plugins/b112_try_except_continue.html. If the flagged input can never come from outside (say why in the review), clear it. |
| `S-989200` | security | subprocess call - check for execution of untrusted input. | `build/build_congress.py:273` | A05:2025 · ASVS V1 | See https://bandit.readthedocs.io/en/1.9.4/plugins/b603_subprocess_without_shell_equals_true.html. If the flagged input can never come from outside (say why in the review), clear it. |
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
| `S-df2a6c` | security | No content-security-policy header | `https://internetarchivecanada.github.io/congressional-letters/` | A02:2025 · ASVS V3 | Set it; it limits the damage of any XSS that gets through; a <meta http-equiv> CSP works on static hosts. |
| `S-2e624e` | security | No x-content-type-options header | `https://internetarchivecanada.github.io/congressional-letters/` | A02:2025 · ASVS V3 | Set it; it stops browsers guessing content types. It has no <meta> form, so on a host that cannot set headers (GitHub Pages) it stays open; the explorer's owners decide whether that matters enough to change host. |
| `A-a23f29` | accessibility | ARIA role should be appropriate for the element | `/Explorer-Letters/ aria-allowed-role` |  | Ensure role attribute has an appropriate value for the element See https://dequeuniversity.com/rules/axe/4.14/aria-allowed-role?application=axeAPI |
| `A-f78bb9` | accessibility | All page content should be contained by landmarks | `/Explorer-Letters/ region` |  | Ensure all page content is contained by landmarks See https://dequeuniversity.com/rules/axe/4.14/region?application=axeAPI |
| `A-077c9d` | accessibility | Table header text should not be empty | `/Explorer-Congressional-Letters-119/ empty-table-header` |  | Ensure table headers have discernible text See https://dequeuniversity.com/rules/axe/4.14/empty-table-header?application=axeAPI |
| `A-5406ea` | accessibility | Heading levels should only increase by one | `/Explorer-Congressional-Letters-119/ heading-order` |  | Ensure the order of headings is semantically correct See https://dequeuniversity.com/rules/axe/4.14/heading-order?application=axeAPI |
| `A-d11ce6` | accessibility | Page should contain a level-one heading | `/Explorer-Congressional-Letters-119/ page-has-heading-one` |  | Ensure that the page, or at least one of its frames contains a level-one heading See https://dequeuniversity.com/rules/axe/4.14/page-has-heading-one?application=axeAPI |

<!-- explorer-checks:state {"passing": true, "date": "2026-11-12", "commit": "d428dfdc054454f4e10afd51c44bc4963de8e53e", "open": [], "titles": {}} -->
