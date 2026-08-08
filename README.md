# TATIANA / MOS — a Mathematical Operating System

A persistent, structured memory for mathematical research, built so that a small context sent to a
cheap language model does the work a large context sent to an expensive one usually does.

MOS ingests papers, holds what it reads as a **growing geometric object** rather than a vector
index, measures how coherent its own current state is, and consolidates what survives verification
into a permanent store. The claim it is built to test is that **structured, accumulated memory beats
a bigger context window** — measured as a gap that widens with experience, not as a single-shot
score.

> **Status: research prototype under active development.** Parts of the architecture are built and
> tested; parts are specified and not yet built; some earlier claims have been measured and
> refuted. The distinction is tracked honestly in `DOCS/TATIANA_LOGBOOK.md`, which is the project's
> real documentation.

---

## The idea in one paragraph

Memory here is a **cognitive state space** `M = (C, F, s)`: a simplicial complex `C` whose vertices
are concepts, a cellular sheaf `F` assigning each concept a local state, and `s` the current
globally-coherent thought. Concepts that are retrieved together get joined by an edge; concepts that
fire together in one assembly get a filled triangle. The **discord** `ρ` measures how far the
current state is from gluing into a global section — high `ρ` means the system is holding views that
cannot be reconciled, and it gates a two-mode RESOLVE/EXPLORE controller. Memory is two-timescale: a
fast working complex `W` and a slow crystallised store `𝕂`, joined by the sheaf adjunction
`ι_! ⊣ ι* ⊣ ι_*`, with consolidation gated on a three-valued verification verdict. That two-store
split is **Complementary Learning Systems**, arrived at independently; the possible contribution is
the sheaf formalisation, not the architecture.

## What is actually built

- **C++ engine** (`MOS/`) — `CognitiveState`, an `OSKernel` executing FlatBuffer operad DAGs over
  IPC, operators (Search / Compute / Reason / Respond / Verify / Context), `ConceptStore` as `𝕂`
  over concepts with its sheaf, `Complex2` with a matrix-free Hodge split, Householder restriction
  maps, rank-`k` SPD stalks, Bures–Wasserstein with Woodbury low-rank updates, and a closed
  consolidation loop.
- **Python organ layer** (`MOS/python/`) — the authoritative `ρ` implementation, expected-precision
  estimation, local CPU embeddings, PDF ingestion, a tiered free-tier LLM router, and the four
  organs as vertices of the coarse complex.
- **A measurement suite** — corpus construction, reference extraction, retrieval evaluation against
  2266 author-asserted dependencies, and a calibration harness that any new instrument must clear.

## What has been measured, including the negatives

The project records refutations as carefully as results. A few:

| finding | number |
|---|---|
| the engine's relevance threshold admits, of true dependencies | **0.31%** |
| rank-based retrieval at the same width | **46.6%** |
| embedding pedestal — unrelated abstracts score cosine ≈ | **0.669** |
| diffusion / heat-kernel retrieval, 12 configurations | **none beats raw cosine** |
| citation dependency vs embedding similarity agree | **~47%** |
| a mis-specified generative null, on identical data | p = 0.02 → **p = 0.45** |

That last row is why the generative process is now an explicit part of the model rather than an
implicit consequence of a retrieval rule.

## Method

1. **No measurement without a positive control.** Four artifacts were caught this way; the fourth
   before it became a reported result.
2. **Any instrument must clear synthetic partition + synthetic cover + a structure-free control at
   one shared parameter setting** before it touches real data.
3. **Every claim carries an epistemic-status tag** — `[MEASURED]`, `[DERIVED]`, `[INFERRED]`,
   `[ENGINEERING CHOICE]`, `[OPEN HYPOTHESIS]`, `[SPECULATION]`.
4. **New mathematics earns its place only if it changes a number the engine prints, or deletes a
   decision a human was making by hand.**
5. **Prior art before implementation.** Literature is checked at each gate, before building.

## Repository

```
MOS/          the engine — C++ core, Python organ layer, measurement suite
DOCS/         the real documentation (start with TATIANA_LOGBOOK.md)
POSTER/       presentation material
```

**Reading order for the current state of the work:**

1. `DOCS/TATIANA_LOGBOOK.md` — the living journal. Decisions, refutations, and dead ends. §5ba is a
   cold-start brief; §7 is the road to a working prototype.
2. `DOCS/WHY_A_MODEL_OF_COGNITION.md` — why the architecture needs a generative layer, argued from
   six measurements rather than from analogy.
3. `DOCS/SPEC_GROWTH_ADDRESS_AND_DYNAMICS.md` — the current specification.
4. `DOCS/MEMORY_MODEL_TWO_COMPLEX.md` — the `𝕂`/`W` split and the adjunction.

## Attribution

The components are standard and are cited as such: the sheaf Laplacian and its Anderson–Morley
normaliser (Hansen–Ghrist), contextuality as a sheaf-cohomological obstruction
(Abramsky–Brandenburger), Bures–Wasserstein geometry, combinatorial Hodge theory, the successor
representation (Dayan), Complementary Learning Systems (McClelland–McNaughton–O'Reilly), and
temporal-context models of recall (Howard–Kahana, Polyn–Norman–Kahana). **The interlocking system is
the contribution; the pieces are borrowed on purpose.**

"A genuine simulation of intelligence" is an overclaim and is not made here. The defensible framing
is *a coherence-gated orchestration architecture with persistent structured memory.*
