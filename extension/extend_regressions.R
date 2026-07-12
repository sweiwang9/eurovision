# extend_regressions.R
# ====================
# AUTHORITATIVE estimator for the EXTENSION (same R/AER::tobit as the replication).
# Python (extend_table3_4.py) does the extended data build -- eschome 1975-2026 with
# fn.18 ever-finalist givers, cumulative ">=2 finals" entry, the 0-12 vote12 DV, and
# Charron Table-2 friend groups -- and exports output/regression_data_extended.csv.
# This script only ESTIMATES it, so R and Python cannot drift on the sample.
#
#     python3 extend_table3_4.py          # builds + exports regression_data_extended.csv
#     Rscript extend_regressions.R
#
# Requires: AER, sandwich, lmtest.

suppressMessages({
  library(AER)        # tobit()
  library(sandwich)   # HC1 robust covariance for OLS
  library(lmtest)     # coeftest()
})

get_here <- function() {
  a <- commandArgs(FALSE); m <- grep("^--file=", a)
  if (length(m)) return(dirname(normalizePath(sub("^--file=", "", a[m]))))
  getwd()
}
here <- get_here(); out <- file.path(here, "output")
df <- read.csv(file.path(out, "regression_data_extended.csv"), stringsAsFactors = FALSE)
# `vote` is the 0-12 vote12 DV; imp_i is fully populated (extension imputes broadly).

star <- function(p) ifelse(p < .01, "***", ifelse(p < .05, "**", ifelse(p < .10, "*", "")))
cell <- function(b, se, p) sprintf("%.3f%s (%.3f)", b, star(p), se)

run_ols <- function(d, rhs) {
  keep <- rhs[sapply(rhs, function(v) length(unique(d[[v]][!is.na(d[[v]])])) > 1)]
  m <- lm(as.formula(paste("vote ~", paste(keep, collapse = " + "))), data = d)
  ct <- coeftest(m, vcov = vcovHC(m, type = "HC1"))
  list(coef = ct[, 1], se = ct[, 2], p = ct[, 4], n = nobs(m), kind = "OLS")
}
run_tobit <- function(d, rhs) {
  keep <- rhs[sapply(rhs, function(v) length(unique(d[[v]][!is.na(d[[v]])])) > 1)]
  m <- tobit(as.formula(paste("vote ~", paste(keep, collapse = " + "))),
             left = -Inf, right = 12, data = d)
  s <- summary(m)$coefficients
  n <- sum(stats::complete.cases(d[, c("vote", keep)]))
  list(coef = s[, 1], se = s[, 2], p = s[, 4], n = n, kind = "Tobit")
}

print_table <- function(results, labels, rows) {
  hdr <- paste0(formatC("", width = 12),
                paste(sapply(labels, formatC, width = 20, flag = "-"), collapse = ""))
  lines <- hdr
  for (rn in rows) {
    line <- formatC(rn, width = 12, flag = "-")
    for (r in results)
      line <- paste0(line, formatC(if (rn %in% names(r$coef))
        cell(r$coef[rn], r$se[rn], r$p[rn]) else "", width = 20, flag = "-"))
    lines <- c(lines, line)
  }
  nl <- formatC("N", width = 12, flag = "-")
  for (r in results) nl <- paste0(nl, formatC(as.character(r$n), width = 20, flag = "-"))
  c(lines, nl)
}

# Controls: extension set (English/French dropped -- no 2024-26 lyrics).
BASE  <- c("quality","friend_m1","imp_i","fm1_x_imp","song_order","host",
           "contig","language","n_part","duet","group","female")
BASE2 <- c("quality","friend_m2","imp_i","fm2_x_imp","song_order","host",
           "contig","language","n_part","duet","group","female")

# ---- Table 3 (extended) ----------------------------------------------------
s3 <- list(
  list("1 OLS all",      run_ols,   df,                          BASE),
  list("2 OLS 75-97",    run_ols,   subset(df, year<=1997),      BASE),
  list("3 OLS 98-26",    run_ols,   subset(df, year>=1998),      BASE),
  list("4 OLS 16-26",    run_ols,   subset(df, year>=2016),      BASE),
  list("5 OLS +lagIJ",   run_ols,   df,                          c(BASE,"lag_vote_ij")),
  list("7 Tobit lagIJ",  run_tobit, df,                          c(BASE,"lag_vote_ij")),
  list("9 OLS 98-26+dia",run_ols,   subset(df, year>=1998),      c(BASE,"diaspora"))
)
res3 <- lapply(s3, function(s) s[[2]](s[[3]], s[[4]]))
rows3 <- c("quality","friend_m1","imp_i","fm1_x_imp","diaspora","contig","language",
           "lag_vote_ij","song_order","host","n_part")
t3 <- print_table(res3, sapply(s3, `[[`, 1), rows3)
writeLines(c("Table 3 (EXTENDED 1975-2026; R: OLS + AER::tobit).", "", t3, "",
             "Signif: *** p<.01, ** p<.05, * p<.10. DV = 0-12 vote (televote half 2016+)."),
           file.path(out, "table3_extended_R.txt"))
cat(t3, sep = "\n"); cat("\n\n")

# ---- Table 4 (extended): friend measure x voting-rule era -----------------
subs <- list(all = df, jury = subset(df, year<=1997),
             tele = subset(df, year>=1998 & year<=2008),
             hybrid = subset(df, year>=2009 & year<=2015),
             split = subset(df, year>=2016), tvera = subset(df, year>=1998))
s4 <- list(
  list("M2 all",         BASE2,               subs$all),
  list("M2 jury",        BASE2,               subs$jury),
  list("M2 tele",        BASE2,               subs$tele),
  list("M2 hybrid",      BASE2,               subs$hybrid),
  list("M2 split16-26",  BASE2,               subs$split),
  list("M2 98-26+dia",   c(BASE2,"diaspora"), subs$tvera),
  list("M1 all",         BASE,                subs$all),
  list("M1 split16-26",  BASE,                subs$split)
)
res4 <- lapply(s4, function(s) run_tobit(s[[3]], s[[2]]))
rows4 <- c("quality","friend_m2","friend_m1","imp_i","fm2_x_imp","fm1_x_imp","diaspora")
t4 <- print_table(res4, sapply(s4, `[[`, 1), rows4)
writeLines(c("Table 4 (EXTENDED; R: AER::tobit).", "", t4, "",
             "Signif: *** p<.01, ** p<.05, * p<.10."),
           file.path(out, "table4_extended_R.txt"))
cat(t4, sep = "\n"); cat("\n")
cat("\nWrote output/table3_extended_R.txt and output/table4_extended_R.txt.\n")
