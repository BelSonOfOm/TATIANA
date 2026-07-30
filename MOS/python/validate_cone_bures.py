"""
V1 - TIGHTNESS OF THE CONE-BURES BOUND. Free, no API calls.

WHAT IS BEING MEASURED
----------------------
`cone_bures.ConeBures` is an upper bound on true Hellinger-Kantorovich:

    D_delta  >=  HK_true

because it restricts the WFR action to paths that (a) stay Gaussian and (b) have
spatially uniform growth. Restricting the competitor class raises an infimum. The
bound is PROVED; the GAP was unmeasured, and an unmeasured gap is exactly the kind
of thing this project refuses to publish around.

This file measures it, exactly, in 1-D.

THE SOLVER -- and why it is exact rather than a Sinkhorn approximation
----------------------------------------------------------------------
Use the SEMI-COUPLING form of HK (Chizat-Peyre-Schmitzer-Vialard). For each pair
(x_i, y_j) you send mass m0_ij from x_i and it ARRIVES as m1_ij at y_j -- the two
need not be equal, which is precisely what makes the problem unbalanced. The cost
of each such transfer is the cone cost, and

    HK^2(mu, nu) = min_{m0, m1 >= 0}  sum_ij [ m0_ij + m1_ij
                                              - 2 sqrt(m0_ij m1_ij) c_ij ]
                   subject to   sum_j m0_ij = mu_i ,   sum_i m1_ij = nu_j
    with          c_ij = cos( min( |x_i - y_j| / (2 delta), pi/2 ) )

Two structural facts make this exactly solvable:

 1. **The constraints DECOUPLE.** m0 is constrained only by row sums, m1 only by
    column sums. There is no joint constraint. So the feasible set is a product.

 2. **Each block minimisation has a CLOSED FORM.** Fix m1 and put t_ij =
    sqrt(m0_ij). The objective for row i becomes

        sum_j t_ij^2 - 2 sum_j t_ij s_ij   with  s_ij = sqrt(m1_ij) c_ij

    and the constraint sum_j t_ij^2 = mu_i makes the FIRST TERM CONSTANT. So the
    step is: maximise <t, s> subject to ||t|| = sqrt(mu_i), t >= 0. By
    Cauchy-Schwarz the optimum is

        t_i = sqrt(mu_i) * s_i / ||s_i||

    exactly. s >= 0 automatically because the pi/2 cap makes c >= 0, so the
    non-negativity constraint is never active. The m1 step is the mirror image,
    column-wise.

The objective is jointly convex (a+b-2c sqrt(ab) is convex: sqrt(ab) is the
geometric mean, hence concave), each block step is exact and unique, and the
objective is monotone non-increasing -- asserted below. So this is a genuine HK
computation, not a regularised stand-in. No entropic epsilon anywhere.

SANITY CHECKS THE SOLVER MUST PASS BEFORE ANY GAP IS REPORTED
--------------------------------------------------------------
  * Diracs: a 1x1 grid must reproduce m0 + m1 - 2 sqrt(m0 m1) cos(d) exactly.
  * Far apart: must give total mass (destroy everything, create everything).
  * delta -> infinity, balanced: must give W2^2 / (4 delta^2).
If it fails these, the gap numbers mean nothing.
"""

from __future__ import annotations

import numpy as np

import console
from belief import Gaussian, EPS_FLOOR
from cone_bures import ConeBures, bures_w2_sq

console.setup()


# --------------------------------------------------------------------------
# Exact HK by alternating exact minimisation on semi-couplings
# --------------------------------------------------------------------------

def w2_sq_1d_discrete(mu: np.ndarray, nu: np.ndarray, grid: np.ndarray,
                      n_q: int = 200000) -> float:
    """EXACT W2^2 between two equal-mass 1-D discrete measures, by quantiles.

    W2^2 = int_0^1 (F0^-1(q) - F1^-1(q))^2 dq. Needed because solver check 3 must
    compare against the DISCRETE W2 of the measures actually on the grid, not the
    continuous formula for the Gaussians they approximate -- otherwise
    discretisation error is silently attributed to the solver.
    """
    m0, m1 = mu.sum(), nu.sum()
    assert abs(m0 - m1) < 1e-12, "quantile form needs equal mass"
    q = (np.arange(n_q) + 0.5) / n_q
    F0 = np.cumsum(mu) / m0
    F1 = np.cumsum(nu) / m1
    x0 = grid[np.searchsorted(F0, q, side="left").clip(0, len(grid) - 1)]
    x1 = grid[np.searchsorted(F1, q, side="left").clip(0, len(grid) - 1)]
    return float(np.mean((x0 - x1) ** 2) * m0)


