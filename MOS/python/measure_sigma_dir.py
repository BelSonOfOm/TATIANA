"""
V6 - measure sigma_dir/delta on the REAL corpus.

WHY
---
5z's verdict on Cone-Bures -- "tracks true HK to under 1% in value and ~87% on
the merge decision" -- rests entirely on sigma_dir/delta ~ 0.09, and that number
came from a CALIBRATED SIMULATION (validate_regime.py, using 5h/E1's cosine
statistics), not from live embeddings. 5z filed the gap itself:

  > V6 (new, from V1c) -- measure sigma_dir on the real corpus with live
  > bge-small embeddings. V1c is a calibrated simulation; it fixes the order of
  > magnitude but the whole verdict now rests on sigma_dir/delta ~ 0.09, so that
  > number must be measured, not simulated.

This script is that measurement. It is deliberately separate from
validate_regime.py, which stays as the simulation it is: overwriting a simulated
number with a measured one in the same file would lose the ability to compare
them, and the comparison is the point.

WHAT IT NEEDS, AND WHAT IT DOES WHEN THAT IS MISSING
-----------------------------------------------------
Two inputs, and it refuses rather than substitutes:

  1. A CORPUS -- concepts grouped by organ. Read from the engine's SQLite store
     (`distilled_theorems`) or from a JSONL file.
  2. LIVE EMBEDDINGS -- embeddings.py, i.e. bge-small via fastembed/ONNX.

If either is absent this prints exactly what is missing and exits non-zero. It
does NOT fall back to simulated vectors: a simulated number is what V6 exists to
replace, and producing one here under the banner "measured" is the single worst
outcome available.

USAGE
-----
    python measure_sigma_dir.py --db ../mos_brain_ipc.db
    python measure_sigma_dir.py --jsonl corpus.jsonl
    python measure_sigma_dir.py --db ... --delta 0.44

`--delta`, if omitted, is CALIBRATED the way V1c calibrated it: delta =
mean(d_BW)/pi, so the saturation cutoff sits at the typical inter-organ Bures
distance. Otherwise delta is idle and nothing is ever "different". The calibrated
value is reported, because it is an input to every number below it.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

import console
from belief import Gaussian, stalk_gaussian
from cone_bures import (ConeBures, REGIME_CHANCE, REGIME_OK, REGIME_WARN,
                        RegimeMonitor, bures_w2_sq)


class MissingInput(RuntimeError):
    """A required input is absent. Never substituted."""


# --------------------------------------------------------------------------
# Corpus loading
# --------------------------------------------------------------------------

def load_gaussians_from_sqlite(path: str) -> List[Tuple[str, Gaussian]]:
    """(name, Gaussian) per stored concept, straight out of the engine's store.

    **This path needs no embedding model at all.** `distilled_theorems` persists
    the geometry itself -- `mu_vector` (BLOB of d doubles), `u_matrix` (BLOB of
    d*k doubles, COLUMN-MAJOR per knowledge_base.cpp:19) and `noise_floor` -- so
    the stalks the engine actually merges on can be read back exactly. That is
    strictly better than re-embedding the text: re-embedding would measure a
    corpus the engine never saw if the model or its version ever drifted.

    Pairs of stored concepts are also the right unit. The merge predicate is
    applied concept-to-concept, so sigma_dir/delta over these pairs is the
    quantity that governs real merge decisions, not an organ-level aggregate.
    """
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    except sqlite3.Error as e:
        raise MissingInput(f"cannot open {path}: {e}") from e

    tables = [r[0] for r in con.execute(
        "select name from sqlite_master where type='table'")]
    if "distilled_theorems" not in tables:
        raise MissingInput(
            f"{path} has no `distilled_theorems` table (found: {tables or 'none'})")

    cols = [r[1] for r in con.execute("pragma table_info(distilled_theorems)")]
    required = {"dimension", "rank", "mu_vector", "noise_floor"}
    missing = required - set(cols)
    if missing:
        raise MissingInput(
            f"{path}: distilled_theorems is missing {sorted(missing)} "
            f"(columns present: {cols}). This is not a MOS concept store.")

    rows = con.execute(
        "select reasoning_chain, dimension, rank, mu_vector, u_matrix, noise_floor "
        "from distilled_theorems").fetchall()
    con.close()

    if not rows:
        raise MissingInput(
            f"{path}: `distilled_theorems` exists but holds 0 ROWS. There is no "
            "corpus to measure. V6 needs a populated store -- run the engine and "
            "ingest something first. (All three checked-in .db files are empty.)")

    out: List[Tuple[str, Gaussian]] = []
    for i, (chain, dim, rank, mu_blob, u_blob, floor) in enumerate(rows):
        d = int(dim)
        k = int(rank or 0)
        mu = np.frombuffer(mu_blob, dtype=np.float64)
        if mu.size != d:
            raise MissingInput(
                f"row {i}: mu_vector holds {mu.size} doubles but dimension={d}. "
                "Refusing to reshape geometry (embeddings.py contract 2).")
        if k and u_blob:
            u_flat = np.frombuffer(u_blob, dtype=np.float64)
            if u_flat.size != d * k:
                raise MissingInput(
                    f"row {i}: u_matrix holds {u_flat.size} doubles, expected "
                    f"d*k = {d * k}. Refusing to reshape.")
            U = np.array(u_flat, dtype=float).reshape((d, k), order="F")  # column-major
        else:
            U = np.zeros((d, 0))
        name = (str(chain)[:40] if chain else f"concept[{i}]")
        out.append((name, Gaussian(mu=np.array(mu, dtype=float), U=U,
                                   eps=float(floor))))
    return out


def load_texts_from_jsonl(path: str) -> Dict[str, List[str]]:
    """{organ: [text, ...]} -- the RAW-TEXT path, which does need live embeddings.

    Only for corpora that have not been through the engine yet. Prefer --db when
    a store exists: it holds the stalks the engine actually merged on.
    """
    return _load_jsonl(path)


def _load_jsonl(path: str) -> Dict[str, List[str]]:
    """{organ: [text, ...]} from one JSON object per line with `organ` + `text`."""
    out: Dict[str, List[str]] = defaultdict(list)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for i, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError as e:
                    raise MissingInput(f"{path}:{i} is not valid JSON: {e}") from e
                text = rec.get("text") or rec.get("statement") or rec.get("content")
                if not text:
                    raise MissingInput(
                        f"{path}:{i} has no text/statement/content field")
                out[str(rec.get("organ", "ALL"))].append(str(text))
    except FileNotFoundError as e:
        raise MissingInput(f"no such file: {path}") from e
    if not out:
        raise MissingInput(f"{path} is empty")
    return dict(out)


def embed_all(corpus: Dict[str, List[str]]) -> Dict[str, List[np.ndarray]]:
    """Live bge-small embeddings, via the project's single source of truth."""
    try:
        import embeddings
    except Exception as e:                       # noqa: BLE001 - report the real cause
        raise MissingInput(
            f"embeddings.py is unusable in this environment ({e.__class__.__name__}: {e}). "
            "V6 requires LIVE bge-small vectors; it will not simulate them, because "
            "a simulated sigma_dir is exactly what V6 exists to replace.") from e

    out: Dict[str, List[np.ndarray]] = {}
    try:
        for organ, texts in corpus.items():
            out[organ] = [np.asarray(embeddings.embed(t), dtype=float) for t in texts]
    except Exception as e:                       # noqa: BLE001 - report the real cause
        raise MissingInput(
            f"live embedding failed ({e.__class__.__name__}: {e}). V6 requires "
            "LIVE bge-small vectors and will not simulate them. If a MOS store "
            "exists, prefer --db: it holds the stalks the engine actually used "
            "and needs no model at all.") from e
    return out


