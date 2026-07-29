# MOS — Resource Budget and Test Plan

**Date:** 2026-07-27
**Target machine:** AMD Ryzen 3 5300U (4c/8t), 5.9 GB RAM, no dedicated GPU.
**LLM budget:** Groq free tier — 30 RPM, 6K TPM, ~1000 requests/day.
**Companion docs:** `MEMORY_MODEL_TWO_COMPLEX.md`, `AUDIT_SCRUTINY_AND_BOOK.md`, logbook §5r.

Numbers, not adjectives. Where I have not measured, I say so.

---

# PART I — SPACE BUDGET

## I.1 Per-object storage (d = 384, fp32)

| object | formula | bytes | note |
|---|---|---|---|
| stalk mean vector | d x 4 | **1.5 KB** | current |
| rank-k factor U (k=8) | d x k x 4 | **12 KB** | covariance structure |
| **restriction map, FULL** | d x d x 4 | **576 KB** | ← the killer |
| restriction map, Householder m=4 | m x d x 4 | **6 KB** | 96x smaller |
| restriction map, low-rank Cayley r=4 | 2 x d x r x 4 | 12 KB | alternative |
| simplex record (ids + weight + ts) | ~64 | 64 B | negligible |

## I.2 The finding that forces a design change

Two maps per edge (one per endpoint). At **full d x d matrices**:

```
  2,000 edges  x  2 maps  x  576 KB   =   2.3 GB
```

against 5.9 GB total system RAM. **Full restriction matrices are dead on arrival.**

### Recommended representation: products of Householder reflections

```
  R  =  H_1 H_2 ... H_m ,      H_i  =  I - 2 v_i v_i^T ,   ||v_i|| = 1
```

| property | value |
|---|---|
| storage | m x d x 4 bytes = **6 KB** at m=4 |
| apply R to a vector | O(m d) = 1,536 flops at m=4 |
| **exactly orthogonal** | by construction — no retraction, no drift |
| **||R|| = 1** | so audit finding F2's hypothesis holds **for free** |
| Q(t) = ||R - I||_F^2 | closed form in the v_i; no matrix ever materialised |
| expressiveness | m reflections span an m-dim rotation subgroup; m<<d is a real restriction |

**This is not a compromise, it is the correct choice**: it is the only representation on the
table that makes the Anderson-Morley bound valid by construction rather than by warning.

**Alternative if m Householders prove too rigid:** Cayley transform R = (I-S)(I+S)^-1 with
S skew-symmetric of rank 2r. Orthogonal by construction; Woodbury makes the inverse O(d r^2).
Storage 12 KB at r=4. Strictly more expressive, ~2x the cost. Escalate only if measured need.

## I.3 Projected store size

Assume a one-year solo research workload:

| quantity | conservative | aggressive |
|---|---|---|
| concepts in 𝕂 | 10^4 | 10^5 |
| edges in 𝕂 | 5 x 10^4 | 5 x 10^5 |
| 2-simplices | 10^4 | 10^5 |
| **stalk means** | 15 MB | 150 MB |
| **rank-k factors** | 120 MB | 1.2 GB |
| **Householder maps** | 600 MB | 6 GB |
| **total 𝕂** | ~735 MB | ~7.3 GB |

**Consequence, and it is the architecture justifying itself:** at the aggressive figure 𝕂 does
not fit in RAM. It does not have to. **𝕂 lives on disk (SQLite); only W is resident.** The
two-complex split, designed for cognitive reasons, is also exactly the memory-budget solution.
Note this in the paper — a design forced twice from independent directions is a good sign.

**W budget:** hard cap. At 100 cells / 300 edges with rank-k stalks and Householder maps:

```
  300 edges x 2 x 6 KB  +  100 x (1.5 + 12) KB   =   3.6 MB + 1.35 MB  ~  5 MB
```

Trivially resident. **Set the cap at |C_W| <= 500 cells (~25 MB) and enforce it in the
instantiation loop by stopping PPR expansion, not by evicting afterwards.**

