# DERIVATION — THE GROWTH LAW'S COST SIDE

*Opened 2026-08-08. Track B, and it is **paper work with near-zero compute** — it can run in parallel
with P1–P4 (logbook §7).*

**State (2026-08-11): §5 — the *shape* of a new concept — is done and validated. The *cost* side was
wrong and is corrected here. §2 overcounted the model term by a factor of `k` (≈5×). §4 as boxed had
a degenerate optimum at `d_w = 0`: the empty concept costs nothing and, by §5.10, still kills the
hole, so the law read literally said *attach always*. §5.11 (Construction 7) replaces it with a
**per-direction** law that is derived, measured against exact code lengths, and needs no `F_MOS`.
§6 and §7 are rewritten. Second instrument: §9.**

Tags: `[MEASURED]` · `[DERIVED]` · `[PROPOSED]` · `[OPEN]`.

---

## 0. THE GAP THIS CLOSES

We have **where** and not **whether.**

The harmonic component of `η` names a cycle no ranking of concepts explains. But the law says only
*"there is a hole, fill it"* — and applied literally that fills **every** hole. `concept_store.hpp`
already warns from the other direction that `b₁` is easily swamped. **A criterion with no cost side
over-generates concepts**, and a memory that invents a concept for every unexplained loop has not
learned anything; it has memorised.

`[SEARCHED 2026-08-08]` Every neighbouring literature uses the same missing ingredient:

- **DreamCoder** — the sleep phase adds a sub-expression to the library **iff it reduces total
  description length**, and it extracts *common* sub-expressions, not any sub-expression.
- **Predicate invention** (ILP) — invent a predicate when the vocabulary cannot express the theory.
- **Chunking** — a chunk is *"a unit in a maximally compressed code"*, formalised via MDL.

**The law we want:** *attach a concept over a cycle that **recurs**, and only when the recurrence
pays for the attachment.*

This document turns that sentence into an inequality.

---

## 1. THE SETUP

Minimum description length, in its two-part form:

$$L_{\text{total}} \;=\; \underbrace{L(\text{model})}_{\text{the memory}} \;+\; \underbrace{L(\text{data}\mid\text{model})}_{\text{the experience}}$$

**Model** = the complex `C` plus the sheaf `F`. This is what MOS *is*.
**Data** = the observed record: the sequence of assemblies `A(1), A(2), …` and the succession
relation `η` read off it. This is what MOS has *seen*.

A new concept is worth inventing exactly when it lowers the **sum**. Not the model term — adding a
concept always raises that. Not the data term alone — you could drive that to zero by memorising
everything. The sum.

---

## 2. THE MODEL TERM

### 2.1 ⚠️ CORRECTION — the first version overcounted by a factor of `k`

An earlier draft priced the cone as one stalk plus `k` independently described restriction maps:

$$\Delta L(\text{model}) \;\overset{?}{=}\; b\,d_v\Big(1 + \textstyle\sum_{e \in \gamma} d_e\Big)$$

**Wrong, and wrong for the same reason the triangles are free.** `[DERIVED]` The cone condition
(§5.4) is `r_i^+ p_{i+1} = r_i^- p_i`. MOS's restriction maps are **orthogonal** (Householder;
`Π_{O(d)}` in consolidation), hence invertible, so

$$p_{i+1} \;=\; (r_i^+)^{-1} r_i^-\, p_i .$$

**`k − 1` of the `k` legs are determined by the first and by maps the decoder already holds.** Only
`p_1` is described. `[MEASURED, §9 [C]]` the propagated legs satisfy `δ⁰ = 0` to `0.00e+00` in all
three sheaf configurations.

The same computation says where `p_1` may live. Round the loop once, `p_1 = H p_1` with the
**holonomy** `H = (r_k^+)^{-1}r_k^- ⋯ (r_1^+)^{-1}r_1^-`, so

$$\varprojlim D_\gamma \;\cong\; \ker(H - I) \;\subseteq\; F(v_1).$$

⭐ **This is the implementable form of Construction 6**: `k` matrix products and one eigenspace at
`d = 384`, not a nullspace in `k·d` dimensions and no sheaf Laplacian anywhere. See §6.6.

### 2.2 The corrected term

`N = |V|` is the concept count.

| item | count | cost |
|---|---|---|
| the leg `p_1` — i.e. a basis of the concept inside `F(v_1)` | 1 | `b · d_w · d_v` |
| the other `k − 1` legs | `k−1` | **0** — propagated, §2.1 |
| the stalk's Gaussian `(μ_w, U_w, D_w)` | 1 | `b(d_w + d_w k_w + 1)` |
| triangles | `k` | **0** — implied by the cone |
| the address of `γ` | 1 | `≈ k·log₂ N ≈ 50` bits |

$$\boxed{\;\Delta L(\text{model}) \;=\; b\,d_w\big(d_v + k_w + 1\big) \;+\; b \;+\; k\log_2 N\;}$$

**Three things to notice.**

**(i) Still linear in `d_w`** — which is what lets §5.11's prefix rule work. But the coefficient is
`b·d_v`, not `b·k·d_v`. At `d = 384, k = 5` that is a **4.98×** overcount removed, and it moves the
recurrence threshold from ~2000 traversals to ~300 (§9).

**(ii) A stalk is a Gaussian, not a vector space.** `rank_k_stalk.hpp` stores `N(μ, UUᵀ + D·I)`. The
old `d_v · b` counted the mean only. `k_w`, the covariance rank, is a **second** size parameter that
§5.11's selection rule does not address — carried forward as `[OPEN]` in §6.

**(iii) The address of `γ` is not free.** The earlier draft omitted it. At ~50 bits against ~2000 for
the leg it changes no decision, but a two-part code whose decoder cannot locate what it is being told
is not a code.

**(iv) Triangles are free.** Unchanged, and now with company: they are *implied* by the cone, so the
`k` new 2-cells cost nothing to describe. This is why coning is cheap relative to what it buys.

---

## 3. THE DATA TERM