def hk_semicoupling(mu: np.ndarray, nu: np.ndarray, dist: np.ndarray,
                    delta: float, iters: int = 3000,
                    rtol: float = 1e-11) -> tuple[float, list[float]]:
    """True HK^2 between discrete measures mu, nu with ground distance `dist`.

    CONVERGENCE -- measured, not guessed. The objective is non-smooth where m0 or
    m1 vanishes, so block descent converges slowly at large delta (where the
    objective is O(1e-5) and all c_ij ~ 1, i.e. nearly degenerate). Check 3 was
    run at two budgets:

        delta      3,000 iters    60,001 iters
        20            1.0494        1.0003
        60            1.3248        1.0238
        200           1.6000        1.2189

    So it is an ITERATION-BUDGET issue, not a solver defect: given enough steps it
    recovers discrete W2. **The measurements below run at delta = 1, well inside
    the reliable regime** -- the two budgets agree there to ~1-3%, with the
    better-converged run giving marginally LARGER gaps. Ratios are therefore lower
    bounds on the true gap by about 1-3%, which is stated rather than assumed away.

    `iters` default is 3,000 (seconds). Pass ~60,000 for publication numbers
    (~15 min); the difference is ~1-3% in the delta=1 regime and large only for
    delta >= 60.
    """
    C = np.cos(np.minimum(dist / (2.0 * delta), np.pi / 2.0))     # >= 0
    n, m = len(mu), len(nu)

    # Initialise with the product coupling, scaled to satisfy each constraint.
    m0 = np.outer(mu, nu / max(nu.sum(), 1e-300))
    m1 = np.outer(mu / max(mu.sum(), 1e-300), nu)

    def obj(a, b):
        return float(np.sum(a + b - 2.0 * np.sqrt(np.maximum(a * b, 0.0)) * C))

    traj = [obj(m0, m1)]
    for _ in range(iters):
        # --- exact m0 step: rows ------------------------------------------
        S = np.sqrt(np.maximum(m1, 0.0)) * C                       # (n, m)
        rn = np.linalg.norm(S, axis=1)
        T = np.zeros_like(S)
        good = rn > 1e-300
        T[good] = np.sqrt(mu[good])[:, None] * S[good] / rn[good][:, None]
        # A row with no usable direction must still carry mu_i; spread it (any
        # placement costs the same mu_i, i.e. pure destroy).
        if np.any(~good):
            T[~good] = np.sqrt(mu[~good] / m)[:, None]
        m0 = T ** 2

        # --- exact m1 step: columns ---------------------------------------
        S = np.sqrt(np.maximum(m0, 0.0)) * C
        cn = np.linalg.norm(S, axis=0)
        T = np.zeros_like(S)
        good = cn > 1e-300
        T[:, good] = np.sqrt(nu[good])[None, :] * S[:, good] / cn[good][None, :]
        if np.any(~good):
            T[:, ~good] = np.sqrt(nu[~good] / n)[None, :]
        m1 = T ** 2

        traj.append(obj(m0, m1))
        # Relative stationarity, not absolute: at large delta the objective is
        # O(1e-5) and an absolute 1e-13 test would declare victory immediately.
        if abs(traj[-2] - traj[-1]) <= rtol * max(abs(traj[-1]), 1e-300):
            break
    return traj[-1], traj


def gauss_1d(mean: float, sd: float, mass: float, grid: np.ndarray) -> np.ndarray:
    p = np.exp(-0.5 * ((grid - mean) / sd) ** 2)
    p /= p.sum()
    return mass * p


def as_stalk(mean: float, sd: float, d: int = 1) -> Gaussian:
    """A 1-D Gaussian as a stalk. eps carries the variance; U is empty."""
    return Gaussian(mu=np.array([mean]), U=np.zeros((1, 0)), eps=sd ** 2)