---

# PART II — TIME BUDGET

## II.1 Per-tick (working complex, |V|=7, |E|=21, d=384)

| operation | cost | wall time (est.) |
|---|---|---|
| omega, identity maps | O(|E| d) = 8K flops | microseconds |
| omega, Householder m=4 | O(|E| m d) = 260K flops | microseconds |
| B_pi (weighted Anderson-Morley) | O(|E|) | negligible |
| lambda_2, lambda_max of 7x7 | O(343) | microseconds |
| **alpha, rho-tilde (E1)** | one centring, O(|V| d) | **negligible — do it now** |
| pi_v fusion, isotropic fast path | O(n d), n<10 | microseconds |
| Karcher mean on sphere (if adopted) | ~5 iterations x O(|V| d) | microseconds |

**Nothing on the per-tick path is a problem.** The engine is not compute-bound and will not be.

## II.2 The one real compute trap: the Hodge split

```
  delta^0 : C^0 -> C^1 ,   dimensions  (|E| d)  x  (|V| d)
```

- **With identity restrictions:** delta^0 = delta_K (x) I_d factors as a Kronecker product.
  The pseudo-inverse factors too: (delta_K)^+ (x) I_d. So all real work is on a **21 x 7 scalar
  matrix**. Free.
- **With genuine restriction maps: it does NOT factor.** Direct pinv is on an
  8064 x 2688 matrix, roughly **10^11 flops**. Minutes. Unusable per-tick.

**Fix — never form the pseudo-inverse. Use iterative least squares.** LSQR or CG on the normal
equations needs only matrix-vector products, each O(|E| m d):

```
  ~50 iterations x 260K flops  =  1.3 x 10^7 flops   ->   milliseconds
```

**Write this into the spec.** It is the difference between the Hodge split being a per-conflict
instrument and being unusable.

## II.3 Scaling: instantiation must not touch |𝕂|

The whole scalability argument rests on one property:

> **Approximate PPR with a sweep cut (Andersen-Chung-Lang 2006) runs in time O(1/(alpha eps)),
> independent of |𝕂|.**

So retrieval cost is a function of the *cache size you asked for*, not the store size. A store
of 10^5 or 10^7 concepts costs the same to query. This is the claim to state and to measure
(Test B3 below).

Contrast: embedding k-NN is O(|𝕂|) brute force, or needs an HNSW index (which is itself
~1.5 KB/vector of overhead and must be rebuilt as 𝕂 grows).

---

# PART III — LLM BUDGET (the binding constraint)

Groq free tier: **~1000 requests/day, 6K TPM, 30 RPM.** This, not RAM or flops, is the wall.

## III.1 The quadratic-cost finding

Pairwise judgements over a coalition of n organs require n(n-1)/2 calls.

| n | calls per event | events/day at 1000 req |
|---|---|---|
| 3 | 3 | 333 |
| 5 | 10 | 100 |
| **7** | **21** | **47** |

**47 ticks per day is not a working system.** Mitigation is mandatory, not optional:

1. **Batch all pairs into ONE structured call.** One prompt, n(n-1)/2 judgements returned as
   structured output. 21 calls -> 1 call. **Do this from the start.**
2. **Judge only edges in W**, which is small by construction.
3. **Judge on conflict, not per tick** — gate on the homeostat's integrated deviation.

With all three: ~1 call per conflict event, ~50 events/day = 50 calls/day. Comfortable.

## III.2 Per-experiment LLM cost

| experiment | calls | days at free tier |
|---|---|---|
| E5 pilot (3 organs, 1 triangle) | ~3-10 | < 1 hour |
| E2 Lambda(t), 50-task workload x 10 timepoints | ~500-2000 | 1-2 days |
| B1 error-catching, 200 items x 3 arms | ~1800 | 2 days |
| B2 multi-hop retrieval, 300 questions x 3 arms | ~2700 | 3 days |
| **main test (T1), 100 problems x 3 arms x 3 seeds** | **~5000-9000** | **6-9 days** |

