# MOS — Finalization Document

**Date:** 2026-07-27
**Purpose:** close the design phase. Everything settled is recorded here or pointed at;
everything still open is a numbered question with a recommended default.
**Read with:** `MEMORY_MODEL_TWO_COMPLEX.md`, `AUDIT_SCRUTINY_AND_BOOK.md`,
`BUDGET_AND_TEST_PLAN.md`, logbook §5r.

---

# PART A — SETTLED

Recorded so nobody reopens them. Reasoning is in the referenced document.

| # | decision | where |
|---|---|---|
| A1 | Memory is **two-timescale**: crystallized store 𝕂 (no section) + working complex W (has a section) | `MEMORY_MODEL_TWO_COMPLEX.md` §2 |
| A2 | They communicate by the sheaf adjunction `ι_! ⊣ ι* ⊣ ι_*`; `ι*ι_! ≅ id` gives a faithful round trip. Write back with `ι_!` (extension by zero), never `ι_*` | ibid §3 |
| A3 | Consolidation: `R^𝕂 ← Π(R^𝕂 + γ(ν)(R^W − R^𝕂))`, γ gated on VerifyOp's three-valued ν. `s_W` is never written back | ibid §4 |
| A4 | **The constant sheaf is abandoned.** Restriction maps become non-trivial | ibid §6 |
| A5 | The category question (audit F10) is **dissolved, not answered** — no Jordan–Hölder, K₀ or Ext¹ needed for memory | ibid §9 |
| A6 | **FCA rejected as substrate** — data-determined, kills path-dependence. Parked as a possible local folding move | logbook §6 |
| A7 | ρ splits as ρ = α·ρ̃ with ρ̃ ∈ [λ₂/B, λ_max/B]; ε set as a quantile of that window | audit Tier 1.1 |
| A8 | Growth is aimed by the **harmonic** component of a *measured* η. Derived cochains cannot work (Prop 8.2) | audit F3, memory model §5 |
| A9 | Notation fork: *scale* = organ/concept; *timescale* = 𝕂/W. Never conflate | memory model §1 |
| A10 | Three papers, not one: (A) coherence measure, (B) cohomological obstruction, (C) ℂℙ³. **C must not be contaminated by MOS** | audit §3.1 |
| A11 | Benchmarks **hold the LLM fixed** and vary the organiser. Main test measures a *derivative*, not a level | `BUDGET_AND_TEST_PLAN.md` Tier 2 |
| A12 | Restriction maps stored as **Householder products** — 6 KB vs 576 KB, and ‖R‖=1 by construction | ibid §I.2 |
| A13 | Hodge split by **iterative least squares (LSQR/CG)**, never pseudo-inverse | ibid §II.2 |
| A14 | Pairwise judgements **batched into one LLM call**; unbatched is 21 calls/tick and unaffordable | ibid §III.1 |
| A15 | Instantiation by **approximate PPR + sweep cut** (Andersen–Chung–Lang), cost independent of \|𝕂\| | this doc §B |
| A16 | **Curvature controller** — κ>0 contract, κ<0 expand, with a floor protecting bridges | §C below |
| A17 | Discipline test: new mathematics must change a number the engine prints, or delete a hand-made decision | logbook §5r |

---

# PART B — INSTANTIATION (resolved this session)

```
1. seed:      S ← top-m by embedding similarity        (approximate — LAST resort, not first)
2. expand:    approximate-PPR from S on the WEIGHTED 1-skeleton of 𝕂
              weights = w(σ,t), so Hebbian history shapes retrieval
3. cut:       sweep cut → low-conductance vertex set V_W
4. close:     W ← smallest downward-closed subcomplex containing V_W
5. diagnose:  CUT WEIGHT = Σ w(σ) over simplices with SOME but not ALL vertices in V_W.
              High cut weight ⇒ a coalition was sliced ⇒ warn (it is a type error to
              return 2 of a jointly-bound 3).
```

**Why:** ACL runs in time O(1/(α·ε)), **independent of |𝕂|**. Retrieval cost is a function of
the cache size requested, not the store size. This is the scalability claim, and B3 tests it.

