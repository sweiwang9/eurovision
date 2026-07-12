# run_all.R
# =========
# One-shot driver for the full R pipeline (mirrors run_all.py). Regenerates the
# R master panel, all tables, all figures and the regressions, in order.
#
#     Rscript run_all.R
#
# Outputs land in ./output/ with an _R suffix so they sit alongside the Python
# outputs without clobbering them.

get_here <- function() {
  a <- commandArgs(FALSE); m <- grep("^--file=", a)
  if (length(m)) return(dirname(normalizePath(sub("^--file=", "", a[m]))))
  getwd()
}
here <- get_here()

steps <- list(
  c("build_dataset.R",       "Master dyad-year panel"),
  c("table1.R",              "Table 1  - top bias dyads"),
  c("cluster_table2_fig1.R", "Table 2 + Fig 1"),
  c("fig2_network.R",        "Fig 2 network (method 2)"),
  c("appendix3.R",           "Appendix 3"),
  c("regressions.R",         "Tables 3-4 + Fig 3")
)
for (s in steps) {
  cat("\n", strrep("=", 70), "\nRUNNING ", s[1], "  --  ", s[2], "\n",
      strrep("=", 70), "\n", sep = "")
  system2("Rscript", file.path(here, s[1]))
}
cat("\nAll R steps complete. See ./output/ for *_R tables and figures.\n")