**Budget the main test as a week of wall-clock, not an afternoon.** Plan it around the daily cap.

---

# PART IV — TEST AND BENCHMARK PLAN

Ordered by dependency. Every test states how it FAILS. A test with no failure mode is a demo.

## Tier 0 — Instrumentation (run now, no new machinery, all free)

| id | test | measures | fails if |
|---|---|---|---|
| **E1** | log alpha, rho-tilde, window [lambda_2/B, lambda_max/B] every tick | which factor compresses rho | alpha ~ 0.5 -> the "encoder anisotropy" explanation (audit F12) is FALSE and must be removed from the paper |
| **E4** | split W_2 into d_semantic / d_epistemic; log both | what drives merges | d_epistemic dominates -> merges are driven by the D-floor, not meaning |
| **Q** | log Q(t) = mean ||R - I||_F^2 over 𝕂 | is the wiring learning? | Q stays 0 -> the sheaf is still constant, nothing structural is being learned |
| **E7** | record assembly/extension data at composition time | (enables later analysis) | nothing — **do it now, unrecoverable later** |
| **E3** | compute the independence relation I on the real operator set; clique polynomial | is the trace-monoid hypothesis true? | I is empty -> all of the book's Part II (Koszul, capacity, HH) is counting DAGs. **One afternoon.** |

## Tier 1 — Mechanism validation (each gates a build decision)

| id | test | cost | fails if |
|---|---|---|---|
| **E5** | **THE GATE.** 3 organs, 1 filled triangle, batched pairwise judgements. Assemble eta, Hodge split. | ~10 calls | eta is always pure gradient -> **no curl, no harmonic, no growth address.** The entire cohomological growth story needs rethinking. |
| **E8** | Phi_inf = ||eta_H||^2 + ||eta_C||^2 predicts the actual post-flow residual | free | prediction and measurement disagree -> the stopping rule is invalid |
| **E9** | PPR instantiation vs embedding k-NN: overlap, cut weight, and downstream rho | free | PPR's W is no better AND slices more coalitions -> keep k-NN |
| **E10** | Householder maps: does the PC learner still converge? does Q(t) rise? | free | m=4 too rigid to fit real relations -> escalate to Cayley r=4 |
| **E11** | Forman-Ricci curvature distribution over 𝕂's edges | free | curvature is uniform -> no community structure, the flow has nothing to act on |
| **E12** | Karcher-mean / tangent-space flow vs flat flow | free | identical results -> sphere geometry is not worth the cost; **keep flat and say so** |
| **E13** | consolidation replay: after N sessions, re-run old W's against updated 𝕂 | moderate | old tasks degrade -> gamma_0 too large; catastrophic interference is happening |
| **E14** | **delta sweep for the concept-identity scale.** Hand-label ~50 concept pairs should-merge / shouldn't (~1 hour). Sweep delta over WFR (or lambda over a blended distance). Plot merge precision/recall. **Report the SENSITIVITY CURVE, never a single fitted value.** | 1 hour of labelling, then free | the curve is flat -> the metric choice does not affect merge decisions at all, and the whole geometry argument is moot. **This is a real possible outcome and it would be worth knowing.** |
| **E15** | ⚠️ **prerequisite for E14:** does WFR / Hellinger-Kantorovich admit a CLOSED FORM between Gaussians, as Bures does? | literature check | no closed form -> WFR needs a geodesic/optimisation solve per distance evaluation, is unusable on the per-tick path, and stays theory only |

## Tier 2 — Comparative benchmarks

> **METHODOLOGICAL RULE, non-negotiable: HOLD THE MODEL FIXED.**
>
> The claim is *architectural*. Benchmarking "MOS vs GPT-5" tests the wrong thing and will
> lose — your own docs say per-inference quality is bounded by the LLM. The only comparison
> that isolates the claim is:
>
> ```
>   MOS(Llama-70B)   vs   plain-RAG(Llama-70B)   vs   bare Llama-70B
> ```
>
> Same model, three organisers. Anything else is a confound.

