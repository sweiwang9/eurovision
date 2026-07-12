"""
lib_countries.py
================
Shared country metadata used across the Charron (2013) replication scripts.

Charron, N. (2013). "Impartiality, friendship-networks and voting behavior:
Evidence from voting patterns in the Eurovision Song Contest."
Social Networks 35 (2013) 484-497.

This module centralises three things that every downstream script needs:

  1. NAME     : ISO-2 (lower-case, as used in votes.csv) -> readable country name.
  2. ISO3     : ISO-2 -> ISO-3 alpha code (used to join the QoG / ICRG data).
  3. Two *dyadic* control variables that the paper uses but that do NOT ship
     in the raw data folder, so they are reconstructed here by hand:
        - CONTIGUITY : 1 if two countries share a land border.
        - LANGUAGE   : 1 if two countries share an official/native language.
     Both are standard, time-invariant geographic/linguistic facts, so hard
     coding them is defensible.  They are clearly flagged as reconstructions.

Every block below is commented so the assumptions are transparent and auditable.
"""

# ---------------------------------------------------------------------------
# 1. Readable names for every country that appears as a voter/receiver in the
#    ESC finals 1975-2012 (the sample window of the paper).  Keys are the
#    lower-case ISO-2 codes exactly as they appear in votes.csv / contestants.csv.
# ---------------------------------------------------------------------------
NAME = {
    "al": "Albania",   "am": "Armenia",     "at": "Austria",   "az": "Azerbaijan",
    "ba": "Bosnia & Herzegovina", "be": "Belgium", "bg": "Bulgaria", "by": "Belarus",
    "ch": "Switzerland", "cs": "Serbia & Montenegro", "cy": "Cyprus", "de": "Germany",
    "dk": "Denmark",   "ee": "Estonia",     "es": "Spain",     "fi": "Finland",
    "fr": "France",    "gb": "United Kingdom", "ge": "Georgia", "gr": "Greece",
    "hr": "Croatia",   "hu": "Hungary",     "ie": "Ireland",   "il": "Israel",
    "is": "Iceland",   "it": "Italy",       "lt": "Lithuania", "lu": "Luxembourg",
    "lv": "Latvia",    "ma": "Morocco",     "mc": "Monaco",    "md": "Moldova",
    "mk": "Macedonia", "mt": "Malta",       "nl": "Netherlands", "no": "Norway",
    "pl": "Poland",    "pt": "Portugal",    "ro": "Romania",   "rs": "Serbia",
    "ru": "Russia",    "se": "Sweden",      "si": "Slovenia",  "sk": "Slovakia",
    "tr": "Turkey",    "ua": "Ukraine",     "yu": "Yugoslavia",
    # later ESC entrants (needed to extend the analysis through 2026)
    "au": "Australia", "cz": "Czechia (Czech Rep.)", "me": "Montenegro", "sm": "San Marino",
}

# ---------------------------------------------------------------------------
# 2. ISO-2 -> ISO-3 map so we can merge the QoG panel (which is keyed on the
#    ISO-3 `ccodealp` column) onto the vote data.  Historical entities map to
#    the ISO-3 code the QoG file actually uses:
#       yu -> YUG (Yugoslavia, pre-1992)
#       cs -> SCG (Serbia & Montenegro, 2003-2006)
#       rs -> SRB (Serbia, 2006+)
# ---------------------------------------------------------------------------
ISO3 = {
    "al": "ALB", "am": "ARM", "at": "AUT", "az": "AZE", "ba": "BIH", "be": "BEL",
    "bg": "BGR", "by": "BLR", "ch": "CHE", "cs": "SCG", "cy": "CYP", "de": "DEU",
    "dk": "DNK", "ee": "EST", "es": "ESP", "fi": "FIN", "fr": "FRA", "gb": "GBR",
    "ge": "GEO", "gr": "GRC", "hr": "HRV", "hu": "HUN", "ie": "IRL", "il": "ISR",
    "is": "ISL", "it": "ITA", "lt": "LTU", "lu": "LUX", "lv": "LVA", "ma": "MAR",
    "mc": "MCO", "md": "MDA", "mk": "MKD", "mt": "MLT", "nl": "NLD", "no": "NOR",
    "pl": "POL", "pt": "PRT", "ro": "ROU", "rs": "SRB", "ru": "RUS", "se": "SWE",
    "si": "SVN", "sk": "SVK", "tr": "TUR", "ua": "UKR", "yu": "YUG",
    "au": "AUS", "cz": "CZE", "me": "MNE", "sm": "SMR",
}

