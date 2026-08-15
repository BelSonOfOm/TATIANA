# Reviewer 2 Audit — `MOS_SCRUTINY_AND_D_MODULES` + `MOS_BOOK`

**Date:** 2026-07-27
**Auditor stance:** hostile referee. Everything below was checked against the source
documents, the `.tex` mathematical description, `TATIANA_LOGBOOK.md`, and the actual
engine (`MOS/src`, `MOS/python`). Where I verified a proof by hand I say so. Where I
did not, I say that too.

**Provenance note.** `MOS_SCRUTINY_AND_D_MODULES.md` and `MOS_SCRUTINY_AND_D_MODULES (1).md`
are byte-identical (36,283 bytes each). There is one scrutiny document, not two.
`MOS_BOOK.md` is its expansion: the scrutiny is the indictment, the book is the
development. They are one work in two registers.

---

## 0. The one-paragraph verdict

The scrutiny/book pair is **the most valuable thing written about MOS so far, and it is
also the most dangerous.** Valuable because roughly six of its criticisms are correct,
checkable, and cheap to act on, and two of them (the ρ splitting and the H¹ vacuity)
close open problems the `.tex` explicitly leaves open. Dangerous because it is
structured as a mathematical cathedral in which perhaps 15% of the floor area is
load-bearing for MOS as it exists, the remaining 85% is conditional on representation
changes nobody has built, and the document's rhetorical confidence does not distinguish
between the two. A referee reading the book cold would find at least four substantive
errors and one circular argument. Those are fixable. What is not fixable by editing is
the deeper problem: **the book audits a document, not a system, and the system moved
three days before the book was written.**

---

## 1. How fundamental are these changes? A tiered answer

I am grading on: *is it a theorem about MOS as built, is it correct, and does it change
what the engine does?*

### Tier 1 — Fundamental, correct, changes the system (act on these)

**1.1 The splitting ρ = α · ρ̃ (§1 scrutiny / §5 book).**
Verified. ρ = ω/(B‖X‖²_F); multiply and divide by ‖x⊥‖². Because ω depends only on
x⊥ (as `ker L` is the diagonal under identity restrictions and a connected 1-skeleton),
ρ̃ = ω/(B‖x⊥‖²) = R_L(x⊥)/B is a genuine Rayleigh quotient on (ker L)^⊥, so by
Courant–Fischer

  ρ̃ ∈ [λ₂(L_K)/B, λ_max(L_K)/B]

with both endpoints computable from the 7-vertex coarse graph before any data is seen.
**This is real and it is the single highest-value item in either document.** It gives a
topology-derived calibration window, it explains the reported non-monotonicity of ρ in
organ count (α dilutes; ρ̃ does not), and it produces a *typed* diagnosis (high α / low ρ̃
= structural split; low α / high ρ̃ = one bad edge) where there was one scalar.

Cost: one centring and one 7×7 eigendecomposition on `bind`/`collapse`. Genuinely free.

**1.2 Proposition 8.2 — the derived 1-cochain is always exact (§3 scrutiny / §8 book).**
Verified, and trivially so: `[δx] = 0` in H¹ because δx ∈ im δ⁰ *by definition*. It
holds for every state and every sheaf, identity restrictions or not.

This kills, unconditionally, the `.tex`'s §15.6 proposal to attach structure at "the
harmonic representative of a persisting [ζ] ∈ H¹" and it kills the b₁-vs-H¹ diagnostic
distinction that Remark 8.2 of the `.tex` spends its most careful argument earning.
**This is the deepest correct criticism in the document.** It is not a small point: the
uncertainty stack lists b₀, b₁ and H¹ as separate instruments and, as specified, two of
those rows are the same row and the third can never fire.

**1.3 The Tietze diagnosis of δ𝔇 (§7/§14 scrutiny / §13 book).**
Verified. Corollary 13.4 is exactly Tietze transformation (T2): adding a generator with
a defining relation expressing it in old generators leaves the algebra isomorphic.
So promotion-of-a-composite, described in `con:micro` as "the essential" growth axis,
does not grow the algebra. The compilation/extension split (filtration refines vs.
new generator not a word in the old ones) is the right correction, and the
workload-compression metric Λ(t) is the right instrument — **it is the first
LLM-independent falsification test the project has been offered**, and the `.tex`
§sec:limits says making augmentation falsifiable is the whole point of the
instrumentation while supplying no such test.

