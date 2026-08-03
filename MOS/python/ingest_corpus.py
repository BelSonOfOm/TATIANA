"""Populate the KnowledgeBase from a local text corpus. No API calls.

WHY THIS EXISTS. mos_brain.db held ONE concept, of dimension 2 -- a stale test
artefact that the engine's fast dimension rejection skips. With an empty store
SearchOp can retrieve nothing, so no tick has a co-activation pair, so
Construction 5 has no matrix to fit and the consolidation loop has no edges.
Everything downstream of retrieval was untestable for want of a corpus.

TWO PARAMETERS HERE ARE COUPLED TO THE ENGINE AND MUST NOT BE CHOSEN FREELY.

1. noise_floor D = 1.0, matching SearchOp's `derived_variance = ||q||`.
   Bures-Wasserstein carries an epistemic term d*(sqrt(D_q) - sqrt(D_c))^2.
   bge-small returns UNIT vectors, so D_q = 1 exactly; a concept stored with the
   usual freshly-grown floor stalk_floor(384, n_eff=1) = O(1/d) would then sit
   384*(1 - 0.05)^2 ~= 346 away on variance alone, and NOTHING would ever be
   retrieved however well the means aligned. That is not a tuning choice, it is
   the only value at which the semantic term is what decides relevance.

2. rank = 0, so no U matrix. A chunk seen once has zero scatter about its own
   mean; inventing a covariance from a single observation is exactly the FIX-13
   error. Rank grows when a concept is seen again, not at ingestion.

WHAT THIS CORPUS IS, SAID PLAINLY: TATIANA's own design documents. It is real
text with real topic structure, and it is NOT general mathematics. A Tier-0
verdict computed from it describes the retrieval structure of THIS corpus. Point
--source at something else to widen the claim.

    python ingest_corpus.py --source ../../DOCS --dry-run
    python ingest_corpus.py --source ../../DOCS
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import os
import re
import sqlite3
import struct
import sys
from typing import List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

DEFAULT_DB = os.path.join(os.path.dirname(HERE), "mos_brain.db")

SCHEMA = """CREATE TABLE IF NOT EXISTS distilled_theorems (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_hash TEXT UNIQUE,
    reasoning_chain TEXT,
    dimension INTEGER,
    rank INTEGER DEFAULT 0,
    mu_vector BLOB,
    u_matrix BLOB,
    noise_floor REAL DEFAULT 1.0,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)"""

MIN_WORDS = 25      # below this a chunk is a heading or a stray line, not a concept
MAX_WORDS = 220     # above this the mean smears across several topics


def clean(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_file(path: str) -> List[str]:
    """Paragraph chunks. Paragraphs are the natural unit here: the corpus is
    prose with blank-line separation, and a fixed token window would cut across
    topic boundaries, blurring exactly the structure the cover model looks for."""
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            raw = fh.read()
    except OSError:
        return []

    out: List[str] = []
    for para in clean(raw).split("\n\n"):
        para = para.strip()
        words = para.split()
        if len(words) < MIN_WORDS:
            continue
        # Long paragraphs are split on sentence boundaries rather than mid-word.
        while len(words) > MAX_WORDS:
            head = " ".join(words[:MAX_WORDS])
            cut = max(head.rfind(". "), head.rfind("? "), head.rfind("! "))
            if cut < len(head) // 3:
                cut = len(head)
            out.append(head[:cut + 1].strip())
            consumed = len(head[:cut + 1].split())
            words = words[consumed:]
        if len(words) >= MIN_WORDS:
            out.append(" ".join(words))
    return out


def collect(source: str, patterns: Tuple[str, ...]) -> List[Tuple[str, str]]:
    """(source_file, chunk_text) pairs, so provenance survives into the DB."""
    found: List[Tuple[str, str]] = []
    for pat in patterns:
        for path in sorted(glob.glob(os.path.join(source, pat))):
            for ch in chunk_file(path):
                found.append((os.path.basename(path), ch))
    return found


def concept_name(src: str, chunk: str, idx: int) -> str:
    """A short, human-readable, UNIQUE name. This string is the vertex identity
    in the concept store and the column label in the assembly matrix, so it has
    to stay stable and readable -- an opaque hash would make every downstream
    table unreadable."""
    head = " ".join(chunk.split()[:9])
    head = re.sub(r"[^\w\s\-/^+]", "", head).strip()
    return f"{src}#{idx:04d}: {head}"


def open_db(path: str) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.execute(SCHEMA)
    return con


def write_concepts(con, names, vectors, dim, noise_floor, batch, texts=None):
    """Insert in committed batches, skipping what is already there.

    CHECKPOINTED AND RESUMABLE ON PURPOSE. The first version of this script held
    every embedding in memory and wrote once at the very end; when it was killed
    ten minutes in, it left ZERO rows and the whole run had to start over. A long
    job whose partial progress is worth nothing is a bug in the job, not bad luck.
    """
    written = skipped = 0
    pending = 0
    for i, (name, vec) in enumerate(zip(names, vectors)):
        if len(vec) != dim:
            skipped += 1
            continue
        src = texts[i] if texts is not None else name
        h = hashlib.sha1(str(src).encode("utf-8")).hexdigest()
        if con.execute("SELECT 1 FROM distilled_theorems WHERE content_hash=?",
                       (h,)).fetchone():
            skipped += 1
            continue
        blob = struct.pack(f"<{dim}d", *[float(x) for x in vec])
        con.execute(
            "INSERT OR REPLACE INTO distilled_theorems "
            "(content_hash, reasoning_chain, dimension, rank, mu_vector, "
            " u_matrix, noise_floor) VALUES (?,?,?,?,?,?,?)",
            (h, str(name), dim, 0, blob, None, noise_floor))
        written += 1
        pending += 1
        if pending >= batch:
            con.commit()
            pending = 0
            print(f"  committed {written} ...", flush=True)
    con.commit()
    return written, skipped


def ingest_precomputed(args) -> int:
    """Load vectors embedded elsewhere (Colab). No model is loaded here at all."""
    import numpy as np

    data = np.load(args.vectors, allow_pickle=True)
    missing = {"names", "vectors"} - set(data.files)
    if missing:
        print(f"[ingest] {args.vectors} is missing {sorted(missing)}", file=sys.stderr)
        return 2

    names = data["names"]
    vectors = data["vectors"]
    texts = data["texts"] if "texts" in data.files else None
    dim = int(vectors.shape[1])

    print(f"[ingest] precomputed : {args.vectors}")
    print(f"[ingest] concepts    : {len(names)} at {dim}-d")
    norms = np.linalg.norm(vectors, axis=1)
    print(f"[ingest] norms       : [{norms.min():.4f}, {norms.max():.4f}]")
    if abs(float(norms.mean()) - 1.0) > 0.05:
        # SearchOp sets derived_variance = ||q||, so non-unit vectors silently
        # move every retrieval threshold. Worth refusing to guess about.
        print("[ingest] WARNING: vectors are not unit-norm. SearchOp derives its "
              "variance from ||q||, so retrieval will not behave as measured.")
    if args.dry_run:
        print("[ingest] DRY RUN -- nothing written.")
        for n in names[:3]:
            print(f"  {str(n)[:88]}")
        return 0

    con = open_db(args.db)
    written, skipped = write_concepts(con, names, vectors, dim,
                                      args.noise_floor, args.batch, texts)
    total = con.execute("SELECT COUNT(*) FROM distilled_theorems WHERE dimension=?",
                        (dim,)).fetchone()[0]
    con.close()
    print(f"[ingest] wrote {written}, skipped {skipped} (already present or wrong dim)")
    print(f"[ingest] db now holds {total} concepts at {dim}-d -> {args.db}")
    print("[ingest] embeddings computed on this machine: 0")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", default=os.path.join(os.path.dirname(HERE), "..", "DOCS"))
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--patterns", default="*.txt,*.md,*.tex")
    ap.add_argument("--noise-floor", type=float, default=1.0,
                    help="stored D. 1.0 matches SearchOp's derived_variance for "
                         "unit embeddings; see the module docstring before changing")
    ap.add_argument("--limit", type=int, default=0, help="0 = no cap")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--vectors", default=None,
                    help="a .npz from colab_prepare_corpus.ipynb (names, texts, "
                         "vectors). Skips embedding entirely -- nothing is "
                         "computed on this machine.")
    ap.add_argument("--threads", type=int, default=2,
                    help="cap for the LOCAL embedding path. fastembed otherwise "
                         "takes every core, which is what made a full-corpus "
                         "embed peg the machine for ten minutes.")
    ap.add_argument("--batch", type=int, default=50,
                    help="commit every N concepts, so an interrupt loses seconds "
                         "rather than the whole run")
    args = ap.parse_args()

    if args.vectors:
        return ingest_precomputed(args)

    patterns = tuple(p.strip() for p in args.patterns.split(",") if p.strip())
    source = os.path.abspath(args.source)
    chunks = collect(source, patterns)
    if args.limit:
        chunks = chunks[:args.limit]

    print(f"[ingest] source   : {source}")
    print(f"[ingest] patterns : {patterns}")
    print(f"[ingest] chunks   : {len(chunks)}")
    if not chunks:
        print("[ingest] nothing to ingest", file=sys.stderr)
        return 2

    by_file: dict = {}
    for src, _ in chunks:
        by_file[src] = by_file.get(src, 0) + 1
    for src, n in sorted(by_file.items(), key=lambda kv: -kv[1])[:8]:
        print(f"           {n:5d}  {src}")

    if args.dry_run:
        print("\n[ingest] DRY RUN -- nothing embedded or written.")
        for src, ch in chunks[:3]:
            print(f"  {concept_name(src, ch, 0)[:88]}")
        return 0

    # THREAD CAP, SET BEFORE THE MODEL IS IMPORTED.
    # ONNX Runtime reads these at session creation, so setting them afterwards
    # does nothing. Uncapped, fastembed takes every core and a full-corpus embed
    # saturates the machine for the whole run -- which is exactly how this script
    # cooked a laptop the first time it was used in anger.
    for var in ("OMP_NUM_THREADS", "ONNXRUNTIME_NUM_THREADS",
                "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ.setdefault(var, str(max(1, args.threads)))

    from embeddings import embed_batch, EMBED_DIM

    print(f"[ingest] embedding {len(chunks)} chunks locally ({EMBED_DIM}-d, no API)")
    print(f"[ingest] threads capped at {args.threads}; committing every {args.batch}")
    print("[ingest] SLOW ON PURPOSE. Prefer --vectors from Colab if you need this fast.")

    con = open_db(args.db)
    names = [concept_name(src, chunk, i) for i, (src, chunk) in enumerate(chunks)]
    texts = [chunk for _, chunk in chunks]

    written = skipped = 0
    # Embedded AND committed in slices, so Ctrl-C costs one slice, not the run.
    for start in range(0, len(chunks), args.batch):
        sl = slice(start, start + args.batch)
        vecs = embed_batch(texts[sl])
        w, s = write_concepts(con, names[sl], vecs, EMBED_DIM,
                              args.noise_floor, args.batch, texts[sl])
        written += w
        skipped += s
        print(f"  {min(start+args.batch, len(chunks))}/{len(chunks)} "
              f"({written} written)", flush=True)

    total = con.execute(
        "SELECT COUNT(*) FROM distilled_theorems WHERE dimension=?",
        (EMBED_DIM,)).fetchone()[0]
    con.close()
    print(f"[ingest] wrote {written}, skipped {skipped}")
    print(f"[ingest] db now holds {total} concepts at {EMBED_DIM}-d -> {args.db}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
