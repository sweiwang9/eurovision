"""
scrape_finalists.py
==================
Build an EXPLICIT list of who performed in each ESC final, rather than inferring
"finalist" from whether a country received points (which would wrongly drop a
finalist that scored 0 from everyone).

Source: eschome's scoreboard endpoint `databaseoutput401.php` ("Result of
<year> Final"), whose rows are:
    Place | Points | No. (running order) | <flag=CODE> | Country | Performer | ...
Every performer is listed regardless of points, so this is the authoritative
finalist roster.  It also gives the running order and final placing, which are
useful controls for the extended analysis.

Output: `output/finalists_eschome.csv` with columns
    year, country_id, country, running_final, place_final, points_final
"""

import csv
import os
import re
import ssl
import time
import urllib.parse
import urllib.request

try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    SSL_CTX = ssl._create_unverified_context()

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
CACHE = os.path.join(OUT, "eschome_cache")
os.makedirs(CACHE, exist_ok=True)

BASE = "https://eschome.net/databaseoutput401.php"
UA = "eschome-research-scraper/1.0 (academic replication)"
DELAY = 0.7


def jahr_code(year):
    return str(year) if year <= 2003 else f"{year}F"


def fetch(jahr):
    cpath = os.path.join(CACHE, f"SCOREBOARD_{jahr}.html")
    if os.path.exists(cpath):
        with open(cpath, encoding="utf-8", errors="ignore") as f:
            return f.read()
    data = urllib.parse.urlencode({"jahr": jahr, "details": "1"}).encode()
    req = urllib.request.Request(BASE, data=data, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30, context=SSL_CTX) as r:
        html = r.read().decode("utf-8", "ignore")
    with open(cpath, "w", encoding="utf-8") as f:
        f.write(html)
    time.sleep(DELAY)
    return html


def parse(html, year):
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S)
    out = []
    for r in rows:
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S)
        if len(cells) < 5:
            continue
        place = re.sub(r"<[^>]+>", "", cells[0]).strip()
        points = re.sub(r"<[^>]+>", "", cells[1]).strip()
        running = re.sub(r"<[^>]+>", "", cells[2]).strip()
        m = re.search(r"/flags/([A-Za-z]{2})\.png", cells[3])
        name = re.sub(r"<[^>]+>", "", cells[4]).strip()
        if not place.isdigit() or not m:          # only real performer rows
            continue
        code = m.group(1).lower()
        out.append([year, code, name,
                    running if running.isdigit() else "",
                    place, points if points.isdigit() else ""])
    return out


def main(start=1975, end=2026):
    rows = []
    for year in range(start, end + 1):
        html = fetch(jahr_code(year))
        recs = parse(html, year)
        rows.extend(recs)
        print(f"  {year}: {len(recs)} finalists")
    path = os.path.join(OUT, "finalists_eschome.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["year", "country_id", "country", "running_final",
                    "place_final", "points_final"])
        w.writerows(rows)
    print(f"\nfinalists_eschome.csv written: {len(rows):,} finalist-years, {start}-{end}.")


if __name__ == "__main__":
    main()
