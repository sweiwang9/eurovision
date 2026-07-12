# Session Summary — Charron (2013) Replication + Extension

A running log of the prompts given and the results produced.

> **This is the `replication/` log — from Prompt 16 on it records only
> replication-folder updates (faithful Charron 1975–2012; `run_all.py`).**
> Extension-folder work is logged separately in `extension/SUMMARY.md`.  Entries
> **through Prompt 15** predate this split and are the shared project history, kept
> identically in both files as the common baseline; new entries diverge by folder.
> Pre-split entries mention bare `output/` paths from when the project was a single
> folder — those artifacts now live under `replication/output/` (see Prompt 15).

---

## Prompt 1
> *"You are an academic researcher who is an expert in statistical analysis.
> Please write code that replicates all the tables and figures in the Charron
> 2013 paper. Check first if the data in the folder is sufficient. Please
> comment each block of code carefully."*

### What was done
1. **Read the paper** (`Charron_Eurovision_SN_2013.pdf`) to enumerate every
   object to replicate: Tables 1–4, Figs 1–3, Appendix 3.
2. **Audited the data folder** and reported sufficiency (details below).
3. **Validated the core method** before coding: the dyad-specific Quality
   formula `(Total_j − vote_ij)/(p−2)` reproduces the paper's Table 1 values
   exactly (Greece→Cyprus 7.1, Turkey→Bosnia 6.7, Croatia→Malta 5.6, etc.).
4. **Wrote a fully-commented Python replication** (Python chosen because the
   installed R had no packages; Python had the full scientific stack).

### Data sufficiency verdict
- **Sufficient (✅):** votes (`votes.csv`), Quality/Bias (derived), Impartiality
  (`qog_std_ts_jan26.csv → icrg_qog`, 1984–2025), Friend Dyads (derived),
  Song Order & Host (`contestants.csv`), Lag Vote, No. Participants.
- **Reconstructed (⚠️):** Contiguity & shared Language (hard-coded standard
  facts in `lib_countries.py`); English/French dummies (lyrics heuristic).
- **Not reproducible (❌):** Duet/Group/Female song traits and Diaspora — not
  present in the data folder. Those specific Table 3/4 columns are omitted.
- `betting_offices.csv` and the `eurovision-dataset-2023` archives are unused.

### Files written
| File | Purpose |
|---|---|
| `lib_countries.py` | names, ISO2→ISO3, contiguity, shared-language |
| `tobit.py` | right-censored Tobit MLE, robust SEs |
| `pairwise_bias.py` | significant pairwise-bias helper |
| `build_dataset.py` | master dyad-year panel → `output/master.csv` |
| `table1.py` | Table 1 |
| `cluster_table2_fig1.py` | Table 2 + Fig 1 |
| `fig2_network.py` | Fig 2 |
| `appendix3.py` | Appendix 3 |
| `regressions_table3_4_fig3.py` | Tables 3 & 4 + Fig 3 |
| `run_all.py` | one-shot driver |
| `README.md` | full documentation |

### Results vs. the published paper
- **Table 1** — headline biased dyads match (Macedonia→Albania 9.4→9.5,
  France→Portugal 8.2→8.3, Lithuania→Georgia 7.8, Greece↔Cyprus, etc.).
- **Table 2 / Fig 1** — recovers the paper's blocs (Greece–Cyprus,
  Romania–Moldova, Spain–Portugal, UK–Ireland, Balkan, Nordic+Baltic,
  ex-Soviet). *Method note:* clustering on mutual voting affinity (not literal
  Ward-on-portfolio, which fails to merge reciprocal pairs) reproduces the
  published groups; documented in the script.
- **Appendix 3** — Greece–Cyprus within-group bias **7.89** (paper 7.88);
  Romania–Moldova **9.45** (paper 9.34); blocs significantly positive.
- **Table 3** — Quality **0.89** (paper 0.90); Friend Dyad +***; Impartiality
  n.s. (paper 0.22 n.s.); **Friend × Impartiality negative & significant**
  (paper −6.61***) → **H1 confirmed**; Contiguity 0.85 (paper 0.80); lag votes
  0.175 / 0.061 (paper 0.17 / 0.06).
- **Table 4** — method-2 Friend Dyad 5.9–7.6 and interaction −1.1 to −3.9,
  inside the paper's ranges (4.9–7.5; −1.0 to −4.4).
- **Fig 3** — non-friend lines indistinguishable across impartiality; friend
  bias much larger under low impartiality — matches the paper's shape.

### A bug caught and fixed mid-build
The method-2 friend measure initially flagged ~96% of dyads (the merge ignored
the significance flag). After the fix, the objective friend measure correctly
reproduced H1, which also revealed the first cluster feature was too coarse →
switched to mutual-affinity clustering.

---

## Prompt 2
> *"Please keep a summary file of all the prompts and results."*

### What was done
Created this file (`SUMMARY.md`) and will append each subsequent prompt and its
outcome here.

---

## Prompt 3
> *"The replicated numbers must be exact. Go back and figure out why the numbers
> differ by reading the details in the paper. Also, why can't you use R? for
> example, R has a tobit package."*

### On exactness — what was investigated and fixed
- **Re-read the Quality definition** (eq. 1): confirmed it is *dyad-specific*,
  `(Total_j − vote_ij)/(p−2)`. Tested alternative denominators against the real
  Greece→Cyprus votes — none change the conclusion.
