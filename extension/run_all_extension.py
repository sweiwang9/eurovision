"""
run_all_extension.py
====================
One-shot driver for the EXTENSION pipeline (everything beyond Charron's 1975-2012
replication).  Assumes the scraped inputs already exist in extension/output/
(votes_eschome.csv, finalists_eschome.csv); re-scrape only when refreshing data:

    python3 scrape_eschome.py       # 1975-2026 dyadic votes  (slow, cached)
    python3 scrape_finalists.py     # explicit finalist roster

Then:

    python3 run_all_extension.py

Steps (in dependency order):
  1. build the extended 1975-2026 panel  -> extension/output/master_extended.csv
     (calls the shared builder in ../replication with --source eschome; it reads
      the scraped inputs from and writes the master back to extension/output/)
  2. extended Table 3 & 4                 -> extension/output/table3/4_extended*.txt
  3. source verification (eschome vs bundled vs official)
  4. Table-1 televote-era diagnostic

Outputs land in extension/output/.  The pure-replication artifacts stay untouched
in ../replication/output/.
"""

import os
import runpy
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPL = os.path.join(os.path.dirname(HERE), "replication")
os.chdir(HERE)


def run_local(script, desc, argv=None):
    print("\n" + "=" * 78 + f"\nRUNNING {script}  --  {desc}\n" + "=" * 78)
    saved = sys.argv
    sys.argv = [script] + (argv or [])
    try:
        runpy.run_path(os.path.join(HERE, script), run_name="__main__")
    finally:
        sys.argv = saved


# 1. Extended panel via the shared builder in ../replication (subprocess so its
#    __file__/paths resolve there; it targets extension/output/ for eschome mode).
print("\n" + "=" * 78 + "\nRUNNING build_dataset.py --source eschome  (../replication)\n" + "=" * 78)
subprocess.run([sys.executable, os.path.join(REPL, "build_dataset.py"),
                "--source", "eschome"], check=True)

# 2. Extended Tables 3 & 4 in Python (also EXPORTS regression_data_extended.csv).
run_local("extend_table3_4.py", "Extended Tables 3 & 4 (1975-2026)")

# 3. Authoritative R re-estimation (AER::tobit), same as the replication.
print("\n" + "=" * 78 + "\nRUNNING extend_regressions.R  --  Extended Tables 3-4 (R, AER::tobit)\n" + "=" * 78)
import shutil
if shutil.which("Rscript"):
    subprocess.run(["Rscript", os.path.join(HERE, "extend_regressions.R")], check=True)
else:
    print("Rscript not found on PATH -- skipping the R extended tables.")

# 4. Jury-channel / public-channel panels + Rest-of-World benchmark (build + R).
run_local("channel_rest_analysis.py", "Jury/public channel panels + Rest-of-World")
print("\n" + "=" * 78 + "\nRUNNING channel_rest_regressions.R  (R, AER::tobit)\n" + "=" * 78)
if shutil.which("Rscript"):
    subprocess.run(["Rscript", os.path.join(HERE, "channel_rest_regressions.R")], check=True)
else:
    print("Rscript not found -- skipping the channel/Rest-of-World R tables.")

# 5-6. Verification / diagnostics.
run_local("compare_sources.py", "Source verification (eschome vs bundled)")
run_local("diagnose_table1.py", "Table-1 televote-era diagnostic")

print("\nExtension pipeline complete.  See extension/output/.")
