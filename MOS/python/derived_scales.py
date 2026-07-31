"""
TATIANA — tau_f AND delta, DERIVED. (Retracts the circularity claim of logbook 5af.)

=============================================================================
THE RETRACTION FIRST, BECAUSE IT IS THE REASON THIS FILE EXISTS
=============================================================================
Logbook 5af claimed a derived tau_f was CIRCULAR: "tau_f IS the C^2 inner
product, and hodge_split uses that inner product to compute the curl projection,
so deriving tau_f from the residual of eta defines the inner product from the
quantity it measures." It further claimed adopting a derived tau_f "would
invalidate E5".

**Both claims are false.** Charbel pushed back and he was right.

With inner products W_0, W_1, W_2 on C^0, C^1, C^2, the adjoint of
delta^1 : C^1 -> C^2 is (delta^1)* = W_1^{-1}(delta^1)^T W_2, so the curl space is

    im( W_1^{-1} (delta^1)^T W_2 )
      = W_1^{-1}(delta^1)^T . im(W_2)
      = W_1^{-1}(delta^1)^T . C^2            (W_2 is positive-definite, hence ONTO)
      = im( W_1^{-1}(delta^1)^T )

**An invertible map does not change an image.** So the curl SUBSPACE -- and
therefore the orthogonal projection onto it, and therefore the entire Hodge
split of eta into grad (+) curl (+) harmonic -- is INDEPENDENT of W_2 = tau.
Verified numerically on the E5 complex: ||P(W_2=I) - P(W_2=random)||_F ~ 5e-16
across trials.

Two consequences:
  * There is no circularity. tau_f may be derived from the circulation
    (delta^1 eta)_f without ever feeding back into how that circulation is split.
  * E5's numbers do not move. hodge.py's `A = (d1 / w).T` (i.e. W_2 = I) computes
    the same projection any other positive W_2 would, so nothing in 5x is re-based.

Where tau_f DOES matter, and why it is still worth deriving: the magnitudes of
the 1-Laplacian Delta_1 = delta^0(delta^0)* + (delta^1)*delta^1 (hence its
spectrum), and Forman's F_MOS via the coface term sum_f pi_e^2 / tau_f.

=============================================================================
1. tau_f  —  THE SAME DERIVATION AS pi_e, ONE DIMENSION UP
=============================================================================
edge_precision.py derives pi_e as the precision of the edge prediction error,
pi_e = 1/Var(eps_e). The 2-cell weight is the same construction on the next
coboundary: tau_f is the precision of the TRIANGLE CIRCULATION

    (delta^1 eta)_f = eta_ab + eta_bc + eta_ca      (signed sum around f)

If the edge cochain values are independent with Var(eta_e) = 1/pi_e, then the
variance of the signed sum is the sum of the variances (signs square away):

    Var( (delta^1 eta)_f ) = sum_{e in f} 1 / pi_e

so the precision of the total circulation is 1 / sum_e (1/pi_e).

**NORMALISATION, STATED AS A CHOICE.** We take tau_f to be the precision of the
MEAN circulation per edge rather than of the total, i.e. multiply by |f| = 3:

    tau_f = |f| / sum_{e in f} (1 / pi_e)   =   HARMONIC MEAN of {pi_e : e in f}

Two reasons, and the second is checkable:
  (a) it keeps tau dimensionally comparable to pi (both are "a precision per
      edge"), which is what makes pi_e^2/tau_f in F_MOS a pure number;
  (b) **exact day-one degradation**: all pi_e = 1  =>  tau_f = 1, and F_MOS
      collapses to the combinatorial 4 - deg u - deg v + 3m of logbook 5ac.
      Without the |f| factor it would not, and the derived curvature would
      silently disagree with the derivation that justified it.

The harmonic mean is also the right *kind* of average for precisions: it is the
arithmetic mean of the variances, inverted.

=============================================================================
2. delta  —  THE CONCEPT-IDENTITY SCALE, FROM THE DATA, WITHOUT HAND LABELS
=============================================================================
5z defines delta as "the semantic distance beyond which two concepts stop being
one thing that moved and become two things", and V2/E14 planned to calibrate it
by SWEEPING over ~50 hand-labelled pairs. That needs labels MOS does not have.

But the organ structure is already weak supervision. Two concepts in the SAME
organ are evidence of "one thing"; two in DIFFERENT organs are evidence of "two
things". So the within- and between-organ distance distributions bracket delta,
and the honest estimator is the scale that best separates them.

We take the **equal-error point**: the distance d* at which

    P(within  > d*)  =  P(between <= d*)

i.e. false-splits equal false-merges. This is parameter-free -- no threshold is
chosen, it is READ OFF the crossing -- and it degrades gracefully: if the two
distributions overlap completely the crossing still exists but the reported
separability collapses to chance, which is exactly the signal that delta is not
identifiable on this corpus. We report that separability alongside delta, so a
meaningless delta cannot be quoted as a meaningful one.

delta then follows from 5z's saturation convention pi*delta = d*:

    delta = d* / pi

**This does not replace E14.** A sweep against real hand labels remains the
stronger evidence, and the SENSITIVITY CURVE (never a fitted point) is still what
should be published. What this gives is a principled starting value that is
derived from data rather than hand-set, and a way to monitor drift.
"""

