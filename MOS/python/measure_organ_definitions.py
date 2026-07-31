"""
V6b — DOES THE ORGAN DEFINITION FIX sigma_dir/delta? Measured, as a BOUND.

THE QUESTION
------------
V6 (logbook 5ah) measured sigma_dir/delta ~= 0.32 with organs = DOCUMENTS, an
organ definition I invented for that experiment and which Charbel correctly
rejected as not being architecture. pi_v v2 (5aj) then ruled out multi-modality
as the cause (prevalence 1/11). So the remaining candidate explanation is the
ORGAN DEFINITION itself -- option (c).

THE CIRCULARITY, AND WHY WE EXPLOIT IT DELIBERATELY
---------------------------------------------------
Construction 4 records the trap: if organs are defined by MINIMISING
within-organ spread, and we then measure within-organ spread (sigma_dir) on
those organs, we have optimised the quantity we are measuring. V6 would stop
testing the metric and start testing the clustering.

k-means is exactly that circular procedure -- it minimises within-cluster
scatter. **So we run it ON PURPOSE, as a BEST CASE.** The logic:

    If the MOST favourable possible organ definition still cannot get
    sigma_dir/delta below the 0.3 alarm line, then no organ definition can,
    and option (c) is dead as a fix for V6.

A bound obtained from an optimistic assumption is informative precisely when it
FAILS. If it succeeds we have learned only that (c) *might* help, and a
non-circular test (a co-activation lens, per Construction 4) is still owed.
This file therefore reports a bound, never a verdict in (c)'s favour.

WHAT IS HELD FIXED
------------------
Same corpus, same paragraphs, same bge-small contract, same stalk construction
(belief.stalk_gaussian), same sigma_dir definition, same global delta estimator
(derived_scales.derive_delta) as V6. ONLY the assignment of concepts to organs
changes. Anything else moving would make the comparison meaningless.
"""

from __future__ import annotations

import os
import sys
from typing import Dict, List, Sequence, Tuple

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import console  # noqa: E402
from embeddings import embed_batch  # noqa: E402
from belief import stalk_gaussian  # noqa: E402
from cone_bures import bures_w2_sq  # noqa: E402
from derived_scales import derive_delta  # noqa: E402
from measure_sigma_dir import load_organs, sigma_dir  # noqa: E402

SIGMA_ALARM = 0.3   # 5z's line: above this, agreement with true HK collapses


def kmeans(X: np.ndarray, k: int, seed: int = 0, iters: int = 100
           ) -> np.ndarray:
    """Plain Lloyd's algorithm with k-means++ init. Deterministic given `seed`.

    Deliberately vanilla: the point is to give the organ definition the BEST
    possible shot at minimising within-organ scatter, not to be clever.
    """
    rng = np.random.default_rng(seed)
    n = X.shape[0]
    # k-means++ seeding
    centres = [X[rng.integers(n)]]
    for _ in range(1, k):
        d2 = np.min([np.sum((X - c) ** 2, axis=1) for c in centres], axis=0)
        tot = d2.sum()
        if tot <= 0:
            centres.append(X[rng.integers(n)])
            continue
        centres.append(X[rng.choice(n, p=d2 / tot)])
    C = np.stack(centres)
    labels = np.zeros(n, dtype=int)
    for _ in range(iters):
        d = ((X[:, None, :] - C[None, :, :]) ** 2).sum(-1)
        new = d.argmin(1)
        if np.array_equal(new, labels):
            break
        labels = new
        for j in range(k):
            m = labels == j
            if m.any():
                C[j] = X[m].mean(0)
    return labels


def ratios_for(groups: Dict[str, np.ndarray],
               delta_global: float) -> Tuple[np.ndarray, np.ndarray]:
    """(per-pair sigma_dir/delta_global, per-pair d_BW) for a grouping."""
    stalks = {}
    for name, M in groups.items():
        if len(M) < 2:
            continue          # an organ of one concept has no scatter to measure
        g = stalk_gaussian([v for v in M])
        if g is not None:
            stalks[name] = g
    names = sorted(stalks)
    rs, ds = [], []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = stalks[names[i]], stalks[names[j]]
            try:
                sa, sb = sigma_dir(a.mu, a.U, b.mu, b.U, a.eps, b.eps)
            except ValueError:
                continue
            d_bw = float(np.sqrt(max(0.0, bures_w2_sq(a, b))))
            if d_bw < 1e-9:
                continue
            rs.append(max(sa, sb) / delta_global)
            ds.append(d_bw)
    return np.array(rs), np.array(ds)


