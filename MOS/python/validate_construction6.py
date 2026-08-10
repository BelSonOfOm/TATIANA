"""Does Construction 6 actually kill the harmonic class? (DERIVATION_MDL_GROWTH_LAW section 6.2)

THE QUESTION. The growth law says: a cycle carrying harmonic mass names a missing
concept, and Construction 6 says what that concept's stalk is --

    F(w) := lim D_gamma  ~=  H^0(gamma; F|gamma)

It is DERIVED that coning makes gamma a boundary and that the harmonic direction
dual to [gamma] dies WITH CONSTANT COEFFICIENTS. It is NOT derived that this
survives TWISTED coefficients, where the restriction maps have holonomy. That is
exactly where a construction like this usually fails, so it is checked before
anything is built on it.

WHAT IS MEASURED. Harmonic 1-cochains are ker(delta0^T) intersect ker(delta1).
With no 2-cells delta1 = 0, so on a bare cycle harmonic = (im delta0)^perp. After
coning there are 2-cells and the curl space is nonempty. Two numbers are
reported: the DIMENSION of the harmonic space, and the harmonic MASS of a
specific cochain eta, before and after.

THE SIGN CONVENTIONS, STATED (getting these wrong silently changes every number):

    e_i = [v_i, v_{i+1}],  (delta0 x)_{e_i} = r_i^+ x_{i+1} - r_i^- x_i
    f_i = [w, v_i],        (delta0 x)_{f_i} = x_i - p_i x_w
    t_i = [w, v_i, v_{i+1}],  boundary = e_i - f_{i+1} + f_i

    F(f_i) := F(v_i) with the v_i-restriction the IDENTITY (section 5.3: a
    deliberately empty choice, so no distortion can hide in the new edge).
    F(t_i) := F(e_i) with the e_i-restriction the identity and the f-restrictions
    the existing r_i^-, r_i^+.

THE INTERNAL CHECK THAT IS ITSELF THE RESULT. Under those conventions,

    (delta1 delta0 x)_{t_i} = (r_i^+ p_{i+1} - r_i^- p_i) x_w

so delta1 . delta0 = 0 IF AND ONLY IF the cone condition holds. The cochain
complex is only a complex when F(w) is a cone over D_gamma. That is not a test of
Construction 6 so much as a demonstration that no other choice was available.
Asserted for the limit, and asserted to FAIL for a deliberate non-cone.

Run: python validate_construction6.py
"""
from __future__ import annotations

import numpy as np

TOL = 1e-9


# --------------------------------------------------------------------------
# linear algebra helpers -- SVD-based, so rank decisions are made once, here
# --------------------------------------------------------------------------
def nullspace(M: np.ndarray, tol: float = TOL) -> np.ndarray:
    """Orthonormal basis of ker(M), as columns."""
    if M.size == 0 or M.shape[0] == 0:
        return np.eye(M.shape[1])
    _, s, vh = np.linalg.svd(M)
    rank = int((s > tol * max(M.shape)).sum())
    return vh[rank:].T.conj()


def harmonic_basis(d0: np.ndarray, d1: np.ndarray) -> np.ndarray:
    """ker(d0^T) intersect ker(d1), as an orthonormal basis of columns.

    Stacking is legitimate because both are linear conditions on the SAME space
    C^1: d0^T maps C^1 -> C^0 and d1 maps C^1 -> C^2, so the intersection is the
    kernel of the stacked map C^1 -> C^0 (+) C^2.
    """
    blocks = [d0.T]
    if d1.size and d1.shape[0] > 0:
        blocks.append(d1)
    return nullspace(np.vstack(blocks))


def harmonic_mass(eta: np.ndarray, H: np.ndarray) -> float:
    """Fraction of ||eta||^2 lying in the harmonic subspace spanned by H."""
    if H.shape[1] == 0:
        return 0.0
    coeffs = H.T @ eta
    return float(coeffs @ coeffs) / float(eta @ eta)


def rot_z(theta: float, n: int) -> np.ndarray:
    """Rotation by theta in the (0,1) plane of R^n, fixing every other axis.

    For n >= 3 the holonomy of a product of these fixes the axes 2..n-1, so
    H^0 is nonzero but SMALLER than a stalk -- the interesting middle case. A
    generic rotation would give H^0 = 0 (the degenerate case, tested separately).
    """
    R = np.eye(n)
    c, s = np.cos(theta), np.sin(theta)
    R[0, 0], R[0, 1], R[1, 0], R[1, 1] = c, -s, s, c
    return R