Caveat, and it matters — see finding **F5** below: the theorem presupposes 𝔇 is an
algebra, which the same document says it is not.

**1.4 Λ(t) and the GK-dimension warning (§19 book).**
Verified. Theorem 19.3 (GK dimension is generating-set independent) is standard, and the
corollary — GK dimension is provably blind to compilation — is correct and would have
been an expensive mistake to make. Choosing the invariant that moves is a real
contribution. Cost: a log.

### Tier 2 — Correct, real, but conditional or low-yield

**2.1 Weighted Anderson–Morley (§2 scrutiny / Thm 7.5 book).**
I checked the proof line by line and it is **correct**: Q_π = BΠBᵀ = D_π + A_π;
nonzero spec(BΠBᵀ) = nonzero spec(Π^½BᵀBΠ^½); Collatz–Wielandt with the test vector
s_e = √π_e gives row sums 2π_e + Σ_{e'~e}π_{e'} = d_π(u) + d_π(v). Reduces to B at π ≡ 1.

But see **F1**: it is already implemented, and **F2**: it is stated more generally than
it is proved.

**2.2 Bures–Wasserstein degeneration (§5 scrutiny / §11 book).**
Verified arithmetic. Corollary 11.3 (Σ₁=Σ₂=DI ⟹ W₂² = ‖μ₁−μ₂‖²) is exact, and today
every grown concept has `GROWN_CONCEPT_VARIANCE_PRIOR = 1.0` with empty U, so **the
optimal-transport apparatus is presently computing squared Euclidean distance.** That
charge lands. Corollary 11.4 and the 384×(1−0.2265)² ≈ 230 vs. semantic ≤ 4 arithmetic
also checks out. The prescription (report `d_semantic` and `d_epistemic` separately) is
correct and free.

Deduction: see **F6** — the attribution of the hazard to "hallucinated confidence" is
partly wrong; the real problem is dimensional, not epistemic.

**2.3 Hodge decomposition on a measured 1-cochain (§9 book).**
Theorem 9.2's proof is correct (standard four-subspaces twice, intersected with
ker δ¹). The gradient/curl/harmonic trichotomy is strictly finer than the b₁/H¹ binary
and each component has a distinct remedy. This is the right fix *in principle*.

But see **F3**: half the proposed source of η is circular, and the document does not
notice.

**2.4 The CP³ derivation (§46 book).**
I re-derived Steps 1–3 and they are correct. Critical points = eigenvectors; in the
affine chart E ≈ λᵢ + Σ_{j≠i}(λⱼ−λᵢ)|zⱼ|²; real Hessian eigenvalues 2(λⱼ−λᵢ) each with
multiplicity 2; index = 2·#{j : λⱼ < λᵢ} ∈ {0,2,4,6}; Morse polynomial 1+t²+t⁴+t⁶ =
Poincaré polynomial of CP³, hence perfect, structurally guaranteed by Frankel. Step 4
(drift Laplacian ≅ Witten Laplacian at t = β/2) is standard.

But see **F7** and **F8**: the headline prediction is weaker than advertised and the
one genuinely new number is never computed.

### Tier 3 — Beautiful, standard, and currently inert for MOS

Parts III (D-modules), V (quivers/roots), VI (Hopf/Butcher), VII (persistence)
contain no errors I found of consequence and a great deal of correct standard
mathematics. Their status for MOS is:

- **§23 (Gaussians are holonomic)** is exact and I verified it, including the careful
  Remark 23.2 distinguishing the order filtration (Ch = zero section, sees neither μ
  nor Λ) from the Bernstein filtration (Lagrangian graph ξ = −Λ(x−μ)). That remark is
  the most intellectually honest paragraph in either document.
  **But its own honesty is the refutation of the section's utility:** every Gaussian
  concept has rank 1, multiplicity 1, and zero-section characteristic variety. The
  three "new integer diagnostics" are constant across every object the engine can
  currently produce. They become informative only if concepts stop being Gaussian, and
  nothing in MOS produces a non-Gaussian concept.
- **§39–40 (Connes–Kreimer / Butcher)** — the observation that the skill-decomposition
  algebra and the RK4 order-condition algebra are the same Hopf algebra is true and
  charming. It is also, by the book's own §12, an argument for deleting RK4. The section
  is a pleasing coincidence, not a result.
