# Contributing to Letters from Congress

Letters from Congress is a collection of letters that members of Congress
published on their own websites, preserved by the Wayback Machine. It is an
experiment from Democracy's Library at the Internet Archive. Corrections and
suggestions from the people who use it make it better, and this page says how
to send them.

There are two ways to reach us:

- **Email** Robin Fay at
  [robin.fay@archive.org](mailto:robin.fay@archive.org?subject=Letters%20from%20Congress),
  who copies each report into a GitHub issue. No account needed.
- **A GitHub issue** in this repository:
  [open one here](https://github.com/Robin-IA/Congressional-Letters-Dev/issues/new/choose).
  It needs a free GitHub account, and anyone can follow the issue as it is
  worked on.

Both end up in the same place. Use whichever suits you.

## Suggesting a correction or an addition

These are the reports that help most, and what to include with each. The issue
forms ask for the same things.

| You found… | Please include |
| --- | --- |
| **A letter with something wrong**: the date, who wrote it, who it was sent to, its subject or its topics | The link to the letter, or the explorer page it is on, and what it should say. If you know how you know (the letter itself says so, say), add that. |
| **Something that is not a letter**: a press release, a page of website furniture, a broken or blank document | The link to it. |
| **A missing letter** | Its address on the member's website, or in the Wayback Machine, if you have it; otherwise the member, roughly when, and who it was to. |
| **A member whose letters are missing or few**: a website we did not find, or letters kept somewhere we did not look | The member, and the website or page where their letters are. |
| **A subject, agency or name the vocabulary lacks or files in the wrong place** | The term, and where you would expect to find it (under which topic or which state, say). |
| **Something hard to use**: a page that does not work with a keyboard or a screen reader, text that is hard to read, a search that does not find what it should | The page, what you did, and what happened. Accessibility problems are fixed first. |
| **An idea** for the explorers: a view, a download, a way to search | What you would want to do with it. |

Every letter here opens as a letter. We cut the collection to that rule, so
some pages whose addresses contain "letter" (press releases about letters,
download pages with no document) are left out on purpose. If you think one of
those should be here, tell us anyway.

### What happens next

Each report becomes a GitHub issue (Robin copies an emailed one in) and is
labelled by kind: `data`, `harvest`, `vocabulary`, `reading`, `dates`, `UX`,
`accessibility` and so on. When the work is done it is labelled
`needs testing` and checked on the published site before the issue is closed.
Nothing on the published sites is edited by hand, so a correction appears after
the next rebuild, usually within a day.

## Changing the code or the data

This is the development repository: the scripts, templates, data, vocabulary,
tests and decisions all live here, and the published sites are built from it
by script. Read [README.md](README.md) for what is here,
[EXPLORERS.md](EXPLORERS.md) for how the sites are built and the decisions
behind them, and [METHODOLOGY.md](METHODOLOGY.md) for the method behind each
step. [CLAUDE.md](CLAUDE.md) holds the working notes: the traps that have cost
real time, and why things are the way they are.

### How to propose a change

1. **Open or find an issue** for it, so the change has a record of why.
2. **Branch from `harvest-member-letters`**, the default branch. (`main` is an
   old scaffold; never base work on it or merge into it.) Fetch first: other
   machines push here often.
3. **Make the change, with a test** where one fits, and run the tests:

   ```bash
   python3 -m unittest discover -s tests
   ```

   Several tests assert that something which looks like debris survives.
   That is the half of cleaning that is easy to get wrong, so read a failing
   test before changing it.
4. **Open a pull request into `harvest-member-letters`**, saying what changed,
   how you checked it, and what is left. Link the issue.
5. **Merging is Robin's call.** A merged change reaches the sites on the next
   build.

### Rules worth knowing before you start

- **Never push to an explorer repository** (`Explorer-Congressional-Letters-<N>`,
  `Explorer-Letters`, `congressional-letters`). They are built output, published
  by `build/publish_explorers.sh` and `build/publish_iac.sh`.
- **The explorer template is `119th/index.html` and `app.js`.** A change to
  either reaches every Congress on the next build. Bump `app.js?v=` in
  `119th/index.html` whenever `app.js` changes, or browsers keep the old copy.
- **The pages are checked against WCAG 2.2 Level AA**, and their footers say so.
  A change to a page needs those checks re-run
  ([security-accessibility-checks.md](security-accessibility-checks.md)).
- **Measure; don't estimate.** A number that goes on a page is computed from the
  data at build time, never typed in. Several typed-in figures here turned out to
  be wrong.
- **Some vocabulary files are rebuilt every time.** `build/build_vocabulary.py`
  rewrites `terms.csv`, `relations.csv`, `sources.csv`, `tree.json` and
  `vocabulary.json`, so an edit to them is lost; change their sources instead.
  Where a term sits is `vocabulary/hierarchy.csv`, made by hand.
  `vocabulary/README.md` says which file holds what.
- **Do not run anything that fetches from the Wayback Machine** beside the
  renderer or a harvest. They share one rate limit.
- **GitHub Pages builds at most ten times an hour from a branch**, and every push
  counts. Batch your commits.

## Questions

Ask in an issue or by email. If you are not sure whether something is a mistake,
send it anyway: most of what has been fixed here was found by someone asking.