# --------------------------------------------------------------------------
# the complexes
# --------------------------------------------------------------------------
def cycle_d0(rminus: list[np.ndarray], rplus: list[np.ndarray],
             n_v: int) -> np.ndarray:
    """delta0 for a k-cycle with stalks R^{n_v} at vertices, R^{n_e} at edges."""
    k = len(rminus)
    n_e = rminus[0].shape[0]
    d0 = np.zeros((k * n_e, k * n_v))
    for i in range(k):
        j = (i + 1) % k
        d0[i * n_e:(i + 1) * n_e, i * n_v:(i + 1) * n_v] = -rminus[i]
        d0[i * n_e:(i + 1) * n_e, j * n_v:(j + 1) * n_v] = rplus[i]
    return d0


def coned(rminus, rplus, n_v, P):
    """delta0 and delta1 for the cone over the cycle, with F(w) spanned by P.

    P has shape (k*n_v, m): its columns are the elements of F(w) written inside
    (+) F(v_i), so p_i = the i-th block row of P. That is exactly how the limit
    presents itself, and it lets a NON-cone be passed in for the negative control.
    """
    k = len(rminus)
    n_e = rminus[0].shape[0]
    m = P.shape[1]

    dim_c0 = k * n_v + m                      # vertices, then w
    dim_c1 = k * n_e + k * n_v                # e-edges, then f-edges (F(f_i)=F(v_i))
    dim_c2 = k * n_e                          # triangles, F(t_i) = F(e_i)

    d0 = np.zeros((dim_c1, dim_c0))
    for i in range(k):
        j = (i + 1) % k
        # e_i = [v_i, v_{i+1}]
        d0[i * n_e:(i + 1) * n_e, i * n_v:(i + 1) * n_v] = -rminus[i]
        d0[i * n_e:(i + 1) * n_e, j * n_v:(j + 1) * n_v] = rplus[i]
        # f_i = [w, v_i]: identity out of v_i, p_i out of w
        row = k * n_e + i * n_v
        d0[row:row + n_v, i * n_v:(i + 1) * n_v] = np.eye(n_v)
        d0[row:row + n_v, k * n_v:] = -P[i * n_v:(i + 1) * n_v, :]

    d1 = np.zeros((dim_c2, dim_c1))
    for i in range(k):
        j = (i + 1) % k
        # boundary t_i = e_i - f_{i+1} + f_i
        d1[i * n_e:(i + 1) * n_e, i * n_e:(i + 1) * n_e] = np.eye(n_e)
        d1[i * n_e:(i + 1) * n_e,
           k * n_e + j * n_v:k * n_e + (j + 1) * n_v] = -rplus[i]
        d1[i * n_e:(i + 1) * n_e,
           k * n_e + i * n_v:k * n_e + (i + 1) * n_v] = rminus[i]
    return d0, d1


def limit_of(rminus, rplus, n_v):
    """lim D_gamma = {(x_i) : r_i^- x_i = r_i^+ x_{i+1}} = ker(delta0 on the cycle)."""
    return nullspace(cycle_d0(rminus, rplus, n_v))


# --------------------------------------------------------------------------
# cases
# --------------------------------------------------------------------------
def run_case(name: str, rminus, rplus, n_v: int, expect_limit_dim: int | None):
    k = len(rminus)
    n_e = rminus[0].shape[0]
    print(f"\n=== {name} ===")

    d0_before = cycle_d0(rminus, rplus, n_v)
    d1_before = np.zeros((0, d0_before.shape[0]))     # no 2-cells on a bare cycle
    H_before = harmonic_basis(d0_before, d1_before)

    P = limit_of(rminus, rplus, n_v)
    m = P.shape[1]
    print(f"  stalk dim {n_v}, cycle length {k}")
    print(f"  dim F(w) = dim lim D_gamma = H^0(gamma; F|gamma) = {m}")
    if expect_limit_dim is not None:
        assert m == expect_limit_dim, f"expected dim lim = {expect_limit_dim}, got {m}"

    # eta: a cochain with genuine harmonic content, taken from the harmonic space
    # itself so the "before" mass is 1 by construction and the "after" number is
    # unambiguous -- no question of eta having been mostly gradient all along.
    if H_before.shape[1] == 0:
        print("  harmonic space is EMPTY before coning -- nothing to kill")
        return
    rng = np.random.default_rng(0)
    eta = H_before @ rng.normal(size=H_before.shape[1])
    print(f"  dim harmonic BEFORE = {H_before.shape[1]}"
          f"   (mass of eta = {harmonic_mass(eta, H_before):.6f})")

    d0_after, d1_after = coned(rminus, rplus, n_v, P)

    # THE INTERNAL CHECK: the cochain complex is a complex iff the cone condition
    # holds. This is Construction 6 justifying itself.
    resid = float(np.abs(d1_after @ d0_after).max())
    print(f"  |d1 . d0|_max with F(w) = lim : {resid:.3e}")
    assert resid < 1e-10, "delta1.delta0 != 0 -- the cone condition FAILED"

    H_after = harmonic_basis(d0_after, d1_after)
    eta_ext = np.zeros(d0_after.shape[0])
    eta_ext[:k * n_e] = eta                            # extend by zero on the f-edges
    mass_after = harmonic_mass(eta_ext, H_after)
    print(f"  dim harmonic AFTER  = {H_after.shape[1]}"
          f"   (mass of eta = {mass_after:.3e})")

    if mass_after < 1e-9:
        print("  ==> VERDICT: harmonic mass KILLED.")
    else:
        print(f"  ==> VERDICT: harmonic mass SURVIVES ({mass_after:.4f}). Section 5 is wrong.")
    return mass_after


