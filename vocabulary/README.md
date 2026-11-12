# The Letters from Congress vocabulary

A controlled vocabulary of its own for the letters members of Congress published
on their websites: **who wrote them, who they were written to, who and what is
named in them, and what they are about.** Started 12 November 2026 from what the
letters already carry; the words inside the letters come next, once the OCR is
done (#40).

It is not LCSH, which was judged not robust enough for letters. Where an outside
authority does know a term, it is linked: Bioguide and Wikidata for members,
Wikidata for federal bodies.

**Generated, except `hierarchy.csv`.** `python3 build/build_vocabulary.py`
rebuilds every other file here from the data and the hand-made tables. To change
a term, change its source: the tables in `build/parse_urls.py` and
`build/topics.py`, or the rosters. **`hierarchy.csv` is made by hand** and is
read, never written, by the build.

**Browse it** on the home page, under "By topic":
<https://robin-ia.github.io/Explorer-Letters/?view=topics>.

## What is in it (first build, 12 November 2026)

| Kind | Preferred | Candidates | From |
| --- | ---: | ---: | --- |
| `member` | 1,572 | | every member of the 106th–119th Congresses, by Bioguide ID; 1,571 with a Wikidata item from congress-legislators |
| `organization` | 66 | 142 | agencies and offices from the hand-made recipient tables; candidates from recipients nobody has reviewed |
| `person` | | 131 | recipients named with a title ("Gov Newsom", "Ambassador Lighthizer") |
| `topic` | 64 | | the subjects `build/topics.py` tags letters with |
| `unclassified` | | 977 | recipients the build could not sort: companies (Google, Amazon, Meta), bare surnames (Hagel, Grassley), fragments |
| `category` | 25 | | the groups of the hierarchy below |

The counts change with every build; `vocabulary.json` and the build's own
summary are the current ones.

## The hierarchy

Four branches, each alphabetical at every level:

- **Topics**, under eleven subject areas, nested where a topic is part of
  another. Health › Public health › COVID-19, Opioids, Vaccines. Disasters ›
  Wildfires.
- **Organizations**, by the structure of the federal government. Executive
  Office of the President; Executive departments, each with its agencies (the
  FDA, CDC, CMS and NIH under Health and Human Services); Independent agencies
  and commissions; Inspectors general; Congress.
- **Members of Congress**, under Senators and Representatives, by surname. A
  member who served in both chambers is under both.
- **Not yet reviewed**, the candidates: organizations, people, and recipients
  the build could not sort.

`hierarchy.csv` places topics and organizations, one row per term and the term
it sits under (`broader`). A label there that is not yet a term becomes a
category. Members and candidates are placed by rule. A topic or organization
missing from the file is placed at the top of its branch, and the build says
so. `tree.json` is the hierarchy nested and sorted, for the home page.

## Statuses

- **`preferred`**: established. A member by Bioguide ID, or a term someone chose
  by hand in this repository (`source: local`).
- **`candidate`**: found in the data and not yet reviewed. **A candidate is a
  suggestion for a person to accept, never a fact.** That holds for terms and
  for relations alike. A Wikidata match found by searching a name is a lead,
  not an identity. So is a bare surname matched to the only member who had it:
  that suggests "Bush" is Cori Bush, when those letters are almost certainly
  to President Bush.

## The files

| File | One row per |
| --- | --- |
| `terms.csv` | term: `term_id`, `label`, `kind`, `facet`, `status`, `source`, `uri`, `letters`, `note` |
| `relations.csv` | relationship: `term_id`, `relation`, `value`, `status`, `source` |
| `sources.csv` | vocabulary or dataset a term or relation comes from, with its license |
| `hierarchy.csv` | term placed by hand: `term`, `broader` |
| `tree.json` | the hierarchy, nested and sorted alphabetically |
| `vocabulary.json` | everything above, each term with its relations, plus the tree, for programs |

`letters` is how many letters in the published explorers carry the term: the
member wrote them, the organization or person received them, the topic was
tagged. So it agrees with what a visitor sees.

### Term IDs

`M-<bioguide>` for members, `O-` organizations, `P-` people, `T-` topics, `U-`
unclassified, then a slug of the label. Deterministic, so a rebuild gives the
same ID to the same term. When a candidate is reviewed and its label corrected,
its ID changes; references should go through `vocabulary.json`.

### Relations

| Relation | Means |
| --- | --- |
| `broader` | the term or category this one sits under |
| `altLabel` | another name or spelling for the term |
| `abbreviation` | the abbreviation the letters use (FEMA) |
| `exactMatch` | the same thing in another vocabulary: Wikidata, Bioguide |
| `servedIn` | a Congress a member served in |
| `officeHolderName` | a surname by which letters name an office ("Garland" for the Department of Justice) |
| `matchWord` | a word that tags a letter with a topic |
| `taggedAs` | the topic tag an organization's letters carry |
| `possibleMember` | a recipient that may be a member: the only one with that surname (always a candidate) |

## What comes next

1. **Review the candidates**, most-written-to first: accept, correct, merge or
   reject. Decide where a reviewed decision is recorded.
2. **Read the letters' text** once the OCR is in. That covers organizations
   and people named in the body and in the signature block, and the
   co-signers (#41).
3. **Link people and organizations to Wikidata** after review, never before.
4. **Decide whether this moves** to a repository of its own or into
   `metadata-vocabulary`.