- **§41–42 (persistence)** — the proof that the barcode exists *because A_n is Dynkin*,
  and that multiparameter persistence therefore has no barcode, is correct and is the
  right thing to say. It is a warning, not a capability.

**Tier 3 is where the paper will die if it leads with it.** The book's own §48.1 says
so ("Tier C is where the mathematics is most beautiful and least urgent") and then
spends 40% of its length there.

---

## 2. Findings — errors, overclaims, and one circularity

Numbered by severity. F1–F3 are the ones that would draw blood in review.

### F1 (High) — The audit is against a stale snapshot; item 2 of 3 is already built

The scrutiny's "shortest path" names three actions. Action 2 is:

> Set π_e = w(σ,t) and use B_π from the Lemma in §2. Cost: none.

**This was implemented on 2026-07-24, three days before the scrutiny was written.**
Confirmed in code:

- `MOS/python/coherence.py:38–39` — `d_pi(v) = sum over edges e incident to v of pi_e`,
  `B = max over edges {u,v} of (d_pi(u) + d_pi(v))  [weighted Anderson-Morley]`
- `MOS/src/core/coarse_complex.cpp:253–254` — the same bound in the engine
- `MOS/include/mos/core/coarse_complex.hpp:117` — documents using "coupling weight as
  pi_e (a more-bound coalition is trusted more)"

Logbook §5q records this as mechanism ① with C++ parity tests green. The scrutiny's
Lemma is therefore not a correction to be applied; it is a **post-hoc proof of a bound
the engine is already using**, which is a genuine and welcome contribution (the code
shipped the bound before it had a written proof) but a completely different claim from
the one the document makes.

**Consequence for the paper.** The `.tex` (§sec:outlook, "proposed, unimplemented") is
stale relative to the engine. Any paper built on the scrutiny's picture of "what MOS
currently does" will misdescribe the system. The `.tex` must be resynchronised with
§5q *before* it becomes the paper's baseline.

### F2 (High) — Theorem 7.5 is stated more generally than it is proved

The theorem is stated for L_π = δᵀΠδ — i.e. the *sheaf* Laplacian, general restriction
maps. The proof writes

  xᵀL_πx = Σ_e π_e‖x_u − x_v‖² ≤ Σ_e π_e(‖x_u‖+‖x_v‖)²

which silently assumes the restriction maps are the identity. With general
R_{v⊴e} the first equality is wrong and the inequality needs ‖R_{v⊴e}‖ ≤ 1; orthogonality
suffices, arbitrary learned maps do not.

This matters because the *entire point* of §2/§7 is to combine Hebbian weights with a
non-trivial sheaf. As stated, the theorem does not cover the case it exists to serve.

**The deployed code is more honest than the book.** `coherence.py:46` explicitly records
the orthogonality assumption, and `coarse_complex.cpp:273–277` warns to stderr rather
than silently clamping when ρ_raw > 1. The paper must carry the hypothesis
`‖R_{v⊴e}‖ ≤ 1` in the statement of the theorem.

### F3 (High) — The proposed fix for H¹ is half circular

§3 of the scrutiny (§8.4 of the book) says: stop deriving the 1-cochain, start measuring
one. Let η ∈ C¹ record claimed pairwise relations directly —

> the residuals of learned restriction maps, **or** explicit pairwise comparison
> judgements from the organs

**The first option does not work, and it fails for exactly the reason Proposition 8.2
gives.** If η_e is the residual of learned restriction maps, then η_e = R_{u,e}x_u −
R_{v,e}x_v = (δx)_e for the learned maps — which is in im δ⁰ by construction, no matter
how non-trivial the maps are. Proposition 8.2 applies verbatim. `[η] = 0`. The
diagnostic still cannot fire.

