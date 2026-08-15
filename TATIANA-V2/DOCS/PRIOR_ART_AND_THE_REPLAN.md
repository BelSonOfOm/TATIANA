# PRIOR ART, AND THE REPLAN IT FORCES

*Written 2026-08-04, after Tier 0 returned a verdict that was decided by the experiment's own
design rather than by the data. Companion to `THE_RETRIEVAL_PROBLEM.md`; that document fixed
retrieval, this one fixes the experiment that consumes it.*

> **⚠️ Every citation below comes from web-search summaries, NOT from reading the papers.** Two are
> load-bearing and must be verified against the actual text before anything is built on them: the
> Gotelli Type-I-error result (§1) and the Lattice Effect (§5). This file follows the logbook's
> standing rule that unsearched citations are flagged; these are *searched* but *unread*.

---

## 0. WHAT WENT WRONG, IN ONE PARAGRAPH

Tier 0 was run on 3000 ticks, where each tick was "one query sentence and its 24 nearest concepts."
A top-k ball around a single query point has **one centre**, so it is a single-cause event by
construction. Tier 0's question is "one cause per tick, or several?" — so the generator answered the
question before the data did. The verdict (`NO EVIDENCE FOR COVER`, p = 0.45) would have come out
the same on a corpus engineered to be 100% overlapping. **It is a fact about the protocol, not about
MOS or the corpus.**

Everything below is what the literature says about that class of mistake, and what we do instead.

---

## 1. ECOLOGY — NULL MODELS FOR BINARY CO-OCCURRENCE MATRICES

**The match is exact.** Species × islands presence/absence is our concepts × ticks matrix. The
question — are the observed co-occurrences more structured than chance? — is the same question, and
it has been fought over since Connor & Simberloff (1979).

**What transfers, and it validates R3:**

> "The three models that maintain **fixed row sums** are invulnerable to Type I errors."
> — Gotelli, *Null Model Analysis of Species Co-Occurrence Patterns* (Ecology, 2000)

Our margin-matched null (`cover.py: _simulate_mixture_margin`) is exactly the fixed-row-sum class.
The legacy null (free margins, independent Bernoulli emissions) is in the class documented to
inflate false positives. **R3 was not a nicety; it is the documented precondition for the test to
mean anything.**

**What it also exposes — a flaw in my implementation.** Sampling uniformly from the set of
fixed-margin binary matrices is a known hard problem, and naive samplers are biased
(*Non-Uniform Sampling of Fixed Margin Binary Matrices*, arXiv:2007.15043). My Gumbel-top-k sampler
hits the right *support* (exactly k ones per row) but does **not** sample it uniformly — I flagged
this as an approximation without knowing there was a literature on the failure mode. The mature
answers are the **swap algorithm** and the faster **curveball / "Babe Ruth" algorithm**
(Strona et al., *Nature Communications* 2014), which is proven unbiased.

**★ AND THIS IS WHERE THE THERMODYNAMICS FINALLY EARNS ITS PLACE.** The fixed-margin ensemble *is*
the maximum-entropy distribution over binary matrices subject to margin constraints — Jaynes's
derivation, the partition function doing real work as a normaliser with a variational
characterisation, not as a relabelled softmax denominator. Charbel's heat-map instinct was pointed
at the metric, where it provably could not help (softmax is monotone, it cannot reorder). Pointed at
the **null**, it is exactly right, and ecology supplies the sampler that the physics does not.

**Action:** replace Gumbel-top-k with curveball. ~60 lines, no new theory, removes hand-waving.

---

## 2. GEOGRAPHY — THE TICK PROBLEM HAS A NAME: MAUP

The **Modifiable Areal Unit Problem** is the sensitivity of a measured pattern to the *size* (scale
problem) and *shape* (aggregation problem) of the unit you aggregate over. The literature's warning:
results "vary artifactually with chosen aggregations."

**Substitute "tick" for "areal unit" and that is our bug, exactly.** A small unit (one query's 24
neighbours) contains one cause. A larger or differently-shaped unit could contain several. We picked
one unit, once, and read the answer off it.

**What transfers:** the standard remedy is **never pick one grain — sweep it and report the
sensitivity.** A cover that appears at one tick size and vanishes at others is an artifact. One that
persists across sizes is structure. This is the same conclusion the accumulation-filtration idea was
reaching for, arriving from a completely different field.

**Action:** grain `k` becomes a swept parameter, never a constant. Report signal vs `k`.

---

## 3. NETWORK SCIENCE — OVERLAPPING COMMUNITY DETECTION

The cover-vs-partition question is routine here. Most relevant: **OSLOM**, which scores each
community against a configuration-model null, **adaptively returns overlapping communities**, and
identifies "background nodes" not significantly attached to anything.

