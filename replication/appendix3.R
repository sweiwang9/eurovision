# appendix3.R
# ===========
# R port of appendix3.py: within-group bias tests (Part A) and the year-by-year
# stability table for 1998-2012 groups (Part B).

get_here <- function() {
  a <- commandArgs(FALSE); m <- grep("^--file=", a)
  if (length(m)) return(dirname(normalizePath(sub("^--file=", "", a[m]))))
  getwd()
}
here <- get_here(); OUT <- file.path(here, "output")
df <- read.csv(file.path(OUT, "master_R.csv"), stringsAsFactors = FALSE)
PERIODS <- list(c("1975-1997", 1975, 1997), c("1998-2012", 1998, 2012))

# within-group directed dyad-year biases for a period
within <- function(d, groups, lo, hi) {
  code2grp <- setNames(groups$group, groups$code)
  s <- d[d$year >= lo & d$year <= hi, ]
  s$gi <- code2grp[s$i]; s$gj <- code2grp[s$j]
  s[which(!is.na(s$gi) & !is.na(s$gj) & s$gi == s$gj & s$i != s$j), ]
}

# ---- Part A: beta = mean within-group bias, t-tested against 0. ------------
lines <- c("Appendix 3 (R, Part A). Test of within-group bias (beta = mean bias).", "")
for (per in PERIODS) {
  g <- read.csv(file.path(OUT, sprintf("friend_groups_R_%s.csv", per[1])), stringsAsFactors = FALSE)
  w <- within(df, g, as.integer(per[2]), as.integer(per[3]))
  lines <- c(lines, sprintf("=== %s ===", per[1]),
             sprintf("%-6s%8s%10s%7s   %s", "Group", "Beta", "p-value", "N", "members"))
  members <- tapply(g$country, g$group, function(x) paste(x, collapse = ", "))
  for (grp in sort(unique(w$gi))) {
    b <- w$bias[w$gi == grp]; if (length(b) < 2) next
    beta <- mean(b)
    p <- if (length(unique(b)) == 1) ifelse(abs(beta) > 1e-9, 0, 1) else t.test(b, mu = 0)$p.value
    lines <- c(lines, sprintf("%-6s%8.2f%10.3f%7d   %s", grp, beta, p, length(b), members[[grp]]))
  }
  lines <- c(lines, "")
}
cat(paste(lines, collapse = "\n"), "\n")
writeLines(lines, file.path(OUT, "appendix3_partA_R.txt"))

# ---- Part B: within-group average bias by year, 1998-2012. -----------------
g <- read.csv(file.path(OUT, "friend_groups_R_1998-2012.csv"), stringsAsFactors = FALSE)
w <- within(df, g, 1998, 2012)
tab <- round(tapply(w$bias, list(w$gi, w$year), mean), 1)
ave <- round(tapply(w$bias, w$gi, mean), 1)
tab <- cbind(tab, Ave.Total = ave[rownames(tab)])
write.csv(tab, file.path(OUT, "appendix3_partB_stability_R.csv"))
cat("\nAppendix 3 (R, Part B). Within-group average bias by year 1998-2012:\n")
print(tab)
