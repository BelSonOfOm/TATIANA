# THE COVER QUESTION — THE ISSUE, AND THREE ATTEMPTS THAT FAILED

*Written 2026-08-04. A standalone problem statement: what we are trying to measure, why three
attempts to measure it did not work, and what is actually known. Readable cold.*

> **STATUS: THE QUESTION IS STILL OPEN.** Nothing below is evidence for or against MOS's cover
> hypothesis. All three attempts failed for reasons of *experimental design*, not because the data
> answered. Read §8 before drawing any conclusion from the numbers.

## 0. EPISTEMIC STATUS TAGS

Every load-bearing claim in this file is tagged. The failure mode in this project has not been bad
statistics — it has been **good numbers attached to conclusions they do not support** — so a reader
should never have to guess which is which.

| Tag | Meaning | Weight |
|---|---|---|
| **[MEASURED]** | Came out of a run, on real data. | Full, subject to its sample. |
| **[DERIVED]** | Arithmetic on a **[MEASURED]** number. | Sound, inherits the measurement's limits. |
| **[INFERRED]** | Reconstructed indirectly, fitted, or a very small sample. | Weak. Remeasure before building. |
| **[ENGINEERING CHOICE]** | Chosen for cost, simplicity or convenience. | **None as evidence.** A different choice would not be wrong. |
| **[OPEN HYPOTHESIS]** | Intended to be tested; not yet tested. | None. It is a plan. |
| **[SPECULATION]** | A proposed mechanism with no test behind it. | None. Never quote as a finding. |

**⚠️ A standing caution on sample size.** Label counts are not counts of independent observations.
The `\ref` labels come from **71 papers**; blocks inside one paper share a topic, an author, and
overlapping neighbourhoods. So `n = 2266` labels is closer to `n ≈ 71` independent units, and any
interval computed from label counts alone is **too narrow**. Where this changes a conclusion below,
it is stated inline.

---

## 1. THE QUESTION, IN ONE SENTENCE

**Does a concept belong to more than one area of thought?**

- **Yes** → the structure is a **cover**: areas overlap, and a single concept can sit in two of them.
- **No** → the structure is a **partition**: every concept sits in exactly one area.

That is the whole question. Everything below is about how hard it turned out to be to ask.

---

## 2. WHY IT MATTERS

MOS is built on the "yes" answer. If it is "no", a large amount of the architecture has nothing to
act on:

| depends on overlap | what it needs |
|---|---|
| the **sheaf** structure | a concept whose meaning changes with the patch you restrict to |
| **restriction maps** (Householder, §5 Phase-2 item 1) | two patches to map between |
| **b₁ / harmonic mass / the growth address** | cycles that only exist because patches overlap |
| **γ(ν)**, what crystallises into 𝕂 | contexts to consolidate across |

A partition is not fatal — but it would mean the cohomological machinery has no work to do on this
data, and that has to be known rather than assumed.

---

## 3. THE TRAP, STATED UP FRONT

Every attempt below failed the same way at a high level:

> **The measurement described our experimental setup rather than the data.**

This is easy to do and hard to notice, because a broken measurement still returns a number, and the
number looks exactly like a result. The three attempts failed through three *different* mechanisms,
which is why each one had to be diagnosed separately.

---

## 4. ATTEMPT 1 — TIER 0 ON TICKS

### The design
A **tick** is one step of thinking. On each tick the system retrieves concepts from memory; those
concepts are *co-active*. Over 3000 ticks this builds a matrix of what-fired-with-what, and Tier 0
asks of that matrix:

- **mixture model (partition):** exactly one hidden cause fires per tick
- **noisy-OR model (cover):** several causes can fire at once, and a concept can belong to several

Ticks were generated as: *take one query sentence, retrieve the 24 nearest concepts.*

### What ran
3000 ticks × 1074 concepts, top-24 retrieval, K = 6, B = 99 bootstrap draws.

### The result
```
observed margin                 −1.9210 nats/tick
null median (margin-matched)    −1.9275
excess over null                +0.0065
p                                0.4500      → NO EVIDENCE FOR COVER
```

### Why it failed
**A top-k ball around one query point has one centre.** Every concept in it is there because it is
near that single centre. So the tick is a **single-cause event by construction**, and Tier 0's
question — "one cause or several?" — was answered by the generator before any data was seen.

