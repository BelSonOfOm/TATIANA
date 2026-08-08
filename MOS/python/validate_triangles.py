"""TATIANA — V8: the two preconditions for filling within-assembly triangles.

Logbook 5ar diagnosed that 5ap's "no triangles => b1 = 0" is BACKWARDS: with no
2-cells delta1 = 0, so curl is trivial and harmonic = (im delta0)^perp of
dimension b1 = E - V + b0. Since concept_store inserts each assembly as a
CLIQUE, b1(K_n) = (n-1)(n-2)/2 and the growth address is SWAMPED by artifacts
rather than blocked. The fix -- fill {a,b,c} exactly when all three co-fired in
one assembly -- also closes the "when is a 2-simplex" gap with no new knob.

5ar attached TWO preconditions to that fix, and this script discharges both.
Neither is a formality: one of them changes the design.

  P1  COST. triangles = sum_t C(|A_t|, 3), and |A_t| is whatever SearchOp
      retrieved. `KnowledgeBase::get_relevant_concepts(mu, D, epsilon)` is a
      THRESHOLD SCAN WITH NO LIMIT -- `while (sqlite3_step(stmt) == SQLITE_ROW)`
      over the whole store -- so |A_t| is bounded by the relevance threshold and
      the corpus size, not by any constant. This measures what that costs.

  P2  COUPLED tau_f. V7 closed tau_f but stated its own limit: "E5's complex has
      exactly ONE filled triangle, so exactly one tau_f exists. A complex with
      several triangles SHARING EDGES could in principle couple their tau_f's;
      nothing here tests that." Filling assembly triangles produces massively
      edge-sharing triangles -- in a filled K_n every edge lies in n-2 of them --
      so that untested configuration becomes the normal one. This tests it.

Zero API calls. Pure numpy.
"""

from __future__ import annotations

import itertools
import math
from typing import Dict, List, Sequence, Tuple

import numpy as np

from hodge import Complex2
from derived_scales import tau, forman_mos
from experiment_v7 import split_with_w2

Edge = Tuple[str, str]
Triangle = Tuple[str, str, str]


# ---------------------------------------------------------------------------
# P1 -- COST
# ---------------------------------------------------------------------------

def clique_counts(n: int) -> Tuple[int, int, int]:
    """(edges, triangles, b1_unfilled) for one assembly of size n inserted as a
    clique. b1 of the UNFILLED clique is the artifact count 5ar identified."""
    if n < 1:
        raise ValueError("assembly size must be >= 1")
    e = n * (n - 1) // 2
    t = n * (n - 1) * (n - 2) // 6
    b1 = e - n + 1 if n >= 1 else 0
    return e, t, b1


def cost_table(sizes: Sequence[int], ticks: int = 1500) -> List[dict]:
    """Per-tick and per-run cost as a function of assembly size.

    BYTES PER TRIANGLE is measured against the C++ representation: a
    HodgeTriangle is three HodgeVertex, and HodgeVertex IS std::string. Names
    are shared with the vertex set, so the marginal cost of a triangle is three
    pointers plus map overhead -- call it 3*8 + 24 = 48 B, which is the
    OPTIMISTIC end. Storing names by value would be far worse. Stated as a
    range rather than a single number because the true figure depends on the
    container, and quoting one digit would be false precision.
    """
    rows = []
    for n in sizes:
        e, t, b1 = clique_counts(n)
        rows.append({
            "n": n,
            "edges_per_tick": e,
            "tri_per_tick": t,
            "b1_artifacts_per_tick": b1,
            "tri_per_run": t * ticks,
            "mb_low": t * ticks * 48 / 1e6,
            "mb_high": t * ticks * 96 / 1e6,
        })
    return rows


