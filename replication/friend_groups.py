"""
friend_groups.py
================
Charron (2013) Table 2 -- "Friend groups via voting portfolio patterns
(method 1)" -- transcribed VERBATIM for the two time periods.  This replaces the
re-clustered groups for the regression's Friend Dyad variable, so the method-1
friend measure matches the paper's exactly (the main lever on the Friend Dyad and
Friend x Impartiality coefficients).

Notation
--------
A trailing '~' marks a country the paper superscripts 'a' = "weaker cluster
linkage… removed from any group in checks of robustness".  Such members are:
  * KEPT in the main analysis (Table 3, and Table 4 method-1 is the *alternative*),
  * REMOVED in the "Alternative Friend Group Method 1" (Table 4 cols 5-8).
Footnote 'b': period-2 "Serbia" was Serbia & Montenegro (code `cs`) before 2007,
so both `rs` and `cs` are placed in that Balkan group.

`friend_pairs(period, alt=False)` returns the set of ordered (i, j) within-group
friend dyads; `alt=True` drops the '~' (weak) members first.
"""

# Country names -> ISO2 codes used throughout the project.
TABLE2 = {
    "1975-1997": [
        ["ba", "tr"],                              # G1  Bosnia&Herz., Turkey
        ["se", "dk", "no", "is", "fi~"],           # G2  Nordic (Finland weak)
        ["ru", "si"],                              # G3  Russia, Slovenia
        ["gb", "ie", "lu~", "be~", "ch~"],         # G4  UK, Ireland (+weak Lux/Bel/Swi)
        ["il", "yu"],                              # G5  Israel, Yugoslavia
        ["ee", "pl", "hu"],                        # G6  Estonia, Poland, Hungary
        ["cy", "gr"],                              # G7  Cyprus, Greece
        ["de~", "fr~", "nl~", "at~"],              # G8  all weak (vanishes in alt)
        ["hr", "mt", "pt"],                        # G9  Croatia, Malta, Portugal
        ["it", "es", "mc~"],                       # G10 Italy, Spain (+weak Monaco)
    ],
    "1998-2012": [
        ["ro", "md"],                              # G1  Romania, Moldova
        ["gr", "cy"],                              # G2  Greece, Cyprus
        ["tr", "az"],                              # G3  Turkey, Azerbaijan
        ["ua", "ge", "ru", "by", "am", "il"],      # G4  ex-Soviet + Israel
        ["it", "al"],                              # G5  Italy, Albania
        ["rs", "si", "hr", "ba", "mk"],            # G6  ex-Yugoslav (rs = Serbia, incl. former cs)
        ["es", "pt", "fr~"],                       # G7  Spain, Portugal (+weak France)
        ["de", "ch", "at"],                        # G8  Germany, Switzerland, Austria
        ["lv", "lt", "ee"],                        # G9  Baltic
        ["se", "dk", "is", "no", "fi"],            # G10 Nordic
        ["gb", "ie", "mt~"],                       # G11 UK, Ireland (+weak Malta)
        ["nl", "be"],                              # G12 Netherlands, Belgium
        ["pl~", "hu~"],                            # G13 both weak (vanishes in alt)
    ],
}

PERIODS = ["1975-1997", "1998-2012"]


def group_members(group, alt=False):
    """Return the member codes of one group; alt=True drops '~' (weak) members."""
    if alt:
        return [c for c in group if not c.endswith("~")]
    return [c.rstrip("~") for c in group]


def groups(period, alt=False):
    """List of member-code lists for a period (weak members dropped if alt)."""
    return [group_members(g, alt) for g in TABLE2[period]]


def friend_pairs(period, alt=False):
    """Set of ordered (i, j) within-group friend dyads for `period`.
    alt=False -> full Table 2 (main, Table 3);
    alt=True  -> weak 'a'-marked members removed (Alternative Method 1, Table 4)."""
    pairs = set()
    for g in TABLE2[period]:
        members = group_members(g, alt)
        for a in members:
            for b in members:
                if a != b:
                    pairs.add((a, b))
    return pairs
