"""
tobit.py
========
A minimal, dependency-light Type-I Tobit estimator (maximum likelihood),
right-censored, used to reproduce the pooled-Tobit columns of the paper.

Why we need this
----------------
Charron (2013) estimates the vote (0-12, censored at the top because a country
can never award 9 or 11 points and the scale stops at 12) with a Tobit model
(Table 3, models 7-10; all of Table 4).  statsmodels ships OLS but not Tobit,
so we implement the log-likelihood directly and optimise it with scipy.

Model
-----
Latent:   y* = X beta + e ,   e ~ N(0, sigma^2)
Observed: y  = min(y*, U)          (right-censored at the upper limit U)

Log-likelihood contributions (tau = log sigma, so the optimiser is unconstrained):
  * uncensored obs (y < U):   -tau - 0.5*log(2*pi) - 0.5*z^2 ,  z = (y - Xb)/sigma
  * censored   obs (y = U):    log Phi(m) ,                     m = (Xb - U)/sigma

Robustness
----------
Standard errors are Huber/White-style robust (sandwich), matching the paper's
"Huber White robust standard errors".  Two things make this numerically stable
even on the large, mixed-scale pooled sample (n_part ~18-43 alongside 0/1 dummies):
  1. the design matrix is STANDARDISED (each non-constant column divided by its
     SD) before optimisation, then coefficients/covariance are transformed back;
  2. the sandwich "bread" is a genuine numerical Hessian of the log-likelihood at
     the optimum, NOT BFGS's approximate `hess_inv` (whose path-dependence made
     the old version intermittently return nonsense SEs).
Analytic per-observation scores are used for both the optimiser gradient and the
sandwich "meat", so nothing relies on noisy finite differences.
"""

import numpy as np
from scipy import optimize, stats


class TobitResult:
    """Small container mirroring the bits of a statsmodels result we use."""

    def __init__(self, params, bse, llf, sigma, sigma_se, names, nobs):
        self.params = params        # coefficient vector (incl. constant)
        self.bse = bse              # robust standard errors
        self.llf = llf              # log-likelihood at optimum
        self.sigma = sigma          # estimated error SD
        self.sigma_se = sigma_se    # SE of sigma
        self.names = names          # regressor names (same order as params)
        self.nobs = nobs

    def summary_frame(self):
        """Return coef/se/z/p as parallel lists for pretty-printing."""
        z = self.params / self.bse
        p = 2 * (1 - stats.norm.cdf(np.abs(z)))
        return list(zip(self.names, self.params, self.bse, z, p))


def _obs_loglik(theta, X, y, upper):
    """Vector of per-observation log-likelihoods (LL, positive sign)."""
    beta = theta[:-1]
    sigma = np.exp(theta[-1])
    xb = X @ beta
    cens = y >= upper - 1e-9
    z = (y - xb) / sigma
    ll_unc = -(theta[-1] + 0.5 * np.log(2 * np.pi) + 0.5 * z ** 2)
    m = (xb - upper) / sigma
    ll_cen = stats.norm.logcdf(m)
    return np.where(cens, ll_cen, ll_unc)


def _obs_score(theta, X, y, upper):
    """Analytic per-observation score d(LL_i)/d(theta), shape (n, k+1).
    Columns 0..k-1 are d/d beta; the last column is d/d tau (tau = log sigma)."""
    beta = theta[:-1]
    tau = theta[-1]
    sigma = np.exp(tau)
    n, k = X.shape
    xb = X @ beta
    cens = y >= upper - 1e-9
    S = np.zeros((n, k + 1))

    # Uncensored rows: z = (y - xb)/sigma
    z = (y - xb) / sigma
    unc = ~cens
    # d/d beta = (z/sigma) * x_i ;  d/d tau = z^2 - 1
    S[unc, :k] = (z[unc] / sigma)[:, None] * X[unc]
    S[unc, k] = z[unc] ** 2 - 1.0

    # Censored rows: m = (xb - U)/sigma, Mills ratio lam = phi(m)/Phi(m)
    m = (xb - upper) / sigma
    # stable lambda via logs (handles deep left tail where Phi(m) -> 0)
    lam = np.exp(stats.norm.logpdf(m) - stats.norm.logcdf(m))
    # d/d beta = lam * (1/sigma) * x_i ;  d/d tau = -lam * m
    S[cens, :k] = (lam[cens] / sigma)[:, None] * X[cens]
    S[cens, k] = -lam[cens] * m[cens]
    return S


