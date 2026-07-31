"""
V6 — MEASURE sigma_dir ON THE REAL CORPUS, WITH LIVE bge-small EMBEDDINGS.

WHY THIS IS OWED
----------------
The entire 5z verdict on the Cone-Bures metric rests on ONE number:

    sigma_dir / delta ~= 0.09   =>  agreement with true HK under 1% in value
                                    and ~87% on the merge decision

V1c produced that number from a CALIBRATED SIMULATION -- stalks generated to
match the logbook's own cos_within ~ 0.833 statistic, not stalks built from real
text. The simulation fixes the ORDER OF MAGNITUDE, which is what the question
turns on, but 5z filed V6 explicitly because "the whole verdict now rests on
sigma_dir/delta ~= 0.09, so that number must be MEASURED, not simulated."

If the real value lands above ~0.3, agreement with true HK collapses and the
merge predicate is near chance. That is a live possibility, not a formality.

WHAT sigma_dir IS (and the error V1c corrected)
-----------------------------------------------
NOT ||U||_F, which aggregates over all 384 dimensions and all k columns. What the
transport problem sees is the spread ALONG THE SEPARATION DIRECTION:

    u = (mu_0 - mu_1)/||mu_0 - mu_1||,     sigma_dir^2 = u^T Sigma u

Reading the regime off ||U||_F instead is the exact mistake that produced 5z's
retracted "MOS sits at ~50% agreement, i.e. chance" claim. Since the rank-k
covariance is mostly orthogonal to the separation (k << d), sigma_dir is far
smaller than ||U||_F.

delta is then fixed by the saturation condition pi*delta = d_BW, so

    sigma_dir / delta = pi * sigma_dir / d_BW

THE CORPUS, STATED PLAINLY
--------------------------
Organs are built from the project's own DOCS -- real research prose in the actual
target domain, embedded with the real bge-small-en-v1.5 contract from
embeddings.py (384-d, unit-normalised, no truncation, no padding). Each document
is one organ; its paragraphs are that organ's concepts. This is a REAL corpus in
the sense V6 requires (live embeddings of real text, not synthetic vectors), and
it is the honest one available: it is Charbel's own working material in the
domain MOS is built for.

It is NOT a claim about arbitrary corpora. What is measured is what MOS's organs
look like when filled with mathematical research prose, which is the deployment
case. Reported per organ-pair so the SPREAD of the ratio is visible, not just a
mean that could hide a bad tail.
"""

from __future__ import annotations

import os
import re
import sys
from typing import Dict, List, Sequence, Tuple

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import console  # noqa: E402
from embeddings import embed_batch, EMBED_DIM  # noqa: E402
from belief import stalk_gaussian  # noqa: E402
from cone_bures import bures_w2_sq  # noqa: E402
from derived_scales import derive_delta  # noqa: E402

DOCS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", "..", "DOCS"))

# A paragraph shorter than this is a heading, a table row, or a fragment -- not a
# concept. Stated rather than tuned: the cut exists to keep the unit of embedding
# a self-contained claim.
MIN_PARA_CHARS = 200
MAX_PARAS_PER_ORGAN = 60


def load_organs(docs_dir: str = DOCS) -> Dict[str, List[str]]:
    """One organ per document; its paragraphs are that organ's concepts."""
    organs: Dict[str, List[str]] = {}
    for name in sorted(os.listdir(docs_dir)):
        if not name.lower().endswith((".md", ".txt")):
            continue
        path = os.path.join(docs_dir, name)
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                text = fh.read()
        except OSError:
            continue
        paras = [re.sub(r"\s+", " ", p).strip()
                 for p in re.split(r"\n\s*\n", text)]
        paras = [p for p in paras if len(p) >= MIN_PARA_CHARS]
        if len(paras) >= 5:
            organs[os.path.splitext(name)[0]] = paras[:MAX_PARAS_PER_ORGAN]
    return organs


def sigma_dir(mu_a: np.ndarray, Sigma_a_factor: np.ndarray,
              mu_b: np.ndarray, Sigma_b_factor: np.ndarray,
              eps_a: float, eps_b: float) -> Tuple[float, float]:
    """Spread along the separation direction, for each of the two stalks.

    Sigma = U U^T + eps I, so u^T Sigma u = ||U^T u||^2 + eps for a unit u.
    """
    diff = mu_a - mu_b
    nrm = float(np.linalg.norm(diff))
    if nrm < 1e-12:
        raise ValueError("organs coincide; separation direction undefined")
    u = diff / nrm
    sa = float(np.sum((Sigma_a_factor.T @ u) ** 2) + eps_a)
    sb = float(np.sum((Sigma_b_factor.T @ u) ** 2) + eps_b)
    return np.sqrt(sa), np.sqrt(sb)