Only the second option escapes, and it carries an architectural cost the document never
prices: **organs must emit genuinely relational outputs** ("Search and Memory disagree
by this much in this direction") that are not functions of any single global 0-cochain.
That is a new organ contract, a new LLM call shape, and a new failure mode
(organs can emit inconsistent pairwise claims that are not merely wrong but
ill-typed). It is not a change of formula; it is a change of what the organs are.

The book asserts the fix "makes the 2-simplices do computational work at last" and
does not notice that half of what it proposes leaves the problem exactly where it was.

### F4 (Medium-High) — The trace-monoid independence relation is asserted, never verified

Parts II §14–§19 — Foata normal form, quadratic Gröbner basis, Koszulity, the
Cartier–Foata clique polynomial, capacity κ, the Anick resolution, HH¹/HH² — **all rest
on one hypothesis**: that operators with disjoint node-support commute, so that

  I = {(i,j) : support(g_i) ∩ support(g_j) = ∅}

is the independence relation of a trace monoid.

In the actual engine, every operator touches shared state: the `CognitiveState`, the
SQLite store, the obstruction counter Ω, the mutation history, and the coarse stalks
that `compute_pi_v` overwrites after execution (logbook §5o). Two operators with
disjoint *fine-complex* support still both mutate Ω and both feed π_v. **They do not
commute as state transformers.**

If I is in fact empty or near-empty then A is (near) the free algebra, μ(z) = 1 − rz,
κ = r, the quadratic dual has no cliques above degree 1, and every result in §16–§18
degenerates to "counting words," which is just counting DAGs. The clique polynomial has
**never been computed for the real operator set** {SearchOp, ComputeOp, ReasonOp,
ContextOp, VerifyOp, …} — five or six generators, all touching shared state.

**This is a one-afternoon experiment and it should be run before a single line about
Koszulity is written.** If I is empty, Part II is decoration. If it is not, Part II is
the best-supported half of the algebra story. Nobody knows which.

### F5 (Medium) — The Tietze theorem presupposes what the same document denies

§7 of the scrutiny: "𝔇 is currently a typed *set* with a growth rule. No product, no
relations, no grading, no unit — nothing that makes 'algebra' more than an honorific."

§14 of the scrutiny, four pages later, proves a theorem about 𝔇 *as an algebra* and
concludes "the fourth growth axis currently does not grow anything."

You cannot have both. The honest statement is conditional: *if* one formalises 𝔇 as the
free algebra on the operator generators modulo disjoint-support commutation, *then*
promotion is a Tietze move and changes nothing. That conditional is correct, useful, and
should be how the paper states it. The unconditional phrasing is a category error and a
referee will say so in one sentence.

Substantively there is also something the criticism misses: promotion changes the
*planner's emission distribution* over composites — a probability measure on the monoid,
not the monoid. Neither GK dimension nor κ sees that. Λ(t) partially does, which is
another argument for Λ(t) being the right instrument.

### F6 (Medium) — The W₂ hazard is misattributed

The 57:1 figure is arithmetically right but the causal story is not. The term
d(√D₁−√D₂)² is large because **d = 384 and the trace of an isotropic covariance is
d-extensive, while ‖μ₁−μ₂‖² is bounded by 4 for unit-normalised embeddings.** That is a
dimensional-analysis problem, not a confidence problem. Any isotropic covariance model
in 384 dimensions has this property, calibrated or not. Additionally, the specific pair
chosen (D₁ = 1.0 uncalibrated prior vs. D₂ = 0.051 confident) is the maximally
adversarial *mixed* pairing — comparing a calibrated concept against an uncalibrated
one. Fully calibrated, both D land in [0.01, 0.69] and the gap shrinks (though the
term is still ~200, so the conclusion survives).

The prescription is right. The diagnosis in the paper should be "you are adding a
d-extensive quantity to a d-intensive one," which is stronger, simpler, and true
independent of the calibration story.

### F7 (Medium) — Proposition 12.4 is false in the deployed case

> Composing a generic RK4 step with a projection destroys the fourth-order accuracy.

For a **fixed affine** constraint set A = x₀ + V with a vector field tangent to V, this
is wrong. Runge–Kutta methods are affine-invariant: every stage k₁ = f(x₀),
k₂ = f(x₀ + (h/2)k₁), … lies in V, and x₁ = x₀ + (h/6)(k₁+2k₂+2k₃+k₄) ∈ A exactly. The
projection after the step is a no-op and the order is preserved.

The claim is true only for **non-linear** constraint manifolds. The `.tex`'s rigid
constraints are hard orthogonal projections onto an affine subspace — precisely the case
where the proposition fails. The `.tex`'s §7 is not damaged by this criticism.

The rest of §12 (that RK4 is dominated by Chebyshev/Lanczos evaluation of e^{−tL}x₀ for
a quadratic Φ, and that the rate is λ₂) is correct — and it is also **low yield**: the
logbook §5n records RK4 producing a measured relaxation of −0.081, and swapping
integrators would change cost, not behaviour. Correct, marginal, and it currently
contains a false proposition. Fix or cut.

### F8 (Medium) — The CP³ prediction is weaker than advertised, and the one new number is missing

Two problems with the headline box.

**(a) The count is not a prediction.** "Δ_β on 1-forms has no low-lying band" — the
*count* part follows from dim ker Δ_β on 1-forms = b₁(CP³) = 0, which holds at **every
β**, not just asymptotically, by Hodge theory. The topology does not "force" a new fact;
it forces a fact that was already true at every temperature. The genuinely new content
is entirely the **gap**: that the bottom of the 1-form spectrum grows *linearly* in β
with a *specific slope*.

**(b) The slope is never computed.** The book says the slope is "a quantitative
prediction, not just a qualitative one" and then gives it only as "determined by the
Hessian frequencies 2|λⱼ−λᵢ|" — with no constant. Working it through: E = λᵢ +
½Σ_j 2(λⱼ−λᵢ)(a_j²+b_j²) gives oscillator frequencies μ_j = 2(λⱼ−λᵢ) each with
multiplicity 2; the Witten model's ground energy on 1-forms at a critical point of even
index is 2t·min_j μ_j; with t = β/2 this yields a bottom-of-spectrum slope of order
**2·min_{i≠j}|λᵢ−λⱼ|** — i.e. proportional to the *minimum spectral gap of K*. That is a
falsifiable number and it is the only new quantity in Part VIII. **It should be derived
carefully with conventions pinned, and checked numerically.** As written the section
promises a number and does not deliver one.

**(c) The distinct-eigenvalue hypothesis is the wrong default for the application.**
Step 1 assumes λ₁ < λ₂ < λ₃ < λ₄. The canonical two-qubit Hamiltonians are degenerate
(Heisenberg XXX has a 3-fold triplet). Then E is Morse–**Bott**, the critical set is
CP¹ ⊔ {pt}, and the analysis changes — the conclusion survives (CP¹ contributes in
degrees 0 and 2, still nothing in degree 1) but the derivation as written does not
cover it. Given that FIRST DRAFT's subject is the *symmetry-broken* spectrum, distinct
eigenvalues may be exactly the intended regime — but then the paper must say so and must
say what happens at the symmetric point, because that is the unperturbed reference the
whole perturbation is measured against.

### F9 (Medium) — HH² is not where the obstructions live

Internal contradiction. Proposition 18.2 says HH² "is where obstructions live."
Theorem 18.3 (Gerstenhaber), correctly, says obstructions live in **HH³** and HH²
parametrises first-order deformations. Both statements are in the same section.

Worse, the application is wrong regardless. **Ore extensions are unobstructed.**
Theorem 18.5 as stated in the book says A[y;σ,δ] exists *iff* σ is an endomorphism and
δ a σ-derivation — that is the definition, not a cohomological condition. There is no
HH² obstruction to an Ore extension. The story "HH¹ = what you could grow, HH² = what
stops you" is decorative; the honest version is "HH¹(𝔇, ^σ𝔇) = the space of admissible
σ-derivations modulo inner, and that is the whole classification."

This is the kind of error that costs a paper its credibility on the algebra, because it
is checkable from a textbook in five minutes.

### F10 (Medium) — The memory schema's K₀ classes are trivial for every object MOS produces

This is the one I would lead with as a referee, because §47 is the book's own
self-nominated biggest win (items 4 and 5 of the shortest path).

The two-part storage law is `M ↦ [M] ∈ K₀ (content) + {[E]} ∈ Ext¹ (structure)`, with
canonicity from Jordan–Hölder. Both halves need a category. **The book never fixes one**,
and the two candidates it offers give incompatible answers:

- **Hol(𝒟_d).** Every Gaussian concept is, by the book's own Theorem 23.1, the module
  generated by a rank-1 exponential — a rank-1 integrable connection on affine space,
  which is **simple**. So JH(M) = {[M]}: every concept is its own single atom,
  composition series has length 1, and `[M] ∈ K₀` carries exactly as much information as
  "which memory is this." Content-addressing by exact multiset intersection returns
  either everything or nothing. The K₀ layer provides no compression, no shared atoms,
  and no deduplication until memories are built as *extensions* of length > 1 — and the
  book never specifies how a memory acquires a composition series longer than one.

- **Rep(Q).** Here simples are the vertex simples S_i and `[V] ∈ K₀` **is the dimension
  vector**. That is non-trivial, but it is also extremely coarse: two entirely unrelated
  memories with the same dimension vector collide exactly. As a retrieval index this is
  a hash with catastrophic collision behaviour.

§29–§32 argue in Hol(𝒟); §33–§37 argue in Rep(Q); §47 writes `K0_class : multiset of
simple-factor ids` without saying which. **The schema is stated in a category that does
not exist yet, and the two available categories are respectively vacuous and too coarse.**

The book's §49 concedes the general form of this ("choosing the category is a modelling
decision, and it is the one place the whole memory design can still go wrong") but does
not notice that both concrete instantiations it has offered already fail.

### F11 (Low-Medium) — "ε need not be fitted at all" is contradicted three pages later

§1(c) of the scrutiny: "The threshold ε need not be fitted at all."
§5.4 of the book, implementation block:

```
ε = window.lo + q·(window.hi − window.lo)
```

with `q` a free parameter. You have replaced one magic number with another. The
improvement is real and worth having — ε is now *topology-adaptive*, recomputed on every
`bind`/`collapse`, and expressed in units the graph supplies rather than units three
observations supplied — but it is **normalisation, not derivation**. State it that way
or a referee will quote the two lines side by side.

### F12 (Low-Medium) — The dead-dynamic-range diagnosis is asserted, not computed, and the arithmetic points the other way

§1(a) claims α is small "for encoder-geometric reasons," so the thermometer occupies
[0, 0.2] "and always will."

`bge-small-en-v1.5` returns **unit-normalised** embeddings. Then ‖X‖²_F = n and
α = 1 − ‖x̄‖², and with mean pairwise cosine c̄,

  α = (n−1)(1 − c̄)/n.

The logbook records cos(math, chat) = 0.449 for genuinely unrelated content. With n = 7
and c̄ ≈ 0.45 that gives **α ≈ 0.47** — nowhere near small. Then ρ = 0.14 implies
ρ̃ ≈ 0.30, comfortably inside a typical [λ₂/B, λ_max/B] window. On this arithmetic the
compression of ρ is coming from **both** factors, roughly comparably, and possibly more
from B being a loose bound on λ_max (Anderson–Morley routinely overestimates by ~2×)
than from anisotropy.

The claim may still be right — c̄ over the *active organ set* during a real run is the
number that matters and I have not measured it. But the document presents a causal
explanation for the project's most conspicuous empirical fact without ever computing the
quantity it blames. **This is a one-line instrumentation change** (log α and ρ̃ alongside
ρ) and it must be run before the claim enters a paper. If α turns out to be ≈ 0.5, the
"encoder anisotropy" story in §5.4(a) is simply false and has to come out.

### F13 (Low) — Novelty overclaims

- Theorem 7.5 is called "the one genuinely new theorem in Part I." Weighted
  Anderson–Morley-type bounds via the signless Laplacian are standard spectral graph
  theory. Present it as "a generalisation, presumably known; we give a self-contained
  proof because we need the exact constant." A novelty claim on folklore is the fastest
  way to lose a referee.
- Corollary 23.4 "characteristic varieties add" — the *defining 1-forms* add; the
  characteristic **cycle** is additive on short exact sequences, not under ⊗. The
  computation is right, the slogan is misleading.
- §36's rigid/moduli dichotomy invokes Kac's theorem, correctly stated **over an
  algebraically closed field**, and then applies it to memory representations that would
  live over ℝ. Over ℝ the classification does not hold in that form. The hypothesis is
  stated in the theorem and silently dropped in the application.

### F14 (Low) — Rhetorical padding that reads as substance

- **The 1/n law (§4 / §10).** Theorem 10.4 is correct and is also the defining property
  of an arithmetic mean. Whether it bites depends entirely on whether the active set is
  bounded — and logbook §5o records "n is tiny (<10/DAG)," so empirically it does not
  bite in the deployed system. The genuinely useful content is one sentence: **the
  definition of the active working set is undefined and load-bearing.** That sentence
  should survive; the three pages around it should not.
- **"400:1 data over topology" (§8).** Comparing 2688 stalk dimensions against 7
  vertices compares incommensurable quantities. It is a rhetorical flourish, not an
  argument. What topology buys (edge-localised blame via `worst_edge`, at O(|E|)) is
  real and is not measured in dimensions.
- **n = 7.** The correct point — persistent homology, branching ratios, avalanche
  statistics and Kinouchi–Copelli are asymptotic instruments undefined at seven vertices
  — is right, is important, and the `.tex` half-concedes it already (§sec:outlook:
  "meaningful only at sample sizes where a branching ratio is statistically defined").
  Note also that the organ count is inconsistent across the corpus: the `.tex` lists 7,
  logbook §0 lists 6, and the runtime uses 4 operator organs plus RESPOND. Fix before
  publication.

---

## 3. What this means for "a complete mathematical description + a bulletproof paper"

### 3.1 The scope is not one paper. It is three, and they have different truth-conditions.

Trying to write one document that contains ρ-splitting, Koszul duality, D-modules,
Kac's theorem, Connes–Kreimer and a CP³ spectral prediction will produce something no
referee can accept, because the papers have incompatible standards of evidence.

**Paper A — "A cellular-sheaf coherence measure for multi-agent LLM orchestration."**
Content: 𝓜 = (C, F, s); ω, ρ; the α/ρ̃ splitting with the [λ₂/B, λ_max/B] window;
weighted Anderson–Morley **with the ‖R‖ ≤ 1 hypothesis**; precision-weighted PC free
energy; the Oja-stabilised local learning rule for restriction maps; `worst_edge`
localisation; the three-valued VerifyOp gate. Every claim here is a theorem plus a
measurement on a running system. **This paper is nearly writable today** and it is the
one that discharges goals 1 and 2 (free research tool, masters thesis vehicle).
Everything in it exists in code and has parity tests.

**Paper B — "Sheaf-cohomological obstruction as a diagnostic for multi-agent
disagreement."** Content: Proposition 8.2 (the derived cochain is exact — a negative
result worth publishing on its own); the measured-η architecture and its organ-contract
cost; the Hodge trichotomy; and the connection to Abramsky–Brandenburger contextuality,
which per the project-goals memory is the strongest thread and the one that makes this a
*quantum information* thesis rather than a software paper. **This paper requires new
engineering** (organs that emit pairwise judgements, 2-simplex storage, δ¹) and cannot
be written before that lands.

