# Extension — beyond Charron (2013)

Everything here **extends** the paper past its 1975–2012 window and original data.
The faithful replication lives in the sibling [`../replication/`](../replication)
folder; this folder depends on its shared modules but keeps its own data and
outputs.

```
python3 run_all_extension.py       # build extended panel + all extension analyses
```

Outputs go to **`extension/output/`**; the replication's artifacts stay in
`../replication/output/`.

## What each script does

| Script | Purpose | Reads | Writes (`extension/output/`) |
|---|---|---|---|
| `scrape_eschome.py` | scrape the full 1975–2026 dyadic vote record from eschome.net (cached, resumable) | eschome.net | `votes_eschome.csv`, `eschome_cache/` |
| `scrape_finalists.py` | scrape the explicit finalist roster (running order, placing) | eschome.net | `finalists_eschome.csv` |
| `compare_sources.py` | verify scraped vs bundled `votes.csv` vs the official result | `../votes.csv`, `votes_eschome.csv` | `source_mismatches.csv`, `source_coverage_gaps.csv` |
| `diagnose_table1.py` | Table-1 televote-era diagnostic (why extreme dyads diverge) | `votes_eschome.csv`, `finalists_eschome.csv` | (console) |
| `extend_table3_4.py` | re-estimate Table 3 & 4 on the 1975–2026 panel; `--dv2016 jury` robustness | `master_extended.csv` | `table3/4_extended*.txt` |
| `eurovision_voting_rules.md` | reference on ESC scoring/voting rules by era | — | — |

## Dependencies on the replication folder

- The **extended panel** is built by the shared `../replication/build_dataset.py
  --source eschome`. It reads the scraped inputs from and writes
  `master_extended.csv` to **`extension/output/`** (bundled/replication mode still
  writes `master.csv` to `../replication/output/`).
- `extend_table3_4.py` reuses the replication's estimators/helpers
  (`tobit`, `cluster_table2_fig1`, `pairwise_bias`, `regressions_table3_4_fig3`)
  via a `sys.path` insert of `../replication`.
- The recovered-variable builders (`diaspora.py`, `build_performer_types.py`) stay
  in `../replication` because they complete Charron's *own* Table 3/4 controls and
  feed the bundled panel too.

## Key result

Charron's H1 (Friend × Impartiality < 0) holds pooled and through 2015, but the
2016–2026 split-vote **televote** breaks it down (juries still moderate). Diaspora
(+0.25\*\*\* televote era) behaves as the paper predicts. Full log in
[`SUMMARY.md`](SUMMARY.md).
