"""TIER 0, ATTEMPT 4: the transitivity deficit, calibrated before it is interpreted.

THE HYPOTHESIS, STATED OPERATIONALLY (not topologically).
  partition: every concept has essentially one home.
  cover:     some concepts genuinely belong to several overlapping contexts, and
             those overlaps are NECESSARY to explain the observed co-activations.

THE SIGNATURE. At the LATENT level a partition forces transitivity: if A and B
share a group and B and C share a group, then A and C do. A cover does not.

⚠️ BUT AN OPEN TRIANGLE IS NOT EVIDENCE OF A COVER. Co-activation is SAMPLED. If
A, B and C all sit in one latent patch you may observe A-B and B-C and simply
never happen to observe A-C. That is an open triangle produced by sampling, with
perfectly transitive latent structure underneath. The claim is therefore only ever:

    EXCESS open triangles relative to an appropriate null
      => the transitivity deficit cannot be explained by sampling and degree
         constraints alone.

That is why the null carries the argument. `curveball_randomize` holds BOTH
margins exactly -- tick widths and concept frequencies -- so anything it cannot
reproduce is not a sampling or degree effect. (Ecology's fixed-margin models are
the ones documented not to inflate Type I error; PRIOR_ART_AND_THE_REPLAN 1.)

WHY THIS BEATS ATTEMPTS 1-3:
  * LOCAL. Scored per concept, so a ~10% minority of bridging concepts is not
    averaged into a 90% majority. Dilution killed the global likelihood margin.
  * MATCHED. Reads the co-activation graph directly -- the same object the cover
    model is about -- instead of a geometric or citation proxy. The proxy
    mismatch killed attempt 3.
  * CALIBRATED BEFORE INTERPRETED. Synthetic partition, synthetic cover and
    geometric balls are run FIRST, and the statistic must order them correctly
    before the corpus is touched at all.

⚠️ WHAT IT DOES NOT ESCAPE. The retrieval protocol still decides which cliques
exist in the first place, so it remains part of the data-generating process. This
statistic probes the CONSISTENCY OF NEIGHBOURHOODS ACROSS retrieval events rather
than the geometry WITHIN one -- less entangled with retrieval than attempts 1-3,
not independent of it.

    python measure_open_triangles.py --synthetic cover        # control
    python measure_open_triangles.py --log assemblies_real.jsonl
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Dict, List, Optional, Tuple

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cover import curveball_randomize                                  # noqa: E402


# ----------------------------------------------------------- the statistic ---

def open_rate(M: np.ndarray, min_weight: int = 1, top_m: int = 0) -> Tuple[np.ndarray, np.ndarray, float]:
    """Per-concept fraction of neighbour PAIRS that are NOT themselves adjacent.

    `open_rate = 1 - local clustering coefficient`. Concepts with < 2 neighbours
    are undefined and returned as NaN rather than silently zero.
    Returns (open_rate, degree, graph_density).
    """
    W = M.T @ M                                   # co-activation counts
    np.fill_diagonal(W, 0)
    if top_m and top_m > 0:
        # DEGREE-CONTROLLED edge selection. `min_weight` thresholds on absolute
        # co-activation count, which is a FREQUENCY filter -- and bridging
        # concepts appear in more ticks, so their edges survive it
        # preferentially. Measured: at min_weight>=3 the synthetic-cover control
        # INVERTS (planted bridges score -1.8 to -7.1 sd on the wrong side).
        # Keeping each concept's top-m strongest partners instead makes degree
        # nearly constant, so frequency cannot drive the statistic.
        idx = np.argsort(-W, axis=1)[:, :int(top_m)]
        A = np.zeros_like(W, dtype=np.float64)
        np.put_along_axis(A, idx, 1.0, axis=1)
        A = A * (np.take_along_axis(W, idx, axis=1).min(axis=1, keepdims=True) >= 0)
        A = np.maximum(A, A.T)                    # symmetrise by union
        A[W == 0] = 0.0                           # never invent an unseen pair
    else:
        A = (W >= min_weight).astype(np.float64)

    deg = A.sum(axis=1)
    pairs = deg * (deg - 1.0) / 2.0
    # triangles at b = (A^3)_bb / 2, computed without forming A^3
    tri = ((A @ A) * A).sum(axis=1) / 2.0

    out = np.full(A.shape[0], np.nan)
    ok = pairs > 0
    out[ok] = 1.0 - tri[ok] / pairs[ok]
    n = A.shape[0]
    density = float(A.sum() / (n * (n - 1))) if n > 1 else 0.0
    return out, deg, density


def null_distribution(M: np.ndarray, B: int, min_weight: int, seed: int, top_m: int = 0,
                      verbose: bool = True) -> Tuple[np.ndarray, np.ndarray]:
    """Per-concept mean and sd of open_rate under the fixed-margin ensemble."""
    rng = np.random.default_rng(seed)
    acc: List[np.ndarray] = []
    t0 = time.time()
    for b in range(B):
        Mb = curveball_randomize(M, rng=rng)
        r, _, _ = open_rate(Mb, min_weight, top_m)
        acc.append(r)
        if verbose and (b + 1) % 10 == 0:
            el = time.time() - t0
            print(f"\r    null {b+1}/{B}  ({el:.0f}s, eta {el/(b+1)*(B-b-1):.0f}s)",
                  end="", flush=True)
    if verbose:
        print()
    Z = np.vstack(acc)
    return np.nanmean(Z, axis=0), np.nanstd(Z, axis=0)


# ------------------------------------------------------------- synthetic -----

def synth(kind: str, n_concepts: int, n_ticks: int, k: int, K: int,
          n_bridge: int, rng: np.random.Generator) -> Tuple[np.ndarray, np.ndarray]:
    """Ground-truth generators. Returns (incidence M, is_bridge mask)."""
    groups = np.array_split(np.arange(n_concepts), K)
    members = [list(g) for g in groups]
    bridge = np.zeros(n_concepts, dtype=bool)

    if kind == "cover":
        # designated concepts join a SECOND group -- the only difference from
        # the partition generator, so any contrast is attributable to overlap.
        picks = rng.choice(n_concepts, size=n_bridge, replace=False)
        for c in picks:
            home = next(i for i, m in enumerate(members) if c in m)
            other = (home + 1 + int(rng.integers(K - 1))) % K
            members[other].append(int(c))
            bridge[c] = True

    M = np.zeros((n_ticks, n_concepts))
    for t in range(n_ticks):
        g = int(rng.integers(K))
        pool = members[g]
        take = min(k, len(pool))
        M[t, rng.choice(pool, size=take, replace=False)] = 1.0
    return M, bridge


def load_log(path: str) -> Tuple[np.ndarray, List[str]]:
    rows, names, index = [], [], {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            r = []
            for nm in rec["retrieved"]:
                if nm not in index:
                    index[nm] = len(names)
                    names.append(nm)
                r.append(index[nm])
            rows.append(r)
    M = np.zeros((len(rows), len(names)))
    for t, r in enumerate(rows):
        M[t, r] = 1.0
    return M, names


# ------------------------------------------------------------------ report ---

def report(tag: str, M: np.ndarray, B: int, min_weight: int, seed: int, top_m: int = 0,
           bridge: Optional[np.ndarray] = None) -> Dict:
    obs, deg, dens = open_rate(M, min_weight, top_m)
    print(f"\n=== {tag} ===")
    print(f"  matrix {M.shape[0]} x {M.shape[1]}, tick width "
          f"{M.sum(axis=1).mean():.1f}, graph density {dens:.4f}")
    if dens > 0.95:
        print("  WARNING: graph is near-complete: clustering saturates and the "
              "statistic cannot discriminate. Raise --min-weight.")
    mu, sd = null_distribution(M, B, min_weight, seed, top_m)
    z = np.full_like(obs, np.nan)
    ok = np.isfinite(obs) & np.isfinite(mu) & (sd > 1e-12)
    z[ok] = (obs[ok] - mu[ok]) / sd[ok]
    zf = z[np.isfinite(z)]
    print(f"  open_rate observed {np.nanmean(obs):.4f}  null {np.nanmean(mu):.4f}")
    print(f"  z: mean {zf.mean():+.3f}  median {np.median(zf):+.3f}  "
          f"sd {zf.std():.3f}  max {zf.max():+.3f}")
    print(f"  tail: z>+2 {int((zf > 2).sum())} ({100*(zf>2).mean():.1f}%)   "
          f"z>+3 {int((zf > 3).sum())} ({100*(zf>3).mean():.1f}%)")
    out = {"tag": tag, "density": dens, "z_mean": float(zf.mean()),
           "z_sd": float(zf.std()), "frac_z_gt2": float((zf > 2).mean())}
    if bridge is not None:
        bz, nz = z[bridge & ok], z[(~bridge) & ok]
        if bz.size and nz.size:
            print(f"  >> bridge z {bz.mean():+.3f} (n={bz.size})  vs  "
                  f"non-bridge {nz.mean():+.3f} (n={nz.size})   "
                  f"separation {(bz.mean()-nz.mean())/max(nz.std(),1e-9):+.2f} sd")
            out["bridge_gap_sd"] = float((bz.mean() - nz.mean()) / max(nz.std(), 1e-9))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log", default=None)
    ap.add_argument("--synthetic", choices=["partition", "cover"], default=None)
    ap.add_argument("--B", type=int, default=49)
    ap.add_argument("--min-weight", type=int, default=1)
    ap.add_argument("--top-m", type=int, default=0,
                    help="degree-controlled edge selection; overrides --min-weight")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--concepts", type=int, default=1074)
    ap.add_argument("--ticks", type=int, default=3000)
    ap.add_argument("--k", type=int, default=24)
    ap.add_argument("--K", type=int, default=6)
    ap.add_argument("--bridges", type=int, default=60)
    ap.add_argument("--tag", default=None)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    if args.synthetic:
        M, bridge = synth(args.synthetic, args.concepts, args.ticks, args.k,
                          args.K, args.bridges, rng)
        tag = args.tag or f"SYNTHETIC {args.synthetic.upper()}"
        if args.synthetic == "partition":
            bridge = None
    elif args.log:
        M, _ = load_log(args.log)
        bridge, tag = None, args.tag or os.path.basename(args.log)
    else:
        print("need --log or --synthetic", file=sys.stderr)
        return 2

    report(f"{tag}  (min_weight={args.min_weight}, B={args.B})",
           M, args.B, args.min_weight, args.seed, args.top_m, bridge)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
