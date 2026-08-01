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
    """T x N binary matrix. This is exactly what E7's assembly log yields."""
    X = np.zeros((len(assemblies), n_concepts), dtype=float)
    for t, a in enumerate(assemblies):
        for c in a:
            if not (0 <= c < n_concepts):
                raise ValueError(f"concept index {c} out of range for N={n_concepts}")
            X[t, c] = 1.0
    return X


# ====================================================== the two model classes ==

@dataclass
class NoisyOr:
    """Disjunctive causes. theta[c, i] = P(organ i recruits concept c)."""
    theta: np.ndarray   # (N, K)
    pi: np.ndarray      # (K,) organ activation rates

    @property
    def K(self) -> int:
        return self.theta.shape[1]

    def loglik(self, X: np.ndarray) -> float:
        return float(np.sum(_noisy_or_row_loglik(X, self.theta, self.pi)))

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

    def loglik(self, X: np.ndarray) -> float:
        return float(np.sum(_mixture_row_loglik(X, self.p, self.w)))

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


def _noisy_or_row_loglik(X: np.ndarray, theta: np.ndarray, pi: np.ndarray) -> np.ndarray:
    """log p(x_t) per tick, marginalising z EXACTLY over 2^K configurations."""
    Z = _configs(theta.shape[1])                       # (C, K)
    lam = -np.log1p(-np.clip(theta, THETA_MIN, THETA_MAX))   # (N, K), lambda = -log(1-theta)

    # drive[c, n] = leak + sum_i z_ci lambda_ni  -> (C, N). The leak keeps the
    # all-off configuration from having likelihood exactly zero.
    drive = LEAK_RATE + Z @ lam.T
    log_p0 = -drive                                    # log P(concept off | z)
    log_p1 = np.log(-np.expm1(-drive))                 # log P(concept on  | z)

    # log p(x_t | z) = sum_n [x log p1 + (1-x) log p0]
    ll_x_given_z = X @ log_p1.T + (1.0 - X) @ log_p0.T  # (T, C)

    log_prior = Z @ np.log(pi) + (1.0 - Z) @ np.log1p(-pi)   # (C,)
    return _logsumexp(ll_x_given_z + log_prior[None, :], axis=1)


def _mixture_row_loglik(X: np.ndarray, p: np.ndarray, w: np.ndarray) -> np.ndarray:
    pc = np.clip(p, THETA_MIN, THETA_MAX)
    ll = X @ np.log(pc) + (1.0 - X) @ np.log1p(-pc)     # (T, K)
    return _logsumexp(ll + np.log(w)[None, :], axis=1)


def _logsumexp(a: np.ndarray, axis: int) -> np.ndarray:
    m = np.max(a, axis=axis, keepdims=True)
    return np.squeeze(m, axis=axis) + np.log(np.sum(np.exp(a - m), axis=axis))


# ==================================================================== fitting ==

def fit_noisy_or(X: np.ndarray, K: int, iters: int = 200, seed: int = 0,
                 tol: float = 1e-8) -> NoisyOr:
    """Exact EM for the noisy-OR model.

    E-step enumerates z exactly. M-step uses the standard auxiliary variable
    y_tci = "cause i fired concept c at tick t", whose posterior given z is
    closed form, so nothing here is a bound.
    """
    rng = np.random.default_rng(seed)
    T, N = X.shape
    theta = np.clip(rng.uniform(0.05, 0.5, size=(N, K)), THETA_MIN, THETA_MAX)
    pi = np.clip(rng.uniform(0.2, 0.6, size=K), 1e-3, 1 - 1e-3)

    Z = _configs(K)
    prev = -np.inf
    for _ in range(iters):
        lam = -np.log1p(-theta)
        drive = LEAK_RATE + Z @ lam.T                      # (C, N)
        log_p0 = -drive
        log_p1 = np.log(-np.expm1(-drive))

        ll_x_given_z = X @ log_p1.T + (1.0 - X) @ log_p0.T
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
        # Ey[n, i] = sum_t x_tn sum_c resp_tc share_cni
        w_cn = resp.T @ X                                  # (C, N) = sum_t resp_tc x_tn
        Ey = np.einsum("cn,cnk->nk", w_cn, share)          # (N, K)

        denom = Ez.sum(axis=0)[None, :]                    # (1, K) = sum_t E[z_ti]
        theta = np.clip(Ey / np.maximum(denom, 1e-12), THETA_MIN, THETA_MAX)
        pi = np.clip(Ez.mean(axis=0), 1e-3, 1 - 1e-3)

        total = float(ll.sum())
        if abs(total - prev) < tol * max(1.0, abs(prev)):
            break
        prev = total

    return NoisyOr(theta=theta, pi=pi)


def fit_mixture(X: np.ndarray, K: int, iters: int = 300, seed: int = 0,
                tol: float = 1e-9) -> Mixture:
    """Standard EM for a mixture of Bernoulli products (the COMPETITIVE class)."""
    rng = np.random.default_rng(seed)
    T, N = X.shape
    p = np.clip(rng.uniform(0.2, 0.8, size=(N, K)), THETA_MIN, THETA_MAX)
    w = np.full(K, 1.0 / K)

    prev = -np.inf
    for _ in range(iters):
        ll_k = X @ np.log(p) + (1.0 - X) @ np.log1p(-p)     # (T, K)
        joint = ll_k + np.log(w)[None, :]
        ll = _logsumexp(joint, axis=1)
        r = np.exp(joint - ll[:, None])                     # (T, K)

        nk = r.sum(axis=0)                                  # (K,)
        w = np.clip(nk / T, 1e-9, None)
        w /= w.sum()
        p = np.clip((X.T @ r) / np.maximum(nk[None, :], 1e-12), THETA_MIN, THETA_MAX)

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
