# SPEC P0 — THE RETRIEVAL FIX

*Filed 2026-08-08. The largest single defect in the running system, diagnosed from measurement in
the Tier-0 chapter and located in the C++ engine this session. Logbook §5bb, §7.*

Tags: `[MEASURED]` · `[DERIVED]` · `[ENGINEERING CHOICE]`.

---

## 1. WHY THIS IS P0

**[MEASURED]** The engine's retrieval policy admits **0.31%** of author-asserted true dependencies.
Rank-based retrieval at the same width gets **46.6%**. Every operator downstream of `SearchOp` —
reasoning, verification, consolidation, the co-activation record that `ConceptStore` is built from —
is currently being fed near-noise.

**Nothing else in the system can be evaluated until this is fixed**, because every measurement taken
downstream is a measurement of the wrong input.

---

## 2. WHAT IS THERE NOW — THREE DEFECTS, NOT ONE

### 2.1 The "dynamic" threshold is dead code

`src/operators/primitives.cpp:58`

```cpp
double relevance_threshold = std::max(0.1, 1.0 / static_cast<double>(query_embedding.size()));
```

At `d = 384` this is `max(0.1, 0.0026) = 0.1`. **It returns `0.1` for every query the system will
ever see.** The dimension-dependence is decorative.

### 2.2 Absolute threshold instead of rank

`src/translation/knowledge_base.cpp:196`

```cpp
double w2_sq = calculate_wasserstein_2_sq(thought_mu, thought_D, mu, U, D);
if (w2_sq <= epsilon) { results.push_back(...); }
```

Full table scan, absolute cutoff, **no ranking, no limit**. `[MEASURED]` this is the 0.31% policy.

**Why an absolute cutoff cannot work here.** The embedding pedestal is real and large: `‖μ̄‖² = 0.671`,
and two *unrelated* abstracts score `cos ≈ 0.669`. For unit-norm means,

```
    semantic = ‖μ₁ − μ₂‖² = 2(1 − cos)
```

so `semantic ≤ 0.1` requires `cos ≥ 0.95`. **[DERIVED]** The cutoff sits about six times below where
unrelated pairs already live — it is a **near-duplicate filter**, confirming from first principles
what the Tier-0 chapter measured empirically.

The pedestal is a *thresholding* problem, not a *ranking* one: for a fixed query it is a constant and
cannot reorder anything. That is why abandoning the absolute cutoff is worth ~140× while improving
the metric is worth ~4 points.

### 2.3 It thresholds a quantity that is mostly not about relevance

`include/mos/core/semantic_skill.hpp:120` states the decomposition:

| field | quantity | scaling |
|---|---|---|
| `semantic` | `‖μ₁ − μ₂‖²` | **d-intensive**, ≤ 4 for unit norm |
| `epistemic` | Bures² between the covariances | **d-extensive** |

and its own comment says:

> *"prefer thresholding the two fields independently — see the WassersteinTerms docs for why summing
> a d-intensive and a d-extensive quantity makes the sum uninterpretable."*

`get_relevant_concepts` thresholds exactly that uninterpretable sum. **At `d = 384` the d-extensive
term dominates, so the engine is selecting by epistemic breadth rather than semantic relevance.**

### 2.4 Secondary: an invented variance

`src/operators/primitives.cpp:52`

```cpp
double derived_variance = std::sqrt(norm_sq) + eps;   // = ‖q‖
```

The query's **norm** used as its **variance**, derived from nothing. It feeds only the `epistemic`
term. Ranking on `semantic` makes it inert, so **one fix removes two problems** — the line is deleted
rather than left as a landmine.

---

## 3. THE FIX

Replace the epsilon-ball with a bounded rank query.

```cpp
[[nodiscard]] std::vector<std::shared_ptr<const core::SemanticEmbedding>>
get_top_k_concepts(const Eigen::VectorXd& thought_mu, std::size_t k) const;
```