`[DERIVED]` Let cycle `γ` occur `n` times in the record — meaning `n` distinct occasions on which
the succession pattern traversed it.

Without the concept, each traversal must be coded as `k` separate transitions, none of which any
global ranking explains, so each costs its full surprisal. With the concept, the traversal is a
single event: *"the thing `v` names happened."*

$$\Delta L(\text{data}\mid\text{model}) \;=\; -\,n\,\big(c_{\text{old}} - c_{\text{new}}\big)$$

where `c_old` is the cost of coding one traversal the long way and `c_new` the cost of naming it.

**This is where frequency enters, and it enters as a derivation rather than a preference.** A cycle
seen once saves `(c_old − c_new)` and pays the full model cost. A cycle seen a thousand times saves a
thousand times as much for the same price.

> ⚠️ **`c_old − c_new` is written here as a constant, and that is the defect §5.11.1 diagnoses.** It
> must depend on **how much of the loop the concept actually reproduces** — otherwise a concept that
> carries nothing saves as much as one that carries everything. §5.11 supplies the dependence.

---

## 4. THE LAW

> ⚠️ **SUPERSEDED BY §5.11.4.** This section is kept because the *shape* of the argument survives —
> a threshold on recurrence, computed rather than chosen — and because the way it fails is
> instructive. Two things are wrong with it: the numerator overcounts by `k` (§2.1), and the
> denominator does not depend on the concept's size, which makes `d_w = 0` optimal (§5.11.1). Use
> §5.11.4.

Attach iff `ΔL_total < 0`:

$$\boxed{\;n \;>\; \frac{b\,d_v\big(1 + \sum_{e \in \gamma} d_e\big)}{c_{\text{old}} - c_{\text{new}}}\;}$$

**Read what this is.** A **recurrence threshold that is computed, not chosen.** It is the ratio of
what the concept costs to store against what it saves per use — the number of times a pattern must
repeat before it is worth naming.

Three consequences, and the second and third were not asked for:

1. **`n` is a number the engine can print.** A17, passed.
2. **It orders the holes.** Several harmonic classes compete; fill in decreasing `|ΔL_total|`. **That
   deletes a decision we had not even noticed we were handing to a human.**
3. **It predicts non-attachment.** A one-off inconsistency is *noise to be tolerated*, not a concept
   to be invented. The old law had no way to say that, which is exactly how it would have
   over-generated.

---

## 5. ⭐ CONSTRUCTION 6 — THE CONED CONCEPT

*The stalk of a newly-grown concept, derived rather than chosen. This section is the finalised
construction; §5.6 corrects a claim made earlier in this document's own drafting.*

### 5.1 The data

Let `γ = (v₁, e₁, v₂, e₂, …, v_k, e_k, v₁)` be a 1-cycle in `C` carrying harmonic mass, with
`e_i = {v_i, v_{i+1}}` (indices mod `k`). Write the existing restriction maps as

$$r_i^- := F_{v_i \trianglelefteq e_i} : F(v_i) \to F(e_i), \qquad r_i^+ := F_{v_{i+1} \trianglelefteq e_i} : F(v_{i+1}) \to F(e_i).$$

### 5.2 The cone, topologically

Attach a vertex `w`, edges `f_i = {w, v_i}`, and triangles `t_i = {w, v_i, v_{i+1}}`.

`[DERIVED]` This kills the cycle. With `∂t_i = e_i − f_{i+1} + f_i`,

$$\partial\Big(\sum_i t_i\Big) \;=\; \sum_i e_i \;+\; \sum_i (f_i - f_{i+1}) \;=\; \gamma$$

— the `f` terms telescope to zero. **`γ` becomes a boundary.**

### 5.3 The new cells' stalks — the minimal choice, so nothing is smuggled in

$$F(f_i) := F(v_i), \qquad F_{v_i \trianglelefteq f_i} := \mathrm{id}.$$

The new edge carries `v_i`'s data undistorted. **`[ENGINEERING CHOICE]`, and a deliberately empty
one:** any distortion here would be a free parameter, and whatever the construction then achieved
could be attributed to a cleverly chosen edge stalk rather than to the concept. All the content is
forced into `F(w)` and the maps out of it, which is where we can reason about it.

The only remaining unknowns are `F(w)` and `p_i := F_{w \trianglelefteq f_i} : F(w) → F(v_i)`.

### 5.4 The derivation — the cone condition is forced, not imposed

Take a 0-cochain `x`. Along a new edge,

$$(\delta x)_{f_i} \;=\; F_{w \trianglelefteq f_i}\,x_w \;-\; F_{v_i \trianglelefteq f_i}\,x_{v_i} \;=\; p_i(x_w) - x_{v_i}.$$

So `δx = 0` on the new edges **iff** `x_{v_i} = p_i(x_w)` for every `i`:

> **The value at `w` GENERATES the section over the whole cycle.** That is what it means for a
> concept to explain a loop — the loop stops being `k` independent facts and becomes one.

Now require consistency on the *old* edges. Substituting `x_{v_i} = p_i(x_w)`:

$$(\delta x)_{e_i} \;=\; r_i^+\,p_{i+1}(x_w) \;-\; r_i^-\,p_i(x_w).$$

This vanishes for **every** `x_w ∈ F(w)` exactly when

$$\boxed{\;r_i^+ \circ p_{i+1} \;=\; r_i^-\circ p_i \qquad \text{for all } i\;}$$

**That is verbatim the definition of a cone over the diagram**

$$D_\gamma:\qquad F(v_1) \xrightarrow{\,r_1^-\,} F(e_1) \xleftarrow{\,r_1^+\,} F(v_2) \xrightarrow{\,r_2^-\,} F(e_2) \xleftarrow{\;} \cdots$$

with apex `F(w)` and legs `p_i`. **The categorical cone condition was not imposed on the
construction; it fell out of demanding that the topological cone do its job.**

### 5.5 The construction

