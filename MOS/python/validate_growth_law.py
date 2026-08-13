"""VALIDATION — THE GROWTH LAW'S COST SIDE (DOCS/DERIVATION_MDL_GROWTH_LAW.md).

Companion to validate_construction6.py, which established that Construction 6 is a
sheaf.  This file tests the claims the COST side rests on, and every assertion
below is a numbered claim from that document, so a failure localises to a section.

    A  (5.10)  Coning kills the harmonic class for ANY cone, including F(w) = 0.
               So annihilation of H^1 does NOT select a size, and RETENTION of
               H^0 is the figure of merit instead.
    B  (5.10)  dim lim D_gamma == dim of the harmonic space of gamma before coning.
    C  (2')    lim = ker(Hol - I): the legs propagate, so k-1 of the k legs are
               NOT free parameters and the model term is b*d_w*(d_v + ...), not
               b*d_w*(1 + k*d_v).
    D  (5.11)  The per-traversal saving of one retained direction is
                   dc_j = (k/2) log2(1/(1 - rho_j^2)) - b_s
               with rho_j^2 the intraclass correlation of that direction's k
               readings, measured against ACTUAL two-part code lengths.
    E  (5.11)  dc_j <= 0 below a reliability floor, at every n.  A frequency
               threshold alone cannot express that.

CONTROLS, per the standing rule -- without these none of the above counts:
    K1  a path (tree, b1 = 0) must report harmonic dim 0.
    K2  an arbitrary NON-cone F(w) must break delta^1 delta^0 (else the check
        in A is vacuous).
    K3  traversals shuffled independently per vertex must destroy the saving
        (else D is measuring the coder, not the recurrence).

Run:
    "$LOCALAPPDATA/Programs/Python/Python311/python.exe" MOS/python/validate_growth_law.py
numpy only.  No corpus, no model, no network.
"""
import numpy as np

rng = np.random.default_rng(20260811)
TOL = 1e-8
LOG2E = 1.0 / np.log(2.0)


# ---------------------------------------------------------------- linear algebra
def rank(M):
    if M.size == 0:
        return 0
    s = np.linalg.svd(M, compute_uv=False)
    return int((s > TOL * s[0]).sum()) if s[0] > 0 else 0


def nullspace(M):
    U, s, Vt = np.linalg.svd(M)
    r = int((s > TOL * s[0]).sum()) if s.size and s[0] > 0 else 0
    return Vt[r:].T


def rand_orth(n):
    Q, R = np.linalg.qr(rng.normal(size=(n, n)))
    return Q * np.sign(np.diag(R))


def rot(n, theta, i=0, j=1):
    R = np.eye(n)
    R[i, i] = R[j, j] = np.cos(theta)
    R[i, j], R[j, i] = -np.sin(theta), np.sin(theta)
    return R


# ------------------------------------------------------- the complex and the cone
# Conventions verbatim from DERIVATION_MDL_GROWTH_LAW.md 8.1:
#     e_i = [v_i, v_{i+1}]     (d0 x)_{e_i} = r_i^+ x_{i+1} - r_i^- x_i
#     f_i = [w, v_i]           (d0 x)_{f_i} = x_i - p_i x_w
#     t_i = [w, v_i, v_{i+1}]  (d1 y)_{t_i} = y_{e_i} - r_i^+ y_{f_{i+1}} + r_i^- y_{f_i}
# with F(f_i) := F(v_i) (5.3) and F(t_i) := F(e_i).

def delta0_cycle(k, n, rm, rp):
    D = np.zeros((k * n, k * n))
    for i in range(k):
        D[i * n:(i + 1) * n, i * n:(i + 1) * n] -= rm[i]
        j = (i + 1) % k
        D[i * n:(i + 1) * n, j * n:(j + 1) * n] += rp[i]
    return D


def coned(k, n, rm, rp, P):
    s = P[0].shape[1]
    D0 = np.zeros((2 * k * n, s + k * n))
    for i in range(k):
        D0[i * n:(i + 1) * n, s + i * n:s + (i + 1) * n] -= rm[i]
        j = (i + 1) % k
        D0[i * n:(i + 1) * n, s + j * n:s + (j + 1) * n] += rp[i]
    for i in range(k):
        r = k * n + i * n
        D0[r:r + n, s + i * n:s + (i + 1) * n] = np.eye(n)
        D0[r:r + n, 0:s] = -P[i]
    D1 = np.zeros((k * n, 2 * k * n))
    for i in range(k):
        r = i * n
        j = (i + 1) % k
        D1[r:r + n, i * n:(i + 1) * n] += np.eye(n)
        D1[r:r + n, k * n + j * n:k * n + (j + 1) * n] -= rp[i]
        D1[r:r + n, k * n + i * n:k * n + (i + 1) * n] += rm[i]
    return D0, D1