1. **Rank, do not threshold.**
2. **Rank on cosine — NOT on `semantic = ‖μ_q − μ_i‖²`.** `[CORRECTED 2026-08-08, before the port
   was accepted]` The first version of this spec said to rank on the d-intensive Wasserstein term.
   That is wrong, and only by an assumption that does not hold:

   $$\|\mu_q - \mu_i\|^2 \;=\; \|\mu_q\|^2 \;-\; 2\langle \mu_q, \mu_i\rangle \;+\; \|\mu_i\|^2$$

   For a fixed query `‖μ_q‖²` is constant and drops out of the ranking. **`‖μ_i‖²` does not.**
   Squared distance reproduces a cosine ranking **only if every stored mean is unit-norm**, and
   stored means are not: `π_v` is a **weighted centroid** of unit vectors (Construction 2,
   `module_vertex.py`), whose norm sits below 1 and falls further the more spread the concepts it
   summarises. The `‖μ_i‖²` term would then act as a per-concept penalty **proportional to how broad
   a concept is** — pushing exactly the general concepts down the list, for a reason unrelated to the
   query.

   And decisively: **recall@30 = 46.6% was MEASURED on a cosine ranking**
   (`measure_reference_recall.py`, transform `raw`). Ranking by cosine is provably the same ordering
   that was measured. Ranking by squared distance is a *different* ordering carrying an unmeasured
   bias — which would have made the acceptance criterion in §5 meaningless.

   Zero-norm vectors are dropped rather than scored: a zero vector has no direction, the same
   refusal `embeddings.py` makes rather than padding a short vector.
3. **Bounded max-heap of size `k`**, keeping the `k` smallest. Returned sorted ascending.
4. **Skip the expensive deserialisation for rows that cannot win.** `μ` is needed to score; `U`, `D`
   and the reasoning string are not. Read `μ`, score, and only read the rest if the row would enter
   the heap. Drops the per-row cost from `O(d k² + k³)` to `O(d)` for the large majority of rows.
5. **`get_relevant_concepts` is removed, not deprecated.** A deprecated landmine is how this survived
   in the first place.

---

## 4. `k` — STATED HONESTLY

**`[ENGINEERING CHOICE]`, `k = 24`.** Not derived. But it is now **constrained on both sides**, which
the old `k = 24` was not:

| bound | source |
|---|---|
| **lower** | recall@30 ≈ 44–48% `[MEASURED]`; smaller widths cost real recall |
| **upper** | `ConceptStore::max_assembly_for_triangles_ = 30`. At `k ≤ 30` the triangle cap **never fires**, `skipped_wide_assemblies()` stays 0, and `b₁` is never contaminated by an assembly whose within-assembly cycles went unfilled |

**[DERIVED]** That upper bound is a real consistency requirement between two parts of the system, and
it did not exist before: with an unbounded threshold scan, `|A|` was bounded only by the corpus size,
so `concept_store.hpp:137` had to call its cap **mandatory rather than prudent**. Bounding retrieval
by rank removes the condition that made the cap necessary.

Stage 2's competition dynamics is what eventually deletes `k` entirely (assembly width emerges from
the inhibition/excitation balance). Until then it is a constant, tagged as one.

---

## 5. TESTS

`tests/test_knowledge_base.cpp` currently asserts that an epsilon-ball behaves like an epsilon-ball —
true and useless. Replaced by the new contract:

1. **Cardinality.** Returns exactly `min(k, |store|)`.
2. **Order.** Results are sorted ascending by `‖μ_q − μ_i‖²`.
3. **The regression that matters.** A query that returned **zero** results under the threshold policy
   returns a populated, correctly-ordered set. This is the 0.31% bug, pinned.
4. **Nearest-first.** With a planted near-duplicate in the store, it comes back first.

**Acceptance, beyond unit tests:** re-run `measure_reference_recall.py` against the **engine** path
rather than the Python path. It should land near **46.6%**. If it does not, the port is wrong — and
that is the whole point of having measured the Python path first.

---

## 6. WHAT THIS DOES NOT FIX

- **`bge-small` has never been compared against a stronger embedder** (carried open from §5ba).
- **Retrieval remains a full table scan.** Correct at the current corpus size, and an index is a
  separate concern; the defect here is the *policy*, not the scan.
- **`k` is still a constant.** See §4.
- **This is Track A.** It makes the tool work. It tests nothing about the model of cognition — see
  logbook §7 for why those are separable and why this one comes first anyway.