from __future__ import annotations

import math
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np

Vertex = str
Edge = Tuple[Vertex, Vertex]
Triangle = Tuple[Vertex, Vertex, Vertex]


# ===========================================================================
# 1. tau_f
# ===========================================================================

def triangle_edges(f: Triangle) -> List[Edge]:
    a, b, c = f
    return [(a, b), (b, c), (a, c)]


def _pi_lookup(pi: Mapping[Edge, float], e: Edge) -> float:
    if e in pi:
        return float(pi[e])
    rev = (e[1], e[0])
    if rev in pi:
        return float(pi[rev])
    raise KeyError(
        f"No precision for edge {e}. Refusing to default to 1 -- a missing "
        "precision is a missing measurement (same rule as coherence.py).")


def tau(triangles: Iterable[Triangle],
        pi: Mapping[Edge, float]) -> Dict[Triangle, float]:
    """tau_f = harmonic mean of the precisions of f's edges.

    = |f| / sum_{e in f} (1/pi_e), the precision of the MEAN circulation.
    Reduces to 1 when every pi_e = 1, so F_MOS degrades exactly to the
    combinatorial augmented Forman curvature.
    """
    out: Dict[Triangle, float] = {}
    for f in triangles:
        edges = triangle_edges(f)
        inv = 0.0
        for e in edges:
            p = _pi_lookup(pi, e)
            if p <= 0.0:
                raise ValueError(
                    f"Precision {p} on edge {e} of triangle {f} must be > 0; a "
                    "zero-precision edge has infinite variance and the "
                    "circulation is undefined.")
            inv += 1.0 / p
        out[tuple(f)] = len(edges) / inv
    return out


def forman_mos(edge: Edge,
               edges: Sequence[Edge],
               triangles: Sequence[Triangle],
               pi: Mapping[Edge, float],
               nu: Mapping[Vertex, float],
               tau_f: Optional[Mapping[Triangle, float]] = None) -> float:
    """F_MOS(e), logbook 5ac, with tau_f derived by default.

        F(e) = pi_e^2 * sum_{f > e} 1/tau_f
             + (nu_u + nu_v)
             - sum_{e' || e} nu_{shared vertex} * sqrt(pi_e / pi_e')

    where e' || e means e' shares a VERTEX with e but does NOT share a triangle
    with it (Forman's "not both" clause -- the source of the coefficient 3 in the
    unit-weight case, see 5ac).
    """
    u, v = edge
    p_e = _pi_lookup(pi, edge)
    if tau_f is None:
        tau_f = tau(triangles, pi)

    key = frozenset(edge)
    cofaces = [f for f in triangles if key <= frozenset(f)]
    coface_term = p_e * p_e * sum(1.0 / tau_f[tuple(f)] for f in cofaces)

    # Edges sharing a triangle WITH e are excluded from the penalty.
    excluded = set()
    for f in cofaces:
        for e2 in triangle_edges(f):
            excluded.add(frozenset(e2))

    penalty = 0.0
    for e2 in edges:
        k2 = frozenset(e2)
        if k2 == key or k2 in excluded:
            continue
        shared = key & k2
        if len(shared) != 1:
            continue                      # not a parallel neighbour
        w = next(iter(shared))
        penalty += nu[w] * math.sqrt(p_e / _pi_lookup(pi, e2))

    return coface_term + (nu[u] + nu[v]) - penalty


