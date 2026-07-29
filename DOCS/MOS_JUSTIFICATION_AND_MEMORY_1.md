# Justification and Memory

**Part I — every piece of technology, on trial: what it augments, what it costs, what it buys, how it is built.**
**Part II — memory as a structural object: atoms, gluing, retrieval, forgetting.**

Companion to *Scrutiny and Extension of MOS / TATIANA*. Same claims-and-non-claims discipline.

---

# Part 0 — The one-paragraph answer

Every technology below is admitted on a single test: **does it replace a hand-set number, an LLM call, or an approximate operation with something exact, canonical, or free?** Technology that merely renames an existing operation is rejected — that is the charge already laid against `δD` in the previous document. On this test, the list divides cleanly into three tiers, and the tiers are what should drive implementation order:

| tier | criterion | members |
|---|---|---|
| **A — pays immediately** | removes a magic number or a per-tick approximation, costs ~nothing | ρ-splitting, weighted Laplacian, clique polynomial / capacity, K₀-class memory, stratum-indexed retrieval |
| **B — pays on accumulation** | costs real compute, returns a measurement the system cannot otherwise make | Ext¹ promotion gate, Hodge decomposition on measured 1-cochains, composition-series memory, workload compression curve |
| **C — pays only at the frontier** | expensive, narrow, but decisive where it applies | full holonomic concepts, characteristic cycles, b-functions, HH¹/HH² neurogenesis |

Tier C is where the mathematics is most beautiful and least urgent. Say so out loud, because the failure mode of a framework like this is spending its budget on tier C while tier A sits unimplemented.

---

# Part I — Technology on trial

Each entry answers the same six questions: **augments what**, **replaces what**, **motivation**, **cost**, **implementation**, **what it gives**.

---

## 1. Splitting ρ into (α, ρ̃)

**Augments.** The controller, §13.

**Replaces.** The hand-fitted threshold ε ≈ 0.10, and the unexplained non-monotonicity of Remark 13.2.

**Motivation.** ρ is a product of two independent quantities that call for opposite remediations. It is not that ρ is imprecise — it is that ρ is *two measurements multiplied*, so no threshold on it can be correct for both.

**Cost.** One vector mean and one subtraction per tick. $O(|V|d)$, subsumed by work already done.

**Implementation.**
```
x̄  = mean over active organs of x_v
x⊥ = x − 1⊗x̄
α  = ‖x⊥‖² / ‖X‖²_F                        # dissent fraction
ρ̃  = ω / (B‖x⊥‖²)                          # mode index; ⊥ if ‖x⊥‖² < tol
window = [λ₂(L_K)/B , λ_max(L_K)/B]        # recompute on bind/collapse only
ε      = window.lo + q·(window.hi − window.lo)   # q a fixed quantile, e.g. 0.25
```
λ₂ and λ_max on a 7-vertex graph are a $7\times7$ eigendecomposition — microseconds, and only on topology change.

**What it gives.** Three things at once: (i) a threshold derived from the graph rather than fitted to three observations; (ii) a controller signal invariant to the organ-count dilution; (iii) a *typed* diagnosis — high α / low ρ̃ means the coalition wants restructuring, low α / high ρ̃ means one edge wants repair. The remediation is now aimed by kind, not just by argmax edge.

> **Non-claim.** This does not make ρ measure truth. It makes ρ measure disagreement without an encoder-geometry confound.

---

## 2. Weighted Laplacian $L_\pi$ with $\pi_e = w(\sigma,t)$

**Augments.** The coupling weights of Definition 9.3, which currently exist and are never read by the coherence computation.

**Replaces.** Nothing — it *connects* two existing subsystems.

**Motivation.** One of four declared growth axes (functional connectivity) is invisible to the only quantity computed every tick. A disagreement across a strongly-bound coalition and a disagreement across a nearly-decayed one currently count the same.

**Cost.** Zero. The lemma in the previous document shows $B_\pi = \max_{e=\{u,v\}}(d_\pi(u)+d_\pi(v))$ preserves the bound at the same $O(|E|)$.

**Implementation.** Two lines: weight the per-edge terms of Eq. (3) by $\pi_e$; compute degrees as weighted degrees.

**What it gives.** ρ becomes sensitive to *which* couplings are disagreeing. A decayed coalition's disagreement stops dominating the score, which is the behaviour you want during pruning. And it makes §15.1 a completed step rather than a proposal.

