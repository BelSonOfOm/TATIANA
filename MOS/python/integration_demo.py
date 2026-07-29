"""
TATIANA — end-to-end integration demo on REAL content.

Wires together every piece built so far and drives it with actual text from
DOCS/FIRST DRAFT.pdf:

    pdf_processor  ->  real pages streamed off disk
    embeddings     ->  real 384-d local geometry (no API quota)
    module_vertex  ->  organs occupying vertices of the coarse complex K
    coherence      ->  rho measured over K, with its guards
    visualize      ->  the whole evolution written to complex_real.html

The point is to show rho responding to GENUINE semantic content rather than to
synthetic random vectors: when the organs are reading the same mathematics they
agree, and when one of them wanders off-topic the discord is measurable and the
guilty edge is named.
"""

from __future__ import annotations

import asyncio
import os
import warnings

warnings.filterwarnings("ignore")

from embeddings import embed
from module_vertex import CoarseComplex, ModuleVertex
from pdf_processor import LocalProcessor
from visualize import render

FIRST_DRAFT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "DOCS", "FIRST DRAFT.pdf"))


class Organ(ModuleVertex):
    """A generic organ for the demo (the real ones migrate one at a time)."""

    def __init__(self, name: str, ops):
        super().__init__(name)
        self._ops = list(ops)

    def operators(self):
        return self._ops


async def main() -> None:
    if not os.path.exists(FIRST_DRAFT):
        print(f"FIRST DRAFT.pdf not found at {FIRST_DRAFT}")
        return

    # 1. Stream the real paper off disk.
    proc = LocalProcessor()
    pages = []
    async for page in proc.stream_extract_pdf(FIRST_DRAFT):
        if page["text"].strip():
            pages.append(page["text"])
    print(f"[1] streamed {len(pages)} non-empty pages from FIRST DRAFT.pdf")

    # 2. Build the coarse complex.
    K = CoarseComplex(bind_threshold=1.0, decay=0.34)
    librarian = Organ("Librarian", ["SearchOp"])
    reasoner = Organ("Reason", ["ReasonOp"])
    verifier = Organ("Verify", ["VerifyOp"])
    for o in (librarian, reasoner, verifier):
        K.register(o)

    snaps = [K.snapshot("t0 — organs idle",
                        "No organ holds anything yet, so no organ has a position. "
                        "rho is UNKNOWN — not high, not low, genuinely undefined.")]

    # 3. Librarian and Reason both read the SAME mathematics (the geometry setup).
    geometry = " ".join(pages[:3])[:2000]
    librarian.hold("FIRST DRAFT: geometric setup", embed(geometry))
    reasoner.hold("Kahler/Fubini-Study reasoning", embed(geometry))
    K.co_activate("Librarian", "Reason", 1.0)
    snaps.append(K.snapshot("t1 — Librarian+Reason on the same material",
                            "Both organs are reading the same geometry section. They bind, "
                            "and their positions nearly coincide: low discord."))
    print(f"[2] same-material bind      -> {K.report().summary()}")

    # 4. Verify joins, reading the operator section — related but distinct.
    operator_sec = " ".join(pages[7:])[:2000]
    verifier.hold("weighted Hodge operator section", embed(operator_sec))
    K.co_activate("Reason", "Verify", 1.0)
    snaps.append(K.snapshot("t2 — Verify joins on a related section",
                            "Verify reads the weighted-Laplacian section: same paper, "
                            "different sub-topic. Mild, honest disagreement appears."))
    print(f"[3] related-section bind    -> {K.report().summary()}")

    # 5. Verify wanders completely off-topic. Discord should spike and be localised.
    verifier.release()
    verifier.hold("off-topic", embed(
        "A recipe for lemon cake with butter, sugar and three eggs."))
    r = K.report()
    snaps.append(K.snapshot("t3 — Verify goes off-topic",
                            "Verify is now holding something semantically unrelated. "
                            f"Discord rises and the guilty edge is named: {r.worst_edge()}."))
    print(f"[4] off-topic organ         -> {r.summary()}")
    print(f"    worst edge = {r.worst_edge()}   <- where RESOLVE would be aimed")

    # 6. Verify returns to the paper; conflict resolves.
    verifier.release()
    verifier.hold("back on task", embed(operator_sec))
    snaps.append(K.snapshot("t4 — Verify returns to the paper",
                            "Conflict resolved: the organ is back on the mathematics."))
    print(f"[5] resolved                -> {K.report().summary()}")

    # 7. Idle decay dissolves the coalitions.
    for _ in range(4):
        K.tick_decay()
    snaps.append(K.snapshot("t5 — idle decay collapses coalitions",
                            "Unreinforced coalitions decayed away. Back to UNKNOWN, "
                            "because nobody is talking again."))
    print(f"[6] after decay             -> {K.report().summary()}")

    out = render(snaps, os.path.join(os.path.dirname(__file__), "complex_real.html"))
    print(f"\n[7] visualisation written: {out}")
    print("\nmutation log:")
    for m in K.mutation_log:
        print("   ", m)


if __name__ == "__main__":
    asyncio.run(main())
