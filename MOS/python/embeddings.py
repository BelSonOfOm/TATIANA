"""
TATIANA — the single source of truth for semantic geometry.

Every vector that enters the cognitive state space M = (C, F, s) MUST come from
here. These vectors are the stalk data of the information sheaf F; the distances
between them are the conflict / Bures-Wasserstein scores the C++ engine computes.

THE CONTRACT
------------
1. ONE model, ONE dimension, system-wide. No component may invent its own.
2. NEVER truncate. NEVER pad. If a vector is not EMBED_DIM long, we RAISE.
   Silently reshaping geometry is how the old pipeline corrupted every distance
   it computed (a 512-truncate here, a fake 128-d hash there). A loud failure is
   always better than a quiet lie about the geometry.
3. Runs LOCALLY on CPU. Embeddings never consume API quota, so ingesting a
   1000-page book is free.

Model: BAAI/bge-small-en-v1.5 (384-d) via fastembed/ONNX — chosen because it runs
comfortably on a low-RAM CPU-only machine. Requires Python 3.11 (NOT the 3.14
beta, which has no onnxruntime wheels).
"""

from __future__ import annotations

import os
from typing import Iterable, List

# The model and its dimension are a matched pair. Changing one REQUIRES changing
# the other, and re-embedding everything already stored.
EMBED_MODEL: str = os.environ.get("TATIANA_EMBED_MODEL", "BAAI/bge-small-en-v1.5")
EMBED_DIM: int = int(os.environ.get("TATIANA_EMBED_DIM", "384"))

_model = None  # lazy singleton: model init is slow, so pay it once, on first use


def _get_model():
    """Load the embedding model once per process."""
    global _model
    if _model is None:
        try:
            from fastembed import TextEmbedding
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "fastembed is not installed. Install it on Python 3.11:\n"
                "    python -m pip install fastembed"
            ) from exc
        _model = TextEmbedding(model_name=EMBED_MODEL)
    return _model


def embed_batch(texts: Iterable[str]) -> List[List[float]]:
    """Embed many texts at once (much faster than one at a time).

    Returns a list of EMBED_DIM-length float vectors, one per input.
    Raises RuntimeError if the model returns an unexpected dimension.
    """
    items = [t if isinstance(t, str) else str(t) for t in texts]
    if not items:
        return []

    vectors = [[float(x) for x in v] for v in _get_model().embed(items)]

    for vec in vectors:
        if len(vec) != EMBED_DIM:
            # Deliberately fatal. See THE CONTRACT above: we do not reshape.
            raise RuntimeError(
                f"Embedding dimension mismatch: model '{EMBED_MODEL}' returned "
                f"{len(vec)} dims but EMBED_DIM is {EMBED_DIM}. Fix the model/dim "
                f"pair rather than truncating or padding."
            )
    return vectors


def embed(text: str) -> List[float]:
    """Embed a single text into an EMBED_DIM-length vector."""
    return embed_batch([text])[0]


def cosine(a: List[float], b: List[float]) -> float:
    """Cosine similarity between two embeddings, without requiring numpy."""
    if len(a) != len(b):
        raise ValueError(f"Cannot compare vectors of different dims: {len(a)} vs {len(b)}")
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)
