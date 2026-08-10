# DERIVATION — THE GROWTH LAW'S COST SIDE

*Opened 2026-08-08. Track B, and it is **paper work with zero compute** — it can run in parallel with
P1–P4 (logbook §7). This is a derivation IN PROGRESS: §1–§4 are done, §5–§7 are the work.*

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

## 5. ⭐ THE STALK — AND WHY IT IS THE SAME PROBLEM

`[PROPOSED]` §2 leaves `d_v` and the maps `F(v) → F(e)` undetermined, and §4's threshold depends on
them. **So "what goes in the new concept" and "when is it worth it" are one problem, not two.**

MDL answers both at once: **choose `F(v)` to minimise `L_total`.** The cost term pushes `d_v` down;
the data term pushes expressiveness up. The optimum is the *smallest* object that still admits maps
to every `F(e)` around the cycle compatibly.

That is a universal property. `[SEARCHED 2026-08-08]` — and it is precisely how the conceptual-
blending literature builds new concepts. Goguen's algebraic semiotics computes a blend as the
**categorical colimit** of the input specifications, *"a general unification operation… which takes
account of shared substructures"*; the amalgam-based model is provably equivalent to the pushout
model in the ordered category of partial maps.

⚠️ **Variance matters and the direction is NOT Goguen's.** His objects are specifications being
merged, so the blend receives maps *from* the inputs — a **colimit**. A cellular sheaf's restriction
maps point *from the vertex to the edge*, so `F(v)` must map *into* the `F(e)` — a **limit**. Same
insight (a universal property determines the new object, so nothing is chosen), opposite direction.

**And the pun is not a pun.** A categorical *cone* over a diagram is an object with compatible maps
to every object in it. A topological *cone* over a cycle is the cell that fills it. **The growth
operator is a cone in both senses simultaneously**, and the limit is the universal one.

> **`[PROPOSED]` — THE CENTRAL CONJECTURE OF THIS DOCUMENT**
> `F(v) = lim` of the diagram of stalks around `γ`, with the restriction maps its projections.
> Canonical (unique up to iso, so no hand-made choice), path-dependent (it depends on the diagram —
> on history — which is exactly the property that got FCA rejected), and **plausibly the MDL
> minimiser**, because the limit is the smallest object admitting the required maps.

---

## 6. WHAT IS ACTUALLY OPEN

1. **`[OPEN]` Is the limit the MDL minimiser?** "Smallest object admitting the maps" and "shortest
   description" are suggestively close and **not the same statement.** This is the theorem to prove
   or refute, and it is the load-bearing claim of §5.
2. **`[OPEN]` Does attaching the limit kill the harmonic class?** Coning kills the cycle
   *topologically* regardless of the stalk. Whether the **sheaf** cohomology class dies depends on
   `F(v)`. **If the limit does not kill it, §5 is wrong** — and this is the cheapest check in the
   document: build a synthetic 4-cycle with known non-vanishing harmonic mass, attach, recompute.
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

1. **Check §6.2 first.** It is a synthetic computation with a positive control and it can refute §5
   outright. If the limit does not kill the harmonic class, everything after §4 is wrong and it is
   better to know before writing more.
2. **Then §6.4** — settle `b` from the standard two-part code. Cheap, and it may derive a constant.
3. **Then §6.1**, the theorem.
4. **§6.3 waits on `F_MOS` being written down**, which is owed independently.

**Nothing here needs the simulator, the corpus, or a single LLM call.**

---

## SOURCES `[SEARCHED 2026-08-08]`

- DreamCoder — <https://royalsocietypublishing.org/rsta/article/381/2251/20220050/112456/DreamCoder-growing-generalizable-interpretable>
- Amalgams, colimits and conceptual blending — <https://www.iiia.csic.es/~enric/papers/Ch1-CoInvent.pdf>
- A computational framework for conceptual blending — <https://www.sciencedirect.com/science/article/pii/S000437021730142X>
- ILP at 30 (predicate invention) — <https://arxiv.org/pdf/2008.07912>
- Chunk formation and data compression — <https://www.sciencedirect.com/science/article/abs/pii/S0010027716301470>
- Minimum description length — <https://en.wikipedia.org/wiki/Minimum_description_length>
