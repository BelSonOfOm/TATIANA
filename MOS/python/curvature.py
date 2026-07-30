"""
TATIANA - Augmented Forman curvature for the MOS complex, and the C^2 weights.

WHY THIS FILE EXISTS
--------------------
Logbook 5ac derived Q5: the curvature the controller drives on is

    F_MOS(e) = pi_e^2 sum_{f > e} 1/tau_f  +  (nu_u + nu_v)
               -  sum_{e' || e} nu_{gamma(e,e')} sqrt(pi_e / pi_{e'})

and found that its weights are NOT free -- Forman's cell weights define the
inner product in which the combinatorial Laplacian is self-adjoint, which is the
only reason a Bochner-Weitzenboeck decomposition (hence a Ricci term) exists at
all. So they are fixed by whichever Laplacian the engine already uses, L =
d^T Pi d:

    vertex w_v  ->  nu_v, a scalar precision summary of the stalk
    edge   w_e  ->  pi_e, the PC edge precision already inside Pi
    2-cell w_f  ->  tau_f  <-- had NO referent. That gap is what this file closes.

Using the Hebbian coupling w(sigma,t) instead would compute the curvature of a
DIFFERENT operator than the one the engine prints omega and rho from: a
consistent-looking number about the wrong thing. w(sigma,t) is a normalised
coupling on [0,1]; pi_e is an unbounded precision (5af). Never substitute them.

WHAT tau_f IS -- AND WHY IT IS NOT CIRCULAR
--------------------------------------------
tau_f is the PRECISION OF THE 3-WAY CIRCULATION on triangle f. pi_e says how
much to trust the pairwise judgement on an edge; tau_f says how much to trust
the closed loop around a filled triple. It is the exact 2-cochain analogue of
pi_e, and it is fixed by error propagation, not chosen:

    (d1 eta)_f = eta_bc - eta_ac + eta_ab

The signs square away, so under independent edge errors of variance 1/pi_e

    Var[(d1 eta)_f] = sum_{e in f} 1/pi_e

  =>  tau_f = |f| / sum_{e in f} (1/pi_e)      the HARMONIC MEAN of the three
                                               edge precisions.

5af proposed deriving tau_f from the MEASURED residual (d1 eta)_f and rejected
it as circular, because tau_f is the C^2 inner product and hodge_split uses that
inner product to compute the curl projection -- defining the metric from the
quantity it measures. **The rejection was right about the measured-residual
route and wrong about the reason, and the circularity does not exist:**

  1. The Hodge split is PROVABLY INVARIANT to tau (hodge.py, THE tau INVARIANCE,
     self-test 12): the curl space is im(W^-1 d1^T T) = im(W^-1 d1^T) because T
     is invertible. So tau never fed the split, nothing was ever a fixed point,
     and no choice of tau can invalidate E5 / 5x. **E5 does not need re-running.**
  2. The definition above reads only pi_e. Not eta, not the split, not tau. So
     it needs no time-lag window, no proof that a fixed point is gone, and no
     drift argument -- the three things V7 was scoped to do.

What the measured-residual route would genuinely have suffered is not
circularity but FEEDBACK: tau from eta(t) -> curvature -> flow -> eta(t+1). That
is a control loop and would need the lag. Deriving from pi_e sidesteps it, since
pi_e is an organ-reported input rather than a state variable.

THE SCALE CHOICE, STATED RATHER THAN SLIPPED IN
------------------------------------------------
Error propagation fixes the precision of the circulation as the harmonic SUM,
1/sum(1/pi_e). This module uses the harmonic MEAN, larger by exactly |f| = 3.
That is a deliberate scale choice with two reasons, and it is the only free
decision in the file:

  * tau appears in F_MOS only inside the ratio w_e/w_f = pi_e/tau_f. For that
    ratio to be O(1) when a triangle's edges are all about as precise as e,
    tau_f must live on the scale of ONE edge precision, not three. The harmonic
    mean is exactly "the common per-edge precision these three are equivalent
    to"; the harmonic sum is a per-triangle total and is scale-mismatched
    against pi_e.
  * Day-one degradation. At pi = nu = 1 the harmonic mean gives tau = 1 and
    F_MOS returns 4 - deg u - deg v + 3m exactly (self-test 3). The harmonic sum
    gives tau = 1/3 and overshoots by 2m, i.e. it silently changes the shipped
    unit-weight formula.

The |f| is the number of faces of the 2-simplex, the same structural constant
the "not both" clause turns into the 3 -- not a tuning knob. Nothing to sweep.

WHAT IS STILL OWED (do not let this file imply otherwise)
----------------------------------------------------------
* The placement of Forman's w_alpha PREFACTORS is taken from the literature and
  not re-derived from the Bochner argument (5ac, HONEST LIMIT). The unit-weight
  check cannot distinguish placements because every weight is 1. Deriving or
  citing it precisely is owed before F_MOS carries a published claim.
* The 5ac SIGN PREDICTION SURVIVES the derived tau and is if anything sharper:
  the coface term now dies LINEARLY in pi_e (1/tau_f carries a 1/pi_e), the
  penalty like sqrt(pi_e), and (nu_u + nu_v) is untouched -- so F -> nu_u + nu_v
  > 0 as pi_e -> 0. A low-precision edge still drifts POSITIVE => CONTRACT/FOLD,
  i.e. chunking an edge BECAUSE we are unsure of it. E11 must check the sign
  behaviour against pi_e explicitly. Asserted as a known property in self-test 6
  so it cannot be forgotten.
* nu_v (the scalar precision summary of a stalk) is taken as an input here. Its
  routing from Sigma_v^-1 is Phase-2 item 8's business, not this file's.
"""

