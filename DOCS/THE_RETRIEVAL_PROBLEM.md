# THE RETRIEVAL PROBLEM

*A full statement of what is wrong, why it is structural rather than a tuning miss, and what the
design space actually looks like. Written 2026-08-04 to be read cold, without assuming background
in embeddings or information retrieval.*

> **Read this before choosing a fix.** The three options currently on the table in §5at (A: widen
> the threshold; B: top-k; C: centre the embeddings) are all *repairs to a mechanism*. This document
> argues that the mechanism is doing something more consequential than it looks, and that the choice
> deserves a design, not a patch. My own suggestions are recorded in §7 and marked as what they are.

---

## 0. HOW TO READ THE NUMBERS IN THIS DOCUMENT

Every quantitative claim is tagged. There are three kinds and they are not interchangeable:

| Tag | Meaning | How much weight it carries |
|---|---|---|
| **[MEASURED]** | Came out of a run, on real data. | Full — subject to the sample it came from. |
| **[DERIVED]** | Algebra or arithmetic applied to a **[MEASURED]** number. | The arithmetic is sound; the conclusion inherits the measurement's limits. |
| **[INFERRED]** | Reconstructed indirectly, fitted, or resting on a very small sample. | Weak. **Do not build on one without remeasuring.** |
| **[ENGINEERING CHOICE]** | A decision made for cost, simplicity or convenience. Defensible, but **not evidence**, and a different choice would not be wrong. | None as evidence. |
| **[OPEN HYPOTHESIS]** | A claim we intend to test and have not. | None yet — it is a plan, not a result. |
| **[SPECULATION]** | A mechanism proposed to explain something, with no test behind it. | None. Flagged so it is never quoted as a finding. |

**The convention is used throughout this file and its companions, on every load-bearing claim.** It
exists because the failure mode in this project has not been bad statistics — it has been *good
numbers attached to conclusions they do not support*. A reader should never have to guess which is
which.

**A standing caution about sample size.** Counts of *labels* are not counts of *independent
observations*. The `\ref` labels come from **71 papers**; blocks inside one paper share a topic, an
author, and overlapping neighbourhoods. So `n = 2266` labels is closer to `n ≈ 71` independent
units, and every confidence interval quoted from label counts alone is **too narrow**. Where this
changes a conclusion it is stated inline.

The other fact about the evidence base worth knowing before §2: **the original claim that retrieval
was "missing genuinely related concepts" rested on exactly one hand-checked pair of sentences.** §10
replaced it with 2266 labels, and reversed part of the conclusion.

---

## 1. THE CHAIN — FROM TEXT TO TOPOLOGY

To see why retrieval matters more than it appears to, you have to see the whole chain it sits at the
head of. Nothing in this section is contested; it is just the mechanism, stated plainly.

### 1.1 A sentence becomes a vector

An **embedding model** is a function from text to a fixed-length list of numbers. MOS uses
`bge-small`, which maps any piece of text to a point in ℝ³⁸⁴, then divides by the length so every
output sits on the unit sphere S³⁸³.

The model was trained so that *similar meanings land near each other*. That training objective is
the only reason any of this works, and — importantly — it is a **soft, statistical** objective. The
model was never promised to produce a metric in which "these two papers are about the same
mathematics" is a clean geometric predicate. It was optimised so that it tends to be.

**Confirmed for our corpus [MEASURED]:** 1115 arXiv abstracts, 384 dimensions, norms in
`[1.0000, 1.0000]`. They really are unit vectors.

### 1.2 Two vectors become one number

For unit vectors the natural comparison is the **cosine**, which for unit vectors is just the dot
product:

```
cos(x, y) = ⟨x, y⟩
```

`1` means identical direction, `0` means orthogonal, `−1` means opposite. Because the vectors are
unit, squared Euclidean distance and cosine carry exactly the same information:

```
‖x − y‖²  =  ‖x‖² + ‖y‖² − 2⟨x,y⟩  =  2 − 2cos  =  2(1 − cos)          … (1)
```

**Identity (1) is exact, not an approximation, and only because the vectors are unit.** It is used
constantly below to move between the engine's units (squared distance) and the interpretable units
(cosine). Keep it in view; it is where the trouble becomes visible.

### 1.3 The engine's actual decision rule

Verified against source, not assumed:

**`SearchOp::apply`** (`src/operators/primitives.cpp:49–60`) sets, per tick:

```
D₁  = ‖q‖₂                    the query's "derived variance"
ε   = max(0.1, 1/dim)         the relevance threshold
```

**`KnowledgeBase::get_relevant_concepts`** (`src/translation/knowledge_base.cpp:153`) then scans
**every row of the store** and keeps a concept when squared Bures–Wasserstein distance is under ε:

```cpp
while (sqlite3_step(stmt) == SQLITE_ROW) {
    if (stored_dim != thought_mu.size()) continue;        // fast dimension rejection
    double w2_sq = calculate_wasserstein_2_sq(thought_mu, thought_D, mu, U, D);
    if (w2_sq <= epsilon) { results.push_back(...); }
}
```

Two properties of this loop matter later and are easy to miss:

- **The scan is unbounded.** There is no `LIMIT`, no top-k, no early exit. The number of concepts
  returned, `|A|`, is whatever the threshold admits — bounded by the corpus size, not by a constant.
- **It is a metric ball.** The retrieved set is exactly `B(q, √ε)`, the ball of radius `√ε` around
  the query in one fixed global metric. That is a strong geometric commitment, and §4 is about what
  it commits you to.

**The distance itself** (`wasserstein_2_terms`, `semantic_skill.cpp:234`) splits into two pieces:

```
W₂²(q, c)  =  ‖μ_q − μ_c‖²   +   [d·D₁ + d·D₂ − 2√D₁ · tr(√Σ_c)]
              ─────────────       ────────────────────────────────
              semantic term            epistemic term
```

For a **rank-0** concept — which is every concept `ingest_corpus.py` writes, since a chunk seen once
has no scatter about its own mean (FIX-13) — the epistemic term collapses **exactly**:

```
tr(√Σ_c) = d·√D₂
⇒ epistemic = d·D₁ + d·D₂ − 2√D₁·d·√D₂ = d·(√D₁ − √D₂)²      … (2)
```

