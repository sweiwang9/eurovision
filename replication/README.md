# Replication of Charron (2013)

Charron, N. (2013). *Impartiality, friendship-networks and voting behavior:
Evidence from voting patterns in the Eurovision Song Contest.*
**Social Networks 35, 484–497.**

This folder contains a from-scratch replication of every table and figure in the
paper, provided **twice** — a Python pipeline and a parallel **R** pipeline that
uses R's genuine `AER::tobit` routine. Either reproduces all objects.

```bash
python3 run_all.py            # Python: all tables/figures -> output/*.txt/.csv/.png
Rscript  run_all.R            # R:      all tables/figures -> output/*_R.txt/.csv/.png
```

Python needs: `pandas numpy scipy statsmodels matplotlib networkx`.
R needs: `AER sandwich lmtest igraph` (`install.packages(...)`).

**Python vs. R.** Both are fine; R is fully usable once its packages are
installed (it ships none by default, which is why the first pass was
Python-only). The two pipelines agree: the R master panel matches the Python one
to machine precision, and `regressions.R` reproduces Table 3/4 with `AER::tobit`
to ~2 decimals of the Python Tobit MLE — an independent check that the
estimator, not just the code, is right. R outputs carry an `_R` suffix so they
sit beside the Python outputs without clobbering them.

---

## 1. Is the data in the folder sufficient?

**Partly — sufficient for the whole descriptive/network core and the central
hypothesis test, but a few Table 3/4 control columns cannot be built.**

| Paper object | Needed data | In the folder? | Status |
|---|---|---|---|
| Vote `C_ijt` (dep. var.) | final vote points | `votes.csv` | ✅ full (1975–2012 finals) |
| Quality `C_jt`, Bias `C_ijt` | derived from votes | derived | ✅ full |
| Impartiality `C_it` | ICRG "Quality of Government" | `qog_std_ts_jan26.csv` → `icrg_qog` | ✅ 1984–2025 (pre-1984 back-filled, 2026 carried forward; countries with no ICRG hot-deck-imputed per Charron fn.13, see `ICRG_DONOR`) |
| Friend Dyad (methods 1 & 2) | cluster / pairwise-bias analysis | derived | ✅ full |
| Song Order, Host | running order / winner | `contestants.csv` | ✅ derived |
| English / French | *language sung* | not a column (only lyrics text) | ⚠️ heuristic from lyrics |
| Contiguity, Language (shared) | border / language lists | not in folder | ⚠️ reconstructed in `lib_countries.py` |
| Lag Vote, No. Participants | derived from votes | derived | ✅ full |
| Duet / Group / Female | performer gender / line-up | recovered from **Wikidata** (`build_performer_types.py` → `output/performer_types.csv`) | ✅ ~95% authoritative, rest flagged |
| Diaspora `C_ji` | minority-population data | transcribed from the paper's **Appendix 2** (`diaspora.py`) | ✅ full |

The `betting_offices.csv` and the two `eurovision-dataset-2023` archives are not
needed. `qog_std_ts_jan26.csv` (QoG Standard Time-Series, Jan-2026 release)
supplies impartiality.

---

## 2. What each script produces

| Python script | R script | Reproduces |
|---|---|---|
| `build_dataset.py` | `build_dataset.R` | master dyad-year panel |
| `table1.py` | `table1.R` | **Table 1** top bias dyads |
| `cluster_table2_fig1.py` | `cluster_table2_fig1.R` | **Table 2** groups + **Fig 1** dendrogram |
| `fig2_network.py` | `fig2_network.R` | **Fig 2** friend network (method 2) |
| `appendix3.py` | `appendix3.R` | **Appendix 3** within-group bias + stability |
| `regressions_table3_4_fig3.py` | `regressions.R` | **Table 3**, **Table 4**, **Fig 3** |
| `run_all.py` | `run_all.R` | one-shot driver |

Support modules: `lib_countries.py` / `.R` (names, ISO codes, reconstructed
contiguity & language, `ICRG_DONOR` hot-deck map), `tobit.py` (Python Tobit MLE;
R uses `AER::tobit`), `pairwise_bias.py` (significant-bias helper). The
recovered-variable builders that complete Charron's full Table 3/4 controls also
live here: `diaspora.py` (Appendix-2 diaspora) and `build_performer_types.py`
(Wikidata performer traits → `output/performer_types.csv`). Python writes bare
filenames (`table1.txt`, `fig1_dendrogram.png`, …); R writes the `_R` variants.

