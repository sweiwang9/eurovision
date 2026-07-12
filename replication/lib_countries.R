# lib_countries.R
# ===============
# R port of lib_countries.py: country names, ISO-2 -> ISO-3 codes, and the two
# reconstructed dyadic controls (land contiguity and shared official language).
# See the Python module for the full commentary on each block; the data are
# identical here so the R and Python pipelines produce the same variables.

# --- Readable names, keyed on lower-case ISO-2 (as in votes.csv). -----------
NAME <- c(
  al="Albania", am="Armenia", at="Austria", az="Azerbaijan",
  ba="Bosnia & Herzegovina", be="Belgium", bg="Bulgaria", by="Belarus",
  ch="Switzerland", cs="Serbia & Montenegro", cy="Cyprus", de="Germany",
  dk="Denmark", ee="Estonia", es="Spain", fi="Finland", fr="France",
  gb="United Kingdom", ge="Georgia", gr="Greece", hr="Croatia", hu="Hungary",
  ie="Ireland", il="Israel", is="Iceland", it="Italy", lt="Lithuania",
  lu="Luxembourg", lv="Latvia", ma="Morocco", mc="Monaco", md="Moldova",
  mk="Macedonia", mt="Malta", nl="Netherlands", no="Norway", pl="Poland",
  pt="Portugal", ro="Romania", rs="Serbia", ru="Russia", se="Sweden",
  si="Slovenia", sk="Slovakia", tr="Turkey", ua="Ukraine", yu="Yugoslavia")

# --- ISO-2 -> ISO-3 (for the QoG / ICRG join). ------------------------------
ISO3 <- c(
  al="ALB", am="ARM", at="AUT", az="AZE", ba="BIH", be="BEL", bg="BGR",
  by="BLR", ch="CHE", cs="SCG", cy="CYP", de="DEU", dk="DNK", ee="EST",
  es="ESP", fi="FIN", fr="FRA", gb="GBR", ge="GEO", gr="GRC", hr="HRV",
  hu="HUN", ie="IRL", il="ISR", is="ISL", it="ITA", lt="LTU", lu="LUX",
  lv="LVA", ma="MAR", mc="MCO", md="MDA", mk="MKD", mt="MLT", nl="NLD",
  no="NOR", pl="POL", pt="PRT", ro="ROU", rs="SRB", ru="RUS", se="SWE",
  si="SVN", sk="SVK", tr="TUR", ua="UKR", yu="YUG")

# --- ICRG hot-deck donors (Charron 2013, fn.13): the donee takes its donor's
#     icrg_qog series (UNCONDITIONAL, matching Charron) instead of being mean-
#     substituted.  ge/mk/md are his exact pairs -- Moldova is imputed from
#     Azerbaijan even though QoG now has a real Moldova series Charron lacked, to
#     reproduce his tables; ba/me/sm/mc extend the same logic. ------------------
# ba<-al: Albania is Bosnia's nearest ESC country by WGI (ICRG doesn't cover Bosnia
# or Monaco at all). ge/mk/md are Charron's exact fn.13 pairs; me/sm/mc same method.
ICRG_DONOR <- c(ge="hr", mk="al", md="az", ba="al", me="rs", sm="it", mc="fr")

# --- Contiguity (land borders within the ESC set); symmetrised below. -------
BORDERS <- list(
  al=c("gr","mk","rs","yu"), am=c("ge","az","tr"),
  at=c("de","ch","it","si","sk","hu","yu"), az=c("am","ge","ru","tr"),
  ba=c("hr","rs"), be=c("fr","nl","de","lu"),
  bg=c("gr","tr","ro","rs","mk","yu"), by=c("pl","lt","lv","ru","ua"),
  ch=c("de","fr","it","at"), cs=c("hr","ba","mk","al","ro","bg","hu"),
  de=c("fr","ch","at","be","nl","dk","pl","lu"), dk=c("de"),
  ee=c("lv","ru"), es=c("pt","fr"), fi=c("se","no","ru"),
  fr=c("es","be","de","ch","it","lu","mc"), gb=c("ie"),
  ge=c("ru","tr","am","az"), gr=c("al","mk","bg","tr","yu"),
  hr=c("si","hu","ba","rs","yu"), hu=c("at","sk","ua","ro","rs","hr","si","yu"),
  ie=c("gb"), it=c("fr","ch","at","si","yu"), lt=c("lv","by","pl","ru"),
  lu=c("be","fr","de"), lv=c("ee","lt","ru","by"), mc=c("fr"),
  md=c("ro","ua"), mk=c("al","gr","bg","rs","yu"), nl=c("be","de"),
  no=c("se","fi","ru"), pl=c("de","sk","ua","by","lt","ru"), pt=c("es"),
  ro=c("hu","rs","bg","ua","md","yu"), rs=c("hu","ro","bg","mk","al","ba","hr"),
  ru=c("no","fi","ee","lv","lt","by","ua","ge","az"), se=c("no","fi"),
  si=c("at","it","hu","hr","yu"), sk=c("pl","ua","hu","at"),
  tr=c("gr","bg","ge","am","az"), ua=c("ru","by","pl","sk","hu","ro","md"),
  yu=c("it","at","hu","ro","bg","mk","al","gr","hr","si"))

CONTIG_PAIRS <- new.env()
for (a in names(BORDERS)) for (b in BORDERS[[a]])
  if (a != b) assign(paste(sort(c(a, b)), collapse = "_"), TRUE, envir = CONTIG_PAIRS)

# --- Shared official/native language groups; any co-membership => 1. --------
LANG_GROUPS <- list(
  german=c("de","at","ch","lu","be"), french=c("fr","be","ch","lu","mc"),
  dutch=c("nl","be"), italian=c("it","ch"), greek=c("gr","cy"),
  turkish=c("tr","cy"), english=c("gb","ie","mt"), swedish=c("se","fi"),
  scandinavian=c("se","no","dk"), romanian=c("ro","md"),
  russian=c("ru","by","ua"), bcms=c("rs","hr","ba","cs","yu"))

LANG_PAIRS <- new.env()
for (g in LANG_GROUPS) for (i in seq_along(g)) for (j in seq_along(g))
  if (i < j) assign(paste(sort(c(g[i], g[j])), collapse = "_"), TRUE, envir = LANG_PAIRS)

contiguous  <- function(a, b) as.integer(exists(paste(sort(c(a,b)),collapse="_"), envir=CONTIG_PAIRS, inherits=FALSE))
same_language <- function(a, b) as.integer(exists(paste(sort(c(a,b)),collapse="_"), envir=LANG_PAIRS, inherits=FALSE))