def report_cost() -> None:
    print("=" * 74)
    print("P1 -- COST OF FILLING WITHIN-ASSEMBLY TRIANGLES")
    print("=" * 74)
    print("\nPer assembly of size n (inserted as a clique, as concept_store does):\n")
    print(f"{'n':>6} {'edges':>10} {'triangles':>12} {'b1 artifacts':>14}"
          f" {'tri @1500 ticks':>18} {'store (MB)':>14}")
    print("-" * 78)
    for r in cost_table([5, 10, 20, 30, 50, 100, 200, 500, 1000]):
        print(f"{r['n']:>6} {r['edges_per_tick']:>10,} {r['tri_per_tick']:>12,}"
              f" {r['b1_artifacts_per_tick']:>14,} {r['tri_per_run']:>18,}"
              f" {r['mb_low']:>7,.0f}-{r['mb_high']:<6,.0f}")

    print("\nTHE SHAPE OF THE PROBLEM: triangles grow as n^3 while edges grow as n^2,")
    print("so the ratio triangles/edges = (n-2)/3 is LINEAR in assembly size.")
    print("There is no assembly size at which the triangle count stops mattering.\n")

    budget_mb = 5900 * 0.10  # a tenth of the 5.9 GB machine, generous for one structure
    print(f"Against a {budget_mb:.0f} MB allowance (10% of the 5.9 GB machine), "
          f"at 1500 ticks:")
    for r in cost_table([10, 20, 30, 50, 100], ticks=1500):
        verdict = "FITS" if r["mb_high"] < budget_mb else "DOES NOT FIT"
        print(f"  n={r['n']:>4}: {r['mb_low']:>8,.0f}-{r['mb_high']:<8,.0f} MB   {verdict}")

    # The cap, derived rather than picked: the largest n whose worst-case store
    # stays inside the allowance.
    cap = max(r["n"] for r in cost_table(list(range(3, 400)), ticks=1500)
              if r["mb_high"] < budget_mb)
    print(f"\n  => LARGEST ASSEMBLY THAT FITS THE ALLOWANCE: n = {cap}")
    print(f"     (at n={cap}: {clique_counts(cap)[1]:,} triangles/tick, "
          f"{clique_counts(cap)[1]*1500:,} per run)")
    print("\n  *** AND get_relevant_concepts HAS NO LIMIT. It is a threshold scan")
    print("      over the whole KB, so |A| is bounded by the relevance threshold")
    print("      and the corpus, NOT by a constant. An uncapped triangle rule is")
    print("      therefore not merely expensive -- at |A|=1000 one tick alone")
    print(f"      wants {clique_counts(1000)[1]:,} triangles. The cap is MANDATORY.")


# ---------------------------------------------------------------------------
# P2 -- COUPLED tau_f
# ---------------------------------------------------------------------------

def filled_clique(n: int) -> Complex2:
    """K_n with every triangle filled: ONE assembly, after the fix. Every edge
    lies in exactly n-2 triangles -- the edge-sharing V7 could not test.

    NOTE it is CONTRACTIBLE (the 2-skeleton of a simplex is simply connected),
    so b1 = 0 and the harmonic space is trivial. That is the whole point of the
    fix, and it also means a single clique is the WRONG object on which to test
    whether W2 moves the harmonic vector: there is no harmonic vector to move.
    Use `necklace` for that.
    """
    vs = [f"c{i}" for i in range(n)]
    es = [(u, v) for u, v in itertools.combinations(vs, 2)]
    ts = [t for t in itertools.combinations(vs, 3)]
    return Complex2(vs, es, ts)


def necklace(k: int, n: int) -> Complex2:
    """k filled assemblies of size n in a ring, consecutive ones sharing ONE
    concept. This is what the store actually looks like after the fix, and it is
    the only configuration on which the W2 question is meaningful.

    Each assembly is a filled clique => contractible, and lots of edge-sharing
    (every internal edge lies in n-2 triangles). The cover {assembly_i} is a
    good cover whose nerve is a k-cycle, so by the nerve lemma b1 = 1: exactly
    ONE surviving cycle, and it is CROSS-ASSEMBLY -- a hole no single assembly
    covers. That is the growth address the fix is meant to expose, as opposed to
    the (n-1)(n-2)/2 within-assembly artifacts it removes.
    """
    if k < 3 or n < 3:
        raise ValueError("need k >= 3 rings of n >= 3 concepts")
    # Shared hinge vertices h0..h_{k-1}; assembly i runs from h_i to h_{i+1}.
    hinges = [f"h{i}" for i in range(k)]
    vs: List[str] = list(hinges)
    groups: List[List[str]] = []
    for i in range(k):
        interior = [f"a{i}_{j}" for j in range(n - 2)]
        vs.extend(interior)
        groups.append([hinges[i]] + interior + [hinges[(i + 1) % k]])

    es_set, ts_set = set(), set()
    for g in groups:
        for u, v in itertools.combinations(sorted(g), 2):
            es_set.add((u, v))
        for t in itertools.combinations(sorted(g), 3):
            ts_set.add(t)
    return Complex2(vs, sorted(es_set), sorted(ts_set))


def betti1(cx: Complex2) -> int:
    """b1 = dim ker(delta1) - dim im(delta0), computed from RANKS.

    Not from the Euler count E - V + b0 - F: that is only valid when delta1 has
    full row rank, which fails badly once triangles share edges (a filled K_7
    has F = 35 but rank(delta1) = 15, and the Euler expression returns -20).
    Getting this wrong is how one would 'measure' a negative Betti number.
    """
    d0, d1 = cx.delta0(), cx.delta1()
    r0 = np.linalg.matrix_rank(d0) if d0.size else 0
    r1 = np.linalg.matrix_rank(d1) if d1.size else 0
    return int(len(cx.edges) - r1 - r0)