**(2) is an algebraic identity, not an approximation.** It has a sharp consequence. With unit
queries, `D₁ = 1`. If a concept were stored with the usual fresh variance floor
`stalk_floor(384, n_eff=1) = O(1/d)`, then `(√1 − √(1/384))² ≈ 0.9` and the epistemic term alone is
`384 × 0.9 ≈ 346` — vastly over any sane ε, so **nothing would ever be retrieved regardless of
meaning**. This is why `ingest_corpus.py` stores `D = 1.0`: it is the unique value making the
epistemic term vanish, so that relevance is decided by meaning rather than by a bookkeeping
mismatch. **Any fix that changes vector norms must preserve `D₁ = D₂` or it silently reintroduces
this 346.** It is the single most breakable coupling in the system.

### 1.4 What retrieval feeds — and this is the part that makes it structural

Retrieval is not a lookup that hands results to a user. Its output *is* the raw material of memory:

```
query
  → RETRIEVAL RULE
      → A(t) = the assembly: the set of concepts co-active on tick t
          → an EDGE between every pair in A(t)              (the co-activation graph)
              → a TRIANGLE for every triple in A(t)          (2-cells, if |A(t)| ≤ 30)
                  → b₁, harmonic mass, the growth address
              → the co-activation matrix X
                  → Tier 0: does a latent COVER explain X?
                      → Constructions 4 and 5, the organ structure, γ(ν), what crystallises into 𝕂
```

Read that top to bottom and the thesis of this document is already visible:

> **The retrieval rule is not a preprocessing step. It is the generating function of the complex.**
> Every edge, every 2-cell, every cycle, every cover element, every number Tier 0 reports, is a
> shadow of the rule that decided which concepts fire together. Choose the rule and you have
> already constrained — before any data is seen — what shapes memory is *able* to take.

That is why "just widen ε" is the wrong register of answer.

---

## 2. THE MEASURED FAILURE

### 2.1 What was run

`simulate_retrieval.py` reproduces the C++ rule exactly (the identity (2) is what makes "exactly"
honest rather than "approximately") and swept ε over the real corpus: 1115 concepts, 3000 distinct
query sentences.

**[MEASURED]:**

| ε | ⟺ cos ≥ | mean concepts/tick | % ticks with a pair | % ticks empty |
|---|---|---|---|---|
| **0.10 (engine default)** | **0.95** | **0.07** | **0.0%** | **93.4%** |
| 0.20 | 0.90 | 0.28 | 0.2% | 71.8% |
| 0.30 | 0.85 | 0.63 | 8.1% | 50.5% |
| 0.40 | 0.80 | 6.34 | 48.0% | 31.8% |
| 0.50 | 0.75 | 58.75 | 70.9% | 21.0% |
| 0.60 | 0.70 | 193.98 | 82.6% | 12.2% |
| 0.80 | 0.60 | 627.44 | 97.0% | 1.8% |

At the engine's own default, **zero ticks out of 3000 retrieved a pair.** Not "sparse" — zero. No
edges, no matrix, no `Q(t)` movement, nothing downstream can run.

### 2.2 The two things that made 0.10 a duplicate filter

**First:** `ε = max(0.1, 1/dim)` is **exactly `0.1` for every `dim > 10`**. The `1/dim` branch has
never executed in the history of the project. The threshold looks dimension-adaptive and is a
constant.

**Second [DERIVED]:** by identity (1), `‖Δμ‖² ≤ 0.1` ⟺ `cos ≥ 0.95`. A cosine of 0.95 between two
independently written mathematical abstracts is a paraphrase, not a topic match. The threshold is a
**near-duplicate detector** wearing a relevance detector's name.

Confirmatory hand-checks **[MEASURED, n=2]**: near-duplicate phrasings scored `0.0245` (admitted);
"sheaf cohomology of a simplicial complex" vs "Hodge decomposition on graphs" scored `0.5214`
(rejected, by more than 5×).

### 2.3 Why no value of ε rescues it — the pedestal

This is the heart of the diagnosis, and it is derivable from the sweep table alone.

Divide each "mean concepts/tick" by 1115. That converts the table into the **survival function of
the pairwise cosine distribution** — the fraction of the corpus above each cosine level
**[DERIVED]**:

| cos ≥ | fraction of corpus above |
|---|---|
| 0.95 | 0.006% |
| 0.90 | 0.03% |
| 0.85 | 0.06% |
| 0.80 | 0.57% |
| 0.75 | 5.3% |
| 0.70 | 17.4% |
| 0.60 | 56.3% |

Since 56.3% of pairs are above 0.60, the **median pairwise cosine is ≈ 0.61** [DERIVED, by
log-linear interpolation between the 0.60 and 0.70 rows].

Now the key algebraic step. Write each unit vector as its shared part plus its individual part:

```
x = μ̄ + rₓ ,     μ̄ = E[x]  (the corpus mean vector),   E[rₓ] = 0
```

For two **independently drawn** documents, `E[⟨x,y⟩] = ⟨E x, E y⟩ = ‖μ̄‖²` — exactly, no
approximation. So the observed median/mean cosine of ≈ 0.61 is telling us directly:

> **‖μ̄‖² ≈ 0.6, i.e. ‖μ̄‖ ≈ 0.78** [INFERRED — from the sweep table rather than from the vectors;
> one line of numpy would confirm it].
>
> **About 60% of the squared length of every single embedding is one and the same direction**,
> shared by all 1115 abstracts regardless of subject. Loosely, it encodes "this is technical English
> prose about mathematics."

Expand the cosine into its parts:

```
cos(x,y)  =   ‖μ̄‖²    +   ⟨μ̄, rₓ⟩ + ⟨μ̄, r_y⟩   +   ⟨rₓ, r_y⟩
              ───────      ────────────────────       ─────────
              constant     per-document nuisance      THE SIGNAL
              (pedestal)   (varies by doc, says       (the only term that
                            nothing about the pair)    knows about the pair)
```

Only the last term carries information about whether *x* and *y* are related. The first is a
constant offset. The middle two vary from document to document and are pure nuisance — they add
spread without adding signal.

Substituting into identity (1), the quantity the engine thresholds is:

