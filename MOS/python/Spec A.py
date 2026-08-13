#!/usr/bin/env python3
"""
SPEC A — THE GROWTH-ADDRESS MEASUREMENT
Implements DOCS/SPEC_GROWTH_ADDRESS_AND_DYNAMICS.md sections 3.3-3.7.

Hodge-decomposes an observed succession flow  eta  on the clique complex of the
undirected citation graph into

        eta  =  grad (ranking)  (+)  curl (local tangles)  (+)  harm (holes)

The harmonic part is the GROWTH ADDRESS: circulation that no global ranking and
no filled triangle can explain.

Usage
    python3 spec_a.py --self-test           # controls 1-4, no data needed
    python3 spec_a.py --edges pairs.tsv     # real run: 'i<TAB>j' = i cites j
    python3 spec_a.py --edges pairs.tsv --null 1000

Epistemic status: this file is an INSTRUMENT, not a result. It reports numbers;
whether they mean anything is decided by the controls, which must ALL pass at
one shared setting before any real-data number is read.
"""

import argparse
import sys
from collections import defaultdict

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import lsqr


# ----------------------------------------------------------------------------
# Complex construction  (spec 3.5 steps 1-3)
# ----------------------------------------------------------------------------

def build_complex(directed_pairs, fill="clique"):
    """directed_pairs: iterable of (i, j) meaning 'i cites j'.

    Returns vertices, edges (i<j, sorted), triangles (i<j<k), and the flow eta.
    """
    count = defaultdict(int)
    verts = set()
    for i, j in directed_pairs:
        if i == j:
            continue                       # self-citation carries no direction
        verts.add(i)
        verts.add(j)
        count[(i, j)] += 1

    verts = sorted(verts)
    vid = {v: n for n, v in enumerate(verts)}

    # step 1: undirected edge whenever a citation runs EITHER way
    und = set()
    for (i, j) in count:
        a, b = vid[i], vid[j]
        und.add((min(a, b), max(a, b)))
    edges = sorted(und)
    eid = {e: n for n, e in enumerate(edges)}

    # step 2: the flow, antisymmetric by construction
    eta = np.zeros(len(edges))
    for (i, j), c in count.items():
        a, b = vid[i], vid[j]
        e = (min(a, b), max(a, b))
        eta[eid[e]] += c if a < b else -c

    # step 3: triangles
    if fill == "clique":
        adj = defaultdict(set)
        for a, b in edges:
            adj[a].add(b)
            adj[b].add(a)
        tris = set()
        for a, b in edges:
            for c in adj[a] & adj[b]:
                tris.add(tuple(sorted((a, b, c))))
        tris = sorted(tris)
    elif fill == "none":
        tris = []
    else:
        raise ValueError(fill)

    return verts, vid, edges, eid, tris, eta


def coboundaries(nV, edges, eid, tris):
    """delta0: E x V,  delta1: T x E, with the i<j orientation convention."""
    r, c, d = [], [], []
    for n, (a, b) in enumerate(edges):
        r += [n, n]
        c += [a, b]
        d += [-1.0, 1.0]                   # (d0 psi)(a,b) = psi(b) - psi(a)
    d0 = sp.csr_matrix((d, (r, c)), shape=(len(edges), nV))

    r, c, d = [], [], []
    for n, (a, b, cc) in enumerate(tris):
        # (d1 eta)(a,b,c) = eta(a,b) + eta(b,c) - eta(a,c)
        r += [n, n, n]
        c += [eid[(a, b)], eid[(b, cc)], eid[(a, cc)]]
        d += [1.0, 1.0, -1.0]
    d1 = sp.csr_matrix((d, (r, c)), shape=(len(tris), len(edges)))
    return d0, d1


# ----------------------------------------------------------------------------
# The decomposition  (spec 3.5 steps 4-7, self-test 3.6)
# ----------------------------------------------------------------------------

def hodge(eta, d0, d1, atol=1e-12, iter_lim=20000):
    psi = lsqr(d0, eta, atol=atol, btol=atol, iter_lim=iter_lim)[0]
    grad = d0 @ psi
    resid = eta - grad

    if d1.shape[0] > 0:
        phi = lsqr(d1.T, resid, atol=atol, btol=atol, iter_lim=iter_lim)[0]
        curl = d1.T @ phi
    else:
        curl = np.zeros_like(eta)
    harm = resid - curl

    tot = float(eta @ eta)
    parts = dict(
        ranking=float(grad @ grad) / tot if tot else 0.0,
        tangles=float(curl @ curl) / tot if tot else 0.0,
        holes=float(harm @ harm) / tot if tot else 0.0,
    )
    # built-in self-test: orthogonality forces the three to sum to 1
    parts["closure_error"] = abs(sum(v for k, v in parts.items()
                                     if k != "closure_error") - 1.0)
    return parts, psi, harm


