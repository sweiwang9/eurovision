"""
build_performer_types.py
========================
Reproduce output/performer_types.csv: the receiver-j performer-type classification
(solo male / solo female / duet / group) used to build Charron's Duet / Group /
Female song-trait dummies (solo male = omitted baseline).

WHY: contestants.csv ships the performer *name* but not the act composition or the
performer's gender.  Charron (p.491) controls for "whether a song ... is performed
by a group, a duet, a solo male or solo female".  We recover this AUTHORITATIVELY
from Wikidata (each ESC act has a Wikidata item with P31 'instance of' and, for
humans, P21 'sex or gender').

SPINE (the acts to classify):
  * 1975-2023 : finalist performers from contestants.csv (running_final/place_final
                set), exactly the receiver-j set build_dataset.py uses.
  * 2024-2026 : finalist roster from output/finalists_eschome.csv (country only;
                performer + type pulled from Wikidata's per-entry data).

METHOD (three passes, each recorded in the `source` column so any row is auditable):
  1. wikidata_exact : batch VALUES match of the performer name to an English
     rdfs:label / skos:altLabel; among candidates that are a human (Q5) or a
     subclass of 'musical ensemble' (Q2088357), take the one with most sitelinks.
     Classify: musical duo (Q9212979) subclass -> duet; other ensemble -> group;
     human -> solo, gender from P21.
  2. wikidata_fuzzy : for names unmatched in pass 1, Wikidata's EntitySearch API
     (diacritic-insensitive) top valid human/ensemble hit.
  3. name_heuristic : residual names classified from the string itself -- explicit
     group words (band/trio/brothers/...) -> group; a conjunction of two credited
     acts (X & Y / X and Y / feat.) -> duet; otherwise solo of unknown gender.
  * 2024-2026 finalists are read from a dedicated Wikidata entry query; any the
    query does not cover (chiefly the post-cutoff 2026 final) are left as
    'unresolved_2426' and fall back to the baseline.

Unresolved rows (source in {unresolved, unresolved_2426}) default to the solo-male
baseline (duet=group=female=0); they are ~4-5% of rows and flagged for audit.

NETWORK: makes live calls to query.wikidata.org via curl.  Re-running is only
needed to refresh the classification; the committed output/performer_types.csv is
the product of this script.  Requires `curl` and internet access.
"""

import csv
import json
import os
import re
import subprocess
import time
import urllib.parse

from lib_countries import NAME

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.dirname(HERE)
OUT = os.path.join(HERE, "output")
SPARQL = "https://query.wikidata.org/sparql"
UA = "esc-replication/1.0 (Charron replication; research use)"

HUMAN = "Q5"
ENSEMBLE = "Q2088357"          # musical ensemble (band/duo/trio/... subclasses)
DUO = "Q9212979"               # musical duo
GENDER = {"Q6581072": "solo_female", "Q6581097": "solo_male",
          "Q1052281": "solo_female", "Q2449503": "solo_male",   # trans woman / man
          "Q48270": "solo_nb"}


# ---------------------------------------------------------------------------
# thin SPARQL client
# ---------------------------------------------------------------------------
def sparql(query, timeout=120):
    url = SPARQL + "?format=json&query=" + urllib.parse.quote(query)
    out = subprocess.run(
        ["curl", "-s", "--max-time", str(timeout),
         "-H", "Accept: application/sparql-results+json", "-H", "User-Agent: " + UA, url],
        capture_output=True, text=True).stdout
    return json.loads(out)["results"]["bindings"]


def _esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


# ---------------------------------------------------------------------------
# 1. the roster to classify
# ---------------------------------------------------------------------------
def load_roster():
    """(year, iso2, performer) finalist rows, 1975-2023 from contestants.csv."""
    rows = []
    with open(os.path.join(DATA, "contestants.csv")) as f:
        for r in csv.DictReader(f):
            if not r["year"].isdigit():
                continue
            y = int(r["year"])
            if not (1975 <= y <= 2023):
                continue
            if r.get("running_final", "") == "" and r.get("place_final", "") == "":
                continue
            p = r.get("performer", "").strip()
            if p:
                rows.append((y, r["to_country_id"], p))
    return rows


def load_finalists_2426():
    """(year, iso2, country) finalists 2024-2026 from the scoreboard scrape."""
    rows = []
    with open(os.path.join(OUT, "finalists_eschome.csv")) as f:
        for r in csv.DictReader(f):
            y = int(r["year"])
            if y >= 2024:
                rows.append((y, r["country_id"], r["country"]))
    return rows


