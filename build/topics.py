#!/usr/bin/env python3
"""A controlled vocabulary of subjects and agencies, and a tagger for it.

Why the raw description is not enough
-------------------------------------
The description beside each letter is cut from its file name, and file names
are written by staffers in a hurry. Two real examples::

    Ne support wildfires
    Wildfire disasters fmags hmgp

The first is one topic wrapped in a state abbreviation and a verb; the second
is two topics followed by the acronyms for FEMA's Fire Management Assistance
Grants and Hazard Mitigation Grant Program. A reader wants "Wildfires" and
"Disasters", not either of those strings.

So each letter is also tagged against a vocabulary. The tags are what search
matches and what the interface can show; the raw description stays as a
fallback for anything the vocabulary does not cover.

Why a vocabulary rather than the frequent words
-----------------------------------------------
Ranking the words that actually appear puts "media", "document", "evo" and
"cache" at the top — path furniture — alongside generic verbs like
"requesting" and the surnames of prolific senders. Frequency finds candidates;
it cannot tell a subject from a directory name. Every term here was chosen,
and every one is checked against the corpus by ``verify``.

Singular and plural are one term. So are an agency's abbreviation and its
name: a letter about FEMA is found by searching either, which is the point of
cross-indexing them.
"""

from __future__ import annotations

import re
import sys

# Suffix rules that do not mangle the words this corpus actually contains.
# A naive "drop a trailing s" turns nexus into nexu and coronavirus into
# coronaviru, both of which appeared in the first pass over real subjects.
_KEEP_WHOLE = ("us", "is", "ss", "as", "ous")
# Whole words kept as they are. "chips" is the semiconductor CHIPS Act; folded
# to "chip" it matched Medicaid's "chip" (the Children's Health Insurance
# Program) and tagged 77 CHIPS letters Medicaid (14 November 2026).
_KEEP_EXACT = {"chips"}


def singular(word: str) -> str:
    """Fold a plural onto its singular, conservatively."""
    w = word.lower()
    if w in _KEEP_EXACT or any(w.endswith(suffix) for suffix in _KEEP_WHOLE):
        return w
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 4 and w.endswith("ches") or w.endswith("shes") or w.endswith("xes"):
        return w[:-2]
    if len(w) > 3 and w.endswith("s"):
        return w[:-1]
    return w