**Paper C — "A thermal Hodge spectrum on CP³."** This is FIRST DRAFT, Section 3, and it
is your actual mathematics. The Morse/Frankel/Witten skeleton (Part VIII) is a
*legitimate and substantial* contribution to it: it fixes the β → ∞ boundary condition
rigorously and reduces the open region to intermediate β. **It has nothing to do with
MOS** and should not be contaminated by it. MOS's role is to be the tool that helped,
mentioned in acknowledgements or a methods note — not a co-author of the theorem.

The book's own §48 tiering already implies this split. It just does not draw the line.

### 3.2 The four things that must be settled before *any* paper is written

1. **Resynchronise the `.tex` with §5q of the logbook.** The mathematical description
   currently describes a system three days out of date and files as "proposed,
   unimplemented" things that are implemented and tested. This is the single largest
   correctness risk in the corpus, because every downstream criticism inherits it.

2. **Fix the category.** Until "what is a simple object / what is a memory atom" has an
   answer, §29–§32 and §47 are unwritable. F10 shows both offered answers fail. This is
   a modelling decision, it is yours, and it cannot be deferred to the algebra.

3. **Compute the independence relation I on the real operator set.** F4. One afternoon.
   It decides whether Part II is mathematics or decoration.

4. **Measure α and ρ̃ on real runs.** F12. One log line. It decides whether §5.4(a) is
   true.