Trace it to the concept level: concept `c` appears in the assemblies of queries near `c`; those
queries are all in one region; so `c` is assigned to one region. **Single-centre retrieval produces
a partition mechanically.**

**The tell:** this setup would have returned "partition" on a corpus engineered to be 100%
overlapping. A measurement whose answer cannot change is not a measurement.

**The name:** this is the **Modifiable Areal Unit Problem** — the measured pattern depends on the
size and shape of the unit you aggregate over. Our "areal unit" is the tick. The literature's
standard remedy is to *sweep* the unit size and report sensitivity, never to pick one.

---

## 5. ATTEMPT 2 — PER-CONCEPT BIMODALITY, WITH arXiv CATEGORY LABELS

### The reframe
Attempt 1 asked a **tick-side** question ("did several causes fire together?"), which the grain
breaks. But a cover is a family of overlapping patches, and *overlapping* means **an element lies in
two patches** — a statement about elements:

```
tick-side    : "did several causes fire together?"          ← broken by the grain
concept-side : "does this concept belong to two contexts?"  ← the definition itself
```

For concept `c`, collect every tick it fired in and ask whether those neighbourhoods **split into
two groups**. The multi-cause structure then lives *across* ticks rather than *within* one — so the
broken single-centre ticks are adequate for this question.

### The score
Per concept, 1-means vs 2-means on its tick centres:
```
bimodality(c) = 1 − SSE₂ / SSE₁          higher = more split
separation(c) = ‖m₁ − m₂‖ / rms spread   effect size of that split
```

### The label
arXiv **cross-listing**: a paper filed under two of our six categories is "one concept claimed by
two topics." 115 positives out of 1070 scored concepts (10.7%).

### The result
```
                    bimodality AUC   separation AUC
real, pca=0             0.5031           0.4853
real, pca=2             0.5144           0.5141
real, pca=5             0.5356           0.5495
geometric null, pca=2   0.5229           0.5288    ← pure noise
```
**[MEASURED]** Everything is inside the noise floor.

> **⚠️ CORRECTION (self-audit). The noise floor was first quoted as ±0.029, computed assuming the
> 1070 scored concepts are independent. They are not** — they come from 1074 abstracts across six
> topics with heavy neighbourhood overlap. Clustering inflates the standard error by roughly
> `√(1 + (m−1)ρ)`; at a modest intra-topic correlation this puts the real floor nearer **±0.04**.
>
> **The consequence is that the negatives are weaker than reported, not stronger.** The most
> suggestive figure — AUC 0.5495 at pca=5 — is about **1.2 standard errors**, not the 1.75 implied
> by the narrow floor. **[MEASURED]** the score does not discriminate; **[INFERRED]** how much power
> it had to do so, and the honest answer is: less than claimed.

### Why it failed — two independent reasons

**(a) The instrument was blind.** A positive control planted two clusters at known separations:
```
condition                 pca=0    pca=2
one blob (null)          0.0199   0.3568
two clusters, gap 2.0    0.0209   0.3901
two clusters, gap 4.0    0.0539   0.6312
```
Without PCA, planted clusters scored **0.0209 against a null of 0.0199** — the first run measured
nothing at all. Sixty-seven points in 384 dimensions have concentrated distances, so every 2-means
split scores alike. Per-concept PCA restores power, but only above roughly **40% of the
neighbourhood radius**.

**(b) The label is administrative, not semantic.** arXiv cross-listing is a *filing decision*. A
paper tagged both math.DG and math.AP may sit entirely inside one semantic region.

> **Without the positive control, "AUC 0.50, no cover structure" would have been reported as a
> finding** — a second setup artifact, one step after diagnosing the first.

### A related correction to the corpus premise
§5ap justified this corpus with *"74% cross-listed — real overlap structure."* Reproduced: 75.8% are
cross-listed to **any** category, but only **10.7%** to a second category *inside the corpus*
(the rest go to cs.LG, math.AP, math.AG, math.CO, stat.ME, hep-th — categories not present). The
overlap Tier 0 can actually see is seven times smaller than recorded.

---

## 6. ATTEMPT 3 — SAME SCORE, CITATION-DERIVED LABELS