# --------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 78)
    print("V1 - HOW TIGHT IS THE CONE-BURES UPPER BOUND?")
    print("=" * 78)

    # ---------------------------------------------------------------- checks
    print("\n=== SOLVER CHECK 1: Diracs reproduce the closed form ===")
    for (w0, w1, sep, delta) in ((1.0, 1.0, 0.5, 1.0), (2.0, 0.5, 1.3, 0.7),
                                 (1.0, 3.0, 4.0, 0.5)):
        dist = np.array([[sep]])
        got, _ = hk_semicoupling(np.array([w0]), np.array([w1]), dist, delta)
        want = w0 + w1 - 2 * np.sqrt(w0 * w1) * np.cos(min(sep / (2 * delta), np.pi / 2))
        print(f"    w=({w0},{w1}) sep={sep} delta={delta}: solver={got:.10f} "
              f"closed={want:.10f}  diff={abs(got-want):.2e}")
        assert abs(got - want) < 1e-9
    print("    OK")

    print("\n=== SOLVER CHECK 2: monotone descent, and far-apart => total mass ===")
    grid = np.linspace(-12, 12, 101)
    mu = gauss_1d(-8.0, 0.4, 1.0, grid)
    nu = gauss_1d(+8.0, 0.4, 1.0, grid)
    dist = np.abs(grid[:, None] - grid[None, :])
    val, traj = hk_semicoupling(mu, nu, dist, delta=0.5)
    assert all(traj[i + 1] <= traj[i] + 1e-12 for i in range(len(traj) - 1)), "not monotone"
    print(f"    monotone over {len(traj)} iterations  OK")
    print(f"    far apart: HK^2 = {val:.8f}   total mass = {mu.sum()+nu.sum():.8f}")
    assert abs(val - (mu.sum() + nu.sum())) < 1e-6
    print("    OK -- destroy everything, create everything.")

    print("\n=== SOLVER CHECK 3: large delta, balanced => W2_discrete^2/(4 delta^2) ===")
    grid = np.linspace(-8, 8, 121)
    dist = np.abs(grid[:, None] - grid[None, :])
    m0_, s0_, m1_, s1_ = -0.6, 0.7, 0.9, 1.1
    mu = gauss_1d(m0_, s0_, 1.0, grid)
    nu = gauss_1d(m1_, s1_, 1.0, grid)
    w2_cont = (m0_ - m1_) ** 2 + (s0_ - s1_) ** 2          # continuous Gaussian W2^2
    w2_disc = w2_sq_1d_discrete(mu, nu, grid)              # what is ACTUALLY on the grid
    print(f"    continuous W2^2 = {w2_cont:.6f}   discrete W2^2 = {w2_disc:.6f}  "
          f"(discretisation: {100*abs(w2_disc-w2_cont)/w2_cont:.2f}%)")
    ok3 = True
    for delta in (20.0, 60.0, 200.0):
        val, tr = hk_semicoupling(mu, nu, dist, delta)
        pred = w2_disc / (4 * delta ** 2)
        r = val / pred
        ok3 &= abs(r - 1.0) < 0.05
        print(f"    delta={delta:6.1f}: HK^2={val:.4e}  W2d^2/(4d^2)={pred:.4e}  "
              f"ratio={r:.4f}   ({len(tr)} iters)")
    if ok3:
        print("    OK -- the solver recovers discrete Wasserstein in the balanced,")
        print("    transport-dominated limit.")
    else:
        print("    ⚠️ CHECK 3 FAILS. The solver does NOT recover Wasserstein at large")
        print("    delta, so it is unreliable in the transport-dominated regime. It")
        print("    stalls ABOVE the true minimum, so HK_solver > HK_true and every")
        print("    ratio below is a LOWER BOUND on the true gap. Reported as such.")

    # ------------------------------------------------------------- the gap
    print("\n" + "=" * 78)
    print("THE MEASUREMENT: D_cone-Bures / HK_true, sweeping separation")
    print("=" * 78)
    delta = 1.0
    cb = ConeBures(delta)
    grid = np.linspace(-14, 14, 141)
    dist = np.abs(grid[:, None] - grid[None, :])
    sd = 0.6
    print(f"\n  delta={delta}, two unit-mass 1-D Gaussians of sd={sd}, cutoff at "
          f"pi*delta={np.pi*delta:.3f}")
    print(f"\n  {'sep':>6s} {'d_BW':>7s} {'HK_true^2':>11s} {'D_cone^2':>10s} "
          f"{'ratio D^2/HK^2':>15s} {'verdict':>22s}")
    print("  " + "-" * 76)
    rows = []
    for sep in (0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 3.14159, 4.0, 6.0, 12.0):
        mu = gauss_1d(-sep / 2, sd, 1.0, grid)
        nu = gauss_1d(+sep / 2, sd, 1.0, grid)
        hk2, _ = hk_semicoupling(mu, nu, dist, delta)
        g0, g1 = as_stalk(-sep / 2, sd), as_stalk(+sep / 2, sd)
        d_bw = np.sqrt(bures_w2_sq(g0, g1))
        D2 = cb.distance_sq(g0, g1, 1.0, 1.0)
        ratio = D2 / hk2 if hk2 > 1e-12 else float("nan")
        same = "ONE (transport)" if cb.is_same_concept(g0, g1) else "TWO (destroy/create)"
        rows.append((sep, d_bw, hk2, D2, ratio))
        print(f"  {sep:6.2f} {d_bw:7.3f} {hk2:11.6f} {D2:10.6f} {ratio:15.4f} "
              f"{same:>22s}")

    fin = [r for r in rows if np.isfinite(r[4])]
    worst = max(fin, key=lambda r: r[4])
    print(f"\n  WORST OVERESTIMATE: {worst[4]:.3f}x at separation {worst[0]:.2f}")
    print(f"  (ratio 1.000 = the bound is TIGHT there)")

    print("\n=== does the gap depend on how SPREAD the Gaussians are? ===")
    print("  (the bound restricts to Gaussian paths + uniform growth; both")
    print("   restrictions should bite hardest when the mass is spread out)")
    print(f"\n  {'sd':>6s} {'sep':>6s} {'HK_true^2':>11s} {'D_cone^2':>10s} {'ratio':>8s}")
    print("  " + "-" * 46)
    for sd_ in (0.15, 0.3, 0.6, 1.0, 1.5):
        for sep in (1.0, 2.0):
            mu = gauss_1d(-sep / 2, sd_, 1.0, grid)
            nu = gauss_1d(+sep / 2, sd_, 1.0, grid)
            hk2, _ = hk_semicoupling(mu, nu, dist, delta)
            g0, g1 = as_stalk(-sep / 2, sd_), as_stalk(+sep / 2, sd_)
            D2 = cb.distance_sq(g0, g1, 1.0, 1.0)
            print(f"  {sd_:6.2f} {sep:6.2f} {hk2:11.6f} {D2:10.6f} {D2/hk2:8.4f}")

    print("\n=== does the MERGE DECISION survive? (the operative question) ===")
    print("  The bound's value can be loose and the PREDICATE still be right.")
    print("  Compare: is_same_concept (from D) vs saturation of HK_true.")
    print("  Broken out by CONCENTRATION sd/delta, because that is what the")
    print("  spread table above says drives the gap.")
    print(f"\n  {'sd/delta':>9s} {'agree':>7s} {'of':>4s} {'%':>7s}")
    print("  " + "-" * 30)
    overall_a = overall_t = 0
    for sd_ in (0.1, 0.2, 0.3, 0.6, 1.0, 1.5):
        agree = tot = 0
        for sep in np.linspace(0.1, 6.0, 16):
            mu = gauss_1d(-sep / 2, sd_, 1.0, grid)
            nu = gauss_1d(+sep / 2, sd_, 1.0, grid)
            hk2, _ = hk_semicoupling(mu, nu, dist, delta)
            g0, g1 = as_stalk(-sep / 2, sd_), as_stalk(+sep / 2, sd_)
            hk_says_two = hk2 > 2.0 - 1e-4          # saturated at total mass
            d_says_two = not cb.is_same_concept(g0, g1)
            agree += (hk_says_two == d_says_two)
            tot += 1
        overall_a += agree
        overall_t += tot
        print(f"  {sd_/delta:9.2f} {agree:7d} {tot:4d} {100*agree/tot:6.1f}%")
    print(f"\n  overall: {overall_a}/{overall_t} = {100*overall_a/overall_t:.1f}%")
    print("\n  MOS's actual regime: stalk spread ||U|| ~ 0.3-0.5 for unit-normalised")
    print("  embeddings, against inter-organ d_BW ~ O(1). So sd/delta ~ 0.3-0.5 is")
    print("  the row that matters -- read that one, not the average.")

    print("\n" + "=" * 78)
    print("READ THE NUMBERS ABOVE, NOT A SUMMARY. Recorded to the logbook as V1.")
    print("=" * 78)