# --------------------------------------------------------------------------
# The measurement
# --------------------------------------------------------------------------

def measure(stalks: List[Tuple[str, Gaussian]],
            delta: Optional[float] = None,
            unit: str = "concept") -> int:
    """Measure sigma_dir/delta over every pair. Returns a process exit code."""
    if len(stalks) < 2:
        raise MissingInput(
            f"need >= 2 {unit}s to have a separation direction at all; got {len(stalks)}")

    names = [n for n, _ in stalks]
    gs = [g for _, g in stalks]
    idx = [(i, j) for i in range(len(gs)) for j in range(i + 1, len(gs))]

    d_bw = [float(np.sqrt(max(bures_w2_sq(gs[i], gs[j]), 0.0))) for i, j in idx]
    if delta is None:
        delta = float(np.mean(d_bw)) / np.pi
        how = "CALIBRATED as mean(d_BW)/pi (V1c's rule)"
    else:
        how = "supplied on the command line"
    if delta <= 0:
        raise MissingInput(f"delta must be > 0, got {delta}")

    metric = ConeBures(delta=delta)
    mon = RegimeMonitor(metric, window=max(len(idx), 1))

    print(f"  {unit}s          : {len(gs)}")
    print(f"  embedding dim    : {gs[0].d}")
    print(f"  ranks            : min {min(g.k for g in gs)}, max {max(g.k for g in gs)}")
    print(f"  pairs measured   : {len(idx)}")
    print(f"  delta            : {delta:.6f}   ({how})")
    print()
    show = len(idx) <= 40
    if show:
        print(f"  {'pair':<44}{'d_BW':>9}{'sigma_dir':>11}{'sd/delta':>10}{'gap':>8}")
        print("  " + "-" * 82)
    skipped = 0
    for (i, j), dbw in zip(idx, d_bw):
        try:
            ratio = metric.regime_ratio(gs[i], gs[j])
        except ValueError:
            skipped += 1
            continue
        mon.observe_ratio(ratio)
        if show:
            sd = float(np.sqrt(metric.sigma_dir_sq(gs[i], gs[j])))
            label = f"{names[i][:20]}~{names[j][:20]}"
            print(f"  {label:<44}{dbw:9.4f}{sd:11.5f}{ratio:10.4f}"
                  f"{1.0 + ratio * ratio:8.4f}")
    if skipped:
        print(f"  ({skipped} pairs skipped: coincident means, no separation direction)")

    rep = mon.report()
    if rep.status == "empty":
        raise MissingInput("every pair had coincident means; nothing measurable")
    print()
    print("  " + rep.report())
    print()
    print(f"  reference points : OK <= {REGIME_OK}   degrading >= {REGIME_WARN}"
          f"   chance >= {REGIME_CHANCE}")
    print("  V1c SIMULATED    : sigma_dir 0.0355-0.0440, sigma_dir/delta 0.084-0.100")
    print(f"  THIS MEASUREMENT : mean {rep.mean:.4f}, p95 {rep.p95:.4f}, "
          f"worst {rep.worst:.4f}")
    if rep.status == "ok":
        print("  => the 5z verdict SURVIVES contact with the real corpus.")
        return 0
    print(f"  => STATUS {rep.status.upper()}. The 5z verdict does NOT hold here:")
    print(f"     Cone-Bures overstates squared merge distances by "
          f"{(rep.mean_implied_gap - 1) * 100:.1f}% on average, and "
          f"{rep.frac_above_chance * 100:.1f}% of pairs are coin flips.")
    print("     5z's own condition for this is met -- act on it, do not average it away.")
    return 2