- **Found and applied a faithful fix:** restrict to **finalist→finalist** dyads
  (from 2004 semi-final-eliminated countries still vote but are not "in the
  final"). This improved matches: Romania→Moldova 9.99 → **9.7** (paper 9.6),
  Turkey↔Azerbaijan → **8.4** (paper 8.0/8.5), France→Portugal **8.3** (8.2).
  Implemented in `build_dataset.py` (`load_finalists`).
- **Explained the irreducible residual:** exact match on a few extreme pairs
  (Greece→Cyprus) is impossible because *this* 2023 dataset records Greece giving
  Cyprus 12 in every relevant final, so bias is mathematically ~10.2, not the
  paper's 8.5. The paper used the author's own eschome.net data (footnote 1),
  which differs. This is data provenance, not a code/formula bug. Documented in
  `README.md` §3 with the evidence.

### On R — resolved
- R *is* usable; it simply shipped with no packages. Installed `AER`,
  `sandwich`, `lmtest` and wrote **`regressions.R`**, which reproduces Table 3 &
  Table 4 with the genuine **`AER::tobit`** (right-censored `survreg`).
- R and Python agree to ~2 decimals (e.g., Table 3 Quality 0.908 vs 0.910;
  Friend Dyad +4.8***, interaction −2.8/−3.3***), cross-validating the estimator.
- Python's `regressions_table3_4_fig3.py` now also exports
  `output/regression_data.csv` for the R script to consume.

---

## Prompt 4
> *"yes please do everything else in R as well and let me look into the original
> data and get back to you."*

### What was done — full parallel R pipeline
Ported the entire replication to R (previously only the regressions were in R):
- `lib_countries.R` — names, ISO codes, contiguity, shared-language.
- `build_dataset.R` — master panel; **matches the Python master to machine
  precision** (max abs diff in quality/bias/impartiality ≈ 1e-14).
- `table1.R` — Table 1 (identical numbers to Python).
- `cluster_table2_fig1.R` — Table 2 + Fig 1 dendrogram (base `hclust`,
  average linkage on mutual-affinity distance). Fig 1 cleanly shows the paper's
  blocs.
- `fig2_network.R` — Fig 2 via `igraph`.
- `appendix3.R` — within-group bias + stability (fixed an NA-subsetting bug:
  `gi==gj` returns NA when a receiver is ungrouped, so guarded with `which()`
  and `!is.na` on both sides).
- `regressions.R` — now standalone: builds the friend-merged frame from R
  outputs and runs Table 3/4 with `AER::tobit`, plus Fig 3.
- `run_all.R` — one-shot R driver. Outputs use an `_R` suffix.

R and Python agree throughout (Table 3 Quality ≈0.88, Friend Dyad +4.8***,
interaction −2.8 to −4.1***; Table 4 method-2 Friend Dyad ≈8.1***).

### Pending (user action)
User is retrieving the **original eschome.net vote data**; once provided, swap
it in for `votes.csv` and the Table 1 extreme dyads (e.g. Greece→Cyprus) should
match the paper's decimals.

---

## Prompt 5–7 (eschome scraper + source verification)
> *"where does the data reside" → "write the scraper for all years up to 2026" →
> "check for mismatches with the bundled data and verify against the official
> Eurovision website which is correct."*

### Where the data resides
eschome.net has no bulk file; data sits behind POST endpoints
`databaseoutputNNN.php`. The dyadic voting record is `databaseoutput433.php`
(`land`=giver, `jahr`=`YYYY` pre-2004 / `YYYYF` from 2004) returning
Country | Points | Points J (jury) | Points T (televote).

### Scraper
`scrape_eschome.py` — polite (cached, resumable, ~0.7s/req), SSL via certifi.
Pulled **all finals 1975–2026 → `output/votes_eschome.csv`, 33,557 dyad rows**
(2,652 live requests). Stores total + jury + televote so the 2016+ split era can
be analysed either way.

### Source comparison (`compare_sources.py`) — verdict
- **Zero value disagreements** on the 32,005 overlapping dyads. Where both
  sources have a real vote, they are identical.
- "bundled-only" 1975–2023 (~24/yr) = **self-vote 0-rows** (artifacts eschome
  correctly omits; pipeline already ignores i==j).
- "bundled-only" 1957–1974 = pre-1975 finals (scrape scoped to 1975+).
- "eschome-only" = **2024–2026** (genuine new-year extension).

### Official verification
eschome's own scoreboard for 2024 final = **591/547/453/445/375/278**, an exact
match to the official Eurovision result. My dyadic totals sit slightly below only
because I exclude the **"Rest of the World" (XX)** online televote (2023+, not a
country dyad); each gap equals XX's contribution exactly (e.g. Switzerland 591−585
= 6 = XX→Switzerland). So all three (eschome, bundled, official) agree.

### Correction to earlier claim
The Greece→Cyprus Table-1 gap (my 10.2 vs paper **9.0** — see Prompt 8; an
earlier note mis-said 8.5) is **not** a data-provenance issue: Charron's actual
source (eschome) also has Greece giving Cyprus 12 every final. The gap comes from
televote-era sample composition, not the vote values — resolved under Prompt 8.

### For the later-years extension (open decisions)
- Rest-of-World (XX) excluded from dyads (correct for pairwise bias).
- 2016+ `total_points` = jury+televote (0–24); decide whether to analyse the
  combined scale or jury/televote separately (both are stored).

---

## Prompt 8 (include Rest-of-World; resolve the irreproducible Table 1 numbers)

### Rest-of-World added
`scrape_eschome.py` now includes giver code `XX` -> `xx` ("Rest of the World"
online televote, 2023+; giver-only, never a receiver). `votes_eschome.csv` now
has 33,613 rows incl. 56 `xx` giver-rows (2023-2026) as a bias-neutral benchmark
voter for the analysis.

### Table 1 puzzle (`diagnose_table1.py`)
CORRECTION: an earlier version misread the paper's Greece->Cyprus 1998-2012 bias
as 8.5; the correct value is **9.0** (8.5 is rows 5-6, Azerbaijan->Turkey and
Serbia->Macedonia). Corrected findings:
1. **Vote values are correct** — eschome == bundled == official (verified).
2. **The Quality/Bias method is Charron's** — the 1975-1997 column reproduces
   the paper essentially exactly (8 of 10 dyads to the decimal: gr->cy 7.1,
   tr->ba 6.7, hr->mt 5.6, si->ru 5.1, ee->fr 4.6, nl->ru 4.5, fi->it 3.6,
   pl->hu 3.5).
3. **1998-2012: 6 of 10 dyads reproduce within +/-0.4** (ro->md +0.1, mk->al
   +0.1, az->tr -0.1, fr->pt +0.1, it->ro -0.2, tr->az +0.4). Four differ:
   gr->cy 10.2 vs 9.0 (+1.2), md->ro 8.5 vs 9.2 (-0.7), and two n=2 pairs
   (rs->mk, lt->ge) that are inherently unstable.
4. **No single formula fixes them** — the well-sampled outliers diverge in
   OPPOSITE directions (gr->cy high, md->ro low), and gr->cy cannot fall below
   ~9.68 under any quality def (`T/(p-2)`) because Greece gave Cyprus 12 every
   year against a very low Cyprus quality. So the residual is televote/semifinal
   -era sample composition + small-n (n=2) noise, not a vote/formula error.

