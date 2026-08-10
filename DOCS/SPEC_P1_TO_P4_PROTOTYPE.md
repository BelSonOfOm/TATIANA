# SPEC P1–P4 — THE ROAD TO A WORKING PROTOTYPE

*Filed 2026-08-08. Track A: MOS as a research tool. **None of this requires the generative model of
cognition.** See logbook §7 for why the two tracks are separable and why this one runs first.*

P0 (retrieval) is done: `111ad33`, `d9fa46d`. What follows is everything between a built engine and
an engine that answers a real question.

Tags: `[MEASURED]` · `[DERIVED]` · `[ENGINEERING CHOICE]` · `[OPEN]`.

---

## P1 — `support` RESOLUTION: LET THE DAG NAME WHAT IT ACTS ON

### The defect

`python/communicator.py:136`

```
"'support' MUST be an array of integers (internal vertex ids) or omitted entirely.
 You do not know the internal vertex ids, so ALWAYS output \"support\": []."
```

The planner is **instructed to emit nothing.** It knows concept *names* — that is what it reasons
about — and the schema wants *integers*, so the prompt resolves the mismatch by discarding the
information.

### Why it matters more than it looks

`src/core/operad.cpp:26` foliates the DAG into maximal commuting slices using
`current_slice_support`. **An empty support means "global mutation":** every node is assumed to touch
everything, so

1. **no two nodes ever commute** — the operad's parallelism is dead code, and the ThreadPool has
   nothing to schedule;
2. **nothing can be scoped** — an operator cannot be told *which* concepts it is about, so
   `VerifyOp` (P2) has no way to know what it is verifying.

P2 is not fully solvable while P1 stands.

### The fix

A resolution layer at the Python/C++ boundary. π keeps emitting what it actually knows.

1. **Change the contract.** The prompt asks for `"support": ["Stokes' theorem", "de Rham cohomology"]`
   — *names*, which the planner can produce truthfully.
2. **Resolve before serialising.** `communicator.py:330` currently reads ints. It should map names to
   vertex ids against the live complex. `ConceptStore` already keys by `std::string` and exposes
   `concepts()` **in insertion order** — deliberately, because *"a concept's name means the same
   thing at tick 900 as at tick 10, which an integer index assigned on first sight would not"*
   (`concept_store.hpp:14`). Insertion order is therefore the canonical name→id table.
3. **Unresolvable names are an event, not a silence.** A name the store has never seen is
   information: the planner is reasoning about something not yet in memory. Log it and continue with
   the resolved subset. **Never silently drop to `[]`** — that reintroduces the defect invisibly.

⚠️ **Confirm before writing code:** that operad vertex ids and `ConceptStore` insertion indices are
the *same id space*. `edge_contraction.hpp:27` and `edge_expansion.hpp:27` return `std::set<int>`
over complex vertices; if those are a different numbering, the resolution table must target that one
instead. **This is the one thing in P1 that could be wrong in a way tests would not catch.**

### Verification

- A DAG whose nodes name disjoint concept sets **foliates into more than one slice.** Today it
  cannot. This is the observable that proves the fix landed.
- A DAG naming overlapping sets stays in one slice.
- An unknown name produces a logged event and a partial support, never `[]`.

---

## P2 — `VerifyOp`: STOP GATING CONSOLIDATION ON AN UNEARNED JUDGEMENT

### The defect

`VerifyOp` exists, returns a three-valued verdict `ν`, and `γ(ν)` gates the consolidation formula

```
    R^𝕂 ← Π_{O(d)}( R^𝕂 + γ(ν)(R^W − R^𝕂) )
```

**But nothing computes `ν` from evidence.** The permanent store is therefore updated on the strength
of a judgement no component earned, and `γ₀ ≪ 1` — the anti-catastrophic-interference property — is
protecting against noise it cannot distinguish from signal.

### The fix, in three tiers

Do them in order; each is useful alone.

**Tier 1 — internal consistency (free, no dependencies).** `ν = REFUTED` when a candidate claim
raises `ρ` above the RESOLVE gate against the concepts in its own support. This is the coherence
functional doing the job it was built for, and it needs nothing new. **[ENGINEERING CHOICE]** on the
threshold — reuse `CriticalityMonitor::eps_rho()`, which is already auto-calibrated, rather than
introducing a second constant.

**Tier 2 — citation grounding (free, data exists).** A claim asserting a dependency that contradicts
the `\ref` record is `REFUTED`; one it corroborates is `VERIFIED`; silence is `UNKNOWN`. Uses
`extract_refs.py` output — 2266 author-asserted dependencies already in hand.

