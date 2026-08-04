"""Phase B against SEMANTIC labels instead of administrative ones.

WHY REDO IT. Phase B on the arXiv corpus scored AUC 0.514-0.550 against
cross-listing -- inside the noise floor (the geometric null scored 0.523-0.529 on
labels that are meaningless by construction). The most likely reason is the LABEL:
arXiv cross-listing is an administrative filing act, not a claim that the work
bridges two areas. The \\ref labels worked for retrieval precisely because they are
semantic -- an author writing "by Lemma 3.2" asserts a real dependency.

THE BRIDGING LABEL, AND WHY IT IS NOT CIRCULAR. A block cited from two DISTANT
parts of a paper serves two parts of the argument -- a lemma used in section 2 and
again in section 9 is doing double duty. So:

    citer_span(v) = (max_pos(citers) - min_pos(citers)) / doclen      in [0, 1]

This is computed from CHARACTER OFFSETS in the LaTeX source. It never touches the
embeddings, so it cannot be circular with the bimodality score it is used to
validate. That was the trap to avoid: labelling "bridges two contexts" using the
same geometry that the score reads.

THE TICKS. Every block is used as a query and retrieves its top-k neighbours, so
each tick is a neighbourhood centred on one block -- the same single-centre ball
as before. That is FINE here: the concept-side question asks whether a block's
neighbourhoods split ACROSS ticks, which single-centre ticks can express (see
DOCS/PRIOR_ART_AND_THE_REPLAN.md 6).

CONTROLS. (1) geometric null -- Gaussian matching the cloud's first two moments,
same labels, must give AUC ~= 0.5. (2) in-degree alone, since a block with more
citers has more ticks and an easier 2-means split.

    python measure_multicontext_refs.py --refs refs_corpus.json --top-k 24
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_assemblies import apply_abtt, fit_abtt, gaussian_surrogate    # noqa: E402
from measure_multicontext import auc, score_concepts                    # noqa: E402


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    ra = np.argsort(np.argsort(a)).astype(float)
    rb = np.argsort(np.argsort(b)).astype(float)
    return float(np.corrcoef(ra, rb)[0, 1])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--refs", required=True)
    ap.add_argument("--vecs", default=None)
    ap.add_argument("--top-k", type=int, default=24)
    ap.add_argument("--abtt", type=int, default=10)
    ap.add_argument("--pca", type=int, default=2)
    ap.add_argument("--min-ticks", type=int, default=8)
    ap.add_argument("--min-citers", type=int, default=2)
    ap.add_argument("--span-threshold", type=float, default=0.30)
    ap.add_argument("--normalize-span", action="store_true",
                    help="divide the citer span by (n-1)/(n+1), removing the "
                         "mechanical growth of range with in-degree")
    ap.add_argument("--geometric", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    data = json.load(open(args.refs, encoding="utf-8"))
    blocks, edges = data["blocks"], data["edges"]
    index = {b["id"]: i for i, b in enumerate(blocks)}
    vecs = args.vecs or os.path.splitext(args.refs)[0] + "_vecs.npz"
    X = np.load(vecs)["vectors"].astype(np.float64)
    if X.shape[0] != len(blocks):
        print(f"[refsB] vector cache is stale ({X.shape[0]} vs {len(blocks)})",
              file=sys.stderr)
        return 2

    rng = np.random.default_rng(args.seed)
    if args.geometric:
        X = gaussian_surrogate(X, X.shape[0], rng)

    mu, P = fit_abtt(X, args.abtt)
    Xn = apply_abtt(X, mu, P)

    # ---- ticks: every block queries, and retrieves its top-k neighbours -------
    k = int(min(args.top_k, Xn.shape[0]))
    centres: Dict[int, List[int]] = {}
    for lo in range(0, Xn.shape[0], 512):
        hi = min(lo + 512, Xn.shape[0])
        S = Xn[lo:hi] @ Xn.T
        for r in range(hi - lo):
            S[r, lo + r] = -np.inf                       # never retrieve self
        top = np.argpartition(-S, k - 1, axis=1)[:, :k]
        for r in range(hi - lo):
            for c in top[r]:
                centres.setdefault(int(c), []).append(lo + r)
    centres_v = {ci: Xn[np.asarray(ts)] for ci, ts in centres.items()}

    # ---- the structural bridging label ---------------------------------------
    citers: Dict[int, List[int]] = {}
    for e in edges:
        d, s = index.get(e["dst"]), e.get("src_pos")
        if d is not None and s is not None:
            citers.setdefault(d, []).append(int(s))

    span: Dict[int, float] = {}
    for bi, ps in citers.items():
        n = len(ps)
        if n < args.min_citers:
            continue
        dl = max(int(blocks[bi].get("doclen", 0)), 1)
        raw = (max(ps) - min(ps)) / dl
        if args.normalize_span:
            # THE RAW SPAN IS CONFOUNDED WITH IN-DEGREE, measured not guessed:
            # in-degree alone predicts the raw label at AUC 0.748, because the
            # range of n points grows with n whether or not anything bridges.
            # For n uniform points on [0,1] the expected range is (n-1)/(n+1),
            # so dividing by it removes the mechanical part and leaves "wider
            # than this many citers would give by chance".
            raw = raw / ((n - 1.0) / (n + 1.0))
        span[bi] = raw

    scored = score_concepts(centres_v, args.min_ticks, seed=args.seed,
                            pca_dim=args.pca)
    ids = sorted(set(scored) & set(span))
    if len(ids) < 30:
        print(f"[refsB] only {len(ids)} blocks have both a score and >= "
              f"{args.min_citers} citers -- too few", file=sys.stderr)
        return 3

    bim = np.array([scored[i][0] for i in ids])
    sep = np.array([scored[i][1] for i in ids])
    nt = np.array([scored[i][2] for i in ids], dtype=float)
    sp = np.array([span[i] for i in ids])
    nc = np.array([len(citers[i]) for i in ids], dtype=float)
    lab = sp >= args.span_threshold

    tag = "REF-LABEL" + (" (GEOMETRIC NULL)" if args.geometric else "")
    print(f"\n=== {tag}  k={args.top_k} pca={args.pca} ===")
    print(f"  blocks scored & labelled : {len(ids)}")
    print(f"  citers per block         : mean {nc.mean():.1f}, max {nc.max():.0f}")
    print(f"  citer_span               : median {np.median(sp):.3f}, "
          f"mean {sp.mean():.3f}")
    print(f"  positives (span >= {args.span_threshold:.2f})  : {int(lab.sum())} "
          f"({100.0*lab.mean():.1f}%)")
    for nm, s in (("bimodality", bim), ("separation", sep)):
        print(f"  {nm:<11} bridge {s[lab].mean():.4f} vs local "
              f"{s[~lab].mean():.4f}   AUC {auc(s, lab):.4f}   "
              f"spearman(vs span) {spearman(s, sp):+.4f}")
    print(f"  CONTROL AUC of in-degree alone   = {auc(nc, lab):.4f}")
    print(f"  CONTROL AUC of n_ticks alone     = {auc(nt, lab):.4f}")
    print(f"  CONTROL corr(bimodality, n_ticks)= {np.corrcoef(bim, nt)[0,1]:+.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
