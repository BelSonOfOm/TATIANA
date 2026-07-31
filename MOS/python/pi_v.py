"""
TATIANA — pi_v **v2**: Construction 2's own escape hatch, taken.

=============================================================================
WHY THIS FILE EXISTS
=============================================================================
Construction 2 (logbook §3) fixes the two-level glue:

    "coarse-graining map pi_v : (C_v, F_v) -> F(v) = R^384.
     v1 = weighted centroid of active concept embeddings (weights = simplex
     weights w(sigma,t)); v2 = top principal component if needed."

Only v1 was ever built (`module_vertex.stalk`, `belief.stalk_gaussian`).
V6 (§5ah, `measure_sigma_dir.py`) is the "if needed": on the real corpus

    sigma_dir / delta  =  0.32 median, 0.42 max     (simulated: 0.09)

which drops agreement with true optimal transport from ~87% to ~62% — the
merge predicate is barely better than a coin. §5ah's own diagnosis blames the
SEPARATION, not sigma_dir. This file tests the other half of that diagnosis:

    if an organ's fine complex is MULTI-MODAL, then collapsing it to one
    weighted centroid makes sigma_dir measure MODEL MISSPECIFICATION -- the
    Gaussian is the wrong SHAPE -- rather than genuine uncertainty.

For a two-cluster organ with modes at m1, m2, the centroid sits between them
and the scatter carries the BETWEEN-mode term ~ ||m1 - m2||^2 along (m1 - m2).
Whenever that direction has a component along the separation u to another
organ, sigma_dir^2 = u^T Sigma u absorbs it. That number is not "how unsure am
I where I am"; it is "I am two places at once". A single Gaussian cannot say
so, and the metric pays for it.

=============================================================================
A DEFECT IN CONSTRUCTION 2'S OWN WORDING, AND HOW IT IS RESOLVED
=============================================================================
"v2 = top principal component" **cannot be read literally**. v1 returns a
POSITION in R^384. A principal component is
  * a DIRECTION, not a location: it is translation-invariant, so it carries
    exactly zero information about where the organ is;
  * defined only up to sign, so even as a direction it is not a well-defined
    element of R^384.
Substituting it for the centroid would make every cross-organ distance
meaningless. Stated plainly rather than quietly reinterpreted.

What the top principal component CAN do is two things, and both are what v2
actually needs:

  (i) DIAGNOSE. The leading spectrum of the concept scatter, plus a test on
      the PC1 projection, says whether one Gaussian is an adequate model.
      That is the number that reads "v1 is not enough for this organ".

 (ii) NAME THE SPLIT. PC1 is the direction along which a multi-modal fine
      complex separates, so it supplies the partition that makes a coarse
      position a coarse-graining of ONE mode instead of an average over
      several.

Hence the definition actually implemented:

    **pi_v2  =  pi_v1  restricted to the DOMINANT MODE of the fine complex.**

v2 is not a new estimator. It is v1 applied to a sub-complex. Every
convention v1 carries (Kish n_eff, the shrinkage prior, the O(1/d) floor of
belief.py) is inherited unchanged, because v2 *calls* v1. Two consequences,
and the second is the one the discipline demands:

  * Exact degradation is STRUCTURAL, not tested into existence: when the fine
    complex has one mode, the restriction is the identity map and v2 returns
    the bit-identical object v1 returns. Tested anyway (test 4).
  * v2 gets NO free lunch. Discarding concepts lowers n_eff, which RAISES the
    shrinkage floor (belief.py: floor = eps + kappa/(d(n_eff+kappa))), so
    sigma_dir^2 gains back a little of what the between-mode term lost.
    A method that only ever removes variance would be cheating; this one is
    charged for its own smaller sample.

=============================================================================
WHAT THE STRUCTURALLY CORRECT ANSWER IS (v2 is a stopgap, and says so)
=============================================================================
A genuinely bimodal organ is not one vertex whose position is hard to
estimate. It is TWO VERTICES. `module_vertex.CoarseComplex` already names
`split` as one of its four typed structural operations (bind / collapse /
split / merge) and has never had a criterion for firing it. The diagnostic
here IS that criterion:

    an organ whose fine complex is decisively multi-modal should be SPLIT,
    and until it is, `pi_v2` reports its dominant mode and its discarded mass.

`pi_v_modes()` returns the split-ready decomposition. So this file does not
merely add an estimator: it converts an unspecified structural operation into
a derived one, which is the bar this project sets for new formalism.

=============================================================================
THE DIAGNOSTIC, AND WHY THE EIGENVALUE GAP ALONE IS NOT ENOUGH
=============================================================================
The obvious statistic is the leading eigenvalue gap of the concept scatter.
It is reported (`explained_1`, `eigengap`) and it is genuinely informative,
but **on its own it cannot answer the question**: a unimodal cigar-shaped
cloud — one topic, discussed at varying length — has lambda_1 >> lambda_2 and
is perfectly well described by one Gaussian. Elongation is not multi-modality.
Test 3 below is exactly that counter-example, and a pure-eigengap rule fails it.

So the verdict is a MODEL COMPARISON, the same instrument belief.py already
uses for flow-vs-adapt:

  1. Project the concepts on PC1 of the weighted scatter:  t_i = <c_i - mu, p1>.
  2. Fit one Gaussian (2 params) and a two-component Gaussian mixture
     (5 params: p, m1, s1, m2, s2) to the weighted 1-D sample.
  3. Compare by BIC.  delta_BIC = BIC(1) - BIC(2) > 0 favours two modes.
  4. Additionally require **Ashman's D = sqrt(2)|m1-m2|/sqrt(s1^2+s2^2) >= 2**.

Step 4 is not a second threshold for its own sake. A two-component mixture
routinely wins on likelihood by modelling KURTOSIS — two concentric
components, one narrow one broad, describing a heavy-tailed unimodal cloud.
That fit has a large delta_BIC and near-zero mode separation, and splitting on
it would be pure noise-chasing. D >= 2 is the standard condition for two
Gaussians to be resolvable at all (below it the mixture density is unimodal),
so it is a statement about the OBJECT, not a tuning knob.

ASSUMPTIONS, ALL STATED
-----------------------
(A1) **Multi-modality is tested along PC1 only.** Justification: for two
     clusters whose separation exceeds their within-cluster spread, PC1
     aligns with the separation. FAILURE MODE, named: an organ that splits
     along a LOW-variance direction is missed. This is a one-dimensional
     projection test, not a d-dimensional clustering, and it is chosen
     because it is what Construction 2 names and because a 384-dimensional
     mixture cannot be fitted from ~60 paragraphs at all.
(A2) **Two components, not k.** `pi_v_modes` recovers more by recursive
     binary splitting; the primitive test is binary. Selecting k by BIC over a
     range would be defensible and is not done, because n_eff here is tens.
(A3) **Weights are fractional counts.** They are rescaled to sum to Kish's
     n_eff so that the weighted log-likelihood lives on the scale of n_eff
     observations and BIC's log(n) term is coherent. With uniform weights this
     is the identity.
(A4) **Component variances are floored at `eps`**, the same floor the stalk
     covariance carries (Sigma = U U^T + eps I means u^T Sigma u >= eps along
     every direction). Not a regularisation invented here: the model cannot
     claim resolution finer than it has anywhere else. It also removes the
     standard degenerate-EM singularity (a component collapsing on one point).
(A5) EM is run from TWO closed-form starts and the higher-likelihood fit is
     kept: the exact optimal 1-D two-means split ("two things"), and a
     concentric narrow/broad pair on the common mean ("heavy tail"). Both are
     deterministic functions of the data -- no random restarts, no seed, so
     the diagnostic is bit-reproducible and order-invariant (test 10). The
     second start is not decoration: with only the first, a concentric
     core+halo cloud is fitted as a left/right split and FALSELY declared
     multi-modal. That was measured, at n/d = 25 as well as n/d = 0.2, before
     the second start was added. See `_fit_two_components`.
(A6) **PC1 is a sample estimate and the test inherits its noise.** With n < d
     (the deployed regime: ~60 paragraphs at d = 384) the leading direction is
     itself uncertain, so a marginal verdict near the BIC bar should not be
     treated as sharp. Not corrected for here; a resampling-stability check on
     the split is the obvious next step and is NOT implemented. Named, not
     hidden.

REFUSALS (the house rule: refuse rather than default)
-----------------------------------------------------
  * an idle organ (no concepts, or total weight 0) has NO position:
    `pi_v1`/`pi_v2` return None, exactly as `module_vertex.stalk` and
    `belief.stalk_gaussian` do.
  * n_eff <= 5 makes the two-component model non-identifiable (5 parameters,
    fewer observations). `multimodality()` returns `decidable=False` with a
    reason, and `multimodal` is False -- it does not guess, and it does not
    silently declare unimodality either. Callers can tell "one mode" from
    "cannot tell".
  * a two-component fit in which either component holds < 2 effective
    observations is DEGENERATE and reported as such, not as a split.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

import numpy as np

from belief import EPS_FLOOR, Gaussian, stalk_gaussian

# ---------------------------------------------------------------------------
# The two named constants of the verdict, each with a reason rather than a fit.
# ---------------------------------------------------------------------------

# delta_BIC evidence scale. 10 is "decisive" on the usual reading, and it is the
# SAME bar belief.compare_models already prints (">10 is decisive"). Using one
# evidence scale across the project is the point; this is not tuned here.
BIC_DECISIVE = 10.0

# Ashman's D. Two Gaussians of equal weight produce a bimodal DENSITY only once
# their separation exceeds ~2 pooled sigmas; below that the mixture is unimodal
# and "two components" is a description of tail shape, not of two things.
ASHMAN_MIN = 2.0

# A 2-component 1-D mixture has 5 free parameters. Fewer effective observations
# than parameters is not a weak fit, it is an unidentifiable one.
MIN_N_EFF_FOR_SPLIT = 5.0

# A component must hold enough mass for its variance to mean anything.
MIN_COMPONENT_MASS = 2.0


# ===========================================================================
# 0. The weighted concept scatter and its spectrum
# ===========================================================================

def _as_matrix(vectors: Sequence[np.ndarray],
               weights: Optional[Sequence[float]]) -> Tuple[np.ndarray, np.ndarray]:
    """(n, d) concept matrix and its (n,) weights, validated. Raises, never pads."""
    M = np.stack([np.asarray(v, dtype=float).ravel() for v in vectors])
    n = M.shape[0]
    w = np.ones(n) if weights is None else np.asarray(weights, dtype=float).ravel()
    if w.size != n:
        raise ValueError(f"{w.size} weights for {n} vectors")
    if np.any(w < 0):
        raise ValueError("negative concept weight")
    return M, w


def kish_n_eff(w: np.ndarray) -> float:
    """(sum w)^2 / sum w^2 -- the same effective count belief.stalk_gaussian uses."""
    s2 = float((w ** 2).sum())
    if s2 <= 0:
        return 0.0
    return float(float(w.sum()) ** 2 / s2)


def scatter_spectrum(vectors: Sequence[np.ndarray],
                     weights: Optional[Sequence[float]] = None
                     ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Eigenvalues, PC1 and the weighted mean of the fine complex's scatter.

        S = sum_i w_i (c_i - mu)(c_i - mu)^T / sum_i w_i

    Returned as (eigenvalues descending, p1, mu). Computed by SVD of the
    weighted centred matrix, so only min(n, d) values exist and no d x d matrix
    is ever formed (d = 384, n ~ tens).

    **This is the raw CONCEPT scatter, not the stalk covariance.** The stalk
    divides by (n_eff + kappa) and adds a floor; the question "is this organ
    several things?" is about the concepts themselves, so the shrinkage is
    deliberately not applied here. Any monotone rescaling leaves the verdict
    below unchanged anyway (BIC and Ashman's D are both scale-equivariant).
    """
    M, w = _as_matrix(vectors, weights)
    tot = float(w.sum())
    if tot <= 0:
        raise ValueError("total concept weight is zero; the organ has no position")
    mu = (w[:, None] * M).sum(axis=0) / tot
    A = (M - mu) * np.sqrt(w / tot)[:, None]          # (n, d), A^T A = S
    s = np.linalg.svd(A, compute_uv=False)
    eig = s ** 2
    # PC1 as the leading right-singular vector (sign is arbitrary; irrelevant --
    # every statistic below is invariant under p1 -> -p1).
    _, _, Vt = np.linalg.svd(A, full_matrices=False)
    p1 = Vt[0] if Vt.shape[0] else np.zeros(M.shape[1])
    return eig, p1, mu


