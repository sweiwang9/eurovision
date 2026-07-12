# Session Summary — Charron (2013) Replication + Extension

A running log of the prompts given and the results produced.

> **This is the `extension/` log — from Prompt 16 on it records only
> extension-folder updates (everything beyond the paper; `run_all_extension.py`).**
> Replication-folder work is logged separately in `replication/SUMMARY.md`.  Entries
> **through Prompt 15** predate this split and are the shared project history, kept
> identically in both files as the common baseline; new entries diverge by folder.
> Pre-split entries mention bare `output/` paths from when the project was a single
> folder — those artifacts now live under `extension/output/` (see Prompt 15).

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

## Prompt 16 (extension uses ALL available ICRG data, not Charron's fn.13 imputation)
When re-checking Charron's footnote-13 ICRG hot-deck imputation (see the
replication log), the user directed that the extension should **use all available
data and need not follow Charron exactly**. `load_impartiality` now takes a
`charron_faithful` flag: the shared builder passes `False` for `--source eschome`,
so `master_extended.csv` keeps every country's own real ICRG series where it exists
-- in particular **Moldova uses its real data (~0.444)**, not the Azerbaijan
imputation the replication uses. Countries that still have NO ICRG series at all
(Georgia<-Croatia, Macedonia<-Albania, and the micro-states Bosnia/Monaco/
Montenegro/San Marino) are still hot-deck imputed in the extension, since there is
no real data to use. Verified in `master_extended.csv`: `md != az`, while
`ge==hr` and `mk==al`. Extended tables re-run; results unchanged (Moldova already
used real data here before the replication-side fix).