### The reframe
If cross-listing is too administrative, use a label an author actually asserted. A paper's own
`\ref` graph is exactly that — "by Lemma 3.2" is a claim of dependency. Those labels had already
worked decisively for the retrieval problem (2266 positives).

### The label
```
citer_span(v) = (max_pos(citers) − min_pos(citers)) / doclen
```
"A lemma invoked in §2 and again in §9 serves two parts of the argument."

Computed from **character offsets in the LaTeX source** — deliberately never touching the
embeddings, so it cannot be circular with the score it validates. 538 blocks with ≥2 citers, 212
labelled bridging.

### The result
```
                  bimodality AUC   separation AUC   spearman vs span
real                  0.4932           0.5210        −0.005 / +0.045
geometric null        0.5171           0.5181        +0.057 / +0.023
```
**[MEASURED] Real sits at or below the geometric null. Zero signal.**

**⚠️ And here the clustering correction bites hardest.** The 538 labelled blocks come from **71
papers** — roughly 7.6 per paper, mutually correlated. The effective sample is closer to 71 than
538, so the AUC floor is wider than a naive calculation gives, and **nothing in this table is
distinguishable from chance under any reasonable correction.** That strengthens "no signal found"
and weakens any claim about *how thoroughly* we looked.

### A confound caught mid-run
The raw span was predicted by **in-degree alone at AUC 0.748** — the range of *n* points widens with
*n* whether or not anything bridges. Dividing by the expected range `(n−1)/(n+1)` cut it to 0.636.
The score's AUC did not move, so the conclusion held, but as first written the label was measuring
popularity.

### Why it failed — and the number was already on file
**The label and the score measure different relations.**

- `citer_span` is **logical**: "I need that result here."
- bimodality is **geometric**: "these texts read alike."

A lemma can be invoked from §9 without resembling §9's prose. And `THE_RETRIEVAL_PROBLEM.md` §10
had already measured the disagreement: **recall@30 = 44–48%** — more than half of cited blocks never
appear in their citer's top-30 most-similar list. Validating a similarity statistic with citation
labels was therefore expected to fail at roughly the observed rate.

**That number was measured days earlier and not connected before the run.**

### One thing that is not nothing
Real neighbourhoods score bimodality **0.445** against the geometric null's **0.397**, where the
positive control puts structure-free at 0.357 and a clean 4σ split at 0.631. So real data does carry
about **a quarter of a clean split's worth** of neighbourhood structure — but it is **not
concentrated in the blocks either label calls bridging.** It reads as generic topic clustering, not
specific multi-context concepts.

---

## 7. WHAT WAS ACTUALLY ESTABLISHED

Three failures, but the session was not empty.

### ★ The old null model produces a false positive — measured, not argued
Identical data, identical model fits, identical observed statistic. Only the null changed:

| null | median | excess | p | verdict |
|---|---|---|---|---|
| **legacy** (free margins) | −2.1538 | **+0.2329** | **0.0200** | **COVER** |
| **margin-matched** (fixed row sums) | −1.9275 | +0.0065 | 0.4500 | no evidence |

**Mechanism.** Real rows have exactly 24 ones (sd 0.00); the legacy null emits Binomial row sums
(sd 3.08). On null data the mixture can spend components capturing row-size variation — an advantage
it does not have on the real fixed-width data — so the null distribution shifts down and the
observed value looks anomalously high. Textbook **Type I error inflation**, exactly as the ecology
null-model literature reports for free-margin models.

> **Had Tier 0 run as originally planned, it would have returned `COVER at K=6, p=0.0200` and we
> would have believed it.**

### The retrieval rule, fixed and validated
**[MEASURED]** Against 2266 ground-truth `\ref` labels: the engine's `ε = 0.10` admitted **0.31%**
of true dependencies; top-k at the same average width scores **46.6%** versus the ε-ball's 37.5%.
This is a large effect and the most durable result of the whole session.

**[ENGINEERING CHOICE]** `k = 24` and the abtt rank. An earlier version called `k = 24` "derived" —
it coincides with §5as's triangle budget (`C(24,3) × 3000 = 6.07M`), but that budget is itself an
unmeasured flop/memory estimate, recall rises monotonically in `k`, and no measurement says 24 is a
good width. **[OPEN HYPOTHESIS]** that tying retrieval width to the topology budget is right; it
needs `k` varied against `b₁`, which has never been run. See `THE_RETRIEVAL_PROBLEM.md` §10.7.

