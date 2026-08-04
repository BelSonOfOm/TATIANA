"""T1 with the bootstrap null spread across processes.

WHY. `calibrated_compare` costs B * n_folds * 2 EM fits. Measured on this machine
(3000 x 1115, K=6): ~24 s per noisy-OR fit, ~15 s per mixture fit => B=49 takes
~165 min SERIAL. The EM is NOT BLAS-bound (36.7 s at OMP=1 vs 31.0 s at OMP=4,
an 18% gain for 4x the threads), so it does not parallelise inside a fit -- but
the B null draws are independent, so they parallelise across processes almost
linearly. Workers are pinned to one thread each to stop them fighting.

WHAT IS AND IS NOT IDENTICAL TO THE SERIAL PATH. Draw b is seeded independently
(`seed + 104729 + b`) rather than consuming one shared RNG stream in order. The
null SAMPLE therefore differs from the serial version's -- it is an equally valid
draw from the same null distribution, not a reproduction of the same draw. The
observed statistic, the folds, and the fitted generators are computed identically.

    python tier0_parallel.py --log assembly_events.jsonl --K 6 --B 49 \
        --match-margins --jobs 4
"""
from __future__ import annotations

import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import argparse
import json
import multiprocessing as mp
import sys
import time
from collections import Counter
from typing import Dict, List

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cover import (CalibratedComparison, assemblies_to_matrix, block_split,   # noqa: E402
                   fit_mixture, fit_noisy_or, _as_mask,
                   _simulate_mixture, _simulate_mixture_margin)
from run_tier0 import load_assemblies                                          # noqa: E402

_G: Dict = {}


def _init(X, M, K, gens, match_margins, seed):
    _G.update(X=X, M=M, K=K, gens=gens, match_margins=match_margins, seed=seed)


def _draw(b: int) -> float:
    X, M, K = _G["X"], _G["M"], _G["K"]
    rng = np.random.default_rng(_G["seed"] + 104729 + b)
    nor_tot = mix_tot = 0.0
    n = 0
    for gen, train, test in _G["gens"]:
        Mtr, Mte = M[train], M[test]
        if _G["match_margins"]:
            Xtr = _simulate_mixture_margin(gen, len(train), rng,
                                           X[train].sum(axis=1), Mtr)
            Xte = _simulate_mixture_margin(gen, len(test), rng,
                                           X[test].sum(axis=1), Mte)
        else:
            Xtr = _simulate_mixture(gen, len(train), rng, Mtr)
            Xte = _simulate_mixture(gen, len(test), rng, Mte)
        nor_tot += fit_noisy_or(Xtr, K, seed=_G["seed"], mask=Mtr).loglik(Xte, Mte)
        mix_tot += fit_mixture(Xtr, K, seed=_G["seed"], mask=Mtr).loglik(Xte, Mte)
        n += len(test)
    return (nor_tot - mix_tot) / n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log", required=True)
    ap.add_argument("--K", type=int, default=6)
    ap.add_argument("--B", type=int, default=49)
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--min-concepts", type=int, default=2)
    ap.add_argument("--jobs", type=int, default=max(1, mp.cpu_count() // 2))
    ap.add_argument("--match-margins", action="store_true",
                    help="REQUIRED under top-k retrieval; see cover."
                         "_simulate_mixture_margin")
    ap.add_argument("--tag", default="run")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    rows, births = load_assemblies(args.log)
    counts = Counter(c for r in rows for c in r)
    keep = sorted(c for c, n in counts.items() if n >= args.min_concepts)
    index = {c: i for i, c in enumerate(keep)}
    idx_rows = [[index[c] for c in r if c in index] for r in rows]
    idx_rows = [r for r in idx_rows if r]
    X = assemblies_to_matrix(idx_rows, len(keep))
    T, N = X.shape
    sizes = X.sum(axis=1)
    print(f"[{args.tag}] matrix {T} x {N}, density {X.mean():.4f}")
    print(f"[{args.tag}] row sizes: mean {sizes.mean():.1f}, sd {sizes.std():.2f}, "
          f"min {sizes.min():.0f}, max {sizes.max():.0f}")
    print(f"[{args.tag}] null: {'MARGIN-MATCHED' if args.match_margins else 'legacy Bernoulli'}")
    if sizes.std() < 1e-9 and not args.match_margins:
        print(f"[{args.tag}] *** WARNING: every row has exactly {sizes[0]:.0f} ones, "
              "but the legacy null emits Binomial row sums. The margin is then "
              "contaminated by the retrieval rule. Use --match-margins.")

    M = _as_mask(None, X)
    folds = block_split(T, args.folds)
    if not folds:
        print("[tier0] STOP: too few ticks to form held-out blocks.", file=sys.stderr)
        return 3

    t0 = time.time()
    nor_tot = mix_tot = 0.0
    n_test = 0
    gens = []
    for train, test in folds:
        Xtr, Mtr = X[train], M[train]
        nor = fit_noisy_or(Xtr, args.K, seed=args.seed, mask=Mtr)
        mix = fit_mixture(Xtr, args.K, seed=args.seed, mask=Mtr)
        nor_tot += nor.loglik(X[test], M[test])
        mix_tot += mix.loglik(X[test], M[test])
        n_test += len(test)
        gens.append((mix, train, test))
    observed = (nor_tot - mix_tot) / n_test
    print(f"[{args.tag}] observed margin {observed:+.4f} nats/tick "
          f"({time.time()-t0:.0f}s for the fold fits)")

    t1 = time.time()
    print(f"[{args.tag}] {args.B} null draws across {args.jobs} processes ...")
    with mp.Pool(args.jobs, initializer=_init,
                 initargs=(X, M, args.K, gens, args.match_margins, args.seed)) as pool:
        null = np.array(pool.map(_draw, range(args.B)))
    print(f"[{args.tag}] null done in {(time.time()-t1)/60:.1f} min")

    res = CalibratedComparison(observed=observed, null=null, K=args.K,
                               n_folds=len(folds), alpha=args.alpha)
    print(f"\n[{args.tag}] observed        : {observed:+.4f}")
    print(f"[{args.tag}] null median     : {np.median(null):+.4f} "
          f"[{null.min():+.4f}, {null.max():+.4f}] over {len(null)} draws")
    print(f"[{args.tag}] excess over null: {res.excess_over_null:+.4f}")
    print(f"[{args.tag}] p               : {res.p_value:.4f}")
    print(f"[{args.tag}] VERDICT: {res.verdict()}")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump({"tag": args.tag, "T": int(T), "N": int(N), "K": args.K,
                       "B": args.B, "match_margins": bool(args.match_margins),
                       "row_size_mean": float(sizes.mean()),
                       "row_size_sd": float(sizes.std()),
                       "observed": float(observed), "null": null.tolist(),
                       "p_value": float(res.p_value),
                       "excess_over_null": float(res.excess_over_null),
                       "favours_cover": bool(res.favours_cover)}, fh, indent=2)
        print(f"[{args.tag}] wrote {args.out}")
    return 0


if __name__ == "__main__":
    mp.freeze_support()
    raise SystemExit(main())