**What transfers:** per-community significance instead of one global verdict. Our
noisy-OR-vs-mixture likelihood contest gives a single number for the whole corpus; a method that
says *which* concepts overlap and how strongly is far more diagnostic, and degrades gracefully when
most of the corpus is partition-like (which ours is — 10.7%).

---

## 4. BAYESIAN NONPARAMETRICS — OUR MODEL COMPARISON, ALREADY SOLVED

| ours | theirs |
|---|---|
| mixture (one cause per tick) = **partition** | Dirichlet Process mixture — every point in exactly one cluster |
| noisy-OR (several causes) = **cover** | **Indian Buffet Process** — each point carries multiple latent features |

Tier 0's question is IBP-vs-DP in different clothing (Griffiths & Ghahramani).

**What transfers, and it kills a hand-set constant:** the IBP **infers the number of features**
rather than requiring `K`. Our `K = 6` was guessed from the category count, while the data has
~1074 distinct retrieval neighbourhoods — so both models were badly underfit and we may have been
comparing two equally bad approximations. That was listed as candidate (c) for the null result and
it is now removable rather than merely testable.

---

## 5. TDA — OUR §4.3 HAZARD IS CALLED THE LATTICE EFFECT

Mapper builds a cover and takes its nerve: structurally the same object as Constructions 4 and 5.
The failure predicted from reading `cover.py` is documented:

> "On dense covers, the nerve can capture the **geometry of the cover itself** rather than the
> underlying manifold topology, a phenomenon termed the **Lattice Effect**."

That is precisely "ball structure could read as cover structure." Established remedies: **multiscale
Mapper** (towers of covers, stable under cover and filter perturbation) and **parameter perturbation
analysis** as a validation requirement, not an optional extra.

**What transfers:** the geometric control (`make_assemblies.py --null geometric`) was the right
instinct and is standard practice. It should be run at every grain, not once.

---

## 6. ★ THE REFRAME THAT MAKES THIS CHEAP

The literature above says sweep the grain and perturb the parameters — which multiplies the cost of
a test that already took ~90 minutes of compute per configuration on a 4-core machine. That is
unaffordable. So the design has to change, not just the parameters.

**The insight: we have been asking the tick-side question when the concept-side question is
equivalent, cheaper, and immune to the grain problem.**

- **Tick-side (what Tier 0 asks):** "does this tick have one cause or several?"
  → Broken by grain: a single-centre ball has one cause by construction.
- **Concept-side (what a cover actually means):** "does this concept belong to more than one
  context?"
  → A cover is a family of overlapping patches. *Overlapping* means some element lies in two
    patches. **That is the concept-side statement.** It is the definition, not a proxy.

**Why the concept-side question survives our broken ticks.** Take concept `c` and collect every tick
it fired in. Each of those ticks is a ball centred somewhere near `c`. If `c` is mono-topical, all
those balls sit in one region and their assemblies look alike. If `c` genuinely bridges two areas,
queries from *both* areas retrieve it, and the assemblies split into two dissimilar groups.

**The multi-cause structure appears ACROSS ticks, not WITHIN one.** So single-centre ticks are fine
for this question. Problem (a) dissolves.

**And it comes with ground truth for free.** Cross-listed papers are the concepts that *should* be
multi-context. So this becomes a labelled detection problem — exactly the move that settled the
retrieval question with 2266 `\ref` labels, applied again:

> Does the instrument rank cross-listed concepts above single-listed ones on a
> multi-context score?

That is an **instrument validation on real data with known positives**, not an unfalsifiable global
verdict. And it costs no EM at all.

**The honest limit:** cross-listing is a high-precision, low-recall label (as `\ref` was). A
single-listed paper may still bridge topics. So it supports recall-style metrics and AUC, never
"this concept is definitely not a bridge."

---

## 7. IMPLEMENTATION PLAN

Ordered so that **something informative exists after Phase B**, even if C and D never run.

### PHASE A — correctness, no significant compute
| # | change | file | cost |
|---|---|---|---|
| A1 | Replace Gumbel-top-k with **curveball** for fixed-margin sampling | `cover.py` | ~60 lines |
| A2 | Measure EM convergence; loosen `tol` / cap `iters` from evidence, not habit | `cover.py` | measurement |
| A3 | Make grain `k` a swept parameter everywhere | `make_assemblies.py` | ~10 lines |

A2 matters more than it looks: the fold fits converged in ~6.8 s while null draws took ~13 min,
which suggests the EM is running its full 200/300 iterations on simulated data. If a looser `tol`
converges to the same answer, that is most of the cost gone.