def control_path(n_v: int = 3):
    """POSITIVE CONTROL (instrument). A path is a tree: b1 = 0, so the harmonic
    space MUST be exactly empty. If this returns anything, the measurement is
    broken and no other number in this file counts."""
    print("\n=== CONTROL: path (tree, b1 = 0) ===")
    k = 4
    n_e = n_v
    d0 = np.zeros(((k - 1) * n_e, k * n_v))
    for i in range(k - 1):
        d0[i * n_e:(i + 1) * n_e, i * n_v:(i + 1) * n_v] = -np.eye(n_v)
        d0[i * n_e:(i + 1) * n_e, (i + 1) * n_v:(i + 2) * n_v] = np.eye(n_v)
    H = harmonic_basis(d0, np.zeros((0, d0.shape[0])))
    print(f"  dim harmonic = {H.shape[1]}  (must be 0)")
    assert H.shape[1] == 0, "INSTRUMENT BROKEN: a tree reported harmonic mass"
    print("  ==> control passed")


def control_noncone(n_v: int = 3):
    """NEGATIVE CONTROL. Feed a deliberately NON-cone F(w) and assert the complex
    stops being a complex. Without this, `d1.d0 = 0` above could be an identity
    that holds for any P, and would prove nothing about Construction 6."""
    print("\n=== CONTROL: a non-cone F(w) must break d1.d0 = 0 ===")
    k, theta = 4, 0.3
    rminus = [np.eye(n_v) for _ in range(k)]
    rplus = [rot_z(theta, n_v) for _ in range(k)]
    rng = np.random.default_rng(1)
    P_bad = rng.normal(size=(k * n_v, 2))              # arbitrary, not a cone
    d0, d1 = coned(rminus, rplus, n_v, P_bad)
    resid = float(np.abs(d1 @ d0).max())
    print(f"  |d1 . d0|_max with an arbitrary F(w) : {resid:.3e}  (must be > 0)")
    assert resid > 1e-6, "a non-cone gave d1.d0 = 0 -- the check is vacuous"
    print("  ==> control passed: only a cone makes the complex a complex")


if __name__ == "__main__":
    print(__doc__.split("Run:")[0])
    control_path()
    control_noncone()

    k, n_v = 4, 3

    # FLAT: every restriction the identity. Holonomy trivial, so H^0 is a whole
    # stalk. dim lim = n_v.
    run_case("FLAT sheaf on a 4-cycle (trivial holonomy)",
             [np.eye(n_v)] * k, [np.eye(n_v)] * k, n_v, expect_limit_dim=n_v)

    # PARTIAL HOLONOMY: rotations in the (0,1) plane. The product fixes axis 2,
    # so H^0 is 1-dimensional -- nonzero but smaller than a stalk. The case the
    # growth law actually cares about.
    theta = 0.3
    run_case("PARTIAL holonomy (rotation about one axis)",
             [np.eye(n_v)] * k, [rot_z(theta, n_v)] * k, n_v, expect_limit_dim=1)

    # DEGENERATE: holonomy fixing nothing, so lim = 0 and Construction 6 REFUSES
    # -- there was nothing consistent around that loop to name.
    #
    # THE STALK DIMENSION HERE IS 2, NOT 3, AND THAT IS FORCED. A first attempt
    # used a "generic" element of SO(3) and got dim lim = 1, not 0. The mistake
    # was mathematical, not numerical: EVERY element of SO(odd) has eigenvalue 1,
    # so it fixes an axis, so H^0(gamma) can never vanish for an odd-dimensional
    # stalk with orthogonal restriction maps. Degeneracy needs an even dimension.
    #
    # THIS IS NOT AN ARTIFACT OF THE TEST -- IT IS A FACT ABOUT MOS. Its
    # restriction maps ARE orthogonal (Householder maps; Pi_{O(d)} in the
    # consolidation formula), so the reachable degenerate cases are governed by
    # the parity of d. At d = 384 (even) degeneracy is possible and the refusal
    # branch is live; had d been odd, every cycle would always have had something
    # consistent to name and the branch would be dead code.
    n_deg = 2
    run_case("DEGENERATE (holonomy with no fixed vector, H^0 = 0)",
             [np.eye(n_deg)] * k, [rot_z(0.3, n_deg)] * k, n_deg,
             expect_limit_dim=0)
