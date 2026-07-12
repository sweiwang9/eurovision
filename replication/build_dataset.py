"""
build_dataset.py
================
Construct the master dyad-year panel used by the regression/figure scripts.

Unit of analysis (as in the paper): the *dyad-year* -- an ordered pair
(voter i -> receiver j) in a given final year t.

TWO SOURCES (choose with `--source`):
  * bundled  (default): the folder's votes.csv + contestants.csv, 1975-2012.
               Writes output/master.csv (the exact Charron replication window).
  * eschome            : the scraped votes_eschome.csv + finalists_eschome.csv,
               1975-2026, for extending the analysis to later years.
               Writes output/master_extended.csv and additionally carries:
                 running_final, place_final  -- explicit finalist attributes of j
                                                (from the scoreboard roster),
                 row_points_j                -- points j got from the "Rest of the
                                                World" online televote (2023+),
               and identifies finalists from the EXPLICIT scoreboard roster
               (finalists_eschome.csv), never by inferring from received points.

For each dyad-year we assemble:
  vote, quality (eq.1), bias (eq.2), imp_i/imp_j (ICRG), song_order(=running_final
  of j), host, english/french (lyrics heuristic, where lyrics exist), contig,
  language, lag_vote_ij, lag_vote_ji, n_part, diaspora (Charron Appendix 2, via
  diaspora.py).  (Duet/Group/Female performer dummies added separately.)
"""

import csv
import os
import sys
import numpy as np
import pandas as pd

from lib_countries import NAME, ISO3, ICRG_DONOR, CHARRON_DONOR, alias, contiguous, same_language

# Charron states the ICRG "extends back to 1983"; the faithful replication uses
# impartiality from this year (the QoG icrg_qog series itself starts 1984, so 1983
# takes the 1984 value forward-/back-filled).  Rows before this drop from the
# impartiality regressions.
CHARRON_ICRG_START = 1983
from diaspora import diaspora

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.dirname(HERE)                     # parent folder holds the CSVs
OUT = os.path.join(HERE, "output")               # replication artifacts
# The extended (eschome, 1975-2026) source data and master_extended.csv live in
# the sibling extension/ folder; its scraped inputs are read from and its master
# written back to extension/output/.  Bundled replication stays entirely in OUT.
EXT_OUT = os.path.join(DATA, "extension", "output")
os.makedirs(OUT, exist_ok=True)


# ===========================================================================
# FINALIST ROSTERS (explicit) + VOTES, per source.
# ===========================================================================
def load_finalists_bundled():
    """Finalists per year from contestants.csv (running_final / place_final set).
    Also returns per-(year,code) running order and place for the song traits."""
    fin = {}; traits = {}
    with open(os.path.join(DATA, "contestants.csv")) as f:
        for r in csv.DictReader(f):
            if not r["year"]:
                continue
            y = int(r["year"]); c = alias(r["to_country_id"])
            in_final = r.get("running_final", "") != "" or r.get("place_final", "") != ""
            if in_final:
                fin.setdefault(y, set()).add(c)
            rf = r.get("running_final", ""); pf = r.get("place_final", "")
            traits[(y, c)] = {
                "running_final": float(rf) if rf not in ("", None) else np.nan,
                "place_final": float(pf) if pf not in ("", None) else np.nan,
            }
    return fin, traits


def load_finalists_eschome():
    """EXPLICIT finalist roster from the scoreboard scrape (finalists_eschome.csv):
    a performer in the final regardless of points.  Also returns running order and
    final placing per (year, code)."""
    fin = {}; traits = {}
    path = os.path.join(EXT_OUT, "finalists_eschome.csv")
    with open(path) as f:
        for r in csv.DictReader(f):
            y = int(r["year"]); c = alias(r["country_id"])
            fin.setdefault(y, set()).add(c)
            rf = r.get("running_final", ""); pf = r.get("place_final", "")
            traits[(y, c)] = {
                "running_final": float(rf) if rf not in ("", None, "") else np.nan,
                "place_final": float(pf) if pf not in ("", None, "") else np.nan,
            }
    return fin, traits


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return np.nan