| id | benchmark | dataset | measures | fails if |
|---|---|---|---|---|
| **B1** | error-catching | 200 items, half seeded with a plausible falsehood | does cross-organ disagreement catch what one call misses? | MOS's catch rate <= self-consistency with the same call budget |
| **B2** | multi-hop retrieval | HotpotQA / MuSiQue / 2WikiMultihop (⚠️ verify availability) | structural retrieval vs dense | MOS <= plain RAG at equal LLM budget |
| **B3** | **retrieval scaling** | own store at |𝕂| = 10^3, 10^4, 10^5 | is instantiation independent of store size? | latency grows with |𝕂| -> the PPR claim is false |
| **B4** | formal math | **miniF2F / ProofNet** (⚠️ verify) | end-to-end with a REAL VerifyOp (Lean), not a simulated one | no gain over RAG at equal budget |

**B4 is the important one.** With Lean, VerifyOp is genuine rather than an LLM grading itself,
which removes the single largest credibility objection to the whole architecture.

## Tier 3 — The main test

**T1 — The slope test.**

```
  Fix a held-out workload of ~100 research tasks in Charbel's own domain.
  Three arms, same LLM:  bare | plain-RAG | MOS.
  Run the workload at t = 0, then again after N sessions of unrelated accumulation.
  Three seeds per arm.

  PRIMARY:   the GAP between MOS and plain-RAG as a function of accumulated experience.
  SECONDARY: Lambda(t) and Q(t) over the same period (LLM-independent).
```

**Why this and not raw accuracy.** The bet was always the slope, never the intercept. Day one
MOS is *worse*. The claim is that it improves with accumulation while the baselines do not,
because the baselines have nothing that accumulates. **The measurement must therefore be a
derivative, not a level** — and a derivative is a much easier claim to defend than "we beat RAG."

**T1 fails if:** the gap is flat or shrinking. Publish that. A well-instrumented negative result
on an architectural bet is a genuine contribution, and it is the outcome the whole
instrumentation programme exists to make visible.

## What is NOT a valid test

- MOS vs a frontier model on single-shot reasoning. **Wrong claim, guaranteed loss.**
- Any comparison where the arms get different LLM call budgets.
- rho improvement as an outcome measure. Coherence is not correctness; a fluent false
  reconciliation improves rho. **VerifyOp or an external label, always.**
- kappa (capacity). Trivially gameable by adding independent useless operators.

---

# PART V — CRITICAL PATH

```
NOW (free, parallel, no new machinery)
  E1, E4, E7, Q, E3
       |
       v
E5 -- THE GATE (~10 LLM calls) ---- if pure gradient: STOP, rethink the growth story
       |
       v
BUILD  Householder maps (I.2) -> LSQR Hodge (II.2) -> PPR instantiation (E9)
       |
       v
E8, E10, E11, E12, E13   (mechanism validation, all free)
       |
       v
B1, B2, B3   (comparative, ~1 week of LLM budget)
       |
       v
B4 (Lean / miniF2F)  --- requires the Lean moderator; largest single build
       |
       v
T1 -- THE MAIN TEST (~1 week wall-clock at free-tier caps)
```

**Everything above E5 is free and can start today. Nothing above E5 depends on the stalk-geometry
decision.** Do not serialise the cheap work behind the interesting arguments.

---

# PART VI — WHAT THIS BUDGET DOES NOT COVER

- **Wall-clock engineering time.** Not estimated; I have no basis for estimating your throughput.
- **The Lean moderator (B4).** Largest single build item, deliberately last.
- **Dataset availability.** HotpotQA / MuSiQue / miniF2F / ProofNet are marked ⚠️ — from model
  knowledge, not verified. Check before planning around them.
- **Groq tier changes.** The entire LLM budget assumes the current free tier. If it changes,
  III.1's batching requirement becomes even more binding.
- **Numbers marked (est.).** Flop counts are arithmetic and reliable; wall times are inferred
  from them and have not been measured on your machine. Measure before trusting.