> ### CONSTRUCTION 6 (the coned concept)
> $$F(w) \;:=\; \varprojlim D_\gamma, \qquad p_i \;:=\; \text{the limit's projections.}$$

**Concretely**, for finite-dimensional stalks,

$$\varprojlim D_\gamma \;=\; \Big\{(x_1,\dots,x_k) \in \bigoplus_i F(v_i) \;\Big|\; r_i^- x_i = r_i^+ x_{i+1}\ \ \forall i \Big\}$$

which is **exactly the space of sections of `F` restricted to `γ`**:

$$F(w) \;\cong\; H^0\big(\gamma;\, F|_\gamma\big).$$

> **What the new concept IS, in words.** *Everything that was consistent around the loop that could
> not be glued.* The concept does not summarise the cycle's members; it **is** the compatible part of
> them. That is "a clever amalgamation of what the others failed to derive", made exact.

**Three properties, and all three were requirements we had written down separately:**

| property | why it matters |
|---|---|
| **canonical** — unique up to unique isomorphism | no hand-made choice enters. A17 |
| **path-dependent** — depends on `D_γ`, i.e. on which cycle history produced | precisely the property whose absence got **FCA rejected** on 2026-07-27 |
| **degenerate case** | if `H⁰(γ; F\|_γ) = 0` the limit is the zero space. ⚠️ **See §5.9 — this branch turns out to be UNREACHABLE**, and the reason is a small theorem |

### 5.9 ⚠️ The refusal branch is unreachable, and that is a result

`[MEASURED 2026-08-08, python/validate_construction6.py]` An earlier draft of §5.5 claimed the
degenerate case is meaningful: *"nothing was consistent around that loop, so the construction refuses
rather than inventing."* **True, and it never happens.**

`[DERIVED]` For a 1-dimensional complex, `χ = dim C⁰ − dim C¹ = dim H⁰ − dim H¹`. On a `k`-cycle with
vertex and edge stalks of equal dimension `n`, `dim C⁰ = dim C¹ = kn`, so `χ = 0` and

$$\dim H^1(\gamma; F|_\gamma) \;=\; \dim H^0(\gamma; F|_\gamma).$$

With no 2-cells the harmonic space **is** `H¹`. So **a cycle carries harmonic mass if and only if it
has sections.** `H⁰ = 0` implies no harmonic mass, which implies no growth address, which implies the
growth law never fires on that cycle at all.

**The construction is never asked to refuse** — confirmed numerically: the degenerate case reports
*"harmonic space is EMPTY before coning — nothing to kill."* In general the gap is
`dim H¹ − dim H⁰ = k(n_e − n_v)`, so the branch could become reachable if edge stalks are ever given
a different dimension from vertex stalks. **Not currently.**

### 5.6 ⚠️ CORRECTION — the limit is NOT the MDL minimiser

An earlier draft of this document claimed `F(w) = lim` because *"the limit is the smallest object
admitting the required maps."* **That is backwards, and the error is worth keeping visible.**

`[DERIVED]` Every cone over `D_γ` factors **uniquely through the limit**. If a candidate `F'(w)` has
jointly injective legs — i.e. carries no data that no restriction map ever sees — that factoring map
is injective, so

$$\dim F'(w) \;\le\; \dim \varprojlim D_\gamma .$$

**The limit is the LARGEST non-redundant choice, not the smallest.** It is a *ceiling* on what a new
concept can usefully carry, not a floor.

So the two determinations are genuinely separate, and both are still derived:

1. **Consistency fixes the shape.** `F(w)` must be a cone; the limit is the universal one, and the
   ceiling.
2. **MDL fixes the size.** §2.2's cost is linear in `d_w`, so the optimum is a **subspace of the
   limit** — keep the directions that pay for themselves and discard the rest. Which ones, and how
   many, is §5.11.4.

`[DERIVED — was PROPOSED, resolved in §5.11.4]` The selection rule is by explanatory power: rank the
limit's directions by the intraclass correlation `ρ²_j` of their readings across traversals, and keep
the prefix satisfying §5.11.4's inequality. That the paying set is a **prefix** is now a consequence
of `Δc` being increasing in `ρ²` against a constant per-direction cost, not an assumption.

⚠️ **But note what §5.10 adds:** MDL is not merely *one* of the determinations of size — after §5.10
it is the **only** one, because every cone kills the class equally well, including the zero cone. So
this rule is not a refinement on top of a topological criterion; it is load-bearing on its own.

### 5.7 The cone in both senses

A **categorical cone** over a diagram is an object with compatible maps to every object in it.
A **topological cone** over a cycle is the cell that fills it.

**The growth operator is a cone in both senses simultaneously, and the limit is the universal one.**
§5.4 is the proof that this is not wordplay: the topological requirement (`δx = 0` across the filled
cycle) *is* the categorical requirement (`r⁺p_{i+1} = r⁻p_i`), written twice.

### 5.8 Provenance, and the variance trap

`[SEARCHED 2026-08-08]` The universal-property route to a new concept is **Goguen's**, not ours.
Algebraic semiotics computes a blend as the **categorical colimit** of the input specifications — *"a
general unification operation… which takes account of shared substructures"* — and the amalgam-based
model is provably equivalent to the pushout model in the ordered category of partial maps
[R2, R3, R4].

⚠️ **The direction is opposite to Goguen's and copying him would have got it backwards.** His inputs
map *into* the blend (colimit). A cellular sheaf's restriction maps point **vertex → edge**, so
`F(w)` must map *out* to the stalks (limit). The insight transfers; the variance does not.

**What is ours:** that the *sheaf's own restriction maps* supply the diagram, so no extra structure
is introduced — the concept is built from data the memory already had. **What is Goguen's:** that a
new concept should be a universal construction at all.

### 5.10 ⚠️ Killing the class does not select a size — RETENTION of `H⁰` does

`[MEASURED 2026-08-11, python/validate_growth_law.py]` §6.2 asked whether Construction 6 kills the
harmonic class and got YES. **The test was never at risk of returning anything else.**

`[DERIVED]` In the coned complex, with `F(f_i) = F(v_i)` and `F(t_i) = F(e_i)` (§8.1):

- `δ¹` is **surjective** — take `y_{e_i} = z_i`, `y_{f_i} = 0` — so `H² = 0`;
- a global section is `(x_w, (p_i x_w))`, determined by *and containing* `x_w`, so `dim H⁰ = d_w`;
- the Euler characteristic is `dim C⁰ − dim C¹ + dim C² = d_w + kn_v − (kn_e + kn_v) + kn_e = d_w`.

Hence `dim H¹ = dim H⁰ + dim H² − d_w = 0` **for every cone, at every size, including `F(w) = 0`.**

| `F(w)` | `dim F(w)` | `\|δ¹δ⁰\|` | harmonic after | `dim H⁰` after |
|---|---|---|---|---|
| `lim D_γ` — Construction 6 | 3 | `3.3e-16` | **0** | 3 |
| a 1-dim subspace of `lim` | 1 | `2.2e-16` | **0** | 1 |
| **`0` — the empty concept** | 0 | `0.0e+00` | **0** | 0 |

**Two consequences, and the second is the one that matters.**

**(i) §8.4's claim is too strong.** *"The only choice for which the coned object is a sheaf at all"*
is true of **cones**, not of **the limit**: every subspace of `lim` is also a cone and also a sheaf,
and the table above builds one. Corrected: **cone is forced; the limit is the terminal cone, hence
§5.6's ceiling.** The `δ¹δ⁰ = 0` test separates cones from non-cones (control: `3.805`) and nothing
finer. §5.6 and §8.4 could not both be read literally; §5.6 was right.

**(ii) No topological or cohomological quantity constrains `d_w`.** The hole dies either way. What
`F(w)` controls is **how much of the loop's consistent content survives as a global section** —
`dim H⁰` after equals `dim F(w)` exactly, in every row. So the figure of merit is **retention of
`H⁰(γ; F|_γ)`, not annihilation of `H¹`**, and the entire determination of size falls to MDL. If §4
is wrong, nothing else catches it. It was; §5.11.

### 5.10a The concept is exactly as large as the hole

`[DERIVED, then MEASURED]` §5.9 gives `dim H¹(γ) = dim H⁰(γ)` on a cycle with equal stalk dimensions,
and §5.5 gives `F(w) ≅ H⁰(γ; F|_γ)`. Therefore

$$\boxed{\;d_w \;=\; \dim \mathcal{H}(\gamma)\;}$$

— **the dimension of the harmonic space of the very cycle being filled.** §6.2's own table already
showed it (`3`/`3`, `1`/`1`) without remarking on it; §9 `[B]` asserts it in three configurations
including the degenerate one (`0`/`0`).

So `d_w` is **known before the decision is taken**, from the same computation that produced the growth
address. With §2.2, the model term is fully determined the moment the address is read.

### 5.11 ⭐ CONSTRUCTION 7 — THE DATA TERM, AND THE REPAIR OF §4

#### 5.11.1 ⚠️ Why §4 as boxed is not yet a law

§4 minimises `ΔL_total = b·d_w(1 + Σd_e) − n(c_old − c_new)`, in which `c_old − c_new` carries **no
`d_w` dependence at all**. Once §5.6 made the size a free variable, that is fatal:

$$\Delta L_{\text{total}}(d_w = 0) \;=\; 0 \;-\; n\,(c_{\text{old}} - c_{\text{new}}) \;<\; 0 .$$

**The empty concept costs nothing and, by §5.10, still kills the class.** Its threshold is `n > 0`.
Read literally, §4 says *always attach, with a concept that carries nothing* — which is §0's
over-generation returning through the **size** axis after being shut out of the **frequency** axis.

§4 was consistent while `d_v := dim lim` was forced. **§5.6 opened the hole; this section closes it.**
The missing dependence is not a patch — it is what falls out of doing the quantisation honestly.

#### 5.11.2 The setup

Fix a direction `u ∈ lim D_γ`, `‖u‖ = 1`, with components `u_i ∈ F(v_i)`. A **traversal** is one
occasion on which the cycle's vertices carried values `x_i ∈ F(v_i)`. Its `k` **readings** of `u` are

$$a_i \;:=\; \langle x_i, u_i\rangle / \|u_i\|^2 .$$

Because `u` is a **section**, the sheaf's prediction is exactly `a_1 = a_2 = ⋯ = a_k`, and the
concept's value is the common number. So *"is this direction worth naming?"* becomes *"do its `k`
readings agree?"* — a one-line statistic, and the reason the data term is computable at all.

#### 5.11.3 The two codes

Both codes send `k` reals per traversal on the same grid `δ`, so **`δ` cancels exactly** and the
residual half of the saving contains no chosen constant.

- **Without the concept:** each `a_i` under its own vertex marginal, variance `σ²_tot`.
- **With the concept:** send `s` once, then `k` residuals of variance `σ²_w`.

`δ_s := σ_w` is `[DERIVED, not chosen]`: the reconstruction error is `σ_w` however finely `s` is
sent, so bits spent below that floor buy nothing.

Write `ρ² := σ²_b/(σ²_b + σ²_w)`, the **intraclass correlation** of the readings. Then

$$\boxed{\;\Delta c(u) \;=\; \frac{k}{2}\log_2\frac{1}{1-\rho^2} \;-\; b_s, \qquad
b_s \;=\; \tfrac12\log_2\!\Big(1 + \frac{2\pi e\,\rho^2}{1-\rho^2}\Big)\;}$$

⚠️ **The `+1` in `b_s` is load-bearing, and its absence was a real error in this section's own
drafting.** The high-rate form `½log₂(2πe σ²_b/σ²_w)` **goes negative** when `σ_b < σ_w`, and no code
length may be negative; without the `+1` the saving diverges to `+∞` exactly where the direction
explains *nothing*. With it, `Δc → 0⁻`.

`[MEASURED, §9 [D]]` against the **exact** entropy of the quantised Gaussian: the closed form is
within **0.042 bits/traversal** over `ρ² ∈ [0, 0.995]`, and it **over**-prices `s`. So the threshold
it yields is **conservative — the law will under-attach, never over-attach.**

#### 5.11.4 The law

The model term is paid **once**; `Δc` is earned on **each** of the `n` traversals. So direction `u_j`
pays for itself iff

$$\boxed{\;n \;>\; \frac{b\,(d_v + k_w + 1)}{\Delta c(u_j)}\;,\qquad\text{and never if } \Delta c(u_j)\le 0.}$$

**Four things this buys; three of them were open items.**

1. **The `d_w`-dependence is back, and it is per direction.** Each direction of `lim` pays its own
   model cost and earns its own saving, so `d_w = |{\,j : n > n_j\,}|` — **the size of the concept is
   decided by how often the loop recurred.** That is §6.1, closed.
2. **The prefix rule is now a theorem, not a proposal.** `Δc` is increasing in `ρ²` and the per-direction
   cost is constant, so sorting by `ρ²_j` descending makes `n_j` increasing and `{j : n > n_j}` a
   **prefix**. §5.6's `[PROPOSED]` becomes `[DERIVED]`.
3. ⭐ **A criterion that is not frequency at all.** `Δc ≤ 0` below a reliability floor, **at every `n`**.
   No amount of recurrence buys a direction whose readings disagree. `[MEASURED, §9 [E]]`:

   | `k` | 3 | 4 | 5 | 8 | 12 | 20 |
   |---|---|---|---|---|---|---|
   | floor on true `ρ²` | 0.576 | 0.370 | 0.239 | 0.055 | 0.000 | 0.000 |

   Long cycles amortise the single transmission of `s` over more vertices and can be worth naming on
   weaker agreement; short ones cannot. **Neither the old law nor §4 could express this.**
4. **It does not need `F_MOS`.** See §6.3.

#### 5.11.5 ⚠️ The estimator is biased, by exactly `(1−ρ²)/k`

`[DERIVED, then MEASURED]` The coder estimates `s` by the mean reading `ā`, so `Var(ā) = σ²_b + σ²_w/k`
and the plug-in ICC is

$$\hat\rho^2 \;=\; \rho^2 + \frac{1-\rho^2}{k}\qquad\text{exactly.}$$

Measured to `< 3e-3` at `ρ² ∈ {0.9, 0.5, 0.2, 0}` (§9 `[F]`). **Pure noise reads as `ρ̂² = 1/k`** — at
`k = 5` that is `0.20`, comfortably inside the range an uncorrected threshold would find encouraging.
Unbias before thresholding:

$$\rho^2 \;=\; \frac{\hat\rho^2 - 1/k}{1 - 1/k}.$$

Control `[K3]`: shuffling each vertex's readings independently drives `ρ̂²` to `0.199` and the saving
to `−0.437` bits/traversal, against `+5.289` intact. **The saving measures the recurrence, not the
coder.**

---

## 6. WHAT IS ACTUALLY OPEN

1. **`[RESOLVED — §5.11.4]` The selection rule for the subspace.** The limit is the *ceiling*, not
   the minimiser (§5.6). The rule is: rank the limit's directions by the intraclass correlation
   `ρ²_j` of their readings, keep every `j` with `n > b(d_v + k_w + 1)/Δc(ρ²_j)`. The paying set is
   provably a **prefix**, and `d_w` is its length — **the size of a concept is decided by how often
   its loop recurred.**
2. **`[RESOLVED — but the test was vacuous; §5.10]` Does attaching Construction 6 kill the harmonic
   class?** YES — **and so does every other cone, including `F(w) = 0`.** `H² = 0` because `δ¹` is
   surjective, `dim H⁰ = d_w`, and the Euler characteristic is `d_w`; so `dim H¹ = 0` identically.
   `validate_construction6.py` confirmed the arithmetic but could not have failed. **The figure of
   merit is retention of `H⁰`, not annihilation of `H¹`.** §8.4's "only choice" is corrected there.
3. **`[RESOLVED — §5.11; `F_MOS` ROUTED AROUND]` `c_old` and `c_new`.** The old plan was surprisal
   under the model's transition distribution, which hooks `F_MOS` — still undefined, and
   `PRECILLA/draft.md` §10.1 still calls it *"the single largest gap"*. **Construction 7 prices
   sections instead of transitions**, using the stalks' own Gaussians (`rank_k_stalk.hpp`), which the
   engine already stores. It needs nothing that is not written down.

   ⚠️ **State the narrowing rather than hide it.** §1 defined the data as the assemblies **and** the
   succession relation. Construction 7 prices only the first — *what was there*, not *which
   succession fired*. It is therefore a **strict under-estimate** of the true saving, so the
   threshold is conservative and the law under-attaches. `F_MOS` would add the second half and can be
   added later as an extra positive term without changing anything derived here. **It is no longer in
   the way of the growth law.**
4. **`[OPEN — and it is a trap, not a quick win]` `b`, bits per real.** `½ log n` is the standard
   two-part-code answer, and it has two consequences the earlier note missed:
   - it makes the threshold **self-referential** (`n` on both sides). Harmless — the left side grows
     linearly and the right logarithmically, so the crossing is unique and two fixed-point iterations
     find it. §9 solves it this way.
   - ⚠️ **it is asymptotic, and it degenerates precisely where the growth law lives.** At `n = 1` it
     gives `b = 0`: the model is free, so a single traversal always pays. That is §0's
     over-generation again. **Do not adopt `½ log n` as "derived, therefore safe"** — use NML, a
     Bayesian marginal likelihood, or the engine's actual float width, and say which.
5. **`[OPEN]` `k_w`, the covariance rank of the new stalk.** §2.2 exposed a **second** size parameter.
   §5.11 selects `d_w` and says nothing about `k_w`. `rank_k_stalk.hpp`'s own argument (*"a concept
   grown from `n` observations has a scatter matrix of rank ≤ `n`"*) probably settles it, but it has
   not been checked against the cost side.
6. **`[OPEN — but now cheap]` Implementation.** `coning.cpp` cones the **complex** and carries no
   sheaf data: `ConeResult` has a `Complex2` and an apex name, no `F(w)` and no legs. And
   `hodge_split` takes a **scalar** cochain (one `double` per edge), so the engine computes the graph
   Hodge split, not the sheaf one. **§2.1 makes this a small job rather than a large one**: `F(w)` is
   `ker(H − I)` for the holonomy `H`, i.e. `k` matrix products at `d = 384` and one eigenspace. No
   sheaf Laplacian is required.
7. **`[OPEN]` Sequencing.** Filling one hole changes the complex and hence the others. Is greedy
   descent on `ΔL` optimal, or does it need lookahead? DreamCoder's answer is refactoring-aware search
   over *semantically equivalent* rewrites, which is more than greedy.
8. **`[OPEN]` The label.** `w` needs a name, and a name is not derivable from a diagram. **The one
   place an LLM is genuinely required and real novelty enters rather than being computed.** Name it
   as an oracle in the formalism rather than pretending it is derived.

---

## 7. ORDER OF WORK

1. ~~Check §6.2.~~ ✅ **DONE 2026-08-08** (§8) — and ⚠️ **re-read 2026-08-11**: it passed, but §5.10
   shows it could not have failed. The instrument was sound; the claim it tested was not the claim
   that needed testing.
2. ~~§6.1, the subspace rule.~~ ✅ **DONE 2026-08-11** — §5.11, measured in §9.
   ⚠️ **The old §7 had this at step 3 and `c_old`/`c_new` at step 4. That ordering was impossible:**
   §6.1's own proposal was *"rank by data-term saving"*, and the data term is what §6.3 was missing.
   §6.3 was always upstream of §6.1. Both are now done, in the right order.
3. **§6.5 next — `k_w`.** Cheapest remaining item, and it is the last free size parameter. Until it is
   settled, §2.2's model term has an unpriced degree of freedom.
4. **Then §6.4, `b`** — with the trap in §6.4 in mind. This is a *decision to justify*, not a formula
   to look up.
5. **Then §6.6, the C++.** In order: carry sheaf data through `cone_off_cycle`; compute `F(w)` by the
   holonomy route (§2.1); accumulate `ρ̂²` per direction per traversal; print `n_j`. The first two are
   pure linear algebra against `Eigen` and need no new theory.
6. **§6.7, §6.8** last.

**Nothing above needs the simulator, the corpus, or a single LLM call** — except §6.8, which is an
LLM by construction.

---

## 8. THE VALIDATION — `python/validate_construction6.py`

`[MEASURED 2026-08-08]` §6.2 was the cheapest way to refute §5, so it was run before anything was
built on top of it. Results in §6.2; this section is the **instrument**, so the numbers can be
re-derived rather than trusted.

### 8.1 What it builds

A cellular sheaf on a `k`-cycle with stalks `R^n`, then the cone over it per §5.2–§5.5, then the two
coboundaries, then the harmonic space of each.

**Sign conventions, stated because getting them wrong changes every number silently:**

```
    e_i = [v_i, v_{i+1}]        (δ⁰x)_{e_i} = r_i^+ x_{i+1} − r_i^- x_i
    f_i = [w, v_i]              (δ⁰x)_{f_i} = x_i − p_i x_w
    t_i = [w, v_i, v_{i+1}]     ∂t_i = e_i − f_{i+1} + f_i
```

with `F(f_i) := F(v_i)` (identity out of `v_i`, §5.3) and `F(t_i) := F(e_i)` (identity out of `e_i`,
and the existing `r_i^∓` out of the two `f` faces).

### 8.2 What it measures

Harmonic 1-cochains are `ker(δ⁰)ᵀ ∩ ker δ¹`, computed as the nullspace of the **stacked** map
`C¹ → C⁰ ⊕ C²` — legitimate because both are linear conditions on the same space. Rank decisions are
made once, by SVD, at a single tolerance.

Two numbers per case: the **dimension** of the harmonic space, and the **mass** of a specific cochain
`η`. `η` is drawn *from the harmonic space itself*, so its "before" mass is 1 by construction and the
"after" number is unambiguous — **no question of `η` having been mostly gradient all along**, which
is the obvious way this measurement could have flattered itself.

### 8.3 The controls — both mandatory, per the standing rule

| control | asserts | why it exists |
|---|---|---|
| **path** (tree, `b₁ = 0`) | harmonic dim `= 0` exactly | if a tree reports harmonic mass the instrument is manufacturing it and **no other number in the file counts** |
| **arbitrary non-cone `F(w)`** | `\|δ¹δ⁰\|_max > 0` | ⭐ without it, `δ¹δ⁰ = 0` might be an identity holding for *any* `F(w)` and would prove nothing. Measured: **1.756** |

### 8.4 What it returned that was not asked for

**[DERIVED, then MEASURED]** `(δ¹δ⁰x)_{t_i} = (r_i^+ p_{i+1} − r_i^- p_i)x_w`, so `δ¹δ⁰ = 0` **iff**
the cone condition holds. Measured: `4.4e-16` with the limit, `1.756` with an arbitrary `F(w)`.

> **The cochain complex is a complex if and only if `F(w)` is a cone over `D_γ`.** Being a cone is
> not a preference; it is the existence condition for the coned object to be a sheaf at all.

⚠️ **CORRECTED 2026-08-11 — this section originally read "Construction 6 is the *only* choice", and
that is too strong.** The test discriminates **cones from non-cones**, not the limit from its
subspaces: every subspace of `lim` is also a cone, also gives `δ¹δ⁰ = 0`, and also kills the class
(§5.10). What is forced is the *cone condition*; the limit is the **terminal** cone, i.e. §5.6's
ceiling. As written, §8.4 contradicted §5.6 — §5.6 was right.

### 8.5 Two errors the run caught in this document

**① "A generic rotation fixes nothing" is false in odd dimensions.** The degenerate case was written
expecting `dim lim = 0` for a generic element of `SO(3)`; it returned `1`. **Every element of
`SO(odd)` has eigenvalue 1**, hence fixes an axis, hence `H⁰(γ) ≠ 0` for any odd-dimensional stalk
with orthogonal restriction maps.

**A fact about MOS, not about the test.** MOS's restriction maps *are* orthogonal (Householder;
`Π_{O(d)}` in consolidation), so which degenerate cases are reachable is governed by **the parity of
`d`**. `d = 384` is even, so they are.

