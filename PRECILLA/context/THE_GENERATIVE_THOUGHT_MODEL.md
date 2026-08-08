# THE GENERATIVE THOUGHT MODEL — THE WORKFLOW

*Opened 2026-08-05, immediately after Tier 0 closed inconclusive (§5az). This is the plan for the
next phase of MOS: stop asking what shape retrieval events have, and start modelling why they
happen.*

---

## 0. HOW TO READ THIS FILE

Every load-bearing claim carries an epistemic-status tag, the convention adopted in §5ay:

`[MEASURED]` · `[DERIVED]` · `[INFERRED]` · `[ENGINEERING CHOICE]` · `[OPEN HYPOTHESIS]` ·
`[SPECULATION]`

⚠️ **All citations below are from model knowledge and were NOT searched this session.** They are
named so they can be found, not quoted as authority. Verify before any bibliography — the logbook's
standing rule.

**This document is a plan, not a result.** Nothing in it has been built. Read §2 before §5; the trap
described there is the reason most of the structure exists.

---

## 1. WHY THE PIVOT — WHAT THE RETRIEVAL WORK ACTUALLY ESTABLISHED

Four Tier-0 instruments, four inconclusive results, every failure diagnosed (§5az). The pattern
underneath all four:

> Every attempt asked **"given these retrieval events, what shape do they have?"**
> A brain model owes the prior question: **"why did these retrieval events happen?"**

**[MEASURED]** The concrete finding that forces this: MOS's retrieval was
`query → top-k nearest neighbours → assembly`. A top-k ball has one centre, so every assembly was
single-cause **by construction**, and Tier 0's cover-vs-partition question was answered by the
generator before any data was seen. It would have returned "partition" on a corpus engineered to be
entirely overlapping.

**[DERIVED]** That is not a bug in the statistic. It is a statement about the architecture: **the
geometry of a static embedding is not a sufficient foundation for a cognitive architecture.** There
is no similarity metric that fixes it, because the problem is not which concepts are near each
other — it is that nothing in the model decides *what the system is thinking about*.

**The retrieval work was not wasted.** It located the missing layer precisely, and it left behind
instruments that the next phase needs (§8).

---

## 2. ⚠️ THE CENTRAL TRAP — READ THIS BEFORE BUILDING ANYTHING

The proposed inversion is:

```
    OLD:  assume a cover  →  test for it
    NEW:  simulate cognition  →  observe the topology that appears
```

That is genuinely stronger. **It is also the exact failure mode of Attempt 1, at ten times the
scale.**

> **A simulator produces the topology its rules imply.**
>
> If activation spreads over a graph built from embedding similarity, you will recover the
> embedding's topology and call it an emergent property of cognition. If the dynamics are written
> with `K` attractor basins, you will find `K` clusters. If the update rule blends two contexts
> whenever they co-occur, you will find overlap.

Attempt 1 failed because a single-centre ball is single-cause by construction. A simulator whose
transition rule encodes the answer is the same error with more code and more conviction — and it is
*harder* to catch, because a simulator is complicated enough to hide its own assumptions.

**Simulation does not escape circularity. It relocates it into the update rule.**

There is exactly one way out, and the whole plan is organised around it.

---

## 3. THE ESCAPE — EXTERNAL VALIDATION BEFORE ANY TOPOLOGY IS READ

> **The simulator must reproduce quantitative signatures of human memory that it was NOT fitted to.
> Only then is its emergent topology a prediction rather than a restatement of its own rules.**

This is the analogue of the positive-control rule that closed Tier 0, moved up a level. There it
was: *no measurement is reportable without a positive control*. Here it is: **no topology is
reportable without behavioural validation.**

Why this works: the behavioural signatures below are **measured in humans, decades old, robust, and
have nothing to do with simplicial complexes.** A dynamical rule tuned to produce a particular
topology will not incidentally produce a lag-CRP with the right forward asymmetry. If the simulator
gets those right *without* being fitted to them, its degrees of freedom have been constrained by
something outside the question being asked — which is precisely what all four Tier-0 attempts
lacked.

**Hard rule, adopted now, before there is any temptation to break it:**

```
No claim about emergent topology until the validation battery in §6 passes.
Not "mostly passes". Not "passes after tuning to it". Passes, on held-out signatures.
```

---

## 4. PRIOR ART — DO NOT REINVENT ANY OF THIS

§5aw's lesson applied again: cover detection turned out to be solved in four other fields, and we
burned weeks re-deriving it. Cognitive architecture is a *much* older field than topological data
analysis. ⚠️ All unsearched.

