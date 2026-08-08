# WHY MOS NEEDS A MODEL OF COGNITION — WHAT, WHERE, AND HOW

*Written 2026-08-05 at the close of the retrieval-and-Tier-0 chapter. This is the **case**;
`THE_GENERATIVE_THOUGHT_MODEL.md` is the **workflow**. Read this one first.*

> **The argument here is not "brains are dynamic, so MOS should be too." That is a slogan.**
> The argument is that six specific measurements, each taken for a different reason, all failed in
> a way that points at the same missing component — and that they further constrain what that
> component has to look like. The evidence does the work.

Tags per §5ay: `[MEASURED]` · `[DERIVED]` · `[INFERRED]` · `[ENGINEERING CHOICE]` ·
`[OPEN HYPOTHESIS]` · `[SPECULATION]`.

---

## 1. THE QUESTION THE CHAPTER ANSWERED — WHICH WAS NOT THE ONE IT ASKED

**Asked:** does MOS's memory have a cover (overlapping contexts) or a partition (one home per
concept)?

**Answered:** nothing about that. Four instruments, four inconclusive results (§5az).

**But the four failures were not independent.** Each was diagnosed, and the diagnoses converge:

| attempt | proximate cause of failure | what it actually revealed |
|---|---|---|
| 1. global likelihood margin | ticks were top-k balls around one point ⇒ single-cause by construction | **nothing in the model decided what was being thought about** |
| 2. bimodality × arXiv labels | instrument blind below ~40% separation; label administrative | the structure sought is not at the scale the geometry expresses |
| 3. bimodality × citation labels | logical and geometric relations disagree | **memory needs more than one kind of edge** |
| 4. transitivity deficit | no setting passes both controls | the co-activation graph carries structure that is **not** geometric — and unreadable without knowing how it was generated |

**[DERIVED]** The common factor is not statistical. In every case the *data-generating process* —
how a "thought" came to contain the concepts it contained — was a fixed, memoryless, metric lookup.
Every question about structure was therefore a question about that lookup.

---

## 2. WHAT — THE THING THAT IS MISSING, STATED PRECISELY

MOS's tick has been:

```
    query  →  top-k nearest concepts  →  assembly
```

There is no state. Tick *t* and tick *t+1* are independent events. Nothing carries over, nothing
is attended to, nothing is inhibited, nothing is expected, nothing is surprising.

**[DERIVED]** That is not a simplified cognitive process. **It is the absence of one.** A lookup
table with a similarity metric is a retrieval index; a memory system is something that decides
*what to retrieve about*, and MOS has never contained that decision.

**The missing component: a generative process that produces assemblies over time.**

---

## 3. WHERE — THE EVIDENCE LOCATES THE LAYER

This is the part that is not a slogan. Each measurement constrains where the process must live.

### 3.1 It cannot live in the metric — [MEASURED]
- The pedestal is real and large: `‖μ̄‖² = 0.671`; two unrelated abstracts score cos ≈ 0.669.
- But the pedestal is a **thresholding** problem, not a **ranking** one — for a fixed query it is
  constant and cannot reorder. Removing it (centering, abtt) is worth **+4 points**; abandoning the
  absolute cutoff is worth **~140×**.
- Twelve diffusion/heat-kernel configurations: **none beats raw cosine.**

**[DERIVED]** Successive attempts to fix relevance by improving the *distance function* produced
diminishing returns that bottomed out around 4 points. The remaining gap is not a metric problem.

