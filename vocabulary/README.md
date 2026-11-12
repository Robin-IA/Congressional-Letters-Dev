# The Letters from Congress vocabulary

A controlled vocabulary of its own for the letters members of Congress published
on their websites: **who wrote them, who they were written to, who and what is
named in them, and what they are about.** Started 12 November 2026 from what the
letters already carry; the words inside the letters come next, once the OCR is
done (#40).

It is not LCSH, which was judged not robust enough for letters. Where an outside
authority does know a term, it is linked: Bioguide and Wikidata for members,
Wikidata for federal bodies.

**Generated, not hand-edited.** `python3 build/build_vocabulary.py` rebuilds every
file here from the data and the hand-made tables. To change a term, change its
source: the tables in `build/parse_urls.py` and `build/topics.py`, or the
rosters. A reviewed decision that has no other home will get a file of its own
here; that has not been needed yet.

## What is in it (first build, 12 November 2026)

| Kind | Preferred | Candidates | From |
| --- | ---: | ---: | --- |
| `member` | 1,572 | | every member of the 106th–119th Congresses, by Bioguide ID; 1,571 with a Wikidata item from congress-legislators |
| `organization` | 66 | 142 | agencies and offices from the hand-made recipient tables; candidates from recipients nobody has reviewed |
| `person` | | 131 | recipients named with a title ("Gov Newsom", "Ambassador Lighthizer") |
| `topic` | 64 | | the subjects `build/topics.py` tags letters with |
| `unclassified` | | 977 | recipients the build could not sort: companies (Google, Amazon, Meta), bare surnames (Hagel, Grassley), fragments |

The counts change with every build; `vocabulary.json` and the build's own
summary are the current ones.

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
| `vocabulary.json` | everything above, each term with its relations, for programs |

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