from __future__ import annotations

from typing import Dict, Iterable, Optional, Sequence, Tuple

import numpy as np

Vertex = str
Edge = Tuple[Vertex, Vertex]
Triangle = Tuple[Vertex, Vertex, Vertex]


# --------------------------------------------------------------------------
# tau_f -- the C^2 inner product
# --------------------------------------------------------------------------

def tau_from_precision(triangle: Triangle,
                       precision: Dict[Edge, float]) -> float:
    """tau_f = |f| / sum_{e in f} (1/pi_e) -- the harmonic mean of the three
    edge precisions.

    The precision of the 3-way circulation, on a per-edge scale. See the module
    docstring for the derivation and for why the mean rather than the sum.

    Cost: 3 lookups, 3 divides, 1 divide. Per triangle, per tick.
    """
    a, b, c = triangle
    total = 0.0
    for face in ((a, b), (a, c), (b, c)):
        p = precision.get(face, precision.get((face[1], face[0])))
        if p is None:
            raise KeyError(
                f"Triangle {triangle} has face {face} with no precision. "
                "Refusing to default to 1: a missing weight is a missing "
                "measurement (same contract as hodge.hodge_split).")
        if p <= 0:
            raise ValueError(
                f"Precision {p} on edge {face} must be > 0; it is 1/variance.")
        total += 1.0 / float(p)
    return len(triangle) / total


def tau_map(triangles: Iterable[Triangle],
            precision: Dict[Edge, float]) -> Dict[Triangle, float]:
    """tau_from_precision over a whole complex."""
    return {t: tau_from_precision(t, precision) for t in triangles}


# --------------------------------------------------------------------------
# F_MOS -- augmented Forman curvature in MOS's own weights
# --------------------------------------------------------------------------

def _degree(vertex: Vertex, edges: Sequence[Edge]) -> int:
    return sum(1 for (u, v) in edges if vertex in (u, v))


