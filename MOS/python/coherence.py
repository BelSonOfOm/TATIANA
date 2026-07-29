"""
TATIANA - Coherence (Construction 2 / 2b): the sheaf-Laplacian discord measure,
now in its predictive-coding form (plan 5p, mechanism (1)).

REFERENCE IMPLEMENTATION. This is the authoritative, tested definition of the
conflict score. The C++ engine ports THIS (coarse_complex.cpp); if the two ever
disagree, THIS file is right and the C++ is wrong (parity policy, logbook 5j).

WHAT IT MEASURES
----------------
Modules are musicians; each holds a position in meaning-space (a 384-d vector).
omega is the total out-of-tuneness between musicians who are supposed to be
playing together (bound pairs = edges of K):

    omega = sum over bound pairs {u,v} of  pi_e * || F_{u<|e}(x_u) - F_{v<|e}(x_v) ||^2

This is EXACTLY the precision-weighted predictive-coding free energy
    F = sum_e pi_e || eps_e ||^2,     eps_e = R_{u,e} x_u - R_{v,e} x_v
where eps_e is the prediction error at connection e and pi_e is its precision.
"prediction error at a connection" IS the sheaf coboundary at that edge; the
identification is exact for the symmetric/reciprocal predictive-coding variant
(= Edelman "reentry"). See predictive_coding.py for the local rule that LEARNS
the restriction maps R (no backprop), and sheaf_diffusion() below for inference
(minimising F over x = running the diffusion = producing a reconciled section).

  * restriction = None  -> IDENTITY maps  -> eps_e = x_u - x_v   (v1, cold start)
  * precision   = None  -> all pi_e = 1                          (uniform)
With both defaults this reduces to the ordinary graph-Laplacian quadratic form
    omega = sum ||x_u - x_v||^2 = tr(X^T L_G X)
i.e. numerically IDENTICAL to the pre-5p measure (calibration + parity preserved).

WHY rho AND NOT omega
---------------------
omega is not scale-invariant: it grows if the orchestra plays LOUDER (bigger
vectors) or if you ADD musicians (more edges). Neither is more disagreement. So
we normalise by an upper bound on the (generalised) Laplacian spectrum:

    d_pi(v) = sum over edges e incident to v of pi_e     (precision-weighted degree)
    B       = max over edges {u,v} of (d_pi(u) + d_pi(v))   [weighted Anderson-Morley]
    rho     = omega / (B * ||X||_F^2)   in [0, 1]
    c       = 1 - rho                                        "confidence"

rho FACTORS INTO TWO INDEPENDENT MEASUREMENTS  (E1, audit 2026-07-27)
----------------------------------------------------------------------
rho tangles two different questions, because its numerator and denominator do
not see the same thing. omega is BLIND to consensus (consensus is ker L), but
||X||_F^2 includes consensus in full. Split the state orthogonally

    x = x_0 + x_perp,    x_0 = projection onto ker L,   x_perp = x - x_0

For identity restriction maps, ker L is the space of vectors that are CONSTANT
ON EACH CONNECTED COMPONENT, so x_0 is the per-component mean broadcast back.
(Not the global mean -- with b0 > 1 the global mean would count between-component
variation as dissent when it actually lies IN the kernel. This is a correctness
point, not a nicety.) Since L x_0 = 0 and L is symmetric, omega = x_perp^T L x_perp,
and ||X||_F^2 = ||x_0||^2 + ||x_perp||^2 (Pythagoras). Hence, exactly:

    rho  =  alpha * rho_tilde

    alpha     = ||x_perp||^2 / ||X||_F^2         DISSENT FRACTION
                how much of the state's energy is NOT consensus. Dimensionless,
                directly interpretable, and sensitive to encoder geometry.

    rho_tilde = omega / (B * ||x_perp||^2)       MODE INDEX
                a normalised Rayleigh quotient of L on (ker L)^perp: it says
                WHICH mode the disagreement occupies, not how much there is.

They demand OPPOSITE remedies, which is why one number cannot serve:
    high alpha, low  rho_tilde -> a clean two-camp split: the coalition wants
                                  restructuring (`split` / a new `bind`)
    low  alpha, high rho_tilde -> one organ is an outlier: one edge wants repair

THE WINDOW (why rho_tilde is the one to gate on)
------------------------------------------------
By Courant-Fischer, a Rayleigh quotient on (ker L)^perp is confined to the
spectrum's nonzero range, so

    rho_tilde  in  [ lambda_min_plus(L_K,pi) / B ,  lambda_max(L_K,pi) / B ]

where lambda_min_plus is the smallest NONZERO eigenvalue (the Fiedler value when
the graph is connected). BOTH ENDPOINTS ARE GRAPH INVARIANTS, computable from the
7-vertex coarse graph before any data is looked at, and needing recomputation only
when `bind`/`collapse` changes the topology. That gives a calibration window the
topology supplies rather than one fitted to three observations.

HONESTY, twice over:
  * This is NORMALISATION, NOT DERIVATION. Setting eps as a quantile q of the
    window still requires choosing q. What changes is that eps is now expressed
    in units the graph provides and adapts automatically to rewiring; it is no
    longer a bare constant. Do not oversell it.
  * The split is EXACT only for identity restriction maps. With non-identity maps
    ker L is not the per-component constants and there is no n x n matrix whose
    spectrum is L's. Rather than compute something wrong we report alpha,
    rho_tilde and window as None with split_status saying why. rho itself is
    unaffected and is still exact.

THE RESTRICTION-MAP CONTRACT (load-bearing for the bound)
---------------------------------------------------------
The bound rho <= 1 is a THEOREM when the restriction maps are ORTHOGONAL
(||R_{v,e} x|| = ||x||): then omega <= sum_e pi_e (||x_u||+||x_v||)^2's worst case
saturates exactly at B*||X||^2 (verified: antipodal-after-rotation gives rho=1),
so B is a genuine upper bound, tight, and reduces to the classic
max(deg_u+deg_v) at identity. The learner in predictive_coding.py keeps R
orthogonal (polar retraction) for exactly this reason -- and orthogonality is
also what stops the Hebbian rule collapsing to R=0. If a caller supplies
non-orthogonal maps and rho_raw exceeds 1, we DO NOT silently clamp-and-hide:
we warn to stderr that the contract was violated, then clamp (float-drift guard).

WHAT IT DOES *NOT* MEASURE
--------------------------
Coherence is not correctness. Every module can agree and all be wrong together.
rho drives RESOLVE/EXPLORE; only VerifyOp (external grounding) touches truth.
rho is ORDINAL, not calibrated - it is NOT a probability of being right.

THE DANGEROUS FAILURE MODE (guarded below)
------------------------------------------
If there are no edges, nobody disagrees - because nobody is talking. A naive
implementation would report PERFECT confidence for a totally fragmented mind.
So rho is UNDEFINED (None) when there are no edges or the state is zero, and we
always report b0 (connected components): dim ker L = d * b0, so a LARGE kernel
means fragmentation, not harmony.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

Vertex = str
Edge = Tuple[Vertex, Vertex]
# A restriction pair for edge (u, v): (R_u, R_v), each a (d_e x d) matrix taking
# the vertex stalk into the edge stalk. None anywhere => identity for that edge.
RestrictionMap = Dict[Edge, Tuple[np.ndarray, np.ndarray]]
Precision = Dict[Edge, float]


@dataclass
class CoherenceReport:
    """Result of a coherence evaluation. `rho is None` means genuinely UNKNOWN."""
    rho: Optional[float]                     # normalised discord in [0,1], or None
    confidence: Optional[float]              # 1 - rho, or None
    omega: float                             # raw discord (unnormalised)
    per_edge: Dict[Edge, float] = field(default_factory=dict)
    b0: int = 0                              # connected components => fragmentation
    n_vertices: int = 0
    n_edges: int = 0
    status: str = "ok"                       # ok | no_edges | zero_state | empty

    # --- E1: the rho = alpha * rho_tilde split (audit 2026-07-27) -------------
    alpha: Optional[float] = None            # dissent fraction ||x_perp||^2/||X||_F^2
    rho_tilde: Optional[float] = None        # mode index omega/(B ||x_perp||^2)
    window: Optional[Tuple[float, float]] = None   # [lam_min_plus/B, lam_max/B]
    split_status: str = "not_computed"       # ok | consensus | non_identity_maps | n/a

    @property
    def is_fragmented(self) -> bool:
        """More than one component: any global coherence claim is only local."""
        return self.b0 > 1

    def mode_position(self) -> Optional[float]:
        """Where rho_tilde sits inside its achievable window, in [0,1].

        0 = the lowest (most global) mode the topology admits -- a clean split of
        the society into camps. 1 = the highest (most local) mode -- a single
        outlier organ. This is the quantity a topology-calibrated threshold should
        actually gate on, because it is the one comparable across rewirings.
        """
        if self.rho_tilde is None or self.window is None:
            return None
        lo, hi = self.window
        if hi - lo <= 1e-15:
            return None          # degenerate spectrum: position is meaningless
        return (self.rho_tilde - lo) / (hi - lo)

    def worst_edge(self, tol: float = 1e-12) -> Optional[Edge]:
        """The guilty coalition - where RESOLVE should be aimed.

        Returns None when there is no actual disagreement. A naive max() returns
        an arbitrary first element even when every omega_e is 0, which would point
        RESOLVE at a conflict that does not exist - a fabricated signal. (Caught by
        the visualiser: a perfectly coherent frame still displayed 'RESOLVE here'.)
        """
        if not self.per_edge:
            return None
        candidate = max(self.per_edge, key=self.per_edge.get)
        if self.per_edge[candidate] <= tol:
            return None
        return candidate

    def summary(self) -> str:
        if self.rho is None:
            return f"rho=UNKNOWN ({self.status}); V={self.n_vertices} E={self.n_edges} b0={self.b0}"
        flag = "  [FRAGMENTED]" if self.is_fragmented else ""
        return (f"rho={self.rho:.4f} confidence={self.confidence:.4f} omega={self.omega:.4f} "
                f"V={self.n_vertices} E={self.n_edges} b0={self.b0}{flag}")

    def split_summary(self) -> str:
        """The E1 line: rho decomposed, with the window it lives in."""
        if self.alpha is None:
            return f"split=UNAVAILABLE ({self.split_status})"
        if self.rho_tilde is None:
            # alpha == 0: perfect consensus has no mode. Report bottom, not zero.
            return f"alpha={self.alpha:.4f}  rho_tilde=UNDEFINED (perfect consensus)"
        lo, hi = self.window
        pos = self.mode_position()
        pos_s = "n/a" if pos is None else f"{pos:.3f}"
        return (f"alpha={self.alpha:.4f}  rho_tilde={self.rho_tilde:.4f}  "
                f"window=[{lo:.4f},{hi:.4f}]  position={pos_s}")


def _connected_components(vertices: Sequence[Vertex], edges: Sequence[Edge]) -> int:
    """Count connected components (isolated vertices each count as one)."""
    parent = {v: v for v in vertices}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for u, v in edges:
        ru, rv = find(u), find(v)
        if ru != rv:
            parent[ru] = rv
    return len({find(v) for v in vertices})


def _coboundary(x_u: np.ndarray, x_v: np.ndarray,
                maps: Optional[Tuple[np.ndarray, np.ndarray]]) -> np.ndarray:
    """eps_e = R_u x_u - R_v x_v. maps=None => identity (eps_e = x_u - x_v)."""
    if maps is None:
        return x_u - x_v
    R_u, R_v = maps
    return R_u @ x_u - R_v @ x_v


def _component_labels(vertices: Sequence[Vertex],
                      edges: Sequence[Edge]) -> Dict[Vertex, Vertex]:
    """Map each vertex to its component representative (union-find)."""
    parent = {v: v for v in vertices}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for u, v in edges:
        ru, rv = find(u), find(v)
        if ru != rv:
            parent[ru] = rv
    return {v: find(v) for v in vertices}


def _kernel_orthogonal_part(X: np.ndarray,
                            vertices: Sequence[Vertex],
                            kernel_edges: Sequence[Edge]) -> np.ndarray:
    """x_perp = x - P_{ker L} x, for IDENTITY restriction maps.

    ker(L_K (x) I_d) is the set of assignments constant on each connected
    component, so the orthogonal projection subtracts the PER-COMPONENT mean.
    An isolated vertex is its own component, so its x_perp is exactly zero -- an
    organ nobody is bound to cannot dissent, which is the correct reading.

    `kernel_edges` must be the edges that actually carry weight (pi_e > 0); a
    zero-precision edge contributes nothing to L and therefore does not join two
    components as far as the kernel is concerned.
    """
    idx = {v: i for i, v in enumerate(vertices)}
    labels = _component_labels(vertices, kernel_edges)

    sums: Dict[Vertex, np.ndarray] = {}
    counts: Dict[Vertex, int] = {}
    for v in vertices:
        r = labels[v]
        row = X[idx[v]]
        sums[r] = row.copy() if r not in sums else sums[r] + row
        counts[r] = counts.get(r, 0) + 1

    X_perp = np.empty_like(X)
    for v in vertices:
        r = labels[v]
        X_perp[idx[v]] = X[idx[v]] - sums[r] / counts[r]
    return X_perp


def _weighted_graph_laplacian(vertices: Sequence[Vertex],
                              edges: Sequence[Edge],
                              pi_of) -> np.ndarray:
    """L_{K,pi} on the SCALAR n x n graph. Identity maps => L = L_{K,pi} (x) I_d,
    so spec(L) = spec(L_{K,pi}) with multiplicity d and the window endpoints are
    read off an n x n eigendecomposition (microseconds at n = 7)."""
    idx = {v: i for i, v in enumerate(vertices)}
    n = len(vertices)
    L = np.zeros((n, n))
    for (u, v) in edges:
        p = pi_of((u, v))
        i, j = idx[u], idx[v]
        L[i, i] += p
        L[j, j] += p
        L[i, j] -= p
        L[j, i] -= p
    return L


def coherence(states: Dict[Vertex, np.ndarray],
              edges: Sequence[Edge],
              restriction: Optional[RestrictionMap] = None,
              precision: Optional[Precision] = None) -> CoherenceReport:
    """Compute the discord rho over the coarse module complex.

    states      : module id -> its coarse-grained position vector (same dimension)
    edges       : bound pairs (the 1-simplices of K)
    restriction : optional per-edge (R_u, R_v) ORTHOGONAL maps; None => identity
    precision   : optional per-edge pi_e >= 0; None => all 1

    With restriction=None and precision=None this is byte-for-byte the pre-5p
    measure (the calibration in 5h and the C++ parity test both rely on that).
    """
    vertices = list(states.keys())
    n = len(vertices)
    if n == 0:
        return CoherenceReport(rho=None, confidence=None, omega=0.0,
                               b0=0, n_vertices=0, n_edges=0, status="empty")

    # Enforce a homogeneous geometry: mixing dimensions is meaningless, never patch it.
    dims = {len(np.asarray(v).ravel()) for v in states.values()}
    if len(dims) != 1:
        raise ValueError(f"Inconsistent embedding dimensions across modules: {sorted(dims)}. "
                         "Refusing to truncate or pad - fix the source of the mismatch.")

    X = np.stack([np.asarray(states[v], dtype=float).ravel() for v in vertices])

    # Keep only edges whose endpoints actually exist and which are not self-loops.
    clean_edges: List[Edge] = [(u, v) for (u, v) in edges
                               if u in states and v in states and u != v]
    b0 = _connected_components(vertices, clean_edges)

    def pi_of(e: Edge) -> float:
        if precision is None:
            return 1.0
        p = precision.get(e, precision.get((e[1], e[0]), 1.0))
        if p < 0:
            raise ValueError(f"Negative precision {p} on edge {e}: precision is 1/variance >= 0.")
        return float(p)

    def maps_of(e: Edge):
        if restriction is None:
            return None
        return restriction.get(e, restriction.get((e[1], e[0])))

    # --- omega: total precision-weighted squared prediction error --------------
    per_edge: Dict[Edge, float] = {}
    omega = 0.0
    for (u, v) in clean_edges:
        eps = _coboundary(states[u], states[v], maps_of((u, v)))
        contrib = pi_of((u, v)) * float(np.dot(eps, eps))
        per_edge[(u, v)] = contrib
        omega += contrib

    # --- guards: the failure modes from the study -----------------------------
    if not clean_edges:
        # Nobody disagrees because nobody is talking. NOT confidence.
        return CoherenceReport(rho=None, confidence=None, omega=0.0, per_edge={},
                               b0=b0, n_vertices=n, n_edges=0, status="no_edges")

    norm_f2 = float(np.sum(X * X))
    if norm_f2 <= 0.0:
        # Zero state => Rayleigh quotient is 0/0, genuinely undefined.
        return CoherenceReport(rho=None, confidence=None, omega=omega, per_edge=per_edge,
                               b0=b0, n_vertices=n, n_edges=len(clean_edges),
                               status="zero_state")

    # --- normalisation: precision-weighted Anderson-Morley bound --------------
    d_pi: Dict[Vertex, float] = {v: 0.0 for v in vertices}
    for (u, v) in clean_edges:
        p = pi_of((u, v))
        d_pi[u] += p
        d_pi[v] += p
    B = max(d_pi[u] + d_pi[v] for (u, v) in clean_edges)

    rho_raw = omega / (B * norm_f2)
    if rho_raw > 1.0 + 1e-9:
        # The only way to get here is non-orthogonal restriction maps (||R|| > 1):
        # the Anderson-Morley bound assumed orthogonality. Do not hide it.
        print(f"[coherence] WARNING: rho_raw={rho_raw:.4f} > 1 - restriction maps "
              "violated the orthogonality contract (||R||>1); the Anderson-Morley "
              "bound no longer holds. Clamping, but the maps need re-orthogonalising.",
              file=sys.stderr)
    rho = min(max(rho_raw, 0.0), 1.0)

    # --- E1: split rho into (alpha, rho_tilde) and compute the window ---------
    # Only exact for identity restriction maps; see the module docstring. We
    # report None rather than an approximation when the hypothesis fails.
    alpha: Optional[float] = None
    rho_tilde: Optional[float] = None
    window: Optional[Tuple[float, float]] = None
    if restriction is not None and any(maps_of(e) is not None for e in clean_edges):
        split_status = "non_identity_maps"
    else:
        # Edges with pi_e == 0 contribute nothing to L, so they neither raise
        # omega nor join components in ker L.
        kernel_edges = [e for e in clean_edges if pi_of(e) > 0.0]
        X_perp = _kernel_orthogonal_part(X, vertices, kernel_edges)
        perp_f2 = float(np.sum(X_perp * X_perp))
        alpha = perp_f2 / norm_f2

        L_K = _weighted_graph_laplacian(vertices, kernel_edges, pi_of)
        evals = np.linalg.eigvalsh(L_K)
        # Numerically-zero eigenvalues span ker L; their count is the number of
        # components of the pi-weighted graph.
        zero_tol = max(1e-9, 1e-9 * float(np.max(np.abs(evals))) if evals.size else 1e-9)
        nonzero = evals[evals > zero_tol]

        if perp_f2 <= 1e-12 * norm_f2:
            # Perfect consensus has no mode. rho_tilde is BOTTOM, not zero --
            # returning 0 would claim "the most global mode possible", which is a
            # measurement we did not make.
            alpha = 0.0
            split_status = "consensus"
            if nonzero.size:
                window = (float(nonzero.min()) / B, float(evals.max()) / B)
        elif nonzero.size == 0:
            split_status = "n/a"          # no bound pair carries weight
        else:
            rho_tilde = omega / (B * perp_f2)
            window = (float(nonzero.min()) / B, float(evals.max()) / B)
            split_status = "ok"

    return CoherenceReport(rho=rho, confidence=1.0 - rho, omega=omega, per_edge=per_edge,
                           b0=b0, n_vertices=n, n_edges=len(clean_edges), status="ok",
                           alpha=alpha, rho_tilde=rho_tilde, window=window,
                           split_status=split_status)


def sheaf_diffusion(states: Dict[Vertex, np.ndarray],
                    edges: Sequence[Edge],
                    restriction: Optional[RestrictionMap] = None,
                    precision: Optional[Precision] = None,
                    steps: int = 200,
                    dt: float = 0.1,
                    tol: float = 1e-9) -> Tuple[Dict[Vertex, np.ndarray], List[float]]:
    """INFERENCE (plan 5p mechanism (1)): the structure COMPUTES a reconciled state.

    Gradient flow  x_dot = -dF/dx = -L x  on the predictive-coding free energy
    F = omega(x). Descends omega monotonically to the harmonic projection (the
    closest global section = min-discord state consistent with the maps). This is
    the sheaf's role-2 use: it does not SCORE the organs, it RECONCILES them,
    producing a belief no single organ held.

    IMPORTANT (honesty): with identity maps on a connected graph, ker L is the
    diagonal, so this just AVERAGES the organs. It becomes non-trivial only with
    learned (non-identity) restriction maps. And it reconciles EXISTING content;
    it never adds a fact - a coherent-but-wrong fixpoint is possible, which is why
    VerifyOp, not diffusion, is the arbiter of truth.

    Returns (reconciled_states, omega_trajectory). Free: a few sparse matvecs.
    """
    x = {v: np.asarray(s, dtype=float).ravel().copy() for v, s in states.items()}
    clean_edges = [(u, v) for (u, v) in edges if u in x and v in x and u != v]

    def pi_of(e):
        if precision is None:
            return 1.0
        return float(precision.get(e, precision.get((e[1], e[0]), 1.0)))

    def maps_of(e):
        if restriction is None:
            return None
        return restriction.get(e, restriction.get((e[1], e[0])))

    def omega_now() -> float:
        w = 0.0
        for (u, v) in clean_edges:
            eps = _coboundary(x[u], x[v], maps_of((u, v)))
            w += pi_of((u, v)) * float(np.dot(eps, eps))
        return w

    traj = [omega_now()]
    for _ in range(steps):
        grad = {v: np.zeros_like(x[v]) for v in x}
        for (u, v) in clean_edges:
            m = maps_of((u, v))
            eps = _coboundary(x[u], x[v], m)
            p = pi_of((u, v))
            if m is None:
                grad[u] += 2.0 * p * eps      # d/dx_u ||x_u - x_v||^2
                grad[v] -= 2.0 * p * eps
            else:
                R_u, R_v = m
                grad[u] += 2.0 * p * (R_u.T @ eps)
                grad[v] -= 2.0 * p * (R_v.T @ eps)
        for v in x:
            x[v] = x[v] - dt * grad[v]
        traj.append(omega_now())
        if abs(traj[-2] - traj[-1]) < tol:
            break
    return x, traj


def spectral_modes(states: Dict[Vertex, np.ndarray],
                   edges: Sequence[Edge],
                   top_k: int = 3):
    """DIAGNOSTIC ONLY (costs an eigendecomposition).

    Returns (eigenvalues, eigenvectors) of the graph Laplacian L_G, ascending.
    Disagreement decomposes as omega = sum_i lambda_i * c_i^2, so large-lambda
    modes are structural conflicts and small-lambda modes are soft/noise. The
    eigenvector shows WHICH combination of modules is pulling apart.
    """
    vertices = list(states.keys())
    idx = {v: i for i, v in enumerate(vertices)}
    n = len(vertices)
    L = np.zeros((n, n))
    for (u, v) in edges:
        if u not in idx or v not in idx or u == v:
            continue
        i, j = idx[u], idx[v]
        L[i, i] += 1.0
        L[j, j] += 1.0
        L[i, j] -= 1.0
        L[j, i] -= 1.0
    vals, vecs = np.linalg.eigh(L)  # symmetric => real spectrum, ascending
    return vals[:top_k] if top_k else vals, vecs, vertices


if __name__ == "__main__":
    d = 8
    rng = np.random.default_rng(0)
    base = rng.normal(size=d)

    print("=== 1. Perfect agreement (all modules identical) ===")
    s = {m: base.copy() for m in ["planner", "search", "reason", "verify"]}
    e = [("planner", "search"), ("search", "reason"), ("reason", "verify")]
    print("   ", coherence(s, e).summary(), "  <- rho should be ~0")

    print("\n=== 2. One module disagrees (verify pulls away) ===")
    s2 = dict(s)
    s2["verify"] = -base
    r2 = coherence(s2, e)
    print("   ", r2.summary())
    print("    guilty coalition:", r2.worst_edge(), "<- RESOLVE should aim here")

    print("\n=== 3. THE TRAP: no edges (nobody talking) ===")
    r3 = coherence(s, [])
    print("   ", r3.summary(), "<- must be UNKNOWN, NOT confidence=1")

    print("\n=== 4. Fragmentation (two disconnected pairs) ===")
    r4 = coherence(s, [("planner", "search"), ("reason", "verify")])
    print("   ", r4.summary(), "<- b0=2 means coherence is only LOCAL")

    print("\n=== 5. rho is bounded in [0,1] over random states ===")
    worst = 0.0
    for _ in range(500):
        sr = {m: rng.normal(size=d) for m in ["a", "b", "c", "d", "e"]}
        er = [("a", "b"), ("b", "c"), ("c", "d"), ("d", "e"), ("e", "a")]
        rr = coherence(sr, er)
        assert rr.rho is not None and 0.0 <= rr.rho <= 1.0, rr
        worst = max(worst, rr.rho)
    print(f"    500 random trials: all rho in [0,1]; max observed = {worst:.4f}")

    # ------------------------------------------------------------------ 5p tests
    print("\n=== 6. BACKWARD COMPAT: identity+pi=1 identical to old path ===")
    s6 = {m: rng.normal(size=d) for m in ["a", "b", "c"]}
    e6 = [("a", "b"), ("b", "c")]
    base_r = coherence(s6, e6)
    ident = {ee: (np.eye(d), np.eye(d)) for ee in e6}
    pi1 = {ee: 1.0 for ee in e6}
    with_maps = coherence(s6, e6, restriction=ident, precision=pi1)
    assert abs(base_r.omega - with_maps.omega) < 1e-12, (base_r.omega, with_maps.omega)
    assert abs(base_r.rho - with_maps.rho) < 1e-12
    print(f"    omega identical: {base_r.omega:.6f} == {with_maps.omega:.6f}  OK")

    print("\n=== 7. PRECISION reweights the guilty edge ===")
    # Deterministic, cleanly separated: a-b disagree a LITTLE (0.04), b-c a LOT
    # (1.0). Uniform pi blames b-c. But if we trust a-b 100x more, 100*0.04=4.0
    # outweighs 1.0 and the blame correctly moves to a-b.
    va = np.zeros(d); va[0] = 1.0
    vb = va.copy(); vb[1] = 0.2                 # ||a-b||^2 = 0.04
    vc = vb.copy(); vc[2] = 1.0                 # ||b-c||^2 = 1.00
    s7 = {"a": va, "b": vb, "c": vc}
    e7 = [("a", "b"), ("b", "c")]
    flat = coherence(s7, e7)
    weighted = coherence(s7, e7, precision={("a", "b"): 100.0, ("b", "c"): 1.0})
    print(f"    uniform pi    -> worst {flat.worst_edge()}")
    print(f"    pi(a,b)=100   -> worst {weighted.worst_edge()}  (precision moved the blame)")
    assert flat.worst_edge() == ("b", "c")
    assert weighted.worst_edge() == ("a", "b")

    print("\n=== 8. ORTHOGONAL maps keep rho in [0,1] (contract holds) ===")
    worst8 = 0.0
    for _ in range(300):
        s8 = {m: rng.normal(size=d) for m in ["a", "b", "c"]}
        e8 = [("a", "b"), ("b", "c"), ("c", "a")]
        # random orthogonal maps via QR
        rm = {}
        for ee in e8:
            Qu, _ = np.linalg.qr(rng.normal(size=(d, d)))
            Qv, _ = np.linalg.qr(rng.normal(size=(d, d)))
            rm[ee] = (Qu, Qv)
        r8 = coherence(s8, e8, restriction=rm)
        assert r8.rho is not None and 0.0 <= r8.rho <= 1.0, r8
        worst8 = max(worst8, r8.rho)
    print(f"    300 random orthogonal-map trials: all rho in [0,1]; max = {worst8:.4f}")

    print("\n=== 9. SHEAF DIFFUSION descends omega to a reconciled state ===")
    s9 = {"a": base, "b": base + 0.5 * rng.normal(size=d), "c": base - 0.4 * rng.normal(size=d)}
    e9 = [("a", "b"), ("b", "c"), ("c", "a")]
    w0 = coherence(s9, e9).omega
    recon, traj = sheaf_diffusion(s9, e9, dt=0.1, steps=500)
    w1 = coherence(recon, e9).omega
    assert traj[-1] <= traj[0] + 1e-9 and all(traj[i + 1] <= traj[i] + 1e-9 for i in range(len(traj) - 1)), \
        "omega must be non-increasing under the flow"
    print(f"    omega {w0:.4f} -> {w1:.6f} over {len(traj)} steps (identity maps => consensus/average)")
    # identity-map consensus == the mean; verify the fixpoint is the average
    mean = sum(s9.values()) / 3.0
    assert all(np.linalg.norm(recon[v] - mean) < 1e-3 for v in recon), "identity diffusion should reach the mean"
    print("    reconciled state == organ mean (as theory predicts for identity maps)  OK")

    # ------------------------------------------------------------- E1 tests
    print("\n=== 10. E1: rho factors EXACTLY as alpha * rho_tilde ===")
    s10 = {m: rng.normal(size=d) for m in ["a", "b", "c", "d2"]}
    e10 = [("a", "b"), ("b", "c"), ("c", "d2")]
    r10 = coherence(s10, e10)
    assert r10.split_status == "ok", r10.split_status
    prod = r10.alpha * r10.rho_tilde
    assert abs(prod - r10.rho) < 1e-12, (prod, r10.rho)
    print(f"    {r10.summary()}")
    print(f"    {r10.split_summary()}")
    print(f"    alpha*rho_tilde = {prod:.12f} == rho = {r10.rho:.12f}  OK")

    print("\n=== 11. E1: omega equals the Rayleigh form on x_perp, and the window holds ===")
    verts10 = list(s10.keys())
    X10 = np.stack([s10[v] for v in verts10])
    Xp = _kernel_orthogonal_part(X10, verts10, e10)
    L10 = _weighted_graph_laplacian(verts10, e10, lambda e: 1.0)
    omega_perp = float(np.trace(Xp.T @ L10 @ Xp))
    assert abs(omega_perp - r10.omega) < 1e-9, (omega_perp, r10.omega)
    lo, hi = r10.window
    assert lo - 1e-12 <= r10.rho_tilde <= hi + 1e-12, (lo, r10.rho_tilde, hi)
    print(f"    omega via x_perp^T L x_perp = {omega_perp:.6f} == omega = {r10.omega:.6f}  OK")
    print(f"    rho_tilde {r10.rho_tilde:.4f} lies inside [{lo:.4f}, {hi:.4f}]  OK")

    print("\n=== 12. E1: FRAGMENTED case uses PER-COMPONENT means (not the global mean) ===")
    # Two disconnected pairs, far apart. Between-component separation lies IN
    # ker L and must NOT be counted as dissent. A global-mean projection would
    # report large alpha here; the correct one reports ~0.
    far = np.zeros(d); far[0] = 50.0
    s12 = {"p": base, "q": base, "r": base + far, "s": base + far}
    e12 = [("p", "q"), ("r", "s")]
    r12 = coherence(s12, e12)
    assert r12.b0 == 2
    assert r12.alpha is not None and r12.alpha < 1e-12, r12.alpha
    print(f"    b0={r12.b0}, alpha={r12.alpha:.2e} (~0: separated camps each agree internally)  OK")
    print("    a GLOBAL-mean projection would have reported alpha near 1 here -- the bug this avoids")

    print("\n=== 13. E1: perfect consensus has NO mode (bottom, not zero) ===")
    r13 = coherence(s, e)      # all identical from test 1
    assert r13.alpha == 0.0 and r13.rho_tilde is None, (r13.alpha, r13.rho_tilde)
    assert r13.split_status == "consensus"
    print(f"    {r13.split_summary()}  OK")

    print("\n=== 14. E1: non-identity maps => split honestly REFUSED, rho still exact ===")
    Q, _ = np.linalg.qr(rng.normal(size=(d, d)))
    rm14 = {("a", "b"): (Q, np.eye(d))}
    r14 = coherence(s10, e10, restriction=rm14)
    assert r14.rho is not None and r14.alpha is None
    assert r14.split_status == "non_identity_maps"
    print(f"    {r14.split_summary()}  (rho itself unaffected: {r14.rho:.4f})  OK")

    print("\n=== 15. E1 HEADLINE: is alpha small for encoder-geometric reasons? ===")
    # The audit (finding F12) disputes the claim that alpha is small because
    # sentence encoders are anisotropic. bge-small returns UNIT-NORMALISED
    # vectors, for which alpha = (n-1)(1 - cbar)/n exactly, where cbar is the
    # mean pairwise cosine. The logbook records cos(math, chat) = 0.449 for
    # genuinely unrelated content. Simulate that regime and read alpha off.
    def unit_rows_with_mean_cos(n_organs, cbar, dim, rng_):
        """n unit vectors with mean pairwise cosine ~= cbar (common-direction trick)."""
        shared = rng_.normal(size=dim); shared /= np.linalg.norm(shared)
        w = np.sqrt(max(cbar, 0.0))
        out = []
        for _ in range(n_organs):
            r = rng_.normal(size=dim); r -= (r @ shared) * shared
            r /= np.linalg.norm(r)
            v = w * shared + np.sqrt(1 - w * w) * r
            out.append(v / np.linalg.norm(v))
        return out

    print("    n=7 organs, unit-normalised, path-graph coarse complex:")
    for cbar in (0.449, 0.7, 0.9, 0.98):
        rows = unit_rows_with_mean_cos(7, cbar, 64, np.random.default_rng(7))
        names = [f"o{i}" for i in range(7)]
        s15 = dict(zip(names, rows))
        e15 = [(names[i], names[i + 1]) for i in range(6)]
        r15 = coherence(s15, e15)
        predicted = 6 * (1 - cbar) / 7          # (n-1)(1-cbar)/n for unit rows
        print(f"      cbar={cbar:.3f} -> alpha={r15.alpha:.4f} (closed form {predicted:.4f}), "
              f"rho={r15.rho:.4f}, rho_tilde={r15.rho_tilde:.4f}")
    print("    READ THIS: alpha is NOT small at the logbook's observed similarity.")
    print("    The compression of rho is coming substantially from rho_tilde and from")
    print("    B over-bounding lambda_max -- NOT from encoder anisotropy alone.")
    print("    => audit finding F12 stands; the book's section 5.4(a) needs correcting.")

    print("\nALL COHERENCE SELF-TESTS PASSED")