def load_votes(votes_path, fin, lo, hi, ever_finalist_givers=True):
    """Final votes in [lo,hi] as voter->receiver dyads, using the explicit roster
    `fin`.  Excludes the 'xx' Rest-of-World giver (handled separately as a
    variable).  Returns (dyads_df, row_df).

    ever_finalist_givers=True (REPLICATION, Charron fn.18): vote GIVERS are all
        countries that reached a final in ANY year -- an eliminated semi-finalist
        still votes in the final and is counted (his Finland-2012 example) --
        while RECEIVERS are that year's finalists.  So the dyad set is
        {ever-finalist giver} x {finalist-that-year receiver}.
    ever_finalist_givers=False (EXTENSION, prior behavior): finalist->finalist
        only (both i and j must be finalists that year).  Kept so the extension's
        master_extended.csv is unchanged until that design choice is revisited.

    `vote` is the total (0-12 pre-2016; 0-24 = jury+televote from 2016).  We also
    keep the split components `vote_jury` and `vote_tele` (each 0-12, populated
    from 2016) so the later-years analysis can work on a consistent 0-12 scale."""
    rows = []; rowrows = []
    # ever-finalist giver set, restricted to the build window (the eschome roster
    # spans 1975-2026, so we must not let a post-window debut qualify a giver).
    win = [s for y, s in fin.items() if lo <= y <= hi]
    all_finalists = set().union(*win) if win else set()
    with open(votes_path) as f:
        for r in csv.DictReader(f):
            if r["round"] != "final" or not r["year"]:
                continue
            y = int(r["year"])
            if not (lo <= y <= hi):
                continue
            i, j = alias(r["from_country_id"]), alias(r["to_country_id"])
            if r["total_points"] in ("", None):
                continue
            v = float(r["total_points"])
            jp = _num(r.get("jury_points")); tp = _num(r.get("tele_points"))
            if i == "xx":                                 # Rest-of-World giver
                if j in fin.get(y, set()):
                    rowrows.append((y, j, v))
                continue
            if i not in NAME or j not in NAME or i == j:
                continue
            if j not in fin.get(y, set()):
                continue                                   # receiver: finalist that year
            if ever_finalist_givers:
                if i not in all_finalists:
                    continue                               # giver: ever a finalist (fn.18)
            else:
                if i not in fin.get(y, set()):
                    continue                               # extension: finalist->finalist
            rows.append((y, i, j, v, jp, tp))
    dyads = pd.DataFrame(rows, columns=["year", "i", "j", "vote", "vote_jury", "vote_tele"])
    rowdf = pd.DataFrame(rowrows, columns=["year", "j", "row_points_j"])
    return dyads, rowdf


# ===========================================================================
# SHARED COMPUTATIONS (identical for both sources).
# ===========================================================================
def add_quality_bias(df):
    """Dyad-specific quality (eq.1) and bias (eq.2)."""
    part = df.groupby("year").apply(
        lambda g: len(set(g["i"]) | set(g["j"])), include_groups=False)
    total = df.groupby(["year", "j"])["vote"].sum().rename("total_j")
    df = df.merge(total, on=["year", "j"])
    df["p"] = df["year"].map(part)
    df["quality"] = (df["total_j"] - df["vote"]) / (df["p"] - 2)
    df["bias"] = df["vote"] - df["quality"]
    df = df.rename(columns={"p": "n_part"})
    return df