# ===========================================================================
# 1. THE MULTI-MODALITY DIAGNOSTIC
# ===========================================================================

@dataclass
class MultimodalityReport:
    """Is one Gaussian an adequate model of this organ's fine complex?"""
    n: int
    n_eff: float
    decidable: bool
    reason: str
    # -- the leading spectrum, so structure is VISIBLE, not silently averaged --
    eig: np.ndarray = field(default_factory=lambda: np.zeros(0))
    explained_1: float = 0.0        # lambda_1 / sum lambda   (in [0, 1])
    eigengap: float = 0.0           # lambda_1 / lambda_2     (>= 1; inf if k = 1)
    # -- the verdict --
    loglik_1: float = 0.0
    loglik_2: float = 0.0
    delta_bic: float = 0.0          # BIC(1 comp) - BIC(2 comp); > 0 favours two
    ashman_d: float = 0.0
    mode_masses: Tuple[float, ...] = ()
    multimodal: bool = False
    labels: Optional[np.ndarray] = None   # hard assignment, None unless multimodal

    @property
    def dominant_fraction(self) -> float:
        return max(self.mode_masses) if self.mode_masses else 1.0

    def line(self) -> str:
        if not self.decidable:
            return (f"n={self.n:>3} n_eff={self.n_eff:>5.1f}  UNDECIDABLE ({self.reason})")
        verdict = "MULTI-MODAL" if self.multimodal else "one mode"
        return (f"n={self.n:>3} n_eff={self.n_eff:>5.1f}  "
                f"lam1/sum={self.explained_1:5.3f} lam1/lam2={self.eigengap:6.2f}  "
                f"dBIC={self.delta_bic:+9.2f}  Ashman={self.ashman_d:5.2f}  "
                f"mass={self.dominant_fraction:5.3f}  {verdict}")

    def __repr__(self) -> str:
        return f"MultimodalityReport({self.line()})"