```
‖Δμ‖²  =  2(1 − cos)  ≈  2(1 − 0.6) − 2⟨rₓ, r_y⟩  =  0.8 − 2⟨rₓ, r_y⟩ − (nuisance)
```

**The engine's distance is a constant 0.8 minus twice the signal.** Requiring `‖Δμ‖² ≤ 0.1` means
requiring `⟨rₓ, r_y⟩ ≥ 0.35` — out of a total residual energy of only `1 − 0.6 = 0.4`. That is
near-perfect alignment of the informative parts, which is precisely what "paraphrase" means. **The
observation in §2.2 falls out of the algebra.** Nothing was mis-set; the rule was always going to do
this on embeddings shaped like these.

### 2.4 The dial, in interpretable units

| what it is | cosine | engine distance ‖Δμ‖² |
|---|---|---|
| two unrelated abstracts (typical) | ~0.61 | ~0.78 |
| **genuinely related** (sheaf ↔ Hodge) **[MEASURED, n=1]** | **0.739** | **0.5214** |
| a paraphrase | ~0.99 | ~0.02 |
| **the engine's cutoff** | **0.95** | **0.10** |

The usable range of the dial runs from ~0.78 (unrelated) down to 0 (identical). The cutoff sits at
0.10 — **13% of the way in.** The one genuinely related pair we have sits at 0.52 — **67% of the way
in.** The cutoff is not slightly too strict. It is in a different regime.

### 2.5 The squeeze — why option A is infeasible, not merely skewed

Three constraints, each independently derived, that do not fit together:

**(i) To admit the one known related pair, you need ε ≥ 0.53.** Its distance is 0.5214 **[MEASURED,
n=1]**. Note this immediately kills option A at ε = 0.40, which corresponds to cos ≥ 0.80 and
therefore still **rejects** the canonical example of what retrieval is supposed to accept.

**(ii) At ε ≈ 0.53 you retrieve ~7% of the corpus, ≈ 77 concepts per tick.** By interpolation in the
survival table, `P(cos ≥ 0.739) ≈ 6.9%`, so rank ≈ 77 of 1115 **[DERIVED]**. This is a *model-free*
quantile — it does not depend on fitting any distribution.

**(iii) But §5as derived a hard ceiling of 30.** `max_assembly_for_triangles = 30`, fixed by the
5.9 GB memory budget: an assembly of size *n* contributes `C(n,3)` triangles, and `n = 30` already
means 4060 triangles per tick. Assemblies wider than 30 keep their edges but **lose their 2-cells**,
and every skipped one leaves `(n−1)(n−2)/2` unfilled cycles that are **indistinguishable from
genuine holes** — b₁ becomes contaminated. The engine counts skips (`skipped_wide_assemblies()`)
precisely because a nonzero count invalidates the topology.

Putting these together **[DERIVED]**:

```
retrieval must return ≈ 77/tick   to be semantically valid
retrieval must return ≤ 30/tick   for b₁ to be trustworthy
retrieval currently returns 0.07/tick
```

**There is no value of ε satisfying both. Option A does not have a weakness; it has an empty
feasible set.**

### 2.6 Why option B, as usually understood, does not escape the squeeze either

Top-k retrieval ("keep the k nearest regardless of absolute distance") is genuinely valuable — it
guarantees a usable assembly every tick, eliminates the empty-tick problem, bounds the unbounded
scan, and satisfies the triangle cap by construction if `k ≤ 30`.

But notice what it does **not** do. Top-k is a **monotone** function of the same cosine. The related
concept sits at **rank ≈ 77**. Taking the top 30 still misses it. k = 30 out of 1115 is the top
2.7%, which is *roughly as strict as ε = 0.40* — the option we just showed is too strict.

> **A and B are both answers to the question "how far down the ranked list do we go?"** They differ
> in the *variance* of the retrieval budget, not in the *ordering*. Neither can promote a related
> concept above an unrelated one, because both read the same number.

**Only a change to the number itself can reorder the list.** That is the entire content of option C,
and it is why C is a different *kind* of proposal rather than a third alternative.

---

## 3. THE FORK: IS THE SCORE BAD, OR IS THE READING OF IT BAD?

Two failures are tangled together and they have very different prices.

**Failure 1 — the score is weak.** `bge-small` genuinely does not separate related mathematics from
unrelated mathematics well. If this dominates, *no retrieval rule fixes it*; you need a different
embedder.

**Failure 2 — the reading is broken.** The score carries real information, but the pedestal plus an
absolute cutoff discards it. If this dominates, the fix is free and lives entirely in our code.

### 3.1 What the evidence says

The related pair at the ~7% quantile means: **ranking by this score, roughly 7 in every 100
completely unrelated pairs outscore a genuinely related pair.** So:

- The score is **not noise** — related does rank above the bulk. There is real signal.
- The score is **mediocre** — a ~1.3–1.5 standard-deviation separation [INFERRED; the σ requires
  fitting a distribution to the tail and the fit is not good globally, which is why the model-free
  7% quantile is the number to quote].

So the honest answer to "is the problem the engine's ability to assign a number to relatedness?" is:

> **Partly, and it is not the engine that assigns it.** `bge-small` assigns it; the engine only
> compares it to a cutoff. The number is real but weak (Failure 1, present, moderate). On top of
> that the engine reads it in a way that destroys most of the information that *is* there (Failure
> 2, severe, self-inflicted, free to fix).

### 3.2 The mechanism by which centering could genuinely help — stated so it can be checked

It is important not to hand-wave here. Centering is *not* merely a rescaling. Look again at the
decomposition:

```
cos(x,y) = ‖μ̄‖² + ⟨μ̄,rₓ⟩ + ⟨μ̄,r_y⟩ + ⟨rₓ,r_y⟩
```

Subtracting the corpus mean and renormalising leaves you comparing `rₓ` and `r_y` directly:

```
cos_centred(x,y) = ⟨rₓ, r_y⟩ / (‖rₓ‖ ‖r_y‖)
```

This removes the constant **and** the two per-document nuisance terms. The nuisance terms were
contributing *variance without signal* — so removing them can raise the separation, not just shift
the origin. **This is a real mechanism, and it is also the reason centering is not guaranteed to
work**: if the nuisance terms happen to be small relative to the spread of `⟨rₓ,r_y⟩` itself, you
gain almost nothing.