### 3.3 The experimental programme, in the order the results actually gate each other

I list these as experiments with **stated falsification conditions**, because the
project's own stated virtue is that it makes its claims falsifiable, and none of the
following currently has a pass/fail line drawn in advance.

**E1 — α/ρ̃ instrumentation.** Log α, ρ̃, and the window [λ₂/B, λ_max/B] on every tick of
existing workloads. *Falsifies:* the encoder-anisotropy explanation of the dead dynamic
range (if α ≈ 0.5). *Also delivers:* the empirical distribution of ρ̃ needed to set q
honestly instead of guessing it (F11). Cost: free. **Do this first.**

**E2 — Λ(t), the workload-compression curve.** Fix a held-out workload of reasoning
acts. Plot mean act length in current atomic generators over time. *Falsifies the whole
augmentation bet* if flat. This is the project's first LLM-independent test and the
`.tex` promises falsifiability without providing it. Cost: a log. **Do this second, and
be willing to publish a flat line.**

**E3 — The clique polynomial of the real operator set.** Compute I, c_k, μ(z), κ. *Falsifies
Part II* if I is empty. Cost: one afternoon.

**E4 — W₂ term separation.** Report `d_semantic` and `d_epistemic` separately in
`knowledge_base.cpp`; log both across a merge/split workload. *Falsifies* the claim that
merge decisions are semantically driven (they may already be dominated by the D-floor).
Cost: free.