### Infrastructure
- `build_corpus.py` — corpus builds locally; the Colab dependency is gone
- `extract_refs.py` — free semantic labels at scale from arXiv LaTeX source
- `curveball_randomize` — unbiased fixed-margin randomisation, tested
- Prior art located: this problem is solved in ecology, geography, network science, Bayesian
  nonparametrics and TDA (see `PRIOR_ART_AND_THE_REPLAN.md`)

---

## 8. THE PATTERN — THE REAL FINDING

**Three design mismatches in a row, each caught only by a control, never by the headline number:**

1. **single-centre ticks** — one cause by construction; the answer was baked in (MAUP)
2. **blind instrument + administrative label** — planted clusters scored 0.0209 against a 0.0199 null
3. **citation label vs similarity score** — different relations, disagreement already quantified

Every measurement so far has described **our setup**, not the data. That is not bad luck. It is what
happens when an experiment is built before deciding precisely **what observation would distinguish a
cover from a partition**.

> **RULE EARNED TODAY: no measurement is reportable without a positive control.** It caught items 2
> and 3, and in both cases the artifact looked exactly like a result.

---

## 9. WHAT IS STILL UNKNOWN

- **Whether MOS's cover hypothesis is right.** Untested. Not one attempt got far enough to be
  evidence either way.
- **Whether this corpus even has cover structure.** The premise it was chosen on (74% overlap) is
  really 10.7% inside the corpus.
- **Whether real bridging exists below the instrument's ~40% separation floor.** Undetectable with
  the current score.
- **Whether `bge-small` is adequate.** Quantified as mediocre (`z = 1.92`, ~47% recall@30), never
  compared against a stronger embedder.

---

## 10. THE ONE THING TO DO NEXT

**Not another score.**

> Write down, in one sentence, **what observation would distinguish a cover from a partition in
> MOS** — then verify the proposed measurement can actually produce that observation, *before*
> writing any code.

Three attempts have now guessed wrong on this. The failure was never in the statistics; it was in
going from "we should measure overlap" to code without pinning what overlap would *look like* in the
data we have.

Two candidate directions, both **[OPEN HYPOTHESIS]**, neither obviously right:

1. **The engine's real tick** — retrieval driven by an accumulated cognitive state that carries
   history, so a thought reaches into several regions because of what it is doing, not because the
   experimenter unioned two circles. Needs `mos.exe`. Truest to the architecture.
2. **Accumulation as the filtration** — co-activation counts only ever increase, so the complex at
   tick 500 is contained in the complex at tick 3000. That is a genuine filtration *by
   construction*, unlike a threshold sweep, and it asks "does structure emerge?" instead of "is
   structure present at setting X?"

**A warning about the obvious fix:** constructing multi-focus ticks by unioning circles around 2–3
points would *plant* the cover. The union of two balls is two causes by construction — the mirror
image of Attempt 1's mistake.

---

## APPENDIX — FILE MAP

| file | what it does |
|---|---|
| `build_corpus.py` | fetch + embed arXiv abstracts locally |
| `extract_refs.py` | `\label`/`\ref` graph → ground-truth relatedness labels |
| `make_assemblies.py` | top-k on abtt vectors → assembly log; `--null geometric` for the control |
| `measure_reference_recall.py` | retrieval rules ranked against `\ref` positives |
| `measure_multicontext.py` | Attempt 2 — per-concept bimodality, arXiv labels |
| `measure_multicontext_refs.py` | Attempt 3 — same score, citation labels |
| `tier0_parallel.py` | Attempt 1 — Tier 0 with the bootstrap spread across processes |
| `cover.py` | `_simulate_mixture_margin` (R3), `curveball_randomize` |

**Related documents:** `THE_RETRIEVAL_PROBLEM.md` (the retrieval fix and its measurements),
`PRIOR_ART_AND_THE_REPLAN.md` (five literatures and what transfers),
`TATIANA_LOGBOOK.md` §5av–§5ax (chronological record).