def harmonic_dim(D0, D1, dimC1):
    """ker(d0^T) cap ker(d1), as the nullspace of the STACKED map C1 -> C0 (+) C2."""
    blocks = [D0.T] + ([D1] if D1 is not None else [])
    return dimC1 - rank(np.vstack(blocks))


def holonomy(k, rm, rp):
    """Hol = A_{k-1} ... A_0 with A_i = (r_i^+)^-1 r_i^-, so x_{i+1} = A_i x_i."""
    H = np.eye(rm[0].shape[0])
    for i in range(k):
        H = np.linalg.solve(rp[i], rm[i]) @ H
    return H


# ============================================================== A, B, C and K1, K2
def structure_case(name, k, n, rm, rp):
    print(f"\n--- {name}   (k={k}, stalk dim n={n}) ---")
    D0c = delta0_cycle(k, n, rm, rp)
    B = nullspace(D0c)                              # lim D_gamma inside (+) F(v_i)
    dlim = B.shape[1]
    harm_before = harmonic_dim(D0c, None, k * n)    # no 2-cells yet

    # ---- claim B: the concept's dimension IS the dimension of the hole
    print(f"  [B] dim lim = {dlim}   harmonic dim before coning = {harm_before}"
          f"   -> {'EQUAL' if dlim == harm_before else 'DIFFER'}")
    assert dlim == harm_before, "B failed: 5.10's d_w = dim H(gamma) is false here"

    # ---- claim C: lim = ker(Hol - I), and the legs propagate from p_1
    H = holonomy(k, rm, rp)
    fixed = nullspace(H - np.eye(n))
    print(f"  [C] dim ker(Hol - I) = {fixed.shape[1]}"
          f"   -> {'MATCHES dim lim' if fixed.shape[1] == dlim else 'DOES NOT MATCH'}")
    assert fixed.shape[1] == dlim, "C failed: the holonomy route disagrees with the limit"
    if dlim:
        # propagate x_1 around the loop and check we recover a section of lim
        prop = np.zeros((k * n, dlim))
        cur = fixed.copy()
        for i in range(k):
            prop[i * n:(i + 1) * n, :] = cur
            cur = np.linalg.solve(rp[i], rm[i]) @ cur
        resid = np.abs(D0c @ prop).max()
        print(f"      propagated sections satisfy delta^0 = 0 to {resid:.2e}"
              f"   [so k-1 of the k legs are DETERMINED, not stored]")
        assert resid < 1e-9, "C failed: propagation does not produce a section"

    # ---- claim A: every cone kills H^1, whatever its size
    tests = [("F(w) = lim  (Construction 6)", np.eye(dlim)),
             ("F(w) = 1-dim subspace of lim", np.eye(dlim)[:, :1] if dlim >= 1 else None),
             ("F(w) = 0    (empty concept)", np.zeros((dlim, 0)))]
    for label, T in tests:
        if T is None:
            continue
        S = B @ T
        P = [S[i * n:(i + 1) * n, :] for i in range(k)]
        D0, D1 = coned(k, n, rm, rp, P)
        comp = np.abs(D1 @ D0).max()
        h1 = harmonic_dim(D0, D1, 2 * k * n)
        h0 = (T.shape[1] + k * n) - rank(D0)
        print(f"  [A] {label:<30} dim F(w)={T.shape[1]}  |d1 d0|={comp:.1e}"
              f"  harmonic AFTER={h1}  dim H^0 after={h0}")
        assert comp < 1e-9, "A failed: a cone did not give a cochain complex"
        assert h1 == 0, "A failed: a cone left harmonic mass"
        assert h0 == T.shape[1], "A failed: H^0 after != dim F(w)"

    # ---- control K2: an arbitrary NON-cone must break the complex
    if dlim:
        P_bad = [rng.normal(size=(n, dlim)) for _ in range(k)]
        D0b, D1b = coned(k, n, rm, rp, P_bad)
        bad = np.abs(D1b @ D0b).max()
        print(f"  [K2] arbitrary non-cone F(w): |d1 d0| = {bad:.3f}"
              f"   -> {'the A check is NOT vacuous' if bad > 1e-3 else 'VACUOUS -- A proves nothing'}")
        assert bad > 1e-3, "K2 failed: delta^1 delta^0 = 0 holds for any F(w), so A is vacuous"


k, n = 5, 3
structure_case("flat sheaf (all identity)", k, n, [np.eye(n)] * k, [np.eye(n)] * k)
structure_case("partial holonomy (one rotation)", k, n,
               [np.eye(n)] * k, [np.eye(n)] * (k - 1) + [rot(n, 0.7)])