Crucially, because `cos_centred` is **not a monotone function of `cos`**, centering *can* change
ranks — moving a related pair from #77 to inside the top 30. That is the only thing that would make
constraints (i) and (ii) of §2.5 compatible. Whether it does is an empirical question nobody has
asked yet.

**Two facts about centering worth knowing before adopting it:**

- **It preserves the `D = 1.0` coupling.** After renormalising, `‖q‖ = 1` still, so `D₁ = D₂ = 1`,
  so the epistemic term (2) still vanishes exactly. The most breakable coupling in the system
  survives. C is *less* invasive than §5at credited it with being.
- **"Centre the mean" and "all-but-the-top" are different fixes.** Mu & Viswanath's *all-but-the-top*
  subtracts the mean **and** projects out the top ~d/100 principal components. Removing the rank-1
  mean is the weak version. Which one you adopt is a separate decision that §5at collapsed into one
  bullet.

### 3.3 The measurement that resolves the fork

One number, computed before and after any candidate transform, on hand-labelled pairs:

```
z  =  ( mean cos of RELATED pairs  −  mean cos of UNRELATED pairs )  /  sd of UNRELATED pairs
```

- **z rises substantially** ⇒ Failure 2 dominated; the reading was the problem; proceed.
- **z barely moves** ⇒ Failure 1 dominates; the embedder cannot separate this material; no retrieval
  rule saves it, and the fix is a different or fine-tuned model.

This is the single highest-value measurement available right now, and it costs no LLM budget. It
does require labels — see §8.

---

## 4. WHY THIS IS STRUCTURAL — THE PART THAT DESERVES YOUR TIME

Everything above treats retrieval as a component that is malfunctioning. This section argues it is
also a **modelling commitment**, and that is the reason to think hard rather than patch.

### 4.1 The retrieval rule is a prior on the shape of memory

From §1.4: assemblies generate edges, edges and triples generate the complex, the complex is what
Tier 0 and Constructions 4 and 5 interrogate. Therefore:

> Whatever family of shapes the retrieval rule can produce **is** the family of shapes memory can
> have. Structure the rule cannot express is not merely hard to find — it is unrepresentable.

The current rule returns `B(q, √ε)`, a **ball in one fixed global metric**. So the assemblies are
metric balls, the graph is a *unit-disc graph* on the embedding sphere, and the complex is (close
to) the **Čech nerve of a cover by equal-radius balls**. That is a very particular family. It is
homotopy-theoretically well-understood and it is *poor at expressing a concept belonging to several
unrelated contexts*, because a ball around a point is a single, convex, isotropic neighbourhood.

### 4.2 The tension with MOS's own theory

This is the sharpest version of the point, and I think it is the one worth sitting with.

MOS's entire architecture asserts that **relatedness is context-dependent.** That is what the cover
is: an object belongs to several patches. That is what the sheaf structure is for: what a concept
*means* depends on which patch you restrict to. §5ap chose arXiv cross-listing as the corpus
precisely because *"a paper filed under both `math.AT` and `math.DG` is literally one concept
claimed by two topics."*

But the retrieval rule says relatedness is a **single global scalar** — one number per pair, one
metric, one radius, context-free. Those two positions are not compatible. A cross-listed paper is
close to `math.AT` work *along one set of directions* and close to `math.DG` work *along a different
set*. A single isotropic ball in the full 384-dimensional space averages those two relationships
into one number and can only report their mean.

> **The engine is looking for context-dependent structure using a context-free instrument.**

This does not mean Tier 0 is meaningless. It does mean a negative Tier-0 result is much harder to
interpret than §5ap assumed: "no cover structure found" could equally well mean "the retrieval rule
cannot express cover structure." That is a limit on the *experiment*, not just on the corpus, and it
should be stated beside any verdict.

### 4.3 A concrete circularity hazard, grounded in the code

Tier 0 asks whether a **noisy-OR latent-cause model** explains the co-activation matrix better than
a **mixture model**, against a bootstrap null. Reading `cover.py:479`, the null is generated by
`_simulate_mixture(gen, n, rng, M)` — it draws synthetic rows from a *fitted mixture*.

Two hazards follow, neither of which is currently controlled:

1. **The null does not know the data are metric balls.** Observed rows are balls in a metric space;
   simulated rows are draws from a mixture of independent Bernoullis. Metric-ball data has strong
   geometric coherence (if *a* and *b* are both near *q*, they are near each other — a triangle
   inequality effect) that a Bernoulli mixture cannot generate. That coherence could read as
   latent-cause structure. **A "cover" might be recovered that is nothing but the ball structure of
   the embedding metric.**
2. **Fixed-k retrieval would make this worse, not better.** Top-k gives every row *exactly* k ones.
   A fitted mixture generates row sizes with genuine variance around its mean; it **cannot** produce
   a constant row sum. So observed and null would differ in a way that has nothing to do with latent
   structure. §5at flagged this as a concern; reading `_simulate_mixture` confirms it is real. The
   direction of the resulting bias is **not obvious** and would need simulation to establish.

**The clean remedy for both is the same in spirit:** the null must be generated by a process that
matches the observed data in every respect *except* the structure being tested. A null built by
sampling ball-shaped assemblies from a *geometrically null* embedding (e.g. the same vectors with
topic structure destroyed but the anisotropy preserved) tests what Tier 0 claims to test. The
current null does not.

### 4.4 The retrieval rule also silently sets the topology's validity

From §2.5(iii): assemblies wider than 30 lose their 2-cells and inject fake b₁. So the retrieval
rule's *width distribution* directly controls whether the harmonic mass — the growth address, the
thing §5r's growth law is built on — means anything at all.

Note this cuts differently for different consumers, and conflating them has been costing us:

| consumer | reads | cares about width? |
|---|---|---|
| Tier 0 / cover fitting | the co-activation **matrix** (edges) | only via the null's calibration |
| b₁ / harmonic growth address | **2-cells** | **hard cap at 30, or the number is contaminated** |