def _gauss_logpdf(t: np.ndarray, m: float, var: float) -> np.ndarray:
    return -0.5 * (np.log(2.0 * np.pi * var) + (t - m) ** 2 / var)


def _best_two_means_split(t: np.ndarray, w: np.ndarray) -> Optional[Tuple[float, float, float]]:
    """EXACT optimal weighted 1-D two-means split, by scanning sorted cut points.

    Returns (m1, m2, mass1_fraction) or None if no admissible cut exists.
    O(n log n) with prefix sums; no iteration, no initialisation, no seed --
    which is why the whole diagnostic is deterministic (A5).
    """
    order = np.argsort(t, kind="stable")
    ts, ws = t[order], w[order]
    n = ts.size
    cw = np.cumsum(ws)
    cwt = np.cumsum(ws * ts)
    cwt2 = np.cumsum(ws * ts * ts)
    W, S, S2 = cw[-1], cwt[-1], cwt2[-1]
    best = None
    for j in range(1, n):                       # left = indices 0..j-1
        wl = cw[j - 1]
        wr = W - wl
        if wl <= 0 or wr <= 0:
            continue
        ml = cwt[j - 1] / wl
        mr = (S - cwt[j - 1]) / wr
        sse = (cwt2[j - 1] - wl * ml * ml) + ((S2 - cwt2[j - 1]) - wr * mr * mr)
        if best is None or sse < best[0]:
            best = (sse, ml, mr, wl / W)
    if best is None:
        return None
    return best[1], best[2], best[3]


def _em_two(t: np.ndarray, w: np.ndarray, start, var_floor: float,
            max_iter: int = 500, tol: float = 1e-11):
    """One EM run of a weighted 2-component 1-D Gaussian mixture from `start`.

    Returns (loglik, p, m1, v1, m2, v2, responsibilities) or None if a component
    dies. Variances are floored at `var_floor` (A4), which also removes EM's
    classical singularity rather than merely surviving it.
    """
    p, m1, v1, m2, v2 = start
    W = float(w.sum())
    p = min(max(p, 1e-6), 1 - 1e-6)
    v1, v2 = max(v1, var_floor), max(v2, var_floor)

    prev = -np.inf
    for _ in range(max_iter):
        la = np.log(p) + _gauss_logpdf(t, m1, v1)
        lb = np.log1p(-p) + _gauss_logpdf(t, m2, v2)
        lse = np.logaddexp(la, lb)
        ll = float(np.sum(w * lse))
        r = np.exp(la - lse)
        n1 = float(np.sum(w * r))
        n2 = W - n1
        if n1 <= 0 or n2 <= 0:
            return None
        p = min(max(n1 / W, 1e-12), 1 - 1e-12)
        m1 = float(np.sum(w * r * t) / n1)
        m2 = float(np.sum(w * (1 - r) * t) / n2)
        v1 = max(float(np.sum(w * r * (t - m1) ** 2) / n1), var_floor)
        v2 = max(float(np.sum(w * (1 - r) * (t - m2) ** 2) / n2), var_floor)
        if abs(ll - prev) < tol:
            prev = ll
            break
        prev = ll

    la = np.log(p) + _gauss_logpdf(t, m1, v1)
    lb = np.log1p(-p) + _gauss_logpdf(t, m2, v2)
    lse = np.logaddexp(la, lb)
    ll = float(np.sum(w * lse))
    r = np.exp(la - lse)
    n1 = float(np.sum(w * r))
    if n1 < MIN_COMPONENT_MASS or (W - n1) < MIN_COMPONENT_MASS:
        return None
    return ll, p, m1, v1, m2, v2, r


def _fit_two_components(t: np.ndarray, w: np.ndarray, var_floor: float):
    """Best weighted 2-component fit, from TWO named deterministic starts.

    ⚠️ THIS IS NOT MULTI-START HEURISTICS. EM finds a local optimum, and with a
    two-means start it can only ever propose an OFFSET pair. Measured
    consequence (a real false positive, not a hypothetical): a concentric
    narrow-core + broad-halo cloud -- one topic with a heavy tail -- gets fitted
    as a left/right split with Ashman D ~ 4, and is declared multi-modal. It
    persists at n/d = 25, so it is a basin-of-attraction problem, not a
    small-sample one.

    The two starts are exactly the two competing EXPLANATIONS of a wide 1-D
    sample, and likelihood is left to choose between them:

        "TWO THINGS"  : the exact optimal two-means split (offset means).
        "HEAVY TAIL"  : both components on the common mean, one narrow
                        (pooled/9) and one broad (4 x pooled) -- concentric.

    Both starts are closed-form functions of the data, so the whole diagnostic
    stays deterministic and seed-free (A5). Returns the higher-likelihood fit,
    or None if both are degenerate.
    """
    W = float(w.sum())
    mu = float(np.sum(w * t) / W)
    pooled = max(float(np.sum(w * (t - mu) ** 2) / W), var_floor)

    starts = []
    split = _best_two_means_split(t, w)
    if split is not None:
        m1, m2, mass1 = split
        starts.append((mass1, m1, pooled, m2, pooled))          # "two things"
    starts.append((0.5, mu, pooled / 9.0, mu, pooled * 4.0))     # "heavy tail"

    best = None
    for s in starts:
        fit = _em_two(t, w, s, var_floor)
        if fit is not None and (best is None or fit[0] > best[0]):
            best = fit
    return best