# ---------------------------------------------------------------- the subjects
#
# canonical label -> the forms that should find it. Forms are matched after
# the same singular() fold, so "wildfires" finds "wildfire" without listing it.
SUBJECTS: dict[str, tuple[str, ...]] = {
    # health
    "COVID-19": ("covid", "covid-19", "covid19", "coronavirus", "pandemic",
                 "sars-cov-2"),
    "Vaccines": ("vaccine", "vaccination", "immunization", "immunisation"),
    "Opioids": ("opioid", "fentanyl", "overdose", "naloxone", "oxycontin"),
    "Medicare": ("medicare",),
    "Medicaid": ("medicaid", "chip"),
    "Affordable Care Act": ("affordable care act", "obamacare", "aca", "ppaca"),
    "Diabetes": ("diabetes", "diabetic", "prediabetes", "insulin"),
    "Mental health": ("mental health", "suicide", "behavioral health"),
    "Prescription drugs": ("prescription", "drug pricing", "insulin",
                           "pharmaceutical", "pbm"),
    "Tobacco": ("tobacco", "cigarette", "vaping", "e-cigarette", "nicotine"),
    "Health care": ("health care", "healthcare", "hospital", "aca",
                    "affordable care"),
    "Abortion": ("abortion", "reproductive", "mifepristone", "roe"),
    "Public health": ("public health", "disease", "outbreak"),

    # environment and energy
    "Wildfires": ("wildfire", "forest fire", "fire season"),
    "Climate": ("climate", "greenhouse gas", "emissions", "carbon",
                "global warming"),
    "Water": ("water", "drinking water", "watershed", "drought", "aquifer"),
    "PFAS": ("pfas", "forever chemical", "pfoa", "pfos"),
    "Pollution": ("pollution", "contamination", "toxic", "superfund",
                  "clean air"),
    "Oil and gas": ("oil and gas", "natural gas", "oil company", "petroleum",
                    "gasoline", "gas price", "refinery", "fracking", "offshore drilling"),
    "Energy": ("energy", "electricity", "grid", "pipeline", "oil", "gas",
               "renewable", "solar", "wind power"),
    "Nuclear": ("nuclear", "radioactive", "uranium"),
    "Public lands": ("public land", "national park", "wilderness", "blm land",
                     "monument"),
    "Wildlife": ("wildlife", "endangered species", "habitat", "fishery",
                 "salmon"),
    "Disasters": ("disaster", "hurricane", "flood", "tornado", "earthquake",
                  "fema assistance", "emergency declaration"),

    # economy
    "Taxes": ("tax", "taxation", "irs audit", "tax credit"),
    "Tariffs": ("tariff", "trade war", "section 232", "section 301"),
    "Trade": ("trade", "export", "import", "usmca", "wto"),
    "Inflation": ("inflation", "cost of living", "price gouging", "prices"),
    "Banking": ("bank", "banking", "credit union", "fdic insurance"),
    "Housing": ("housing", "mortgage", "rent", "homeless", "eviction",
                "housing cost", "cost of housing", "unhoused"),
    "Student loans": ("student loan", "student debt", "tuition", "pell"),
    "Small business": ("small business", "ppp", "sba loan"),
    "Jobs": ("jobs", "unemployment", "workforce", "labor", "wage", "union"),
    "Social Security": ("social security", "ssi", "ssdi"),
    "Investing": ("investing", "investor", "mutual fund", "brokerage",
                  "retirement savings", "retirement account", "index fund"),
    "Credit reporting": ("credit report", "credit reporting", "credit score",
                         "credit bureau", "consumer reporting agency"),
    "Crypto": ("crypto", "cryptocurrency", "bitcoin", "stablecoin", "ftx"),

    # security and justice
    "Immigration": ("immigration", "immigrant", "asylum", "refugee", "daca",
                    "deportation", "visa", "border wall"),
    "Border": ("border", "border security", "migrant"),
    # The ATF's name is read whole, so its "Tobacco" is not the topic.
    "Guns": ("gun", "firearm", "atf rule", "assault weapon", "gun violence",
             "alcohol tobacco firearms and explosives"),
    "Policing": ("police", "policing", "law enforcement"),
    "Prisons": ("prison", "incarceration", "bureau of prisons", "inmate"),
    "Civil rights": ("civil right", "voting right", "discrimination",
                     "disability right"),
    "Elections": ("election", "voting", "ballot", "redistricting",
                  "election security"),
    "Privacy": ("privacy", "surveillance", "data broker", "fisa"),
    "Cybersecurity": ("cyber", "cybersecurity", "ransomware", "hacking",
                      "data breach"),
    "Oversight": ("oversight", "investigation", "subpoena", "inspector general",
                  "whistleblower", "foia"),
    "Ethics": ("ethics", "conflict of interest", "insider trading",
               "stock trading"),

    # defence and foreign
    "Defense": ("defense", "pentagon", "military", "armed force",
                "national defense"),
    "Veterans": ("veteran", "va care", "gi bill"),
    "Ukraine": ("ukraine", "ukrainian"),
    "Russia": ("russia", "russian", "putin"),
    "China": ("china", "chinese", "ccp", "taiwan"),
    "Israel and Gaza": ("israel", "gaza", "palestinian", "hamas"),
    "Iran": ("iran", "iranian"),
    "Afghanistan": ("afghanistan", "afghan"),
    "Foreign aid": ("foreign aid", "usaid", "humanitarian assistance"),

    # infrastructure and services
    "Broadband": ("broadband", "internet access", "rural broadband",
                  "digital divide"),
    "Transportation": ("transportation", "highway", "transit", "rail",
                       "transportation cost", "cost of transportation",
                       "amtrak", "bridge"),
    # Amtrak is all three: Transportation, Railroads, Public transportation.
    "Railroads": ("railroad", "railway", "rail", "amtrak", "passenger rail",
                  "freight rail", "rail safety"),
    "Public transportation": ("public transportation", "public transit",
                              "transit", "amtrak", "commuter rail", "subway",
                              "bus service"),
    "Cars": ("car", "automobile", "automaker", "auto industry", "vehicle recall"),
    "Aviation": ("aviation", "airline", "airport", "faa certification",
                 "boeing"),
    "Postal Service": ("postal", "usps delay", "mail delivery"),
    "Agriculture": ("agriculture", "farm", "farmer", "crop", "livestock",
                    "snap benefit", "farm bill"),
    "Education": ("education", "school", "teacher", "student", "university",
                  "title ix"),
    "Childcare": ("childcare", "child care", "head start"),
    "Technology": ("artificial intelligence", "social media", "algorithm",
                   "big tech", "antitrust"),
    "Media": ("media platform", "social media", "youtube", "streaming",
              "television", "tv network"),
    "News media": ("news media", "journalist", "journalism", "newspaper",
                   "broadcaster", "cnn"),
    "Telecom": ("spectrum", "telecom", "robocall", "net neutrality"),

    # government operations
    "Appropriations": ("appropriation", "funding request", "budget request",
                       "continuing resolution", "shutdown", "earmark"),
    "Federal workforce": ("federal employee", "federal worker", "rif",
                          "hiring freeze", "telework"),
    "Nominations": ("nomination", "nominee", "confirmation"),
    "Regulation": ("rulemaking", "proposed rule", "comment period",
                   "regulatory"),
    # Assigned by hand only (vocabulary/letter-topics.csv), from reading
    # the letter: no match words, because the obvious ones mislead. 'budget'
    # names the Office of Management and Budget and the Congressional Budget
    # Office; 'shipping' is any parcel. Added 14 November 2026 (#143).
    "Budgets": (),
    "Shipping": (),
    # Costs and sub-topics. Each phrase is also a word of its parent, so a
    # letter gets both: see "gun violence" under Guns. Without that the
    # longer phrase wins alone and the parent is lost.
    "Housing costs": ("housing cost", "cost of housing", "rent burden",
                      "rental cost", "rising rent"),
    "Unhoused": ("unhoused", "homeless", "homelessness", "encampment"),
    "Health premiums": ("health premium", "insurance premium",
                        "premium increase", "premium cost"),
    "Transportation costs": ("transportation cost", "transit fare",
                             "cost of transportation", "fuel cost"),
    # The bare word "affordable" is left out: 976 letters use it, many of
    # them about the Affordable Care Act or affordable housing, which are
    # their own topics. "affordability" and "cost of living" are the ones
    # that mean this.
    # "rising cost" is left out: it begins one word earlier than "cost of
    # living" and shadowed it, so a letter about the rising cost of living
    # got Affordability and not Cost of living.
    "Affordability": ("affordability", "unaffordable", "household cost"),
    "Cost of living": ("cost of living", "cost-of-living adjustment",
                       "col a increase", "purchasing power"),
    # The armed services, under Defense. The parent says a letter is about
    # defence; these say which service. Each uses its own name rather than a
    # own name. "navy" and "army" are kept bare: letters say "the Navy", not
    # "the United States Navy", and the near-misses -- the Navy Yard, the Army
    # Corps of Engineers -- belong to those services anyway. Army Corps keeps
    # its own agency tag as well.
    "Air Force": ("air force", "department of the air force"),
    "Army": ("army", "department of the army", "army national guard"),
    # Not "marines": tag() singularises it to "marine", which tagged marine
    # sanctuaries, monuments and mammals as the Corps (60 of 76 letters,
    # measured 14 Nov 2026). The dozen saying only "Marines" get hand rows.
    "Marine Corps": ("marine corps", "usmc"),
    "Navy": ("navy", "department of the navy", "naval"),
    "Space Force": ("space force", "united states space force"),
    "Social media": ("social media", "content moderation", "section 230",
                     "platform moderation", "online platform"),
    "Data centers": ("data center", "data centre", "hyperscale",
                     "server farm"),
    # Under Guns. The parent keeps the broad words; these take the argument,
    # so a letter can be about guns and about which side of it.
    "Gun control": ("gun control", "gun safety", "background check",
                    "assault weapons ban", "red flag law", "magazine ban",
                    "gun buyback"),
    "Gun rights": ("second amendment", "gun rights", "right to keep and bear arms",
                   "concealed carry", "law-abiding gun owner"),
    "Gun violence": ("gun violence", "firearm death", "gun homicide",
                     "shooting death", "gun suicide"),
    "Mass shootings": ("mass shooting", "school shooting", "active shooter",
                       "mass casualty shooting"),
    "Cannabis": ("cannabis", "marijuana", "hemp"),
    # Not the bare word "judiciary": it names the Judiciary Committees, and
    # 320 of 382 letters it tagged were committee correspondence (Peace
    # Corps oversight, H-1B, ATF grants), not the courts. Measured 14 Nov 2026.
    # Courts, not "Judiciary": the letters name particular courts far more
    # often than they discuss the branch. Sub-topics can be split out of this
    # later -- Supreme Court, circuit courts, immigration courts -- without
    # the parent having to be renamed first.
    #
    # The bare words are deliberately absent. "judiciary" tagged the Judiciary
    # Committees' correspondence as the courts: 382 letters, about 320 of them
    # committee files; without it, 62, every sampled one about courts or judges
    # (the Mac, #147). "court" alone appears in any letter about litigation.
    "Courts": ("judicial", "federal judge", "federal court",
               "circuit court", "district court", "supreme court",
               "court of appeals", "appellate court"),
    "Violence against government officials": (
        "violence against judges", "violence against public officials",
        "violence against government officials", "violence against election",
        "threats against judges", "threats against public officials",
        "threats against election officials", "threats against members of congress",
        "political violence", "threatened with violence"),

    # Named laws a letter cites. The name is the match word, so these are
    # found by rule as well as assigned by hand. Counted across all 17,519
    # letters with text on 14 November 2026; each is cited by at least six.
    "Jones Act": ('jones act', 'merchant marine act'),   # 10 letters
    "CARES Act": ('cares act', 'coronavirus aid, relief, and economic security'),   # 349 letters
    "National Defense Authorization Act": ('national defense authorization', 'ndaa'),   # 306 letters
    "Clean Water Act": ('clean water act',),   # 240 letters
    "Omnibus Crime Control and Safe Streets Act": ('safe streets act', 'omnibus crime control'),   # 185 letters
    "Immigration and Nationality Act": ('immigration and nationality act',),   # 165 letters
    "Freedom of Information Act": ('freedom of information act', 'foia'),   # 137 letters
    "Clean Air Act": ('clean air act',),   # 131 letters
    "Safe Drinking Water Act": ('safe drinking water act',),   # 131 letters
    "Stafford Act": ('stafford act', 'stafford disaster relief'),   # 130 letters
    "National Environmental Policy Act": ('national environmental policy act', 'nepa'),   # 119 letters
    "American Rescue Plan Act": ('american rescue plan',),   # 116 letters
    "Inflation Reduction Act": ('inflation reduction act',),   # 116 letters
    "Endangered Species Act": ('endangered species act',),   # 110 letters
    "Water Resources Development Act": ('water resources development act', 'wrda'),   # 97 letters
    "Dodd-Frank Act": ('dodd-frank', 'dodd frank'),   # 90 letters
    "Civil Rights Act": ('civil rights act',),   # 54 letters
    "Higher Education Act": ('higher education act',),   # 53 letters
    "Defense Production Act": ('defense production act',),   # 53 letters
    "Administrative Procedure Act": ('administrative procedure act',),   # 51 letters
    "American Recovery and Reinvestment Act": ('american recovery and reinvestment', 'arra'),   # 47 letters
    "Families First Coronavirus Response Act": ('families first coronavirus response',),   # 45 letters
    "Americans with Disabilities Act": ('americans with disabilities act',),   # 44 letters
    "Controlled Substances Act": ('controlled substances act',),   # 43 letters
    "Social Security Act": ('social security act',),   # 42 letters
    "Elementary and Secondary Education Act": ('elementary and secondary education act', 'esea'),   # 38 letters
    "Voting Rights Act": ('voting rights act',),   # 32 letters
    "Congressional Review Act": ('congressional review act',),   # 32 letters
    "International Emergency Economic Powers Act": ('international emergency economic powers', 'ieepa'),   # 32 letters
    "Comprehensive Addiction and Recovery Act": ('comprehensive addiction and recovery',),   # 30 letters
    "CHIPS and Science Act": ('chips and science act', 'chips act'),   # 29 letters
    "Antiquities Act": ('antiquities act',),   # 25 letters
    "Secure Rural Schools": ('secure rural schools',),   # 16 letters
    "21st Century Cures Act": ('21st century cures',),   # 13 letters
    "Wildfire Disaster Funding Act": ('wildfire disaster funding act',),   # 6 letters
    # Read from the letters themselves, November 2026. Every term below was
    # needed by a letter in the 145-letter class-noun pool (#164): the subject
    # was plainly on the page and no existing term carried it.
    #
    # Where a parent and a named law share a subject, the parent repeats the
    # law's phrase, because tag() keeps only the longest phrase at a position:
    # "Surveillance" lists "foreign intelligence surveillance act" so a FISA
    # letter carries both, and "Higher education" lists "higher education act"
    # for the same reason.

    # Read from the agency letters of November 2026. Each of these was a
    # subject I had been bending an existing term around -- Cuba as
    # "Foreign aid", drones as "Aviation", pensions as "Investing" -- which
    # is the thing the vocabulary rule exists to stop. The count beside each
    # is the letters mentioning it three or more times, the bar the text
    # rules already use.
    "Mexico": ('mexico', 'mexican'),
    "Sanctions": ('sanctions', 'sanctioned entity', 'ofac'),
    "National parks": ('national park', 'park service'),
    "Solar power": ('solar', 'photovoltaic'),
    "Retirement": ('pension', 'pensions', '401(k)', 'retirement savings', 'annuitant'),
    "Drones": ('drone', 'drones', 'unmanned aerial', 'unmanned aircraft'),
    "Firefighters": ('firefighter', 'fire brigade', 'volunteer fire'),
    "Electric grid": ('electric grid', 'transmission line', 'grid reliability'),
    "Hydrogen": ('hydrogen',),
    "Cuba": ('cuba', 'cuban'),
    "Whales": ('whale', 'whales', 'right whale', 'humpback'),
    "Shipbuilding": ('shipbuilding', 'shipyard'),
    "Title X": ('title x',),
    "Afghan refugees": ('afghan nationals', 'afghan refugees', 'afghan allies'),
    "Wild horses": ('wild horse', 'wild horses', 'burro', 'burros'),
    "Hate crimes": ('hate crime', 'hate crimes'),
    "Nuclear waste": ('nuclear waste', 'spent nuclear fuel', 'spent fuel',
                      'radioactive waste', 'yucca mountain'),
    "Child labor": ('child labor', 'child labour'),
    "Artificial intelligence": ('artificial intelligence', 'generative ai', 'ai model',
                                'deepfake', 'large language model'),
    "Chemical weapons": ('chemical weapon', 'nerve agent', 'sarin', 'chemical attack'),
    "Syria": ('syria', 'syrian', 'assad'),
    "Venezuela": ('venezuela', 'venezuelan'),
    "War powers": ('war powers', 'authorization for use of military force',
                   'declare war'),
    "Government shutdown": ('government shutdown', 'federal shutdown',
                            'lapse in appropriations', 'furloughed'),
    "Senate procedure": ('parliamentarian', 'filibuster', 'cloture', 'senate rule'),
    "Impeachment": ('impeachment', 'impeach'),
    "Space program": ('nasa', 'space shuttle', 'astronaut', 'space station',
                      'space telescope'),
    "Scientific research": ('scientific research', 'research funding',
                            'research workforce', 'national science foundation',
                            'principal investigator'),
    "Ports": ('port authority', 'seaport', 'cargo port'),
    "Nutrition assistance": ('snap benefit', 'supplemental nutrition assistance',
                             'food stamp', 'school meal', 'child nutrition',
                             'food bank', 'wic program'),
    "Food safety": ('food safety', 'meat inspection', 'food safety and inspection'),
    "Fisheries": ('fishery', 'fisheries', 'fishermen', 'lobster', 'aquaculture'),
    "Family planning": ('family planning', 'contraception', 'contraceptive', 'title x'),
    "Hyde Amendment": ('hyde amendment',),
    "Maternal health": ('maternal health', 'postpartum', 'pregnant worker',
                        'pregnancy discrimination'),
    "Medical research": ('medical research', 'biomedical research', 'clinical trial',
                         'national institutes of health'),
    "Telehealth": ('telehealth', 'telemedicine'),
    "Hospitals": ('hospital',),
    "Dental care": ('dental', 'oral health'),
    "Energy efficiency": ('energy efficiency', 'energy efficient', 'weatherization'),
    "Drought": ('drought',),
    # Not the bare word "ocean": it is a place name as often as a subject --
    # Ocean County, Ocean City, Ocean Bay, Ocean Shores, Ocean Boulevard, about
    # 15 of the 44 letters it tagged (measured 14 Nov 2026). These phrases are
    # the ones the letters about the sea itself use.
    "Oceans": ("ocean policy", "national ocean policy", "ocean program",
               "ocean data", "ocean carbon", "ocean acidification",
               "ocean caucus", "ocean conference", "ocean disposal",
               "ocean observation", "ocean obs", "ocean task force",
               "ocean priority", "ocean health", "ocean conservation",
               "coastal ocean", "ocean and coastal", "atlantic ocean",
               "pacific ocean", "arctic ocean", "coastal restoration",
               "marine ecosystem"),
    "Flooding": ('flooding', 'floodwater', 'flood damage'),
    "Hurricanes": ('hurricane',),
    "Higher education": ('higher education', 'higher education act', 'postsecondary',
                         'community college', 'historically black college', 'hbcu',
                         'minority serving institution'),
    "Title IX": ('title ix',),
    "College sports": ('college athletic', 'college sport', 'student athlete',
                       'name, image, and likeness'),
    "Museums": ('smithsonian', 'museum'),
    "Supply chains": ('supply chain',),
    "Gig work": ('gig worker', 'gig economy', 'independent contractor'),
    "Unemployment": ('unemployment insurance', 'unemployment benefit', 'jobless claim'),
    "Nonprofits": ('nonprofit', 'non-profit', 'charitable organization'),
    "Restaurants": ('restaurant',),
    "Child tax credit": ('child tax credit',),
    "Low-Income Housing Tax Credit": ('low-income housing tax credit', 'housing credit',
                                      'lihtc'),
    "Build Back Better Act": ('build back better',),
    "HEROES Act": ('heroes act',),
    "Surveillance": ('surveillance', 'section 702', 'warrantless', 'wiretap',
                     'foreign intelligence surveillance act', 'fisa'),
    "Foreign Intelligence Surveillance Act": ('foreign intelligence surveillance act',
                                              'fisa'),
    "Domestic violence": ('domestic violence', 'sexual assault',
                          'intimate partner violence', 'violence against women'),
    "Native Americans": ('native american', 'american indian', 'alaska native',
                         'tribal government', 'indigenous women'),
    "Drug trafficking": ('drug trafficking', 'drug trafficker', 'drug cartel',
                         'high intensity drug trafficking'),
    # Crime and demographic terms, measured 15 Nov 2026 against the
    # 11,272 letters we hold text for and checked against LCDGT and
    # FAST before adoption (Robin). "Hispanic Americans" is LCDGT's
    # own authorized form, not "LatinX".
    # Plain words, not regular expressions: tag() matches whole words after
    # singular() (so "americans" finds "american" and "disabilities"
    # "disability"), and a pattern like 'americans?' never matches. Not bare
    # "senior", which is senior officials as often as older people.
    "Crime": ('crime', 'violent crime', 'criminal justice'),
    "Sexual assault": ('sexual assault', 'sexual abuse', 'rape', 'rape kit', 'sexual violence'),
    "Human trafficking": ('human trafficking', 'sex trafficking', 'trafficking victim'),
    "Child abuse": ('child abuse', 'child sexual abuse', 'abused children', 'child exploitation'),
    "Victim services": ('victims of crime act', 'victim services', 'victim compensation'),
    "Asian Americans": ('asian american', 'asian-american', 'aapi', 'pacific islander'),
    "Black Americans": ('african american', 'african-american', 'black american'),
    "Hispanic Americans": ('hispanic american', 'hispanic-american', 'latino', 'latina'),
    "LGBTQ people": ('lgbtq', 'transgender', 'same-sex'),
    "People with disabilities": ('people with disability', 'individuals with disability',
                                 'persons with disability', 'americans with disability'),
    "Older adults": ('older adult', 'older american', 'older people', 'senior citizen'),

}

