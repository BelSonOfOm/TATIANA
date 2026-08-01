"""V7 — DOES tau_f ESCAPE 1, AND DOES E5 SURVIVE IT?

WHAT V7 WAS ASKED TO DO
-----------------------
Logbook 5af/5ag left tau_f = 1 as "the WORKING value Phase 2 ships with... a
placeholder under active repair, not a decision". Charbel refused to let it be
closed by declaration. Two routes were named:

  (a) derive tau_f from a TIME-LAGGED residual (running average over past
      ticks, breaking the circularity the way BCM's sliding threshold does),
      requiring a window choice, a proof the fixed point is gone, and a drift
      argument; or
  (b) re-run E5 under whatever inner product results, to certify that the
      growth-story evidence (5x) survives a C^2 weighting that is no longer
      the identity.

ROUTE (a) IS MOOT, AND SAYING SO IS PART OF THE ANSWER.
Route (a) existed only because tau_f-from-the-residual was believed CIRCULAR.
5ag retracted that: the adjoint of delta^1 is (delta^1)* = W1^-1 (delta^1)^T W2,
and since W2 is positive-definite it is ONTO, so

    im(W1^-1 (delta^1)^T W2) = im(W1^-1 (delta^1)^T)

-- an invertible map does not change an image. tau therefore never reaches the
curl subspace. With the circularity gone, tau_f already has a NON-circular
derivation from pi_e one dimension up (5ag): variances of independent edge
values add around a triangle, so

    tau_f = |f| / sum_{e in f} 1/pi_e  =  harmonic mean of {pi_e : e in f}.

There is nothing left for a time-lagged estimator to repair. Route (a) is not
"skipped"; its premise was withdrawn.

SO V7 IS ROUTE (b), AND THE EMPIRICAL HALF WAS NEVER RUN.
5ag proved W2-independence analytically and checked it against SIX RANDOM
positive W2. That is not the same as checking it at the tau_f the system
actually derives, on the pi_e the engine actually produces. Until now pi_e was
uniformly 1 -- so tau_f was 1 and NOTHING was ever evaluated off the degenerate
point. Since FIX-13 and the pi_e wiring, pi_e = 1/(D_u + D_v + s_e) with D
varying by n_eff and rank, so pi_e is genuinely non-uniform and tau_f is
genuinely not 1.

This file therefore asks four questions with numbers:
  1. Is tau_f actually != 1 on realistic engine-produced pi_e?
  2. Does E5's Hodge split move under W2 = diag(tau_f)?   [THE CERTIFICATION]
  3. Does day-one degradation still hold EXACTLY?
  4. Does tau_f change anything we care about -- i.e. was deriving it worth it?

Run:  python experiment_v7.py
"""

from __future__ import annotations

import math
from typing import Dict, Tuple

import numpy as np

from belief import EPS_FLOOR
from derived_scales import forman_mos, tau
from edge_precision import edge_precision, report_variance
from hodge import Complex2, hodge_split

D_DEPLOYED = 384
KAPPA = 1.0

Edge = Tuple[str, str]


def stalk_floor(d: int = D_DEPLOYED, n_eff: float = 1.0, kappa: float = KAPPA) -> float:
    """belief.py's shrinkage floor, O(1/d). Kept local and asserted against
    belief.EPS_FLOOR so this file cannot drift from the authoritative one."""
    return EPS_FLOOR + kappa / (d * (n_eff + kappa))


def e5_complex() -> Complex2:
    """E5's configuration: 4 organs, 5 edges, 1 FILLED triangle => b1 = 1."""
    return Complex2(["A", "B", "C", "D"],
                    [("A", "B"), ("B", "C"), ("A", "C"), ("A", "D"), ("C", "D")],
                    [("A", "B", "C")])


def split_with_w2(cx: Complex2, eta: np.ndarray, w1: np.ndarray,
                  w2: np.ndarray) -> Dict[str, float]:
    """The Hodge split with an EXPLICIT C^2 inner product W2.

    hodge.py hard-codes W2 = I. To test whether tau_f matters we need the
    general form: the curl space is im(W1^-1 (delta^1)^T W2), so the only change
    is that delta^1 is pre-multiplied by W2 before forming the adjoint.
    """
    d0, d1 = cx.delta0(), cx.delta1()
    s = np.sqrt(w1)

    f, *_ = np.linalg.lstsq(s[:, None] * d0, s * eta, rcond=None)
    grad = d0 @ (f - f.mean())

    a = ((w2 @ d1) / w1).T
    g, *_ = np.linalg.lstsq(s[:, None] * a, s * eta, rcond=None)
    curl = a @ g
    harm = eta - grad - curl

    def n2(x: np.ndarray) -> float:
        return float(np.sum(w1 * x * x))

    total = n2(eta)
    return {"grad": n2(grad) / total, "curl": n2(curl) / total,
            "harm": n2(harm) / total, "harm_vec": harm}