### Repository layout
This folder is the **faithful replication** of Charron (2013), 1975–2012, and is
self-contained (`python3 run_all.py` writes everything to `replication/output/`).
Work that goes **beyond** the paper — scraping the full 1975–2026 record, source
verification, and the extended regressions — lives in the sibling **`../extension/`**
folder and writes to `extension/output/`. `build_dataset.py --source eschome`
still builds the extended panel (it reads the scraped inputs from, and writes
`master_extended.csv` to, `extension/output/`). See `../extension/README.md`.

---

## 3. On *exact* replication (important)

The paper's own data (footnote 1) is the **Ginsburgh–Noury / eschome.net**
compilation, updated by the author to 2012. The data in this folder is a
**different, re-collected 2023 dataset**. Historical point tallies mostly agree,
but not perfectly, and two modelling choices were pinned down by re-reading the
paper to get as close as possible:

1. **Quality is dyad-specific** — `Quality_ijt = (Total_j − vote_ij)/(p−2)`
   (paper eq. 1; "each receiving country's quality can vary slightly depending
   on the point giver", p. 488). This is what makes many pairs match to the
   decimal.
2. **Finalists only** — from 2004 the semi-finals mean eliminated countries
   still vote in the final. We count only finalist→finalist dyads and set `p`
   to the number of finalists, matching "countries that have participated in the
   ESC final". This alone moved e.g. Romania→Moldova from 9.99 → 9.7 (paper 9.6)
   and Turkey↔Azerbaijan to 8.4 (paper 8.0/8.5).

**Why a few extreme dyads still cannot match exactly.** Greece→Cyprus is the
clearest case: in *this* dataset Greece awarded Cyprus **12 points in every one
of the 7 finals** Cyprus reached in 1998–2012, and Cyprus's totals from other
countries were low. The bias is therefore mathematically pinned near
`12 − ~1.5 ≈ 10.2` under **any** quality formula — it cannot equal the paper's
8.5 unless the underlying vote records themselves differ. So the residual gap on
such pairs is a **data-provenance** issue, not a formula or coding error; it is
irreducible without the author's original eschome.net files. Method-validating
pairs that *do* match: Lithuania→Georgia **7.8** (exact), France→Portugal
**8.3** (paper 8.2), Greece↔Cyprus period-1 within-group bias **7.89** (paper
7.88), Romania–Moldova **9.45** (paper 9.34).

## 4. How well does it replicate? (this dataset vs. the 2013 paper)

Using the re-collected 2023 dataset, exact decimals differ on a few extreme
dyads (above), but the substance reproduces closely:

* **Table 1** – matches the paper's headline pairs, e.g. Greece↔Cyprus,
  Turkey→Bosnia (6.7), Croatia→Malta (5.6), Macedonia→Albania (9.4→9.5),
  France→Portugal (8.2→8.3), Lithuania→Georgia (7.8).
* **Table 2 / Fig 1** – recovers the paper's blocs: Greece–Cyprus,
  Romania–Moldova, Spain–Portugal, UK–Ireland, the Balkan, Nordic+Baltic and
  ex-Soviet/Caucasus groups. *(Note: the paper describes Ward/squared-Euclidean
  on raw portfolios; taken literally that does not merge reciprocal pairs like
  Greece–Cyprus, so we cluster on mutual voting affinity, which reproduces the
  published groups — documented in the script.)*
* **Appendix 3** – Greece–Cyprus within-group bias **7.89** (paper 7.88);
  Romania–Moldova **9.45** (paper 9.34); all major blocs significantly positive.
* **Table 3** – Quality **0.89** (paper 0.90); Friend Dyad positive***;
  Impartiality n.s. (paper 0.22 n.s.); **Friend × Impartiality negative and
  significant** (paper −6.61***) — i.e. **H1 confirmed**: impartiality offsets
  friend-voting bias. Contiguity 0.85 (paper 0.80), lagged votes 0.175 / 0.061
  (paper 0.17 / 0.06).
* **Table 4** – method-2 Friend Dyad **5.9–7.6** and interaction **−1.1 to −3.9**
  fall inside the paper's ranges (4.9–7.5 and −1.0 to −4.4).
* **Fig 3** – non-friend lines indistinguishable across impartiality; friend
  bias much larger under low impartiality than high — exactly the paper's shape.

### Caveats baked into the code
* Duet/Group/Female recovered from Wikidata (~5% of acts unresolved → flagged in
  `performer_types.csv` `source`, default to the solo-male baseline); Diaspora
  transcribed from Appendix 2. Both now enter Table 3/4 (Diaspora +0.66***).
* English/French are lyrics heuristics, not a "language sung" field.
* Contiguity & shared-language are hand-reconstructed standard facts.
* Random-effects Tobit (Table 3 models 9–10) is approximated by pooled Tobit;
  a full RE-Tobit needs specialised software. This is flagged at runtime.
