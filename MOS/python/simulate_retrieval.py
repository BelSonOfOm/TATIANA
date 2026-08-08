"""Simulate SearchOp's retrieval, faithfully, without the C++ engine.

WHY THIS EXISTS. accumulate.py drives the real engine (mos.exe) over stdin/
stdout IPC -- but that binary is compiled MSVC/Windows (`#include <Windows.h>`
unconditionally in main.cpp, colibri_kernel.cpp, primitives.cpp), so it cannot
run on Colab's Linux VM. Rather than approximate retrieval, this reproduces the
EXACT rule the engine uses, verified against the actual C++ source rather than
assumed:

    SearchOp::apply            (src/operators/primitives.cpp:49-60)
        D1 = ||q||_2                         (derived_variance, NOT squared)
        eps = max(0.1, 1/dim)                (relevance_threshold)

    KnowledgeBase::get_relevant_concepts     (src/translation/knowledge_base.cpp)
        keep concept c iff  W2^2(q, c) <= eps

    wasserstein_2_terms                       (src/core/semantic_skill.cpp:234-278)
        semantic  = ||mu1 - mu2||^2
        epistemic = d*D1 + d*D2 - 2*sqrt(D1)*trace_Sigma2_sqrt

    For a RANK-0 concept (k=0, which is every concept ingest_corpus.py writes --
    a chunk seen once has zero scatter about its own mean, per FIX-13):
        trace_Sigma2_sqrt = d*sqrt(D2)
        epistemic = d*D1 + d*D2 - 2*sqrt(D1)*d*sqrt(D2) = d*(sqrt(D1)-sqrt(D2))^2

    This is an algebraic identity, not an approximation -- confirmed by hand
    against the C++ so this script and the engine can never silently diverge on
    the one thing that decides every retrieval.

WHAT THIS DOES NOT MODEL, STATED RATHER THAN HIDDEN. SearchOp also calls
grow_concept every tick (neurogenesis), but growth writes to CognitiveState's
math_complex_, NOT to the KnowledgeBase -- commit_concept is a separate,
un-triggered call. So the KB a SEARCH-only run retrieves against is STATIC for
the whole run, and this simulation is exact for every tick, not just the first.
`grown` is emitted as an empty list per tick for schema compatibility; Tier 0
never reads it.

    python simulate_retrieval.py --concepts concepts.npz --queries queries.npz \
        --out assembly_events.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

import numpy as np


def retrieval_sets(query_vectors: np.ndarray, concept_vectors: np.ndarray,
                   concept_names: List[str], epsilon: float,
                   concept_D: Optional[np.ndarray] = None) -> List[List[str]]:
    """The exact rule, vectorised. One row of output per query.

    concept_D defaults to 1.0 per concept, matching ingest_corpus.py's default
    --noise-floor (chosen there to match SearchOp's own D1 for unit embeddings,
    so the epistemic term vanishes and relevance is decided by the means).
    """
    dim = query_vectors.shape[1]
    if concept_vectors.shape[1] != dim:
        raise ValueError(
            f"query dim {dim} != concept dim {concept_vectors.shape[1]}")
    D2 = (np.ones(concept_vectors.shape[0]) if concept_D is None
          else np.asarray(concept_D, dtype=float))

    D1 = np.linalg.norm(query_vectors, axis=1)              # SearchOp's derived_variance

    # semantic[t,c] = ||q_t - m_c||^2, via the expansion so the full T x N x d
    # tensor of differences never materialises.
    q2 = np.sum(query_vectors ** 2, axis=1)[:, None]
    c2 = np.sum(concept_vectors ** 2, axis=1)[None, :]
    cross = query_vectors @ concept_vectors.T
    semantic = np.maximum(q2 + c2 - 2.0 * cross, 0.0)

    # epistemic[t,c] = dim*(sqrt(D1_t) - sqrt(D2_c))^2, the rank-0 identity above.
    sq1 = np.sqrt(D1)[:, None]
    sq2 = np.sqrt(D2)[None, :]
    epistemic = dim * (sq1 - sq2) ** 2

    total = semantic + epistemic
    keep = total <= epsilon

    names = np.asarray(concept_names, dtype=object)
    return [names[keep[t]].tolist() for t in range(query_vectors.shape[0])]


def report(sizes: np.ndarray) -> None:
    print(f"[simulate] ticks               : {len(sizes)}")
    print(f"[simulate] mean concepts/tick   : {sizes.mean():.2f} "
          f"(median {np.median(sizes):.0f}, max {int(sizes.max())})")
    print(f"[simulate] ticks with >=2       : {int((sizes >= 2).sum())} "
          f"({100.0*(sizes >= 2).mean():.1f}%)")
    print(f"[simulate] ticks with 0         : {int((sizes == 0).sum())} "
          f"({100.0*(sizes == 0).mean():.1f}%)")
    if (sizes >= 2).mean() < 0.2:
        print("[simulate] WARNING: fewer than 20% of ticks retrieve a pair. "
              "Tier 0 will refuse to fit on this -- widen epsilon or the corpus "
              "before spending time on run_tier0.py.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--concepts", required=True, help="concepts.npz (names, vectors)")
    ap.add_argument("--queries", required=True, help="queries.npz (texts, vectors)")
    ap.add_argument("--out", default="assembly_events.jsonl")
    ap.add_argument("--epsilon", type=float, default=None,
                    help="default: the engine's own max(0.1, 1/dim)")
    ap.add_argument("--concept-D", type=float, default=1.0,
                    help="must match --noise-floor used at ingest time")
    ap.add_argument("--ticks", type=int, default=0, help="0 = one tick per query")
    args = ap.parse_args()

    cdata = np.load(args.concepts, allow_pickle=True)
    qdata = np.load(args.queries, allow_pickle=True)
    names = [str(n) for n in cdata["names"]]
    CV = cdata["vectors"].astype(np.float64)
    QV = qdata["vectors"].astype(np.float64)
    dim = CV.shape[1]

    eps = args.epsilon if args.epsilon is not None else max(0.1, 1.0 / dim)
    print(f"[simulate] concepts: {len(names)} at {dim}-d")
    print(f"[simulate] queries : {QV.shape[0]}")
    print(f"[simulate] epsilon : {eps:.4f}"
          + ("  (engine default)" if args.epsilon is None else "  (override)"))

    n_ticks = args.ticks or QV.shape[0]
    if n_ticks > QV.shape[0]:
        reps = -(-n_ticks // QV.shape[0])
        print(f"[simulate] WARNING: {QV.shape[0]} distinct queries for {n_ticks} "
              f"ticks -- each repeats ~{reps}x. Repeated queries retrieve "
              "identical sets, inflating apparent co-activation.")
    idx = np.arange(n_ticks) % QV.shape[0]
    Q = QV[idx]

    concept_D = np.full(len(names), args.concept_D)
    sets = retrieval_sets(Q, CV, names, eps, concept_D=concept_D)
    sizes = np.array([len(s) for s in sets])
    report(sizes)

    with open(args.out, "w", encoding="utf-8") as fh:
        for t, retrieved in enumerate(sets):
            # Minimal but VALID: run_tier0.load_assemblies reads only "retrieved"
            # and "grown" per line. grown is always empty -- see module docstring
            # for why that is exact, not a shortcut.
            fh.write(json.dumps({"tick": t, "retrieved": retrieved, "grown": []}) + "\n")
    print(f"[simulate] wrote {n_ticks} ticks -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
