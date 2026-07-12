"""
diaspora.py
===========
Charron (2013) 'Diaspora' control variable, transcribed directly from the paper's
**Appendix 2** ("Distribution of significant minority groups in ESC countries").

Charron's construction (p.491-492):
  * For each ESC host country, the FIVE largest minority groups *that are
    themselves ESC participant countries* are identified (Eurostat foreign-resident
    counts 1998-2011 for EU states, national censuses elsewhere).
  * They are then "coded inversely 1-5": the single largest group scores 5, the
    fifth-largest scores 1 (Appendix-2 note: "coded inversely so that the top
    group is '5'").
  * The variable is DYADIC and directional -- Diaspora_Cji is the size-rank of the
    minority in *voter* country i that originates from *receiver* country j.  The
    idea (p.491): a diaspora from j living in host/voter i votes for its homeland j.
    Paper's own examples (fn.16): Germany->Turkey = 5 (Turks are Germany's largest
    ESC minority); Austria->Turkey = 5.  Both reproduce below.
  * Special coding rule (Appendix-2 note): where the group "Jewish" is listed, it
    is coded for **Israel**.

The variable is time-invariant (Charron averages 1998-2011 and applies it to 2012
as well); we therefore apply the same code to every dyad-year.  It only carries
signal in the televote era -- Charron finds diasporas had "no effect on the vote
prior to televoting" -- so downstream code should restrict it to >= 1998 when
interpreting, but the structural attribute itself is defined here for all years.

Countries that did NOT appear in Appendix 2 (they had not participated in >=2
finals by 2012: Australia, Czechia, Montenegro, San Marino) have no minority
profile and score 0 on every dyad, which is the correct 'no measured diaspora'
default.  Historical Serbian codes (Serbia & Montenegro 'cs', Yugoslavia 'yu') are
aliased to Serbia 'rs' for the lookup.
"""

# ---------------------------------------------------------------------------
# Appendix 2, transcribed verbatim: host country -> its top-5 minority groups
# in RANK ORDER (rank 1 first).  Demonyms are exactly as printed in the paper
# (typos in the PDF such as "Aremnians"/"Norwegens" are normalised in DEMONYM
# below, not here, so this block stays a faithful transcription).
# ---------------------------------------------------------------------------
APPENDIX2 = {
    "Albania":      ["Greeks", "Serbs", "Macedonians", "Bulgarians", "Jewish"],
    "Armenia":      ["Russians", "Ukrainians", "Greeks", "Jewish", "Georgians"],
    "Austria":      ["Turks", "Germans", "Bosnians", "Croatians", "Polish"],
    "Azerbaijan":   ["Armenians", "Russians", "Turks", "Ukrainians", "Georgians"],
    "Belarus":      ["Russians", "Polish", "Ukrainians", "Jewish", "Armenians"],
    "Belgium":      ["Italians", "French", "Dutch", "Turks", "Spanish"],
    "Bosnia & Herzegovina": ["Serbs", "Croats", "Albanians", "Ukrainians", "Macedonians"],
    "Croatia":      ["Serbs", "Bosnians", "Italians", "Hungarians", "Albanians"],
    "Cyprus":       ["Greeks", "Turks", "British", "Romanians", "Bulgarians"],
    "Denmark":      ["Turks", "Bosnians", "Germans", "Norwegians", "British"],
    "Estonia":      ["Russians", "Ukrainians", "Belarusians", "Finnish", "Latvians"],
    "Finland":      ["Russians", "Estonians", "Swedes", "British", "Germans"],
    "France":       ["Portuguese", "Turks", "Italians", "Spanish", "British"],
    "Georgia":      ["Azerbaijani", "Armenians", "Russians", "Greeks", "Ukrainians"],
    "Germany":      ["Turks", "Italians", "Polish", "Croats", "Austrians"],
    "Greece":       ["Albanians", "Bulgarians", "Russians", "Cypriots", "Romanians"],
    "Hungary":      ["Romanians", "Ukrainians", "Germans", "Serbians", "Polish"],
    "Iceland":      ["Polish", "Danish", "Germans", "Lithuanians", "British"],
    "Ireland":      ["British", "Polish", "Lithuanians", "Latvians", "Germans"],
    "Israel":       ["Russians", "Romanians", "Polish", "Spanish", "Germans"],
    "Italy":        ["Romanians", "Albanians", "Ukrainians", "Polish", "Macedonians"],
    "Latvia":       ["Russians", "Belarusians", "Ukrainians", "Polish", "Lithuanians"],
    "Lithuania":    ["Polish", "Russians", "Belarusians", "Ukrainians", "Germans"],
    "Macedonia":    ["Albanians", "Turkish", "Serbs", "Bosnians", "Croats"],
    "Malta":        ["British", "Serbs", "Italians", "Germans", "Bulgarians"],
    "Netherlands":  ["Turks", "Germans", "British", "Belgians", "Polish"],
    "Norway":       ["Swedes", "Danish", "Polish", "Germans", "British"],
    "Poland":       ["Germans", "Belarusians", "Ukrainians", "Russians", "Lithuanians"],
    "Portugal":     ["Ukrainians", "British", "Spanish", "Romanians", "Germans"],
    "Romania":      ["Hungarians", "Ukrainians", "Germans", "Russians", "Turks"],
    "Russia":       ["Ukrainians", "Armenians", "Azerbaijanis", "Belarusians", "Germans"],
    "Serbia":       ["Hungarians", "Bosnians", "Croats", "Albanians", "Romanians"],
    "Slovenia":     ["Bosnians", "Serbs", "Croats", "Macedonians", "Italians"],
    "Spain":        ["Romanians", "British", "Germans", "Italians", "Portuguese"],
    "Sweden":       ["Finnish", "Norwegians", "Danish", "Polish", "Bosnians"],
    "Switzerland":  ["Italians", "Portuguese", "Germans", "Serbs", "Turks"],
    "Turkey":       ["Azerbaijanis", "Georgians", "Bosnians", "Albanians", "British"],
    "United Kingdom": ["Irish", "Polish", "Italians", "French", "Germans"],
    "Ukraine":      ["Russians", "Hungarians", "Romanians", "Bulgarians", "Belarusians"],
}