# ---------------------------------------------------------------------------
# 2b. ICRG IMPARTIALITY HOT-DECK DONORS (Charron 2013, footnote 13).
#     QoG's `icrg_qog` has no series for some ESC countries.  Charron warns that
#     mean-substitution is inappropriate for this NON-RANDOM missingness and
#     instead uses HOT-DECK imputation: borrow impartiality from the most similar
#     ESC country (judged by the World Governance Indicators).  We follow that:
#     each donee inherits its donor's ICRG series (ffilled/bfilled over the panel).
#
#       ge <- hr, mk <- al, md <- az  are Charron's *exact* footnote-13 pairs, and
#       the imputation is applied UNCONDITIONALLY to match what he did.  Moldova now
#       HAS its own icrg_qog in the current QoG release, but Charron lacked it and
#       imputed Moldova from Azerbaijan, so we do the same (donee takes donor even
#       when a real series exists) to reproduce his tables faithfully.
#
#     ICRG (PRS Group, 141 countries) does NOT cover Bosnia or Monaco at all -- so,
#     contrary to an earlier note here, Charron could not have had real ICRG for
#     them either; his fn.13 simply did not enumerate them.  Montenegro/San Marino
#     are later ESC entrants (no ESC final before 2014, so absent from the 1975-2012
#     replication).  For these four we extend Charron's OWN method -- pick the most
#     WGI-similar ESC country that has its own ICRG:
#       ba <- al (Albania is Bosnia's nearest ESC country by WGI corruption/gov-
#                 effectiveness/rule-of-law, among countries with real ICRG),
#       me <- rs (Montenegro <- Serbia, former state union; WGI-close),
#       sm <- it (San Marino <- Italy, enclave; no WGI of its own),
#       mc <- fr (Monaco <- France; Monaco has almost no WGI, French-associated).
# ---------------------------------------------------------------------------
# Charron fn.13 names EXACTLY three hot-deck imputations.  The faithful
# replication uses ONLY these; every other country with no ICRG is DROPPED as a
# voter (he rejects mean-substitution), which is what reproduces his sample size.
CHARRON_DONOR = {"ge": "hr", "mk": "al", "md": "az"}
# The EXTENSION additionally imputes countries Charron omitted, by the same
# WGI-nearest method, to keep them in the 1975-2026 panel.
ICRG_DONOR = {
    **CHARRON_DONOR,
    "ba": "al", "me": "rs", "sm": "it", "mc": "fr",   # same method, countries he omitted
}

# Country lineage.  Serbia & Montenegro (`cs`, 2004-2006) is the predecessor of
# Serbia (`rs`, 2007+); Charron's Table 2 fn.b treats period-2 "Serbia" as
# continuous across the 2006 split, so we merge cs -> rs everywhere (votes and the
# finalist roster).  SFR Yugoslavia (`yu`, 1975-1992) is a DISTINCT entity (its own
# Table 2 period-1 group) and is NOT merged.
ALIAS = {"cs": "rs"}


def alias(code):
    return ALIAS.get(code, code)