### 4.1 Context-driven retrieval — this IS the proposed Layer 1
- **TCM, Temporal Context Model** (Howard & Kahana). A slowly drifting context vector cues
  retrieval; retrieved items update the context. That is exactly `context state → attention →
  activation → assembly`, formalised, and it **predicts the temporal contiguity effect** (§6.2)
  rather than assuming it.
- **CMR, Context Maintenance and Retrieval** (Polyn, Norman & Kahana). TCM plus source/task context
  — gives the "task relevance" edge component for free.
- **SAM, Search of Associative Memory** (Raaijmakers & Shiffrin). Cue-dependent sampling and
  recovery, with a stopping rule.

**These are not competitors to MOS. They are the missing Layer 1, already written down and already
validated against human data.** Starting from TCM/CMR rather than from scratch converts §6 from "we
hope this works" into "we are reproducing known results, then extending."

### 4.2 Activation and competition
- **ACT-R declarative memory** (Anderson). Base-level activation with power-law decay, plus
  spreading activation from the current goal, plus noise. Predicts the **fan effect** (§6.4).
- **Hopfield networks / modern Hopfield.** Assemblies as attractors; the modern variant is
  mathematically attention, which is a useful bridge if the "attention" state variable is ever
  implemented with softmax.
- **k-winners-take-all** and global inhibition — the standard competition mechanism.