**Tier 3 — a real checker (costly, later).** Lean/`miniF2F` for formal statements; a sandbox for
numerics. **Out of scope for the prototype**, and named here so it is not mistaken for done.

### The rule that makes this safe

**`UNKNOWN` must map to `γ = 0`, not to a small positive number.** An unverified claim should leave
the crystallised store *untouched*, not nudge it slightly. Nudging is how an unverified claim becomes
a verified one after enough repetitions.

### Verification

- A deliberately contradictory claim gets `REFUTED` and `Q(t)` does not move.
- A corroborated claim gets `VERIFIED` and `Q(t)` moves.
- With every verdict forced to `UNKNOWN`, the crystallised store is **bit-identical** before and
  after a run. This is the test that proves `γ(UNKNOWN) = 0` is real.

---

## P3 — CONFIRM `Q(t)` MOVES

Commit `1e7fc88` closed the consolidation loop with **"Q(t) left zero."** Consolidation that never
accumulates is consolidation in name only.

**Three candidate causes, and they are distinguishable:**

| cause | diagnosis | expected after |
|---|---|---|
| retrieval returned nothing, so `W` was empty | P0 | fixed already — re-measure first |
| `ν` never reached `VERIFIED`, so `γ(ν) = 0` always | P2 tier 1–2 | `Q(t)` moves on corroborated claims |
| `R^W ≈ R^𝕂`, so the update term vanishes | neither | genuine finding: **nothing is being learned**, and the restriction-map learner needs looking at |

**Do this before P4 and before writing any new code.** Re-run the consolidation loop now that P0 has
landed and see which branch you are in. It costs one run and it decides what P2 has to achieve.

⚠️ Log `‖R^W − R^𝕂‖` per tick, not just `Q(t)`. `Q(t) = 0` with a large gap means the *gate* is
closed; `Q(t) = 0` with a zero gap means there is *nothing to consolidate*. Same symptom, opposite
diagnoses, and only the extra number separates them.

---

## P4 — ONE END-TO-END RUN ON A REAL QUESTION

### The question

Eigenvalues of the Hodge–Laplacian on differential forms of `ℂℙ³`. On record as the reference
problem since the beginning, and doubly appropriate now: it is also the two-qubit pure-state space,
so it sits on the M1 track as well.

### The run

```
    ingest papers → π: question → DAG → Φ: execute → retrieve → reason → verify → respond
```

### What must be recorded — and this is the actual deliverable

**The answer is the least interesting output.** P4 is an *instrument*, not an experiment
(logbook §7). What it produces that nothing else can:

| logged | why |
|---|---|
| the full assembly trajectory `A(1), A(2), …` | the co-activation record every later measurement consumes. **Without a P4-style run there is no accumulated experience**, and Spec A on the co-activation graph has no data |
| `ρ(t)` per tick | **predicted to be a sawtooth** — falling as a thought coheres, jumping when fatigue ejects it. If it decays monotonically to a floor, that is a real finding about the architecture, obtainable months before the simulator exists |
| `‖R^W − R^𝕂‖` and `Q(t)` | P3's diagnosis, continuously |
| `\|A(t)\|` | should stay ≤ 30, so `skipped_wide_assemblies()` stays 0 and `b₁` is uncontaminated |
| every LLM call and its cost | the budget is real |

### Pass criteria — stated before the run

1. It **completes** without a crash, on the 5.9 GB machine.
2. `skipped_wide_assemblies() == 0`. If not, `k` and the triangle cap disagree and `b₁` is
   contaminated.
3. `Q(t)` is **non-zero** at the end, or P3's diagnosis says exactly why not.
4. The trajectory is **checkpointed and resumable.** A long job whose partial progress is worth
   nothing is a bug in the job.

**Explicitly NOT a pass criterion: whether the answer is correct.** One question is not an
evaluation. The evaluation is T1 — three arms, same LLM, bare | plain-RAG | MOS, measuring the **gap
as a function of accumulated experience**, a derivative rather than a level.

---

## ORDER, AND WHAT BLOCKS WHAT

```
    P0 ✅ ──▶ P3 diagnostic run ──▶ P2 (tiers 1–2) ──▶ P4
                     │                    ▲
                     └──▶ P1 ─────────────┘
```

- **P3's diagnostic run comes first** and costs one execution. It decides what P2 must do.
- **P1 before P2**, because an operator that cannot be told what it is about cannot verify it.
- **P4 last**, because it is the instrument and everything else is what makes its output readable.

## WHAT THIS DOES NOT GIVE YOU

- Not a test of the model of cognition. Track B — Spec A, G0, G1.
- Not an evaluation. That is T1.
- Not `bge-small` validated against a stronger embedder `[OPEN, carried from §5ba]`.
