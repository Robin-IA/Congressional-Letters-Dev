// Letters from Congress — letters published on members' own websites.
//
// One static page over a small index plus one file per member, fetched when
// that member is opened. Nothing is kept outside the URL, so every view is a
// link and the back button works:
//
//   ?view=members                 the members, ranked            (default)
//   ?member=<bioguide>            one member, their letters
//   ?member=<id>&as=list          the same, as a table
//   ?view=recipients              who Congress writes to
//   ?to=<name>                    one recipient
//   ?view=timeline                letters by year
//   ?year=<yyyy>                  one year
//   ?view=search&q=<text>         search
//   ?view=about                   method and caveats

// index.json sits beside the page in the repository; the per-member files and
// the thumbnails come from wherever it says they do. For a local checkout that
// is ./payload/, and for the published page an archive.org item, which serves
// Access-Control-Allow-Origin: * so the browser can read it directly. Same
// arrangement as internetarchivecanada/etd-viewer.
const INDEX_URL = './index.json';
let DATA_BASE = './payload/member/';
const WALL = 48;       // letters shown on a member page before "show more"
const CARDS = 60;      // member cards before "show more"
const ROWS = 150;      // table rows before "show more"

let INDEX, MEMBERS;
let byId = new Map();
const memberCache = new Map();
let SEARCH = null;            // the whole-corpus index, fetched on first search
let searchLoading = null;
let shown = 0;

// ------------------------------------------------------------------ helpers

const $ = (sel, root = document) => root.querySelector(sel);
const num = n => (n ?? 0).toLocaleString('en-US');

function el(tag, attrs = {}, ...kids) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === 'class') node.className = v;
    else if (k === 'html') node.innerHTML = v;
    else if (k.startsWith('on')) node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v);
  }
  for (const kid of kids.flat()) {
    if (kid === null || kid === undefined || kid === false) continue;
    node.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  }
  return node;
}

// Letters are arrays; the column order comes from index.json so the page and
// the build cannot disagree about it.
const F = {};
const get = (row, field) => row[F[field]];

// The letter as the Wayback Machine serves it. `id_` asks for the original
// bytes rather than a rewritten page, which for a PDF is what you want.
// `key` is the letter's identity, not its address: it drops a cache-busting
// prefix the archive needs (#107), so `url` carries the observed address
// when it differs. Older payloads have no `url` column; they fall back.
// A letter that is a web page (it carries an excerpt, #1330) opens in the
// ordinary replay, so the archived page shows with its images and the Wayback
// Machine's own banner; `id_` would hand over the bare HTML.
const waybackUrl = row =>
  `https://web.archive.org/web/${get(row, 'timestamp')}${get(row, 'excerpt') ? '' : 'id_'}/${get(row, 'url') || get(row, 'key')}`;

const thumbUrl = row => {
  const digest = get(row, 'digest');
  // WebP: same quality setting as the JPEGs it replaced and 21% smaller,
  // which is the difference between fitting two thirds of the corpus inside
  // the 1 GB Pages ceiling and fitting all of it.
  return digest ? `${INDEX.thumb_base || './payload/thumbs/'}${digest}.webp` : null;
};

// A date the slug stated, versus one inferred from when Wayback saw the file.
// The difference matters enough to show: "by 12 Mar 2016" is not a letter date.
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function when(row, long = false) {
  const iso = get(row, 'date');
  const precision = get(row, 'precision');
  if (!iso) return '—';
  const [y, m, d] = iso.split('-');
  const month = MONTHS[Number(m) - 1] || '';
  // 'letterhead': the date the letter prints on itself (#186) -- a day, and
  // the best kind; without this it read as a capture, "in the archive by".
  if (precision === 'day' || precision === 'letterhead') {
    return long ? `${Number(d)} ${month} ${y}` : `${month} ${y}`;
  }
  if (precision === 'month') return `${month} ${y}`;
  // 'year': a date the letter does not print but its content fixes to a year,
  // marked approximate (an undated funding request names its fiscal year).
  if (precision === 'year') return `about ${y}`;
  return long ? `in the archive by ${Number(d)} ${month} ${y}` : `by ${month} ${y}`;
}

// Members carry a two-letter state code, so a filter matching only that found
// nothing for "california" — the obvious thing to type. Matching both.
const STATE_NAMES = {
  AL: 'Alabama', AK: 'Alaska', AZ: 'Arizona', AR: 'Arkansas', CA: 'California',
  CO: 'Colorado', CT: 'Connecticut', DE: 'Delaware', FL: 'Florida', GA: 'Georgia',
  HI: 'Hawaii', ID: 'Idaho', IL: 'Illinois', IN: 'Indiana', IA: 'Iowa',
  KS: 'Kansas', KY: 'Kentucky', LA: 'Louisiana', ME: 'Maine', MD: 'Maryland',
  MA: 'Massachusetts', MI: 'Michigan', MN: 'Minnesota', MS: 'Mississippi',
  MO: 'Missouri', MT: 'Montana', NE: 'Nebraska', NV: 'Nevada',
  NH: 'New Hampshire', NJ: 'New Jersey', NM: 'New Mexico', NY: 'New York',
  NC: 'North Carolina', ND: 'North Dakota', OH: 'Ohio', OK: 'Oklahoma',
  OR: 'Oregon', PA: 'Pennsylvania', RI: 'Rhode Island', SC: 'South Carolina',
  SD: 'South Dakota', TN: 'Tennessee', TX: 'Texas', UT: 'Utah', VT: 'Vermont',
  VA: 'Virginia', WA: 'Washington', WV: 'West Virginia', WI: 'Wisconsin',
  WY: 'Wyoming', DC: 'District of Columbia', PR: 'Puerto Rico', GU: 'Guam',
  VI: 'Virgin Islands', AS: 'American Samoa', MP: 'Northern Mariana Islands',
};

const stateName = code => STATE_NAMES[(code || '').toUpperCase()] || code || '';

function chamber(m) { return m.chamber === 'sen' ? 'Senate' : 'House'; }

// A member who left during the Congress carries `left`, the date their last
// term ended; everyone else is still sitting.
const service = m => `${m.since}–${m.left ? m.left.slice(0, 4) : 'present'}`;

// A departed member's site is usually gone or someone else's by now, so link
// the Wayback Machine's copy as of the day they left rather than the address.
// Better still, the last capture inside this Congress, from the build's
// Wayback lookup (#79): the site as it was while the member served in it.
const siteHref = m => (m.wayback && m.wayback.last) || (m.left
  ? `https://web.archive.org/web/${m.left.replaceAll('-', '')}/${m.site}`
  : m.site);
// The address to show: the whole of it, since an early member's host alone
// is just "www.house.gov".
// A roster can list two sites ("a | b"). Name the one the Wayback count is
// of, so "archived X on N days" is about X (#112); failing that, the first.
const siteName = m => {
  const site = (m.wayback && m.wayback.site) || (m.site || '').split('|')[0];
  return site.trim()
    ? site.trim().replace(/^https?:\/\/(www\.)?/, '').replace(/\/$/, '')
    : m.host;
};

// A member with no letters still had a website. Say what the Wayback Machine
// holds of it during this Congress (build_congress.py's wayback_record), and
// whether a harvest searched it, so an empty page reads as "looked, found
// none" or "not searched yet", never as a blank (#79). `first` and `last` are
// capture URLs, checked at build time to be on web.archive.org; `searched` is
// true only when a harvest queried the site's address.
const captureDay = url => {
  const d = (url.match(/\/web\/(\d{8})/) || [])[1];
  return d ? `${MONTHS[+d.slice(4, 6) - 1]} ${+d.slice(6, 8)}, ${d.slice(0, 4)}` : 'capture';
};
function archivedSite(m) {
  const wb = m.wayback;
  const name = siteName(m);
  const out = (url, text) => el('a', { href: url, target: '_blank', rel: 'noopener' }, text);
  if (!wb) {
    return m.site
      ? el('p', {}, 'Their website: ',
        el('a', { href: siteHref(m), target: '_blank', rel: 'noopener' }, name), '.')
      : el('p', {}, 'No website is recorded for this member in this Congress.');
  }
  if (!wb.days) {
    return el('p', {}, `The Wayback Machine holds no capture of ${name} from this Congress.`);
  }
  const captures = [];
  if (wb.first) captures.push(out(wb.first, `first capture, ${captureDay(wb.first)}`));
  if (wb.last && wb.last !== wb.first) {
    captures.push(' · ', out(wb.last, `last capture, ${captureDay(wb.last)}`));
  }
  return el('p', {},
    `The Wayback Machine archived ${name} on ${num(wb.days)} `
    + `${wb.days === 1 ? 'day' : 'days'} during this Congress. `
    + (wb.searched
      ? 'We searched everything it holds from the site for files named as letters. '
      : 'Its letters have not been searched yet: no harvest has reached this address. ')
    + 'See the archived site: ',
    ...captures, '.');
}

function partyClass(party) {
  const p = (party || '').toLowerCase();
  if (p.startsWith('democrat')) return 'b-dem';
  if (p.startsWith('republican')) return 'b-rep';
  return 'b-ind';
}

function memberBadges(m) {
  return [
    el('span', { class: `badge ${m.chamber === 'sen' ? 'b-sen' : 'b-hou'}` },
      chamber(m)),
    el('span', { class: `badge ${partyClass(m.party)}` },
      (m.party || '').slice(0, 11)),
    el('span', { class: 'state', title: stateName(m.state) },
      m.district != null && m.district !== '' ? `${m.state}-${m.district}` : m.state),
    m.left
      ? el('span', { class: 'chip', title: `Term ended ${m.left}` }, `Left office ${m.left.slice(0, 4)}`)
      : null,
  ];
}

// -------------------------------------------------------------------- state

function params() { return new URLSearchParams(location.search); }

