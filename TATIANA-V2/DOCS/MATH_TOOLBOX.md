# MATH TOOLBOX — founding material for TATIANA V1

**Purpose.** V0 (the organ-complex-around-an-LLM architecture) closes once §7's P0–P4 land (see
`TATIANA_LOGBOOK.md` §8). This document inventories everything V0's construction produced —
theorems, derivations, mechanisms, dead ends — so V1 (a single self-mutating kernel, not a complex
dispatched by external code) starts from the full record instead of institutional memory. Organized
by **topic**, not by session. Where an idea was proposed, broken, and re-derived across many
sessions, only the **final status** is given as the headline, with the breakage kept underneath as
a caveat — that history is exactly what "worked and didn't work" means and none of it is trimmed.

**Sourcing.** Compiled from `TATIANA_LOGBOOK.md` (read in full, 5193 lines) and 15 companion docs in
`DOCS/` (`DERIVATION_MDL_GROWTH_LAW.md`, `SPEC_GROWTH_ADDRESS_AND_DYNAMICS.md`,
`MEMORY_MODEL_TWO_COMPLEX.md`, `SPEC_P0_RETRIEVAL_FIX.md`, `SPEC_P1_TO_P4_PROTOTYPE.md`,
`THE_RETRIEVAL_PROBLEM.md`, `THE_COVER_QUESTION.md`, `MOS_JUSTIFICATION_AND_MEMORY_1.md`,
`THE_GENERATIVE_THOUGHT_MODEL.md`, `MOS_FINALIZATION.md`, `AUDIT_SCRUTINY_AND_BOOK.md`,
`WHY_A_MODEL_OF_COGNITION.md`, `PLAN AND IDEAS.md`, `PRIOR_ART_AND_THE_REPLAN.md`,
`BUDGET_AND_TEST_PLAN.md`), extracted in full by two background agents plus a direct read.

**Status tags**, used throughout: ✅ verified/measured · 🔵 proposed/derived, unverified in practice
· ❌ refuted/dead end · ⚠️ open/unresolved caveat · 🔴 explicitly rejected.

**Citations.** Nearly every citation in the source corpus is flagged in its own document as "from
model knowledge, NOT searched" unless marked `[SEARCHED]` below. Verify authors/years/venues before
any of this goes in a paper.

---

## PART I — THE SURVIVING CORE: STATE SPACE, SHEAF, COHERENCE

### I.1 The cognitive state space and cellular sheaf
✅ **Foundational, unretracted throughout V0.** `M = (C, F, s)`: `C` a stratified simplicial
complex (coarse level = cognitive organs as vertices, each organ's stalk is itself a fine complex
of concepts), `F` a cellular sheaf assigning a vector space (later: a Gaussian, later: an SPD
matrix — see Part IV) to each cell, `s` the current coherent global section. Restriction maps
`F_{v⊴e}: F(v)→F(e)` per incidence. Coboundary `(δx)_e = F_{u⊴e}(x_u) − F_{v⊴e}(x_v)`. Sheaf
Laplacian `L = δᵀδ`, real symmetric PSD — this is what makes the spectral theorem apply for real,
rather than being borrowed. `H⁰(K;F) = ker L` — "a coherent thought is literally a matrix kernel."

Simplices = **honest n-ary joint relations**, not decomposed pairwise facts (a theorem depending on
3 prerequisites is one 3-simplex, not three edges) — this is the one place the topology is "earned,
not borrowed," and it stays true throughout every later revision.

