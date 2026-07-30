"""
TATIANA - Hodge decomposition of a measured 1-cochain on the coarse complex.

WHY THIS FILE EXISTS (logbook 5r, the critical connection)
----------------------------------------------------------
Plan 5p states the growth law we actually want:

    "struggle = a persistent obstruction; the obstruction cocycle names the
     cell to attach."

Prop 8.2 killed the engine's only candidate for that cocycle: the engine's one
1-cochain is  delta*x  (the coboundary of the global state), and a coboundary
is BY DEFINITION exact, so [delta*x] = 0 in H^1 always, for every state, every
sheaf, identity restrictions or not. **The growth mechanism has no address to
grow at.**

Restoring the aim needs a genuinely MEASURED 1-cochain eta -- organs emitting
pairwise judgements, NOT delta of any global state -- and then the Hodge split

    C^1  =  im(delta^0)  (+)  ker(Delta_1)  (+)  im(delta^1)^*
             GRADIENT         HARMONIC          CURL

    gradient : eta is explained by a per-organ potential. Everyone is
               consistent; there is a global story. NOTHING TO GROW.
    curl     : inconsistency around a FILLED triangle. Local repair --
               fix one 2-simplex.
    harmonic : inconsistency around an UNFILLED cycle that no potential and no
               filled face can explain. This is the piece that survives in
               H^1, and ITS SUPPORT IS THE GROWTH ADDRESS.

This module is the free half of experiment E5 (the GATE). It also supplies the
Phi_infinity of the two-complex model's control rule

    Phi_infinity = ||eta_H||^2 + ||eta_C||^2      (residual of the descent,
    Phi_infinity / ||eta||^2 > theta  =>  do not flow, GROW)

computable BEFORE flowing, by two least-squares solves.

THE NULL MODEL -- READ THIS BEFORE INTERPRETING ANY RESULT
-----------------------------------------------------------
The run sheet's PASS criterion ("||harm||^2 + ||curl||^2 is a non-trivial
fraction of ||eta||^2") is NOT SAFE AS WRITTEN, and this is the single easiest
way to fool ourselves here.

The three pieces are orthogonal projections onto subspaces of KNOWN dimension:

    dim(gradient) = V - b0            (= 3 in the E5 configuration)
    dim(curl)     = rank(delta^1)     (= 1)
    dim(harmonic) = E - the other two (= 1)

For eta drawn ISOTROPICALLY (pure noise, no signal at all), the expected energy
fraction in each subspace is exactly  dim / E.  In the E5 configuration that is

    gradient 3/5 = 0.60      curl 1/5 = 0.20      harmonic 1/5 = 0.20

so a COMPLETELY RANDOM instrument scores  harm + curl = 0.40  and would sail
through a naive "non-trivial fraction" test. 0.40 is the number to beat, not 0.
`null_fractions()` computes it for any complex, and every report prints the
measured fraction NEXT TO its null so the comparison cannot be skipped.

Consequently there are THREE outcomes, not two (same shape as VerifyOp):

    FAIL          harm+curl << null   -> eta is essentially pure gradient; the
                                         organs are implicitly consistent, H^1
                                         has nothing to find, and the whole
                                         cohomological growth story needs
                                         rethinking. Say so and stop.
    UNINFORMATIVE harm+curl ~= null AND unstable across re-elicitation -> we
                                         measured our own noise. Says nothing
                                         about the growth story; fix the
                                         instrument first.
    PASS          harm+curl departs from null AND reproduces across repeats.

Reproducibility is not optional: it is the only thing separating PASS from
UNINFORMATIVE, because both look identical in a single run.

CONVENTIONS (pinned here so nothing downstream has to guess)
-------------------------------------------------------------
* Vertices carry a fixed total order. An edge is STORED as (u, v) with u < v
  and its orientation is u -> v. A 1-cochain value eta_e is read as the signed
  quantity "v relative to u"; eta(v, u) = -eta(u, v). ANTISYMMETRY IS THE
  CONTRACT -- a symmetric "agreement" score is not a 1-cochain (see
  experiment_e5.py, which measures the violation instead of assuming it away).
* (delta^0 f)_(u,v) = f(v) - f(u).
* A triangle is stored as (a, b, c) with a < b < c and
  (delta^1 eta)_(a,b,c) = eta_(b,c) - eta_(a,c) + eta_(a,b),
  with a sign flip for any face whose stored orientation is reversed.
* Precision pi_e > 0 puts a weighted inner product <x,y>_W = sum_e pi_e x_e y_e
  on C^1 (HodgeRank's weighted least squares). All three projections are
  orthogonal in THAT inner product, so Pythagoras still holds exactly -- and it
  is asserted numerically on every call, not trusted.
* tau_f > 0 is the inner product on C^2. It is accepted as an argument and then
  provably IGNORED -- see THE tau INVARIANCE below. It exists in the signature
  so that the invariance is a tested property rather than a hard-coded I.

THE tau INVARIANCE -- WHY THE C^2 WEIGHTS CANNOT MOVE THESE NUMBERS
--------------------------------------------------------------------
Logbook 5af asserted that deriving tau_f would be CIRCULAR, on the grounds that
hodge_split uses the C^2 inner product to compute the curl projection, so any
derived tau would change curl, harm, and therefore every number in 5x (E5, the
only empirical evidence for the growth story). **That assertion is false, and
the one-line proof is:**

    with T = diag(tau) on C^2, the W-adjoint of d1 is  d1* = W^-1 d1^T T,
    so the curl space is  im(W^-1 d1^T T).
    T is diagonal and strictly positive, hence a BIJECTION C^2 -> C^2, so

        im(W^-1 d1^T T)  =  im(W^-1 d1^T)      for every tau > 0.

Same subspace => same W-orthogonal projection => identical curl, identical harm,
identical Phi_infinity. The gradient space never involved tau to begin with, and
the harmonic space is the orthogonal complement of two tau-free subspaces.

So tau is NOT IDENTIFIABLE from a Hodge split: no choice of it can be validated
or invalidated here, and no choice of it can invalidate E5. What tau does move
is the NON-ZERO spectrum of Delta_1 (the kernel, i.e. the harmonic space, is
fixed) and the Forman curvature -- see curvature.py, which is where tau earns
its keep. Self-test 12 asserts the invariance over 1e-3..1e3.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

Vertex = str
Edge = Tuple[Vertex, Vertex]
Triangle = Tuple[Vertex, Vertex, Vertex]


# --------------------------------------------------------------------------
# The complex
# --------------------------------------------------------------------------

class Complex2:
    """An oriented 2-dimensional simplicial complex (vertices, edges, triangles).

    Small by construction: the coarse complex has a handful of organs, so dense
    matrices are the right call and every operation here is microseconds.
    Downward closure is ENFORCED, not assumed -- a triangle whose faces are not
    all present is not a simplex, and silently inserting the missing edges would
    change the topology (and hence b1) behind the caller's back.
    """

    def __init__(self,
                 vertices: Sequence[Vertex],
                 edges: Sequence[Edge],
                 triangles: Sequence[Triangle] = ()):
        self.vertices: List[Vertex] = list(vertices)
        if len(set(self.vertices)) != len(self.vertices):
            raise ValueError(f"Duplicate vertices: {self.vertices}")
        self._vidx = {v: i for i, v in enumerate(self.vertices)}

        canon: List[Edge] = []
        for (u, v) in edges:
            if u == v:
                raise ValueError(f"Self-loop {(u, v)}: not a 1-simplex.")
            for w in (u, v):
                if w not in self._vidx:
                    raise ValueError(f"Edge {(u, v)} references unknown vertex {w!r}.")
            e = self._canon_edge(u, v)
            if e in canon:
                raise ValueError(f"Duplicate edge {e}.")
            canon.append(e)
        self.edges: List[Edge] = canon
        self._eidx = {e: i for i, e in enumerate(self.edges)}

        tri: List[Triangle] = []
        for t in triangles:
            if len(set(t)) != 3:
                raise ValueError(f"Degenerate triangle {t}.")
            a, b, c = sorted(t, key=lambda w: self._vidx[w])
            for face in ((a, b), (a, c), (b, c)):
                if self._canon_edge(*face) not in self._eidx:
                    raise ValueError(
                        f"Triangle {(a, b, c)} has face {face} that is not an edge. "
                        "Downward closure is required; refusing to invent the edge, "
                        "because that would change b1 silently.")
            if (a, b, c) in tri:
                raise ValueError(f"Duplicate triangle {(a, b, c)}.")
            tri.append((a, b, c))
        self.triangles: List[Triangle] = tri

    # -- ordering helpers ---------------------------------------------------

    def _canon_edge(self, u: Vertex, v: Vertex) -> Edge:
        return (u, v) if self._vidx[u] < self._vidx[v] else (v, u)

    def edge_index(self, u: Vertex, v: Vertex) -> Tuple[int, float]:
        """(row index, +1 if (u,v) matches stored orientation else -1)."""
        e = self._canon_edge(u, v)
        if e not in self._eidx:
            raise KeyError(f"No such edge: {(u, v)}")
        return self._eidx[e], (1.0 if e == (u, v) else -1.0)

    # -- coboundaries -------------------------------------------------------

    def delta0(self) -> np.ndarray:
        """(E x V).  (delta^0 f)_(u,v) = f(v) - f(u)."""
        D = np.zeros((len(self.edges), len(self.vertices)))
        for i, (u, v) in enumerate(self.edges):
            D[i, self._vidx[u]] = -1.0
            D[i, self._vidx[v]] = +1.0
        return D

    def delta1(self) -> np.ndarray:
        """(F x E).  (delta^1 eta)_(a,b,c) = eta_(b,c) - eta_(a,c) + eta_(a,b)."""
        D = np.zeros((len(self.triangles), len(self.edges)))
        for k, (a, b, c) in enumerate(self.triangles):
            for (face, sign) in (((b, c), +1.0), ((a, c), -1.0), ((a, b), +1.0)):
                j, orient = self.edge_index(*face)
                D[k, j] += sign * orient
        return D

    # -- topology -----------------------------------------------------------

    def b0(self) -> int:
        parent = {v: v for v in self.vertices}

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        for (u, v) in self.edges:
            ru, rv = find(u), find(v)
            if ru != rv:
                parent[ru] = rv
        return len({find(v) for v in self.vertices})

    def b1(self) -> int:
        """dim H^1 of the SHAPE = E - rank(delta^0) - rank(delta^1).

        Computed from ranks rather than the Euler characteristic so it stays
        correct if a triangle is dependent (three triangles on four vertices,
        say) -- E - V + b0 - F would be wrong there, ranks are not.
        """
        d0, d1 = self.delta0(), self.delta1()
        r0 = int(np.linalg.matrix_rank(d0)) if d0.size else 0
        r1 = int(np.linalg.matrix_rank(d1)) if d1.size else 0
        return len(self.edges) - r0 - r1

    def describe(self) -> str:
        return (f"V={len(self.vertices)} E={len(self.edges)} F={len(self.triangles)} "
                f"b0={self.b0()} b1={self.b1()}")


# --------------------------------------------------------------------------
# The decomposition
# --------------------------------------------------------------------------

@dataclass
class HodgeSplit:
    """One decomposition of one measured eta. Fractions are of ||eta||^2_W."""
    eta: np.ndarray
    grad: np.ndarray
    curl: np.ndarray
    harm: np.ndarray
    norm2: float                      # ||eta||^2_W
    grad2: float
    curl2: float
    harm2: float
    dims: Tuple[int, int, int]        # (grad, curl, harm) subspace dimensions
    null: Tuple[float, float, float]  # expected fractions under isotropic noise
    potential: np.ndarray             # the f with grad = delta^0 f (mean-zero)
    residual: float                   # Pythagoras violation; must be ~0

    @property
    def frac(self) -> Tuple[float, float, float]:
        if self.norm2 <= 0:
            return (float("nan"),) * 3
        return (self.grad2 / self.norm2, self.curl2 / self.norm2,
                self.harm2 / self.norm2)

    @property
    def phi_infinity(self) -> float:
        """Residual the descent CANNOT remove: ||eta_H||^2 + ||eta_C||^2."""
        return self.harm2 + self.curl2

    @property
    def phi_ratio(self) -> Optional[float]:
        """Phi_infinity / ||eta||^2 -- the quantity the growth rule gates on."""
        if self.norm2 <= 0:
            return None
        return self.phi_infinity / self.norm2

    @property
    def excess_over_null(self) -> Optional[float]:
        """(harm+curl fraction) - (its value for pure noise). THE number.

        Positive = more non-gradient structure than noise alone would give.
        Negative = MORE gradient-like than random, i.e. evidence the organs are
        implicitly consistent. Zero = indistinguishable from noise.
        """
        if self.norm2 <= 0:
            return None
        return (self.curl2 + self.harm2) / self.norm2 - (self.null[1] + self.null[2])

    def harmonic_support(self, top: int = 3) -> List[Tuple[Edge, float]]:
        """Edges carrying the most harmonic mass -- THE GROWTH ADDRESS.

        Meaningful only when harm2 is materially above the null; the caller is
        responsible for checking that. Returned as (edge, signed value).
        """
        order = np.argsort(-np.abs(self.harm))
        return [(self._edges[i], float(self.harm[i])) for i in order[:top]]

    _edges: List[Edge] = field(default_factory=list)

    def report(self, label: str = "") -> str:
        g, c, h = self.frac
        ng, nc, nh = self.null
        head = f"[{label}] " if label else ""
        exc = self.excess_over_null
        return (f"{head}||eta||^2={self.norm2:.4f}  "
                f"grad={g:.3f}(null {ng:.3f})  curl={c:.3f}(null {nc:.3f})  "
                f"harm={h:.3f}(null {nh:.3f})  "
                f"Phi_inf/||eta||^2={self.phi_ratio:.3f}  "
                f"excess_over_null={exc:+.3f}")


def null_fractions(cx: Complex2) -> Tuple[float, float, float]:
    """Expected (grad, curl, harm) energy fractions for ISOTROPIC eta.

    Orthogonal projection of isotropic noise puts energy in each subspace in
    proportion to its dimension, so this is exactly (dim/E, dim/E, dim/E). It is
    the baseline every measured split must be compared against; see the module
    docstring. Verified by Monte Carlo in the self-test.
    """
    E = len(cx.edges)
    if E == 0:
        return (float("nan"),) * 3
    d0, d1 = cx.delta0(), cx.delta1()
    r0 = int(np.linalg.matrix_rank(d0)) if d0.size else 0
    r1 = int(np.linalg.matrix_rank(d1)) if d1.size else 0
    rh = E - r0 - r1
    return (r0 / E, r1 / E, rh / E)


def hodge_split(cx: Complex2,
                eta: Sequence[float],
                precision: Optional[Dict[Edge, float]] = None,
                tau: Optional[Dict[Triangle, float]] = None) -> HodgeSplit:
    """Split a measured 1-cochain into gradient + curl + harmonic.

    eta        : one value per edge, in `cx.edges` order, SIGNED with the stored
                 orientation (u -> v).
    precision  : optional pi_e > 0 per edge; None => all 1. Puts the weighted
                 inner product <x,y>_W = sum pi_e x_e y_e on C^1, which is the
                 correct thing when the organs report a confidence per pair
                 (logbook 5t, Q9: confidence feeds pi_e).
    tau        : optional tau_f > 0 per triangle -- the inner product on C^2.
                 **Validated and then ignored, deliberately.** The curl space is
                 im(W^-1 d1^T T) and T is invertible, so it equals im(W^-1 d1^T)
                 for every positive tau: the split cannot depend on it (module
                 docstring, THE tau INVARIANCE; self-test 12). Accepted so that
                 callers holding a derived tau can pass it without special-casing
                 and without believing it does something here.

    Uses lstsq (not an explicit pseudo-inverse) throughout, consistent with the
    budget finding in 5s: never form pinv. At E=5 it is free either way, but the
    same code path has to survive the real complex.
    """
    E = len(cx.edges)
    eta = np.asarray(eta, dtype=float).ravel()
    if eta.shape != (E,):
        raise ValueError(f"eta has shape {eta.shape}, expected ({E},) "
                         f"-- one value per edge, in cx.edges order.")

    if precision is None:
        w = np.ones(E)
    else:
        w = np.empty(E)
        for i, e in enumerate(cx.edges):
            p = precision.get(e, precision.get((e[1], e[0])))
            if p is None:
                raise KeyError(f"No precision supplied for edge {e}. Refusing to "
                               "default silently -- a missing weight is a missing "
                               "measurement, not a weight of 1.")
            if p <= 0:
                raise ValueError(f"Precision {p} on edge {e} must be > 0 (it is "
                                 "1/variance, and 0 would delete the edge from the "
                                 "inner product without deleting it from the complex).")
            w[i] = float(p)

    if tau is not None:
        # Validated for positivity (a non-positive tau would be a real error in
        # the caller) and then dropped: see the module docstring. Refusing to
        # silently accept tau <= 0 costs nothing and catches a bad derivation.
        for t in cx.triangles:
            tv = tau.get(t)
            if tv is None:
                raise KeyError(f"No tau supplied for triangle {t}. Refusing to "
                               "default silently, for the same reason as pi_e.")
            if tv <= 0:
                raise ValueError(f"tau {tv} on triangle {t} must be > 0 (it is an "
                                 "inverse variance on C^2; 0 would make the C^2 "
                                 "inner product degenerate).")

    S = np.sqrt(w)                     # W = S^2, so ||x||^2_W = ||S x||^2
    d0 = cx.delta0()
    d1 = cx.delta1()

    # --- GRADIENT: argmin_f ||eta - d0 f||^2_W   (weighted least squares) ----
    # Solve in the whitened coordinates y = S x, where the problem is ordinary
    # least squares and numpy's lstsq gives the minimum-norm solution.
    f, *_ = np.linalg.lstsq(S[:, None] * d0, S * eta, rcond=None)
    f = f - f.mean()                   # potentials are defined up to a constant
    grad = d0 @ f

    # --- CURL: project onto im(delta^1 *), the W-adjoint image ---------------
    # The W-adjoint of d1 : C^1 -> C^2 is  d1* = W^{-1} d1^T T, so the curl space
    # is im(W^{-1} d1^T T) = im(W^{-1} d1^T), the equality holding because T is
    # invertible -- which is exactly why `tau` is absent below. Projecting eta
    # onto it in the W-metric is again a weighted least-squares problem,
    # whitened the same way.
    if d1.size:
        A = (d1 / w).T                 # W^{-1} d1^T, shape (E, F)
        g, *_ = np.linalg.lstsq(S[:, None] * A, S * eta, rcond=None)
        curl = A @ g
    else:
        curl = np.zeros(E)

    harm = eta - grad - curl

    def n2(x):
        return float(np.sum(w * x * x))

    norm2, grad2, curl2, harm2 = n2(eta), n2(grad), n2(curl), n2(harm)
    residual = abs(norm2 - (grad2 + curl2 + harm2))
    scale = max(norm2, 1e-30)
    if residual / scale > 1e-8:
        # The three pieces are orthogonal projections; Pythagoras is a theorem,
        # not a hope. If it fails, the decomposition is wrong and every number
        # downstream is meaningless -- refuse rather than report.
        raise AssertionError(
            f"Hodge orthogonality violated: ||eta||^2={norm2:.6g} but "
            f"grad+curl+harm={grad2 + curl2 + harm2:.6g} (rel. err "
            f"{residual / scale:.3g}). The decomposition is invalid.")

    r0 = int(np.linalg.matrix_rank(d0)) if d0.size else 0
    r1 = int(np.linalg.matrix_rank(d1)) if d1.size else 0
    split = HodgeSplit(eta=eta, grad=grad, curl=curl, harm=harm,
                       norm2=norm2, grad2=grad2, curl2=curl2, harm2=harm2,
                       dims=(r0, r1, E - r0 - r1), null=null_fractions(cx),
                       potential=f, residual=residual)
    split._edges = list(cx.edges)
    return split


# --------------------------------------------------------------------------
# The E5 configuration
# --------------------------------------------------------------------------

def e5_complex(organs: Sequence[Vertex] = ("A", "B", "C", "D")) -> Complex2:
    """The minimal configuration that can detect HARMONIC mass (run sheet, 5t).

    The originally-specified "one filled triangle" CANNOT: a filled triangle has
    b1 = 0, so dim C^1 = 3 = 2 gradient + 1 curl + 0 harmonic. You would measure
    curl and learn nothing about the component that carries the growth address.

        organs   A, B, C, D
        edges    AB, AC, AD, BC, CD        (5; BD deliberately absent)
        filled   {A, B, C}                 (1 two-simplex)
        unfilled cycle A-C-D-A             <- where harmonic mass can live

        dim C^1 = 5 = 3 (gradient) + 1 (curl) + 1 (harmonic)
    """
    a, b, c, d = organs
    edges = [(a, b), (a, c), (a, d), (b, c), (c, d)]
    return Complex2([a, b, c, d], edges, [(a, b, c)])


# --------------------------------------------------------------------------
# Self-test (free; no API calls)
# --------------------------------------------------------------------------

if __name__ == "__main__":
    import console
    console.setup()

    rng = np.random.default_rng(5)
    cx = e5_complex()
    print("=== E5 configuration ===")
    print("   ", cx.describe())
    print("    edges:", cx.edges, " triangles:", cx.triangles)
    assert cx.b0() == 1 and cx.b1() == 1, (cx.b0(), cx.b1())
    print("    b1 = 1: exactly one independent unfilled cycle (A-C-D-A)  OK")

    print("\n=== 1. delta^1 . delta^0 = 0 (a coboundary has no curl) ===")
    z = cx.delta1() @ cx.delta0()
    assert np.allclose(z, 0), z
    print("    max|d1 d0| =", f"{np.abs(z).max():.2e}", " OK")

    print("\n=== 2. dimensions match the design ===")
    d0, d1 = cx.delta0(), cx.delta1()
    r0, r1 = np.linalg.matrix_rank(d0), np.linalg.matrix_rank(d1)
    assert (r0, r1) == (3, 1), (r0, r1)
    print(f"    dim grad={r0}  dim curl={r1}  dim harm={5 - r0 - r1}  OK")

    print("\n=== 3. CONTROL: a PURE GRADIENT eta must report harm=curl=0 ===")
    # This is the Prop 8.2 situation: eta = delta^0 of a potential, which is
    # exactly what the engine produces today. If the decomposer cannot return 0
    # here it can never certify a FAIL.
    for _ in range(200):
        pot = rng.normal(size=4)
        s = hodge_split(cx, d0 @ pot)
        assert s.curl2 < 1e-18 and s.harm2 < 1e-18, s.report()
    print("    200 trials: curl=harm=0 to machine precision  OK")
    print("    (this is the delta*x that Prop 8.2 says the engine emits today)")

    print("\n=== 4. CONTROL: a PURE CURL eta must report grad=harm=0 ===")
    for _ in range(200):
        g = rng.normal(size=1)
        s = hodge_split(cx, (d1.T @ g))
        assert s.grad2 < 1e-18 and s.harm2 < 1e-18, s.report()
    print("    200 trials: grad=harm=0 to machine precision  OK")

    print("\n=== 5. CONTROL: a PURE HARMONIC eta must report grad=curl=0 ===")
    # Build it explicitly: cycles orthogonal to the curl space.
    #   z1 = A->B->C->A = AB + BC - AC   (this is exactly d1^T, the curl space)
    #   z2 = A->C->D->A = AC + CD - AD   (the unfilled cycle)
    # harmonic = z2 - <z2,z1>/<z1,z1> * z1
    idx = {e: i for i, e in enumerate(cx.edges)}
    z1 = np.zeros(5); z1[idx[("A", "B")]] = 1; z1[idx[("B", "C")]] = 1; z1[idx[("A", "C")]] = -1
    z2 = np.zeros(5); z2[idx[("A", "C")]] = 1; z2[idx[("C", "D")]] = 1; z2[idx[("A", "D")]] = -1
    h = z2 - (z2 @ z1) / (z1 @ z1) * z1
    assert np.allclose(d1 @ h, 0) and np.allclose(d0.T @ h, 0), "not harmonic"
    s = hodge_split(cx, h)
    assert s.grad2 < 1e-18 and s.curl2 < 1e-18, s.report()
    print(f"    harmonic representative {np.round(h, 3)}")
    print(f"    -> {s.report('pure-harm')}")
    print("    it is a CYCLE (d0^T h = 0) with NO curl (d1 h = 0)  OK")

    print("\n=== 6. THE NULL: isotropic noise scores 0.60/0.20/0.20 ===")
    acc = np.zeros(3)
    N = 20000
    for _ in range(N):
        s = hodge_split(cx, rng.normal(size=5))
        acc += np.array(s.frac)
    acc /= N
    theo = np.array(null_fractions(cx))
    print(f"    Monte Carlo ({N}): grad={acc[0]:.4f} curl={acc[1]:.4f} harm={acc[2]:.4f}")
    print(f"    dim/E predicts  : grad={theo[0]:.4f} curl={theo[1]:.4f} harm={theo[2]:.4f}")
    assert np.max(np.abs(acc - theo)) < 0.01, (acc, theo)
    print("    => a RANDOM instrument scores harm+curl = 0.40.")
    print("       THIS is the number E5 must beat, not 0.  OK")

    print("\n=== 7. Pythagoras holds under a weighted inner product ===")
    for _ in range(200):
        pi = {e: float(rng.uniform(0.1, 10.0)) for e in cx.edges}
        s = hodge_split(cx, rng.normal(size=5), precision=pi)
        assert s.residual / s.norm2 < 1e-10, s.residual
    print("    200 random precision profiles: orthogonality exact  OK")

    print("\n=== 8. weighted null still equals dim/E ===")
    # The projections are orthogonal in the W-metric, so isotropy must be taken
    # in that metric too: eta = W^{-1/2} g with g standard normal.
    pi = {e: float(v) for e, v in zip(cx.edges, [0.2, 5.0, 1.0, 3.0, 0.7])}
    w = np.array([pi[e] for e in cx.edges])
    acc = np.zeros(3)
    for _ in range(20000):
        s = hodge_split(cx, rng.normal(size=5) / np.sqrt(w), precision=pi)
        acc += np.array(s.frac)
    acc /= 20000
    print(f"    weighted MC: grad={acc[0]:.4f} curl={acc[1]:.4f} harm={acc[2]:.4f}")
    assert np.max(np.abs(acc - theo)) < 0.01, (acc, theo)
    print("    OK -- the baseline is topological, not a property of the weights")

    print("\n=== 9. Phi_infinity is exactly the un-removable residual ===")
    # Gradient descent on ||eta - delta^0 f||^2 can only remove the gradient
    # part; what is left is curl + harmonic. Check against a direct solve.
    eta9 = rng.normal(size=5)
    s9 = hodge_split(cx, eta9)
    f9, *_ = np.linalg.lstsq(d0, eta9, rcond=None)
    residual_direct = float(np.sum((eta9 - d0 @ f9) ** 2))
    assert abs(residual_direct - s9.phi_infinity) < 1e-10, (residual_direct, s9.phi_infinity)
    print(f"    Phi_inf={s9.phi_infinity:.6f} == best-fit residual {residual_direct:.6f}  OK")

    print("\n=== 10. downward closure is ENFORCED ===")
    try:
        Complex2(["A", "B", "C"], [("A", "B"), ("B", "C")], [("A", "B", "C")])
    except ValueError as e:
        print("    refused a triangle with a missing face:", str(e)[:70], "... OK")
    else:
        raise AssertionError("should have refused")

    print("\n=== 11. b1 is computed from RANKS, not Euler ===")
    # Three triangles on four vertices, all faces present (the full 2-skeleton
    # of a tetrahedron minus one face): E - V + b0 - F would give the wrong
    # answer if the triangles were dependent.
    full = Complex2(list("ABCD"), list(combinations("ABCD", 2)),
                    [("A", "B", "C"), ("A", "B", "D"), ("A", "C", "D")])
    print(f"    {full.describe()}  (6 edges, 3 independent triangles => b1=0)")
    assert full.b1() == 0, full.b1()
    print("    OK")

    print("\n=== 12. THE tau INVARIANCE: the C^2 weights cannot move the split ===")
    # This is the test that retires logbook 5af's circularity claim. If it ever
    # fails, tau IS identifiable from a Hodge split, E5 does depend on it, and
    # V7's original framing comes back.
    worst = 0.0
    for _ in range(2000):
        eta12 = rng.normal(size=5)
        pi12 = {e: float(rng.uniform(0.1, 10.0)) for e in cx.edges}
        lo = {t: float(rng.uniform(1e-3, 1e-2)) for t in cx.triangles}
        hi = {t: float(rng.uniform(1e2, 1e3)) for t in cx.triangles}
        a = hodge_split(cx, eta12, precision=pi12, tau=lo)
        b = hodge_split(cx, eta12, precision=pi12, tau=hi)
        c = hodge_split(cx, eta12, precision=pi12)          # tau = I
        worst = max(worst,
                    np.abs(a.curl - b.curl).max(), np.abs(a.harm - b.harm).max(),
                    np.abs(a.curl - c.curl).max(), np.abs(a.harm - c.harm).max(),
                    abs(a.phi_infinity - b.phi_infinity))
    assert worst < 1e-9, worst
    print(f"    2000 trials, tau over 1e-3..1e3: worst deviation {worst:.2e}")
    print("    curl, harm and Phi_inf are INVARIANT to tau  OK")
    print("    => tau is NOT identifiable here, and E5 (5x) cannot depend on it.")

    print("\n=== 13. tau is still VALIDATED even though it is unused ===")
    for bad in (0.0, -1.0):
        try:
            hodge_split(cx, rng.normal(size=5), tau={("A", "B", "C"): bad})
        except ValueError:
            pass
        else:
            raise AssertionError(f"should have refused tau={bad}")
    try:
        hodge_split(cx, rng.normal(size=5), tau={})
    except KeyError:
        pass
    else:
        raise AssertionError("should have refused a missing tau")
    print("    refuses tau <= 0 and missing tau  OK")

    print("\nALL HODGE SELF-TESTS PASSED (zero API calls)")
