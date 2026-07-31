"""
TATIANA — pi_e, DERIVED (Q9's "confidence feeds the edge precision", made precise).

WHAT THIS REPLACES, AND WHY IT IS A BUG FIX RATHER THAN A FEATURE
----------------------------------------------------------------
coherence.report() takes an optional per-edge precision pi_e. Until now the only
thing that ever supplied one was C++ `CoarseComplex::set_use_precision(true)`,
whose documented behaviour is

    "each edge uses its COUPLING WEIGHT as pi_e (a more-bound coalition is
     trusted more)"

That is a type error, and it is the same one logbook 5af isolated from two other
directions:

  * w(sigma, t) is a NORMALISED COUPLING, capped on [0, 1] (Construction 1, and
    coarse_complex.cpp returns 1.0 as the absent-weight default, i.e. 1.0 already
    means "fully bound").
  * pi_e is a PRECISION -- an inverse variance -- and is UNBOUNDED ABOVE.

Substituting one for the other has already caused a divergence once: 5q records
"raw coupling weight as precision made lr*precision huge -> divergence", patched
with max_step=0.5. And 5ac reached the identical separation from the Forman side
(the curvature's cell weights must be pi_e, not w). Three independent routes to
one conclusion, so this module stops type-punning and derives pi_e instead.

The old intent -- "a more-bound coalition should be trusted more" -- is not
wrong. It is simply not a precision, and if it is wanted it must enter as its own
term rather than by borrowing pi_e's slot.

THE DERIVATION
--------------
pi_e is the precision of the PREDICTION ERROR on edge e, which is the only thing
it can be if omega is to remain the predictive-coding free energy (5p mechanism 1):

    F = sum_e pi_e ||eps_e||^2,     eps_e = R_{u,e} x_u - R_{v,e} x_v

Assume:
  (H1) the two stalks are independent given the edge;
  (H2) the restriction maps are ORTHOGONAL, ||R|| = 1 -- this is not a new
       assumption, it is the standing Anderson-Morley hypothesis (FIX-10, audit
       F2) that rho <= 1 already depends on;
  (H3) coarse stalk covariances are isotropic, Sigma_v = D_v I.

Then, because an orthogonal map carries an isotropic covariance to itself,
R (D I) R^T = D R R^T = D I, and independence adds the variances:

    Var(eps_e) = R_u Sigma_u R_u^T + R_v Sigma_v R_v^T = (D_u + D_v) I

Adding the reported-judgement noise on that edge (Q9's confidence c_e) as a
per-component variance s_e:

    Var(eps_e) = (D_u + D_v + s_e) I

        ==>     pi_e = 1 / (D_u + D_v + s_e)

WHY CONFIDENCE IS SAFE HERE AND WAS CATASTROPHIC IN D (this is the whole of FIX-13)
----------------------------------------------------------------------------------
FIX-13 removed -ln(c) from the stalk noise floor D because the Bures term between
two isotropic covariances is d*(sqrt(D1)-sqrt(D2))^2 -- d-EXTENSIVE, ~230 at
d = 384 against a semantic term bounded by 4. Confidence drowned meaning.

Nothing of that kind happens here. pi_e is ONE SCALAR multiplying ||eps_e||^2.
Confidence enters as a per-component variance s_e = -ln(c_e)/d, so its
contribution to the trace is -ln(c_e) = O(1) and NO d-extensive quantity is
created anywhere. This is exactly what Q9 meant by "the confidence feeds pi_e
directly": pi_e is the dimensionally harmless home, D was not.

DAY-ONE DEGRADATION (exact, and the parity test depends on it)
--------------------------------------------------------------
rho = omega / (B * ||X||^2) with B = max_e (d_pi[u] + d_pi[v]), and omega and B
are BOTH linear in pi. So rho is INVARIANT under uniform rescaling of pi. Hence
with all D_v equal and no confidences, this module's pi_e is a constant and rho
is bit-identical to the pi = None path. Improvement is strictly opt-in on real
variation, never a silent regime change.

WHAT THIS DOES NOT DO
---------------------
It does not manufacture a confidence. An edge with no reported judgement gets
s_e = 0 (no extra noise), not a guessed one -- the same discipline as
belief.stalk_gaussian returning None for an idle organ.
"""

from __future__ import annotations

import math
from typing import Dict, Iterable, Mapping, Optional, Sequence, Tuple

Vertex = str
Edge = Tuple[Vertex, Vertex]

# Mirrors belief.EPS_FLOOR / core::EPS_FLOOR. A stalk floor is strictly positive,
# so pi_e is always finite; this is a guard, not a tuning knob.
MIN_TOTAL_VARIANCE = 1e-12