# ===========================================================================
# 2. delta
# ===========================================================================

class DeltaEstimate:
    """A derived delta, reported together with how much to trust it."""

    def __init__(self, delta: float, d_star: float, separability: float,
                 n_within: int, n_between: int):
        self.delta = delta
        self.d_star = d_star
        self.separability = separability   # 1 - (FP+FN)/2 at d*; 0.5 = chance
        self.n_within = n_within
        self.n_between = n_between

    @property
    def identifiable(self) -> bool:
        """Below ~0.6 the two distributions barely separate and delta is noise."""
        return self.separability >= 0.6

    def __repr__(self) -> str:
        flag = "" if self.identifiable else "  [NOT IDENTIFIABLE]"
        return (f"DeltaEstimate(delta={self.delta:.4f}, d*={self.d_star:.4f}, "
                f"separability={self.separability:.3f}, "
                f"n_within={self.n_within}, n_between={self.n_between}){flag}")


def derive_delta(within: Sequence[float],
                 between: Sequence[float],
                 grid: int = 512) -> DeltaEstimate:
    """delta from the equal-error crossing of the two distance distributions.

    within  : distances between concepts KNOWN to belong together (same organ)
    between : distances between concepts KNOWN to differ (different organs)

    Returns d* where P(within > d*) = P(between <= d*), and delta = d*/pi from
    5z's saturation convention. No threshold is chosen; it is read off.
    """
    w = np.asarray(list(within), dtype=float)
    b = np.asarray(list(between), dtype=float)
    if w.size == 0 or b.size == 0:
        raise ValueError("need both within- and between-organ distances")

    lo = float(min(w.min(), b.min()))
    hi = float(max(w.max(), b.max()))
    if hi <= lo:
        raise ValueError("degenerate distance distribution")

    xs = np.linspace(lo, hi, grid)
    # false split: a same-thing pair judged different; false merge: the converse
    fs = np.array([(w > x).mean() for x in xs])
    fm = np.array([(b <= x).mean() for x in xs])
    i = int(np.argmin(np.abs(fs - fm)))
    d_star = float(xs[i])
    err = 0.5 * (fs[i] + fm[i])
    return DeltaEstimate(delta=d_star / math.pi, d_star=d_star,
                         separability=float(1.0 - err),
                         n_within=int(w.size), n_between=int(b.size))


# ===========================================================================
# Self-tests. Run: python derived_scales.py
# ===========================================================================