## Prompt 17 (Bosnia/Monaco ICRG search -> ba<-al donor; applies to the extension too)
Confirmed ICRG has NO data for Bosnia or Monaco anywhere (QoG `icrg_qog` empty;
ICRG/PRS covers 141 countries, excludes both). Since WGI covers Bosnia, its donor
was reselected by Charron's own WGI-similarity method: **Bosnia <- Albania** (was
Serbia). This is a shared change in `lib_countries.ICRG_DONOR`, so the extended
panel (`master_extended.csv`) uses it as well -- Bosnia still needs a donor here too
(no real ICRG exists for it, so "use all available data" can't help Bosnia). Monaco
stays `mc <- fr` (no usable WGI). Extended tables re-run green; fm2 x Imp -3.41***.
Full detail in the replication log (Prompt 17).

## Prompt 18 (align the extension to the replication methodology; R estimator)
> *"Now correct the extension files to use the same methodology as the replication
> when it makes sense and only deviating for something genuinely better."*

While matching the replication to Charron (replication log Prompts 19-24), the shared
data build and the friend measure moved on; the extension had been left on the old
methodology.  Aligned it, keeping only the deviations that are genuinely better for an
extension (not a faithful reproduction).

**Now SAME as the replication:**
- **Givers = ever-finalist (fn.18)** and **cumulative ">=2 finals" entry** -- both were
  gated to the replication before; the shared `build_dataset.py` now applies them to
  `--source eschome` too (givers `ever_finalist_givers=True`; the cumulative-entry
  sample rule is unconditional).  All-voter Quality `p` follows automatically.
- **Method-1 friend dyads = Charron's Table 2, VERBATIM** (`friend_groups.py`), replacing
  the mutual-affinity clustering in `extend_table3_4.py`.  The extended 1998-2026 period
  uses his 1998-2012 groups (blocs are slow-moving); post-2012 entrants (Australia) have
  no method-1 friends.
- **Estimation in R** (`extend_regressions.R`, `AER::tobit`) -- extend_table3_4.py now
  EXPORTS `regression_data_extended.csv` and R estimates it (same Python-builds /
  R-estimates split as the replication).  Wired into `run_all_extension.py`.

**Genuinely-better DEVIATIONS kept:** (a) Impartiality uses ALL available real ICRG +
the wider hot-deck donor set (Bosnia<-Albania, Monaco<-France, ...), so real Balkan
voters stay in the panel instead of being dropped as the strict fn.13 replication does;
(b) the 0-12 `vote12` DV (televote half for 2016+); (c) method-2 friend dyads recomputed
on the extended data so they can pick up post-2012 friendships; (d) English/French
dropped (no 2024-2026 lyrics).

**Effect.**  `master_extended.csv` 25,901 -> **30,730** rows (giver expansion), 1976-2026.
Friend Dyad now on the Table-2 scale (all-years OLS 7.30, interaction -5.85***).  The
headline extension finding is UNCHANGED: Friend x Impartiality < 0 holds pooled/jury
(-5.49***)/hybrid, but **weakens to n.s. in the 2016-2026 split-televote era**
(Table 3 model 4 fm1 x imp -1.39 n.s.; Table 4 M1 split -1.91*).  R and Python agree.
Pipeline green (`run_all_extension.py`).

## Prompt 19 (Serbia merge + full-sample/cohort refactor propagate to the extension)
> *(replication log Prompt 25: Table 1 fixes.)*

The shared-build changes from the replication's Table 1 work carry into the extension:
- **Serbia & Montenegro `cs` -> Serbia `rs`** merge (`lib_countries.ALIAS`, Charron fn.b)
  applies to the eschome build too -> `master_extended.csv` now has 49 (not 50) countries,
  Serbia continuous.
- **`master_extended.csv` is now the FULL sample + a `cohort` flag**; `extend_table3_4.load`
  filters `cohort==1` for the regressions (same cumulative "2nd-final entry" rule as
  before -- results essentially unchanged, just relocated from the build to the load).
Panel 30,730 -> **33,375 rows (full)**, cohort==1 = 30,785, 1976-2026.  Extended Tables
3 & 4 re-run (Python + R) green; headline finding intact (Friend x Impartiality < 0
holds pooled/jury/hybrid, weakens in the 2016-2026 split-televote era).

## Prompt 20 (extension beamer deck)
> *"please produce beamer slides for the extension."*

Built `slides/extension.tex` (8 slides, compiles to `slides/extension.pdf`), styled like
the replication deck (`charron_vs_replication.tex`):
1. title; 2. what it tests (design + same-methodology / deliberate-deviations columns);
3. the four voting-rule eras (jury/televote/hybrid/split, with the DV used); 4. Table 3
extended -- Friend x Impartiality -5.79/-5.54/-2.42*** across all/jury/televote, -1.41
(n.s.) in the split era; 5. FIGURE of the interaction by era; 6. split era public vs jury
half (-2.33 vs -3.78, method 2); 7. what else holds to 2026 (Quality, Diaspora
+0.24..0.56***, contiguity, language); 8. takeaways.

Generated the supporting figure `extension/output/fig_era_interaction.png` (bar chart of
Friend x Impartiality by voting-rule era, with the jury-half point for the split era);
copied to `slides/img/ext_era_interaction.png`.

Framing note: with the CURRENT aligned methodology the recent-era moderation
**attenuates** (split 16-26 fm1 x imp -1.41, n.s. in the 10-year all-controls OLS) but
stays negative and significant in the pooled era models (-1.93*** to -2.33***) and is
stronger on the jury half (-3.78) -- so the deck says "attenuates, not reverses" (softer
than the older Prompt-11 "breaks down").

Deck build note: **beamer decks must be compiled TWICE** so the `x/y` page footer
resolves `\inserttotalframenumber` from the `.aux` (a one-pass build showed "6 / 1").
Both `extension.pdf` and `charron_vs_replication.pdf` rebuilt with two passes.

## Prompt 21 (jury-channel vs public-channel panels; Rest-of-World benchmark)
> *"have you done specifications ... that aggregate over all jury votes (including the
> split ones) and all public votes (including the split ones)? can you also do the rest
> of the world vote analysis you suggested?"*

New: `channel_rest_analysis.py` (builds the panels, Python) + `channel_rest_regressions.R`
(estimates, R AER::tobit), wired into `run_all_extension.py`.  Data fact: jury/televote
components exist ONLY from 2016 (the 2009-2015 hybrid publishes just the combined score),
so the clean channels are:
- **JURY channel** = 1975-1997 (juries were the whole vote) + 2016-2026 (jury half) --
  17,139 dyad-years.
- **PUBLIC channel** = 1998-2008 (100% televote) + 2016-2026 (televote half) -- 15,380.
Quality/Bias recomputed on each channel's 0-12 DV; friend = Table 2; imp = ICRG.

**Result -- the moderation is a JURY phenomenon.**  Friend x Impartiality (method 1):
  JURY channel:   pooled **-2.92\*\*\*** (75-97 -5.54\*\*\*, 2016-26 jury half -1.54\*)
  PUBLIC channel: pooled **-1.46\*\*** (98-08 -1.68\*\*, 2016-26 televote half -1.41 n.s.)
Pooling across ALL years (not just the 2016+ split), impartiality tempers friend-voting
about **twice as strongly through juries as through the public** -- and it is the strong
early expert-jury era (75-97) that carries it; both channels are weak in the modern split
era.  Quality ~0.91-0.95 in both.  This is the cleanest statement of Charron's mechanism
(impartiality works via expert/meritocratic judgment) on the full 1975-2026 record.

