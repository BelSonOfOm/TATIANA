"""Construction 5 -- organs as latent causes of co-activation. Phase-2 item 9.

=============================================================================
WHAT THIS IS, AND WHAT IT IS NOT YET
=============================================================================
Construction 5 derives the cover element: an organ is a LATENT CAUSE in a
noisy-OR model of co-activation, and its content is the recruitment vector
theta_.i in [0,1]^N. The cover/partition question then stops being aesthetic
and becomes model selection, because the two model classes have genuinely
different latent structure:

    competitive (mixture)  : p(c) = sum_i pi_i p(c|i),  sum pi_i = 1
                             -> causes COMPETE for normalised mass
                             -> the latent structure is a PARTITION

    disjunctive (noisy-OR) : p(x_c = 0 | z) = exp(-sum_i z_i lambda_ci)
                             -> causes SUPERPOSE, no normalisation
                             -> the latent structure is a COVER

A sum versus a convex combination. That is the whole difference, and it is
testable: fit both, compare on held-out data (T1).

**THIS FILE IMPLEMENTS THE INSTRUMENT AND VALIDATES IT ON SYNTHETIC DATA WITH
KNOWN GROUND TRUTH. IT DOES NOT YET SAY ANYTHING ABOUT MOS's OWN CORPUS.**
T1-T3 need accumulated E7 assembly records, and none exist yet -- the tick only
started recording them today. What is established here is narrower and has to
come first: that the instrument can tell the two model classes apart on data
where we already know the answer. An instrument that cannot do that could not be
trusted on data where we do not.

=============================================================================
EXACT EM, NOT VARIATIONAL -- BECAUSE K IS SMALL
=============================================================================
K is a count of ORGANS, not of concepts, so K <= ~12 and 2^K <= 4096. The
posterior over latent configurations is therefore computed EXACTLY by
enumeration, and the M-step is closed form via the standard noisy-OR auxiliary
variable ("which cause fired this concept"). No mean-field bound, no sampling,
so nothing here is an approximation whose error has to be tracked.

The cost is exponential in K and that is stated, not hidden: this is affordable
because K is small by construction, and it would NOT be affordable if organs were
concepts. `MAX_K` refuses rather than silently taking minutes.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

# Enumerating 2^K latent configurations is exact and cheap for organ counts, and
# catastrophic for concept counts. Refuse rather than silently take minutes.
MAX_K = 14

# theta is clipped away from the open interval's endpoints: theta = 1 makes a
# cause fire a concept with certainty (so no other cause can ever explain it) and
# theta = 0 removes it from the model without removing it from K.
THETA_MIN = 1e-6
THETA_MAX = 1.0 - 1e-6

# THE LEAK, AND WHY IT IS NOT OPTIONAL.
# Without it, the all-organs-off configuration gives P(concept fires) = 0
# EXACTLY, so any tick where a concept fires while the model thinks every cause
# is silent has likelihood zero and the log-likelihood is -inf. Numerically that
# surfaces as 0 * -inf = NaN in the marginalisation; conceptually it is worse
# than a numerical problem -- it says the model must explain every single
# co-activation or be infinitely surprised.
#
# A leak node is the standard noisy-OR answer and it is the honest one here:
# concepts sometimes fire for reasons outside the organ decomposition, and the
# model should be allowed to say so rather than being forced to invent an organ
# for every stray activation. Held as a rate lambda_0 = -log(1 - p_leak).
LEAK_PROB = 1e-3
LEAK_RATE = -math.log1p(-LEAK_PROB)


# =============================================================== the data ====

Assembly = Sequence[int]  # concept indices active at one tick


def assemblies_to_matrix(assemblies: Sequence[Assembly], n_concepts: int) -> np.ndarray:
    """T x N binary matrix of co-activation.

    WHAT FEEDS THIS. An assembly is the set of STORED concepts retrieved in one
    tick -- `retrieved` in the E7 record, which the engine fills from SearchOp's
    Wasserstein query. It is NOT `grown`: neurogenesis adds each concept exactly
    once, so a matrix built from growth has one firing per column and its
    "co-activation" is nothing but growth order. Both fields are recorded; only
    this one can carry a latent-cause model.

    (An earlier version of this docstring claimed the log already yielded this.
    It did not: NodeRecord.support is a foliation-scheduling constant, never a
    concept index.)
    """
    X = np.zeros((len(assemblies), n_concepts), dtype=float)
    for t, a in enumerate(assemblies):
        for c in a:
            if not (0 <= c < n_concepts):
                raise ValueError(f"concept index {c} out of range for N={n_concepts}")
            X[t, c] = 1.0
    return X


def alive_mask(birth_tick: Sequence[int], T: int, n_concepts: int) -> np.ndarray:
    """T x N mask: 1 where the concept EXISTED at that tick, 0 before it was born.

    WHY THIS IS NOT OPTIONAL FOR A GROWING STORE. Construction 5 assumes a fixed
    N x K theta, but MOS grows concepts as it runs. Without a mask, every tick
    before concept c was born contributes a (1 - x_tc) = 1 "this concept stayed
    silent" term to the likelihood -- and the model is forced to explain the
    silence of something that did not exist. That drives theta_c down in
    proportion to how late c was born, so the fitted organs would systematically
    under-recruit recent concepts. Missing-not-at-random, in the direction that
    exactly mimics "organs stopped growing".
    """
    if len(birth_tick) != n_concepts:
        raise ValueError(f"birth_tick has {len(birth_tick)} entries, need {n_concepts}")
    ticks = np.arange(T)[:, None]
    return (ticks >= np.asarray(birth_tick)[None, :]).astype(float)


def _as_mask(mask: Optional[np.ndarray], X: np.ndarray) -> np.ndarray:
    """None means everything was always alive -- the fixed-N case, unchanged."""
    if mask is None:
        return np.ones_like(X)
    if mask.shape != X.shape:
        raise ValueError(f"mask shape {mask.shape} != data shape {X.shape}")
    return mask.astype(float)


# ====================================================== the two model classes ==

@dataclass
class NoisyOr:
    """Disjunctive causes. theta[c, i] = P(organ i recruits concept c)."""
    theta: np.ndarray   # (N, K)
    pi: np.ndarray      # (K,) organ activation rates

    @property
    def K(self) -> int:
        return self.theta.shape[1]

    def loglik(self, X: np.ndarray, mask: Optional[np.ndarray] = None) -> float:
        return float(np.sum(_noisy_or_row_loglik(X, self.theta, self.pi, mask)))

    def n_params(self) -> int:
        return self.theta.size + self.pi.size


@dataclass
class Mixture:
    """Competitive causes: one component per tick, Bernoulli product emissions."""
    p: np.ndarray       # (N, K) P(concept c fires | component i)
    w: np.ndarray       # (K,) mixing weights, sum to 1

    @property
    def K(self) -> int:
        return self.p.shape[1]

    def loglik(self, X: np.ndarray, mask: Optional[np.ndarray] = None) -> float:
        return float(np.sum(_mixture_row_loglik(X, self.p, self.w, mask)))

    def n_params(self) -> int:
        return self.p.size + self.w.size - 1   # weights are simplex-constrained


# ------------------------------------------------------------- likelihoods ---

def _configs(K: int) -> np.ndarray:
    """All 2^K latent configurations, as a (2^K, K) 0/1 array."""
    if K > MAX_K:
        raise ValueError(
            f"K={K} exceeds MAX_K={MAX_K}. Exact enumeration is 2^K and is only "
            "affordable because organs are few. If K is this large the latent "
            "variables are not organs.")
    return np.array(list(itertools.product([0, 1], repeat=K)), dtype=float)


def _noisy_or_row_loglik(X: np.ndarray, theta: np.ndarray, pi: np.ndarray,
                         mask: Optional[np.ndarray] = None) -> np.ndarray:
    """log p(x_t) per tick, marginalising z EXACTLY over 2^K configurations."""
    Z = _configs(theta.shape[1])                       # (C, K)
    lam = -np.log1p(-np.clip(theta, THETA_MIN, THETA_MAX))   # (N, K), lambda = -log(1-theta)

    # drive[c, n] = leak + sum_i z_ci lambda_ni  -> (C, N). The leak keeps the
    # all-off configuration from having likelihood exactly zero.
    drive = LEAK_RATE + Z @ lam.T
    log_p0 = -drive                                    # log P(concept off | z)
    log_p1 = np.log(-np.expm1(-drive))                 # log P(concept on  | z)

    # log p(x_t | z) = sum_{n alive at t} [x log p1 + (1-x) log p0]
    # The mask multiplies BOTH terms, so a concept not yet born contributes
    # nothing at all -- neither a firing nor, more importantly, a silence.
    M = _as_mask(mask, X)
    ll_x_given_z = (X * M) @ log_p1.T + ((1.0 - X) * M) @ log_p0.T  # (T, C)

    log_prior = Z @ np.log(pi) + (1.0 - Z) @ np.log1p(-pi)   # (C,)
    return _logsumexp(ll_x_given_z + log_prior[None, :], axis=1)


def _mixture_row_loglik(X: np.ndarray, p: np.ndarray, w: np.ndarray,
                        mask: Optional[np.ndarray] = None) -> np.ndarray:
    pc = np.clip(p, THETA_MIN, THETA_MAX)
    M = _as_mask(mask, X)
    ll = (X * M) @ np.log(pc) + ((1.0 - X) * M) @ np.log1p(-pc)   # (T, K)
    return _logsumexp(ll + np.log(w)[None, :], axis=1)


def _logsumexp(a: np.ndarray, axis: int) -> np.ndarray:
    m = np.max(a, axis=axis, keepdims=True)
    return np.squeeze(m, axis=axis) + np.log(np.sum(np.exp(a - m), axis=axis))


# ==================================================================== fitting ==

def fit_noisy_or(X: np.ndarray, K: int, iters: int = 200, seed: int = 0,
                 tol: float = 1e-8, mask: Optional[np.ndarray] = None) -> NoisyOr:
    """Exact EM for the noisy-OR model.

    E-step enumerates z exactly. M-step uses the standard auxiliary variable
    y_tci = "cause i fired concept c at tick t", whose posterior given z is
    closed form, so nothing here is a bound.
    """
    rng = np.random.default_rng(seed)
    T, N = X.shape
    M = _as_mask(mask, X)
    theta = np.clip(rng.uniform(0.05, 0.5, size=(N, K)), THETA_MIN, THETA_MAX)
    pi = np.clip(rng.uniform(0.2, 0.6, size=K), 1e-3, 1 - 1e-3)

    Z = _configs(K)
    prev = -np.inf
    for _ in range(iters):
        lam = -np.log1p(-theta)
        drive = LEAK_RATE + Z @ lam.T                      # (C, N)
        log_p0 = -drive
        log_p1 = np.log(-np.expm1(-drive))

        ll_x_given_z = (X * M) @ log_p1.T + ((1.0 - X) * M) @ log_p0.T
        log_prior = Z @ np.log(pi) + (1.0 - Z) @ np.log1p(-pi)
        joint = ll_x_given_z + log_prior[None, :]
        ll = _logsumexp(joint, axis=1)
        resp = np.exp(joint - ll[:, None])                 # (T, C) posterior over z

        # --- M-step -------------------------------------------------------
        # E[z_ti] under the posterior.
        Ez = resp @ Z                                      # (T, K)

        # E[y_tci]: for x_tc = 1, cause i's share of the firing, given z. The
        # shares over organs sum to <= 1 rather than = 1, with the remainder
        # attributed to the leak -- which is exactly what the leak is for.
        p_on = -np.expm1(-drive)                           # (C, N)
        p_on = np.clip(p_on, 1e-300, None)
        num = Z[:, None, :] * theta[None, :, :]            # (C, N, K)
        share = num / p_on[:, :, None]

        # Weight by the posterior over z and by whether the concept actually fired.
        # Ey[n, i] = sum_t m_tn x_tn sum_c resp_tc share_cni
        w_cn = resp.T @ (X * M)                            # (C, N)
        Ey = np.einsum("cn,cnk->nk", w_cn, share)          # (N, K)

        # THE DENOMINATOR IS PER-(CONCEPT, ORGAN), NOT PER-ORGAN.
        # theta_ni is a rate per OPPORTUNITY, and concept n's opportunities are
        # only the ticks where it existed. The unmasked code divided by
        # sum_t E[z_ti], which counts every tick for every concept -- correct
        # only when all concepts are alive throughout. With a growing store that
        # inflates the denominator for late concepts and shrinks their theta,
        # which is the very bias the mask exists to remove; leaving this line
        # alone would have reintroduced it one step after the E-step fixed it.
        denom = M.T @ Ez                                   # (N, K) = sum_t m_tn E[z_ti]
        theta = np.clip(Ey / np.maximum(denom, 1e-12), THETA_MIN, THETA_MAX)
        pi = np.clip(Ez.mean(axis=0), 1e-3, 1 - 1e-3)

        total = float(ll.sum())
        if abs(total - prev) < tol * max(1.0, abs(prev)):
            break
        prev = total

    return NoisyOr(theta=theta, pi=pi)


def fit_mixture(X: np.ndarray, K: int, iters: int = 300, seed: int = 0,
                tol: float = 1e-9, mask: Optional[np.ndarray] = None) -> Mixture:
    """Standard EM for a mixture of Bernoulli products (the COMPETITIVE class)."""
    rng = np.random.default_rng(seed)
    T, N = X.shape
    M = _as_mask(mask, X)
    p = np.clip(rng.uniform(0.2, 0.8, size=(N, K)), THETA_MIN, THETA_MAX)
    w = np.full(K, 1.0 / K)

    prev = -np.inf
    for _ in range(iters):
        ll_k = (X * M) @ np.log(p) + ((1.0 - X) * M) @ np.log1p(-p)   # (T, K)
        joint = ll_k + np.log(w)[None, :]
        ll = _logsumexp(joint, axis=1)
        r = np.exp(joint - ll[:, None])                     # (T, K)

        nk = r.sum(axis=0)                                  # (K,)
        # The MIXING WEIGHTS are unmasked on purpose: w_i is how often component
        # i is the active one, which every tick observes regardless of which
        # concepts happened to exist then. Only the EMISSIONS are masked.
        w = np.clip(nk / T, 1e-9, None)
        w /= w.sum()
        # Same per-(concept, component) opportunity count as the noisy-OR M-step.
        p = np.clip((X * M).T @ r / np.maximum(M.T @ r, 1e-12), THETA_MIN, THETA_MAX)

        total = float(ll.sum())
        if abs(total - prev) < tol * max(1.0, abs(prev)):
            break
        prev = total

    return Mixture(p=p, w=w)


# ============================================== T1: the model-class comparison ==

def block_split(T: int, n_folds: int = 5) -> List[Tuple[np.ndarray, np.ndarray]]:
    """Contiguous BLOCK folds, not random ticks.

    Assemblies are temporally correlated, so a random split leaks: a held-out
    tick would sit between two training ticks that nearly determine it, and both
    models would look better than they are. Blocks break that.
    """
    edges = np.linspace(0, T, n_folds + 1).astype(int)
    folds = []
    for i in range(n_folds):
        test = np.arange(edges[i], edges[i + 1])
        train = np.concatenate([np.arange(0, edges[i]), np.arange(edges[i + 1], T)])
        if len(test) and len(train):
            folds.append((train, test))
    return folds


@dataclass
class ModelComparison:
    noisy_or_heldout: float
    mixture_heldout: float
    K: int
    n_folds: int

    @property
    def favours_cover(self) -> bool:
        return self.noisy_or_heldout > self.mixture_heldout

    @property
    def margin_per_tick(self) -> float:
        return self.noisy_or_heldout - self.mixture_heldout

    def verdict(self) -> str:
        if self.favours_cover:
            return (f"COVER (noisy-OR) wins by {self.margin_per_tick:.4f} nats/tick "
                    f"at K={self.K}")
        return (f"PARTITION (mixture) wins by {-self.margin_per_tick:.4f} nats/tick "
                f"at K={self.K} -- Constructions 4 AND 5 are refuted")


def compare_model_classes(X: np.ndarray, K: int, n_folds: int = 5,
                          seed: int = 0) -> ModelComparison:
    """T1. Fit both classes, compare HELD-OUT predictive log-likelihood.

    Held-out and not in-sample: noisy-OR has more parameters than the mixture at
    the same K, so in-sample fit would reward it for flexibility alone and the
    comparison would be rigged in the cover's favour.
    """
    folds = block_split(X.shape[0], n_folds)
    if not folds:
        raise ValueError("Not enough ticks to form held-out blocks.")

    nor_total, mix_total, n_test = 0.0, 0.0, 0
    for train, test in folds:
        nor = fit_noisy_or(X[train], K, seed=seed)
        mix = fit_mixture(X[train], K, seed=seed)
        nor_total += nor.loglik(X[test])
        mix_total += mix.loglik(X[test])
        n_test += len(test)

    return ModelComparison(noisy_or_heldout=nor_total / n_test,
                           mixture_heldout=mix_total / n_test,
                           K=K, n_folds=len(folds))


# ==================================== T1, CALIBRATED: the margin is not zero ==
#
# WHY compare_model_classes ABOVE IS NOT ENOUGH, MEASURED RATHER THAN ARGUED.
#
# Its pass criterion is `noisy_or_heldout > mixture_heldout`, i.e. margin > 0.
# Zero is the right threshold only if the two classes are on equal footing when
# neither is true. They are not. Held-out margins from data with KNOWN truth,
# N=24, K=3, 5-fold block CV, 8 replicates (nats/tick, + favours cover):
#
#                       T=300    T=450    T=700   T=1200
#     cover  theta=0.20  +0.212   +0.182   +0.128   +0.127
#     cover  theta=0.12  +0.267   +0.112   +0.049   +0.023
#     partition p=0.20   +0.305   +0.082   -0.027   -0.089
#     partition p=0.12   +0.489   +0.291   +0.123   +0.015
#     permuted null      +0.062   +0.037   +0.021   +0.000
#
# Read the p=0.12 row. Data generated by a PARTITION scores +0.489 at T=300 and
# is still positive at T=700 -- and scores HIGHER than a genuine cover of the
# same strength. Applied to a weak real corpus, `margin > 0` would return COVER
# and confirm Constructions 4 and 5 by artefact.
#
# It is not an EM local-optimum artefact. Raising both fitters from 1 to 12
# random restarts moved partition p=0.12 from +0.137 to +0.128 -- nothing. The
# asymmetry is structural: at K=3 the noisy-OR marginalises 2^K = 8 latent
# configurations against the mixture's K = 3, at effectively the same parameter
# count, and that extra latent flexibility pays off on sparse data whichever
# class generated it.
#
# So the threshold has to be MEASURED, not assumed. The null is "a partition of
# whatever strength and sparsity this corpus actually has": fit the mixture,
# simulate from it, and push each simulation through the identical pipeline. The
# bias then appears in the null statistic exactly as in the observed one.
#
# THE PART THAT MAKES IT CALIBRATED, AND THE PART A FIRST ATTEMPT GOT WRONG:
# the null generator is fitted on the TRAINING FOLD ONLY. Fitting it on all of X
# lets it see the held-out rows, so null data is easier for the mixture than
# real data is, the null margin sits too low, and the test over-rejects -- 25%
# false COVER at a nominal 5%. Same fold, same protocol, both sides.

@dataclass
class CalibratedComparison:
    """T1 with a measured threshold instead of an assumed one."""
    observed: float            # margin per tick on the real data
    null: np.ndarray           # B margins from simulated partitions
    K: int
    n_folds: int
    alpha: float = 0.05

    @property
    def p_value(self) -> float:
        """P(a true partition would look at least this cover-like).

        The +1s are the standard finite-B correction: with B draws the smallest
        attainable p is 1/(B+1), never 0. A p of exactly 0 would claim more
        resolution than B simulations can support.
        """
        B = len(self.null)
        return (1 + int(np.sum(self.null >= self.observed))) / (1 + B)

    @property
    def favours_cover(self) -> bool:
        return self.p_value < self.alpha

    @property
    def margin_per_tick(self) -> float:
        return self.observed

    @property
    def excess_over_null(self) -> float:
        """How far above a true partition's typical margin the data sits.
        THIS is the effect size, not `observed` -- which is biased upward."""
        return self.observed - float(np.median(self.null))

    def verdict(self) -> str:
        if self.favours_cover:
            return (f"COVER (noisy-OR) at K={self.K}: margin {self.observed:+.4f} "
                    f"nats/tick, {self.excess_over_null:+.4f} above a fitted "
                    f"partition's median, p={self.p_value:.4f}")
        return (f"NO EVIDENCE FOR COVER at K={self.K}: margin {self.observed:+.4f} "
                f"nats/tick is within what a true partition produces "
                f"(p={self.p_value:.4f}). NOT proof of a partition -- see the "
                f"power table before reading this as one.")


def _simulate_mixture(mix: Mixture, T: int, rng: np.random.Generator,
                      mask: Optional[np.ndarray] = None) -> np.ndarray:
    """Draw T assemblies from a fitted mixture: pick a component, then emit."""
    comp = rng.choice(mix.K, size=T, p=mix.w / mix.w.sum())
    X = (rng.random((T, mix.p.shape[0])) < mix.p[:, comp].T).astype(float)
    if mask is not None:
        X *= mask       # a concept that did not exist cannot have fired
    return X


def calibrated_compare(X: np.ndarray, K: int, n_folds: int = 5, B: int = 49,
                       seed: int = 0, alpha: float = 0.05,
                       mask: Optional[np.ndarray] = None) -> CalibratedComparison:
    """T1 against a fitted-partition null. Use this, not `compare_model_classes`.

    Cost is B * n_folds * 2 EM fits. The null generator is fitted once per fold
    and reused across draws -- it is a function of the training data only, so
    refitting it per draw would burn time without changing its distribution.
    """
    folds = block_split(X.shape[0], n_folds)
    if not folds:
        raise ValueError("Not enough ticks to form held-out blocks.")
    M = _as_mask(mask, X)

    nor_total, mix_total, n_test = 0.0, 0.0, 0
    generators = []
    for train, test in folds:
        Xtr, Mtr = X[train], M[train]
        nor = fit_noisy_or(Xtr, K, seed=seed, mask=Mtr)
        mix = fit_mixture(Xtr, K, seed=seed, mask=Mtr)
        nor_total += nor.loglik(X[test], M[test])
        mix_total += mix.loglik(X[test], M[test])
        n_test += len(test)
        generators.append((mix, train, test))
    observed = (nor_total - mix_total) / n_test

    rng = np.random.default_rng(seed + 104729)
    null = np.empty(B)
    for b in range(B):
        b_nor, b_mix, b_n = 0.0, 0.0, 0
        for gen, train, test in generators:
            Mtr, Mte = M[train], M[test]
            Xtr = _simulate_mixture(gen, len(train), rng, Mtr)
            Xte = _simulate_mixture(gen, len(test), rng, Mte)
            f_nor = fit_noisy_or(Xtr, K, seed=seed, mask=Mtr)
            f_mix = fit_mixture(Xtr, K, seed=seed, mask=Mtr)
            b_nor += f_nor.loglik(Xte, Mte)
            b_mix += f_mix.loglik(Xte, Mte)
            b_n += len(test)
        null[b] = (b_nor - b_mix) / b_n

    return CalibratedComparison(observed=observed, null=null, K=K,
                                n_folds=len(folds), alpha=alpha)


# ================================================ T2: free energy over K ======

def free_energy(model: NoisyOr, X: np.ndarray) -> float:
    """F = -loglik + (model description cost). MDL, i.e. the same free-energy
    principle 5ag used to derive pi_e -- not a new import.

    The complexity term uses the BIC form (k/2) log T. It grows with K while the
    accuracy term falls, so F(K) CAN have an interior minimum -- which sigma_dir
    provably cannot, since k-means drives it monotonically down by construction.
    That is the whole reason 5ak's sweep found no optimum.
    """
    T = X.shape[0]
    return -model.loglik(X) + 0.5 * model.n_params() * math.log(max(T, 2))


def sweep_K(X: np.ndarray, Ks: Sequence[int], seed: int = 0) -> Dict[int, float]:
    """T2. F(K) over a bounded range. An interior minimum is a natural organ
    count; a monotone curve means this corpus has none, which is a FINDING and
    not an artefact of the instrument."""
    return {K: free_energy(fit_noisy_or(X, K, seed=seed), X) for K in Ks}


def interior_optimum(curve: Dict[int, float]) -> Optional[int]:
    """The argmin, or None when it sits at an endpoint (no natural scale)."""
    if len(curve) < 3:
        return None
    Ks = sorted(curve)
    best = min(Ks, key=lambda k: curve[k])
    return None if best in (Ks[0], Ks[-1]) else best


# ==================================================== T3: is overlap real? ====

def overlap_fraction(model: NoisyOr, threshold: float = 0.5) -> float:
    """Fraction of concepts claimed by MORE THAN ONE organ.

    Zero means the fitted cover degenerated to a partition and the overlap was
    fiction -- Construction 4's failure mode 3.
    """
    claims = (model.theta > threshold).sum(axis=1)
    return float(np.mean(claims > 1))


def membership_prior(n_ci: np.ndarray, m_i: np.ndarray, pi0: np.ndarray,
                     kappa: float) -> np.ndarray:
    """The initialisation, per Construction 5: Beta-per-(c,i), NOT Dirichlet.

        theta_ci = (n_ci + kappa * pi0_ci) / (m_i + kappa)

    At n = 0 this returns the hand-set six modules; as history accumulates it
    returns the data. kappa is what the hand-set structure is worth in
    observations.

    BETA-PER-PAIR and not Dirichlet-over-organs: a Dirichlet normalises sum_i to
    1, which would force a partition in expectation and destroy the overlap the
    whole construction exists to have -- through the PRIOR, even under a
    noisy-OR likelihood.
    """
    if n_ci.shape != pi0.shape:
        raise ValueError("n_ci and pi0 must have the same shape (N, K).")
    if m_i.shape[0] != n_ci.shape[1]:
        raise ValueError("m_i must have one entry per organ.")
    if kappa <= 0:
        raise ValueError("kappa must be positive -- it is a pseudo-count.")
    return np.clip((n_ci + kappa * pi0) / (m_i[None, :] + kappa), THETA_MIN, THETA_MAX)


# ================================================== synthetic ground truth ====

def generate_noisy_or(N: int, K: int, T: int, seed: int = 0,
                      overlap: float = 0.3) -> Tuple[np.ndarray, NoisyOr]:
    """Assemblies from a KNOWN noisy-OR model, with genuine overlap."""
    rng = np.random.default_rng(seed)
    theta = np.full((N, K), 0.02)
    per = N // K
    for i in range(K):
        theta[i * per:(i + 1) * per, i] = 0.85          # each organ's core concepts
    n_shared = max(1, int(overlap * per))
    for i in range(K):                                   # deliberate overlap
        j = (i + 1) % K
        theta[i * per:i * per + n_shared, j] = 0.85
    pi = np.full(K, 0.4)

    Z = (rng.random((T, K)) < pi).astype(float)
    drive = LEAK_RATE + Z @ (-np.log1p(-theta)).T
    X = (rng.random((T, N)) < -np.expm1(-drive)).astype(float)
    return X, NoisyOr(theta=theta, pi=pi)


def generate_mixture(N: int, K: int, T: int, seed: int = 0) -> Tuple[np.ndarray, Mixture]:
    """Assemblies from a KNOWN mixture -- one component per tick, no overlap."""
    rng = np.random.default_rng(seed)
    p = np.full((N, K), 0.02)
    per = N // K
    for i in range(K):
        p[i * per:(i + 1) * per, i] = 0.85
    w = np.full(K, 1.0 / K)

    comp = rng.choice(K, size=T, p=w)
    X = (rng.random((T, N)) < p[:, comp].T).astype(float)
    return X, Mixture(p=p, w=w)


def permuted_null(X: np.ndarray, seed: int = 0) -> np.ndarray:
    """T4's structureless null: permute concept identities WITHIN each tick,
    preserving assembly sizes and (approximately) concept marginals while
    destroying co-activation structure. Any apparent organ structure that
    survives this was an artefact of the instrument."""
    rng = np.random.default_rng(seed)
    Y = np.zeros_like(X)
    N = X.shape[1]
    for t in range(X.shape[0]):
        k = int(X[t].sum())
        if k:
            Y[t, rng.choice(N, size=k, replace=False)] = 1.0
    return Y
