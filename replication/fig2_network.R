# fig2_network.R
# ==============
# R port of fig2_network.py: Fig 2 network of significant pairwise bias, drawn
# with igraph.  Also writes friend_dyads_method2_R.csv (significant positive
# directed bias) for the regressions.

get_here <- function() {
  a <- commandArgs(FALSE); m <- grep("^--file=", a)
  if (length(m)) return(dirname(normalizePath(sub("^--file=", "", a[m]))))
  getwd()
}
here <- get_here(); source(file.path(here, "lib_countries.R"))
suppressMessages(library(igraph))
OUT <- file.path(here, "output")
df <- read.csv(file.path(OUT, "master_R.csv"), stringsAsFactors = FALSE)
MIN_OBS <- 3

# Per ordered dyad in [lo,hi]: mean bias, n, t-test p, significant-positive flag.
directed_bias <- function(d, lo, hi) {
  s <- d[d$year >= lo & d$year <= hi, ]
  key <- paste(s$i, s$j)
  res <- lapply(split(s$bias, key), function(b) {
    if (length(b) < MIN_OBS) return(NULL)
    p <- if (length(unique(b)) == 1) ifelse(abs(mean(b)) > 1e-9, 0, 1) else t.test(b, mu = 0)$p.value
    c(mean(b), length(b), p, as.integer(mean(b) > 0 && p < 0.05))
  })
  res <- res[!sapply(res, is.null)]
  ij <- do.call(rbind, strsplit(names(res), " "))
  data.frame(i = ij[, 1], j = ij[, 2],
             bias = sapply(res, `[`, 1), n = sapply(res, `[`, 2),
             pval = sapply(res, `[`, 3), sig_pos = sapply(res, `[`, 4),
             stringsAsFactors = FALSE)
}

# Persist method-2 friend dyads (both periods) for the regressions.
m2 <- do.call(rbind, lapply(list(c("1975-1997",1975,1997), c("1998-2012",1998,2012)),
  function(p) { d <- directed_bias(df, as.integer(p[2]), as.integer(p[3]))
                data.frame(period = p[1], i = d$i, j = d$j, friend_m2 = d$sig_pos) }))
write.csv(m2, file.path(OUT, "friend_dyads_method2_R.csv"), row.names = FALSE)

# Undirected edges for the graph: pair kept if >=1 direction is sig-positive.
d <- directed_bias(df, 1998, 2012)
d <- d[d$sig_pos == 1, ]
pk <- apply(d[, c("i", "j")], 1, function(x) paste(sort(x), collapse = "_"))
edge_bias <- tapply(d$bias, pk, mean)
ends <- do.call(rbind, strsplit(names(edge_bias), "_"))
edges <- data.frame(a = ends[, 1], b = ends[, 2], bias = as.numeric(edge_bias))

width_of <- function(x) ifelse(x < 2.5, 1, ifelse(x < 4.5, 2.5, ifelse(x < 6.5, 4, 6)))
g <- graph_from_data_frame(edges[, c("a", "b")], directed = FALSE)
E(g)$width <- width_of(edges$bias)
grp <- read.csv(file.path(OUT, "friend_groups_R_1998-2012.csv"), stringsAsFactors = FALSE)
code2grp <- setNames(grp$group, grp$code)
pal <- rainbow(length(unique(grp$group)))
V(g)$color <- pal[as.integer(factor(code2grp[V(g)$name]))]
V(g)$label <- NAME[V(g)$name]

png(file.path(OUT, "fig2_network_R.png"), width = 1200, height = 1000, res = 120)
set.seed(42)
plot(g, layout = layout_with_fr(g), vertex.size = 14, vertex.label.cex = 0.7,
     vertex.label.color = "black", edge.color = "gray40",
     main = "Fig. 2 (R). Friend network (method 2): 1998-2012")
legend("bottomleft", legend = c("<2.5", "2.5-4.5", "4.5-6.5", ">6.5"),
       lwd = c(1, 2.5, 4, 6), col = "gray40", title = "Pairwise bias level")
dev.off()
cat(sprintf("Fig 2 saved -> output/fig2_network_R.png (%d edges, %d nodes)\n",
            ecount(g), vcount(g)))