# ------------------------------------------------------------- the agencies
#
# Abbreviation and full name index to the same label, so either finds the
# letter. Only agencies that actually appear as SUBJECTS of letters are here;
# the recipient vocabulary in parse_urls.py is a separate, larger list.
AGENCIES: dict[str, tuple[str, ...]] = {
    "FEMA": ("fema", "federal emergency management agency"),
    "EPA": ("epa", "environmental protection agency"),
    "FDA": ("fda", "food and drug administration"),
    "CDC": ("cdc", "centers for disease control"),
    "CMS": ("cms", "centers for medicare and medicaid services"),
    "HHS": ("hhs", "health and human services"),
    "DHS": ("dhs", "homeland security"),
    "DOJ": ("doj", "justice department", "department of justice"),
    "FBI": ("fbi", "federal bureau of investigation"),
    "ICE": ("ice detention", "immigration and customs enforcement"),
    "CBP": ("cbp", "customs and border protection"),
    "USDA": ("usda", "department of agriculture"),
    "VA": ("veterans affairs", "va hospital"),
    "DOD": ("dod", "department of defense"),
    "DOE": ("doe", "department of energy"),
    "DOT": ("dot", "department of transportation"),
    "FAA": ("faa", "federal aviation administration"),
    "FCC": ("fcc", "federal communications commission"),
    "FTC": ("ftc", "federal trade commission"),
    "SEC": ("sec filing", "securities and exchange commission"),
    "IRS": ("irs", "internal revenue service"),
    "SSA": ("ssa", "social security administration"),
    "HUD": ("hud", "housing and urban development"),
    "USPS": ("usps", "postal service"),
    "NIH": ("nih", "national institutes of health"),
    "NOAA": ("noaa", "national oceanic and atmospheric"),
    "GAO": ("gao", "government accountability office"),
    "OMB": ("omb", "office of management and budget"),
    "SBA": ("sba", "small business administration"),
    "NASA": ("nasa",),
    "Army Corps": ("army corps", "usace", "corps of engineers"),
    "Federal Reserve": ("federal reserve", "the fed"),
}