**Connection already in the formalism:** Cheeger, `λ₂/2 ≤ h(G) ≤ sqrt(2λ₂)`. Cluster quality,
reconciliation rate, and ε calibration are three views of one spectral object.

> **Honest limit.** Higher-order (simplicial) Cheeger inequalities are substantially weaker
> than the graph case and admit known counterexamples to the naive generalisation
> (Gundert–Szedlák; Parzanchevski–Rosenthal–Tessler). **Cluster on the 1-skeleton where the
> theorem is solid; treat cut weight as a diagnostic, not a bound.** Do not claim more.

---

# PART C — THE CURVATURE CONTROLLER (new, this session)

## C.1 Correction to the earlier warning

Ricci flow **is** homogenising — positive curvature contracts, negative expands. It is
already two-directional. What destroys bridges is the **surgery** step that community-detection
work adds afterwards. **Run the flow; skip the surgery.**

## C.2 Reading the sign

```
κ > 0    many alternative paths.  Redundant.  Well-understood.   LOW information per edge.
κ < 0    near-cut.  A bridge between separate bodies of knowledge. HIGH information per edge.
```

Curvature is, up to sign, an information-content-per-edge measure.

## C.3 The rule

```
  κ > κ_hi   →  CONTRACT / FOLD    collapse, merge, microneuron promotion   (= chunking)
  κ_lo ≤ κ ≤ κ_hi →  HOLD
  κ < κ_lo   →  EXPAND             bind, attach; mark as an attachment site
```

One signed quantity drives both directions — removing the separate grow- and prune-thresholds.

## C.4 The weight flow, and the protection

**MOS uses a COUPLING convention (w = strength). The sign is flipped from the literature,
where w is a distance. Getting this backwards inverts the whole controller.**

```
  w(σ, t+1)  =  ( 1 + ε·κ(σ,t) ) · w(σ,t)        subject to   w ≥ w_floor  whenever κ < 0
```

The floor is the safety argument: negative curvature **weakens but never severs**. Without it,
a bridge decays past the bind threshold and the connection between two domains is silently
deleted. With it, the gap widens — which is exactly what makes room for a new cell — and the
bridge survives.

**This replaces the magic constant `decay = 0.1` with a computed geometric quantity.**
Thresholds κ_hi, κ_lo set as **quantiles of the observed κ distribution over 𝕂**, not fixed
numbers — the same move that fixed ε. Hysteresis via the existing homeostat (integrated
deviation, not instantaneous κ).

## C.5 Which curvature

**Augmented Forman–Ricci — the version that counts triangles:**

```
  F(e)  =  4  −  deg(u)  −  deg(v)  +  3·#{ 2-simplices containing e }
```

The bare version is essentially degree and adds nothing. The augmented version is positive
exactly when local cycles around e are **filled**, negative when **unfilled**.

- Cost: O(1) per edge with adjacency sets. Fast path.
- **It makes the 2-simplices do computational work** — answering the audit's standing complaint
  that they are stored and never used. Every tick, O(1).

Ollivier–Ricci (`κ = 1 − W₁(m_u,m_v)/d(u,v)`) is more informative and reuses the Wasserstein
machinery already implemented, but costs a W₁ solve per edge. **Start with Forman; escalate
selectively.**

## C.6 The aiming rule — two independent signals

Shape signal κ (free, any time) pre-filters for data signal η_H (costs LLM calls).

```
                    η_H ≈ 0                       η_H ≠ 0
              ┌────────────────────────┬───────────────────────────────────┐
   κ ≥ 0      │ nothing to do          │ contradiction with NO structural  │
              │                        │ cause → suspect the MEASUREMENT,  │
              │                        │ not the complex                   │
              ├────────────────────────┼───────────────────────────────────┤
   κ < 0      │ latent frontier        │ ★ SPEND THE SAMPLE HERE ★         │
              │ log, low priority      │ structural hole actively causing  │
              │                        │ a conflict                        │
              └────────────────────────┴───────────────────────────────────┘
```

At ~1000 requests/day this is not a nicety, it is what makes the selectionist loop affordable.
Note the top-right cell: the architecture detects its own instrumentation failure.

---

# PART D — THE FINALIZATION QUESTIONNAIRE

