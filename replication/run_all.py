"""
run_all.py
==========
One-shot driver: rebuild the master panel and regenerate every table and figure
in the Charron (2013) replication, in dependency order.

    python3 run_all.py

Outputs land in ./output/ (text tables, CSVs, and PNG figures).
"""

import runpy
import os
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

STEPS = [
    ("build_dataset.py",          "Master dyad-year panel"),
    ("table1.py",                 "Table 1  - top bias dyads"),
    ("cluster_table2_fig1.py",    "Table 2 + Fig 1  - friend groups / dendrogram"),
    ("fig2_network.py",           "Fig 2  - friend network (method 2)"),
    ("appendix3.py",              "Appendix 3  - within-group bias"),
    # Python regressions also EXPORT output/regression_data.csv (the merged,
    # N-matched frame) for R to estimate on.
    ("regressions_table3_4_fig3.py", "Tables 3-4 + Fig 3  - regressions (+ export regression_data.csv)"),
]

for script, desc in STEPS:
    print("\n" + "=" * 78)
    print(f"RUNNING {script}  --  {desc}")
    print("=" * 78)
    runpy.run_path(os.path.join(HERE, script), run_name="__main__")

# AUTHORITATIVE estimation is done in R (AER::tobit is a stable, standard Tobit;
# the Python MLE is only a cross-check).  regressions.R reads the Python-exported
# regression_data.csv and writes table3_R.txt / table4_R.txt.
print("\n" + "=" * 78)
print("RUNNING regressions.R  --  Tables 3-4 (authoritative, AER::tobit)")
print("=" * 78)
if shutil.which("Rscript"):
    subprocess.run(["Rscript", os.path.join(HERE, "regressions.R")], check=True)
else:
    print("Rscript not found on PATH -- skipping the R tables (install R + "
          "AER/sandwich/lmtest to regenerate table3_R.txt / table4_R.txt).")

print("\nAll steps complete.  See ./output/ for tables (.txt/.csv) and figures (.png).")
