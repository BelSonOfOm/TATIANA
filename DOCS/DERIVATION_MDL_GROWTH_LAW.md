# DERIVATION — THE GROWTH LAW'S COST SIDE

*Opened 2026-08-08. Track B, and it is **paper work with near-zero compute** — it can run in parallel
with P1–P4 (logbook §7).*

**State: §1–§5 are done and §5 has been validated numerically (§8). §6 lists what is left; §6.2, the
item that could have voided everything after §4, is RESOLVED.**

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

`[DERIVED]` Coning a cycle `γ` of length `k` with a new vertex `v` adds:

| item | count | cost each |
|---|---|---|
| a vertex with a stalk | 1 | `d_v · b` bits, `b` = bits per real |
| restriction maps `F(v) → F(e)` | `k` | `d_v · d_e · b` bits |
| triangles | `k` | **0** — determined by the cone, not described separately |

$$\Delta L(\text{model}) \;=\; b\,d_v\Big(1 + \textstyle\sum_{e \in \gamma} d_e\Big)$$

**Two things to notice, and both matter.**

**(i) The cost is linear in `d_v`.** The dimension of the new stalk is the dominant free quantity, so
whatever fixes `d_v` fixes most of the cost. That is §5.

**(ii) Triangles are free.** They are *implied* by the cone, so the `k` new 2-cells cost nothing to
describe. This is why coning is cheap relative to what it buys — and it is a real asymmetry, not a
bookkeeping convenience.

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

---

## 4. THE LAW

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
2. **MDL fixes the size.** §4's cost is linear in `d_w`, so the optimum is a **subspace of the
   limit** — keep the directions that pay for themselves and discard the rest.

`[PROPOSED]` the natural selection rule is by explanatory power: rank the limit's directions by how
much data-term saving each yields (the dominant directions of the legs `p_i`), and keep the prefix
satisfying §4's inequality. **This replaces §4's `d_v` with a derived quantity and makes the
threshold computable.**

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

---

## 6. WHAT IS ACTUALLY OPEN

1. **`[RESOLVED — negatively, §5.6]` Is the limit the MDL minimiser?** **No.** It is the *ceiling*:
   the largest non-redundant cone, since every cone factors uniquely through it. The MDL optimum is a
   **subspace** of the limit. Consistency fixes the shape, MDL fixes the size; two separate
   determinations, both derived. **What remains open is the selection rule for that subspace**
   (§5.6's proposal: rank the limit's directions by data-term saving and keep the paying prefix).
2. **`[RESOLVED — MEASURED 2026-08-08]` Does attaching Construction 6 kill the harmonic class?**
   **YES, including in the twisted case.** `python/validate_construction6.py`:

   | case | `dim F(w)` | harmonic before | harmonic after | mass of `η` after |
   |---|---|---|---|---|
   | flat sheaf, trivial holonomy | 3 | 3 | **0** | `0.000e+00` |
   | **partial holonomy** (rotation) | 1 | 1 | **0** | `0.000e+00` |
   | degenerate, `H⁰ = 0` | 0 | **0** | — | unreachable, §5.9 |

   Controls, both required and both passed: a **path** (tree, `b₁ = 0`) reports harmonic dim `0`, so
   the instrument is not manufacturing mass; and an **arbitrary non-cone** `F(w)` gives
   `|δ¹δ⁰|_max = 1.756`, so the `δ¹δ⁰ = 0` check below is **not vacuous.**

   ⭐ **The stronger finding.** With `F(w) = lim`, `|δ¹δ⁰|_max = 4.4e-16`; with an arbitrary `F(w)`
   it is `1.756`. Since `(δ¹δ⁰x)_{t_i} = (r_i^+p_{i+1} − r_i^-p_i)x_w`, **the cochain complex is a
   complex if and only if `F(w)` is a cone over `D_γ`.** Construction 6 is therefore not a good
   choice among several — **it is the only choice for which the coned object is a sheaf at all.**
3. **`[OPEN]` `c_old` and `c_new` need actual code lengths.** The natural choice is surprisal under
   the model's own transition distribution, which hooks `F_MOS` — but `F_MOS` is still not written
   down as an equation (the largest gap flagged in `PRECILLA/draft.md` §10.1).
4. **`[OPEN]` `b`, bits per real.** Not free, and not arbitrary: MDL for continuous parameters
   normally uses `½ log n` bits per parameter (the standard two-part-code result). **If that is
   right, `b` is derived and not chosen** — check it before assuming.
5. **`[OPEN]` Sequencing.** Filling one hole changes the complex and hence the others. Is greedy
   descent on `ΔL` optimal, or does it need lookahead? DreamCoder's answer is refactoring-aware
   search over *semantically equivalent* rewrites, which is more than greedy.
6. **`[OPEN]` The label.** `v` needs a name, and a name is not derivable from a diagram. **The one
   place an LLM is genuinely required and real novelty enters rather than being computed.** Name it
   as an oracle in the formalism rather than pretending it is derived.

---

## 7. ORDER OF WORK

1. ~~**Check §6.2 first.**~~ ✅ **DONE 2026-08-08** — see §8. Construction 6 survives, and the check
   returned more than was asked of it.
2. **§6.4 next** — settle `b` from the standard two-part code (`½ log n` bits per continuous
   parameter). Cheap, and it may turn a constant into a derived quantity.
3. **Then §6.1**, the subspace-selection rule. Consistency already fixed the shape; this fixes the
   size.
4. **§6.3 is now BLOCKING rather than merely open.** `c_old` and `c_new` need real code lengths, the
   natural choice is surprisal under the model's own transition distribution, and that requires
   `F_MOS` **written down as an equation** — owed since `PRECILLA/draft.md` §10.1 named it the single
   largest gap. It has moved from "outstanding" to "in the way of the growth law."
5. **§6.5, §6.6** last.

**Nothing here needs the simulator, the corpus, or a single LLM call.**

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

> **The cochain complex is a complex if and only if `F(w)` is a cone over `D_γ`.** Construction 6 is
> not the best choice among several — it is the **only** choice for which the coned object is a sheaf
> at all. The universal property was never a preference; it is the existence condition.

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