function go(next, replace = false) {
  const url = next.toString() ? `?${next}` : location.pathname;
  history[replace ? 'replaceState' : 'pushState']({}, '', url);
  // Rebuilding the view would otherwise drop focus to the top of the page.
  const key = document.activeElement?.dataset?.key;
  Promise.resolve(render()).then(() => {
    if (key) document.querySelector(`[data-key="${key}"]`)?.focus();
  });
}

function link(paramsObj, cls, ...kids) {
  const next = new URLSearchParams();
  for (const [k, v] of Object.entries(paramsObj)) if (v != null) next.set(k, v);
  return el('a', {
    class: cls,
    href: `?${next}`,
    onclick: e => {
      if (e.metaKey || e.ctrlKey || e.shiftKey) return;
      e.preventDefault();
      shown = 0;
      go(next);
    },
  }, ...kids);
}

// The corpus-wide search index, fetched once. Before this existed, search
// could only see members the visitor had already opened — so from a cold load
// it found nothing, which is not a search.
// Every build rewrites the per-member files and search.json, and they are
// served from an archive.org item behind a CDN. Fetched by bare name the
// browser kept being handed the previous build's copy — Grassley's first four
// letters had thumbnails in the file the item was serving and none in the file
// the page received, so the wall showed "preview coming soon" over pictures
// that existed. The stamp changes when the files do, which busts the cache on
// a rebuild and lets everything be cached hard in between.
const v = () => `?v=${INDEX.stamp || INDEX.built || ''}`;