# ---------------------------------------------------------------------------
# 2. Wikidata passes
# ---------------------------------------------------------------------------
def _ensemble_duo_flags(qids):
    """For a set of P31 QIDs, which are subclass* of musical ensemble / musical duo."""
    ens, duo = {}, {}
    qids = sorted(qids)
    for k in range(0, len(qids), 200):
        vals = " ".join("wd:" + q for q in qids[k:k + 200])
        b = sparql(f"""SELECT ?c ?e ?d WHERE {{ VALUES ?c {{ {vals} }}
          BIND(EXISTS{{?c wdt:P279* wd:{ENSEMBLE}}} AS ?e)
          BIND(EXISTS{{?c wdt:P279* wd:{DUO}}} AS ?d) }}""")
        for r in b:
            q = r["c"]["value"].split("/")[-1]
            ens[q] = r["e"]["value"] == "true"
            duo[q] = r["d"]["value"] == "true"
    return ens, duo


def pass_exact(names):
    """name -> {'cat','e','source'} via exact English-label match + local disambig."""
    cand = {}
    for k in range(0, len(names), 100):
        vals = " ".join(f'"{_esc(n)}"@en' for n in names[k:k + 100])
        b = sparql(f"""SELECT ?name ?e ?ptype ?gender ?sl WHERE {{
          VALUES ?name {{ {vals} }}
          {{ ?e rdfs:label ?name. }} UNION {{ ?e skos:altLabel ?name. }}
          ?e wikibase:sitelinks ?sl .
          OPTIONAL {{ ?e wdt:P31 ?ptype. }} OPTIONAL {{ ?e wdt:P21 ?gender. }} }}""")
        tmp = {}
        for r in b:
            nm = r["name"]["value"]; e = r["e"]["value"].split("/")[-1]
            rec = tmp.setdefault((nm, e), {"e": e, "sl": int(r["sl"]["value"]),
                                           "p31": set(), "gender": ""})
            if "ptype" in r:
                rec["p31"].add(r["ptype"]["value"].split("/")[-1])
            if "gender" in r:
                rec["gender"] = r["gender"]["value"].split("/")[-1]
        for (nm, e), rec in tmp.items():
            cand.setdefault(nm, []).append(rec)
        time.sleep(0.4)

    allq = {q for v in cand.values() for c in v for q in c["p31"]}
    ens, duo = _ensemble_duo_flags(allq)

    def valid(c):
        return HUMAN in c["p31"] or any(ens.get(q) for q in c["p31"])

    def classify(c):
        if any(duo.get(q) for q in c["p31"]):
            return "duet"
        if any(ens.get(q) for q in c["p31"]):
            return "group"
        if HUMAN in c["p31"]:
            return GENDER.get(c["gender"], "solo_ungendered")
        return "unknown"

    out = {}
    for nm, cs in cand.items():
        v = [c for c in cs if valid(c)]
        if v:
            best = max(v, key=lambda c: c["sl"])
            out[nm] = {"cat": classify(best), "e": best["e"], "source": "wikidata_exact"}
    return out


def pass_fuzzy(names):
    """name -> {'cat','e','source'} via EntitySearch (diacritic-insensitive)."""
    out = {}
    for nm in names:
        q = f'''SELECT ?e ?ord ?h ?g ?d ?gender WHERE {{
          SERVICE wikibase:mwapi {{
            bd:serviceParam wikibase:endpoint "www.wikidata.org".
            bd:serviceParam wikibase:api "EntitySearch".
            bd:serviceParam mwapi:search "{_esc(nm)}". bd:serviceParam mwapi:language "en".
            ?e wikibase:apiOutputItem mwapi:item. ?ord wikibase:apiOrdinal true. }}
          BIND(EXISTS{{?e wdt:P31 wd:{HUMAN}}} AS ?h)
          BIND(EXISTS{{?e wdt:P31/wdt:P279* wd:{ENSEMBLE}}} AS ?g)
          BIND(EXISTS{{?e wdt:P31/wdt:P279* wd:{DUO}}} AS ?d)
          OPTIONAL {{ ?e wdt:P21 ?gender. }} }} ORDER BY ?ord LIMIT 10'''
        try:
            b = sparql(q, timeout=40)
        except Exception:
            time.sleep(2)
            continue
        for r in b:
            h = r["h"]["value"] == "true"; g = r["g"]["value"] == "true"; d = r["d"]["value"] == "true"
            if h or g:
                if d:
                    cat = "duet"
                elif g:
                    cat = "group"
                else:
                    cat = GENDER.get(r.get("gender", {}).get("value", "").split("/")[-1],
                                     "solo_ungendered")
                out[nm] = {"cat": cat, "e": r["e"]["value"].split("/")[-1], "source": "wikidata_fuzzy"}
                break
        time.sleep(0.3)
    return out