---

## 3. Clique polynomial and capacity κ

**Augments.** The operator algebra $\mathcal D$, §9, and the scheduler, §10.

**Replaces.** The absence of any measure of procedural reach.

**Motivation.** §9 calls $\mathcal D$ an algebra and gives it no product and no relations. The one relation the architecture *forces* is already stated in §10: operators with disjoint support commute. That single relation determines everything.

**Cost.** Cliques of the independence graph on $r$ generators. For a sparse support structure this is small; the polynomial is recomputed only when $\mathcal D$ changes. Tier A.

**Implementation.**
```
I  = {(i,j) : support(g_i) ∩ support(g_j) = ∅}
μ(z) = Σ_k (−1)^k c_k z^k        # c_k = # of k-cliques in I
H(z) = 1/μ(z)                     # Cartier–Foata
κ    = 1/r_min,  r_min = least positive root of μ
```

**What it gives.** Three uses from one polynomial, which is the test of whether an abstraction is earning its place:
1. $[z^m]H(z)$ = number of distinct $m$-step reasoning acts → **capacity**.
2. The Koszul dual has basis the cliques → **it is the scheduler's parallel-slice structure**. Sequential algebra and parallel layering are Koszul dual.
3. The Koszul/Anick resolution is indexed by the same cliques → this is the input to HH¹/HH² (§8 below).

---

## 4. Ext¹ as the promotion gate

**Augments.** Construction 9.4 (microneuron promotion) and §14's central untested bet.

**Replaces.** "Repeatedly resolves conflict and passes verification" — a heuristic — as the *structural* half of the promotion criterion.

**Motivation.** §14 states the bet (whole > sum) is unknown and that no elegance guarantees it. In an abelian category the bet has an exact form: a composite exceeds its parts precisely when the extension $0\to N\to E\to M\to0$ does not split, i.e. its class in $\mathrm{Ext}^1(M,N)$ is nonzero. A split composite is a bookkeeping convenience. A non-split one is the object the architecture exists to find.

**Cost.** Real. Ext¹ requires a free resolution. For rank-$k$ concepts ($k\le8$) this is feasible; for general holonomic modules it is not per-tick. **Ration it to promotion events only** — which is fine, because promotion is rare by design.

**Implementation.** At the promotion gate, in order:
```
1. VerifyOp(composite)             → if Refuted, discard.  (unconditional, first)
2. compute [E] ∈ Ext¹(M,N)
3. promote iff [E] ≠ 0
4. if [E] = 0: log as a *macro* (an abbreviation), not a generator
```
Step 4 matters: split composites are still useful as abbreviations, they just should not be counted as skill growth.

**What it gives.** A falsifiable, LLM-independent criterion separating genuine composite structure from renaming. It is the sharpest available form of §14's bet, and it prevents the failure mode where capacity is inflated by promoting useless independent operators.

> **Non-claim.** $\mathrm{Ext}^1\ne0$ does not mean the composite is *true* or *useful*. VerifyOp remains the sole arbiter of truth and runs first. Ext¹ answers only "is this structurally new."

---

## 5. Hodge decomposition on a *measured* 1-cochain

**Augments.** The diagnostic hierarchy §8, and the 2-simplices that Remark 2.2 justifies at length and the engine never uses.

**Replaces.** The currently vacuous $H^1$ reading (δx is exact by construction; its class is always zero).

**Motivation.** The $b_1$ / $H^1$ distinction is the conceptual heart of §8 and it cannot fire in the present formalism. Fixing it requires the engine to record *pairwise judgements* as primary data rather than deriving them from a global assignment.

**Cost.** Requires $\delta^1$, hence storing 2-simplices, hence $O(|F|)$ in the number of triangles. The decomposition is two least-squares solves. Medium; run on conflict, not per tick.

**Implementation.**
```
η ∈ C¹  := measured pairwise residuals (learned-restriction residuals,
            or explicit organ-vs-organ comparison judgements)
grad  = δ⁰ (δ⁰)⁺ η                    # least squares: best global explanation
curl  = (δ¹)ᵀ ((δ¹)(δ¹)ᵀ)⁺ (δ¹) η     # inconsistency around FILLED triangles
harm  = η − grad − curl               # inconsistency around UNFILLED cycles
```