def report_variance(confidence: Optional[float], d: int) -> float:
    """The per-component variance s_e contributed by a reported confidence.

    s_e = -ln(c) / d, so the TRACE contribution is -ln(c) = O(1) and stays
    commensurate with the semantic scale, exactly as belief.py's Sigma_0 = (1/d)I
    carries trace 1. Returns 0.0 for an absent confidence -- absence of a
    measurement is not evidence of noise, and inventing one would be the failure
    mode this project exists to avoid.

    Raises on c outside (0, 1]: a "confidence" of 0 is not a confidence, and one
    above 1 is a bug in the caller, not something to clamp away quietly.
    """
    if d <= 0:
        raise ValueError(f"embedding dimension must be positive, got {d}")
    if confidence is None:
        return 0.0
    c = float(confidence)
    if not (0.0 < c <= 1.0):
        raise ValueError(
            f"confidence {c} outside (0, 1]. Zero confidence is not a "
            "measurement and >1 is a caller bug; refusing to clamp.")
    return -math.log(c) / float(d)


def edge_precision(edges: Iterable[Edge],
                   stalk_floor: Mapping[Vertex, float],
                   d: int,
                   confidence: Optional[Mapping[Edge, float]] = None,
                   ) -> Dict[Edge, float]:
    """Build the per-edge precision map pi_e = 1 / (D_u + D_v + s_e).

    Parameters
    ----------
    edges        : the bound pairs of the coarse complex.
    stalk_floor  : D_v per organ -- belief.stalk_gaussian(...).eps, or the C++
                   core::stalk_floor(d, n_eff). Must be strictly positive.
    d            : embedding dimension (384 deployed), for the s_e normalisation.
    confidence   : optional c_e in (0, 1] per edge, from the Q9 judgement
                   contract. Missing edges contribute no extra noise.

    Returns a dict accepted directly by coherence.report(precision=...).
    """
    conf = confidence or {}
    out: Dict[Edge, float] = {}
    for (u, v) in edges:
        for endpoint in (u, v):
            if endpoint not in stalk_floor:
                raise KeyError(
                    f"No stalk floor for organ {endpoint!r} on edge {(u, v)}. "
                    "Refusing to default silently -- a missing floor is a "
                    "missing measurement, not a floor of 1.")
        D_u = float(stalk_floor[u])
        D_v = float(stalk_floor[v])
        if D_u <= 0.0 or D_v <= 0.0:
            raise ValueError(
                f"Stalk floors must be strictly positive; got D[{u}]={D_u}, "
                f"D[{v}]={D_v}. A zero floor is infinite precision.")
        c = conf.get((u, v), conf.get((v, u)))
        total = D_u + D_v + report_variance(c, d)
        if total < MIN_TOTAL_VARIANCE:
            raise ValueError(
                f"Edge {(u, v)} has total error variance {total:.3g}, which "
                "would give an effectively infinite precision. Check the stalk "
                "floors -- they should be O(1/d), not O(1/d^2).")
        out[(u, v)] = 1.0 / total
    return out


def is_uniform(pi: Mapping[Edge, float], rel_tol: float = 1e-12) -> bool:
    """True if every pi_e agrees to within rel_tol.

    Useful as an assertion at call sites: a uniform pi means rho is bit-identical
    to the pi = None path, so any DIFFERENCE in rho must be attributable to real
    variation in the floors or confidences, never to switching this module on.
    """
    vals = list(pi.values())
    if not vals:
        return True
    lo, hi = min(vals), max(vals)
    return (hi - lo) <= rel_tol * max(1.0, abs(hi))


# ---------------------------------------------------------------------------
# Self-tests. Run: python edge_precision.py
# ---------------------------------------------------------------------------

