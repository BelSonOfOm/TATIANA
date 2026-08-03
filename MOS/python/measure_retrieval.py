"""How many concepts does a query actually retrieve, at what threshold?

RUN THIS BEFORE ACCUMULATING. Construction 5 explains CO-ACTIVATION, so it needs
ticks that retrieve two or more concepts. If the engine's relevance threshold
admits only near-duplicates, almost every tick retrieves exactly one and the
whole accumulation produces a matrix with no pairs in it -- 25 minutes of CPU
for a file that cannot answer the question.

WHAT THE ENGINE ACTUALLY USES. SearchOp sets

    derived_variance    = ||q||                     (= 1, embeddings are unit)
    relevance_threshold = max(0.1, 1/dim)           (= 0.1 for any dim > 10)

and KnowledgeBase keeps a concept when the SQUARED Bures-Wasserstein distance is
<= that threshold. With D_query = D_concept = 1 the epistemic term vanishes and
the criterion is ||q - c||^2 <= 0.1, i.e. cos >= 0.95 -- a near-duplicate filter.
This script measures what that costs on the real corpus, and what a range of
thresholds would give instead, so any change to the threshold is a calibration
against measured retrieval sizes rather than a number someone liked.
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

DEFAULT_DB = os.path.join(os.path.dirname(HERE), "mos_brain.db")


def load_concepts(db: str, dim: int):
    con = sqlite3.connect(db)
    names, mus, Ds = [], [], []
    for name, d, blob, D in con.execute(
            "SELECT reasoning_chain, dimension, mu_vector, noise_floor "
            "FROM distilled_theorems"):
        if d != dim or blob is None or len(blob) != dim * 8:
            continue
        names.append(name)
        mus.append(struct.unpack(f"<{dim}d", blob))
        Ds.append(D)
    con.close()
    return names, np.array(mus), np.array(Ds)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--tasks", default=os.path.join(HERE, "tasks.txt"))
    ap.add_argument("--sample", type=int, default=300)
    args = ap.parse_args()

    from embeddings import embed_batch, EMBED_DIM

    names, MU, D = load_concepts(args.db, EMBED_DIM)
    if len(names) == 0:
        print(f"[retrieval] no {EMBED_DIM}-d concepts in {args.db}", file=sys.stderr)
        return 2
    print(f"[retrieval] concepts: {len(names)}, stored D in "
          f"[{D.min():.3f}, {D.max():.3f}]")

    tasks = [ln.strip() for ln in open(args.tasks, encoding="utf-8")
             if ln.strip() and not ln.startswith("#")]
    rng = np.random.default_rng(0)
    sample = [tasks[i] for i in rng.choice(len(tasks),
                                           size=min(args.sample, len(tasks)),
                                           replace=False)]
    print(f"[retrieval] embedding {len(sample)} sampled queries...")
    Q = np.array(embed_batch(sample))

    # ||q - c||^2 for every (query, concept), via the expansion so the 300x1126
    # matrix never materialises as differences.
    d2 = (np.sum(Q**2, axis=1)[:, None] + np.sum(MU**2, axis=1)[None, :]
          - 2.0 * Q @ MU.T)
    np.maximum(d2, 0.0, out=d2)

    # The epistemic term the engine adds, with D_query = ||q|| = 1.
    epi = EMBED_DIM * (1.0 - np.sqrt(D)) ** 2
    total = d2 + epi[None, :]

    print(f"\n{'epsilon':>9} {'mean size':>10} {'median':>7} {'%>=2 ticks':>11} "
          f"{'%==0':>6}")
    print("-" * 48)
    rows = []
    for eps in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0):
        sizes = (total <= eps).sum(axis=1)
        rows.append((eps, sizes))
        marker = "   <- engine default" if abs(eps - 0.1) < 1e-9 else ""
        print(f"{eps:>9.2f} {sizes.mean():>10.2f} {np.median(sizes):>7.0f} "
              f"{100.0*(sizes >= 2).mean():>10.1f}% {100.0*(sizes == 0).mean():>5.1f}%"
              f"{marker}")

    eps0 = rows[0][1]
    print(f"\n[retrieval] at the engine default, {100.0*(eps0 >= 2).mean():.1f}% of "
          f"ticks would yield a co-activation PAIR.")
    if (eps0 >= 2).mean() < 0.2:
        print("[retrieval] That is too sparse for Construction 5. The threshold, "
              "not the corpus, is the binding constraint:")
        print("[retrieval] eps=0.1 on SQUARED distance means cos >= 0.95, which "
              "admits near-duplicates only.")
        good = [(e, s) for e, s in rows if 3.0 <= s.mean() <= 12.0]
        if good:
            e, s = good[0]
            print(f"[retrieval] eps={e:.2f} gives mean {s.mean():.1f} concepts/tick "
                  f"({100.0*(s >= 2).mean():.0f}% with a pair) -- a relevance "
                  "filter rather than a duplicate filter.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