Two independent axes, repeatedly conflated and repeatedly re-separated across the record — **keep
distinct in V1**:
- **scale**: coarse (organs) vs fine (concepts inside an organ's stalk) — the stratification.
- **timescale**: crystallized `𝕂` vs working `W` — store vs cache (Part II).
Both scale levels exist inside both timescale levels.

Cut from the original inherited formalism as decorative, borrowing guarantees whose preconditions
were never checked: infinite-dimensional Banach spaces, Pachner moves (a knowledge graph is not a
manifold — replaced by typed ops `bind`/`collapse`/`split`/`merge`, each logged to a mutation
history), cohomology on undefined restriction maps.

### I.2 Coherence ρ — the exact decomposition ρ = α·ρ̃
✅ **Verified, "the single highest-value item" across the whole corpus.**
`ω(x) = xᵀLx = Σ_e ‖F_{u⊴e}(x_u) − F_{v⊴e}(x_v)‖²`, `ρ = ω/(B‖X‖²_F)` with Anderson–Morley
normalizer `B = max_e(d(u)+d(v))` (weighted: `B_π = max(d_π(u)+d_π(v))`, `π_e` the edge precision —
this makes ρ∈[0,1] with **no eigendecomposition** on the fast path).

Split: `x̄` = mean over active organs, `x⊥ = x − 1⊗x̄`, `α = ‖x⊥‖²/‖X‖²_F` (dissent fraction),
`ρ̃ = ω/(B‖x⊥‖²)` (mode index, `⊥` — genuinely undefined, not 0 — when `‖x⊥‖²` is negligible).
Since `ω` depends only on `x⊥` (`ker L` is the *per-component* constants, not the global diagonal —
a correctness point missed even by the theorem's own first two write-ups; get this right when `b0>1`
or a between-component separation scores as dissent when it's in the kernel), `ρ̃` is a genuine
**Rayleigh quotient** on `(ker L)^⊥`, so by Courant–Fischer:
`ρ̃ ∈ [λ₂(L_K)/B, λ_max(L_K)/B]` — **both endpoints computable from the graph before any data.**
Gives a topology-derived `ε` window (`ε = window.lo + q·(window.hi−window.lo)`, q a fixed
quantile — explicitly **normalisation, not derivation**, say so) and a **typed diagnosis**: high
α/low ρ̃ = structural split; low α/high ρ̃ = one bad edge.

**Why this mattered empirically**: ρ is NOT monotonic in organ count (adding a well-aligned organ
raises ω but raises `B‖X‖²_F` more — comparisons across differently-sized complexes need care), and
the "dead dynamic range" worry (`α` small "for encoder-geometric reasons," an early undischarged
claim) was ✅ **measured and found FALSE**: for unit-normalized embeddings `α = (n−1)(1−c̄)/n`
exactly; at the corpus's own `c̄≈0.449, n=7`, `α≈0.463` — nowhere near small, and `ρ̃` sits invariant
across very different `c̄` (0.471 constant), which is the claimed invariance, demonstrated. **Gate
on `ρ̃`, report `α` alongside.**

### I.3 Weighted Anderson–Morley bound
✅ **Correct, standard spectral graph theory** (not novel — an earlier draft's "the one genuinely
new theorem" framing was an overclaim, retract it). `s_e = √π_e` in a Collatz–Wielandt argument
gives row sums `d_π(u)+d_π(v)`. **Stated hypothesis, not optional**: requires `‖R_{v⊴e}‖ ≤ 1`
(orthogonal restriction maps suffice; general learned maps do not — an early proof silently assumed
identity maps and needs the norm bound carried explicitly in any theorem statement).

### I.4 Restriction maps are quantum channels
✅ **Derived, "the big consequence."** Store the stalk as `Σ = UUᵀ + DI` (rank-k SPD). This is
**the cone over density-matrix space**: `Σ ≅ (Tr Σ) × (Σ/Tr Σ)`. Restriction maps act by congruence
`Σ ↦ RΣRᵀ`; if `R` is orthogonal, trace is preserved, so `R` is a **unitary (orthogonal) CPTP
channel**. Potency ladder: level 0 identity ("same thing, verbatim"); level 1 Householder/unitary
("same content, different basis" — reversible, lossless); level 2 general CPTP/Kraus (lossy —
translating destroys information, the added entropy IS a measure of connection quality). Costs
nothing extra in spectral theory: CPTP maps are linear on the vector space of symmetric matrices, so
`L` stays symmetric PSD, `ker L = H⁰`, ρ's bound survives.

**Practical representation, forced by a 5.9 GB RAM budget, not by taste**: full `d×d` restriction
matrices are `576 KB` each at `d=384` — `2.3 GB` at 2000 edges, dead on arrival. Use **Householder
products** `R = H₁···H_m`, `H_i = I − 2v_iv_iᵀ`: `6 KB` at `m=4`, **exactly** orthogonal by
construction (not to tolerance — `7.1e-15` measured at `d=384`), `det = (−1)^m` so `m=4` lands in
`SO(d)`. Apply `O(md)`. 96× storage reduction. ✅ **shipped, tested, C++.**

⚠️ Caveat, found late: the `m=4` Householder family is **NOT closed** under the consolidation
formula's `Π_{O(d)}` retraction — a convex combination of two products-of-4-reflections is not
itself orthogonal, and SVD-projecting back can need up to `d−1` reflections. Two retraction choices
exist and differ by a real margin (2.96 at γ=0.5) — this is **a modelling choice, not an
approximation of one by the other**, and must be picked deliberately in V1, not defaulted.

⚠️ Second caveat: reflection-count **parity is a topological obstruction** — `det=(−1)^m` puts
differing-parity maps in different components of `O(d)`; no continuous path joins them, and
`crystallise` correctly **refuses** to interpolate across the gap rather than jumping. A store
starting at the identity has no reflection vectors to interpolate from at all (fixed by padding the
identity with cancelling reflection pairs — `H_vH_v=I`).

### I.5 Predictive coding, precision, and the derived scale ladder
✅ **The "quality of connection" thesis, measured, not just argued.** PC free energy
`F = Σ_e π_e‖ε_e‖²`, `ε_e = (δx)_e = R_{u,e}x_u − R_{v,e}x_v` **is** precision-weighted ω;
inference `ẋ = −Lx` is sheaf diffusion; learning `∂F/∂R = 2π_eε_ex_uᵀ` (rank-1 Hebbian, Oja-
stabilised — capped `max_step=0.5` after raw coupling-as-precision caused divergence). Money-shot
measurement: PC maps collapse a FALSE conflict (same content, rotated frame: 1.96→0.00) while a REAL
conflict (off-topic) survives untouched (2.14→2.14). **Identity maps cannot do this.**

Three derived quantities, each replacing an earlier hand-set or type-erroneous version — **this
progression is itself worth keeping as a template for how a magic number gets deleted in this
codebase**:
- **`π_e` (edge precision).** ❌ Engine's first source was a **type error**: `set_use_precision`
  documented itself as using the Hebbian **coupling weight** `w(σ,t)` — but `w∈[0,1]` is a capped
  coupling and `π_e` is an **unbounded precision**; conflating them already caused one divergence
  bug. ✅ Correct, derived from the PC free energy given independent stalks + orthogonal
  restrictions + isotropic coarse stalks: `π_e = 1/(D_u + D_v + s_e)`, `s_e = −ln(c_e)/d` —
  **this is where Q9's organ confidence belongs**, and it's dimensionally safe there (one scalar
  multiplying `‖ε_e‖²`, `O(1)` contribution) unlike `D` (see I.6).
- **`τ_f` (2-cochain/triangle weight).** Same construction one dimension up: harmonic mean of the
  edge precisions on the triangle's three edges, `τ_f = |f|/Σ_{e∈f}1/π_e`. ⚠️ **Circularity
  claimed, then retracted.** First claim: deriving τ_f from the triangle circulation is circular
  because that circulation is exactly what the Hodge split uses τ_f to measure. ✅ **Retracted**:
  with inner products `W₀,W₁,W₂`, the curl subspace is `im(W₁⁻¹(δ¹)ᵀW₂)`, and since `W₂` positive-
  definite is **onto**, `im(W₁⁻¹(δ¹)ᵀW₂) = im(W₁⁻¹(δ¹)ᵀ)` — **an invertible map does not change an
  image.** Verified numerically to `8.4e-16` over six random `W₂`. So the whole grad⊕curl⊕harmonic
  split is independent of τ, τ_f may be derived without feeding back, and E5's evidence (Part III)
  does not move. 🚨 **The distortion from pinning `τ_f=1` while `π_e` is genuinely derived is
  ~280× (27,871%)** — `τ_f=1` was only ever safe at the degenerate point where `π_e=1` too, and
  gets worse as stalks sharpen. C++ (`core::forman_mos`) is structurally immune (derives τ
  internally, no parameter through which the two can decouple); Python's version accepts an
  override and that is how the hazard became measurable at all.
- **`δ` (the concept-identity length scale).** ✅ Derived from data, no hand labels: same-organ
  pairs are weak-supervision evidence of "one thing," different-organ pairs of "two things"; `δ`
  = the **equal-error crossing** (false-splits = false-merges) of the within/between distance
  distributions, `δ = d*/π`. Parameter-free — reports **separability** and flags
  NOT-IDENTIFIABLE rather than quoting a meaningless number from overlapping distributions.

- **`γ(∅)` (crystallization rate on unchecked ticks)** — same idiom applied a third time. "No test
  ran" is absence of evidence, not a failed test; `γ(∅) = γ₀·[(n_V+κπ⁰_V)+ε(n_U+κπ⁰_U)]/(n+κ)`,
  same Beta shrinkage prior Construction 5 (Part VI) uses for organ membership. Exact day-one
  degradation to the old hand-set `ε·γ₀`. ⚠️ Honestly conditional on selection bias (ticks that
  ran VerifyOp may not resemble ticks that didn't) — testable, strictly better than a constant,
  **never quote as unbiased**.

### I.6 The variance floor — a genuinely load-bearing bug fix
✅ **The single fix with the largest measured downstream effect in the entire record.** A hardcoded
confidence-fallback `0.5` fed `D = −ln(c)` straight into the isotropic noise floor of **every**
stored concept — since the fallback branch always ran (Groq never returns logprobs for the model
used), every concept got the identical `D=0.693`, and the entire Bures–Wasserstein geometry was
computing against a constant. Root fix: `D` demoted to a **floor**, `stalk_floor(d,n_eff,κ)=O(1/d)`
(not `O(1)`) — the correct invariant is "floor carries trace `O(1)`, matching unit-normalised
embeddings," not "shared epsilon," which is subtly different and was gotten wrong once (giving
`k=387`, `6.0s/report` before the correct statement dropped it to `k=3–6`, `0.128s`, 47× faster).
Measured: epistemic term `229.76 → 0` (antipodal means, old vs new); W₂ **no longer inert**
(`0 → 0.206` on rank-0 vs rank-1 stalks — the OT machinery finally measures directional structure).
A magic `1e-9` confidence clamp, which admitted a Bures term of 15.80 against a semantic budget of
4, was replaced by a **derived** `t_max = 4(1+√(εd)) = 6.479` at `d=384` — solving the actual E4
budget constraint exactly, not guessed.

### I.7 The curvature controller
✅ **Derived, not imported — and the derivation is the finding, not the formula.** Ricci flow
itself is already two-directional (positive curvature contracts, negative expands); it's the
**surgery** step community-detection papers add that destroys bridges. "Run the flow, skip the
surgery." `κ>0` = many alt paths = redundant = low info/edge (→ CONTRACT/FOLD, i.e. chunking);
`κ<0` = near-cut = bridge = high info/edge (→ EXPAND).

**Augmented Forman–Ricci**, derived not assumed: for a p-cell in a weighted complex, Forman's
general formula specialises (all weights 1) to `F(e) = 4 − deg(u) − deg(v) + 3·#{triangles ∋ e}`.
The `3` is `1+2`: 1 from the coface sum, 2 from the pair of triangle edges the "not both" clause
removes from the penalty — **a consequence of the clause, not a tuning knob.**

★ **The real finding underneath it**: Forman's cell weights are **not decorative masses** — they
define the inner product in which the combinatorial Laplacian is self-adjoint, the only reason a
Bochner–Weitzenböck/Ricci term exists at all. So the weights are **not free to pick** — they're
already fixed by whichever Laplacian the engine actually prints ω and ρ from: vertex weight → `ν_v`
(precision summary from `Σ_v⁻¹`), edge weight → `π_e`, 2-cell weight → `τ_f`. **Using the Hebbian
coupling `w(σ,t)` as the Forman weight computes the curvature of a *different* Laplacian than the
one the engine actually uses** — worse than the plain unit-weight approximation, because it's a
consistent-*looking* number about the wrong operator. Full formula:
`F_MOS(e) = π_e²Σ_{f⊃e}1/τ_f + (ν_u+ν_v) − Σ_{ẽ∥e}ν_γ(e,ẽ)√(π_e/π_ẽ)`, reducing exactly to the
unit-weight formula when `π=ν=τ=1`.

⚠️ **A prediction flagged, not measured**: as `π_e→0` the coface term dies like `π_e²` but the
`(ν_u+ν_v)` term is untouched, so a low-precision edge may drift **positive** ⇒ CONTRACT/FOLD —
chunking an edge *because we're unsure about it*, backwards. Check the sign behaviour against π_e
explicitly before trusting the controller near low precision.

**The floor mechanism** (`w_floor`), a second derivation worth keeping as a template: the discrete
update `w←(1+ε·κ)w` is a forward-Euler step whose *continuous* flow `w(t)=w(0)exp(ε∫κ)` is strictly
positive for all finite time — **the exact flow can never sever anything**; what *can* sever is the
Euler discretisation flipping sign. So `w_floor` was patching a numerical artefact and had been
misdiagnosed as a plasticity-safety mechanism. Fix (free): **exponential integration**
`w ← w·exp(ε_flow·κ)` — unconditionally positive, `ε_flow`/`ε_ρ` renamed apart to stop a symbol
collision. Threshold protection then needs a **control barrier function**
(`ẇ = max(ε_flow·κ·w, −α(w−θ_safe))`), and neuroscience's weight-dependent soft-bound plasticity
(van Rossum, Gütig) turns out to be *exactly this object* with a linear class-𝒦 function —
"implement the neuroscience and inherit the invariance certificate, or implement the CBF and
inherit the biological precedent." `w_floor` (and the open question `Q8` about its value) is
**deleted as a mechanism**, replaced by `θ_safe` which sits strictly above the collapse trigger by
construction (the flow never reaches it), not by a hand-tuned margin.

⚠️ ❌ **A floating-point trap the derivation missed**: `exp` underflows to exactly 0 below ≈−745, so
a large negative `ε_flow·κ` severs the edge silently anyway, in *exact* arithmetic's clothing. The
barrier does not have this failure mode (it *adds* the floor rather than multiplying, so an
underflowed decay lands *on* `θ_safe`, not through it) — **bare exponential integration is not
sufficient on its own; only the barrier's guarantee survives floating point.**

**Status at close of V0: derived and unit-tested in isolation (`curvature.{hpp,cpp}`), never wired
into a running tick.** No line of the curvature controller has moved a real edge weight yet.

### I.8 VerifyOp trichotomy and the promotion gate
✅ **A real epistemic bug, fixed.** Two outcomes (pass/fail) conflated REFUTED with UNVERIFIABLE —
"the error of concluding falsehood from inability to check" — and would have spiked conflict over
the oracle's own blind spots. Fixed to three: VERIFIED (obstruction clears), REFUTED
(obstruction +=1000, forced into RESOLVE), **UNVERIFIABLE** (obstruction untouched — "absence of
proof is not proof of absence"). A checker crash also returns UNVERIFIABLE, never a refutation.
Gates consolidation via `γ(ν)`. **Status at close of V0: `VerifyOp` exists and computes the
trichotomy, but is not connected to a real prover or sandbox** — `ν` is not earned from evidence in
the live loop (this is P2 of §7's blocking list, Part IX).

---

## PART II — MEMORY: THE TWO-COMPLEX MODEL (𝕂 / W)

### II.1 What was tried and abandoned for memory identity first
🔴 **FCA (Formal Concept Analysis) — rejected as the substrate.** Would compute the complex's shape
canonically from an object×attribute context (Galois connection). Rejected on the correct ground:
FCA is **data-determined**, and its canonicity comes precisely from discarding the path-dependence
that makes a memory a memory. "MOS must GROW, not be RECOMPUTED." Parked only as a possible *local*
folding move during consolidation, never the foundation.

❌ **K₀ / Jordan–Hölder canonical-atom memory schema — dropped.** A large, carefully worked-out
proposal (full schema in `MOS_JUSTIFICATION_AND_MEMORY_1.md`: memory ↦ `[M]∈K₀` (content, an integer
composition-factor multiset) + `{[E]∈Ext¹}` (structure/gluing), with a promotion gate on `Ext¹≠0`,
consolidation as passing to `gr(M)`, and a richer categorical-level stratification (concept=objects,
theorem=morphisms, skill=endofunctors)). It dies on the choice of category, and **both** concrete
candidates fail for opposite reasons: in `Hol(𝒟)` every Gaussian concept is a *simple* module
(`k[x]` is simple over the Weyl algebra in char 0) ⇒ every composition series has length 1 ⇒ the K₀
class carries no information beyond "which memory is this"; in `Rep(Q)` the K₀ class **is** the bare
dimension vector, which collides catastrophically as a retrieval index. "Jordan–Hölder gives
canonicity *given* a category — it cannot pick the atoms." **Dissolved, not solved**, by the
two-complex model below: memory identity comes from growth **history**, and no canonical schema is
needed anywhere. Same tension as the FCA rejection (canonicity vs. growth), resolved the same way.
`Q24`'s default (keep D-module/quiver/Hopf chapters out of every published paper) gets a second
independent reason from this.

❌ **Characteristic cycles, b-functions, HH¹/HH² neurogenesis, holonomic-module concepts — Tier C,
currently inert, not adopted.** All individually correct standard mathematics (Kashiwara's six
operations, Bernstein–Sato polynomials, Ore extensions, the Connes–Kreimer Hopf algebra of rooted
trees for skill decomposition, Kac's theorem for quiver classification) but **decorative for MOS as
built** — every Gaussian concept is currently rank-1/multiplicity-1/zero-section, "constant across
every object the engine can currently produce," so none of this machinery is doing work yet. One
internal error is worth flagging for V1 so it isn't re-derived wrong: **HH² is NOT where extension
obstructions live** (Gerstenhaber: they live in HH³, HH² parametrises first-order deformations), and
Ore extensions are **unobstructed** given `(σ,δ)` in the first place — there is no HH² obstruction to
an Ore extension to compute. Kac's theorem, applied to memory representations, needs an
algebraically closed field and was silently applied over ℝ, where the classification does not hold
in that form — check this before reusing it.

### II.2 The adopted design: 𝕂 (crystallized store) / W (working complex)
✅ **Adopted; the sheaf adjunction is a genuine, standard, provable theorem (not asserted).**
`𝕂 = (C_𝕂, F_𝕂, w)` — stratified simplicial complex, cellular sheaf, coupling weights
`w: C_𝕂×ℕ→[0,1]`. **𝕂 carries NO distinguished section** — a space of possible states, structure,
not a thought. `W = (C_W, F_W, s_W)`, `C_W ⊆ C_𝕂` downward-closed, **W has a section** `s_W`. `F_W`
initialised from `F_𝕂` but not required to equal it — the divergence is what a session learns.
`ι: W↪𝕂` is a full subposet inclusion.

**Theorem (standard category theory, stated not re-proved).** For this inclusion,
`ι* F = F∘ι` (restriction/pullback = instantiate, store→cache), `ι_!` = left Kan extension =
extension by zero (write back only what was touched), `ι_*` = right Kan extension (write back
filling untouched cells by limits from above). Because `ι` is a full subposet inclusion, the
(co)units are isomorphisms: **`ι*ι_! ≅ id`** — the load/work/store round trip is faithful. **Chosen
write-back: `ι_!`, never `ι_*`** — the cache must assert nothing about untouched cells, which is the
sheaf-theoretic form of the project's `⊥`-invariant ("no measurement ≠ a measurement of zero"). This
is a genuine adjunction (unlike an earlier, unverified `ℒ⊣ℳ` construction it replaces).

**Consolidation — one formula, "this is Complementary Learning Systems (McClelland/McNaughton/
O'Reilly 1995) realised sheaf-theoretically, derived independently here from the geometry":**
```
R^𝕂_e ← Π_{O(d)}( R^𝕂_e + γ(ν)(R^W_e − R^𝕂_e) )
```
`γ(ν) = γ₀` if Verified, `εγ₀` if Unverifiable, `0` if Refuted. `γ₀ ≪ 1` is the
**anti-catastrophic-interference property** — this IS the mechanism the user's original question
("how does new learning coexist with old memories without overwriting them") is asking about, made
concrete. `s_W` is explicitly **never** written back — content and wiring persist, the episode does
not. ⚠️ For small `γ` the convex-combination-plus-retraction is a first-order approximation to
geodesic interpolation on `O(d)`; use the exact geodesic only if shown to matter.

★ **`γ₀ ≪ 1` was independently *forced by the evidence*, not just chosen for the
anti-interference argument.** A model-comparison measurement (§I.5-adjacent, via `belief.py`) showed
**no restriction-map parameterisation is affordable to learn from a single tick** — at real scale
(`d=384,n=7`, 21 edges ⇒ 2688 observations/tick), even the cheapest Householder `m=1` map is
over-parameterised **3.0×**, `m=4` is **12.0×**, a full orthogonal map is **574.5×**. Restriction
maps *require accumulation*; the slow-crystallization design and the affordability finding are two
independent routes to the same conclusion.

**`Q(t) = (1/|E|)Σ_e‖R^𝕂_e(t)−I‖²_F`** — new metric, constant sheaf ⇔ Q=0 ("every concept means the
same thing in every context" — nothing learned about the wiring). **The LLM contributes nothing to
this number**, so together with `Λ(t)` (workload-compression curve, mean act-length in current
atomic generators on held-out workload — proved LLM-independent because GK dimension is
generating-set-invariant and provably blind to it) these are the project's two
**LLM-independent falsification instruments.** ⚠️ Precision note: "LLM-independent" means the
*frozen* LLM contributes no *trend*, not that no LLM is involved.

**Day-one degradation, exact**: `k=1, R≡I, γ₀=0, η:=δs, θ=∞` reproduces pre-two-complex MOS exactly.

### II.3 What actually happened when this was wired in
✅ **Measured end-to-end, real SQLite store, first time the engine consolidated rather than merely
ran.** `Q(t)` moved 0 → 4.9e-4 → 2.0e-3 → 4.4e-3 → 7.8e-3 across four ticks, monotone, and
**exactly** 0 when `crystallise_unverified=false` and nothing is verified. A refuted session leaves
`𝕂` **bit-identical**; `ι_!` moves only the touched edge. "Q(t) leaving zero is not a proxy for
consolidation; it is the definition."

🐛 Two bugs the tests caught that would otherwise have rotted silently: (1) **`Store`'s constructor
pre-filled every edge with identity, and `emplace` did not overwrite** — carried-over learned maps
were silently dropped on every rebuild, resetting to the constant sheaf; (2) **one Householder
reflection is the wrong parity** — aligning two unit vectors with a single reflection gives
`det=−1`, landing in the other component of `O(d)` from the identity the store starts at, so
`crystallise` correctly refuses to interpolate, "the learned map would never reach the store, Q(t)
would stay 0, and every test would still pass." Fixed with a product of **two** reflections.

⚠️ **Status at close of V0**: `crystallise_unverified` (what an unchecked tick is worth) was left
as an explicit open decision for Charbel, later resolved by deriving `γ(∅)` rather than hand-setting
it (§I.5). `i_star` (instantiation) is seeded with the raw retrieved set, not yet PPR-instantiated —
Phase-2's sweep-cut item is unwired into this path.

### II.4 The growth-budget theorems (Propositions 5.1/5.2)
✅ **Proved, standard, load-bearing.** Prerequisite for both: a **genuinely measured** 1-cochain
`η ∈ C¹(W;F_W)` from organs, **not** `δ` of any global assignment (forced by Prop 8.2, Part III —
`[δs]=0` unconditionally). Hodge decomposition `η = η_G ⊕ η_H ⊕ η_C`.

**Prop 5.1.** The flow `ṡ=−(δ⁰)ᵀ(δ⁰s−η)` converges to `s*=(δ⁰)⁺η`, with residual
`Φ_∞ = lim_{t→∞}‖δ⁰s(t)−η‖² = ‖η_H‖²+‖η_C‖²` — computable by **two least-squares solves before
flowing.** Proof: gradient descent on a convex quadratic converges to the LS solution; the residual
splits by orthogonality of the Hodge summands.

**Prop 5.2.** `ker Δ₁ ≅ H¹(W;F_W)`, and attaching a 2-cell along a cycle reduces `dim H¹` by at most
1. Hence **at most `dim H¹(W;F_W)` cell attachments suffice to make `W` fully reconcilable** — a
growth budget computed from **shape**, before any LLM call.

⚠️ ❌ **The naive control rule built on top of these theorems failed, and the failure is
instructive.** `Φ_∞/‖η‖²>θ ⇒ grow` is a **fraction**, and a planted-positive-control measurement
(§III.2) showed a real, large obstruction can score as low as **0.21** on exactly that fraction
when ordinary rankable disagreement sits alongside it — **the rule as specified systematically
under-triggers.** Worse: `Φ_∞=‖η_H‖²+‖η_C‖²` sums **curl** (repairable locally, edit one 2-simplex)
and **harmonic** (only fixable by growth) — two signals needing opposite remedies were being
summed into one threshold. **Decided: split them, give different remedies, drop `θ` for a measured
noise floor** (from the negative control's own |L₂| level). `Q25` (θ) **dissolves rather than gets
answered** — it was never the right knob.

---

## PART III — GROWTH: THE ADDRESS PROBLEM, AND HOW IT WAS SOLVED

### III.1 Prop 8.2 — the blocker that reframed everything
✅ **Verified, trivially, and "the deepest correct criticism the project received."**
`[δx] = 0` in `H¹` **unconditionally** — a coboundary is by definition not a gluing failure. Holds
for every state, every sheaf, identity restrictions or not. This kills, permanently, the original
growth-law intuition ("the obstruction cocycle names the cell to attach," reading the address off
`H¹` of a state the engine already computes): the engine's only 1-cochain (`δx` for global state
`x`) is **always exact**, so **the growth mechanism has no address to grow at**, structurally, no
matter how the state is computed. Also kills the naive `b₁`-vs-`H¹` diagnostic distinction under a
constant sheaf (`H^k(C;F)≅H^k(C;ℝ)⊗ℝ^d` makes them the same row with a factor of 384).

**The fix, and it is the whole reframe**: growth needs a genuinely **measured** 1-cochain `η` —
organs emitting pairwise judgements that are **not** the coboundary of any single global state —
plus the Hodge split. **The harmonic component is the address.** Half of an early proposed fix
("residuals of *learned restriction maps*") is ❌ **circular for the same reason**: those residuals
are still `(δx)_e` for the learned maps, still exact, still zero in `H¹`. Only genuinely relational
organ output escapes.

### III.2 E5 — measuring η, the saga (four runs, one retraction, real methodology lessons)
This is the single best-documented example in the corpus of a claim being checked against its own
null and revised twice — kept in full because the *pattern* (not just the conclusion) is the
reusable asset.

**Run 1** [§5v]: contested non-gradient fraction = 0.209 vs isotropic null 0.400, reported **FAIL**
(z=−2.19, p=0.014).

❌ **Retracted same day** [§5w], two independent errors: (1) the p-value was overstated ~4–10× —
repeats of one question are not independent (ICC≈0.48), corrected p≈0.06; (2) **the statistic could
not support the verdict** — a planted-positive control (a rock-paper-scissors cycle of organ
competence, ground truth = cycle present) scored **0.214** on the exact statistic that called the
contested data's 0.209 a FAIL. "A statistic that a known-positive also fails cannot be used to
declare that real questions lack obstructions." Verdict withdrawn.

**Run 2** [§5x]: gate moved to |L₂| (absolute obstruction around the unfilled cycle), calibrated by
probes, question as the independent unit. **PASS, weakly**: contested |L₂|=0.41 (95% CI
[0.28,0.53]) vs planted-cycle P1=1.22 and no-cycle-null P2=0.26 — clears the null but only at **15%
of the planted-cycle level**. 🚨 **A "consistent growth address" was nearly reported as a finding
and is an artifact**: at `b₁=1` the harmonic subspace is one-dimensional, so *every* harmonic
component is a scalar multiple of the same fixed vector — the two largest entries are the same two
edges *by construction*, whatever the data says. "A 1-dimensional harmonic space can report THAT an
obstruction exists but can NEVER report WHERE." **⇒ any configuration used for a real address needs
`b₁ ≥ 2`** — not yet run at close of V0.

**Sharp reformulation, kept**: "η is a pure gradient" means exactly *one number per organ explains
all pairwise data*; non-gradient mass means pairs are locally consistent but not globally glueable —
**this is Abramsky–Brandenburger contextuality**, later given a well-posed (not established, but
well-posed) thesis-level bridge (§III.5).

**Organ-contract lesson, load-bearing (FIX-12)**: a symmetric `{u,v,agreement,confidence}` schema
**cannot be a 1-cochain** — antisymmetrising a symmetric table gives `η≡0` identically. Correct
contract: `(u, v, sub_claim, push_u, push_v, confidence)`, `η_(u,v)=p_v(c_uv)−p_u(c_uv)`,
**antisymmetric by construction, never reported directly** so no downstream step can re-symmetrise
it. Two earlier elicitation designs failed *informatively* before this worked: plain "agreement"
gives `η≡0`; a "how much must you revise" framing got read by the model as **valence not
comparison** (both directions came back positive).

### III.3 Construction 6 — the coned concept (the growth operator)
✅ **The single most-verified new construction in the record — derived, self-corrected twice in the
open, measured, and checked against its own controls.**

**Setup.** Cone a cycle `γ=(v₁,e₁,…,v_k,e_k,v₁)` carrying harmonic mass: new vertex `w`, edges
`f_i={w,v_i}`, triangles `t_i={w,v_i,v_{i+1}}`. `F(f_i):=F(v_i)`, `F_{v_i⊴f_i}:=id`
**[engineering choice, deliberately empty]** so no distortion hides in the new edge and all content
is forced into `F(w)`.

**Derivation.** Consistency on the new edges forces `x_{v_i}=p_i(x_w)` — the value at `w` *generates*
the section over the whole cycle, which is what it means for a concept to explain a loop (`k`
independent facts becoming one). Substituting into the old edges gives
`r_i^+∘p_{i+1} = r_i^-∘p_i` for all `i` — **verbatim the categorical cone condition** over the
diagram `D_γ` of stalks and restriction maps. "The cone condition was not imposed — it fell out of
demanding the topological cone do its job."

**The construction.** `F(w) := lim D_γ`, `p_i` its projections; concretely
`lim D_γ = {(x_i)∈⊕F(v_i) : r_i^-x_i=r_i^+x_{i+1}} ≅ H⁰(γ;F|γ)`. **"What the new concept IS: not a
summary of the cycle's members, but their compatible part."**

⚠️ **Two self-corrections kept visible, both instructive:**
1. An earlier draft argued `F(w)=lim` as "the smallest object admitting the required maps" —
   **backwards.** Every cone factors uniquely through the limit, so the limit is the **largest**
   non-redundant choice — a *ceiling*, not a floor. Two separate determinations result: consistency
   fixes the **shape** (must be a cone; the limit is the universal/ceiling choice), MDL fixes the
   **size** (a subspace of that ceiling — see III.4).
2. An earlier draft claimed the degenerate case (`H⁰(γ;F|γ)=0`, "nothing was consistent, so the
   construction refuses rather than inventing") is a *meaningful* third outcome. ❌ **True but it
   never happens.** For a 1-complex, `χ=dim H⁰−dim H¹`; on a `k`-cycle with equal vertex/edge stalk
   dimension, `dim C⁰=dim C¹` so `χ=0`, giving `dim H¹(γ;F|γ)=dim H⁰(γ;F|γ)` — and with no 2-cells
   the harmonic space **is** `H¹`. So **a cycle carries harmonic mass if and only if it has
   sections** — `H⁰=0` implies no harmonic mass implies no growth address implies the law never
   fires on that cycle at all. The refusal branch is logically real but structurally unreachable
   (unless edge and vertex stalks are ever given different dimensions — they are not).

**A structural surprise found while validating**: "a generic rotation fixes nothing" is **false in
odd dimensions** — every element of `SO(odd)` has eigenvalue 1, so it fixes an axis. This is a fact
about MOS specifically (restriction maps are orthogonal by construction): reachability of the
degenerate case is governed by the **parity of `d`**. At `d=384` (even) it's reachable; had `d` been
odd, no cycle could ever have failed to have something consistent to name.

**Measured** (`validate_construction6.py`, controls: a path/tree reports harmonic dim 0 — not
manufacturing mass; an arbitrary non-cone `F(w)` gives `‖δ¹δ⁰‖_max=1.756` — the complex-check is not
vacuous): with `F(w)=lim`, `‖δ¹δ⁰‖_max=4.4e-16`; arbitrary `F(w)`, `1.756`. ★ **This upgrades the
construction**: since `(δ¹δ⁰x)_{t_i}=(r_i^+p_{i+1}−r_i^-p_i)x_w`, the cochain complex is a complex
**if and only if** `F(w)` is a cone over `D_γ`. **Construction 6 is not the best choice among
several — it is the only choice for which the coned object is a sheaf at all.** The universal
property was never a preference; it was the existence condition.

**Provenance, stated honestly, direction matters**: the universal-property route to a new concept is
**Goguen's** (algebraic semiotics computes a conceptual blend as a categorical **colimit** —
"taking account of shared substructures," provably equivalent to the pushout model in the ordered
category of partial maps), **not ours** — and the variance is **opposite**: Goguen's inputs map
*into* the blend (colimit); a sheaf's restriction maps point vertex→edge, so `F(w)` must map *out*
(a **limit**). "Copying him would have gotten it backwards." What's genuinely ours: the sheaf's own
restriction maps supply the diagram, so nothing new is introduced beyond what the memory already
held.

**What a concept IS, converging with independent literature** [SEARCHED]: Gärdenfors' *Conceptual
Spaces* argues concepts are **convex regions**, not points (interpolation-based categorisation,
empirical support from colour-space division, convex regions are easier to learn). A Gaussian
stalk's level sets are ellipsoids, hence convex — **the SPD stalk already IS a Gärdenfors region**;
this upgrades `Σ` from "a covariance, useful for Bures" to "the concept's extent, because concepts
have extent." ⚠️ Live inconsistency recorded, not yet resolved: in C++ a concept *is* a stalk
(rank-k SPD)+restriction-maps+position; in the Python reference layer (`module_vertex.py`) a
`Concept` is still `(label, vector, weight)` — a genuinely poorer object. **Reconcile these in V1.**

### III.4 Construction 7 — the MDL growth law (the cost side)
✅ **Repairs a real defect and is measured/asserted, not just derived.** The original law (§4,
`ΔL(model) = b·d_v(1+Σd_e)/(c_old−c_new)`) is ❌ **superseded, kept as the record of how it failed**:
the numerator overcounted by a factor of `k` (fixed via **holonomy propagation** — MOS's restriction
maps are orthogonal hence invertible, so only the first leg `p_1` needs describing, the rest are
determined by the round-trip holonomy `H`; `lim D_γ ≅ ker(H−I)` — ✅ measured, propagated legs
satisfy `δ⁰=0` to `0.00e+00`); and fatally, the **denominator did not depend on concept size at
all**, so `d_w=0` was always optimal — "attach always, with a concept that carries nothing,"
reintroducing exactly the over-generation problem the law was meant to prevent.

**Construction 7 fixes the data term with a per-direction code.** Fix a direction `u` in the limit,
`‖u‖=1`. A traversal gives `k` readings `a_i=⟨x_i,u_i⟩/‖u_i‖²`; since `u` is a section, the sheaf's
prediction is `a_1=…=a_k` — "is this direction worth naming" becomes "do its `k` readings agree."
With intraclass correlation `ρ²=σ²_b/(σ²_b+σ²_w)`, the derived savings per traversal:
`Δc(u) = (k/2)log₂(1/(1−ρ²)) − b_s`, `b_s = ½log₂(1+2πe·ρ²/(1−ρ²))`. **The law**:
`n > b(d_v+k_w+1)/Δc(u_j)`, and never if `Δc(u_j)≤0`. ✅ **Measured**: within 0.042 bits/traversal
of exact quantised-Gaussian entropy over `ρ²∈[0,0.995]`, and it over-prices its own reference code
`s` so the threshold is **conservative** — under-attaches, never over-attaches. ⚠️ The `+1` in `b_s`
is load-bearing (its absence, in an earlier draft, made the high-rate form go negative exactly where
a direction explains nothing).

**Consequences restored**: `d_w`-dependence is back, per-direction (`d_w=|{j:n>n_j}|`); the
subspace-selection rule (rank by `ρ²_j`, keep a prefix — earlier merely proposed) is now a
**theorem** (Δc increasing in ρ², constant per-direction cost ⇒ sorting descending makes `n_j`
increasing); a **reliability floor exists independent of frequency** (below it, `Δc≤0` at every n —
measured table by `k`: k=3→0.576, k=4→0.370, k=5→0.239, k=8→0.055, k=12→0, k=20→0). ✅ Also derived
and measured: the estimator bias in `ρ̂²` (plug-in from mean reading gives `ρ̂²=ρ²+(1−ρ²)/k` exactly,
unbiasing formula `ρ²=(ρ̂²−1/k)/(1−1/k)`); a shuffle-readings control drops the saving from
+5.289 to **−0.437** bits/traversal — "the saving measures the recurrence, not the coder."

**Combined with §III.3**: `d_w = dim H(γ)` — the new concept's dimension is exactly the dimension of
the harmonic space of the cycle being filled, known *before* the growth decision, from the same
computation producing the growth address.

⚠️ **What Construction 7 explicitly narrows, stated not hidden**: it prices only "what was there"
(the assemblies), not "which succession fired" (the original data definition included both) — a
**strict under-estimate**, making the law conservative by construction, not by luck.

**⚠️ Open, not a quick fix**: `b` (bits per real number) taken as `½log n` is self-referential but
resolvable by fixed-point iteration — **except it degenerates precisely where the growth law
lives**: at `n=1`, `b=0`, the model is free, over-generation returns. "Do not adopt `½log n` as
derived-therefore-safe — use NML, Bayesian marginal likelihood, or the engine's actual float width."
Also open: `k_w` (the new stalk's covariance rank) is a second, unaddressed size parameter; the
label for `w` is not derivable from a diagram at all — **"the one place an LLM is genuinely
required, real novelty enters rather than being computed."**

**Status at close of V0**: derived, self-tested (two independent numpy-only instruments,
`validate_construction6.py` and `validate_growth_law.py`, both under a second, no corpus/model/
network), **not wired into the engine**. `coning.cpp` cones the complex topologically but carries no
sheaf data (`ConeResult` has no `F(w)`/legs); `hodge_split` in the engine takes a scalar cochain
(graph Hodge split), not a sheaf one.

### III.5 The contextuality bridge — a well-posed open problem, not a claim
🔵 **Upgraded from `[SPECULATION]` to `[OPEN, well-posed]`** [SEARCHED]. Both halves are standard,
separately: **Abramsky–Barbosa–Mansfield** (arXiv:1111.3620): Čech cohomology on an abelian presheaf
built from the **support** of a probabilistic model, obstruction = a cohomology class, nonvanishing
for PR boxes/GHZ/Peres–Mermin/Cabello's 18-vector configuration. **Hansen**, *Laplacians of Cellular
Sheaves*: "the space of harmonic cochains coincides with the space of global sections" — confirms
MOS's own side outright. The intersection is **not an established area** (searched as two separate
literatures). Precise difference table: base space (measurement contexts vs. complex of concepts);
coefficients (presheaf of **distributions** vs. sheaf of **vector spaces**); obstruction question
(does a global distribution **exist**? vs. is `H⁰` **nontrivial**?). The real gap, sharper than
"different coefficients": a sheaf of vector spaces always admits the zero global section, so MOS's
obstruction is fundamentally about **dimension**; Abramsky et al.'s is about **existence**. The
prerequisite is already discharged: an assembly is structurally a measurement context, and
`concept_store.hpp` already establishes `{Δ(A_t)}` is a good cover with the **nerve-lemma hypotheses
verified exactly**, not assumed (§III.6) — the technical precondition for a Čech argument. Named as
a genuine thesis-sized problem: bridge by working with distributions on the assembly cover, or show
the linear version is a genuine linearisation of the ABM one. Proposed toy object: a cellular sheaf
whose stalks are quantum states, whose Laplacian is a Hamiltonian (`L_F` Hermitian PSD ⇒
`e^{−iL_Ft}` unitary), whose ground space is the globally-consistent assignments, whose ground-state
energy is a contextuality witness.

### III.6 The fine-store triangle rule — closing the b₁-swamping bug
✅ **A real bug found, diagnosed backwards once, then fixed cleanly with no new knob.**
❌ An earlier record ("no triangles ⇒ `b₁`=0 in the fine store, so the growth address can't fire
there") was **backwards**. For a 1-dim complex `b₁=E−V+b₀`; with no 2-cells `δ¹=0` so curl is
trivial and harmonic `=(im δ⁰)^⊥`, dimension **exactly** `b₁`. No triangles **maximises** `b₁`, it
doesn't zero it — and since each tick's assembly is inserted as a **clique**, `b₁(K_n)=(n−1)(n−2)/2`
— one 20-concept assembly alone contributes 171 artifact cycles. "The growth address was never
blocked; it was **swamped** by artifacts of inserting cliques and refusing to fill them."

**The fix, same signal, no new knob**: a 2-simplex `{a,b,c}` is recorded **exactly when its three
concepts co-fired in one assembly** — the edge rule, one dimension up. Justified rigorously, not
just cheaply: (1) the 2-skeleton of a simplex is simply connected ⇒ every within-assembly cycle
dies, no tetrahedra needed; (2) `H₁` depends only on the 2-skeleton ⇒
`b₁(filled)=b₁(⋃_tΔ(A_t))`; (3) `{Δ(A_t)}` is a **good cover** (simplices contractible, pairwise
intersections are simplices or empty) ⇒ **the nerve lemma applies with its hypotheses verified
exactly** (unlike the Čech-cover construction below, whose analogous claim is only suggestive).
**⇒ `b₁`(fine complex) = `b₁`(assembly nerve).** Surviving cycles are genuinely cross-assembly.

✅ Measured: filled cliques go from `b₁=(n−1)(n−2)/2` at n=3,5,7,10 to **0**, while a 3-assembly
necklace keeps `b₁=1` — the real hole survives.

⚠️ **Two costs stated before building**: (i) triangle count `Σ_t C(|A_t|,3)` is fine at assembly
width 20 (~1.7M/1500 ticks, ~100MB) but not at width 50 (~29M, ~2GB) — **cap is mandatory, not
prudent**, since retrieval was an unbounded threshold scan and `|A|` had no ceiling at all;
`max_assembly_for_triangles=30` is **derived** from the RAM budget, and skips are **counted, never
silent** (`skipped_wide_assemblies()`), because a skipped assembly's `(n−1)(n−2)/2` cycles survive
as harmonic mass indistinguishable from a real hole. (ii) this makes edge-sharing triangles the
*normal* configuration — a coupled-τ_f scenario V7 had flagged as untested; ✅ **discharged**
(measured `corr(τ_f,τ_f′)=+0.29` over 840 edge-sharing pairs, harmonic vector moves only `1.67e-14`
under it — V7's analytic argument never depended on triangle count).

🚨 **A methodology trap, recorded because the positive control is the only reason it was caught**:
the first coupled-τ_f test ran on a filled `K₇`, which is **contractible** (`b₁=0`, harmonic space
identically zero) — "asking whether `W₂` moves a vector that is always the zero vector. Unfailable,
therefore worthless," and it would have printed a confident `1e-15` PASS. The positive control
(perturbing `W₁`) returned `1.5e-29` instead of something large, exposing the vacuous design.
Rebuilt on a necklace (edge-sharing **and** a real `b₁=1`). *"Always compute what a statistic does
when the effect is absent, before reading it when present" — recurred a third time in this
project.* Related trap: `b₁=E−V+b₀−F` (the Euler formula) is **wrong** once triangles share edges
— `δ¹` may not have full row rank (filled `K₇`: `F=35`, `rank(δ¹)=15`, Euler gives a nonsensical
`−20`) — **compute `b₁` from ranks**, always.

⚠️ Consequence nobody asked for: `F_MOS`'s coface term now has `n−2` terms per edge instead of 1 and
scales **exactly linearly** with cofaces/edge — any `κ_hi`/`κ_lo` calibrated when every edge had one
coface is now stale and must be re-quantiled after real assemblies exist.

---

## PART IV — GEOMETRY: WHICH METRIC FOR WHICH JOB

### IV.1 The dispatch rule — information geometry vs. optimal transport
✅ **Resolved, and the resolution is a genuine theorem-vs-modelling-choice distinction, not an
arbitrary split.** MOS mixes two Riemannian structures on the same Gaussian-stalk objects:
`π_v` fusion `= (ΣΣ_i⁻¹)⁻¹(ΣΣ_i⁻¹μ_i)` is **information/Fisher–Rao/KL** geometry (a genuine MLE
for `n` independent noisy measurements of one latent — a theorem); `W₂` distance is
**Bures–Wasserstein optimal transport** geometry. These *genuinely disagree*: by Agueh–Carlier,
the Wasserstein barycenter of Gaussians has the **plain** weighted mean, not the precision-weighted
one. **Rule: ESTIMATION → information (the MLE has a derivation, do not touch); COMPARISON →
transport (accounts for spread, quantum-native).** `π_v`/pairwise fusion/entropy diagnostics →
information; merge/split/`ω`/`ρ`/Karcher mean → transport. "Estimation is where a theorem exists,
comparison is where a modelling choice exists — never blend into the first."

⚠️ **The seam, a paper-owed paragraph not a bug**: `π_v` **fuses** in information geometry but its
output is **immediately compared** in transport geometry by `ω` — `π_v` is *not* the
transport-barycenter of its own fine complex. "A referee who knows Agueh–Carlier will find it."

🔴 **Training a blend weight between the two geometries — rejected, four reasons**, kept because
the reasoning generalises: (1) it reintroduces exactly what an earlier fix removed — replacing a
choice-of-geometry-with-a-reason by a fitted-constant-with-none is the backwards move; (2) no
training signal exists (VerifyOp answers "is this true," not "are these the same concept"); (3) one
scalar needs a **sweep**, not an optimizer — "an optimizer buys an overfitting failure mode and
nothing else"; (4) the two uses are asymmetric — blending damages a proven MLE for a fitted number.
**Interpolating for distance only is legitimate** (see IV.2); training the interpolation weight is
not.

### IV.2 Cone–Bures — δ recovered, then measured down to a smaller claim
Charbel explicitly refused to accept the loss of a concept-identity length scale and asked for an
all-out attempt after the natural candidate (Wasserstein–Fisher–Rao) failed to have a closed form
(❌ **E15, searched**: WFR/Hellinger–Kantorovich has **no** closed form between two arbitrary
Gaussians — the nearest results either regularize into a different object (entropic OT) or need a
per-pair **Riccati solve**, ~2–3 orders of magnitude slower than Bures for all 21 edges combined.
"Per the project's own stated FAIL condition, Q2c collapses to theory. The merge metric stays plain
Bures–Wasserstein.")

✅ **The construction (Cone–Bures), genuinely recovered δ**: HK is a cone metric over *any* base
metric space (`r=√mass`, `d²=r₀²+r₁²−2r₀r₁cos(min(d_base,π/2))`) — nothing requires the base to be
`ℝ^d`. Build the cone over **(Gaussian space, Bures–Wasserstein)** instead, with mass = the existing
Hebbian weight `w(σ,t)` (decay destroys it, reinforcement creates it — "WFR's reaction term IS
bind/collapse, not an import"). Derivation gives
`D_δ² = w_0+w_1−2√(w_0w_1)cos(min(d_BW/2δ,π/2))`. ✅ Proven and measured a genuine metric (20,000
random triples across five δ, worst violation `+0.000e+00`), rank-k reduction to a `p×p` (`p≤2k`)
square root (`5.45 ms/tick` for 21 edges vs. Riccati's `~10¹⁰–10¹¹` flops/tick), exact day-one
degradation to weighted Bures as `δ→∞`, and — independently — kills the E4 epistemic-term runaway
because `D²` **saturates** at `w_0+w_1` beyond `πδ` (bounded by construction).

★ **Empirical law found**: `HK_true² ≈ D²/(1+σ²/δ²)` to ~3% over a 10× spread range, where `σ` is
the stalks' spread. ❌ **The obvious correction, `D̃²=D²/(1+σ_eff²/δ²)`, breaks the metric** —
"usable as a ranking score, never as a metric; merge transitivity is lost."

🚨🚨 **The regime claim inverted, twice, and both errors are worth keeping as a lesson.**
1. First measurement of "how concentrated are MOS's stalks" read the wrong norm — `‖U‖_F` instead
   of spread **along the separation direction**, `σ_dir²=ûᵀΣû`. Corrected reading gave
   `σ_dir/δ≈0.09` ("the BEST row of the agreement table — ~87% predicate agreement, sub-1% value
   gap") — but this correction was itself computed on a **calibrated simulation**, not real text.
2. ✅ **Measured on real text** (project's own DOCS, 11 organs): `σ_dir/δ` measures **0.32
   (median), 0.42 (max)** — ~4× worse than the simulation. "The number the whole closeness claim
   rested on was simulated; measured, it is worse." Diagnosis, arithmetically exact: not `σ_dir`
   (came in only ~2× the simulated value), it's the **between-organ separation** — real
   same-project, same-author prose separates by only ~0.5 in `d_BW`, vs. 1.3–1.4 assumed. Against
   the project's own agreement table, `σ/δ≈0.32` is **~60% merge agreement, not the claimed 87%**.

🔴 **Two attempted rescues, both failed or bounded small**: (a) a "D̃" correction turned out to be
**vacuous by a general fact** — "multiplying a score AND its threshold by the same number cannot
change any decision," and D̃ is always smaller than D, so a D̃-based predicate returns True for
*every* pair. The **actual** fix was reframing it as a length scale, `δ_eff=√(δ²+σ_dir²)`
(spread adds to the identity scale in quadrature — physically right), which is a real, monotone,
never-splits-what-D-merges correction, but its motivating benefit was **never separately measured
against exact HK** — it remains a defensible construction, not evidence. (b) A better organ
**definition** (k-means, deliberately circular as a best-case bound) buys only **−22.9%** and makes
the **tail worse** (max `σ_dir/δ` 0.396→0.466) — "does not approach 87%, and honest expectation for
any real, non-circular definition is less."

✅ **Final ruling, accepted by Charbel**: **KEEP** Cone–Bures as a metric (everything that earned it
a place survives: genuine metric, bounded, derived length scale, deletes a hand-set threshold).
**DROP** the closeness-to-true-HK claim. **MONITOR, NEVER CLAIM** `σ_dir/δ` as telemetry. Note for
scope: **Cone–Bures is not wired into the engine at all** — `coherence.py` has zero Bures
references; the falsified claim was about a proposed upgrade, not a working mechanism.

### IV.3 What a concept "is" — geometric summary
✅ Combining III.3's Gärdenfors result with the Fisher-Rao/transport split: a concept's **extent**
(`Σ`) is a convex Gärdenfors region under the information metric it's estimated in, and its
**distance to other concepts** is measured in the transport metric that accounts for that extent's
spread. A concept is not a point; treating it as one (the Python `(label,vector,weight)` layer,
still live and inconsistent with the C++ layer at close of V0) throws away exactly the structure
this whole geometry programme built.

---

## PART V — RETRIEVAL: THE EMPIRICAL SAGA

### V.1 The bug, measured
✅ **The largest-magnitude measured defect in the project.** `SearchOp` computed a relevance
**threshold** (`max(0.1, 1/dim)` — the `1/dim` branch is dead for any `dim>10`, so it's always 0.1)
against **squared** Bures–Wasserstein distance, and `KnowledgeBase::get_relevant_concepts` was an
**unbounded threshold scan with no LIMIT** — `|A|` bounded only by corpus size, not any constant.
Against **2266 author-asserted ground-truth dependencies** (built free from `\ref`/`\label` graphs
in 71 arXiv papers — no hand-labelling, no LLM budget): this scheme admits **0.31%** of true
dependencies. On the engine's real 1115-abstract corpus, at the shipped default: **literally zero
of 3000 ticks retrieve a pair at all** (93.4% of ticks empty).

**Root cause 1 — it's a near-duplicate filter, not a relevance filter.** For unit vectors,
`‖Δμ‖²=2(1−cos)` exactly, so `≤0.1` means `cos≥0.95` — a paraphrase threshold. Root cause 2 — a
**pedestal**: mean pairwise cosine of unrelated bge-small embeddings sits around 0.6–0.8 regardless
of topic (later measured precisely: `‖μ̄‖²=0.671`, unrelated-pair cos mean 0.669, cited-pair cos
mean 0.777, separation `z=1.92`) — a large common-mode offset that any absolute-distance threshold
mostly measures. Root cause 3 (secondary but real, and load-bearing): the epistemic term
`d·(√D₁−√D₂)²` is **d-extensive** while the semantic term `‖μ₁−μ₂‖²≤4` is **d-intensive** —
summing them at `d=384` lets the epistemic term dominate by two orders of magnitude regardless of
meaning. `D=1.0` (not a tuning choice — "the unique value at which the semantic term decides
relevance") was the engine's actual coupling that made this survivable at all; any fix touching
embedding norms must preserve `D₁=D₂` or reintroduce this ~230–346 penalty.

### V.2 The fix, and what it is not
✅ **Rank, don't threshold. Rank on cosine, not squared distance.** `‖μ_q−μ_i‖²` includes `‖μ_i‖²`,
which does **not** cancel across candidates (unlike `‖μ_q‖²`), and stored means are **not**
unit-norm (`π_v` is a weighted centroid, norm falls the broader the concept) — squared-distance
ranking would silently penalise general concepts for a reason unrelated to the query. The 46.6%
recall figure below was measured on cosine ranking specifically; ranking by squared distance is a
different, unmeasured ordering and would invalidate the acceptance criterion.

✅ **Measured**, against the 2266-label ground truth: **rank-based retrieval at width ~25 gets
46.6% recall, vs. 37.5% for the best-matched ε-ball at the same width** — "nine points free, and it
eliminates the variance entirely." Centering the embeddings (removing the corpus mean, "all-but-
the-top") is worth a further **~+4 points**. Abandoning the *absolute* threshold in favour of *any*
rank-based scheme is worth **0.31%→44.2%, ~140×** — "the whole A-vs-B-vs-C design argument [ε-fix
vs. k-NN vs. centering] was about a 4-point effect; the actual fix was worth 140×."

❌ **Diffusion/heat-kernel retrieval, refuted**: 12 configurations, none beats raw cosine, recall
degrades monotonically with diffusion time. Mechanism: the pedestal makes pairwise distances nearly
equal, the kernel nearly constant, the walk nearly uniform — "diffusion distance ends up dominated
by the stationary distribution, i.e. by degree — it amplifies hubness rather than removing it."

⚠️ ❌ **Two claims about the fix were themselves overstated and walked back in a self-audit**:
(1) `abtt-10` (centering + removing the top 10 principal components) was reported "best" — it was
**argmax on a flat sweep** (`abtt-1`/`-5`/`-10` all land at 48.3–48.5%, indistinguishable once the
**effective sample size** (~71 papers, not 2266 correlated labels) is accounted for). Corrected:
removing the mean + a **small** number of PCs is worth ~+4 points [MEASURED]; `r=1`
[ENGINEERING CHOICE], for simplicity. (2) `k=24` was reported "derived, not chosen" (from a
triangle-storage budget coinciding numerically with `C(24,3)×3000≈6.1M`) — **[ENGINEERING CHOICE]
after correction**: the triangle budget itself is an unmeasured flop/memory estimate, recall rises
**monotonically** in `k` (35.5% at k=10 → 53.4% at k=50, so 24 is where a cost constraint bites,
not where quality peaks), and "two independent constraints landing on the same number is exactly
the tidiness motivated reasoning produces." [OPEN HYPOTHESIS] whether retrieval width *should*
equal the topology budget — never tested (vary `k` against measured `b₁`).

✅ **What survives all corrections, the two results to keep if everything else here is wrong**:
rank-based retrieval over the ε-ball (0.31%→46.6%, large, measured), and the fixed-margin null
catching a false positive in the cover test (Part VI) on identical data (p=0.02→0.45, direct).

**Status at close of V0**: the fix is validated on labelled data and in a Python simulation but was
**never ported into the C++ engine** — `src/operators/primitives.cpp:58` still computes a threshold
and `concept_store.hpp` still confirms an unbounded scan. This is **P0** of §7's blocking list
(Part IX) and — per `SPEC_P1_TO_P4_PROTOTYPE.md` — was subsequently marked done (commits `111ad33`,
`d9fa46d`); confirm this against current source before relying on it.

---

## PART VI — COVER VS. PARTITION: FOUR FAILED TIER-0 ATTEMPTS

### VI.1 Two constructions for "what is an organ"
🔵 **Construction 4 — organs as an overlapping cover, coarse complex as its Čech nerve.**
A k-simplex appears exactly when k+1 organs share a concept — "interdisciplinary knowledge literally
creates higher-dimensional simplices," making "simplices = honest n-ary relations" true *by
construction* rather than by promise. **The cover is the state** (persistent objects with birth
time, accumulated concept set, growing via the typed structural ops), **the nerve is the
observable**, recomputed on demand — this is the resolution to the trap of a naive nerve just
repeating FCA's mistake (data-determined, recomputed each time). ⚠️ **Amended same day it was
proposed**: the claimed filtration is actually a **zigzag** (Carlsson–de Silva) — `split` and
`decay` reverse the simplicial-map direction that `grow`/`birth`/`merge` produce forward, so
standard persistent homology cannot consume the whole history uniformly. Fixed by restarting the
filtration at each split/decay event (an epoch boundary), not by adopting full zigzag persistence.
Also amended: "cover element" was used in two incompatible senses (geometric region vs.
combinatorial concept-set) — resolved to the **combinatorial** reading (a cover element is a
persistent concept-ID set; the geometric reading reintroduces circularity through soft membership).

🔵 → ✅ **Construction 5 — the cover element DERIVED: organs as latent causes of co-activation
(a noisy-OR generative model), superseding Construction 4's undecided "what is a cover element."**
The model-class choice is not stylistic: a **mixture** (one cause per event, convex combination) is
structurally a **partition** (provably cannot represent overlap); a **noisy-OR** (several causes
superpose additively, no normalisation) is structurally a **cover**. "COVER ⟺ ADDITIVE latent
causes. PARTITION ⟺ CONVEX latent causes" — this gives Construction 4's purely structural argument
a **statistical, falsifiable** characterisation (fit both, compare on held-out data). The objective
is variational free energy = accuracy + complexity = MDL — "the same free-energy principle already
used to derive `π_e`, not a new import" — and unlike a naive within-organ-spread sweep (which is
monotone by construction and *cannot* have an interior optimum), `F(K)` **can** have one, because
accuracy improves in `K` while complexity grows `O(KN)`. ★ Thresholding the recruitment
probabilities `θ` to build a nerve was Mapper's most-criticised knob; instead, filtering by
`w(S)=Σ_cΠ_{i∈S}θ_ci ≥ τ` gives a **provably monotone filtration** (`N_τ' ⊆ N_τ` for `τ'≥τ`, and
`N_τ` is closed under faces, both proved by hand) — the overlap knob **dissolves into a filtration
parameter**, and the nerve theorem is no longer even needed (`N_τ` is *defined* from `θ`, not
approximating anything).

**A 16-test, 4-tier gated battery was written before any implementation** (Tier 0: is the model
class right, cheap kill-shots including "does noisy-OR actually beat mixture on held-out
likelihood"; Tier 1: is the fit an artefact (nulls, restart stability, identifiability); Tier 2:
does the topology earn its place; Tier 3: does the cover actually **grow**, or is it "the hand-set
list with extra steps" — the FCA-rejection discipline, made testable). ⭐ Test 14 is the sharpest:
refit `θ` with embeddings **permuted** — must be **bit-identical**, or embedding geometry has leaked
into a construction whose entire point was metric-independence.

**Status at close of V0**: Construction 5's *instrument* is built and validated on synthetic ground
truth in both directions (recovers a planted cover, recovers a planted partition). **It has never
been run on MOS's own corpus** — needs accumulated real assembly records, which the engine only
began producing near the end of the record. Its underlying API also has **no structural operations
at all** (no split/merge/birth/decay) — "the cover is a batch EM fit, not a grown object" — so the
epoch-length question (T13) doesn't merely lack data, it lacks a *subject*; it dissolves rather than
being answered, with an explicit re-open trigger for the day typed structural ops land on the cover.

### VI.2 Four attempts to test cover-vs-partition on real data — all inconclusive, each diagnosed
This sequence is worth keeping in full: it is the corpus's strongest demonstration that a null
model and a positive control are not optional add-ons, they are the difference between a false
positive being reported as a finding and being caught.

**Attempt 1 — global likelihood margin, mixture vs. noisy-OR on ticks.** ❌ Instrument invalid: a
tick was a top-k ball around one query point — **one cause by construction**, so the test's own
answer ("partition") was fixed *before any data was seen* — a textbook **Modifiable Areal Unit
Problem** (MAUP: results vary artifactually with the size/shape of the aggregation unit; the
standard remedy is to sweep the unit and report sensitivity, never pick one). **Compounded by a
second, independent bug**: the null model used **free** row margins (independent Bernoulli
draws), while real rows have a fixed size — on identical data, this flipped the verdict from
`p=0.4500` (no evidence) to `p=0.0200` (**COVER**) purely by changing the null to fixed-margin. "Had
Tier 0 run as originally planned, it would have returned COVER and we would have believed it." This
is exactly the documented failure mode in ecology's null-model literature (Gotelli 2000: "the three
models that maintain fixed row sums are invulnerable to Type I errors") [SEARCHED, one of the few
citations in the corpus actually verified against the literature].

**Attempt 2 — per-concept bimodality vs. arXiv cross-listing labels.** ❌ Two independent failures.
The bimodality instrument was **blind without dimensionality reduction** — a positive control
(planted two-cluster data with a *known* separation) scored **0.0209 against a one-blob null's
0.0199** — "the first run measured nothing at all," because distances in `ℝ^384` concentrate;
PCA restores power only above ~40% of neighbourhood radius. Separately, the label was
**administrative, not semantic** — cross-listing is a filing decision; a genuinely mono-topic paper
can carry two tags. (A related correction: the corpus's own "74% cross-listed" claim, once checked
*inside* the corpus rather than against all of arXiv, was **10.7%** — "seven times smaller than
recorded.")

**Attempt 3 — same bimodality score, against a citation-derived (non-administrative) label.**
❌ Zero signal (real AUC at or below its own geometric null). Root cause identified precisely:
the label is **logical/argumentative** ("this lemma is invoked over there"); the score is
**similarity-geometric** ("this block's neighbourhoods split"). These are different relations, and
the disagreement was *already independently measured* elsewhere in the same project (recall@30 ≈
44–48% between citation and embedding similarity, Part V) — "that number was measured days earlier
and not connected before the run." A confound caught mid-run: the raw label statistic was predicted
by in-degree alone at AUC 0.748 (more citers mechanically widens a span regardless of bridging) —
corrected by normalising to expected range, conclusion held.

**Attempt 4 — per-concept transitivity deficit (open triangles) vs. a fixed-margin curveball
null**, reframed on Charbel's instruction to ask "what observation would force us to believe overlap
is *necessary*." ❌ **The instrument itself is refuted**, not merely underpowered: across four
weight-thresholding settings, **there is no parameterisation where a synthetic cover's planted
bridges are recovered in the correct direction AND a structure-free geometric control stays clean
simultaneously** — wherever the geometric control is clean, planted bridges score on the **wrong
side** (inverted). ★ Caught *before* interpretation: the real corpus showed 87.8% of concepts at
`z>2` against a clean geometric control's 0.1% — "without the cover control that would have been
reported as a decisive positive. The fourth artifact this week, and the first that never reached a
conclusion."

**What is established after all four attempts, and what is not.** ✅ Established:
retrieval was broken and is fixed (0.31%→46.6%); the legacy null manufactures false positives and
is fixed; the corpus carries a **real, unexplained transitivity deficit** reproduced by neither the
margin-preserving null nor plain ball geometry (its shape — near-universal rather than confined to
a minority of concepts — [SPECULATION] "looks more like a continuum than K discrete patches," but
the instrument that produced it fails its own control, so this is a hunch). ❌ **Not established:
anything about whether MOS's memory has cover structure.** "Four failures to reject the partition
are not evidence that the partition is true." **Acceptance criterion for any future Tier-0
instrument, earned the hard way**: must pass a synthetic partition, a synthetic cover *with planted
bridges recovered in the right direction*, and a structure-free geometric control, **at one shared
parameter setting**, before ever touching real data. None of the four met it.

### VI.3 Prior art — cover detection is not novel, and that's fine
🔴 **Explicit non-claim, load-bearing for any future paper**: cover-vs-partition detection has
mature machinery in at least four fields — ecology's fixed-margin null-model debate (Gotelli;
curveball/Strona et al. 2014 for **unbiased** fixed-margin sampling, since the project's own
Gumbel-top-k sampler was found to hit the right *support* but not sample it *uniformly*);
geography's MAUP; Bayesian nonparametrics (the mixture-vs-noisy-OR question is IBP-vs-DP "in
different clothing" — the IBP also **infers** the cause count, which the project's hand-guessed
`K=6` never did); network science's OSLOM (per-community significance, degrading gracefully when
most of a corpus is partition-like, exactly this corpus's case); and TDA's documented **Lattice
Effect** (on dense covers, the nerve can capture the geometry of the cover construction itself
rather than the underlying structure — the name for a failure mode the project predicted from first
principles before finding the term for it). "MOS cannot claim contribution there... What remains
genuinely MOS's own: the sheaf over the cover, the growth law, the accumulating-not-recomputing
engine, the 𝕂/W architecture. The cover is infrastructure — infrastructure should be borrowed, not
invented." ⚠️ All these citations are flagged unread from search summaries except where marked
[SEARCHED] above — verify before citing.

---

## PART VII — THE PIVOT: FROM RETRIEVAL-AS-GEOMETRY TO A GENERATIVE MODEL

This is where V0's own investigation arrived at a conclusion structurally identical to the one
driving the V0→V1 restart — worth reading as the project's own earlier, narrower version of "the
architecture as built cannot do the thing we actually want," now generalised by the user to the
whole kernel, not just retrieval.

### VII.1 The diagnosis (six independent measurements, one conclusion)
✅ Each of six measurements, made for different reasons across the retrieval and cover work, points
at the same missing component: **MOS has never had a memory system that decides what to retrieve
about — only a lookup table with a similarity metric.** Tick `t` and tick `t+1` are independent
events; nothing carries state, attention, inhibition, expectation, or surprise between them. In
particular: (1) retrieval cannot live in the metric alone — twelve metric-improvement attempts
bottomed out around a 4-point effect while the *rule* (threshold→rank) was worth 140×; (2) it cannot
live in a single relation — citation and embedding-similarity agree only ~47% of the time, "no
single edge type can serve as memory"; (3) it cannot live in the corpus — Attempt 1's generator
would return "partition" even on a corpus engineered to be 100% overlapping; (4) there is real,
structured signal in the co-activation data that is currently uninterpretable precisely because
nothing controls how the activity was generated; (5) ✅ **demonstrated directly, not argued**: on
*identical* data, fits, and observed statistic, only changing the null's generative assumption
flipped `p=0.02→0.45` — "when the generating process is mis-specified, the conclusion inverts."

### VII.2 The trap this pivot must not fall into
⚠️ **Stated as the load-bearing warning for whatever comes next, and it applies with extra force to
a V1 that is a self-mutating kernel rather than a scored complex**: "A simulator produces the
topology its rules imply." Moving from "assume a cover, test for it" to "simulate cognition, observe
the emergent topology" is a genuinely stronger design — and is *also* Attempt 1's exact failure
mode, at ten times the scale, harder to catch because a sufficiently complicated generator can hide
its own assumptions inside its update rule rather than its retrieval rule. **The only stated
escape**: no claim about emergent structure until a **validation battery of human-memory signatures
not fitted to** — serial position curve, semantic clustering (Bousfield), fan effect (Anderson),
spacing effect, and above all **lag-CRP with forward asymmetry** ("THE decisive one, no free
parameter to hide in") — passes on held-out signatures, built and tested **before** the simulator
that's meant to be scored against it. "Building the test first makes it impossible to tune the
model to the test without noticing. Every failure in this project came from building an instrument
and a result at the same time."

### VII.3 The proposed tick loop (design only, never built)
🔵 A `cue → activation spread (recurrent) → k-WTA competition → assembly → Hebbian update` loop with
seven state variables, each justified by a specific signature it must produce, not by intuition:
activation `a` (the assembly itself), context `c` (drifting, cues retrieval — predicts lag-CRP),
working memory (recency/capacity), **fatigue `φ`** (without it the system provably collapses to a
fixed point and freezes — see §I.1's Lyapunov argument, later derived independently in the sheaf
formalism as the same object), base-level strength (spacing/practice), goal context (source
clustering), inhibition (sets assembly size **emergently**, deleting the hand-set `k=24` — "the
single cleanest argument that this architecture is an improvement rather than an elaboration,"
passing the discipline test by deletion). Edge weights proposed as a **five-term sum**
(semantic + episodic/Hebbian + temporal/directed + predictive + task-context), explicitly flagged:
"five new knobs — must be learned or derived, never hand-set, or the circularity trap has already
closed." The directed/temporal term is flagged [OPEN HYPOTHESIS] as "possibly the most interesting
mathematical question the new architecture raises" — it would make the coupling matrix `J` genuinely
asymmetric, changing what the sheaf cohomology even means.

**Prior art explicitly borrowed, not reinvented** [unsearched citations, flag before use]: Temporal
Context Model / CMR (Howard & Kahana; Polyn–Norman–Kahana) for the drifting-context Layer 1; ACT-R +
k-WTA for activation/competition; the Successor Representation (`M=(I−γT)⁻¹`) for the dynamic graph,
explicitly identified as "precisely 'activation history → weighted dynamic graph.'" ✅ **The 𝕂/W
sheaf split, independently, is a candidate genuine formalisation of Complementary Learning Systems**
(McClelland/McNaughton/O'Reilly 1995) — "if so, that is the paper, not 'we invented a two-store
memory.'"

**Phased build with hard behavioural gates (G0 skeleton → G1 context, gated on lag-CRP → G2 full
state, gated on every ablation changing something → G3 multi-source edges → G4 long-run generation
→ G5, only now, topology)** — proposed, **no phase begun** at close of V0.

### VII.4 A correction ledger against an external draft (`PRECILLA/draft.md`), kept as a template
9 numbered corrections applied to an external design document while integrating it — kept because
several are generic category errors worth checking for in any future draft, not just that one: a
dimensional type error (`ℝ^d` context vector added directly to an `ℝ^N` activation vector, missing
a required `V∈ℝ^{N×384}` embedding matrix — this also silently forced `d=384`, not a claimed
`d≈100`); a symbol collision (`W` used for both the working complex and a coupling matrix — renamed
`J`); a missing noise model (probabilities computed downstream with no stochastic source declared
upstream — "the draft declared a measure without a kernel for it to belong to"); "not fitted" that
was actually fitted (an upper-triangular successor matrix installed by hand, with forward asymmetry
then presented as *derived* from it — "the asymmetry was inserted, not predicted"); an
unacknowledged identifiability failure (two of five proposed edge-weight components are collinear by
construction, so a claimed "read off the weight" argument may be reading off nothing — "report the
Gram matrix and its condition number *before* learning anything").

---

## PART VIII — DEAD-END REGISTRY (consolidated)

A single table of everything explicitly refuted, rejected, or dissolved across the record, with the
reason, so none of it gets re-proposed without knowing why it died last time.

| what | verdict | why | where |
|---|---|---|---|
| Pachner moves as the structural-op vocabulary | ❌ killed 2026-07-22 | a knowledge graph is not a manifold; the preservation guarantee doesn't transfer | I.1 |
| Constant sheaf (identity restriction maps everywhere) | 🔴 abandoned | "obviously asinine" (Charbel) — identity maps on a connected graph make the reconciled state the plain average; no knowledge lives in the wiring | I.1, I.5 |
| FCA as the memory substrate | 🔴 rejected | data-determined; canonicity requires discarding the path-dependence that makes it a memory | II.1 |
| K₀/Jordan–Hölder canonical memory atoms | ❌ dropped | both candidate categories fail for opposite reasons; dissolved by growth-history identity instead | II.1 |
| Original growth law (`n > bd_v(1+Σd_e)/(c_old−c_new)`) | ❌ superseded | numerator overcounted by k; denominator size-independent, made `d_w=0` always optimal | III.4 |
| "Residuals of learned restriction maps" as a measured η | ❌ circular | still `(δx)_e` for the learned maps, still exact, still zero in H¹ | III.1 |
| τ_f-from-residual is circular | ❌ retracted (was itself wrong) | an invertible map cannot change an image; verified 8.4e-16 | I.5 |
| E5 run 1 "FAIL" verdict | ❌ retracted same day | p-value overstated ~4-10×; the statistic scored a known-positive control (0.214) the same as the "failing" data (0.209) | III.2 |
| D̃ merge-score correction | ❌ vacuous as a decision rule | multiplying a score and its threshold by the same factor cannot change any decision | IV.2 |
| Cone-Bures "tracks true HK to <1%" claim | ❌ does not survive real text | measured σ_dir/δ=0.32 (real) vs 0.09 (simulated); ~60% not 87% agreement | IV.2 |
| WFR/Hellinger-Kantorovich closed form for merge metric | ❌ doesn't exist for general Gaussians | nearest results are entropic (different object) or need a per-pair Riccati solve | IV.2 |
| Diffusion/heat-kernel retrieval | ❌ refuted | pedestal makes the walk near-uniform; amplifies hubness instead of removing it | V.1 |
| Alexandrov sheaves for directed cohomology | ❌ retracted | constant on each SCC; a dense recurrent J is one giant SCC, cohomology trivial by construction | III.5 |
| Attempt 1-4 Tier-0 cover instruments | ❌ all inconclusive/refuted | MAUP, blind instrument, label/score relation mismatch, no setting passes both controls | VI.2 |
| Legacy (free-margin) null for the co-activation matrix | ❌ manufactures false positives | fixed-width real rows vs. variable-width null rows — Type I inflation, matches Gotelli's documented finding | VI.2 |
| "abtt-10 is best" / "k=24 is derived" | ❌ downgraded on self-audit | both were reading an optimum off a flat sweep / an unmeasured budget coincidence | V.2 |
| Characteristic cycles / b-functions / HH¹,HH² / holonomic concepts (Tier C) | ❌ correct math, currently inert | every concept the engine produces is rank-1/multiplicity-1 — nothing for the machinery to act on yet | II.1 |
| HH² as the home of extension obstructions | ❌ wrong, checkable in a textbook | obstructions live in HH³ (Gerstenhaber); Ore extensions are unobstructed given (σ,δ) | II.1 |
| Random mutation as the growth mechanism (bacteria→human framing) | 🔴 rejected | variation-and-selection needs randomness *because it has no address* — MOS computes an address; adding randomness discards the architecture's asset | III.3 (concept formation) |

---

## PART IX — METHODOLOGY: THE DISCIPLINE ITSELF IS AN ASSET

These are process-level findings, not mathematical ones, but they were earned by repeated failure
across the whole V0 record and are exactly as load-bearing for V1 as any formula above — several
constructions above were only caught wrong *because* these rules were followed, or were nearly
reported wrong because they weren't followed yet.

- **A17 — "new mathematics earns its place only if it changes a number the engine prints, or
  deletes a decision a human was making by hand."** Applied consistently to admit `π_e`/`τ_f`/`δ`/
  `γ(∅)` derivations and to reject Tier-C D-module machinery, characteristic cycles, and a trained
  geometry-blend weight.
- **No measurement is reportable without a positive control.** Caught four distinct artifacts in
  the cover-detection work alone, the fourth (§VI.2 Attempt 4) *before* it became a false
  conclusion rather than after. "The rule earned today: no measurement is reportable without a
  positive control."
- **Any classifier/instrument must pass a synthetic positive, a synthetic negative, AND a
  structure-free geometric control, at one shared parameter setting, before touching real data.**
  Derived specifically because three of four Tier-0 attempts would have reported a confident,
  wrong verdict without this.
- **Always compute what a statistic does when the effect is absent, before reading it when
  present.** Recurred at least three separate times (E5's original PASS criterion scoring 0.400 on
  pure noise; the coupled-τ_f test on a contractible `K₇`; the cover instrument's Attempt 4).
- **Effective sample size, not label count.** Correlated labels (e.g. 2266 `\ref` edges from only
  71 papers) make every naively-computed confidence interval too narrow; cluster by the true
  independent unit before trusting a p-value.
- **Never read an optimum off a flat sweep.** Happened twice, the second time in a document citing
  the first as the reason not to.
- **Epistemic-status tags on every load-bearing claim**: `[MEASURED]` `[DERIVED]` `[INFERRED]`
  `[ENGINEERING CHOICE]` `[OPEN HYPOTHESIS]` `[SPECULATION]`. Adopted specifically because the
  failure mode of one particular week was never bad statistics — "it was good numbers attached to
  conclusions they do not support," and the tag makes the mismatch mandatory to notice rather than
  optional.
- **A superseded "NEXT — blocking" line is worse than no line at all** — it re-blocks work that was
  already unblocked. This exact failure recurred **four separate times** (the memory-schema
  question F10, a stale `Q2b 🔴` marker, a duplicated "Phase 3" numbering, and the `b₁`-swamping
  claim being recorded backwards) — always caught late, always costing real time. Renumber/retract
  stale planning lines the moment they're superseded, not when convenient.
- **Log decisions to a durable record as they land, not at session end** — an early retrospective
  write-up nearly lost the FCA-rejection reasoning and the Prop-8.2-blocks-growth connection.
- **Checkpoint long jobs; a job whose partial progress is worth nothing is a bug in the job.** Cost
  a 10+ minute machine-melting ingest that produced zero rows.
- **Time one full unit of work before extrapolating.** A 15-minute wall-clock estimate became 90
  minutes by naively multiplying two sample draws.
- **Prior art before implementation.** Cover detection alone cost roughly a week that ecology,
  geography, Bayesian nonparametrics, and TDA had each already spent, under different names.
- **Plain-language-first, math-second, worked example before any symbol** — the one explicit
  process correction Charbel gave on communication style, after two complaints that explanations
  were "clouding everything with technicalities," and the one that worked: he re-derived a correct
  answer to the growth-address question independently once it was taught this way.

---

## PART X — STATUS AT CLOSE OF V0 (§7's P0–P4)

For orientation, since this is what V0 was closing out when the V1 restart was decided (per
`TATIANA_LOGBOOK.md` §8). Track A (working research tool) vs. Track B (genuine model of cognition)
were explicitly separated late in V0 — **V1 is squarely Track B, generalised**: not just retrieval
needing a generative process instead of a static metric, but the whole kernel needing to generate
and mutate its own structure rather than being an externally-scored, externally-dispatched complex.

- **P0 (retrieval fix into the C++ engine)** — validated on labelled data, ported per commit
  history; verify against current `src/operators/primitives.cpp` before trusting.
- **P1 (`support` name→vertex-id resolution)** — designed, not confirmed implemented; flagged as
  "the one thing that could be wrong in a way tests would not catch" (whether operad vertex ids and
  `ConceptStore` insertion indices share one id space).
- **P2 (VerifyOp hooked to a real checker)** — three-tier design (internal consistency → citation
  grounding → Lean/sandbox), Tier 3 explicitly out of scope for a first pass. Not wired.
- **P3 (confirm Q(t) moves)** — a diagnostic to run, not yet run at the point the record stops;
  three distinguishable causes pre-registered for why it might not (retrieval, verdict never
  reaching VERIFIED, or `R^W≈R^𝕂` genuinely).
- **P4 (one end-to-end run)** — reference problem on record: eigenvalues of the Hodge–Laplacian on
  differential forms of `ℂℙ³` (also the two-qubit pure-state space). Explicitly **not** a
  correctness test — "the answer is the least interesting output" — an instrumentation run, whose
  real deliverable is a first accumulated trajectory (`A(t)`, `ρ(t)`, `Q(t)`, `‖R^W−R^𝕂‖`).

**What Track A never needed and Track B (V1) needs from the ground up**: the generative model of
Part VII. That pivot — from "score a static structure" to "generate the structure's own history" —
is the V0-scale precedent for the V1 restart the user has now generalised to the whole kernel.
