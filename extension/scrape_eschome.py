"""
scrape_eschome.py
=================
Reconstruct the ESC country-to-country final voting record from eschome.net --
the primary source Charron (2013) used (footnote 1) -- for ALL finals in a year
range (default 1975-2026), so the replication can be extended to later years to
test whether Charron's findings still hold.

Where the data lives
---------------------
eschome.net exposes no bulk file; its data sits in a server-side database reached
through POST forms.  The relevant endpoint is:

    POST https://eschome.net/databaseoutput433.php
         land = <ISO-2-ish country code>   (the point GIVER)
         jahr = <year+round code>          ("1975" pre-2004, "2010F" from 2004)

which returns, for that giver in that final, a table:
    Country (receiver) | Points (total) | Points J (jury) | Points T (televote) | ...
For 1975-2015 only the combined "Points" column is populated (0-12); from 2016
"Points" is jury+televote combined (0-24) and the J/T split is also given.

Output
------
`output/votes_eschome.csv` in the SAME schema as the bundled votes.csv, so the
existing pipeline can consume it unchanged:
    year, round, from_country_id, to_country_id, from_country, to_country,
    total_points, tele_points, jury_points

Politeness
----------
Every response is cached to `output/eschome_cache/` (so re-runs are free and the
scrape is resumable), requests are rate-limited, and a descriptive User-Agent is
sent.  Run:  python3 scrape_eschome.py [start_year] [end_year]
"""

import csv
import os
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request

# This Python's default trust store can't verify eschome's cert; use certifi's
# CA bundle if available, otherwise fall back to an unverified context (the data
# is public and read-only, so this only affects transport verification).
try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    SSL_CTX = ssl._create_unverified_context()

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
CACHE = os.path.join(OUT, "eschome_cache")
os.makedirs(CACHE, exist_ok=True)

BASE = "https://eschome.net/databaseoutput433.php"
UA = "eschome-research-scraper/1.0 (academic replication; contact via project)"
DELAY = 0.7                          # seconds between live requests (be gentle)

# eschome giver codes -> our lower-case pipeline codes.  XX = "Rest of the World"
# aggregated online televote (from 2023): it is a *giver* only (it never
# competes / receives), and is INCLUDED because it is a useful bias-neutral
# benchmark voter for the analysis.  It maps to code 'xx'.
ESC_CODES = ["AL","AD","AM","AU","AT","AZ","BY","BE","BA","BG","HR","CY","CZ",
             "DK","EE","FI","FR","GE","DE","GR","HU","IS","IE","IL","IT","LV",
             "LT","LU","MT","MA","MD","MC","ME","NL","MK","NO","PL","PT","RO",
             "RU","SM","RS","CS","SK","SI","ES","SE","CH","TR","UA","GB","YU","XX"]

# Canonical receiver-name -> code map (from eschome's own country list), plus a
# few historical aliases so older result rows still resolve.
NAME2CODE = {
    "Albania":"al","Andorra":"ad","Armenia":"am","Australia":"au","Austria":"at",
    "Azerbaijan":"az","Belarus":"by","Belgium":"be","Bosnia & Herzegovina":"ba",
    "Bulgaria":"bg","Croatia":"hr","Cyprus":"cy","Czechia":"cz","Denmark":"dk",
    "Estonia":"ee","Finland":"fi","France":"fr","Georgia":"ge","Germany":"de",
    "Greece":"gr","Hungary":"hu","Iceland":"is","Ireland":"ie","Israel":"il",
    "Italy":"it","Latvia":"lv","Lithuania":"lt","Luxembourg":"lu","Malta":"mt",
    "Marocco":"ma","Morocco":"ma","Moldova":"md","Monaco":"mc","Montenegro":"me",
    "Netherlands":"nl","North Macedonia":"mk","Macedonia":"mk","Norway":"no",
    "Poland":"pl","Portugal":"pt","Romania":"ro","Russia":"ru","San Marino":"sm",
    "Serbia":"rs","Serbia & Montenegro":"cs","Slovakia":"sk","Slovenia":"si",
    "Spain":"es","Sweden":"se","Switzerland":"ch","Turkey":"tr","Ukraine":"ua",
    "United Kingdom":"gb","Yugoslavia":"yu", "Czech Republic":"cz",
}


def jahr_code(year):
    """Final-round code: plain year up to 2003, 'YYYYF' from 2004 (semifinals)."""
    return str(year) if year <= 2003 else f"{year}F"


def fetch(land, jahr):
    """Return raw HTML for (land, jahr), from cache if present else live POST."""
    cpath = os.path.join(CACHE, f"{land}_{jahr}.html")
    if os.path.exists(cpath):
        with open(cpath, encoding="utf-8", errors="ignore") as f:
            return f.read(), True
    data = urllib.parse.urlencode({"land": land, "jahr": jahr}).encode()
    req = urllib.request.Request(BASE, data=data, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30, context=SSL_CTX) as r:
        html = r.read().decode("utf-8", "ignore")
    with open(cpath, "w", encoding="utf-8") as f:
        f.write(html)
    time.sleep(DELAY)                # rate-limit only on live hits
    return html, False


def parse(html):
    """Yield (receiver_name, total, juryP, teleP) rows from a 433 response.
    Returns [] for 'did not vote' / 'not allowed' / empty pages."""
    if "did not vote" in html or "not allowed" in html:
        return []
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S)
    out = []
    for r in rows:
        cells = [re.sub(r"<[^>]+>", "", c).strip()
                 for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S)]
        # data rows look like ['', Country, Points, PointsJ, PointsT, ...]
        if len(cells) >= 5 and cells[1] in NAME2CODE and cells[2].isdigit():
            total = int(cells[2])
            jury = int(cells[3]) if cells[3].isdigit() else ""
            tele = int(cells[4]) if cells[4].isdigit() else ""
            out.append((cells[1], total, jury, tele))
    return out


def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 1975
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 2026
    rows = []
    live = cached = skipped = 0
    for year in range(start, end + 1):
        jahr = jahr_code(year)
        for land in ESC_CODES:
            code_i = land.lower()
            try:
                html, from_cache = fetch(land, jahr)
            except Exception as e:
                print(f"  ! {land} {jahr}: {e}")
                continue
            live += (not from_cache); cached += from_cache
            recs = parse(html)
            if not recs:
                skipped += 1
                continue
            for name, total, jury, tele in recs:
                code_j = NAME2CODE[name]
                if code_j == code_i:
                    continue
                rows.append([year, "final", code_i, code_j, code_i, code_j,
                             total, tele, jury])
        print(f"  {year}: cumulative rows={len(rows)} (live={live}, cached={cached})")

    # Write in the bundled votes.csv schema.
    path = os.path.join(OUT, "votes_eschome.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["year", "round", "from_country_id", "to_country_id",
                    "from_country", "to_country", "total_points",
                    "tele_points", "jury_points"])
        w.writerows(rows)
    print(f"\nvotes_eschome.csv written: {len(rows):,} dyad rows, {start}-{end}. "
          f"(live requests={live}, cache hits={cached}, empty (did-not-vote)={skipped})")


if __name__ == "__main__":
    main()