**These two may not want the same retrieval rule, and nothing says they must share one.** The
existing code already records edges for wide assemblies while skipping their triangles *and counting
the skips*. That is arguably already the right architecture, and it means "one ε for everything" was
never a requirement — it was an assumption.

---

## 5. THE DESIGN SPACE

A wider menu than A/B/C, each entry stated with what it *assumes* and what shapes it can produce —
because per §4.1 that is the real cost, not the implementation effort.

### 5.1 Rules that keep one global metric

**(a) Absolute threshold — the current rule.**
Assumes relatedness is a context-free scalar with a *corpus-wide meaningful scale*. §2 shows the
scale is dominated by a pedestal, so this assumption fails on these embeddings. Produces: equal-radius
metric balls. Cost: nothing. Verdict: infeasible per §2.5.

**(b) Top-k / k-NN.** Assumes relatedness is a context-free *ranking* — no scale needed. Robust to
any monotone distortion, including the pedestal. Produces: fixed-size neighbourhoods, a k-regular
digraph. Cost: trivial. **Watch:** breaks the null (§4.3.2), and introduces **hubness** — in an
anisotropic space, the vectors nearest the mean direction μ̄ land in almost everyone's top-k, which
would manufacture one giant spurious cover element. k-NN *without* fixing the geometry is actively
hazardous for the experiment being run.

**(c) Mutual k-NN.** Keep *c* only if *q* is in *c*'s top-k **and** *c* is in *q*'s top-k.
Standard hubness suppressant; produces a sparser, symmetric, more honest graph. Cost: trivial.
Changes the shape family meaningfully — mutual-kNN graphs are much less prone to giant components.

**(d) Locally-adaptive radius** (Zelnik-Manor–Perona self-tuning). Give each concept its own scale
`σ_c` = distance to its m-th neighbour, and threshold `‖Δμ‖²/(σ_q σ_c)`. Assumes relatedness is
context-free but **density varies across the space**. Produces: variable-radius balls — a genuinely
richer nerve than (a). This is the "principled ε" version of A and nobody has costed it. Cheap.

**(e) Centering / all-but-the-top / whitening.** Not a retrieval rule at all — a **change of the
metric** that any of (a)–(d) then run on top of. This is the only family that reorders. Whitening is
the aggressive end (equalise all directions); mean-removal the mild end. **Watch:** whitening
destroys `‖x‖ = 1` unless you renormalise, and §1.3's identity (2) then reintroduces the 346.

### 5.2 Rules that abandon the single global metric — the sheaf-native direction

These are more work and are, I think, where the interesting version of this problem lives, because
they are the only ones whose expressible shapes match what MOS claims memory is.

**(f) Subspace-restricted relatedness.** Relatedness *within a context* = cosine after projecting
both vectors onto that context's subspace. A cross-listed paper is then genuinely close to `math.AT`
work in one projection and `math.DG` work in another, with no averaging. Directly expresses
"one concept claimed by two topics." **This is what a restriction map already is in your own
formalism** — §5's Householder maps are exactly linear maps into patch-local coordinates. The
retrieval rule and the sheaf's restriction maps would stop being separate mechanisms.
**Hard part, and it is a real one:** the contexts are what Tier 0 is supposed to *discover*, so this
looks circular. It may not be — a bootstrapping or EM-style alternation (retrieve with current
contexts → refit contexts → re-retrieve) is a standard escape, and it converts a static filter into
a *learning* one, which is arguably what "the structure molds and evolves" requires.

**(g) Multi-scale / persistent retrieval.** Refuse to pick one ε. Build the filtration over all ε
and keep the features that persist. Assumes nothing about the right scale — it makes scale a
*variable* rather than a constant. Produces: a persistence diagram rather than one complex. Fits
this project unusually well, because §5ah already found **no privileged granularity exists in this
corpus** — a monotone k-sweep with no interior optimum. That finding is *evidence that a
single-scale rule is the wrong object*, and it has been sitting in the logbook unexploited.

**(h) Asymmetric / directional relevance.** Drop the assumption that relatedness is symmetric.
"Hodge theory is relevant to my sheaf question" and the converse are not the same claim. Produces a
directed complex; changes what cohomology means; substantial theoretical work.

**(i) Learned metric.** Use labelled pairs to fit a Mahalanobis metric `⟨x, My⟩` or fine-tune the
embedder. Highest ceiling; requires labels; risks overfitting to the labelled set and to this
corpus.

### 5.3 Rules that change what is being compared

**(j) Better embedder.** `bge-small` is 384-d and small by design. If §3.3's `z` says Failure 1
dominates, this is the answer and nothing else is. Costs compute, not theory.

**(k) Hybrid lexical + dense.** Combine cosine with a sparse term-overlap score (BM25). Mathematics
has heavy technical vocabulary; exact term matches carry a lot of signal that a 384-d compression
loses. Cheap, well-understood, and orthogonal to everything else — it adds information rather than
re-reading existing information.

**(l) Ask a model.** Have an LLM judge relatedness. Highest quality, blows the budget at 1115 × 3000
scale, but viable to generate *the labelled set* (see §8) — which is exactly the leverage point.

---

## 6. INVARIANTS ANY SOLUTION MUST RESPECT

A checklist to design against. Each is derived above or verified in source.

1. **`D₁ = D₂` must hold**, or identity (2) reintroduces an epistemic penalty of ~346 and nothing is
   ever retrieved. Any transform that changes norms must renormalise. *(§1.3)*
2. **The C++ scan is unbounded.** `|A|` is bounded by corpus size, not a constant. Any rule that does
   not impose a cap leaves an O(N) tail risk at every tick. *(`knowledge_base.cpp:153`)*
3. **`|A| ≤ 30` for 2-cells**, or b₁ is contaminated by `(n−1)(n−2)/2` fake cycles per skipped
   assembly. Skips are counted; a nonzero count must be reported beside any topological claim. *(§5as)*
4. **The Tier-0 null must match the observed data in everything except the tested structure** —
   including row-size distribution and geometric coherence. It currently matches neither. *(§4.3)*
5. **Queries are drawn from the same abstracts that became concepts.** This inflates *how much* is
   retrieved. It does not obviously bias the *shape*, but it belongs beside any verdict. *(§5ap)*
