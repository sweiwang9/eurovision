# Eurovision Song Contest — Voting Rules Through the Years

A reference for the voting-bias research. Three things changed independently over
time and should not be conflated: **(A) the points scale**, **(B) who casts the
vote** (juries / public / both), and **(C) the contest structure** (single final,
relegation, semi-finals, auto-qualifiers). Items marked ✔ are directly
corroborated by this project's scraped data (`votes_eschome.csv`, 1975–2026).

---

## A. The points scale

| Years | Scale each country awards | Notes |
|---|---|---|
| 1956 | 2 jurors/country, each scored **every song 1–10** | Only the winner was announced |
| 1957–1961 | 10 jurors each give **1 point** to their favourite (10 pts/country, spreadable) | |
| 1962 | **3–2–1** to top 3 | First "ranked points" system |
| 1963 | **5–4–3–2–1** to top 5 | |
| 1964–1966 | 9 points: 5–3–1, or 6–3, or 9 to one song | |
| 1967–1970 | Back to 10 jurors × **1 point** each | |
| 1971–1973 | 2 jurors/country, each gives **1–5** to *every* song (min 1) | Everyone scores |
| 1974 | Same 2-juror 1–5 system | |
| **1975–present** | **12, 10, 8, 7, 6, 5, 4, 3, 2, 1** to the top ten (no 9, no 11) | ✔ The modern "douze points" system; the sample window of Charron (2013) and this project |

The 1975 reform is why serious voting-bias analysis (incl. Charron) starts in
1975 — it is the first year with a consistent, comparable preference-ranking
scale. ✔ Confirmed in the data: single-source awards take only values
{0,1,2,3,4,5,6,7,8,10,12}.

---

## B. Who casts the vote (juries → public → hybrid → split)

| Years | Who decides each country's points |
|---|---|
| 1956–1996 | **National expert juries** (size/rules varied) |
| **1997** | **Televoting trial**: 5 countries use a public televote (Austria, Germany, Sweden, Switzerland, UK), the other 20 still use juries |
| **1998–2000** | Televoting **encouraged for all**, juries retained only as backup — effectively the public-vote era begins |
| **2001–2002** | Broadcasters could **choose** full televote *or* a 50/50 jury+televote mix |
| **2003** | Televote + SMS, juries as backup for technical failure |
| **2004–2007** | Televote/SMS for all, with 8-member **backup juries**; the **final** was ~100% public. From **2008** juries also picked one semi-final "wildcard" qualifier |
| **2009–2012** | **50% jury + 50% televote**, combined into ONE 1–12 set per country (juries return after televote-only era) |
| **2013–2015** | Same 50/50, but juries and televoters now **rank all entries**, not just their top ten |
| **2016–2017** | **Split reveal**: jury and public each award an **independent** set of 1–12 (two 12-sets per country → combined totals up to 24) |
| **2018–2022** | Same split; jury scores use an **exponential weighting** model |
| **2023–2025** | **Semi-finals decided by public televote only** (juries as backup); the **final** keeps the split jury+televote sets; **"Rest of the World"** aggregated online vote added (counts as one extra "country", in semis and final) |
| **2026** | **Juries return to the semi-finals** (≈50/50, first time since 2022); jury panels expand **5 → 7 members** (incl. ≥2 aged 18–25); with RoW counted as one country the Grand Final split is **50.7% audience / 49.3% jury**; max votes per person/method **cut 20 → 10**; promotion-campaign rules tightened; fraud-detection expanded |

Key consequences for the data (all ✔ in `votes_eschome.csv`):
- **Pre-2016**: one 0–12 number per ordered country pair per final.
- **2016+**: the recorded *total* per pair runs **0–24** = jury(0–12) + televote(0–12);
  the jury and televote halves are stored separately (`vote_jury`, `vote_tele`).
- **2023+**: a giver coded **`xx` = "Rest of the World"** appears (online public
  vote from non-participating countries), giving televote points only. It is a
  *giver only* — it never competes/receives. In this project it is kept as the
  variable `row_points_j` and excluded from country-to-country dyads.

For Charron-style analysis the important eras are: **jury era 1975–1997**,
**televote era 1998–2008**, **hybrid 50/50 era 2009–2015**, and **split era
2016–present** (where jury vs televote can be analysed separately).

---

## C. Contest structure & qualification

| Era | Structure |
|---|---|
| 1956–1993 | Single **final**, all participants perform and vote |
| 1993–2003 | **Relegation**: lowest-placed countries sit out the *next* contest to cap the field. ✔ e.g. Greece was relegated in 1999–2000 after a low 1998 result, so it cast **no votes** those years |
| **2004** | First **semi-final** (one), held days before the final; non-qualifiers still **vote in the final** |
| **2008–present** | **Two semi-finals**; each participant is allocated to one semi. ✔ Finalist rosters in `finalists_eschome.csv` reflect this |
| Auto-qualifiers | The **host** plus the **"Big Four"** (France, Germany, Spain, UK) auto-qualify to the final from 2000; **Italy** returns in 2011 making the **"Big Five"** |
| Semi-final voting | From 2004, semi-final-eliminated countries **still vote in the final** — so "finalist" (performed) ≠ "voter" (cast points). This project therefore identifies finalists **explicitly** from the scoreboard roster, not from who received points |

---

## D. Other standing rules relevant to bias research

- **No self-voting**: a country never awards points to itself. ✔ (no i==j rows.)
- **Songs**: max 3 minutes; language rules varied (native-language requirement
  1966–1972 and 1978–1998; free choice otherwise) — not a *voting* rule but
  affects the "language" and "English/French" controls.
- **One entry per country per year**; all EBU-member broadcasters eligible
  (hence non-"European" entrants like Israel, and Australia from 2015).
- **Weighting**: all participating countries' votes are weighted equally
  regardless of population.

---

## E. Quick timeline of the changes that matter most for voting bias

```
1975  modern 12-10-8..1 scale begins              (analysis start)
1997  televoting trial (5 countries)
1998  televoting becomes standard (public vote)    <- Charron's split point
2004  first semi-final; non-finalists vote in final
2008  two semi-finals
2009  50/50 jury + televote in the final
2016  jury & televote split into two 1-12 sets      <- 0-24 combined totals
2023  Rest-of-World online vote; juries dropped from semis
2026  juries return to semis; 7-member juries; max votes 20->10
```

*Corroborated in this project's data: the 1975 scale, 2004/2008 semi-final
rosters, the 2016 split (0–24 combined totals), and the 2023 Rest-of-World giver
(`xx`) are all directly visible in the scraped eschome data.*

## Sources
- [Voting at the Eurovision Song Contest — Wikipedia](https://en.wikipedia.org/wiki/Voting_at_the_Eurovision_Song_Contest) (full scoring/voting-method history)
- [EBU: changes to Eurovision voting rules (Nov 2025, for 2026)](https://www.ebu.ch/news/2025/11/ebu-announces-changes-to-eurovision-song-contest-voting-rules-to-strengthen-trust-and-transparency) (official governing-body announcement)
- [eurovisionworld.com — major changes to the voting system](https://eurovisionworld.com/esc/major-changes-to-the-eurovision-voting-system)
- Eurovision Song Contest 2024 — [Wikipedia](https://en.wikipedia.org/wiki/Eurovision_Song_Contest_2024) (Rest-of-World window, semis televote-only)
- Note: the official site **eurovision.tv** is Cloudflare-protected and blocks automated access (HTTP 403), so the EBU announcement and Wikipedia's cited history were used as the authoritative sources.