def main() -> int:
    console.setup()
    print("=" * 78)
    print("V6 — sigma_dir ON THE REAL CORPUS (live bge-small, not simulated)")
    print("=" * 78)

    organs_text = load_organs()
    if len(organs_text) < 2:
        print(f"Not enough documents in {DOCS} to form two organs.")
        return 1

    print(f"corpus: {DOCS}")
    print(f"organs: {len(organs_text)}   (one per document, paragraphs = concepts)")
    print(f"embedding: bge-small-en-v1.5, d = {EMBED_DIM}, unit-normalised\n")

    stalks: Dict[str, object] = {}
    for name, paras in organs_text.items():
        vecs = [np.asarray(v, dtype=float) for v in embed_batch(paras)]
        if len(vecs[0]) != EMBED_DIM:
            raise RuntimeError(
                f"embedding dim {len(vecs[0])} != {EMBED_DIM}; refusing to reshape")
        g = stalk_gaussian(vecs)
        if g is None:
            continue
        stalks[name] = g
        print(f"  {name[:44]:<44} n={len(paras):>3}  n_eff={g.n_eff:>5.1f}  "
              f"k={g.U.shape[1]:>3}  ||U||_F={np.linalg.norm(g.U):.3f}")

    names = sorted(stalks)
    print(f"\n{'pair':<52} {'d_BW':>7} {'sigma_dir':>10} {'sd/delta':>9}")
    print("-" * 82)

    ratios: List[float] = []
    rows: List[Tuple[str, float, float, float]] = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = stalks[names[i]], stalks[names[j]]
            try:
                sa, sb = sigma_dir(a.mu, a.U, b.mu, b.U, a.eps, b.eps)
            except ValueError:
                continue
            sd = max(sa, sb)          # the worse of the two; do not average away
            # delta is fixed by the saturation condition pi*delta = d_BW, and
            # d_BW is the TRUE Bures-Wasserstein distance, not ||mu_a - mu_b||.
            # (d_BW >= ||dmu||, so using ||dmu|| would understate delta and
            # therefore OVERSTATE the ratio -- exactly the direction that would
            # flatter a bad result. Use the real thing.)
            d_bw = float(np.sqrt(max(0.0, bures_w2_sq(a, b))))
            if d_bw < 1e-9:
                continue
            delta = d_bw / np.pi
            ratio = sd / delta
            ratios.append(ratio)
            rows.append((f"{names[i][:24]} | {names[j][:24]}", d_bw, sd, ratio))

    for label, sep, sd, r in sorted(rows, key=lambda t: -t[3])[:12]:
        print(f"{label:<52} {sep:>7.3f} {sd:>10.4f} {r:>9.3f}")
    if len(rows) > 12:
        print(f"  ... {len(rows) - 12} more pairs")

    # ---- GLOBAL delta, derived (derived_scales.derive_delta) ----------------
    # The per-pair ratio above uses delta = d_BW/pi, i.e. a delta that SHRINKS
    # for close pairs and therefore inflates sigma_dir/delta exactly where the
    # pairs are hardest. A deployed system has ONE delta. Derive it from the
    # concept-level within/between distance distributions and re-read the ratio
    # against that, which is the number telemetry would actually carry.
    print("\n" + "=" * 78)
    print("GLOBAL delta, DERIVED FROM THE SAME CORPUS")
    print("=" * 78)
    within: List[float] = []
    between: List[float] = []
    embs = {n: np.stack([np.asarray(v, float)
                         for v in embed_batch(organs_text[n])])
            for n in names}
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
    print(f"  {est!r}")
    if not est.identifiable:
        print("  ⚠ within/between barely separate on this corpus, so this delta is")
        print("    weak evidence. Reported anyway rather than suppressed.")
    global_ratios = np.array([sd / est.delta for (_, _, sd, _) in rows])
    print(f"\n  sigma_dir / delta_global :  med {np.median(global_ratios):.4f}   "
          f"max {global_ratios.max():.4f}   "
          f"frac>0.3 {float((global_ratios > 0.3).mean()):.3f}")

    arr = np.array(ratios)
    print("\n" + "=" * 78)
    print("RESULT")
    print("=" * 78)
    print(f"  pairs measured        : {len(arr)}")
    print(f"  sigma_dir/delta  min  : {arr.min():.4f}")
    print(f"  sigma_dir/delta  med  : {np.median(arr):.4f}")
    print(f"  sigma_dir/delta  mean : {arr.mean():.4f}")
    print(f"  sigma_dir/delta  max  : {arr.max():.4f}   <-- the one that matters")
    print(f"  fraction above 0.3    : {float((arr > 0.3).mean()):.3f}")

    print("\n  V1c simulated: sigma_dir/delta ~= 0.084 - 0.100")
    worst = arr.max()
    if worst <= 0.3:
        print(f"  MEASURED worst case {worst:.3f} <= 0.30  ==> the 5z verdict HOLDS;")
        print("  Cone-Bures tracks true HK in MOS's real regime.")
    else:
        print(f"  MEASURED worst case {worst:.3f} > 0.30  ==> 5z's verdict does NOT")
        print("  hold uniformly. The metric degrades on the worst pairs and")
        print("  sigma_dir/delta must gate the merge predicate, not be assumed.")
    print("\n  (Telemetry: coarse_complex should log this ratio per tick;")
    print("   above ~0.3 the agreement with true HK collapses.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