def main() -> int:
    console.setup()
    print("=" * 78)
    print("V6b — DOES THE ORGAN DEFINITION FIX sigma_dir/delta?")
    print("=" * 78)
    print("k-means organs are CIRCULAR by construction (they minimise the very")
    print("scatter we then measure). That is deliberate: they give a BEST CASE.")
    print("A failure here is conclusive; a success is only permission to test")
    print("properly with a non-circular lens.\n")

    organs_text = load_organs()
    names = sorted(organs_text)
    embs = {n: np.stack([np.asarray(v, float)
                         for v in embed_batch(organs_text[n])]) for n in names}
    allX = np.vstack([embs[n] for n in names])
    doc_of = np.concatenate([[i] * len(embs[n]) for i, n in enumerate(names)])
    print(f"corpus: {len(names)} documents, {len(allX)} concepts, d={allX.shape[1]}")

    # --- global delta, derived exactly as V6 does, held FIXED across arms ----
    within, between = [], []
    for i, n in enumerate(names):
        M = embs[n]
        for a in range(len(M)):
            for b in range(a + 1, len(M)):
                within.append(float(np.linalg.norm(M[a] - M[b])))
        for n2 in names[i + 1:]:
            M2 = embs[n2]
            for a in range(0, len(M), 3):
                for b in range(0, len(M2), 3):
                    between.append(float(np.linalg.norm(M[a] - M2[b])))
    est = derive_delta(within, between)
    print(f"global delta (held fixed across all arms): {est.delta:.4f} "
          f"(d*={est.d_star:.4f}, separability={est.separability:.3f})\n")

    print(f"{'organ definition':<34} {'pairs':>6} {'d_BW med':>9} "
          f"{'sd/delta med':>13} {'max':>7} {'>0.3':>6}")
    print("-" * 78)

    # ARM 1: documents (V6's definition -- the baseline to beat)
    r, d = ratios_for({n: embs[n] for n in names}, est.delta)
    base = float(np.median(r))
    print(f"{'documents (V6 baseline)':<34} {len(r):>6} {np.median(d):>9.3f} "
          f"{base:>13.4f} {r.max():>7.4f} {float((r > SIGMA_ALARM).mean()):>6.2f}")

    # ARM 2..: k-means organs, swept over k -- the BEST-CASE bound
    best = (None, 9e9)
    for k in (4, 6, 8, 11, 16, 24, 32):
        lab = kmeans(allX, k, seed=0)
        groups = {f"c{j}": allX[lab == j] for j in range(k)
                  if (lab == j).sum() >= 2}
        if len(groups) < 2:
            continue
        r, d = ratios_for(groups, est.delta)
        if r.size == 0:
            continue
        med = float(np.median(r))
        if med < best[1]:
            best = (k, med)
        print(f"{'k-means organs, k=' + str(k):<34} {len(r):>6} "
              f"{np.median(d):>9.3f} {med:>13.4f} {r.max():>7.4f} "
              f"{float((r > SIGMA_ALARM).mean()):>6.2f}")

    print("\n" + "=" * 78)
    print("VERDICT")
    print("=" * 78)
    k_best, med_best = best
    print(f"  V6 baseline (documents)     : {base:.4f}")
    print(f"  BEST CASE (k-means, k={k_best})   : {med_best:.4f}")
    change = 100.0 * (med_best - base) / base
    print(f"  change                      : {change:+.1f}%")
    print(f"  alarm line                  : {SIGMA_ALARM}")
    if med_best > SIGMA_ALARM:
        print("\n  >> Even the MOST FAVOURABLE organ definition stays above the")
        print("     alarm line. Option (c) CANNOT fix V6's number. The problem is")
        print("     not how concepts are grouped -- it is that this corpus's")
        print("     concepts are genuinely that close together.")
    else:
        print("\n  >> The best case clears the alarm line, so (c) MIGHT help.")
        print("     This is NOT evidence that it does: k-means optimised the")
        print("     measured quantity. A non-circular lens (co-activation, per")
        print("     Construction 4) is still owed before claiming anything.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