def _selftest() -> int:
    """Round-trip the store reader against a synthetic DB in the REAL schema.

    The loader is the part of V6 that will run unattended on data nobody has
    looked at, and a silent misread (wrong U ordering, wrong dtype) would produce
    a plausible sigma_dir that is simply wrong. So it is checked against
    hand-constructed Gaussians whose sigma_dir is known in closed form.
    """
    import os
    import tempfile

    d, k = 8, 2
    rng = np.random.default_rng(0)
    truth = []
    for i in range(4):
        mu = rng.normal(size=d)
        U = rng.normal(size=(d, k)) * 0.3
        truth.append(Gaussian(mu=mu, U=U, eps=1e-3 * (i + 1)))

    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        con = sqlite3.connect(path)
        con.execute("create table distilled_theorems ("
                    "id integer primary key autoincrement, content_hash text, "
                    "reasoning_chain text, dimension integer, rank integer, "
                    "mu_vector blob, u_matrix blob, noise_floor real, timestamp text)")
        for i, g in enumerate(truth):
            con.execute(
                "insert into distilled_theorems (content_hash, reasoning_chain, "
                "dimension, rank, mu_vector, u_matrix, noise_floor) "
                "values (?,?,?,?,?,?,?)",
                (f"h{i}", f"concept {i}", d, k,
                 g.mu.astype(np.float64).tobytes(),
                 # COLUMN-MAJOR, matching knowledge_base.cpp:19
                 np.asfortranarray(g.U, dtype=np.float64).tobytes(order="F"),
                 g.eps))
        con.commit()
        con.close()

        loaded = load_gaussians_from_sqlite(path)
        assert len(loaded) == len(truth), (len(loaded), len(truth))
        for (name, g), t in zip(loaded, truth):
            assert np.allclose(g.mu, t.mu), name
            assert g.U.shape == t.U.shape, (g.U.shape, t.U.shape)
            assert np.allclose(g.U, t.U), f"{name}: U did not round-trip (ordering?)"
            assert abs(g.eps - t.eps) < 1e-15, name
        print("  [ok] mu, U (column-major) and noise_floor round-trip exactly")

        # sigma_dir against a hand computation on the loaded pair.
        cb = ConeBures(delta=1.0)
        g0, g1 = loaded[0][1], loaded[1][1]
        u = (g0.mu - g1.mu) / np.linalg.norm(g0.mu - g1.mu)
        hand = 0.5 * ((g0.eps + float((u @ g0.U) @ (u @ g0.U)))
                      + (g1.eps + float((u @ g1.U) @ (u @ g1.U))))
        assert abs(cb.sigma_dir_sq(g0, g1) - hand) < 1e-15
        print(f"  [ok] sigma_dir^2 matches the hand computation ({hand:.6f})")

        # A rank mismatch must be refused, not reshaped.
        con = sqlite3.connect(path)
        con.execute("update distilled_theorems set rank = 3 where id = 1")
        con.commit(); con.close()
        try:
            load_gaussians_from_sqlite(path)
        except MissingInput as e:
            assert "Refusing to reshape" in str(e)
            print("  [ok] a rank/blob-size mismatch is REFUSED, not reshaped")
        else:
            raise AssertionError("should have refused a size mismatch")

        print("  [ok] end-to-end measure() on the synthetic store:")
        print()
        rc = measure(loaded[:3], delta=None, unit="concept")
        assert rc in (0, 2)
    finally:
        os.unlink(path)
    print()
    print("V6 SELF-TEST PASSED (the reader is verified; the CORPUS is what is missing)")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="V6: measure sigma_dir/delta on the real corpus")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--db", help="engine SQLite store (preferred: needs no model)")
    src.add_argument("--jsonl", help="raw-text JSONL: {organ, text} per line")
    src.add_argument("--selftest", action="store_true",
                     help="round-trip the SQLite reader against a synthetic store")
    ap.add_argument("--delta", type=float, default=None,
                    help="length scale; default calibrates as mean(d_BW)/pi")
    args = ap.parse_args(argv)

    console.setup()
    print("=" * 78)
    print("V6 - sigma_dir/delta ON THE REAL CORPUS (measured, not simulated)")
    print("=" * 78)
    try:
        if args.selftest:
            return _selftest()
        if args.db:
            # Preferred path: the store holds the stalks the engine merged on,
            # so no embedding model is involved and no re-embedding drift is
            # possible.
            stalks = load_gaussians_from_sqlite(args.db)
            print(f"  source           : {args.db} (stored stalks, no model needed)")
            return measure(stalks, args.delta, unit="concept")
        corpus = load_texts_from_jsonl(args.jsonl)
        print(f"  source           : {args.jsonl} "
              f"({sum(len(v) for v in corpus.values())} texts, LIVE embedding)")
        vecs = embed_all(corpus)
        organs = [(k, stalk_gaussian(v)) for k, v in vecs.items() if len(v) >= 2]
        if len(organs) < 2:
            raise MissingInput(
                f"need >= 2 organs with >= 2 texts each; got "
                f"{ {k: len(v) for k, v in vecs.items()} }")
        return measure(organs, args.delta, unit="organ")
    except MissingInput as e:
        print()
        print("V6 CANNOT RUN - a required input is missing:")
        print(f"   {e}")
        print()
        print("   Refusing to substitute simulated data. V1c's number is already a")
        print("   simulation; producing another one here and labelling it 'measured'")
        print("   would be worse than having no number at all.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