**② §5.5's "refusal" branch is unreachable** — corrected in §5.9, with the `χ = 0` argument that
makes `dim H¹ = dim H⁰` on a cycle.

### 8.6 To re-run

```bash
"$LOCALAPPDATA/Programs/Python/Python311/python.exe" MOS/python/validate_construction6.py
```

Python **3.11** specifically (project interpreter; `python` alone hits the Windows Store stub).
numpy only — no corpus, no model, no network. Runs in under a second, and **every assertion in it is
a claim from this document**, so a failure localises to a section number.

---

## 9. THE SECOND INSTRUMENT — `python/validate_growth_law.py`

`[MEASURED 2026-08-11]` §8 tested whether Construction 6 is a **sheaf**. This one tests the claims the
**cost** side rests on. Same discipline: every assertion is a numbered claim above, and it asserts
rather than prints, so a failure localises.

```bash
"$LOCALAPPDATA/Programs/Python/Python311/python.exe" MOS/python/validate_growth_law.py
```

### 9.1 What it asserts

| tag | claim | section | result |
|---|---|---|---|
| **A** | every cone kills `H¹`, including `F(w) = 0` | §5.10 | 3 sheaf configurations × 3 apex sizes, all `0` |
| **B** | `d_w = dim 𝓗(γ)` | §5.10a | `3`/`3`, `1`/`1`, `0`/`0` |
| **C** | `lim ≅ ker(H − I)`; the legs propagate | §2.1 | dims match; `δ⁰ = 0` to `0.00e+00` |
| **D** | the closed form for `Δc` **is** the code length | §5.11.3 | within `0.042` bits over `ρ² ∈ [0, 0.995]` |
| **E** | a reliability floor exists at every `n` | §5.11.4 | `ρ² > 0.576` at `k=3` down to `0` at `k≥12` |
| **F** | `ρ̂² = ρ² + (1−ρ²)/k`, exactly | §5.11.5 | error `< 3e-3` at four values |