def _main() -> None:
    ok = 0

    def check(name: str, cond: bool) -> None:
        nonlocal ok
        assert cond, f"FAILED: {name}"
        ok += 1
        print(f"  [ok] {name}")

    print("=== 0. THE RETRACTION: the Hodge split is INDEPENDENT of tau ===")
    from hodge import e5_complex
    cx = e5_complex()
    d1 = cx.delta1()
    E, F = len(cx.edges), len(cx.triangles)
    rng = np.random.default_rng(3)
    w1 = rng.uniform(0.5, 3.0, size=E)

    def projector(M):
        Q, _ = np.linalg.qr(M)
        return Q @ Q.T

    P_I = projector((d1 / w1).T)
    worst = 0.0
    for _ in range(6):
        W2 = np.diag(rng.uniform(0.05, 20.0, size=F))
        worst = max(worst, float(np.linalg.norm(P_I - projector(((W2 @ d1) / w1).T))))
    check(f"curl projector is tau-independent (worst dev {worst:.2e})", worst < 1e-12)
    print("      => no circularity, and E5's numbers do not move.\n")

    print("=== 1. tau_f ===")
    tris = [("A", "B", "C")]
    unit = {("A", "B"): 1.0, ("B", "C"): 1.0, ("A", "C"): 1.0}
    t = tau(tris, unit)
    check("all pi_e = 1  =>  tau_f = 1 (exact day-one degradation)",
          abs(t[("A", "B", "C")] - 1.0) < 1e-15)

    t2 = tau(tris, {("A", "B"): 2.0, ("B", "C"): 2.0, ("A", "C"): 2.0})
    check("uniform pi = p  =>  tau_f = p", abs(t2[("A", "B", "C")] - 2.0) < 1e-15)

    t3 = tau(tris, {("A", "B"): 1e-6, ("B", "C"): 10.0, ("A", "C"): 10.0})
    check("harmonic mean is dominated by the WORST edge (as a variance sum must be)",
          t3[("A", "B", "C")] < 1e-5)

    check("tau is orientation-independent",
          abs(tau([("B", "A", "C")], unit)[("B", "A", "C")] - 1.0) < 1e-15)

    for name, fn in [("a missing precision is refused",
                      lambda: tau(tris, {("A", "B"): 1.0})),
                     ("a zero precision is refused",
                      lambda: tau(tris, {("A", "B"): 0.0, ("B", "C"): 1.0,
                                         ("A", "C"): 1.0}))]:
        try:
            fn()
            raise AssertionError(f"FAILED: {name}")
        except (KeyError, ValueError):
            ok += 1
            print(f"  [ok] {name}")

    print("\n=== 2. F_MOS with derived tau ===")
    # The 5ac configuration: 4 organs, 5 edges, 1 filled triangle.
    V = ["A", "B", "C", "D"]
    E5 = [("A", "B"), ("B", "C"), ("A", "C"), ("C", "D"), ("A", "D")]
    T = [("A", "B", "C")]
    pi1 = {e: 1.0 for e in E5}
    nu1 = {v: 1.0 for v in V}

    # deg A = 3 (B, C, D), deg B = 2 (A, C); m = 1 triangle on AB
    # combinatorial: 4 - 3 - 2 + 3*1 = 2
    f_ab = forman_mos(("A", "B"), E5, T, pi1, nu1)
    check(f"unit weights reproduce 4 - deg u - deg v + 3m exactly (AB: {f_ab:.6f} == 2)",
          abs(f_ab - 2.0) < 1e-12)

    # edge CD: deg C = 3, deg D = 2, m = 0  =>  4 - 3 - 2 + 0 = -1
    f_cd = forman_mos(("C", "D"), E5, T, pi1, nu1)
    check(f"an UNFILLED edge is negatively curved (CD: {f_cd:.6f} == -1)",
          abs(f_cd - (-1.0)) < 1e-12)
    check("filled edge is more positively curved than unfilled", f_ab > f_cd)

    # Sign behaviour: a filled neighbourhood should stay above an unfilled one
    # even once the derived tau is in play with non-uniform precisions.
    pi_v = {("A", "B"): 3.0, ("B", "C"): 2.0, ("A", "C"): 2.5,
            ("C", "D"): 1.0, ("A", "D"): 1.0}
    check("ordering survives non-uniform precisions",
          forman_mos(("A", "B"), E5, T, pi_v, nu1) >
          forman_mos(("C", "D"), E5, T, pi_v, nu1))

    print("\n=== 3. delta ===")
    rng2 = np.random.default_rng(11)
    within = rng2.normal(0.30, 0.06, size=400)
    between = rng2.normal(0.90, 0.12, size=400)
    est = derive_delta(within, between)
    check(f"well-separated data gives an identifiable delta ({est!r})",
          est.identifiable and 0.4 < est.d_star < 0.8)
    check("delta = d*/pi (5z saturation convention)",
          abs(est.delta - est.d_star / math.pi) < 1e-12)

    overlap = derive_delta(rng2.normal(0.5, 0.2, size=400),
                           rng2.normal(0.5, 0.2, size=400))
    check(f"fully overlapping data is reported NOT identifiable "
          f"(sep={overlap.separability:.3f})", not overlap.identifiable)
    check("i.e. an unusable delta cannot be quoted as a usable one",
          overlap.separability < 0.6)

    print(f"\nAll {ok} derived-scale tests passed.")


if __name__ == "__main__":
    _main()