### 3.2 It cannot live in a single relation — [MEASURED], and this is the sharpest datum
Citation dependency ("this proof needs that lemma") and embedding similarity ("these texts read
alike") **agree only about 47% of the time** — recall@30 = 44–48% over 2266 author-asserted
dependencies.

**[DERIVED]** Two relations that both plainly matter to thought, and they disagree more than they
agree. **No single edge type can serve as memory.** This is the direct empirical warrant for the
multi-source edge model — semantic *plus* episodic *plus* temporal *plus* predictive *plus* task —
rather than a stylistic preference for richness.

### 3.3 It cannot live in the corpus — [MEASURED]
Attempt 1's generator would have returned "partition" on a corpus engineered to be **100%**
overlapping. `§5ap`'s stated premise (74% cross-listed) was, within the corpus, **10.7%**.

**[DERIVED]** Changing the data cannot fix a protocol whose answer is fixed before the data arrives.

### 3.4 But there *is* structure in the activity — [MEASURED], unexplained
The co-activation graph has a large transitivity deficit reproduced by **neither** a margin-
preserving null **nor** structure-free ball geometry. Both controls are clean; the effect is not.

**[SPECULATION]** its shape — near-universal rather than a minority of concepts — resembles a
continuum more than K discrete patches.

**[DERIVED]** Something real is present in *what co-activated with what*, and it is not a property
of the embedding. **That is a positive result pointing at the activity layer**, and it is currently
uninterpretable only because we do not control how the activity was generated.

### 3.5 And generation determines the verdict — [MEASURED], demonstrated
Identical data, identical fits, identical observed statistic; only the null's *generative shape*
changed: **p = 0.0200 (COVER) → p = 0.4500 (nothing)**.

**[DERIVED]** When the generating process is mis-specified, the conclusion inverts. This was
measured on our own data, not argued from theory. **It is the strongest single reason the generative
process must become an explicit, controlled part of the model rather than an implicit consequence of
a retrieval rule.**

> **Where the model must live, derived:** between input and assembly — the layer that maintains
> state across ticks, selects what is relevant by something other than distance, and produces
> assemblies as a *consequence* of that state rather than as a query result.

---

## 4. HOW — THE CONSTRAINTS THE EVIDENCE IMPOSES

Not a wish list. Each item is forced by something above.

**① Assemblies must be trajectories, not snapshots.** Forced by 3.1/3.3: `A(t)` and `A(t+1)` must
share concepts, lose some, gain others. Persistence, birth and death across ticks are observables
the old design discarded entirely.

**② Selection must be non-metric.** Forced by 3.1. A concept enters an assembly because activation
*reached* it — possibly along a path, possibly from context — not because it is near. Bridges then
occur for the reason brains have them: reachability, not proximity.

**③ Edges must be multi-relational.** Forced by 3.2 (the 47% figure). Semantic similarity becomes
one term among several, not memory itself.

**④ Assembly size must emerge.** Forced by honesty: `k = 24` is an **[ENGINEERING CHOICE]** whose
budget input is unmeasured. Under competition dynamics, width follows from the
inhibition/excitation balance. **This deletes the last hand-set constant standing after the
retrieval work** — the A17 test, passed.

**⑤ The generative process must be explicit and controllable.** Forced by 3.5. If a mis-specified
generator can invert a p-value from 0.02 to 0.45, the generator is not a detail.

**⑥ The model must be validated against something outside the question.** Forced by the entire
chapter. Four instruments produced numbers; all four numbers described the setup. **Internal
coherence is not evidence.**

---

## 5. THE TRAP THIS CREATES — AND WHY §4⑥ IS NOT OPTIONAL

The natural next move is: *simulate cognition, then observe what topology appears.* That inverts
"assume a cover, test for it" and is genuinely stronger.

**It is also Attempt 1's failure at ten times the scale.**

> A simulator produces the topology its rules imply. Spread activation over a graph built from
> embedding similarity and you recover the embedding's topology and call it emergent. Give the
> dynamics `K` attractor basins and you find `K` clusters.

**Simulation does not escape circularity. It moves it into the update rule, where it is harder to
see** — a simulator is complicated enough to hide its own assumptions, which a top-k ball was not.

**The only escape:** the model must reproduce **quantitative signatures of human memory it was not
fitted to** — serial position, semantic clustering, the fan effect, spacing, and above all the
**lag-CRP with forward asymmetry**, which is fine-grained, robust, and has no free parameter to hide
in. A model tuned toward a target topology will not produce it by accident.

**[OPEN HYPOTHESIS]** that MOS's representation can support a drifting temporal context at all. If
it cannot, the architecture needs rethinking — which is why that test is placed first and cheap.

---

## 6. WHAT THIS IS *NOT* A LICENCE FOR

- **Not biological realism for its own sake.** Spiking, oscillations, neurotransmitters, anatomy —
  excluded. None would change a number the model predicts; each adds parameters.
- **Not abandoning the topology programme.** Topology moves from *assumption to be validated* to
  *prediction of a validated model*. Tier 0's acceptance criterion carries over unchanged.
- **Not discarding the chapter's work.** The retrieval fix is the semantic edge term; `curveball`
  is the null for any co-activation claim; the `\ref` labels validate the semantic term and are a
  candidate input stream; `measure_open_triangles.py`'s calibration harness is now the acceptance
  test for future instruments.
- **Not novelty where there is none.** **[INFERRED]** Layer 1 is TCM/CMR; competition is ACT-R plus
  k-WTA; the dynamic graph is the successor representation; and the 𝕂/W split is Complementary
  Learning Systems. Borrow all of it. **The contribution is the sheaf formalisation over a
  well-motivated architecture, not the architecture.**

---

## 7. THE FALSIFIABLE COMMITMENTS

Written down now, so that being wrong is unambiguous later.

1. **A memoryless metric lookup cannot produce cover structure.** Already **[MEASURED]** — it
   returns partition by construction.
2. **A stateful generative process will produce assemblies whose co-activation graph is not a
   union of metric balls.** **[OPEN HYPOTHESIS]**, testable at G0.
3. **A drifting-context model will reproduce the lag-CRP with forward asymmetry.** **[OPEN
   HYPOTHESIS]**, the G1 gate. If it fails, the architecture is wrong.
4. **Assembly size will stabilise without being set.** **[OPEN HYPOTHESIS]**, and it deletes `k`.
5. **Whatever topology appears will be a property of the dynamics, not of the embedding.** Testable
   by re-running with a shuffled embedding: the behavioural signatures should survive, the topology
   should change. **[OPEN HYPOTHESIS]**, and the cleanest single test of the whole thesis.

---

## 8. THE ONE-PARAGRAPH VERSION

MOS spent this chapter asking what shape its retrieval events had. Four instruments returned four
inconclusive answers, and the diagnoses converged: the events were produced by a memoryless metric
lookup, so every question about their structure was a question about that lookup. The measurements
further show the fix is not a better metric — twelve diffusion variants beat nothing, and removing
the pedestal is worth 4 points against 140× for abandoning the threshold — and that no single
relation can serve as memory, since citation and similarity agree only 47% of the time. Meanwhile
the co-activation record carries real structure that neither margins nor geometry explain, and a
mis-specified generative null was shown to invert a verdict from p = 0.02 to p = 0.45. Together
these locate the missing layer precisely: **between input and assembly, a stateful process that
decides what is being thought about.** Memory is not the geometry; **the geometry is the shadow the
activity leaves behind.**

---

**Next:** `THE_GENERATIVE_THOUGHT_MODEL.md` for the phased workflow, gates, prior art and compute
budget. `TATIANA_LOGBOOK.md` §5az–§5ba for the chapter record and the cold-start handoff.