Every question has a **recommended default** so it can be answered with "default" and a
sentence. Marked 🔴 if it blocks implementation, 🟡 if it blocks the paper, 🟢 if deferrable.

## D.1 Stalk geometry

**Q1 ✅ ANSWERED (2026-07-27): rank-k SPD for implementation, density matrices for theory.**

This is not a compromise — the two are related by a projection:

```
    SPD cone          ≅        ℝ₊        ×    {density matrices}
    Σ = UUᵀ + DI              Tr Σ            ρ = Σ / Tr Σ
    (stored)                  (scale)         (theory)
```

The SPD cone is the **cone over density-matrix space**. Store Σ; the theory works with ρ; the
trace is a free scalar. Nothing lost either way. **The Bures–Wasserstein distance already in
`knowledge_base.cpp`, restricted to trace 1, IS the Bures metric on density matrices — the
quantum fidelity metric.** The projection makes this exact rather than suggestive.

### Consequence: restriction maps are quantum channels

Restriction maps become congruences `Σ ↦ R Σ Rᵀ`. And:

```
  R orthogonal  ⟹  Tr(RΣRᵀ) = Tr(Σ)  ⟹  trace-preserving
                ⟹  maps density matrices to density matrices
                ⟹  it is a UNITARY (orthogonal) QUANTUM CHANNEL
```

**The Householder representation forced by the RAM budget (A12) lands exactly on the simplest
class of CPTP maps.** Orthogonality was forced by the Anderson–Morley bound (audit F2); it
arrives at unitary channels for free.

### The connection-potency ladder (replaces the book's characteristic-cycle proposal)

| level | restriction map | what it says about the connection |
|---|---|---|
| 0 — today | identity | "these two see the same thing, verbatim" |
| 1 — Householder | **unitary channel** | "same content, different basis" — **reversible**, lossless |
| 2 — general CPTP (Kraus) | lossy channel | "translating u→v **destroys** information" — decoherence |

Level 2 is better than the book's `CC(M)` proposal because it is computable and degrades
gracefully: a non-unitary channel has a **measurable** information loss (the entropy it adds),
and that is a number saying how good a connection is.

**Crucially this costs nothing in spectral theory.** Symmetric matrices form a vector space and
CPTP maps are LINEAR on it. So the sheaf remains a sheaf of vector spaces with linear
restriction maps: L stays symmetric PSD, ker L = H⁰, ρ keeps its bound. The QI reading is free.

**Q2 ✅ ANSWERED: tangent-space linearised.** Karcher mean each tick, lift via log, run the
existing apparatus in the tangent space, map back. E12 tests whether it earns its cost.

**Q2b ✅ ANSWERED (2026-07-27) — linearised in WHICH geometry?** *(Raised by Q1's answer. The
🔴 on this heading was stale for four days while the answer sat 25 lines below it — see the
dispatch rule at the end of this subsection. A superseded open-marker is worse than no marker,
because it makes settled work look blocking; corrected 2026-07-31.)*

MOS currently uses **two different Riemannian structures on the same objects**:

```
  π_v fusion:    π_v = (Σ Σᵢ⁻¹)⁻¹ (Σ Σᵢ⁻¹ μᵢ)    ← INFORMATION (Fisher–Rao / KL) geometry
  W₂ distance:   Bures–Wasserstein                ← OPTIMAL TRANSPORT geometry
```

These are genuinely distinct. Concretely: the **Wasserstein barycenter of Gaussians has mean
equal to the PLAIN weighted average of the μᵢ** (Agueh–Carlier), *not* the precision-weighted
average. So the fusion operation and the distance function disagree about what "average" means.

Not fatal — they serve different purposes, and the `.tex` correctly justifies π_v as the MLE for
independent noisy measurements. **But it is implicit, and a referee will find it.** And the
Karcher mean of Q2 is different in each geometry, so a choice is forced:

- **(a) Wasserstein.** Barycenter by fixed-point iteration (Álvarez-Esteban et al.),
  O(dk² + k³) per iteration, ~5 iterations. Matches the existing W₂ and the quantum reading.
- **(b) Information / Fisher–Rao.** Barycenter is close to what π_v already computes.
  Matches the existing fusion.
- **(c) Both, explicitly scoped** — Wasserstein for *distance/merge decisions*, information for
  *fusion*, with the difference stated and defended in the paper.

