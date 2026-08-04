"""Decide the retrieval question with numbers instead of argument.

WHAT THIS ANSWERS. DOCS/THE_RETRIEVAL_PROBLEM.md lists candidate fixes that
nobody could rank, because relatedness had exactly ONE hand-checked label. With
`extract_refs.py`'s \\ref edges as ground-truth positives, every candidate becomes
measurable by the same question:

    when block B explicitly cites block A, where does A land in B's ranked
    retrieval list?

That is a RECALL metric, which is the only kind these labels support: \\ref edges
are high-precision positives and say nothing about non-edges (see extract_refs).

THE HEADLINE NUMBER IS recall@30, because 5as derived `max_assembly_for_triangles
= 30` from the memory budget -- a positive ranked below 30 is one the engine can
never put in a 2-cell.

TRANSFORMS COMPARED (the design space of THE_RETRIEVAL_PROBLEM 5.1/5.2):
    raw          cosine on unit vectors                 -- what the engine does now
    centered     subtract corpus mean, renormalise      -- option C, weak form
    abtt-k       centered + drop top k PCs              -- option C, Mu-Viswanath
    localscale   Zelnik-Manor/Perona self-tuning        -- 5.1(d) / R1-lite
    diffusion    Coifman-Lafon diffusion distance       -- R1 proper

`raw` is monotone in cosine, so raw and any global rescaling of it give IDENTICAL
ranks. Softmax/Boltzmann is therefore NOT listed: it provably cannot change a
single number in this table. Only the non-monotone transforms can.

    python measure_reference_recall.py --refs refs_corpus.json
"""
from __future__ import annotations

# The thread cap MUST be set before onnxruntime is imported -- it reads these at
# session creation. Setting them afterwards does nothing, which is how the first
# ingest pegged every core and lost a 10-minute run (5ap).
import os
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("ONNXRUNTIME_NUM_THREADS", "2")

import argparse
import json
import sys
from typing import Dict, List, Optional

import numpy as np

KS = (1, 5, 10, 30, 100)
CAP = 30          # 5as: max_assembly_for_triangles


# ------------------------------------------------------------- embed blocks --

def embed_blocks(texts: List[str], cache: str, batch: int = 64) -> np.ndarray:
    if os.path.exists(cache):
        V = np.load(cache)["vectors"]
        if V.shape[0] == len(texts):
            print(f"[embed] cache hit: {V.shape}")
            return V
        print("[embed] cache stale, re-embedding")
    from fastembed import TextEmbedding
    print(f"[embed] loading BAAI/bge-small-en-v1.5 (2 threads) ...")
    model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5", threads=2)
    out = []
    for i in range(0, len(texts), batch):
        out.extend(model.embed(texts[i:i + batch]))
        print(f"\r[embed] {min(i+batch, len(texts))}/{len(texts)}", end="", flush=True)
    print()
    V = np.asarray(out, dtype=np.float64)
    V /= np.linalg.norm(V, axis=1, keepdims=True)
    np.savez_compressed(cache, vectors=V)
    return V


# --------------------------------------------------------------- transforms --