# Phrases that contain a topic's word but are not that topic. Matched like
# any other phrase -- the longest wins -- and they tag nothing, so their words
# are used up: "new mexico" is a state, and its "mexico" must not tag Mexico.
# A match word cannot say "but not in this phrase"; a shield can. Each entry
# says what it shields and why (measured 14 November 2026).
SHIELDS: tuple[str, ...] = (
    "new mexico", "new mexican",       # the state, not Mexico: 11 of 170 letters
    "mexican american",                # an American community, not Mexico: 4
    # The same check run over the other 17 terms of #188. Measured across the
    # letters we hold text for; only these four matched something that is not
    # the subject.
    "solarwinds",                      # the company in the 2020 breach, not solar: 3
    "solar system",                    # astronomy, not solar power: 3
    "hydrogen sulfide",                # a pollutant, not hydrogen as fuel: 5
    "cuban american",                  # an American community, not Cuba: 2
    # Medicaid's "chip" is the Children's Health Insurance Program; these
    # chips are not (measured 14 November 2026: 124 letters tagged Medicaid
    # without the word, most of them semiconductors or Rep. Chip Roy).
    "chip roy", "rep chip",            # Representative Chip Roy (TX-21), and
    "chip tx", "chip austin", "u s chip",   # his own files' names
    "semiconductor chip", "memory chip", "ai chip", "computer chip",
    "chip manufacturing", "chip vulnerability", "chip export", "chip shortage",
    "amtrak chip",                     # an Amtrak grant program
)


