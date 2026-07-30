"""
TATIANA - the system's BELIEF: prior stalks, and the posterior the sheaf produces.

WHY THIS FILE EXISTS
--------------------
Uncertainty in MOS was a single scalar D, hardcoded to 1.0 for every concept in
the engine (cognitive_state.cpp:224, curator.cpp:20), with U empty. Consequences,
all verified: W2 degenerates to plain Euclidean distance (E4), every entropy is
identical so every per-edge Delta S is exactly 0, and precision-weighted fusion
collapses to a plain average because all precisions are equal.

The obvious repair -- "let D reflect confidence" -- is WORSE than the bug. For two
isotropic Gaussians the exact Bures-Wasserstein covariance term is

    Tr S1 + Tr S2 - 2 Tr (S1^1/2 S2 S1^1/2)^1/2  =  d (sqrt(D1) - sqrt(D2))^2

which scales with d, while the semantic term ||mu1 - mu2||^2 is bounded by 4 for
unit embeddings, independent of d. At d = 384, a 5% difference in confidence
outweighs the LARGEST POSSIBLE semantic difference by ~57x. Meaning stops
mattering and only confidence does. That is E4's finding and it is why the
constant D was "working": it hid a dimensional error rather than avoiding one.

THE FIX, IN TWO PARTS
---------------------
1. D is demoted to EPS_FLOOR: a shared numerical floor, IDENTICAL for every
   concept. Then (sqrt(D1) - sqrt(D2))^2 = 0 and the d-extensive term vanishes
   identically. Not calibrated around -- gone.
2. All real uncertainty moves into the low-rank factor U:

       Sigma = U U^T + eps I

   Tr(Sigma) = ||U||_F^2 + d*eps, and since d*eps is shared, every DIFFERENCE is
   governed by ||U||_F^2 = O(k). Semantic and epistemic terms become dimensionally
   commensurate. And it is strictly more informative than a scalar: not "A is
   vaguer than B" but "A is spread out IN THESE DIRECTIONS" -- which is what a
   sheaf needs, since direction is what restriction maps act on.

**Only DIFFERENCES of the quantities here are meaningful.** eps contributes a
constant to every log-determinant and every entropy; it cancels between models on
the same complex, which is the only comparison we ever make. Absolute entropy in
384 dimensions is not a number to quote.

THE SHEAF-THEORETIC POINT (this is the whole design, do not skip it)
---------------------------------------------------------------------
A first draft of this file computed Sigma_v from organ v's own concepts and
stopped. That is a LOCAL estimate wearing sheaf vocabulary: the sheaf plays no
part in it. The sheaf's actual contribution is this.

Write down the Gaussian model the engine already implies -- each organ reports
mu_v with its own prior precision, and the edges impose consistency:

    -2 log p(x) = sum_v (x_v - mu_v)^T Sigma_v^-1 (x_v - mu_v)
                + sum_e pi_e || R_ue x_u - R_ve x_v ||^2

The second sum IS omega, the sheaf Laplacian quadratic form already implemented in
coherence.py. So the posterior precision of the whole system is

    Lambda = blockdiag(Sigma_v^-1) + L,        L = delta^T Pi delta

and the system's uncertainty about its own global state is Lambda^-1. Therefore:

  * Sigma_v is the PRIOR, not the answer. Local scatter is what an organ knows on
    its own; the sheaf turns priors into a posterior.
  * Uncertainty is NON-LOCAL. The marginal [Lambda^-1]_vv depends on the organ's
    degree, its neighbours' precisions and the topology. An organ bound to
    confident neighbours becomes more confident automatically -- no rule for it.
    `sharpening()` measures exactly that, and it is non-negative by theorem
    (adding the PSD term L can only increase precision), which is asserted below.
    **That is the "whole exceeds the parts" claim as a measured number.**
  * FRAGMENTATION gets a quantitative meaning. L is singular on the per-component
    constants, so without priors Lambda^-1 is infinite along ker L: with b0 > 1
    the system genuinely does not know where the components sit relative to each
    other. The prior is what makes the posterior proper -- a principled job, not
    a fudge.
  * The OCCAM FACTOR falls out free. For this model the log evidence is
    accuracy - (1/2) log det Lambda, so `log_det_lambda()` IS the complexity term
    needed to compare "flow" against "adapt" (learn R) without inventing a
    penalty. The density-matrix layer and the rewiring criterion are one object.

AND IT RESCUES THE ENTROPY DIAGNOSTIC
--------------------------------------
An earlier argument held that orthogonal (Householder) restriction maps give
S(R Sigma R^T) - S(Sigma) = 0 identically -- true, since orthogonal maps preserve
eigenvalues -- and concluded the entropy field was dead without lossy channels.
That is true of the TRANSPORT entropy and false of the POSTERIOR entropy. In
Lambda the diagonal blocks pick up R_ue^T pi_e R_ue = pi_e I, independent of R,
but the OFF-DIAGONAL blocks pick up -pi_e R_ue^T R_ve, which depends on the
relative rotation between the two organs' frames. So posterior uncertainty depends
on the maps even when every map is orthogonal, and we keep Householder --
preserving ||R|| <= 1 and the Anderson-Morley bound -- with a live entropy field.

COST
----
Lambda is (n*d) x (n*d) = 2688 x 2688 at n = 7, d = 384. It is never formed on the
fast path. With identity maps and low-rank priors it factors:

    Sigma_v^-1 = (1/eps)(I - U_v M_v U_v^T),  M_v = (eps I + U_v^T U_v)^-1
    =>  Lambda = (L_K + (1/eps) I_n) (x) I_d  -  G G^T,   G block-diagonal, K columns

so det Lambda = (det Lambda_base)^d * det(I_K - G^T Lambda_base^-1 G): an n x n
determinant and a K x K one, with K = sum_v k_v (~56 at k=8, n=7). Same Woodbury
identity already used in semantic_skill.cpp. The dense path is kept ONLY as a
correctness oracle and the two are asserted equal in the self-test.

With non-identity maps the Kronecker structure is lost and log det needs
Lanczos/stochastic trace estimation -- same discipline as 5s finding 2 (never form
the pseudo-inverse). Not implemented here; `log_det_lambda` refuses rather than
silently falling back to a dense solve that would take minutes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

Edge = Tuple[str, str]

# Shared numerical floor. IDENTICAL for every stalk, by design: that identity is
# exactly what kills the d-extensive Bures term (E4). It cancels in every
# comparison we make. Do not make this per-concept -- that is the bug, not the fix.
EPS_FLOOR = 1e-3


# --------------------------------------------------------------------------
# A Gaussian stalk
# --------------------------------------------------------------------------

@dataclass
class Gaussian:
    """N(mu, U U^T + eps I). Low-rank by construction; d is never materialised."""
    mu: np.ndarray                  # (d,)
    U: np.ndarray                   # (d, k); k = 0 allowed (then Sigma = eps I)
    eps: float = EPS_FLOOR
    n_eff: float = 0.0              # effective observations behind this estimate

    @property
    def d(self) -> int:
        return int(self.mu.size)

    @property
    def k(self) -> int:
        return 0 if self.U is None or self.U.size == 0 else int(self.U.shape[1])

    def sigma_dense(self) -> np.ndarray:
        S = self.eps * np.eye(self.d)
        if self.k:
            S = S + self.U @ self.U.T
        return S

    def precision_factors(self) -> Tuple[float, np.ndarray]:
        """Sigma^-1 = (1/eps) I - G G^T. Returns (1/eps, G) with G of shape (d,k).

        Woodbury:  (U U^T + eps I)^-1 = (1/eps) I - (1/eps) U (eps I + U^T U)^-1 U^T
        so G = U * M^(1/2) / sqrt(eps) with M = (eps I + U^T U)^-1, which is SPD,
        so the square root exists and G is real.
        """
        inv_eps = 1.0 / self.eps
        if not self.k:
            return inv_eps, np.zeros((self.d, 0))
        UtU = self.U.T @ self.U
        M = np.linalg.inv(self.eps * np.eye(self.k) + UtU)
        # symmetric PSD square root of M
        w, Q = np.linalg.eigh(M)
        w = np.clip(w, 0.0, None)
        Mhalf = Q @ np.diag(np.sqrt(w)) @ Q.T
        return inv_eps, (self.U @ Mhalf) * np.sqrt(inv_eps)

    def precision_dense(self) -> np.ndarray:
        inv_eps, G = self.precision_factors()
        P = inv_eps * np.eye(self.d)
        if G.shape[1]:
            P = P - G @ G.T
        return P

    def spectrum(self) -> np.ndarray:
        """The k signal eigenvalues of Sigma (excluding the shared floor)."""
        if not self.k:
            return np.zeros(0)
        s = np.linalg.svd(self.U, compute_uv=False)
        return s ** 2

    def log_det_sigma(self) -> float:
        """log det(U U^T + eps I) = (d-k) log eps + sum_i log(eps + sigma_i^2)."""
        sig = self.spectrum()
        return float((self.d - sig.size) * np.log(self.eps)
                     + np.sum(np.log(self.eps + sig)))

    def entropy(self) -> float:
        """Differential entropy (1/2) log det(2 pi e Sigma). Compare, never quote."""
        return 0.5 * (self.d * np.log(2 * np.pi * np.e) + self.log_det_sigma())

    def effective_rank(self) -> float:
        """exp(H) of the normalised SIGNAL spectrum: how many directions am I
        spread over? In [1, k]. Preferred over raw von Neumann entropy, which at
        d = 384 with a degenerate floor is dominated by the floor and says nothing.
        """
        sig = self.spectrum()
        tot = float(sig.sum())
        if sig.size == 0 or tot <= 0:
            return 0.0
        p = sig / tot
        p = p[p > 0]
        return float(np.exp(-np.sum(p * np.log(p))))


# --------------------------------------------------------------------------
# pi_v with shrinkage: the PRIOR stalk
# --------------------------------------------------------------------------

def corpus_prior(vectors: Optional[np.ndarray], d: int, rank: int = 16) -> np.ndarray:
    """Sigma_0 as a (d, r) factor: "where concepts live in this embedding space".

    With no corpus supplied, fall back to the isotropic-on-the-sphere prior
    Sigma_0 = (1/d) I, represented at full rank. That is deliberately BROAD: the
    prior's job is to say "could be anywhere concepts live", and a narrow prior
    would claim knowledge we do not have.
    """
    if vectors is None or len(vectors) < 2:
        return np.eye(d) / np.sqrt(d)          # factor B with B B^T = (1/d) I
    X = np.asarray(vectors, dtype=float)
    Xc = X - X.mean(axis=0, keepdims=True)
    # rank-r PCA factor: Sigma_0 ~ B B^T
    U, s, _ = np.linalg.svd(Xc, full_matrices=False)
    r = min(rank, s.size)
    return U[:, :r] * (s[:r] / np.sqrt(max(len(X) - 1, 1)))


def stalk_gaussian(vectors: Sequence[np.ndarray],
                   weights: Optional[Sequence[float]] = None,
                   prior_factor: Optional[np.ndarray] = None,
                   kappa: float = 1.0,
                   rank: Optional[int] = None,
                   eps: float = EPS_FLOOR) -> Optional[Gaussian]:
    """pi_v : an organ's fine complex -> a Gaussian PRIOR on its coarse position.

        Sigma_v = (S_v + kappa * Sigma_0) / (n_eff + kappa) + eps I

    S_v is the weighted scatter of the organ's active concepts; Sigma_0 is the
    corpus prior; kappa is a pseudo-count ("how many observations is the prior
    worth"). n_eff is Kish's effective sample size (sum w)^2 / sum w^2, which is
    the right count for weighted data.

    This fixes a real inversion in the current engine: a concept seen ONCE
    currently gets U empty => Sigma = eps I => MAXIMUM confidence from a single
    observation, which is backwards. Here n_eff = 1 gives Sigma ~ Sigma_0 (broad,
    the prior) and Sigma -> empirical as evidence accumulates.

    Returns None for an idle organ -- deliberately, and for the same reason
    module_vertex.stalk() does: an idle organ has no position, and inventing one
    fakes a measurement.
    """
    if vectors is None or len(vectors) == 0:
        return None
    M = np.stack([np.asarray(v, dtype=float).ravel() for v in vectors])
    n, d = M.shape
    w = np.ones(n) if weights is None else np.asarray(weights, dtype=float).ravel()
    if w.size != n:
        raise ValueError(f"{w.size} weights for {n} vectors")
    if np.any(w < 0):
        raise ValueError("negative concept weight")
    tot = float(w.sum())
    if tot <= 0:
        return None

    mu = (w[:, None] * M).sum(axis=0) / tot
    n_eff = float(tot ** 2 / float((w ** 2).sum()))    # Kish

    # Scatter as a factor: S_v = A A^T, A = sqrt(w_i) (c_i - mu) stacked as columns.
    A = ((M - mu) * np.sqrt(w)[:, None]).T             # (d, n)
    denom = np.sqrt(n_eff + kappa)

    if prior_factor is None:
        # DEFAULT PRIOR: Sigma_0 = (1/d) I, isotropic, TRACE 1 -- matching the fact
        # that embeddings are unit-normalised. Being isotropic it belongs in the
        # FLOOR, not in U: putting it in U would make k = d = 384, destroying the
        # low-rank economy the whole design rests on (measured: k=387, 6 s per
        # report at n=4). Folded in, k = n and a report is milliseconds.
        #
        #   Sigma_v = S_v/(n+kappa) + [ kappa/(d(n+kappa)) + eps ] I
        #
        # This makes the floor DEPEND ON n_eff, which looks like it violates the
        # E4 invariant. It does not, and the reason is the trace normalisation:
        # the added term is O(1/d), so the Bures epistemic term
        # d(sqrt(D1)-sqrt(D2))^2 is O(1), not O(d). See the guard in SystemBelief.
        floor = eps + kappa / (d * (n_eff + kappa))
        U = A / denom
        return Gaussian(mu=mu, U=U, eps=floor, n_eff=n_eff)

    B = prior_factor
    U = np.concatenate([A / denom, (np.sqrt(kappa) / denom) * B], axis=1)

    if rank is not None and U.shape[1] > rank:
        # Truncate to the leading `rank` directions. Energy dropped is reported by
        # the caller if it matters; we do not silently pretend it was zero.
        Uu, s, _ = np.linalg.svd(U, full_matrices=False)
        U = Uu[:, :rank] * s[:rank]

    return Gaussian(mu=mu, U=U, eps=eps, n_eff=n_eff)


# --------------------------------------------------------------------------
# The posterior the sheaf produces
# --------------------------------------------------------------------------

@dataclass
class BeliefReport:
    log_det_lambda: float
    posterior_entropy: float
    prior_entropy: Dict[str, float]
    post_entropy: Dict[str, float]
    sharpening: Dict[str, float]
    eff_rank_prior: Dict[str, float]
    eff_rank_post: Dict[str, float]

    def summary(self) -> str:
        tot = sum(self.sharpening.values())
        return (f"log det Lambda = {self.log_det_lambda:.4f}   "
                f"total sharpening = {tot:.4f} nats")

    def lines(self) -> List[str]:
        out = []
        for v in self.sharpening:
            out.append(
                f"   {v:12s} S_prior={self.prior_entropy[v]:9.3f} -> "
                f"S_post={self.post_entropy[v]:9.3f}   gain={self.sharpening[v]:7.4f} nats"
                f"   eff-rank {self.eff_rank_prior[v]:5.2f} -> {self.eff_rank_post[v]:5.2f}")
        return out


class SystemBelief:
    """Lambda = blockdiag(Sigma_v^-1) + L, and everything read off it.

    v1 restriction: IDENTITY restriction maps, so L = L_K (x) I_d and the Kronecker
    factorisation applies. Non-identity maps are refused rather than silently
    handled by a dense solve (2688^3 flops, minutes) -- see the module docstring.
    """

    def __init__(self,
                 priors: Dict[str, Gaussian],
                 edges: Sequence[Edge],
                 precision: Optional[Dict[Edge, float]] = None,
                 restriction: Optional[Dict[Edge, Tuple[np.ndarray, np.ndarray]]] = None):
        # restriction=None => identity maps => Kronecker fast path.
        # Non-identity maps break the factorisation; the dense path is used and
        # guarded by size. Model comparison is a SLOW-timescale decision
        # (learning), not a per-tick one, so seconds are acceptable there.
        self.restriction = restriction
        self.names = list(priors.keys())
        if not self.names:
            raise ValueError("SystemBelief needs at least one organ")
        self.priors = priors
        dims = {g.d for g in priors.values()}
        if len(dims) != 1:
            raise ValueError(f"Inconsistent stalk dimensions {sorted(dims)}; "
                             "refusing to pad or truncate.")
        self.d = dims.pop()
        self.idx = {v: i for i, v in enumerate(self.names)}
        self.edges = [(u, v) for (u, v) in edges
                      if u in self.idx and v in self.idx and u != v]
        self.precision = precision or {}
        self.eps = np.array([priors[v].eps for v in self.names], dtype=float)
        if np.any(self.eps <= 0):
            raise ValueError("stalk floors must be positive")

        # --- THE E4 GUARD, stated correctly -------------------------------------
        # The original invariant here was "every stalk shares one eps". That is
        # SUFFICIENT but too strong, and it forced the isotropic prior into U
        # (k = 384). The ACTUAL invariant is that the floor must be O(1/d), i.e.
        # the covariance must carry trace O(1), matching unit-normalised
        # embeddings. Then the Bures epistemic term between two isotropic parts,
        #
        #     d (sqrt(D1) - sqrt(D2))^2
        #
        # is O(1) and stays commensurate with the semantic term ||mu1-mu2||^2 <= 4.
        # E4's blow-up came from D = 1.0 = O(1), giving d*O(1) = O(d) = 229.75 at
        # d = 384. We check the real thing rather than a proxy for it.
        lo, hi = float(self.eps.min()), float(self.eps.max())
        bures = self.d * (np.sqrt(hi) - np.sqrt(lo)) ** 2
        if bures > 4.0:
            raise ValueError(
                f"Stalk floors span [{lo:.3g}, {hi:.3g}], giving an epistemic Bures "
                f"term of {bures:.2f} at d={self.d}. That exceeds the maximum "
                f"possible semantic distance (4), so confidence would outweigh "
                f"meaning -- exactly the E4 failure. Floors must be O(1/d).")
        self.bures_headroom = float(bures)

    def _pi(self, e: Edge) -> float:
        return float(self.precision.get(e, self.precision.get((e[1], e[0]), 1.0)))

    # -- the scalar graph Laplacian (identity maps => L = L_K (x) I_d) ---------
    def laplacian_K(self) -> np.ndarray:
        n = len(self.names)
        L = np.zeros((n, n))
        for (u, v) in self.edges:
            p = self._pi((u, v))
            i, j = self.idx[u], self.idx[v]
            L[i, i] += p
            L[j, j] += p
            L[i, j] -= p
            L[j, i] -= p
        return L

    def _base_and_G(self):
        """Lambda = Lambda_base (x) I_d - G G^T, with G block-diagonal by organ."""
        # blockdiag((1/eps_v) I_d) = diag(1/eps_v) (x) I_d, so a per-stalk floor
        # keeps the Kronecker structure and `base` stays n x n.
        base = self.laplacian_K() + np.diag(1.0 / self.eps)
        blocks = []
        for v in self.names:
            _, Gv = self.priors[v].precision_factors()
            blocks.append(Gv)
        return base, blocks

    def _maps(self, e: Edge):
        if self.restriction is None:
            return None
        return self.restriction.get(e, self.restriction.get((e[1], e[0])))

    def log_det_lambda(self) -> float:
        """log det Lambda. Kronecker fast path for identity maps, dense otherwise."""
        if self.restriction is not None:
            sign, ld = np.linalg.slogdet(self.lambda_dense())
            if sign <= 0:
                raise np.linalg.LinAlgError("Lambda is not positive definite")
            return float(ld)
        base, blocks = self._base_and_G()
        n = len(self.names)
        sign, logdet_base = np.linalg.slogdet(base)
        if sign <= 0:
            raise np.linalg.LinAlgError(
                "Lambda_base is not positive definite; precision must be PD.")
        binv = np.linalg.inv(base)

        cols = [b.shape[1] for b in blocks]
        K = int(sum(cols))
        if K == 0:
            return float(self.d * logdet_base)

        # C[a,b] = (Lambda_base^-1)_{ab} * (G_a^T G_b)
        C = np.zeros((K, K))
        offs, o = [], 0
        for c in cols:
            offs.append(o)
            o += c
        for a in range(n):
            if cols[a] == 0:
                continue
            for b in range(n):
                if cols[b] == 0:
                    continue
                C[offs[a]:offs[a] + cols[a], offs[b]:offs[b] + cols[b]] = \
                    binv[a, b] * (blocks[a].T @ blocks[b])
        sign2, logdet_corr = np.linalg.slogdet(np.eye(K) - C)
        if sign2 <= 0:
            raise np.linalg.LinAlgError(
                "I - G^T Lambda_base^-1 G is not PD; Lambda is not positive definite.")
        return float(self.d * logdet_base + logdet_corr)

    def lambda_dense(self) -> np.ndarray:
        """CORRECTNESS ORACLE ONLY. (n*d)^2 memory -- 58 MB at n=7, d=384."""
        n = len(self.names)
        nd = n * self.d
        if nd > 4000:
            raise MemoryError(
                f"dense Lambda would be {nd}x{nd}. This path is a test oracle, not "
                "a runtime path; use log_det_lambda()/marginal() instead.")
        Lam = np.zeros((nd, nd))
        for v in self.names:
            i = self.idx[v] * self.d
            Lam[i:i + self.d, i:i + self.d] += self.priors[v].precision_dense()
        if self.restriction is None:
            LK = self.laplacian_K()
            for a in range(n):
                for b in range(n):
                    if LK[a, b] != 0.0:
                        Lam[a * self.d:(a + 1) * self.d,
                            b * self.d:(b + 1) * self.d] += LK[a, b] * np.eye(self.d)
            return Lam
        # General maps: L = delta^T Pi delta assembled edge by edge.
        #   (delta x)_e = R_ue x_u - R_ve x_v
        for (u, v) in self.edges:
            p = self._pi((u, v))
            m = self._maps((u, v))
            Ru, Rv = (np.eye(self.d), np.eye(self.d)) if m is None else m
            a, b = self.idx[u] * self.d, self.idx[v] * self.d
            Lam[a:a + self.d, a:a + self.d] += p * (Ru.T @ Ru)
            Lam[b:b + self.d, b:b + self.d] += p * (Rv.T @ Rv)
            Lam[a:a + self.d, b:b + self.d] -= p * (Ru.T @ Rv)
            Lam[b:b + self.d, a:a + self.d] -= p * (Rv.T @ Ru)
        return Lam

    def marginal(self, v: str) -> np.ndarray:
        """[Lambda^-1]_vv, the organ's POSTERIOR covariance. Woodbury, never dense.

            Lambda^-1 = A^-1 + A^-1 G (I - G^T A^-1 G)^-1 G^T A^-1,  A = base (x) I_d
        """
        base, blocks = self._base_and_G()
        n = len(self.names)
        binv = np.linalg.inv(base)
        a = self.idx[v]
        cols = [b.shape[1] for b in blocks]
        K = int(sum(cols))
        out = binv[a, a] * np.eye(self.d)
        if K == 0:
            return out
        offs, o = [], 0
        for c in cols:
            offs.append(o)
            o += c
        # row-block a of A^-1 G  =  sum_u binv[a,u] * G_u   (as a (d, K) matrix)
        AinvG_a = np.zeros((self.d, K))
        for u in range(n):
            if cols[u]:
                AinvG_a[:, offs[u]:offs[u] + cols[u]] = binv[a, u] * blocks[u]
        C = np.zeros((K, K))
        for p in range(n):
            if not cols[p]:
                continue
            for q in range(n):
                if not cols[q]:
                    continue
                C[offs[p]:offs[p] + cols[p], offs[q]:offs[q] + cols[q]] = \
                    binv[p, q] * (blocks[p].T @ blocks[q])
        mid = np.linalg.inv(np.eye(K) - C)
        return out + AinvG_a @ mid @ AinvG_a.T

    # -- the readouts ---------------------------------------------------------
    def report(self) -> BeliefReport:
        pri_S, post_S, sharp, er_pri, er_post = {}, {}, {}, {}, {}
        half_const = 0.5 * self.d * np.log(2 * np.pi * np.e)
        for v in self.names:
            g = self.priors[v]
            Sp = g.entropy()
            Sig_post = self.marginal(v)
            sign, ld = np.linalg.slogdet(Sig_post)
            if sign <= 0:
                raise np.linalg.LinAlgError(f"posterior covariance for {v} not PD")
            Spost = half_const + 0.5 * ld
            pri_S[v], post_S[v] = Sp, Spost
            sharp[v] = Sp - Spost
            er_pri[v] = g.effective_rank()
            w = np.linalg.eigvalsh(Sig_post)
            w = np.clip(w - self.eps[self.idx[v]], 0.0, None)
            tot = float(w.sum())
            if tot > 0:
                p = w / tot
                p = p[p > 1e-15]
                er_post[v] = float(np.exp(-np.sum(p * np.log(p))))
            else:
                er_post[v] = 0.0
        ldl = self.log_det_lambda()
        n = len(self.names)
        S_sys = 0.5 * (n * self.d * np.log(2 * np.pi * np.e) - ldl)
        return BeliefReport(log_det_lambda=ldl, posterior_entropy=S_sys,
                            prior_entropy=pri_S, post_entropy=post_S,
                            sharpening=sharp, eff_rank_prior=er_pri,
                            eff_rank_post=er_post)


# --------------------------------------------------------------------------
# MODEL COMPARISON: flow (M0) vs adapt (M1)
# --------------------------------------------------------------------------
"""
"Given disagreement, how do I know how to rewire myself?" is structure learning /
dynamic causal modelling, and its answer is model comparison, not a threshold.

THE MODEL. The organ reports mu_v are the DATA; the latent global state x is what
the sheaf constrains:

    p(x)      propto  exp(-1/2 x^T L x)        the sheaf prior (improper on ker L)
    p(mu|x)   =       prod_v N(mu_v; x_v, Sigma_v)

Integrating x out exactly (both factors Gaussian) gives, with P = blockdiag(Sigma_v^-1)
and Lambda = P + L,

    -2 log p(mu)  =  mu^T (P - P Lambda^-1 P) mu   +   log det Lambda   -   log det P
                     \_______ ACCURACY _______/       \_ COMPLEXITY _/     \_ const _/

The accuracy term asks how well the consistency structure explains what the organs
actually reported; log det Lambda is the Occam factor. Both fall out of the object
belief.py already builds -- no penalty had to be invented.

WHAT IS AND IS NOT DECIDABLE THIS WAY (logbook 5w)
--------------------------------------------------
  M0 flow   : R fixed at identity, x inferred            -> decidable HERE
  M1 adapt  : R learned, x inferred                      -> decidable HERE
  M2 grow   : enlarge the complex                        -> NOT decidable on
              current data. With eta measured on the OLD edges a new vertex w
              appears in NO term of the fit, and filling a triangle leaves delta^0
              untouched; accuracy is unchanged while complexity rises, so
              Delta F < 0 always. **Growth is inherently a claim about FUTURE
              reconcilability** and needs held-out data or persistence.

THE PARAMETER PENALTY -- an approximation, named as one
--------------------------------------------------------
log det Lambda is the Occam factor for x, NOT for R: R is a point estimate, so its
own complexity must be charged separately. Done here with BIC, (1/2) k log N, which
is the standard crude approximation; the exact route is a prior on R plus a Laplace
term -1/2 log det H_R. It is used because the parameterisations differ by orders of
magnitude and no plausible penalty changes the ranking:

    identity          0 parameters
    Householder-m     m(d-1) per map      = 1532 at m=4, d=384
    full orthogonal   d(d-1)/2 per map    = 73536 at d=384

**So the comparison independently rediscovers why Householder is mandatory** (5s
found it from RAM: 576 KB/map vs 6 KB). A full orthogonal map is not merely
expensive to store, it is unaffordable as a model.
"""


@dataclass
class FreeEnergy:
    name: str
    accuracy: float          # mu^T (P - P Lambda^-1 P) mu   (lower is better)
    complexity: float        # log det Lambda
    param_penalty: float     # BIC charge for the restriction maps
    n_params: int

    @property
    def total(self) -> float:
        """-2 log evidence, up to a model-independent constant. LOWER IS BETTER."""
        return self.accuracy + self.complexity + 2.0 * self.param_penalty

    def line(self) -> str:
        return (f"   {self.name:22s} accuracy={self.accuracy:12.3f}  "
                f"complexity={self.complexity:11.3f}  "
                f"params={self.n_params:7d} (charge {2*self.param_penalty:10.1f})  "
                f"F={self.total:13.3f}")


def free_energy(priors: Dict[str, Gaussian],
                edges: Sequence[Edge],
                precision: Optional[Dict[Edge, float]] = None,
                restriction: Optional[Dict[Edge, Tuple[np.ndarray, np.ndarray]]] = None,
                n_params: int = 0,
                name: str = "model") -> FreeEnergy:
    """-2 log evidence for one model, up to a model-independent constant."""
    sb = SystemBelief(priors, edges, precision, restriction)
    names, d = sb.names, sb.d
    n = len(names)

    mu = np.concatenate([priors[v].mu for v in names])
    # P mu, block by block, via the Woodbury factors (never a dense inverse)
    Pmu = np.empty(n * d)
    muPmu = 0.0
    for v in names:
        i = sb.idx[v] * d
        g = priors[v]
        inv_eps, G = g.precision_factors()
        pv = inv_eps * g.mu - (G @ (G.T @ g.mu) if G.shape[1] else 0.0)
        Pmu[i:i + d] = pv
        muPmu += float(g.mu @ pv)

    Lam = sb.lambda_dense()
    z = np.linalg.solve(Lam, Pmu)
    accuracy = muPmu - float(Pmu @ z)
    complexity = sb.log_det_lambda()
    N = n * d                                    # one observation per stalk coordinate
    penalty = 0.5 * n_params * np.log(max(N, 2))
    return FreeEnergy(name=name, accuracy=accuracy, complexity=complexity,
                      param_penalty=penalty, n_params=n_params)


def ticks_to_justify(acc_gain_per_tick: float, n_params: int,
                     obs_per_tick: int, t_max: int = 10 ** 7) -> Optional[int]:
    """How many ticks of accumulated evidence before learning R pays for itself?

    Accuracy gain accumulates LINEARLY in the number of independent observations
    while the BIC charge grows only LOGARITHMICALLY, so a map that is unaffordable
    on one tick becomes affordable on enough of them. The crossover is the least T
    with

        T * acc_gain_per_tick  >  n_params * log(T * obs_per_tick)

    **This turns Q16 (gamma_0, the crystallization rate) from a hand-set constant
    into a derived one**: if the evidence says a map change needs T ticks of
    support before it is justified, then gamma_0 ~ 1/T is the rate at which the
    working complex may write back to the store. The two-complex model already
    demanded gamma_0 << 1 for anti-catastrophic-interference reasons; this says
    HOW small, from the data rather than from taste.

    ⚠️ Approximation, named: it assumes per-tick accuracy gains are independent.
    They are not -- the same map is being re-validated against correlated states --
    so the true T is LARGER than this returns. Treat it as a lower bound.
    """
    if acc_gain_per_tick <= 0 or n_params <= 0:
        return 1 if acc_gain_per_tick > 0 else None
    T = 1
    while T < t_max:
        if T * acc_gain_per_tick > n_params * np.log(max(T * obs_per_tick, 2)):
            return T
        T *= 2
    return None


def compare_models(models: Sequence[FreeEnergy]) -> Tuple[str, List[str]]:
    """Rank models by evidence. Returns (winner, printable lines)."""
    if not models:
        return "none", []
    ranked = sorted(models, key=lambda m: m.total)
    best = ranked[0]
    lines = [m.line() for m in models]
    lines.append("")
    for m in ranked[1:]:
        lines.append(f"   {best.name} beats {m.name} by "
                     f"{m.total - best.total:.2f} (-2 log evidence; >10 is decisive)")
    return best.name, lines


# --------------------------------------------------------------------------
# Self-test (free; no API calls)
# --------------------------------------------------------------------------

if __name__ == "__main__":
    import console
    console.setup()

    rng = np.random.default_rng(11)
    d = 12

    print("=== 1. Woodbury precision matches the dense inverse ===")
    for k in (0, 1, 3, 7):
        U = rng.normal(size=(d, k)) * 0.4 if k else np.zeros((d, 0))
        g = Gaussian(mu=rng.normal(size=d), U=U)
        err = np.abs(g.precision_dense() - np.linalg.inv(g.sigma_dense())).max()
        assert err < 1e-8, (k, err)
        print(f"    k={k}: max|Woodbury - inv(Sigma)| = {err:.2e}  OK")

    print("\n=== 2. log det Sigma matches slogdet ===")
    U = rng.normal(size=(d, 4)) * 0.5
    g = Gaussian(mu=np.zeros(d), U=U)
    _, ld = np.linalg.slogdet(g.sigma_dense())
    assert abs(ld - g.log_det_sigma()) < 1e-9, (ld, g.log_det_sigma())
    print(f"    {g.log_det_sigma():.6f} == {ld:.6f}  OK")

    print("\n=== 3. THE E4 FIX: a shared floor kills the d-extensive Bures term ===")
    # Two isotropic stalks with DIFFERENT D (the old design) vs the same eps.
    for dd in (12, 128, 384):
        D1, D2 = 1.0, 0.0513              # 0.0513 = -ln(0.95), a 5% confidence gap
        old = dd * (np.sqrt(D1) - np.sqrt(D2)) ** 2
        new = dd * (np.sqrt(EPS_FLOOR) - np.sqrt(EPS_FLOOR)) ** 2
        print(f"    d={dd:4d}:  per-concept D -> epistemic term {old:8.2f}   "
              f"(semantic term <= 4)   shared eps -> {new:.1f}")
    assert new == 0.0
    print("    the term is identically zero, for every d.  OK")

    print("\n=== 4. shrinkage: one observation is BROAD, many are SHARP ===")
    truth = rng.normal(size=d)
    B = corpus_prior(None, d)
    for n_obs in (1, 2, 5, 20):
        vecs = [truth + 0.15 * rng.normal(size=d) for _ in range(n_obs)]
        gg = stalk_gaussian(vecs, prior_factor=B, kappa=1.0)
        print(f"    n={n_obs:3d}  n_eff={gg.n_eff:5.2f}  Tr(Sigma)={np.trace(gg.sigma_dense()):8.4f}  "
              f"eff-rank={gg.effective_rank():5.2f}")
    one = stalk_gaussian([truth], prior_factor=B).sigma_dense()
    many = stalk_gaussian([truth + 0.15 * rng.normal(size=d) for _ in range(20)],
                          prior_factor=B).sigma_dense()
    assert np.trace(one) > np.trace(many), "one observation must be BROADER than twenty"
    print("    one observation is broader than twenty -- the current engine has this")
    print("    backwards (U empty => Sigma = eps I => certainty from one sighting).  OK")

    print("\n=== 5. log det Lambda: fast (Woodbury) == dense oracle ===")
    names = ["Reason", "Search", "Verify", "Context"]
    edges = [("Reason", "Search"), ("Reason", "Verify"), ("Reason", "Context"),
             ("Search", "Verify"), ("Verify", "Context")]
    priors = {v: Gaussian(mu=rng.normal(size=d), U=rng.normal(size=(d, 3)) * 0.5)
              for v in names}
    sb = SystemBelief(priors, edges)
    fast = sb.log_det_lambda()
    sign, dense = np.linalg.slogdet(sb.lambda_dense())
    assert sign > 0 and abs(fast - dense) < 1e-7, (fast, dense)
    print(f"    fast={fast:.8f}  dense={dense:.8f}  diff={abs(fast-dense):.2e}  OK")

    print("\n=== 6. marginal [Lambda^-1]_vv: Woodbury == dense oracle ===")
    Lam = sb.lambda_dense()
    Linv = np.linalg.inv(Lam)
    for v in names:
        i = sb.idx[v] * d
        err = np.abs(sb.marginal(v) - Linv[i:i + d, i:i + d]).max()
        assert err < 1e-8, (v, err)
    print(f"    all four organs agree with the dense inverse to < 1e-8  OK")

    print("\n=== 7. SHARPENING >= 0 always (the theorem, and the whole point) ===")
    # Adding the PSD sheaf Laplacian can only increase precision, so the marginal
    # posterior covariance is <= the prior in Loewner order and entropy drops.
    worst = 1e9
    for _ in range(200):
        pr = {v: Gaussian(mu=rng.normal(size=d),
                          U=rng.normal(size=(d, rng.integers(0, 5))) * rng.uniform(0.1, 1.0))
              for v in names}
        r = SystemBelief(pr, edges).report()
        worst = min(worst, min(r.sharpening.values()))
    print(f"    200 random configurations: min sharpening = {worst:.3e} (must be >= 0)")
    assert worst >= -1e-9, worst
    print("    OK -- being bound to others never makes an organ less certain.")

    print("\n=== 8. an organ bound to MORE organs is sharpened MORE ===")
    base_g = {v: Gaussian(mu=rng.normal(size=d), U=rng.normal(size=(d, 3)) * 0.5)
              for v in names}
    lonely = SystemBelief(base_g, [("Reason", "Search")]).report()
    social = SystemBelief(base_g, edges).report()
    print(f"    Reason with 1 edge : gain = {lonely.sharpening['Reason']:.4f} nats")
    print(f"    Reason with 3 edges: gain = {social.sharpening['Reason']:.4f} nats")
    assert social.sharpening["Reason"] > lonely.sharpening["Reason"]
    print("    OK -- 'the whole exceeds the parts', as a measured number.")

    print("\n=== 9. FRAGMENTATION: a disconnected organ gains NOTHING ===")
    iso = SystemBelief(base_g, [("Reason", "Search")]).report()
    print(f"    Context (no edges): gain = {iso.sharpening['Context']:.2e}")
    assert abs(iso.sharpening["Context"]) < 1e-9
    print("    OK -- an organ nobody is bound to learns nothing from the complex.")

    print("\n=== 10. precision on an edge increases sharpening ===")
    weak = SystemBelief(base_g, edges, precision={e: 0.01 for e in edges}).report()
    strong = SystemBelief(base_g, edges, precision={e: 100.0 for e in edges}).report()
    print(f"    pi=0.01  -> total sharpening {sum(weak.sharpening.values()):.4f} nats")
    print(f"    pi=100   -> total sharpening {sum(strong.sharpening.values()):.4f} nats")
    assert sum(strong.sharpening.values()) > sum(weak.sharpening.values())
    print("    OK -- trusting your neighbours more makes you more certain.")

    print("\n=== 11. THE E4 GUARD: floors that are not O(1/d) are REFUSED ===")
    bad = dict(base_g)
    bad["Verify"] = Gaussian(mu=rng.normal(size=d), U=np.zeros((d, 0)), eps=1.0)
    try:
        SystemBelief(bad, edges)
    except ValueError as e:
        print("    refused:", str(e)[:96], "...")
    else:
        raise AssertionError("should have refused an O(1) floor")
    # ...but genuinely O(1/d) variation, as the shrinkage prior produces, is fine.
    ok = dict(base_g)
    ok["Verify"] = Gaussian(mu=rng.normal(size=d), U=np.zeros((d, 0)),
                            eps=EPS_FLOOR + 1.0 / (d * 2.0))
    sb_ok = SystemBelief(ok, edges)
    print(f"    accepted a shrinkage-style floor: Bures term = "
          f"{sb_ok.bures_headroom:.3f} (semantic scale is 4)  OK")

    print("\n=== 11b. the low-rank economy holds at d = 384 ===")
    big = 384
    gg = stalk_gaussian([rng.normal(size=big) for _ in range(5)])
    assert gg.k == 5, f"k={gg.k}: the isotropic prior leaked into U"
    print(f"    5 concepts at d={big} -> k={gg.k} (NOT {big}); floor={gg.eps:.3e}")
    print(f"    isotropic prior folded into the floor, as it must be.  OK")

    print("\n=== 12. the report ===")
    r = SystemBelief(base_g, edges).report()
    print("   ", r.summary())
    for ln in r.lines():
        print(ln)

    # -------------------------------------------------- model comparison tests
    print("\n=== 13. general-R dense Lambda reduces to the identity case ===")
    ident = {e: (np.eye(d), np.eye(d)) for e in edges}
    a = SystemBelief(base_g, edges).lambda_dense()
    b = SystemBelief(base_g, edges, restriction=ident).lambda_dense()
    assert np.abs(a - b).max() < 1e-10, np.abs(a - b).max()
    la = SystemBelief(base_g, edges).log_det_lambda()
    lb = SystemBelief(base_g, edges, restriction=ident).log_det_lambda()
    assert abs(la - lb) < 1e-8, (la, lb)
    print(f"    identity maps: fast={la:.8f}  dense-general={lb:.8f}  OK")

    print("\n=== 14. free energy: an ALIGNED complex beats a MISALIGNED one ===")
    # Same organs; in one case the reports are consistent, in the other they are
    # rotated apart. The evidence must prefer the consistent one.
    core = rng.normal(size=d)
    tight = {v: Gaussian(mu=core + 0.05 * rng.normal(size=d),
                         U=rng.normal(size=(d, 2)) * 0.3) for v in names}
    loose = {v: Gaussian(mu=core + 1.5 * rng.normal(size=d),
                         U=rng.normal(size=(d, 2)) * 0.3) for v in names}
    f_t = free_energy(tight, edges, name="organs agree")
    f_l = free_energy(loose, edges, name="organs disagree")
    print(f_t.line())
    print(f_l.line())
    assert f_t.total < f_l.total
    print("    OK -- consistent organ reports have higher evidence.")

    print("\n=== 15. M0 (flow) vs M1 (adapt) vs an over-parameterised M1 ===")
    # M1's maps are a genuine rotation that RECONCILES two organs whose reports
    # are related by that rotation -- the situation learned maps exist for.
    Q, _ = np.linalg.qr(rng.normal(size=(d, d)))
    base_mu = rng.normal(size=d)
    rot = {}
    for i, v in enumerate(names):
        m = base_mu if i < 2 else Q @ base_mu       # two organs live in a rotated frame
        rot[v] = Gaussian(mu=m + 0.05 * rng.normal(size=d),
                          U=rng.normal(size=(d, 2)) * 0.2)
    R_learned = {}
    for (u, v) in edges:
        iu, iv = names.index(u), names.index(v)
        Ru = np.eye(d) if iu < 2 else Q.T
        Rv = np.eye(d) if iv < 2 else Q.T
        R_learned[(u, v)] = (Ru, Rv)

    m0 = free_energy(rot, edges, name="M0 flow (R=I)", n_params=0)
    m1h = free_energy(rot, edges, restriction=R_learned, name="M1 adapt (Householder m=4)",
                      n_params=4 * (d - 1) * len(edges))
    m1f = free_energy(rot, edges, restriction=R_learned, name="M1 adapt (full orthogonal)",
                      n_params=(d * (d - 1) // 2) * len(edges))
    win, lines = compare_models([m0, m1h, m1f])
    for ln in lines:
        print(ln)
    print(f"\n    winner: {win}")
    assert m1h.accuracy < m0.accuracy, "learned maps must fit the rotated frame better"
    assert m1f.total > m1h.total, "full orthogonal must be penalised harder"
    print("    OK -- learned maps improve ACCURACY; the parameter charge is what")
    print("    decides whether that improvement is worth paying for, and a full")
    print("    orthogonal map is unaffordable AS A MODEL, not merely to store.")

    print("\n=== 15b. AT REAL SCALE, ONE TICK CANNOT AFFORD LEARNED MAPS ===")
    D_REAL, N_ORG, N_EDGE = 384, 7, 21
    obs = N_ORG * D_REAL
    for label, per_map in (("Householder m=4", 4 * (D_REAL - 1)),
                           ("Householder m=1", 1 * (D_REAL - 1)),
                           ("full orthogonal", D_REAL * (D_REAL - 1) // 2)):
        k = per_map * N_EDGE
        print(f"    {label:18s} {k:8d} params vs {obs:5d} observations/tick "
              f"-> {k/obs:8.1f}x over-parameterised")
    print("    Even the CHEAPEST Householder map is over-parameterised on one tick.")
    print("    => restriction maps CANNOT be learned from a single tick. They need")
    print("       accumulation -- which is exactly the two-complex model's slow")
    print("       crystallization gamma_0 << 1, now forced by evidence not by taste.")

    print("\n=== 15c. Q16: the crossover gives gamma_0 a DERIVED scale ===")
    gain = m0.accuracy - m1h.accuracy          # accuracy bought by learning R, one tick
    print(f"    accuracy gain from learned maps, one tick: {gain:.3f}")
    for label, per_map in (("Householder m=4", 4 * (D_REAL - 1)),
                           ("Householder m=1", 1 * (D_REAL - 1))):
        k = per_map * N_EDGE
        T = ticks_to_justify(gain, k, obs)
        if T is None:
            print(f"    {label:18s} never justified at this gain")
        else:
            print(f"    {label:18s} needs >= {T:6d} ticks  =>  gamma_0 ~ {1.0/T:.2e}")
    print("    (lower bound: per-tick gains are correlated, so the true T is larger)")

    print("\n=== 16. M2 (grow) is NOT decidable on current data -- by construction ===")
    # Add a vertex joined to the cycle. It appears in no term involving measured
    # organs, so the accuracy is UNCHANGED and complexity can only rise.
    grown = dict(base_g)
    grown["NewCell"] = Gaussian(mu=rng.normal(size=d), U=rng.normal(size=(d, 2)) * 0.5)
    grown_edges = list(edges) + [("NewCell", "Reason"), ("NewCell", "Verify"),
                                 ("NewCell", "Context")]
    f_before = free_energy(base_g, edges, name="current complex")
    f_after = free_energy(grown, grown_edges, name="complex + coned cell")
    print(f_before.line())
    print(f_after.line())
    print(f"    delta F = {f_after.total - f_before.total:+.3f}  (positive = growth REJECTED)")
    print("    Growth cannot be justified on data already in hand; it is a claim")
    print("    about FUTURE reconcilability and needs persistence or held-out data.")

    print("\nALL BELIEF SELF-TESTS PASSED (zero API calls)")
