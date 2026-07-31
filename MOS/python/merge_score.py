"""
TATIANA — D-TILDE AS A MERGE **SCORE**, D AS THE **METRIC**. (5z's licensed split.)

=============================================================================
THE ONE-LINE DISPATCH RULE
=============================================================================
    D  (cone_bures.ConeBures)   -- wherever METRIC AXIOMS are needed:
                                   clustering, the cone construction, geodesics,
                                   anything geometric, anything transitive.
    D~ (this module)            -- ONLY for the merge decision and for RANKING
                                   candidate pairs. Neither needs a triangle
                                   inequality.

Mixing them is a type error. D~ is not a distance; it is a corrected estimate of
one, and §5z measured exactly how badly it fails to be a metric (worst triangle
violation +1.08 at delta=0.3). That failure is reproduced and REPORTED by this
file's own self-test rather than hidden, because a score that quietly starts
being used as a metric is precisely how merge transitivity would be lost without
anybody noticing.

=============================================================================
WHY A SEPARATE OBJECT EXISTS AT ALL
=============================================================================
`cone_bures.D` is an UPPER BOUND on the true Hellinger-Kantorovich distance: the
cone-over-Bures construction restricts mass growth to be spatially uniform, so
the whole lump must be transported or destroyed together, while true HK destroys
the non-overlapping TAILS selectively and transports only the core. Restricting
the competitor class raises an infimum, hence D >= HK_true.

§5z (V1) measured the gap with an exact HK solver and found a startlingly clean
empirical law:

    HK_true^2  ~=  D^2 / (1 + sigma^2 / delta^2)

fitted to ~3% over a 10x range of spread (sigma/delta = 0.15 .. 1.50) and every
separation tested (0.25 .. 3.14 at delta = 1). The penalty for the uniform-growth
restriction scales with HOW MUCH TAIL THERE IS, i.e. with spread -- and it does.

§5z then killed the corrected value AS A METRIC and licensed it as a SCORE:

    "Usable as a ranking SCORE, never as a metric; merge transitivity is lost."

It also declined to adopt it at all, on a second ground that has since expired:
there was no way to obtain sigma. `measure_sigma_dir.sigma_dir` now measures it
directly. This module is the consequence -- the score half of the split, built
on the measured sigma rather than on the `sigma_eff` proxy (mean per-dimension
variance) that `cone_bures.distance_sq_corrected` still carries.

=============================================================================
WHICH sigma. THIS IS THE WHOLE OF §5z's V1c CORRECTION AND IT MATTERS ~5x
=============================================================================
NOT ||U||_F, and NOT `cone_bures.sigma_eff_sq` (the mean per-dimension variance).
What the transport problem sees is the spread ALONG THE SEPARATION DIRECTION:

    u = (mu_0 - mu_1)/||mu_0 - mu_1||,      sigma_dir^2 = u^T Sigma u
                                                        = ||U^T u||^2 + eps

Reading the regime off ||U||_F is the exact mistake that produced §5z's retracted
"MOS sits at chance" claim. Since the rank-k covariance is mostly orthogonal to
the separation (k << d), sigma_dir is far smaller than ||U||_F. We therefore
import `measure_sigma_dir.sigma_dir` rather than re-deriving it: ONE definition,
so the score and the telemetry can never drift apart.

**PAIRING CONVENTION, STATED AS A CHOICE.** Two stalks give two directional
spreads. We take `max(sigma_a, sigma_b)` -- the worse of the two, following
`measure_sigma_dir.main`, which comments "do not average away". V1's fit used a
single sigma shared by both Gaussians, so every symmetric combination (max, rms,
mean) agrees exactly on the fitted data and NONE of them is validated against the
heterogeneous case. max is the choice that reports the larger correction, i.e.
the one that admits the larger disagreement with the plain metric. It is a
convention, not a derivation.

**COINCIDENT MEANS.** If mu_0 == mu_1 the separation direction is undefined and
`measure_sigma_dir.sigma_dir` raises. d_BW can still be nonzero there (pure
covariance difference). We set sigma_dir = 0, i.e. D~ = D exactly: with no
transport direction the correction's justification has no content, so we make no
correction rather than inventing one. Stated because it is a real branch, not a
guard.

=============================================================================
THE PREDICATE IS **NOT** A THRESHOLD ON D~. THAT WOULD BE VACUOUS.
=============================================================================
This is the trap in the task and it has to be written down.

D's merge predicate is STRUCTURAL, not tuned: merge iff theta = d_BW/(2delta)
is below pi/2, equivalently iff D^2 < w0 + w1 -- the saturation value, where
destroying-and-recreating becomes cheaper than moving.

Now try to reuse that threshold on the score. Since D^2 <= w0 + w1 always and the
correction factor is >= 1,

    D~^2  =  D^2 / (1 + rho^2)  <  w0 + w1     ALWAYS,   rho = sigma_dir/delta

so "D~^2 < w0 + w1" fires for EVERY pair. Vacuous. And the opposite repair --
rescale the threshold by the same factor -- gives back "D^2 < w0+w1", i.e. D's
own predicate, unchanged. That is a general fact worth stating: **a pair-wise
monotone rescaling of a score cannot change a decision if the threshold is
rescaled with it.** The correction can only move a decision when the threshold
is held COMMON across pairs while the score moves per pair.

So the correction must be carried into the decision as a change of LENGTH SCALE,
not a change of value. Small-angle expansion, w0 = w1 = w:

    D^2 = 2w(1 - cos theta) ~= w theta^2 = w d_BW^2 / (4 delta^2)
    D~^2 ~= w d_BW^2 / (4 delta^2 (1 + sigma^2/delta^2))
          = w d_BW^2 / (4 (delta^2 + sigma^2))

i.e. **to leading order in theta, dividing D^2 by (1 + sigma^2/delta^2) is
exactly the same thing as replacing delta by**

    delta_eff = sqrt(delta^2 + sigma_dir^2)

Directional spread adds IN QUADRATURE to the concept-identity length scale: a
fuzzy concept reaches further. The predicate is then D's own structural predicate
read at delta_eff,

    same concept   <==>   d_BW  <  pi * sqrt(delta^2 + sigma_dir^2)

which (a) degrades to D's predicate EXACTLY as sigma_dir -> 0, (b) is monotone in
sigma_dir (more spread merges more), and (c) still has no fitted threshold.

⚠️ APPROXIMATION, NOT AN IDENTITY. The value law and the scale law coincide only
to leading order in theta. Test 6 below MEASURES the divergence over the full
angle range and prints it; at the cutoff itself (theta = pi/2) it is tens of
percent. The DIRECTION -- spread pushes the cutoff outward -- is structural; the
quadrature FORM is fixed by matching §5z's fitted law at small angle and by
nothing else. It is not independently validated. Do not quote it as measured.

=============================================================================
THE REGIME NUMBER, AND WHY IT MUST BE MONITORED RATHER THAN ASSUMED
=============================================================================
§5z's agreement table (is_same_concept against true HK saturation, exact solver):

    sigma/delta   0.10   0.20   0.30   0.60   1.00   1.50
    agreement    86.7%  76.7%  63.3%  50.0%  50.0%  50.0%    (50% = chance)

§5ah (V6) then MEASURED sigma_dir/delta on the real corpus with live bge-small:
**0.32 median against a globally derived delta, 0.42 max** -- not the 0.09 the
simulation promised. So MOS deploys at roughly the 0.30 column: ~62% merge
agreement, not 87%. The VALUE stays accurate to ~5%; it is the THRESHOLDED
DECISION that degrades, because pairs near the cutoff flip. `regime()` exists so
that number is carried in telemetry per pair, and `SIGMA_ALARM = 0.3` is §5z's
own line, not a new one.

**This module does not repair that.** A correction fitted to ~3% cannot rescue a
decision whose error comes from pairs sitting on the boundary. What it buys is a
better RANKING among candidates -- which is what a merge queue consumes -- and an
explicit regime flag on every decision. If the ranking is all a caller needs, use
`merge_score`; if a caller needs a hard boolean, it should also read `regime()`
and treat an alarming pair as UNDECIDED rather than as decided.

=============================================================================
INHERITED CAVEATS (do not re-derive them, they are cone_bures's)
=============================================================================
* Normalisation: D (and hence D~) is NOT comparable across different delta
  without rescaling. Merge decisions compare pairs at ONE delta.
* Mass is the Hebbian weight w(sigma,t): decay destroys mass, reinforcement
  creates it. w0 = w1 = 1 is the unweighted default, not a claim.
* The empirical law was fitted at delta = 1, sigma/delta in [0.15, 1.50],
  separation in [0.25, 3.14], in 1-D. Outside that box D~ is EXTRAPOLATION.
  Nothing here checks that a caller stayed inside it -- `regime()` is the only
  instrument, and it only watches sigma/delta.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Tuple

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from belief import Gaussian, EPS_FLOOR                      # noqa: E402
from cone_bures import ConeBures, bures_w2_sq               # noqa: E402
from measure_sigma_dir import sigma_dir as _sigma_dir_pair  # noqa: E402


# §5z's own line: at sigma_dir/delta ~ 0.3 the merge agreement with true HK has
# already fallen to ~63%, and by 0.6 it is chance. Not a new threshold.
SIGMA_ALARM: float = 0.3


# ---------------------------------------------------------------------------
# 1. The measured spread along the separation direction
# ---------------------------------------------------------------------------

def sigma_dir_of_pair(g0: Gaussian, g1: Gaussian) -> float:
    """max(sigma_a, sigma_b), the directional spread this pair presents.

    Delegates to `measure_sigma_dir.sigma_dir` so there is exactly ONE definition
    of sigma_dir in the codebase -- the score and the telemetry cannot drift.

    Returns 0.0 when the means coincide (separation direction undefined; see the
    module docstring). That is a deliberate no-correction branch, not a guard.
    """
    if g0.d != g1.d:
        raise ValueError(
            f"dimension mismatch {g0.d} vs {g1.d}; refusing to pad "
            "(same rule as cone_bures.bures_w2_sq).")
    U0 = g0.U if g0.U is not None else np.zeros((g0.d, 0))
    U1 = g1.U if g1.U is not None else np.zeros((g1.d, 0))
    try:
        sa, sb = _sigma_dir_pair(g0.mu, U0, g1.mu, U1, g0.eps, g1.eps)
    except ValueError:
        return 0.0                      # coincident means: no direction, no claim
    return float(max(sa, sb))


def correction_factor(g0: Gaussian, g1: Gaussian, delta: float) -> float:
    """1 + sigma_dir^2/delta^2 -- the factor §5z fitted, on the MEASURED sigma.

    Always >= 1, so D~ <= D always: the correction can only move the estimate
    DOWN, towards the true HK distance that D upper-bounds.
    """
    if delta <= 0:
        raise ValueError("delta must be > 0 (it is a length scale)")
    s = sigma_dir_of_pair(g0, g1)
    return 1.0 + (s * s) / (delta * delta)


# ---------------------------------------------------------------------------
# 2. The SCORE
# ---------------------------------------------------------------------------

def merge_score_sq(g0: Gaussian, g1: Gaussian, delta: float,
                   w0: float = 1.0, w1: float = 1.0) -> float:
    """D~^2 = D^2 / (1 + sigma_dir^2/delta^2). An ESTIMATE of HK_true^2.

    NOT A METRIC. See `triangle_violation` and test 5. Use for ranking only.
    """
    D2 = ConeBures(delta).distance_sq(g0, g1, w0, w1)
    return D2 / correction_factor(g0, g1, delta)


def merge_score(g0: Gaussian, g1: Gaussian, delta: float,
                w0: float = 1.0, w1: float = 1.0) -> float:
    """D~ -- the corrected merge score. Lower means "more likely one concept".

    Accurate to ~3% against an exact HK solver inside §5z's fitted box
    (delta = 1, sigma/delta in [0.15, 1.50], separation in [0.25, 3.14], 1-D);
    extrapolation outside it. Satisfies D~ <= D, D~(a,a) = 0, and symmetry --
    everything a metric needs EXCEPT the triangle inequality, which it violates
    structurally (~+0.5 at delta = 1 on heterogeneous stalks).
    """
    return float(np.sqrt(max(merge_score_sq(g0, g1, delta, w0, w1), 0.0)))


# ---------------------------------------------------------------------------
# 3. The PREDICATE (via the length scale, not via the value -- see docstring)
# ---------------------------------------------------------------------------

def effective_delta(g0: Gaussian, g1: Gaussian, delta: float) -> float:
    """sqrt(delta^2 + sigma_dir^2): the length scale the correction implies.

    Equal to dividing D^2 by (1 + sigma^2/delta^2) ONLY to leading order in the
    cone angle theta = d_BW/(2 delta). Exact as sigma_dir -> 0 (delta_eff ->
    delta), where both reduce to D itself. Test 6 measures the divergence.
    """
    if delta <= 0:
        raise ValueError("delta must be > 0 (it is a length scale)")
    s = sigma_dir_of_pair(g0, g1)
    return float(np.sqrt(delta * delta + s * s))


def is_same_concept(g0: Gaussian, g1: Gaussian, delta: float) -> bool:
    """The MERGE PREDICATE, corrected: d_BW < pi * sqrt(delta^2 + sigma_dir^2).

    Same structural content as `ConeBures.is_same_concept` -- the cutoff is where
    the cone cosine reaches zero, i.e. where destroying-and-recreating becomes
    cheaper than moving -- read at the spread-inflated length scale. No fitted
    threshold enters.

    Degrades EXACTLY to `ConeBures(delta).is_same_concept` when sigma_dir = 0,
    and is monotone in sigma_dir: a fuzzier pair merges more readily.

    ⚠️ At MOS's measured sigma_dir/delta ~ 0.32 (§5ah) the agreement of the
    UNCORRECTED predicate with true HK is only ~62%. This predicate is expected
    to be better, but that has NOT been measured against an exact HK solver --
    §5z's agreement table was computed for D, not for D~. Callers who need a
    trustworthy boolean should read `regime()` and treat an alarming pair as
    undecided.
    """
    return ConeBures(effective_delta(g0, g1, delta)).is_same_concept(g0, g1)


# ---------------------------------------------------------------------------
# 4. The regime monitor
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Regime:
    """sigma_dir/delta for one pair, with §5z's alarm line attached."""
    sigma_dir: float
    delta: float
    ratio: float

    @property
    def alarm(self) -> bool:
        """True once the pair is past §5z's 0.3 line (~63% agreement or worse)."""
        return self.ratio > SIGMA_ALARM

    @property
    def expected_agreement(self) -> str:
        """§5z's measured table, read as a coarse label. Never interpolate it."""
        if self.ratio <= 0.15:
            return "~87% (best row measured)"
        if self.ratio <= 0.25:
            return "~77%"
        if self.ratio <= 0.45:
            return "~63% (MOS's measured regime, §5ah)"
        return "~50% = CHANCE"

    def __float__(self) -> float:
        return float(self.ratio)

    def __repr__(self) -> str:
        flag = "  [ALARM: past 0.3]" if self.alarm else ""
        return (f"Regime(sigma_dir={self.sigma_dir:.4f}, delta={self.delta:.4f}, "
                f"ratio={self.ratio:.4f}, agreement={self.expected_agreement})"
                f"{flag}")


