"""Ask the COVER question the cheap way: per concept, not per tick.

THE PROBLEM THIS ROUTES AROUND. Tier 0 asks "does this tick have one latent cause
or several?" Our ticks are top-k balls around a single query point, and a ball has
one centre -- so it is single-cause BY CONSTRUCTION and the answer was fixed by
the generator before any data was seen. That is the Modifiable Areal Unit Problem:
the measured pattern is an artifact of the aggregation unit (see
DOCS/PRIOR_ART_AND_THE_REPLAN.md 2 and 6).

THE ROUTE AROUND IT. A cover is a family of OVERLAPPING patches, and "overlapping"
means some element lies in two patches. That is a statement about ELEMENTS, not
about ticks:

    tick-side  : "did several causes fire together?"   <- broken by the grain
    concept-side: "does this concept belong to two contexts?"  <- the definition

For concept c, collect every tick it fired in. Each such tick is a ball centred
somewhere near c. If c is mono-topical those centres form one blob. If c genuinely
bridges two areas, queries from BOTH areas retrieve it and the centres split into
two groups. The multi-cause structure lives ACROSS ticks, not WITHIN one -- so the
broken single-centre ticks are perfectly adequate for this question.

THE SCORE. For each concept, 1-means vs 2-means on its tick centres:

    bimodality(c) = 1 - SSE_2 / SSE_1        in [0, 1], higher = more split
    separation(c) = ||m1 - m2|| / rms spread  effect size of that split

GROUND TRUTH, FREE. arXiv cross-listing: a paper filed under two of our six
categories is literally one concept claimed by two topics. So this is a LABELLED
detection problem, exactly the move that settled retrieval with 2266 \\ref labels.
Cross-listing is HIGH-PRECISION / LOW-RECALL -- a single-listed paper may still
bridge topics -- so AUC and recall are meaningful and "definitely not a bridge" is
not. Cross-listing is never shown to any model; it is only ever a label here.

CONTROLS, because a score that separates nothing still produces a number:
  * the geometric null (Gaussian matching the cloud's first two moments) must give
    AUC ~= 0.5. If it does not, the score is reading geometry, not semantics.
  * bimodality must not be a restatement of how OFTEN a concept fires -- hubs fire
    more, and more points make a 2-means split easier. Reported as a correlation.

    python measure_multicontext.py --corpus corpus/ --log assemblies_real.jsonl
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List, Optional, Tuple

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_assemblies import apply_abtt, fit_abtt                     # noqa: E402


def two_means(P: np.ndarray, rng: np.random.Generator,
              restarts: int = 5, iters: int = 25) -> Tuple[float, float]:
    """Best-of-restarts 2-means. Returns (SSE_2, ||m1 - m2||)."""
    best_sse, best_gap = np.inf, 0.0
    n = P.shape[0]
    for _ in range(restarts):
        c = P[rng.choice(n, size=2, replace=False)].copy()
        for _ in range(iters):
            d = ((P[:, None, :] - c[None, :, :]) ** 2).sum(axis=2)
            lab = d.argmin(axis=1)
            if lab.min() == lab.max():                 # degenerate split
                break
            new = np.stack([P[lab == 0].mean(axis=0), P[lab == 1].mean(axis=0)])
            if np.allclose(new, c):
                c = new
                break
            c = new
        d = ((P[:, None, :] - c[None, :, :]) ** 2).sum(axis=2)
        lab = d.argmin(axis=1)
        if lab.min() == lab.max():
            continue
        sse = float(d[np.arange(n), lab].sum())
        if sse < best_sse:
            best_sse = sse
            best_gap = float(np.linalg.norm(c[0] - c[1]))
    return best_sse, best_gap


def score_concepts(centres_by_concept: Dict[int, np.ndarray], min_ticks: int,
                   seed: int = 0, pca_dim: int = 0) -> Dict[int, Tuple[float, float, int]]:
    """`pca_dim > 0` projects each concept's tick centres onto their OWN top
    principal directions before clustering.

    WHY THIS IS NOT OPTIONAL, measured rather than argued. With ~67 points in
    384 dimensions, pairwise distances concentrate: every 2-means split scores
    about the same, so the statistic carries no information about whether a real
    split exists. The positive control quantified it -- planted clusters separated
    by up to 2 sd scored 0.0212 against a one-blob null of 0.0201, i.e. the
    instrument was blind at every realistic separation. Projecting onto the few
    directions along which THIS concept's neighbourhoods actually vary restores
    the power. Re-run `poscontrol.py` after changing this."""
    rng = np.random.default_rng(seed)
    out: Dict[int, Tuple[float, float, int]] = {}
    for ci, P in centres_by_concept.items():
        n = P.shape[0]
        if n < min_ticks:
            continue
        if pca_dim > 0:
            Pc = P - P.mean(axis=0, keepdims=True)
            r = int(min(pca_dim, n - 1, Pc.shape[1]))
            if r >= 1:
                _, _, Vt = np.linalg.svd(Pc, full_matrices=False)
                P = Pc @ Vt[:r].T
        mu = P.mean(axis=0)
        sse1 = float(((P - mu) ** 2).sum())
        if sse1 <= 0:
            continue
        sse2, gap = two_means(P, rng)
        if not np.isfinite(sse2):
            continue
        bim = 1.0 - sse2 / sse1
        sep = gap / np.sqrt(sse1 / n)
        out[ci] = (float(bim), float(sep), n)
    return out


def auc(scores: np.ndarray, labels: np.ndarray) -> float:
    """Rank-based AUC (Mann-Whitney), ties handled by average rank."""
    pos, neg = int(labels.sum()), int((~labels.astype(bool)).sum())
    if pos == 0 or neg == 0:
        return float("nan")
    order = np.argsort(scores)
    ranks = np.empty(len(scores), dtype=float)
    ranks[order] = np.arange(1, len(scores) + 1)
    # average ranks within tied groups
    s_sorted = scores[order]
    i = 0
    while i < len(s_sorted):
        j = i
        while j + 1 < len(s_sorted) and s_sorted[j + 1] == s_sorted[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = np.mean(ranks[order[i:j + 1]])
        i = j + 1
    return float((ranks[labels.astype(bool)].sum() - pos * (pos + 1) / 2.0)
                 / (pos * neg))


def load_run(corpus_dir: str, log_path: str, abtt_r: int,
             geometric: bool, seed: int) -> Tuple[Dict[int, np.ndarray], List[str]]:
    cd = np.load(os.path.join(corpus_dir, "concepts.npz"), allow_pickle=True)
    qd = np.load(os.path.join(corpus_dir, "queries.npz"), allow_pickle=True)
    names = [str(x) for x in cd["names"]]
    C, Q = cd["vectors"].astype(np.float64), qd["vectors"].astype(np.float64)

    if geometric:
        from make_assemblies import gaussian_surrogate
        rng = np.random.default_rng(seed)
        n_q = Q.shape[0]
        C = gaussian_surrogate(C, C.shape[0], rng)
        Q = gaussian_surrogate(C, n_q, rng)

    mu, P = fit_abtt(C, abtt_r)
    Qn = apply_abtt(Q, mu, P)

    index = {n: i for i, n in enumerate(names)}
    buckets: Dict[int, List[int]] = {}
    with open(log_path, encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            t = int(rec["tick"]) % Qn.shape[0]
            for nm in rec["retrieved"]:
                ci = index.get(nm)
                if ci is not None:
                    buckets.setdefault(ci, []).append(t)
    return {ci: Qn[np.asarray(ts)] for ci, ts in buckets.items()}, names


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--abtt", type=int, default=10)
    ap.add_argument("--min-ticks", type=int, default=8)
    ap.add_argument("--pca", type=int, default=2,
                    help="per-concept PCA before 2-means; 0 disables. See "
                         "score_concepts for why 0 is nearly blind.")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--tag", default="real")
    ap.add_argument("--geometric", action="store_true",
                    help="negative control: replace the cloud with a Gaussian "
                         "matching its first two moments")
    args = ap.parse_args()

    man = json.load(open(os.path.join(args.corpus, "corpus_manifest.json"),
                         encoding="utf-8"))
    ours = set(man["categories"])
    xlist = {p["id"]: len(set(p["categories"]) & ours) > 1 for p in man["papers"]}

    centres, names = load_run(args.corpus, args.log, args.abtt,
                              args.geometric, args.seed)
    scored = score_concepts(centres, args.min_ticks, seed=args.seed,
                            pca_dim=args.pca)
    if not scored:
        print("[multi] no concept met the min-ticks floor", file=sys.stderr)
        return 3

    ids = sorted(scored)
    bim = np.array([scored[i][0] for i in ids])
    sep = np.array([scored[i][1] for i in ids])
    nt = np.array([scored[i][2] for i in ids], dtype=float)
    lab = np.array([bool(xlist.get(names[i], False)) for i in ids])

    print(f"\n=== {args.tag}{' (GEOMETRIC NULL)' if args.geometric else ''} ===")
    print(f"  concepts scored          : {len(ids)} of {len(names)} "
          f"(>= {args.min_ticks} ticks)")
    print(f"  cross-listed (positives) : {int(lab.sum())} "
          f"({100.0*lab.mean():.1f}%)")
    print(f"  ticks per concept        : mean {nt.mean():.1f}, "
          f"median {np.median(nt):.0f}")
    for nm, s in (("bimodality", bim), ("separation", sep)):
        a = auc(s, lab)
        print(f"  {nm:<12} cross {s[lab].mean():.4f} vs single "
              f"{s[~lab].mean():.4f}   AUC {a:.4f}")
    print(f"  CONTROL corr(bimodality, n_ticks) = "
          f"{np.corrcoef(bim, nt)[0,1]:+.4f}   "
          f"(large |corr| => the score is reading firing frequency)")
    print(f"  CONTROL AUC of n_ticks alone      = {auc(nt, lab):.4f}   "
          f"(if this matches, the score adds nothing)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
