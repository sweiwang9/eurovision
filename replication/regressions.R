# regressions.R
# =============
# R replication of Table 3 & Table 4, using R's genuine Tobit routine
# (AER::tobit, a wrapper around survival::survreg) rather than a hand-rolled
# MLE.  This mirrors the paper, which estimates a right-censored Tobit on the
# 0-12 vote.  Run the Python pipeline first (it writes output/regression_data.csv):
#
#     python3 build_dataset.py
#     python3 cluster_table2_fig1.py
#     python3 fig2_network.py
#     python3 regressions_table3_4_fig3.py   # exports regression_data.csv
#     Rscript regressions.R
#
# Requires: AER, sandwich, lmtest  (install.packages(c("AER","sandwich","lmtest")))

suppressMessages({
  library(AER)        # tobit()
  library(sandwich)   # robust (Huber-White) covariance for OLS
  library(lmtest)     # coeftest()
  library(censReg)    # random-effects panel Tobit (models 9-10, Table 4)
  library(plm)        # pdata.frame panel structure
})

get_here <- function() {
  a <- commandArgs(FALSE); m <- grep("^--file=", a)
  if (length(m)) return(dirname(normalizePath(sub("^--file=", "", a[m]))))
  if (!is.null(sys.frame(1)$ofile)) return(dirname(normalizePath(sys.frame(1)$ofile)))
  getwd()
}
here <- get_here(); out <- file.path(here, "output")

# SINGLE SOURCE OF TRUTH for the data: the Python build (build_dataset.py) does
# all the careful sample construction -- Charron's eschome source, fn.18 ever-
# finalist givers, cumulative ">=2 finals" entry, fn.13 impartiality, 1983 start
# -- and exports the fully-merged, regression-ready frame (incl. friend_m1,
# friend_m2 and the interactions).  R is the ESTIMATOR (AER::tobit), reading that
# frame, so the two languages cannot drift apart on the sample definition.
df <- read.csv(file.path(out, "regression_data.csv"), stringsAsFactors = FALSE)
# imp_i is NA before ICRG (pre-1983) and for dropped no-ICRG voters; those rows
# leave the impartiality regressions automatically (lm/tobit drop NA rows).
df$dyad <- paste(df$i, df$j)          # panel unit for the random-effects Tobit

# ---- Helper: format one coefficient with significance stars. --------------
star <- function(p) ifelse(p < .01, "***", ifelse(p < .05, "**", ifelse(p < .10, "*", "")))
cell <- function(b, se, p) sprintf("%.3f%s (%.3f)", b, star(p), se)

# ---- OLS with Huber-White (HC1) robust SEs (Table 3 models 1-6). ----------
run_ols <- function(d, rhs) {
  f <- as.formula(paste("vote ~", paste(rhs, collapse = " + ")))
  m <- lm(f, data = d)
  ct <- coeftest(m, vcov = vcovHC(m, type = "HC1"))
  list(coef = ct[, 1], se = ct[, 2], p = ct[, 4],
       n = nobs(m), kind = "OLS")
}

# ---- Right-censored Tobit at 12 (Table 3 models 7-10; all of Table 4). -----
# Within a voting-rule subset some regressors can become constant (e.g. no host
# in a short window); drop those zero-variance columns so the model is not
# rank-deficient (which otherwise breaks summary.tobit's Wald test).
run_tobit <- function(d, rhs) {
  keep <- rhs[sapply(rhs, function(v) length(unique(d[[v]][!is.na(d[[v]])])) > 1)]
  f <- as.formula(paste("vote ~", paste(keep, collapse = " + ")))
  m <- tobit(f, left = -Inf, right = 12, data = d)   # upper-censored at 12
  s <- summary(m)$coefficients
  # actual estimation N = complete cases on the outcome and the kept regressors
  # (survreg drops rows with a missing imp_i, so this is < nrow when imp is NA).
  n <- sum(stats::complete.cases(d[, c("vote", keep)]))
  list(coef = s[, 1], se = s[, 2], p = s[, 4], n = n, kind = "Tobit")
}