### 9.2 The controls — three, all mandatory

| control | asserts | why it exists |
|---|---|---|
| **K1** path (tree, `b₁ = 0`) | harmonic dim `= 0` | if a tree reports harmonic mass the instrument manufactures it and no other number counts |
| **K2** arbitrary non-cone `F(w)` | `\|δ¹δ⁰\| > 0` | measured `3.805`, so **A** is not vacuous |
| **K3** readings shuffled per vertex | saving goes negative | `+5.289 → −0.437` bits/traversal. ⭐ Without it, **D** would be measuring the coder rather than the recurrence |

### 9.3 ⚠️ What it caught in this document

**① `b_s` went negative.** §5.11.3's first draft used the high-rate form `½log₂(2πe σ²_b/σ²_w)`, which
is negative whenever `σ_b < σ_w` — so the "saving" *diverged to `+∞`* exactly where the direction
explains nothing, and the reliability floor of `[E]` did not exist for `k ≥ 8`. Fixed by the `+1`, and
now checked against the **exact** quantised-Gaussian entropy rather than any closed form.

**② The estimator's bias.** `[F]` was not on the list of things to test; it showed up as a systematic
gap between the target `ρ²` and the measured one, in the same direction at every value. It is exactly
`(1−ρ²)/k`, so **pure noise reads as `ρ̂² = 1/k = 0.20` at `k = 5`** — and an uncorrected threshold
would have treated that as signal.