def betti1(nV, edges, d1):
    g = sp.csr_matrix((np.ones(len(edges)), ([e[0] for e in edges],
                                             [e[1] for e in edges])),
                      shape=(nV, nV))
    ncomp = sp.csgraph.connected_components(g, directed=False)[0]
    rank_d1 = np.linalg.matrix_rank(d1.toarray()) if d1.shape[0] else 0
    return len(edges) - (nV - ncomp) - rank_d1


def run(directed_pairs, fill="clique", label=""):
    verts, vid, edges, eid, tris, eta = build_complex(directed_pairs, fill)
    d0, d1 = coboundaries(len(verts), edges, eid, tris)
    parts, psi, harm = hodge(eta, d0, d1)
    parts["b1"] = betti1(len(verts), edges, d1)
    parts["V"], parts["E"], parts["T"] = len(verts), len(edges), len(tris)
    parts["_edges"], parts["_harm"], parts["_psi"] = edges, harm, psi
    parts["_verts"] = verts
    return parts


# ----------------------------------------------------------------------------
# Controls  (spec 3.7) — ALL must pass at one shared setting
# ----------------------------------------------------------------------------

def self_test():
    print("SPEC A — CONTROLS (spec 3.7)\n" + "=" * 62)
    ok = True

    # 1. directed path / tree -> holes = 0
    r = run([("a", "b"), ("b", "c"), ("c", "d"), ("b", "e")])
    p = r["holes"] < 1e-8
    ok &= p
    print(f"  1  path/tree            holes={r['holes']:.3e}  b1={r['b1']}   "
          f"{'PASS' if p else 'FAIL'}   (catches: broken decomposition)")

    # 2. directed 4-cycle, no triangles -> holes = 100%
    r = run([("a", "b"), ("b", "c"), ("c", "d"), ("d", "a")], fill="none")
    p = r["holes"] > 0.999
    ok &= p
    print(f"  2  4-cycle, unfilled    holes={r['holes']:.6f}  b1={r['b1']}   "
          f"{'PASS' if p else 'FAIL'}   (catches: insensitivity)")

    # 3. directed triangle, FILLED -> curl = 100%, holes = 0   [the crucial one]
    r = run([("a", "b"), ("b", "c"), ("c", "a")], fill="clique")
    p = r["tangles"] > 0.999 and r["holes"] < 1e-8
    ok &= p
    print(f"  3  filled 3-cycle       curl={r['tangles']:.6f} "
          f"holes={r['holes']:.3e}   {'PASS' if p else 'FAIL'}   "
          f"(catches: curl/harmonic LEAKAGE)")

    # 4. planted gradient on a graph WITH cycles -> ranking = 100%, holes = 0
    rng = np.random.default_rng(0)
    nV, nE = 40, 160
    und = set()
    while len(und) < nE:
        a, b = rng.integers(0, nV, 2)
        if a != b:
            und.add((min(a, b), max(a, b)))
    und = sorted(und)
    psi_true = rng.normal(size=nV)
    pairs = [(a, b) for a, b in und]       # geometry only; eta is planted below
    verts, vid, edges, eid, tris, _ = build_complex(pairs)
    d0, d1 = coboundaries(len(verts), edges, eid, tris)
    eta_exact = d0 @ psi_true[[vid[v] for v in verts]]
    parts, _, _ = hodge(eta_exact, d0, d1)
    p = parts["ranking"] > 0.999 and parts["holes"] < 1e-6
    ok &= p
    print(f"  4  planted gradient     rank={parts['ranking']:.6f} "
          f"holes={parts['holes']:.3e}  b1={betti1(len(verts), edges, d1)}  "
          f"{'PASS' if p else 'FAIL'}   (catches: leakage between parts)")

    # 4b. THE QUANTISATION FLOOR — not in the spec, and it should be.
    #     Real eta is a difference of integer citation counts, so an exact
    #     gradient is UNREACHABLE on real data. This measures the holes% that
    #     integer rounding alone manufactures. Any real number below it is noise.
    eta_int = np.round(eta_exact * 20.0)
    parts_q, _, _ = hodge(eta_int, d0, d1)
    print(f"  4b QUANTISATION FLOOR   rank={parts_q['ranking']:.6f} "
          f"holes={parts_q['holes']:.3e}        FLOOR   "
          f"(integer counts cannot express an exact gradient)")

    # 5b. planted HOLE: a long cycle with no chords, circulation on it.
    #     Not in the spec's list; added because controls 1-4 never check that a
    #     hole survives the presence of a large filled background.
    n = 12
    pairs = [(f"c{i}", f"c{(i + 1) % n}") for i in range(n)]
    r = run(pairs, fill="clique")
    p = r["holes"] > 0.999
    ok &= p
    print(f"  5b 12-cycle, chordless  holes={r['holes']:.6f}  b1={r['b1']}   "
          f"{'PASS' if p else 'FAIL'}   (catches: hole destroyed by clique fill)")

    print("=" * 62)
    print("ALL CONTROLS PASS" if ok else "*** CONTROL FAILURE — instrument unusable ***")
    return ok