### PHASE B — the cheap instrument (the new centrepiece)
| # | change | cost |
|---|---|---|
| B1 | Per-concept **multi-context score**: collect each concept's ticks, measure whether its assemblies split into dissimilar groups | seconds |
| B2 | Label concepts by cross-listing (2+ of our six categories) | free, in the manifest |
| B3 | Report AUC / recall@k of the score against those labels, plus the geometric-null control | seconds |

**No EM. No bootstrap. Minutes on an old laptop.** If B fails — the score cannot separate
cross-listed concepts from mono-listed ones — then nothing downstream is worth running, and that is
a real finding delivered cheaply.

### PHASE C — the MAUP sweep
Repeat B at `k ∈ {8, 16, 24, 48}` and on the geometric null at each. Signal that does not persist
across grain is an artifact. Still EM-free: **minutes**.

### PHASE D — the expensive test, ONLY if B and C justify it
Tier 0 with the curveball null, at the grain(s) where B/C found signal, `B = 39`, `folds = 3`,
`jobs = 2`. Budget it in advance and checkpoint.

---

## 8. RULES FOR NOT BURNING THE MACHINE

Learned the hard way: 4 cores, 5.9 GB, and a lid that closes.

1. **`jobs = 2`, never 4.** Leave headroom so the machine stays usable.
2. **Checkpoint every draw to disk.** The 2026-08-04 run lost nothing to sleep only by luck; a
   killed job currently loses everything. A long job whose partial progress is worth nothing is a
   bug in the job (5ap's own lesson, unlearned).
3. **Resumable by construction** — re-running skips completed draws.
4. **Measure one full unit of work before extrapolating.** The 15-min estimate that became 90 came
   from timing 2 draws and multiplying. Time one *complete* draw next time.
5. **Cheap phases first**, so an interrupted evening still produces a result.
6. **Sleep kills wifi and compute both.** Anything fetching from arXiv must be resumable
   (`extract_refs.py` already caches; `build_corpus.py` does not — fix or accept).

---

## 9. WHAT THIS MEANS FOR THE PROJECT'S CLAIMS

Stated plainly because it affects what can be written up:

**Cover detection is not novel.** Overlapping-vs-disjoint latent structure has mature machinery in
at least four fields. MOS cannot claim contribution there, and any paper that frames "we detect
covers" as the advance will be met with IBP, OSLOM, and forty years of ecology.

**What remains genuinely MOS's:** the sheaf structure over the cover (restriction maps, γ(ν),
what crystallises into 𝕂), the growth law driven by free energy, the engine that accumulates
history rather than recomputing from data, and the two-complex 𝕂/W architecture. **Those are the
contribution. The cover is infrastructure — and infrastructure should be borrowed, not invented.**

---

## 10. SOURCES

- Strona et al., *A fast and unbiased procedure to randomize ecological binary matrices with fixed
  row and column totals* — https://www.nature.com/articles/ncomms5114
- Gotelli, *Null Model Analysis of Species Co-Occurrence Patterns* (Ecology 2000) —
  https://esajournals.onlinelibrary.wiley.com/doi/10.1890/0012-9658(2000)081%5B2606:NMAOSC%5D2.0.CO;2
- *The Babe Ruth Algorithm* (curveball) — https://arxiv.org/pdf/1404.3466
- *Non-Uniform Sampling of Fixed Margin Binary Matrices* — https://arxiv.org/pdf/2007.15043
- EcoSimR — https://www.uvm.edu/~ngotelli/EcoSim/EcoSim.html
- *Overlapping Community Detection in Networks: The State-of-the-Art* —
  https://www.cs.rpi.edu/~szymansk/papers/acm-cs.13.pdf
- *Significance-based community detection in weighted networks* (JMLR) —
  https://jmlr.org/papers/volume18/17-377/17-377.pdf
- Griffiths & Ghahramani, *The Indian Buffet Process: An Introduction and Review* —
  https://cocosci.princeton.edu/tom/papers/indianbuffet.pdf
- Griffiths & Ghahramani, *Infinite Latent Feature Models and the IBP* (JMLR) —
  https://mlg.eng.cam.ac.uk/pub/pdf/GriGha11.pdf
- *The Modifiable Areal Unit Problem and Implications for Landscape Ecology* —
  https://www.researchgate.net/publication/226397878_The_Modifiable_Areal_Unit_Problem_and_Implications_for_Landscape_Ecology
- *A Three Axis Evaluation Framework for Mapper Algorithms* — https://arxiv.org/pdf/2606.21688
- *A comprehensive review of the Mapper algorithm (2007–2025)* —
  https://www.researchgate.net/publication/398378892_A_comprehensive_review_of_the_mapper_algorithm_a_topological_data_analysis_technique_and_Its_applications_across_various_fields_2007-2025