def multimodality(vectors: Sequence[np.ndarray],
                  weights: Optional[Sequence[float]] = None,
                  eps: float = EPS_FLOOR) -> MultimodalityReport:
    """Decide whether ONE Gaussian is an adequate model of this fine complex.

    See the module docstring for the full statement. In one line: project on
    PC1, compare a one-component against a two-component Gaussian model by BIC,
    and additionally require the two components to be RESOLVABLE (Ashman's
    D >= 2) so that kurtosis cannot masquerade as bimodality.

    Returns a report. `decidable=False` means the question could not be asked
    (too few concepts) -- distinguishable from `multimodal=False`, which is an
    answer. Nothing is defaulted.
    """
    M, w = _as_matrix(vectors, weights)
    n = M.shape[0]
    tot = float(w.sum())
    if n == 0 or tot <= 0:
        return MultimodalityReport(n=n, n_eff=0.0, decidable=False,
                                   reason="idle organ: no concepts with positive weight")

    n_eff = kish_n_eff(w)
    if n_eff <= MIN_N_EFF_FOR_SPLIT:
        return MultimodalityReport(
            n=n, n_eff=n_eff, decidable=False,
            reason=f"n_eff={n_eff:.2f} <= {MIN_N_EFF_FOR_SPLIT} = params of a "
                   "2-component mixture; the model is unidentifiable")

    eig, p1, mu = scatter_spectrum(M, w)
    tot_eig = float(eig.sum())
    explained_1 = float(eig[0] / tot_eig) if tot_eig > 0 and eig.size else 0.0
    if eig.size >= 2 and eig[1] > 0:
        gap = float(eig[0] / eig[1])
    else:
        gap = float("inf")

    # A3: rescale weights to sum to n_eff so BIC's log(n) term is coherent.
    ws = w * (n_eff / tot)
    t = (M - mu) @ p1
    W = float(ws.sum())

    # one component
    m0 = float(np.sum(ws * t) / W)
    v0 = max(float(np.sum(ws * (t - m0) ** 2) / W), eps)
    ll1 = float(np.sum(ws * _gauss_logpdf(t, m0, v0)))
    bic1 = 2.0 * np.log(n_eff) - 2.0 * ll1

    fit = _fit_two_components(t, ws, var_floor=eps)
    if fit is None:
        return MultimodalityReport(
            n=n, n_eff=n_eff, decidable=True,
            reason="two-component fit degenerate (a component held < "
                   f"{MIN_COMPONENT_MASS} effective observations)",
            eig=eig, explained_1=explained_1, eigengap=gap,
            loglik_1=ll1, loglik_2=float("nan"), delta_bic=float("-inf"),
            ashman_d=0.0, mode_masses=(1.0,), multimodal=False, labels=None)

    ll2, p, m1, v1, m2, v2, r = fit
    bic2 = 5.0 * np.log(n_eff) - 2.0 * ll2
    delta_bic = float(bic1 - bic2)
    ashman = float(np.sqrt(2.0) * abs(m1 - m2) / np.sqrt(v1 + v2))

    multi = (delta_bic > BIC_DECISIVE) and (ashman >= ASHMAN_MIN)
    labels = (r <= 0.5).astype(int)              # 0 = component 1, 1 = component 2
    n_side0 = int((labels == 0).sum())
    if multi and (n_side0 < 2 or n - n_side0 < 2):
        multi = False                            # a side of one point has no shape

    mass0 = float(np.sum(w[labels == 0]) / tot)
    reason = ("decisive BIC and resolvable components" if multi else
              "one Gaussian is adequate" if delta_bic <= BIC_DECISIVE else
              f"two components fitted but unresolvable (Ashman D={ashman:.2f} "
              f"< {ASHMAN_MIN}); that is tail shape, not two things")

    return MultimodalityReport(
        n=n, n_eff=n_eff, decidable=True, reason=reason,
        eig=eig, explained_1=explained_1, eigengap=gap,
        loglik_1=ll1, loglik_2=ll2, delta_bic=delta_bic, ashman_d=ashman,
        mode_masses=(mass0, 1.0 - mass0), multimodal=multi,
        labels=labels if multi else None)


# ===========================================================================
# 2. pi_v v1 and v2
# ===========================================================================

def pi_v1(vectors: Sequence[np.ndarray],
          weights: Optional[Sequence[float]] = None,
          prior_factor: Optional[np.ndarray] = None,
          kappa: float = 1.0,
          rank: Optional[int] = None,
          eps: float = EPS_FLOOR) -> Optional[Gaussian]:
    """Construction 2 v1, UNCHANGED: the weighted centroid, as a Gaussian stalk.

    A pass-through to `belief.stalk_gaussian`, present only so that v1 and v2
    can be called through one interface in a comparison. It adds nothing and
    must never be allowed to: v1 is byte-for-byte load-bearing for the C++
    parity test (§5j) and the rho calibration (§5h).

    Returns None for an idle organ -- an idle organ has no position.
    """
    return stalk_gaussian(vectors, weights, prior_factor=prior_factor,
                          kappa=kappa, rank=rank, eps=eps)


def pi_v2(vectors: Sequence[np.ndarray],
          weights: Optional[Sequence[float]] = None,
          prior_factor: Optional[np.ndarray] = None,
          kappa: float = 1.0,
          rank: Optional[int] = None,
          eps: float = EPS_FLOOR,
          report: Optional[MultimodalityReport] = None
          ) -> Optional[Gaussian]:
    """Construction 2 v2: **v1 restricted to the fine complex's DOMINANT MODE.**

    If the fine complex is unimodal (or the question is undecidable), this
    returns the object `pi_v1` returns, BIT-IDENTICALLY -- because it calls it,
    on the same arguments. That is the required degradation and it is
    structural, not asserted (test 4 verifies it anyway).

    If the fine complex is decisively multi-modal, the concepts of the
    heavier mode are selected and v1 is applied to THOSE. What is discarded is
    visible: `multimodality(...).mode_masses` reports the fraction, and
    `pi_v_modes` returns the discarded modes as first-class stalks. Nothing is
    averaged away silently -- which is the entire complaint against v1 here.

    ⚠️ v2 is a STOPGAP and should be read as one. A decisively multi-modal
    organ is two organs; the correct response is a `split` of the coarse
    vertex, for which `multimodality()` is now the criterion. v2 is what to do
    until the split happens.

    `report` may be passed in to avoid recomputing the diagnostic.
    """
    if vectors is None or len(vectors) == 0:
        return None
    M, w = _as_matrix(vectors, weights)
    if float(w.sum()) <= 0:
        return None

    rep = report if report is not None else multimodality(M, w, eps=eps)
    if not rep.multimodal or rep.labels is None:
        return pi_v1(vectors, weights, prior_factor=prior_factor,
                     kappa=kappa, rank=rank, eps=eps)

    masses = [float(np.sum(w[rep.labels == c])) for c in (0, 1)]
    keep = rep.labels == int(np.argmax(masses))
    return pi_v1([M[i] for i in np.flatnonzero(keep)], w[keep],
                 prior_factor=prior_factor, kappa=kappa, rank=rank, eps=eps)