→ **✅ ANSWERED (2026-07-27): (c) — a HYBRID metric with an explicit dispatch rule.** Tangent-space
linearisation done in **Wasserstein** (quantum-native; W₂ already implemented).

### The dispatch rule (normative — cite this table, do not re-decide per site)

The principle deciding every case:

> **Is the operation ESTIMATING one thing from many, or COMPARING two things?**
> ```
>   ESTIMATION  →  information / Fisher–Rao      (the MLE has a derivation — do not touch)
>   COMPARISON  →  optimal transport / Bures–W₂  (accounts for spread; quantum-native)
> ```

| operation | geometry | why |
|---|---|---|
| `π_v` coarse-graining (fuse n concepts → organ belief) | **information** | MLE for n independent noisy measurements of one quantity — proved in the `.tex` |
| pairwise concept fusion (Eq. 13, Woodbury) | **information** | same theorem at n = 2 |
| merge / split decision | **transport** | asks "are these the same concept" — needs spread, not precision |
| `ω`, `ρ`, the discord | **transport** | comparison across an edge |
| Karcher mean for the Q2 linearisation | **transport** | it is the base point of the *comparison* structure |
| entropy / `H(Σ)` diagnostics | **information** | a property of one distribution, not a comparison |

**Why this is not arbitrary:** estimation is where a **theorem** exists; comparison is where a
**modelling choice** exists. Never blend into the first. Interpolation is legitimate inside the
second — that is where WFR (Q2c) would live, contingent on E15.

### ⚠️ The seam, and the paragraph the paper owes

`π_v` **fuses** in information geometry, and its output is **immediately compared** in transport
geometry by `ω`. So a coarse stalk is *produced* by one metric and *measured* by another.

Concretely: **`π_v` is not the transport-barycenter of its own fine complex.** By Agueh–Carlier
the Wasserstein barycenter of Gaussians has the **plain** weighted mean, not the precision-weighted
one. So the two levels of the stratification are joined by a map that is optimal in one geometry
and not in the other.

This is **defensible but not self-evident**, and a referee who knows Agueh–Carlier will find it.
It needs one justifying paragraph — the same sense in which a maximum-likelihood estimate and a
confidence region are computed differently without either being wrong — **not a fix.** Write it
into Paper A rather than leaving it implicit.

### Q2c — should the two be blended into one learned metric? (asked 2026-07-27)

**Proposal considered:** a new metric interpolating both, with the weight obtained by training.
**Verdict: interpolate yes (for distance only), train no.**

**The mathematics — two ways to combine, each loses something:**

```
 (1) blend the METRIC TENSORS   g_λ = (1−λ)g_FR + λ g_W
     ✓ legitimate Riemannian metric (convex comb. of pos-def forms is pos-def)
     ✓ keeps geodesics, exp/log, Karcher mean  ← what Q2 needs
     ✗ NO CLOSED FORM.  d_λ ≠ (1−λ)d_FR + λ d_W  (inf of a sum ≠ sum of infs).
       Geodesic ODE per distance evaluation. Almost certainly fatal per-tick.

 (2) blend the DISTANCES        d_λ = (1−λ)d_FR + λ d_W
     ✓ is a metric (triangle inequality survives nonneg combination)
     ✓ cheap — both have closed forms for Gaussians
     ✗ NOT the geodesic distance of any Riemannian metric ⇒ no exp/log, NO KARCHER MEAN
     ⚠ blend the DISTANCES, not the squares: (1−λ)d₁² + λd₂² is not a metric squared
```

**The principled version already exists.** ⚠️(verify) Chizat–Peyré–Schmitzer–Vialard (2018),
*An interpolating distance between optimal transport and Fisher–Rao metrics*; equivalently
Liero–Mielke–Savaré (2018), Hellinger–Kantorovich. **Wasserstein–Fisher–Rao** is unbalanced
optimal transport: mass is either **moved** (Wasserstein) or **created/destroyed in place**
(Fisher–Rao). Its parameter is not a blend weight but a **length scale δ**:

```
   below δ  →  cheaper to TRANSPORT      above δ  →  cheaper to DESTROY + CREATE
   (hard cutoff: beyond πδ, no transport occurs at all)
```