def _unit(X: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(X, axis=1, keepdims=True)
    n[n == 0] = 1.0
    return X / n


def t_raw(X: np.ndarray) -> np.ndarray:
    return X @ X.T


def t_centered(X: np.ndarray) -> np.ndarray:
    Y = _unit(X - X.mean(axis=0, keepdims=True))
    return Y @ Y.T


def t_abtt(X: np.ndarray, k: int) -> np.ndarray:
    """Mu & Viswanath: remove the mean AND the top-k principal directions."""
    Xc = X - X.mean(axis=0, keepdims=True)
    _, _, Vt = np.linalg.svd(Xc, full_matrices=False)
    P = Vt[:k]                                   # k x d
    Y = _unit(Xc - (Xc @ P.T) @ P)
    return Y @ Y.T


def _sq_dists(X: np.ndarray) -> np.ndarray:
    g = (X * X).sum(axis=1)
    D = g[:, None] + g[None, :] - 2.0 * (X @ X.T)
    np.maximum(D, 0.0, out=D)
    np.fill_diagonal(D, 0.0)
    return D


def t_localscale(X: np.ndarray, m: int = 7) -> np.ndarray:
    """Zelnik-Manor & Perona self-tuning: each point gets its own bandwidth,
    sigma_i = distance to its m-th neighbour. Similarity -d2/(sigma_i sigma_j)
    is NOT monotone in d2, so this can and does reorder."""
    D = _sq_dists(X)
    d = np.sqrt(D)
    part = np.partition(d, m, axis=1)[:, m]
    sig = np.maximum(part, 1e-9)
    return -D / (sig[:, None] * sig[None, :])


def t_diffusion(X: np.ndarray, t: float = 2.0, alpha: float = 1.0,
                m_bw: int = 7, n_comp: int = 128) -> np.ndarray:
    """Coifman-Lafon. alpha=1 divides out sampling density; t is diffusion time.
    Returned as a SIMILARITY (negated diffusion distance) so ranking is uniform
    across transforms."""
    D = _sq_dists(X)
    d = np.sqrt(D)
    part = np.partition(d, m_bw, axis=1)[:, m_bw]
    sig = np.maximum(part, 1e-9)
    W = np.exp(-D / (sig[:, None] * sig[None, :]))       # adaptive-bandwidth kernel

    q = W.sum(axis=1)
    W = W / np.power(np.outer(q, q), alpha)              # density normalisation
    dd = W.sum(axis=1)
    dd[dd <= 0] = 1e-12
    s = 1.0 / np.sqrt(dd)
    S = W * s[:, None] * s[None, :]                      # symmetric conjugate of P
    S = 0.5 * (S + S.T)

    n_comp = int(min(n_comp, S.shape[0]))
    lam, U = np.linalg.eigh(S)
    idx = np.argsort(lam)[::-1][:n_comp]
    lam, U = lam[idx], U[:, idx]
    Phi = U * s[:, None]                                 # right eigenvectors of P
    Psi = Phi * np.power(np.abs(lam), t)[None, :]        # diffusion coordinates
    return -_sq_dists(Psi)


# ------------------------------------------------------------------ scoring --

def rank_positives(S: np.ndarray, edges: List[tuple],
                   restrict: Optional[np.ndarray] = None) -> np.ndarray:
    """Rank of each cited block within the source's ranked candidate list.
    Rank 1 = the top hit. `restrict[i]` is a boolean mask of admissible
    candidates for source i (used for the within-paper variant)."""
    ranks = np.empty(len(edges), dtype=np.int64)
    for e, (i, j) in enumerate(edges):
        row = S[i].copy()
        row[i] = -np.inf                                    # never retrieve self
        if restrict is not None:
            row = np.where(restrict[i], row, -np.inf)
        # rank = 1 + number of admissible candidates scoring strictly higher
        ranks[e] = 1 + int(np.sum(row > row[j]))
    return ranks


def summarise(ranks: np.ndarray, n_cand: float) -> Dict[str, float]:
    out = {f"r@{k}": float(np.mean(ranks <= k)) for k in KS}
    out["median_rank"] = float(np.median(ranks))
    out["mrr"] = float(np.mean(1.0 / ranks))
    out["n"] = int(len(ranks))
    out["cand"] = float(n_cand)
    return out


def geometry_report(X: np.ndarray, papers: np.ndarray, rng) -> Dict[str, float]:
    """The pedestal, measured directly rather than inferred from a sweep."""
    mu = X.mean(axis=0)
    pedestal = float(mu @ mu)
    n = X.shape[0]
    a = rng.integers(0, n, 40000)
    b = rng.integers(0, n, 40000)
    ok = (a != b) & (papers[a] != papers[b])
    cos_unrel = np.einsum("ij,ij->i", X[a[ok]], X[b[ok]])
    return {"pedestal_mu_sq": pedestal,
            "mu_norm": float(np.sqrt(pedestal)),
            "cos_unrelated_mean": float(cos_unrel.mean()),
            "cos_unrelated_median": float(np.median(cos_unrel)),
            "cos_unrelated_sd": float(cos_unrel.std())}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--refs", required=True)
    ap.add_argument("--cache", default=None)
    ap.add_argument("--abtt-k", type=int, default=3)
    ap.add_argument("--diff-t", type=float, default=2.0)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    with open(args.refs, encoding="utf-8") as fh:
        data = json.load(fh)
    blocks, edge_recs = data["blocks"], data["edges"]
    index = {b["id"]: i for i, b in enumerate(blocks)}
    edges = [(index[e["src"]], index[e["dst"]]) for e in edge_recs]
    papers = np.array([b["paper"] for b in blocks])
    print(f"[data] {len(blocks)} blocks, {len(edges)} ref-edges, "
          f"{len(set(papers))} papers")

    cache = args.cache or os.path.splitext(args.refs)[0] + "_vecs.npz"
    X = embed_blocks([b["text"] for b in blocks], cache)
    print(f"[data] vectors {X.shape}, norms in "
          f"[{np.linalg.norm(X,axis=1).min():.4f}, {np.linalg.norm(X,axis=1).max():.4f}]")

    rng = np.random.default_rng(0)
    geo = geometry_report(X, papers, rng)
    print("\n=== GEOMETRY (measured, not inferred) ===")
    for k, v in geo.items():
        print(f"  {k:24s} {v:.4f}")

    # Reproduce the engine's own rule on this data: eps=0.1 <=> cos >= 0.95.
    cos_pos = np.array([float(X[i] @ X[j]) for i, j in edges])
    print(f"\n=== THE ENGINE'S CURRENT RULE, ON THE LABELLED POSITIVES ===")
    print(f"  cited-pair cosine: median {np.median(cos_pos):.4f}, "
          f"mean {cos_pos.mean():.4f}")
    for eps in (0.10, 0.40, 0.53):
        print(f"  eps={eps:.2f} (cos>={1-eps/2:.3f}): admits "
              f"{100.0*np.mean(cos_pos >= 1-eps/2):.2f}% of cited pairs")
    z = (cos_pos.mean() - geo["cos_unrelated_mean"]) / geo["cos_unrelated_sd"]
    print(f"  separation z = {z:.3f}  (related vs unrelated, in sd units)")

    same = papers[[i for i, _ in edges]] == papers[[j for _, j in edges]]
    print(f"  {100.0*same.mean():.1f}% of ref-edges are within-paper (expected ~100%)")

    print("\n[transforms] computing ...")
    mats = {
        "raw":        t_raw(X),
        "centered":   t_centered(X),
        f"abtt-{args.abtt_k}": t_abtt(X, args.abtt_k),
        "localscale": t_localscale(X),
        f"diffusion-t{args.diff_t:g}": t_diffusion(X, t=args.diff_t),
    }

    same_paper = papers[:, None] == papers[None, :]
    results = {"geometry": geo, "z_raw": float(z), "corpus": {}, "within": {}}

    print(f"\n=== CORPUS-WIDE RANKING ({len(blocks)-1} candidates per query) ===")
    hdr = f"{'transform':<16}" + "".join(f"{'r@'+str(k):>9}" for k in KS) + \
          f"{'median':>9}{'MRR':>8}"
    print(hdr); print("-" * len(hdr))
    for name, S in mats.items():
        r = rank_positives(S, edges)
        s = summarise(r, len(blocks) - 1)
        results["corpus"][name] = s
        print(f"{name:<16}" + "".join(f"{100*s['r@'+str(k)]:>8.1f}%" for k in KS) +
              f"{s['median_rank']:>9.0f}{s['mrr']:>8.3f}")

    print(f"\n=== WITHIN-PAPER RANKING (topic held fixed) ===")
    print(hdr); print("-" * len(hdr))
    ncand = float(np.mean([same_paper[i].sum() - 1 for i, _ in edges]))
    for name, S in mats.items():
        r = rank_positives(S, edges, restrict=same_paper)
        s = summarise(r, ncand)
        results["within"][name] = s
        print(f"{name:<16}" + "".join(f"{100*s['r@'+str(k)]:>8.1f}%" for k in KS) +
              f"{s['median_rank']:>9.0f}{s['mrr']:>8.3f}")
    print(f"(mean candidates per query: {ncand:.0f})")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2)
        print(f"\n[wrote] {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