6. **Dimension must stay 384** or `get_relevant_concepts`'s fast dimension rejection silently skips
   every stored concept — the exact failure that left the store looking empty. *(§5ap)*
7. **Whatever is chosen must be stated as a modelling assumption in any write-up**, because per §4.1
   it bounds the conclusions. A retrieval rule is not an implementation detail in a paper about the
   shape of memory.

---

## 7. MY OWN SUGGESTIONS, MARKED AS WHAT THEY ARE

Recorded for completeness. **These are repairs that get the pipeline running; they are not answers
to §4.** If the aim is to get *a* number out of Tier 0 this week, this is the cheap path. If the aim
is to get the structure right, §5.2 is where to look.

- **Fix the metric before choosing the rule** (5.1e). Centering is cheap, preserves invariant 1, and
  is the only cheap move that can reorder.
- **Then use k as a cap, not a fixed count** (5.1b/c). Satisfies invariants 2 and 3 by construction;
  "cap" rather than "fixed" avoids the constant-row-sum problem in invariant 4.
- **Consider letting Tier 0 and b₁ use different widths** (§4.4). Nothing requires one ε.
- **Fix the null regardless of which rule wins** (§4.3). This is not optional — it determines whether
  a Tier-0 PASS means anything, and it is currently the weakest link in the whole experiment. It is
  arguably higher priority than the retrieval rule itself.

The honest summary of my position: **item 4 is the one I would defend hardest, and it is
independent of the A/B/C choice entirely.**

---

## 8. WHAT IS ACTUALLY BLOCKING PROGRESS

**Not the theory. Labels and files.**

**The labels.** Everything quantitative about semantic quality in this document rests on **one**
hand-checked pair. `z` (§3.3) cannot be computed, options cannot be compared, and no rule from §5
can be evaluated, without a labelled set. E14's ~50 hand-labelled pairs has been on the owed list for
a while. **It is now the binding constraint on every path in §5.** Roughly an hour of your time, zero
compute, zero LLM budget — or generated by (5.3l) at a very small budget with spot-checking. Nothing
else in this document is worth doing first.

**The files.** `concepts.npz`, `queries.npz`, `corpus_manifest.json` were generated on Colab and
**exist nowhere on this machine** (`MOS/python/` and `~/Downloads` both checked, 2026-08-04, still
absent). Every measurement proposed here needs them.

**And the reason Colab existed has evaporated.** Colab was chosen so `DOCS/` would not be uploaded to
Google. §5ap then changed the corpus to **public arXiv abstracts**. The privacy constraint no longer
applies, so Colab now contributes only file hand-off friction — which is exactly what broke. The
arXiv fetch (`arxiv.org/api/query`) currently lives *only* inside `colab_prepare_corpus.ipynb`;
`ingest_corpus.py` reads `DOCS/` or a precomputed `.npz`. Lifting that fetch into a local script is
small and ends the entire class of failure.

---

## 9. OPEN QUESTIONS WORTH YOUR TIME

Ordered roughly by how much they change the design rather than the settings.

1. **Should relatedness be one number at all?** §4.2 says MOS's own theory says no. If relatedness is
   context-dependent, a scalar filter is a category error, and every option in §5.1 is a compromise.
   What is the smallest departure from a scalar that buys real expressiveness — a small set of
   subspace projections? A rank-r metric?
2. **Should the rule be static, or should it evolve with the structure it builds?** Currently
   retrieval is fixed and memory grows underneath it. Option (f) makes retrieval a function of the
   current cover, which then updates the cover. That is closer to "the structure molds and evolves"
   — and it is also a fixed-point / convergence question with real mathematical content. Does the
   alternation converge? To what? Is it the free-energy descent you already have?
3. **Is a single scale defensible at all, given §5ah found no privileged granularity?** That finding
   is stronger evidence than it has been given credit for. Option (g) takes it seriously.
4. **What is the right null?** (§4.3) Not a detail. If the null cannot distinguish "latent cover" from
   "balls in a metric space", Tier 0 answers a different question than the one asked.
5. **Should Tier 0 and the b₁ machinery share a retrieval rule?** (§4.4) They have different
   requirements and the code already treats them differently.
6. **Is `bge-small` adequate?** (§3.3) Answerable in one hour once labels exist, and it gates
   everything.

---

## APPENDIX — QUICK REFERENCE

**Identities (exact, both used throughout):**
```
(1)  ‖x − y‖² = 2(1 − cos(x,y))                    for unit vectors
(2)  epistemic term = d·(√D₁ − √D₂)²                for rank-0 concepts
```

**Key measured quantities:**
```
corpus                      1115 concepts, 384-d, unit norm, 74% cross-listed
queries                     3000 distinct sentences
median pairwise cosine      ≈ 0.61                         [DERIVED from the sweep]
‖μ̄‖² (the pedestal)         ≈ 0.60,  ‖μ̄‖ ≈ 0.78            [INFERRED — verify with numpy]
engine cutoff               ε = 0.10  ⟺  cos ≥ 0.95        [MEASURED / DERIVED]
one related pair            0.5214    ⟺  cos = 0.739       [MEASURED, n = 1]
  → its quantile            ≈ 6.9%,  rank ≈ 77 of 1115     [DERIVED]
triangle cap                |A| ≤ 30                        [DERIVED from 5.9 GB budget]
```

**The squeeze, in one line:**
```
need ~77/tick for validity   |   allowed ≤30/tick for topology   |   getting 0.07/tick today
```

**Source anchors:**
```
src/operators/primitives.cpp:49-60          SearchOp — sets D₁ and ε
src/translation/knowledge_base.cpp:153      the unbounded threshold scan
src/core/semantic_skill.cpp:234             wasserstein_2_terms
MOS/python/cover.py:479                     calibrated_compare — the Tier-0 null
MOS/python/simulate_retrieval.py            the faithful no-engine reproduction
DOCS/TATIANA_LOGBOOK.md §5ap, §5as, §5at    corpus decision, triangle cap, the handoff
```

---

# 10. MEASURED (2026-08-04) — THE LABELS EXIST, AND THEY OVERTURNED THE PLAN

§8 said labels were the binding constraint. They were built, and they changed the answer. **Read
this section before §5 or §7 — it supersedes their recommendations.**