# ---------------------------------------------------------------------------
# Host-country NAME (as in APPENDIX2) -> ISO-2 voter/receiver code (votes.csv).
# ---------------------------------------------------------------------------
HOST2ISO = {
    "Albania": "al", "Armenia": "am", "Austria": "at", "Azerbaijan": "az",
    "Belarus": "by", "Belgium": "be", "Bosnia & Herzegovina": "ba",
    "Croatia": "hr", "Cyprus": "cy", "Denmark": "dk", "Estonia": "ee",
    "Finland": "fi", "France": "fr", "Georgia": "ge", "Germany": "de",
    "Greece": "gr", "Hungary": "hu", "Iceland": "is", "Ireland": "ie",
    "Israel": "il", "Italy": "it", "Latvia": "lv", "Lithuania": "lt",
    "Macedonia": "mk", "Malta": "mt", "Netherlands": "nl", "Norway": "no",
    "Poland": "pl", "Portugal": "pt", "Romania": "ro", "Russia": "ru",
    "Serbia": "rs", "Slovenia": "si", "Spain": "es", "Sweden": "se",
    "Switzerland": "ch", "Turkey": "tr", "United Kingdom": "gb", "Ukraine": "ua",
}

# ---------------------------------------------------------------------------
# Minority-group DEMONYM (as printed in Appendix 2) -> homeland ISO-2 code.
# 'Jewish' -> Israel (paper's explicit rule).  Spelling variants folded in.
# ---------------------------------------------------------------------------
DEMONYM = {
    "Greeks": "gr", "Serbs": "rs", "Serbians": "rs", "Macedonians": "mk",
    "Bulgarians": "bg", "Jewish": "il", "Russians": "ru",
    "Ukrainians": "ua", "Ukraine": "ua", "Georgians": "ge",
    "Turks": "tr", "Turkish": "tr", "Germans": "de", "Bosnians": "ba",
    "Croatians": "hr", "Croats": "hr", "Polish": "pl",
    "Armenians": "am", "Italians": "it", "French": "fr", "Dutch": "nl",
    "Spanish": "es", "Albanians": "al", "British": "gb",
    "Romanians": "ro", "Hungarians": "hu", "Norwegians": "no", "Belarusians": "by",
    "Finnish": "fi", "Latvians": "lv", "Estonians": "ee", "Swedes": "se",
    "Portuguese": "pt", "Azerbaijani": "az", "Azerbaijanis": "az",
    "Cypriots": "cy", "Danish": "dk", "Lithuanians": "lt",
    "Austrians": "at", "Belgians": "be", "Irish": "ie",
}

# Historical-code aliases: map to the modern homeland/host code for the lookup.
_ALIAS = {"cs": "rs", "yu": "rs"}


def _build_table():
    """host_iso -> {homeland_iso: code(5..1)} from Appendix 2."""
    tbl = {}
    for host, groups in APPENDIX2.items():
        hi = HOST2ISO[host]
        d = {}
        for rank, dem in enumerate(groups):        # rank 0..4 -> code 5..1
            code = 5 - rank
            homeland = DEMONYM[dem]
            # keep the strongest code if a homeland appears twice (it never does
            # in Appendix 2, but be safe).
            if homeland not in d or code > d[homeland]:
                d[homeland] = code
        tbl[hi] = d
    return tbl


DIASPORA_TABLE = _build_table()


def diaspora(i, j):
    """Diaspora_Cji: size-rank (5=largest .. 1=fifth; 0=not in top 5) of the
    minority in VOTER country i that originates from RECEIVER country j.

    i = host/voter, j = homeland/receiver -- matches the DV direction (vote i->j)
    and the paper's Germany->Turkey = 5 example."""
    i = _ALIAS.get(i, i)
    j = _ALIAS.get(j, j)
    return DIASPORA_TABLE.get(i, {}).get(j, 0)


if __name__ == "__main__":
    # sanity checks against the paper's stated examples / structure
    assert diaspora("de", "tr") == 5, "Germany->Turkey should be 5"
    assert diaspora("at", "tr") == 5, "Austria->Turkey should be 5"
    assert diaspora("gr", "al") == 5, "Greece->Albania (largest) should be 5"
    assert diaspora("gr", "ro") == 1, "Greece->Romania (fifth) should be 1"
    assert diaspora("cy", "gr") == 5 and diaspora("cy", "tr") == 4
    assert diaspora("au", "tr") == 0, "non-Appendix-2 host scores 0"
    nz = sum(1 for h in DIASPORA_TABLE for _ in DIASPORA_TABLE[h])
    print(f"diaspora.py OK: {len(DIASPORA_TABLE)} host countries, "
          f"{nz} non-zero directed dyads (5 each).")
    print("  Germany->Turkey =", diaspora("de", "tr"),
          "| UK->Ireland =", diaspora("gb", "ie"),
          "| Russia->Ukraine =", diaspora("ru", "ua"))
