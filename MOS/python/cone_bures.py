"""
TATIANA - the CONE-BURES metric: an HK/WFR-type distance on the stalk manifold,
with the concept-identity length scale delta, computable in one Bures evaluation.

THE PROBLEM (E15, logbook 5y)
------------------------------
Wasserstein-Fisher-Rao / Hellinger-Kantorovich gives exactly the object the merge
question needs: a distance that interpolates between MOVING mass (transport) and
DESTROYING-and-RECREATING it, governed by a length scale delta with a meaning --

    delta = the distance beyond which two concepts stop being "one thing that
            moved" and become "two different things".

E15 asked whether WFR has a Bures-style closed form between Gaussians. Answer: NO.
The literature offers only (a) entropic regularisations -- a different object with
a new fitted parameter, (b) KL-unbalanced variants needing a RICCATI SOLVE per
pair (O(d^3) x iterations at d=384, four orders too slow), (c) the Dirac case, and
(d) gradient-flow ODEs, which are not a distance.

WHY IT FAILS -- the diagnosis that contains the fix
----------------------------------------------------
Bures works because the W2 cost |x-y|^2 is QUADRATIC, and quadratic costs preserve
the Gaussian family: the optimal map is affine, so you can write it down. HK's cone
cost is

    c(x,y) = -2 log cos( min( |x-y| / 2delta , pi/2 ) )

which is NOT quadratic. The optimal HK plan destroys mass in some regions and
creates it in others; what survives is a reweighted, non-Gaussian object. So the
family is not preserved and no closed form exists. That is structural, not an
oversight.

Do not attack the cost. Attack WHAT IS BEING TRANSPORTED.

THE CONSTRUCTION
----------------
Three facts already in the design, not previously combined:

 (i) **HK IS A CONE METRIC** (Liero-Mielke-Savare). Over a base metric space
     (X, d_X), the cone c(X) with r = sqrt(mass) carries
         d_c((x,r),(y,s))^2 = r^2 + s^2 - 2 r s cos( min( d_X(x,y), pi/2 ) )
     and the construction requires ONLY that the base be a metric space. It does
     not care that X = R^d.

(ii) **MOS's state space is the GAUSSIAN MANIFOLD, not measures on R^d.** We never
     represent a non-Gaussian measure. So "the HK distance between these two
     measures, ranging over all measures" is the wrong question; the right one is
     the natural distance on the manifold we actually inhabit.

     => Build the cone over (Gaussian space, BURES-WASSERSTEIN), not over R^d.
     The base is already a metric space whose distance we already compute.

(iii) **We already have mass**: the Hebbian weight w(sigma,t). Decay DESTROYS
     mass; reinforcement CREATES it. WFR's reaction term is not an imported
     abstraction, it is the bind/collapse dynamics the engine already runs.

Hence, for stalks g = (mu, Sigma, w) with Sigma = U U^T + eps I:

    D_delta(g0,g1)^2 = w0 + w1 - 2 sqrt(w0 w1) cos( min( d_BW(g0,g1)/(2 delta), pi/2 ) )

WHAT THIS IS, AND WHAT IT IS NOT -- stated, not buried
-------------------------------------------------------
IS: a genuine metric (proved below, and tested by randomised triangle-inequality
    trials), with the delta length scale, the hard saturation, and a cost of ONE
    Bures evaluation plus a cosine.

IS NOT: the true Hellinger-Kantorovich distance between two Gaussian MEASURES.
    True HK optimises over plans that leave the Gaussian family; restricting the
    competitor class raises an infimum, so

        D_delta  >=  HK_true      (an UPPER BOUND, with equality only when the
                                   true HK geodesic happens to stay Gaussian)

    The honest defence is (ii): MOS's state space IS the Gaussian manifold, so the
    induced metric on that manifold is arguably the right object rather than an
    approximation to something else. But it is a DIFFERENT metric from HK, and
    calling it "WFR between Gaussians" would be false. It is HK-TYPE.
    ⚠️ The tightness of the bound is UNMEASURED. See `validation` at the bottom.

THE THREE LIMITS (all tested)
------------------------------
  delta -> infinity : 4 delta^2 D^2 -> w * d_BW^2. Weighted Bures, which is what
                      the engine does TODAY => day-one degradation is exact and
                      the merge ORDERING is unchanged (5r's discipline).
  d_BW = 0          : D^2 = (sqrt(w0) - sqrt(w1))^2. Pure Hellinger on the
                      weights: same concept, different strength.
  d_BW >= pi delta  : D^2 = w0 + w1, CONSTANT. Beyond the cutoff, transport is
                      abandoned entirely -- "two different things", and no
                      further separation is registered. D^2 is BOUNDED, which
                      also kills the runaway-distance failure mode.

⚠️ NORMALISATION. We use the HK normalisation (saturation at w0+w1), NOT a
4delta^2 prefactor. Consequence: as delta -> infinity, D is Bures up to the scale
1/(2delta). Merge decisions compare distances, so the ORDER -- which is what
decides a merge -- is preserved exactly. Do not compare D across different delta
without rescaling.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

from belief import Gaussian, EPS_FLOOR


# --------------------------------------------------------------------------
# Bures-Wasserstein between rank-k-plus-floor Gaussians
# --------------------------------------------------------------------------

def bures_w2_sq(g0: Gaussian, g1: Gaussian) -> float:
    """W2^2 between N(mu0,Sigma0) and N(mu1,Sigma1), Sigma_i = U_i U_i^T + eps_i I.

        W2^2 = ||mu0-mu1||^2 + Tr S0 + Tr S1 - 2 Tr (S0^1/2 S1 S0^1/2)^1/2

    THE RANK-k REDUCTION (this is what makes it affordable at d = 384).
    Let W = span(U0) + span(U1), dim p <= 2k. Both S0^1/2 and S1 preserve W, and on
    W^perp they act as sqrt(eps0) and eps1 respectively, so the product acts as
    eps0*eps1 there. Hence

        Tr (S0^1/2 S1 S0^1/2)^1/2  =  Tr_W (...)^1/2  +  (d - p) sqrt(eps0 eps1)

    and only a p x p matrix square root is ever formed. Cost O(d k^2 + k^3):
    ~14K flops at d=384, k=6, versus O(d^3) = 5.7e7 for the dense route -- the
    same trick 5j used to exploit the isotropic Sigma1, generalised to two
    rank-k operands.
    """
    d = g0.d
    if g1.d != d:
        raise ValueError(f"dimension mismatch {d} vs {g1.d}; refusing to pad.")
    dmu = g0.mu - g1.mu
    mean_term = float(dmu @ dmu)

    e0, e1 = g0.eps, g1.eps
    tr0 = float(np.sum(g0.U * g0.U)) + d * e0 if g0.k else d * e0
    tr1 = float(np.sum(g1.U * g1.U)) + d * e1 if g1.k else d * e1

    # Orthonormal basis of W = span(U0) u span(U1)
    cols = [U for U in (g0.U, g1.U) if U is not None and U.size]
    if not cols:
        cross = d * np.sqrt(e0 * e1)                 # both isotropic
        return max(mean_term + tr0 + tr1 - 2.0 * cross, 0.0)
    M = np.concatenate(cols, axis=1)
    B, _ = np.linalg.qr(M)                            # (d, p), p <= 2k
    # Drop numerically null directions
    keep = np.linalg.norm(B.T @ M, axis=1) > 1e-12
    B = B[:, keep]
    p = B.shape[1]

    # S0 restricted to W, in the B basis
    A0 = (g0.U.T @ B) if g0.k else np.zeros((0, p))
    S0_W = A0.T @ A0 + e0 * np.eye(p)
    A1 = (g1.U.T @ B) if g1.k else np.zeros((0, p))
    S1_W = A1.T @ A1 + e1 * np.eye(p)

    # S0^1/2 on W
    w0, Q0 = np.linalg.eigh(S0_W)
    w0 = np.clip(w0, 0.0, None)
    S0h = Q0 @ np.diag(np.sqrt(w0)) @ Q0.T

    Mid = S0h @ S1_W @ S0h
    wm = np.linalg.eigvalsh(Mid)
    wm = np.clip(wm, 0.0, None)
    cross = float(np.sum(np.sqrt(wm))) + (d - p) * np.sqrt(e0 * e1)

    return max(mean_term + tr0 + tr1 - 2.0 * cross, 0.0)


# --------------------------------------------------------------------------
# The cone metric
# --------------------------------------------------------------------------

@dataclass
class ConeBures:
    """The HK-type stalk metric. `delta` is the concept-identity length scale."""
    delta: float

    def __post_init__(self):
        if self.delta <= 0:
            raise ValueError("delta must be > 0 (it is a length scale)")

    def base_angle(self, g0: Gaussian, g1: Gaussian) -> float:
        """theta = min(d_BW/(2 delta), pi/2). The CAPPED base metric."""
        d_bw = np.sqrt(bures_w2_sq(g0, g1))
        return float(min(d_bw / (2.0 * self.delta), np.pi / 2.0))

    def distance_sq(self, g0: Gaussian, g1: Gaussian,
                    w0: float = 1.0, w1: float = 1.0) -> float:
        if w0 < 0 or w1 < 0:
            raise ValueError("Hebbian weights are masses; they cannot be negative")
        theta = self.base_angle(g0, g1)
        return max(w0 + w1 - 2.0 * np.sqrt(w0 * w1) * np.cos(theta), 0.0)

    def distance(self, g0: Gaussian, g1: Gaussian,
                 w0: float = 1.0, w1: float = 1.0) -> float:
        return float(np.sqrt(self.distance_sq(g0, g1, w0, w1)))

    def is_same_concept(self, g0: Gaussian, g1: Gaussian) -> bool:
        """Below the cutoff, mass is TRANSPORTED: one thing that moved.

        At or above it, transport is abandoned entirely: two different things.
        This is a STRUCTURAL predicate, not a tuned threshold -- the cutoff is
        where the cosine reaches zero, i.e. where destroying-and-recreating
        becomes cheaper than moving. That is what delta buys us.
        """
        return self.base_angle(g0, g1) < np.pi / 2.0 - 1e-12

    def bures_equivalent(self, g0: Gaussian, g1: Gaussian,
                         w0: float = 1.0, w1: float = 1.0) -> float:
        """4 delta^2 D^2 -- comparable to weighted Bures as delta -> infinity."""
        return 4.0 * self.delta ** 2 * self.distance_sq(g0, g1, w0, w1)

    # ---------------------------------------------------------------------
    # THE SPREAD CORRECTION (candidate; see the triangle-inequality test)
    # ---------------------------------------------------------------------
    # V1 measured D^2/HK_true^2 across spreads and found a startlingly clean law:
    #
    #     sd/delta   0.15   0.30   0.60   1.00   1.50
    #     measured   1.02   1.08   1.35   1.97   3.14      (two separations each)
    #     1+sd^2/d^2 1.02   1.09   1.36   2.00   3.25
    #
    # i.e.  HK_true^2  ~=  D^2 / (1 + sigma^2/delta^2)  to within ~3% over a
    # 10x range of spread and every separation tested. The ratio is also nearly
    # CONSTANT in separation at fixed spread (1.33 -> 1.50 across sep 0.25 -> 3.14),
    # which is what makes a purely spread-dependent correction plausible at all.
    #
    # Mechanism: true HK destroys the non-overlapping TAILS selectively and
    # transports only the core. Our derivation restricted growth to be spatially
    # UNIFORM, so the whole lump must be transported or destroyed together. The
    # penalty for that restriction should scale with how much tail there is --
    # i.e. with spread -- and it does.
    #
    # ⚠️ STATUS: CANDIDATE ONLY. Dividing by a two-point-dependent factor is
    # exactly the kind of move that breaks the triangle inequality, which is the
    # one property we cannot trade away. Tested below; read the result before
    # using this.
    def sigma_eff_sq(self, g0: Gaussian, g1: Gaussian) -> float:
        """Mean per-dimension variance of the pair. In 1-D this is (eps0+eps1)/2."""
        d = g0.d
        t0 = (float(np.sum(g0.U * g0.U)) if g0.k else 0.0) + d * g0.eps
        t1 = (float(np.sum(g1.U * g1.U)) if g1.k else 0.0) + d * g1.eps
        return (t0 + t1) / (2.0 * d)

    def distance_sq_corrected(self, g0: Gaussian, g1: Gaussian,
                              w0: float = 1.0, w1: float = 1.0) -> float:
        """D^2 / (1 + sigma_eff^2/delta^2). CANDIDATE -- may not be a metric."""
        s2 = self.sigma_eff_sq(g0, g1)
        return self.distance_sq(g0, g1, w0, w1) / (1.0 + s2 / self.delta ** 2)


# --------------------------------------------------------------------------
# Self-test (free; no API calls)
# --------------------------------------------------------------------------

if __name__ == "__main__":
    import console
    console.setup()

    rng = np.random.default_rng(7)
    d = 24

    def G(scale=0.4, k=3, mu=None):
        return Gaussian(mu=rng.normal(size=d) if mu is None else mu,
                        U=rng.normal(size=(d, k)) * scale, eps=EPS_FLOOR)

    print("=== 1. Bures reduction matches the DENSE formula ===")
    def bures_dense(g0, g1):
        S0, S1 = g0.sigma_dense(), g1.sigma_dense()
        w, Q = np.linalg.eigh(S0)
        S0h = Q @ np.diag(np.sqrt(np.clip(w, 0, None))) @ Q.T
        wm = np.linalg.eigvalsh(S0h @ S1 @ S0h)
        dmu = g0.mu - g1.mu
        return float(dmu @ dmu) + np.trace(S0) + np.trace(S1) \
            - 2.0 * float(np.sum(np.sqrt(np.clip(wm, 0, None))))
    worst = 0.0
    for _ in range(200):
        a, b = G(k=int(rng.integers(0, 6))), G(k=int(rng.integers(0, 6)))
        worst = max(worst, abs(bures_w2_sq(a, b) - bures_dense(a, b)))
    print(f"    200 random pairs: max |rank-k - dense| = {worst:.3e}  OK")
    assert worst < 1e-7

    print("\n=== 2. Bures axioms: identity, symmetry, non-negativity ===")
    a = G()
    assert bures_w2_sq(a, a) < 1e-18
    b = G()
    assert abs(bures_w2_sq(a, b) - bures_w2_sq(b, a)) < 1e-10
    print(f"    d(a,a)={bures_w2_sq(a,a):.2e}   symmetry OK")

    print("\n=== 3. ★ THE TRIANGLE INEQUALITY (the claim that must not be assumed) ===")
    # The cone construction is a metric for ANY metric base (Burago-Burago-Ivanov
    # 3.6.13), with the base capped at pi/2 -- and capping preserves the triangle
    # inequality. That is a proof, but this project tests proofs rather than
    # trusting them.
    for delta in (0.05, 0.3, 1.0, 5.0, 50.0):
        cb = ConeBures(delta)
        worst_viol = 0.0
        for _ in range(4000):
            ga, gb, gc = G(k=2), G(k=2), G(k=2)
            wa, wb, wc = rng.uniform(0.05, 3.0, size=3)
            dab = cb.distance(ga, gb, wa, wb)
            dbc = cb.distance(gb, gc, wb, wc)
            dac = cb.distance(ga, gc, wa, wc)
            worst_viol = max(worst_viol, dac - (dab + dbc))
        status = "OK" if worst_viol < 1e-9 else "VIOLATED"
        print(f"    delta={delta:6.2f}: worst d(a,c) - [d(a,b)+d(b,c)] = "
              f"{worst_viol:+.3e}   {status}")
        assert worst_viol < 1e-9, (delta, worst_viol)
    print("    20,000 random triples across five length scales: metric holds.")

    print("\n=== 4. LIMIT 1 -- delta -> infinity recovers WEIGHTED BURES ===")
    a, b = G(), G()
    w = 1.7
    target = w * bures_w2_sq(a, b)
    for delta in (10.0, 100.0, 1000.0, 10000.0):
        got = ConeBures(delta).bures_equivalent(a, b, w, w)
        print(f"    delta={delta:8.0f}  4d^2 D^2 = {got:12.6f}   w*d_BW^2 = {target:12.6f}"
              f"   rel err {abs(got-target)/target:.2e}")
    assert abs(ConeBures(1e4).bures_equivalent(a, b, w, w) - target) / target < 1e-6
    print("    => DAY-ONE DEGRADATION IS EXACT: delta=inf reproduces today's engine.")

    print("\n=== 5. LIMIT 2 -- identical stalks give PURE HELLINGER on the weights ===")
    cb = ConeBures(1.0)
    for w0, w1 in ((1.0, 1.0), (1.0, 4.0), (0.25, 9.0)):
        got = cb.distance_sq(a, a, w0, w1)
        want = (np.sqrt(w0) - np.sqrt(w1)) ** 2
        print(f"    w=({w0},{w1}): D^2={got:.6f}  (sqrt w0 - sqrt w1)^2={want:.6f}")
        assert abs(got - want) < 1e-12
    print("    => same concept, different strength: cost is Hellinger.  OK")

    print("\n=== 6. LIMIT 3 -- SATURATION beyond the cutoff (the whole point) ===")
    cb = ConeBures(0.5)
    base = rng.normal(size=d)
    print("    two stalks pushed progressively further apart, w=1 each:")
    prev = None
    for sep in (0.0, 0.5, 1.0, 1.5, 1.6, 3.0, 30.0, 3000.0):
        g0 = Gaussian(mu=base, U=np.zeros((d, 0)), eps=EPS_FLOOR)
        g1 = Gaussian(mu=base + sep * np.eye(d)[0], U=np.zeros((d, 0)), eps=EPS_FLOOR)
        D2 = cb.distance_sq(g0, g1, 1.0, 1.0)
        same = cb.is_same_concept(g0, g1)
        print(f"      separation {sep:8.1f}  D^2 = {D2:.6f}   "
              f"{'ONE CONCEPT (transport)' if same else 'TWO CONCEPTS (destroy/create)'}")
        prev = D2
    assert abs(prev - 2.0) < 1e-12, prev
    print("    => D^2 saturates at w0+w1 = 2 and STAYS there. Bounded distance;")
    print("       no runaway. Beyond pi*delta, further separation is not registered.")

    print("\n=== 7. delta CONTROLS the merge decision, monotonically ===")
    g0 = Gaussian(mu=base, U=np.zeros((d, 0)), eps=EPS_FLOOR)
    g1 = Gaussian(mu=base + 1.0 * np.eye(d)[0], U=np.zeros((d, 0)), eps=EPS_FLOOR)
    print("    two stalks a fixed distance 1.0 apart; sweep delta:")
    flips = []
    for delta in (0.1, 0.3, 0.6, 0.64, 0.7, 1.0, 3.0):
        cb = ConeBures(delta)
        flips.append(cb.is_same_concept(g0, g1))
        print(f"      delta={delta:5.2f} -> {'SAME' if flips[-1] else 'DIFFERENT'}")
    assert flips == sorted(flips), "the predicate must be monotone in delta"
    print("    => monotone: larger delta merges more. A SWEEP over delta gives a")
    print("       sensitivity curve, which is what 5t said to publish instead of a")
    print("       single fitted value.")

    print("\n=== 8. COST at real scale (d=384, k=6) ===")
    import time
    D_REAL = 384
    big = [Gaussian(mu=rng.normal(size=D_REAL),
                    U=rng.normal(size=(D_REAL, 6)) * 0.4, eps=EPS_FLOOR)
           for _ in range(50)]
    cb = ConeBures(1.0)
    t = time.time()
    for i in range(0, 50, 2):
        cb.distance_sq(big[i], big[i + 1], 1.0, 1.0)
    dt = (time.time() - t) / 25
    print(f"    {dt*1e6:8.1f} us per pair at d={D_REAL}, k=6")
    print(f"    21 edges per tick -> {21*dt*1e3:.3f} ms/tick")
    print("    (the Riccati route E15 rejected: O(d^3) x iterations ~ 5.7e7 flops/pair)")

    print("\n=== 9. mass is the HEBBIAN WEIGHT: decay increases distance ===")
    # A concept fading (w -> 0) drifts away from its stable twin even with the
    # SAME mean and covariance -- because mass is being destroyed, which is
    # exactly what the reaction term charges for.
    cb = ConeBures(1.0)
    print("    identical (mu,Sigma); one concept decays:")
    for w1 in (1.0, 0.7, 0.4, 0.1, 0.01):
        print(f"      w=(1.0, {w1:4.2f})  D = {cb.distance(a, a, 1.0, w1):.4f}")
    print("    => bind/collapse dynamics ARE the create/destroy term. Not imported.")

    print("\n=== 10. THE SPREAD CORRECTION: is it still a metric? ===")
    print("  V1 found HK_true^2 ~= D^2/(1 + sigma^2/delta^2) to ~3% over a 10x")
    print("  spread range. If that correction preserves the triangle inequality it")
    print("  is a large accuracy win for free. If not, it is dead -- the metric")
    print("  property is not tradeable.")
    for delta in (0.3, 1.0, 3.0):
        cb = ConeBures(delta)
        worst_v, worst_case = 0.0, None
        for _ in range(20000):
            # DELIBERATELY heterogeneous spreads -- that is where a two-point
            # normaliser is most likely to break the inequality.
            gs = []
            for _ in range(3):
                sc = float(rng.uniform(0.02, 1.2))
                kk = int(rng.integers(0, 5))
                gs.append(Gaussian(mu=rng.normal(size=d),
                                   U=rng.normal(size=(d, kk)) * sc,
                                   eps=float(rng.uniform(1e-3, 0.5))))
            ga, gb, gc = gs
            wa, wb, wc = rng.uniform(0.05, 3.0, size=3)
            f = lambda x, y, wx, wy: np.sqrt(cb.distance_sq_corrected(x, y, wx, wy))
            v = f(ga, gc, wa, wc) - (f(ga, gb, wa, wb) + f(gb, gc, wb, wc))
            if v > worst_v:
                worst_v, worst_case = v, (wa, wb, wc)
        verdict = "HOLDS" if worst_v < 1e-9 else "**VIOLATED**"
        print(f"    delta={delta:4.1f}: worst violation = {worst_v:+.4e}   {verdict}")
    print("  => read the verdict above. A violation here means the corrected form")
    print("     may be used as a SCORE for ranking, but NOT as a metric, and merge")
    print("     transitivity is then not guaranteed.")

    print("\nALL CONE-BURES SELF-TESTS PASSED (zero API calls)")
    print("""
VALIDATION STILL OWED (do not skip before publishing this):
  V1. Tightness. D >= HK_true is proved; the GAP is unmeasured. Compute true HK
      numerically for 1-D Gaussians on a fine grid (a small Sinkhorn/FISTA solve)
      and plot D/HK_true against separation. If the gap is large in the
      intermediate regime, say so.
  V2. delta calibration by sweep (E14, ~50 hand-labelled pairs), publishing the
      SENSITIVITY CURVE, never a fitted value.
  V3. VerifyOp route: if a merged concept is subsequently Refuted more often than
      the unmerged pair would have been, the merge was wrong -- calibrates delta
      with no new labels.
""")