### 4.3 The 𝕂/W split is a rediscovery, and that is good news
- **Complementary Learning Systems** (McClelland, McNaughton & O'Reilly). A fast hippocampal store
  for episodes, a slow neocortical store for structure, with consolidation between them.

**[INFERRED]** MOS's crystallised-𝕂 / working-W architecture is CLS. That is not a problem — it means
decades of constraints, failure modes and empirical targets already exist for it, and the sheaf
adjunction `ι_! ⊣ ι* ⊣ ι_*` may be a genuinely new *formalisation* of a well-motivated architecture.
**That is a much better paper than "we invented a two-store memory."**

### 4.4 The dynamic graph
- **Successor Representation** (Dayan; Stachenfeld, Botvinick & Gershman). `M = (I − γT)⁻¹` — the
  expected discounted future occupancy under a transition policy. **This is precisely "activation
  history → weighted dynamic graph"**, it is learnable online by TD, and it has a known relationship
  to place/grid cell structure.
- **Predictive coding / free energy** (Friston). Already inside MOS via `F_MOS` and the `π_e`
  derivation, so the new dynamics should hook into the existing free energy rather than run a
  parallel objective.

### 4.5 Classic effects the model must respect
Bousfield (semantic clustering), Murdock (serial position), Kahana (lag-CRP), Anderson (fan effect),
Ebbinghaus/Cepeda (spacing), Wickens (release from PI).

---

## 5. THE ARCHITECTURE

### 5.1 State — every variable must earn its place

The A17 discipline applies with full force here, because **every state variable is a new knob**, and
a model with fifteen free parameters can produce any topology you like. Each variable must either
change a number the model predicts, or delete a decision currently made by hand.

| variable | symbol | what it does | earns its place by |
|---|---|---|---|
| activation | `a ∈ ℝᴺ` | current excitation per concept | it *is* the assembly |
| context | `c ∈ ℝᵈ` | slowly drifting recent history | predicts lag-CRP (§6.2) |
| working memory | `WM` | small capacity buffer, recent winners | predicts recency + capacity limits |
| fatigue / adaptation | `φ ∈ ℝᴺ` | recently-active concepts are suppressed | **without it the model gets stuck in one attractor forever** |
| base-level strength | `B ∈ ℝᴺ` | long-run frequency + recency of use | predicts practice and spacing effects |
| goal / task context | `g` | the current task's bias | predicts source clustering (CMR) |
| inhibition | `λ` | global competition strength | sets assembly size **without a hand-set `k`** |

> **★ NOTE WHAT THE LAST ROW DELETES.** Assembly width is currently the hand-set `k = 24`
> (**[ENGINEERING CHOICE]**, §10.7 of `THE_RETRIEVAL_PROBLEM.md`). Under competition dynamics,
> assembly size **emerges** from the inhibition/excitation balance. That is one hand-made decision
> removed, which is exactly the A17 test — and it is the single cleanest argument that this
> architecture is an improvement rather than an elaboration.

**Explicitly NOT modelled**, so the scope does not drift: spiking, neurotransmitters, cortical
layers, anatomical regions, oscillations. **[ENGINEERING CHOICE]** — none of them would change a
number this model predicts, and each would add parameters.

### 5.2 The tick loop

```
    external input  x_t   (may be empty — the model must also think unprompted)
             │
             ▼
    ┌─ cue formation ────────────────────────────────────────────┐
    │   cue = α·x_t  +  β·c_{t-1}  +  γ·g_t                      │
    └────────────────────────────────────────────────────────────┘
             │
             ▼
    ┌─ activation spread (recurrent, a few inner iterations) ─────┐
    │   a ← σ( W·a  +  cue  +  B  −  λ·Σa  −  φ )                │
    └────────────────────────────────────────────────────────────┘
             │
             ▼
    ┌─ competition ──────────────────────────────────────────────┐
    │   winners = concepts surviving k-WTA / threshold            │
    │   ASSEMBLY A(t) = winners        ← EMERGENT, not top-k      │
    └────────────────────────────────────────────────────────────┘
             │
             ▼
    ┌─ update ───────────────────────────────────────────────────┐
    │   Hebbian:  ΔW_ij = η·a_i·a_j − ζ·W_ij                     │
    │   context:  c_t = ρ·c_{t-1} + β·f(A(t)),  ‖c_t‖ = 1        │
    │   fatigue:  φ ← κ·φ + a                                     │
    │   base:     B_i ← ln Σ_k (t − t_k)^(−d)                    │
    │   WM:       push winners, evict oldest beyond capacity      │
    └────────────────────────────────────────────────────────────┘
```

**Three properties this has and the old pipeline did not:**

1. **Assemblies are trajectories, not snapshots.** `A(t)` and `A(t+1)` share concepts, lose some,
   gain others. `cat, dog, animal → animal, pet, owner → owner, vet, hospital`. **Persistence,
   birth and death of concepts across ticks is new observable data that the old design threw away.**
2. **Bridges arise from reachability, not proximity.** A concept enters an assembly because
   activation *reached* it, possibly along a path, possibly from context rather than similarity.
   Overlap becomes a natural consequence rather than a geometric coincidence.
3. **The model thinks with no input.** With `x_t = ∅` the loop still runs — spreading, competing,
   fatiguing, drifting. That is mind-wandering, and it is where consolidation and replay live.

### 5.3 The edge model — embeddings become one term among five

**[MEASURED]** the retrieval work established the semantic term is real but mediocre: `z = 1.92`
separation, ~47% recall@30. Treating it as memory itself was the original error.

```
    W_ij  =  w₁·semantic(i,j)        cosine on abtt vectors      [MEASURED, weak-moderate]
          +  w₂·episodic(i,j)        Hebbian co-activation count [the SR term]
          +  w₃·temporal(i,j)        i preceded j                [ASYMMETRIC]
          +  w₄·predictive(i,j)      i reduces surprise about j  [hooks F_MOS]
          +  w₅·task(i,j)            co-relevance under a goal   [CMR source context]
```

Two consequences worth stating up front:

- **`w₃` makes the graph directed.** Temporal succession is not symmetric. That changes what
  cohomology means and is a real theoretical decision, not a detail. **[OPEN HYPOTHESIS]** —
  possibly the most interesting mathematical question the new architecture raises.
- **The five weights are five new knobs.** They must be *learned* (from the validation battery) or
  *derived* (from free energy), never hand-set. If they are hand-set, §2's trap has already closed.

---

## 6. THE VALIDATION BATTERY — THE GATE ON EVERYTHING

Ordered by how strongly each constrains the dynamics. **Each is a pass/fail with a stated criterion,
decided before the run.** ⚠️ Human reference values are from model knowledge; verify.

### 6.1 Serial position curve
Present a list, free-recall it. **Pass:** recall probability is U-shaped — elevated at the start
(primacy) and end (recency). **Fails if:** flat, or monotone. Primacy needs rehearsal/base-level
strengthening; recency needs context drift or WM. **A model without both mechanisms cannot pass.**

### 6.2 ★ Lag-CRP with forward asymmetry — THE decisive one
After recalling item at serial position `i`, plot the probability that the next recalled item is at
`i + lag`. **Pass:** sharply peaked at `|lag| = 1`, decaying with `|lag|`, and **asymmetric in favour
of `+1`** (forward transitions more likely than backward).

**Why this one carries the argument:** it is a fine-grained, robust, quantitative signature with
*no* free parameter to hide in, and it is a direct consequence of a drifting temporal context. A
model that produces it has genuinely captured how retrieval is cued. A model tuned to produce a
target topology will not produce it by accident.

**If nothing else in this document is implemented, implement this test.**

### 6.3 Semantic clustering
With a categorised list (animals, tools, …), recall transitions cluster within category above chance
(Bousfield). **Pass:** measured clustering exceeds a permutation null. Note this needs the *semantic*
edge term — which is why the retrieval fix still matters.

### 6.4 Fan effect
Concepts associated with more others are retrieved more slowly / less reliably (Anderson).
**Pass:** a monotone relationship between fan and retrieval latency (tick count to activate).

### 6.5 Spacing effect
Spaced repetitions produce better long-run retention than massed ones. **Pass:** spaced beats massed
at long delay. Requires base-level decay with the right functional form; **[INFERRED]** power-law
rather than exponential.

### 6.6 Capacity
Assembly size should stabilise in a small range without being told to. **Pass:** emergent mean
assembly size is stable across inputs and is not a parameter that was set. **[OPEN HYPOTHESIS]**
whether it lands anywhere near human WM capacity — it does not have to, but it must not be `k`.

### 6.7 Negative controls — mandatory, per Tier 0's closing rule
- **Shuffled input:** signatures must *disappear*. If a lag-CRP appears with randomised input, the
  statistic is measuring the analysis, not the model.
- **Ablations:** remove context drift → 6.2 must fail. Remove fatigue → the model must stick in one
  attractor. **An ablation that changes nothing means the variable did not earn its place** and
  should be deleted (A17).

---

## 7. PHASED IMPLEMENTATION, WITH HARD GATES

**No phase begins until the previous phase's gate passes.** This is the structure Tier 0 lacked.

### PHASE G0 — the skeleton (days)
Minimal loop: activation, spreading, k-WTA competition, Hebbian update. No context, no fatigue, no
goals. Synthetic concept graph with **known** structure (planted partition; planted cover).
**GATE:** the simulator recovers the planted structure in the co-activation graph. If it cannot
recover a structure it was *given*, nothing later is interpretable.

### PHASE G1 — context and the decisive test (1–2 weeks)
Add the drifting context vector (TCM). Implement free recall.
**GATE: §6.2 lag-CRP with forward asymmetry, plus §6.1 serial position.** This is the phase that
decides whether the whole approach is viable. **[OPEN HYPOTHESIS]** — if a TCM-style context cannot
be made to work inside MOS's representation, the architecture needs rethinking, and better to know
in week two than in month six.

### PHASE G2 — the full state (weeks)
Fatigue, base-level decay, WM capacity, goal context.
**GATE:** §6.3–§6.6 pass, and every §6.7 ablation changes something. Any variable whose ablation
changes nothing gets deleted.

### PHASE G3 — the multi-source edge model (weeks)
Introduce the five-term `W`. Weights **learned or derived, never hand-set**.
**GATE:** the battery still passes, and each term's removal degrades at least one signature. A term
that degrades nothing is not in the brain's edge model either — drop it.

### PHASE G4 — long-run generation (compute-bound)
Run 10⁵–10⁶ ticks over a realistic input stream. Record the full assembly trajectory, not snapshots.
**GATE:** the run is reproducible, checkpointed, resumable (§5ap's lesson: a long job whose partial
progress is worth nothing is a bug in the job).

### PHASE G5 — topology, at last
Build the co-activation complex from the *generated* trajectory and ask: partition? cover?
hierarchy? persistent cycles?

**These are now PREDICTIONS of a validated dynamical model rather than assumptions about a corpus.**
And Tier 0's acceptance criterion applies unchanged: any instrument must pass a synthetic partition,
a synthetic cover **with planted bridges recovered in the right direction**, and a structure-free
control, **all at one shared parameter setting**, before it is pointed at the generated data.

---

## 8. WHAT CARRIES OVER — NOT STARTING FROM ZERO

| asset | role in the new architecture |
|---|---|
| **abtt + top-k retrieval** (`make_assemblies.py`) | the `semantic(i,j)` edge term — one of five, no longer the whole model |
| **`curveball_randomize`** | the fixed-margin null for *any* co-activation claim, unchanged |
| **`extract_refs.py`** (2266 labels) | validates the semantic term, and `\ref` chains are a plausible **input stream** for G4 |
| **`measure_open_triangles.py`** | refuted as an instrument, but the calibration harness (synthetic partition/cover/geometric) is reusable **and is now the acceptance test** |
| **`build_corpus.py`** | local corpus generation, no Colab |
| **`F_MOS`, `π_e`, free energy** | the `predictive(i,j)` term should hook into this rather than run a parallel objective |
| **𝕂/W split, sheaf adjunction** | reinterpreted as CLS with a formalisation — see §4.3 |
| **the epistemic-status convention** | applies to every claim in the new phase |

---

## 9. COMPUTE — ON A 4-CORE, 5.9 GB MACHINE THAT SLEEPS

**[DERIVED]** from this session's measurements. With `N = 1074` concepts and a dense `W`:

- spreading is one `N × N` matvec ≈ **1.2 M flops/tick**
- Hebbian update is another `N²` ≈ **1.2 M flops/tick**
- ⇒ roughly **2–3 ms/tick** in numpy ⇒ **10⁶ ticks ≈ 40–60 minutes**

That is affordable. Two constraints that are not:

- **`W` is `N²` dense.** At `N = 1074` it is 9 MB. At `N = 10 000` it is **800 MB** — the ceiling on
  this machine. **[ENGINEERING CHOICE]** stay under ~5000 concepts dense, or go sparse before
  growing the corpus.
- **The loop is sequential.** Ticks cannot be parallelised across time. The only parallelism is
  across independent *runs* (parameter sweeps, seeds), which is the same embarrassingly-parallel
  structure the Tier-0 bootstrap had.

**Rules, from the false starts:** checkpoint every N ticks; resumable by construction; **time one
complete unit of work before extrapolating** (a 15-minute estimate became 90 by multiplying two
draws); `jobs = 2`, never 4; and sleep kills both compute and wifi.

---

## 10. DISCIPLINE — THE RULES THIS PROJECT PAID FOR

1. **No topology claim before the §6 battery passes.** The trap in §2 is the whole reason.
2. **No measurement without a positive control.** Four artifacts caught this way; the fourth was
   caught *before* it became a reported result.
3. **Every instrument passes partition + cover + geometric at ONE shared setting**, or it is not
   used.
4. **Every state variable must survive ablation**, or it is deleted (A17).
5. **Every claim carries an epistemic-status tag.**
6. **Effective sample size, not label count.** Clustered data has wider intervals than it looks.
7. **Never read an optimum off a flat sweep.** Done twice now; the second time in a document citing
   the first.
8. **Log as decisions land**, not at session end.
9. **Prior art before implementation.** Cover detection cost weeks that four other fields had
   already spent.

---

## 11. RISKS, RANKED

1. **⚠️ Circularity (§2).** The dominant risk. Mitigation: §6 is a gate, not a checkbox.
2. **Parameter explosion.** ~15 free parameters can produce any topology. Mitigation: rule 4, plus
   learning or deriving the edge weights rather than setting them.
3. **Validation failure at G1.** **[OPEN HYPOTHESIS]** — if lag-CRP cannot be produced, the
   architecture is wrong. This is deliberately placed early and cheap.
4. **Scope drift into neuroscience.** Spiking, oscillations, anatomy. Mitigation: §5.1's explicit
   exclusion list.
5. **The input stream is unspecified.** A brain model needs something to think *about*. `\ref`
   chains, paper sequences, task streams — undecided, and it will shape everything downstream the
   way the tick definition did. **Decide it deliberately, with §2 in mind.**
6. **Directed edges break the existing cohomology.** `w₃` makes `W` asymmetric. Real theoretical
   work, not a detail.

---

## 12. THE FIRST THING TO BUILD

Not the simulator. **The lag-CRP test harness (§6.2), against a trivial baseline.**

Reason: it is the gate that decides whether the whole architecture is viable, it is cheap, and
building the test before the model makes it impossible to tune the model to the test without
noticing. Every failure in this project came from building an instrument and a result at the same
time.

Then G0's skeleton, then G1.

---

## 13. THE ONTOLOGICAL SHIFT, RECORDED

> MOS has been treating memory as **geometry**. It should treat memory as **dynamics**.
>
> Geometry is static. A brain is a dynamical system whose geometry is the **shadow left behind by
> repeated activity**.

**[SPECULATION]**, and it is the bet the whole next phase rests on. Worth writing down plainly so
that if it turns out to be wrong, it is obvious what was assumed.

If it is right, then the cover — if it exists — is not a property of the corpus, or of the
embedding, or of any similarity metric. It is a property of **what the system does over time**, and
none of the four Tier-0 attempts could have found it, because none of them was looking at a system
that did anything.