> **δ = the semantic distance beyond which two concepts stop being "one thing that moved" and
> become "two different things."** That is exactly the merge/split question, so δ is an
> interpretable modelling quantity rather than a fudge factor.

⚠️ **Check first:** whether WFR admits a closed form between Gaussians as Bures does. If not,
the cost story changes completely and this stays theory.

**Why NOT to train the weight — four reasons, first is decisive:**

1. **It reintroduces exactly what the audit removed.** The α/ρ̃ result replaced `ε ≈ 0.10, fitted
   on three observations` with a graph invariant. Replacing a *choice of geometry* (which has a
   reason) with a *fitted constant* (which has none) is that move in reverse.
2. **No training signal exists.** Merge/no-merge labels are not available. VerifyOp answers
   "is this true," not "are these the same concept." Downstream task performance is honest but
   extremely noisy for one scalar and costs a full pipeline run per evaluation at 1000 req/day.
3. **One scalar needs a sweep, not an optimiser.** 20 values on a validation set. Adding a loss
   and an optimiser buys an overfitting failure mode and nothing else.
4. **The two uses are not symmetric, and one has a proof.** π_v's precision weighting is *the MLE*
   for n independent noisy measurements — a theorem in the `.tex`, not a preference. Blending it
   toward Wasserstein damages a derived result in exchange for a fitted number.

| use | question | status |
|---|---|---|
| **fusion (π_v)** | "given n noisy measurements of one thing, what is it?" | **MLE — derived. Do not touch.** |
| **distance (W₂)** | "how far apart are these two concepts?" | genuinely open — interpolation legitimate here |

**Decision:** keep (c) — scope the two geometries explicitly. If one metric is wanted for
*distance*, use WFR with δ as the concept-identity scale. **Calibrate δ by sweep and report the
sensitivity curve, never a single fitted value** — a curve is honest; a fitted constant invites
precisely the criticism the audit levelled at ε.

**Longer-term, data-driven without training:** if two concepts merge and the merged concept is
subsequently Refuted more often than the unmerged pair would have been, the merge was wrong.
That calibrates δ from VerifyOp without inventing labels — slow and noisy, but real, and it uses
machinery that already exists.

**Q3 🟡 Hyperbolic geometry for the prerequisite DAG specifically?**
→ *Default: not yet.* Provably right for trees (Nickel–Kiela; Sala et al.) but a separate
embedding space to maintain. Revisit if the DAG proves strongly tree-like.

**Q4 🔴 Householder count m for restriction maps?**
→ *Default: m = 4* (6 KB/map). E10 tests whether it is expressive enough; escalation path is
Cayley r = 4 at ~2× cost.

## D.2 Curvature

**Q5 🔴 Forman or Ollivier?** → *Default: augmented Forman* (O(1)); Ollivier only on flagged edges.

**Q6 🔴 κ as signal only, or as an actual weight flow?**
→ *Default: signal-only for two weeks, then enable the flow.* Reversible, and E11 tells you what
the flow would have done before you let it.

**Q7 🟡 κ_hi / κ_lo as fixed values or quantiles?** → *Default: quantiles of κ over 𝕂*, recomputed
on structural change. Same discipline as ε.

**Q8 🟡 w_floor value?** → *Default: the bind threshold itself* — a negatively-curved edge may
decay to, but never below, the point of collapse.

## D.3 The organ contract (blocks E5, the gate)

> ### 🚨 FIX-12 — Q9/Q10/Q11 BELOW WERE THE WRONG TYPE. NORMATIVE CORRECTION (2026-07-31).
> **A symmetric `agreement` cannot be a 1-cochain.** A 1-cochain is *antisymmetric*
> (`η_(u,v) = −η_(v,u)`), and antisymmetrising a symmetric table gives **η ≡ 0 identically** —
> so the Hodge split would have run on the zero cochain and reported a clean result forever.
> This is now an assertion in `experiment_e5.py`'s self-test so it cannot silently return.
>
> **THE CONTRACT, as implemented and shipped in `experiment_e5.py`:** per bound pair `{u,v}`,
> the instrument returns the sub-claim `c_uv` *those two organs jointly bear on*, plus **each
> organ's own push** on it, and
> > `η_(u,v) = p_v(c_uv) − p_u(c_uv)`
>
> **η is therefore antisymmetric BY CONSTRUCTION, not by measurement.** No antisymmetrisation
> step is applied or needed. The old `{u, v, agreement, confidence}` schema is **retracted, not
> deprecated** — do not implement it.
>
> **What survives unchanged:** Q9's *dimension* answer (η is one scalar per edge, which is all the
> Hodge split needs) and the confidence channel. **The `.tex` inherits this correction**, as does
> §7. Retraction recorded in `TATIANA_LOGBOOK.md` §5y and the fix registry.