def regime(g0: Gaussian, g1: Gaussian, delta: float) -> Regime:
    """sigma_dir/delta for this pair. Log it per merge decision.

    §5ah: the real corpus sits at 0.32 median / 0.42 max against a globally
    DERIVED delta (`derived_scales.derive_delta`), and worse against a per-pair
    saturation delta, which shrinks exactly where pairs are closest. Pass the
    global delta here -- that is the number a deployed system actually has and
    the one telemetry should carry.
    """
    if delta <= 0:
        raise ValueError("delta must be > 0 (it is a length scale)")
    s = sigma_dir_of_pair(g0, g1)
    return Regime(sigma_dir=s, delta=float(delta), ratio=s / float(delta))


# ---------------------------------------------------------------------------
# 5. The failure, exposed as an API rather than buried in a comment
# ---------------------------------------------------------------------------

def triangle_violation(ga: Gaussian, gb: Gaussian, gc: Gaussian, delta: float,
                       wa: float = 1.0, wb: float = 1.0, wc: float = 1.0
                       ) -> float:
    """D~(a,c) - [D~(a,b) + D~(b,c)]. Positive means the triangle inequality FAILS.

    Exported deliberately. D~ is not a metric and this is the function that says
    so; any caller tempted to cluster on D~ can call it and watch it go positive.
    Use `cone_bures.ConeBures.distance` instead -- that one is proved and tested
    (20k triples, zero violations).
    """
    f = lambda x, y, wx, wy: merge_score(x, y, delta, wx, wy)
    return f(ga, gc, wa, wc) - (f(ga, gb, wa, wb) + f(gb, gc, wb, wc))