**What it gives.** Three genuinely distinct diagnoses where there was one: *edit the stalks* (gradient), *repair a 2-simplex* (curl), *the loop is not closable — grow structure* (harmonic). The harmonic part is the real gluing failure, and it is the address that §15.6's selectionism needs and currently cannot compute.

---

## 6. Holonomic concepts (beyond Gaussian)

**Augments.** Definition 5.1.

**Replaces.** The Gaussian assumption — not the Gaussian *machinery*, which is preserved exactly as the multiplicity-1 case.

**Motivation.** Gaussians are holonomic of rank 1. Rank 1 means: *one* local instantiation consistent with the constraints. A great many real beliefs are not like that — a theorem with two inequivalent proofs, a concept with a genuine bimodality, a belief constrained to a variety rather than to a point. The current type system cannot represent them, and silently unimodalises them.

**Cost.** Honest and severe in general: Gröbner bases in the Weyl algebra $A_d$ are doubly exponential in the worst case, and $A_{384}$ is hopeless. **The saving grace is already in your design**: $\Sigma = UU^\top + DI$ with $k$ small means the real computation lives in $A_k$. Feasible to roughly $k\le8$. Ration like paraphrase-perturbation $J$.

**Implementation.** Widen the concept type to `(annihilator ideal I ⊂ A_k, ambient embedding)`, with the Gaussian case stored as today and only escalated when a concept is flagged multimodal or constrained. Fusion is $\otimes_{\mathcal O}$, which reduces to Eq. (13) on Gaussians — so nothing existing breaks.