**Q9 ✅ ANSWERED (2026-07-27), then RE-TYPED by FIX-12 (2026-07-31): one scalar per edge plus a
confidence — but the scalar is a DIFFERENCE OF PUSHES, not an agreement.** η is one-dimensional
per edge — cheap, and enough for the Hodge split to be meaningful. **The confidence feeds π_e
directly, which finally gives precision a non-constant source that is not a hallucinated
logprob** (the gap Remark 6.6 of the `.tex` leaves open and the audit finding on the 1/n law
identifies as disabling the whole π_v mechanism).
*Engine status (2026-07-31): `core::edge_precision()` now derives `π_e = 1/(D_u + D_v + s_e)`
with `s_e = −ln(c)/d`, and `CoarseComplex::set_edge_precision` accepts it. **Nothing yet produces
the confidences `c` — this contract is the missing source**, so `π_e` currently reduces to
`1/(D_u + D_v)`.*

**Q10 ✅ SETTLED BY FIX-12 — only bound pairs are judged**, since η is defined per bound pair
`{u,v}` via a *shared sub-claim*, and an unbound pair has no such claim to be pushed on. What was
a default is now forced by the contract's type.

**Q11 ✅ RE-SPECIFIED BY FIX-12 — the schema is
`{u, v, sub_claim, push_u, push_v, confidence}`**, one call, batched, mandatory per A14.
**NOT `{u, v, agreement, confidence}`.** `η` is computed as `push_v − push_u`; it is never
reported directly, so no downstream step can accidentally symmetrise it.

**Q12 🟢 Do organs judge, or does one moderator judge on their behalf?**
→ *Default: organs judge.* A single moderator would make η a function of one global view, which
risks reintroducing exactness through the back door — the precise trap of audit F3.

## D.4 The growth operator (blocks the growth law)

**Q13 ✅ ANSWERED (2026-07-27): cone off the cycle.** Add one vertex joined to every vertex of the
offending cycle. **Provably kills the homology class** — dim H¹ drops by exactly 1 — so the growth
loop cannot spin (which the chord option risks: it often relocates a class rather than killing it).
Matches §5p's stated intent, "kill an H¹ class by coning." The new vertex is the cell an aimed
LLM sample fills.

**Q14 🟡 How many candidate fills per attachment (Edelman variation k)?**
→ *Default: k = 1 today, raise to 3 when budget allows.* Consistent with §5p.

**Q15 🟡 Who fills the new cell?** → *Default: an aimed LLM sample, VerifyOp-gated.* Unchanged
from §5p; the only difference is that the address is now real.

## D.5 Consolidation and forgetting

**Q16 🔴 γ₀?** → *Default: 0.05,* tuned by E13 (replay). Must be small enough that one session
cannot overwrite the store.

**Q17 🟡 Does γ₀ decay with region age (critical periods)?**
→ *Default: yes* — `γ(σ) = γ₀ / (1 + age(σ)/τ)`. Young regions learn fast; crystallised ones
resist. Free, and it is a real brain mechanism.

**Q18 🟡 Offline replay pass?** → *Default: yes, nightly.* Sample past W's, re-run against the
updated 𝕂, check for degradation. This is how catastrophic interference gets detected rather
than discovered.

**Q19 🔴 What leaves 𝕂?** *(Currently: nothing. This is a scaling requirement, not a nicety.)*
→ *Default: nothing is deleted; low-weight regions demote to `gr` form* — keep the cells, drop
the learned restriction maps back to identity. Content persists, structure is what decays.

## D.6 Verification

