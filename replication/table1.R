# table1.R
# ========
# R port of table1.py: Table 1, top-10 most biased dyads pre/post televoting.
# Average each ordered dyad's bias within a period; require >= 3 observations.

get_here <- function() {
  a <- commandArgs(FALSE); m <- grep("^--file=", a)
  if (length(m)) return(dirname(normalizePath(sub("^--file=", "", a[m]))))
  getwd()
}
here <- get_here(); source(file.path(here, "lib_countries.R"))
OUT <- file.path(here, "output")
df <- read.csv(file.path(OUT, "master_R.csv"), stringsAsFactors = FALSE)
MIN_OBS <- 3

top_dyads <- function(d, lo, hi, n = 10) {
  s <- d[d$year >= lo & d$year <= hi, ]
  key <- paste(s$i, s$j)
  agg <- data.frame(
    key = names(tapply(s$bias, key, mean)),
    bias = as.numeric(tapply(s$bias, key, mean)),
    n = as.integer(tapply(s$bias, key, length)))
  agg <- agg[agg$n >= MIN_OBS, ]
  agg <- agg[order(-agg$bias), ][seq_len(min(n, nrow(agg))), ]
  parts <- do.call(rbind, strsplit(agg$key, " "))
  agg$i <- parts[, 1]; agg$j <- parts[, 2]; agg
}

lines <- c("Table 1 (R). Top 10 most bias dyads pre and post televoting.", "")
for (per in list(c("1975-1997", 1975, 1997), c("1998-2012", 1998, 2012))) {
  t <- top_dyads(df, as.integer(per[2]), as.integer(per[3]))
  lines <- c(lines, sprintf("=== %s ===", per[1]),
             sprintf("%-5s%-22s%-22s%6s%5s", "Rank", "Voter", "Receiver", "Bias", "N"))
  for (k in seq_len(nrow(t)))
    lines <- c(lines, sprintf("%-5d%-22s%-22s%6.1f%5d", k,
                              NAME[t$i[k]], NAME[t$j[k]], t$bias[k], t$n[k]))
  lines <- c(lines, "")
}
cat(paste(lines, collapse = "\n"), "\n")
writeLines(lines, file.path(OUT, "table1_R.txt"))
