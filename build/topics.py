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
    # Under Elections (hierarchy.csv), added at Robin's request 15 November
    # 2026. The longest phrase wins, so "absentee ballot" is Voting alone.
    "Campaign financing": ("campaign finance", "campaign financing",
                           "campaign contribution", "campaign spending",
                           "political contribution", "super pac", "dark money",
                           "disclose act", "federal election commission"),
    "Citizens United": ("citizens united",),
    "Electoral College": ("electoral college", "electoral vote",
                          "electoral count", "faithless elector"),
    "Voting": ("voter registration", "vote by mail", "voting by mail",
               "mail-in ballot", "mail-in voting", "absentee ballot",
               "early voting", "polling place", "polling location", "voter id",
               "voter roll", "provisional ballot", "ballot access",
               "access to the ballot", "same-day registration"),
    "Election integrity": ("election integrity", "election security",
                           "election interference", "election fraud",
                           "voter fraud", "voting machine", "voting system",
                           "election infrastructure", "election audit",
                           "post-election audit", "election official"),
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
    # Requested by Robin, 15 November 2026, for the airline-CEO letters of
    # Daines and Tester. No match words: "airline" already tags Aviation, and
    # a state's name is on every letterhead from that state, so tagging by
    # word would file each senator's whole output under the home state.
    "Airlines": (),
    "Tennessee": (),
    "Montana": (),
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
    # Laws and bills the readers left out because the vocabulary lacked them
    # (#1324, 17 November 2026): 181 named in reading notes. One letter is
    # enough for a subject (#81). The count is letters whose text names the
    # law; the parent in LAW_PARENTS is tagged with it.
    'Consolidated Appropriations Act': ('consolidated appropriations act',),   # 888 letters
    'Infrastructure Investment and Jobs Act': ('infrastructure investment and jobs act', 'bipartisan infrastructure law', 'bipartisan infrastructure bill', 'bipartisan infrastructure deal', 'iija'),   # 704 letters
    'Tax Cuts and Jobs Act': ('tax cuts and jobs act', 'tcja'),   # 205 letters
    'JCPOA': ('jcpoa', 'joint comprehensive plan of action', 'iran nuclear deal'),   # 201 letters
    'NAFTA': ('nafta', 'north american free trade agreement'),   # 197 letters
    'Public Health Service Act': ('public health service act',),   # 194 letters
    'One Big Beautiful Bill Act': ('one big beautiful bill',),   # 179 letters
    'FAA Reauthorization Act': ('faa reauthorization',),   # 144 letters
    'Fair Labor Standards Act': ('fair labor standards act',),   # 143 letters
    'Federal Food, Drug, and Cosmetic Act': ('food drug and cosmetic act',),   # 142 letters
    'Privacy Act': ('privacy act of', 'the privacy act'),   # 124 letters
    'Bipartisan Budget Act': ('bipartisan budget act',),   # 119 letters
    'Global Magnitsky Act': ('magnitsky',),   # 114 letters
    'Individuals with Disabilities Education Act': ('individuals with disabilities education act',),   # 111 letters
    'Budget Control Act': ('budget control act',),   # 110 letters
    'Comprehensive Environmental Response, Compensation, and Liability Act': ('cercla', 'comprehensive environmental response compensation'),   # 108 letters
    'Violence Against Women Act': ('violence against women act', 'violence against women reauthorization', 'vawa'),   # 107 letters
    'Foreign Agents Registration Act': ('foreign agents registration act', 'fara'),   # 106 letters
    'USA PATRIOT Act': ('patriot act',),   # 106 letters
    'Energy Policy Act': ('energy policy act',),   # 98 letters
    'Trafficking Victims Protection Reauthorization Act': ('trafficking victims protection', 'tvpra'),   # 96 letters
    'Rehabilitation Act': ('rehabilitation act',),   # 93 letters
    'False Claims Act': ('false claims act',),   # 90 letters
    'SUPPORT for Patients and Communities Act': ('support for patients and communities act', 'support act'),   # 90 letters
    'Bank Secrecy Act': ('bank secrecy act',),   # 88 letters
    'Energy Independence and Security Act': ('energy independence and security act',),   # 88 letters
    'Employee Retirement Income Security Act': ('employee retirement income security act', 'erisa'),   # 85 letters
    'Trade Act': ('trade act of',),   # 85 letters
    'Every Student Succeeds Act': ('every student succeeds act', 'essa'),   # 81 letters
    'Disaster Recovery Reform Act': ('disaster recovery reform act',),   # 79 letters
    'Fair Housing Act': ('fair housing act',),   # 78 letters
    'Paycheck Protection Program and Health Care Enhancement Act': ('paycheck protection program and health care enhancement act',),   # 77 letters
    'Hatch Act': ('hatch act',),   # 74 letters
    'Magnuson-Stevens Act': ('magnuson-stevens', 'magnuson stevens'),   # 71 letters
    'Impoundment Control Act': ('impoundment control act',),   # 68 letters
    'Family Smoking Prevention and Tobacco Control Act': ('family smoking prevention and tobacco control act',),   # 67 letters
    'VA MISSION Act': ('va mission act', 'mission act of'),   # 63 letters
    'Bipartisan Safer Communities Act': ('bipartisan safer communities act',),   # 62 letters
    'PACT Act': ('honoring our pact act', 'pact act'),   # 60 letters
    'Arms Trade Treaty': ('arms trade treaty',),   # 58 letters
    "Countering America's Adversaries Through Sanctions Act": ('caatsa', "countering america's adversaries through sanctions act", 'countering america s adversaries through sanctions act'),   # 58 letters
    'Workforce Innovation and Opportunity Act': ('workforce innovation and opportunity act', 'wioa'),   # 58 letters
    'Coronavirus Preparedness and Response Supplemental Appropriations Act': ('coronavirus preparedness and response supplemental appropriations act',),   # 57 letters
    'Full-Year Continuing Appropriations and Extensions Act': ('full-year continuing appropriations and extensions act',),   # 56 letters
    'Great American Outdoors Act': ('great american outdoors act',),   # 55 letters
    'National Firearms Act': ('national firearms act',),   # 53 letters
    'Dream Act': ('dream act', 'american dream and promise act', 'dream and promise act'),   # 52 letters
    'Federal Power Act': ('federal power act',),   # 51 letters
    'Community Reinvestment Act': ('community reinvestment act',),   # 50 letters
    'Gun Control Act': ('gun control act',),   # 50 letters
    'Occupational Safety and Health Act': ('occupational safety and health act',),   # 49 letters
    'Federal Advisory Committee Act': ('federal advisory committee act',),   # 48 letters
    'Trade Expansion Act': ('trade expansion act',),   # 48 letters
    'Federal Insecticide, Fungicide, and Rodenticide Act': ('fifra', 'federal insecticide fungicide'),   # 46 letters
    'Federal Land Policy and Management Act': ('federal land policy and management act',),   # 45 letters
    'Help America Vote Act': ('help america vote act',),   # 43 letters
    'Communications Act of 1934': ('communications act of',),   # 41 letters
    'Presidential Records Act': ('presidential records act',),   # 40 letters
    'Medicare Access and CHIP Reauthorization Act': ('macra', 'medicare access and chip reauthorization'),   # 39 letters
    'STOCK Act': ('stock act',),   # 39 letters
    'Epstein Files Transparency Act': ('epstein files transparency act', 'epstein files'),   # 38 letters
    'Bayh-Dole Act': ('bayh-dole', 'bayh dole'),   # 37 letters
    'Communications Decency Act': ('communications decency act',),   # 37 letters
    'PROMESA': ('promesa', 'puerto rico oversight management and economic stability act'),   # 36 letters
    'WIIN Act': ('wiin act', 'water infrastructure improvements for the nation'),   # 36 letters
    'Radiation Exposure Compensation Act': ('radiation exposure compensation act',),   # 34 letters
    'Regulatory Flexibility Act': ('regulatory flexibility act',),   # 34 letters
    'Fair Credit Reporting Act': ('fair credit reporting act',),   # 33 letters
    'American Health Care Act': ('american health care act',),   # 32 letters
    'Military Lending Act': ('military lending act',),   # 32 letters
    'Natural Gas Act': ('natural gas act',),   # 32 letters
    'Outer Continental Shelf Lands Act': ('outer continental shelf lands act',),   # 32 letters
    'Carl D. Perkins Career and Technical Education Act': ('perkins career and technical education', 'carl d perkins', 'perkins v', 'perkins cte'),   # 30 letters
    'Foreign Corrupt Practices Act': ('foreign corrupt practices act', 'fcpa'),   # 30 letters
    'Telephone Consumer Protection Act': ('telephone consumer protection act',),   # 29 letters
    'Personal Responsibility and Work Opportunity Reconciliation Act': ('personal responsibility and work opportunity', 'prwora'),   # 28 letters
    'FIRRMA': ('firrma', 'foreign investment risk review modernization act'),   # 27 letters
    'Federal Election Campaign Act': ('federal election campaign act',),   # 26 letters
    'Medicare Modernization Act': ('medicare modernization act',),   # 25 letters
    'American Taxpayer Relief Act': ('american taxpayer relief act',),   # 24 letters
    'Comprehensive Addiction Resources Emergency Act': ('comprehensive addiction resources emergency',),   # 24 letters
    'Alaska Native Claims Settlement Act': ('alaska native claims settlement act', 'ancsa'),   # 22 letters
    'Employment Non-Discrimination Act': ('employment non-discrimination act', 'employment nondiscrimination act'),   # 22 letters
    'American Relief Act': ('american relief act',),   # 20 letters
    'Consumer Financial Protection Act': ('consumer financial protection act',),   # 20 letters
    'America Invents Act': ('america invents act',),   # 19 letters
    'Clery Act': ('clery act',),   # 18 letters
    'Intelligence Authorization Act': ('intelligence authorization act',),   # 17 letters
    'Taiwan Travel Act': ('taiwan travel act',),   # 17 letters
    'Federal Vacancies Reform Act': ('federal vacancies reform act',),   # 16 letters
    'Allow States and Victims to Fight Online Sex Trafficking Act': ('allow states and victims to fight online sex trafficking', 'fosta'),   # 14 letters
    'Comprehensive Iran Sanctions, Accountability, and Divestment Act': ('cisada', 'comprehensive iran sanctions accountability'),   # 14 letters
    'Pregnant Workers Fairness Act': ('pregnant workers fairness act',),   # 14 letters
    'Asia Reassurance Initiative Act': ('asia reassurance initiative act',),   # 13 letters
    'American Jobs Creation Act': ('american jobs creation act',),   # 12 letters
    'Conscience Protection Act': ('conscience protection act',),   # 12 letters
    'INF Treaty': ('inf treaty', 'intermediate-range nuclear forces treaty', 'intermediate range nuclear forces treaty'),   # 12 letters
    'Iran Threat Reduction Act': ('iran threat reduction act', 'iran threat reduction and syria human rights act'),   # 12 letters
    'STELA Reauthorization Act': ('stela reauthorization', 'satellite television extension and localism act'),   # 12 letters
    'Tomato Suspension Agreement': ('tomato suspension agreement',),   # 12 letters
    'CONNECT for Health Act': ('connect for health act',),   # 11 letters
    'Prescription Drug User Fee Act': ('prescription drug user fee act', 'pdufa'),   # 11 letters
    'Deborah Sampson Act': ('deborah sampson act',),   # 10 letters
    'Dickey Amendment': ('dickey amendment',),   # 10 letters
    'Ensuring Patient Access and Effective Drug Enforcement Act': ('ensuring patient access and effective drug enforcement act',),   # 10 letters
    'PREP Act': ('public readiness and emergency preparedness act', 'prep act'),   # 10 letters
    'Pregnancy Discrimination Act': ('pregnancy discrimination act',),   # 10 letters
    'INVEST in America Act': ('invest in america act',),   # 9 letters
    'Not Invisible Act': ('not invisible act',),   # 9 letters
    'STOP School Violence Act': ('stop school violence act',),   # 9 letters
    'Unlawful Internet Gambling Enforcement Act': ('unlawful internet gambling enforcement act', 'uigea'),   # 9 letters
    'Veterans Court Improvement Act': ('veterans court improvement act',),   # 9 letters
    'Healthy, Hunger-Free Kids Act': ('hunger-free kids act',),   # 8 letters
    'Lifespan Respite Care Act': ('lifespan respite care',),   # 8 letters
    'Mammography Quality Standards Reauthorization Act': ('mammography quality standards',),   # 8 letters
    'Protecting Access to Medicare Act': ('protecting access to medicare act',),   # 8 letters
    'Bridge Investment Act': ('bridge investment act',),   # 7 letters
    'Nunn-McCurdy Act': ('nunn-mccurdy', 'nunn mccurdy'),   # 7 letters
    'Taylor Force Act': ('taylor force act',),   # 7 letters
    'Women, Peace, and Security Act': ('women peace and security act',),   # 7 letters
    'Equal Access Act': ('equal access act',),   # 6 letters
    'Fair RETIRE Act': ('fair retire act',),   # 6 letters
    'Iran Freedom and Counter-Proliferation Act': ('iran freedom and counter-proliferation act',),   # 6 letters
    'Nursing Home Fire Safety Act': ('nursing home fire safety act',),   # 6 letters
    'Opioid Crisis Response Act': ('opioid crisis response act', 'crib act'),   # 6 letters
    '21st Century Conservation Corps Act': ('st century conservation corps',),   # 5 letters
    'Biological Weapons Convention': ('biological weapons convention',),   # 5 letters
    'Miners Protection Act': ('miners protection act',),   # 5 letters
    'National Apprenticeship Act': ('national apprenticeship act',),   # 5 letters
    'Native American Suicide Prevention Act': ('native american suicide prevention act',),   # 5 letters
    'Scientific Integrity Act': ('scientific integrity act',),   # 5 letters
    'Senior Safe Act': ('senior safe act',),   # 5 letters
    'Break the Cycle of Violence Act': ('break the cycle of violence act',),   # 4 letters
    'Climate Corporate Data Accountability Act': ('climate corporate data accountability act',),   # 4 letters
    'DETER Act': ('deter act', 'defending elections from threats by establishing redlines'),   # 4 letters
    'Infrastructure 2.0 Act': ('infrastructure act',),   # 4 letters
    'Quality Housing and Work Responsibility Act': ('quality housing and work responsibility act',),   # 4 letters
    'SAFE Justice Act': ('safe justice act',),   # 4 letters
    'Saracini Aviation Safety Act': ('saracini aviation safety act',),   # 4 letters
    "Savanna's Act": ("savanna's act", 'savannas act'),   # 4 letters
    'Ten-in-Ten Fuel Economy Act': ('ten-in-ten fuel economy act',),   # 4 letters
    'Cybersecurity Disclosure Act': ('cybersecurity disclosure act',),   # 3 letters
    'Doha Agreement': ('doha agreement', 'agreement with the taliban', 'us-taliban agreement'),   # 3 letters
    'Fighting Fraud to Protect Care for Seniors Act': ('fighting fraud to protect care for seniors act',),   # 3 letters
    'Interim Consolidated Storage Act': ('interim consolidated storage act',),   # 3 letters
    'Medicare Advantage Quality Payment Relief Act': ('medicare advantage quality payment relief act',),   # 3 letters
    'Nationwide Consumer and Fuel Retailer Choice Act': ('nationwide consumer and fuel retailer choice act',),   # 3 letters
    'Partnership to Build America Act': ('partnership to build america act',),   # 3 letters
    'Reclamation Recycling and Water Conservation Act': ('reclamation recycling and water conservation act',),   # 3 letters
    'Supporting Grandparents Raising Grandchildren Act': ('supporting grandparents raising grandchildren act',),   # 3 letters
    'TAILOR Act': ('tailor act',),   # 3 letters
    'VA Website Accessibility Act': ('va website accessibility act',),   # 3 letters
    'Advanced Air Mobility Coordination and Leadership Act': ('advanced air mobility coordination and leadership act',),   # 2 letters
    'Boundary Waters Canoe Area Wilderness Act': ('boundary waters canoe area wilderness act',),   # 2 letters
    'Digital Accountability and Transparency Act': ('digital accountability and transparency act',),   # 2 letters
    'Earmark Elimination Act': ('earmark elimination act',),   # 2 letters
    'Electronic Prescribing of Controlled Substances Act': ('epcs act', 'electronic prescribing of controlled substances'),   # 2 letters
    'Keeping American Workers Paid and Employed Act': ('keeping american workers paid and employed act',),   # 2 letters
    'Nuclear Energy Innovation and Modernization Act': ('nuclear energy innovation and modernization act', 'neima'),   # 2 letters
    'Probation Officer Protection Act': ('probation officer protection act',),   # 2 letters
    'STREET Act': ('smart technology for resilient efficient economic and reliable transportation',),   # 2 letters
    'School Food Modernization Act': ('school food modernization act',),   # 2 letters
    'Unclaimed Savings Bond Act': ('unclaimed savings bond act',),   # 2 letters
    'A-PLUS Act': ('a-plus act',),   # 1 letters
    'ACCESS Act': ('assessing critical core efforts to strengthen service',),   # 1 letters
    'ANTI Drugs Act': ('anti drugs act',),   # 1 letters
    'Appalachian Energy for National Security Act': ('appalachian energy for national security act',),   # 1 letters
    'Bipartisan Health Care Stabilization Act': ('bipartisan health care stabilization act',),   # 1 letters
    'CHIPPING IN Act': ('chipping in act',),   # 1 letters
    'CHP Support Act': ('chp support act',),   # 1 letters
    'Chemical and Biological Weapons Control and Warfare Elimination Act': ('chemical and biological weapons control and warfare elimination act', 'cbw act'),   # 1 letters
    'Electronic Currency and Secure Hardware Act': ('electronic currency and secure hardware act', 'ecash act'),   # 1 letters
    'Endangered Salmon and Fisheries Protection Act': ('endangered salmon and fisheries protection act',),   # 1 letters
    'Ensuring Diplomats Safety Act': ('ensuring diplomats safety act',),   # 1 letters
    "Improving Seniors' Access to Quality Benefits Act": ('improving seniors access to quality benefits act', "improving seniors' access to quality benefits act"),   # 1 letters
    'Keep Innovation in America Act': ('keep innovation in america act',),   # 1 letters
    'Keystone XL Pipeline Act': ('keystone xl pipeline act',),   # 1 letters
    'NRC Survey Act': ('nrc survey act',),   # 1 letters
    'National MEP Supply Chain Database Act': ('national mep supply chain database act',),   # 1 letters
    'PACE Act': ('promoting affordable childcare for everyone',),   # 1 letters
    'RACE for Children Act': ('race for children act',),   # 1 letters
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

    # Hand-filed only (#221; Robin, 16 November 2026): subjects the readers
    # asked for. No match words, so no letter is tagged by them automatically.
    "Iraq": (),
    "Homeland security": (),
    "Terrorism": (),
    "Intelligence": (),
    "Detained Americans": (),
    "West Bank": (),
    "Sudan": (),
    "Armenia": (),
    "Honduras": (),
    "Haiti": (),
    "Caribbean": (),
    "Passports": (),
    # Hand-filed only (#221; Robin, 16 November 2026): subjects the readers
    # asked for. No match words, so no letter is tagged by them automatically.
    "Torture": (),
    "Antisemitism": (),
    "Religion": (),
    "Holocaust restitution": (),
    "Human rights": (),
    "Adoption": (),
    "Welfare": (),
    "Census": (),
    "Federal statistics": (),
    "Animal welfare": (),
    "Solid waste": (),
    "Consumer product safety": (),
    "Sports": (),
    "Parks and recreation": (),
    "Public facilities": (),
    # Hand-filed only (#221; Robin, 16 November 2026): subjects the readers
    # asked for. No match words, so no letter is tagged by them automatically.
    "Brazil": (),
    "Ethiopia": (),
    "Rwanda": (),
    "Sri Lanka": (),
    "El Salvador": (),
    "Cyprus": (),
    "Saudi Arabia": (),
    "Turkey": (),
    "Taiwan": (),
    "Western Sahara": (),
    # Hand-filed only (#221; Robin, 16 November 2026): subjects the readers
    # asked for. No match words, so no letter is tagged by them automatically.
    "Arts and culture": (),
    "National symbols": (),
    "Government records": (),
    "Labor rights": (),
    "House procedure": (),
    "Resignations from Congress": (),
    "Death penalty": (),
    "Pardons": (),
    "Bankruptcy": (),
    "Gambling": (),
    "Intellectual property": (),
    "Coast Guard": (),
    "Food and beverages": (),
    # Hand-filed only (#221; Robin, 16 November 2026): subjects the readers
    # asked for. No match words, so no letter is tagged by them automatically.
    "Yemen": (),
    "Foreign investment": (),
    # Hand-filed only (#1250; Robin, 17 November 2026): asked for by the
    # 106th-115th reading. U.S. territories is the group; the five territories
    # are the subjects under it.
    "Puerto Rico": (),
    "Guam": (),
    "U.S. Virgin Islands": (),
    "Northern Marianas": (),
    "American Samoa": (),
    "North Korea": (),
    "Nicaragua": (),
    "Foster care": (),
    "School safety": (),
    "Assisted suicide": (),
    "Foreign bribery": (),
    "Invasive species": (),
    "Currency": (),
    # Hand-filed only (the PC's reading batches 61-64, #1343 #1349 #1350 #1356;
    # 19 November 2026): subjects and laws the held letters needed.
    "Indian Housing Block Grant": (),
    "Low Income Home Energy Assistance Program": (),
    "Senior Community Service Employment Program": (),
    "Veterans treatment courts": (),
    "Guantanamo Bay": (),
    "Nagorno Karabakh": (),
    "Compacts of Free Association": (),
    "Antideficiency Act": (),
    "Partial Birth Abortion Ban Act": (),
    "Agent Orange": (),
    "Cameroon": (),
    "Caregivers": (),
    "Chechnya": (),
    "Earthquakes": (),
    "HIV": (),
    "Hong Kong": (),
    "Kurds": (),
    "Libya": (),
    "Mining": (),
    "Nursing homes": (),
    "Refugees": (),
    "Uyghurs": (),
    "Wolves": (),
    "Women": (),
    "Consolidated Farm and Rural Development Act": (),
    "America's Water Infrastructure Act": (),
    "Flood Control Act of 1946": (),
    "Trade Act of 1974": (),
    "Import Tax Relief Act": (),
    "Agriculture Improvement Act of 2018": (),
    "Packers and Stockyards Act": (),
    "International Religious Freedom Act": (),
    "Restoring Tax Fairness for States and Localities Act": (),
    "CHIMP Act": (),
    "Animal Welfare Act": (),
    "Wild and Scenic Rivers Act": (),
    "Coastal Zone Management Act": (),
    "Federal Tort Claims Act": (),
    "Soil Conservation and Allotment Domestic Act of 1935": (),
    "Religious Freedom Restoration Act": (),
    "Food Safety Modernization Act": (),
    "Taiwan Relations Act": (),
    "Small Business Act": (),
    "Healthcare Workforce Resilience Act": (),
    "BUILD Act": (),
    "Flood Control Act of 1944": (),
    "Water Supply Act of 1958": (),
    "American Data Dissemination Act": (),
    "Mental Health Services for Students Act": (),
    "Map Improvement Act": (),
    "Middle Class Health Benefits Tax Repeal Act": (),
    "Truth in Lending Act": (),
    "TREAD Act": (),
    "MAP-21": (),
    "Federal Meat Inspection Act": (),
    "Equal Credit Opportunity Act": (),
    "Home Mortgage Disclosure Act": (),
    "Food and Drug Administration Safety and Innovation Act": (),
    "Bipartisan Background Checks Act": (),
    "Enhanced Background Checks Act": (),
    "Motor Carrier Safety Improvement Act": (),
    "Water Infrastructure Improvements for the Nation Act": (),
    "Cable Communications Policy Act": (),
    "Fair Debt Collection Practices Act": (),
    "USMCA": (),
    "Agriculture Improvement Act (2018 Farm Bill)": (),
    "Tornadoes": (),
    "Tunisia": (),
    "Eritrea": (),
    "Germany": (),
    "Brunei": (),
    "Bahrain": (),
    "Bahamas": (),
    "NATO": (),
    "ISIS": (),
    "Payment Integrity Information Act": (),
    "Uniform Code of Military Justice": (),
    "Child Soldiers Prevention Act": (),
    "Frank LoBiondo Coast Guard Authorization Act": (),
    "Marine Mammal Protection Act": (),
    "Civil Service Reform Act": (),
    "First Step Act": (),
    "Agriculture Improvement Act": (),
    "Food Quality Protection Act": (),
    "Natural Gas Pipeline Safety Act": (),
    "Paycheck Fairness Act": (),
    "Paycheck Protection Program Flexibility Act": (),
    "Crime Victims Rights Act": (),
    "Treaty on Open Skies": (),
    "South Korea": (),
    "United Arab Emirates": (),
    "Colombia": (),
    "Vietnam": (),
    "Myanmar": (),
    "Water Infrastructure Finance and Innovation Act": (),
    # Hand-filed only (#1330; 18 November 2026): laws and a bill the 105th
    # Congress's HTML letters name. No match words, so no other letter changes.
    "Government Performance and Results Act": (),
    "School-to-Work Opportunities Act": (),
    "Legal Timber Protection Act": (),
}