**Q20 🟡 Lean now or later?** → *Default: later*, per the budget plan — it is the largest single
build. But it is what makes VerifyOp genuine rather than an LLM grading itself, so it is the
single highest-credibility item in the programme.

**Q21 🔴 What happens on Refuted?** *(Currently γ=0, i.e. "don't consolidate" — but nothing is
retracted from 𝕂.)*
→ *Default: mark the supporting cells `Refuted` and exclude them from instantiation; do not
delete.* Full AGM contraction deferred.

## D.7 Scope

**Q22 🟡 Which paper first?** → *Default: Paper A* (coherence measure). Nearly writable today;
every claim is a theorem plus a measurement on a running system.

**Q23 🟡 Main test T1 on your own workload or a public benchmark?**
→ *Default: both* — your workload for Λ(t) and the slope; miniF2F/ProofNet for external
credibility, because Lean makes VerifyOp real there.

**Q24 🟢 Do the D-module / Koszul / quiver chapters go in any paper?**
→ *Default: no.* They currently fail the A17 discipline test. Park them as a "future directions"
paragraph, and revisit only if E3 shows the independence relation is non-empty.

---

# PART E — PATH TO PUBLICATION

```
NOW ──────────────────────────────────────────────────────────────
  Tier 0 tests (E1, E3, E4, E7, Q) — free, parallel, no new machinery
  Answer the 🔴 questions above
        │
        ▼
GATE ─────────────────────────────────────────────────────────────
  E5 — measured η on one filled triangle (~10 LLM calls)
  If η is always pure gradient → STOP. The growth story needs rethinking.
        │
        ▼
BUILD ────────────────────────────────────────────────────────────
  Householder maps → LSQR Hodge → PPR instantiation → Forman κ
  𝕂/W split → γ(ν) consolidation → attachment operator
        │
        ▼
VALIDATE ─────────────────────────────────────────────────────────
  E8–E13 (all free) → B1, B2, B3 (~1 week LLM budget)
        │
        ▼
PAPER A ──────────────────────────────────────────────────────────
  "A cellular-sheaf coherence measure for multi-agent LLM orchestration"
  Content: 𝓜=(C,F,s); ω,ρ; the α/ρ̃ splitting; weighted Anderson–Morley WITH the
  ‖R‖≤1 hypothesis; PC free energy; the Oja rule; worst_edge; three-valued VerifyOp;
  the 𝕂/W adjunction; the curvature controller.
  Every claim = a theorem + a measurement on a running system.
        │
        ▼
PAPER B ──────────────────────────────────────────────────────────
  "Sheaf-cohomological obstruction as a diagnostic for multi-agent disagreement"
  Needs E5 to have passed. Prop 8.2 is publishable as a negative result on its own.
  Abramsky–Brandenburger contextuality is the QI thread that makes this a thesis chapter.
        │
        ▼
PAPER C ── (INDEPENDENT, START ANY TIME) ─────────────────────────
  "A thermal Hodge spectrum on ℂℙ³"  = FIRST DRAFT §3.
  §3.1 β=0 exact (Ikeda–Taniguchi)
  §3.2 β→∞ asymptotic (Morse/Frankel/Witten; slope ≈ 2β·gap(K), CONVENTIONS PINNED)
  §3.3 small-β perturbation (SU(4) → T³ symmetry breaking)
  §3.4 numerics in the SU(4) harmonic basis, checking §3.1–3.3 against each other
  MOS goes in the methods note. NOT a co-author of the theorem.
```

**Overlapping regimes that must agree is what "bulletproof" means in practice.** Paper C has
three regimes checking each other; Paper A has theorem-and-measurement for every claim.

---

# PART F — WHAT REMAINS UNCLAIMED

- Nothing here raises the LLM's per-call reasoning quality.
- Coherence is not correctness. VerifyOp remains the sole arbiter, and runs first.
- Curvature says where structure is redundant or thin. It says nothing about what is **true**.
- κ<0 marks a frontier. Whether that frontier is *worth* crossing is not a geometric question.
- All citations in this document set are from model knowledge and **were not searched**.
  Verify years and titles before any bibliography.
- Wall-clock estimates in `BUDGET_AND_TEST_PLAN.md` are inferred from flop counts, not measured
  on the target machine.