**What it gives.**
- **Holonomic rank $r$** — a finite integer counting independent interpretations. The architecture currently has no analogue.
- **Multiplicity** — additive on exact sequences, hence a conserved quantity under belief composition.
- **Closure under the six operations** (Kashiwara), which is the finiteness discipline the growth axes lack.
- Rigid constraints become $i_+$ (Kashiwara's equivalence), which composes and handles non-linear constraint varieties — your projector $P$ is its linear shadow.

---

## 7. Characteristic cycles as connection potency

**Augments.** The stratification of §2.2, which currently only resolves a naming ambiguity.

**Replaces.** The scalar coupling weight, as a *description* of what a connection carries (the scalar is still fine as a decay variable).

**Motivation.** The request was a notion of connection strength beyond neural weights. A weight says magnitude. A restriction map says change-of-frame. A characteristic cycle $\mathrm{CC}(M)=\sum_\alpha m_\alpha[N^*_{Z_\alpha}X]$ says **where on the stratification the connection carries information, and with what integer multiplicity** — i.e. *"A determines B up to a 2-fold ambiguity, and that ambiguity is located on this stratum."* No scalar can say that.

**Cost.** Tier C. But — see Part II — CC's *combinatorial shadow* (the support pattern over strata) is cheap and is the piece that does the memory work.

**What it gives.** Additivity on short exact sequences (a conserved charge), and the Dubson–Kashiwara index theorem $\chi(X,\mathrm{DR}(M))=\mathrm{CC}(M)\cdot[T^*_XX]$, which welds the topological diagnostics of §8 to the operator invariants of §9 — currently two unconnected chapters.

---

## 8. HH¹ / HH² — the space of possible growth and its obstructions

**Augments.** The fourth growth axis $\delta\mathcal D$, shown in the previous document to be a Tietze transformation (i.e. to grow nothing).

**Replaces.** "Name a composite and call it a generator."

**Motivation.** Genuine extension means a new generator that is *not* a word in the old ones. Formally an Ore extension $\mathcal D[y;\sigma,\delta]$, which exists iff $\sigma$ is an endomorphism and $\delta$ a $\sigma$-derivation. Deformation theory then says exactly:
- $HH^1(\mathcal D,{}^\sigma\!\mathcal D)$ = **the space of admissible new operators**;
- $HH^2$ = **the obstructions to consistency**.

**Cost.** Requires the Anick resolution from the Gröbner presentation. For the trace algebra of §3 above, that resolution is indexed by the cliques already computed — so the marginal cost over tier A is much lower than it looks.

**Implementation pipeline.**
```
support structure → Gröbner basis → Anick/Koszul resolution → HH¹, HH² 
                                                     ↓
                          admissible neurogenesis + its obstructions
```

**What it gives.** The distinction the architecture most needs and currently cannot make: **compilation** (fixed algebra, refined filtration — real, measurable, and LLM-independent) versus **extension** (new generator, genuinely enlarging the algebra). And a measurement for the first: mean act-length in current atomic generators over a fixed held-out workload. If the architecture is learning, that curve falls. Note that GK dimension is invariant under change of generating set and therefore *does not* track this; the growth rate $\kappa_t$ relative to current generators does.

---

## 9. b-functions

**Augments.** The reconciliation flow of §7.

**Motivation.** The coherence locus $Z=\{\Phi=0\}$ has a singularity type, and it governs whether reconciliation is well-posed. The log-canonical threshold $\mathrm{lct}(\Phi)$, read off the roots of the Bernstein–Sato polynomial, measures degeneracy: small lct means the flow crawls and small perturbations reorganise the whole basin.

**Cost.** Tier C, and only meaningful once Φ stops being quadratic — which it must if rigid constraints ever become non-linear.

**What it gives.** A **pre-flight check**: is this reconciliation problem well-posed, computable *before* spending an LLM call on it. For the current quadratic Φ the Łojasiewicz exponent is ½ and the rate is exponential at λ₂ — the b-function is what generalises this.

---

## 10. Summary table

| technology | augments | cost | tier | headline return |
|---|---|---|---|---|
| ρ → (α, ρ̃) | controller | free | A | ε from graph invariants |
| $L_\pi$ | Hebbian axis | free | A | connectivity enters the measurement |
| clique polynomial | $\mathcal D$, scheduler | cheap | A | capacity + Koszul duality + resolution |
| Ext¹ gate | promotion | per-event | B | "whole > sum" made computable |
| Hodge on measured η | diagnostics | medium | B | three real diagnoses, located |
| holonomic concepts | concept type | $A_k$, $k\le8$ | C | rank, multiplicity, closure |
| characteristic cycles | strata | high | C | potency with location + integers |
| HH¹/HH² | $\delta\mathcal D$ | moderate given Anick | B/C | real neurogenesis vs. renaming |
| b-functions | flow | high | C | well-posedness pre-flight |

---

# Part II — Memory

The diagnosis is correct: storing memories as text blobs with embeddings is the weakest component of the architecture, and the addition of the algebraic layer makes it *worse* by contrast, because everything else acquires exact structure while retrieval stays approximate.

But the deeper problem is not the storage format. It is that **the framework has no answer to "what is a memory atom, and is the decomposition canonical?"** Without that, "abstract storage" is just a different blob. With it, everything else follows. So start there.

## 11. The atom question, and its answer

> **Jordan–Hölder.** In an abelian category, every object of finite length admits a composition series
> $$0 = M_0 \subset M_1 \subset \dots \subset M_n = M,\qquad M_i/M_{i-1}\ \text{simple},$$
> and the multiset of simple factors $\{M_i/M_{i-1}\}$ is **unique up to isomorphism and permutation**, independent of the chosen series.

Holonomic $\mathcal D$-modules form an abelian category in which every object has finite length. Therefore:

$$\boxed{\ \text{A memory has canonical atoms. They are its composition factors. The decomposition is forced, not chosen.}\ }$$

This is the exact thing being asked for — "a reduction to an atomic scale of memory" — and the point is that it is *not a design decision*. Two different ingestion paths, two different LLM parses, two different orderings all produce the same multiset of atoms. Compare: chunking a text file into paragraphs is arbitrary; embedding it is basis-dependent and encoder-dependent; both give different answers on Tuesday.

And the atoms come with a natural home. For a finite-length abelian category,
$$K_0(\mathcal C) \;=\; \bigoplus_{S\ \text{simple}} \mathbb Z\cdot[S],$$
so **the content of a memory is an integer vector of multiplicities.** Not a float vector. Integers, exact, comparable by exact set operations.

## 12. The two-part storage law

Jordan–Hölder gives the atoms and *loses the gluing* — that is precisely its content. So a memory decomposes into two parts, and they should be stored differently:

$$\text{memory } M \;\longmapsto\; \underbrace{[M]\in K_0}_{\textbf{content: what it is made of}} \;\;+\;\; \underbrace{\{[E]\in\mathrm{Ext}^1\}}_{\textbf{structure: how the parts are glued}}$$

This is the single most useful thing the algebra says about memory, for four reasons:

1. **Content is exact and cheap.** An integer multiset. Retrieval by content is exact multiset intersection, no floating point, no approximate nearest neighbour, no encoder drift.
2. **Structure is where the value is.** From §4: a *non-split* extension is a memory carrying information neither of its parts has. Split extensions are just co-storage.
3. **It gives a principled compression law.** Passing to the associated graded $\mathrm{gr}(M)=\bigoplus_i M_i/M_{i-1}$ is exactly "keep the atoms, discard the gluing." It is the maximally-forgetful operation that is lossless on content.
4. **It therefore gives a principled theory of forgetting** — see §16.

> **Claims and non-claims.** Jordan–Hölder and the structure of $K_0$ are theorems, and they apply to holonomic modules as stated. What is *proposed* is the design decision to make $([M], \mathrm{Ext\ data})$ the storage schema. The proposal's weight rests on the exactness of the content half and the §4 argument for the structure half.

## 13. Roots: the microlevel classification

The instinct about "roots" is exactly right, and there is a theorem waiting at the end of it.

Model the local memory structure as a **quiver** $Q$: vertices = memory sites, arrows = the directed logical-prerequisite relation that Remark 2.4 already insists on keeping separate from the undirected simplices. A memory configuration is a representation of $Q$.

> **Kac's theorem.** For any quiver $Q$, the dimension vectors of indecomposable representations are exactly the **positive roots** of the associated Kac–Moody root system $\Delta^+(Q)$. For a **real** root there is a unique indecomposable. For an **imaginary** root there is a positive-dimensional family.

Three consequences, and each is directly usable:

**(a) The indecomposable memories are indexed by positive roots.** This is the microlevel atom classification, and it is complete. Not a heuristic clustering — a classification theorem.

**(b) Real vs. imaginary roots is a real distinction the architecture needs.**
- *Real root* → a **rigid** memory. One way to hold this content. No moduli. Safe to canonicalise, hash, deduplicate.
- *Imaginary root* → a memory with **moduli**: a continuous family of ways to glue the same atoms. These are exactly the memories where "the same facts, differently assembled" is a real phenomenon — where paraphrase-perturbation (§8.2) should be spent, and where naive deduplication would silently destroy information.

That single distinction tells the curator which memories can be compressed by canonical form and which cannot. It is a checkable property of a dimension vector.

**(c) Representation type is an enforceable design constraint.** By Gabriel, a connected quiver has finitely many indecomposables iff its underlying graph is ADE; affine ADE gives tame type; everything else is **wild**, meaning classification is provably hopeless (it contains the classification of all finite-dimensional algebras).

So there is a hard design rule available:

$$\boxed{\ \text{Keep local memory quivers of finite or tame type. Wild subquivers must be split.}\ }$$

This is checkable in $O(|Q|)$ by graph pattern matching, and it is a genuine constraint that bites — it says the prerequisite graph cannot be allowed to accumulate arbitrary structure locally without paying for it in unclassifiability. Constraints that bite are the useful kind.

## 14. Trees: composite skills and their decomposition

The other half of the "roots and how they connect" instinct, and it lands somewhere unexpectedly concrete.

A composite skill (a microneuron, Construction 9.4) is a rooted tree of operator applications. The canonical algebra of rooted trees is the **Connes–Kreimer Hopf algebra** $\mathcal H_{CK}$, with coproduct
$$\Delta(T) \;=\; T\otimes 1 + 1\otimes T + \sum_{c\ \text{admissible cut}} P^c(T)\otimes R^c(T).$$

This is the canonical answer to "decompose a composite skill into a sub-skill and a remainder": admissible cuts enumerate *exactly* the ways a skill factors into a prefix and a completion, and the coproduct is coassociative, so iterated decomposition is order-independent. The **antipode** gives skill inversion — the formal undoing of a composite.

And there is a genuine coincidence worth noting: **the Butcher group of $\mathcal H_{CK}$ is the group of Runge–Kutta methods**, whose order conditions are indexed by rooted trees. §7's RK4 integrator is literally an element of this group. The tree algebra governing composite-skill decomposition and the tree algebra governing your existing integrator are the same algebra. That is not a metaphor — it is the same Hopf algebra, and it means the composition theory for skills is already implicitly present in the numerics.

**What this buys operationally.** A sub-skill library is not built by ad-hoc pattern mining over logs. It is read off the coproduct: the sub-trees that appear with high multiplicity across many $\Delta(T)$ are the candidates for promotion, and the multiplicity is a Hopf-algebraic count, not a heuristic frequency.

## 15. Retrieval: exact structure first, similarity last

Here is the concrete form of "abandon the LLM's way of parsing memory."

**Current.** query → embed → k-NN in $\mathbb R^{384}$ → text blobs → LLM re-reads them. Approximate at every step, and the LLM does the parsing *again on every retrieval*.

**Proposed.** Invert the order of exactness:

```
1. STRATUM QUERY   (exact, O(#strata))
   Locate the query's support: which strata does it touch?
   Return memories whose support meets that closure — a poset query,
   using the closure relations Z_α ⊆ cl(Z_β). Not a distance.

2. CONTENT FILTER  (exact, integer)
   Intersect K₀-classes. Rank by |[M] ∧ [Q]| — exact multiset overlap.

3. STRUCTURE FILTER (exact)
   Prefer memories whose Ext data is non-split and relevant:
   these carry assembled structure, not just co-present facts.

4. EMBEDDING TIEBREAK (approximate, last)
   Only now, and only to order the surviving candidates.
```

The inversion is the whole point. Today retrieval is approximate-only. Here approximation is the *tiebreak*, and every earlier stage is exact and explainable — you can say precisely why a memory was returned.

**The honest trade-off, stated plainly.** Lifting text into a structured object requires an LLM parse. The LLM does not disappear; it **moves from retrieval time to ingestion time**. That is the actual argument for the whole scheme:

- parse **once**, at ingestion, where it can be gated by VerifyOp;
- retrieve **exactly**, thereafter, forever, with no LLM in the loop;
- amortise the parse cost over every future retrieval.

Under current practice the parse happens on *every* retrieval, is ungated, and is silently re-approximated each time. That is the cost being eliminated, and it is a large one.

## 16. Forgetting, consolidation, and what the strata are actually for

Nothing in the source document addresses forgetting except weight decay, which deletes coalitions rather than compressing knowledge. The algebra supplies the missing operation.

**Consolidation = pass to the associated graded.**
$$M \;\rightsquigarrow\; \mathrm{gr}(M) = \bigoplus_i M_i/M_{i-1}$$
Atoms preserved exactly; gluing discarded. This is lossless on $K_0$-content and maximally lossy on structure — a compression law with a theorem behind it rather than a heuristic.

**The consolidation policy then writes itself:**
- **Always keep** the composition factors. Content is cheap (integers) and canonical.
- **Keep the Ext class only if it was verified useful** — i.e. only if the non-split extension passed the §4 promotion gate.
- **Everything else** degrades to its associated graded on a schedule.

This is a sharp and defensible account of sleep-consolidation: *forgetting is the loss of extension data, not the loss of facts.* And it explains a familiar phenomenon — remembering all the pieces of an argument while having lost how they fitted together is precisely $M \rightsquigarrow \mathrm{gr}(M)$.

**Now the strata question, which is the one being underused.** The source document has exactly two strata (organ, concept), and they encode *scale*. That is a thin use of a rich structure. The richer stratification is by **categorical level**, and it is already implicit in the three memory types being asked about:

| memory type | categorical level | object |
|---|---|---|
| **concept** | 0 — objects | a holonomic module |
| **theorem** | 1 — morphisms | a map $M_{\text{hyp}} \to M_{\text{concl}}$; the theorem is the *existence*, the proof is the *map* |
| **skill / technique** | 2 — endofunctors | an element of $\mathcal D$ acting on the category |

This is the answer to "lift concepts and theorems and techniques to something more abstract," and it is not a taxonomy imposed from outside — it is forced by what each thing *does*. A concept is a thing you can hold. A theorem is a thing that takes you from one holding to another; theorems compose because morphisms compose. A skill transforms whole classes of concepts at once, which is what a functor is; "a technique applies to a theorem" is a natural transformation.

With that, the stratification becomes genuinely two-dimensional — **scale × categorical level** — and constructibility acquires teeth. A memory constructible with respect to the stratification is, by the exit-path equivalence, a functor $\mathrm{Exit}(X)\to\mathrm{Vect}$. The **generization maps** (stalk at a deep stratum → stalk at a nearby generic one) are then exactly *"how a specific memory generalises."*

That is the deepest structural point here: **abstraction becomes a map in the data, not an LLM call.** Today, generalising from a specific instance to a general principle requires prompting a model and hoping. In a constructible memory it is the generization map along a stratum closure — computed, inspectable, and composable.

## 17. Persistence, and one honest limitation

Consolidation (Construction 9.4) currently runs persistent homology over the weight filtration alone. With the above, memory naturally carries at least three filtration parameters — time, coupling weight, verification status — and multiparameter persistence is the right frame.

**But:** there is no complete discrete invariant for multiparameter persistence (Carlsson–Zomorodian). There is no barcode. Anyone who tells you otherwise is selling something. What exists is the **rank invariant** and fibered barcodes along one-parameter slices, which are incomplete but computable and genuinely useful.

So: use fibered barcodes along the slices you care about (e.g. fix verification status, vary weight and time), and do not claim a complete classification. This is exactly the register of §15's box — a proposal with its limitation stated in the same breath.

## 18. What memory should look like, concretely

```
Memory := {
  # ---- identity ----
  level         : 0 | 1 | 2                    # concept | theorem | skill
  
  # ---- content (exact, cheap, canonical) ----
  K0_class      : multiset of simple-factor ids       # Jordan–Hölder, ordering-independent
  
  # ---- structure (expensive, valuable, verified) ----
  ext_data      : list of (pair, class)               # gluing; non-split ⇒ keep
  
  # ---- location (exact retrieval index) ----
  support       : set of stratum ids                  # poset-queryable
  cc_shadow     : stratum ↦ multiplicity (ℤ)          # cheap shadow of CC
  
  # ---- microstructure ----
  root_type     : real | imaginary                    # rigid vs. has moduli
  tree          : rooted tree (level 2 only)          # Connes–Kreimer decomposable
  
  # ---- provenance ----
  verify_status : Verified | Refuted | Unverifiable    # three-valued, §12
  
  # ---- legacy / tiebreak only ----
  embedding     : ℝ³⁸⁴
  source_text   : str                                  # kept for audit, NOT for retrieval
}
```

Note where `source_text` sits: retained for audit and human inspection, **not** on the retrieval path. That single demotion is the practical content of "abandon the LLM's way of parsing memory."

## 19. Implementation order for memory

1. **Add `support` and query by strata before querying by embedding.** No new theory required — the stratification already exists. Immediate: retrieval becomes explainable.
2. **Add `K0_class` for a coarse notion of simple factor** (initially: verified atomic propositions). Exact integer retrieval, no floats. Even a crude simple-object set beats embedding-only.
3. **Record `ext_data` at composition time**, when the assembly is known and free. Do not try to recover it later — that is expensive, and at composition time it costs nothing.
4. **Consolidation = `gr`,** gated on verification of the Ext class. This is the forgetting law and it needs steps 2–3 first.
5. **Quiver type check** on the prerequisite graph. $O(|Q|)$ pattern match, flags wild subquivers for splitting.
6. Only then: real holonomic modules, real Ext¹ computation, characteristic cycles.

Steps 1–3 are tier A and require no D-module machinery at all. That is worth emphasising: **the memory redesign's largest wins do not depend on the hardest mathematics.** The algebra tells you *what the right schema is*; implementing the schema is much cheaper than implementing the theory that justifies it.

---

## Closing: the honest bottom line

The technology is not admitted because it is beautiful. It is admitted where it converts a fitted constant into a derived one (§1), an unread variable into a measurement (§2), a renaming into a growth (§8), a heuristic into a theorem (§11, §13), and an approximate retrieval into an exact one (§15).

Two things it does **not** buy, in the source document's own register:

- **It does not raise the LLM's per-call reasoning quality.** On day one — Gaussian concepts, split extensions only, $\pi\equiv1$, embedding retrieval — the whole apparatus degrades exactly to the architecture of Sections 2–13. The bet remains on accumulation.
- **Canonical atoms are not true atoms.** Jordan–Hölder guarantees the decomposition is unique *given the category*. Choosing the category — deciding what counts as a simple object — is a modelling decision, and it is the one place where the whole memory design can still go wrong. It should be made explicitly, gated by VerifyOp, and revisited, rather than allowed to accrete by default from whatever the first ingestion pipeline happened to emit.

That last point is the real risk, and it is worth stating as plainly as §14 states its own: the algebra makes the decomposition canonical, but it cannot tell you what the simple objects are. That remains a bet — just a much better-instrumented one.