def cofaces_per_edge(cx: Complex2) -> Dict[Edge, int]:
    counts = {e: 0 for e in cx.edges}
    for f in cx.triangles:
        for e in itertools.combinations(sorted(f), 2):
            key = cx._canon_edge(*e)
            if key in counts:
                counts[key] += 1
    return counts


def report_coupling(n: int = 7, trials: int = 200, seed: int = 0) -> bool:
    """Does W2 = diag(tau_f) change the Hodge split when triangles SHARE edges?

    V7 proved analytically that it cannot: the adjoint is (delta1)* =
    W1^-1 (delta1)^T W2, and W2 positive-definite => onto => the image is
    unchanged, so tau never reaches the curl subspace. That argument never
    mentions the number of triangles, so it should survive edge-sharing intact.
    But V7 only CHECKED it where exactly one tau_f existed. This checks it where
    every edge is shared by n-2 triangles and the tau_f are therefore correlated
    by construction (they are harmonic means over overlapping edge sets).
    """
    print("\n" + "=" * 74)
    print("P2 -- COUPLED tau_f (V7's stated limit, discharged)")
    print("=" * 74)

    rng = np.random.default_rng(seed)
    # A NECKLACE, not a single clique. One filled clique is contractible, so its
    # harmonic space is ZERO and "does W2 move the harmonic vector" is a
    # question about a vector that is identically zero -- unfailable, therefore
    # worthless. The necklace has the edge-sharing AND a real cycle.
    cx = necklace(k=4, n=n)
    cof = cofaces_per_edge(cx)
    print(f"\nNecklace of 4 filled assemblies of size {n} (consecutive share one"
          f" concept):")
    print(f"  V={len(cx.vertices)} E={len(cx.edges)} F={len(cx.triangles)}")
    print(f"  cofaces per edge: min={min(cof.values())} max={max(cof.values())}"
          f"  (V7 tested this at 1)")
    b1 = betti1(cx)
    print(f"  b1 (from ranks) = {b1}  <- the CROSS-assembly cycle; there must be"
          f" one to move")
    assert b1 >= 1, "the necklace must have a harmonic space or this test is vacuous"

    # Non-uniform pi_e spanning the range V7 measured (203 .. 479, a 2.36x spread).
    pi = {e: float(rng.uniform(203.0, 479.0)) for e in cx.edges}
    tau_f = tau(cx.triangles, pi)
    tv = np.array(list(tau_f.values()))
    print(f"  pi_e  spread: {min(pi.values()):.2f} .. {max(pi.values()):.2f}")
    print(f"  tau_f spread: {tv.min():.2f} .. {tv.max():.2f}  "
          f"({len(tv)} distinct values, V7 had 1)")

    # Correlation between tau_f of triangles that SHARE an edge -- the coupling
    # V7 named. Nonzero correlation is EXPECTED and is not itself a problem;
    # the question is whether it moves the split.
    shared, disjoint = [], []
    tri = list(cx.triangles)
    for a, b in itertools.combinations(range(len(tri)), 2):
        common = len(set(tri[a]) & set(tri[b]))
        pair = (tau_f[tuple(tri[a])], tau_f[tuple(tri[b])])
        (shared if common == 2 else disjoint).append(pair)
    if shared:
        s = np.array(shared)
        r_shared = float(np.corrcoef(s[:, 0], s[:, 1])[0, 1])
        print(f"  corr(tau_f, tau_f') over EDGE-SHARING pairs: {r_shared:+.4f} "
              f"({len(shared)} pairs)  <- the coupling is REAL")

    # hodge.py hard-codes W2 = I, so varying W2 needs V7's explicit form. Reused
    # rather than reimplemented: a second copy of the adjoint is a second place
    # for the (delta1)* = W1^-1 (delta1)^T W2 convention to drift.
    w1 = np.array([pi[e] for e in cx.edges], dtype=float)
    w2_identity = np.eye(len(cx.triangles))
    w2_derived = np.diag([tau_f[tuple(f)] for f in cx.triangles])

    worst_frac = 0.0
    worst_harm = 0.0
    for _ in range(trials):
        eta = rng.standard_normal(len(cx.edges))
        base = split_with_w2(cx, eta, w1, w2_identity)
        derived = split_with_w2(cx, eta, w1, w2_derived)
        for k in ("grad", "curl", "harm"):
            worst_frac = max(worst_frac, abs(base[k] - derived[k]))
        worst_harm = max(worst_harm,
                         float(np.max(np.abs(base["harm_vec"] - derived["harm_vec"]))))

    print(f"\n  W2 = I  vs  W2 = diag(tau_f), over {trials} random cochains:")
    print(f"    worst fraction delta  : {worst_frac:.3e}")
    print(f"    worst harmonic delta  : {worst_harm:.3e}   <- the growth address")

    # A POSITIVE CONTROL, because a comparison that cannot fail proves nothing.
    # Perturbing W1 (the C^1 inner product) MUST move the split -- if this comes
    # back at 1e-16 too, the harness is comparing something to itself and the
    # PASS above is meaningless.
    moved = 0.0
    for _ in range(trials):
        eta = rng.standard_normal(len(cx.edges))
        a = split_with_w2(cx, eta, w1, w2_identity)
        b = split_with_w2(cx, eta, w1 * rng.uniform(0.5, 2.0, size=w1.size),
                          w2_identity)
        moved = max(moved, abs(a["harm"] - b["harm"]))
    print(f"    positive control (perturb W1): {moved:.3e}  <- MUST be large")

    # F_MOS is where the coface count actually bites: the term is
    # pi_e^2 * sum_{f > e} 1/tau_f, and that sum now has n-2 terms, not 1.
    print("\n  F_MOS coface term vs. cofaces per edge (this is what CHANGES):")
    print(f"  {'n':>5} {'cofaces/edge':>14} {'F_MOS(e)':>16} {'vs n=3':>12}")
    print("  " + "-" * 50)
    base = None
    for m in (3, 4, 5, 6, 7, 8):
        cxm = filled_clique(m)
        pim = {e: 300.0 for e in cxm.edges}
        e0 = cxm.edges[0]
        f = forman_mos(e0, cxm.edges, cxm.triangles, pim, nu={v: 0.0 for v in cxm.vertices})
        cofm = cofaces_per_edge(cxm)[e0]
        if base is None:
            base = f
        print(f"  {m:>5} {cofm:>14} {f:>16,.2f} {f/base:>11.2f}x")

    ok = worst_harm < 1e-9 and moved > 1e-6
    print(f"\n  => {'PASS' if ok else 'FAIL'}: edge-sharing does NOT move the Hodge "
          f"split (worst {worst_harm:.1e}), and the control confirms the")
    print(f"     harness can detect movement when there is any ({moved:.1e}).")
    print("     V7's analytic argument (W2 invertible => image unchanged) never")
    print("     depended on the triangle count, and it survives the coupling.")
    print("     ** But F_MOS DOES scale with cofaces/edge, which is not a bug --")
    print("        it is the curvature of a genuinely denser complex. Any kappa_hi/")
    print("        kappa_lo threshold calibrated on ONE triangle per edge is stale.")
    return ok