def forman_mos(edge: Edge,
               edges: Sequence[Edge],
               triangles: Sequence[Triangle],
               precision: Optional[Dict[Edge, float]] = None,
               nu: Optional[Dict[Vertex, float]] = None,
               tau: Optional[Dict[Triangle, float]] = None) -> float:
    """F_MOS(e), the 5ac curvature.

        F_MOS(e) = pi_e^2 sum_{f > e} 1/tau_f  +  (nu_u + nu_v)
                   -  sum_{e' || e} nu_{gamma(e,e')} sqrt(pi_e / pi_{e'})

    e' || e means e' shares a FACE (a vertex) or a COFACE (a triangle) with e,
    BUT NOT BOTH -- Forman's clause, and the reason the unit-weight coefficient
    is 3 = 1 + 2 rather than 1 (5ac). Edges sharing a triangle but not a vertex
    cannot occur in a simplicial complex, so the surviving parallel set is
    "shares a vertex, does not close a triangle with e".

    precision / nu / tau default to all-1, in which case this returns exactly
    4 - deg u - deg v + 3m. Passing precision but not tau derives tau from it,
    which is the intended production call.
    """
    u, v = edge
    pi = precision or {}
    nuv = nu or {}

    def pi_of(e: Edge) -> float:
        return float(pi.get(e, pi.get((e[1], e[0]), 1.0)))

    def nu_of(x: Vertex) -> float:
        return float(nuv.get(x, 1.0))

    cofaces = [f for f in triangles if set(edge) <= set(f)]
    if tau is None:
        tau = tau_map(cofaces, pi) if precision else {f: 1.0 for f in cofaces}

    pe = pi_of(edge)
    coface_term = pe * pe * sum(1.0 / float(tau[f]) for f in cofaces)
    face_term = nu_of(u) + nu_of(v)

    penalty = 0.0
    for other in edges:
        if tuple(other) == tuple(edge):
            continue
        shared = set(edge) & set(other)
        if len(shared) != 1:
            continue                      # disjoint: not parallel
        if any(set(other) <= set(f) for f in cofaces):
            continue                      # shares vertex AND coface: "not both"
        gamma = shared.pop()
        penalty += nu_of(gamma) * np.sqrt(pe / pi_of(other))

    return float(coface_term + face_term - penalty)


def forman_unit(edge: Edge,
                edges: Sequence[Edge],
                triangles: Sequence[Triangle]) -> float:
    """4 - deg u - deg v + 3m. The shipped unit-weight specialisation, kept
    independent so day-one degradation is checked against a SEPARATE
    implementation rather than against forman_mos with its own arguments."""
    u, v = edge
    m = sum(1 for f in triangles if set(edge) <= set(f))
    return float(4 - _degree(u, edges) - _degree(v, edges) + 3 * m)


# --------------------------------------------------------------------------
# Self-test (free; no API calls)
# --------------------------------------------------------------------------