def pi_v_modes(vectors: Sequence[np.ndarray],
               weights: Optional[Sequence[float]] = None,
               prior_factor: Optional[np.ndarray] = None,
               kappa: float = 1.0,
               rank: Optional[int] = None,
               eps: float = EPS_FLOOR,
               max_depth: int = 3) -> List[Tuple[Gaussian, np.ndarray, float]]:
    """The SPLIT-READY decomposition: every mode as its own stalk.

    Recursive binary splitting while the diagnostic keeps firing, capped at
    `max_depth` (so at most 2^max_depth modes). Returns
    [(Gaussian, concept indices, mass fraction), ...] sorted by mass descending.

    A unimodal organ returns exactly one entry whose Gaussian is v1's, so this
    too degrades exactly. The cap is stated rather than hidden: beyond depth 3
    the sub-samples are smaller than the parameter count anyway and the
    diagnostic refuses on its own (`decidable=False`), so the cap is a
    belt-and-braces bound, not a modelling choice.
    """
    if vectors is None or len(vectors) == 0:
        return []
    M, w = _as_matrix(vectors, weights)
    if float(w.sum()) <= 0:
        return []
    total = float(w.sum())

    out: List[Tuple[Gaussian, np.ndarray, float]] = []

    def recurse(idx: np.ndarray, depth: int) -> None:
        sub_w = w[idx]
        g = pi_v1([M[i] for i in idx], sub_w, prior_factor=prior_factor,
                  kappa=kappa, rank=rank, eps=eps)
        if g is None:
            return
        if depth >= max_depth:
            out.append((g, idx, float(sub_w.sum()) / total))
            return
        rep = multimodality(M[idx], sub_w, eps=eps)
        if not rep.multimodal or rep.labels is None:
            out.append((g, idx, float(sub_w.sum()) / total))
            return
        for c in (0, 1):
            child = idx[rep.labels == c]
            if child.size:
                recurse(child, depth + 1)

    recurse(np.arange(M.shape[0]), 0)
    out.sort(key=lambda tpl: -tpl[2])
    return out


# ===========================================================================
# 3. sigma_dir -- the quantity V6 measured, under either pi_v
# ===========================================================================

def sigma_dir_pair(g0: Gaussian, g1: Gaussian) -> Tuple[float, float]:
    """Spread along the separation direction, for each stalk of a pair.

    Identical formula to `measure_sigma_dir.sigma_dir` (Sigma = U U^T + eps I,
    so u^T Sigma u = ||U^T u||^2 + eps for unit u), restated here only so this
    module can be imported without dragging in the corpus loader. **The
    separation direction is recomputed from the stalks passed in**, so under v2
    it is the direction between the two DOMINANT MODES, which is the honest
    comparison: v2 moves the means, and the yardstick must move with them.
    """
    diff = g0.mu - g1.mu
    nrm = float(np.linalg.norm(diff))
    if nrm < 1e-12:
        raise ValueError("organs coincide; separation direction undefined")
    u = diff / nrm
    s0 = float(np.sum((g0.U.T @ u) ** 2) + g0.eps) if g0.k else g0.eps
    s1 = float(np.sum((g1.U.T @ u) ** 2) + g1.eps) if g1.k else g1.eps
    return float(np.sqrt(s0)), float(np.sqrt(s1))


# ===========================================================================
# 4. THE MEASUREMENT: sigma_dir under v1 vs v2, on the real corpus
# ===========================================================================