# ---- Random-effects Tobit (dyad-level RE), Table 3 models 9-10. ------------
# censReg panel Tobit via Gauss-Hermite quadrature.  Two robustness details:
#   * we supply START VALUES from a pooled Tobit with a POSITIVE logSigmaMu, so
#     the optimiser does not collapse the RE variance to the 0 boundary (which
#     otherwise yields a singular Hessian / infinite SEs);
#   * complete-case panel so pdata.frame indices are clean.
run_retobit <- function(d, rhs) {
  keep <- rhs[sapply(rhs, function(v) length(unique(d[[v]][!is.na(d[[v]])])) > 1)]
  d2 <- d[stats::complete.cases(d[, c("vote", "dyad", "year", keep)]), ]
  f <- as.formula(paste("vote ~", paste(keep, collapse = " + ")))
  pooled <- censReg(f, left = -Inf, right = 12, data = d2)      # for start values
  b <- coef(pooled)
  st <- c(b[-length(b)], logSigmaMu = log(1.0), logSigmaNu = b[length(b)])
  m <- censReg(f, left = -Inf, right = 12, data = plm::pdata.frame(d2, index = c("dyad", "year")),
               method = "BHHH", nGHQ = 12, start = st)
  cf <- coef(summary(m))
  su <- exp(cf["logSigmaMu", 1]); sv <- exp(cf["logSigmaNu", 1])
  list(coef = cf[, 1], se = cf[, 2], p = cf[, 4], n = nrow(d2), kind = "RE-Tobit",
       sigma_u = su, sigma_e = sv, rho = su^2 / (su^2 + sv^2))
}

# Base right-hand-side.  Duet/Group/Female (Wikidata) and Diaspora (Appendix 2)
# are now recovered and present in the data, so this is Charron's full control set.
BASE <- c("quality", "friend_m1", "imp_i", "fm1_x_imp",
          "english", "french", "duet", "group", "female", "song_order", "host",
          "contig", "language", "n_part")

# ---------------------------------------------------------------------------
# Table 3.
# ---------------------------------------------------------------------------
cat("\n================ Table 3 (R: OLS + AER::tobit) ================\n")
specs3 <- list(
  list("1 OLS all",     run_ols,   df,                 BASE),
  list("2 OLS 75-97",   run_ols,   subset(df, year<=1997), BASE),
  list("3 OLS 98-12",   run_ols,   subset(df, year>=1998), BASE),
  list("4 OLS 98+Dia",  run_ols,   subset(df, year>=1998), c(BASE, "diaspora")),
  list("5 OLS +lagIJ",  run_ols,   df,                 c(BASE, "lag_vote_ij")),
  list("6 OLS +lagJI",  run_ols,   df,                 c(BASE, "lag_vote_ji")),
  list("7 Tobit lagIJ", run_tobit, df,                 c(BASE, "lag_vote_ij")),
  list("8 Tobit lagJI", run_tobit, df,                 c(BASE, "lag_vote_ji")),
  list("9 RE-Tob lagIJ",run_retobit, df,               c(BASE, "lag_vote_ij")),
  list("10 RE-Tob lagJI",run_retobit, df,              c(BASE, "lag_vote_ji"))
)
rows3 <- c("quality","friend_m1","imp_i","fm1_x_imp","diaspora","contig","language",
           "lag_vote_ij","lag_vote_ji","song_order","host","n_part")

results3 <- lapply(specs3, function(s) s[[2]](s[[3]], s[[4]]))
labels3  <- sapply(specs3, `[[`, 1)

print_table <- function(results, labels, rows) {
  hdr <- paste0(formatC("", width = 12),
                paste(sapply(labels, formatC, width = 20, flag = "-"), collapse = ""))
  cat(hdr, "\n")
  for (rn in rows) {
    line <- formatC(rn, width = 12, flag = "-")
    for (r in results) {
      v <- if (rn %in% names(r$coef)) cell(r$coef[rn], r$se[rn], r$p[rn]) else ""
      line <- paste0(line, formatC(v, width = 20, flag = "-"))
    }
    cat(line, "\n")
  }
  nl <- formatC("N", width = 12, flag = "-")
  for (r in results) nl <- paste0(nl, formatC(as.character(r$n), width = 20, flag = "-"))
  cat(nl, "\n")
  # variance components for any random-effects Tobit columns
  if (any(sapply(results, function(r) !is.null(r$rho)))) {
    for (comp in c("sigma_u", "sigma_e", "rho")) {
      line <- formatC(comp, width = 12, flag = "-")
      for (r in results) {
        v <- if (!is.null(r[[comp]])) sprintf("%.3f", r[[comp]]) else ""
        line <- paste0(line, formatC(v, width = 20, flag = "-"))
      }
      cat(line, "\n")
    }
  }
}
t3 <- capture.output(print_table(results3, labels3, rows3))
writeLines(c("Table 3 (R: OLS + AER::tobit; data = Python regression_data.csv)", "",
             t3, "", "Signif: *** p<.01, ** p<.05, * p<.10.  SE in parentheses.",
             "Tobit = AER::tobit (survreg, right-censored at 12)."),
           file.path(out, "table3_R.txt"))
cat(t3, sep = "\n"); cat("\n")

