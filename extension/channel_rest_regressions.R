# channel_rest_regressions.R
# ===========================
# (A) Jury-channel and public-channel Friend x Impartiality tests, and
# (B) the Rest-of-World (XX) benchmark.  Estimates the frames exported by
# channel_rest_analysis.py.  Authoritative estimator = R AER::tobit / lm.
#
#     python3 channel_rest_analysis.py   # builds the CSVs
#     Rscript channel_rest_regressions.R

suppressMessages({ library(AER); library(sandwich); library(lmtest) })

get_here <- function() {
  a <- commandArgs(FALSE); m <- grep("^--file=", a)
  if (length(m)) return(dirname(normalizePath(sub("^--file=", "", a[m]))))
  getwd()
}
out <- file.path(get_here(), "output")
star <- function(p) ifelse(p<.01,"***",ifelse(p<.05,"**",ifelse(p<.10,"*","")))
cell <- function(b,se,p) sprintf("%.3f%s (%.3f)", b, star(p), se)

ols  <- function(d,rhs){ keep<-rhs[sapply(rhs,function(v) length(unique(d[[v]][!is.na(d[[v]])]))>1)]
  m<-lm(as.formula(paste("vote ~",paste(keep,collapse="+"))),data=d)
  ct<-coeftest(m,vcov=vcovHC(m,type="HC1")); list(c=ct[,1],se=ct[,2],p=ct[,4],n=nobs(m)) }
tob  <- function(d,rhs){ keep<-rhs[sapply(rhs,function(v) length(unique(d[[v]][!is.na(d[[v]])]))>1)]
  m<-tobit(as.formula(paste("vote ~",paste(keep,collapse="+"))),left=-Inf,right=12,data=d)
  s<-summary(m)$coefficients; list(c=s[,1],se=s[,2],p=s[,4],n=sum(complete.cases(d[,c("vote",keep)]))) }

BASE <- c("quality","friend_m1","imp_i","fm1_x_imp","song_order","host",
          "contig","language","n_part","duet","group","female")
keyrows <- c("quality","friend_m1","imp_i","fm1_x_imp")

run_channel <- function(file, label, early, late){
  d <- read.csv(file.path(out,file), stringsAsFactors=FALSE)
  specs <- list(
    list(paste(label,"OLS all"),   ols, d,                                   BASE),
    list(paste(label,"OLS",early[3]), ols, subset(d, year>=early[1] & year<=early[2]), BASE),
    list(paste(label,"OLS",late[3]),  ols, subset(d, year>=late[1]  & year<=late[2]),  BASE),
    list(paste(label,"Tobit all"), tob, d,                                   BASE))
  res <- lapply(specs, function(s) s[[2]](s[[3]], s[[4]]))
  labs<- sapply(specs, `[[`, 1)
  hdr <- paste0(formatC("",width=12), paste(sapply(labs,formatC,width=22,flag="-"),collapse=""))
  lines <- c(paste0("== ",label," channel =="), hdr)
  for (rn in keyrows){ line<-formatC(rn,width=12,flag="-")
    for(r in res) line<-paste0(line,formatC(if(rn %in% names(r$c)) cell(r$c[rn],r$se[rn],r$p[rn]) else "",width=22,flag="-"))
    lines<-c(lines,line) }
  nl<-formatC("N",width=12,flag="-"); for(r in res) nl<-paste0(nl,formatC(as.character(r$n),width=22,flag="-"))
  c(lines, nl, "")
}

# (A) channels ---------------------------------------------------------------
txtA <- c("Table: Friend x Impartiality by VOTING CHANNEL (R: OLS + AER::tobit).",
          "  Jury channel   = 1975-1997 (juries) + 2016-2026 (jury half).",
          "  Public channel = 1998-2008 (televote) + 2016-2026 (televote half).","",
  run_channel("regression_data_jurychannel.csv","JURY",  c(1975,1997,"75-97"), c(2016,2026,"16-26")),
  run_channel("regression_data_pubchannel.csv", "PUBLIC",c(1998,2008,"98-08"), c(2016,2026,"16-26")),
  "Signif: *** p<.01, ** p<.05, * p<.10.  DV = 0-12 vote of that channel.")
writeLines(txtA, file.path(out,"channel_analysis_R.txt")); cat(txtA, sep="\n"); cat("\n\n")

# (B) Rest-of-World benchmark ------------------------------------------------
r <- read.csv(file.path(out,"regression_data_rowvote.csv"), stringsAsFactors=FALSE)
xx  <- subset(r, is_xx==1); nat <- subset(r, is_xx==0)
L <- c("== REST-OF-WORLD (XX) benchmark, 2023-2026 public vote ==","")

# 1. Does XX reward quality?  (national public consensus quality)
m1 <- lm(pub ~ quality, data=xx)
L <- c(L, sprintf("1) XX rewards quality:  pub = %.2f + %.2f*quality   R2=%.2f  (n=%d)",
        coef(m1)[1], coef(m1)[2], summary(m1)$r.squared, nrow(xx)))
mn <- lm(pub ~ quality, data=nat)
L <- c(L, sprintf("   national comparison:  slope %.2f, R2 %.2f", coef(mn)[2], summary(mn)$r.squared))

# 2. Does XX favor friend-bloc receivers beyond quality? (bias ~ recv_bloc)
bx <- coeftest(lm(bias ~ recv_bloc, data=xx), vcov=vcovHC)
bn <- coeftest(lm(bias ~ recv_bloc, data=nat), vcov=vcovHC)
L <- c(L, "",
  sprintf("2) Extra points to friend-bloc receivers (bias ~ recv_bloc):"),
  sprintf("     XX       : %s", cell(bx["recv_bloc",1],bx["recv_bloc",2],bx["recv_bloc",4])),
  sprintf("     national : %s", cell(bn["recv_bloc",1],bn["recv_bloc",2],bn["recv_bloc",4])))

# 3. National diaspora bias (which XX structurally cannot have)
dn <- coeftest(lm(bias ~ diaspora, data=nat), vcov=vcovHC)
L <- c(L, "",
  sprintf("3) National diaspora bias (bias ~ diaspora, national voters): %s",
          cell(dn["diaspora",1],dn["diaspora",2],dn["diaspora",4])),
  sprintf("   XX has no diaspora ties -> diaspora=0 by construction."),
  "",
  sprintf("Mean bias: XX = %+.2f (sd %.2f)   national = %+.2f (sd %.2f)",
          mean(xx$bias), sd(xx$bias), mean(nat$bias), sd(nat$bias)))
writeLines(L, file.path(out,"rest_of_world_R.txt")); cat(L, sep="\n"); cat("\n")
