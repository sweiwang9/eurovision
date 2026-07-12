# build_dataset.R
# ===============
# R port of build_dataset.py: constructs the master dyad-year panel
# (Quality/Bias/Impartiality/controls) and writes output/master.csv.
# Mirrors the Python logic block-for-block so the two agree numerically.

get_here <- function() {
  a <- commandArgs(FALSE); m <- grep("^--file=", a)
  if (length(m)) return(dirname(normalizePath(sub("^--file=", "", a[m]))))
  if (!is.null(sys.frame(1)$ofile)) return(dirname(normalizePath(sys.frame(1)$ofile)))
  getwd()
}
here <- get_here()
source(file.path(here, "lib_countries.R"))
DATA <- dirname(here)                 # parent folder holds the raw CSVs
OUT  <- file.path(here, "output"); dir.create(OUT, showWarnings = FALSE)
YEAR_LO <- 1975; YEAR_HI <- 2012

# --- 1. Finalists per year: performed in the final (running/place present). --
con <- read.csv(file.path(DATA, "contestants.csv"), stringsAsFactors = FALSE)
con$year <- suppressWarnings(as.integer(con$year))
is_fin <- (!is.na(con$running_final) & con$running_final != "") |
          (!is.na(con$place_final)   & con$place_final   != "")
finalists <- split(con$to_country_id[is_fin], con$year[is_fin])

# --- 2. Final votes 1975-2012, finalist->finalist dyads only. ---------------
v <- read.csv(file.path(DATA, "votes.csv"), stringsAsFactors = FALSE)
v <- v[v$round == "final" & !is.na(v$year) &
       v$year >= YEAR_LO & v$year <= YEAR_HI &
       v$total_points != "" & !is.na(v$total_points), ]
v <- v[v$from_country_id %in% names(NAME) & v$to_country_id %in% names(NAME) &
       v$from_country_id != v$to_country_id, ]
keep <- mapply(function(y, i, j) {
  f <- finalists[[as.character(y)]]
  is.null(f) || (i %in% f && j %in% f)
}, v$year, v$from_country_id, v$to_country_id)
df <- data.frame(year = as.integer(v$year), i = v$from_country_id,
                 j = v$to_country_id, vote = as.numeric(v$total_points),
                 stringsAsFactors = FALSE)[keep, ]

# --- 3. Dyad-specific Quality (eq.1) and Bias (eq.2). -----------------------
#   quality_ijt = (Total_j - vote_ij)/(p-2);  bias = vote - quality.
part  <- tapply(c(df$i, df$j), rep(df$year, 2), function(x) length(unique(x)))
key   <- paste(df$year, df$j)
total <- tapply(df$vote, key, sum)
df$total_j <- as.numeric(total[key])
df$p       <- as.integer(part[as.character(df$year)])
df$quality <- (df$total_j - df$vote) / (df$p - 2)
df$bias    <- df$vote - df$quality
df$n_part  <- df$p

# --- 4. Impartiality (ICRG icrg_qog), ffill/bfill per country, 1975-2012. ----
# slim ICRG subset (ccodealp/year/icrg_qog) of the QoG Jan-2026 release; the full
# 71 MB file stays out of git (see qog_icrg_jan26.csv / README).
q <- read.csv(file.path(DATA, "qog_icrg_jan26.csv"), stringsAsFactors = FALSE)
q <- q[!is.na(q$icrg_qog), c("ccodealp", "year", "icrg_qog")]
imp_env <- new.env(); allvals <- c()
for (iso2 in names(ISO3)) {
  sub <- q[q$ccodealp == ISO3[[iso2]], ]
  if (nrow(sub) == 0) next
  yrs <- YEAR_LO:YEAR_HI
  s <- setNames(rep(NA_real_, length(yrs)), as.character(yrs))
  s[as.character(sub$year[sub$year %in% yrs])] <- sub$icrg_qog[sub$year %in% yrs]
  # forward then backward fill
  last <- NA; for (k in seq_along(s)) { if (!is.na(s[k])) last <- s[k] else s[k] <- last }
  nxt  <- NA; for (k in rev(seq_along(s))) { if (!is.na(s[k])) nxt <- s[k] else s[k] <- nxt }
  assign(iso2, s, envir = imp_env); allvals <- c(allvals, s[!is.na(s)])
}
# Hot-deck imputation (Charron fn.13), UNCONDITIONAL to match what he did: the
# donee takes the donor's ICRG series wholesale (incl. Moldova <- Azerbaijan, even
# though QoG now carries a real Moldova series Charron lacked), not mean-substituted.
for (donee in names(ICRG_DONOR)) {
  donor <- ICRG_DONOR[[donee]]
  if (exists(donor, envir = imp_env, inherits = FALSE)) {
    assign(donee, get(donor, envir = imp_env), envir = imp_env)
  }
}
grand <- mean(allvals)
look <- function(iso2, yr) {
  if (!exists(iso2, envir = imp_env, inherits = FALSE)) return(grand)
  val <- get(iso2, envir = imp_env)[as.character(yr)]
  if (is.na(val)) grand else as.numeric(val)
}
df$imp_i <- mapply(look, df$i, df$year)
df$imp_j <- mapply(look, df$j, df$year)