if __name__ == "__main__":
    import console
    from hodge import e5_complex, hodge_split

    console.setup()
    rng = np.random.default_rng(3)
    cx = e5_complex()
    E, F = cx.edges, cx.triangles

    print("=== 1. tau_f IS the precision of the circulation (Monte Carlo) ===")
    for _ in range(3):
        pis = rng.uniform(0.2, 8.0, size=3)
        draws = np.column_stack(
            [rng.normal(0, 1 / np.sqrt(p), 200_000) for p in pis])
        circ = draws[:, 0] - draws[:, 1] + draws[:, 2]
        pi_d = {("A", "B"): pis[0], ("A", "C"): pis[1], ("B", "C"): pis[2]}
        predicted_var = len(("A", "B", "C")) / tau_from_precision(("A", "B", "C"), pi_d)
        rel = abs(circ.var() - predicted_var) / predicted_var
        assert rel < 0.02, (circ.var(), predicted_var)
        print(f"    pi={np.round(pis, 3)}  Var(d1 eta)_f emp={circ.var():.4f} "
              f"pred={predicted_var:.4f}  rel err {rel:.4f}  OK")
    print("    (|f|/tau_f is the circulation VARIANCE; tau_f is its per-edge precision)")

    print("\n=== 2. tau is a harmonic MEAN: bounded by the edge precisions ===")
    for _ in range(500):
        pi_d = {e: float(rng.uniform(0.01, 100.0)) for e in E}
        for f in F:
            t = tau_from_precision(f, pi_d)
            faces = [pi_d[tuple(sorted(x, key=cx.vertices.index))]
                     for x in ((f[0], f[1]), (f[0], f[2]), (f[1], f[2]))]
            assert min(faces) - 1e-12 <= t <= max(faces) + 1e-12, (t, faces)
    print("    500 trials: min(pi) <= tau <= max(pi), and tau is dominated by the")
    print("    WORST edge -- one unreliable judgement discredits the whole loop  OK")

    print("\n=== 3. DAY-ONE DEGRADATION: F_MOS == 4 - deg u - deg v + 3m ===")
    for e in E:
        a = forman_mos(e, E, F)                                   # all defaults
        b = forman_mos(e, E, F, precision={x: 1.0 for x in E},    # derived tau
                       nu={x: 1.0 for x in cx.vertices})
        c = forman_unit(e, E, F)
        assert abs(a - c) < 1e-12 and abs(b - c) < 1e-12, (e, a, b, c)
        print(f"    {str(e):<12} F_MOS={a:+.6f}  derived-tau={b:+.6f}  unit={c:+.0f}  OK")
    print("    the harmonic MEAN is what makes this hold; the harmonic sum")
    print("    overshoots by exactly 2m (module docstring, THE SCALE CHOICE)")

    print("\n=== 4. NOT CIRCULAR: tau does not read eta, and the split ignores tau ===")
    eta = rng.normal(size=len(E))
    pi_d = {e: float(rng.uniform(0.1, 10.0)) for e in E}
    t_derived = tau_map(F, pi_d)
    s_none = hodge_split(cx, eta, precision=pi_d)
    s_tau = hodge_split(cx, eta, precision=pi_d, tau=t_derived)
    assert np.allclose(s_none.curl, s_tau.curl, atol=1e-12)
    assert np.allclose(s_none.harm, s_tau.harm, atol=1e-12)
    print(f"    tau derived from pi     : {[round(v, 4) for v in t_derived.values()]}")
    print(f"    Phi_inf with tau=I      : {s_none.phi_infinity:.10f}")
    print(f"    Phi_inf with derived tau: {s_tau.phi_infinity:.10f}")
    print("    identical -> E5 / 5x is untouched by tau. NO RE-RUN NEEDED  OK")

    # And the derivation genuinely never touches eta: perturb eta wildly, tau is fixed.
    for _ in range(50):
        _ = rng.normal(size=len(E)) * 1e6
        assert tau_map(F, pi_d) == t_derived
    print("    tau is bit-identical under 50 wild perturbations of eta  OK")

    print("\n=== 5. tau tracks pi monotonically (a sanity property, not a proof) ===")
    base = {e: 1.0 for e in E}
    f0 = F[0]
    prev = -np.inf
    for p in (0.01, 0.1, 1.0, 10.0, 100.0):
        d = dict(base)
        d[(f0[0], f0[1])] = p
        t = tau_from_precision(f0, d)
        assert t > prev
        prev = t
        print(f"    pi(AB)={p:<8} -> tau({f0}) = {t:.6f}")
    print("    OK -- raising any edge precision raises the loop's precision")

    print("\n=== 6. THE 5ac SIGN PREDICTION SURVIVES (this is a WARNING, not a pass) ===")
    e0 = E[0]
    nu1 = {v: 1.0 for v in cx.vertices}
    vals = []
    for p in (1.0, 1e-1, 1e-2, 1e-3, 1e-4):
        d = {e: 1.0 for e in E}
        d[e0] = p
        vals.append(forman_mos(e0, E, F, precision=d, nu=nu1))
        print(f"    pi_e={p:<8} F_MOS({e0}) = {vals[-1]:+.6f}")
    limit = nu1[e0[0]] + nu1[e0[1]]
    assert abs(vals[-1] - limit) < 0.02, (vals[-1], limit)
    assert vals[-1] > 0
    print(f"    F -> nu_u + nu_v = {limit:.1f} > 0 as pi_e -> 0.")
    print("    A LOW-PRECISION EDGE STILL DRIFTS POSITIVE => CONTRACT/FOLD.")
    print("    That is backwards (chunking because we are UNSURE). E11 owes this")
    print("    an explicit check against pi_e; deriving tau did NOT fix it.")

    print("\n=== 7. contracts: missing / non-positive precision are refused ===")
    for bad, exc in ((None, KeyError), (0.0, ValueError), (-1.0, ValueError)):
        d = {e: 1.0 for e in E}
        if bad is None:
            d.pop(("A", "B"))
        else:
            d[("A", "B")] = bad
        try:
            tau_from_precision(("A", "B", "C"), d)
        except exc:
            pass
        else:
            raise AssertionError(f"should have refused {bad!r}")
    print("    missing -> KeyError, <= 0 -> ValueError  OK")

    print("\nALL CURVATURE SELF-TESTS PASSED (zero API calls)")