### 9.4 What the law then prints

`d_v = 384`, `k = 5`, one direction, `k_w = 1`, `b = ½log₂ n` solved self-consistently:

| true `ρ²` | `Δc` (bits/traversal) | `n` with §2 **as written** | `n` with §2 **corrected** |
|---|---|---|---|
| 0.99 | 11.89 | 775 | **110** |
| 0.95 | 7.27 | 1378 | **204** |
| 0.90 | 5.30 | 1987 | **300** |
| 0.70 | 2.26 | 5265 | **830** |
| 0.50 | 0.94 | 14122 | **2299** |
| 0.30 | 0.17 | 95569 | **16235** |

> **A recurrence threshold in the low hundreds for a reliable direction on a 5-cycle.** ⚠️ Read the
> `n` column as *conditional on §6.4*: `b = ½log₂ n` is the item §6.4 warns against adopting
> uncritically, and it is what sets the absolute scale here. The **ratio** between the two columns —
> `≈ 6.5×` — is not conditional on it, and is the cost of §2's overcount.

---

## REFERENCES

⚠️ **All searched 2026-08-08 under the §9 gate protocol. URLs verified as returned by search; author
lists and years are from search summaries and MUST be checked against the papers themselves before
any bibliography.** The logbook's standing rule.

### The universal-construction route to a new concept — Construction 6's provenance