# --- 5. Receiver-j song traits: running order, host, heuristic EN/FR. --------
EN <- c(" the "," and "," you "," love "," my "," me "," to "," it "," is "," in ")
FR <- c(" les "," le "," la "," je "," tu "," et "," un "," une "," mon "," est "," que "," de ")
lang_flags <- function(lyr) {
  if (is.na(lyr) || lyr == "") return(c(NA, NA))
  t <- paste0(" ", tolower(gsub("\\\\n|\n", " ", lyr)), " ")
  en <- sum(sapply(EN, function(w) lengths(regmatches(t, gregexpr(w, t, fixed = TRUE)))))
  fr <- sum(sapply(FR, function(w) lengths(regmatches(t, gregexpr(w, t, fixed = TRUE)))))
  if (en == 0 && fr == 0) return(c(0, 0))
  c(as.integer(en >= fr && en > 0), as.integer(fr > en))
}
traits <- new.env(); winners <- list()
for (k in seq_len(nrow(con))) {
  y <- con$year[k]; j <- con$to_country_id[k]; if (is.na(y)) next
  fl <- lang_flags(con$lyrics[k])
  so <- suppressWarnings(as.numeric(con$running_final[k]))
  assign(paste(y, j), list(song_order = so, english = fl[1], french = fl[2]), envir = traits)
  if (!is.na(con$place_final[k]) && con$place_final[k] == "1") winners[[as.character(y)]] <- j
}
getT <- function(y, j, f) { k <- paste(y, j); if (exists(k, envir=traits, inherits=FALSE)) get(k, envir=traits)[[f]] else NA }
df$song_order <- mapply(function(y,j) getT(y,j,"song_order"), df$year, df$j)
df$english    <- mapply(function(y,j) getT(y,j,"english"),    df$year, df$j)
df$french     <- mapply(function(y,j) getT(y,j,"french"),     df$year, df$j)
host_key <- sapply(names(winners), function(y) paste(as.integer(y) + 1, winners[[y]]))
df$host <- as.integer(paste(df$year, df$j) %in% host_key)

# --- 6. Dyadic controls: contiguity, language, lagged votes. ----------------
df$contig   <- mapply(contiguous, df$i, df$j)
df$language <- mapply(same_language, df$i, df$j)
vk <- paste(df$year, df$i, df$j); vmap <- setNames(df$vote, vk)
df$lag_vote_ij <- as.numeric(vmap[paste(df$year - 1, df$i, df$j)])
df$lag_vote_ji <- as.numeric(vmap[paste(df$year - 1, df$j, df$i)])

# --- 7. Keep countries with >= 2 finals; write master.csv. ------------------
app <- tapply(df$year, df$j, function(x) length(unique(x)))
keepc <- names(app)[app >= 2]
df <- df[df$i %in% keepc & df$j %in% keepc, ]
df$voter <- NAME[df$i]; df$receiver <- NAME[df$j]
df <- df[, c("year","i","j","vote","total_j","p","quality","bias","n_part",
             "imp_i","imp_j","song_order","english","french","host",
             "contig","language","lag_vote_ij","lag_vote_ji","voter","receiver")]
write.csv(df, file.path(OUT, "master_R.csv"), row.names = FALSE)
cat(sprintf("master_R.csv written: %d dyad-year rows, %d-%d, %d countries.\n",
            nrow(df), min(df$year), max(df$year), length(unique(df$j))))