def report_b1_repair() -> None:
    """The claim 5ar makes: filling within-assembly triangles kills the
    artifacts. Asserted numerically rather than cited."""
    print("\n" + "=" * 74)
    print("WHAT THE FIX ACTUALLY REPAIRS")
    print("=" * 74)
    print("\nONE assembly in isolation -- every cycle here is an ARTIFACT of")
    print("inserting a clique and refusing to fill it:\n")
    print(f"{'n':>5} {'b1 UNFILLED':>14} {'b1 FILLED':>12}   (both from ranks)")
    print("-" * 50)
    for n in (3, 5, 7, 10, 20, 50):
        _, _, b1u_formula = clique_counts(n)
        if n <= 10:  # rank computation is O(E^3); check the formula where cheap
            vs = [f"c{i}" for i in range(n)]
            es = [(u, v) for u, v in itertools.combinations(vs, 2)]
            b1u = betti1(Complex2(vs, es))
            b1f = betti1(filled_clique(n))
            assert b1u == b1u_formula, "clique b1 formula disagrees with ranks"
            assert b1f == 0, "a filled clique must be simply connected"
            print(f"{n:>5} {b1u:>14,} {b1f:>12}")
        else:
            print(f"{n:>5} {b1u_formula:>14,} {0:>12}   (formula; rank check "
                  f"done up to n=10)")

    print("\n  The 2-skeleton of a simplex is simply connected, so EVERY")
    print("  within-assembly cycle dies. No tetrahedra are needed -- H1 depends")
    print("  only on the 2-skeleton. What survives is CROSS-assembly, i.e. real:")

    for k in (3, 4, 5):
        nk = necklace(k, 5)
        print(f"    necklace of {k} filled assemblies -> b1 = {betti1(nk)}"
              f"  (nerve is a {k}-cycle, so the nerve lemma predicts 1)")


if __name__ == "__main__":
    report_cost()
    ok = report_coupling()
    report_b1_repair()
    print("\n" + "=" * 74)
    print("VERDICT")
    print("=" * 74)
    print("P1 COST     : the rule is affordable ONLY with an explicit cap on")
    print("              assembly size. get_relevant_concepts is unbounded, so")
    print("              without a cap one wide tick can dominate the store.")
    print(f"P2 COUPLING : {'DISCHARGED' if ok else 'FAILED'} -- edge-sharing tau_f does not move the")
    print("              Hodge split. F_MOS scale DOES change; recalibrate.")
    raise SystemExit(0 if ok else 1)