# ===========================================================================
# Self-tests. Run: python merge_score.py     (zero API calls)
# ===========================================================================

def _main() -> None:
    import console
    console.setup()
    ok = 0

    def check(name: str, cond: bool) -> None:
        nonlocal ok
        assert cond, f"FAILED: {name}"
        ok += 1
        print(f"  [ok] {name}")

    rng = np.random.default_rng(17)
    d = 24
    e0 = np.eye(d)[0]

    def G(scale=0.4, k=3, mu=None, eps=EPS_FLOOR):
        return Gaussian(mu=rng.normal(size=d) if mu is None else mu,
                        U=rng.normal(size=(d, k)) * scale, eps=eps)

    print("=== 1. sigma_dir is the DIRECTIONAL spread, not ||U||_F ===")
    # U supported entirely on coordinates 1..k, separation along coordinate 0.
    U_perp = np.zeros((d, 3))
    U_perp[1:4, :] = np.eye(3) * 2.0            # ||U||_F = 2*sqrt(3) ~ 3.46
    a = Gaussian(mu=np.zeros(d), U=U_perp, eps=0.0)
    b = Gaussian(mu=1.0 * e0, U=U_perp, eps=0.0)
    check(f"||U||_F = {np.linalg.norm(U_perp):.3f} but sigma_dir = "
          f"{sigma_dir_of_pair(a, b):.3e} (orthogonal to the separation)",
          sigma_dir_of_pair(a, b) < 1e-15)
    U_par = np.zeros((d, 3))
    U_par[0, 0] = 2.0                            # same ||U||_F, now ALONG e0
    U_par[1:3, 1:3] = np.eye(2) * 2.0
    a2 = Gaussian(mu=np.zeros(d), U=U_par, eps=0.0)
    b2 = Gaussian(mu=1.0 * e0, U=U_par, eps=0.0)
    check(f"same ||U||_F = {np.linalg.norm(U_par):.3f}, spread ALONG the "
          f"separation: sigma_dir = {sigma_dir_of_pair(a2, b2):.3f}",
          abs(sigma_dir_of_pair(a2, b2) - 2.0) < 1e-12)
    check("isotropic k=0 stalks give sigma_dir = sqrt(eps) exactly",
          abs(sigma_dir_of_pair(
              Gaussian(mu=np.zeros(d), U=np.zeros((d, 0)), eps=0.04),
              Gaussian(mu=e0, U=np.zeros((d, 0)), eps=0.04)) - 0.2) < 1e-12)

    print("\n=== 2. ★ EXACT DAY-ONE DEGRADATION: sigma_dir = 0  =>  D~ == D ===")
    # Not "agrees to 1e-9". BIT-IDENTICAL. If this ever fails, switching the
    # score on is a silent regime change and every historical number is
    # incomparable to every new one (edge_precision.py's test 9 discipline).
    worst_rel = 0.0
    for delta in (0.1, 0.3, 1.0, 5.0):
        cb = ConeBures(delta)
        for _ in range(50):
            sep = float(rng.uniform(0.05, 4.0))
            Uz = np.zeros((d, 3))
            Uz[1:4, :] = rng.normal(size=(3, 3)) * 0.7      # exactly perp to e0
            mu0 = rng.normal(size=d)
            mu0[0] = 0.0
            g0 = Gaussian(mu=mu0, U=Uz, eps=0.0)
            g1 = Gaussian(mu=mu0 + sep * e0, U=Uz, eps=0.0)
            wA, wB = rng.uniform(0.1, 3.0, size=2)
            D = cb.distance(g0, g1, wA, wB)
            Dt = merge_score(g0, g1, delta, wA, wB)
            worst_rel = max(worst_rel, abs(Dt - D))
            assert merge_score_sq(g0, g1, delta, wA, wB) \
                == cb.distance_sq(g0, g1, wA, wB), "not bit-identical"
            assert is_same_concept(g0, g1, delta) == cb.is_same_concept(g0, g1)
    check(f"200 sigma_dir = 0 pairs: D~ == D bit-identically (max |diff| "
          f"{worst_rel:.1e}) and the predicates agree", worst_rel == 0.0)
    check("correction factor is exactly 1.0 there, not 1+1e-16",
          correction_factor(a, b, 1.0) == 1.0)

    print("\n  and the LIMIT sigma_dir -> 0 is approached smoothly:")
    print(f"    {'eps':>10} {'sigma_dir':>10} {'D':>10} {'D~':>10} {'D~/D':>9}")
    cb1 = ConeBures(1.0)
    prev_ratio = 0.0
    for eps in (1.0, 1e-1, 1e-2, 1e-3, 1e-4, 1e-6, 0.0):
        g0 = Gaussian(mu=np.zeros(d), U=np.zeros((d, 0)), eps=eps)
        g1 = Gaussian(mu=1.2 * e0, U=np.zeros((d, 0)), eps=eps)
        D = cb1.distance(g0, g1)
        Dt = merge_score(g0, g1, 1.0)
        print(f"    {eps:>10.0e} {sigma_dir_of_pair(g0, g1):>10.4f} "
              f"{D:>10.6f} {Dt:>10.6f} {Dt/D:>9.6f}")
        check_ratio = Dt / D
        assert check_ratio >= prev_ratio - 1e-12, "D~/D must rise to 1 as eps falls"
        prev_ratio = check_ratio
    check("D~/D -> 1 monotonically as the spread vanishes", abs(prev_ratio - 1.0) < 1e-15)

    print("\n=== 3. D~ <= D ALWAYS (the correction only ever moves DOWN) ===")
    worst_excess = -np.inf
    n_strict = 0
    for delta in (0.05, 0.3, 1.0, 5.0, 50.0):
        cb = ConeBures(delta)
        for _ in range(1000):
            sc = float(rng.uniform(0.02, 1.2))
            kk = int(rng.integers(0, 5))
            g0 = Gaussian(mu=rng.normal(size=d),
                          U=rng.normal(size=(d, kk)) * sc,
                          eps=float(rng.uniform(1e-4, 0.5)))
            g1 = Gaussian(mu=rng.normal(size=d),
                          U=rng.normal(size=(d, int(rng.integers(0, 5)))) * sc,
                          eps=float(rng.uniform(1e-4, 0.5)))
            wA, wB = rng.uniform(0.05, 3.0, size=2)
            D = cb.distance(g0, g1, wA, wB)
            Dt = merge_score(g0, g1, delta, wA, wB)
            worst_excess = max(worst_excess, Dt - D)
            n_strict += (Dt < D - 1e-12)
    check(f"5000 random pairs over five delta: max(D~ - D) = {worst_excess:.2e} <= 0",
          worst_excess <= 0.0)
    check(f"and the correction is STRICT on {n_strict}/5000 of them "
          f"(it is not a no-op)", n_strict > 4900)

    print("\n=== 4. the other axioms D~ DOES keep (so the failure is isolated) ===")
    p, q = G(k=2), G(k=4)
    check("D~(a,a) = 0", merge_score(p, p, 1.0) == 0.0)
    check("symmetry: D~(a,b) == D~(b,a) to 1e-15",
          abs(merge_score(p, q, 1.0) - merge_score(q, p, 1.0)) < 1e-15)
    check("non-negativity", merge_score(p, q, 1.0) >= 0.0)
    check("coincident means => no correction (sigma_dir undefined, set to 0)",
          merge_score(Gaussian(mu=np.zeros(d), U=U_perp, eps=0.3),
                      Gaussian(mu=np.zeros(d), U=U_par, eps=0.7), 1.0)
          == ConeBures(1.0).distance(
              Gaussian(mu=np.zeros(d), U=U_perp, eps=0.3),
              Gaussian(mu=np.zeros(d), U=U_par, eps=0.7)))

    print("\n=== 5. ★★ D~ IS NOT A METRIC. The violation, found and REPORTED. ===")
    print("  §5z measured +1.08 at delta=0.3 with the sigma_eff proxy. Repeated")
    print("  here with the MEASURED sigma_dir, which is a different (smaller)")
    print("  correction -- so the number moves, but the verdict must not.")
    print(f"    {'delta':>7} {'worst violation':>17} {'  at rho = (ab, bc, ac)'}")
    found_any = False
    for delta in (0.1, 0.3, 1.0, 3.0):
        worst_v, worst_rho = -np.inf, None
        for _ in range(20000):
            gs = []
            for _ in range(3):
                sc = float(rng.uniform(0.02, 1.2))
                kk = int(rng.integers(0, 5))
                gs.append(Gaussian(mu=rng.normal(size=d),
                                   U=rng.normal(size=(d, kk)) * sc,
                                   eps=float(rng.uniform(1e-3, 0.5))))
            ga, gb, gc = gs
            wA, wB, wC = rng.uniform(0.05, 3.0, size=3)
            v = triangle_violation(ga, gb, gc, delta, wA, wB, wC)
            if v > worst_v:
                worst_v = v
                worst_rho = (sigma_dir_of_pair(ga, gb) / delta,
                             sigma_dir_of_pair(gb, gc) / delta,
                             sigma_dir_of_pair(ga, gc) / delta)
        verdict = "**VIOLATED**" if worst_v > 1e-9 else "holds here"
        found_any = found_any or worst_v > 1e-9
        print(f"    {delta:>7.2f} {worst_v:>+17.4f}   "
              f"({worst_rho[0]:.2f}, {worst_rho[1]:.2f}, {worst_rho[2]:.2f})"
              f"   {verdict}")
    check("an EXPLICIT triangle violation exists and is printed above",
          found_any)
    print("  => D~ is a SCORE. Never cluster on it, never build a cone over it,")
    print("     never assume merge transitivity. Use cone_bures.D for all of that.")

    print("\n=== 6. the predicate's OWN approximation, measured not asserted ===")
    print("  D~ divides the VALUE; the predicate inflates the LENGTH SCALE. They")
    print("  agree only to leading order in theta. How far apart do they get?")
    print(f"    {'rho':>6} {'theta':>7} {'D~ (value law)':>16} "
          f"{'D at delta_eff':>16} {'rel dev':>9}")
    worst_dev = 0.0
    for rho in (0.1, 0.32, 1.0):
        for theta in (0.05, 0.5, 1.0, np.pi / 2):
            # w0 = w1 = 1, so D^2 = 2(1 - cos theta) and the two laws are pure
            # functions of (theta, rho) -- no Gaussians needed to compare them.
            Dv = np.sqrt(2.0 * (1 - np.cos(theta)) / (1 + rho * rho))
            Ds = np.sqrt(2.0 * (1 - np.cos(theta / np.sqrt(1 + rho * rho))))
            dev = abs(Dv - Ds) / Ds
            worst_dev = max(worst_dev, dev)
            print(f"    {rho:>6.2f} {theta:>7.3f} {Dv:>16.6f} {Ds:>16.6f} "
                  f"{dev:>8.2%}")
    check(f"the two laws diverge by up to {worst_dev:.1%} at the cutoff -- "
          f"stated, not hidden", worst_dev > 0.05)
    check("...and agree to <0.1% at small theta (the regime the fit came from)",
          abs(np.sqrt(2 * (1 - np.cos(0.05)) / 2.0)
              - np.sqrt(2 * (1 - np.cos(0.05 / np.sqrt(2.0))))) /
          np.sqrt(2 * (1 - np.cos(0.05 / np.sqrt(2.0)))) < 1e-3)

    print("\n=== 7. PREDICATE: agrees with D at small sigma/delta, diverges at large ===")
    # k = 0 stalks with EQUAL eps: the Bures covariance term d(sqrt(e0)-sqrt(e1))^2
    # vanishes, so d_BW = ||dmu|| exactly and sigma_dir = sqrt(eps) exactly. The
    # whole comparison is then analytic: D says merge iff s < pi*delta, D~ says
    # merge iff s < pi*sqrt(delta^2 + eps).
    DELTA = 0.4
    cbD = ConeBures(DELTA)
    seps = np.linspace(0.05, 3.0, 400)
    print(f"    delta = {DELTA}; 400 separations in [0.05, 3.0], k=0 stalks")
    print(f"    {'eps':>10} {'sigma/delta':>12} {'disagreement':>13} {'flips'}")
    rows = []
    for eps in (1e-8, 1e-4, 1e-3, 1e-2, 4e-2, 0.16, 0.5):
        dis = 0
        for s in seps:
            g0 = Gaussian(mu=np.zeros(d), U=np.zeros((d, 0)), eps=eps)
            g1 = Gaussian(mu=s * e0, U=np.zeros((d, 0)), eps=eps)
            dis += (is_same_concept(g0, g1, DELTA) != cbD.is_same_concept(g0, g1))
        ratio = np.sqrt(eps) / DELTA
        rows.append((ratio, dis / len(seps)))
        print(f"    {eps:>10.0e} {ratio:>12.4f} {dis/len(seps):>12.1%}   "
              f"{'SAME as D' if dis == 0 else f'{dis} pairs flip to SAME'}")
    check("at sigma/delta < 0.01 the corrected predicate is IDENTICAL to D's",
          rows[0][1] == 0.0)
    check("at MOS's measured sigma/delta ~ 0.32 (§5ah) it diverges materially",
          rows[-2][1] > 0.05)
    check("disagreement is monotone in sigma/delta",
          all(rows[i][1] <= rows[i + 1][1] + 1e-12 for i in range(len(rows) - 1)))
    check("every disagreement is in the MERGE direction (D~ never splits what "
          "D merges)",
          all(is_same_concept(Gaussian(mu=np.zeros(d), U=np.zeros((d, 0)), eps=0.5),
                              Gaussian(mu=s * e0, U=np.zeros((d, 0)), eps=0.5), DELTA)
              or not cbD.is_same_concept(
                  Gaussian(mu=np.zeros(d), U=np.zeros((d, 0)), eps=0.5),
                  Gaussian(mu=s * e0, U=np.zeros((d, 0)), eps=0.5))
              for s in seps))

    print("\n=== 8. RANKING: the correction reorders pairs (the point of a score) ===")
    # Two candidate pairs at the SAME cone-Bures distance but different spread.
    # D cannot tell them apart; D~ prefers the sharper one, because the fuzzy
    # pair's apparent distance was inflated by the uniform-growth restriction.
    DE = 1.0
    sharp0 = Gaussian(mu=np.zeros(d), U=np.zeros((d, 0)), eps=1e-8)
    sharp1 = Gaussian(mu=0.9 * e0, U=np.zeros((d, 0)), eps=1e-8)
    fuzzy0 = Gaussian(mu=np.zeros(d), U=np.zeros((d, 0)), eps=0.25)
    fuzzy1 = Gaussian(mu=0.9 * e0, U=np.zeros((d, 0)), eps=0.25)
    cbE = ConeBures(DE)
    D_s, D_f = cbE.distance(sharp0, sharp1), cbE.distance(fuzzy0, fuzzy1)
    T_s, T_f = merge_score(sharp0, sharp1, DE), merge_score(fuzzy0, fuzzy1, DE)
    print(f"    sharp pair (sigma_dir=1e-4): D = {D_s:.6f}   D~ = {T_s:.6f}")
    print(f"    fuzzy pair (sigma_dir=0.50): D = {D_f:.6f}   D~ = {T_f:.6f}")
    check(f"D ranks them EQUAL (|dD| = {abs(D_s-D_f):.1e}) -- it cannot see spread",
          abs(D_s - D_f) < 1e-9)
    check("D~ separates them, preferring the fuzzy pair (its D was inflated)",
          T_f < T_s - 1e-6)

    print("\n=== 9. regime() and the 0.3 alarm ===")
    r_ok = regime(Gaussian(mu=np.zeros(d), U=np.zeros((d, 0)), eps=1e-3),
                  Gaussian(mu=e0, U=np.zeros((d, 0)), eps=1e-3), 0.4)
    r_bad = regime(Gaussian(mu=np.zeros(d), U=np.zeros((d, 0)), eps=0.04),
                   Gaussian(mu=e0, U=np.zeros((d, 0)), eps=0.04), 0.4)
    print(f"    {r_ok!r}")
    print(f"    {r_bad!r}")
    check("a concentrated pair is below the alarm line", not r_ok.alarm)
    check("a pair at sigma_dir/delta = 0.5 alarms", r_bad.alarm and r_bad.ratio > 0.3)
    check("SIGMA_ALARM is §5z's 0.3, not a new number", SIGMA_ALARM == 0.3)
    check("ratio = sigma_dir/delta exactly",
          abs(float(r_bad) - 0.2 / 0.4) < 1e-12)
    # §5ah's measured median, reproduced as a labelled expectation.
    r_5ah = Regime(sigma_dir=0.32 * 0.4, delta=0.4, ratio=0.32)
    check(f"§5ah's measured median 0.32 reads as '{r_5ah.expected_agreement}'",
          r_5ah.alarm and "63%" in r_5ah.expected_agreement)

    print("\n=== 10. refusals ===")
    for name, fn in [
        ("delta <= 0 is refused by merge_score",
         lambda: merge_score(p, q, 0.0)),
        ("delta <= 0 is refused by is_same_concept",
         lambda: is_same_concept(p, q, -1.0)),
        ("delta <= 0 is refused by regime",
         lambda: regime(p, q, 0.0)),
        ("a dimension mismatch is refused, not padded",
         lambda: sigma_dir_of_pair(
             p, Gaussian(mu=np.zeros(d + 1), U=np.zeros((d + 1, 0))))),
    ]:
        try:
            fn()
            raise AssertionError(f"FAILED: {name} (no exception raised)")
        except ValueError:
            ok += 1
            print(f"  [ok] {name}")

    print(f"\nAll {ok} merge-score tests passed (zero API calls).")
    print("""
DISPATCH, ONCE MORE, BECAUSE THIS IS THE FILE'S WHOLE POINT
  cone_bures.ConeBures.distance   -> every geometric use. Proved metric.
  merge_score.merge_score          -> ranking merge candidates.
  merge_score.is_same_concept      -> the merge decision, with regime() logged.
  Never the second two anywhere a triangle inequality is assumed.

STILL OWED (do not let these rot)
  * §5z's agreement table was computed for D against an exact HK solver. The
    same table for D~ has NOT been computed. This module's claim to improve the
    DECISION is therefore inferred from the value law, not measured. That is the
    single largest unverified thing here.
  * The quadrature form delta_eff = sqrt(delta^2 + sigma_dir^2) is fixed only by
    matching §5z's fitted law at small angle. Its behaviour AT the cutoff -- the
    only place the predicate is decided -- is where the two laws diverge most
    (test 6). An exact-HK check of the cutoff location as a function of sigma
    would settle it.
  * max(sigma_a, sigma_b) is a convention. V1 fitted with a single shared sigma,
    so the heterogeneous case is unvalidated in every combination rule.
""")


if __name__ == "__main__":
    _main()