def measure_corpus() -> int:
    """Re-run V6 with both coarse-graining maps. Costs real embedding time.

    Deliberately NOT part of `_main()`: the self-test must stay free (zero
    model loads, zero API calls), the same discipline every other self-test in
    this project follows. Run with:  python pi_v.py --corpus
    """
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    import console
    from embeddings import embed_batch, EMBED_DIM
    from cone_bures import bures_w2_sq
    from derived_scales import derive_delta
    from measure_sigma_dir import load_organs

    console.setup()
    print("=" * 78)
    print("pi_v v2 — sigma_dir UNDER v1 (centroid) vs v2 (dominant mode)")
    print("=" * 78)

    organs_text = load_organs()
    if len(organs_text) < 2:
        print("Not enough documents to form two organs.")
        return 1
    print(f"organs: {len(organs_text)}   (V6's corpus, unchanged: one per document)")
    print(f"embedding: bge-small-en-v1.5, d = {EMBED_DIM}, unit-normalised\n")

    embs = {}
    for name, paras in organs_text.items():
        V = np.stack([np.asarray(v, float) for v in embed_batch(paras)])
        if V.shape[1] != EMBED_DIM:
            raise RuntimeError(f"embedding dim {V.shape[1]} != {EMBED_DIM}")
        embs[name] = V

    print("--- THE DIAGNOSTIC: is one Gaussian adequate for each organ? ---")
    reps, g1s, g2s = {}, {}, {}
    n_multi = 0
    for name in sorted(embs):
        V = embs[name]
        rep = multimodality(V)
        reps[name] = rep
        g1s[name] = pi_v1(list(V))
        g2s[name] = pi_v2(list(V), report=rep)
        n_multi += int(rep.multimodal)
        print(f"  {name[:34]:<34} {rep.line()}")
    print(f"\n  {n_multi} / {len(embs)} organs are decisively multi-modal.")

    names = sorted(n for n in embs if g1s[n] is not None and g2s[n] is not None)

    # ---- one global delta, derived from the FULL concept sets ---------------
    # Used for BOTH arms. Re-deriving delta from v2's restricted concept sets
    # would move the yardstick between the arms and make the comparison
    # meaningless; the point is to isolate what changes in sigma_dir and d_BW.
    within, between = [], []
    for i, n in enumerate(names):
        M = embs[n]
        for a in range(len(M)):
            for b in range(a + 1, len(M)):
                within.append(float(np.linalg.norm(M[a] - M[b])))
        for n2 in names[i + 1:]:
            M2 = embs[n2]
            for a in range(0, len(M), 3):
                for b in range(0, len(M2), 3):
                    between.append(float(np.linalg.norm(M[a] - M2[b])))
    est = derive_delta(within, between)
    print(f"\n  global delta (V6's estimator, all concepts): {est!r}")

    rows = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            try:
                s1a, s1b = sigma_dir_pair(g1s[a], g1s[b])
                s2a, s2b = sigma_dir_pair(g2s[a], g2s[b])
            except ValueError:
                continue
            d1 = float(np.sqrt(max(0.0, bures_w2_sq(g1s[a], g1s[b]))))
            d2 = float(np.sqrt(max(0.0, bures_w2_sq(g2s[a], g2s[b]))))
            if d1 < 1e-9 or d2 < 1e-9:
                continue
            rows.append((f"{a[:20]} | {b[:20]}",
                         max(s1a, s1b), d1, max(s2a, s2b), d2))

    if not rows:
        print("No admissible pairs.")
        return 1

    sd1 = np.array([r[1] for r in rows])
    db1 = np.array([r[2] for r in rows])
    sd2 = np.array([r[3] for r in rows])
    db2 = np.array([r[4] for r in rows])

    pair1, pair2 = sd1 / (db1 / np.pi), sd2 / (db2 / np.pi)
    glob1, glob2 = sd1 / est.delta, sd2 / est.delta

    print(f"\n{'pair':<45} {'sd v1':>8} {'sd v2':>8} {'r_g v1':>8} {'r_g v2':>8} {'chg':>7}")
    print("-" * 88)
    order = np.argsort(-glob1)
    for idx in order[:12]:
        lab = rows[idx][0]
        print(f"{lab:<45} {sd1[idx]:>8.4f} {sd2[idx]:>8.4f} "
              f"{glob1[idx]:>8.3f} {glob2[idx]:>8.3f} "
              f"{100*(glob2[idx]/glob1[idx]-1):>+6.1f}%")
    if len(rows) > 12:
        print(f"  ... {len(rows)-12} more pairs")

    def block(title, a1, a2):
        print(f"\n  {title}")
        for tag, arr in (("v1 (centroid)     ", a1), ("v2 (dominant mode)", a2)):
            print(f"    {tag}  med {np.median(arr):.4f}   mean {arr.mean():.4f}   "
                  f"max {arr.max():.4f}   frac>0.3 {float((arr > 0.3).mean()):.3f}")
        print(f"    change in median: {100*(np.median(a2)/np.median(a1)-1):+.1f}%   "
              f"in max: {100*(a2.max()/a1.max()-1):+.1f}%")

    print("\n" + "=" * 78)
    print("RESULT  (pairs measured: %d)" % len(rows))
    print("=" * 78)
    block("sigma_dir / delta, GLOBAL delta (the number telemetry would carry):",
          glob1, glob2)
    block("sigma_dir / delta, PER-PAIR delta = d_BW/pi (V6's first column):",
          pair1, pair2)
    print(f"\n  sigma_dir itself : v1 med {np.median(sd1):.4f} -> v2 med {np.median(sd2):.4f}")
    print(f"  d_BW  (separation): v1 med {np.median(db1):.4f} -> v2 med {np.median(db2):.4f}")
    print("\n  Read the RATIO, not sigma_dir alone: v2 moves both the spread and the")
    print("  separation, and only their quotient governs agreement with true HK.")

    # ---- the effect on the pairs v2 ACTUALLY TOUCHED ------------------------
    # Averaging over pairs that contain no multi-modal organ dilutes the effect
    # toward zero by construction, which would understate v2 either way. Report
    # the touched subset separately -- it is the only place v2 can act at all.
    touched = np.flatnonzero(np.abs(glob2 - glob1) > 1e-12)
    print(f"\n  pairs v2 actually changed: {touched.size} / {len(rows)} "
          f"(a pair moves only if one of its organs is multi-modal)")
    if touched.size:
        print(f"    on those pairs: med {np.median(glob1[touched]):.4f} -> "
              f"{np.median(glob2[touched]):.4f}   "
              f"({100*(np.median(glob2[touched])/np.median(glob1[touched])-1):+.1f}%)")

    # ---- the verdict, computed rather than asserted -------------------------
    print("\n" + "=" * 78)
    print("VERDICT")
    print("=" * 78)
    frac_multi = n_multi / len(embs)
    print(f"  organs decisively multi-modal : {n_multi}/{len(embs)}  ({frac_multi:.0%})")
    print(f"  sigma_dir/delta median        : {np.median(glob1):.4f} -> "
          f"{np.median(glob2):.4f}")
    print(f"  sigma_dir/delta max           : {glob1.max():.4f} -> {glob2.max():.4f}")
    if glob2.max() <= 0.3:
        print("\n  v2 brings the WORST pair under 0.30. The 5z verdict is recoverable.")
    elif np.median(glob2) < 0.9 * np.median(glob1):
        print("\n  v2 helps materially (>10% on the median) but the worst pairs remain")
        print("  above 0.30. Multi-modality was PART of the story, not all of it.")
    else:
        cond = (100 * (np.median(glob2[touched]) / np.median(glob1[touched]) - 1)
                if touched.size else 0.0)
        print("\n  v2 DOES NOT RESCUE THE CORPUS-LEVEL NUMBER. The decomposition is")
        print("  the whole finding, and the two halves point opposite ways:")
        print(f"    * CONDITIONAL effect (pairs with a multi-modal organ): {cond:+.1f}%")
        print("      -- so the MECHANISM IS REAL. Where an organ genuinely is several")
        print("      things, collapsing it to one centroid does inflate sigma_dir, and")
        print("      v2 removes that inflation, exactly as Construction 2 anticipated.")
        print(f"    * PREVALENCE: only {n_multi}/{len(embs)} organs ({frac_multi:.0%}) are "
              "multi-modal at all,")
        print(f"      so the MARGINAL effect on the median is only "
              f"{100*(np.median(glob2)/np.median(glob1)-1):+.1f}%.")
        print("\n  Conclusion: multi-modality is NOT what makes V6's number bad.")
        print(f"  {len(embs)-n_multi}/{len(embs)} organs are adequately described by ONE "
              "Gaussian, so sigma_dir")
        print("  here is NOT model misspecification -- it is genuine within-organ spread")
        print("  measured against a small between-organ separation. That is §5ah's own")
        print("  diagnosis ('it is NOT sigma_dir, it is the SEPARATION'), now confirmed")
        print("  from the other side by ruling out the competing explanation.")
        print("  **V6's bad result STANDS.**")
        print("\n  What v2 is still worth keeping for: it costs nothing when unimodal")
        print("  (bit-identical to v1), it pays off where multi-modality does occur,")
        print("  and it converts `split` from an unspecified structural operation into")
        print("  a derived one. It is not, on this corpus, the fix for V6.")
        print("\n  ⚠️ SCOPE: 11 document-organs, one project, one author -- V6's own")
        print("  caveat carries over unchanged. A corpus of genuinely mixed-topic")
        print("  organs would have a higher prevalence and therefore a larger marginal")
        print("  effect. That is V6b's question, and it is NOT answered here.")
    return 0