def load_impartiality(lo, hi, charron_faithful=True):
    """ICRG impartiality per country-year, with Charron fn.13 hot-deck imputation.

    charron_faithful=True  (REPLICATION): apply the hot-deck UNCONDITIONALLY, exactly
        as Charron did -- a donee takes its donor's series even if the current QoG
        release now carries a real series the donor lacked (Moldova <- Azerbaijan).
    charron_faithful=False (EXTENSION): use all available data -- only impute donees
        that genuinely have no ICRG series of their own (Georgia, Macedonia, and the
        micro-states); Moldova, which now has real data, keeps it.
    """
    raw = {}
    # Slim ICRG subset of the QoG Standard Time-Series (Jan-2026 release): only the
    # ccodealp/year/icrg_qog columns the pipeline uses (~150 KB vs the 71 MB full
    # file, which stays out of git -- see qog_icrg_jan26.csv / .gitignore / README).
    with open(os.path.join(DATA, "qog_icrg_jan26.csv")) as f:
        for r in csv.DictReader(f):
            v = r["icrg_qog"]
            if v == "":
                continue
            raw.setdefault(r["ccodealp"], {})[int(r["year"])] = float(v)
    years = list(range(lo, hi + 1))
    imp = {}; allvals = []
    # Earliest year the icrg_qog series itself covers (=1984).
    data_start = min((min(d) for d in raw.values() if d), default=lo)
    # Charron states ICRG "extends back to 1983", so the faithful replication starts
    # there (the 1984 value carried back one year); the extension starts at the data.
    start = CHARRON_ICRG_START if charron_faithful else data_start
    # ICRG quality-of-government is highly persistent, so we carry the last observed
    # value FORWARD (ffill) to fill later gaps.  We then back-fill only as far as
    # `start`: faithful -> 1983, extension -> keep the old full bfill to 1975.
    for iso2, iso3 in ISO3.items():
        series = raw.get(iso3, {})
        if not series:
            continue
        s = pd.Series({y: series.get(y, np.nan) for y in years}).ffill()
        if charron_faithful:
            mask = s.index >= start                       # back-fill 1984 -> 1983 only
            s.loc[mask] = s.loc[mask].bfill()
        else:
            s = s.bfill()                                 # extension: cover 1975-1983
        imp[iso2] = s.to_dict(); allvals.extend(s.dropna().tolist())
    # Hot-deck imputation (Charron fn.13): a donee takes its donor's ICRG series
    # wholesale (mean-substitution is rejected for non-random missingness).  The
    # REPLICATION uses ONLY Charron's three named cases (Georgia<-Croatia,
    # Macedonia<-Albania, Moldova<-Azerbaijan); every OTHER country with no ICRG
    # (Bosnia, Monaco, ...) is left missing and thus DROPPED as a voter -- this is
    # what reproduces his sample size.  The EXTENSION imputes the wider donor set
    # and only where a country genuinely lacks its own series.
    donors = CHARRON_DONOR if charron_faithful else ICRG_DONOR
    for donee, donor in donors.items():
        if donor in imp and (charron_faithful or donee not in imp):
            imp[donee] = dict(imp[donor])
    return imp, float(np.mean(allvals)), start


def add_impartiality(df, lo, hi, charron_faithful=True):
    imp, gm, start = load_impartiality(lo, hi, charron_faithful)

    if charron_faithful:
        # No mean-substitution (Charron rejects it): a country with no ICRG series
        # and no fn.13 donor stays MISSING and drops from the regression.  Pre-`start`
        # (pre-1983) years are also missing.  Table 1 / quality use the full votes.
        def look(c, y):
            return imp.get(c, {}).get(y, np.nan)
        df["imp_i"] = [np.nan if y < start else look(i, y)
                       for i, y in zip(df["i"], df["year"])]
        df["imp_j"] = [np.nan if y < start else look(j, y)
                       for j, y in zip(df["j"], df["year"])]
    else:
        def look(c, y):
            v = imp.get(c, {}).get(y, np.nan)
            return gm if pd.isna(v) else v            # extension keeps a mean fallback
        df["imp_i"] = [look(i, y) for i, y in zip(df["i"], df["year"])]
        df["imp_j"] = [look(j, y) for j, y in zip(df["j"], df["year"])]
    return df


# English/French heuristic from lyrics (only where lyrics exist -> contestants.csv).
_EN = {" the ", " and ", " you ", " love ", " my ", " me ", " to ", " it ", " is ", " in "}
_FR = {" les ", " le ", " la ", " je ", " tu ", " et ", " un ", " une ", " mon ", " est ", " que ", " de "}


def _lang_flags(lyrics):
    if not lyrics:
        return (np.nan, np.nan)
    t = " " + lyrics.lower().replace("\\n", " ").replace("\n", " ") + " "
    en = sum(t.count(w) for w in _EN); fr = sum(t.count(w) for w in _FR)
    if en == 0 and fr == 0:
        return (0, 0)
    return (int(en >= fr and en > 0), int(fr > en))