- **[R1] Goguen, J.** — *algebraic semiotics*; conceptual blending given a representation-independent,
  mathematically precise account, with the core definitions **based on the notion of pushout**.
  Overview and further work: <https://cseweb.ucsd.edu/~goguen/papers/sm/node7.html>
- **[R2] Bou, Plaza et al.** — *Amalgams, Colimits, and Conceptual Blending* (CoInvent, ch. 1).
  **The amalgam-based category-theoretical model is essentially equivalent to Goguen's pushout model
  in the ordered category of partial maps**, and the theory generalises from pushouts to colimits,
  *"which capture the notion of putting together objects to form larger objects, in a way that takes
  account of shared substructures."* ⭐ **The load-bearing citation for §5.**
  <https://www.iiia.csic.es/~enric/papers/Ch1-CoInvent.pdf>
- **[R3]** *A computational framework for conceptual blending* — Artificial Intelligence.
  Blend computed as the **categorical colimit** of input specifications enriched with priority
  information (semiotic systems).
  <https://www.sciencedirect.com/science/article/pii/S000437021730142X>
- **[R4]** *A uniform model of computational conceptual blending* — Cognitive Systems Research.
  Computational realisations across representation formalisms.
  <https://www.sciencedirect.com/science/article/abs/pii/S1389041720300759>
