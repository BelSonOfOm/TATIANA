"""Generate assembly logs under the NEW retrieval rule: top-k on abtt vectors.

Supersedes `simulate_retrieval.py` as the generator. That file is KEPT because it
is the faithful record of the OLD rule (eps-ball on raw vectors), and the two
must remain comparable.

THE RULE, AND WHY EACH PIECE (measured, DOCS/THE_RETRIEVAL_PROBLEM.md 10):
  * top-k, not an eps-ball. Measured against 2266 ground-truth \\ref positives:
    the engine's eps=0.10 admits 0.31% of true dependencies; top-k at the same
    average width scores 46.6% vs the eps-ball's 37.5%, and removes the variance
    (no empty ticks, no over-cap ticks).
  * k = 24, DERIVED not chosen: 5as budgeted 6.1M triangles from the 5.9 GB
    machine, and C(24,3) * 3000 ticks = 6.07M. Retrieval width IS the triangle
    cap, so no assembly is ever skipped and b1 is uncontaminated BY CONSTRUCTION
    rather than by a counter that warns afterwards.
  * abtt (all-but-the-top): subtract the corpus mean and the top-r principal
    directions, renormalise. Worth +4.3 points of recall@30. Renormalising is
    NOT optional -- it keeps ||q|| = 1, hence D1 = D2 = 1, hence the epistemic
    term of W2 vanishes exactly (identity (2)); without it a fresh stalk floor
    puts every concept ~346 away on variance alone and nothing is ever retrieved.

THE GEOMETRIC NULL (`--null geometric`). 4.3 raised a hazard the Tier-0 machinery
cannot see: the observed rows are METRIC BALLS, and ball geometry has coherence
(if a and b are both near q they are near each other) that a Bernoulli mixture
cannot generate -- so ball structure could be read as latent-cause structure. The
control: replace the concept cloud with a draw from the maximum-entropy
distribution matching its first two moments -- a Gaussian with the same mean and
covariance -- then run the SAME top-k rule. That preserves the pedestal, the
anisotropy, the effective dimensionality and the ball geometry, and destroys any
latent cover. If Tier 0 reports COVER on this too, the signal is geometry, not
semantics.

    python make_assemblies.py --concepts concepts.npz --queries queries.npz \\
        --top-k 24 --abtt 10 --out assembly_events.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Optional, Tuple

import numpy as np


def unit(X: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(X, axis=1, keepdims=True)
    n[n == 0] = 1.0
    return X / n


def fit_abtt(C: np.ndarray, r: int) -> Tuple[np.ndarray, np.ndarray]:
    """Fit on the CONCEPTS only, then apply to both concepts and queries -- the
    transform must be one shared map or the two live in different geometries."""
    mu = C.mean(axis=0, keepdims=True)
    Cc = C - mu
    if r <= 0:
        return mu, np.zeros((0, C.shape[1]))
    _, _, Vt = np.linalg.svd(Cc, full_matrices=False)
    return mu, Vt[:r]


def apply_abtt(X: np.ndarray, mu: np.ndarray, P: np.ndarray) -> np.ndarray:
    Y = X - mu
    if P.shape[0]:
        Y = Y - (Y @ P.T) @ P
    return unit(Y)


def gaussian_surrogate(C: np.ndarray, n: int, rng: np.random.Generator,
                       ridge: float = 1e-6) -> np.ndarray:
    """Max-entropy sample matching the concept cloud's mean and covariance.
    Anything beyond second order -- clusters, latent causes, a cover -- is gone."""
    mu = C.mean(axis=0)
    S = np.cov(C, rowvar=False) + ridge * np.eye(C.shape[1])
    L = np.linalg.cholesky(S)
    Z = rng.standard_normal((n, C.shape[1]))
    return unit(mu[None, :] + Z @ L.T)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--concepts", required=True)
    ap.add_argument("--queries", required=True)
    ap.add_argument("--top-k", type=int, default=24)
    ap.add_argument("--abtt", type=int, default=10)
    ap.add_argument("--ticks", type=int, default=0, help="0 = one per query")
    ap.add_argument("--null", choices=["none", "geometric"], default="none")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    cd, qd = np.load(args.concepts, allow_pickle=True), np.load(args.queries,
                                                                allow_pickle=True)
    names = [str(x) for x in cd["names"]]
    C, Q = cd["vectors"].astype(np.float64), qd["vectors"].astype(np.float64)
    rng = np.random.default_rng(args.seed)
    print(f"[assemble] {C.shape[0]} concepts, {Q.shape[0]} queries, {C.shape[1]}-d")

    if args.null == "geometric":
        n_q = Q.shape[0]
        C = gaussian_surrogate(C, C.shape[0], rng)
        Q = gaussian_surrogate(C, n_q, rng)
        print("[assemble] GEOMETRIC NULL: concepts and queries replaced by a "
              "Gaussian matching the original cloud's mean and covariance. "
              "Ball geometry preserved, latent structure destroyed.")

    mu, P = fit_abtt(C, args.abtt)
    Cn, Qn = apply_abtt(C, mu, P), apply_abtt(Q, mu, P)
    print(f"[assemble] abtt-{args.abtt}: pedestal "
          f"{float(C.mean(0) @ C.mean(0)):.4f} -> {float(Cn.mean(0) @ Cn.mean(0)):.4f}; "
          f"norms in [{np.linalg.norm(Cn,axis=1).min():.4f}, "
          f"{np.linalg.norm(Cn,axis=1).max():.4f}]  (D1 = D2 = 1 preserved)")

    n_ticks = args.ticks or Qn.shape[0]
    if n_ticks > Qn.shape[0]:
        print(f"[assemble] WARNING: {Qn.shape[0]} distinct queries for {n_ticks} "
              "ticks -- repeats retrieve identical sets and inflate co-activation.")
    idx = np.arange(n_ticks) % Qn.shape[0]

    k = int(min(args.top_k, Cn.shape[0]))
    names_arr = np.asarray(names, dtype=object)
    written = 0
    with open(args.out, "w", encoding="utf-8") as fh:
        for lo in range(0, n_ticks, 512):                 # chunked: T x N never
            hi = min(lo + 512, n_ticks)                   # materialises in full
            S = Qn[idx[lo:hi]] @ Cn.T
            top = np.argpartition(-S, k - 1, axis=1)[:, :k]
            row = np.arange(top.shape[0])[:, None]
            top = top[row, np.argsort(-S[row, top], axis=1)]   # ranked, for the log
            for j in range(top.shape[0]):
                fh.write(json.dumps({"tick": lo + j,
                                     "retrieved": names_arr[top[j]].tolist(),
                                     "grown": []}) + "\n")
                written += 1
    print(f"[assemble] wrote {written} ticks of exactly {k} concepts -> {args.out}")
    print(f"[assemble] triangles implied: C({k},3) * {written} = "
          f"{k*(k-1)*(k-2)//6*written/1e6:.2f}M")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