## 10.1 The labelled set

`extract_refs.py` fetches arXiv LaTeX source and turns each paper's own `\label`/`\ref` graph into
ground-truth relatedness positives. **[MEASURED]**

```
71 papers, six categories (math.AT, math.DG, math-ph, quant-ph, math.PR, stat.ML)
2468 blocks   (957 section, 506 lemma, 304 proposition, 280 theorem, 191 corollary, ...)
2266 ref-edges = ground-truth positives
```

We went from **1** hand-checked pair to **2266**. Cost: no hand-annotation, no LLM budget, ~15 min
of network time. Labels are high-precision positives and unusable as negatives, so every metric
below is recall-style.

## 10.2 The geometry, now measured rather than inferred

```
pedestal ||mu_bar||^2   0.671      (2.3 INFERRED 0.60 from the sweep -- right phenomenon,
||mu_bar||              0.819       underestimated by ~12%)
cos, unrelated pairs    mean 0.669, median 0.672, sd 0.056
cos, cited pairs        mean 0.777, median 0.778
separation z            1.92        (3.1 INFERRED 1.3-1.5 -- the signal is BETTER than feared)
```

> **Note the corpus difference, honestly:** this is 2468 *blocks within papers*, not the 1115
> *abstracts* of §5ap. The pedestal phenomenon is confirmed and is large; the specific value for the
> abstract corpus remains unmeasured.

## 10.3 The engine's own rule, against ground truth

**`ε = 0.10` admits 0.31% of true dependencies.** The blocker of §2 is reproduced on labelled data.

## 10.4 THE TABLE — threshold vs rank, at equal cost

Retrieval width per tick, recall of true positives, against the `|A| ≤ 30` triangle cap. **[MEASURED]**

| ε-ball | cos ≥ | width/tick | recall | vs cap |
|---|---|---|---|---|
| 0.10 *(engine today)* | 0.950 | **0.3** | **0.3%** | OK |
| 0.30 | 0.850 | 4.2 | 13.4% | OK |
| **0.40** | 0.800 | **25.8** | **37.5%** | OK |
| 0.50 | 0.750 | 185.0 | 66.1% | 6× over |
| 0.53 | 0.735 | 306.9 | 72.5% | 10× over |
| 0.70 | 0.650 | 1623.4 | 96.6% | 54× over |

| top-k *(on abtt-10)* | width/tick | recall | triangles @3000 ticks |
|---|---|---|---|
| 10 | 10 | 35.5% | 0.4 M |
| 20 | 20 | 44.3% | 3.4 M |
| **24** | **24** | **46.6%** | **6.1 M** |
| 30 | 30 | 48.5% | 12.2 M |
| 50 | 50 | 53.4% | 58.8 M |

**At equal width (~25), rank-based retrieval scores 46.6% against the ε-ball's 37.5% — nine points
free — and it eliminates the variance entirely: no empty ticks, no over-cap ticks.**

## 10.5 The transforms — every candidate from §5, measured

Corpus-wide, 2467 candidates per query. **[MEASURED]**