# ---------------------------------------------------------------------------
# 3a. CONTIGUITY (reconstructed).  For each country we list its land-border
#     neighbours *within the ESC set*.  The relation is symmetric; the helper
#     below symmetrises it so we only have to list each border once-ish.
#     Islands (Cyprus, Iceland, Malta) and Israel have no ESC land neighbour.
# ---------------------------------------------------------------------------
_BORDERS = {
    "al": ["gr", "mk", "rs", "yu"],
    "am": ["ge", "az", "tr"],
    "at": ["de", "ch", "it", "si", "sk", "hu", "yu"],
    "az": ["am", "ge", "ru", "tr"],
    "ba": ["hr", "rs"],
    "be": ["fr", "nl", "de", "lu"],
    "bg": ["gr", "tr", "ro", "rs", "mk", "yu"],
    "by": ["pl", "lt", "lv", "ru", "ua"],
    "ch": ["de", "fr", "it", "at"],
    "cs": ["hr", "ba", "mk", "al", "ro", "bg", "hu"],   # Serbia & Montenegro
    "de": ["fr", "ch", "at", "be", "nl", "dk", "pl", "lu"],
    "dk": ["de"],
    "ee": ["lv", "ru"],
    "es": ["pt", "fr"],
    "fi": ["se", "no", "ru"],
    "fr": ["es", "be", "de", "ch", "it", "lu", "mc"],
    "gb": ["ie"],
    "ge": ["ru", "tr", "am", "az"],
    "gr": ["al", "mk", "bg", "tr", "yu"],
    "hr": ["si", "hu", "ba", "rs", "yu"],
    "hu": ["at", "sk", "ua", "ro", "rs", "hr", "si", "yu"],
    "ie": ["gb"],
    "it": ["fr", "ch", "at", "si", "yu"],
    "lt": ["lv", "by", "pl", "ru"],
    "lu": ["be", "fr", "de"],
    "lv": ["ee", "lt", "ru", "by"],
    "mc": ["fr"],
    "md": ["ro", "ua"],
    "mk": ["al", "gr", "bg", "rs", "yu"],
    "nl": ["be", "de"],
    "no": ["se", "fi", "ru"],
    "pl": ["de", "sk", "ua", "by", "lt", "ru"],
    "pt": ["es"],
    "ro": ["hu", "rs", "bg", "ua", "md", "yu"],
    "rs": ["hu", "ro", "bg", "mk", "al", "ba", "hr"],
    "ru": ["no", "fi", "ee", "lv", "lt", "by", "ua", "ge", "az"],
    "se": ["no", "fi"],
    "si": ["at", "it", "hu", "hr", "yu"],
    "sk": ["pl", "ua", "hu", "at"],
    "tr": ["gr", "bg", "ge", "am", "az"],
    "ua": ["ru", "by", "pl", "sk", "hu", "ro", "md"],
    "yu": ["it", "at", "hu", "ro", "bg", "mk", "al", "gr", "hr", "si"],  # pre-1992
    # later entrants
    "au": [],                                    # island continent, no ESC neighbour
    "cz": ["de", "pl", "sk", "at"],
    "me": ["hr", "ba", "rs", "al"],
    "sm": ["it"],                                # enclave within Italy
}


def _build_contiguity():
    """Return a symmetric set of frozenset({a,b}) pairs that share a border."""
    pairs = set()
    for a, nbrs in _BORDERS.items():
        for b in nbrs:
            if a != b:
                pairs.add(frozenset((a, b)))
    return pairs


CONTIGUITY_PAIRS = _build_contiguity()

# ---------------------------------------------------------------------------
# 3b. SHARED LANGUAGE (reconstructed).  The paper codes Language_ij = 1 when
#     two countries "share any officially recognized native language"
#     (its examples: Switzerland-France, Finland-Sweden, Russia-Ukraine).
#     We list, per language, the ESC countries where it is official/native;
#     any dyad that co-occurs in a group gets Language = 1.
# ---------------------------------------------------------------------------
_LANGUAGE_GROUPS = {
    "german":       ["de", "at", "ch", "lu", "be"],
    "french":       ["fr", "be", "ch", "lu", "mc"],
    "dutch":        ["nl", "be"],
    "italian":      ["it", "ch", "sm"],               # Italian is official in San Marino
    "greek":        ["gr", "cy"],
    "turkish":      ["tr", "cy"],                     # Turkish is co-official in Cyprus
    "english":      ["gb", "ie", "mt", "au"],         # English official in Malta & Australia
    "swedish":      ["se", "fi"],                     # Swedish is official in Finland
    "scandinavian": ["se", "no", "dk"],               # mutually intelligible N. Germanic
    "romanian":     ["ro", "md"],
    "russian":      ["ru", "by", "ua"],               # East-Slavic / Russian widely official
    "bcms":         ["rs", "hr", "ba", "cs", "yu", "me"],  # Serbo-Croatian continuum
    "czechoslovak": ["cz", "sk"],                     # mutually intelligible Czech/Slovak
}


def _build_language():
    """Return a symmetric set of frozenset({a,b}) pairs that share a language."""
    pairs = set()
    for members in _LANGUAGE_GROUPS.values():
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                pairs.add(frozenset((members[i], members[j])))
    return pairs


LANGUAGE_PAIRS = _build_language()


# ---------------------------------------------------------------------------
# Convenience accessors used by the dataset builder.
# ---------------------------------------------------------------------------
def contiguous(a, b):
    """1 if a and b share a land border, else 0."""
    return int(frozenset((a, b)) in CONTIGUITY_PAIRS)


def same_language(a, b):
    """1 if a and b share an official/native language, else 0."""
    return int(frozenset((a, b)) in LANGUAGE_PAIRS)