def _build_index() -> dict[str, list[tuple[str, str]]]:
    """first-word -> [(normalised phrase, label)], longest phrases first.
    A shield's label is None: it matches, and tags nothing."""
    index: dict[str, list[tuple[str, str]]] = {}
    for form in SHIELDS:
        words = [singular(w) for w in form.split()]
        index.setdefault(words[0], []).append((" ".join(words), None))
    for mapping in (SUBJECTS, AGENCIES):
        for label, forms in mapping.items():
            for form in forms:
                words = [singular(w) for w in form.split()]
                if not words:
                    continue
                index.setdefault(words[0], []).append((" ".join(words), label))
    for key in index:
        index[key].sort(key=lambda pair: -len(pair[0].split()))
    return index


INDEX = _build_index()
WORD = re.compile(r"[a-z][a-z0-9'-]*")


def tag(text: str, limit: int = 8) -> list[str]:
    """The vocabulary terms a description is about, most specific first.

    Multi-word forms win over single words at the same position, so
    "social security" is one tag rather than two unrelated ones.

    The limit was 4 and is 8 (Robin, 14 November 2026). Four was not enough:
    a letter on Payments in Lieu of Taxes is about taxes, public lands and
    appropriations before anything specific to it is reached, and letters
    read by hand routinely earn three or four topics of their own.
    """
    if not text:
        return []
    words = [singular(w) for w in WORD.findall(text.lower())]
    found: list[str] = []
    i = 0
    while i < len(words):
        hit = None
        for phrase, label in INDEX.get(words[i], ()):
            size = len(phrase.split())
            # Every label of the longest matching phrase: "amtrak" is
            # Transportation, Railroads and Public transportation at once.
            if hit is None and " ".join(words[i:i + size]) == phrase:
                hit = phrase
            if phrase == hit and label is not None and label not in found:
                found.append(label)
        if hit:
            i += len(hit.split()) - 1
        i += 1
    return found[:limit]


def verify(samples: list[str]) -> dict[str, int]:
    """How often each term fires, so a term that never fires can be cut."""
    counts = {label: 0 for label in list(SUBJECTS) + list(AGENCIES)}
    for text in samples:
        for label in tag(text, limit=99):
            counts[label] += 1
    return counts


if __name__ == "__main__":
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    texts = []
    for path in (root / "119th" / "payload" / "member").glob("*.json"):
        for row in json.loads(path.read_text(encoding="utf-8")):
            if row[6]:
                texts.append(row[6])
    print(f"{len(texts):,} descriptions", file=sys.stderr)
    counts = verify(texts)
    tagged = sum(1 for t in texts if tag(t))
    print(f"{tagged:,} tagged ({tagged / max(1, len(texts)) * 100:.1f}%)",
          file=sys.stderr)
    dead = [label for label, n in counts.items() if n == 0]
    print(f"terms that never fire: {len(dead)}  {dead[:12]}", file=sys.stderr)
    for label, n in sorted(counts.items(), key=lambda kv: -kv[1])[:30]:
        print(f"  {n:>6}  {label}", file=sys.stderr)