| transform | r@10 | r@30 | median rank |
|---|---|---|---|
| **raw** (the engine's metric) | 32.0% | **44.2%** | 48 |
| centered (option C, weak) | 32.6% | 46.7% | 39 |
| abtt-1 | 33.8% | 48.3% | 36 |
| abtt-10 | 35.5% | 48.5% | 36 |
| localscale m=30 (5.1d) | 33.3% | 47.5% | 37 |
| two-stage (coarse→fine) | 34.5% | 48.4% | 34 |
| diffusion α=0, t=0.25 (R1, best of 12) | 27.0% | 39.6% | 105 |
| diffusion α=1, t=2 (R1, as first configured) | 7.4% | 13.2% | 450 |

> **⚠️ CORRECTION (2026-08-04, self-audit). An earlier version of this table called `abtt-10` "option
> C, best" and the decision in §10.7 adopted it on that basis. That was argmax-of-a-flat-sweep.**
> abtt-1 → 48.3%, abtt-5 → 48.3%, abtt-10 → 48.5% are **indistinguishable** once the effective
> sample size (~71 papers, not 2266 labels) is accounted for. The honest reading is:
>
> **[MEASURED]** removing the mean plus a *small* number of principal directions is worth ~+4 points
> over raw. **[ENGINEERING CHOICE]** any `r` in 1–10 is equivalent; **take `r = 1`** because it is
> the simplest and needs no justification for the number.
>
> This is the same error §5aj identified in the k-sweep — reading an optimum off a flat curve — made
> again in the document that cites it.

## 10.6 ★ WHAT THIS OVERTURNS

**1. The pedestal was never a ranking problem — only a thresholding problem.** For a fixed query,
`||mu_bar||^2` and `<mu_bar, r_q>` are constant in `k` and **cannot affect rank order**. Only
`<mu_bar, r_k>` (hubness) can, and removing it is worth **+4.3 points**. Meanwhile abandoning the
absolute threshold is worth **0.3% → 44.2%, a factor of ~140.**

> **The entire A-vs-B-vs-C argument was about a 4-point effect while the actual fix was worth 140×.**
> §2.6 was correct that only C reorders, and wrong to make that the decisive criterion.

**2. §2.5's "empty feasible set" was too pessimistic.** It generalised from one pair at rank 77.
With 2266 pairs the median rank is 48 and ~47% land inside the cap. A median positive outside the
cap is not a broken system — it is a system that captures roughly half of true co-activation, which
is ample for accumulating statistics.

**3. R1 (diffusion / the heat-map metric) is refuted on this data.** Twelve configurations
(α ∈ {0, 0.5, 1} × t ∈ {0.25, 0.5, 1, 2}); **none beats raw**, and recall degrades monotonically in
`t`. Mechanism: with a pedestal, every pairwise distance is nearly equal, so the kernel is nearly
constant, so the walk is nearly uniform — diffusion distance ends up dominated by the stationary
distribution, i.e. by degree. **Diffusion amplifies hubness rather than removing it.** The
α-normalisation that was supposed to prevent this corrects for sampling *density*, which is not the
same thing as a rank-1 ambient offset.

**4. The two-stage idea (mine) did not pay** — 48.4% vs 47.9% for abtt alone. The coarse and fine
metrics are too correlated for a pre-filter to add anything.

## 10.7 THE DECISION, BY EPISTEMIC STATUS

**Retrieve top-`k` with `k ≈ 24`, on abtt vectors with `r = 1`.** The three parts of that sentence
have very different support and must not travel as one recommendation:

**① Replace the ε-ball with rank-based retrieval — [MEASURED], strong.**
`ε = 0.10` admits 0.31% of true dependencies; top-k at the same average width scores 46.6% against
the ε-ball's 37.5%. A large effect against real labels, and it survives every caveat in §10.9.
**This is the part to keep if everything else here turns out to be wrong.**

**② Apply abtt — [MEASURED], modest.** ~+4 points over raw.
**[ENGINEERING CHOICE]** `r = 1` rather than 10, per the correction in §10.5.

**③ Set `k` equal to the triangle cap — [ENGINEERING CHOICE], and the weakest leg.**
§5as budgeted 6.1 M triangles and `C(24,3) × 3000 = 6.07 M`, so retrieval width can be made to
*coincide* with the cap. The consequences are real and pleasant:

- ε is deleted; `max_assembly_for_triangles` stops being an independent knob
- no assembly is ever skipped, so `b₁` is uncontaminated **by construction** rather than by a
  counter that warns after the fact
- invariant 1 holds (abtt renormalises ⇒ `||q|| = 1` ⇒ `D₁ = D₂ = 1` ⇒ epistemic term vanishes)
- invariant 2 holds (the unbounded scan becomes bounded)

> **⚠️ CORRECTION (2026-08-04, self-audit). An earlier version of this section called `k = 24`
> "derived, not chosen" and presented the collapse of two constants as the headline. That oversold
> it on three counts:**
> 1. **Its input is unmeasured.** §5as's 6.1 M budget comes from flop and memory *estimates*, and
>    the logbook's own standing reminder says such figures are inferred, not measured.
> 2. **Nothing measured says 24 is a good retrieval width.** Recall rises monotonically with `k`
>    (35.5% at k=10 → 53.4% at k=50). 24 is where a cost constraint bites, not where quality peaks.
> 3. **The coincidence points the way motivated reasoning would.** Two independent constraints
>    landing on the same number is exactly the tidiness to distrust.
>
> **[OPEN HYPOTHESIS]** that tying retrieval width to the topology budget is the right architecture.
> Testing it means varying `k` and watching `b₁`. That has never been run.

## 10.8 DISPOSITION OF R1 / R2 / R3

**R1 — diffusion / heat-map metric: DROP.** Refuted above across 12 configurations. The salvage is
that its *scale* parameter has a successor: `k`, now derived from the budget rather than tuned.

**R2 — Fisher local metric: DEFER, and re-justify.** Untested, and the prior has dropped hard —
every local or spectral competitor measured here moves recall by at most ±4 points. It also has a
bootstrapping flaw: `Σ_q` is estimated from `P(·|q)`, so a positive at rank 48 contributes almost no
weight to the covariance meant to rescue it. **It cannot be justified as a retrieval fix.** It
survives only as a *theory* bet — it is still the one proposal that makes relatedness
context-dependent, which §4.2 argues MOS's cover requires — and it must then be judged by what it
does to Tier 0's cover, not by recall.

**R3 — max-entropy null: PROMOTE. It is now a prerequisite, not an option.** Adopting top-`k` makes
every row of the co-activation matrix have **exactly** `k` ones. `cover.py:479` generates its null
via `_simulate_mixture` — a Bernoulli mixture, which **provably cannot** produce constant row sums.
So the chosen fix breaks the existing null outright. The max-entropy ensemble with fixed margins is
the standard object that handles this, and it simultaneously fixes the deeper hazard of §4.3 (the
null does not know the data are metric balls). **The retrieval decision forces R3.**

## 10.9 WHAT IS STILL NOT KNOWN

- **★ THE EFFECTIVE SAMPLE SIZE IS ~71, NOT 2266.** Every label comes from one of **71 papers**, and
  blocks inside a paper share a topic, an author, and overlapping neighbourhoods — they are not
  independent. Treating 2266 correlated labels as 2266 observations makes every interval in this
  file **too narrow**, and it is what let §10.5 read an optimum off a flat sweep. Any future
  significance claim must cluster by paper.
- **★ IT IS A CONSTRUCT GAP, NOT ONLY A SAMPLING GAP.** "Find the lemma this proof cites, inside one
  paper" and "find a related abstract, across a corpus" are **different tasks**. Remeasuring on the
  1115-abstract corpus does **not** close it, because that corpus has no labels at all — which is
  precisely why the `\ref` labels were built, and precisely why they do not transfer cleanly.
- **These numbers are for blocks-within-papers, not for the 1115-abstract corpus.** The qualitative
  findings transfer (pedestal, threshold failure, small transform gains, rank ≫ threshold); the
  recall figures do not.
- **100% of ref-edges are within-paper.** So the corpus-wide task is "find the cited block among
  2467, where ~80 same-paper blocks are the real competitors." That is a different shape of task
  from MOS's "find a related abstract."
- **`bge-small` is adequate but mediocre**, now quantified: `z = 1.92`, ~47% of true dependencies
  inside a 24-wide assembly. A better embedder remains the largest single lever nobody has pulled.
- **R2 is untested**, and the argument above is a prior, not a measurement.

## 10.10 NEXT, DEPENDENCY-ORDERED

1. **Implement top-`k` retrieval in `KnowledgeBase::get_relevant_concepts`** (`k = 24`, a bounded
   heap over the scan instead of a threshold). Deletes `relevance_threshold` and
   `max_assembly_for_triangles` as independent knobs.
2. **Add `abtt-10` to `embeddings.py`** as a corpus-level post-process, fitted once at ingest and
   stored with the corpus so queries and concepts share the transform.
3. **R3 — replace `_simulate_mixture`** with a fixed-margin max-entropy ensemble. Blocking for any
   Tier-0 verdict.
4. **Re-run this measurement on the 1115-abstract corpus** once it is embedded locally, to confirm
   the numbers transfer.
5. Then: ingest → accumulate → `run_tier0.py`.