# ---------------------------------------------------------------------------
# Table 4 -- alternative friend measure (method 2) x voting-rule subsets,
# all estimated with AER::tobit.
# ---------------------------------------------------------------------------
cat("\n================ Table 4 (R: AER::tobit) ================\n")
BASE2 <- c("quality", "friend_m2", "imp_i", "fm2_x_imp",
           "english", "french", "duet", "group", "female", "song_order", "host",
           "contig", "language", "n_part")
# "Alternative Friend Group Method 1" = Table 2 with the weak 'a' members removed.
BASE_ALT <- c("quality", "friend_m1_alt", "imp_i", "fm1alt_x_imp",
              "english", "french", "duet", "group", "female", "song_order", "host",
              "contig", "language", "n_part")
sub_all <- df
sub_jury <- subset(df, year <= 1997)
sub_tele <- subset(df, year >= 1998 & year <= 2008)
sub_hyb  <- subset(df, year >= 2009)
specs4 <- list(
  list("M2 all",     BASE2,    sub_all), list("M2 jury",   BASE2,    sub_jury),
  list("M2 tele",    BASE2,    sub_tele),list("M2 hybrid", BASE2,    sub_hyb),
  list("M1alt all",  BASE_ALT, sub_all), list("M1alt jury",BASE_ALT, sub_jury),
  list("M1alt tele", BASE_ALT, sub_tele),list("M1alt hybrid",BASE_ALT, sub_hyb)
)
results4 <- lapply(specs4, function(s) run_tobit(s[[3]], s[[2]]))
labels4  <- sapply(specs4, `[[`, 1)
rows4 <- c("quality","friend_m2","friend_m1_alt","imp_i","fm2_x_imp","fm1alt_x_imp")
t4 <- capture.output(print_table(results4, labels4, rows4))
writeLines(c("Table 4 (R: AER::tobit; data = Python regression_data.csv)", "",
             t4, "", "Signif: *** p<.01, ** p<.05, * p<.10.  SE in parentheses.",
             "Tobit = AER::tobit (survreg, right-censored at 12)."),
           file.path(out, "table4_R.txt"))
cat(t4, sep = "\n"); cat("\n")

cat("\nNote: signif *** p<.01, ** p<.05, * p<.10; SE in parentheses.\n")
cat("Tobit fitted with AER::tobit (survreg, right-censored at 12).\n")
cat("Wrote output/table3_R.txt and output/table4_R.txt.\n")

# ---------------------------------------------------------------------------
# Fig. 3 -- marginal effect of friend voting over song quality, by impartiality
# (mean +/- 1 s.d.) and friend status, from the Table-3 Tobit (model 7 here).
# ---------------------------------------------------------------------------
m9 <- results3[[6]]$coef              # "7 Tobit lagIJ" coefficients
b <- function(n) if (n %in% names(m9)) m9[[n]] else 0
q0 <- mean(df$quality); qs <- sd(df$quality)
qgrid <- seq(q0, q0 + 2 * qs, length.out = 50)
imp_lo <- mean(df$imp_i) - sd(df$imp_i); imp_hi <- mean(df$imp_i) + sd(df$imp_i)
means <- sapply(c("english","french","song_order","host","contig","language",
                  "n_part","lag_vote_ij"), function(c) mean(df[[c]], na.rm = TRUE))
pred <- function(friend, imp) {
  v <- b("(Intercept)") + b("quality") * qgrid + b("friend_m1") * friend +
       b("imp_i") * imp + b("fm1_x_imp") * friend * imp
  for (c in names(means)) v <- v + b(c) * means[[c]]
  pmin(pmax(v, 0), 12)
}
png(file.path(out, "fig3_marginal_effects_R.png"), width = 900, height = 600, res = 120)
plot(qgrid, pred(1, imp_lo), type = "l", lty = 1, lwd = 2, ylim = c(0, 12),
     xlab = "Song quality of country j", ylab = "Predicted vote i -> j",
     main = "Fig. 3 (R). Marginal effect of friend voting, by impartiality")
lines(qgrid, pred(1, imp_hi), lty = 1, lwd = 1)
lines(qgrid, pred(0, imp_lo), lty = 2, lwd = 2)
lines(qgrid, pred(0, imp_hi), lty = 3, lwd = 1)
legend("topleft", lty = c(1, 1, 2, 3), lwd = c(2, 1, 2, 1),
       legend = c("low imp, F.D.=1", "high imp, F.D.=1",
                  "low imp, F.D.=0", "high imp, F.D.=0"))
dev.off()
cat("Fig 3 saved -> output/fig3_marginal_effects_R.png\n")