def _main() -> None:
    D_DEPLOYED = 384
    ok = 0

    def check(name: str, cond: bool) -> None:
        nonlocal ok
        assert cond, f"FAILED: {name}"
        ok += 1
        print(f"  [ok] {name}")

    print("=== pi_e, derived ===")

    edges = [("A", "B"), ("B", "C"), ("C", "A")]
    flat = {v: 0.0023 for v in "ABC"}  # ~ core::stalk_floor(384, n_eff=1)

    # 1. Uniform floors, no confidence => uniform pi => rho unchanged (day-one).
    pi = edge_precision(edges, flat, D_DEPLOYED)
    check("uniform floors give uniform pi (rho bit-identical to pi=None)",
          is_uniform(pi))
    check("pi = 1/(D_u+D_v) exactly",
          abs(pi[("A", "B")] - 1.0 / 0.0046) < 1e-9)

    # 2. pi is UNBOUNDED ABOVE -- the property w(sigma,t) does not have, and the
    #    whole reason the coupling weight could never have been a precision.
    tight = {v: 1e-6 for v in "ABC"}
    pi_tight = edge_precision(edges, tight, D_DEPLOYED)
    check("a tight stalk gives pi >> 1 (uncapped, unlike w in [0,1])",
          pi_tight[("A", "B")] > 1e5)

    # 3. Directions. Broader stalk => less precision. Lower confidence => less.
    broad = {"A": 0.05, "B": 0.0023, "C": 0.0023}
    pi_broad = edge_precision(edges, broad, D_DEPLOYED)
    check("a broader organ lowers the precision of its edges",
          pi_broad[("A", "B")] < pi[("A", "B")])
    pi_conf = edge_precision(edges, flat, D_DEPLOYED,
                             confidence={("A", "B"): 0.2})
    check("a low-confidence judgement lowers that edge's precision",
          pi_conf[("A", "B")] < pi[("A", "B")])
    check("and leaves the other edges untouched",
          abs(pi_conf[("B", "C")] - pi[("B", "C")]) < 1e-15)

    # 4. Confidence is dimensionally harmless here -- the FIX-13 property.
    #    s_e's TRACE contribution is -ln(c) = O(1), never O(d).
    s = report_variance(0.2, D_DEPLOYED)
    check("s_e trace contribution is -ln(c) = O(1), not O(d)",
          abs(s * D_DEPLOYED - (-math.log(0.2))) < 1e-12)
    check("s_e itself is O(1/d)", s < 1.0 / 50.0)

    # 5. c = 1 (certain) must add NOTHING, not epsilon.
    check("c = 1 contributes exactly zero noise",
          report_variance(1.0, D_DEPLOYED) == 0.0)
    check("absent confidence contributes exactly zero noise",
          report_variance(None, D_DEPLOYED) == 0.0)

    # 6. Edge orientation must not matter.
    pi_rev = edge_precision([("B", "A")], flat, D_DEPLOYED,
                            confidence={("A", "B"): 0.5})
    pi_fwd = edge_precision([("A", "B")], flat, D_DEPLOYED,
                            confidence={("A", "B"): 0.5})
    check("confidence lookup is orientation-independent",
          abs(pi_rev[("B", "A")] - pi_fwd[("A", "B")]) < 1e-15)

    # 7. Refusals, each a real failure mode rather than a defensive reflex.
    for name, fn in [
        ("missing stalk floor is refused, not defaulted to 1",
         lambda: edge_precision([("A", "Z")], flat, D_DEPLOYED)),
        ("zero floor (infinite precision) is refused",
         lambda: edge_precision([("A", "B")], {"A": 0.0, "B": 0.1}, D_DEPLOYED)),
        ("confidence of 0 is refused, not clamped",
         lambda: report_variance(0.0, D_DEPLOYED)),
        ("confidence > 1 is refused, not clamped",
         lambda: report_variance(1.5, D_DEPLOYED)),
    ]:
        try:
            fn()
            raise AssertionError(f"FAILED: {name} (no exception raised)")
        except (KeyError, ValueError):
            ok += 1
            print(f"  [ok] {name}")

    # 8. The rejected alternative, stated as a test so it cannot creep back:
    #    the coupling weight is NOT a precision.
    coupling = {("A", "B"): 0.9, ("B", "C"): 0.4, ("C", "A"): 0.1}
    check("coupling weights all lie in [0,1] ...",
          all(0.0 <= w <= 1.0 for w in coupling.values()))
    check("... while derived precisions do not, so they are different objects",
          any(p > 1.0 for p in pi.values()))

    # 9. THE LOAD-BEARING ONE, against the real coherence.coherence rather than
    #    against the algebra: uniform pi must give a BIT-IDENTICAL rho, and real
    #    variation must actually move it. If the first half ever fails, switching
    #    this module on is a silent regime change and every historical rho is
    #    incomparable to every new one.
    import numpy as np
    import coherence as _coh

    rng = np.random.default_rng(7)
    V = ["P", "M", "S", "R"]
    E4 = [("P", "M"), ("M", "S"), ("S", "R"), ("R", "P")]
    X = {v: rng.normal(size=8) for v in V}
    flat4 = {v: 0.0023 for v in V}

    rho_none = _coh.coherence(X, E4, precision=None).rho
    rho_unif = _coh.coherence(
        X, E4, precision=edge_precision(E4, flat4, D_DEPLOYED)).rho
    check(f"uniform pi => rho bit-identical to pi=None ({rho_none!r})",
          rho_none == rho_unif)

    varied = {"P": 0.0023, "M": 0.05, "S": 0.0023, "R": 0.0023}
    rho_var = _coh.coherence(
        X, E4, precision=edge_precision(E4, varied, D_DEPLOYED)).rho
    check(f"a genuinely broader organ moves rho ({rho_var:.6f})",
          rho_var != rho_none)

    rho_conf = _coh.coherence(
        X, E4, precision=edge_precision(E4, flat4, D_DEPLOYED,
                                        confidence={("P", "M"): 0.2})).rho
    check(f"a low-confidence judgement moves rho ({rho_conf:.6f})",
          rho_conf != rho_none)

    print(f"\nAll {ok} pi_e tests passed.")


if __name__ == "__main__":
    _main()