# A named law's phrase also tags its parent topic (and any topic its words
# would otherwise hide: tag() keeps only the longest phrase at a position),
# so "Violence Against Women Act" still carries Domestic violence (#1324).
LAW_PARENTS: dict[str, tuple[str, ...]] = {
    'Government Performance and Results Act': ('Oversight',),
    'School-to-Work Opportunities Act': ('Jobs',),
    'Legal Timber Protection Act': ('Trade',),
    'Consolidated Appropriations Act': ('Appropriations',),
    'Infrastructure Investment and Jobs Act': ('Transportation',),
    'Tax Cuts and Jobs Act': ('Taxes',),
    'JCPOA': ('Iran', 'Nuclear'),
    'NAFTA': ('Trade',),
    'Public Health Service Act': ('Public health',),
    'One Big Beautiful Bill Act': ('Taxes',),
    'FAA Reauthorization Act': ('Aviation', 'FAA'),
    'Fair Labor Standards Act': ('Labor rights',),
    'Federal Food, Drug, and Cosmetic Act': ('Prescription drugs',),
    'Privacy Act': ('Privacy',),
    'Bipartisan Budget Act': ('Budgets',),
    'Global Magnitsky Act': ('Sanctions',),
    'Individuals with Disabilities Education Act': ('Education', 'People with disabilities'),
    'Budget Control Act': ('Budgets',),
    'Comprehensive Environmental Response, Compensation, and Liability Act': ('Pollution',),
    'Violence Against Women Act': ('Domestic violence',),
    'Foreign Agents Registration Act': ('Ethics',),
    'USA PATRIOT Act': ('Surveillance',),
    'Energy Policy Act': ('Energy',),
    'Trafficking Victims Protection Reauthorization Act': ('Human trafficking',),
    'Rehabilitation Act': ('People with disabilities',),
    'False Claims Act': ('Oversight',),
    'SUPPORT for Patients and Communities Act': ('Opioids',),
    'Bank Secrecy Act': ('Banking',),
    'Energy Independence and Security Act': ('Energy',),
    'Employee Retirement Income Security Act': ('Retirement',),
    'Trade Act': ('Trade',),
    'Every Student Succeeds Act': ('Education',),
    'Disaster Recovery Reform Act': ('Disasters',),
    'Fair Housing Act': ('Housing',),
    'Paycheck Protection Program and Health Care Enhancement Act': ('Small business',),
    'Hatch Act': ('Ethics',),
    'Magnuson-Stevens Act': ('Fisheries',),
    'Impoundment Control Act': ('Budgets',),
    'Family Smoking Prevention and Tobacco Control Act': ('Tobacco',),
    'VA MISSION Act': ('Veterans',),
    'Bipartisan Safer Communities Act': ('Guns',),
    'PACT Act': ('Veterans',),
    'Arms Trade Treaty': ('Defense',),
    "Countering America's Adversaries Through Sanctions Act": ('Sanctions',),
    'Workforce Innovation and Opportunity Act': ('Jobs',),
    'Coronavirus Preparedness and Response Supplemental Appropriations Act': ('COVID-19', 'Appropriations'),
    'Full-Year Continuing Appropriations and Extensions Act': ('Appropriations',),
    'Great American Outdoors Act': ('Public lands',),
    'National Firearms Act': ('Guns',),
    'Dream Act': ('Immigration',),
    'Federal Power Act': ('Electric grid',),
    'Community Reinvestment Act': ('Banking',),
    'Gun Control Act': ('Guns', 'Gun control'),
    'Occupational Safety and Health Act': ('Labor rights',),
    'Federal Advisory Committee Act': ('Oversight',),
    'Trade Expansion Act': ('Tariffs',),
    'Federal Insecticide, Fungicide, and Rodenticide Act': ('Pollution',),
    'Federal Land Policy and Management Act': ('Public lands',),
    'Help America Vote Act': ('Elections',),
    'Communications Act of 1934': ('Telecom',),
    'Presidential Records Act': ('Government records',),
    'Medicare Access and CHIP Reauthorization Act': ('Medicare',),
    'STOCK Act': ('Ethics',),
    'Epstein Files Transparency Act': ('Oversight',),
    'Bayh-Dole Act': ('Intellectual property',),
    'Communications Decency Act': ('Social media',),
    'PROMESA': ('Puerto Rico',),
    'WIIN Act': ('Water',),
    'Radiation Exposure Compensation Act': ('Nuclear',),
    'Regulatory Flexibility Act': ('Regulation',),
    'Fair Credit Reporting Act': ('Credit reporting',),
    'American Health Care Act': ('Health care',),
    'Military Lending Act': ('Banking', 'Defense'),
    'Natural Gas Act': ('Oil and gas', 'Energy'),
    'Outer Continental Shelf Lands Act': ('Oil and gas',),
    'Carl D. Perkins Career and Technical Education Act': ('Education',),
    'Foreign Corrupt Practices Act': ('Foreign bribery',),
    'Telephone Consumer Protection Act': ('Telecom',),
    'Personal Responsibility and Work Opportunity Reconciliation Act': ('Welfare',),
    'FIRRMA': ('Foreign investment',),
    'Federal Election Campaign Act': ('Campaign financing', 'Elections'),
    'Medicare Modernization Act': ('Medicare',),
    'American Taxpayer Relief Act': ('Taxes',),
    'Comprehensive Addiction Resources Emergency Act': ('Opioids',),
    'Alaska Native Claims Settlement Act': ('Native Americans',),
    'Employment Non-Discrimination Act': ('LGBTQ people',),
    'American Relief Act': ('Appropriations',),
    'Consumer Financial Protection Act': ('Banking',),
    'America Invents Act': ('Intellectual property',),
    'Clery Act': ('Higher education',),
    'Intelligence Authorization Act': ('Intelligence',),
    'Taiwan Travel Act': ('Taiwan',),
    'Federal Vacancies Reform Act': ('Nominations',),
    'Allow States and Victims to Fight Online Sex Trafficking Act': ('Human trafficking',),
    'Comprehensive Iran Sanctions, Accountability, and Divestment Act': ('Sanctions', 'Iran'),
    'Pregnant Workers Fairness Act': ('Labor rights', 'Maternal health'),
    'Asia Reassurance Initiative Act': ('China',),
    'American Jobs Creation Act': ('Taxes',),
    'Conscience Protection Act': ('Abortion',),
    'INF Treaty': ('Russia',),
    'Iran Threat Reduction Act': ('Sanctions', 'Iran'),
    'STELA Reauthorization Act': ('Telecom',),
    'Tomato Suspension Agreement': ('Trade',),
    'CONNECT for Health Act': ('Telehealth',),
    'Prescription Drug User Fee Act': ('Prescription drugs',),
    'Deborah Sampson Act': ('Veterans',),
    'Dickey Amendment': ('Gun violence',),
    'Ensuring Patient Access and Effective Drug Enforcement Act': ('Opioids',),
    'PREP Act': ('Public health',),
    'Pregnancy Discrimination Act': ('Labor rights', 'Civil rights', 'Maternal health'),
    'INVEST in America Act': ('Transportation',),
    'Not Invisible Act': ('Native Americans',),
    'STOP School Violence Act': ('School safety',),
    'Unlawful Internet Gambling Enforcement Act': ('Gambling',),
    'Veterans Court Improvement Act': ('Veterans',),
    'Healthy, Hunger-Free Kids Act': ('Nutrition assistance',),
    'Lifespan Respite Care Act': ('Older adults',),
    'Mammography Quality Standards Reauthorization Act': ('Health care',),
    'Protecting Access to Medicare Act': ('Medicare',),
    'Bridge Investment Act': ('Transportation',),
    'Nunn-McCurdy Act': ('Defense',),
    'Taylor Force Act': ('Israel and Gaza',),
    'Women, Peace, and Security Act': ('Human rights',),
    'Equal Access Act': ('Education',),
    'Fair RETIRE Act': ('Retirement',),
    'Iran Freedom and Counter-Proliferation Act': ('Sanctions', 'Iran'),
    'Nursing Home Fire Safety Act': ('Older adults',),
    'Opioid Crisis Response Act': ('Opioids',),
    '21st Century Conservation Corps Act': ('Public lands',),
    'Biological Weapons Convention': ('Chemical weapons',),
    'Miners Protection Act': ('Retirement',),
    'National Apprenticeship Act': ('Jobs',),
    'Native American Suicide Prevention Act': ('Native Americans', 'Mental health'),
    'Scientific Integrity Act': ('Scientific research',),
    'Senior Safe Act': ('Older adults',),
    'Break the Cycle of Violence Act': ('Crime',),
    'Climate Corporate Data Accountability Act': ('Climate',),
    'DETER Act': ('Election integrity',),
    'Infrastructure 2.0 Act': ('Transportation',),
    'Quality Housing and Work Responsibility Act': ('Housing',),
    'SAFE Justice Act': ('Prisons',),
    'Saracini Aviation Safety Act': ('Aviation',),
    "Savanna's Act": ('Native Americans',),
    'Ten-in-Ten Fuel Economy Act': ('Cars',),
    'Cybersecurity Disclosure Act': ('Cybersecurity',),
    'Doha Agreement': ('Afghanistan',),
    'Fighting Fraud to Protect Care for Seniors Act': ('Older adults',),
    'Interim Consolidated Storage Act': ('Nuclear waste',),
    'Medicare Advantage Quality Payment Relief Act': ('Medicare',),
    'Nationwide Consumer and Fuel Retailer Choice Act': ('Oil and gas',),
    'Partnership to Build America Act': ('Transportation',),
    'Reclamation Recycling and Water Conservation Act': ('Water',),
    'Supporting Grandparents Raising Grandchildren Act': ('Foster care',),
    'TAILOR Act': ('Banking',),
    'VA Website Accessibility Act': ('Veterans',),
    'Advanced Air Mobility Coordination and Leadership Act': ('Aviation',),
    'Boundary Waters Canoe Area Wilderness Act': ('Public lands',),
    'Digital Accountability and Transparency Act': ('Oversight',),
    'Earmark Elimination Act': ('Appropriations',),
    'Electronic Prescribing of Controlled Substances Act': ('Opioids',),
    'Keeping American Workers Paid and Employed Act': ('Small business',),
    'Nuclear Energy Innovation and Modernization Act': ('Nuclear', 'Energy'),
    'Probation Officer Protection Act': ('Crime',),
    'STREET Act': ('Transportation',),
    'School Food Modernization Act': ('Nutrition assistance',),
    'Unclaimed Savings Bond Act': ('Investing',),
    'A-PLUS Act': ('Education',),
    'ACCESS Act': ('Health care',),
    'ANTI Drugs Act': ('Drug trafficking',),
    'Appalachian Energy for National Security Act': ('Energy',),
    'Bipartisan Health Care Stabilization Act': ('Health care',),
    'CHIPPING IN Act': ('Scientific research',),
    'CHP Support Act': ('Energy',),
    'Chemical and Biological Weapons Control and Warfare Elimination Act': ('Chemical weapons',),
    'Electronic Currency and Secure Hardware Act': ('Currency',),
    'Endangered Salmon and Fisheries Protection Act': ('Fisheries', 'Wildlife'),
    'Ensuring Diplomats Safety Act': ('Foreign aid',),
    "Improving Seniors' Access to Quality Benefits Act": ('Medicare',),
    'Keep Innovation in America Act': ('Taxes',),
    'Keystone XL Pipeline Act': ('Oil and gas', 'Energy'),
    'NRC Survey Act': ('Nuclear',),
    'National MEP Supply Chain Database Act': ('Supply chains',),
    'PACE Act': ('Childcare',),
    'RACE for Children Act': ('Medical research',),
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
                for parent in LAW_PARENTS.get(label, ()):
                    index[words[0]].append((" ".join(words), parent))
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