**E5 — The measured-η pilot.** Before building organ pairwise-judgement contracts, run
the cheapest possible version: on a 3-organ coalition with a filled 2-simplex, have each
organ emit a scalar pairwise agreement judgement, assemble η, and compute the
gradient/curl/harmonic split. *Falsifies* the Hodge programme if η turns out to be
essentially always a gradient (i.e. organs are implicitly consistent and there is no
curl or harmonic mass to find). Cost: 3 LLM calls per trial. **This is the decisive
experiment for Paper B and it is cheap.**

**E6 — The CP³ numerics.** Discretise Δ_β on 1-forms over CP³ (or on a suitable
finite-element/spectral truncation), sweep β, and check (i) no low-lying band, (ii) the
bottom grows linearly, (iii) the slope matches the constant derived per F8(b).
*Falsifies* the Part VIII skeleton, which is the one result in the corpus that is a
statement about the world rather than about MOS. **This is the highest-value experiment
in the entire programme** because it is the only one whose outcome is interesting to
someone who has never heard of MOS.

**E7 — Ext¹ recorded at composition time.** Per §48.3 item 5: record extension data when
composites are assembled, when the assembly is known and free. Do not attempt to recover
it later. This is cheap now and impossible later, so it should start immediately even
though the category question (F10) is unresolved — record the raw assembly, decide what
it means afterwards.