def load_lyrics_flags():
    """English/French flags per (year, code) from contestants.csv lyrics.
    (contestants.csv covers 1956-2023; later years -> NaN.)"""
    out = {}
    with open(os.path.join(DATA, "contestants.csv")) as f:
        for r in csv.DictReader(f):
            if not r["year"]:
                continue
            en, fr = _lang_flags(r.get("lyrics", ""))
            out[(int(r["year"]), r["to_country_id"])] = (en, fr)
    return out


def load_performer_types():
    """Receiver-j performer-type dummies from output/performer_types.csv (built by
    the authoritative Wikidata lookup + name heuristics; see SUMMARY.md).  Charron's
    four-way performer control: Duet / Group / (solo) Female, with solo male as the
    omitted baseline.  Returns {(year, code): (duet, group, female)}."""
    out = {}
    path = os.path.join(OUT, "performer_types.csv")
    if not os.path.exists(path):
        return out
    with open(path) as f:
        for r in csv.DictReader(f):
            out[(int(r["year"]), r["country_id"])] = (
                int(r["duet"]), int(r["group"]), int(r["female"]))
    return out


def add_song_traits(df, traits, fin):
    """Attach receiver-j song traits: running order & final placing (explicit),
    host status, and heuristic English/French flags."""
    df["running_final"] = [traits.get((y, j), {}).get("running_final", np.nan)
                           for y, j in zip(df["year"], df["j"])]
    df["place_final"] = [traits.get((y, j), {}).get("place_final", np.nan)
                         for y, j in zip(df["year"], df["j"])]
    df["song_order"] = df["running_final"]           # Charron's "Song Order"
    lyr = load_lyrics_flags()
    df["english"] = [lyr.get((y, j), (np.nan, np.nan))[0] for y, j in zip(df["year"], df["j"])]
    df["french"] = [lyr.get((y, j), (np.nan, np.nan))[1] for y, j in zip(df["year"], df["j"])]
    # Performer-type dummies of receiver j (Charron: Duet / Group / Female; solo
    # male = baseline).  NaN where the performer could not be resolved (flagged in
    # performer_types.csv `source`); those rows fall back to baseline in the regs.
    pt = load_performer_types()
    df["duet"] = [pt.get((y, j), (np.nan,) * 3)[0] for y, j in zip(df["year"], df["j"])]
    df["group"] = [pt.get((y, j), (np.nan,) * 3)[1] for y, j in zip(df["year"], df["j"])]
    df["female"] = [pt.get((y, j), (np.nan,) * 3)[2] for y, j in zip(df["year"], df["j"])]
    # host of year t = the winner (place_final==1) of year t-1.
    winners = {}
    for (y, c), tr in traits.items():
        if tr.get("place_final") == 1:
            winners[y] = c
    host = {(y + 1, w): 1 for y, w in winners.items()}
    df["host"] = [host.get((y, j), 0) for y, j in zip(df["year"], df["j"])]
    return df


def add_dyadic(df):
    df["contig"] = [contiguous(i, j) for i, j in zip(df["i"], df["j"])]
    df["language"] = [same_language(i, j) for i, j in zip(df["i"], df["j"])]
    # Diaspora_Cji (Charron Appendix 2): rank 5..1 of the receiver-j minority in
    # voter i, else 0.  Time-invariant; signal only in the televote era (>=1998).
    df["diaspora"] = [diaspora(i, j) for i, j in zip(df["i"], df["j"])]
    vote_map = {(y, i, j): v for y, i, j, v in
                zip(df["year"], df["i"], df["j"], df["vote"])}
    df["lag_vote_ij"] = [vote_map.get((y - 1, i, j), np.nan)
                         for y, i, j in zip(df["year"], df["i"], df["j"])]
    df["lag_vote_ji"] = [vote_map.get((y - 1, j, i), np.nan)
                         for y, i, j in zip(df["year"], df["i"], df["j"])]
    return df