def _neg_loglik(theta, X, y, upper):
    return -np.sum(_obs_loglik(theta, X, y, upper))


def _neg_grad(theta, X, y, upper):
    return -_obs_score(theta, X, y, upper).sum(axis=0)


def _num_hessian(theta, X, y, upper, eps=1e-5):
    """Numerical Hessian of the NEGATIVE log-likelihood at theta, via central
    differences of the analytic gradient (accurate and cheap: O(k) grad evals)."""
    p = len(theta)
    H = np.zeros((p, p))
    for j in range(p):
        step = np.zeros(p); step[j] = eps
        gp = _neg_grad(theta + step, X, y, upper)
        gm = _neg_grad(theta - step, X, y, upper)
        H[:, j] = (gp - gm) / (2 * eps)
    return 0.5 * (H + H.T)          # symmetrise


def tobit(y, X, names, upper=12.0):
    """Fit a right-censored Tobit and return a TobitResult with robust SEs.

    Parameters
    ----------
    y     : (n,) outcome (already censored at `upper`).
    X     : (n, k) design matrix INCLUDING a constant column.
    names : list of k regressor names matching X's columns.
    upper : censoring ceiling (12 for ESC points).
    """
    y = np.asarray(y, float)
    X = np.asarray(X, float)
    n, k = X.shape

    # --- Standardise columns (divide by SD) for conditioning; constant/zero-
    #     variance columns keep scale 1 so they are untouched. -----------------
    scale = X.std(axis=0)
    scale[scale < 1e-12] = 1.0
    Xs = X / scale

    # --- Start from OLS on the scaled design; sigma from residual SD. ---------
    beta0, *_ = np.linalg.lstsq(Xs, y, rcond=None)
    resid = y - Xs @ beta0
    theta0 = np.append(beta0, np.log(resid.std() + 1e-6))

    # --- Optimise the negative log-likelihood with the analytic gradient. -----
    res = optimize.minimize(_neg_loglik, theta0, args=(Xs, y, upper),
                            jac=_neg_grad, method="BFGS",
                            options={"maxiter": 5000, "gtol": 1e-6})
    theta = res.x
    beta_s = theta[:-1]
    sigma = np.exp(theta[-1])

    # --- Robust (sandwich) covariance in SCALED coords:  H^-1 (G'G) H^-1. -----
    #     H = observed information (numerical Hessian of the negative LL);
    #     G = analytic per-observation scores of the LL.
    H = _num_hessian(theta, Xs, y, upper)
    G = _obs_score(theta, Xs, y, upper)
    H_inv = np.linalg.pinv(H)                       # pinv: robust if near-singular
    cov_s = H_inv @ (G.T @ G) @ H_inv

    # --- Transform back to original scale:  beta = beta_s / scale, and the
    #     covariance rescales by the outer product of 1/scale (tau unscaled). --
    inv_scale = np.append(1.0 / scale, 1.0)         # last entry = tau (log sigma)
    cov = cov_s * np.outer(inv_scale, inv_scale)
    se_all = np.sqrt(np.clip(np.diag(cov), 0, None))

    beta = beta_s / scale
    return TobitResult(
        params=beta, bse=se_all[:-1], llf=-res.fun,
        sigma=sigma, sigma_se=se_all[-1] * sigma,   # delta method for exp()
        names=names, nobs=n,
    )