structure_case("random orthogonal restriction maps", k, n,
               [rand_orth(n) for _ in range(k)], [rand_orth(n) for _ in range(k)])

# ---- control K1: a tree must report no harmonic mass
print("\n--- [K1] CONTROL: a path, not a cycle ---")
kp = 5
Dp = np.zeros(((kp - 1) * n, kp * n))
for i in range(kp - 1):
    Dp[i * n:(i + 1) * n, i * n:(i + 1) * n] = -np.eye(n)
    Dp[i * n:(i + 1) * n, (i + 1) * n:(i + 2) * n] = np.eye(n)
hp = harmonic_dim(Dp, None, (kp - 1) * n)
print(f"  harmonic dim on a path = {hp}"
      f"   -> {'instrument is not manufacturing mass' if hp == 0 else 'INSTRUMENT IS BROKEN'}")
assert hp == 0, "K1 failed: a tree reports harmonic mass; no other number here counts"


# ================================================================= D, E, F and K3
# The data term.  A traversal of gamma reads one direction u of lim at each of its
# k vertices: a_i = <x_i, u_i>/||u_i||^2.  If u is a section and the record
# respects it, those k readings are ONE number seen k times.  Without the concept
# they are coded as k numbers under the vertex marginals; with it, s is sent once
# and the k residuals follow.
#
# Precision on the DATA cancels exactly between the two codes -- both code k reals
# per traversal at the same grid -- so the residual half of the saving,
# (k/2) log2(sigma_tot^2 / sigma_w^2), is EXACT for Gaussian readings and involves
# no chosen constant.  Precision on s does NOT cancel: s is sent n times, once per
# traversal, and THAT is the d_w-dependence 4 was missing.
#
# delta_s := sigma_w.  [DERIVED, not chosen] The reconstruction error is sigma_w
# whatever precision s is sent at, so bits spent below that floor buy nothing.
#
# WARNING, and it is why this block was rewritten once: the high-rate form
# 1/2 log2(2 pi e sigma_b^2 / sigma_w^2) for the cost of s GOES NEGATIVE when
# sigma_b < sigma_w, which no code length may do.  Below we measure the EXACT
# entropy of the quantised Gaussian and report the closed form's error against it
# rather than assuming the closed form.

from math import erf, sqrt


def quantised_gaussian_entropy(sigma, delta, span=14.0):
    """EXACT H(round(s/delta)) for s ~ N(0, sigma^2), to machine precision."""
    if sigma <= 0:
        return 0.0
    m = int(np.ceil(span * sigma / delta)) + 2
    edges = (np.arange(-m, m + 2) - 0.5) * delta
    cdf = np.array([0.5 * (1.0 + erf(e / (sigma * sqrt(2.0)))) for e in edges])
    p = np.diff(cdf)
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def b_s_closed(rho2):
    """Closed form for the cost of sending s.  The +1 is what keeps it >= 0."""
    return 0.5 * np.log2(1.0 + 2 * np.pi * np.e * rho2 / (1.0 - rho2))


def dc_closed(kk, rho2):
    return 0.5 * kk * np.log2(1.0 / (1.0 - rho2)) - b_s_closed(rho2)


def measure(a):
    """Two-part code on readings a[t, i].  Returns (dc_measured, rho2_hat, b_s_exact)."""
    kk = a.shape[1]
    s_hat = a.mean(axis=1)                      # MLE of the concept's value
    var_b = s_hat.var()
    var_w = (a - s_hat[:, None]).var()
    var_w = max(var_w, np.finfo(float).tiny)
    rho2 = var_b / (var_b + var_w)
    b_s = quantised_gaussian_entropy(np.sqrt(var_b), np.sqrt(var_w))
    return 0.5 * kk * np.log2(1.0 / (1.0 - rho2)) - b_s, rho2, b_s


print("\n--- [D] per-traversal saving: EXACT code length vs the closed form ---")
print(f"  {'rho^2 true':>10} {'rho^2 hat':>10} {'b_s exact':>10} {'b_s closed':>11} "
      f"{'dc measured':>12} {'dc closed':>10} {'err':>8}")
NT, KK = 40000, 5
worst = 0.0
for target in (0.995, 0.99, 0.95, 0.9, 0.7, 0.5, 0.3, 0.2, 0.1, 0.0):
    sb = sqrt(target)
    sw = sqrt(1.0 - target) if target < 1 else 0.0
    s_true = rng.normal(scale=max(sb, 1e-12), size=NT)
    a = s_true[:, None] + rng.normal(scale=max(sw, 1e-12), size=(NT, KK))
    dc_m, rho2, b_exact = measure(a)
    b_c, dc_c = b_s_closed(rho2), dc_closed(KK, rho2)
    worst = max(worst, abs(dc_m - dc_c))
    print(f"  {target:>10.3f} {rho2:>10.4f} {b_exact:>10.3f} {b_c:>11.3f} "
          f"{dc_m:>12.3f} {dc_c:>10.3f} {dc_m - dc_c:>8.3f}")