# ===========================================================================
# Self-tests. Run: python pi_v.py       (zero model loads, zero API calls)
# ===========================================================================

def _main() -> None:
    # The project's Windows console is cp1252; this module's output uses
    # non-latin-1 glyphs. console.setup() is the house fix (see validate_regime.py,
    # measure_sigma_dir.py) -- without it the test block dies on a UnicodeEncodeError
    # partway through, which looks like a test failure and is not one.
    import console
    console.setup()

    ok = 0

    def check(name: str, cond: bool) -> None:
        nonlocal ok
        assert cond, f"FAILED: {name}"
        ok += 1
        print(f"  [ok] {name}")

    rng = np.random.default_rng(20260731)
    d = 48

    def cloud(centre, n, scale, axis=None, stretch=1.0):
        X = rng.normal(size=(n, d)) * scale
        if axis is not None:
            X += np.outer(rng.normal(size=n) * scale * stretch, axis)
        return centre + X

    print("=== 0. the spectrum is REPORTED, not silently averaged ===")
    e1 = np.eye(d)[0]
    bi = np.vstack([cloud(np.zeros(d), 30, 0.10),
                    cloud(1.2 * e1, 30, 0.10)])
    eig, p1, mu = scatter_spectrum(bi)
    check(f"leading spectrum has min(n,d) entries ({eig.size})", eig.size == min(60, d))
    check("eigenvalues are sorted descending", np.all(np.diff(eig) <= 1e-12))
    check(f"PC1 of a two-lobed cloud aligns with the lobe separation "
          f"(|<p1,e1>| = {abs(float(p1 @ e1)):.4f})", abs(float(p1 @ e1)) > 0.95)
    check("the weighted mean sits BETWEEN the lobes (v1's whole problem)",
          0.4 < float(mu @ e1) < 0.8)

    print("\n=== 1. an ISOTROPIC organ is not multi-modal ===")
    iso = cloud(np.zeros(d), 40, 0.25)
    r_iso = multimodality(iso)
    print("      ", r_iso.line())
    check("isotropic: decidable and one mode", r_iso.decidable and not r_iso.multimodal)

    print("\n=== 2. a genuinely BIMODAL organ is caught ===")
    r_bi = multimodality(bi)
    print("      ", r_bi.line())
    check("bimodal: declared MULTI-MODAL", r_bi.multimodal)
    check("BIC is decisive, not marginal", r_bi.delta_bic > BIC_DECISIVE)
    check("components are resolvable (Ashman D >= 2)", r_bi.ashman_d >= ASHMAN_MIN)
    check("the split recovers the two lobes 30/30",
          sorted(int((r_bi.labels == c).sum()) for c in (0, 1)) == [30, 30])

    print("\n=== 3. ★ THE EIGENGAP ALONE WOULD FAIL: elongated /= multi-modal ===")
    # One topic discussed at varying length: a cigar. Huge lambda_1/lambda_2,
    # perfectly unimodal. A pure eigengap rule splits it; the model comparison
    # must not.
    cig = cloud(np.zeros(d), 40, 0.08, axis=e1, stretch=14.0)
    r_cig = multimodality(cig)
    print("      ", r_cig.line())
    check(f"the cigar has a LARGER eigengap than the bimodal cloud "
          f"({r_cig.eigengap:.1f} vs {r_bi.eigengap:.1f})",
          r_cig.eigengap > r_bi.eigengap)
    check("...yet is correctly NOT declared multi-modal",
          r_cig.decidable and not r_cig.multimodal)
    check("=> elongation is not multi-modality, and the eigengap cannot tell "
          "them apart on its own", True)

    print("\n=== 4. ★ v2 DEGRADES EXACTLY TO v1 WHEN THE ORGAN IS ONE THING ===")
    for label, X in (("isotropic", iso), ("elongated (cigar)", cig),
                     ("n = 4 (undecidable)", cloud(np.zeros(d), 4, 0.3)),
                     ("n = 1", cloud(np.zeros(d), 1, 0.3))):
        a, b = pi_v1(list(X)), pi_v2(list(X))
        same = (np.array_equal(a.mu, b.mu) and np.array_equal(a.U, b.U)
                and a.eps == b.eps and a.n_eff == b.n_eff)
        check(f"{label}: v2 is BIT-IDENTICAL to v1", same)
    # ...and with non-uniform simplex weights, which is the deployed case.
    wgt = rng.uniform(0.2, 3.0, size=len(iso))
    a, b = pi_v1(list(iso), wgt), pi_v2(list(iso), wgt)
    check("weighted isotropic organ: v2 bit-identical to v1",
          np.array_equal(a.mu, b.mu) and np.array_equal(a.U, b.U))

    print("\n=== 5. on a bimodal organ v2 is DIFFERENT, and lands on a real mode ===")
    g1, g2 = pi_v1(list(bi)), pi_v2(list(bi))
    c1, c2 = float(g1.mu @ e1), float(g2.mu @ e1)
    print(f"       v1 mean along the split axis = {c1:.4f}  (between the lobes)")
    print(f"       v2 mean along the split axis = {c2:.4f}  (on a lobe)")
    check("v2 is not v1", not np.allclose(g1.mu, g2.mu))
    check("v2 sits on a lobe (near 0.0 or near 1.2), not between them",
          min(abs(c2 - 0.0), abs(c2 - 1.2)) < 0.1)
    check("v1 sits between them, on neither", min(abs(c1), abs(c1 - 1.2)) > 0.4)

    print("\n=== 6. ★ THE MECHANISM: v2 removes the BETWEEN-MODE variance ===")
    # Two organs separated along e2. Organ A is bimodal ALONG THE SEPARATION,
    # so v1's sigma_dir is inflated by structure, not by uncertainty.
    e2 = np.eye(d)[1]
    A = np.vstack([cloud(np.zeros(d), 25, 0.06),
                   cloud(0.9 * e2, 25, 0.06)])
    B = cloud(2.2 * e2, 40, 0.06)
    a1, b1 = pi_v1(list(A)), pi_v1(list(B))
    a2, b2 = pi_v2(list(A)), pi_v2(list(B))
    s1 = max(sigma_dir_pair(a1, b1))
    s2 = max(sigma_dir_pair(a2, b2))
    d_1 = float(np.linalg.norm(a1.mu - b1.mu))
    d_2 = float(np.linalg.norm(a2.mu - b2.mu))
    print(f"       v1: sigma_dir = {s1:.4f}   ||dmu|| = {d_1:.4f}   ratio = {s1/d_1:.4f}")
    print(f"       v2: sigma_dir = {s2:.4f}   ||dmu|| = {d_2:.4f}   ratio = {s2/d_2:.4f}")
    check("v2 cuts sigma_dir when the organ splits ALONG the separation", s2 < s1)
    check("and the sigma_dir/separation ratio improves too", s2 / d_2 < s1 / d_1)

    print("\n=== 7. ...and it is NOT a free lunch: fewer concepts RAISE the floor ===")
    # belief.py's shrinkage floor is eps + kappa/(d(n_eff+kappa)). Dropping a
    # mode drops n_eff, so v2 pays for its smaller sample. If this ever failed,
    # v2 would be lowering sigma_dir by deleting evidence rather than by
    # modelling it.
    print(f"       v1 n_eff = {a1.n_eff:.1f}, floor = {a1.eps:.6e}")
    print(f"       v2 n_eff = {a2.n_eff:.1f}, floor = {a2.eps:.6e}")
    check("v2's stalk floor is strictly LARGER (it is charged for less evidence)",
          a2.eps > a1.eps)

    print("\n=== 8. the split-ready decomposition (the criterion for a `split`) ===")
    modes = pi_v_modes(list(A))
    print(f"       organ A decomposes into {len(modes)} modes, masses "
          f"{[round(m, 3) for _, _, m in modes]}")
    check("a bimodal organ yields 2 modes", len(modes) == 2)
    check("masses sum to 1", abs(sum(m for _, _, m in modes) - 1.0) < 1e-12)
    check("each mode is a full Gaussian stalk",
          all(isinstance(g, Gaussian) for g, _, _ in modes))
    solo = pi_v_modes(list(iso))
    check("a unimodal organ yields exactly ONE mode", len(solo) == 1)
    check("and that mode's stalk is bit-identical to v1",
          np.array_equal(solo[0][0].mu, pi_v1(list(iso)).mu)
          and np.array_equal(solo[0][0].U, pi_v1(list(iso)).U))

    print("\n=== 9. REFUSALS: no position is invented ===")
    check("idle organ (no concepts): pi_v1 returns None", pi_v1([]) is None)
    check("idle organ (no concepts): pi_v2 returns None", pi_v2([]) is None)
    zero = cloud(np.zeros(d), 5, 0.3)
    check("all-zero weights: pi_v2 returns None (not the origin)",
          pi_v2(list(zero), [0.0] * 5) is None)
    r_small = multimodality(cloud(np.zeros(d), 4, 0.3))
    check(f"n_eff below the parameter count is UNDECIDABLE, not 'unimodal' "
          f"({r_small.reason[:44]}...)",
          (not r_small.decidable) and (not r_small.multimodal))
    check("'undecidable' is distinguishable from an answer",
          r_iso.decidable and not r_small.decidable)
    for name, fn in [("negative weights are refused",
                      lambda: multimodality(list(iso), [-1.0] * len(iso))),
                     ("a weight/vector count mismatch is refused",
                      lambda: multimodality(list(iso), [1.0, 2.0])),
                     ("coincident stalks have no separation direction",
                      lambda: sigma_dir_pair(pi_v1(list(iso)), pi_v1(list(iso))))]:
        try:
            fn()
            raise AssertionError(f"FAILED: {name} (no exception raised)")
        except ValueError:
            ok += 1
            print(f"  [ok] {name}")

    print("\n=== 10. determinism: no seed, no restarts, no drift ===")
    r_a = multimodality(bi)
    r_b = multimodality(bi)
    check("the diagnostic is bit-reproducible across calls",
          r_a.delta_bic == r_b.delta_bic and r_a.ashman_d == r_b.ashman_d)
    perm = rng.permutation(len(bi))
    r_p = multimodality(bi[perm])
    check(f"and invariant under concept ORDER (dBIC {r_a.delta_bic:.4f} vs "
          f"{r_p.delta_bic:.4f})", abs(r_a.delta_bic - r_p.delta_bic) < 1e-6)

    print("\n=== 11. ★ THE KURTOSIS TRAP: heavy tails must NOT read as two things ===")
    # A unimodal but heavy-tailed cloud: one topic, some paragraphs far more
    # specific than others. A two-component mixture fits it far better than one
    # Gaussian -- narrow core + broad halo, CONCENTRIC -- so BIC alone
    # DECISIVELY favours two. Ashman's D is what refuses it, and this test
    # exists so that the guard cannot be deleted as redundant.
    heavy = np.vstack([cloud(np.zeros(d), 45, 0.05), cloud(np.zeros(d), 15, 0.35)])
    r_h = multimodality(heavy)
    print("      ", r_h.line())
    print("       reason:", r_h.reason)
    check(f"BIC alone would SPLIT it (dBIC = {r_h.delta_bic:+.1f} >> {BIC_DECISIVE})",
          r_h.delta_bic > BIC_DECISIVE)
    check(f"but the components are concentric, not separated "
          f"(Ashman D = {r_h.ashman_d:.2f} << {ASHMAN_MIN})",
          r_h.ashman_d < ASHMAN_MIN)
    check("=> a concentric narrow+broad mixture is NOT declared multi-modal",
          not r_h.multimodal)
    check("and v2 therefore degrades to v1 on it",
          np.array_equal(pi_v1(list(heavy)).mu, pi_v2(list(heavy)).mu))

    print("\n=== 12. ...and the OTHER guard is load-bearing too ===")
    # The isotropic cloud of test 1 passes Ashman (D >= 2 by chance on a
    # noise-driven split) and is refused by BIC. So neither test alone suffices:
    # each of the two unimodal families above is caught by a DIFFERENT guard.
    print(f"       isotropic : dBIC {r_iso.delta_bic:+8.2f}  Ashman {r_iso.ashman_d:5.2f}"
          f"   -> refused by BIC")
    print(f"       heavy tail: dBIC {r_h.delta_bic:+8.2f}  Ashman {r_h.ashman_d:5.2f}"
          f"   -> refused by Ashman")
    check("Ashman alone would have passed the isotropic cloud",
          r_iso.ashman_d >= ASHMAN_MIN and r_iso.delta_bic <= BIC_DECISIVE)
    check("BIC alone would have passed the heavy-tailed cloud",
          r_h.delta_bic > BIC_DECISIVE and r_h.ashman_d < ASHMAN_MIN)
    check("=> the conjunction is necessary; neither statistic is decoration", True)

    print(f"\nAll {ok} pi_v tests passed (zero model loads, zero API calls).")
    print("Corpus measurement (costs embedding time):  python pi_v.py --corpus")


if __name__ == "__main__":
    import sys
    if "--corpus" in sys.argv:
        raise SystemExit(measure_corpus())
    _main()