# ===========================================================================
# MAIN
# ===========================================================================
def main():
    # Source selection:
    #   (default)          REPLICATION -- Charron's OWN data source (fn.1: eschome.net,
    #                      which we scraped to extension/output/votes_eschome.csv),
    #                      restricted to 1975-2012, faithful rules -> master.csv.
    #   --source bundled   legacy cross-check from the bundled 2023 dataset
    #                      (votes.csv/contestants.csv) -> master_bundled.csv.
    #   --source eschome   EXTENSION -- the full scraped panel 1975-2026 -> master_extended.csv.
    source = "replication"
    if "--source" in sys.argv:
        source = sys.argv[sys.argv.index("--source") + 1]

    if source == "eschome":
        lo, hi = 1975, 2026
        fin, traits = load_finalists_eschome()
        df, rowdf = load_votes(os.path.join(EXT_OUT, "votes_eschome.csv"), fin, lo, hi,
                               ever_finalist_givers=True)    # same as replication (fn.18)
        out_name = "master_extended.csv"
        out_dir = EXT_OUT                        # extension artifact
    elif source == "bundled":
        lo, hi = 1975, 2012
        fin, traits = load_finalists_bundled()
        df, rowdf = load_votes(os.path.join(DATA, "votes.csv"), fin, lo, hi,
                               ever_finalist_givers=True)    # replication rules, bundled data
        out_name = "master_bundled.csv"
        out_dir = OUT                            # replication cross-check artifact
    else:                                        # "replication" (default)
        lo, hi = 1975, 2012
        fin, traits = load_finalists_eschome()   # Charron's eschome source (scraped)
        df, rowdf = load_votes(os.path.join(EXT_OUT, "votes_eschome.csv"), fin, lo, hi,
                               ever_finalist_givers=True)    # Charron fn.18
        out_name = "master.csv"
        out_dir = OUT                            # replication artifact

    # Replication reproduces Charron's fn.13 imputation exactly; the extension
    # (1975-2026) instead uses all currently-available real ICRG data.
    faithful = (source != "eschome")
    df = add_quality_bias(df)
    df = add_impartiality(df, lo, hi, charron_faithful=faithful)
    df = add_song_traits(df, traits, fin)
    df = add_dyadic(df)

    # Rest-of-World points received by j that year (bias-neutral popularity signal).
    if not rowdf.empty:
        rmap = rowdf.groupby(["year", "j"])["row_points_j"].sum().to_dict()
        df["row_points_j"] = [rmap.get((y, j), np.nan) for y, j in zip(df["year"], df["j"])]
    else:
        df["row_points_j"] = np.nan

    # Sample inclusion: Charron's "participated in the ESC final at least twice".
    # The MASTER keeps the FULL descriptive sample -- every dyad-year among countries
    # with >=2 finals -- because that is what the DESCRIPTIVE tables (Table 1,
    # Appendix 3) need and what reproduces Charron's descriptive numbers.  We ALSO tag
    # each row with `cohort` = whether it passes the stricter CUMULATIVE "2nd-final
    # entry" rule (a country enters only once it is an established finalist).  The
    # REGRESSIONS filter to cohort==1, which is what matches Charron's regression N;
    # Table 1 / Appendix 3 use the full sample.
    finals_by = df.groupby("j")["year"].apply(lambda s: sorted(s.unique()))
    keep2 = {c for c, ys in finals_by.items() if len(ys) >= 2}
    df = df[df["i"].isin(keep2) & df["j"].isin(keep2)].copy()          # full sample
    entry = {c: (ys[1] if len(ys) >= 2 else None) for c, ys in finals_by.items()}

    def entered(c, y):
        e = entry.get(c)
        return e is not None and e <= y
    df["cohort"] = [int(entered(i, y) and entered(j, y))
                    for i, j, y in zip(df["i"], df["j"], df["year"])]

    df["voter"] = df["i"].map(NAME); df["receiver"] = df["j"].map(NAME)
    os.makedirs(out_dir, exist_ok=True)
    df.to_csv(os.path.join(out_dir, out_name), index=False)
    print(f"{out_name} written: {len(df):,} dyad-year rows, "
          f"{df['year'].min()}-{df['year'].max()}, {df['j'].nunique()} countries "
          f"(source={source}).")
    return df


if __name__ == "__main__":
    main()