**Rest-of-World (XX) benchmark** (`rest_of_world_R.txt`).  The 2023+ global online
televote (giver `xx`, 56 dyad-rows) has no nationality/impartiality/friends/diaspora, so
it is a natural "impartial voter":
- **Rewards quality ~1-for-1**: pub = 0.52 + **1.02 x quality**, R2 0.51 -- a higher slope
  than national voters (0.92).
- **No friend-bloc favouritism**: extra points to bloc receivers -0.16 (n.s.) vs national
  +0.08 (n.s.).
- **Lacks the diaspora bias national electorates show**: national bias ~ diaspora =
  **+0.79\*\*\*** per rank; XX has diaspora=0 by construction.
So the global online audience votes on merit and shows none of the diaspora/bloc bias of
national electorates -- confirming the model's friend/diaspora effects are about national
ties, not song popularity.  Caveat: only 56 XX observations (2023-2026), so its
coefficients are low-powered; the quality-tracking result is the robust one.
New outputs: `regression_data_{jurychannel,pubchannel,rowvote}.csv`,
`channel_analysis_R.txt`, `rest_of_world_R.txt`.

**Slides.**  Added two slides to `slides/extension.tex` (now 10 pp): (1) "Jury vs public
channel" with a grouped-bar figure (`output/fig_channels.png`); (2) "The Rest-of-World
vote -- an impartial-voter benchmark" with a quality-scatter (`output/fig_restofworld.png`,
slope 1.02 vs the 1-for-1 line).  Takeaways slide updated (jury 2x public; RoW = merit
benchmark).  Figures copied to `slides/img/`.  Reminder: compile the deck TWICE for the
`x/y` footer.

## Prompt 22 (use Charron's MAIN friend measure (method 1) consistently in the deck)
> *"what is the main friend measure Charron uses? use that one for both slides."*

Charron's MAIN friend measure is **method 1** (voting-portfolio friend groups = Table 2);
§5.3 defines the Friend Dyad by "overall voting portfolios" and calls the pairwise
measure (method 2) the ROBUSTNESS check.  Table 3 and Fig. 3 use method 1.  The deck's
era figure (slide 5) and split-era slide (slide 6) had used method 2 -> switched both to
method 1.

**This corrected a substantive claim.**  The "jury half markedly stronger in the 2016+
split era" was a METHOD-2 result ($-3.78$ vs $-2.33$).  On method 1 the split-era jury
half ($-1.54$, p=0.10) and televote half ($-1.41$, p=0.12) are **statistically
indistinguishable -- both weak**.  So the expert-judgment mechanism is a statement about
the WHOLE record (jury era $-5.54$, hybrid $-4.04$ strong; pure-public televote $-1.68$
and 2016+ televote half $-1.41$ weak; and the pooled JURY channel $-2.92$ vs PUBLIC
$-1.46$), NOT the 2016+ split specifically.  Slide 5 figure regenerated in method 1
(green = juries involved, red = pure public); slide 6 retitled "the jury advantage has
narrowed" and reports the honest method-1 result (with a footnote that method 2 still
shows a gap).  Deck now uses method 1 throughout (Table 3 slide already did); 10 pp,
compiled twice for the footer.

## Output artifacts
`replication/output/`: `table1.txt/.csv`, `table2.txt`, `table3.txt`, `table4.txt`,
`appendix3_*`, `fig1/2/3*.png`, `master.csv`, `friend_groups_*`,
`friend_dyads_*`, `performer_types.csv` (`_R` variants from the R pipeline).
`extension/output/`: `votes_eschome.csv`, `finalists_eschome.csv`, `eschome_cache/`,
`master_extended.csv` (FULL sample + `cohort` flag; regressions filter `cohort==1`),
`regression_data_extended.csv`, `table3/4_extended*.txt` (Python) and
`table3/4_extended_R.txt` (authoritative, AER::tobit), `source_*.csv`.

Extension methodology now mirrors the replication (fn.18 ever-finalist givers, all-voter
Quality, cumulative-entry cohort, Serbia `cs`->`rs` merge, Table 2 friend groups, R
estimator) EXCEPT the deliberate "use all ICRG data" impartiality, the 0-12 `vote12` DV,
and the data-driven method-2 friend measure.  Data runs through 2026.

Reproduce: `python3 replication/run_all.py` (replication) and
`python3 extension/run_all_extension.py` (extension).  Regenerate the performer
classification (live Wikidata) with `replication/build_performer_types.py`; the
diaspora table is static in `replication/diaspora.py`.