- **[R5]** *ASP, Amalgamation, and the Conceptual Blending Workflow*.
  <https://www.researchgate.net/publication/280733527_ASP_Amalgamation_and_the_Conceptual_Blending_Workflow>

### What a concept is, so that a stalk is motivated rather than convenient

- **[R6] Gärdenfors, P.** — *Conceptual Spaces: The Geometry of Thought* (2000). **Concepts are
  CONVEX REGIONS**, not points. Convexity is argued, not assumed: categorisation extends by
  interpolation, colour-space division supports it empirically, and convex regions are easier to
  learn. Connects to prototype theory.
  <https://books.google.com/books/about/Conceptual_Spaces.html?id=FSLFjw1EcBwC> ·
  review: <https://junctures.org/index.php/junctures/article/download/134/138/252>
  > **[DERIVED]** A Gaussian stalk's level sets are ellipsoids, hence convex, so MOS's SPD stalk
  > **already is** a Gärdenfors region in the ellipsoidal case. This upgrades `Σ` from "a covariance,
  > needed for Bures" to **"the concept's extent, because concepts have extent."**
- **[R7]** *Conceptual spaces: a mathematical framework for concept engineering* (collection).
  <https://link.springer.com/collections/ehbihgjeah>

### The compression criterion — §1–§4's provenance

- **[R8] Ellis, K. et al.** — *DreamCoder: growing generalizable, interpretable knowledge with
  wake–sleep Bayesian program learning*, Phil. Trans. R. Soc. A **381**(2251), 2023. Wake phase
  solves with the current library; **sleep phase extracts COMMON sub-expressions and adds them as new
  primitives iff they reduce total MDL**, over semantically equivalent refactorings.
  ⭐ **The load-bearing citation for §3–§4** (frequency, not novelty, is the criterion).
  <https://royalsocietypublishing.org/rsta/article/381/2251/20220050/112456/DreamCoder-growing-generalizable-interpretable> ·
  full text + supplement: <https://www.cs.cornell.edu/~ellisk/documents/dreamcoder_with_supplement.pdf>
- **[R9]** *Inductive logic programming at 30: a new introduction* — **predicate invention**: invent
  auxiliary predicates rather than requiring all background knowledge up front; an ILP learner
  compensates for **missing** background predicates this way. Field's verdict: *"without predicate
  invention, learning always will be shallow."*
  <https://arxiv.org/pdf/2008.07912> · overview:
  <https://www.researchgate.net/publication/225190311_Predicate_invention_in_ILP_-_an_overview>
- **[R10]** *Chunk formation in immediate memory and how it relates to data compression* — a chunk as
  a unit in a maximally compressed code.
  <https://www.sciencedirect.com/science/article/abs/pii/S0010027716301470> · and
  *What's magic about magic numbers? Chunking and data compression in short-term memory*:
  <https://www.sciencedirect.com/science/article/abs/pii/S0010027711002733>
- **[R11]** *Minimum description length* — the two-part code, and the standard `½ log n` bits per
  continuous parameter that §6.4 must check `b` against.
  <https://en.wikipedia.org/wiki/Minimum_description_length>

### Sheaf side — the machinery Construction 6 is built on

- **[R12] Hansen, J.** — *Laplacians of Cellular Sheaves: Theory and Applications* (thesis).
  **The space of harmonic cochains coincides with the space of global sections.**
  <https://www.jakobhansen.org/publications/thesis.pdf>
- **[R13] Grigor'yan, Lin, Muranov, Yau** — *Homologies of path complexes and digraphs*
  (arXiv:1207.2834). GLMY path homology, the correct directed theory; **replaces the retracted
  Alexandrov proposal** (logbook §5bb).
  <https://arxiv.org/abs/1207.2834> · persistent version: <https://arxiv.org/abs/1701.00565> ·
  efficient 1-D algorithm (SoCG 2020, the dimension the growth address lives in):
  <https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.SoCG.2020.36>

### The M1 / quantum-information track

- **[R14] Abramsky, Barbosa, Mansfield** — *The Cohomology of Non-Locality and Contextuality*
  (arXiv:1111.3620, QPL 2011). Čech cohomology on an abelian presheaf built from the **support** of a
  probabilistic model; the obstruction is a cohomology class, non-vanishing for PR boxes, GHZ, the
  Peres–Mermin magic square and Cabello's 18-vector configuration.
  <https://arxiv.org/pdf/1111.3620>
- **[R15]** *Formalising and Learning a Quantum Model of Concepts* (arXiv:2302.14822) and
  *The Conceptual VAE* (arXiv:2203.11216). **A quantum model of concepts already exists — read
  before the thesis framing hardens.**
  <https://arxiv.org/pdf/2302.14822> · <https://arxiv.org/pdf/2203.11216>
- **[R16]** *Contextuality, Cohomology and Paradox* (arXiv:1502.03097) and *On the Cohomology of
  Contextuality* (arXiv:1701.00656) — follow-ups worth reading before committing to the bridge.
  <https://arxiv.org/pdf/1502.03097> · <https://arxiv.org/pdf/1701.00656>

### Behavioural side — carried from the G1 gate

- **[R17]** CMR / retrieved-context models: **start-list context reinstatement** fits primacy better
  than a learning-rate gradient alone; sCMR handles serial/free-recall dissociations.
  <https://collaborate.princeton.edu/en/publications/a-context-maintenance-and-retrieval-model-of-organizational-proce/> ·
  <https://d-nb.info/135447953X/34>
- **[R18]** Active inference: **precision is the inverse temperature in the softmax** and controls
  selection stochasticity — `τ² = 1/π_e` is standard, novelty disclaimed.
  <https://www.sciencedirect.com/science/article/pii/S0022249620300857> ·
  <https://activeinference.github.io/papers/process_theory.pdf>