# ----------------------------------------------------------------------------
# Control 5 — the direction-randomised null.  Without it the number is unreadable.
# ----------------------------------------------------------------------------

def analytic_null_holes(b1, nE):
    """[DERIVED] For an isotropically direction-randomised flow, the expected
    fraction of energy in any subspace is its dimension fraction. dim H^1 = b1,
    so  E[holes%] = b1 / |E|.  Confirmed against simulation to ~1% (see notes).

    CONSEQUENCE, and it amends spec 3.8: on a sparse graph b1/|E| is LARGE
    (0.61 on the synthetic corpus), so a high holes% is the NULL EXPECTATION,
    not a signal. 'Holes above null' is the wrong headline. Use ranking% vs
    null, plus per-cycle localisation of harmonic mass.
    """
    return b1 / nE if nE else 0.0


def null_distribution(directed_pairs, draws, seed=0):
    rng = np.random.default_rng(seed)
    pairs = list(directed_pairs)
    out = []
    for _ in range(draws):
        flipped = [(j, i) if rng.random() < 0.5 else (i, j) for i, j in pairs]
        out.append(run(flipped)["holes"])
    return np.array(out)


def top_cycles(res, k=10):
    """The concept pairs carrying the most harmonic mass — the addresses."""
    edges, harm, verts = res["_edges"], res["_harm"], res["_verts"]
    order = np.argsort(-np.abs(harm))[:k]
    return [(verts[edges[i][0]], verts[edges[i][1]], float(harm[i]))
            for i in order]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--edges", help="TSV of 'citing<TAB>cited'")
    ap.add_argument("--null", type=int, default=0)
    a = ap.parse_args()

    if a.self_test or not a.edges:
        sys.exit(0 if self_test() else 1)

    pairs = []
    with open(a.edges) as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) >= 2:
                pairs.append((parts[0], parts[1]))

    if not self_test():
        print("\nRefusing to report a real-data number: controls failed.")
        sys.exit(1)

    r = run(pairs)
    print(f"\nREAL RUN   V={r['V']}  E={r['E']}  T={r['T']}  b1={r['b1']}")
    print(f"  ranking (one global ordering)   {r['ranking']*100:6.2f}%")
    print(f"  tangles (loops around units)    {r['tangles']*100:6.2f}%")
    print(f"  holes   (GROWTH ADDRESSES)      {r['holes']*100:6.2f}%")
    print(f"  closure error                   {r['closure_error']:.2e}")

    if a.null:
        nd = null_distribution(pairs, a.null)
        z = (r["holes"] - nd.mean()) / (nd.std() + 1e-30)
        print(f"\nNULL ({a.null} direction-randomised draws)")
        print(f"  mean {nd.mean()*100:.2f}%   sd {nd.std()*100:.2f}%   z = {z:+.2f}")
        print(f"  p(null >= observed) = {(nd >= r['holes']).mean():.4f}")
        print("  READ THIS, NOT THE RAW PERCENTAGE.")

    print("\nTOP HARMONIC EDGES (the addresses):")
    for u, v, h in top_cycles(r):
        print(f"  {h:+.3f}   {u} — {v}")


if __name__ == "__main__":
    main()