"""
TATIANA — live end-to-end demo: the REAL organs, the REAL brain, a REAL paper.

Everything built so far, wired together and driven by DOCS/FIRST DRAFT.pdf:

    pdf_processor   -> streams the actual paper off disk
    embeddings      -> real 384-d local geometry (free, no quota)
    librarian /
    canonicalizer /
    harvester /
    context_manager -> the four migrated organs, each a vertex of K
    router          -> Groq, tiered (8B triage / 70B reasoning)
    coherence       -> rho measured over K, with its guards
    visualize       -> the evolution written to complex_live.html

This is the "prove the loop" demonstration in its current honest form: the system
ingests, holds, binds, measures its own internal agreement, localises conflict,
and reasons remotely — all at $0.

It does NOT claim to solve Section 3. It shows the machinery running on real
mathematics and reporting its own state truthfully.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
import warnings

warnings.filterwarnings("ignore")

import console
console.setup()

from canonicalizer import Canonicalizer
from context_manager import ContextManager
from embeddings import embed
from harvester import KnowledgeCurator
from librarian import IntelligentLibrarian
from module_vertex import CoarseComplex
from pdf_processor import LocalProcessor
from router import CloudRouter, RouterError
from storage import DatabaseManager
from visualize import render

FIRST_DRAFT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "DOCS", "FIRST DRAFT.pdf"))
SESSION = "first-draft-session"


async def main() -> None:
    db_path = os.path.join(tempfile.gettempdir(), "tatiana_live_demo.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    db = DatabaseManager(db_path)

    try:
        router = CloudRouter()
    except RouterError as e:
        print(f"Cannot start: {e}")
        return

    # ---- 1. the four organs become vertices of K --------------------------
    librarian = IntelligentLibrarian(db, router)
    canonicalizer = Canonicalizer(db, router)
    curator = KnowledgeCurator(db, router)
    memory = ContextManager(db, router)

    K = CoarseComplex(bind_threshold=1.0, decay=0.34)
    for organ in (librarian, canonicalizer, curator, memory):
        K.register(organ)
    print(f"[1] registered {len(K.vertices)} organs as vertices of K: "
          f"{list(K.vertices)}")

    snaps = [K.snapshot("t0 — organs registered, all idle",
                        "Four organs exist but none holds anything, so none has a "
                        "position. rho is UNKNOWN — genuinely undefined, not zero.")]

    # ---- 2. stream the real paper ----------------------------------------
    proc = LocalProcessor()
    pages = [p["text"] async for p in proc.stream_extract_pdf(FIRST_DRAFT)
             if p["text"].strip()]
    print(f"[2] streamed {len(pages)} pages of FIRST DRAFT.pdf")

    # ---- 3. Librarian ingests; Working Memory records the goal ------------
    for i, text in enumerate(pages[:4]):
        librarian.hold_evidence(f"FIRST DRAFT p{i+1}", text, weight=1.0)

    db.update_working_memory_state(
        SESSION,
        current_project="FIRST DRAFT",
        current_file="FIRST DRAFT.pdf",
        current_goal="Solve Section 3: spectrum of the weighted Hodge-de Rham "
                     "Laplacian on 1-forms over CP^3",
        last_decision="Prove the loop rather than claim a correct proof")
    memory.sync_stalk(SESSION)

    K.co_activate("Librarian", "WorkingMemory", 1.0)
    r = K.report()
    print(f"[3] Librarian + WorkingMemory bound -> {r.summary()}")
    snaps.append(K.snapshot("t1 — Librarian ingests, WorkingMemory holds the goal",
                            "The retrieval organ is holding real pages of the paper and "
                            "working memory holds the stated goal. They bind and broadly "
                            "agree: both are 'about' this paper."))

    # ---- 4. Curator digests a different part; Canonicalizer joins ---------
    curator.hold("digest: weighted operator section", embed(" ".join(pages[7:])[:2000]))
    canonicalizer.hold("cluster: Kahler / Fubini-Study terms",
                       embed(" ".join(pages[:2])[:2000]))
    K.co_activate("Librarian", "Canonicalizer", 1.0)
    K.co_activate("Canonicalizer", "Curator", 1.0)
    r = K.report()
    print(f"[4] all four active            -> {r.summary()}")
    print(f"    worst edge: {r.worst_edge()}")
    snaps.append(K.snapshot("t2 — all four organs active and bound",
                            "Each organ holds a different facet of the same paper. "
                            f"Discord is real but modest; worst edge {r.worst_edge()}."))

    # ---- 5. one real reasoning call on the heavy tier ---------------------
    context_block = memory.get_context_block(SESSION)
    prompt = (
        "You are the Reasoning organ of a mathematical operating system.\n"
        f"{context_block}\n"
        "Given the following excerpt from the user's own paper, state in 3 short "
        "bullets what must be established to solve the eigenvalue problem. "
        "Say plainly if something is not determined by the excerpt.\n\n"
        f"EXCERPT:\n{' '.join(pages[7:])[:1500]}")
    try:
        answer = await router.query_frontier_brain(prompt, intent="reason")
        print("\n[5] 70B reasoning on the real excerpt:")
        for line in answer.strip().splitlines()[:8]:
            if line.strip():
                print("   ", line.strip()[:110])
    except RouterError as e:
        print(f"\n[5] reasoning call FAILED (reported, not hidden): {e}")

    # ---- 6. idle decay ----------------------------------------------------
    for _ in range(4):
        K.tick_decay()
    print(f"\n[6] after idle decay           -> {K.report().summary()}")
    snaps.append(K.snapshot("t3 — idle decay collapses the coalitions",
                            "Unreinforced coalitions decayed. Nobody is bound, so "
                            "agreement is undefined again."))

    out = render(snaps, os.path.join(os.path.dirname(__file__), "complex_live.html"))
    print(f"[7] visualisation: {out}")
    print(f"[8] budget: {router.budget.summary()}")
    print("\nmutation log:")
    for m in K.mutation_log:
        print("   ", m)

    db.close()


if __name__ == "__main__":
    asyncio.run(main())