async function loadSearch() {
  if (SEARCH) return SEARCH;
  if (!searchLoading) {
    searchLoading = fetch((INDEX.search_url || 'payload/search.json') + v())
      .then(r => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then(d => { SEARCH = d; return d; })
      .catch(err => { SEARCH = { failed: String(err.message || err) }; return SEARCH; });
  }
  return searchLoading;
}

async function lettersOf(bioguide) {
  if (memberCache.has(bioguide)) return memberCache.get(bioguide);
  const response = await fetch(`${DATA_BASE}${bioguide}.json${v()}`);
  const rows = response.ok ? await response.json() : [];
  memberCache.set(bioguide, rows);
  return rows;
}

function tally(rows, field) {
  const counts = new Map();
  for (const row of rows) {
    const v = get(row, field);
    if (v) counts.set(v, (counts.get(v) || 0) + 1);
  }
  return [...counts.entries()].sort((a, b) => b[1] - a[1]);
}

function yearsOf(rows) {
  const counts = new Map();
  for (const row of rows) {
    const iso = get(row, 'date');
    if (!iso) continue;
    const y = Number(iso.slice(0, 4));
    counts.set(y, (counts.get(y) || 0) + 1);
  }
  return counts;
}

// ---------------------------------------------------------------- fragments

function sparkline(counts, from, to) {
  const span = to - from + 1;
  if (span <= 0 || !counts.size) return el('span');
  const max = Math.max(...counts.values());
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('class', 'spark');
  svg.setAttribute('viewBox', `0 0 ${span * 3} 22`);
  svg.setAttribute('preserveAspectRatio', 'none');
  svg.setAttribute('aria-hidden', 'true');
  for (const [year, n] of counts) {
    const h = Math.max(1.5, (n / max) * 22);
    const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    rect.setAttribute('x', (year - from) * 3);
    rect.setAttribute('y', 22 - h);
    rect.setAttribute('width', 2.2);
    rect.setAttribute('height', h);
    svg.append(rect);
  }
  return svg;
}


// The letter itself, shown as its first page. Measured on 50 at random, one
// request at a time: 65% of these PDFs do carry a text layer, which is the
// opposite of what an earlier 21-file sample claimed. The page is still the
// primary thing to show — it is the signed original — but "they are mostly
// scans" was not true and is not a reason for anything.
function topicTags(row) {
  const raw = get(row, 'topics');
  if (!raw) return null;
  return raw.split(',').filter(Boolean).map(t =>
    link({ view: 'search', q: t }, 'topic', t));
}

// Notes joining this letter to another by hand (vocabulary/letter-related.csv):
// "Supports" on a supporting document, "Supporting document" on the letter it
// supports. Each names the other letter and opens its PDF.
const relatedNotes = row => (INDEX.related || {})[get(row, 'digest')] || [];

// A letter dated before the posting member held the address it was found at:
// another member's, or an older one, posted later (#239, #1284). It keeps its
// own date and is placed by the file's first capture.
const postedLater = row => (INDEX.posted_later || {})[get(row, 'digest')] || '';

function relatedLine(row) {
  const notes = relatedNotes(row);
  const later = postedLater(row);
  if (!notes.length && !later) return null;
  return el('span', { class: 'related' },
    ...(later ? [`Posted later: first captured on this site ${later}, after the letter's date`] : []),
    ...notes.flatMap(([label, title, url], i) => [
      (i || later) ? ' · ' : '', `${label}: `,
      el('a', { href: url, target: '_blank', rel: 'noopener' }, title),
    ]));
}

function shot(row) {
  const src = thumbUrl(row);
  const subject = get(row, 'subject');
  const recipient = get(row, 'recipient');
  const caption = subject || recipient || get(row, 'key').split('/').pop();
  return el('a', {
    class: 'shot',
    href: waybackUrl(row),
    target: '_blank',
    rel: 'noopener',
    title: get(row, 'key'),
  },
    el('span', { class: get(row, 'excerpt') ? 'frame text' : 'frame' },
      // A letter that is not a PDF has no picture: the card shows how it opens,
      // from the text read off the archived page (#1330).
      get(row, 'excerpt')
        ? el('span', { class: 'excerpt' },
          el('span', { class: 'kind' }, get(row, 'kind') === 'pdf' ? 'PDF, text read from it'
            : /\.docx?$/i.test(get(row, 'key')) ? 'Word document' : 'Archived web page'),
          get(row, 'excerpt'))
        :
      // Asked for whether or not it has been rendered yet, and replaced by the
      // placeholder if it is not there. The alternative was for the build to
      // record which pictures exist, which tied every member file to the
      // renderer's progress and meant re-uploading all 514 of them to the item
      // after every build — at the five files a minute the item accepts, a
      // loop that could not keep up with the renderer feeding it.
      //
      // Images are lazy, so a letter nobody scrolls to never asks, and the
      // misses shrink as coverage grows.
      src
        ? el('img', {
          src, loading: 'lazy', alt: '', width: 170, height: 220,
          onerror: event => event.target.replaceWith(
            el('span', { class: 'none' }, 'Preview coming soon')),
        })
        // Every letter here is a document now, so the old "Press release"
        // fallback labelled nothing that exists — the handful of non-pdf rows
        // are letters whose web server gave them the wrong content type.
        : el('span', { class: 'none' }, 'Preview coming soon')),
    el('span', { class: 'cap' }, caption),
    (() => { const t = topicTags(row); return t && t.length ? el('span', { class: 'topics' }, t) : null; })(),
    el('span', { class: 'when' }, when(row),
      recipient && subject ? ` · ${recipient}` : ''),
  );
}

function wall(rows) {
  const limit = shown || WALL;
  const box = el('div', { class: 'wall' },
    // A card is itself a link, and a link cannot hold another, so a related
    // note sits just under its card rather than inside it.
    ...rows.slice(0, limit).map(row => {
      const note = relatedLine(row);
      return note ? el('div', { class: 'shotwrap' }, shot(row), note) : shot(row);
    }));
  const out = el('div', {}, box);
  if (rows.length > limit) {
    out.append(el('button', {
      class: 'more',
      onclick: () => { shown = limit + WALL; render(); },
    }, `Show more — ${num(rows.length - limit)} more letters`));
  }
  return out;
}

function table(rows, opts = {}) {
  const limit = shown || ROWS;
  const body = el('tbody');
  for (const row of rows.slice(0, limit)) {
    const member = opts.member || byId.get(opts.lookup?.(row));
    body.append(el('tr', {},
      el('td', { class: 'wh' }, when(row)),
      opts.showMember
        ? el('td', { class: 'who' },
          member ? link({ member: member.id }, null, member.name) : '—')
        : null,
      el('td', { class: 'who' },
        get(row, 'recipient')
          ? link({ to: get(row, 'recipient') }, null, get(row, 'recipient'))
          : el('span', { class: 'faint' }, 'not named')),
      el('td', { class: 'sub2' },
        get(row, 'subject') || el('span', { class: 'faint' }, '—'),
        (() => { const t = topicTags(row); return t && t.length ? el('span', { class: 'topics' }, t) : null; })(),
        relatedLine(row)),
      el('td', {},
        el('a', {
          href: waybackUrl(row), target: '_blank', rel: 'noopener',
          class: 'small',
        }, get(row, 'kind') === 'pdf' ? 'PDF' : 'page')),
    ));
  }
  const out = el('div', {},
    el('table', { class: 'letters' },
      el('thead', {}, el('tr', {},
        el('th', {}, 'Date'),
        opts.showMember ? el('th', {}, 'Member') : null,
        el('th', {}, 'Sent to'),
        el('th', {}, 'Scope of letter'),
        el('th', {}, ''))),
      body));
  if (rows.length > limit) {
    out.append(el('button', {
      class: 'more',
      onclick: () => { shown = limit + ROWS; render(); },
    }, `Show more — ${num(rows.length - limit)} more letters`));
  }
  return out;
}

function rankList(entries, makeLink, limit = 14) {
  const max = entries.length ? entries[0][1] : 1;
  const list = el('ul', { class: 'rank' });
  for (const [name, n] of entries.slice(0, limit)) {
    list.append(el('li', {},
      el('span', { class: 'nm' }, makeLink(name)),
      el('span', { class: 'track' },
        el('i', { style: `width:${Math.max(4, (n / max) * 100)}%` })),
      el('span', { class: 'n tab' }, num(n)),
    ));
  }
  return list;
}

// -------------------------------------------------------------------- views

function viewMembers() {
  const p = params();
  const q = (p.get('q') || '').toLowerCase();
  const ch = p.get('chamber') || '';
  const party = p.get('party') || '';
  const sort = p.get('sort') || 'letters';

  let list = MEMBERS.filter(m => {
    if (q) {
      // The state CODE has to match exactly. As a substring, "ca" also finds
      // Cassidy and McCarthy — 108 members for a query meaning California's
      // 54. The state NAME matches loosely, which is what makes the written
      // abbreviations work without listing them: Calif, Tenn, Penn, Mass and
      // Wash are all prefixes of the state they stand for.
      const code = (m.state || '').toLowerCase();
      const hit = m.name.toLowerCase().includes(q)
        || code === q
        || stateName(m.state).toLowerCase().includes(q);
      if (!hit) return false;
    }
    if (ch && m.chamber !== ch) return false;
    if (party && !(m.party || '').startsWith(party)) return false;
    return true;
  });
  if (sort === 'name') list = [...list].sort((a, b) => a.last.localeCompare(b.last));
  else if (sort === 'state') list = [...list].sort((a, b) =>
    (a.state || '').localeCompare(b.state || '') || a.last.localeCompare(b.last));
  else list = [...list].sort((a, b) => b.letters - a.letters);

  const setParam = (key, value) => {
    const next = params();
    if (value) next.set(key, value); else next.delete(key);
    go(next, true);
  };

  const controls = el('div', { class: 'controls' },
    el('input', {
      type: 'search', value: p.get('q') || '',
      placeholder: 'Name or state — California, Calif, CA, or a member’s name',
      oninput: e => {
        const next = params();
        if (e.target.value) next.set('q', e.target.value); else next.delete('q');
        history.replaceState({}, '', `?${next}`);
        render();
        const box = $('.controls input[type=search]');
        if (box) { box.focus(); box.setSelectionRange(box.value.length, box.value.length); }
      },
    }),
    el('select', { 'aria-label': 'Chamber', 'data-key': 'chamber', onchange: e => setParam('chamber', e.target.value) },
      el('option', { value: '', selected: !ch }, 'Both chambers'),
      el('option', { value: 'sen', selected: ch === 'sen' }, 'Senate'),
      el('option', { value: 'rep', selected: ch === 'rep' }, 'House')),
    el('select', { 'aria-label': 'Party', 'data-key': 'party', onchange: e => setParam('party', e.target.value) },
      el('option', { value: '', selected: !party }, 'Any party'),
      el('option', { value: 'Democrat', selected: party === 'Democrat' }, 'Democrat'),
      el('option', { value: 'Republican', selected: party === 'Republican' }, 'Republican'),
      el('option', { value: 'Independent', selected: party === 'Independent' }, 'Independent')),
    el('select', { 'aria-label': 'Sort by', 'data-key': 'sort', onchange: e => setParam('sort', e.target.value) },
      el('option', { value: 'letters', selected: sort === 'letters' }, 'Most letters'),
      el('option', { value: 'name', selected: sort === 'name' }, 'By surname'),
      el('option', { value: 'state', selected: sort === 'state' }, 'By state')),
    el('span', { class: 'count tab', role: 'status' },
      `${num(list.length)} of ${num(MEMBERS.length)} members`),
  );

  // Say what the order means. The count is how many letters we ARCHIVED, not
  // how many a member wrote, and an unlabelled ranking reads as the latter.
  const none = MEMBERS.length - INDEX.members_with_letters;
  const orderNote = {
    letters: 'Ordered by how many letters have been archived.'
      + (none > 0 ? ` The ${num(none)} members with no letters found come last; `
        + 'each one’s page links to their website as archived during this Congress.' : ''),
    name: 'In alphabetical order by surname.',
    state: 'Grouped by state.',
  }[sort];

  const limit = shown || CARDS;
  const grid = el('div', { class: 'grid' });
  const [from, to] = INDEX.span || [2000, 2026];
  for (const m of list.slice(0, limit)) {
    grid.append(link({ member: m.id }, 'card',
      el('span', { class: 'top' },
        el('span', { class: 'nm' }, m.name),
        el('span', { class: 'ct tab' }, num(m.letters))),
      el('span', { class: 'meta' }, memberBadges(m),
        m.since
          ? el('span', { class: 'since', title: 'Dates of service' },
            service(m))
          : null),
      m.top.length
        ? el('span', { class: 'with' }, `wrote to ${m.top.slice(0, 2).join(', ')}`)
        : el('span', { class: 'with faint' }, m.letters
          ? 'no recipients named in filenames'
          : m.wayback && m.wayback.days
            ? `no letters found · site archived on ${num(m.wayback.days)} `
              + `${m.wayback.days === 1 ? 'day' : 'days'}`
            : 'no letters found'),
    ));
  }

  const out = el('div', {},
    el('h1', { class: 'hero' }, '119th Congress (2025-26)'),
    el('p', { class: 'dates' }, 'January 3, 2025 – January 3, 2027'),
    el('p', { class: 'sub' },
      el('b', {}, num(INDEX.letters)), ' letters published on ',
      el('b', {}, num(INDEX.members_with_letters)),
      ' members of Congress, archived from their own websites by the Wayback Machine, ',
      `${(INDEX.span || [])[0]} to ${(INDEX.span || [])[1]}. `,
      'Select a Congressperson to see who they wrote to and about what.'),
    el('p', { class: 'note' },
      'This is what the Wayback Machine has archived — not every letter '
      + 'Congress has written.'),
    controls,
    orderNote ? el('p', { class: 'small muted', style: 'margin:-.6rem 0 1.2rem' },
      orderNote) : null,
    grid);

  if (list.length > limit) {
    out.append(el('button', {
      class: 'more',
      onclick: () => { shown = limit + CARDS; render(); },
    }, `Show more — ${num(list.length - limit)} more members`));
  }
  if (!list.length) out.append(el('div', { class: 'empty' }, 'No members match those filters.'));
  return out;
}

async function viewMember(id) {
  const m = byId.get(id);
  if (!m) return el('div', { class: 'empty' }, 'No such member.');
  // No member file is written for a member with no letters; don't ask for it.
  const all = (m.letters || m.received || m.posted) ? await lettersOf(id) : [];
  // Three lists (Robin, 17 November 2026, #175, #352): letters this member's
  // office wrote; letters written to them (posted on their site, or found on
  // another site and addressed to them, "As recipient"); and documents with no
  // member at either end that the office posted.
  const dirOf = r => get(r, 'direction') || '';
  const groups = {
    written: all.filter(r => !dirOf(r)),
    received: all.filter(r => ['to', 'received'].includes(dirOf(r))),
    posted: all.filter(r => dirOf(r) === 'neither'),
  };
  const LABELS = { written: 'Letters written', received: 'Letters received', posted: 'Other documents posted' };
  const pdir = params().get('dir');
  const dir = groups[pdir]?.length ? pdir
    : ['written', 'received', 'posted'].find(k => groups[k].length) || 'written';
  const rows = groups[dir];
  if (!all.length) {
    return el('div', {},
      link({ view: 'members' }, 'back', '← All members'),
      el('div', { class: 'panel' },
        el('div', { class: 'dhead' }, el('h2', {}, m.name),
          el('span', { class: 'meta' }, memberBadges(m)))),
      el('div', { class: 'empty' },
        el('p', {}, 'No letters were found on this member’s website from this Congress.'),
        archivedSite(m)));
  }

  const p = params();
  const asList = p.get('as') === 'list';
  const recipients = tally(groups.written, 'recipient');
  const counts = yearsOf(groups.written);
  const years = [...counts.keys()].sort();
  const dated = rows.filter(r => ['day', 'letterhead', 'month']
    .includes(get(r, 'precision'))).length;

  const switchTo = next => {
    const q = params();
    if (next === 'list') q.set('as', 'list'); else q.delete('as');
    shown = 0;
    go(q);
  };

  return el('div', {},
    link({ view: 'members' }, 'back', '← All members'),
    el('div', { class: 'panel' },
      el('div', { class: 'dhead' },
        el('h2', {}, m.name),
        el('span', { class: 'meta' }, memberBadges(m)),
        el('a', {
          href: siteHref(m), target: '_blank', rel: 'noopener',
          class: 'small', style: 'margin-left:auto',
          title: m.wayback && m.wayback.last
            ? 'The website as the Wayback Machine archived it during this Congress' : null,
        }, siteName(m))),
      el('div', { class: 'stats' },
        el('div', {},
          el('span', { class: 'v tab' }, num(groups.written.length)),
          el('span', { class: 'k' },
            years.length
              ? (years[0] === years[years.length - 1]
                ? `Letters written, ${years[0]}`
                : `Letters written, ${years[0]}–${years[years.length - 1]}`)
              : 'Letters written')),
        groups.received.length
          ? el('div', {}, el('span', { class: 'v tab' }, num(groups.received.length)),
            el('span', { class: 'k' }, 'Letters received'))
          : null,
        m.since
          ? el('div', {},
            el('span', { class: 'v tab' }, service(m)),
            el('span', { class: 'k' }, 'Dates of service'))
          : null,
        el('div', {}, el('span', { class: 'v tab' }, num(recipients.length)),
          el('span', { class: 'k' }, 'Named recipients')),
      )),
    el('div', { class: 'cols' },
      el('div', {},
        (groups.received.length || groups.posted.length)
          ? el('div', { class: 'toggle dirs', role: 'group', 'aria-label': 'Which letters' },
            ...['written', 'received', 'posted'].filter(k => groups[k].length).map(k =>
              el('button', {
                'aria-pressed': String(k === dir),
                onclick: () => { const q = params(); if (k === 'written') q.delete('dir'); else q.set('dir', k); shown = 0; go(q); },
              }, `${LABELS[k]} (${num(groups[k].length)})`)))
          : null,
        el('div', { class: 'controls' },
          el('div', { class: 'toggle' },
            el('button', {
              'aria-pressed': String(!asList),
              onclick: () => switchTo('wall'),
            }, 'The letters'),
            el('button', {
              'aria-pressed': String(asList),
              onclick: () => switchTo('list'),
            }, 'As a list')),
          el('span', { class: 'count tab' },
            `${num(dated)} of ${num(rows.length)} have an exact date`)),
        el('p', { class: 'note' },
          dir === 'received'
            ? `Letters written to ${m.name}: those posted on ${siteName(m)}, and those `
              + 'addressed to them that other members posted ("As recipient").'
            : 'These are the letters the Wayback Machine has archived from '
              + `${siteName(m)} — not necessarily everything this office published.`),
        // A received copy may have been posted by another member, whom the row
        // does not name; the list leaves its member column empty rather than
        // naming this one.
        asList ? table(rows, { member: dir === 'received' ? null : m }) : wall(rows)),
      el('div', {},
        el('div', { class: 'panel' },
          el('h3', {}, 'Who they wrote to'),
          recipients.length
            ? rankList(recipients, name => link({ to: name }, null, name))
            : el('p', { class: 'faint small' },
              'This office doesn’t name recipients in its file names, so we '
              + 'can’t tell who these went to.')),
        years.length > 1
          ? el('div', { class: 'panel' },
            el('h3', {}, 'By year'),
            rankList([...counts.entries()].sort((a, b) => b[0] - a[0]),
              y => link({ year: y }, null, String(y)), 12))
          : null)),
  );
}

function viewRecipients() {
  const p = params();
  const q = (p.get('q') || '').toLowerCase();
  const all = INDEX.recipients || [];
  // Filtering only the 200 carried in index.json meant the box answered "no
  // matches" for 3,970 recipients that exist. If the search index is already
  // in memory it knows them all; if it is not, this kicks off the fetch and
  // re-renders, so the first search of a rare name fills in a moment later.
  let pool = all;
  if (q && SEARCH && !SEARCH.failed && Array.isArray(SEARCH.recipients)) {
    const tally = new Map();
    for (const row of SEARCH.rows) {
      if (row[1] < 0) continue;
      const name = SEARCH.recipients[row[1]];
      if (!name.toLowerCase().includes(q)) continue;
      tally.set(name, (tally.get(name) || 0) + 1);
    }
    if (tally.size) pool = [...tally.entries()].sort((a, b) => b[1] - a[1]);
  } else if (q && !SEARCH) {
    loadSearch().then(() => render());
  }
  const list = q ? pool.filter(([name]) => name.toLowerCase().includes(q)) : all;
  const limit = shown || CARDS;
  const max = all.length ? all[0][1] : 1;

  const grid = el('div', { class: 'grid' });
  for (const [name, n] of list.slice(0, limit)) {
    grid.append(link({ to: name }, 'card',
      el('span', { class: 'top' },
        el('span', { class: 'nm' }, name),
        el('span', { class: 'ct tab' }, num(n))),
      el('span', { class: 'track', style: 'width:100%;height:.55rem;background:var(--tint);border-radius:3px;overflow:hidden' },
        el('i', {
          style: `display:block;height:100%;width:${Math.max(3, (n / max) * 100)}%;`
            + 'background:var(--active);opacity:.5',
        })),
    ));
  }

  const out = el('div', {},
    el('h1', { class: 'hero' }, 'Who gets these letters'),
    el('p', { class: 'sub' },
      el('b', {}, num(INDEX.recipients_total || all.length)),
      ' agencies, officials and companies have been written to',
      INDEX.recipients_total && INDEX.recipients_total > all.length
        ? `. The ${num(all.length)} most written-to are below. ` : '. ',
      'We group an agency with the people who ran it, so letters to the EPA and ',
      'letters to its administrator show up together.'),
    el('div', { class: 'controls' },
      el('input', {
        type: 'search', value: p.get('q') || '', placeholder: 'Filter recipients',
        oninput: e => {
          const next = params();
          if (e.target.value) next.set('q', e.target.value); else next.delete('q');
          history.replaceState({}, '', `?${next}`);
          render();
          const box = $('.controls input[type=search]');
          if (box) { box.focus(); box.setSelectionRange(box.value.length, box.value.length); }
        },
      }),
      el('span', { class: 'count tab', role: 'status' }, `showing ${num(list.length)}`)),
    grid);
  if (list.length > limit) {
    out.append(el('button', {
      class: 'more', onclick: () => { shown = limit + CARDS; render(); },
    }, `Show more — ${num(list.length - limit)} more`));
  }
  return out;
}

async function viewRecipient(name) {
  // WHICH MEMBERS WROTE TO THIS RECIPIENT — asked of the search index, not
  // guessed from the member cards.
  //
  // This used to keep only members with this recipient in their top three:
  //
  //     MEMBERS.filter(m => m.top.includes(name))
  //
  // which is right for the handful of correspondents everyone writes to and
  // wrong for everyone else. 107 of the 200 recipients on the recipients page
  // had no member with them in a top three at all, so the page announced
  // "37 letters in total" and then listed none of them. Amazon, Google, the
  // Army, the Federal Election Commission, the Office of the Inspector
  // General — over half the page led somewhere empty.
  //
  // search.json already carries a recipient for every letter, so it can
  // answer the question exactly. It is one fetch, cached after the first.
  const search = await loadSearch();
  let counts = new Map();          // bioguide -> letters to this recipient
  if (search && !search.failed && Array.isArray(search.recipients)) {
    const slot = search.recipients.indexOf(name);
    if (slot >= 0) {
      for (const row of search.rows) {
        if (row[1] !== slot) continue;
        const id = search.members[row[0]];
        counts.set(id, (counts.get(id) || 0) + 1);
      }
    }
  }

  // The totals index holds only the 200 commonest recipients, so for anything
  // rarer it reports nothing. The search index knows them all.
  const fromIndex = (INDEX.recipients || []).find(([n]) => n === name)?.[1] ?? 0;
  const fromSearch = [...counts.values()].reduce((sum, n) => sum + n, 0);
  const indexCount = fromIndex || fromSearch;

  // Busiest first, and bounded: "The President" is 289 members, and a page
  // that fetches 289 files before it draws anything is its own kind of broken.
  const RECIPIENT_MEMBERS = 40;
  let ids = [...counts.entries()].sort((a, b) => b[1] - a[1]).map(([id]) => id);
  const withheld = Math.max(0, ids.length - RECIPIENT_MEMBERS);
  ids = ids.slice(0, RECIPIENT_MEMBERS);

  // If search could not be loaded at all, fall back to the old behaviour
  // rather than showing nothing.
  const candidates = ids.length
    ? ids.map(id => byId.get(id)).filter(Boolean)
    : MEMBERS.filter(m => m.top.includes(name));

  const loaded = await Promise.all(candidates.map(async m =>
    [m, (await lettersOf(m.id)).filter(r => get(r, 'direction') !== 'received' && get(r, 'recipient') === name)]));
  const pairs = loaded.filter(([, rows]) => rows.length)
    .sort((a, b) => b[1].length - a[1].length);
  const total = pairs.reduce((sum, [, rows]) => sum + rows.length, 0);

  return el('div', {},
    link({ view: 'recipients' }, 'back', '← All recipients'),
    el('div', { class: 'panel' },
      el('div', { class: 'dhead' }, el('h2', {}, name)),
      el('div', { class: 'stats' },
        el('div', {}, el('span', { class: 'v tab' }, num(indexCount)),
          el('span', { class: 'k' }, 'Letters in total')),
        el('div', {}, el('span', { class: 'v tab' }, num(pairs.length)),
          el('span', { class: 'k' }, 'Members shown')),
      )),
    withheld
      ? el('p', { class: 'note' },
        `${num(withheld)} more members also wrote to ${name}. The busiest `
        + `${RECIPIENT_MEMBERS} are shown here; the rest are on their own pages.`)
      : null,
    pairs.length
      ? el('div', {}, ...pairs.map(([m, rows]) =>
        el('div', { class: 'panel' },
          el('h3', {}, link({ member: m.id }, null, m.name), ` · ${num(rows.length)}`),
          el('div', { class: 'wall' }, ...rows.slice(0, 12).map(shot)))))
      : el('div', { class: 'empty' },
        total === 0 && indexCount > 0
          ? 'Could not load the letters for this recipient — try reloading.'
          : 'No letters loaded for this recipient.'));
}

function viewTimeline() {
  const years = INDEX.years || {};
  const entries = Object.entries(years).map(([y, n]) => [Number(y), n])
    .sort((a, b) => a[0] - b[0]);
  if (!entries.length) return el('div', { class: 'empty' }, 'No dated letters.');
  const from = entries[0][0], to = entries[entries.length - 1][0];
  const max = Math.max(...entries.map(e => e[1]));

  const bars = el('div', { class: 'bars' });
  for (let y = from; y <= to; y++) {
    const n = years[String(y)] || 0;
    bars.append(el('button', {
      style: `height:${n ? Math.max(2, (n / max) * 100) : 0}%`,
      title: `${y}: ${num(n)} letters`,
      'aria-label': `${y}, ${n} letters`,
      onclick: () => { const q = params(); q.set('year', y); q.delete('view'); shown = 0; go(q); },
    }));
  }

  const exact = ((INDEX.precisions || {}).day || 0) + ((INDEX.precisions || {}).letterhead || 0);
  const fromPdf = (INDEX.precisions || {}).scanned || 0;
  const guessed = (INDEX.precisions || {})['captured-by'] || 0;

  return el('div', {},
    el('h1', { class: 'hero' }, 'Letters over time'),
    el('p', { class: 'sub' },
      'Click any year to read what was sent that year. ',
      el('span', { class: 'muted' },
        'Keep in mind this chart shows when letters were '),
      el('span', { class: 'muted' }, el('em', {}, 'archived')),
      el('span', { class: 'muted' },
        ', not everything Congress sent.')),
    el('div', { class: 'panel' }, bars,
      el('div', { class: 'axis' },
        ...[from, Math.round((from + to) / 2), to].map((y, i) => el('span', {
          style: `position:absolute;left:${((y - from) / Math.max(1, to - from)) * 100}%;`
            + `transform:translateX(${i === 0 ? 0 : i === 2 ? -100 : -50}%)`,
        }, y)))),
    el('div', { class: 'panel' },
      el('h3', {}, 'How we know when a letter was sent'),
      el('p', { class: 'small' },
        'Three ways, and the site always tells you which one it used.'),
      el('ul', { class: 'rank' },
        el('li', {}, el('span', { class: 'nm' },
          el('b', {}, 'The date is in the file name. '),
          'Exact. Shown as a normal date.'),
          el('span', { class: 'n tab' }, num(exact))),
        fromPdf
          ? el('li', {}, el('span', { class: 'nm' },
            el('b', {}, 'The PDF records when it was made. '),
            'Usually the day the letter was scanned and posted — close, but it '
            + 'can run a little late.'),
            el('span', { class: 'n tab' }, num(fromPdf)))
          : null,
        el('li', {}, el('span', { class: 'nm' },
          el('b', {}, 'Neither. '),
          'We show when the Wayback Machine first saw the file, written as '
          + '“by March 2016”. The letter existed by then, and may be older.'),
          el('span', { class: 'n tab' }, num(guessed))))));
}

async function viewYear(yearText) {
  const year = Number(yearText);

  // Same shape as viewRecipient: ask the search index which members actually
  // wrote that year rather than loading everyone whose service span covers it.
  // The span filter was not WRONG, it was indiscriminate — 416 member files
  // fetched to draw the 2024 page, 316 for 2020. The index knows who, so only
  // the busiest are fetched and the page draws without pulling 12 MB first.
  //
  // search.json omits the few hundred letters that have neither a subject nor
  // a recipient, which is fine here: it is choosing WHICH members to load, and
  // every letter of a loaded member is still counted from the member's own file.
  const search = await loadSearch();
  let counts = new Map();
  if (search && !search.failed && Array.isArray(search.rows)) {
    for (const row of search.rows) {
      if (row[2] !== year) continue;
      counts.set(row[0], (counts.get(row[0]) || 0) + 1);
    }
  }
  const YEAR_MEMBERS = 40;
  let ids = [...counts.entries()].sort((a, b) => b[1] - a[1]).map(([i]) => i);
  const withheld = Math.max(0, ids.length - YEAR_MEMBERS);
  ids = ids.slice(0, YEAR_MEMBERS).map(i => search.members[i]);

  const candidates = ids.length
    ? ids.map(id => byId.get(id)).filter(Boolean)
    : MEMBERS.filter(m => m.span && m.span[0] <= year && year <= m.span[1]);

  const loaded = await Promise.all(candidates.map(async m =>
    [m, (await lettersOf(m.id)).filter(r => get(r, 'direction') !== 'received' &&
      (get(r, 'date') || '').startsWith(String(year)))]));
  const pairs = loaded.filter(([, rows]) => rows.length)
    .sort((a, b) => b[1].length - a[1].length);
  const rows = pairs.flatMap(([, r]) => r);
  const total = (INDEX.years || {})[String(year)] || 0;

  return el('div', {},
    link({ view: 'timeline' }, 'back', '← Timeline'),
    el('div', { class: 'panel' },
      el('div', { class: 'dhead' }, el('h2', {}, year)),
      el('div', { class: 'stats' },
        el('div', {}, el('span', { class: 'v tab' }, num(total)),
          el('span', { class: 'k' }, 'Letters')),
        el('div', {}, el('span', { class: 'v tab' }, num(pairs.length)),
          el('span', { class: 'k' }, 'Members')),
      )),
    withheld
      ? el('p', { class: 'note' },
        `${num(withheld)} more members also wrote in ${year}. The busiest `
        + `${YEAR_MEMBERS} are shown here; the rest are on their own pages.`)
      : null,
    el('div', { class: 'cols' },
      el('div', { class: 'panel' }, wall(rows)),
      el('div', { class: 'panel' },
        el('h3', {}, 'Wrote the most that year'),
        rankList(pairs.map(([m, r]) => [m.id, r.length]),
          id => link({ member: id }, null, byId.get(id)?.name || '—'), 14))));
}

// Full-text search, from the Pagefind index build/build_search.py writes into
// this explorer's pagefind/ folder. Loaded only when someone searches, and
// only once. An explorer built without the index (the template's own preview)
// says so instead.
let pagefindLoad = null;
const pagefind = () => (pagefindLoad ??= import('./pagefind/pagefind.js').catch(() => null));

// Pagefind escapes the letter's text and wraps matches in <mark>. Built as
// nodes, not inserted as markup: the excerpt is split on its <mark> tags and
// each piece decoded as text, so nothing in a letter can become markup.
const decodeEntities = t => t.replace(/&(lt|gt|quot|#39|#x27|amp);/g,
  m => ({ '&lt;': '<', '&gt;': '>', '&quot;': '"', '&#39;': "'", '&#x27;': "'", '&amp;': '&' })[m]);
function excerptNodes(html) {
  const out = [];
  let marked = false;
  for (const piece of String(html || '').split(/(<mark>|<\/mark>)/)) {
    if (piece === '<mark>') { marked = true; continue; }
    if (piece === '</mark>') { marked = false; continue; }
    if (!piece) continue;
    const text = decodeEntities(piece);
    out.push(marked ? el('mark', {}, text) : text);
  }
  return out;
}

function fullTextResult(d) {
  const m = d.meta || {};
  const ids = (m.member_ids || '').split(';').filter(Boolean);
  const names = (m.members || '').split('; ');
  const who = ids.map((id, i) => link({ member: id }, null, names[i] || id));
  const row = [];                       // when() reads a letter row by column
  row[F.date] = m.date; row[F.precision] = m.precision;
  const date = m.date ? when(row, true) : '';
  return el('li', { class: 'fulltext' },
    el('a', { href: d.url, target: '_blank', rel: 'noopener', class: 'ft-title' }, m.title || 'Letter'),
    el('span', { class: 'ft-meta' },
      ...who.flatMap((a, i) => (i ? [', ', a] : [a])),
      m.recipient ? ` to ${m.recipient}` : '',
      date ? ` · ${date}` : '',
      m.source === 'ocr'
        ? el('span', { class: 'chip', title: 'Read by OCR from a scanned page; the excerpt may contain misreadings' }, 'OCR')
        : null),
    el('p', { class: 'ft-excerpt' }, ...excerptNodes(d.excerpt)));
}

function fullTextPanel(query) {
  const status = el('p', { class: 'small muted', role: 'status' }, 'Searching the text of the letters…');
  const list = el('ol', { class: 'fulltext-list' });
  const panel = el('div', { class: 'panel' },
    el('h2', { class: 'panel-h' }, 'In the letters’ own words'), status, list);
  (async () => {
    const pf = await pagefind();
    if (!pf) { status.textContent = 'Full-text search is not available for this explorer.'; return; }
    const res = await pf.search(query);
    const total = res.results.length;
    status.textContent = total
      ? `${num(total)} letters contain “${query}”. About two thirds of letters have readable text; scans are read by OCR.`
      : `No letter’s text contains “${query}”. About two thirds of letters have readable text.`;
    let next = 0;
    const more = el('button', { class: 'more', type: 'button' });
    const page = async () => {
      const batch = await Promise.all(res.results.slice(next, next + 20).map(r => r.data()));
      next += batch.length;
      list.append(...batch.map(fullTextResult));
      if (next < total) { more.textContent = `Show more — ${num(total - next)} more`; if (!more.isConnected) panel.append(more); }
      else more.remove();
    };
    more.addEventListener('click', page);
    if (total) await page();
  })().catch(() => { status.textContent = 'Full-text search is unavailable right now.'; });
  return panel;
}

// ------------------------------------------------ vocabulary suggestions
//
// search.json carries the vocabulary as [tag, name, forms, broader] (#1449):
// the tags letters are filed under, the other words that mean each one, and
// the tag it sits under. Two uses here, both only ever offering something the
// index has letters for:
//
//   Filed under — a search for a word the vocabulary knows ("coronavirus",
//     "Environmental Protection Agency") names the tag it belongs to, so the
//     letters tagged with it but not using that word can be reached. Broader
//     and narrower tags are offered beside it.
//   Did you mean — a search that finds little is checked, as a phrase and
//     word by word, against the vocabulary, member and recipient names and the
//     words in letter descriptions, for something one or two keystrokes away.

const fold = s => (s || '').toLowerCase().normalize('NFKD')
  .replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, ' ').trim();

// Optimal string alignment distance, giving up once it passes `max`.
function editDistance(a, b, max) {
  if (Math.abs(a.length - b.length) > max) return max + 1;
  let prev2 = null, prev = Array.from({ length: b.length + 1 }, (_, j) => j);
  for (let i = 1; i <= a.length; i++) {
    const cur = [i];
    let best = i;
    for (let j = 1; j <= b.length; j++) {
      let d = Math.min(prev[j] + 1, cur[j - 1] + 1,
        prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
      if (prev2 && i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) {
        d = Math.min(d, prev2[j - 2] + 1);
      }
      cur.push(d);
      if (d < best) best = d;
    }
    if (best > max) return max + 1;
    prev2 = prev; prev = cur;
  }
  return prev[b.length];
}

// How far off a word may be and still be a typo of it: none below five
// letters, where one keystroke is usually a different word (ice, ira, va);
// two from seven, which is what "fentynal" and "tarrifs" need.
const slack = n => (n < 5 ? 0 : n < 7 ? 1 : 2);

// The same test viewSearch applies, so a suggestion's count is what clicking
// it will show.
function rowMatches(data, row, needle) {
  const recipient = row[1] >= 0 ? data.recipients[row[1]] : '';
  return row[4].toLowerCase().includes(needle)
    || recipient.toLowerCase().includes(needle)
    || (row[6] || '').toLowerCase().includes(needle);
}
function countMatches(data, needle) {
  let n = 0;
  for (const row of data.rows) if (rowMatches(data, row, needle)) n++;
  return n;
}

// Members by name, or by another name the vocabulary has for them.
function membersNamed(data, needle) {
  const aka = (data && data.aka) || {};
  return MEMBERS.filter(m => m.name.toLowerCase().includes(needle)
    || (aka[m.id] || []).some(a => a.toLowerCase().includes(needle)));
}

let VOCAB = null;   // built from SEARCH once, on the first search that needs it
function vocabOf(data) {
  if (VOCAB && VOCAB.data === data) return VOCAB;
  const entries = (data.vocab || []).map(([tag, name, forms, broader]) =>
    ({ tag, name, forms: forms || [], broader, narrower: [], count: 0 }));
  const byTag = new Map(entries.map(e => [e.tag, e]));
  for (const row of data.rows) {
    for (const t of (row[6] || '').split(',')) {
      const e = t && byTag.get(t);
      if (e) e.count++;
    }
  }
  for (const e of entries) {
    const up = e.broader && byTag.get(e.broader);
    if (up) up.narrower.push(e);
  }
  // Exact lookups. A tag outranks another tag's form: "Defense" is a topic
  // and also one of the Department of Defense's names.
  const exact = new Map();
  for (const e of entries) {
    for (const f of [e.name, ...e.forms]) {
      const k = fold(f);
      if (k.length >= 3 && !exact.has(k)) exact.set(k, e);
    }
  }
  for (const e of entries) exact.set(fold(e.tag), e);

  // Phrases a whole query might be a typo of, with how many letters each finds.
  const phrases = new Map();
  const addPhrase = (text, n) => {
    const k = fold(text);
    if (k.length < 5 || !n) return;
    const was = phrases.get(k);
    if (!was || was.n < n) phrases.set(k, { text, n });
  };
  for (const e of entries) {
    addPhrase(e.tag, e.count);
    if (e.name) addPhrase(e.name, e.count);
    for (const f of e.forms) addPhrase(f, e.count);
  }
  for (const m of MEMBERS) {
    addPhrase(m.name, m.letters || 1);
    for (const a of (data.aka || {})[m.id] || []) addPhrase(a, m.letters || 1);
  }
  const recipientCounts = new Map();
  for (const row of data.rows) {
    if (row[1] >= 0) recipientCounts.set(row[1], (recipientCounts.get(row[1]) || 0) + 1);
  }
  for (const [i, n] of recipientCounts) addPhrase(data.recipients[i], n);

  // Single words, for a query that is right but for one misspelled word.
  const words = new Map();
  const addWords = text => {
    for (const w of fold(text).split(' ')) {
      if (w.length >= 3) words.set(w, (words.get(w) || 0) + 1);
    }
  };
  for (const row of data.rows) { addWords(row[4]); addWords(row[6]); }
  for (const name of data.recipients) addWords(name);
  for (const m of MEMBERS) {
    addWords(m.name);
    ((data.aka || {})[m.id] || []).forEach(addWords);
  }
  for (const e of entries) { addWords(e.name); e.forms.forEach(addWords); }

  VOCAB = { data, entries, byTag, exact, phrases, words };
  return VOCAB;
}

// The tag a query names, if it names one exactly.
function filedUnder(data, query) {
  const v = vocabOf(data);
  const e = v.exact.get(fold(query));
  return e && e.count ? e : null;
}

// The likeliest thing the visitor meant, or null. Only offered when it would
// find letters, and never the query itself.
function didYouMean(data, query) {
  const v = vocabOf(data);
  const q = fold(query);
  if (!q) return null;

  // The whole query against whole names and terms.
  let best = null;
  const max = slack(q.length);
  if (max) {
    for (const [k, p] of v.phrases) {
      if (k === q) return null;   // it is already a name the index knows
      const d = editDistance(q, k, max);
      if (d <= max && (!best || d < best.d || (d === best.d && p.n > best.n))) {
        best = { d, text: p.text, n: p.n };
      }
    }
  }
  if (best) {
    const n = countMatches(data, best.text.toLowerCase());
    if (n) return { text: best.text, n, what: 'letter' };
    const m = membersNamed(data, best.text.toLowerCase()).length;
    if (m) return { text: best.text, n: m, what: 'member' };
  }

  // Word by word: mend each word the index has never seen.
  const fixed = q.split(' ').map(w => {
    if (v.words.has(w) || slack(w.length) === 0) return w;
    let pick = null;
    for (const [cand, n] of v.words) {
      const d = editDistance(w, cand, slack(w.length));
      if (d <= slack(w.length) && (!pick || d < pick.d || (d === pick.d && n > pick.n))) {
        pick = { d, cand, n };
      }
    }
    return pick ? pick.cand : w;
  }).join(' ');
  if (fixed !== q) {
    const n = countMatches(data, fixed);
    if (n) return { text: fixed, n, what: 'letter' };
    const m = membersNamed(data, fixed).length;
    if (m) return { text: fixed, n: m, what: 'member' };
  }
  return null;
}

function vocabPanel(data, query, explained) {
  const e = filedUnder(data, query);
  if (!e) return null;
  const tagLink = (t, n) => el('span', {},
    link({ view: 'search', q: t.tag }, null, t.tag),
    el('span', { class: 'faint' }, ` (${num(n ?? t.count)})`));
  const sameAsTag = fold(query) === fold(e.tag);
  const up = e.broader ? vocabOf(data).byTag.get(e.broader) : null;
  const down = e.narrower.filter(t => t.count).sort((a, b) => b.count - a.count);
  if (sameAsTag && !up && !down.length && (explained || !e.name)) return null;
  return el('div', { class: 'note' },
    sameAsTag
      ? (explained ? null : el('p', {}, el('b', {}, e.tag), e.name ? `: ${e.name}.` : ': a topic in the vocabulary.'))
      : el('p', {}, `Letters about “${query}” are filed under `,
        el('b', {}, link({ view: 'search', q: e.tag }, null, e.tag)),
        e.name && fold(e.name) !== fold(query) ? ` (${e.name})` : '',
        ': ', el('b', {}, num(e.count)), e.count === 1 ? ' letter.' : ' letters.'),
    up && up.count
      ? el('p', { class: 'small' }, 'Broader: ', tagLink(up)) : null,
    down.length
      ? el('p', { class: 'small' }, 'Narrower: ',
        ...down.slice(0, 12).flatMap((t, i) => [i ? ' · ' : '', tagLink(t)]))
      : null);
}

// ------------------------------------------------------------- acronyms
//
// A search for "ice" or "ai" matches every description with those letters in
// it: justice, service, said, Maine. search.json says what such a search
// might stand for (#1448), and the letters that use it in that sense are put
// first: rank 0 tagged with it, rank 1 using it as a word or spelled out,
// rank 2 the letters merely containing the string.

let ACRO_MEMO = null;
function acronymOf(data, query) {
  if (ACRO_MEMO && ACRO_MEMO.data === data && ACRO_MEMO.query === query) return ACRO_MEMO.value;
  const value = acronymLookup(data, query);
  ACRO_MEMO = { data, query, value };
  return value;
}

function acronymLookup(data, query) {
  const q = (query || '').trim();
  if (!data || !data.acronyms || !/^[A-Za-z&]{2,8}$/.test(q)) return null;
  const meanings = data.acronyms[q.toUpperCase()];
  if (!meanings || !meanings.length) return null;
  const word = new RegExp(`(^|[^a-z0-9])${q.toLowerCase().replace('&', '\\&')}($|[^a-z0-9])`);
  const list = meanings.map(([meaning, tag, forms]) => ({ meaning, tag, forms, n: 0 }));
  const rank = (subject, recipient, topics) => {
    const tags = topics ? topics.split(',') : [];
    if (list.some(m => m.tag && tags.includes(m.tag))) return 0;
    const text = `${subject} ${recipient}`.toLowerCase();
    if (word.test(text) || list.some(m => m.forms.some(f => text.includes(f)))) return 1;
    return 2;
  };
  // Which meaning the letters lean to, for the order they are named in.
  for (const row of data.rows) {
    const recipient = row[1] >= 0 ? data.recipients[row[1]] : '';
    const text = `${row[4]} ${recipient}`.toLowerCase();
    const tags = row[6] ? row[6].split(',') : [];
    for (const m of list) {
      if ((m.tag && tags.includes(m.tag)) || m.forms.some(f => text.includes(f))) m.n++;
    }
  }
  list.sort((a, b) => b.n - a.n);
  return { key: q.toUpperCase(), list, rank };
}

function acronymNote(acro, letterHits, query, capped) {
  const first = letterHits.filter(h => h[7] < 2).length;
  const rest = letterHits.length - first;
  const [top, ...others] = acro.list;
  return el('div', { class: 'note' },
    el('p', {}, el('b', {}, acro.key), ` stands for ${top.meaning}`,
      others.length ? el('span', {}, ', or for ',
        ...others.flatMap((m, i) => [i ? ', ' : '',
          link({ view: 'search', q: m.meaning }, null, m.meaning)])) : null,
      '. ',
      first
        ? el('span', {}, el('b', {}, num(first)),
          first === 1 ? ' letter is' : ' letters are',
          ` tagged with it, spell it out, or use “${acro.key}” as a word, and come first`,
          rest ? el('span', {}, `; the ${capped ? `next ${num(rest)}` : `other ${num(rest)}`} only contain “${query.trim().toLowerCase()}” inside another word.`) : '.')
        : `No letter here uses “${acro.key}” as a word or spells it out.`),
    top.n && fold(top.tag || top.meaning) !== fold(query)
      ? el('p', { class: 'small' }, 'Or search for ',
        link({ view: 'search', q: top.tag || top.meaning }, null, top.tag || top.meaning), ' itself.')
      : null);
}

async function viewSearch(query) {
  const needle = (query || '').trim().toLowerCase();
  const runSearch = text => {
    const next = new URLSearchParams();
    next.set('view', 'search');
    next.set('q', text);
    shown = 0;
    go(next);
  };

  // A form, so Enter searches at once rather than waiting out the typing
  // delay, and then takes the visitor to the results (#1416).
  const box = el('form', {
    class: 'controls', role: 'search',
    onsubmit: e => {
      e.preventDefault();
      clearTimeout(window.__st);
      const v = $('#bigsearch').value.trim();
      const next = new URLSearchParams();
      next.set('view', 'search');
      if (v) next.set('q', v);
      shown = 0;
      history.pushState({}, '', `?${next}`);
      render().then(() => $('#sr-h')?.focus());
    },
  },
    el('input', {
      type: 'search', value: query || '', id: 'bigsearch',
      'aria-label': 'Search letters',
      placeholder: 'Search letters — a topic, an agency, a member’s name',
      oninput: e => {
        const v = e.target.value;
        clearTimeout(window.__st);
        window.__st = setTimeout(() => {
          const next = params();
          if (v) next.set('q', v); else next.delete('q');
          history.replaceState({}, '', `?${next}`);
          render().then(() => {
            const b = $('#bigsearch');
            if (b) { b.focus(); b.setSelectionRange(b.value.length, b.value.length); }
          });
        }, 220);
      },
    }),
    el('button', { type: 'submit', class: 'go' }, 'Search'));

  if (!needle) {
    const picks = (INDEX.topics || []).slice(0, 18).map(([t]) => t);
    return el('div', {}, box,
      el('h1', { class: 'hero' }, 'What are you looking for?'),
      el('p', { class: 'sub' },
        'Search ', el('b', {}, num(INDEX.letters)),
        ' letters by topic, by the agency they were sent to, or by who wrote them.'),
      picks.length
        ? el('div', { class: 'panel' },
          el('h3', {}, 'Try one of these'),
          el('div', { class: 'controls' },
            // .pill, not .chip: these were already buttons and nobody could
            // tell, because .chip is the label style used for topic tags.
            ...picks.map(t => el('button', {
              class: 'pill', type: 'button',
              title: `Search for ${t}`,
              onclick: () => runSearch(t),
            }, t))))
        : null,
      el('div', { class: 'panel' },
        el('h3', {}, 'Or browse instead'),
        el('p', { class: 'small' },
          link({ view: 'members' }, null, 'By member of Congress'), ' · ',
          link({ view: 'recipients' }, null, 'By who the letters went to'), ' · ',
          link({ view: 'timeline' }, null, 'By year'))));
  }

  const nameHits = MEMBERS.filter(m => m.name.toLowerCase().includes(needle));

  const loaded = await loadSearch();
  const data = loaded && !loaded.failed ? loaded : null;
  const failed = loaded && loaded.failed;
  // Other names for members, from the vocabulary: "Bernie Sanders" (#1449).
  if (data) {
    for (const m of membersNamed(data, needle)) {
      if (!nameHits.includes(m)) nameHits.push(m);
    }
  }
  // An acronym inside a member's name is not the acronym: "ai" is in Daines
  // and Kaine. Keep only the members whose name has it as a word (#1448).
  const acro = acronymOf(data, query);
  if (acro) {
    const asWord = new RegExp(`(^|[^a-z0-9])${needle.replace(/[^a-z0-9]/g, '')}($|[^a-z0-9])`);
    nameHits.splice(0, nameHits.length,
      ...nameHits.filter(m => asWord.test(fold(m.name))));
  }

  // Shortcuts to a recipient's own page, counted over EVERY recipient rather
  // than the 200 the totals list carries. 3,970 of the 4,170 are outside that
  // list, so searching for one of them found its letters — search has always
  // matched the full list — but never offered the page they sit on.
  const recipientHits = [];
  if (data) {
    const tally = new Map();
    const r = name => (acro ? acro.rank(name, '', '') : 2);
    for (const row of data.rows) {
      if (row[1] < 0) continue;
      const name = data.recipients[row[1]];
      // An acronym also finds the recipients that spell it out: "va" finds
      // the Department of Veterans Affairs.
      if (!name.toLowerCase().includes(needle) && r(name) === 2) continue;
      tally.set(name, (tally.get(name) || 0) + 1);
    }
    // For an acronym, recipients that are what it stands for come first:
    // "ai" is inside Department of Veterans Affairs (#1448).
    recipientHits.push(...[...tally.entries()].sort((a, b) => r(a[0]) - r(b[0]) || b[1] - a[1]));
  } else {
    recipientHits.push(...(INDEX.recipients || [])
      .filter(([name]) => name.toLowerCase().includes(needle)));
  }
  const letterHits = [];
  let loose = 0;
  if (data) {
    for (const [mIdx, rIdx, year, rowIdx, subject, exact, topics] of data.rows) {
      const recipient = rIdx >= 0 ? data.recipients[rIdx] : '';
      // Topics are matched too, so "FEMA" finds a letter whose description
      // never says FEMA but which the vocabulary tagged as being about it.
      const hit = subject.toLowerCase().includes(needle)
          || recipient.toLowerCase().includes(needle)
          || (topics || '').toLowerCase().includes(needle);
      // An acronym also finds the letters that spell it out, and the cap
      // applies only to the loose matches, so it can never cut off the
      // letters that use it ("ai" is inside 4,309 descriptions).
      const rank = acro ? acro.rank(subject, recipient, topics || '') : 2;
      if (hit || rank < 2) {
        if (rank === 2 && loose >= 4000) continue;
        if (rank === 2) loose++;
        letterHits.push([data.members[mIdx], recipient, year, subject, exact,
                         rowIdx, topics || '', rank]);
        if (!acro && letterHits.length >= 4000) break;
      }
    }
  }
  // Letters whose description matches come before those matched only by
  // recipient or topic tag (#1416), after the acronym's own ranking (#1448).
  const bySubject = h => (h[3].toLowerCase().includes(needle) ? 0 : 1);
  letterHits.sort((a, b) => a[7] - b[7] || bySubject(a) - bySubject(b)
    || (b[2] || 0) - (a[2] || 0) || (b[4] - a[4]));

  const limit = shown || 60;
  const visible = letterHits.slice(0, limit);

  // The index stores a pointer rather than the letter's URL, which is by far
  // its longest field. Resolving it means loading the member files for the
  // results actually on screen — a few dozen small files, already cached if
  // the visitor has opened any of those members.
  const needed = [...new Set(visible.map(h => h[0]))];
  const files = new Map();
  await Promise.all(needed.map(async id => {
    files.set(id, await lettersOf(id).catch(() => []));
  }));

  const letterOf = (mid, rowIdx) => {
    const rows = files.get(mid);
    return rows && rows[rowIdx] ? rows[rowIdx] : null;
  };

  const table = el('table', { class: 'letters' },
    el('thead', {}, el('tr', {},
      el('th', {}, 'Year'), el('th', {}, 'Member'),
      el('th', {}, 'Sent to'), el('th', {}, 'Scope of letter'), el('th', {}, ''))),
    el('tbody', {}, ...visible.map(([mid, recipient, year, subject, exact, rowIdx, topics]) => {
      const m = byId.get(mid);
      const row = letterOf(mid, rowIdx);
      const href = row ? waybackUrl(row) : null;
      return el('tr', {},
        el('td', { class: 'wh' },
          year ? (exact ? String(year) : `by ${year}`) : '—'),
        el('td', { class: 'who' }, m ? link({ member: mid }, null, m.name) : '—'),
        el('td', { class: 'who' }, recipient
          ? link({ to: recipient }, null, recipient)
          : el('span', { class: 'faint' }, 'not named')),
        el('td', { class: 'sub2' },
          href
            ? el('a', { href, target: '_blank', rel: 'noopener' },
              subject || 'Open this letter')
            : (subject || el('span', { class: 'faint' }, '—')),
          topics
            ? el('span', { class: 'topics' },
              topics.split(',').filter(Boolean).map(t =>
                link({ view: 'search', q: t }, 'topic', t)))
            : null),
        el('td', {}, href
          ? el('a', { href, target: '_blank', rel: 'noopener', class: 'small' },
            row && get(row, 'kind') === 'pdf' ? 'Read it' : 'Open')
          : null));
    })));

  // Only worth the work, and only worth the visitor's attention, when the
  // search came back thin.
  const suggestion = data && letterHits.length < 5 && !nameHits.length
    ? didYouMean(data, query) : null;

  // Topics the search names (#1416): tags in this Congress's vocabulary whose
  // name, or another word for them, contains the query.
  // A word must start with the query: "ice" is not in Justice or Service.
  const wordStart = new RegExp(`(^|[^a-z0-9])${fold(needle).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}`);
  const topicHits = data && fold(needle).length >= 2 ? vocabOf(data).entries
    .filter(e => e.count && [e.tag, e.name, ...e.forms].some(f => f && wordStart.test(fold(f))))
    .sort((a, b) => (fold(a.tag) === fold(needle) ? -1 : 0) - (fold(b.tag) === fold(needle) ? -1 : 0)
      || b.count - a.count)
    : [];
  const topicsPanel = topicHits.length
    ? el('div', { class: 'panel', id: 'sr-topics' }, el('h2', { class: 'panel-h' }, 'Topics'),
      el('div', { class: 'controls' }, ...topicHits.slice(0, 16).map(e =>
        link({ view: 'search', q: e.tag }, 'pill', e.tag, el('span', { class: 'faint' }, ` ${num(e.count)}`)))))
    : null;
  const membersPanel = nameHits.length
    ? el('div', { class: 'panel', id: 'sr-members' }, el('h2', { class: 'panel-h' }, 'Members'),
      el('div', { class: 'grid' }, ...nameHits.slice(0, 9).map(m =>
        link({ member: m.id }, 'card',
          el('span', { class: 'top' }, el('span', { class: 'nm' }, m.name),
            el('span', { class: 'ct tab' }, num(m.letters))),
          el('span', { class: 'meta' }, memberBadges(m))))))
    : null;
  const lettersPanel = letterHits.length
    ? el('div', { class: 'panel', id: 'sr-letters' }, el('h2', { class: 'panel-h' }, 'Letters'), table,
      letterHits.length > limit
        ? el('button', { class: 'more', onclick: () => { shown = limit + 120; render(); } },
          `Show more — ${num(letterHits.length - limit)} more letters`)
        : null)
    : null;
  const sentPanel = recipientHits.length
    ? el('div', { class: 'panel', id: 'sr-to' }, el('h2', { class: 'panel-h' }, 'Sent to'),
      rankList(recipientHits, name => link({ to: name }, null, name), 8))
    : null;
  const ftPanel = fullTextPanel(query);
  ftPanel.id = 'sr-ft';
  // Subjects first; members first when the search is someone's name (#1416).
  const nameFirst = nameHits.length > 0;
  const ordered = nameFirst
    ? [[membersPanel, 'Members', nameHits.length], [topicsPanel, 'Topics', topicHits.length]]
    : [[topicsPanel, 'Topics', topicHits.length], [membersPanel, 'Members', nameHits.length]];
  ordered.push([lettersPanel, 'Letters', letterHits.length], [sentPanel, 'Sent to', recipientHits.length],
    [ftPanel, 'In the letters’ own words', null]);
  const shownPanels = ordered.filter(([panel]) => panel);
  const jump = shownPanels.length > 1
    ? el('nav', { class: 'jump', 'aria-label': 'Search results' }, 'Jump to: ',
      ...shownPanels.flatMap(([panel, label, n], i) => [i ? ' · ' : '',
        el('a', { href: `#${panel.id}`, onclick: e => {
          e.preventDefault();
          panel.scrollIntoView({ block: 'start' });
          panel.setAttribute('tabindex', '-1');
          panel.focus({ preventScroll: true });
        } }, n === null ? label : `${label} (${num(n)})`)]))
    : null;

  const out = el('div', {}, box,
    el('h1', { class: 'hero', id: 'sr-h', tabindex: '-1' }, `“${query}”`),
    el('p', { class: 'sub' },
      data
        ? el('span', {}, el('b', {}, num(letterHits.length)), ' letters')
        : failed
          ? el('span', { class: 'red' }, 'Letter search is unavailable right now')
          : el('span', {}, 'Searching…'),
      nameHits.length ? el('span', {}, ', ', el('b', {}, num(nameHits.length)),
        nameHits.length === 1 ? ' member' : ' members') : null,
      recipientHits.length ? el('span', {}, ', ', el('b', {}, num(recipientHits.length)),
        ' written to') : null,
      '. ',
      el('span', { class: 'faint' },
        'Matches in letter descriptions come first; the text of the letters is searched under “In the letters’ own words”.')),
    suggestion
      ? el('p', { class: 'note' }, 'Did you mean ',
        el('b', {}, link({ view: 'search', q: suggestion.text }, null, suggestion.text)),
        '? ', el('span', { class: 'faint' },
          `${num(suggestion.n)} ${suggestion.what}${suggestion.n === 1 ? '' : 's'}`))
      : null,
    jump,
    acro ? acronymNote(acro, letterHits, query, loose >= 4000) : null,
    data ? vocabPanel(data, query, !!acro) : null,
    ...shownPanels.map(([panel]) => panel));
  if (failed) {
    out.append(el('p', { class: 'note' },
      'The search index could not be loaded, so only member and recipient names '
      + 'were searched. Browsing by '
      , link({ view: 'members' }, null, 'member'), ' or '
      , link({ view: 'recipients' }, null, 'recipient'), ' still works.'));
  }
  if (data && !letterHits.length && !nameHits.length && !recipientHits.length) {
    out.append(el('div', { class: 'empty' },
      el('p', {}, `Nothing matched “${query}”.`),
      el('p', { class: 'small' },
        'Try a broader word, or ',
        link({ view: 'search' }, null, 'start from a suggestion'), '.')));
  }
  return out;
}

function viewAbout() {
  const k = INDEX.congress || {};
  return el('div', { class: 'prose' },
    el('h1', { class: 'hero' }, 'About these letters'),

    el('p', {}, `Letters that members of the ${k.ordinal || '119th'} Congress published on
      their own websites — to government agencies, companies, the President and each
      other — as the Wayback Machine archived them: ${num(INDEX.letters)} letters from
      ${num(INDEX.members_with_letters)} members.`),

    el('h3', {}, 'Why the archive matters'),
    el('p', {}, `When a member of Congress leaves office, their website may not remain.
      The Wayback Machine archived these sites, so for many of these letters the archive
      is the only copy left.`),

    // Robin, #1371 (19 November 2026): explain the numbers.
    el('h3', {}, 'How the letters are counted'),
    el('p', {}, `A letter written by several members appears for each of them: every
      co-author who published it on their own website has it listed under their name, so
      the same letter can be counted more than once.`),
    el('p', {}, `A letter written to a member of Congress is included when the member
      published it on their own website. It is filed under that member, as recipient.`),
    el('p', {}, `The numbers will continue to grow and change as regular harvests find
      letters the Wayback Machine has newly archived, and as letters are read and filed.`),

    el('h3', {}, 'Where the details come from'),
    el('p', {}, `Who a letter went to and what it is about come mostly from the file’s
      name, which staff write for people to read, and from the letter’s text where it can
      be read. Where a file was named something vague, the description is vague too.`),
    el('p', {}, `Dates come from the file name or the PDF where they can. Where there is
      no date, we show when the Wayback Machine first saw the file, written as
      “by March 2016”: the letter existed by then.`),

    el('h3', {}, 'What’s missing'),
    el('p', {}, `Only letters the Wayback Machine archived and we have found so far. A letter
      posted without “letter” in its file name or web address is not here yet, and letters published as web pages or
      Word files rather than PDFs are only partly here.`),
    // Robin's wording, 18 November 2026 (#1330).
    el('p', {}, `While this explorer contains letters from Congress as archived in the
      Wayback Machine, coverage is not complete. The further back in time we go, the less
      digital content was produced and saved, limiting what the Wayback Machine could
      archive.`),
    el('p', {}, `Letters from Congress is incomplete: it holds only what members published on their websites and
      what could be archived from the earliest days of the internet on. Letters in print are not included unless
      they were digitized and published on a member's website.`),

    // The data download lives here, not on the home page's cards (EXPLORERS.md,
    // 2026-11-13). export_csv.py writes it beside each explorer's index.json.
    ...(k.ordinal ? [
      el('h3', { id: 'download' }, 'Download the data'),
      el('p', {}, el('a', {
        href: `data/letters-from-congress-${k.ordinal}.csv`, download: '',
      }, `Download the ${k.ordinal} Congress data (${num(INDEX.letters)} letters, CSV)`),
        ': one row per letter, with the member, date, recipient, topics, subject and its ',
        'Wayback Machine links.'),
    ] : []),

    el('p', {}, 'Built at the Internet Archive from the Wayback Machine’s ',
      `archive of congressional websites. Updated ${INDEX.built}.`),
  );
}

// -------------------------------------------------------------------- shell

const TABS = [
  ['members', 'Members'],
  ['recipients', 'Recipients'],
  ['timeline', 'Timeline'],
  ['search', 'Search'],
  ['about', 'About'],
];

function currentView(p) {
  if (p.get('member')) return 'members';
  if (p.get('to')) return 'recipients';
  if (p.get('year')) return 'timeline';
  return p.get('view') || 'members';
}

async function render() {
  const p = params();
  const view = currentView(p);

  $('#tabs').replaceChildren(...TABS.map(([key, label]) =>
    el('button', {
      'aria-current': view === key ? 'page' : null,
      onclick: () => {
        const next = new URLSearchParams();
        if (key !== 'members') next.set('view', key);
        if (key === 'search' && p.get('q')) next.set('q', p.get('q'));
        shown = 0;
        go(next);
      },
    }, label)));

  let body;
  try {
    if (p.get('member')) body = await viewMember(p.get('member'));
    else if (p.get('to')) body = await viewRecipient(p.get('to'));
    else if (p.get('year')) body = await viewYear(p.get('year'));
    else if (view === 'recipients') body = viewRecipients();
    else if (view === 'timeline') body = viewTimeline();
    else if (view === 'search') body = await viewSearch(p.get('q'));
    else if (view === 'about') body = viewAbout();
    else body = viewMembers();
  } catch (err) {
    body = el('div', { class: 'empty' }, 'Something went wrong. ',
      el('span', { class: 'small' }, String(err.message || err)));
  }
  for (const t of body.querySelectorAll('table.letters')) {
    const wrap = el('div', { class: 'tablewrap' }); t.replaceWith(wrap); wrap.append(t);
  }
  $('#main').replaceChildren(body);

  const box = $('#q');
  if (box && view === 'search') box.value = p.get('q') || '';
  document.title = p.get('member')
    ? `${byId.get(p.get('member'))?.name || 'Member'} · Letters from Congress (2007-present)`
    : p.get('to') ? `${p.get('to')} · Letters from Congress (2007-present)`
      : '119th Congress (2025-26) · Letters from Congress (2007-present)';
}

async function boot() {
  // Revalidated rather than taken from cache. index.json is rewritten by every
  // build and carries every headline figure on the page, so a stale copy does
  // not degrade the page — it makes it state numbers that are wrong.
  const response = await fetch(INDEX_URL, { cache: 'no-cache' });
  if (!response.ok) throw new Error(`index.json: HTTP ${response.status}`);
  INDEX = await response.json();
  if (INDEX.data_base) DATA_BASE = INDEX.data_base;
  MEMBERS = INDEX.members;
  INDEX.columns.forEach((name, i) => { F[name] = i; });
  byId = new Map(MEMBERS.map(m => [m.id, m]));

  $('#topsearch').addEventListener('submit', e => {
    e.preventDefault();
    const next = new URLSearchParams();
    next.set('view', 'search');
    next.set('q', $('#q').value);
    shown = 0;
    go(next);
  });
  document.addEventListener('click', e => {
    const a = e.target.closest('a[data-view]');
    if (!a) return;
    e.preventDefault();
    const next = new URLSearchParams();
    next.set('view', a.dataset.view);
    shown = 0;
    go(next);
  });
  window.addEventListener('popstate', () => { shown = 0; render(); });
  await render();
}

boot().catch(err => {
  $('#main').replaceChildren(
    el('div', { class: 'empty' }, 'Could not load the letters. ',
      el('span', { class: 'small' }, String(err.message || err))));
});
