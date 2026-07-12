# cluster_table2_fig1.R
# =====================
# R port of cluster_table2_fig1.py: Table 2 friend groups + Fig 1 dendrogram.
# Countries are clustered on mutual voting affinity (avg points exchanged);
# average-linkage hclust, cut into the paper's group counts.  See the Python
# module docstring for why mutual affinity (not Ward-on-portfolio) reproduces
# the published groups.

get_here <- function() {
  a <- commandArgs(FALSE); m <- grep("^--file=", a)
  if (length(m)) return(dirname(normalizePath(sub("^--file=", "", a[m]))))
  getwd()
}
here <- get_here(); source(file.path(here, "lib_countries.R"))
OUT <- file.path(here, "output")
df <- read.csv(file.path(OUT, "master_R.csv"), stringsAsFactors = FALSE)

N_GROUPS <- c("1975-1997" = 10, "1998-2012" = 13)
PERIODS <- list(c("1975-1997", 1975, 1997), c("1998-2012", 1998, 2012))

# Build the mutual-affinity distance object for a period.
build_dist <- function(d, lo, hi) {
  s <- d[d$year >= lo & d$year <= hi, ]
  app <- tapply(s$year, s$j, function(x) length(unique(x)))
  cc <- sort(names(app)[app >= 3])
  s <- s[s$i %in% cc & s$j %in% cc, ]
  give <- matrix(0, length(cc), length(cc), dimnames = list(cc, cc))
  mv <- tapply(s$vote, paste(s$i, s$j), mean)
  ij <- do.call(rbind, strsplit(names(mv), " "))
  for (k in seq_along(mv)) give[ij[k, 1], ij[k, 2]] <- mv[k]
  mutual <- (give + t(give)) / 2; diag(mutual) <- 0
  D <- max(mutual) - mutual; diag(D) <- 0
  list(cc = cc, dist = as.dist(D))
}

# ---- Table 2: cut each period's tree into the paper's number of groups. ----
lines <- c("Table 2 (R). Friend groups via voting portfolio patterns (method 1).", "")
dyad_rows <- list()
for (per in PERIODS) {
  label <- per[1]; bd <- build_dist(df, as.integer(per[2]), as.integer(per[3]))
  hc <- hclust(bd$dist, method = "average")
  labs <- cutree(hc, k = N_GROUPS[[label]])
  groups <- split(bd$cc, labs)
  ord <- groups[order(-sapply(groups, length))]
  lines <- c(lines, sprintf("=== Time period: %s ===", label))
  gm <- data.frame()
  for (gi in seq_along(ord)) {
    members <- ord[[gi]]
    lines <- c(lines, sprintf("  G%d: %s", gi, paste(NAME[members], collapse = ", ")))
    gm <- rbind(gm, data.frame(period = label, group = paste0("G", gi),
                               country = NAME[members], code = members))
    for (a in members) for (b in members) if (a != b)
      dyad_rows[[length(dyad_rows) + 1]] <- data.frame(period = label, i = a, j = b, friend_m1 = 1)
  }
  lines <- c(lines, "")
  write.csv(gm, file.path(OUT, sprintf("friend_groups_R_%s.csv", label)), row.names = FALSE)
}
cat(paste(lines, collapse = "\n"), "\n")
writeLines(lines, file.path(OUT, "table2_R.txt"))
write.csv(do.call(rbind, dyad_rows), file.path(OUT, "friend_dyads_method1_R.csv"), row.names = FALSE)

# ---- Fig 1: dendrogram for 1998-2012. --------------------------------------
bd <- build_dist(df, 1998, 2012)
hc <- hclust(bd$dist, method = "average")
hc$labels <- NAME[bd$cc]
png(file.path(OUT, "fig1_dendrogram_R.png"), width = 900, height = 1100, res = 120)
par(mar = c(5, 4, 4, 8))
plot(as.dendrogram(hc), horiz = TRUE,
     xlab = "Voting-affinity dissimilarity measure",
     main = "Fig. 1 (R). Cluster tree of ESC voting patterns: 1998-2012")
dev.off()
cat("Fig 1 saved -> output/fig1_dendrogram_R.png\n")