**Conclusion:** method and vote values are correct; the modest 1998-2012 residuals
reflect which televote-era dyad-year observations enter each average plus n=2
noise. Purely descriptive; the regression results (the paper's claims) reproduce
robustly. `diagnose_table1.py` reproduces the argument.

---

## Prompt 9 (explicit finalist identification)
Flaw caught: inferring "finalist" from whether a country received points would
wrongly drop a finalist that scored 0 from everyone. Fix: `scrape_finalists.py`
scrapes eschome's scoreboard (`databaseoutput401.php`) into
`output/finalists_eschome.csv` (year, country_id, country, running_final,
place_final, points_final) — the authoritative performer roster, plus running
order and final placing as bonus controls. `diagnose_table1.py` now uses this
explicit roster. Verification: the explicit roster == the receiver-based set
(0 differences), because eschome lists explicit 0-point rows for every finalist,
so all Table-1 numbers are unchanged and confirmed. (The main `build_dataset.py`
already identified finalists explicitly via contestants.csv running_final/
place_final, so the regressions were never affected either.)

---

## Prompt 10 (fold explicit finalists into build_dataset; extended panel)
`build_dataset.py` is now source-aware:
- `python3 build_dataset.py` (default) -> `output/master.csv`, bundled source,
  1975-2012 (validated replication, unchanged; downstream scripts unaffected).
- `python3 build_dataset.py --source eschome` -> `output/master_extended.csv`,
  scraped source, **1975-2026** (24,983 dyad-years, 46 countries).

The extended panel identifies finalists from the EXPLICIT scoreboard roster
(`finalists_eschome.csv`) and carries extra columns:
- `running_final`, `place_final` — explicit finalist attributes of receiver j
  (100% populated); `song_order` = `running_final`.
- `row_points_j` — points j got from the Rest-of-World online televote (2023+).
- `vote` = total (0-12 pre-2016, **0-24 = jury+televote from 2016**), plus
  `vote_jury` and `vote_tele` (each 0-12, populated from 2016) so the later-years
  analysis can run on a consistent 0-12 scale.
- `english`/`french` from lyrics where available (contestants.csv ends 2023, so
  NaN for 2024-2026).

CAVEAT for the extension: because 2016+ `vote` is 0-24, decide up front whether to
analyse `vote_jury`/`vote_tele` separately (each 0-12, Charron-comparable) or the
combined scale; the columns are provided for either.

---

## Prompt 11 (run Tables 3 & 4 on the extended data through 2026)
Added 4 later ESC entrants to lib_countries (au Australia, cz Czechia, me
Montenegro, sm San Marino; SMR/MNE lack ICRG -> sample-mean impartiality).
Czechia == Czech Republic: eschome already uses one code `cz` for all years.
Rebuilt master_extended.csv -> 50 countries, 25,901 dyad-years, 1975-2026.

`extend_table3_4.py` re-estimates Table 3 & 4 on the extended panel:
- DV = consistent 0-12 public vote (`vote12`): the single vote 1975-2015, the
  0-12 TELEVOTE component for 2016+ (combined 2016+ total is 0-24).
- Quality/Bias/lags recomputed on vote12; friend dyads recomputed (method 1
  clusters + method 2 sig-bias) over 1975-1997 and 1998-2026; english/french
  dropped (no 2024-26 lyrics).

RESULT — Charron's H1 (Friend x Impartiality < 0) holds pooled and through 2015,
but breaks down in the 2016-2026 split-vote era:
  All 1975-2026: fm1xImp -1.78***, fm2xImp -3.37***
  1975-1997 jury: -2.48***;  1998-2008 televote: -2.41***;  2009-2015 hybrid: -3.38***
  2016-2026 split (televote DV): fm1xImp +0.97*/+1.35 n.s., fm2xImp -1.51 n.s.
Quality ~0.90, Friend Dyad +~4***, Impartiality n.s., contig/language/lags all
significant -- the rest of the model stays Charron-like across 1975-2026.
Interpretation: the public televote in the recent era appears friend/diaspora-
biased regardless of the voter country's impartiality (also fewer years -> less
power). Outputs: table3_extended.txt, table4_extended.txt.
Jury-half robustness check (`extend_table3_4.py --dv2016 jury`, separate outputs
table3/4_extended_jury2016.txt; does NOT replace the televote main analysis):
with the JURY vote as the 2016+ DV, the moderation RETURNS in 2016-2026 --
fm2xImp -3.78*** and fm1xImp -1.64*** (vs televote +0.97*/-1.51 n.s.). So the
breakdown is specific to the public televote; juries (experts) in impartial
countries still reward quality over friendship. This strengthens Charron's
mechanism (impartiality works via meritocratic/expert judgment) while showing the
mass public vote has drifted from it.

---

## Prompt 12 (comprehensive Eurovision voting-rules summary)
Created `eurovision_voting_rules.md` — a full reference covering (A) the points
scale by era (1956 → 1975 modern 12-10-8..1 → present), (B) who votes (juries →
1997 trial → televote → 2009 50/50 → 2016 split → 2023 Rest-of-World → 2026
juries return to semis), and (C) structure (relegation 1993-2003, semis from
2004/2008, Big Four/Five). eschome's "voting procedure" endpoints only cover show
timing, not scoring rules. On request, verified against the OFFICIAL record:
eurovision.tv is Cloudflare-blocked (HTTP 403), so used the EBU Nov-2025
announcement (2026 changes: 7-member juries, juries back in semis, max votes
20->10, final split 50.7/49.3) and Wikipedia's voting-history article; key
transitions (1975 scale, 2004/2008 semis, 2016 split -> 0-24 totals, 2023 `xx`
Rest-of-World) are corroborated by this project's scraped data. Sources listed in
the file.

---

## Prompt 13 (recover the previously-omitted variables: Diaspora + performer traits; extend all to 2026)
The two variables flagged "Not reproducible" in Prompt 1 (Diaspora; Duet/Group/
Female performer traits) are now recovered and folded into the pipeline, and the
extension/impartiality carried through 2026.

