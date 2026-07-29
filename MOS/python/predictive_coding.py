"""
TATIANA - Predictive coding (plan 5p, mechanism (1): the learning half).

coherence.py showed the MEASURE is the precision-weighted predictive-coding free
energy  F = sum_e pi_e || R_u x_u - R_v x_v ||^2  and that INFERENCE (minimising F
over x) is sheaf diffusion. This file is the other half: LEARNING - minimising F
over the restriction maps R, which is exactly "learn the quality of the
connections" (the formal home of the connectome thesis).

THE RULE (local, Hebbian, no backprop)
--------------------------------------
For a bound pair that SHOULD agree (a verified-coherent co-activation),
    eps      = R_u x_u - R_v x_v            (prediction error at the edge)
    dR_u     = -lr * pi * eps x_u^T         (= -lr * dF/dR_u)
    dR_v     = +lr * pi * eps x_v^T         (= -lr * dF/dR_v)
This is Hebbian: the update is (error) x (presynaptic activity)^T, an outer
product, using only quantities available at that one edge. No global gradient.

WHY ORTHOGONALISE (Oja, done properly)
--------------------------------------
Raw Hebb on both maps has a trivial minimiser R_u = R_v = 0 (predict nothing,
zero error), and it also diverges. We forbid both by retracting R onto the
orthogonal group after each step (polar decomposition = nearest orthogonal
matrix). Orthogonality is ALSO the contract coherence.py's rho<=1 bound needs.
So the same constraint (a) stops collapse, (b) stops divergence, (c) keeps the
discord measure honest. One stone.

HONESTY / WHAT NOT TO DO
------------------------
* Only call update() on pairs you have REASON to believe are coherent (VerifyOp
  passed, or _low_ measured discord). Training on garbage teaches the system to
  agree on garbage - the maps would learn to hide real contradictions.
* Precision must be a REAL precision (from rho-history or coalition weight),
  never a fabricated LLM self-confidence (Groq serves no logprobs; see 5c).
* Cold start is identity => coherence.py reduces to the pre-5p measure. The maps
  earn their keep on the SLOPE, as verified pairs accumulate; day 1 they do
  nothing. Same bet as the whole project.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import numpy as np

Edge = Tuple[str, str]


def _nearest_orthogonal(M: np.ndarray) -> np.ndarray:
    """Polar factor of M: the orthogonal matrix closest to M in Frobenius norm.
    M = U S V^T  =>  nearest orthogonal = U V^T."""
    U, _, Vt = np.linalg.svd(M, full_matrices=False)
    return U @ Vt


class RestrictionMapLearner:
    """Holds and learns the per-edge restriction maps R_{v,e} of the sheaf on K.

    Edges are stored canonically (sorted) so (u,v) and (v,u) are one edge; get()
    returns the pair oriented for the key order (R_first, R_second).
    """

    def __init__(self, dim: int, learning_rate: float = 0.05, max_step: float = 0.5):
        self.dim = dim
        self.lr = learning_rate
        self.max_step = max_step   # cap on lr*precision => guaranteed monotone descent
        # edge -> (R_first, R_second); absent => identity (lazy, memory-cheap)
        self._maps: Dict[Edge, Tuple[np.ndarray, np.ndarray]] = {}

    @staticmethod
    def _key(u: str, v: str) -> Edge:
        return (u, v) if u <= v else (v, u)

    def get(self, u: str, v: str) -> Tuple[np.ndarray, np.ndarray]:
        """Return (R_u, R_v) oriented for the (u, v) argument order.
        Identity if this edge has never been trained."""
        k = self._key(u, v)
        pair = self._maps.get(k)
        if pair is None:
            eye = np.eye(self.dim)
            return eye.copy(), eye.copy()
        R_a, R_b = pair
        # stored for key order; re-orient to caller's (u, v)
        return (R_a, R_b) if (u, v) == k else (R_b, R_a)

    def as_restriction_dict(self, edges) -> Dict[Edge, Tuple[np.ndarray, np.ndarray]]:
        """Bundle current maps for coherence.coherence(restriction=...)."""
        out = {}
        for (u, v) in edges:
            out[(u, v)] = self.get(u, v)
        return out

    def error(self, u: str, v: str, x_u: np.ndarray, x_v: np.ndarray) -> np.ndarray:
        R_u, R_v = self.get(u, v)
        return R_u @ x_u - R_v @ x_v

    def update(self, u: str, v: str, x_u: np.ndarray, x_v: np.ndarray,
               precision: float = 1.0) -> float:
        """One local Hebbian step toward agreement on THIS (coherent) pair.
        Returns ||eps|| AFTER the update (so callers can watch it fall)."""
        x_u = np.asarray(x_u, dtype=float).ravel()
        x_v = np.asarray(x_v, dtype=float).ravel()
        if x_u.size != self.dim or x_v.size != self.dim:
            raise ValueError(f"dim mismatch: got {x_u.size},{x_v.size}, expected {self.dim}.")
        k = self._key(u, v)
        R_a, R_b = self.get(*k)          # oriented for key order
        xa, xb = (x_u, x_v) if (u, v) == k else (x_v, x_u)

        eps = R_a @ xa - R_b @ xb
        # NORMALISED Hebbian step: divide by presynaptic energy ||x||^2. This is
        # still local (||x||^2 is available at the node) and makes the step
        # scale-robust - stability needs lr*precision < 1 regardless of embedding
        # magnitude. Reduces to the plain rule for unit-norm embeddings (||x||=1),
        # which is what bge produces; the raw rule overshoots when ||x||^2 > 1/lr.
        na = float(xa @ xa) or 1.0
        nb = float(xb @ xb) or 1.0
        # Effective step = lr*precision. Since eps shrinks by ~(1 - eff) per step
        # (normalised rule), eff >= 1 overshoots and eff > 2 diverges. Callers may
        # legitimately pass a large precision (e.g. a coupling weight of 100), so
        # we CAP the effective step at max_step (<1) to guarantee monotone descent
        # rather than trusting the caller to keep lr*precision small.
        eff = min(self.lr * precision, self.max_step)
        R_a = R_a - eff * np.outer(eps, xa) / na
        R_b = R_b + eff * np.outer(eps, xb) / nb
        # retract to the orthogonal group (Oja): stops collapse+divergence, keeps
        # coherence.py's Anderson-Morley bound valid.
        R_a = _nearest_orthogonal(R_a)
        R_b = _nearest_orthogonal(R_b)
        self._maps[k] = (R_a, R_b)

        eps_after = R_a @ xa - R_b @ xb
        return float(np.linalg.norm(eps_after))


if __name__ == "__main__":
    rng = np.random.default_rng(1)
    d = 16

    print("=== 1. Two organs hold the SAME content in ROTATED coordinates ===")
    # They SHOULD be judged coherent, but identity maps see a big error. The
    # learner should discover maps that shrink the error while staying orthogonal.
    Q, _ = np.linalg.qr(rng.normal(size=(d, d)))     # the hidden relation x_v = Q x_u
    learner = RestrictionMapLearner(d, learning_rate=0.1)

    # error under identity, averaged over samples
    samples = [rng.normal(size=d) for _ in range(40)]
    before = np.mean([np.linalg.norm(xu - Q @ xu) for xu in samples])

    for epoch in range(60):
        for xu in samples:
            learner.update("Reason", "Search", xu, Q @ xu, precision=1.0)
    after = np.mean([np.linalg.norm(learner.error("Reason", "Search", xu, Q @ xu))
                     for xu in samples])
    print(f"    mean ||eps||:  identity {before:.3f}  ->  learned {after:.3f}")
    assert after < 0.5 * before, "learner should roughly halve the disagreement or better"

    print("\n=== 2. Learned maps stay ORTHOGONAL (contract for rho<=1) ===")
    R_u, R_v = learner.get("Reason", "Search")
    err_u = np.linalg.norm(R_u.T @ R_u - np.eye(d))
    err_v = np.linalg.norm(R_v.T @ R_v - np.eye(d))
    print(f"    ||R_u^T R_u - I|| = {err_u:.2e}   ||R_v^T R_v - I|| = {err_v:.2e}")
    assert err_u < 1e-9 and err_v < 1e-9

    print("\n=== 3. Orientation symmetry: get(u,v) and get(v,u) are transposes-of-roles ===")
    a1, b1 = learner.get("Reason", "Search")
    b2, a2 = learner.get("Search", "Reason")
    assert np.allclose(a1, a2) and np.allclose(b1, b2)
    print("    get(u,v) == swap(get(v,u))  OK")

    print("\n=== 4. Feeding coherence.py the learned maps lowers omega ===")
    from coherence import coherence
    xu = rng.normal(size=d)
    states = {"Reason": xu, "Search": Q @ xu}
    edges = [("Reason", "Search")]
    w_ident = coherence(states, edges).omega
    w_learned = coherence(states, edges,
                          restriction=learner.as_restriction_dict(edges)).omega
    print(f"    omega:  identity {w_ident:.3f}  ->  learned {w_learned:.4f}")
    assert w_learned < w_ident

    print("\n=== 5. STABILITY: a huge precision does not diverge (step is capped) ===")
    # lr*precision = 0.1*100 = 10 would diverge without the cap; must stay finite
    # and still converge.
    learner2 = RestrictionMapLearner(d, learning_rate=0.1)
    before2 = np.mean([np.linalg.norm(xu - Q @ xu) for xu in samples])
    for _ in range(80):
        for xu in samples:
            learner2.update("A", "B", xu, Q @ xu, precision=100.0)
    after2 = np.mean([np.linalg.norm(learner2.error("A", "B", xu, Q @ xu)) for xu in samples])
    print(f"    precision=100 (uncapped step would be 10x): mean ||eps|| {before2:.3f} -> {after2:.3f}")
    assert np.isfinite(after2) and after2 < before2, "capped step must converge, not blow up"

    print("\nALL PREDICTIVE-CODING SELF-TESTS PASSED")