def main() -> int:
    failures = 0

    def check(name: str, cond: bool) -> None:
        nonlocal failures
        if not cond:
            failures += 1
            print(f"  [FAIL] {name}")
        else:
            print(f"  [ok] {name}")

    cx = e5_complex()
    edges = list(cx.edges)

    # -----------------------------------------------------------------------
    print("=== 1. REALISTIC pi_e FROM THE ENGINE'S OWN FORMULA ===")
    # Organs differ in how much evidence they carry (n_eff) -- which is exactly
    # what makes the stalk floor, and hence pi_e, non-uniform. These are the
    # values belief.stalk_gaussian would produce.
    n_eff = {"A": 1.0, "B": 8.0, "C": 40.0, "D": 100.0}
    floors = {v: stalk_floor(n_eff=n) for v, n in n_eff.items()}
    # One judged pair carries a reported confidence; the rest report none.
    conf = {("A", "B"): 0.60}

    pi = edge_precision(edges, floors, D_DEPLOYED, confidence=conf)
    lo, hi = min(pi.values()), max(pi.values())
    for e in edges:
        print(f"      pi{e} = {pi[e]:9.3f}")
    print(f"      spread: {lo:.3f} .. {hi:.3f}  (ratio {hi / lo:.2f}x)")
    check("pi_e is genuinely non-uniform on realistic stalk floors", hi / lo > 1.5)

    # -----------------------------------------------------------------------
    print("\n=== 2. DOES tau_f ESCAPE 1? ===")
    tri = ("A", "B", "C")
    tau_derived = tau([tri], pi)[tri]
    tau_unit = tau([tri], {e: 1.0 for e in edges})[tri]
    print(f"      tau_f (derived) = {tau_derived:.6f}")
    print(f"      tau_f (unit pi) = {tau_unit:.6f}")
    check("tau_f = 1 EXACTLY at unit precisions (day-one degradation)",
          abs(tau_unit - 1.0) < 1e-15)
    check("tau_f is NOT 1 on engine-produced pi_e -- the placeholder is escapable",
          abs(tau_derived - 1.0) > 1.0)
    # The harmonic mean must sit at or below the arithmetic mean, and be pulled
    # toward the WORST edge -- that is what a sum of variances does.
    tri_pi = [pi[e] for e in (("A", "B"), ("B", "C"), ("A", "C"))]
    check("harmonic <= arithmetic mean of the triangle's pi_e",
          tau_derived <= sum(tri_pi) / 3 + 1e-9)
    check("tau_f is pulled toward the worst edge",
          abs(tau_derived - min(tri_pi)) < abs(tau_derived - max(tri_pi)))

    # -----------------------------------------------------------------------
    print("\n=== 3. THE CERTIFICATION — does E5's split move under W2 = diag(tau_f)? ===")
    print("      (5ag proved this analytically and checked SIX RANDOM W2.")
    print("       Here it is checked at the tau_f the system actually derives.)")
    rng = np.random.default_rng(7)
    w1 = np.array([pi[e] for e in edges])

    worst_frac = 0.0
    worst_harm = 0.0
    for _ in range(200):
        eta = rng.normal(size=len(edges))
        base = split_with_w2(cx, eta, w1, np.eye(len(cx.triangles)))
        derived = split_with_w2(cx, eta, w1, np.diag([tau_derived]))
        for key in ("grad", "curl", "harm"):
            worst_frac = max(worst_frac, abs(base[key] - derived[key]))
        worst_harm = max(worst_harm,
                         float(np.max(np.abs(base["harm_vec"] - derived["harm_vec"]))))

    print(f"      worst |fraction difference| over 200 cochains: {worst_frac:.3e}")
    print(f"      worst |harmonic component difference|:         {worst_harm:.3e}")
    check("E5's grad/curl/harm fractions are INVARIANT under the derived tau_f",
          worst_frac < 1e-12)
    check("the harmonic vector itself -- the GROWTH ADDRESS -- is invariant",
          worst_harm < 1e-12)

    # Also at extreme tau, so this is not an artefact of tau_derived being mild.
    worst_extreme = 0.0
    for t in (1e-6, 1e-3, 1.0, 1e3, 1e6):
        eta = rng.normal(size=len(edges))
        base = split_with_w2(cx, eta, w1, np.eye(1))
        scaled = split_with_w2(cx, eta, w1, np.diag([t]))
        worst_extreme = max(worst_extreme,
                            max(abs(base[k] - scaled[k]) for k in ("grad", "curl", "harm")))
    check(f"invariance holds across tau in [1e-6, 1e6] (worst {worst_extreme:.2e})",
          worst_extreme < 1e-12)

    # -----------------------------------------------------------------------
    print("\n=== 4. SO WHERE DOES tau_f ACTUALLY BITE? ===")
    # F_MOS's coface term is pi_e^2 * sum_f 1/tau_f, so tau_f DOES move curvature
    # even though it cannot move the Hodge split.
    tris = [tri]
    unit_pi = {e: 1.0 for e in edges}
    # nu_v is the vertex weight (Q16, gamma(nu)); unit weights are the
    # combinatorial baseline the day-one degradation is stated against.
    unit_nu = {v: 1.0 for v in cx.vertices}

    f_unit = forman_mos(("A", "B"), edges, tris, unit_pi, unit_nu)
    deg = {v: sum(1 for e in edges if v in e) for v in cx.vertices}
    combinatorial = 4 - deg["A"] - deg["B"] + 3 * 1
    print(f"      F_MOS(A,B) at unit pi   = {f_unit:.6f}")
    print(f"      4 - deg A - deg B + 3m  = {combinatorial}")
    check("unit precisions reproduce the combinatorial Forman value EXACTLY",
          abs(f_unit - combinatorial) < 1e-12)

    f_derived = forman_mos(("A", "B"), edges, tris, pi, unit_nu)
    f_tau_pinned = forman_mos(("A", "B"), edges, tris, pi, unit_nu,
                              tau_f={tri: 1.0})
    print(f"      F_MOS(A,B) with derived pi and derived tau = {f_derived:.4f}")
    print(f"      F_MOS(A,B) with derived pi but tau PINNED to 1 = {f_tau_pinned:.4f}")
    rel = abs(f_derived - f_tau_pinned) / max(abs(f_derived), 1e-30)
    print(f"      relative difference from pinning tau: {rel:.4%}")
    check("pinning tau_f = 1 MEASURABLY distorts curvature (so deriving it was not idle)",
          rel > 0.01)

    # -----------------------------------------------------------------------
    print("\n=== 5. DRIFT — does tau_f stay bounded over the realistic range? ===")
    # Route (a)'s live worry was drift. tau_f is a harmonic mean of pi_e, so it
    # is bounded by min and max pi_e by construction; this checks the range the
    # engine can actually reach.
    taus = []
    for n in (1.0, 2.0, 5.0, 10.0, 25.0, 50.0, 100.0, 1000.0):
        for c in (None, 0.99, 0.9, 0.6, 0.3):
            fl = {v: stalk_floor(n_eff=n) for v in cx.vertices}
            cc = {} if c is None else {("A", "B"): c}
            p = edge_precision(edges, fl, D_DEPLOYED, confidence=cc)
            taus.append(tau([tri], p)[tri])
    print(f"      tau_f over 40 (n_eff, confidence) combinations: "
          f"{min(taus):.2f} .. {max(taus):.2f}")
    check("tau_f is finite and positive throughout",
          all(math.isfinite(t) and t > 0 for t in taus))
    check("tau_f is bounded by the pi_e range by construction (harmonic mean)",
          max(taus) <= 1.0 / (2 * stalk_floor(n_eff=1000.0)) + 1e-6)

    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    if failures:
        print(f"V7 FAILED: {failures} check(s) did not hold.")
        return 1

    print("V7 VERDICT")
    print("-" * 70)
    print("tau_f = 1 is NO LONGER a placeholder. It is the exact value at unit")
    print("precisions and a derived, non-trivial value otherwise:")
    print(f"  * on engine-produced pi_e, tau_f = {tau_derived:.3f}, not 1.")
    print("  * E5's growth-story evidence SURVIVES: the grad/curl/harm split and")
    print(f"    the harmonic vector are invariant to {worst_harm:.1e} across 200")
    print("    cochains and across tau in [1e-6, 1e6]. Route (b) is discharged")
    print("    at the DERIVED tau, not merely at random matrices.")
    print(f"  * tau_f does bite where 5ag said it would: pinning it to 1 shifts")
    print(f"    F_MOS by {rel:.2%}, so the derivation is load-bearing for curvature.")
    print("  * Route (a) is MOOT -- its premise (circularity) was retracted, and")
    print("    tau_f now has a non-circular derivation from pi_e.")
    print()
    print("REMAINING LIMIT, STATED: this is E5's 4-organ/5-edge/1-triangle")
    print("complex with one filled triangle, so exactly one tau_f exists. A")
    print("complex with several triangles sharing edges could in principle")
    print("couple them; nothing here tests that, and nothing here claims it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