**Diaspora (`diaspora.py`).** Transcribed Charron's **Appendix 2** (39 host
countries x top-5 minority groups) directly from the paper and coded it inversely
5..1.  `diaspora(i,j)` = size-rank of the receiver-j minority living in voter i
(0 if not in i's top 5); direction matches the paper's Germany->Turkey = 5 example
and the DV (vote i->j).  "Jewish" -> Israel per the Appendix-2 note; historical
`cs`/`yu` aliased to `rs`.  Wired into `build_dataset.py::add_dyadic` -> `diaspora`
column (both panels; ~13% of dyads non-zero).

**Performer traits (`build_performer_types.py` -> `output/performer_types.csv`).**
Authoritative classification of every finalist act into solo-male / solo-female /
duet / group via **Wikidata** (each act's P31 'instance of' + P21 'sex or gender').
Three passes, each logged in a `source` column: (1) exact English-label VALUES
match with local disambiguation (keep human Q5 / musical-ensemble Q2088357
subclass, max sitelinks) -> ~879 names; (2) EntitySearch fuzzy for diacritic/
spelling misses -> ~118 more; (3) name-pattern heuristic for the residual multi-
artist strings.  2024-2026 finalists pulled from a dedicated Wikidata entry query.
Net: ~95% resolved authoritatively; ~5% unresolved rows (obscure diacritic-heavy
soloists + the post-cutoff 2026 final) are flagged and default to the solo-male
baseline.  Duet/Group/Female dummies attached to receiver j in `build_dataset.py`
(100% column coverage; Female ~39%, Group ~20%, Duet ~11%).

*Wikidata modeling note:* ESC **entry** items (P31 `Q35718073`) carry P17 country +
P585 year but link the performer only sparsely; the reliable signal is the
**performer entity** itself (P31/P21), so we match on performer name, not on the
entry graph.

**Impartiality to 2026.** ICRG (`icrg_qog`) in the QoG file (updated to the
`qog_std_ts_jan26.csv` release, coverage 1984-2025) runs to 2025; it is highly
persistent, so `load_impartiality` carries 2025 forward to 2026 (ffill) -- the
same sticky/apply-forward logic Charron uses for sparse years -- giving 100% imp
coverage 1975-2026 (documented in code).

**Regressions re-run with the recovered controls.**
- Main replication (`regressions_table3_4_fig3.py`, 1975-2012): the placeholder
  "OLS 98-12+Dia" column is now real -> **Diaspora +0.66*** (p<.01)**; Table 4
  "M2 98+Dia" -> **Diaspora +0.35*** ** -- diaspora minorities reward their
  homeland, exactly Charron's prediction.  Duet/Group/Female small & mostly n.s.
  (as in the paper; Female mildly positive).  H1 (Friend x Impartiality < 0)
  **unchanged** by their inclusion.
- Extended panel (`extend_table3_4.py`, 1975-2026): controls added to BASE and a
  Diaspora spec added.  Diaspora +0.25*** in the televote era; H1 still holds
  pooled/jury/tele/hybrid and the 2016-2026 televote breakdown is unchanged.

New/updated files: `diaspora.py`, `build_performer_types.py`,
`output/performer_types.csv`; edits to `build_dataset.py`,
`regressions_table3_4_fig3.py`, `extend_table3_4.py`.

---

## Prompt 14 (newest QoG release + footnote-13 hot-deck imputation of missing ICRG)
**QoG updated.** Swapped the impartiality source to the uploaded
`qog_std_ts_jan26.csv` (QoG Standard Time-Series, Jan-2026 release; `icrg_qog`
coverage 1984-**2025**, vs 1984-2024 in `jan25`).  Only the filename changed in
`build_dataset.py`/`build_dataset.R`; the panel now has a real 2025 and carries
2025 forward to 2026.  Historical estimates are unchanged (ICRG revisions are
negligible): Table 3 quality 0.878, friend 4.80, Friend x Imp -2.77 pre-fix.

**Footnote-13 fix (the important one).** Re-reading Charron fn.13: ICRG is missing
for some countries, and because the missingness is non-random he uses HOT-DECK
imputation (borrow the most-similar ESC country by WGI), NOT mean-substitution.
Our `load_impartiality` had been doing exactly the rejected thing -- countries
with no `icrg_qog` series silently fell through to the global sample mean (~0.70).
In `jan26` that hit SIX ESC countries: Bosnia, Georgia, Monaco, Macedonia,
Montenegro, San Marino.  (Georgia & Macedonia are Charron's own fn.13 cases;
Moldova, his third, NOW has a real series in QoG; Bosnia/Monaco are NOT in ICRG at
all [correction in Prompt 17 -- an earlier claim that Charron's raw ICRG covered
them was wrong]; Montenegro/San Marino are later entrants.)

Fix: `lib_countries.py/.R` now define `ICRG_DONOR` and `load_impartiality` fills a
donee that lacks its own series from its donor (ffilled over the panel), only as a
last resort using the mean.  Donors: `ge<-hr, mk<-al, md<-az` (Charron's exact
pairs; md's is unused since real data now exists) and `ba<-rs, me<-rs, sm<-it,
mc<-fr` (documented nearest-neighbour extension).  Imputed 2012 values, e.g.
Macedonia 0.42 (was 0.70), Bosnia 0.47, Georgia 0.63 -- all well away from the old
0.70 mean.  No ESC country now falls back to the global mean.

Effect: it STRENGTHENS H1 (correctly-lower impartiality for the low-governance
Balkan friend-bloc voters sharpens the moderation): Table 3 Friend x Imp
-2.77 -> **-3.06*** **, friend 4.80 -> 5.00***, imp_i 0.15 -> 0.19*; quality and
Diaspora (+0.66***) unchanged.  Extended Table 4 fm2 x Imp -3.45***.

---

## Prompt 15 (separate replication vs extension folders)
Split the project into two sibling folders. `replication/` keeps the faithful
Charron 1975-2012 replication (self-contained; `run_all.py` -> `replication/
output/`), including the recovered-variable builders `diaspora.py` and
`build_performer_types.py` (they complete Charron's OWN Table 3/4 controls and feed
the bundled panel).  `extension/` holds everything beyond the paper: the eschome
scrapers, `compare_sources.py`, `diagnose_table1.py`, `extend_table3_4.py`,
`eurovision_voting_rules.md`, plus `run_all_extension.py`, all writing to
`extension/output/`.

Cross-folder wiring (pipeline stays fully runnable):
- `build_dataset.py` stays shared in `replication/` but is now `EXT_OUT`-aware:
  bundled mode -> `replication/output/master.csv`; `--source eschome` reads the
  scraped inputs from and writes `master_extended.csv` to `extension/output/`.
  `performer_types.csv` is always read from `replication/output/`.
- `extend_table3_4.py` `sys.path`-inserts `../replication` to reuse the shared
  estimators; `_print_table` gained an `out_dir` arg so extended tables land in
  `extension/output/`.
- Per-folder `output/` chosen by the user; verified `replication/output/` has no
  `*_extended`/eschome artifacts and both `run_all.py` and `run_all_extension.py`
  run green.

---

## Prompt 16 (re-verify footnote-13 ICRG imputation matches Charron exactly)
Re-read Charron's impartiality section + fn.13. He measures impartiality with the
ICRG "quality of government" (corruption + rule of law + government effectiveness),
and for the THREE countries with no ICRG -- Georgia, Macedonia, Moldova -- he does
NOT mean-substitute (non-random missingness); he HOT-DECK imputes each from its
most-WGI-similar ESC country: "Croatia, Albania and Azerbaijan respectively", i.e.
ge<-hr, mk<-al, md<-az, taking the donor's ICRG scores.

Verification found ge<-hr and mk<-al already exact, but **Moldova did NOT match**:
our `load_impartiality` had a `if donee not in imp` guard, and because the newer
`qog_std_ts_jan26.csv` now carries a real Moldova series (which Charron lacked),
Moldova was using its own data (~0.444) instead of Azerbaijan's (~0.361).

Fix: made the hot-deck imputation apply to the REPLICATION exactly as Charron did
-- a `charron_faithful` flag on `load_impartiality`/`add_impartiality` (default
True) applies the donor UNCONDITIONALLY, so bundled `master.csv` now imputes
Moldova from Azerbaijan. Verified md==az, ge==hr, mk==al in `master.csv`. Effect is
small (Moldova is a minor 2005-2012 voter): Table 3 Friend x Imp -3.06 -> -3.081,
friend 5.00 -> 5.02, quality/Diaspora unchanged. (`lib_countries.py/.R` comments +
the replication-only R pipeline updated to the same unconditional logic.)

## Prompt 17 (searched for Bosnia & Monaco ICRG; corrected donor via Charron's WGI method)
Searched the data + web for ICRG data on Bosnia and Monaco. Result: **ICRG does not
cover either.** QoG's only ICRG column (`icrg_qog`) is empty for BIH and MCO in
every release, ICRG (PRS Group) spans just 141 countries, and an academic ICRG
evaluation states Bosnia-Herzegovina data is "not available in the ICRG dataset."
So the earlier note that "Charron's raw ICRG covered Bosnia and Monaco" was WRONG --
that data never existed; his fn.13 just didn't enumerate them.

WGI (`wbgi_*`) IS available for Bosnia (1996-2024). Charron picks fn.13 donors by
WGI-similarity, so I applied his OWN method to Bosnia: nearest ESC country (by WGI
corruption/gov-effectiveness/rule-of-law, among those with real ICRG) is **Albania**
(dist 0.485), not Serbia (0.668) which I'd chosen by geography. Changed `ba <- al`
in `ICRG_DONOR` (lib_countries.py/.R). Monaco can't be WGI-matched (its
corruption/effectiveness WGI is empty for its ESC years 1975-79 & 2004-06) -> kept
`mc <- fr`; Monaco is a negligible edge case anyway. Impact (Bosnia is a real
Balkan-bloc voter): Table 3 Friend x Imp -3.08 -> -3.116, friend 5.02 -> 5.04,
quality unchanged.

## Prompt 18 (was Bosnia in Charron's sample? why fn.13 omits it -> justifies ba<-al)
Checked whether Bosnia was relevant to Charron's 1975-2012 study, since ICRG has no
Bosnia data yet fn.13 doesn't list it. It was clearly IN-sample and central:
- 18 finals 1975-2012 (debut 1993, then almost every year);
- voter in 420 dyad-years + receiver in 420 (~4.6% of the 18,276-row panel);
- a core member of the ex-Yugoslav/Balkan friend bloc (G2: with Croatia in
  1975-1997; Croatia+Serbia+Macedonia+Slovenia in 1998-2012) -- so its voter
  impartiality feeds the Friend x Impartiality interaction that IS the paper's H1.

So Charron did not actually "have" Bosnia ICRG (it does not exist); he simply did
not enumerate it in fn.13. Most plausible reading: fn.13's "three cases" list is
illustrative, not exhaustive, and Bosnia (like Monaco) was imputed the same hot-deck
way but left unnamed -- consistent with his stated aim of KEEPING observations
rather than dropping them (dropping Bosnia would delete ~4.6% of dyads and a whole
friend bloc's voter side, which he never mentions). Can't be proven from the text,
but every reading except "silently dropped" implies Bosnia was imputed. This
justifies our `ba <- al` hot-deck (Albania = Bosnia's WGI-nearest ESC country with
real ICRG, Prompt 17): it applies Charron's documented method to a country his
footnote omitted but his analysis required.

## Prompt 19 (exact-replication diagnosis + Phase 0/1: sample & givers)
> *"Do a thorough diagnosis of the differences, read the Charron paper including the
> footnotes closely on methods, and make a plan to move towards exact replication."*
> *"please update summary file and start with the first phases."*

Re-read the paper's methods sections and footnotes line-by-line and traced every
divergence into the code.  Diagnosis grouped the gaps into buckets:

- **(A) Sample/givers — biggest N driver.**  §6 + **fn.18**: givers are *all countries
  that reached a final in ANY year*, counted even when eliminated in that year's
  semi-final (his Finland-2012 example); receivers are that year's finalists.  Our
  `build_dataset.load_votes` kept **finalist->finalist only** (dropped the eliminated-
  semi-finalist givers).  Also ICRG "extends back to **1983**" (text), so impartiality
  is missing pre-~1984 and those rows drop from every model -- but the code **back-filled**
  ICRG to 1975 (bfill), keeping 1975-1982 rows Charron never had.
- **(B) Quality `p`.**  Eq.1 `p` = "total number of voting participants" (all voters);
  the code computed it over finalists only.
- **(C) Friend dyads.**  Friend = both countries in the SAME Table-2 group (fixed
  membership).  The code **re-clusters** (mutual-affinity, size-ordered) and its groups
  differ from Table 2 (e.g. it puts Albania with Greece-Cyprus).  This drives the
  Friend-Dyad / interaction magnitude gap (8.30/-6.61 vs our ~5/-3).
- **(D) Spec.**  Missing the year-count trend (text line 652); Diaspora only in model 4
  (paper: models 4-10); Tobit upper-censored only (vote is also massed at 0).
- **(E) Estimator.**  Models 9-10 + all of Table 4 are random-effects Tobit; we
  approximate with pooled Tobit.
- **(F) Irreducible.**  Table 1 extreme televote dyads (Greece->Cyprus); heuristic
  English/French; reconstructed Diaspora/performer types (already near-exact).

Empirical reconciliation of N: paper Model 1 = 16,686 = [1984-97 jury ~6.4k] +
[1998-2012 tele w/ semi-final givers ~10.4k]; our old 18,276 = full 1975-2012
finalist->finalist.  Fix = drop pre-1984 (no ICRG) + add eliminated-semi-final givers.

**Plan (6 phases):** 0 validation harness; 1 sample & givers; 2 quality/`p`; 3 friend
groups verbatim from Table 2; 4 spec (year trend, diaspora in 5-10, two-limit Tobit);
5 true RE-Tobit in R; 6 reconcile + doc.  Honest target: N matched, signs/significance
matched everywhere, key coefficients within a small tolerance (not decimal-exact --
his private eschome series + heuristic English/French preclude that).

**Phase 0 — `validate_replication.py`** (new): runs the OLS models and prints N + the
four hypothesis coefficients beside Charron's published Table-3 values with a diff
column.  Reuses the live estimation code so it always tracks the pipeline.

**Phase 1 — sample & givers (build_dataset.py):**
- `load_votes`: giver `i` now = *ever a finalist* (`all_finalists = union of the
  yearly rosters`) instead of finalist-that-year; receiver `j` still = finalist that
  year.  This restores the eliminated-semi-final giver rows (fn.18).
- `load_impartiality`/`add_impartiality`: in faithful (replication) mode, **no bfill**
  before ICRG start, and impartiality is set MISSING for `year < icrg_start` (=1984,
  detected from the data) so those rows drop from the regressions -- while Table 1 /
  quality still use the full 1975-2012 votes.  Extension mode (`charron_faithful=False`)
  keeps the old bfill, so `master_extended.csv` is unchanged.  `load_impartiality` now
  also returns `icrg_start`.

*Phase 2 came for free:* with givers expanded, the quality `p`/`total_j` group-bys now
span all voters, so eq.1 matches the paper without further change.

**Results.**  master.csv 18,276 -> **21,198** rows (giver expansion), 1975-2012.
Regression N vs paper: **jury 6,650 vs 6,442 (+3%)**, tele 11,500 vs 10,402 (+11%),
all 18,150 vs 16,686.  The tele overshoot is concentrated in the 2004-2012 semi-final
era (~37 givers/yr vs paper's implied ~31); a cumulative-past reading of fn.18 barely
moves it (11,428), so the residual is data provenance (bundled votes.csv vs Charron's
private eschome extract of eliminated-semi-final voters), not the rule.  Payoffs:
- **Quality now near-exact**: 0.894 / 0.879 / 0.902 (paper 0.90 / 0.87 / 0.89).
- **Table 1 televote era improved**: Macedonia->Albania **9.4**, Azerbaijan->Turkey
  **8.5**, Turkey->Azerbaijan **8.0**, Lithuania->Georgia **7.8** now match the paper
  to the decimal, and Lithuania->Georgia correctly enters the top-10.
- Friend-Dyad / interaction still off (3.9 / -1.5) -- expected; awaits **Phase 3**
  (hard-code Table-2 membership), the main lever on those.
Pipeline green end-to-end (`run_all.py`).  Next: Phase 3.

## Prompt 20 (use Charron's OWN eschome scrape as the replication source; correct the "provenance" claim)
> *"you should be using the votes dataset that you extract from eschome website that
> goes up to 2026 … We already got the dataset from the website. it should be in the
> log. that is the dataset you should be using. please look in the code in the folders."*

Charron's fn.1 says his votes come from **eschome.net** (Ginsburgh-Noury to 2003, his
own updates to 2012).  We scraped exactly that into `extension/output/votes_eschome.csv`
(+ `finalists_eschome.csv`).  The replication had been building `master.csv` from the
**bundled** `votes.csv` instead.  Fixed `build_dataset.main()`:
- **default source is now `replication`** = the scraped eschome votes/roster restricted
  to 1975-2012, faithful rules (ever-finalist givers fn.18, `charron_faithful=True`)
  -> `output/master.csv`.
- `--source bundled` = legacy cross-check from the 2023 dataset -> `master_bundled.csv`.
- `--source eschome` = the 1975-2026 extension -> `master_extended.csv` (unchanged).
- `load_votes` now restricts the ever-finalist giver set to the build window (the
  eschome roster spans 1975-2026).

**Verified eschome === bundled, exactly.**  Rebuilt both and merged on (year,i,j):
**0 dyads differ**, and `vote`/`quality`/`imp_i`/`n_part` all have max|Δ| = 0 across
21,198 rows.  So the source switch makes the replication provenance-correct (it now
uses Charron's actual data) but **changes no number** -- consistent with Prompt 5-8's
"zero value disagreements."

**Correction to Prompt 19:** the tele-era N overshoot (11,500 vs paper 10,402) was
attributed there to "data provenance (bundled vs eschome)."  That was WRONG -- the two
sources are identical.  The overshoot is a **modeling/definition** question: how many
eliminated-semi-final givers (fn.18) belong in Model 3.  Finalist->finalist gives 8,578
(too few); ever-finalist givers give 11,500 (too many); the paper's 10,402 sits between,
so the exact giver rule / country-inclusion still needs to be pinned down.  Still open.

**Also flagged (introduced in Phase 1):** the hand-rolled `tobit.py` MLE is unstable on
the larger pooled sample -- the Model-1 "all years" pooled Tobit intermittently returns
non-converged SEs (e.g. 1681).  OLS is unaffected.  This is an estimator-robustness bug
to fix in Phase 5 (proper Tobit), not a data problem.

## Prompt 21 (match Charron's sample size N; three rules; residual analysis)
> *"fix N first" … "keep #2 is fine. do you have any other guesses as to why the Ns
> are still not exactly the same?"*

Pinned down the giver/sample rules that reproduce Charron's N.  Three changes, all
gated to the faithful replication (extension untouched):

1. **Cumulative "at least twice" entry** (`build_dataset.main`): a country joins the
   panel in the year of its **2nd** final appearance (not window-wide >=2).  This is
   the big lever -- it removes the newer eastern entrants who flood the 2004-2012
   semi-final era as eliminated voters *before* they have two finals.  Tele 11,500 ->
   ~10,700.
2. **fn.13 imputation = only Charron's 3 named cases** (`CHARRON_DONOR` = Georgia<-
   Croatia, Macedonia<-Albania, Moldova<-Azerbaijan; `lib_countries.py`).  Every other
   no-ICRG country (Bosnia, Monaco) is DROPPED as a voter (he rejects mean-substitution)
   -- so faithful mode no longer applies the wider donor set or a mean fallback.  This
   also *resolves the Prompt 18 question*: the near-exact tele match with Bosnia dropped
   is evidence Charron dropped it, not imputed it silently.  (Extension keeps Bosnia.)
3. **ICRG from 1983** (`CHARRON_ICRG_START`): the paper says ICRG "extends back to 1983",
   so faithful mode back-fills the 1984 value one year to 1983; pre-1983 stays missing.

Result (regression-eligible N):
  jury 6,475 (paper 6,442, +0.5%) | tele 10,415 (paper 10,402, **+0.1%**) | all 16,890 (paper 16,686, +1.2%).
Also switched the replication SOURCE to Charron's own eschome scrape (Prompt 20); it is
byte-identical to the bundled data, so it changes no number.  master.csv now 19,522 rows.

**Why N still isn't identical (ranked):**
- **The "all" gap is mostly the paper's OWN inconsistency.** Charron's Model 1 (16,686)
  is 158 *below* his jury+tele sum (16,844); ours is internally consistent
  (6,475+10,415 = 16,890).  So ~158 of the +204 is his quirk, not ours -- the true
  per-period excess is only +33 / +13.
- **We drop fewer rows than he did:** our controls are 100% populated (English/French
  lyric heuristic; performer types baseline-filled), so listwise deletion never fires
  for us, whereas his coding gaps (diaspora/language/performer) would drop some
  receiver-songs across all voters.  Direction matches (we sit slightly high).
- **ICRG vintage for early-1990s ex-Yugoslav/Soviet debutants:** QoG's icrg_qog starts
  late (Croatia/Slovenia 1999, Estonia 1999, Cyprus/Lux 1985); we carry the first value
  back over the gap (342 rows).  Charron used raw PRS ICRG (a different vintage) + his
  sticky fill, so a few dozen rows differ here -- right in the +/-33 range.
- **Roster / lineage / country count:** we have 45 countries, he reports 46; single-year
  finalist-roster disagreements and lineage-ambiguous 2nd-final entry (Yugoslavia ->
  Serbia&Montenegro -> Serbia) move a handful of rows.

Net: matched to 0.1-0.5% per period; the exact integer needs his private roster, his
ICRG vintage, and his exact control-missingness -- none fully specified in the paper.
(Still outstanding from Phase 1: the hand-rolled `tobit.py` is unstable on the pooled
sample; Phase 3 friend groups; both unchanged here.)

## Prompt 22 (fix the Tobit; make R the authoritative estimator)
> *"update summary file and fix tobit" … "you should be running analysis with R
> whenever possible."*

**Fixed `tobit.py`.**  The instability (intermittent nonsense SEs, e.g. 1681, on the
larger pooled sample) came from using BFGS's approximate `res.hess_inv` for the
covariance -- path-dependent and unreliable when regressors are mixed-scale (n_part
18-43 next to 0/1 dummies).  Rewrote the estimator to be stable and deterministic:
(1) **standardise** the design (divide each non-constant column by its SD, transform
coefficients/covariance back); (2) **analytic per-observation scores** for the
optimiser gradient and the sandwich "meat"; (3) sandwich "bread" = a real **numerical
Hessian** of the log-likelihood at the optimum, not `hess_inv`.  SEs are now sane and
identical across runs.

**Made R the authoritative estimator** (per user preference: run analysis in R when
possible; logged to memory [[prefer-r-for-analysis]]).  R's `AER::tobit` (survreg) is a
mature, stable Tobit.  Rewired `regressions.R` to read the **Python-exported
`output/regression_data.csv`** (single source of truth -- Python does the careful
N-matched data build; R only estimates, so the two can't drift on the sample).  Added
Duet/Group/Female + a Diaspora model to the R specs, and it now WRITES
`table3_R.txt` / `table4_R.txt`.  Fixed a reporting bug in R `run_tobit` (it reported
`sum(!is.na(vote))` instead of the actual estimation N; now `complete.cases`, so e.g.
M1-all Tobit correctly shows 16,890 not 19,522).  `run_all.py` now invokes
`Rscript regressions.R` as its final step (graceful skip if Rscript absent).

**Cross-validation (R vs Python Tobit, Table 4 M1-all pooled):** point estimates are
IDENTICAL to 3 dp -- quality 0.922, friend_m1 5.559, imp_i 0.095, fm1_x_imp -3.561.
SEs differ only because Python reports Huber-White robust and R reports classical
survreg SEs (a robust-vs-classical choice, not an error).  This both validates the
Python fix and confirms the R tables.  (Note: friend_m1 ~5.56 / interaction ~-3.56 are
already closer to Charron's 8.30 / -6.61 than pre-N-match, but the remaining gap awaits
Phase 3 -- Table-2 friend groups verbatim.)

## Prompt 23 (Phase 3: friend groups verbatim from Table 2)
> *"yes move onto phase 3"*

Replaced the re-clustered method-1 friend groups with **Charron's Table 2 membership,
transcribed verbatim** (`friend_groups.py`): both periods, with the paper's 'a'
weak-linkage marks encoded ('~') and footnote-b handled (period-2 "Serbia" = both `rs`
and `cs`).  `cluster_table2_fig1.py` now writes `friend_dyads_method1.csv` (full, for
Table 3) and `friend_dyads_method1_alt.csv` ('a'-removed, for Table 4's "Alternative
Friend Group Method 1") from this hard-coded table; the clustering is kept only to draw
the Fig. 1 dendrogram.  `table2.txt` is now the paper's table verbatim.  Both estimators
(Python `regressions_table3_4_fig3.py` and authoritative R `regressions.R`) carry the
new `friend_m1` (Table 3) and `friend_m1_alt` (Table 4 method-1 cols).

**Result -- the headline H1 test now essentially matches Charron.** Table 3 Model 1
(OLS, all years), ours vs paper:
  quality 0.903 / 0.90 | **friend_m1 8.319 / 8.30** | imp_i 0.173 / 0.22 | **fm1 x imp -6.884 / -6.61**.
The Friend Dyad jumped from ~5.56 (clustering) to **8.32** -- the clustering had been
the whole gap.  Diaspora 0.677 / 0.66.  Table 4 "Alternative Method 1" also lines up
(jury near-exact: friend 7.008 / 7.01, interaction -4.775 / -4.87; other subsets close).
Method 2 (pairwise, `fig2_network.py`) still our own reconstruction -- closer on jury
(7.64 / 7.47) than elsewhere; a possible later refinement.  Pipeline green end-to-end
(`run_all.py`, Python + R).

**State of the replication now:** N matched to 0.1-0.5% per period; Table 1 headline
dyads matched; Table 2 verbatim; Table 3 quality/friend/impartiality/interaction and
Diaspora all matched; Table 4 method-1 close; Tobit stable (R AER::tobit authoritative,
Python cross-checks to 3 dp).  Remaining: RE-Tobit (models 9-10 use pooled/AER as a
stand-in), and method-2 pairwise friend groups.

## Prompt 24 (Phase 5: genuine random-effects Tobit; why it differs from Stata)
> *"do the re-tobit first" … "Charron probably did this with Stata. what could be
> driving the discrepancy?"*

Replaced the pooled-Tobit stand-in for Table 3 models 9-10 with a **genuine dyad-level
random-effects Tobit** via R's `censReg` (panel `pdata.frame`, Gauss-Hermite
quadrature).  Installed `censReg`/`plm`.  `run_retobit()` in `regressions.R` fits it and
reports Sigma_u / Sigma_e / Rho.  Two robustness fixes were needed:
  * **Start values.** From a naive start, censReg collapsed the RE variance to the 0
    boundary (Sigma_u -> 0, singular Hessian, infinite SEs).  We start from a pooled
    Tobit for the betas with a POSITIVE `logSigmaMu`, which recovers a proper interior
    optimum with finite SEs.
  * nGHQ=12 quadrature (checked 8/12/16/20 -- estimates stable, so point-count is not a
    factor).

Result (models 9/10): friend 8.09/8.64, fm1 x imp -7.14/-7.52, **rho 0.158/0.170**
(paper 0.12/0.14), Sigma_u 1.22/1.28 (paper 0.98/1.04), Sigma_e 2.81/2.82 (2.63/2.64).
Same shape, modestly larger RE variance.

**Why it differs from Charron's Stata `xttobit` (diagnosis):**
1. **Weak identification of the lagged-DV + RE model (dominant).** Model 9 has BOTH a
   lagged DV and a dyad random intercept; both soak up dyad persistence, so the
   likelihood is flat along a ridge trading off (lag coef) <-> (Sigma_u) <-> time-
   invariant coefs (friend).  Evidence: censReg collapses to the Sigma_u=0 boundary from
   a naive start; and our LAG coefficient is where we most diverge (ours 0.204 vs his
   **0.09**).  His xttobit attributes persistence to the RE-shrunk lag (0.09, Sigma_u
   0.98); ours attributes more to the lag (0.204) + slightly more Sigma_u -- same data,
   different point on the ridge.  (fn.19 itself flags the lag as problematic.)
2. **xttobit vs censReg internals.** Stata default = ADAPTIVE Gauss-Hermite (re-centred
   per panel) + its own optimiser/boundary handling; censReg = non-adaptive GHQ.  Ruled
   OUT the point count (rho stable 8->20), but adaptive centring (not available in
   censReg) can still shift the estimate on the flat ridge from (1).
3. **Sample.** model 9 drops first-year-per-dyad rows; our N=12,670 vs his 12,355, plus
   the ~1% cascade (control missingness, ICRG vintage, roster) already documented.
Contrast: OLS + pooled-Tobit (models 1-8) match Charron closely; only the RE+lag models
(9-10) diverge -- exactly the numerically hard, weakly-identified spec.  Sanity check:
the RE Tobit WITHOUT the lag is well-identified (rho 0.19, finite SEs, no boundary
issue), where both packages would agree closely -- confirming the lag+RE combination is
the culprit.  `run_all.py` runs it (adds ~30s).

## Prompt 25 (explain Table 1 discrepancies -> fix them: full sample, Serbia merge)
> *"can you explain all the discrepancies in table 1, one by one?" … "why aren't you
> doing the Serbia fix too? you should do all possible fixes to match Charron."*

Diagnosed Table 1 dyad-by-dyad, then applied every fix that legitimately closes a gap.

**Root cause (dominant): Table 1 was reading the REGRESSION sample.**  `master.csv`
carried the cumulative "2nd-final entry" cohort (a regression rule to match Charron's
N); Table 1 is DESCRIPTIVE and Charron averages each dyad over ALL years both were
finalists.  The cohort filter crushed newer-country dyads below the obs floor and
shifted averages.  Fix: **`master.csv` is now the FULL sample** (every dyad-year among
>=2-final countries) **plus a `cohort` flag**; the REGRESSIONS filter `cohort==1`
(build_dataset writes the flag; `regressions_table3_4_fig3.load` and
`extend_table3_4.load` filter it), while **Table 1 / Appendix 3 use the full sample**.
On the full sample the jury biases reproduce Charron to the decimal (Greece->Cyprus 7.1,
Turkey->Bosnia 6.7, Croatia->Malta 5.6, Estonia->France 4.6, ...).

**Serbia lineage merge (fn.b):** `lib_countries.ALIAS = {"cs": "rs"}` -- Serbia &
Montenegro (`cs`, 2004-06) is folded into Serbia (`rs`), applied in `load_votes` and both
finalist loaders (SFR Yugoslavia `yu` stays separate).  This gives Serbia continuous
observations, so **Serbia->Macedonia is now 8.5 (n=5), matching Charron exactly** (was
n=1, filtered).  Removed the now-redundant `cs` from friend_groups G6.

**MIN_OBS:** tried 2 (Charron flags one n=2 pair, Malta->Slovakia), but our sparse
jury era has many high-bias n=1/2 dyads Charron's list lacks (relegation-era = few
co-final appearances), so n>=2 floods the table with noise.  Kept **MIN_OBS=3** -- the
clean, Charron-like list; his single flagged n=2 exception is simply outside a uniform
rule (a top-10 of small-n averages is inherently noisy in the tail).

**Results.**  Table 1 televote now matches on 7 dyads incl. Serbia->Macedonia 8.5 and
Lithuania->Georgia 7.8 (both exact); jury matches on the values.  **Appendix 3 improved
dramatically** (it also now uses the full sample): 1975-97 blocs Bosnia-Turkey 4.66,
Russia-Slovenia 5.36/5.35, UK-Ireland 0.41, Israel-Yugoslavia 1.67, Est-Pol-Hun 2.07,
Greece-Cyprus 7.89/7.88 -- near-exact; Turkey-Azerbaijan 8.22/8.23 (98-12).  Regression
UNCHANGED (Serbia merge +22 rows): Table 3 M1 N 16,912, friend 8.33, interaction -6.90.
Remaining Table 1 residuals: Greece->Cyprus 10.3 vs 9.0 (irreducible -- Greece gives
Cyprus 12 every final), Cyprus->Greece 8.7 vs 9.1, and small-n tail composition.
Pipeline green (`run_all.py`).  (Deck Table 1 / Appendix 3 slides regenerated to match.)

## Current design (after Prompts 19-25) -- read this first
- **Data source:** Charron's own eschome scrape (`extension/output/votes_eschome.csv`),
  restricted to 1975-2012.  Byte-identical to the bundled 2023 dataset on overlap.
- **`master.csv` = the FULL descriptive sample** (every dyad-year among >=2-final
  countries) with a **`cohort`** flag = Charron's cumulative "2nd-final entry" subset.
  Table 1 / Appendix 3 use the full sample; the REGRESSIONS filter `cohort==1`.
- **Sample rules (regression):** fn.18 ever-finalist givers; all-voter Quality `p`;
  fn.13 impartiality = impute only Georgia/Macedonia/Moldova (drop other no-ICRG voters),
  ICRG from 1983.  Serbia & Montenegro `cs` merged into Serbia `rs` (`lib_countries.ALIAS`).
- **Friend dyads (method 1) = Charron's Table 2 VERBATIM** (`friend_groups.py`);
  `friend_m1_alt` = 'a'-weak members removed (Table 4).  Method 2 = pairwise sig. bias.
- **Estimator: R is authoritative** -- `regressions.R` reads the Python-exported
  `regression_data.csv` and runs `AER::tobit` (Tobit) + `censReg` (RE-Tobit, models
  9-10); Python `tobit.py` is a cross-check (matches R to 3 dp).  `run_all.py` runs both.

## Output artifacts
`replication/output/`: `table1.txt/.csv`, `table2.txt`, `table3.txt`/`table4.txt` (Python),
**`table3_R.txt`/`table4_R.txt` (authoritative, AER::tobit/censReg)**, `appendix3_*`,
`fig1/2/3*.png`, `master.csv` (full + `cohort`), `friend_groups_*`, `friend_dyads_method1*`,
`friend_dyads_method2*`, `regression_data.csv`, `performer_types.csv` (`_R` = R pipeline).
`extension/output/`: `votes_eschome.csv`, `finalists_eschome.csv`, `eschome_cache/`,
`master_extended.csv` (full + `cohort`), `regression_data_extended.csv`,
`table3/4_extended*.txt` (Python) + `table3/4_extended_R.txt` (R), `source_*.csv`.

Key scripts: `build_dataset.py` (panel), `friend_groups.py` (Table 2), `table1.py`,
`cluster_table2_fig1.py`, `fig2_network.py`, `appendix3.py`,
`regressions_table3_4_fig3.py` (+ exports `regression_data.csv`), `regressions.R`
(authoritative), `validate_replication.py` (N/coeff check vs Charron).

Reproduce: `python3 replication/run_all.py` (replication; runs `Rscript regressions.R`
at the end) and `python3 extension/run_all_extension.py` (extension; runs
`extend_regressions.R`).  Both need R with `AER`, `sandwich`, `lmtest`, `censReg`, `plm`.
Regenerate the performer classification (live Wikidata) with
`replication/build_performer_types.py`; the diaspora table is static in
`replication/diaspora.py`.