print(f"  worst closed-form error over the sweep: {worst:.3f} bits/traversal"
      f"   [the closed form is an OVER-estimate of the cost of s, so dc_closed is"
      f" conservative]")
assert worst < 0.35, "D failed: the closed form is not within a third of a bit"

# ---- claim F: the plug-in ICC is inflated by exactly (1 - rho^2)/k
print("\n--- [F] the coder's rho^2 is BIASED, and by an exactly known amount ---")
print(f"  {'rho^2 true':>10} {'rho^2 hat':>10} {'predicted hat':>14} {'err':>10}")
for target in (0.9, 0.5, 0.2, 0.0):
    sb, sw = sqrt(target), sqrt(1.0 - target)
    s_true = rng.normal(scale=max(sb, 1e-12), size=200000)
    a = s_true[:, None] + rng.normal(scale=sw, size=(200000, KK))
    _, rho2, _ = measure(a)
    pred = target + (1.0 - target) / KK
    print(f"  {target:>10.3f} {rho2:>10.4f} {pred:>14.4f} {rho2 - pred:>10.2e}")
    assert abs(rho2 - pred) < 3e-3, "F failed: rho_hat^2 != rho^2 + (1-rho^2)/k"
print("  -> UNBIAS BEFORE THRESHOLDING:  rho^2 = (rho_hat^2 - 1/k) / (1 - 1/k)")

print("\n--- [E] the reliability floor: dc <= 0 at EVERY n below it ---")
for KK2 in (3, 4, 5, 8, 12, 20):
    lo, hi = 1e-9, 1 - 1e-12
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if dc_closed(KK2, mid) > 0:
            hi = mid
        else:
            lo = mid
    true_floor = (hi - 1.0 / KK2) / (1.0 - 1.0 / KK2)
    print(f"  k = {KK2:>2}:  rho_hat^2 > {hi:.3f}  (true rho^2 > {max(true_floor, 0):.3f})"
          f"  before ANY recurrence count can pay for that direction")
assert dc_closed(5, 0.05) < 0 < dc_closed(5, 0.9), "E failed: no floor"

print("\n--- [K3] CONTROL: shuffle each vertex's readings independently ---")
s_true = rng.normal(scale=sqrt(0.9), size=40000)
a = s_true[:, None] + rng.normal(scale=sqrt(0.1), size=(40000, KK))
intact, rho2_i, _ = measure(a)
a_sh = np.column_stack([rng.permutation(a[:, i]) for i in range(KK)])
shuf, rho2_s, _ = measure(a_sh)
print(f"  intact traversals : rho_hat^2 = {rho2_i:.4f}   saving = {intact:+.3f} bits/traversal")
print(f"  shuffled control  : rho_hat^2 = {rho2_s:.4f}   saving = {shuf:+.3f} bits/traversal")
print(f"  -> {'the saving is the RECURRENCE, not the coder' if shuf < 0 < intact else 'BROKEN'}")
assert intact > 0 > shuf, "K3 failed: shuffling did not destroy the saving"


# ================================================== what the law then prints
print("\n--- THE THRESHOLD, and what 2's overcount was costing ---")
d_v, kcyc = 384, 5
print(f"  d_v = {d_v}, k = {kcyc}, one direction (d_w = 1), covariance rank k_w = 1;"
      f"  b = 1/2 log2 n, solved self-consistently")
print(f"  {'rho^2':>6} {'dc (bits/trav)':>15} {'n: 2 as written':>17} {'n: 2 corrected':>16}")
for rho2_true in (0.99, 0.95, 0.9, 0.7, 0.5, 0.3):
    rho2 = rho2_true + (1 - rho2_true) / kcyc          # what the coder will see
    dc = dc_closed(kcyc, rho2)
    if dc <= 0:
        print(f"  {rho2_true:>6.2f} {dc:>15.3f} {'never':>17} {'never':>16}")
        continue
    out = []
    for params in (1 + kcyc * d_v, d_v + 1 + 1):       # 2 as written; 2 corrected
        nn = 100.0
        for _ in range(300):
            nn = max(0.5 * np.log2(max(nn, 4.0)), 1.0) * params / dc
        out.append(nn)
    print(f"  {rho2_true:>6.2f} {dc:>15.3f} {out[0]:>17.0f} {out[1]:>16.0f}")

print("\nALL ASSERTIONS PASSED.")