_GROUP_KW = re.compile(r"\b(band|group|trio|quartet|quintet|sextet|ensemble|orchestra|"
                       r"choir|brothers|sisters|familja|family|collective|boys|girls|"
                       r"singers|crew|project|feat\.?|featuring)\b", re.I)
_CONJ = re.compile(r"\s(?:&|\+|and|vs\.?|x|feat\.?|featuring|con|e|et|und|ja|és)\s|,", re.I)


def pass_heuristic(name):
    if _GROUP_KW.search(name):
        return {"cat": "group", "source": "name_heuristic", "e": ""}
    if _CONJ.search(name):
        return {"cat": "duet", "source": "name_heuristic", "e": ""}
    return {"cat": "solo_ungendered", "source": "unresolved", "e": ""}


def wikidata_2426():
    """(year, iso2) -> {'cat','performer'} for 2024-2026 ESC entries."""
    b = sparql(f"""SELECT ?year ?countryLabel ?performerLabel ?h ?g ?d ?genderLabel WHERE {{
      ?entry wdt:P31 wd:Q35718073 ; wdt:P585 ?date ; wdt:P17 ?country .
      BIND(YEAR(?date) AS ?year) FILTER(?year >= 2024 && ?year <= 2026)
      {{ ?entry wdt:P175 ?performer. }} UNION {{ ?song wdt:P1344 ?entry ; wdt:P175 ?performer. }}
      BIND(EXISTS{{?performer wdt:P31 wd:{HUMAN}}} AS ?h)
      BIND(EXISTS{{?performer wdt:P31/wdt:P279* wd:{ENSEMBLE}}} AS ?g)
      BIND(EXISTS{{?performer wdt:P31/wdt:P279* wd:{DUO}}} AS ?d)
      OPTIONAL {{ ?performer wdt:P21 ?gender. }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}""")
    aliases = {"czech republic": "cz", "north macedonia": "mk", "republic of ireland": "ie"}
    inv = {v.lower(): k for k, v in NAME.items()}
    gmap = {"female": "solo_female", "male": "solo_male", "trans woman": "solo_female",
            "intersex man": "solo_male", "non-binary": "solo_nb"}
    out = {}
    for r in b:
        y = int(r["year"]["value"])
        lab = r.get("countryLabel", {}).get("value", "").lower()
        iso = aliases.get(lab) or inv.get(lab)
        if not iso:
            continue
        if r["d"]["value"] == "true":
            cat = "duet"
        elif r["g"]["value"] == "true":
            cat = "group"
        elif r["h"]["value"] == "true":
            cat = gmap.get(r.get("genderLabel", {}).get("value", "").lower(), "solo_ungendered")
        else:
            continue
        out[(y, iso)] = {"cat": cat, "performer": r.get("performerLabel", {}).get("value", "")}
    return out


# ---------------------------------------------------------------------------
# 3. assemble
# ---------------------------------------------------------------------------
def dummies(cat):
    return int(cat == "duet"), int(cat == "group"), int(cat == "solo_female")


def main():
    roster = load_roster()
    names = sorted({p for _, _, p in roster})
    print(f"classifying {len(names)} unique performer names (1975-2023) ...")

    cat = pass_exact(names)
    print(f"  exact match: {len(cat)}")
    todo = [n for n in names if n not in cat]
    cat.update({n: v for n, v in pass_fuzzy(todo).items() if n not in cat})
    print(f"  after fuzzy: {len(cat)}")
    for n in names:
        cat.setdefault(n, pass_heuristic(n))

    w2426 = wikidata_2426()
    finals2426 = load_finalists_2426()

    rows = []
    for (y, iso, p) in roster:
        d, g, f = dummies(cat[p]["cat"])
        rows.append([y, iso, p, cat[p]["cat"], d, g, f, cat[p]["source"]])
    for (y, iso, country) in finals2426:
        rec = w2426.get((y, iso))
        if rec:
            c, pname, src = rec["cat"], rec["performer"], "wikidata_2426"
        else:
            c, pname, src = "solo_ungendered", "", "unresolved_2426"
        d, g, f = dummies(c)
        rows.append([y, iso, pname, c, d, g, f, src])

    path = os.path.join(OUT, "performer_types.csv")
    with open(path, "w", newline="") as fo:
        w = csv.writer(fo)
        w.writerow(["year", "country_id", "performer", "perf_type",
                    "duet", "group", "female", "source"])
        w.writerows(sorted(rows))
    print(f"wrote {path}: {len(rows)} rows.")


if __name__ == "__main__":
    main()