### 3.4 What the paper must not claim

Carrying forward the `.tex`'s own honesty discipline, which is the best thing about the
corpus and must not be lost in the expansion:

- Not "we prove the whole exceeds the sum." Ext¹ ≠ 0 says a composite is *structurally
  new*, not that it is true or useful. VerifyOp remains the sole arbiter and runs first.
- Not "capacity κ measures learning." It is gameable by adding independent useless
  operators. Report it; never optimise it.
- Not "MOS uses D-module theory." MOS uses Gaussians, which *are* the simplest holonomic
  modules — an exact identification that currently buys three invariants all of which
  are constant. The correct claim is: "the concept type admits a conservative extension
  to holonomic modules, feasible only because of the existing rank-k design (k ≤ 8)."
- Not "Riemann–Hilbert applies." One leg is rigorous (cellular sheaves are constructible
  sheaves via exit paths); the other is a design commitment to an algebraic
  stratification that has not been made. The book says this correctly in §49; keep it.
- Not "the threshold is derived." It is normalised (F11).
- Not "Theorem 7.5 is new" (F13).

---

## 4. Bottom line for the referee's report

**Accept the criticism; reject the architecture of the document.**

The scrutiny identifies four real defects in the `.tex` — the entangled ρ, the vacuous
H¹, the inert Hebbian weights, and the Tietze-triviality of δ𝔇 — and three of the four
are correct as stated. That is a strong result for a critique. The α/ρ̃ splitting and
Proposition 8.2 alone justify the entire document's existence.

But the document then spends four fifths of its length building a superstructure whose
foundations it has not tested: an independence relation nobody has computed (F4), a
category nobody has chosen (F10), a concept type nobody has built (Tier 3), and an
architectural change (measured η) whose cheaper half is circular (F3). It contains at
least four checkable technical errors (F2, F7, F9, F13) and one internal contradiction
(F11), any of which a competent referee finds in an afternoon. And it audits a document
rather than a system, so its second-highest-priority recommendation was already shipped
before it was written (F1).

The right response is neither to adopt it wholesale nor to dismiss it. It is to
**harvest Tier 1, run E1–E3 to decide whether Tier 2 is real, and quarantine Tier 3 as a
research direction with an explicit feasibility gate.** And to write Paper C — the CP³
result — as mathematics, separately, because it is the only part of this corpus whose
truth does not depend on any of the above.
