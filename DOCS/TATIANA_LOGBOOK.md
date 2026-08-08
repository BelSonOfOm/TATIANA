# TATIANA — Working Logbook

A living, chronological record of what we decide, build, learn, and break. Newest entries at the bottom of each section. This is the "backtrack everything" ledger.

Legend: ✅ done · 🔵 in progress · ⏸️ parked · ❌ dead end · ⚠️ open risk

---

## 0. Orientation — what TATIANA is, what it honestly claims, what it uses

*(Framing conversation, 2026-07-22. Read this first. It states the project plainly and — deliberately — states its limits with equal plainness, because self-honesty is the one property this whole design exists to protect.)*

### 0.1 What it is
TATIANA is a **cognitive architecture layered AROUND a large language model, not a new LLM.** It uses a remote LLM (Groq's Llama) as a black-box reasoning component and orchestrates whole reasoning acts across time. The organising object is a **cognitive state space `M = (C, F, s)`**: `C` a stratified simplicial complex (coarse level = cognitive organs as vertices; fine level = concepts inside each organ's stalk), `F` a sheaf assigning local state to each piece, `s` the current coherent global state. It is a **persistent, self-checking, self-restructuring organiser** for research-grade mathematics, built to run on ~zero budget.

### 0.2 What it claims to be — and what it does NOT
- **CLAIMS (defensible, now with evidence):** persistent memory across sessions; grounding answers in the user's own curated library; **detecting its own internal contradictions** and localising them; verifying results against an external oracle; **growing its structure with use**. Its superiority over a plain LLM is **architectural, not intellectual** — a better-remembering, self-checking, self-restructuring organiser wrapped around a weaker brain. The bet is on the **slope** (it compounds over time), not the **intercept** (day 1 it is *worse* than just opening Claude).
- **DOES NOT CLAIM:** that the raw reasoner gets smarter. No simplex proves a theorem; the sheaf Laplacian integrates no differential form. Any single inference's "IQ" is bounded by the LLM. It will NOT beat a frontier model on genuinely novel reasoning. Saying otherwise would be the exact self-delusion this architecture is built to prevent.

### 0.3 What it uses (the stack)
- **Reasoning brain:** Groq API, tiered — 8B (`llama-3.1-8b-instant`) for cheap high-frequency triage/extraction, 70B (`llama-3.3-70b-versatile`, also free) for real reasoning. Free tier: 30 RPM / 6k TPM / ~1k req-day.
- **Geometry:** local CPU embeddings (`BAAI/bge-small-en-v1.5`, 384-d, fastembed/ONNX) — free, no quota, because they run thousands of times.
- **Engine:** C++ (Eigen, SQLite, FlatBuffers), MSVC build. Python frontend (3.11) does the π morphism + orchestration; the two talk over a length-prefixed CRC32 IPC frame.
- **Verification:** sandboxed sympy oracle (`verify/check.py`).

### 0.4 On the HARNESS (what runs the math on the real machine)
A **harness** is the infrastructure that *runs* a program rather than the program's logic: process lifecycle, I/O plumbing, resource allocation, scheduling, the boundary between code and hardware. (Same word as a "test harness"; same concept as what hosts Claude Code itself.) TATIANA's harness is everything deciding *how the mathematics touches Charbel's actual hardware*, and it is the layer we have been MOST disciplined about — we started from the real machine's limits (5.9 GB RAM, no dedicated GPU) and let them shape the architecture, rather than assuming infinite compute and apologising later. Concrete harness decisions in the code:
- **Process separation** — the C++ engine runs as a subprocess (`--ipc-server`), isolating a math-engine crash from the Python orchestration layer.
- **Thread harnessing** — `ThreadPool` auto-detects concurrency; the Operad scheduler foliates the DAG into maximal commuting slices sized to the real machine.
- **The split-brain IS the central harness decision** — heavy inference → remote (Groq); cheap high-frequency geometry → local CPU. Driven by what THIS machine can and can't host, not by preference.
- **Storage harnessing** — single-file SQLite, right for a single-machine low-resource harness (and the first thing that will need to change to scale out).

### 0.5 Why simplices / sheaves / algebraic topology (what actually earns its keep)
Most of the *original* inherited formalism was decorative and was CUT (infinite-dim Banach spaces, Pachner moves, cohomology on undefined restriction maps — borrowed guarantees from theorems whose preconditions weren't met). What survived earns its keep:
- **Simplices** = honest joint (n-ary) relations. A theorem bound to 3 prerequisites is ONE 3-ary fact, not three pairwise ones. Already in code (`insert_n_ary_relation`).
- **The sheaf** turns "do my parts agree?" from a vibe into a derivable object. It hands you, cheaply: a **provably bounded** discord `ρ∈[0,1]` (Anderson–Morley), **localisation** (`worst_edge` — WHICH organs disagree), a **genuine spectral decomposition** (L is really symmetric PSD, so the "Cognitive FFT" is earned not borrowed), and a **precise vocabulary for what's missing** (`b₁` = structural hole vs `H¹` = data contradiction — different diagnoses).
- **One-line honest answer:** we don't use topology because it makes the system smarter; we use it because it is the **cheapest rigorous language for "do the parts of my system agree, and if not, where"** — a local-to-global consistency check plus a bounded, localisable, spectrally-decomposable measure of disagreement, for the price of a quadratic form and a union-find.

### 0.6 Does this give intelligence augmentation that MoE machines don't?
**Category correction:** MoE lives INSIDE one LLM (opaque expert sub-nets + a learned gate, trained end-to-end, combined by weighted sum — a parameter-scaling trick, not cognition). TATIANA lives AROUND an LLM. Different layers; the LLM TATIANA calls may itself be MoE.
- **Three things the complex does that MoE structurally CANNOT:** (1) explicit, persistent **higher-order coalitions** (a 2-simplex as a unit, not just a set of co-firing experts); (2) **cross-component contradiction detection** (MoE only weighted-sums its experts; it never asks if they *disagree* — TATIANA's ω/H⁰ measures and localises exactly that); (3) **inference-time structural growth** (MoE is frozen after training; TATIANA's complex binds/decays/consolidates with use).
- **Honest asymmetry (where MoE is BETTER):** MoE's router is *trained* against task loss → strong per-decision. TATIANA's binding is Hebbian + conflict-driven → interpretable and retrain-free, but weaker per single decision.
- **The credible augmentation mechanism (whole > parts):** NOT raw IQ, but **measured cross-organ error-correction** — a lone 8B call hallucinates confidently and you never know; but Search-retrieves + Reason-derives + Verify-checks, with the sheaf *flagging disagreement*, catches what any single call misses (same reason ensembles/debate/self-consistency work — TATIANA's version is just principled and localised). Plus **accumulation** over time. Both are real; neither needs a smart reasoner; both are absent from MoE.
- **The topology's DEEPEST gift:** it makes the claim of intelligence **falsifiable.** You could get memory + contradiction-checking + verification with plain data structures; what the sheaf uniquely adds is *unification* (memory, consistency, growth = operations on ONE object), *provable cheap guarantees*, and — above all — the ability to **measure whether augmentation is actually happening instead of fooling yourself.** (When the lemon-cake vector spiked ρ to 0.14 and named the guilty edge, the system refused to let us pretend. That is the point.)

### 0.7 Does it model the brain?
At a doable level it models three real principles of neural **organisation** — NOT neural **computation**: **Hebbian plasticity** (`co_activate` → bind), **functional coalitions** (the coarse complex as cartoon functional-connectivity), **structural growth/pruning** (bind/collapse/split ≈ neurogenesis/decay). It borrows the brain's *organising principles, not its mechanics*. Real neural computation is not sheaf-consistency-maintenance. This is the right altitude for a solo, from-scratch project; modelling neural computation would be a fool's errand at any budget.



### 0.8 The bottom line (state it every time we drift)
The simplices don't hand you augmented intelligence. They hand you a **rigorous, measurable, self-checking substrate on which augmentation-via-structure MIGHT emerge** — through measured cross-organ error-correction and accumulation over time — and on which you can **tell whether it's emerging rather than deceiving yourself.** Whether the bet *wins* (whole genuinely exceeds sum) is unknown, and no elegance of topology guarantees it. But this is a real, well-instrumented research bet, not a beautiful story — and the instrumentation is what makes it real.

### 0.9 Scaling the harness (only when forced — none of this is forced yet)
In the order the harness will actually hit walls: (1) **SQLite** single-writer → Postgres, with separate machines holding *subcomplexes* synced through what is literally a restriction map; (2) **Groq free tier** → pay for throughput or shift the cheap tier fully local (router already makes this a config change); (3) **subprocess-over-stdio** (one machine) → message queue / RPC (the persistent `--ipc-server` is halfway there); (4) **hardware-awareness** already future-proofed (auto-thread-detect + config-driven split-brain); (5) **containerise** (Docker) when deploying beyond the laptop. Recommendation: build NONE of it yet. The only near-term risk is #1 if Librarian + Curator run concurrently in one process.

COMMENTS FROM CHARBEL:
1- Then... how can we use this mathematical model to create something that makes the system smarter? if the topological structure and it's ability to evolve over time isn't making the system smarter than what is? raw computational prowess and hardware optimization can only take you so far... so how can we use what we do here to achieve not "smarter" models, but genuinely cognitive models which folds evolves adapts becomes smarter the more and more you feed it? 

2- why is it a fool's errand to model neural computation? I'm not talking at a very fundamental level of neural computation but there's a thing my neurologist sister told me once, intelligence is achieved by the quality and **structure** of the connections of the neurons and not by the shear numbers of neurons. I believe topology and sheaf theory allows us to model both structure and quality, so if that's not achieved even at a basic level, how can we make it so? what does modern research give us that  we can use and levereage here? 

3- from the bottom line, well why aren't we using this to actually model a form of intelligence, what aren't we doing proper research on what we already have to use it to our advantage.

---

## 1. Decisions (the forks we've resolved)

- **2026-07-22 — `C` is TWO-LEVEL.** The base complex of `M=(C,F,s)` is stratified: the **coarse** complex has the *cognitive modules* as vertices (Planner, Memory, Search, Reasoning, Verify, Reflection); each module's stalk is *itself* a **fine** complex of concepts. Resolves the "concepts-vs-subsystems" contradiction between the code (concepts) and the endorsed design (subsystems). Preserves all current C++. Chosen by Charbel.
- **2026-07-22 — Kill "Pachner move" as terminology.** A knowledge/architecture graph is not a manifold, so the Pachner preservation guarantee doesn't transfer. Replaced by honest typed structural ops: `bind`, `collapse`, `split`, `merge`, each logged to a mutation history.
- **2026-07-22 — Working method.** Learn-as-we-go / dynamical. Definition → C++ impl → visualize → experiment → debug → math refinement, looping. No new math object unless implementation forces it. Slow down and digest on request.
- **2026-07-22 — Legacy Python = subcomplexes.** The old Python scripts (Librarian, Canonicalizer, Harvester, ContextManager, Communicator) are NOT retired; each is reformulated as a **module-vertex of the coarse complex `K`**, with its local state as its stalk. "Reformulate the Python" ≡ "give each script its coordinates in `M=(C,F,s)`." (e.g. Librarian = the Search/Memory organ; Communicator = the π side of the ℒ⊣ℳ adjunction.)

## 2. Concepts & definitions learned (glossary as we go)

- **Simplicial complex** — vertices + downward-closed family of "simplices" (k+1 things bound at once). 0-simplex=vertex, 1=edge, 2=filled triangle, 3=tetrahedron. Downward closure: a simplex present ⇒ all its faces present.
- **Sheaf / stalk / section** — a sheaf `F` attaches data to each piece of the complex; the data on one piece is its **stalk**; a **global section** `s` is a consistent choice of data everywhere that agrees on overlaps (= one coherent "thought").
- **Cohomological obstruction (H¹)** — when local pieces are each fine but can't be glued into a global agreement, that failure is measured by the first cohomology `H¹(C,F)`. It is the rigorous fingerprint of a contradiction / cognitive dissonance — the parent of the "conflict score".
- **Filtration / persistent homology** — a weighted complex where weights grow/decay; persistent homology reads which structures *survive*. Consumer here: deciding which coalitions are stable enough to consolidate into permanent memory.
- **Model / inference** — a "model" is a big file of numbers (weights); "inference" = running it to produce output. Cost of local inference ≈ enough fast memory to hold the weights + enough compute to be fast. A small chat model needs ~5–8 GB just for weights.
- **Local vs. API (remote)** — Local: the model lives on your PC and your PC computes (free to run, needs a strong PC). Remote/API: the model lives on a provider's servers (Groq/Google/Anthropic), you send text over the internet and pay per use / use a free tier (needs only internet). An "API call" = send text → their server runs the model → text comes back.
- **Token / tokenization** — models read text as "tokens" (chunks ≈ ¾ of a word; a page ≈ ~500 tokens). APIs bill by tokens **in** + tokens **out**. The "send 30 pages not 3000" strategy is literally a token-reduction strategy.
- **Embedding** — a *different* kind of model that turns text into a fixed list of numbers (a vector) capturing meaning; similar meanings → nearby vectors. These vectors ARE the stalk data of `F`; distances between them are the conflict/Wasserstein scores. Embedding models are tiny (MBs) and run on a weak CPU. A random/fake embedding = random coordinates = every distance is noise (why FIX-1 is fatal).

## Hardware & infra decisions

- **2026-07-22 — PC verdict.** Charbel's machine: AMD Ryzen 3 5300U (4c/8t), **5.9 GB RAM total**, integrated Radeon (no dedicated GPU). CANNOT run a local reasoning/chat model (weights won't fit in RAM). CAN run a tiny CPU embedding model.
- **2026-07-22 — Split-brain architecture (decided in principle).** Reasoning brain = **Groq API** (remote, free tier, already wired: `llama-3.1-8b-instant`). Embeddings = **tiny local CPU model** (free, no quota burn even when ingesting whole books; proposed: `fastembed` + a 384-dim small model). System-wide embedding dimension = whatever that model outputs (**384**), killing the fake-128 and truncated-512 regimes. This grounds FIX-1 in real hardware.

## 3. Constructions (the formal build, crystallized)

- **Construction 1 — Coarse cognitive complex `K`.** Vertices = modules; simplex = a bound *coalition* of modules working as one unit; weight `w(σ,t)∈[0,1]` = coupling strength; dynamics via `bind`/`collapse`/`split`/`merge`; no-global-section on a coalition ⇒ `H¹≠0` ⇒ conflict spike ⇒ RESOLVE mode; persistent coalitions get consolidated (= learning changes topology). Maps to existing `topology::SimplicialComplex` + `core::Sheaf` + `core::GlobalSection`, reinterpreting `VertexID` as a module id. **Status: drafted, endorsed; being amended to make coarse-level growth (neurogenesis via `split`) explicit.**
- ✅ **Construction 2 — Cellular sheaf on K; the conflict score DERIVED (2026-07-22).** Use a **cellular sheaf** (Curry, Hansen–Ghrist): stalk `F(v)=R^384` per module-vertex, `F(e)=R^384` per bound edge, restriction maps `F_{v⊴e}: F(v)→F(e)`. Coboundary `(δx)_e = F_{u⊴e}(x_u) − F_{v⊴e}(x_v)`; **sheaf Laplacian `L = δᵀδ`** (real, symmetric, PSD).
  $$\omega(x) = x^\top L x = \sum_{e=\{u,v\}} \lVert F_{u⊴e}(x_u) − F_{v⊴e}(x_v)\rVert^2$$
  - `ω=0` ⟺ state is a global section. **`H⁰(K;F) = ker L`** — "a coherent thought" is literally a matrix kernel.
  - Cheap: `O(|edges|·d)` sparse. **Diagnostic:** decomposes PER EDGE → the system knows WHICH two modules disagree, so RESOLVE can be aimed.
  - **Rescues the "Cognitive FFT":** the old doc never established its obstruction operator was self-adjoint; `L` genuinely IS symmetric PSD, so the spectral theorem applies for real. Eigenvectors = honest modes of disagreement (small λ = droppable noise, large λ = structural conflict). Uses `Eigen::SelfAdjointEigenSolver`, already called in `algebra.cpp`.
  - Gates the controller: `ω > ε ⇒ RESOLVE`, else EXPLORE.
  - **Two-level glue:** coarse-graining map `π_v : (C_v,F_v) → F(v)=R^384`. **v1 = weighted centroid of active concept embeddings** (weights = simplex weights `w(σ,t)`); v2 = top principal component if needed.
  - **OPEN (let implementation force it):** what the restriction maps actually are. **v1 = identity** ⇒ `ω = Σ‖x_u − x_v‖²` ("do bound modules agree in embedding space"). v2 = learned projections only if v1 proves too blunt.

- ✅ **Construction 3 — The uncertainty stack (2026-07-22).** Four layers, ordered by cost, answering different questions. Coherence ≠ correctness, so they are NOT interchangeable.
  | Layer | Question | Cost | When |
  |---|---|---|---|
  | `ρ` (coherence) | are my parts agreeing? | ~free | every tick |
  | `ρ̂` vs `ρ` (expected precision) | did I *know* whether I'd agree? | free (k-NN over history) | every tick once history exists |
  | `b₀ / b₁` (topology) | what's structurally missing? | medium | on conflict, ACTIVE SUBCOMPLEX ONLY |
  | perturbation `J` | am I stable? | **k× API calls** | high-stakes only (before promotion) |
  | **VerifyOp** | am I actually *right*? | medium | promotion gate |
  Feedback edge: **Verify failure ⇒ update the ρ̂ store ⇒ better self-knowledge next time.**
  - **Corrections made to the source text:** (1) it conflated simplicial `b₁` with sheaf `H¹` — these are DIFFERENT: `b₁` = a hole in the shape ⇒ *structure missing* (no binding theorem); sheaf `H¹` = failure to glue ⇒ *data inconsistent* (modules contradict). Conflating them makes you fill a hole when you actually have a contradiction. (2) The "Fréchet derivative" `J = ‖∂F/∂x‖` **does not exist** — F runs through discrete LLM token sampling, a DAG generator and DB lookups; nothing is differentiable. Reformulated honestly as **paraphrase-perturbation variance** (run k paraphrases, measure spread), which costs k× API and must be rationed.
  - `b₁` is defensible here (unlike most TDA-on-knowledge-graphs hand-waving) *only because* we defined simplices to mean genuine n-ary binding (Construction 1). Earned, not borrowed.

- 🔵 **Construction 4 — ORGANS AS AN OVERLAPPING COVER; THE COARSE COMPLEX AS ITS NERVE
  (proposed 2026-07-31, NOT IMPLEMENTED).** **⚠️ RE-BASED SAME DAY BY CONSTRUCTION 5 (below):
  the NERVE half survives intact; the COVER half — what a cover element *is*, and how it is
  initialized — is SUPERSEDED. Read Construction 5 before building anything here.** Answers the question A17 says we owe: *what determines
  the organ decomposition?* Today it is a hand-set list of ~6 cognitive modules, and **FIX-8 is the
  symptom of its arbitrariness** — the corpus says 7 organs in the `.tex`, 6 in the logbook, 4+RESPOND
  at runtime. A structure nobody can count consistently is a structure nobody derived.

  **⚠️ FIRST, A CLARIFICATION THAT COST US CONFUSION.** There are TWO orthogonal axes and they are
  routinely merged (Charbel merged them, and the merged version is intuitive enough that it will
  happen again):

  | | 𝕂 (accumulated over time) | W (adapted to this problem) |
  |---|---|---|
  | **coarse** (organs) | all organs, all learned couplings | the organs this task woke |
  | **fine** (concepts) | everything ever crystallised | concepts instantiated by `ι*` |

  *coarse/fine* is the **stratification** (modules vs concepts inside a module, §1 2026-07-22).
  *𝕂/W* is **store vs cache** (§5r). "Accumulated over time" vs "adapts to the problem" describes
  **𝕂/W, not coarse/fine.** Both levels exist in both complexes.

  **⚠️ AND A RELIC TO KILL: "organs = documents" was never architecture.** It was invented for V6
  (§5ah) because a real corpus was needed and documents were the nearest grouping. Rejected by
  Charbel, correctly. V6's organ definition is a proxy and its number inherits that.

  **THE CONSTRUCTION.** Sheaf theory never required a *partition* — it requires a **cover**, and
  covers may **overlap**. Let organs be regions `{U_i}` of concept space. The **Čech nerve**
  `N({U_i})` has one vertex per organ and a k-simplex for every (k+1)-fold non-empty intersection.
  That **is** the coarse complex — derived rather than drawn.

  > **★ A k-simplex appears exactly when k+1 organs SHARE a concept.** 2 organs → an edge;
  > 3 → a filled triangle; 4 → a tetrahedron. **Interdisciplinary knowledge literally creates
  > higher-dimensional simplices.** This finally makes §0.5's claim ("simplices = honest n-ary
  > relations") true *by construction* rather than by our promising to build them honestly.

  **🚨 THE TRAP, AND THE FIX — a naive nerve repeats FCA's mistake.** Mapper/nerve as classically
  used is a SNAPSHOT: fix data, build cover, take nerve, **recompute** when data changes. That is
  data-determined, which is precisely why FCA was rejected (§6: "MOS must GROW, not be RECOMPUTED").
  **Resolution: the COVER is the state, the NERVE is the observable.** Cover elements are persistent
  objects with birth time, weight and accumulated concept set; they grow / split / merge / are born /
  decay via the typed ops of Construction 1. The nerve is recomputed cheaply on demand from current
  overlaps. Structure is derived (A17 ✓); the thing it derives *from* accumulates (growth ✓).
  The cover lives on the **𝕂** side.

  **WHAT IT TURNS ON.** Cover growth induces simplicial maps (the nerve is functorial), so a growing
  cover is a **filtration** — exactly what persistent homology consumes. §2's glossary already
  specifies the consumer ("deciding which coalitions are stable enough to consolidate into permanent
  memory") and it has sat unused since July for want of a principled filtration. This supplies one.

  **INITIALIZATION — the prior, not the truth.** Candidates: (a) empty, grow from nothing — purely
  history-determined but the first few concepts fix the organ structure permanently (the
  growth-address problem at its worst); (b) **seed with the functional modules and let them evolve**;
  (c) bootstrap by clustering a first batch — reintroduces recomputation at t=0 plus Mapper's
  parameter sensitivity. **Take (b), framed as the shrinkage prior `belief.py` already implements
  and tests:** `Σ_v = (S_v + κΣ₀)/(n_eff + κ) + εI`. The six modules are `Σ₀`, worth `κ`
  observations. At `n_eff = 0` you get the hand-set list; as evidence accumulates you get the data.
  **The hand-set structure becomes a starting condition evidence can move, not a permanent decision.**

  **★ OPTIMAL INITIAL CONDITIONS — criticality pins Mapper's worst hyperparameter.** §5p mechanism ②:
  *"σ = mean binds triggered per co-activation; σ≈1 → scale-free avalanches, max dynamic range
  (Beggs–Plenz, Kinouchi–Copelli)."* Too few/large organs ⇒ everything overlaps ⇒ σ ≫ 1,
  supercritical. Too many/small ⇒ nothing overlaps ⇒ σ ≪ 1, nothing propagates. **Mapper's most
  criticised parameter is the GAIN (how much cover elements overlap) — and overlap is exactly what
  controls branching. So: set initial granularity/overlap so the measured branching parameter starts
  near 1.** A hand-tuned knob becomes a derived one, measurable per tick, with independent empirical
  support.

  **🚨 THE CIRCULARITY TRAP — any data-driven organ definition can make V6 VACUOUS.** If organs are
  defined by minimising within-organ spread and we then measure σ_dir (the within-organ spread) on
  those organs, we have optimised the quantity we are measuring. V6 stops testing the metric and
  starts testing the clustering. **Two honest exits:** (1) build the cover from a lens INDEPENDENT of
  the metric under test — **co-activation history** (which concepts fire together), not embedding
  distance; or (2) demote V6 to a consistency check and stop citing it as evidence for the metric.
  *Note this is an argument FOR the hand-set list that nobody expected to be making.*
  **Recommended: (1), a co-activation lens** — it is history-determined (the 𝕂 side), independent of
  embedding distance so V6 still bites, and it is what "constructed over time" actually means.

  **⚠️ TWO COSTS, NOT HIDDEN.** (i) **Combinatorial blow-up**: generous overlap produces many
  high-dimensional simplices; criticality wants overlap, the §5s cell budget wants sparsity, and
  these pull against each other. It may turn out σ≈1 is unaffordable and we must run subcritical.
  (ii) **The Nerve Theorem's hypothesis is probably not met**: it needs a *good* cover (every
  non-empty intersection contractible), unverifiable for concept regions in ℝ³⁸⁴. So `b₁` of the
  nerve is **suggestive of** the concept space's shape, NOT provably equal to it. This is exactly the
  borrowed-guarantee pattern §0.5 cut from the inherited formalism — state it as a caveat, never
  quote it as a theorem.

  **📋 STATED WAYS TO FAIL (per §7's discipline — written before building):**
  1. If the grown cover's nerve has `b₁ = 0` always (or `b₁` a trivial function of vertex count),
     the topology carries no information and this is an expensive clustering. **Drop it.**
  2. If the branching parameter cannot be brought near 1 at any overlap the cell budget affords,
     the criticality criterion is vacuous and initialization is back to hand-tuning.
  3. If σ_dir on cover-organs is **not** lower than on document-organs (§5ah's 0.32), the
     multi-modality diagnosis behind π_v v2 and this construction is wrong.
  4. If after N sessions the cover has produced no split/merge/birth events and still equals the
     initial prior, it is not growing — it is the hand-set list with extra steps.

  *Prior art to cite, not claim:* **Mapper** (Singh, Mémoli & Carlsson 2007) is this construction
  made algorithmic — cover via a lens, take the nerve. Cellular sheaves over such complexes:
  Hansen & Ghrist. Nerve theorem: standard (Borsuk). **Mapper's known weakness is exactly the
  parameter sensitivity item (ii) and the criticality rule address.**

  ---

  ### ⚠️ AMENDMENT 2026-07-31 (same day, after §5aj/§5ak). Three corrections. None fatal; all
  are scoping decisions that must be made BEFORE anyone builds this.

  **A4-1. 🚨 THE FILTRATION CLAIM IS FALSE AS WRITTEN — the history is a ZIGZAG, not a filtration.**
  The construction says *"cover growth induces simplicial maps, so a growing cover is a filtration —
  exactly what persistent homology consumes"*, while two lines earlier allowing cover elements to
  *"grow / split / merge / are born / decay."* Those are not compatible. Write `N(𝒰)` = the complex
  with a simplex on `S ⊆ I` iff `⋂_{i∈S} U_i ≠ ∅`, and check each op:

  | op | induced map | direction |
  |---|---|---|
  | **grow** `U_i ⊆ U_i'` | every non-empty intersection stays non-empty ⇒ `N(𝒰) ↪ N(𝒰')` | forward, inclusion ✓ |
  | **birth** | old simplices survive, vertex added | forward, inclusion ✓ |
  | **merge** `i,j ↦ k`, `U_k = U_i ∪ U_j` | vertex map `f` has `U_{f(i)} ⊇ U_i`, so `⋂_{f(S)}U ⊇ ⋂_S U ≠ ∅` | forward, **simplicial map** (collapses, not an inclusion) ✓ |
  | **split** `U_k ↦ U_i,U_j` with `U_i,U_j ⊆ U_k` | the map that exists is `N(new) → N(old)` | **REVERSED** ✗ |
  | **decay / shrink** | shrinking kills intersections ⇒ simplices vanish ⇒ no forward simplicial map; only `N(new) ↪ N(old)` | **REVERSED** ✗ |

  Standard persistent homology consumes a one-directional sequence (inclusions, or simplicial maps
  à la Dey–Fan–Wang). It does **not** consume alternating arrows. Split and decay reverse the
  arrows, so the cover's history is a **zigzag** (Carlsson–de Silva) — a heavier machine with no
  drop-in barcode.
  > **★ AND THE STING: §5aj just derived a firing criterion for `split` (`pi_v_modes()`) — the one
  > structural op that was previously undefined is precisely the op that breaks the filtration.**

  **DECISION TAKEN: exit (a) — restart the filtration at each split/decay.** Run standard PH within
  growth/birth/merge epochs; a split or decay closes the epoch and opens a new one. Costs nothing,
  is honest, and the named consumer (§2: *"which coalitions are stable enough to consolidate"*) is a
  **within-epoch** question anyway. Rejected: (b) zigzag persistence — real but expensive and not
  yet justified; (c) forbid `split` — unattractive now that it is the one derived op we have.

  **A4-2. 🚨 "COVER ELEMENT" IS USED IN TWO INCOMPATIBLE SENSES IN THE TEXT ABOVE, and the choice
  decides the circularity question.** The construction says both *"regions `{U_i}` of concept
  space"* (geometric — membership predicate in ℝ³⁸⁴) and *"accumulated concept set"*
  (combinatorial — overlap = shared concept IDs). These are different objects:

  | | geometric region | **concept set** |
  |---|---|---|
  | overlap test | membership predicate in ℝ³⁸⁴ | set intersection, trivial |
  | nerve-theorem caveat (ii) | live | **irrelevant** |
  | shrinkage-prior init | natural (`Σ₀` = the six modules) | needs re-derivation |
  | V6 circularity | **reintroduced** — regions defined by embedding distance | **avoided** — co-activation is metric-independent |

  **The geometric reading is close to dead, and the stalk decision is what kills it.** Since §5t Q1
  a concept's stalk is a rank-k SPD Gaussian `Σ = UUᵀ + DI`, **not a point**. So *"is concept `c`
  inside `U_i`?"* has no crisp answer — it needs a soft membership (Bures ball, mass threshold),
  which is **exactly the metric under test**, reintroducing the V6 circularity through the back
  door. **TAKE THE COMBINATORIAL READING:** a cover element is a persistent object carrying an
  accumulated **set of concept IDs**; overlap is set intersection. This is also what makes the
  recommended co-activation lens actually implementable. **Cost, stated:** the shrinkage-prior
  initialization `Σ_v = (S_v + κΣ₀)/(n_eff + κ) + εI` is a statement about *covariances*, i.e. about
  ellipsoids — under the combinatorial reading it must be restated as a prior over **membership**
  (κ pseudo-observations of "concept `c` belongs to module `i`"), not over shape. **Not yet done.**

  **A4-3. CAVEAT (ii) COSTS LESS THAN STATED — the nerve theorem is not needed for the primary use.**
  Once *"the COVER is the state"* is taken seriously, `b₁` of the nerve is an honest invariant **of
  the cover itself**, not an estimate of anything. The nerve theorem is required only to claim
  `H_*(N(𝒰)) ≅ H_*(⋃U_i)` — i.e. only if we say *"concept space has a hole."* We do not need that
  claim: the consumer wants *"the organ cover has a hole,"* which is a fact, not an approximation.
  **Keep caveat (ii) worded as-is for any statement about concept space; drop it for statements
  about the cover.** Do not quote the nerve theorem in either case.

  **STILL UNEXECUTABLE (not a correction, a gap):** the criticality rule for the gain parameter.
  §5p's `σ` = *"mean binds triggered per co-activation"* presupposes a **propagation process on the
  cover** that is nowhere defined. Stated failure mode 2 asks *"can we afford σ≈1"*; the prior
  question is **"σ is measured on what dynamics."** Answer that before failure mode 2 means anything.

  **NET LEDGER AFTER THIS AMENDMENT.**
  - **Stands unconditionally:** derived-not-drawn structure (A17) · overlaps as first-class objects ·
    **n-ary simplices honest by construction** (the strongest item; nothing has touched it).
  - **Retracted:** the σ_dir / multi-modality argument (§5aj).
  - **Now qualified:** the PH payoff (epoch-restricted, per A4-1) · "no privileged granularity"
    (needs a null, see §5ak amendment).
  - **Verdict: keep, but do NOT cite the persistence payoff without the epoch qualifier.**

- 🔵 **Construction 5 — THE COVER ELEMENT DERIVED: ORGANS AS LATENT CAUSES OF CO-ACTIVATION
  (proposed 2026-07-31, NOT IMPLEMENTED. Phase-2 item 9.)** Construction 4 left *what a cover
  element is* undecided between "region of ℝ³⁸⁴" and "set of concepts" (amendment A4-2), and its
  criticality rule had no process to be measured on (the fourth blocker). **Both are the same
  wound — nobody said what GENERATES the cover. This derives it.**

  **THE CONSTRAINTS PIN THE ANSWER — nothing here is chosen.** (C1) metric-independence, or V6 goes
  vacuous ⇒ the only admissible raw material is **co-activation history**; (C2) accumulates, never
  recomputed (§6, the FCA rejection); (C3) overlap structurally possible, not a fudge; (C4) supports
  the five typed ops; (C5) §5s cell budget. (C1) fixes the data: concepts `c = 1..N`, at tick `t`
  an assembly `A_t ⊆ {1..N}` fires, `x_tc = 1` iff `c ∈ A_t`. **That record is exactly E7's output
  and it is the entire input.**

  **★ THE DERIVATION — the MODEL CLASS *is* the cover/partition choice.** Organs should be the
  latent causes of co-activation. There are two model classes and the difference is not stylistic:

  | | **competitive** (mixture / categorical / Dirichlet) | **disjunctive** (multiple-cause / noisy-OR) |
  |---|---|---|
  | latent | one `z_t ∈ {1..K}` picks a cause | `z_ti ~ Bern(π_i)`, several on at once |
  | combination | convex, `Σ_i π_i p(c\|i)`, `Σπ_i = 1` | **additive**, `p(x_tc=0\|z_t) = exp(−Σ_i z_ti λ_ci)` |
  | causes | compete for normalised mass | superpose, no normalisation |
  | latent structure | **a PARTITION** — provably cannot represent overlap | **a COVER** |

  with `θ_ci ∈ [0,1]` the probability organ `i` recruits concept `c`, and `λ_ci = −log(1−θ_ci) ≥ 0`.
  > **COVER ⟺ ADDITIVE latent causes. PARTITION ⟺ CONVEX latent causes.** Construction 4 argued for
  > the cover structurally ("sheaves only need a cover"). It now has a **statistical** characterisation
  > and therefore a **falsifiable** one — fit both, compare on held-out data (T1).

  **⇒ A cover element `U_i` IS a latent cause in a noisy-OR model of co-activation; its content is
  the recruitment vector `θ_·i ∈ [0,1]^N`.** Neither "region" nor "set" was right: it is a **soft
  membership vector**; the set reading is its thresholding, and the region reading never arises
  because the model contains no geometry. Constraints check: (C1) ✓ the embedding never appears —
  **so V6 still bites**; (C2) ✓ accumulates via sufficient statistics `n_ci` (times `c` fired with
  organ `i`), `m_i` (times `i` was active); (C3) ✓ `Σ_i θ_ci` is unconstrained and its excess over 1
  **is** the overlap; (C4) ✓ birth = new column, growth = statistics accumulate, split/merge = column
  ops, decay = discounting; (C5) ✓ `K·N` sparse.

  **THE OBJECTIVE, AND WHY IT HAS AN OPTIMUM WHERE σ_dir HAD NONE.** Variational free energy with
  `q(z_t) = ∏_i Bern(q_ti)`:
  `F = Σ_t E_q[−log p(x_t|z_t,θ)] + Σ_t KL(q(z_t)‖p(z)) + KL(q(θ)‖p(θ))`
  — accuracy plus complexity, i.e. MDL, i.e. **the same free-energy principle §5ag already used to
  derive `π_e`. Not a new import.** Accuracy decreases in `K`; complexity grows `O(KN)`. **So `F(K)`
  CAN have an interior minimum, whereas `σ_dir` cannot** — §5ak swept `k` with an instrument k-means
  drives monotonically downward by construction (see that section's amendment), so of course it found
  no dip. **`F(K)` is the non-monotone instrument that sweep needed.** Not guaranteed: if the corpus
  has no organ structure `F` bottoms at `K=1` or `K=N`. **Its absence is then a finding, not an
  artefact of the instrument** (T2/T4).

  **INITIALIZATION — Construction 4's option (b), now derived instead of analogised.** Beta prior
  **per `(c,i)` pair**, strength `κ`, base `π⁰_ci` = the hand-set six modules. Posterior mean:
  > `θ̂_ci = (n_ci + κ·π⁰_ci) / (m_i + κ)`

  At `n=0` you get the hand-set list; as history accumulates you get the data; `κ` is what the
  hand-set structure is worth in observations. **The hand-set structure becomes a starting condition
  evidence can move** — Construction 4's stated intent, now falling out of the model. **Beta-per-pair,
  NOT Dirichlet-over-organs: Dirichlet normalises `Σ_i` to 1 and would smuggle the partition back in
  through the PRIOR even under a noisy-OR likelihood.** This discharges A4-2's stated debt.

  **★ THE NERVE BECOMES A GENUINE FILTRATION, AND THE LAST KNOB DISSOLVES.** Thresholding `θ` would
  reintroduce a hand-set number. Instead define, for a set of organs `S`, the expected number of
  concepts shared by all of them, and filter by it:
  > `w(S) = Σ_c ∏_{i∈S} θ_ci`,  `N_τ = { S : w(S) ≥ τ }`

  - **`N_τ` is a simplicial complex.** For `S' ⊆ S`, each `θ_ci ∈ [0,1]` gives `∏_{S'} θ ≥ ∏_S θ`,
    so `w(S') ≥ w(S)`, so `S ∈ N_τ ⇒ S' ∈ N_τ`. Closed under faces. ∎
  - **`{N_τ}` is a monotone filtration.** `τ' ≤ τ ⇒ N_τ ⊆ N_τ'`. ∎

  Consequences: (1) **the overlap/gain parameter — Mapper's most-criticised knob, and the one A4-2
  threatened to reintroduce — dissolves into a filtration parameter.** Don't pick `τ`; take what
  persists across `τ`. Same dissolution that worked for F10 and that §5ak wants for δ. (2) **This
  filtration is MONOTONE, so standard PH applies unconditionally** — A4-1's zigzag afflicts only the
  *time* axis. **The persistence payoff is rescued more cleanly than by A4-1's epoch fix:** honest PH
  over `τ` at every tick, epoch-restricted PH along time. (3) **The nerve theorem is not needed**
  (A4-3, cleaner): `N_τ` is *defined* from `θ`, not approximating an underlying space. Nothing borrowed.

  **⚠️ `(τ, t)` IS A BI-FILTRATION AND WE ARE NOT GOING THERE.** Multiparameter persistence has no
  complete discrete invariant (Carlsson–Zomorodian). **Use the `τ`-barcode at fixed `t`; read time as
  a SEQUENCE of barcodes.**

  **THE FOURTH BLOCKER, CLOSED BY THE SAME OBJECT.** `σ` needed a process; the generative model **is**
  one. Given fitted `θ, π`, the expected number of further concepts recruited when `c` fires is closed
  form, so criticality becomes a condition on the fitted model, measurable per tick.
  **⚠️ STATED LIMIT, NOT BURIED: this is the branching of the MODEL's implied cascade — a statistic of
  co-activation — NOT the engine's causal bind dynamics.** Better than a synthetic random walk (it is
  fitted to real assemblies), weaker than instrumenting the real causal tree. **Never quote it as the
  engine's σ.**

  **🚧 SCOPE FENCE — WHAT WE ARE DELIBERATELY NOT BUILDING** (the over-engineering trap, named before
  it is fallen into): no multiparameter persistence · no zigzag persistence (A4-1's epoch fix stands) ·
  no geometric regions or Bures membership · no learned restriction maps · no organ-count search beyond
  a bounded `K` sweep · **and no topology half at all until Tier 0 passes.** Three cheap tests can kill
  this before one line of PH code exists. That is the point of the tiering.

  ### 📋 TEST BATTERY — WHAT CONSTRUCTION 5 MUST PASS TO OPERATE AT OPTIMUM
  Written before building, per §7. **Tiers are GATES: do not start a tier until the previous passes.**

  **TIER 0 — IS THE MODEL CLASS RIGHT? Cheap kill-shots. Run these FIRST; they can end the whole thing.**
  | | test | pass criterion | if it fails |
  |---|---|---|---|
  | **T1** | **noisy-OR vs mixture**, both fitted to the same assembly record, compared on **held-out predictive log-likelihood** (NOT in-sample `F`, which rewards flexibility). Split by **tick BLOCKS**, not random ticks — assemblies are temporally correlated | noisy-OR wins held-out | **the COVER IS WRONG and the partition was right. Constructions 4 AND 5 both die.** This is Construction 4's failure mode 1, made decisive |
  | **T2** | **`F(K)` interior optimum**, `K` swept over a bounded range | interior minimum, reproducible across restarts (T5) | no natural organ count; MDL fails exactly where σ_dir failed |
  | **T3** | **overlap is real**: fraction of concepts with `Σ_i θ_ci > 1`, and fitted `θ` not near-binary/near-disjoint | a stated non-trivial fraction, surviving T4 | cover degenerates to a partition — **overlap was fiction**; Construction 4's failure mode 3 |

  **TIER 1 — IS THE FIT AN ARTEFACT? Nulls and stability.**
  | | test | pass criterion | notes |
  |---|---|---|---|
  | **T4** | **structureless null**: refit on assemblies with concept identities permuted within ticks, **preserving assembly sizes and concept marginals** so only co-activation structure is destroyed | real corpus's `F(K)` optimum lies outside the null's spread | **⭐ this ABSORBS the owed V6d.** Same null answers "is there a privileged granularity" properly, with a non-monotone instrument |
  | **T5** | **restart stability**: multiple random restarts; report spread of `F` at the optimum and cover agreement (organs matched by overlap) | a stated agreement threshold | **noisy-OR fitting is non-convex. "Optimal cover" means a LOCAL optimum, restart-dependent. Report the spread; never report a single fit as "the" cover** |
  | **T6** | **identifiability flag**: detect always-co-active cause pairs, which are not separable from one cause | flagged, never silently reported as distinct organs | mirrors the δ identifiability flag already in `derived_scales.py` |
  | **T7** | **sample adequacy**: `θ` has `K·N` parameters against `~T·E[\|A\|]` observations | a stated minimum `T` before ANY fit is reported | **do not repeat §5aj's `n < d` problem.** No fit below the floor gets quoted, even informally |

  **TIER 2 — DOES THE TOPOLOGY EARN ITS PLACE?**
  | | test | pass criterion | if it fails |
  |---|---|---|---|
  | **T8** | **filtration validity as a regression assertion** on real fitted `θ`: `N_τ` closed under faces, nested in `τ` | both hold | it is proved above — so a failure is an implementation bug, and this is the test that catches it |
  | **T9** | **barcode non-triviality**: `τ`-barcode bars vs the T4 null's barcode | bars significantly longer than null | **the nerve's topology carries nothing — drop the PH half and keep the cover.** Construction 4's failure mode 1 |
  | **T10** | **`b₁` not a trivial function of `K`**: regress bar count/length on vertex count | not fully explained by `K` | it is an expensive clustering. **Drop it** |

  **TIER 3 — DOES IT ACTUALLY GROW? (the FCA requirement, §6)**
  | | test | pass criterion | notes |
  |---|---|---|---|
  | **T11** | **structural events occur**: after `N` sessions the cover shows split/merge/birth and differs measurably from `π⁰` | nonzero events + stated divergence from the prior | Construction 4's failure mode 4 verbatim: *"it is the hand-set list with extra steps"* |
  | **T12** | **incremental ≡ batch**: refit from accumulated `n_ci, m_i` vs a from-scratch batch fit | agreement to stated tolerance | **this is the test that proves it GROWS rather than secretly RECOMPUTING.** The FCA rejection is only honoured if this passes |
  | **T13** | **epoch length**: ticks between split/decay events, vs the bar lengths T9 finds | epochs long enough to contain the bars | **closes A4-1's unmeasured consequence.** If epochs are ~3 ticks, epoch-restricted PH sees nothing and A4-1's fix is hollow |

  **TIER 4 — DOES IT BREAK WHAT ALREADY WORKS?**
  | | test | pass criterion | notes |
  |---|---|---|---|
  | **T14** | **⭐ non-circularity, directly**: refit `θ` with the **embeddings permuted**; `θ` must be **bit-identical** | bit-identical | strong and cheap. **If `θ` moves at all, embedding geometry has leaked in and the V6 circularity trap has fired.** This is the test that protects the whole point of (C1) |
  | **T15** | **cold start**: at `n = 0`, `θ̂ = π⁰` exactly | exact | regression test on the prior formula |
  | **T16** | **budget**: `K·N` sparse storage + per-tick nerve recomputation against §5s | within budget, numbers stated | (C5) |

  **⚠️ PRECONDITION, NOT A QUEUE ITEM: E7 AT ENGINE LEVEL.** No assembly record ⇒ no `θ` ⇒ no cover.
  **Construction 5 cannot be built, and NONE of T1–T16 can be run, until the tick records assemblies** —
  and the registry says that data is *"impossible to recover later."* **Every tick run without E7 is
  cover-training data permanently destroyed.** This is why E7 is NEXT item 1 and why it now has a second
  independent consumer.

  **OTHER COSTS, STATED:** non-convexity (T5) · identifiability (T6) · **cold start defers the
  growth-address problem rather than solving it** — early structure is the hand-set list by design.

  *Prior art to cite, not claim:* multiple-cause mixture model (Saund 1995) · noisy-OR component
  analysis (Šingliar & Hauskrecht 2006) · Mapper (Singh, Mémoli & Carlsson 2007) · cellular sheaves
  (Hansen & Ghrist) · MDL/free-energy equivalence (standard).

## 3c. FIX-1 CLOSED (2026-07-22)

Single embedding contract established: **`python/embeddings.py`**, model `BAAI/bge-small-en-v1.5` via fastembed/ONNX, **EMBED_DIM=384**, local CPU, zero API quota. **Rule: never truncate, never pad — RAISE on mismatch** (silent reshaping is what corrupted every distance before). Verified live: cos(math, chat)=0.449 vs cos(math, math)=0.833 — real semantic structure.
- `canonicalizer.py`: fake hash-seeded random 128-d ➜ real 384-d.
- `communicator.py`: 512 truncate/pad ➜ 384 strict; π repointed from (nonexistent) local Ollama ➜ **Groq** `llama-3.1-8b-instant`, temp 0, JSON mode, 429-aware; fixed latent `NameError` on unbound `mos.fbs`; stopped re-embedding once per constraint.
- **Project interpreter is Python 3.11** (`%LOCALAPPDATA%\Programs\Python\Python311`), NOT the 3.14 beta (no onnxruntime wheels).
- **Construction 3 — δ𝔇: the operator algebra grows (from Charbel's 6-phase plan, 2026-07-22).** The formalism previously had only δC, δF, δs with 𝔇 FIXED. Phase-3 neurogenesis forces a fourth axis: **𝔇(t) → 𝔇(t+1)**. Precise definition: **a "microneuron" is a promoted operad sub-tree** — when a composite DAG repeatedly resolves conflicts, it is promoted from composite to first-class *generator* of 𝔇, named, and thereafter emitted by the planner as a single atomic node. Immediately implementable (save sub-DAG → name it → planner may emit it). **The promotion gate is VerifyOp (Phase 6): a composite becomes a generator ONLY if it survives verification.** Phases 3 and 6 are one mechanism. This gives the old `SkillLibrary` its formal home.
  - **Growth trichotomy:** δC-fine = facts/concepts (semantic memory) · δC-coarse = module coalitions (functional connectivity) · δ𝔇 = new executable operators (procedural skill).

## 3b. Python → vertex assignment (Phase 5, decided 2026-07-22)

| Legacy Python | Vertex in coarse complex `K` | Stalk `F(v)` | Operators induced |
|---|---|---|---|
| `librarian.py` | Search / Retrieval | evidence graph, acquisition queue, category graph | `SearchOp`, sub-query decomposition |
| `canonicalizer.py` | **Canonicalizer (special)** | synonym clusters | `merge`, `link` — **mutates K itself** |
| `harvester.py`→Curator | Consolidation (REM) | ephemeral logs, persistence scores | scaffold promotion; **𝔇-generator promotion** |
| `context_manager.py` | Working Memory | `s` restricted to active task | boundary-condition inject/drop |
| C++ `OSKernel` | Orchestrator / Planner | goal, conflict score, mode | selects operadic tree `T(t)` |
| `communicator.py` | **NOT a vertex — the adjunction boundary** | — | π (Lift), G (Project) |

**Already-existing code that implements the formalism:** `canonicalizer.py`'s `insert_n_ary_relation("depends_on", [node]+deps)` IS simplex construction (a theorem + its prerequisite closure = a k-simplex). `operad.cpp`'s foliation into "maximal commuting slices" via `get_support()` IS Phase-2 parallel retrieval.

**Open tensions to respect:** (1) a prerequisite chain is *directed*, a simplicial complex is not — keep TWO structures on the same vertices (directed poset for logical dependency + simplices for n-ary co-binding); do not conflate. (2) "compile an executable primitive" is research-grade — **v1 = promoted parameterized sub-DAG, NOT novel code synthesis**. (3) Phases 1–6 are months of work; the Friday target is a thin vertical slice through Phases 4→1→2→6 only.

## 4. Fix registry (the "fix everything, no half-baking" list)

Found during the 2026-07-22 codebase read. Priority H/M/L. Nothing here is fixed yet — status will update as we go.

- ⚠️ **FIX-1 (H) — Three embedding regimes.** `communicator.py` hardcodes 512 (truncate/pad — the "straitjacket"); `canonicalizer.py` returns a FAKE hash-seeded random 128-D vector; C++ is dynamic. They disagree ⇒ every cross-component distance is corrupted. → unify to one real embedding contract. **[Batch1 verdict: CONFIRMED BROKEN — this is now the #1 real problem. The C++ math is sound but is being fed inconsistent/garbage vectors.]**
- ✅ **FIX-2 (H) — Bures-Wasserstein.** **[Batch1 verdict: CORRECT.]** `knowledge_base.cpp:141` `calculate_wasserstein_2_sq` implements the TRUE trace formula W²=‖μ1−μ2‖²+Tr Σ1+Tr Σ2−2Tr((Σ1½Σ2Σ1½)½), exploiting isotropic Σ1=D1·I to reduce to O(k³) (eigendecompose only the k×k U₂ᵀU₂). Verified by hand. NOT the diagonal approximation. Caveat: specialized to isotropic Σ1 (documented, exact for that case). No action; a unit test would be nice.
- ✅ **FIX-3 (M) — `algebra.cpp` eigenspectrum.** **[Batch1 verdict: ALREADY FIXED in code; only the doc lies.]** `compute_eigenspectrum` uses `Eigen::SelfAdjointEigenSolver` (SIMD), not hand-rolled Jacobi. The stale part is the HEADER comment in `algebra.hpp:43` still saying "Jacobi Eigenvalue Algorithm". → trivial: fix the comment.
- 🔵 **FIX-3b (L) — `semantic_skill.cpp` merge_with.** **[Batch1 verdict: CORRECT full-covariance Woodbury fusion, NOT elementwise.]** Verified y=P₁μ₁+P₂μ₂ (precision-weighted) by hand; entropy via Matrix Determinant Lemma is exact; the old −100.0 magic number is gone. TWO caveats: (a) the exact fused-covariance construction `U_exact` (the `W` matrix, lines 89–103) is structurally right but I did NOT certify bit-exactness — needs a small numerical unit test vs a dense (P₁+P₂)⁻¹. (b) hardcoded **95% energy threshold** (line 126) is exactly the kind of magic number Charbel objects to — should be an ε-configurable dynamic rank.
- ⚠️ **FIX-4 (M) — Hand-parsed JSON in `colibri_kernel.cpp`.** Uses `extract_json_value/array` instead of the vendored `nlohmann/json`. Fragile. (Not re-read in Batch 1.)
- ⚠️ **FIX-5 (?) — Legacy Python status. RESOLVED as a plan:** reformulate each legacy Python script as a **subcomplex / module-vertex of the OS** (see Decisions). Not retire. The `SkillLibrary.query_similar_experiences` crash (output 2.txt) belongs to the old Python stack that's being reformulated.

## 5. North star & feasibility

- **Target problem = `DOCS/FIRST DRAFT.pdf`.** Charbel's own research paper: spectrum & time-evolution of a thermally-weighted Hodge–de Rham Laplacian on 1-forms on ℂℙ³ (Fubini–Study), weight `e^{-βE}` from a two-qubit Hamiltonian K. **Section 3 ("Solving the eigenvalue problem") is BLANK** — "solve FIRST DRAFT" = fill Section 3.
- **Two halves:** (1) *retrievable core* — unweighted Hodge spectrum on ℂℙⁿ is classical (Ikeda–Taniguchi / SU(4) rep theory); `Δ_β` is a Witten/Bakry–Émery drift-Laplacian, known theory. Winnable via retrieval + 70B. (2) *novel frontier* — the thermally-weighted, symmetry-broken spectrum is a genuine new step; high confident-wrong risk; beyond a free 70B to do rigorously by Friday.
- **Feasibility verdict (honest):** A first-draft, free-tier TATIANA is *day-1 worse* than opening Claude, and will NOT autonomously produce a correct rigorous Section 3 by Friday. Its edge is architectural (persistent memory, grounding in Charbel's library, contradiction-awareness, self-verification, cumulative growth), not raw reasoning. The bet is on the SLOPE (accumulation over time), not the intercept.
- **2026-07-22 — Friday goal = "PROVE THE LOOP" (chosen).** Success = the engine runs end-to-end on FIRST DRAFT and *visibly* thinks → researches → grows concept-nodes → adapts (conflict spike at the frontier) → produces a GROUNDED, HONEST attempt at Section 3, flagging what it doesn't know, at $0. NOT a guaranteed-correct proof. This problem is the ideal test: winnable core + revealing ceiling.

### Critical path to Friday (minimal, dependency-ordered)
- ✅ **Step 0 — DONE (2026-07-22).** Engine now builds and runs from current source.
  - Python bridge wired: installed `flatbuffers` (25.12.19) + `requests`; regenerated FlatBuffers Python bindings via vendored `flatc` → `python/mos/fbs/*.py`; imports verified. OpType vocabulary confirmed: SEARCH/COMPUTE/REASON/RESPOND/VERIFY/CONTEXT.
  - C++ rebuilt: `cmake --build build --target mos --config Debug` → **succeeded first try, exit 0, zero errors** (only C4244 conversion warnings; the `pwsh.exe not recognized` line is a harmless post-build step). New `build/Debug/mos.exe` (5.3 MB) replaces the stale root `mos.exe` (4.4 MB, built from an OLD REPL main.cpp).
  - Verified: bare run prints the current IPC banner; `--ipc-server` starts and exits cleanly on EOF.
  - Build tree notes: Eigen + FlatBuffers already cached in `build/_deps` (no re-download); generator = Visual Studio 17 2022; MSVC 14.40.33807 present. **Do NOT try a fresh MinGW/g++ build** — `CMakeLists.txt:14` passes the MSVC-only flag `/std:c++17` in the non-MSVC branch, which would break g++.
- ⛔ **NEW BLOCKER (found in Step 0) — π points at a local Ollama that cannot exist here.** `communicator.py` POSTs to `localhost:11434` for BOTH the π morphism and embeddings. Ollama is not installed and nothing listens on 11434 — and the PC can't host a local LLM anyway. Meanwhile `main.cpp` already wires the C++ ColibriKernel to **Groq** (`api.groq.com`, llama-3.1-8b-instant). So: **C++ = Groq ✓ / Python π = Ollama ✗.** Must repoint π to Groq. Also needs a `GROQ_API_KEY` (not set in shell).
- **Step 1 — Repoint π to Groq + FIX-1 embeddings.** Both live in `communicator.py`. Reasoning → Groq API; embeddings → tiny LOCAL model (fastembed, 384-d), killing fake-128 / trunc-512. Geometry is meaningless until this is done.
- **Step 2 — Minimal real retrieval.** SearchOp actually ingests the FIRST DRAFT paper (+ maybe 1–2 arXiv hits) into the KB. Reuse librarian.py's arXiv code.
- **Step 3 — Orchestrate the attempt.** π turns "solve Section 3" into a DAG (Search → Reason → Respond); wire existing operators.
- **Step 4 — Run on FIRST DRAFT; document honestly** what worked / broke / was faked-vs-real.

## 5b. FULL CODE AUDIT — placeholders, mocks, silent no-ops (2026-07-22)

Ranked by severity. "Silent" = fabricates or discards data with NO warning to the user.

### CRITICAL — fabricates or destroys data silently
| # | Location | Problem |
|---|---|---|
| A1 | `python/librarian.py:62-70` `_cmd_inspect` | Returns **entirely fabricated telemetry** — hardcoded `processed: 87%`, `concepts: 342`, `skills: 56`, `missing: "Spectral theory chapter"` — unrelated to any real document. Looks exactly like real stats. Worst offender. |
| A2 | `python/librarian.py:48-60` `_cmd_reorganize` | Returns **invented file moves** (`Topology/Rudin.pdf → Math/Topology/Rudin.pdf`) regardless of actual vault contents. Marked "Stub implementation". |
| A3 | `python/librarian.py:39-44` `learn` / `repair` actions | Return success strings ("Targeted extraction triggered", "Repair executed (duplicate detection and orphan pruning complete)") while **doing nothing at all**. Claims completed work that never happened. |
| A4 | `python/canonicalizer.py:130-132` `_add_provenance_to_existing` | **Silent `pass`.** It is CALLED on every MERGE (line ~47), so **every merge silently loses provenance** — violating the explicit design requirement that every node carry Source/Edition/Date/Confidence. |
| A5 | `src/translation/colibri_kernel.cpp:238` | `thought.confidence = 0.5;` hardcoded whenever the provider returns no logprobs. Groq likely never returns them ⇒ **confidence is probably ALWAYS the constant 0.5**, so every confidence-driven escalation/conflict decision runs on a constant. (Comment ironically reads "Strict constant removal of false mathematical mock" while being exactly that.) |

### HIGH — non-functional / dead
| # | Location | Problem |
|---|---|---|
| B1 | `python/librarian.py:8-9` | Imports `STORAGE.database` and `PROCESSING.pdf_processor` — **modules that do not exist**. The Librarian (the entire retrieval organ) **cannot even import**. |
| B2 | `python/harvester.py:130-133` `_evidence_reflection` | Silent `pass`, but **prints a message claiming it evaluated impact**. Pretends to work. |
| B3 | `src/dormant/` (`homology.cpp`, `boundary_matrix.cpp`) | **Referenced nowhere** outside itself, yet compiled into the binary. Dead weight — matches the docs' own "a Betti number nobody reads is not worth computing." **Construction 2 now gives it a real consumer** (persistence → consolidation), so: wire it or drop it from the build. |

### MEDIUM — correctness/quality
| # | Location | Problem |
|---|---|---|
| C1 | `python/canonicalizer.py:63-82` `_fetch_local_candidates` | "Crude filter": naive word-overlap on titles + arbitrary `LIMIT 50`. Misses synonyms — the exact job it exists to do. **Now fixable properly: FIX-1 gives real 384-d embeddings, so use cosine similarity.** |
| C2 | `src/core/semantic_skill.cpp:126` | Hardcoded **95% energy threshold** for rank truncation; mandate was an ε-configurable dynamic rank. |
| C3 | `include/mos/math/algebra.hpp:43` | Stale doc comment claims "Jacobi Eigenvalue Algorithm"; code correctly uses `Eigen::SelfAdjointEigenSolver`. Doc lies about the code. |
| C4 | `include/mos/translation/colibri_kernel.hpp` | Declares hand-rolled `extract_json_value/extract_json_array` though the `.cpp` now uses nlohmann. Likely vestigial — verify and remove. |
| C5 | `src/core/semantic_skill.cpp:89-103` | Fused-covariance `U_exact`/`W` construction unverified for exactness — needs a numerical unit test vs dense `(P₁+P₂)⁻¹`. |

### Decisions
- ✅ **D1 (decided 2026-07-22): WIRE `src/dormant/*` to consolidation.** Persistent homology gets its real consumer at last: which module-coalitions/concept-cycles survive long enough to be promoted into the permanent scaffold. No longer dead code.
- ⏳ **D2 (pending explanation):** `colibri_kernel.cpp:238` fake `confidence = 0.5`.
- ✅ **D3 (decided 2026-07-22): FOLD ALL PYTHON SCRIPTS into the Python-as-subcomplexes reformulation (Phase 5).** Not just `librarian.py` — every legacy script (`librarian`, `canonicalizer`, `harvester`, `context_manager`) becomes a module-vertex of the coarse complex `K` with a defined stalk, rather than being patched in place. The missing `STORAGE`/`PROCESSING` modules get rebuilt as part of that reformulation, not as a separate repair.

## 5c. FIX BATCH APPLIED (2026-07-22) — build verified, exit 0

**New reference implementations (Python 3.11, tested):**
- `python/coherence.py` — **authoritative implementation of ρ** (Construction 2/2b). Sheaf Laplacian v1 (identity restriction maps ⇒ graph Laplacian quadratic form), Anderson–Morley normaliser `B = max(d_u+d_v)` so `ρ∈[0,1]` needs **NO eigendecomposition**; per-edge diagnostics (`worst_edge()` = the guilty coalition to aim RESOLVE at); `b₀` via union-find; `spectral_modes()` for diagnostics only. **Guards implemented:** `|E|=0 ⇒ ρ=None (UNKNOWN)` — never `confidence=1`; `‖X‖=0 ⇒ UNKNOWN`; mixed dimensions ⇒ raises (never pads). Self-test verified all 5 cases incl. ρ∈[0,1] over 500 random trials (max 0.71). **This is the spec the C++ should port once the coarse complex K exists there.**
- `python/precision.py` — Expected Precision via **similarity-weighted k-NN over logged `(query_embedding, ρ)` pairs**. No training, no GPU, no API cost. Verdicts: COMPETENCE / **KNOWN_IGNORANCE** ("I'm confident I don't know this") / **HALLUCINATION_RISK** (predicted agree, didn't — alarm) / UNDERESTIMATED / COLD_START. Cold start returns None, never a guess. Self-test verified all four verdicts (hallucination case: calibration error 0.81).

**Honesty purge — fabrications removed:**
- `librarian.py` `_cmd_inspect` — fabricated telemetry (87%/342/56) ➜ `not_implemented`, reports nothing rather than inventing numbers.
- `librarian.py` `_cmd_reorganize` — invented file moves ➜ `not_implemented`, empty changes.
- `librarian.py` `learn`/`repair` — false success claims ➜ `not_implemented`.
- `harvester.py` `_evidence_reflection` — printed "Evaluating impact…" then `pass` ➜ now states it did NOT evaluate.
- `canonicalizer.py` `_add_provenance_to_existing` — silent `pass` losing provenance on EVERY merge ➜ **actually implemented** (reads, appends to a JSON source list, writes back); failures reported loudly to stderr.

**D2 RESOLVED — and it was worse than first reported.**
`compute_variance(c) = -ln(c)`, and `curator.cpp:54` feeds `AgentThought.confidence` straight into **D, the isotropic noise floor of every stored `SemanticEmbedding`**. Since the hardcoded `0.5` branch is the one that actually runs against Groq, **every concept ever stored received the identical variance D = -ln(0.5) = 0.693** — the whole Bures–Wasserstein/Woodbury geometry was computing against a constant.
Fix: `AgentThought::confidence` is now `std::optional<double>`; colibri sets it ONLY from real logprobs and otherwise `.reset()`s it; `compute_variance` takes the optional and, when empty, uses a **named, warned, transitional** `UNCALIBRATED_VARIANCE_PRIOR = 1.0` (deliberately humbler than the old hidden 0.5) instead of a silent fabrication. Retired once ρ-based confidence is wired.

**Smaller fixes:** `algebra.hpp` doc no longer claims a Jacobi algorithm the code doesn't use; `semantic_skill.cpp` bare `0.95` ➜ named `SPECTRAL_TRUNCATION_EPSILON = 0.05`; `test_colibri.cpp` updated for the optional.

**C1 answered:** Groq DOES document `logprobs` / `top_logprobs` (0–20) on chat completions — but verify empirically with one real call before trusting it, since Groq documents some OpenAI params it doesn't fully populate. Either way ρ remains the primary signal (self-reported confidence is miscalibrated).

### GROQ_API_KEY live (2026-07-22) — and a landmine found + defused
- Key verified working: real call to `llama-3.1-8b-instant` returned 200.
- **C1 CLOSED empirically (docs were misleading):** requesting `logprobs` on `llama-3.1-8b-instant` returns a **hard 400** ("logprobs is not supported with this model"), not a silent omission. `colibri_kernel.cpp:175` was unconditionally sending `req["logprobs"]=true` on every `generate_thought()` call — **this would have broken every single reasoning call against the model we actually use.** Removed. Confidence from this provider/model pair is now permanently UNKNOWN by design, not by fallback — reinforces Construction 2b (ρ as primary signal) as necessary, not optional. Rebuilt clean, exit 0.

## 5d. LIVE π TEST + AUDIT (2026-07-22) — first real end-to-end evidence

`python/smoke_test_pi.py` added (reusable; ~3 Groq calls). **π WORKS: 3/3.** Notably the kernel behaviour from the design docs is REAL — "then come here so we can make out" appeared in **zero** nodes; the joke mapped to ker(π) exactly as intended.

**Bugs found by the live test (all fixed):**
| # | Sev | Finding |
|---|---|---|
| F1 | 🔴 | **DAG direction inverted.** `kernel.cpp:122` does `add_dependency(self, child)` and `operad.cpp` runs `in_degree==0` first ⇒ children run AFTER. The model emitted a *decomposition* tree (children = prerequisites), so **COMPUTE ran before the CONTEXT it depends on**. Fixed by making execution-order semantics explicit in the π system prompt. |
| F2 | 🔴 | **`support` returned as STRINGS** (`["CP^3","Fubini-Study metric"]`) but serializer calls `PrependInt32` and C++ wants `std::set<int>` ⇒ **serializing any MATH DAG would crash**. Architecturally the LLM cannot know internal vertex ids. Fixed: prompt forces `support: []`; serializer drops non-integers loudly. **Name→id resolution is still unbuilt (open).** |
| F3 | 🟠 | **No RESPOND node ever emitted** ⇒ a perfect execution returned nothing to the user. Prompt now requires exactly one terminal RESPOND. |
| F4 | 🟠 | **Disconnected forest** (nodes 3,5,7,9 parentless) ⇒ uncontrolled parallelism, no ordering. Now rejected by the validator. |
| F5 | 🟡 | **Hallucinated constraints marked RIGID** — emitted `"Metric signature": "(4,2)"` for Fubini–Study, which is **mathematically false** (FS is positive-definite; real 6-manifold ⇒ (6,0)). RIGID = hard subspace projection, so this injected a false axiom as unbreakable truth. Prompt now: RIGID only for user-stated constraints, everything inferred is FLUID, never invent numeric facts. |
| F6 | 🔴 | **Groq JSON mode requires the literal word "json" in the messages** — the rewritten prompt dropped it ⇒ every call 400'd. |
| F7 | 🔴 | **API errors returned `{"type":"NOISE"}`** ⇒ an API failure was indistinguishable from "user said something non-mathematical"; every failed math query silently routed to chat and looked fine. Now returns `{"type":"ERROR", "reason":...}`. |

Added `Communicator.validate_dag()` — checks duplicate ids, dangling children, **cycles** (DFS colouring), presence of terminal RESPOND, and **connectivity**. Malformed DAGs are refused at the boundary (`type: INVALID`) rather than shipped to a C++ engine that trusts whatever it receives.

**After fixes, π emits well-formed chains:** `CONTEXT→CONTEXT→CONTEXT→COMPUTE→REASON→RESPOND`, contexts as parents, constraints FLUID, validation CLEAN, 3/3 smoke cases pass.

## 5e. VISUAL DEBUGGER (2026-07-22) — `python/visualize.py`

Self-contained HTML (no CDN/deps beyond numpy) rendering a *sequence of snapshots* of the coarse complex: vertices=modules, edges thicker+redder with ω_e, dashed red = worst edge ("RESOLVE here"), component tinting so **fragmentation is visible at a glance**, and ρ/confidence/b₀/status per frame with UNKNOWN shown honestly as UNKNOWN. Arrow keys step through evolution.

**It immediately earned its keep by finding a bug in `coherence.py`:** `worst_edge()` used a bare `max()`, which returns an arbitrary first element even when EVERY ω_e is 0 — so a perfectly coherent frame still displayed "◀ RESOLVE here", pointing resolution at a non-existent conflict. Fixed with a tolerance guard returning None. *Numbers hid it; the picture exposed it — which is precisely the argument for having a visual sense.*

## 5f. MIGRATION SUBSTRATE BUILT (2026-07-22) — `python/module_vertex.py`

This is what "the Python scripts become subcomplexes" concretely means: a script is not rewritten, it is given **coordinates**.

- **`ModuleVertex`** (ABC): a cognitive organ occupying one vertex of `K`. Holds a *fine complex* of `Concept(label, vector, weight)`; exposes `stalk()` = the coarse-graining map **π_v = weight-weighted centroid** of its active concepts (Construction 2, v1); declares `operators()` = its share of 𝔇. **`stalk()` returns None when idle, NOT a zero vector** — an idle module has no position, and a zero vector would silently drag every distance toward the origin and fake a measurement. Concept dim mismatch ⇒ raises (never pads).
- **`CoarseComplex`**: holds `weights w(σ,t)`, Hebbian `co_activate()` (fire together ⇒ wire together), `tick_decay()` (idle collapse = garbage collection), `is_bound()`/`edges()` (1-simplices = pairs past the bind threshold), `states()`, `report()` (→ ρ via coherence.py), `snapshot()` (→ visualize.py). Uses **bind/collapse/split/merge**, deliberately NOT "Pachner moves". Every structural change is written to a `mutation_log`.

**Verified end-to-end:** idle ⇒ UNKNOWN(empty) → active-but-unbound ⇒ UNKNOWN(no_edges) → two binds ⇒ coherent + FRAGMENTED flagged → Curator contradicts ⇒ **ρ=0.333, worst edge correctly = ('Canonicalizer','Curator')** → idle decay ⇒ coalitions collapse back to UNKNOWN. Mutation log records every bind/unbind. **This is learning-as-topology running for real.**

⚠️ **NEW CALIBRATION FINDING (important):** ρ's practical dynamic range is compressed at high dimension. With 384-d vectors `‖X‖²_F ≈ 1536`, so a real disagreement of ω=0.14 gives ρ≈4.6e-5, while an antipodal contradiction gives ρ=0.333. **ε is therefore NOT ~0.5 — it will be orders of magnitude smaller and MUST be calibrated empirically** against the observed ρ distribution on real runs before the RESOLVE/EXPLORE gate can be trusted. Do not hardcode a threshold before measuring.

## 5g. STORAGE LAYER REBUILT + LIBRARIAN MIGRATED (2026-07-22)

**`python/storage.py`** — rebuild of the missing `STORAGE.database`, written against the EXACT interface extracted from the legacy call sites (13 `self.db.*` methods, 14 tables). Full schema incl. `semantic_nodes`, `concept_embeddings`, `n_ary_relations` (**= the simplices**), `graph_mutations` (audit trail of typed structural ops), `ingestion_queue`, `working_memory`, category graph, papers/bridges. Thread-safe (`RLock`, `check_same_thread=False`). **Rules enforced:** empty DB returns **zeros, never invented numbers** (contrast the old `_cmd_inspect`); provenance is a JSON list so merges accumulate sources; `insert_concept_embedding` **RAISES** on dimension mismatch (verified: refused a 128-d vector). Self-test passes.

**`python/pdf_processor.py`** — rebuild of the missing `PROCESSING.pdf_processor`. Streaming page-by-page extraction (a 1000-page book never sits in RAM at once — critical at 5.9 GB). pdfplumber with pypdf fallback; 1-indexed pages; empty pages are emitted rather than skipped so numbering stays truthful. **Verified on FIRST DRAFT.pdf: 10 pages, 12,931 chars.** (Also fixed a Windows `cp1252` crash printing U+2011 from typeset PDFs.)

**`librarian.py` MIGRATED to a ModuleVertex** — the first organ given coordinates. `IntelligentLibrarian(ModuleVertex)`, `name="Librarian"`, `operators() = [SearchOp, scavenge_internet, ingest_document, curate_search]`. New `hold_evidence()` embeds retrieved text locally (free) into its fine complex, wired into `curate_search` so retrieval weight becomes concept weight ⇒ **π_v tracks what the Librarian is genuinely holding.** Imports fixed (`storage`, `pdf_processor`); `harvester.py` import fixed to `canonicalizer`. **It now imports and runs — previously impossible.**

## 5h. INTEGRATION DEMO ON REAL CONTENT — `python/integration_demo.py`

Drives the whole stack (pdf_processor → embeddings → module_vertex → coherence → visualize) with actual FIRST DRAFT.pdf text:

| frame | ρ | |
|---|---|---|
| both organs on the same section | **0.0000** | perfect agreement |
| Verify on a related subsection | **0.0605** | mild, honest disagreement |
| **Verify goes off-topic (lemon cake)** | **0.1408** | **2.3× spike**; worst edge correctly `('Reason','Verify')` |
| back on task | **0.0605** | resolved |
| idle decay | **UNKNOWN** | coalitions collapsed |

✅ **CORRECTION to the §5f calibration warning.** That warning was based on *synthetic random* vectors. With **real normalized embeddings** ρ's dynamic range is perfectly usable — roughly 0.00 / 0.06 / 0.14 across agreement / related / off-topic, so **ε ≈ 0.1** is a sensible starting threshold. Still calibrate on more real runs, but the earlier "orders of magnitude smaller" concern does NOT apply to real data.

## 5i. D3 COMPLETE — ALL FOUR ORGANS MIGRATED + LIVE LOOP (2026-07-22)

**`python/router.py`** — the remote brain, rebuilt to the legacy `query_frontier_brain(prompt, context, intent)` interface. Implements the **tiered-brain strategy** from the budget analysis: `intent∈{triage,classify,extract,canonicalize,route}` → **8B** (cheap/high-frequency), everything else → **70B** (`llama-3.3-70b-versatile`, also free). Async via `asyncio.to_thread` so the event loop stays free. Per-process `Budget` tracking (requests/tokens/by-model). **Errors RAISE (`RateLimited`/`RouterError`) rather than returning empty content** — a rate-limit must never be mistakable for "the model had nothing to say". Verified live: both tiers respond, 70B confirmed free.

**All four organs are now vertices of K:**
| Organ | Class | Operators (its share of 𝔇) |
|---|---|---|
| Librarian | `IntelligentLibrarian` | SearchOp, scavenge_internet, ingest_document, curate_search |
| **Canonicalizer** | `Canonicalizer` | **merge, link, insert_node, log_mutation** — *special: these MUTATE the topology itself* |
| Curator | `KnowledgeCurator` | digest, evaluate_acquisition, extract_objects, promote_to_scaffold |
| WorkingMemory | `ContextManager` | update_state, get_context_block, inject_boundary, drop_boundary (+ `sync_stalk()`) |

**`python/console.py`** — project-wide fix for a recurring Windows crash: cp1252 cannot encode Δ, ρ, ω or the U+2011 hyphens in typeset PDFs, so *printing mathematics killed the process*. `console.setup()` forces UTF-8. This had already crashed the PDF test and the router test.

**`python/live_demo.py` — the loop running on real content, at $0:**
```
[1] 4 organs registered as vertices of K
[2] streamed 10 pages of FIRST DRAFT.pdf
[3] Librarian+WorkingMemory bound  -> rho=0.1210  V=2 E=1 b0=1
[4] all four active                -> rho=0.0761  V=4 E=3 b0=1
    worst edge: ('Canonicalizer','Curator')
[5] 70B reasoning on the real excerpt: correctly identified self-adjointness,
    the L^2 domain, and the spectrum as the three things needing establishment
[6] after idle decay               -> rho=UNKNOWN (no_edges)
[8] budget: 1 request, 1070+162 tokens
```
⚠️ **Observation worth understanding:** ρ went DOWN (0.1210→0.0761) as organs were added. This is correct — adding a well-aligned organ raises ω but raises the normaliser `B·‖X‖²_F` more, so overall discord dilutes. **ρ is therefore NOT monotonic in the number of active organs**, and comparisons across different-sized complexes must be made with care.

✅ Evidence for the retrievable-core thesis: the 70B answer on the real excerpt was mathematically sound.

## 5j. K + ρ PORTED TO C++ (2026-07-22) — with parity tests

**`include/mos/core/coarse_complex.hpp` + `src/core/coarse_complex.cpp`** — the coarse complex K now exists engine-side.
- `ModuleId` vertices, canonical `CoarseEdge` 1-simplices, `std::optional<Eigen::VectorXd>` stalks (**idle = no stalk, NEVER a zero vector**).
- Hebbian `co_activate()`, `tick_decay()` with bind/unbind/collapse, `mutation_log()` audit trail.
- `CoherenceReport` with **`std::optional<double> rho`** — empty means genuinely UNKNOWN, which is the type system enforcing the guard rather than a sentinel value.
- Same maths as the Python reference: ω = Σ‖x_u−x_v‖², Anderson–Morley `B = max(deg u + deg v)`, ρ = ω/(B·‖X‖²_F), **no eigensolver in the fast path**. b0 by union-find. `worst_edge()` returns empty below tolerance (the phantom-RESOLVE bug is fixed in BOTH implementations).
- Guards ported: `|E|=0 ⇒ no_edges/UNKNOWN`, `‖X‖=0 ⇒ zero_state/UNKNOWN`, dimension mismatch ⇒ **throws**.

**`tests/test_coarse_complex.cpp`** (target `mos_coarse_complex_tests`) — 8 tests, ALL PASS:
✅ **PARITY CONFIRMED: C++ ρ = 0.2500 exactly matches python/coherence.py** on the identical configuration. Also verified: no-edges ⇒ UNKNOWN; fragmentation b0=2; idle organ excluded (not zero-filled); dimension mismatch refused; decay collapses coalitions; ρ∈[0,1] over 500 random trials (max 0.721).
**Policy: if the two ever disagree, `python/coherence.py` is authoritative and the C++ is wrong.**

## 5k. VERIFYOP GROUNDED (2026-07-22) — the promotion gate closes

**`verify/check.py`** — the external oracle. Sandboxed sympy checker invoked as `python <abs-path> <spec.json>`, matching VerifyOp's existing security whitelist (no `-c`, no shell metacharacters, no shell at all — `CreatePipe`). Checks implemented: `symbolic_equal`, `simplify_zero`, `eigenvalues`, `limit`, `derivative`. Verified live across all outcome states.

🔑 **THREE outcomes, not two** — and this fixed a real epistemic bug in `primitives.cpp`:
| exit | verdict | effect on state |
|---|---|---|
| 0 | VERIFIED | obstruction cleared → state may crystallize |
| 1 | REFUTED | obstruction += 1000 → forced into RESOLVE |
| 2 | **UNVERIFIABLE** | **obstruction UNTOUCHED** |

VerifyOp previously treated *every* nonzero exit as failure, collapsing REFUTED and UNVERIFIABLE together. That is the error of concluding falsehood from inability to check — it would have spiked conflict over the oracle's own blind spots and locked the system in RESOLVE mode over perfectly good mathematics. A checker crash now also returns UNVERIFIABLE, never a refutation. **Absence of proof is not proof of absence.**

This closes the promotion gate that Construction 3 requires: coherence (ρ) governs RESOLVE/EXPLORE; only the external oracle touches truth.

## 5l. 🎯 THE LOOP IS CLOSED (2026-07-22) — ρ measured during real execution

`proto/operad.fbs` extended: `Operator.geometry: [float]` appended (FlatBuffers-safe). Python embeds **every** operator payload locally (free) and ships it across the boundary, so the C++ engine gets a position per organ **without ever deriving meaning from a string** — the adjunction holds.

`OSKernel` now owns a `CoarseComplex coarse_`:
- Each **OpType is a cognitive organ** (CONTEXT/COMPUTE/REASON/RESPOND/VERIFY/SEARCH); its stalk is that operator's payload geometry. **No geometry ⇒ organ stays IDLE and is excluded from ρ** (honest, not zero-filled).
- **DAG adjacency IS cooperation:** parent→child edges `co_activate()` the two organs (Hebbian), so organs that work together bind.
- After `cpp_operad.run()`, `last_coherence_ = coarse_.report()` and the kernel logs ρ, fragmentation, and the guilty edge.

**`python/test_full_loop.py` — VERIFIED END-TO-END:**
```
pi (Groq) -> CONTEXT->COMPUTE->COMPUTE->RESPOND, validation CLEAN
          -> 4 x 384-d local embeddings -> 8188-byte FlatBuffer
          -> IPC (valid CRC32) -> C++ engine
          -> ContextOp injected axiom; ComputeOps ran; RespondOp completed
          -> [OSKernel] coherence: rho=0.1537 confidence=0.8463 omega=1.3834 V=3 E=2 b0=1
          -> highest discord: 'COMPUTE' <-> 'CONTEXT'
```
(V=3 from 4 nodes is correct: organs are per-OpType, so the two COMPUTE nodes share one organ.)

**Build gotcha recorded:** CMake's `build_flatbuffers` did NOT regenerate `build/operad_generated.h` after the schema change, and `#include "operad_generated.h"` resolves to the BUILD copy, not `proto/`. After editing `operad.fbs` you must run:
`./vendor/flatbuffers/flatc.exe --cpp -o build/ proto/operad.fbs` (and `--python -o python/`).

### 🐛 NEW BUG FOUND BY THE LOOP (open)
`[ComputeOp] Failed to generate embedding` — **`ColibriKernel::generate_embedding` POSTs to Groq's `/v1/embeddings`, which Groq does not provide.** Every C++-side embedding call fails, on every invocation. The split-brain decision (embeddings LOCAL and free) is not honoured engine-side; this remote path is vestigial and always-failing. Fix: operators should consume the `geometry` already arriving in the FlatBuffer instead of fetching embeddings remotely. (The loop still completes because the failure is handled, but any C++ path depending on embeddings is dead.)

### Two transient/robustness notes
- A one-off `SSLError` to api.groq.com occurred and then cleared (OpenSSL 1.1.1u, retry returned 200). Worth a retry-with-backoff in `router.py` eventually.
- The F7 fix proved itself: the SSL failure surfaced as `{"type":"ERROR","reason":"SSLError"}` instead of masquerading as NOISE. Also fixed `pi_morphism` falling through and printing "Identified as rigorous mathematics" over an ERROR payload.

## 5m. COMPUTEOP RESURRECTED + ρ NOW DRIVES THE CONTROLLER (2026-07-22)

**Bug killed — ComputeOp was a total no-op.** `ComputeOp::apply` called `llm_->generate_embedding()`, which hits Groq's non-existent `/v1/embeddings`, threw, and `return false`d — so `apply_flow()` NEVER RAN. Every COMPUTE node in every DAG did nothing while appearing to execute.
Fix: `ComputeOp` and `SearchOp` now take the **locally-computed `geometry`** carried in the FlatBuffer (`OperatorFactory` extracts `op_data->geometry()`), using the remote call only as a legacy fallback that fails loudly. Empty direction ⇒ refuse rather than apply a zero flow "that would look like work".
**Verified:** `"status":"Compute_Success"` now appears where `Failed to generate embedding` used to.

**ρ now DRIVES the two-mode controller** (`CognitiveMode` + `KernelConfig::rho_threshold = 0.10`):
```
[OSKernel] coherence: rho=0.1537 confidence=0.8463 omega=1.3834 V=3 E=2 b0=1
[OSKernel] mode=RESOLVE (rho=0.153707 > eps=0.1): organs disagree; reconcile before expanding.
[OSKernel]   aim resolution at 'COMPUTE' <-> 'CONTEXT' (omega_e=0.819743)
```
- ε=0.10 is **empirically calibrated**, not guessed: real 384-d embeddings gave agreement≈0.00, related-but-distinct≈0.06, off-topic≈0.14 (§5h).
- **THREE modes, not two.** When ρ is undefined the mode is `UNKNOWN` — the controller explicitly refuses to default to EXPLORE, because "no measurement" is not "everything is fine". That conflation is precisely what the `|E|=0` guard exists to prevent, and it would have been trivially easy to reintroduce here.
- Fragmentation (b0>1) is warned separately: a coherence claim over a fragmented complex is only LOCAL.

### 🐛 NEXT GAP EXPOSED (open): the FINE complex is never populated
`"delta_strain": 0.0` on both COMPUTE nodes. The flow now genuinely runs, but the underlying `CognitiveState` math complex has **no concepts for it to act on**, so `calculate_conflict_score()` stays 0.0 and the Banach state never moves. Currently only the COARSE organs get positions (from operator geometry); the fine level — the actual concept complex `C_math` where Construction 2's `π_v` is supposed to coarse-grain FROM — is still empty during execution. ρ over K is real; the fine-level state underneath it is not yet alive. This is the next structural piece.

## 5n. THE FINE COMPLEX IS ALIVE (2026-07-22) — the gap from §5m closed

**Root cause confirmed:** `ContextOp` (via `inject_temporary_axiom`) was the ONLY operator that ever inserted a vertex into `math_complex_`/`math_sheaf_`. `SearchOp` only grew the complex when the knowledge base had hits (empty KB today, since nothing's been consolidated yet); `ComputeOp` and `ReasonOp` never grew it at all. `apply_flow()` needs ≥1 concept vertex to act; `calculate_conflict_score_internal()` needs **≥2** to report anything but a trivial 0.0 — so with only the single CONTEXT axiom present, `delta_strain` was mathematically guaranteed to read 0.0 regardless of whether ComputeOp "worked."

**Fix — new `CognitiveState::grow_concept(label, geometry)`** (`cognitive_state.hpp`/`.cpp`): the organic-growth path, deliberately **distinct** from `inject_temporary_axiom()`. Axioms are transient boundary conditions that perturb `P_`/`fluid_center_` and get dropped at turn-end; a grown concept is a **permanent** addition to `C_math` with no such perturbation. Uses a named `GROWN_CONCEPT_VARIANCE_PRIOR = 1.0` (not a fabricated near-zero "certain axiom" value — an inferred concept is not a stated fact). Dimension mismatch **throws**, consistent with the rest of the geometry contract.

Wired into all three operators that produce reasoning:
- `SearchOp` — grows a concept from the **query itself** after the retrieval loop, so an empty-KB search still leaves a trace of what the system was pursuing (previously: zero trace if nothing matched).
- `ComputeOp` — grows a concept from its `logic_code_`/geometry **before** `apply_flow`, so the flow has real multi-point state to act on.
- `ReasonOp` — now takes geometry too (factory updated); grows a concept from its `premise_`, preferring local payload geometry over `thought.latent` (which is typically empty against Groq, which serves no embeddings).

**Verified — before/after on the identical query:**
```
BEFORE: "delta_strain": 0.0                    (both COMPUTE nodes — state never moved)
AFTER:  "delta_strain": 0.20222876965999598    (1st COMPUTE: complex grows 1->2 concepts)
        "delta_strain": -0.08106337688893961   (2nd COMPUTE: RK4 flow pulls conflict back down)
```
Non-zero, non-fake, and the sign flip is the expected physical behaviour: `apply_flow`'s deductive gradient descent pulling the state back toward coherence after a structural jump. `mos_coarse_complex_tests` and `mos_kernel_tests` re-verified clean — no regressions.

**Honest residual gap:** the coarse-level π_v (Construction 2's promise that a module's coarse position is the weighted centroid of ITS fine complex) is still not wired — the coarse organs currently get their position directly from operator payload geometry, not by summarizing `C_math`. Coarse ρ and fine-level conflict are both real now, but not yet the SAME measurement at two granularities as the two-level design intends.

## 5o. THE RESIDUAL GAP CLOSED — π_v is real (2026-07-22)

The two-level design is now genuinely two-level: a coarse organ's position is the **precision-weighted Gaussian fusion of its OWN fine complex**, not a borrowed payload embedding.

**Math (derived, not asserted):** treat organ v's concepts as independent Gaussian estimates N(μ_i, Σ_i), Σ_i = U_iU_iᵀ + D_iI, of one underlying "what this organ believes". The max-likelihood fused mean is the information-form solution
`π_v = (Σ Σ_i⁻¹)⁻¹ (Σ Σ_i⁻¹ μ_i)` — each concept pulls π_v toward itself in proportion to its PRECISION (small D ⇒ dominates). This is the n-way, NON-DESTRUCTIVE generalisation of `merge_with`'s pairwise Woodbury fusion.

**Impl — `core::fuse_concept_means()`** (`semantic_skill.hpp/.cpp`), pure & shared:
- **Isotropic fast path (EXACT):** all U empty (current reality of every grown concept) ⇒ scalar precision-weighted average, O(n·d), no inversion.
- **General path (EXACT):** low-rank via Woodbury per term into a dense information matrix, one solve. O(n·d·k + d³).
- **D-floor (1e-6):** a near-certain axiom (D~eps) strongly but not infinitely pins π_v — prevents 1/eps≈1e16 numerical blow-up.

**Wiring:** concepts are now tagged by organ. `grow_concept(label, geom, organ)` and `inject_temporary_axiom(..., organ)` push into `organ_concepts_`; the 4 operators pass their OpType name (SEARCH/COMPUTE/REASON/CONTEXT). After execution, `OSKernel::execute_dag` calls `state_.compute_pi_v(organ)` for each organ and **overwrites the coarse stalk** with π_v (organs that grew nothing keep their payload position). So coarse ρ and fine-level geometry are now ONE measurement at two resolutions.

**Tests — `mos_pi_fusion_tests` (all pass):** equal precision → plain mean; 9:1 precision → pulled to the certain concept; **order-independence** (maxdiff 0); D-floor keeps a 1e-300 axiom finite (→0.999999); **low-rank Woodbury path matches a dense ground-truth solve to 2.2e-16**. Coarse-complex regression still green.

**End-to-end proof it's genuinely fine-derived (not payload-copy):** on the identical query, coarse ρ moved 0.1537 → **0.1056** and the guilty edge moved COMPUTE↔CONTEXT → **COMPUTE↔RESPOND**, because COMPUTE's position is now the fusion of the 2 concepts it grew, not its single payload embedding.

**Honest note / follow-ons (not done, low priority):** (1) the O(1) incremental information-filter accumulator was modelled but NOT implemented — on-demand fusion is O(n) and n is tiny (<10/DAG), so it's not worth the state-management complexity yet; (2) the exponential-forgetting factor γ and its unification with coarse `decay_rate_` is modelled but unwired; (3) the H(Σ_v*) "internal spread vs cross-organ discord" 2×2 diagnostic is available for free (entropy code exists) but not surfaced. These are enhancements, not correctness gaps — π_v itself is exact.

### STILL OUTSTANDING (honest status)
- ~~**ρ is NOT wired into C++**~~ **STALE — resolved by §5j.** `K` + ρ live in C++ ([`coarse_complex.hpp/cpp`]); `OSKernel` holds a `CoarseComplex coarse_` and calls `coarse_.report()` in `execute_dag`. `coherence.py` remains the tested SPEC/ORACLE (parity policy), not the runtime.
- **D1 (dormant→consolidation)** — decided, but needs `K` + persistence to exist first. Not yet wired.
- **D3 (fold ALL python into subcomplexes)** — decided; the largest remaining item. Do ONE VERTEX AT A TIME, starting with the Librarian (Friday depends on it).
- **`GROQ_API_KEY`** still unset ⇒ no end-to-end run yet.
- Unverified: `semantic_skill.cpp` fused-covariance exactness (needs a numerical test vs dense `(P₁+P₂)⁻¹`); vestigial hand-rolled JSON helpers in `colibri_kernel.hpp`.

## 5p. PLAN — the four computational-neuroscience mechanisms (2026-07-24)

Charbel's three §0 comments ("why isn't the topology making it *smarter*; why is modelling neural computation a fool's errand; why aren't we doing real research on what we have") were handled, and resolve to ONE move: **stop using the sheaf only DIAGNOSTICALLY (role 1: it scores a process happening in the LLM) and promote it to CONSTITUTIVE (role 2: the structure participates in the computation).** §0's "not smarter" was right about the LLM's per-*inference* IQ (bounded by Llama, untouched) but wrongly let that collapse into "the structure only watches." Sister's thesis — *intelligence is the quality+structure of connections, not neuron count* — is a claim about SYSTEM-level competence, and its formal home is the **restriction maps** `F_{v⊴e}` (currently IDENTITY = zero-quality connections; with identity maps on a connected graph the reconciled state is just the plain AVERAGE of organs → no knowledge in the wiring). "Fool's errand" was about the *implementational* level (biophysics); the *organizational/connectomic* level is exactly what a sheaf models, and modern research cashes it out cheaply.

### The proposition (Charbel's)
A fractal, struggle-driven simplicial solver: **struggle = a persistent obstruction** (ρ won't fall / `H¹≠0`); the **obstruction cocycle names the cell to attach** (kill an `H¹` class by coning); an **aimed** LLM sample fills the new cell; VerifyOp gates; survivors are promoted (δ𝔇). "Fractal" = a **scale-invariant growth rule on a recursively nested (operadic) complex** (honest sense), NOT literal Hausdorff-dimension geometry (rejected). The one-sentence "next level": **promote the complex from a coherence-SCORER to an adaptive SEARCH CONTROLLER** that detects struggle as obstruction, reads the cocycle as a blueprint, spends the scarce Groq sample precisely at that cell, verifies, and promotes — same rule self-similarly at every level. This does NOT raise Llama's IQ; the "spark" is a trajectory found by SEARCH, and the shape of the search is what the growing structure controls (the honest, unfaked way it touches "how the LLM gets sparks").

### The four comp-neuro mechanisms ARE the four structural moves, seen functionally
| Comp-neuro principle | = structural move | what the neuro framing ADDS |
|---|---|---|
| **① Predictive coding** | diffusion + restriction maps | the **local learning rule** `ΔR = −η·π·ε·xᵀ` (rank-1 Hebbian, Oja-stabilised, no backprop) — fills the "how to learn R at $0" gap; + **precision-weighting** of ω |
| **② Criticality / SOC** | the ε threshold + persistence | a **self-tuned setpoint** (branching ratio σ→1) — kills hardcoded `rho_threshold=0.10` |
| **③ Homeostatic plasticity** | persistence / growth trigger | an **integrated-deviation trigger** (thrash-proof) — kills flat `decay=0.1` |
| **④ Selectionism** (Edelman) | the attachment / search-controller | **variation** (k candidates) + verify-selection + δ𝔇 promotion |

**Math anchors.** ① PC free energy `F = Σ_e π_e‖ε_e‖²` with `ε_e = (δx)_e = R_{u,e}x_u − R_{v,e}x_v` **is** precision-weighted ω; inference = `ẋ=−Lx` (sheaf diffusion); learning = `∂F/∂R = 2π_e ε_e x_uᵀ`. Exact for the *symmetric/reciprocal* PC variant (= Edelman "reentry"); textbook directed PC is the special case. ② σ = mean binds triggered per co-activation; σ≈1 → scale-free avalanches, max dynamic range (Beggs–Plenz, Kinouchi–Copelli). ③ Butz–van Ooyen: `dz/dt = ν(a* − a(t))`, growth ∝ deviation from setpoint. ④ variation→selection→amplification; fitness = VerifyOp when available else Δρ (Δρ ALONE must never promote — coherent-but-wrong).

**The headline win (for someone who rages at magic numbers):** ①②③ collapse the **three** hand-set constants `rho_threshold=0.10`, `bind_threshold=1.0`, `decay=0.1` into **ONE homeostatic setpoint**, and criticality tells us where to put it. The system stops being parameterised by guesses and self-tunes to a principled operating point.

### Assets the C++ port (§5j–§5o) already gives us
- **Precision already exists:** `fuse_concept_means`/`compute_pi_v` compute with per-concept precisions (`D`/`Σᵢ`); PC's precision-weighted ω just wires them into the edge sum — no new infra.
- **Fine-level PC inference already exists:** `apply_flow`'s RK4 descent on conflict IS diffusion-as-inference at the fine level (§5n). The addition is doing it at the COARSE level with the sheaf `L` and learned `R`.
- **The obstruction locator already exists but is DISCARDED:** `kernel.cpp:218–233` computes RESOLVE mode + `worst_edge()` and only PRINTS them. The search-controller consumes that.

### Implementation division (CONFIRMED 2026-07-24)
Engine is C++; `coherence.py` is the tested SPEC/ORACLE for the ρ-measure only (§5j parity policy: if they disagree, coherence.py wins, C++ is wrong).
| Mechanism | Primary site | coherence.py spec-dance? |
|---|---|---|
| ① Predictive coding | `coarse_complex.cpp` (measure) | **Yes** — spec in `coherence.py` + keep `test_coarse_complex` parity green |
| ② Criticality setpoint | `coarse_complex.cpp` / `kernel.hpp` | No (control logic, C++-native) |
| ③ Homeostatic trigger | `CoarseComplex` integrator + `kernel.cpp` RESOLVE branch | No |
| ④ Selectionism | attachment loop at `kernel.cpp` seam | No |
`module_vertex.py` = reference testbed, not a build target.

### The unified RESOLVE policy (cost-ordered)
1. **Cheap first — diffuse (①):** reconcile with info already in the organs (sparse matvec, free).
2. **Expensive only if that fails — attach (④):** spend k aimed Groq samples at `worst_edge`, VerifyOp-select, promote/decay. Homeostasis (③) gates this on *integrated* deviation, not one-tick ρ, so we never pay for a transient spike.

### Sequence (CONFIRMED: PC keystone first)
1. **① PC layer** — precision-weight ω + local Hebbian `ΔR` learner (Oja); spec in `coherence.py`, port to `coarse_complex.cpp`, parity test. *Free CPU.* Subsumes/justifies diffusion + restriction maps.
2. **③ Homeostatic trigger** — leaky-integrated deviation-from-setpoint for grow/retract; gate attachment on it. *Free.*
3. **② Criticality setpoint** — self-tune ε toward σ≈1 at the **fine** level (N large enough to mean anything; the 6-organ coarse level uses empirical-quantile ε meanwhile). *Free.*
4. **④ Selectionism** — k-variant attach + verify-select + δ𝔇 promotion; **k budget-gated** (start k=1 = today; raise to 2–3 as budget allows; paraphrase-perturbation for cheap variance). *Costs Groq — last.*

### What this does NOT buy (honesty)
- Does NOT raise Llama's per-call IQ; ④'s samples are aimed+rationed, not smarter.
- Diffusion reconciles, never manufactures a true fact; VerifyOp stays the sole truth gate.
- **All four are SLOPE mechanisms** — day 1 they degrade to today's behaviour (identity maps, fixed ε, reactive trigger, k=1). Same bet as the whole project: earn on accumulation, not intercept.
- Do NOT feed fake confidence into precision (Groq logprobs are dead, §5c) — precision from ρ̂-history or coalition weight only. Raw Hebb diverges → Oja normalisation mandatory.
- Criticality is contested science; used as an ENGINEERING setpoint (max dynamic range), not a law. Only meaningful where N is large (fine level).

**STATUS: IMPLEMENTED + TESTED 2026-07-24 - see §5q for what landed, test results, and the honest in-engine-vs-spec-only status. Original note kept for context:** plan endorsed; resume at step 1 (① PC layer) when the token limit resets. v2 deferred: the clean cocycle→cell attachment (coning off an `H¹` class) and higher-cell Laplacians (③ frustrated-triangle detection) — build only once v1 aimed-injection is shown to move ρ on real content (per §1: no new math object unless implementation forces it).**

## 5q. 5p IMPLEMENTED + TESTED (2026-07-24) - the four mechanisms are real

All four mechanisms built and green. Authoritative Python spec (5j policy) implements
ALL FOUR; the C++ engine has mechanism (1) ported with parity preserved.

**New / changed files:**
- `python/coherence.py` (extended) - precision-weighted PC free energy `omega = sum pi_e ||R_u x_u - R_v x_v||^2`; optional restriction maps + precision; `sheaf_diffusion()` (role-2 inference: descends omega to the reconciled section). **Identity+pi=1 is byte-identical to pre-5p** (test 6 asserts it) so 5h calibration + C++ parity hold. Contract: ORTHOGONAL maps (warns to stderr, never silently clamps, if `rho_raw>1`).
- `python/predictive_coding.py` (NEW) - `RestrictionMapLearner`: local Hebbian `dR = -eff * eps x^T / ||x||^2` + polar retraction to O(d). Solves the "$0 learn-the-maps" gap. **Audit bug found + fixed:** raw coupling weight as precision made `lr*precision` huge -> divergence; now the effective step is capped at `max_step=0.5` (guaranteed monotone descent). Note: polar retraction is an O(d^3) SVD per update - fine for the coarse complex, NOT for high-frequency fine-level use.
- `python/plasticity.py` (NEW) - `Homeostat` (3): leaky-integrated per-organ discord vs setpoint; a transient spike does NOT trigger growth, sustained discord does (tested). `CriticalityMonitor` (2): auto-calibrates the RESOLVE gate epsilon as the q-quantile of observed rho (kills hardcoded 0.10); sigma branching-ratio decay controller (documented underpowered at 6-organ coarse level - belongs at fine level).
- `python/selection.py` (NEW) - `select_best` (4): REFUTED never promoted; VERIFIED beats UNVERIFIABLE even if it raised discord (truth > coherence); delta_rho alone never promotes past a possible verification.
- `python/module_vertex.py` (extended) - `CoarseComplex` holds a `RestrictionMapLearner`; `use_learned_maps`/`use_precision` flags **default OFF** (cold start = pre-5p behaviour); `learn_coherent_pairs()` learns only from low-discord pairs (training on a contradiction would teach the maps to HIDE it).
- `python/test_5p_integration.py` (NEW) - all four composed. **Money shot:** PC maps collapse a FALSE conflict (same content, rotated frame: 1.96 -> 0.00) while a REAL conflict (off-topic) survives untouched (2.14 -> 2.14). Identity maps cannot do this - it is the "quality of connection" thesis, measured.
- `include/mos/core/coarse_complex.hpp` + `src/core/coarse_complex.cpp` (extended) - **mechanism (1) ported to the engine**: `set_restriction()`, `set_use_precision()`, precision-weighted omega + weighted Anderson-Morley B. Default path (no maps, pi off) is byte-identical.
- `tests/test_coarse_complex.cpp` (extended) - test 9: precision reweighting moves the guilty edge; identity maps reproduce plain rho exactly.

**Test results (all PASS):**
- Python: `coherence` (incl. backward-compat + [0,1] under 300 random orthogonal maps + diffusion->mean), `predictive_coding` (converges 6.13->0.90, orthogonal to 1e-15, high-precision stable), `plasticity`, `selection`, `module_vertex` (existing test unchanged), `test_5p_integration` (four composed).
- C++: `mos_coarse_complex_tests` 9/9 (rho=0.2500 parity exact; 500 random in [0,1]; precision reweight; identity no-op). `mos_kernel_tests` PASS (no regression). Built clean via MSVC.

**HONEST STATUS - what is and is NOT in the live engine:**
- **In the C++ engine:** mechanism (1) MEASURE (precision + restriction maps). Nothing auto-enables it: `use_precision`/restriction maps are off/empty until set, and there is no learner in C++ yet (the maps would be trained in Python and pushed, or a C++ learner written later).
- **Python spec/reference only (NOT engine-wired):** the (1) LEARNER, `sheaf_diffusion` inference, and ALL of (2)(3)(4). The controller in `kernel.cpp` still only LOGS `worst_edge` - the search-controller attachment loop (homeostat trigger -> aimed sample -> verify-select -> promote) is NOT wired. That is the next engine step and it is where (4) starts costing Groq.
- **Defaults OFF = slope not intercept:** day-1 behaviour is unchanged from pre-5p. The mechanisms earn their keep only once (a) maps are trained on verified pairs and (b) the flags/loop are enabled. Deliberate, but nothing visibly changes until that wiring lands.
- **Untouched (pre-existing, out of 5p scope):** FIX-4 (hand-parsed JSON), dormant homology still not wired to consolidation (D1), operad.hpp:33 C4101 unref-var warning, the pwsh.exe post-build noise.

**NEXT:** wire the engine control loop - `kernel.cpp` RESOLVE branch consumes `worst_edge` + homeostat, runs the aimed attachment + selection, and (optionally) a C++ restriction-map learner or a Python->engine map push. Then criticality auto-epsilon into `KernelConfig`.

## 5r. EXTERNAL SCRUTINY AUDITED + THE TWO-COMPLEX MEMORY MODEL (2026-07-27)

Two external documents arrived (`MOS_SCRUTINY_AND_D_MODULES.md`, `MOS_BOOK.md`) — a critique
of the `.tex` and its 2771-line expansion. **Note: the two "different" scrutiny files are
byte-identical duplicates (36,283 bytes each). There is one document.** Audited hostile-referee
style; proofs checked by hand, not taken on trust. Two new DOCS produced:

- **`DOCS/AUDIT_SCRUTINY_AND_BOOK.md`** — 14 findings F1–F14, tiered by severity.
- **`DOCS/MEMORY_MODEL_TWO_COMPLEX.md`** — the replacement memory model (Charbel's design, formalised).

### ✅ WHAT SURVIVED VERIFICATION (checked line by line — use these)

- **ρ splits exactly: ρ = α·ρ̃**, α = ‖x⊥‖²/‖X‖²_F (dissent fraction), ρ̃ = ω/(B‖x⊥‖²) (mode index).
  ρ̃ is a Rayleigh quotient on (ker L)^⊥, so **ρ̃ ∈ [λ₂(L_K)/B, λ_max(L_K)/B]** — both endpoints
  computable from the 7-vertex graph before any data. Explains the non-monotonicity caution in
  §sec:controller; gives a topology-derived ε window; yields a TYPED diagnosis (high α/low ρ̃ =
  structural split; low α/high ρ̃ = one bad edge). **Highest-value item in either document.**
- **Prop 8.2: [δx] = 0 in H¹ unconditionally.** A coboundary is by definition not a gluing failure.
  Holds for every state, every sheaf, identity restrictions or not.
- **Tietze (Cor 13.4): promoting a composite does NOT change 𝔇 as an algebra.** δ𝔇 as currently
  specified grows nothing. Correct formalisation splits into compilation (filtration refines) vs
  extension (new generator not a word in the old ones).
- **Λ(t) = mean act-length in current atomic generators on a held-out workload.** First
  LLM-independent falsification test the project has. GK dimension is provably blind to this
  (generating-set independent) — do NOT use it.
- **W₂ degenerates to Euclidean today** (all D = GROWN_CONCEPT_VARIANCE_PRIOR = 1.0, U empty ⇒
  W₂² = ‖μ₁−μ₂‖² exactly). The OT apparatus is currently decoration.
- **Weighted Anderson–Morley proof is correct** (Collatz–Wielandt with s_e = √π_e). ⚠️ But see F2.

### 🐛 THE CRITICAL CONNECTION — Prop 8.2 BLOCKS §5p's GROWTH LAW

§5p states the growth law we actually want: *"struggle = a persistent obstruction; the obstruction
cocycle names the cell to attach."* **The obstruction it reads from is always zero.** The engine's
only 1-cochain is δx, which is in im δ⁰ by construction. So:

> **The growth mechanism has no address to grow at.** This is not an abstract complaint about a
> definition — it is the specific thing standing between MOS and brain-like aimed growth.

Restoring the aim requires a genuinely MEASURED 1-cochain η (organs emitting pairwise judgements,
NOT δ of any global state) plus the Hodge split. **The harmonic component is the address.**

### ⚠️ ERRORS FOUND IN THE INCOMING DOCUMENTS (do not propagate these)

- **F1 — the audit is against a stale snapshot.** Its "item 2 of 3" (set π_e = w(σ,t), use B_π)
  **was implemented in §5q on 2026-07-24**, three days before the scrutiny was written
  (`coherence.py:38-39`, `coarse_complex.cpp:253-254`, `coarse_complex.hpp:117`). **The `.tex` is
  stale relative to the engine and must be resynced with §5q — highest-priority correctness risk,
  since every downstream criticism inherits it.**
- **F2 — Theorem 7.5 (weighted A–M) is stated for the sheaf Laplacian δᵀΠδ but proved only for
  identity restrictions.** With general maps the bound needs ‖R_{v⊴e}‖ ≤ 1. **Our code is more
  honest than the book** — `coherence.py:46` records the orthogonality assumption,
  `coarse_complex.cpp:273-277` warns to stderr instead of clamping. Carry the hypothesis.
- **F3 — half the proposed H¹ fix is CIRCULAR.** "Residuals of learned restriction maps" is still
  δx for the learned maps, still exact, still zero in H¹. Only explicit organ pairwise judgements
  escape — and that is a new organ contract, not a new formula.
- **F7 — Prop 12.4 is FALSE for affine constraints.** RK4 is affine-invariant: every stage lies in
  V, so x₁ ∈ x₀+V exactly and projection is a no-op. True only for NON-linear constraint manifolds.
  Our §7 rigid constraints (orthogonal projection onto an affine subspace) are undamaged.
- **F9 — HH² is not where obstructions live** (HH³ is), and **Ore extensions are unobstructed**
  given (σ,δ). The "HH¹ = what you could grow, HH² = what stops you" story is decorative.
- **F10 — the K₀ memory schema is vacuous.** In Hol(𝒟) every Gaussian is a SIMPLE module ⇒ every
  memory is length 1 ⇒ [M] carries only "which memory is this", and the simples form a continuum
  (not a data structure). In Rep(Q), [V] = the bare dimension vector (catastrophic collisions).
  §29-32 argue in one category, §33-37 in the other, §47 in neither.
- **F11 — "ε need not be fitted" is contradicted 3 pages later** by `ε = window.lo + q·(hi−lo)`.
  It is NORMALISATION, not derivation. Real improvement (topology-adaptive), but say it correctly.
- **F12 — the dead-dynamic-range diagnosis is asserted, never computed.** bge-small returns
  UNIT-NORMALISED vectors ⇒ α = (n−1)(1−c̄)/n. At our logged c̄ ≈ 0.45 with n=7 that is **α ≈ 0.47**,
  nowhere near small. The "encoder anisotropy" story may simply be false. **One log line settles it.**
- **F13 — novelty overclaim.** Weighted A–M is folklore spectral graph theory, not "the one
  genuinely new theorem." Also: Kac's theorem is over an ALGEBRAICALLY CLOSED field; our data is real.
- **F8 — the CP³ prediction is weaker than advertised.** "No low band on 1-forms" follows from
  b₁(ℂℙ³)=0 at EVERY β by Hodge theory — the count is a consistency check, not a discovery. The
  real content is the GAP, and the book never computes the slope. Derived: with Hessian
  eigenvalues 2(λⱼ−λᵢ) (multiplicity 2), model first-excited level 2t·min|a_j|, and t = β/2,
  **slope ≈ 2β·gap(K)**, gap(K) = min spectral spacing. ⚠️ CONVENTION-DEPENDENT (definition of Δ_β;
  FS normalisation; chart orthonormality) — pin all three in ONE numbered display before writing.
  Also: Step 1 assumes DISTINCT eigenvalues; Heisenberg XXX is degenerate ⇒ Morse–**Bott**,
  critical set ℂℙ² ⊔ pt, Morse-Bott polynomial still 1+t²+t⁴+t⁶, conclusion survives, derivation
  as written does not cover it.

### ✅ DECISIONS TAKEN (2026-07-27)

1. **Three papers, not one.** (A) sheaf coherence measure — nearly writable today, all claims are
   theorem+measurement. (B) cohomological obstruction as diagnostic — needs measured-η engineering
   first; Prop 8.2 publishable as a negative result; Abramsky–Brandenburger contextuality is the
   QI thread. (C) ℂℙ³ thermal spectrum = FIRST DRAFT §3. **C must NOT be contaminated by MOS** — it
   is true whether or not MOS exists; MOS goes in acknowledgements/methods.
2. **❌ FCA (Formal Concept Analysis) REJECTED as the memory substrate.** It was proposed to fix
   F10 by COMPUTING the category from data. Charbel correctly rejected it: FCA is
   **data-determined** (C = F(data)), and its canonicity comes precisely from discarding the
   path-dependence we want. We want **history-determined** growth (C(t+1) = G(C(t), what happened)).
   Parked as a possible local *move* (compute a lattice when folding a region) — NOT the foundation.
3. **✅ TWO-COMPLEX MEMORY MODEL ADOPTED** (Charbel's design). See `MEMORY_MODEL_TWO_COMPLEX.md`.
4. **F10 is DISSOLVED, not answered.** The two-complex model never needs canonical memory atoms,
   so Jordan–Hölder, K₀ and Ext¹ all drop out of the memory design. If canonical atoms are ever
   wanted for another purpose the question returns unchanged.
5. **Constant sheaf abandoned** (decision endorsed by Charbel: "obviously change from a constant
   sheaf, that's asinine").
6. **NOTATION FORK — two orthogonal stratification axes.** *scale* = organ/concept (existing
   coarse/fine). *timescale* = crystallized 𝕂 / working W (new). **Do not conflate the vocabularies.**
   Both scale levels exist inside both timescale levels.

### 🔵 THE TWO-COMPLEX MODEL (summary; full spec in `MEMORY_MODEL_TWO_COMPLEX.md`)

`𝕂 = (C_𝕂, F_𝕂, w)` the crystallized store — **carries NO section** (structure, not a thought).
`W = (C_W, F_W, s_W)` the working complex — a downward-closed subcomplex WITH a state.

**They communicate by a genuine adjunction** (standard; Curry ch. 4-6), unlike the `.tex`'s
unverified ℒ⊣ℳ:  `ι_! ⊣ ι* ⊣ ι_*`  for the poset inclusion ι: W ↪ 𝕂.
- `ι*` = instantiate (store→cache);  `ι_!` = extension by zero = write back only what was touched.
- **Theorem: ι*ι_! ≅ id** — the load/work/store round trip is faithful. Use ι_! not ι_*: the cache
  must assert nothing about untouched cells (sheaf-theoretic form of our ⊥ invariant).

**Adaptation = the sheaf stops being constant.** Store maps = how concepts relate IN GENERAL;
cache maps = how they relate IN THIS PROBLEM. The session's learning is `ΔR = R^W − ι*R^𝕂`.

**Topology molds the descent (the constitutive move).** With a measured η and its Hodge split:
> **Prop.** The flow converges with residual **Φ_∞ = ‖η_H‖² + ‖η_C‖²** — computable by two
> least-squares solves BEFORE flowing. Control rule: `Φ_∞/‖η‖² > θ ⇒ don't flow, GROW.`
> **Prop.** dim ker Δ₁ = dim H¹, each attached cell kills ≤1 class ⇒ **≤ dim H¹ attachments make W
> reconcilable** — a growth budget computed from shape, before any Groq call.
Typed remedy: curl ⇒ repair one 2-simplex (local); harmonic ⇒ GROW, and η_H's support is the address.

**Crystallization = one formula (this is CLS made into a coefficient):**
`R^𝕂_e ← Π_O(d)( R^𝕂_e + γ(ν)(R^W_e − R^𝕂_e) )`, γ(ν) = γ₀ / εγ₀ / 0 for Verified/Unverifiable/Refuted.
γ₀ ≪ 1 = slow transfer = the anti-catastrophic-interference property. **s_W is NOT written back** —
content and wiring persist, the episode does not.

**NEW METRIC — `Q(t) = (1/|E|)Σ_e ‖R^𝕂_e(t) − I‖²_F`.** Constant sheaf is Q=0 ("every concept means
the same in every context" = nothing learned about the wiring). Departure from constancy is
accumulated relational knowledge, and **the LLM contributes nothing to it**. Second LLM-independent
falsification instrument alongside Λ(t). Cost: a log.

**Day-one degradation (slope not intercept, as always):** k=1, R≡I, γ₀=0, η:=δs, θ=∞ reproduces
current MOS EXACTLY. Nothing visibly changes on day one, deliberately.

**⚠️ Prior art to cite:** this is **Complementary Learning Systems** (McClelland, McNaughton &
O'Reilly 1995; Kumaran/Hassabis/McClelland 2016) realised sheaf-theoretically — derived
independently here from the geometry. Also: schema ↔ restriction maps, schema-consistency ↔ small ω
(Tse et al. 2007 *Science*); structure/content factorisation ↔ Tolman-Eichenbaum Machine
(Whittington et al. 2020 *Cell*); our diffusion IS a Hopfield-style associative memory;
Hansen–Ghrist for the sheaf Laplacian; **Abramsky–Brandenburger for contextuality (the QI thread)**;
HodgeRank (Jiang–Lim–Yao–Ye) for the gradient/curl/harmonic split. Must also position against
GraphRAG, HippoRAG, MemGPT, Generative-Agents "reflection" (= our promotion, done heuristically).
⚠️ **Citations are from model knowledge, NOT searched — verify years/titles before any bibliography.**

### 📋 EXPERIMENT REGISTRY (each with a stated way to FAIL)

| id | experiment | cost | falsifies |
|---|---|---|---|
| **E1** | log α, ρ̃, window [λ₂/B, λmax/B] every tick | free | the encoder-anisotropy story (F12) if α≈0.5 |
| **E2** | Λ(t) compression curve on a held-out workload | a log | **the whole augmentation bet** if flat |
| **E3** | clique polynomial on the REAL operator set | 1 day | all of Part II if I is empty (see below) |
| **E4** | split W₂ into d_semantic / d_epistemic | free | that merges are semantically driven |
| **E5** | ✅ **RUN ×2, 2026-07-29 → PASS, weakly (§5x).** ~~FAIL (§5v)~~ retracted in §5w. 4 organs, 5 edges, 1 filled triangle (the 3-organ version has b₁=0 and detects nothing) | 54 calls | **THE GATE. Contested \|L₂\| = 0.41 vs a 0.26 no-cycle null, p ≈ 0.02–0.08. Obstruction real but small; ⚠️ b₁=1 ⇒ the ADDRESS is uninformative. Next config needs b₁ ≥ 2.** |
| **E6** | ℂℙ³ numerics: sweep β, check no low band + linear growth + slope | weeks | Part VIII (the only result interesting outside MOS) |
| **E7** | record Ext/assembly data AT COMPOSITION TIME | small | nothing — **do it now, impossible to recover later** |
| **Q** | log Q(t) | a log | that the wiring is learning anything |

**F4 / E3 note:** ALL of the book's Part II (Foata, Gröbner, Koszul, Cartier–Foata, capacity κ,
Anick, HH¹/HH²) rests on ONE unverified hypothesis: that operators with disjoint node-support
COMMUTE. In our engine every operator touches shared state (CognitiveState, SQLite, Ω, the mutation
history, and the coarse stalks π_v overwrites). **They do not commute as state transformers.** If
I is empty then A is the free algebra, μ(z)=1−rz, and Part II is counting DAGs. Nobody has computed
I for {SearchOp, ComputeOp, ReasonOp, ContextOp, VerifyOp}. One afternoon; do it before writing a
line about Koszulity.

### ⚠️ NEW FIX-REGISTRY ITEMS

- **FIX-6 (H) — `.tex` is stale vs the engine.** §sec:outlook files as "proposed, unimplemented"
  things §5q implemented and tested. Resync before the `.tex` becomes any paper's baseline.
- **FIX-7 (H) — `.tex` §15.6 "harmonic representative of a persisting [ζ]∈H¹" has no source.**
  Rewrite or delete; by Prop 8.2 it cannot fire from δx.
- **FIX-8 (M) — organ count is inconsistent across the corpus.** `.tex` lists 7, logbook §0 lists 6,
  runtime uses 4 operator organs + RESPOND. Pick one before publication.
- **FIX-9 (M) — `.tex` b₁/H¹ distinction is incompatible with identity restrictions.** Under the
  constant sheaf H^k(C;F) ≅ H^k(C;ℝ)⊗ℝ^d, so H¹≠0 ⟺ b₁≠0 ALWAYS. Two rows of the uncertainty
  stack are one row with a factor of 384. Resolved by the two-complex model's non-constant sheaf,
  but the `.tex` text must be corrected.
- **FIX-10 (L) — Anderson–Morley hypothesis.** State ‖R_{v⊴e}‖ ≤ 1 in the theorem, not just in the
  code comments.

### NEXT (dependency-ordered)

1. **Resync the `.tex` with §5q** (FIX-6). Writing, no code. Everything else inherits this.
2. **E1, E3, E4, Q(t)** — all cheap, all this week, each can come out badly.
3. **E7** — start recording assembly data immediately; it is unrecoverable later.
4. **E5 — THE GATE.** Three LLM calls decide whether the cohomological growth story is real.
5. Then, and only then: build the 𝕂/W split, the Φ_∞ stopping rule, and the γ(ν) consolidation rule.
6. Separately/in parallel: **E6 (ℂℙ³)** — this is the thesis and does not depend on any of the above.

**⚠️ COORDINATION:** steps 1–4 of the earlier plan were branched to a SEPARATE chat. This logbook is
the shared state between the two threads — both must read §5r before acting, and both must append here.

**⚠️ DISCIPLINE ADOPTED (2026-07-27):** three layers of mathematics have now been proposed on top of
MOS (sheaves → D-modules/quivers → FCA). Adopted test, to be applied to every future proposal:
> **A new piece of mathematics earns its place only if it changes a number the engine prints, or
> removes a decision a human was making by hand.**
The two-complex model passes. D-modules currently fail. FCA was rejected under it.

## 5s. INSTANTIATION + CURVATURE CONTROLLER + FINALIZATION (2026-07-27, same session as §5r)

Closed the two blocking gaps left open by §5r. Two new DOCS:
**`DOCS/BUDGET_AND_TEST_PLAN.md`** (space/time/LLM budget + 4-tier test plan) and
**`DOCS/MOS_FINALIZATION.md`** (settled decisions A1–A17 + a 24-question finalization
questionnaire with recommended defaults + the path to publication).

### ✅ GAP (a) CLOSED — instantiation by local graph clustering
Seed by embedding (LAST, not first) → **approximate Personalized PageRank on the WEIGHTED
1-skeleton** (weights = w(σ,t), so Hebbian history finally shapes retrieval) → sweep cut →
downward closure → report **CUT WEIGHT** (Σ w over sliced simplices; returning 2 of a
jointly-bound 3 is a type error). **Andersen–Chung–Lang 2006: cost O(1/(αε)), INDEPENDENT of
|𝕂|.** That is the scalability claim; B3 tests it. Cheeger (λ₂/2 ≤ h ≤ √(2λ₂)) ties cluster
quality, reconciliation rate and ε calibration to ONE spectral object. ⚠️ Higher-order
simplicial Cheeger is much weaker with known counterexamples — cluster on the 1-skeleton,
treat cut weight as a diagnostic not a bound.

### ✅ GAP (b) CLOSED — the curvature controller (Charbel's requirement: expand AND contract)
**Correction to my earlier warning:** Ricci flow IS homogenising (positive curvature contracts,
negative expands) — already two-directional. What destroys bridges is the **surgery** step
community-detection papers add. **Run the flow, skip the surgery.**

κ>0 = many alternative paths = redundant = LOW info/edge. κ<0 = near-cut = bridge = HIGH info/edge.
So curvature is (up to sign) information-content-per-edge, and:
- **κ > κ_hi ⇒ CONTRACT/FOLD** (collapse, merge, promote) — *this is chunking, what Λ(t) measures*
- **κ < κ_lo ⇒ EXPAND** (bind, attach) — you know A relates to B but not HOW

**Weight flow — ⚠️ SIGN FLIPS from the literature (they use distance, MOS uses coupling):**
`w(σ,t+1) = (1 + ε·κ(σ,t))·w(σ,t)` **subject to w ≥ w_floor whenever κ < 0.**
The floor is the entire safety argument: negative curvature **weakens but never severs**, so the
gap widens (making room for a new cell) without silently deleting the only bridge between two
domains. **Kills the third magic constant: `decay=0.1` becomes ε·κ(σ).** κ_hi/κ_lo as quantiles
of the observed κ distribution, not fixed numbers (same discipline as ε).

**Use AUGMENTED Forman–Ricci** (the bare version is just degree and adds nothing):
`F(e) = 4 − deg(u) − deg(v) + 3·#{2-simplices containing e}` — O(1) per edge, positive iff local
cycles are FILLED. **This finally makes the 2-simplices do computational work every tick**,
answering the audit's standing complaint that they are stored and never used. Ollivier–Ricci
(reuses the existing W₁) is more informative but needs a transport solve per edge — escalate
selectively only.

### ★ THE AIMING RULE — two independent obstruction signals
Shape signal κ (free, any time) **pre-filters** for data signal η_H (costs LLM calls):

|  | η_H ≈ 0 | η_H ≠ 0 |
|---|---|---|
| **κ ≥ 0** | nothing to do | contradiction with NO structural cause → **suspect the MEASUREMENT, not the complex** |
| **κ < 0** | latent frontier (log, low priority) | ★ **SPEND THE SAMPLE HERE** ★ |

At ~1000 Groq req/day this is what makes the selectionist loop affordable. Note the top-right
cell: the architecture detects its own instrumentation failure.

### ⚠️ THREE BUDGET FINDINGS THAT FORCE DESIGN CHANGES
1. **Full restriction maps are dead on arrival.** 384²×4B = **576 KB/map**, 2 per edge ⇒ 2.3 GB at
   2000 edges on a 5.9 GB machine. **Use Householder products** R = H₁···H_m, H_i = I − 2vᵢvᵢᵀ:
   **6 KB at m=4**, exactly orthogonal by construction (so **audit F2's ‖R‖≤1 hypothesis holds for
   free**), apply in O(md), and Q(t) is closed-form in the vᵢ. 96× reduction.
2. **Never form the Hodge pseudo-inverse.** With identity maps δ⁰ = δ_K⊗I_d factors (21×7 scalar
   work, free). With REAL maps it does not factor: pinv of an 8064×2688 matrix ≈ 10¹¹ flops,
   minutes. **Use LSQR/CG** — ~50 matvecs ≈ 1.3×10⁷ flops, milliseconds.
3. **Measured-η has QUADRATIC LLM cost.** n(n−1)/2 = 21 calls/tick at n=7 ⇒ only 47 ticks/day at
   the free tier. **Batching all pairs into ONE structured call is mandatory, not an optimisation.**

### 📋 THE MAIN TEST (T1) — measure a DERIVATIVE, not a level
Three arms, **SAME LLM**: bare | plain-RAG | MOS. Run a held-out workload at t=0 and again after N
sessions of accumulation. **PRIMARY = the GAP between MOS and plain-RAG as a function of
accumulated experience.** The bet was always the slope, never the intercept — day one MOS is
*worse* by our own documents, so the measurement must be a derivative. Also far easier to defend
than "we beat RAG," and it makes a negative result publishable.
**NOT valid tests:** MOS vs a frontier model single-shot (wrong claim, guaranteed loss); unequal
call budgets; Δρ as an outcome (coherence ≠ correctness); κ capacity (gameable).

### NEXT
🔴 questions in `MOS_FINALIZATION.md` §D block implementation — Q1/Q2 (stalk geometry), Q4
(Householder m), Q5/Q6 (curvature), Q9–Q11 (organ judgement contract), Q13 (attachment operator),
Q16 (γ₀), Q19 (what leaves 𝕂), Q21 (Refuted handling). Each has a recommended default.
**Tier 0 tests (E1, E3, E4, E7, Q) are free, parallel, and depend on NONE of the open arguments —
do not serialise them behind the stalk-geometry debate.**

## 5t. FOUR BLOCKING DECISIONS ANSWERED (2026-07-27) — the stalk is a density matrix

Charbel answered the four 🔴 questions that gated implementation. Recorded in
`MOS_FINALIZATION.md` §D; the consequences are larger than expected.

**Q1 — stalk type: rank-k SPD for IMPLEMENTATION, density matrices for THEORY.**
Not a compromise — a projection. The SPD cone is the **cone over density-matrix space**:
`Σ = UUᵀ + DI  ≅  (Tr Σ) × (Σ/Tr Σ)`. Store Σ, theorise about ρ = Σ/Tr Σ, get the trace free.
**The Bures–Wasserstein already in `knowledge_base.cpp`, restricted to trace 1, IS the Bures
metric on density matrices — the quantum fidelity metric.** The QI convergence stops being an
analogy and becomes a change of coordinates.

**★ THE BIG CONSEQUENCE — restriction maps are quantum channels.** Congruence `Σ ↦ RΣRᵀ`, and
R orthogonal ⇒ Tr preserved ⇒ density matrices map to density matrices ⇒ **R is a unitary
(orthogonal) CPTP channel.** The Householder representation forced by the RAM budget (§5s) and
the orthogonality forced by Anderson–Morley (audit F2) **independently land on the simplest class
of quantum channels.** New potency ladder, better than the book's characteristic-cycle proposal
because it is computable and degrades gracefully:

| level | map | meaning |
|---|---|---|
| 0 today | identity | "same thing, verbatim" |
| 1 Householder | **unitary channel** | "same content, different basis" — reversible, lossless |
| 2 general CPTP (Kraus) | lossy channel | translating u→v **destroys** information; the entropy added IS a measure of connection quality |

**And it costs NOTHING in spectral theory:** symmetric matrices are a vector space and CPTP maps
are LINEAR on it, so L stays symmetric PSD, ker L = H⁰, ρ keeps its bound.

**Q2 — tangent-space linearised.** Karcher mean each tick, lift by log, run the whole existing
apparatus in the tangent space, map back. E12 tests whether it earns its cost.

**⚠️ Q2b — NEW BLOCKING QUESTION raised by Q1's answer. MOS is mixing TWO geometries:**
- `π_v` fusion `= (ΣΣᵢ⁻¹)⁻¹(ΣΣᵢ⁻¹μᵢ)` — **information / Fisher–Rao / KL** geometry
- `W₂` distance — **optimal transport / Bures–Wasserstein** geometry

These are genuinely distinct. The **Wasserstein barycenter of Gaussians has mean = the PLAIN
weighted average of μᵢ** (Agueh–Carlier), NOT the precision-weighted one. So fusion and distance
disagree about what "average" means. Not fatal (different purposes; the `.tex` correctly justifies
π_v as an MLE) **but it is implicit and a referee will find it** — and Q2's Karcher mean differs
per geometry, so a choice is forced. Recommended: keep both, **explicitly scoped** (Wasserstein
for distance/merge, information for fusion), and linearise in **Wasserstein** since that is the
quantum-native one and W₂ is already implemented.

**Q9 — organ emits a scalar in [−1,1] PLUS a confidence.** η stays 1-D per edge (cheap, enough
for the Hodge split). **The confidence feeds π_e directly — finally a non-constant precision
source that is not a hallucinated logprob**, closing the gap Remark 6.6 leaves open and which the
audit's 1/n analysis identifies as disabling the entire π_v mechanism.

**Q13 — attachment = CONE OFF THE CYCLE.** Add one vertex joined to every vertex of the offending
cycle. **Provably drops dim H¹ by exactly 1**, so the growth loop cannot spin (the chord option
often relocates a class rather than killing it). Matches §5p's stated intent. The new vertex is
the cell the aimed LLM sample fills.

### COST RE-CHECK WITH RANK-k SPD STALKS (8× the storage per stalk — still fits)

| item | cost | verdict |
|---|---|---|
| stalk (U ∈ ℝ³⁸⁴ˣ⁸, D) | 12 KB (vs 1.5 KB) | 10⁴ concepts = 120 MB ✓ |
| apply Householder to rank-k factor `U ↦ RU` | O(m·d·k) = 12K flops | ✓ |
| ω over 21 edges with BW distance | ~520K flops | ✓ **still per-tick affordable** |
| Wasserstein barycenter, ~5 iterations | O(dk²+k³)×5 ≈ 130K flops | ✓ |

**The rank-k design choice keeps paying for itself** — it was the feasibility condition for the
D-module layer, it is the feasibility condition for SPD stalks, and it keeps everything on the
fast path.

### Q2c — "blend the two geometries into one LEARNED metric?" — INTERPOLATE YES, TRAIN NO

Charbel proposed a weighted metric combining Fisher–Rao and Wasserstein, weight obtained by
training. Assessed:

**Two ways to combine, each loses something:**
- **blend the METRIC TENSORS** `g_λ = (1−λ)g_FR + λg_W` — valid Riemannian metric (convex comb.
  of pos-def forms), keeps geodesics/exp/log/Karcher mean, **but NO CLOSED FORM** (d_λ ≠ the
  blend of distances; inf of a sum ≠ sum of infs). Geodesic ODE per evaluation ⇒ fatal per-tick.
- **blend the DISTANCES** `d_λ = (1−λ)d_FR + λd_W` — is a metric, cheap (both closed-form),
  **but not the geodesic distance of ANY Riemannian metric ⇒ no Karcher mean**, which is exactly
  what Q2's linearisation needs. ⚠️ blend the DISTANCES not the squares.

**The principled version already exists:** ⚠️(verify) **Wasserstein–Fisher–Rao** /
**Hellinger–Kantorovich** (Chizat–Peyré–Schmitzer–Vialard 2018; Liero–Mielke–Savaré 2018).
Unbalanced OT: mass is either MOVED (Wasserstein) or CREATED/DESTROYED in place (Fisher–Rao),
and the parameter is **a length scale δ**, not a blend weight: below δ transport is cheaper,
above δ create/destroy is cheaper, hard cutoff at πδ.
> **δ = the semantic distance beyond which two concepts stop being "one thing that moved" and
> become "two different things."** That IS the merge/split question — an interpretable modelling
> quantity, not a fudge factor. **New test E15: check whether WFR has a closed form between
> Gaussians as Bures does. If not it stays theory.**

**❌ TRAINING THE WEIGHT REJECTED — four reasons, first is decisive:**
1. **It reintroduces exactly what the audit removed.** α/ρ̃ replaced `ε≈0.10 fitted on three
   observations` with a graph invariant. Replacing a *choice of geometry* (has a reason) with a
   *fitted constant* (has none) is that move in reverse — the first backwards step in the redesign.
2. **No training signal exists.** VerifyOp answers "is this true," not "are these the same
   concept." Downstream performance is honest but very noisy for one scalar and costs a full
   pipeline run per evaluation against 1000 req/day.
3. **One scalar needs a SWEEP, not an optimiser.** 20 values on a validation set. An optimiser
   buys an overfitting failure mode and nothing else.
4. **The two uses are asymmetric and one has a proof.** π_v's precision weighting IS the MLE for
   n independent noisy measurements — a theorem in the `.tex`. Blending it toward Wasserstein
   damages a derived result in exchange for a fitted number. Distance, by contrast, is genuinely
   open and interpolation there is legitimate.

**DECISION:** keep Q2b option (c) — scope the geometries explicitly (information for FUSION
because it is an MLE; transport for DISTANCE/merge). If one distance metric is wanted, use WFR
with δ as the concept-identity scale. **Calibrate δ by sweep and publish the SENSITIVITY CURVE,
never a single fitted value** — a curve is honest, a fitted constant invites precisely the
criticism the audit levelled at ε. **New test E14** (label ~50 pairs by hand, ~1 hour, then free).
Longer-term data-driven option without training: if a merged concept is subsequently Refuted more
often than the unmerged pair would have been, the merge was wrong — calibrates δ from VerifyOp
with no new labels.

### ✅ Q2b RESOLVED — HYBRID METRIC with an explicit dispatch rule

Charbel chose option (c): each geometry used for the task it is correct for. **Normative rule,
recorded so it does not degrade into "whichever was handy":**

> **ESTIMATION → information/Fisher–Rao** (the MLE has a derivation — do not touch)
> **COMPARISON → optimal transport/Bures–W₂** (accounts for spread; quantum-native)

| operation | geometry |
|---|---|
| `π_v` coarse-graining · pairwise fusion (Eq. 13) · entropy `H(Σ)` | **information** |
| merge/split · `ω`, `ρ` · the Karcher mean for the Q2 linearisation | **transport** |

**Why it is not arbitrary:** estimation is where a THEOREM exists, comparison is where a
MODELLING CHOICE exists. Never blend into the first; interpolation (WFR, Q2c) is legitimate only
inside the second.

**⚠️ THE SEAM — one paragraph the paper owes.** `π_v` FUSES in information geometry and its output
is IMMEDIATELY COMPARED in transport geometry by `ω`. So a coarse stalk is produced by one metric
and measured by another. Concretely: **`π_v` is NOT the transport-barycenter of its own fine
complex** — by Agueh–Carlier the Wasserstein barycenter of Gaussians has the PLAIN weighted mean,
not the precision-weighted one. The two levels of the stratification are joined by a map optimal
in one geometry and not the other. Defensible, but not self-evident; **a referee who knows
Agueh–Carlier will find it.** Needs a justifying paragraph in Paper A (same sense in which an MLE
and a confidence region are computed differently without either being wrong), NOT a fix.

### ⚠️ SELF-CAUGHT: WE KILLED THREE MAGIC NUMBERS AND INTRODUCED A FOURTH

Removed this session: `ε≈0.10` → quantile of the ρ̃ window · `decay=0.1` → ε·κ(σ) ·
`bind_threshold` → folded into the curvature controller.

**But the growth rule `Φ_∞/‖η‖² > θ ⇒ grow` introduces θ, a hand-set constant with no principled
source** — precisely the thing this whole session was spent removing. Not noticed when the memory
model was written.
→ **NEW Q25 🔴: θ as a quantile of the observed distribution of Φ_∞/‖η‖² over past conflicts**,
recomputed on structural change (same trick as ε and κ_hi/κ_lo). Needs deciding, not assuming.

**Precision note on Q(t) and Λ(t):** "LLM-independent" means *the frozen LLM contributes no
trend* — not that no LLM is involved. Both metrics depend on organ output, which depends on the
model; the point is that the model does not change, so any movement in the curve is attributable
to accumulation. State it that way in the paper; the stronger reading is false.

### STILL OPEN (🔴)
Q4 (Householder m) · Q5/Q6 (curvature: Forman vs Ollivier; signal vs flow) · Q10/Q11 (which pairs
judged; batched schema) · Q16 (γ₀) · Q19 (what leaves 𝕂) · Q21 (Refuted handling) ·
**Q25 (θ for the growth trigger — new)**.
All have recommended defaults in `MOS_FINALIZATION.md` §D. **Q1, Q2, Q2b, Q2c, Q9, Q13 resolved.**

### ⚠️ BEFORE ANY WRITING TOMORROW — three cheap things that can invalidate work
1. ~~**E5, the gate** (~10 LLM calls, 1 hour). NOT YET RUN.~~ ✅ **RUN ×2, 2026-07-29 → PASS, weakly (§5x).** ~~FAIL (§5v)~~ retracted in §5w.
   The growth law, the aiming 2×2, the Φ_∞ rule and half of Paper B all assume measured η has
   harmonic/curl mass. It does not, under this protocol. **Running it before writing the theory
   was the right call — it would have invalidated the writing.**
2. **E15** (30 min literature): does WFR have a closed form between Gaussians? If not, Q2c
   collapses to theory and the merge metric stays plain Bures.
3. **E3** (one afternoon): decides whether the book's Part II is mathematics or bookkeeping.

### ⚠️ COORDINATION RISK — ✅ RESOLVED 2026-07-29, see §5u
~~Steps 1–4 were branched to a separate chat which has NOT seen §5r–§5t.~~ The branched thread has
now read §5r–§5t and reported in at **§5u**: it shipped E1 and E4, partially ran E3, and closed
FIX-6 and FIX-10. All three risks flagged here were avoided — the `.tex` is resynced, α was
*measured* at ≈0.46 (F12 confirmed, not assumed away), and the ‖R‖≤1 hypothesis is now stated in
the theorem. Both threads must keep appending here.

## 5u. E1 + E4 SHIPPED, E3 PARTIALLY RUN, `.tex` RESYNCED (2026-07-29) — the branched thread reporting in

**This is the branched chat referred to in §5r's ⚠️ COORDINATION RISK.** It has now read
§5r–§5t and is appending here. Everything below is the *execution* of the registry in
§5r; no new theory was invented. Independent referee-grade audit also written to
**`DOCS/AUDIT_SCRUTINY_AND_BOOK.md`** (14 findings) — it agrees with §5r's verified list
and adds F7 (Prop 12.4 false for affine constraints — RK4 is affine-invariant, so
projection is a no-op and 4th order survives; the claim holds only for non-linear
manifolds) and F10 (the K₀ memory schema is stated in a category that is never fixed;
both candidates fail — see NEXT).

### ✅ FIX-6 CLOSED — `.tex` resynced with §5q
- §sec:outlook's "nothing here has been implemented" box **deleted**, replaced by a
  per-mechanism status list: measure implemented, control loop not.
- §coherence: new subsection — Prop `split`, Remark `percomp`, Prop `window`, honesty
  box, Remark `e1measured`.
- §semantic: Construction `w2split`, Prop `w2hazard` + honesty box.
- §operad: Remark `tracemonoid` + honesty box carrying the E3 defects below.
- Added missing labels `rem:uncal`, `rem:controller`, `def:hebb-decay`; new Remark
  `gate-tilde` supersedes the empirical-ε cautions.
- ⚠️ **FIX-7, FIX-8, FIX-9 NOT done** — still open, still owed.

### ✅ FIX-10 CLOSED — Anderson–Morley hypothesis is now in the theorem
Prop `wam` states ‖R_{v⊴e}‖ ≤ 1 explicitly, with the full Collatz–Wielandt proof, and
**disclaims novelty** (standard signless-Laplacian material — the book calls it "the one
genuinely new theorem in Part I", which a referee kills in one line).

### ✅ E1 — SHIPPED, spec + engine, parity green
`coherence.py` + `coarse_complex.hpp/.cpp`. ρ = α·ρ̃ asserted exactly (1e-12) in both.
Window from a 7×7 eigendecomposition; `mode_position()` normalises to [0,1].
**Correctness point both source documents missed:** ker L is the **per-component**
constants, not the global diagonal. With b0>1 a global-mean projection scores
between-component separation as dissent when it lies *in* the kernel. Pinned by test.
⊥-discipline held: consensus ⇒ ρ̃=⊥ (not 0); non-identity maps ⇒ split honestly refused.

**🔬 RESULT — F12 CONFIRMED, the encoder-anisotropy story is FALSE.** bge-small is
unit-normalised ⇒ α = (n−1)(1−c̄)/n *exactly*. At the logbook's own c̄≈0.449, n=7:

| c̄ | α | ρ | ρ̃ |
|---|---|---|---|
| 0.449 | 0.463 | 0.218 | 0.471 |
| 0.700 | 0.252 | 0.119 | 0.471 |
| 0.900 | 0.084 | 0.040 | 0.471 |

**ρ̃ invariant across all of them** (the claimed invariance, demonstrated), sitting
mid-window (0.509 in [0.146, 0.854]). **The mode index has healthy dynamic range that ρ
was multiplying away.** Gate on ρ̃; report α alongside.

### ✅ E4 — SHIPPED
New `core::wasserstein_2_terms`. **Also removed a real duplication:**
`knowledge_base.cpp` and `curator.cpp` each carried a byte-identical private copy of the
Bures formula; both now delegate to one implementation.
- **Today the OT machinery is provably inert:** D1=D2=1.0, U empty ⇒ epistemic ≡ 0 ⇒
  W₂² *is* squared Euclidean distance.
- **The latent bug is worse than the book claimed: 115:1, not 57:1.** At d=384, D1=1.0
  vs c=0.95: epistemic=229.76, semantic=2. The book compared against the worst-case
  antipodal bound of 4; typical orthogonal separation is 2.
- **Root cause is dimensional, not epistemic** (the book misattributes it): semantic is
  d-intensive (≤4 for unit vectors), epistemic is d-extensive (= d(√D₁−√D₂)²). Summing
  them is a dimensional error *regardless of calibration*.

### 🟡 E3 — PARTIALLY RUN. Part II is dead anyway, but the owed work is NOT done.
`python/independence.py`. **I executed steps 3–4 of §5r's procedure against the
DECLARED supports. I did NOT do steps 1–2** — no read/write sets were derived, and the
shared state (SQLite, Ω, mutation history, the π_v stalk overwrite) is still unmodelled.
Recording that plainly because the conclusion below does not depend on it and could
otherwise look better-founded than it is.

Three defects found, **any one of which is fatal to the trace-monoid programme**:
1. ⚠️ **NEW BUG — the scheduler's relation is NOT SYMMETRIC.** 8 of 15 operator pairs
   can share a slice in one order but not the other. Cause: `operad.cpp` sets
   `slice_is_global_mutation = true` when admitting *any* empty-support node —
   **including a READ_ONLY one** — which then blocks everything after it. An
   independence relation is symmetric by definition ⇒ no trace monoid, no Foata normal
   form, no Hilbert series. **Worth fixing on its own merits as a scheduling bug,
   independent of all the algebra.** → new FIX-11.
2. **The supports are hardcoded placeholders.** Every `get_support()` returns a literal
   ({}, {0}, {1}); three of six operators return the same {0}, with a comment standing
   in for analysis. Any invariant computed from them describes six constants.
3. **The {} convention is INVERTED**: engine says ∅ = GLOBAL (run isolated); the
   formalism reads ∅ as disjoint-from-everything = independent-of-everything.
   κ=3.00 (formalism) vs κ=5.45 (code) vs κ=6 (free) — a 1.8× disagreement about the
   quantity Part II calls "procedural reach".

Under the reading the engine implements, the algebra is **nearly free** (9% below).
§5r's FAIL condition is met in substance. **Q24's default (drop Part II) stands.**

### ⚠️ NEW FIX-REGISTRY ITEM
- **FIX-11 (M) — `operad.cpp` co-schedulability is order-dependent.** A READ_ONLY
  empty-support node (SearchOp, RespondOp) poisons the slice for every later node by
  setting `slice_is_global_mutation`. Read-only ops should not set that flag. Cheap fix,
  real parallelism win, and it is the precondition for E3 ever being meaningful.

**Tests:** `coherence.py` 15/15 · `mos_coarse_complex_tests` 12/12 ·
`mos_pi_fusion_tests` 6/6 · `mos_kernel_tests` PASS. No regressions, no new warnings.

> **🚨 THE "NEXT — BLOCKING" LINE THAT WAS HERE IS RETRACTED (2026-07-31).** It read
> *"blocking, and it is a modelling decision, not a computation: CHOOSE THE CATEGORY"* and it
> **was already superseded when it was written** — `MEMORY_MODEL_TWO_COMPLEX.md` dissolved F10
> the same day (2026-07-27), and §5r's two-complex decision removed the dependency entirely.
> It sat here for four days making settled work look blocked. **See §5aa.**
>
> **The reasoning below stands as a dead-end record; only the claim that it BLOCKS anything is
> withdrawn.** F10 is **dissolved, not answered**: the two-complex model does not require
> memories to have canonical atoms, so it needs neither Jordan–Hölder, K₀, nor Ext¹.
> Retrieval is **geometric, not algebraic** — the k-fold closed star of the seed set (`ι*`),
> budget-gated on k, returning a *complex* rather than a top-n list. No canonical index is
> required anywhere, which is why K₀ was never needed.
>
> **Lesson, third time recorded: a superseded "NEXT — BLOCKING" line is worse than no line,
> because it re-blocks work that was already unblocked.**

**THE DEAD END, FOR THE RECORD** (audit F10). Both candidates the book offers fail: in Hol(𝒟)
every Gaussian concept is a *simple* module (k[x] is simple over the Weyl algebra in char 0), so
JH(M)={[M]}, length 1, and the K₀ class says no more than "which memory is this"; in
Rep(Q) the K₀ class *is* the dimension vector, which collides catastrophically as a
retrieval index. §29–32 of the book argue in one category, §33–37 in the other, §47 in
neither. Jordan–Hölder guarantees canonicity **given** the category; it cannot pick the
atoms.

## 5v. ⭐ E5 RUN (2026-07-29). ⚠️ **THE "FAIL" BELOW IS RETRACTED — see §5w.**

> **🚨 READ THIS FIRST. The verdict in this section is WITHDRAWN.**
> Two errors, both mine, both found the same day:
> 1. **The p-value is wrong.** Repeats of one question are not independent
>    (ICC ≈ 0.48, design effect ≈ 1.96, n_eff ≈ 4.6 not 9). Corrected: **z ≈ −1.56,
>    p ≈ 0.06**, or p ≈ 0.12 treating questions as the unit. Not 0.014.
> 2. **The statistic cannot support the verdict.** A positive control with a cycle
>    planted *by construction* scores **0.214** on the non-gradient fraction; the
>    contested questions scored **0.209**. Indistinguishable. A statistic a
>    known-positive also fails cannot be used to declare that real questions lack
>    obstructions.
>
> **Revised verdict: weak positive, underpowered — NOT a FAIL.** The instrument is
> sound (probe separation 6.2× on |L₂|); the scoring rule was not. Everything below
> is retained as the record of how it was found, not as a conclusion. §5w has the
> corrected analysis.

New files: **`python/hodge.py`** (the decomposition, free, 11 self-tests) ·
**`python/experiment_e5.py`** (elicitation + verdict, 3 self-tests + `--analyze`) ·
`python/e5_inspect.py` · `python/e5_elicitations.jsonl` (raw data, E7 discipline).
Cost: **16 Groq calls total**, 70B, ~21k+11k tokens. `router.py` gained an optional
`temperature=` kwarg (default unchanged at 0.2, so every existing caller is byte-identical).

### THE RESULT

| question | kind | n | non-grad mean | harm mean |
|---|---|---|---|---|
| Q-ikeda (SU(n+1) determines the CPⁿ 1-form spectrum?) | contested | 3 | **0.438** | 0.301 |
| Q-cp3-gap (the north-star, FIRST DRAFT §3) | contested | 3 | 0.103 | 0.073 |
| Q-rho-truth (is low ρ evidence of correctness?) | contested | 3 | 0.086 | 0.017 |
| Q-b1-cp3 (b₁(ℂℙ³)=0? — everyone agrees) | control | 3 | 0.058 | 0.030 |
| Q-lemon (cake crumb — nobody has competence) | control | 3 | 0.066 | 0.034 |

> **contested non-gradient fraction = 0.209 against an isotropic null of 0.400.
> z = −2.19, one-sided p = 0.014.** η is significantly MORE gradient-like than
> random. **One potential per organ largely explains the pairwise data, so H¹ has
> little to find and the growth law still has no address to fire at.**

⚠️ The p-value is optimistic: repeats of one question are not independent, so n=9 over-counts.
Read it as a signed effect size. The dispersion used is max(null sd, observed sd).

### ⚠️ THREE CORRECTIONS THE RUN SHEET NEEDED — all found before the result, not after

1. **★ THE PASS CRITERION AS WRITTEN WOULD HAVE PASSED PURE NOISE.** §7 says PASS if
   `‖harm‖²+‖curl‖²` is "a non-trivial fraction of ‖η‖²". But the three pieces are
   orthogonal projections onto subspaces of *known dimension* (3 grad, 1 curl, 1 harm out
   of 5), so isotropic η puts energy in each in proportion to dimension:
   **grad 0.60 / curl 0.20 / harm 0.20 — a random instrument scores 0.400.**
   Exact nulls now derived in closed form and verified against 40k Monte Carlo draws:
   `P(harm ≥ t) = 1 − (3/2)√t + (1/2)t^{3/2}` (Beta(½,2)) ·
   `P(harm+curl ≥ t) = (1−t)^{3/2}` (Beta(1,3/2)).
   **0.400 is the number to beat, not 0.** This is the single easiest way we could have
   fooled ourselves here, and it would have converted this FAIL into a PASS.
2. **★ THE ORGAN CONTRACT IS NOT A 1-COCHAIN.** §7/Q9 specify `{u, v, agreement∈[−1,1],
   confidence}`. **Agreement is symmetric; a 1-cochain is antisymmetric.** Antisymmetrising a
   symmetric table gives η ≡ 0 identically (now an assertion in the self-test). → FIX-12.
3. **The E5 test-design correction in §7 was right and is now implemented and checked**:
   the original "one filled triangle" has b₁=0 and can detect NO harmonic mass. The
   4-organ/5-edge/1-triangle configuration gives dim C¹ = 5 = 3+1+1 ✓, b₁=1 ✓.

### WHAT η ACTUALLY IS HERE (stated, not hidden)
Per bound pair {u,v} the instrument returns the sub-claim `c_uv` *those two* organs jointly
bear on, plus each organ's push on it, and `η_(u,v) = p_v(c_uv) − p_u(c_uv)`.
**So η is antisymmetric BY CONSTRUCTION, not by measurement**, and the file says so in its
docstring. Two earlier designs were tried and failed informatively:
- symmetric "agreement" (the run sheet's) ⇒ η ≡ 0, as above;
- directed "how much must u revise given v", elicited both ways ⇒ **the model read it as
  VALENCE, not comparison**, returning Reason→Verify **+0.55 AND** Verify→Reason **+0.60**.
  Antisymmetric part was a small residue on a large symmetric one — measuring "do these two
  both like the claim", which is not the object the theory is about.
- (Also: the first prompt returned **all ten judgements 0.0 with confidence 1.0**. Cause was
  ours — one rule licensed zeroing, another told the model organs cannot inform each other.)

### ★ THE SHARP REFORMULATION — E5 IS A CONTEXTUALITY TEST
With η built as above, "η is a pure gradient" means exactly: *there is one number f(u) per
organ with η_(u,v) = f(v) − f(u)*, i.e. **each organ pushes every sub-claim it touches by the
same amount**, so a single global assignment explains all pairwise data. Non-gradient mass
means no such assignment exists — pairs locally consistent, not globally glueable.
**That is Abramsky–Brandenburger contextuality**, which §5r already names as the QI thread.
The harmonic part is the contextuality no filled 2-simplex can repair — which is precisely
why it, and not curl, is the growth address.

Free necessary condition now logged every run: **push spread** = sd of organ u's push across
the sub-claims it participates in. **Spread = 0 ⇒ pure gradient by construction ⇒ FAIL before
the Hodge split is consulted.** Observed mean spread: 0.107 — small but nonzero.

### 🔍 THE FAIL IS NOT UNIFORM, AND THE EXCEPTION IS MECHANISTIC
- **The controls behaved correctly** (0.058, 0.066 — near-pure gradient). On a question
  everyone agrees on and one nobody can reach, there is genuinely nothing to glue.
  Contested is **3.4× the controls**. So the instrument is NOT emitting noise; it does track
  real disagreement. That is what makes this FAIL informative rather than vacuous.
- **Q-ikeda averaged 0.438, ABOVE the null**, driven by one repeat at **0.778 with 65%
  harmonic mass whose support was exactly the two unfilled-cycle edges**
  `(Verify,Context) = +0.520` and `(Reason,Context) = −0.462`. The mechanism produced an
  address, in the right place, once.
- Reading the raw records explains when: in that repeat the model named genuinely *distinct*
  sub-claims per pair ("Relevance of representation theory" / "Existence of published proof" /
  "Correctness of derivation") and Reason's push varied 0.80→0.60→0.30 across them. In the
  low repeats the sub-claims were near-duplicates and each organ's push was near-constant.
- Quantified: **corr(push spread, non-gradient fraction) = +0.548, permutation p = 0.057,
  n = 15.** Suggestive, NOT significant at 0.05. Do not lean on it.

### WHAT THIS DOES AND DOES NOT LICENSE
- ❌ It does **not** show H¹ is always zero for real organs. This is a **pilot with SIMULATED
  organs**: all judgements come from ONE model in ONE call (batching is mandatory per §5s
  finding 3), and a single mind asked for related numbers is biased *toward* consistency —
  i.e. **the protocol is biased toward FAIL**, and it failed.
- ✅ It **does** mean: per §7's own stated FAIL action, **stop before building on it.** Do NOT
  write the Φ_∞ stopping rule, the aiming 2×2, or §5p's growth law as settled theory. Q25 (θ)
  is moot until this passes — there is nothing to threshold.
- ✅ It **does** identify the precondition for a rerun to be worth anything: organ judgements
  must be genuinely **contextual**. Non-contextual organs ⇒ pure gradient ⇒ no growth address,
  as a matter of arithmetic rather than of evidence.

### NEXT ON THIS THREAD (E5b, the decisive version — NOT yet run)
The pilot's confound is that one model produced every judgement. The decisive test is
**real organs**: each organ's push computed from its OWN stalk/state (Librarian from retrieved
evidence, Verify from an actual `verify/check.py` verdict, Context from live working memory),
so no single mind is enforcing consistency. Cheap intermediate if that is too big a step:
force per-pair sub-claim distinctness and split the call per pair (5× cost, breaks the
single-mind coherence). **Until one of those passes, the growth law stays unbuilt.**

### ⚠️ NEW FIX-REGISTRY ITEM
- **FIX-12 (H) — the organ judgement contract is the wrong type.** `MOS_FINALIZATION.md`
  Q9/Q10/Q11 and §7 specify a symmetric `agreement`; a 1-cochain is antisymmetric, and
  antisymmetrising a symmetric score yields η ≡ 0. Replace with the (sub-claim, push_u, push_v,
  confidence) contract implemented in `experiment_e5.py`. The `.tex` inherits this.

**Tests:** `hodge.py` 11/11 · `experiment_e5.py` 3/3 (incl. both FAIL and PASS modes proven
detectable by construction) · closed-form nulls match 40k-draw Monte Carlo to <0.01.
`--analyze` re-scores the recorded data at **zero API cost** — which is exactly what E7 was
for, and it already paid off once when the verdict thresholds had to be replaced.

## 5w. E5 VERDICT RETRACTED + THE BELIEF LAYER (2026-07-29, later same day)

### 🚨 THE RETRACTION — a positive control killed my own verdict
§5v declared FAIL. Two independent errors, both found by tests I should have run first.

**(1) The p-value was overstated ~4–10×.** One-way ANOVA on the 9 contested
measurements: MSB ≈ 0.119, MSW ≈ 0.032 ⇒ **ICC ≈ 0.48**, design effect ≈ 1.96,
**n_eff ≈ 4.6 not 9**. Corrected: z ≈ −1.56, **p ≈ 0.06**; or p ≈ 0.12 with questions
as the unit (n=3, t-test). I flagged the clustering as a caveat and then reported
0.014 anyway. Don't do that again.

**(2) ⭐ THE STATISTIC COULD NOT SUPPORT THE VERDICT.** We had two NEGATIVE controls
and **no positive control** — nothing ever established the instrument could report an
obstruction that *is* there. Added two probes (`--probe`, 6 calls):

| probe | ground truth | non-grad fraction | **\|L₂\|** |
|---|---|---|---|
| **P1** rock-paper-scissors of competence (Verify beats Reason on algebra, Context beats Verify on scope, Reason beats Context on entailment) | cycle present | **0.214** | **1.23** (0.90–1.60) |
| **P2** nested competences | no cycle | 0.084 | **0.20** (0.00–0.40) |

> **P1 — cycle planted by construction — scores 0.214. The contested questions scored
> 0.209.** The statistic behind the FAIL cannot tell a known-positive from the data.
> **Verdict withdrawn.**

**Why the fraction fails:** it is a *share*. P1's ‖η‖ was 1.57–1.81 because Search was
uniformly weak — a large pure-**gradient** component. The obstruction was real and
large; dividing by total disagreement diluted it to 0.21.

**On |L₂| — the sum round the unfilled cycle — the instrument separates 6.2× with no
overlap in range.** It sees obstructions and does not invent them. Rescored:

| | Q-ikeda | Q-cp3-gap | Q-rho-truth | b1 (ctrl) | lemon (ctrl) |
|---|---|---|---|---|---|
| \|L₂\| | **0.63** | 0.33 | 0.13 | 0.23 | 0.18 |

Contested 0.36 vs a no-obstruction null of 0.20. **Weak positive, underpowered.**
corr(push spread, non-gradient) now **p = 0.015** at n=21 — the interaction story is
significant.

**Power:** to resolve a 0.19 shift against sd 0.262 needs ~12 *independent* units, and
with ICC 0.48 the unit is the QUESTION. 5 questions × 3 repeats was the wrong
allocation; **~12 questions × 2 repeats ≈ 25 calls** is right.

### ⚠️ CONSEQUENCE FOR THE THEORY, NOT JUST THE EXPERIMENT
§5r's control rule `Φ_∞/‖η‖² > θ ⇒ GROW` is a **fraction**, and P1 just demonstrated
that a real, large obstruction scores 0.21 on exactly that fraction when ordinary
rankable disagreement sits alongside it. **The rule as specified will systematically
under-trigger.** Worse: `Φ_∞ = ‖η_H‖² + ‖η_C‖²` **sums the two things that encode the
adapt-vs-grow distinction** — curl ⇒ repair an existing 2-simplex, harmonic ⇒ attach a
cell. Q-ikeda r2 was almost pure curl (0.242/0.013), r3 almost pure harmonic
(0.649/0.128): opposite correct remedies, identical Φ_∞ treatment.
**Decided (Charbel): split them, give them different remedies, drop θ for a measured
noise floor (|L₂| ≈ 0.20 from P2). Q25 dissolves rather than gets answered.**

### 📐 MODEL COMPARISON IMPORTED — with a correction that sharpens it
Charbel's import: *"given disagreement, how do I rewire?"* is structure learning / DCM,
answered by model comparison, not a threshold. **But `grow iff F(C+cell) − F(C) > 0`
never fires**, and structurally: with η measured on the OLD edges, a new vertex w
appears in NO term of the fit (x_w is unconstrained), and filling a triangle leaves δ⁰
untouched. Accuracy is unchanged, complexity rose ⇒ ΔF < 0 always.
> **Adding structure cannot improve the explanation of data you already have.
> Growth is inherently a claim about FUTURE reconcilability.** That rules out a whole
> class of designs and is worth more than the criterion as stated.

Repair — three nested models:
| model | fitted | decidable on current data? |
|---|---|---|
| **M0 flow** | x only | ✅ |
| **M1 adapt** | x and R (learned maps) | ✅ |
| **M2 grow** | enlarged complex | ❌ needs held-out or **persistence** (= §5p's "*persistent* obstruction"; persistent homology is the existing machinery, cf. D1) |

**Q4 (Householder m) is answered as a by-product**: m is the complexity knob, chosen by
model evidence rather than by hand.

### ✅ THE BELIEF LAYER — `python/belief.py` (NEW, 13 self-tests, 0 API calls)

**Charbel's question — "since we discussed what the sheaf should be, shouldn't we use it
when modelling uncertainty?" — caught a real defect.** The first design computed Σ_v from
each organ's own concepts and stopped: a LOCAL estimate wearing sheaf vocabulary.

The sheaf's actual contribution. The engine already implies a Gaussian model whose
consistency term IS ω, so the posterior precision of the whole system is
$$\Lambda = \mathrm{blockdiag}(\Sigma_v^{-1}) + L, \qquad L=\delta^\top\Pi\delta$$
- **Σ_v is the PRIOR, not the answer.** `sheaf_diffusion()` already computes the posterior
  MEAN; nobody had ever computed the **covariance**, which is where the structure is.
- **Uncertainty is NON-LOCAL**: `[Λ⁻¹]_vv` depends on degree, neighbours' precisions, topology.
- **`−½ log det Λ` IS the Occam factor** for M0-vs-M1. The density-matrix layer and the
  rewiring criterion turn out to be *the same object*.
- **It rescues the entropy diagnostic.** I had argued orthogonal maps give ΔS ≡ 0 so we'd
  need lossy contractions. True of *transport* entropy, false of *posterior* entropy: Λ's
  diagonal blocks get `R ᵀπR = πI` (R-independent) but the **off-diagonal** blocks get
  `−π R_uᵀR_v`, the relative rotation. So Householder stays, ‖R‖≤1 and Anderson–Morley
  stay, and the field is live.

**★ THE MEASURED NUMBER: `sharpening(v) = S(prior) − S(posterior) ≥ 0`** — how much
certainty an organ gains *from being part of the complex*. Non-negative by theorem
(adding PSD L can only increase precision); asserted over 200 random configurations.
Verified: Reason with 1 edge **1.76 nats**, with 3 edges **3.23 nats**; a disconnected
organ gains **−9.3e-13** (exactly nothing); π 0.01→100 moves total 0.52→41.07 nats.
**This is "the whole exceeds the parts" as a number the engine prints (A17: passes).**

### ✅ BLOCKER 2 (D = 1.0) SOLVED — and E4 closed with it
D was two incompatible things (epistemic confidence *and* semantic breadth) forced into an
isotropic variance in 384 dims — the one shape guaranteeing E4's blow-up. Fix:
1. **D demoted to a floor**; all real uncertainty moves into the low-rank U.
2. **⚠️ The invariant is NOT "shared eps" — it is "floor = O(1/d)".** I had it as the
   former, which is sufficient but too strong, and it forced the isotropic prior into U
   giving **k = 387 and 6.0 s per report at d=384**. Correct statement: the covariance must
   carry trace O(1) (matching unit-normalised embeddings), so `d(√D₁−√D₂)²` is O(1) and
   stays commensurate with `‖μ₁−μ₂‖² ≤ 4`. E4's 229.75 came from D = O(1) ⇒ d·O(1).
   Now enforced as an explicit guard that **refuses** configurations exceeding the semantic
   scale. After folding the isotropic prior into the floor: **k = 3–6, 0.128 s (47× faster),
   `log det Λ` bit-identical at 9924.2665, Bures headroom 0.005 vs 4.**
3. **Shrinkage prior** `Σ_v = (S_v + κΣ₀)/(n_eff+κ) + εI`, n_eff = Kish. Fixes a real
   inversion: a concept seen ONCE currently gets U empty ⇒ Σ = εI ⇒ **maximum confidence
   from a single sighting**. Now n=1 ⇒ Σ ≈ Σ₀ (broad), → empirical as evidence accumulates.
4. **Entropy quantity = effective rank** `exp(H)` of the normalised signal spectrum, not raw
   von Neumann (which at d=384 is dominated by the floor and says nothing).

`module_vertex.stalk_gaussian()` added **alongside** `stalk()`, which stays byte-identical
— it is load-bearing for the C++ parity test (§5j) and the ρ calibration (§5h).

**Cost control:** Λ is 2688×2688 at n=7,d=384 and is never formed. Kronecker + matrix
determinant lemma ⇒ an n×n det plus a K×K det (K=Σk_v). Dense path retained ONLY as a
test oracle; fast and dense asserted equal to 5.7e-14. Non-identity maps break the
factorisation and are **refused** rather than silently falling into a minutes-long solve.

### ⚠️ NEW FIX-REGISTRY ITEMS
- **FIX-13 (H) — `cognitive_state.cpp:224` / `curator.cpp:20` still hardcode D=1.0 with
  empty U.** The Python fix above is not ported. Until it is, C++ W₂ remains Euclidean and
  every C++ entropy identical.
- **FIX-14 (M) — `verdict()` in `experiment_e5.py` still gates on the isotropic-fraction
  null.** Must move to the probe-calibrated absolute statistic. It currently prints FAIL on
  data that no longer supports it.

**Tests:** `belief.py` 13/13 · `hodge.py` 11/11 · `experiment_e5.py` 3/3 · `coherence.py`
15/15 · `module_vertex.py` demo clean. No regressions. Today's spend: **22 Groq calls**.

## 5x. ⭐ E5 RUN 2 — **PASS**, but weakly, and the address is an artifact (2026-07-29, later still)

Closes **FIX-14**. Run 2 = 32 calls (16 questions × 2 repeats); combined with run 1 + probes
the dataset is **53 measurements** in `python/e5_elicitations.jsonl`. Prompt for non-probe
questions is byte-identical to run 1, so the two runs are poolable. Today's total: **54 calls**.

### ✅ FIX-14 CLOSED — the gate moved off the isotropic-fraction null
`verdict()` now gates on **|L₂|, the absolute obstruction round the unfilled cycle**,
calibrated by the probes, with **the QUESTION as the independent unit** (ICC ≈ 0.48, §5w)
and a percentile bootstrap CI. Added `_q_means`, `_bootstrap_ci`, `calibration`, and a
**Gate 0 the old verdict lacked: if P1 does not clearly exceed P2 the instrument is blind
and nothing else in the run is licensed.** Run 1's allocation error is also fixed —
9 new contested questions, repeats cut 3 → 2.

### THE RESULT

| | \|L₂\| |
|---|---|
| **P1 — planted cycle** | **1.22** |
| **P2 — no cycle (the null)** | **0.26** |
| **contested, 12 questions** | **0.41**, 95% CI **[0.28, 0.53]** |
| controls, 2 questions | 0.22 |

Instrument sensitivity re-confirmed at n=5 each: **4.7×**. Contested clears the null with
the CI excluding it — but only at **15% of the planted-cycle level**.

| question | \|L₂\| | | question | \|L₂\| |
|---|---|---|---|---|
| Q-prop82 | **0.75** | | Q-cp3-gap | 0.34 |
| Q-wfr | **0.65** | | Q-morse-bott | 0.30 |
| Q-witten | 0.55 | | Q-rho-truth | 0.15 |
| Q-h1-b1 | 0.55 | | Q-am-novel | 0.15 |
| Q-householder | 0.52 | | Q-fca | **0.00** |
| Q-ikeda | 0.48 | | Q-commute | 0.45 |

`Q-fca = 0.00` is the right answer, not a failure: on a pure design question every organ
defers to Context, so there is genuinely nothing to glue.

**Mechanism now solid:** corr(push spread, non-gradient) = **+0.449, permutation p = 0.0008,
n = 53**. The organ×claim interaction (§5w's exact iff) is confirmed as the driver, no longer
marginal.

### ⚠️ HOW STRONG IS THIS, HONESTLY — weaker than the verdict line says
**The CI does not propagate uncertainty in the calibration.** The null 0.26 is itself
estimated from 5 P2 measurements, se ≈ 0.076. Folding that in:

| treatment | t | one-sided p |
|---|---|---|
| as `verdict()` computes it (null taken as exact) | 2.28 | **0.022** |
| null uncertainty folded in | 1.48 | **0.083** |

**Read it as p ≈ 0.02–0.08. Marginal-positive, NOT established.** Same class of error as
run 1's overstatement, caught this time before publishing the number. → FIX-15.

### 🚨 THE "CONSISTENT GROWTH ADDRESS" IS AN ARTIFACT — nearly reported as a finding
Every measurement carrying harmonic mass named the same two edges, `(Verify,Context)` and
`(Reason,Context)`. That looks like striking localisation. **It is forced by the geometry.**
With b₁ = 1 the harmonic subspace is ONE-dimensional, so every harmonic component is a scalar
multiple of the same fixed vector h ∝ (⅓, ⅔, −1, ⅓, 1); the two largest entries are RC and VC
*by construction*, whatever the data says.

> **A 1-dimensional harmonic space can report THAT an obstruction exists but can NEVER report
> WHERE.** The address carries exactly zero bits. §5p's growth law needs the address, so the
> minimal configuration — chosen in §7 precisely because it is minimal — is structurally
> unable to test the half of the story that matters.

**⇒ NEW REQUIREMENT: the next configuration must have b₁ ≥ 2.** That is the difference between
"there is an obstruction" and "here is where to grow", and it costs roughly the same per run.

### WHERE THIS LEAVES THE THEORY
- The mechanism is **alive**, reversing §5v. The instrument is validated in both directions.
- The measured obstruction is **real but small** (~1/6 of a constructed one) and **not yet
  solidly significant**.
- **Localisation is currently impossible by construction** — the binding limitation, and the
  one to fix next.

### ⚠️ NEW FIX-REGISTRY ITEM
- **FIX-15 (M) — `verdict()` treats the probe calibration as exact.** The null level is an
  estimate with its own se; the bootstrap CI should be over both. Currently overstates
  significance by roughly 4×, the same failure mode as run 1's ICC error.

## 5y. E15 ANSWERED (**NO**) + F(M1) vs F(M0) BUILT — and Q16 gets a DERIVED scale (2026-07-29)

### ❌ E15 CLOSED — WFR/HK has NO Bures-analogue between Gaussians
**First citations in this project that were actually SEARCHED, not recalled.** The standing
⚠️ on §5r's bibliography is lifted for these four.

| claim | status |
|---|---|
| Liero–Mielke–Savaré, *Optimal Entropy-Transport problems and a new Hellinger–Kantorovich distance*, **Inventiones mathematicae** (2018), arXiv:1508.07941 | ✅ **verified** — cite as is |
| Chizat–Peyré–Schmitzer–Vialard, *An Interpolating Distance between Optimal Transport and Fisher–Rao* | ✅ exists, as described |
| **Janati–Muzellec–Peyré–Cuturi, *Entropic OT between Unbalanced Gaussian Measures has a Closed Form*, NeurIPS 2020, arXiv:2006.02572** | ✅ **NEW — was not in our bibliography.** Closed form, but **entropic** (Sinkhorn-regularised): a different object with an extra parameter ε |
| arXiv:2605.02497 (2026), *Closed Forms for Gaussian KL Unbalanced OT without Coupling Entropy* | ✅ closed form, **but** the covariance map is the solution of a **Riccati equation**, and the penalty is **KL, not HK** |

What exists for HK proper: an explicit **cone formula between Diracs**,
`HK²(δ_{x₁}m₁, δ_{x₂}m₂) = m₁ + m₂ − 2√(m₁m₂)·cos(|x₁−x₂|)` (cut off at π/2); LMS §7.8 treats
"Gaussian Hellinger–Kantorovich"; and HK-Boltzmann gradient flow preserves Gaussians with
explicit ODEs. **No single closed-form distance between two arbitrary Gaussians surfaced.**

> **VERDICT: NO, in the operative sense.** The nearest results either regularise (entropic —
> different object) or need a **Riccati solve per pair**: O(d³)×iterations ≈ 5.7e7 flops per
> pair at d=384, against Bures at ~520K flops for **all 21 edges** (§5s). Two to three orders
> of magnitude worse, per pair. That is exactly §7's stated FAIL condition — "needs an
> optimisation solve per distance evaluation, dead on the per-tick path".

**⇒ Per §7's own decision rule: Q2c COLLAPSES TO THEORY. The merge metric stays plain
Bures–Wasserstein.** δ (the concept-identity length scale) is not available via WFR, so the
merge/split question loses its interpretable parameter and must be settled another way.

*Possible escape, flagged NOT claimed:* our stalks are now rank-k with k = 3–6 (§5w), and a
Riccati on a rank-k-plus-floor structure may reduce to k×k. Unverified. Do not build on it.

### ✅ F(M1) vs F(M0) BUILT — `belief.py` model comparison (tests 13–16)
Integrating the latent state out exactly (both factors Gaussian) gives, with
`P = blockdiag(Σ_v⁻¹)` and `Λ = P + L`:
$$-2\log p(\mu) = \underbrace{\mu^\top(P - P\Lambda^{-1}P)\mu}_{\text{accuracy}} + \underbrace{\log\det\Lambda}_{\text{Occam}} - \log\det P$$
Both terms come from the object §5w already builds. **No penalty had to be invented.**

- **13** general-R dense Λ reduces to the identity fast path exactly (261.08856219 both ways).
- **14** consistent organ reports beat inconsistent ones (F 287 vs 499).
- **15** learned maps cut accuracy 29.75 → 0.24 — **and M0 still wins**, because the parameter
  charge is 851.7. The comparison independently rediscovers §5s's RAM finding: a full
  orthogonal map is unaffordable **as a model**, not merely to store.

### ★ 15b — THE RESULT THAT MATTERS: one tick cannot afford ANY learned map
At real scale (d=384, n=7, 21 edges ⇒ **2688 observations/tick**):

| parameterisation | params | over-parameterised by |
|---|---|---|
| Householder m=1 | 8,043 | **3.0×** |
| Householder m=4 | 32,172 | **12.0×** |
| full orthogonal | 1,544,256 | **574.5×** |

> **Restriction maps CANNOT be learned from a single tick — even the cheapest one.** They
> require accumulation. That is precisely the two-complex model's slow crystallization
> γ₀ ≪ 1, which was adopted on anti-catastrophic-interference grounds; it is now **forced by
> the evidence**, independently.

### ★ 15c — Q16 (γ₀) MOVES FROM HAND-SET TO DERIVED
Accuracy gain accumulates **linearly** in observations while the BIC charge grows only
**logarithmically**, so the crossover T (least T with `T·gain > k·log(T·obs)`) gives
**γ₀ ~ 1/T** — the rate at which W may write back to 𝕂. New `ticks_to_justify()`.

⚠️ **The numbers printed (m=4 → T ≥ 32768 ⇒ γ₀ ~ 3e-5; m=1 → T ≥ 8192 ⇒ γ₀ ~ 1.2e-4) are the
METHOD demonstrated on a d=12 SYNTHETIC accuracy gain. They are NOT a calibrated γ₀.** The
real value needs the real per-tick gain measured on real organ data. What is established is
the *derivation route*, not the constant.

Two approximations, both named in code: **BIC** is crude (exact route = prior on R + Laplace
`−½ log det H_R`); and `ticks_to_justify` assumes **independent** per-tick gains, which they
are not — so T is a **lower** bound and γ₀ an **upper** bound.

### 16 — M2 (grow) confirmed undecidable on current data
ΔF = **+124.08**: growth rejected, as §5w predicted structurally. A new vertex appears in no
term of the fit and filling a triangle leaves δ⁰ untouched, so accuracy cannot improve while
complexity rises. **Growth is a claim about FUTURE reconcilability** — persistence or
held-out data, never current fit.

**Tests:** `belief.py` **16/16**. No regressions.

## 5z. CONE–BURES: δ RECOVERED, THEN MEASURED, AND THE CLAIM CUT DOWN (2026-07-29)

Charbel refused to accept E15's loss of δ and asked for an all-out attempt. New files:
**`python/cone_bures.py`** (10 test groups) · **`python/validate_cone_bures.py`** (V1).
Zero API calls. **Read §V1 RESULT before using any of this** — the construction works,
the *interpretation* I first gave it does not survive measurement.

### THE DIAGNOSIS THAT CONTAINED THE CONSTRUCTION
Bures exists because the W₂ cost `|x−y|²` is **quadratic**, and quadratic costs preserve
the Gaussian family (optimal map affine). HK's cone cost
`−2log cos(min(|x−y|/2δ, π/2))` is **not** quadratic, so the optimal plan destroys mass in
some regions and creates it in others and leaves the family. That is why no Bures analogue
exists — structural, not an oversight. **So: don't attack the cost, attack what is
transported.**

### THE CONSTRUCTION — three facts we already had, never combined
1. **HK IS a cone metric** (LMS): over any base metric space, `r = √mass`,
   `d² = r₀²+r₁²−2r₀r₁cos(min(d_base, π/2))`. **The construction needs only that the base
   be a metric space** — it does not care that the base is ℝᵈ.
2. **MOS's state space is the GAUSSIAN MANIFOLD**, not measures on ℝᵈ. So build the cone
   over **(Gaussian space, Bures–Wasserstein)** — a base whose distance we already compute.
3. **We already have mass**: the Hebbian weight `w(σ,t)`. Decay destroys it, reinforcement
   creates it. WFR's reaction term *is* bind/collapse, not an import.

Derivation: restricting the WFR action to Gaussian paths with spatially uniform growth and
substituting `r=√m` gives `𝒜 = ∫[r²|ẋ|²_BW + 4λṙ²]dt`, exactly the geodesic energy of
`ds² = 4λdr² + r²ds²_BW` — a metric cone over BW rescaled by `1/(2δ)`, `δ=√λ`. Hence
$$D_\delta^2 = w_0 + w_1 - 2\sqrt{w_0w_1}\cos\!\big(\min(d_{BW}/2\delta,\ \pi/2)\big)$$

- **Metric**: capping a metric preserves the triangle inequality; the cone over a metric
  space is a metric (BBI 3.6.13); `d̄ ≤ π/2 < π` so the min is inactive. **Tested: 20,000
  random triples across five δ, worst violation exactly `+0.000e+00`.**
- **Rank-k reduction**: `W = span(U₀)+span(U₁)`, `dim p ≤ 2k`; both `Σ₀^{1/2}` and `Σ₁`
  preserve `W` and act as scalars on `W^⊥`, so only a `p×p` square root is formed.
  Verified against dense: **max err 3.2e-12** over 200 pairs. **259.7 µs/pair at d=384,k=6
  ⇒ 5.45 ms/tick for 21 edges** (the Riccati route E15 rejected: ~10¹⁰–10¹¹ flops/tick).
- **Three limits, measured**: δ→∞ gives weighted Bures to **1e-8** (day-one degradation
  exact, convergence `O(1/δ²)`) · `d_BW=0` gives pure Hellinger `(√w₀−√w₁)²` to 1e-12 ·
  beyond `πδ` **saturates at `w₀+w₁`** and stays there (cutoff fires exactly at πδ), so
  **D² is bounded — which independently kills the E4 runaway.**

### 🚨 V1 RESULT — THE BOUND IS TIGHT ONLY FOR CONCENTRATED STALKS
Built an **exact** HK solver (no entropic ε): semi-coupling form, constraints decouple
(m₀ by rows, m₁ by columns), and each block step is closed-form — with `t=√m₀` the
constraint makes `Σt²` constant so the step is `max⟨t,s⟩` s.t. `‖t‖=√μᵢ`, i.e.
`t = √μᵢ·s/‖s‖` by Cauchy–Schwarz. Diracs exact to 4e-16; far-apart exact.

**✅ SOLVER CAVEAT RESOLVED — and it was milder than first recorded.** A first pass capped
at 3,000 iterations failed check 3 (ratio 1.05/1.32/1.60) and I recorded the solver as
unreliable. A 60,001-iteration run on a finer grid shows it is a **convergence-RATE issue
at very large δ, not a solver defect**:

| δ | 3,000 iters | **60,001 iters** |
|---|---|---|
| 20 | 1.0494 | **1.0003** |
| 60 | 1.3248 | 1.0238 |
| 200 | 1.6000 | 1.2189 |

At δ=20 it is essentially exact. Slow convergence only bites where the objective is O(1e-5).
**The measurement below runs at δ=1, well inside the reliable regime**, and the two runs
agree to ~1–3% with the better-converged one giving marginally *larger* gaps. So the
"lower bound" caveat stands but is **quantified at ~1–3%**, not open-ended.

Numbers below are from the 60,001-iteration run.

| σ (spread) | D²/HK² at sep 1 | at sep 2 | `1+σ²/δ²` |
|---|---|---|---|
| 0.15 | 1.022 | 1.030 | 1.02 |
| 0.30 | 1.094 | 1.116 | 1.09 |
| 0.60 | 1.369 | 1.414 | 1.36 |
| 1.00 | 2.010 | 2.039 | 2.00 |
| 1.50 | 3.240 | 3.210 | 3.25 |

**★ EMPIRICAL LAW FOUND: `HK_true² ≈ D²/(1 + σ²/δ²)`** to ~3% over a 10× spread range and
every separation (the ratio is also near-constant in separation at fixed σ: 1.33→1.50
across sep 0.25→3.14). Mechanism: true HK destroys the non-overlapping **tails**
selectively; our uniform-growth restriction must move or destroy the whole lump, and the
penalty scales with how much tail there is.

### ❌ THE SPREAD CORRECTION IS DEAD — it breaks the metric
`D̃² = D²/(1+σ_eff²/δ²)` would buy most of that accuracy back. Tested:
**worst triangle violation +1.08 at δ=0.3 and +0.54 at δ=1.0** — structural, not numerical.
Holds only at δ=3 where the correction is ≈1 anyway. **Usable as a ranking SCORE, never as
a metric; merge transitivity is lost.** Not adopted.

### 🚨🚨 CORRECTION (V1c, `python/validate_regime.py`) — THE REGIME CLAIM BELOW IS WRONG
The section that follows concluded MOS sits at σ/δ ≳ 0.5 and therefore at ~50% agreement.
**That was my error and it inverts the verdict.** I read the regime off **‖U‖_F**, which
aggregates over all 384 dimensions and all k columns. What the transport problem sees is the
spread **along the separation direction**, `σ_dir² = ûᵀΣû`, `û = Δμ/‖Δμ‖`. Since the rank-k
covariance is mostly orthogonal to Δμ (k ≪ d), σ_dir is far smaller than ‖U‖_F.

Measured, on stalks built the way `belief.py` builds them (calibrated to the logbook's own
5h/E1 cosine statistics — cos_within ≈ 0.833, unit-normalised bge-small):

| concepts/organ | ‖Δμ‖ | **σ_dir** | d_BW | δ (πδ = d_BW) | **σ_dir/δ** | implied gap |
|---|---|---|---|---|---|---|
| 2 | 1.361 | 0.0440 | 1.389 | 0.442 | **0.100** | 1.010 |
| 5 | 1.317 | 0.0400 | 1.369 | 0.436 | 0.092 | 1.008 |
| 25 | 1.291 | 0.0361 | 1.340 | 0.427 | 0.085 | 1.007 |
| 50 | 1.291 | 0.0355 | 1.329 | 0.423 | **0.084** | 1.007 |

**σ_dir ≈ 0.035–0.044, not ~0.3. So σ_dir/δ ≈ 0.084–0.100 — the BEST row of the table
below, not the worst: ~87% predicate agreement and a value gap under 1%.**

Two further points, both checked against the V1 data:
- **The governing ratio really is σ/δ, not Mahalanobis separation.** Two V1 configurations
  with identical `R = sep/σ = 6.67` give different gaps (1.022 vs 1.116), whereas the law
  `1 + (σ/δ)²` fits every point to ~3% independently of separation. So the §5z framing was
  right; only my estimate of σ was wrong.
- **The residual ~13% disagreement is concentrated near the cutoff**, where any boundary is
  intrinsically uncertain — not spread uniformly. Less damaging than the bare figure suggests.

⚠️ Calibrated simulation, not live bge-small embeddings. It fixes the order of magnitude,
which is what the question turns on. **Measuring σ_dir on the real corpus is now owed (V6).**

### 🚨 AND THE OPERATIVE NUMBER IS WORSE THAN THE VALUES ~~(in MOS's regime)~~ — SEE THE CORRECTION ABOVE
Merge-predicate agreement (`is_same_concept` vs HK saturation), by concentration:

| σ/δ | 0.10 | 0.20 | 0.30 | 0.60 | 1.00 | 1.50 |
|---|---|---|---|---|---|---|
| agreement | 86.7% | 76.7% | 63.3% | **50.0%** | 50.0% | 50.0% |

(n=30 per row, 60,001-iteration solver. A coarser 16-point/3,000-iteration pass gave
87.5/75.0/62.5/50.0/50.0/50.0 — the pattern is stable, so this is not a resolution artefact.)

~~**MOS's regime is structurally in the bad half.** Unit-normalised embeddings give
`‖μ₀−μ₁‖ ≤ 2`, so δ ≤ 2/π ≈ 0.64; stalk spread is σ ~ 0.3–0.45, hence σ/δ ≳ 0.5 always ⇒
~50% agreement ⇒ chance level.~~ **RETRACTED — see the V1c correction above. σ was read off
‖U‖_F instead of the directional spread; the true σ_dir ≈ 0.04 puts MOS at σ/δ ≈ 0.09,
i.e. ~87% agreement and a sub-1% value gap.**

### ✅ BUT IT IMPROVES WITH ACCUMULATION — and that is testable
`σ² ≈ S/(n_eff+κ)`. At n=5, σ~0.3; at n=50, σ drops ~2.9× to ~0.10, giving σ/δ ~0.16 and
**~80%+ agreement**. So the metric becomes reliable *as organs accumulate concepts* —
slope not intercept, the project's own thesis, and a concrete prediction to test.

### ❌ V4 — NOT NOVEL. Cite, do not claim.
Searched. Prior art exists: **"weighted Wasserstein–Bures" distances for unbalanced
transport with BW as the balanced case, forming complete geodesic cones with radial (mass)
/ angular (shape) splitting** (see *Conic Formulations of Transport Metrics for Unbalanced
Measure Networks*, arXiv:2508.10888), and the cone-over-unit-trace-PSD-with-Bures = BW
identification (which is §5t's own SPD≅cone-over-density-matrices observation). **The
construction must be cited, not presented as new.** Under A17 that is fine: it earns its
place by changing a number the engine prints, not by novelty.

### WHERE THIS HONESTLY LEAVES US
**SURVIVES:** a genuine metric with a length scale · bounded distance (E4 runaway killed) ·
a **structural** merge predicate instead of a threshold · mass = Hebbian weight inside the
metric · exact day-one degradation · 5.45 ms/tick · **and, per V1c, agreement with true HK
to under 1% in value and ~87% on the merge decision at MOS's measured σ_dir/δ ≈ 0.09**.
**DOES NOT SURVIVE:** novelty (V4) · and the bound is only this tight *because* our stalks
are concentrated along the separation direction — it degrades fast if σ_dir/δ ever rises
above ~0.3, so σ_dir/δ must be **monitored, not assumed**.

> **δ is recovered and usable.** The construction is not new mathematics (V4) and it is not
> literally WFR (it is the cone over Bures rather than over ℝᵈ, an upper bound by
> construction) — but in MOS's measured regime it tracks true HK to under 1%, which is far
> better than the qualitative agreement we would have settled for. The path there ran
> through two of my own errors: an over-alarmed solver caveat, and reading the regime off
> the wrong norm. Both were caught by measurement, which is the only reason the number can
> be trusted now.

### ⚠️ STILL OWED
- ~~**V1b** — a non-stalling HK solver.~~ ✅ **Resolved by the 60k-iteration run**: the
  solver converges (δ=20 → 1.0003); it was iteration budget, not a defect. Residual
  caveat quantified at ~1–3%. A proper accelerated solver would still be needed to certify
  the very-large-δ regime, but that regime is not where MOS operates.
- **V2 / E14** — calibrate δ by sweep on ~50 hand-labelled pairs; publish the SENSITIVITY
  CURVE, never a fitted value. Test 7 confirms the predicate is monotone in δ, so the
  sweep is well-posed. **Needs Charbel: the labels.**
- **V3** — the VerifyOp route (a merge that is later Refuted more often than the unmerged
  pair was wrong). Needs accumulated sessions.
- **V5** — test the accumulation prediction: does agreement rise with n_eff? V1c already
  shows σ_dir falls 0.044 → 0.036 from 2 to 50 concepts, so the direction is confirmed;
  the agreement measurement itself is still owed.
- **V6 (new, from V1c)** — measure **σ_dir on the real corpus** with live bge-small
  embeddings. V1c is a calibrated simulation; it fixes the order of magnitude but the whole
  verdict now rests on σ_dir/δ ≈ 0.09, so that number must be measured, not simulated.
  **Add σ_dir/δ to the per-tick telemetry** — if it ever drifts above ~0.3 the metric's
  agreement with HK collapses and we need to know immediately.

## 5aa. THE FINALIZATION QUESTIONNAIRE CLOSED (2026-07-30) — four decisions by Charbel, curvature held open

Before any further building, the 🔴 questions in `MOS_FINALIZATION.md` §D were put to Charbel.
**Three of them had MOVED since the questionnaire was written and the stale versions were not
put to him** — recording that, because answering the old Q9/Q11 would have re-standardised a
contract that FIX-12 already proved is the wrong type.

### ✅ F10 — DISSOLVED, not answered. The K₀ / Jordan–Hölder memory schema is DROPPED.
Both categories the book offers fail: in `Hol(𝒟)` every Gaussian concept is a *simple* module
(k[x] is simple over the Weyl algebra in char 0) ⇒ JH length 1, and the K₀ class says no more
than "which memory is this"; in `Rep(Q)` the K₀ class **is** the dimension vector, which
collides catastrophically as a retrieval index. Jordan–Hölder guarantees canonicity *given* a
category and cannot pick the atoms.
**Decision: adopt §5r's position — the two-complex 𝕂/W model supplies memory identity through
GROWTH HISTORY, so the canonical-schema programme is dropped rather than forced into a
category.** Same reasoning that rejected FCA: canonicity and growth are in tension and we chose
growth. Filed as a dead end in §6.

> **🚨 CORRECTION (2026-07-30, later) — F10 WAS NOT ACTUALLY BLOCKING, AND I SAID IT WAS.**
> `MEMORY_MODEL_TWO_COMPLEX.md` **already dissolved F10 on 2026-07-27**: its header says
> "closes finding F10", and §"what remains unclaimed" states "The category question (audit F10)
> is **dissolved, not answered.** This model does not require memories to have canonical atoms,
> so it does not need Jordan–Hölder, K₀, or Ext¹." The decision above is therefore a
> **re-confirmation, not a new resolution**, and 𝕂/W implementation was never actually waiting
> on it. What made it *look* blocking is a **stale "NEXT" line in §5t** ("blocking, and it is a
> modelling decision: CHOOSE THE CATEGORY"), written the same day and never updated after §5r's
> two-complex decision superseded it. **Lesson: a superseded "NEXT — BLOCKING" line is worse
> than no line, because it re-blocks work that was already unblocked.** The dead-end entry in §6
> and the reasoning both stand; only the claim that it was open is withdrawn.
> **Retrieval, for the record, is geometric not algebraic:** the k-fold closed star of the seed
> set (`ι*`), budget-gated on k, returning a *complex* rather than a top-n list. No canonical
> index is required anywhere, which is exactly why K₀ was never needed.

### ✅ Q9 / Q10 / Q11 — the ANTISYMMETRIC contract is now normative. Q9's ✅ is RETRACTED.
`MOS_FINALIZATION.md` Q9 records "a scalar in [−1,1] plus a confidence" as ANSWERED and Q11
defaults to `{u, v, agreement, confidence}`. **Both are wrong by FIX-12:** a 1-cochain is
antisymmetric and a symmetric `agreement` score antisymmetrises to η ≡ 0.
**Decision: standardise on `(sub-claim, push_u, push_v, confidence)` as implemented in
`experiment_e5.py`** — the contract that actually produced the §5x weak PASS — and judge
**bound pairs only** (Q10 default). Propagation owed: `MOS_FINALIZATION.md` Q9/Q10/Q11 and the
`.tex`. FIX-12 stays OPEN but now has a decided target rather than an open question.

### ✅ Q16 (γ₀) — USE THE DERIVED SCALE, not the hand-set 0.05.
§5y's affordability result (no restriction-map parameterisation is affordable on one tick)
forces γ₀ ≪ 1 **from evidence**. Adopted. E13 replay still validates rather than sets it.
Passes A17 on the nose: it deletes a decision a human was making by hand.

### ✅ Q4, Q19, Q21, Q25 — recommended defaults ADOPTED, logged as decided.
- **Q4** — Householder m = 4 (6 KB/map). E10 may escalate to Cayley r = 4 at ~2× cost.
- **Q19** — nothing is deleted from 𝕂; low-weight regions **demote to `gr` form** (keep the
  cells, drop the learned restriction maps back to identity). Content persists, structure decays.
- **Q21** — on Refuted, mark the supporting cells `Refuted` and exclude them from
  instantiation; do NOT delete. Full AGM contraction deferred.
- **Q25** — θ for the growth trigger = a **quantile of observed Φ_∞/‖η‖²**, same discipline as
  ε and κ_hi/κ_lo.
These are adopted so Phase 2 can start; the experiments (E10, E13) are free to overturn them.

### 🔵 Q5 / Q6 — HELD OPEN by Charbel's choice: the curvature controller gets discussed first.
Correct instinct — it is the only one of the mechanical questions that **actively moves weight
around**, i.e. the only one whose default can silently damage the store. See §5ab.

### ⚠️ Q2b / Q2c — the questionnaire is STALE and should be corrected.
Q2b is still listed 🔴; it was resolved in §5t (hybrid metric + explicit dispatch rule). Q2c
collapsed when E15 returned NO (§5y). Neither is open. Fold into the FIX-12 propagation pass.

## 5ab. THE CURVATURE CONTROLLER — SIX FINDINGS, DECISION STILL OPEN (2026-07-30)

Q5/Q6 held open per §5aa. Discussion raised six things, none of which are in `MOS_FINALIZATION.md`
Part C. **Decision NOT yet taken** — recorded now because the findings stand independently of it.

### ⚠️ C5-1 — Part C quotes the UNWEIGHTED Forman formula, but MOS's complex is WEIGHTED.
Forman's curvature is defined for *weighted* cell complexes (ratios `w_v/w_e`, sums over parallel
neighbours). `F(e) = 4 − deg u − deg v + 3m` is its **unit-weight specialisation**, as used in the
network-science literature. MOS carries a real coupling `w(σ,t) ∈ [0,1]` on every simplex — that
coupling *is* the plasticity substrate. **So Part C applies the all-weights-equal formula to a
complex whose weights are the entire point.** Same family as FIX-12: right formula, wrong type of
object. Not fatal (the combinatorial signal is still legitimate) but it must be a DECLARED
approximation, never a silent one. Options: use Forman's weighted form, or state the
specialisation and justify it.

### ⚠️ C5-2 — the coefficient 3 is an UNVERIFIED convention, and Part C introduces it while
claiming to remove a magic number (`decay = 0.1`). It is the standard unit-weight value but was
**not** derived from Forman's general formula here. Either derive it, or label it a convention and
let E11 report sensitivity to it.

### ★ C5-3 — THE STRONGEST ARGUMENT FOR FORMAN IS VALIDITY, NOT COST (new).
C.6's aiming 2×2 pairs κ (shape) against η_H (data), and its diagnostic power **depends on the two
axes being independent** — that is what licenses the top-right cell ("contradiction with no
structural cause ⇒ suspect the MEASUREMENT"). Augmented Forman reads only combinatorics and
**never touches a stalk**; Ollivier reads stalk geometry through both `W₁` and `d`. Under Ollivier
the axes partially correlate, a stalk-level artefact moves BOTH, and the self-diagnosis cell
degrades to noise. **Forman keeps the signals genuinely independent.**

### C5-4 — Ollivier got MORE available but is still off the per-tick path.
§5z's Cone–Bures supplies the principled ground metric `d` Ollivier needs. But `W₁` over
neighbourhoods costs `|N(u)|×|N(v)|` Cone–Bures evaluations per edge plus an LP, on top of a
metric measured at 5.45 ms/tick. "Forman first, Ollivier on flagged edges" survives — now for a
**measured** reason rather than an asymptotic one.

### ⚠️ C6-1 — "signal-only for two weeks" is a CALENDAR, not a criterion (fails A17).
Replace with **SHADOW MODE**: compute what `w` would become, record the counterfactual trajectory,
apply nothing. Strictly more informative than signal-only (which logs κ; shadow logs κ's
*consequence*) at the same zero cost. Then gate the live switch on evidence: E11 shows a
non-degenerate κ distribution **and** the shadow trajectory drives no edge to `w_floor` faster
than observed natural decay.

### ⚠️ C6-2 — TWO DIFFERENT ε's ARE ABOUT TO COLLIDE.
The flow's ε in `w ← (1 + ε·κ)w` is a **step size**; the coherence gate's ε in `ω > ε ⇒ RESOLVE`
is a **threshold**. Part C's prose conflates them ("the same move that fixed ε"). **Rename to
`ε_flow` and `ε_ρ` before implementation.**

### ⚠️ C6-3 — Q6 CANNOT BE DECIDED WITHOUT Q8, AND Q8's DEFAULT IS TOO WEAK.
The entire safety argument for the live flow *is* `w_floor`. Q8's default sets it to the bind
threshold itself, so C.4 reads "may decay to, but never below, the point of collapse." **A bridge
parked exactly AT the collapse point is not safe** — survival then depends on whether collapse
fires on `w < θ` or `w ≤ θ` and on floating-point luck. If the floor is to guarantee bridges
survive it must sit **strictly above** the trigger with a stated margin. Q8 is filed 🟡 but is
load-bearing for a 🔴.

### ⚠️ C6-4 — THE SIGN CONVENTION NEEDS A TEST, NOT A COMMENT.
MOS uses coupling (`w` = strength); the literature uses distance. Inverted, the controller
strengthens redundant edges and weakens bridges — **plausible-looking while quietly flattening the
store.** One-line invariant test: positively-curved edge's weight rises, negatively-curved falls,
floor holds.

### ❓ OPEN, needs one line from Charbel — is `w` capped?
C.3 sends `κ > κ_hi` to CONTRACT/FOLD while C.4 grows `w` when `κ > 0`. Reads as coherent and
intended (gaining weight *is* becoming a fold candidate), but **no `w_ceiling` is stated anywhere**
in Part C. Confirm whether `w` saturates at 1.

### RECOMMENDATION ON THE TABLE (not yet accepted)
- **Q5 = augmented Forman**, on C5-3, with C5-1 declared as an approximation and C5-2 declared a
  convention. Ollivier as selective escalation.
- **Q6 = shadow mode + measured gate**, bundled with the ε rename (C6-2), Q8 decided jointly with
  a strict margin (C6-3), and the sign-invariant test (C6-4).

## 5ac. Q5 DERIVED, NOT IMPORTED (2026-07-30) — the 3 is real and the WEIGHTS are the finding

Charbel refused to import Forman before bending it to MOS's case. Correct call: the derivation
closes C5-2 outright and turns C5-1 into something much more useful than a caveat.

### ✅ C5-2 CLOSED — the coefficient 3 is DERIVED, not a convention.
Forman's edge formula, for a p-cell α in a weighted complex:
$$\mathrm{Ric}(\alpha) = w_\alpha\Big[\sum_{\beta > \alpha}\tfrac{w_\alpha}{w_\beta} + \sum_{\gamma < \alpha}\tfrac{w_\gamma}{w_\alpha}\Big] \;-\; w_\alpha\!\!\sum_{\alpha' \parallel \alpha}\Big|\sum_{\beta > \alpha,\alpha'}\tfrac{\sqrt{w_\alpha w_{\alpha'}}}{w_\beta} - \sum_{\gamma < \alpha,\alpha'}\tfrac{w_\gamma}{\sqrt{w_\alpha w_{\alpha'}}}\Big|$$
where α ∥ α′ means they share a coface **or** a face, **but not both**. Specialise to an edge
`e = {u,v}` in a graph-with-triangles, all weights 1, `m = #{triangles ∋ e}`:
- **cofaces:** the m triangles, each contributing `w_e/w_f = 1` → **m**
- **faces:** the two vertices, each contributing `w_γ/w_e = 1` → **2**
- **parallel neighbours:** edges meeting e at a vertex number `(deg u − 1) + (deg v − 1)`. Of
  those, the `2m` edges that close the m triangles share a vertex **and** a coface, so the "not
  both" clause **excludes** them. Edges sharing a triangle but not a vertex cannot exist in a
  simplicial complex. → **deg u + deg v − 2 − 2m**, each contributing `|0 − 1| = 1`.

$$F(e) = (m + 2) - (\deg u + \deg v - 2 - 2m) = 4 - \deg u - \deg v + 3m \quad\checkmark$$

**So `3 = 1 + 2`: one from the coface sum, two from the pair of triangle edges REMOVED from the
penalty.** It is a consequence of the "not both" clause, not a tuning knob. Nothing to sweep.

### ★ C5-1 RESOLVED, AND IT IS THE REAL FINDING — the weights must be Π, not w(σ,t).
The instinct "don't import Forman unbent" pays off here. Forman's cell weights are **not**
decorative masses: they define the **inner product** in which the combinatorial Laplacian is
self-adjoint, which is the only reason a Bochner–Weitzenböck decomposition (and hence a Ricci
term) exists at all. So the weights are not ours to pick freely — **they are already fixed by
whichever Laplacian the engine actually uses.**

MOS's Laplacian is `L = δᵀΠδ` (§5p's precision-weighted ω), and `belief.py` puts
`Λ = blockdiag(Σ_v⁻¹) + L` on 0-cochains. Therefore:

| Forman cell weight | MOS's already-existing object |
|---|---|
| vertex `w_v` | `ν_v`, a scalar precision summary of the stalk (from `Σ_v⁻¹`) |
| edge `w_e` | **`π_e`**, the PC edge precision already inside Π |
| 2-cell `w_f` | **UNDEFINED — MOS has no inner product on 2-cochains** |

**Using `w(σ,t)` (the Hebbian coupling) as the Forman weight would compute the curvature of a
DIFFERENT Laplacian than the one the engine prints ω and ρ from.** That is the substantive error
C5-1 was circling, and it is worse than the unit-weight approximation: it would be a *consistent-
looking* number about the wrong operator. Substituting the table above:

$$\boxed{F_{\mathrm{MOS}}(e) = \pi_e^2\sum_{f \supset e}\frac{1}{\tau_f} \;+\; (\nu_u + \nu_v) \;-\; \sum_{\tilde e \parallel e} \nu_{\gamma(e,\tilde e)}\sqrt{\frac{\pi_e}{\pi_{\tilde e}}}}$$

with `γ(e,ẽ)` the shared vertex. Setting `π = ν = τ = 1` returns `4 − deg u − deg v + 3m`, so the
unit-weight formula is recovered exactly as the special case — day-one degradation, same
discipline as everywhere else.

### ~~⚠️ THE GAP THE DERIVATION EXPOSED — MOS has no 2-cochain inner product.~~
### ✅ **CLOSED by §5ag/V7 (marker was stale until 2026-08-03; see §5ar).** Option (b) below is
### what was built: `τ_f` = precision of the triangle circulation, the same derivation as `π_e` one
### dimension up. `curvature.hpp:56` — *"tau_f: the 2-cochain weight on face f, derived (5ag)."*
### **The residual that DOES stand: Forman's `w_α` prefactor placement (see HONEST LIMIT below).**
`τ_f` has no existing referent. `hodge.py` builds δ¹ so the 2-cochain *space* exists, but its
weighting is implicitly identity and was never chosen. Augmented Forman **needs** it. Two honest
options, and this is a real modelling decision, not a default:
- **(a) `τ_f ≡ 1`**, declared. Cheap, and the triangle term then counts filled cycles as the
  unit-weight formula does.
- **(b) derive `τ_f` from the 3-way coherence residual** on the triple — the natural analogue of
  π_e being the 2-way precision. More principled, gives the 2-simplices genuine computational
  work (the audit's standing complaint), and would make τ a *measured* quantity.
Recommend (b) if it is cheap to compute from what δ¹ already assembles, else (a) declared.

### ⚠️ A PREDICTION TO TEST, NOT A CLAIM — the low-precision limit may be backwards.
As `π_e → 0` the coface term dies like `π_e²`, the penalty like `√π_e`, but `(ν_u + ν_v)` is
untouched. So a **low-precision edge drifts POSITIVE** ⇒ `κ > κ_hi` ⇒ CONTRACT/FOLD. That would
mean chunking an edge *because we are unsure about it*, which is backwards. It may be damped in
practice by the ν terms. **E11 must check the sign behaviour against π_e explicitly** — flagged as
a prediction because I have not measured it.

### HONEST LIMIT OF THIS DERIVATION
The **combinatorial** content is verified by hand above, including the 3. The **placement of the
`w_α` prefactors** in Forman's general formula is taken from the literature and NOT re-derived
here from the Bochner argument — and the unit-weight check cannot distinguish placements, since
every weight is 1. If `F_MOS` ever becomes load-bearing for a published claim, that placement
needs deriving or citing precisely. It does not affect the unit-weight case we would ship first.

## 5ad. Q6 ANSWERED — THE FLOOR IS THE WRONG MECHANISM (2026-07-30)

Charbel: drop signal-only ("no make-believe"), C6-2 is a no-brainer, and for C6-3 asked the right
question — *how does the brain avoid severing, and does dynamical systems give us anything?*
It does, and it deletes `w_floor` rather than tuning it.

### ★ THE DIAGNOSIS — the danger is severing-by-TIMESTEP, not severing-by-decay.
`w ← (1 + ε·κ)w` is a **forward-Euler step** on `ẇ = ε·κ·w`. The continuous flow is multiplicative,
so `w(t) = w(0)·exp(ε∫κ)` is **strictly positive for all finite time**: the exact flow can never
sever anything. What can sever is the *discretisation* — if `ε·κ < −1` then `(1 + εκ) < 0` and the
weight **flips sign**. So `w_floor` was introduced to patch a numerical artefact of Euler, and it
was diagnosed as a plasticity-safety mechanism.

**Fix, free:** exponential (exact) integration `w ← w·exp(ε_flow·κ)`. Unconditionally positive for
any ε, κ — positivity becomes *structural* rather than clipped. One `exp` per edge.

### ★ THRESHOLD PROTECTION — the brain's answer and the control-theory answer are the SAME.
Positivity is not enough: exponential decay still crosses the collapse threshold θ in finite time,
which is the bridge-severing C.4 actually cares about. Two literatures converge.

**Neuroscience — soft bounds.** Weight-dependent plasticity (van Rossum et al.; Gütig et al.):
depression scales with distance from the bound, so `ẇ = ε·κ·(w − θ_safe)` for `κ < 0` sends
`w → θ_safe` **asymptotically and never crosses it**. The vector field *vanishes* at the boundary,
so `(θ_safe, ∞)` is forward invariant with no clip anywhere. Two further real mechanisms worth
importing:
- **Turrigiano's homeostatic synaptic scaling** regulates total drive **multiplicatively**, which
  preserves relative weights and cannot zero anything. **Subtractive** normalisation is what
  severs weak synapses. ⇒ *if MOS ever normalises w, it must normalise multiplicatively.*
- **BCM sliding threshold** (Bienenstock–Cooper–Munro): the potentiation/depression boundary moves
  with recent activity, so nothing can be depressed indefinitely. This is the same shape as
  §5p's mechanism ③ (Butz–van Ooyen `dz/dt = ν(a* − a(t))`) — already in the design.

**Control theory — control barrier functions** (Ames et al.). Take `h(w) = w − θ_safe`, safe set
`C = {h ≥ 0}`. `C` is forward invariant iff `ḣ ≥ −α(h)` for a class-𝒦 function α. Given the
*desired* flow `ẇ_des = ε·κ·w`, minimally modify it to satisfy the barrier condition — in 1-D the
QP is closed-form:
$$\dot w = \max\big(\varepsilon_{\text{flow}}\,\kappa\,w,\;-\alpha(w - \theta_{\text{safe}})\big)$$
**This is exactly "monitor and control the flow so it doesn't sever the connections", with a
proof instead of a clip.**

> **And the two are the same object.** Choosing `α(h) = ε|κ|·h` recovers the soft bound exactly.
> The brain's weight-dependent plasticity **is** a control barrier function with a linear class-𝒦
> function. That is not decoration: it means we can implement the neuroscience and inherit the
> invariance certificate, or implement the CBF and inherit the biological precedent.

### ✅ DECISIONS
- **Q5 = `F_MOS`** as derived in §5ac, shipped first in its unit-weight specialisation (which is
  now a *derived special case*, not an imported formula), with `τ_f` per the §5ac choice.
  Ollivier stays the selective escalation on flagged edges (C5-3: Forman keeps κ independent of
  η_H, which is what makes C.6's 2×2 diagnostic).
- **Q6 = live flow, no signal-only phase.** Per Charbel. Implemented as exponential integration
  plus the CBF/soft-bound barrier, so "reversibility" is supplied by a *proof of invariance*
  rather than by a two-week probation.
- **`w_floor` is DELETED as a mechanism** (Q8 dissolves with it) and replaced by `θ_safe` inside
  the barrier, which — unlike Q8's default — sits **strictly above** the collapse trigger by
  construction, because the flow never reaches it. This closes C6-3 properly: the earlier worry
  was that a bridge parked *exactly at* the collapse point is unsafe; under a barrier it never
  arrives there at all. **Passes A17 twice: deletes a hand-set constant and changes a printed number.**
- **C6-2 accepted:** rename to `ε_flow` (step size) and `ε_ρ` (RESOLVE threshold) before implementing.
- **C6-4 accepted:** the sign-convention invariant gets a test, not a comment.
- **`w` ceiling:** still owed, one line from Charbel. Not blocking — the barrier construction
  applies symmetrically to an upper bound if one is wanted (`h(w) = w_max − w`).

### ⚠️ NOT YET IMPLEMENTED
§5ac and §5ad are derivation and decision only. `F_MOS`, the exponential integrator, the barrier,
and the sign test are Phase-2 work and **no line of the curvature controller is in the engine yet.**
Saying otherwise would misreport the state.

## 5ae. ✅ FIX-11 AND FIX-13 CLOSED — the engine computes real geometry again (2026-07-30)

Both were "silently wrong" bugs: neither ever failed a test, which is why both needed tests that
assert the *property* rather than the symptom. New file `MOS/tests/test_stalk_floor.cpp`
(16 assertions, registered as `mos_stalk_floor_tests`).

### ✅ FIX-13 — the stalk noise-floor contract, ported from `belief.py`
New in `core` (single source of truth, `semantic_skill.{hpp,cpp}`):
`EPS_FLOOR = 1e-3` (asserted equal to belief.py's) · `stalk_floor(d, n_eff, kappa)` ·
`max_epistemic_trace(d, eps)` · `assert_e4_budget(d, D_lo, D_hi)`.

- **`cognitive_state.cpp` grow_concept:** `D = 1.0` ➜ `stalk_floor(dim, n_eff=1)` = **0.00230208**
  at d=384. Trace `d·D = 0.884` — O(1), so the epistemic term is commensurate with the semantic
  one instead of swamping it. Empty U was always CORRECT (one observation has zero scatter about
  its own mean); the floor was the defect.
- **`curator.cpp`:** `compute_variance` no longer returns `−ln(c)` as an isotropic variance, and
  `UNCALIBRATED_VARIANCE_PRIOR = 1.0` is gone. **An isotropic variance in d dimensions is the wrong
  destination for a scalar confidence** — per Q9 confidence belongs in the edge precision π_e.
  Signature now takes `d` explicitly rather than inferring it (FIX-1 discipline).
- **★ MEASURED, the E4 regression:** antipodal means (the largest possible semantic distance, 4).
  Old constants ⇒ **epistemic = 229.76 vs semantic 4** — the documented ~230, reproduced. New
  floor ⇒ **epistemic = 0** exactly (identical floors ⇒ the d-extensive term vanishes
  identically, not "is small").
- **★ W₂ is no longer inert:** same mean, rank-0 vs rank-1 stalk ⇒ epistemic `0 → 0.206`. The
  optimal-transport machinery now measures *directional* structure, which is the whole point.
- **★ A MAGIC NUMBER DELETED.** The old `min confidence = 1e-9` clamp existed only to dodge
  `log(0)`. It admits `−ln c = 20.72`, i.e. a Bures term of **15.80 — nearly 4× the entire
  semantic budget of 4.** Solving `d(√(eps+t/d) − √eps)² = 4` exactly gives
  **`t_max = 4(1 + √(eps·d))` = 6.479** at d=384. Verified by substituting back at d=2, 16, 384,
  4096 (all within 1e-9). The clamp is now a *consequence of the E4 budget*, not a guess.
- The guard **fires** on the old `D = 1.0` and passes the new floor — a guard that never fires is
  not a guard.

**⚠️ HONESTLY NOT PORTED, and stated rather than faked:** part 2 of the Python fix ("all real
uncertainty moves into U") cannot apply at `grow_concept`, because a single observation has no
scatter and a scalar confidence carries no DIRECTION to put in U. Directional uncertainty appears
only on aggregation (n ≥ 2) — `compute_pi_v`'s job. **Routing confidence to π_e is NOT done** and
remains owed.

### ✅ FIX-11 — operad co-schedulability is no longer order-dependent
`operad.cpp:66` set `slice_is_global_mutation` for **any** empty-support node, so although the
READ_ONLY guard let such a node *join* a slice, the flag then poisoned it for every node evaluated
afterwards. Fix is `if (support.empty() && !is_read_only)`.

**The fix required a seam to test it at.** The foliation rule lived inside `Operad::run`, entangled
with a ThreadPool and a live CognitiveState, so the bug had been unobservable by construction.
Extracted as `core::select_commuting_slice(ready, deferred)`; `run` now calls it. Measured:
read-only-node-first goes from **3 slices to 1** on three co-schedulable nodes.

Safety properties asserted to SURVIVE the loosening: a MUTATION global node still runs isolated ·
a global MUTATION *holding* the slice still locks out a later read-only node · overlapping supports
still serialise · slice count is insertion-order independent.

**⚠️ One of my own tests was wrong and the code was right.** I first asserted that
`[worker{5}, global-MUTATION, read-only]` puts the worker alone in slice 1. It does not, correctly:
the global mutation cannot join a non-empty slice, so it is **deferred** and never sets the flag,
leaving the read-only node free to join the worker. The mutation is not in that slice at all, so
nothing leaks. Test corrected to put the mutation first (where it genuinely holds the slice), and a
second test added pinning the deferred-mutation case explicitly.

### 📋 TEST REPORT (2026-07-30, full suite)
**C++ — 13 of 14 executables PASS**, including the new `mos_stalk_floor_tests` (16/16).
- `mos_algebra` · `mos_coarse_complex` · `mos_curator` · `mos_fourier` · `mos_homology` ·
  `mos_kernel` · `mos_knowledge_base` · `mos_pi_fusion` · `mos_plasticity` · `mos_probabilistic` ·
  `mos_reflection` · `mos_stalk_floor` · `mos_tests` — all exit 0. **Zero compile errors.**
- ❌ **`mos_colibri_tests` FAILS — PRE-EXISTING, not caused by these fixes.** Asserts
  `!parsed.latent.empty()` at `test_colibri.cpp:31` on a **live Groq call**. Verified by
  `git stash`-ing all changes, rebuilding, and reproducing the identical assertion on unmodified
  code. `GROQ_API_KEY` **is** set (len 56), so this is not a missing-key problem; the call returns
  without a usable latent.
  **⚠️ New fix-registry item below — the test has a design hole:** it catches `ColibriException`
  and passes when there is *no* connection, but has no path for a connection that *succeeds and
  returns an error payload*. So a real API/auth/quota failure presents as a hard assert instead of
  a diagnosable message.

**Python — 4 of 4 PASS:** `belief.py` · `hodge.py` · `coherence.py` · `cone_bures.py`. No
regressions from the C++ changes (as expected — they share no code, only the `EPS_FLOOR` constant,
which is now asserted equal on the C++ side).
*Note: `python` is not on PATH in the bash shell; the project interpreter is
`%LOCALAPPDATA%\Programs\Python\Python311\python.exe` (3.11.4), per §3c.*

### ⚠️ NEW FIX-REGISTRY ITEM
- **FIX-16 (M) — `test_colibri.cpp` cannot distinguish "no LLM" from "LLM returned an error".**
  It passes on `ColibriException` (no connection) but hard-asserts on an empty latent, so auth,
  quota and malformed-response failures all surface as the same opaque abort. Should report the
  HTTP status and body. This is the only red test in the suite and it currently tells us nothing
  about *why*.

## 5af. τ_f IS CIRCULAR · w IS CAPPED AND π IS NOT · THE PRE-PHASE-2 LIST (2026-07-30)

### ❌ τ_f "derived from the 3-way residual" — MY OWN SUGGESTION, AND IT DOES NOT SURVIVE.
Charbel said: derive it if it's cheap. **It is cheap to COMPUTE and not cheap to ADOPT.**
- **Cheap to compute:** the 3-way residual is `(δ¹η)_f`, the signed circulation around triangle
  `f`. `hodge.py` already forms `d1 @ eta` inside every Hodge split. Three adds per triangle.
- **🚨 But it is CIRCULAR.** `τ_f` is not a free parameter of the curvature — **it IS the C²
  inner product**, and `hodge_split` uses that inner product to compute the curl projection.
  Read the code: `A = (d1 / w).T` weights **only C¹**; the C² weight is implicitly `I`. So
  deriving `τ_f` from the residual of η means defining the inner product *from* the quantity that
  inner product is used to *measure*. That is a fixed point, not a derivation.
- **🚨 And it would invalidate E5.** Changing the C² inner product changes `curl` and `harm`, i.e.
  **every number in §5x** — the only empirical evidence the growth story has.

**INTERIM: `τ_f ≡ 1`, DECLARED** (option (a) of §5ac), on those two grounds and not on cost. This
is a placeholder to unblock Phase 2, NOT a closure of the question.

> **🚨🚨 THE CIRCULARITY CLAIM BELOW IS RETRACTED — SEE §5ag. Charbel was right to push back:
> the Hodge split is provably independent of τ (an invertible `W₂` cannot change an image),
> verified to 8.4e-16. τ_f is now DERIVED and implemented; E5 is untouched. The interim
> `τ_f ≡ 1` above is superseded by the harmonic mean of the edge precisions, which reduces to 1
> in the unit case so nothing regresses.**

> **🚨 CHARBEL (2026-07-30, later): REFUSED. "I don't want τ_f to die."** Explicit direction: do
> NOT let the circularity kill a derived τ_f by default. Take **the arduous path** — fix the
> parts that don't work (the circularity, and E5's dependence on the C² inner product) rather than
> retreating to the declared constant. Same posture as the δ refusal in §5z ("Charbel refused to
> accept E15's loss of δ and asked for an all-out attempt") — he now has a track record of that
> refusal paying off (δ was recovered). **This one is HARDER: §5z's fix was a construction found
> in one session; this one requires either (a) the time-lagged residual done properly — which is
> itself a small research programme (choosing a window, proving it's no longer circular, showing
> it doesn't drift), or (b) re-running E5 under the new inner product to certify the growth-story
> evidence survives τ_f ≠ 1.** Neither is a quick fix. **`τ_f ≡ 1` remains the WORKING value
> Phase 2 ships with**, but it is now explicitly a placeholder under active repair, not a decision.
> Owed item **V7 (new): break the τ_f circularity via the time-lagged residual, then re-verify E5
> under it.** Filed as its own line in the pre-Phase-2 list below, separate from the routine items.

### ✅ IS `w` CAPPED AT 1? — YES, AND THE QUESTION HAS A METHOD, NOT A TASTE.
Charbel asked *how we can know*. **The method: enumerate every consumer of the variable and read
off the range each one requires.** Doing that finds two consumers with *conflicting* requirements
— which is the actual answer:
1. **As a coupling / bind indicator.** `coarse_complex.cpp:138,169` test `weights_[k] >=
   bind_threshold_`, and `:255` returns **1.0 as the default** when a weight is absent — i.e. 1.0
   already means "fully bound" in the engine. Construction 1 declares `w(σ,t) ∈ [0,1]`.
   **Bounded, and the bound is 1.**
2. **As a precision feeding Π.** Precisions are inverse variances and are **unbounded above**;
   capping at 1 would cap confidence.

**These are two different objects, and conflating them has ALREADY caused a divergence bug** —
§5q's own note: *"raw coupling weight as precision made `lr*precision` huge → divergence"*, patched
with `max_step=0.5`. §5ac independently reached the same separation from the other direction
(Forman's weight must be `π_e`, **not** `w(σ,t)`). Two independent routes to one conclusion:

> **`w(σ,t)` is a normalised coupling, capped on [0,1]. `π_e` is a precision, uncapped.
> They are not the same variable and must never be substituted for one another.**

**Consequence for the controller:** the flow `w ← w·exp(ε_flow·κ)` acts on **w**, which *is*
capped — so the symmetric upper barrier is required, not optional: `h(w) = 1 − w` alongside
`h(w) = w − θ_safe`. §5ad's construction covers it unchanged.

### 📋 WHAT ACTUALLY REMAINS BEFORE PHASE 2
All eight Phase-2 items now have their blocking questions answered (Q4 · Q5+τ_f · Q13 · Q16 ·
Q1/Q2/Q2b · F10) — **τ_f = 1 is the WORKING value they ship with**, per Charbel's refusal above,
not a settled answer. Phase 2 proceeds; V7 runs alongside it, not before it.

**Open research item, not a quick fix — Charbel refused to let this die:**
- **V7 — break the τ_f circularity properly.** Either (a) derive it from a **time-lagged**
  residual (running average over past ticks, breaking the circularity the way BCM's sliding
  threshold does) — requires choosing a window, proving the fixed point is actually gone, and
  showing it doesn't drift; or (b) re-run E5 under whatever inner product results, to certify the
  growth-story evidence (§5x, the whole empirical case for the cohomological growth law) survives
  a C² weighting that is no longer identity. **Do not silently ship τ_f=1 as final** — it stays
  flagged as a placeholder until V7 lands one way or the other.

**Time-sensitive — do first:**
- **E7 at engine level. NOT DONE.** E7 discipline exists only for E5's elicitations
  (`e5_elicitations.jsonl`). The general "record assembly at composition time" is unimplemented,
  and §5r's registry says *"impossible to recover later"*. Every tick run without it is data
  permanently lost. **This is the only item on the list that gets worse by waiting.**
- **V6** — σ_dir on the real corpus + `σ_dir/δ` in telemetry. Free. The §5z verdict still rests on
  a calibrated simulation, and Phase-2 item 8 (rank-k stalks) builds on that metric.

**Cheap, blocking a specific item:**
- **ε rename** (`ε_flow` / `ε_ρ`, C6-2) — before item 3, or it becomes a bug.
- **FIX-12 propagation** — the antisymmetric contract is decided but not written into
  `MOS_FINALIZATION.md` (Q9/Q10/Q11) or the `.tex`; items 2 and 3 inherit it. Fold in the stale
  **Q2b 🔴** flag and §5t's stale **"CHOOSE THE CATEGORY"** NEXT line at the same time.
- **Confidence → π_e routing** — newly owed from FIX-13 (§5ae). `π_e` is the *only* remaining home
  for reported confidence, and Q9 says precision needs a non-constant source.

**Owed, not blocking Phase 2:**
- FIX-7 / FIX-8 / FIX-9 (doc corrections) · FIX-15 (E5 significance overstated ~4×; fix before
  quoting the p-value) · FIX-16 (colibri test cannot diagnose its own failure) · E5b at b₁ ≥ 2 ·
  V2/E14 (**needs Charbel's ~50 labelled pairs**) · V3 · V5 · **V7 (τ_f, above — running
  alongside Phase 2, not blocking it, but not to be forgotten either).**

## 5ag. 🚨 THE τ_f CIRCULARITY CLAIM IS RETRACTED — Charbel was right (2026-07-31)

§5af claimed a derived `τ_f` was **circular** ("τ_f IS the C² inner product, and `hodge_split` uses
that inner product to compute the curl projection") and that adopting one "would invalidate E5".
Charbel rejected both. **Both were wrong.**

### THE ALGEBRA
With inner products `W₀, W₁, W₂` the adjoint of `δ¹ : C¹ → C²` is `(δ¹)* = W₁⁻¹(δ¹)ᵀW₂`, so the
curl space is
$$\mathrm{im}\big(W_1^{-1}(\delta^1)^\top W_2\big) = W_1^{-1}(\delta^1)^\top\!\cdot\mathrm{im}(W_2) = W_1^{-1}(\delta^1)^\top\!\cdot C^2 = \mathrm{im}\big(W_1^{-1}(\delta^1)^\top\big)$$
because `W₂` is positive-definite and therefore **onto**. **An invertible map does not change an
image.** So the curl subspace — hence the projection onto it, hence the whole grad ⊕ curl ⊕
harmonic split of η — is **independent of τ**.

**Verified numerically, not just argued:** on the E5 complex,
`‖P(W₂=I) − P(W₂=random)‖_F ≈ 8.4e-16` over six random positive `W₂`. Test lives in
`derived_scales.py` §0 so the retraction cannot silently un-retract.

**Consequences:** (1) no circularity — τ_f may be derived from the circulation `(δ¹η)_f` without
feeding back into how that circulation is split; (2) **E5's numbers do not move**, so §5x is not
re-based. `hodge.py`'s `A = (d1/w).T` (implicitly `W₂ = I`) computes the same projector any
positive `W₂` would, which also means hodge.py was never missing anything.
**Where τ_f DOES matter:** the magnitudes of `Δ₁ = δ⁰(δ⁰)* + (δ¹)*δ¹` (hence its spectrum), and
`F_MOS`'s coface term. Worth deriving — just not load-bearing for E5.

**Lesson:** I inferred a functional dependence from an *appearance* in a formula without checking
whether it survived to the object being computed. The check was four lines of numpy.

### ✅ τ_f DERIVED — the same construction as π_e, one dimension up
`π_e = 1/Var(ε_e)` where `ε_e = (δ⁰x)_e`. The 2-cell weight is the same thing on the next
coboundary: **τ_f is the precision of the triangle circulation** `(δ¹η)_f = η_ab + η_bc + η_ca`.
Independent edge values ⇒ variances add (signs square away) ⇒ `Var((δ¹η)_f) = Σ_{e∈f} 1/π_e`, so
$$\tau_f = \frac{|f|}{\sum_{e \in f} 1/\pi_e} = \text{harmonic mean of } \{\pi_e : e \in f\}$$
**The `|f|` factor is a stated NORMALISATION choice, not a derivation:** τ_f is the precision of
the *mean* circulation per edge rather than the total. Two reasons, the second checkable —
(a) it keeps τ dimensionally comparable to π so `π_e²/τ_f` is a pure number; (b) **exact day-one
degradation: all π_e = 1 ⇒ τ_f = 1 ⇒ `F_MOS` collapses to `4 − deg u − deg v + 3m`.** Without it
the derived curvature would silently disagree with the derivation that justified it.
**Tested:** unit weights reproduce the combinatorial value exactly (edge AB: 2.000000, edge CD:
−1.000000); the filled/unfilled sign ordering survives non-uniform precisions.

### ✅ π_e DERIVED — and the engine's current source is a TYPE ERROR
`CoarseComplex::set_use_precision(true)` documents itself as using **the coupling weight** as π_e.
That is exactly the conflation §5af isolated: `w(σ,t)` is capped on [0,1], `π_e` is an unbounded
precision. `python/edge_precision.py` derives the right thing from the PC free energy — with
(H1) independent stalks, (H2) orthogonal restrictions (the standing Anderson–Morley hypothesis,
not a new assumption) and (H3) isotropic coarse stalks, `R(D I)Rᵀ = D I` and variances add:
$$\pi_e = \frac{1}{D_u + D_v + s_e}, \qquad s_e = \frac{-\ln c_e}{d}$$
**This is where Q9's confidence belongs and why it is safe here:** π_e is ONE SCALAR multiplying
‖ε_e‖², so `s_e`'s trace contribution is `−ln(c) = O(1)` and no d-extensive term is created —
unlike D, where the Bures term `d(√D₁−√D₂)²` reached 229.76 (§5ae).
**Measured day-one degradation:** ρ is invariant under uniform rescaling of π (ω and the
Anderson–Morley bound B are both linear in π), so uniform floors give ρ **bit-identical** to
`π=None` — verified against the real `coherence.coherence`, 0.3483650554768379 both ways — while
a genuinely broader organ (0.2493) and a low-confidence judgement (0.3315) do move it.

### ✅ δ DERIVED — from the data, without hand labels
V2/E14 planned to calibrate δ by sweeping ~50 **hand-labelled** pairs. The organ structure is
already weak supervision: same-organ pairs are evidence of "one thing", different-organ pairs of
"two things". `derived_scales.derive_delta` takes the **equal-error crossing** — the `d*` where
false-splits equal false-merges — and `δ = d*/π` by §5z's saturation convention. Parameter-free:
no threshold is chosen, it is read off. It also reports **separability**, so a δ from two
overlapping distributions is flagged NOT IDENTIFIABLE rather than quoted as meaningful.
**This does not replace E14** — a sweep against real labels, published as a SENSITIVITY CURVE
rather than a fitted point, is still the stronger evidence.

## 5ah. 🚨 V6 RUN — THE §5z VERDICT DOES NOT SURVIVE REAL TEXT (2026-07-31)

`python/measure_sigma_dir.py`. Live bge-small on the project's own DOCS (11 organs, one per
document, paragraphs as concepts). **The number the whole §5z verdict rests on was simulated;
measured, it is ~4× worse.**

| | V1c simulated | **V6 measured** | factor |
|---|---|---|---|
| σ_dir | 0.035–0.044 | **0.06–0.10** | ~2× |
| d_BW (separation) | 1.33–1.39 | **~0.5** | **~2.7× smaller** |
| σ_dir/δ (per-pair) | 0.084–0.100 | **0.42 med, 0.62 max** | ~5× |
| σ_dir/δ (global δ) | — | **0.32 med, 0.42 max** | ~3.5× |

### THE DIAGNOSIS — it is NOT σ_dir, it is the SEPARATION
σ_dir came in at ~2× the simulation, same order. The gap is almost entirely that V1c placed organ
means **1.33–1.39 apart** while real same-project prose separates by **~0.5**. (2× larger σ) ×
(2.7× smaller δ) ≈ 5.4×, and 0.09 × 5.4 ≈ 0.49 ≈ the measured median. **The arithmetic fully
accounts for the discrepancy — nothing anomalous happened.**
**Root cause: V1c calibrated the WITHIN-organ spread to `cos_within ≈ 0.833` but never calibrated
the BETWEEN-organ separation** — it placed the means far apart by fiat. bge-small maps
same-author, same-project prose into a tight cone.

### ⚠️ ONE OF MY OWN ERRORS, CAUGHT BY MY OWN COLUMN LABEL
The first run computed δ from `‖Δμ‖` while the column said `d_BW`. Since
`d_BW² = ‖Δμ‖² + TrΣ₀ + TrΣ₁ − 2Tr(...) ≥ ‖Δμ‖²`, that understated δ ~2.4× and **overstated** the
ratio by the same factor (max 1.47 → 0.62 once fixed) — the direction that flatters a bad result.

### WHAT THIS DOES AND DOES NOT KILL
- **SURVIVES:** Cone–Bures is still a genuine metric (20k triples, zero violation), still bounded,
  still gives δ a structural meaning, still 5.45 ms/tick. None of that was regime-dependent.
- **DOES NOT SURVIVE:** the claim that it *tracks true HK closely in MOS's regime.* Against §5z's
  own agreement table, σ/δ ≈ 0.32 is roughly **60% merge agreement**, not the 87% V1c implied.
  Better than chance, far short of the claim.
- **Using a GLOBAL derived δ (what a deployed system actually has) is materially better than the
  per-pair saturation δ** — median 0.42 → 0.32 — because per-pair δ shrinks exactly where pairs
  are closest. Telemetry should carry the global ratio.

### ⚠️ CAVEATS, STATED NOT BURIED
Organs here are **documents**; MOS's coarse organs are cognitive modules — this is a proxy. The
corpus is monothematic (one project, one author). But the direction is robust: any grouping of one
project's corpus gives small separations, and that is arguably the deployment case. **V6b owed:
re-run with organs defined as topic clusters, and once real module stalks exist, on those.**
δ's own separability here is **0.628**, only just above the identifiability bar — so δ is usable
but weak on this corpus, and that is reported rather than smoothed over.

## 5ai. D̃ SHIPPED — AND MY OWN RECOMMENDATION WAS A CATEGORY ERROR (2026-07-31)

`python/merge_score.py` (30 self-tests, 0 API calls, ~420 µs/pair at d=384, k=6). I recommended
"use D̃ for the merge decision, D as the metric". **Implemented literally, that ships a predicate
that returns True for every pair.**

### 🚨 THE VACUITY — why a value correction can never fix a decision
- Cone–Bures is **bounded**: `D² ≤ w₀+w₁` always (the property that killed E4's runaway).
- `D̃ = D/√(1+σ²/δ²)` is always **smaller** than D.
- So `D̃² < w₀+w₁` is satisfied unconditionally. Everything merges.
- And rescaling the threshold by the same factor returns D's own predicate unchanged.

> **General fact, worth keeping: multiplying a score AND its threshold by the same number cannot
> change any decision.** A pairwise monotone rescaling is decision-invariant. I proposed a value
> correction and called it a decision fix.

**Verified independently of the implementation:** max `D̃²` = **1.7987** over 3000 random pairs
against the bound 2.0 — never reaches it.

### ✅ THE ACTUAL FIX — the correction is a LENGTH SCALE, not a value
Small-angle expansion gives `D̃² ≈ w·d_BW²/(4(δ²+σ²))` against `D² ≈ w·d_BW²/(4δ²)`, so dividing
by `(1+σ²/δ²)` **is** replacing δ by
$$\delta_{\text{eff}} = \sqrt{\delta^2 + \sigma_{\text{dir}}^2}$$
**Directional spread adds to the identity scale in quadrature** — physically right: fuzzier
concepts genuinely cannot be resolved below that scale, so they should merge more readily. The
predicate becomes D's own structural cutoff read at δ_eff: `d_BW < π√(δ² + σ_dir²)`.
Exact at σ→0, monotone in σ, **still no fitted threshold**. This is a better construction than the
one asked for.

### MEASURED
- **Day-one degradation is exact**: σ_dir = 0 constructed exactly ⇒ D̃ **bit-identical** to D
  (`max|diff| = 0.0`, asserted with `==`, not a tolerance); correction factor exactly 1.0.
- **D̃ ≤ D always**: 5000 pairs over five δ, strict on 5000/5000.
- **Predicate divergence** (δ=0.4, analytic stalks): σ/δ = 0.079 → 0% · 0.25 → 1.2% · 0.50 → 5.0%
  · 1.00 → 17.5% · 1.77 → 43.8%. Monotone.
- **★ Every flip is in the MERGE direction — D̃ never splits what D merges.** Structural
  (δ_eff ≥ δ). The correction can only make the system more permissive, never more fragmentary.
- **Ranking works**: two pairs at *identical* D (0.446213, |ΔD| = 0.0) with σ_dir 1e-4 vs 0.50 are
  separated by D̃ (0.446213 vs 0.399105). D is blind to spread; that reordering is the whole
  operational value of the score.

### 🚨 THE TRIANGLE VIOLATION IS WORSE WITH MEASURED σ_dir, NOT BETTER
| δ | §5z (σ_eff) | **measured σ_dir** |
|---|---|---|
| 0.3 | +1.08 | **+1.29** |
| 3.0 | held | **+0.13** |

So switching to a measured σ does not soften §5z's "never a metric" verdict — it hardens it, and
newly breaks at δ=3 where §5z reported it holding. **The D/D̃ dispatch is MANDATORY, not
stylistic.** ⚠️ *Reproduction note: the δ=0.3 violation is easy to find (+0.58 at 4k triples, grows
with sample size). The δ=3 violation is RARE — not reproduced at 4k draws; it rests on the 20k run.*

### ⚠️ THE CLAIM THAT MOTIVATED THIS IS STILL UNMEASURED
**§5z's agreement table was computed for D against an exact HK solver. The same table for D̃ has
never been computed.** So "D̃ improves the merge decision" — my entire argument for doing this —
is **inferred from the value law, not measured**. Worse, δ_eff is pinned only by matching at
*small* angle, while the two laws diverge most **at the cutoff**, which is the only place the
predicate is ever decided (5.2% at σ/δ=1, 0.99% at 0.32). **Owed: an exact-HK measurement of
cutoff location vs σ.** Until then D̃ is a defensible construction, not evidence.
Also unvalidated: `max(σ_a, σ_b)` as the pairing rule — V1 fitted a single shared σ, so no
combination rule is validated on heterogeneous stalks.

### ⚠️ SYNTHETIC STALKS ALARM RATHER THAN FLATTER
Random `U` at scale 0.4 gives σ_dir/δ ≈ **1.9**, far worse than §5ah's corpus median of 0.32,
because random `U` is not concentrated orthogonally to Δμ the way real stalk covariance is.
**Never tune this metric against simulated stalks** — the failure direction is not conservative.

## 5aj. π_v v2 SHIPPED — AND IT RULES OUT THE COMPETING EXPLANATION FOR V6 (2026-07-31)

`python/pi_v.py`, 45 self-tests, zero model loads. Built to test the §5ah hypothesis that σ_dir is
inflated by **model misspecification** (an organ that is really several topics collapsed to one
Gaussian centroid). **It is not. The hypothesis is refuted, and that is the value of the run.**

### ⚠️ CONSTRUCTION 2'S WORDING IS DEFECTIVE — resolved, not quietly reinterpreted
Construction 2 says *"v2 = top principal component if needed."* **That cannot be read literally:**
v1 returns a **position**; a principal component is a **direction** — translation-invariant (carries
zero location information) and sign-ambiguous. Substituting one for the other makes every
cross-organ distance meaningless. What PC1 *can* do is diagnose inadequacy and name a split. So:
> **π_v2 = π_v1 restricted to the dominant mode of the fine complex.**

v2 is not a new estimator — it **calls v1 on a sub-complex**, inheriting Kish `n_eff`, the shrinkage
prior and the O(1/d) floor unchanged. Day-one degradation is therefore **structural, not asserted**:
one mode ⇒ the restriction is the identity ⇒ bit-identical output. **Construction 2's text should be
amended to this.**

### ★ THE EIGENGAP IS NOT THE VERDICT — elongation ≠ multi-modality
The obvious diagnostic (leading eigengap) fails, with an explicit counter-example in the tests: an
**elongated unimodal "cigar" scores eigengap 49.8** while a **genuinely bimodal cloud scores 12.2**.
So the verdict is a model comparison instead: project on PC1, compare 1-Gaussian vs 2-component
mixture by **BIC (ΔBIC > 10** — the same "decisive" bar `belief.compare_models` already prints**)**
**and** require **Ashman's D ≥ 2**. Tests 11/12 show each guard catching a *different* unimodal
family, so the conjunction is necessary and neither statistic is decoration.

### 🐛 A REAL BUG FOUND AND FIXED MID-BUILD (worth remembering)
EM from a two-means initialisation can only propose **offset** splits, so a **concentric core+halo**
cloud (one topic with a heavy tail) was fitted as left/right and **falsely declared multi-modal ~60%
of the time**. It persisted at n/d = 25, so it was a **basin-of-attraction** problem, not
small-sample noise. Fixed with a second closed-form start (concentric narrow/broad), letting
likelihood choose. False positives went to **0/120** across d = 8…384. Both starts are
deterministic, so the diagnostic remains seed-free and order-invariant.

### 🚨 THE RESULT — v2 does NOT fix V6, and the decomposition is the finding
| σ_dir/δ (global δ = 0.2553) | v1 | v2 |
|---|---|---|
| median | 0.3242 | **0.3138** (−3.1%) |
| max | 0.4164 | **0.4164** (0.0%) |
| fraction > 0.3 | 0.709 | 0.582 |

- **Conditional effect: −29.1%.** On the 10 pairs v2 touched, median ratio 0.318 → 0.226.
  **The mechanism is real** — where an organ genuinely is several things, the centroid *does*
  inflate σ_dir and v2 removes it.
- **Prevalence: 1/11 organs (9%).** Ten of eleven are adequately described by ONE Gaussian, so the
  marginal effect is only −3.1% and the worst pair does not move at all. (The single hit,
  `output 2`, keeps 95.2% of its mass — an outlier trim, not a two-topic organ.)

> **⇒ Multi-modality is NOT what makes V6's number bad.** σ_dir here is *genuine within-organ
> spread* measured against a *small between-organ separation* — which is §5ah's own diagnosis
> ("it is NOT σ_dir, it is the SEPARATION"), **now confirmed from the other side by eliminating the
> competing explanation. V6's bad result STANDS.**

### ✅ v2 STILL EARNS ITS PLACE (A17), just not as V6's fix
Free when unimodal (bit-identical to v1), pays off where multi-modality does occur, and —
the real win — **it converts `split`, one of `CoarseComplex`'s four typed structural operations,
from an operation with NO firing criterion into a derived one.** `pi_v_modes()` returns the
split-ready decomposition.

### ⚠️ CONSEQUENCE FOR CONSTRUCTION 4 — its motivation must be re-based
Construction 4's stated failure mode 3 was "if σ_dir on cover-organs is not lower than on
document-organs, the multi-modality diagnosis behind π_v v2 and this construction is wrong."
**This run does not test cover-organs, but it does show multi-modality is rare (9%) at the
document granularity** — so the "organs are secretly multi-modal" argument for Construction 4 is
**weakened and should not be leaned on.** Construction 4's remaining justification is the part that
never depended on it: derived rather than hand-drawn structure, overlaps as first-class objects,
the growth filtration that activates persistent homology, and n-ary simplices that are honest by
construction. Those stand. **The σ_dir argument does not — recorded so it is not silently reused.**

### COULD NOT VERIFY (stated, not buried)
- **PC1 only.** An organ splitting along a low-variance direction is missed. A 384-d mixture cannot
  be fitted from ~60 paragraphs, so this is the *affordable* test, not the complete one.
- **n < d makes PC1 itself noisy**, so verdicts near the BIC bar are not sharp. A resampling
  stability check is the obvious next step and is **not implemented**.
- **Scope**: 11 document-organs, one project, one author. V6's caveat carries over unchanged.
  A genuinely mixed-topic corpus would show higher prevalence and a larger marginal effect —
  **that is V6b's question and it is not answered here.**

## 5ak. V6b — HOW MUCH CAN THE ORGAN DEFINITION FIX? A BOUND, AND IT IS SMALL (2026-07-31)

`python/measure_organ_definitions.py`. Charbel asked for the (c) question to be **measured, not
argued**. Design: use k-means organs — which are **circular by construction**, since k-means
minimises exactly the within-organ scatter we then measure — **deliberately, as a BEST CASE**.
A bound from an optimistic assumption is informative when it fails.

Everything held fixed against §5ah: same corpus, same paragraphs, same bge-small contract, same
`stalk_gaussian`, same `sigma_dir`, same global δ (0.2558, separability 0.632). **Only the
assignment of concepts to organs changes.**

| organ definition | pairs | d_BW med | **σ_dir/δ med** | max | frac>0.3 |
|---|---|---|---|---|---|
| documents (V6 baseline) | 55 | 0.611 | **0.3233** | 0.3962 | 0.71 |
| k-means, k=4 | 6 | 0.556 | 0.2961 | 0.3620 | 0.50 |
| k-means, k=11 | 55 | 0.593 | 0.2708 | 0.3630 | 0.27 |
| k-means, k=16 | 120 | 0.671 | 0.2588 | 0.3692 | 0.20 |
| k-means, k=32 | 435 | 0.708 | **0.2491** | **0.4657** | 0.15 |

### 🚨 THE BOUND: −22.9%, AND THE TAIL GETS WORSE
**The most favourable organ definition available — one that optimises the measured quantity —
buys 23%.** Median 0.3233 → 0.2491. Against §5z's agreement table that moves merge agreement from
~62% to roughly ~70%. **It does not approach 87%, and it is an optimistic bound, so the honest
expectation for any real (non-circular) organ definition is less.**

**And the maximum gets WORSE, not better: 0.3962 → 0.4657.** Finer organs help the typical pair and
hurt the tail, because more organs means more *adjacent* pairs with small separation and comparable
spread. Since the merge predicate fails pair-by-pair, **the tail is what corrupts the store** — so
the headline median improvement overstates the real gain.

### ★ NO PRIVILEGED GRANULARITY EXISTS IN THIS CORPUS — the deeper finding
The k-sweep IS a granularity sweep, and the ratio moves **monotonically and slowly**
(0.296, 0.298, 0.297, 0.271, 0.259, 0.258, 0.249) with **no dip, no optimum, no natural scale.**
If the concept space had a preferred organ granularity we would see the ratio bottom out at some k.
It does not. Consequences, and they are the useful part of this run:
- **No k is "correct".** Choosing one is arbitrary at every scale, which undercuts *every*
  partition-based organ definition, not just documents.
- **This supports the COVER over the PARTITION** (Construction 4): if no natural partition scale
  exists, forcing a partition is arbitrary by construction — whereas overlap is exactly what a
  scale-free continuum looks like when you insist on grouping it.
- **It supports replacing δ-calibration with PERSISTENCE ACROSS δ.** Don't pick the scale; take
  what survives across scales. Same dissolution move that worked for F10.

> ### ⚠️ AMENDMENT (same day) — "NO PRIVILEGED GRANULARITY" IS UNDER-SUPPORTED AS STATED
> **k-means minimises within-cluster scatter, and its objective is monotone non-increasing in `k`
> by construction.** σ_dir *is* within-organ spread and δ is held global and fixed, so
> **σ_dir/δ falling as `k` rises is guaranteed by the algorithm, not observed in the corpus.**
> The same sweep run on isotropic Gaussian noise would produce the same monotone shape. Therefore
> *"no dip ⇒ no natural scale exists"* does **not** follow: absence of an optimum in a
> monotone-by-construction quantity is close to vacuous.
> - **To make it bite:** re-run the k-sweep against a **structureless null** (isotropic Gaussians,
>   n and d matched) and show the real corpus fails to dip *relative to the null*. Cheap — one
>   afternoon, no new machinery. **NOT DONE.**
> - **What survives untouched:** the **max worsening 0.3962 → 0.4657**. That is not implied by
>   k-means monotonicity — finer organs producing *more adjacent pairs with small separation* is a
>   fact about this corpus, and since the merge predicate fails pair-by-pair it is the tail that
>   corrupts the store. **The −22.9% bound and the worsening tail both stand.**
> - **Consequence for Construction 4:** the "supports COVER over PARTITION" bullet above is
>   **downgraded to a conjecture pending the null.** Construction 4 does not need it (see the §3
>   amendment's net ledger) — but it must not be cited as a measured result.

### ⚠️ WHAT THIS DOES AND DOES NOT SETTLE
- **Settles:** (c) cannot rescue §5z's closeness claim. Best case ~70% vs the claimed 87%, with a
  worsening tail. **Three fixes have now been tried — (a) unmeasured, (b) refuted, (c) bounded
  at −23% — and none rescues the number.**
- **Does NOT settle:** whether a *non-circular* organ definition (co-activation lens, Construction
  4) helps at all. k-means cheats in (c)'s favour, so its result is a ceiling, never evidence.
- **Scope unchanged:** one project, one author, 400 concepts, 11 documents.

### 📉 AND THE SCOPE OF THE DAMAGE IS SMALLER THAN §5ah IMPLIED
Traced the consumers: **`coherence.py` (ω, ρ, contradiction detection) contains ZERO references to
Bures** — it runs on `L = δᵀΠδ` with the derived π_e. C++ edge formation (`curator.cpp:102`) uses
plain `wasserstein_2_terms`, **not** Cone–Bures. The only importers of `cone_bures`/`merge_score`
are `measure_sigma_dir`, `pi_v` and `validate_regime` — **all measurement scripts.**
> **Cone–Bures is not wired into the engine at all.** V6 falsifies a claim about a *proposed
> upgrade*, not a working mechanism. Of §0.2's five claims it touches **growth**, and only the
> `merge` quarter of it. This does not make V6's result less true; it makes it less blocking.

## 5an. 🏁 PHASE 2 IS CLOSED (2026-08-01). All nine items built, tested, committed.

Charbel: *"finish phase 2, take all the time you need, but let's end phase 2."* Done.
**C++ suite 21/22** (`mos_colibri_tests` exit 3 is the known FIX-16 red and predates all of this);
Python parity and instrument checks pass.

| # | item | where | what it actually establishes |
|---|---|---|---|
| 1 | Householder maps (m=4) | `householder.{hpp,cpp}` | 96× storage cut (12 KB vs 1.15 MB); **exactly** orthogonal, not to tolerance (7.1e-15 at d=384); `det = (−1)^m` ⇒ m=4 lands in SO(d) |
| 2 | Hodge split via LSQR | `hodge.{hpp,cpp}` | matrix-free; **parity with `hodge.py` to 1e-12** in both uniform and π-weighted inner products; Pythagoras enforced, not hoped |
| 3 | `F_MOS` + barrier | `curvature.{hpp,cpp}` | exact degradation to `4−deg u−deg v+3m`; barrier makes severing **structurally impossible** |
| 4 | PPR instantiation | `instantiate.{hpp,cpp}` | **132 pushes at \|V\|=50, 500 AND 5000** — ACL size-independence measured, not cited; cut weight first-class |
| 5+6 | 𝕂/W split + γ(ν) | `two_complex.{hpp,cpp}` | `ι*ι_! = id` asserted; Q rises 0 → 2.34; refuted sessions leave 𝕂 **bit-identical** |
| 7 | Coning off cycles | `coning.{hpp,cpp}` | kills **exactly one** class per attachment; the rejected chord makes b₁ **worse** (1→2) |
| 8 | rank-k SPD stalks | `rank_k_stalk.{hpp,cpp}` | Woodbury exact vs dense; congruence preserves form, trace **and spectrum** ⇒ unitary CPTP is a fact, not an analogy |
| 9 | Construction 5 | `cover.py`, `test_cover.py` | the **instrument** validated on known ground truth, both directions |

### 🔬 SIX FINDINGS THE DERIVATIONS DID NOT HAVE
1. **⚠️ `5ad`'s positivity claim is false in floating point.** Exponential integration makes positivity
   "structural" only in *exact arithmetic*: `exp` underflows to exactly 0 below ≈ −745, so
   `ε_flow·κ = −1e5` severs the edge anyway — silently, and to zero rather than to something
   negative anyone would notice. **The barrier does not have this failure mode**, and structurally
   so: it *adds* the floor rather than multiplying, so an underflowed decay lands **on** `θ_safe`.
   **⇒ bare exponential integration is NOT sufficient; only the barrier's guarantee survives float.**
2. **⚠️ `5ac`'s low-precision prediction is CONFIRMED, in the direction it feared.** On the bridge
   (A,D), `F(π) = 2 − 3√π` exactly, so the edge runs from −1 (EXPAND, correct for a bridge) to +2
   (CONTRACT) as `π → 0`. **An edge we know nothing about gets folded away for being uninformative.**
   Also: the approach is **not monotone** in general — on a filled edge `F` dips below its unit value
   first. 5ac predicts the *limit*, not the path.
3. **⚠️ The m=4 Householder family is NOT CLOSED under γ(ν) crystallisation.** A convex combination
   of two products-of-4-reflections is not orthogonal, and the SVD projection back gives a general
   orthogonal matrix needing up to `d−1` reflections. **The literal `Π_O(d)(R + γΔR)` cannot be
   applied in the representation item 1 ships.** Both retractions are provided and they differ by
   2.96 at γ=0.5 — a modelling choice, not an approximation of one by the other.
4. **⚠️ A store starting as the constant sheaf could not learn at all.** Every `R^𝕂_e` is the
   identity, which has **no reflection vectors**, so there was nothing to interpolate *from* and
   crystallisation was a no-op for every `γ < 0.5` — while `γ₀ ≪ 1` by design. Fixed via
   `H_v H_v = I`: the identity has many m-reflection representations, so the shorter map is padded
   with cancelling duplicate pairs. **Falling out of it: reflection-count PARITY is a topological
   obstruction** — `det = (−1)^m`, so maps of differing parity lie in different components of O(d)
   and no continuous path joins them. `crystallise` refuses rather than jumping.
5. **⚠️ Q13's chord is worse than "relocates".** Q13 says a chord *"often relocates a class rather
   than killing it"*. Measured: on a 4-ring it splits one cycle into two and fills neither, so
   **b₁ goes 1 → 2**. A growth loop built on chords would not spin — it would diverge.
6. **⚠️ Noisy-OR without a leak is degenerate.** With all organs off, `P(concept fires) = 0`
   exactly, so any tick where a concept fires while the model thinks every cause is silent has
   likelihood zero. Not merely `0·(−∞) = NaN`: it says **the model must explain every co-activation
   or be infinitely surprised.** A leak node is the standard answer and the honest one — concepts
   fire for reasons outside the organ decomposition, and the model must be able to say so rather
   than invent an organ for every stray activation.

### 📋 WHAT PHASE 2 DOES *NOT* CLAIM
- **Construction 5 has not been run on MOS's corpus.** The instrument recovers a planted organ
  count and calls cover-data a cover *and* partition-data a partition — but **T1–T3's verdict about
  this project needs accumulated E7 records, and the tick only began producing them yesterday.**
- **`verified` in the E7 record is still NULL.** Coherence ≠ correctness (Construction 3), so
  inferring it from a ρ improvement would fabricate the promotion gate's own evidence.
  **Routing VerifyOp's real outcome is owed.**
- **Nothing yet produces per-edge confidences**, so `π_e` reduces to `1/(D_u+D_v)`. Q9's contract
  is specified (FIX-12) and unimplemented.
- **The nine items are built and unit-tested; they are not yet composed into a running tick.**
  Wiring them into `execute_dag` is Phase 3, not Phase 2.
- ~~**FIX-17 is open**~~ — **CLOSED 2026-08-01**, see §5am. The engine was already correct; the
  lag was documentation, and the contract is now pinned by a test rather than a comment.
- **V7 (τ_f) still runs alongside**; τ_f = 1 remains a working value, not a closure.

## 5am. ✅ THE FOUR PRE-PHASE-2 BLOCKERS, CLOSED (2026-07-31)

Charbel: *"do all four, not in a cheap way, in a way that matters."* Done. **Phase 2 is
unblocked.** C++ suite **14/15** (`mos_colibri_tests` exit 3 is the known FIX-16 red and predates
this work); Python parity checks pass.

| | what shipped | the part that mattered |
|---|---|---|
| **E7** | `AssemblyLog` ported to C++; `record()` before `Operad::run`, `close()` after ρ is re-measured | **`canonical_signature` had to be byte-identical or every recurrence count splits silently across two keys with nothing failing.** Ported statement-by-statement (front-pop, back-append, stable re-sort; edge strings sort *lexicographically*, so `0>10` precedes `0>2` — invisible under 10 nodes). 6 cases duplicated in `check_signature_parity.py` with the same expected strings on both sides, so changing one implementation breaks the other's test. **Verified: both emit identical strings.** |
| **ε** | `ε_ρ` (`eps_rho`) across 9 files | Renamed the ε that EXISTS *before* `ε_flow` arrives, so there is no name left to collide with. Doing it after would mean two live meanings of one identifier and a rename under load. |
| **FIX-12** | `MOS_FINALIZATION.md` D.3 normative block; Q10/Q11 re-specified | The retracted schema is marked **retracted, not deprecated** — `η = p_v(c_uv) − p_u(c_uv)` is antisymmetric *by construction*, and `η` is now never reported directly, so no downstream step can re-symmetrise it. |
| **π_e** | `edge_precision.{hpp,cpp}` ported; `CoarseComplex::precision_` map | The regression test is the real deliverable: **`use_precision` with no π_e set must now change nothing.** Before, it silently reweighted by coupling and moved the blame — which is exactly how a Hebbian count masqueraded as an inverse variance. Precisions deliberately do NOT share storage with `weights_`. Parity: 233.95225871270583 / 250.0, C++ and Python. |

### ⚠️ NOT FAKED, STATED
- **`verified` in the E7 record stays NULL.** Construction 3 says coherence ≠ correctness, so
  inferring VERIFIED from a ρ improvement would fabricate the very evidence the promotion gate
  exists to supply. **Routing VerifyOp's real outcome is owed.**
- **Nothing yet produces per-edge confidences.** Q9's contract is unimplemented, so π_e currently
  reduces to `1/(D_u+D_v)`. The wiring is there to receive them; the source is not built.
- **`plan_foliation` is exact only while `get_support()` is stable across `apply()`** — true today,
  not enforced by the interface. So `Operad::run` returns the foliation it *actually* executed and
  the kernel writes a mismatch into the record's `note` rather than assuming.
- **Absent measurements serialise as `null`, never `0.0`**, or a composite that was never measured
  would read as one that reliably did nothing.

### ✅ FIX-17 — CLOSED 2026-08-01. The investigation resolved the OPPOSITE way to the worry.

**Found while propagating FIX-12:** the `.tex` still said the grown-concept floor is `D = −ln c`
with no `1/d`, contradicting FIX-13 and its own neighbouring remark. It was left open because the
honest fix needed a check of whether the *engine* was wrong too — an investigation, not a text edit.

**The investigation's answer: the engine was already right.** `AgentCurator::compute_variance`
returns `core::stalk_floor(d, n_eff=1)` and **deliberately ignores `confidence`**;
`UNCALIBRATED_VARIANCE_PRIOR = 1.0` and `D = −ln c` are both gone from the code, removed by FIX-13.
The only Python use of `−ln c` is `edge_precision.py:118`, which is `−ln(c)/d` — the **correct**
home per Q9. **So FIX-17 was pure documentation lag, not a live defect.**

**But the lag had a cause worth fixing, and that is the real content of FIX-17.**
- **The contract was held by a COMMENT.** Nothing executable asserted that confidence stays out of
  the stalk geometry, so the `.tex` drifted back to the retired behaviour for four days with
  nothing failing. **Now pinned:** `test_stalk_floor.cpp` asserts `compute_variance` returns the
  *identical* floor for `c ∈ {none, 0.99, 0.05}`, that the isotropic trace `d·D` stays `O(1)` at
  `d = 12/128/384`, and that confidence is *relocated* rather than discarded (`s_e·d = −ln c`).
  `compute_variance` was made public for exactly this — a comment is what regresses.
- **`curator.hpp` carried the same defect and nobody had noticed.** Two doc comments were stacked
  on `compute_variance`: the FIX-13 one, and *above it* the retired one still saying
  "*Isotropic noise floor D from confidence: sigma^2 = −ln(c)*" and citing
  `UNCALIBRATED_VARIANCE_PRIOR in curator.cpp`, **a constant that no longer exists**. Removed.
- **The `.tex`'s `\begin{hon}` passage asserted TWO resolved problems as current** — "(i) today the
  machinery is inert" and "(ii) it becomes actively harmful the moment calibration is fixed". Both
  were true when written and both were fixed by FIX-13. Rewritten to keep the diagnosis (it is what
  forced the fix) while recording the resolution with the numbers: epistemic `229.76 → 0`, and
  `0 → 0.206` on rank-0 vs rank-1 stalks, i.e. the geometry is live rather than inert.

**Numbers now in the paper, replacing the retired claim:** at `d = 384` the two retired forms give
isotropic traces of `−ln(0.95)·d ≈ 19.7` and `1.0·d = 384`, against a semantic budget of `4`.
The shrinkage floor gives `0.88`.

## 5aq. ⚠️ "PHASE 3" MEANT TWO DIFFERENT THINGS. RESOLVED (2026-08-01)

Charbel asked *"what is phase 3?"* and the file gave **two incompatible answers**:

| where | what it says |
|---|---|
| §5an, the Phase-2 close (2026-08-01) | *"NEXT IS PHASE 3, AND IT IS **COMPOSITION, NOT CONSTRUCTION**"* — wire the nine unit-tested items into a running tick |
| §7 run sheet, `## PHASE 3 — TEST AND BENCHMARK` | E8–E14 mechanism validation · B1–B4 comparative · **T1** the three-arm main test |

**The §7 numbering is STALE and is hereby superseded** — the handoff (§5al) already flagged that
run sheet as written 2026-07-27 and out of date. **Phase 3 = COMPOSITION.** The test-and-benchmark
block is real and still owed, but it is what comes *after* composition: it cannot start earlier,
because **T1 measures the gap as a function of accumulated experience**, and there is no
accumulated experience until the tick actually consolidates. Renamed in place to **PHASE 4 — TEST
AND BENCHMARK** so the two cannot be confused again.

**Third time this exact failure has been recorded** (F10's "CHOOSE THE CATEGORY", Q2b's stale 🔴,
now this). **A superseded numbering is a stale NEXT line wearing a different hat.**

## 5ap. ✅ PHASE 3 STAGES 0/3a/3b — THE LOOP IS CLOSED, AND Q(t) LEFT ZERO (2026-08-01)

Phase 2 shipped nine items that were **unit-tested and unreachable**: none was called from
`execute_dag`. Phase 3 is wiring, and the first three stages are in. **Suite 25/25, zero red.**

### STAGE 0 — what a tick must publish but was discarding
Two signals never left the tick: the **promotion verdict**, and the **activation record**.
`Verdict` moved to its own header (`verdict.hpp`) because `CognitiveState` must carry one and had
no other reason to know about Eigen. Small move, load-bearing consequence:
> **`gamma_nu` takes a Verdict, not a number. No verdict ⇒ no γ ⇒ `i_!` is never called ⇒ nothing
> crystallises ⇒ Q(t) is pinned at 0 — the constant sheaf, i.e. nothing learned.** One wire, three
> consumers: γ, E7's `verified` column, and the operator-algebra promotion gate.

Pinned by `test_tick_record.cpp`, and each assertion guards a failure that would rot **silently**:
- **`combine` takes the WEAKEST verdict.** Taking the strongest would let one passing check launder
  a refutation into the store — nothing crashes, the store just absorbs false wiring.
- **No verdict ≠ Unverifiable.** `nullopt` means no oracle ran; the enum value means one ran and
  could not decide. Collapsing them makes *"we never checked"* indistinguishable from *"we checked
  and learned nothing"* in every downstream count.
- **`retrieved` and `grown` are DIFFERENT SETS.** A cover fitted to `grown` is fitted to *growth
  order*, since a concept is grown exactly once. The test asserts they can disagree so nobody can
  alias one to the other and still pass.
- **`clear_tick_activation` actually clears**, or tick *t* inherits *t−1* and the assembly matrix
  accumulates instead of sampling.

### STAGE 2 — the accumulation driver, and a costing error it corrects
`accumulate.py` + `tasks_sample.txt`. Drives the engine until there are enough E7 ticks for
Construction 5's Tier 0.

> **🚨 THE PLANNING WAS COSTED WRONG.** The logbook's *"47 events/day"* is the **quadratic pairwise
> judgement** cost — n=7 organs ⇒ 21 calls per tick. **Tier 0 needs none of that.** It needs
> *assemblies*, and an assembly comes from SearchOp's retrieval, whose geometry is embedded
> **locally** by `embeddings.py` (bge-small, 384-d, ONNX). Only ReasonOp's `generate_thought`
> reaches Groq. **So a SEARCH-only accumulation run makes ZERO API calls and is bounded by CPU, not
> by quota.** That is why the driver builds its DAGs directly rather than going through
> `Communicator.pi_morphism`, which would spend a completion per tick planning a shape we already
> know.

**⚠️ THE VALIDITY COST OF THAT CHOICE, STATED IN THE FILE ITSELF:** a SEARCH-only corpus describes
MOS's **retrieval** structure, not its **reasoning**. Tier 0 passing on it is a statement about
retrieval co-activation, and must not be quoted as one about reasoning.

> ### 🚨 THE DAG SCHEMA WAS FLAT, AND A WRONG SHAPE DOES NOT THROW — IT PRODUCES BLANKS
> The driver first built nodes as `{"id", "op_type", "payload", "children"}`. But
> `serialize_to_flatbuffer` reads **`node["operator"]["type"]`**, **`node["operator"]["payload"]`**
> and **`node["children_ids"]`** (`communicator.py:315,403`) — the very shape its own LLM prompt
> documents at `:146–151`. A flat node is **not rejected**: `.get("operator", {})` returns `{}`, so
> the node serialises as an **UNKNOWN operator with an empty payload and NO geometry**.
>
> **The result is a structurally valid ~80-byte DAG that runs, retrieves nothing, and logs a tick
> with an empty assembly.** An accumulation run would have produced *thousands of blank rows*, and
> **only the cover fit would ever have noticed** — as a finding about organs that stopped
> recruiting concepts. `verify_dag()` now parses the buffer back and asserts it says what it was
> meant to say, because *serialising without throwing proves almost nothing here*.

**Not verified end-to-end:** the dry run reaches serialisation and stops on a missing `fastembed`
(the local bge-small ONNX embedder). The schema fix is verified **structurally** against the
serialiser's reader, not by a completed run. **A real accumulation run is still owed.**

### STAGE 3a — the bridge, and a det = −1 trap that would have passed every test
Operators act on `CognitiveState` (a `SimplicialComplex` + sheaf); every Phase-2 item is built on
`hodge::Complex2`. **Two parallel representations of "the complex" with nothing joining them —
which is exactly why nine finished items sat unreachable.**

The join is cheap because **`HodgeVertex` IS `std::string` and concepts already have names**: no
index map, no renumbering, and an identity that does not drift — a concept's name means the same
thing at tick 900 as at tick 10, which an integer assigned on first sight would not.
**Edges = concepts retrieved in the SAME tick**, the fine-level mirror of `CoarseComplex::co_activate`
— and the *same* co-activation signal Construction 5 fits its latent causes to, so the store's
wiring and the cover model come from **one** signal.

> ### 🚨 THE FINDING: ONE REFLECTION IS THE WRONG PARITY, AND IT FAILS INVISIBLY
> Aligning two unit vectors needs only **one** Householder reflection: with `w = (a−b)/‖a−b‖`,
> `H_w a = b` exactly. But **`det(H_w) = −1`**, so that map lies in the *other component of O(d)*
> from the identity the store starts at — and `crystallise` **correctly refuses** to interpolate
> across the gap, because no continuous path joins them and any blend would be a jump, not a
> transfer. **The learned map would never reach the store, Q(t) would stay 0, and every test would
> still pass.** The alignment is therefore built as a product of **TWO** reflections, `det = +1`.

**Deliberately absent: triangles.** `Complex2` supports them and `b₁` needs them, but nothing yet
decides when three concepts form a 2-simplex rather than three edges, and guessing would move `b₁`
— *the number the harmonic part exists to expose* — for a reason nobody could later reconstruct.
**Edges only, until something earns the triangle.**

### STAGE 3b — the loop closed through `execute_dag`, with the number that proves it
`Q(t) = mean ‖R^K_e − I‖²_F` is the whole acceptance criterion. **Q = 0 is the constant sheaf:
every concept means the same thing in every context, i.e. nothing learned.** Measured, on a real
SQLite `KnowledgeBase` (a stub would have been testing the stub, since SearchOp's retrieval *is*
the co-activation signal):

| | |
|---|---|
| tick 1 — 15 edges learned, γ = 0.005 (no oracle) | **Q = 0.00049347** |
| tick 2 — 10 further edges | **Q = 0.00147376** (rising) |
| `crystallise_unverified = false` | **Q = 0 exactly** |
| after a *verified* session, 3 edges | **Q = 0.0492466** |
| the learned map itself | moved **0.221916 of 2.82843** at γ = 0.05 |

**A refuted session leaves 𝕂 bit-identical**, and `i_!` moved **only the touched edge** — the rest
bit-identical. So crystallisation is gated, local, and monotone in evidence.

> **⇒ This is the first evidence the engine CONSOLIDATES rather than merely runs.** Q(t) leaving
> zero is not a proxy for it; it is the definition.

### ALSO LANDED: the cover instrument's alive-mask
`cover.py` + `test_cover_mask.py`. **A mask bug is silent** — it does not crash, it shifts `θ`, and
the shift *looks exactly like the finding it would be corrupting* ("organs stopped recruiting new
concepts"). So the mask tests assert an all-ones mask reproduces the unmasked numbers **exactly**.

### ⚠️ STILL OWED (stated, not buried)
- ~~**No triangles ⇒ `b₁` is structurally 0 in the fine store**, so the harmonic/growth-address half
  of the machinery cannot fire there yet.~~ **🚨 RETRACTED 2026-08-03 — BACKWARDS. See §5ar.**
  With no 2-cells `δ¹ = 0`, so curl is trivial and harmonic = `(im δ⁰)^⊥` of dimension
  `b₁ = E − V + b₀`: **no triangles MAXIMISES `b₁`, it does not zero it.** And since each assembly
  is inserted as a clique, `b₁(K_n) = (n−1)(n−2)/2` — one 20-concept assembly contributes 171
  artifactual cycles. **The address is not blocked, it is SWAMPED.** Stage 3a's caution about
  guessing stands; its stated consequence does not.
- **γ = 0.005 in the measured runs is the "no oracle" rate** — VerifyOp's real outcome still does
  not reach the kernel, so the verified path is exercised only in the unit test, not in the loop.
- Construction 5's **verdict about THIS corpus** still needs accumulated E7 records.

## 5ao. ✅ V7 RUN — τ_f IS NO LONGER A PLACEHOLDER, AND τ_f=1 WAS A 280× HAZARD (2026-08-01)

`python/experiment_v7.py`. Charbel refused to let τ_f=1 be closed by declaration. It is now closed
by measurement. **All checks pass; the headline is a finding nobody predicted.**

### ROUTE (a) IS MOOT — and saying so is part of the answer
V7 offered two routes. Route (a) — derive τ_f from a **time-lagged** residual, BCM-style — existed
**only because τ_f-from-the-residual was believed circular.** §5ag retracted that: the adjoint is
`(δ¹)* = W₁⁻¹(δ¹)ᵀW₂`, and `W₂` positive-definite ⇒ **onto** ⇒
`im(W₁⁻¹(δ¹)ᵀW₂) = im(W₁⁻¹(δ¹)ᵀ)`. An invertible map does not change an image, so τ never reaches
the curl subspace. With the circularity withdrawn, τ_f already has a non-circular derivation from
`π_e` one dimension up. **There is nothing left for a time-lagged estimator to repair.** Route (a)
is not skipped — *its premise was withdrawn.*

### ROUTE (b) DISCHARGED, AND THE EMPIRICAL HALF HAD NEVER BEEN RUN
§5ag proved W₂-independence analytically and checked **six random `W₂`**. That is not the same as
checking it *at the τ_f the system actually derives, on the π_e the engine actually produces* —
and until FIX-13 + the π_e wiring, **π_e was uniformly 1, so τ_f was 1 and nothing was ever
evaluated off the degenerate point.**

| measured on E5's complex, π_e from `edge_precision` at n_eff ∈ {1, 8, 40, 100} | |
|---|---|
| π_e spread | 203.18 … 478.63 (**2.36×**, genuinely non-uniform) |
| **τ_f derived** | **281.95** — not 1. The placeholder is escapable |
| τ_f at unit π | **1.000000 exactly** — day-one degradation intact |
| grad/curl/harm fractions, `W₂=I` vs `W₂=diag(τ_f)`, 200 cochains | **worst Δ = 5.55e-16** |
| the harmonic vector itself (**the growth address**) | **worst Δ = 6.66e-16** |
| invariance across τ ∈ [1e-6, 1e6] | worst Δ = 8.88e-16 |

> **⇒ E5's growth-story evidence (§5x) SURVIVES a non-identity C² weighting**, verified at the
> derived τ rather than at random matrices. §5x is not re-based.

### 🚨 THE FINDING: τ_f = 1 WAS SAFE ONLY WHILE π_e WAS ALSO 1
`F_MOS`'s coface term is `π_e²·Σ_f 1/τ_f`, so pinning τ_f=1 scales it by **τ_f itself**:

| `F_MOS(A,B)` with derived π_e | value |
|---|---|
| τ_f derived (281.95) | **147.60** |
| τ_f pinned to 1 | **41 283.86** |
| distortion | **≈ 280× (27 871 %)** |

**Shipping derived `π_e` while leaving `τ_f = 1` would have been a two-orders-of-magnitude error in
curvature** — and it gets *worse* as stalks sharpen, since τ_f scales with π_e. τ_f=1 was never a
conservative default; it was only ever correct at the point where π_e=1 too.

**The C++ engine is structurally immune, and that is by design, not luck.** `core::forman_mos`
takes only `pi` and `nu` and derives τ internally via `tau_face` — **there is no parameter through
which the two can be decoupled.** (Python's `forman_mos` *does* accept a `tau_f` override, which is
how the hazard was measurable at all.) Pinned by `test_curvature.cpp`
`test_tau_cannot_be_decoupled_from_pi`.

### DRIFT (route (a)'s live worry) — bounded by construction
τ_f is a harmonic mean of `{π_e}`, so it is bounded by min/max π_e identically. Over 40
(n_eff, confidence) combinations spanning n_eff ∈ [1, 1000] and c ∈ {none, 0.99, 0.9, 0.6, 0.3}:
**τ_f ∈ [177.01, 498.70]**, finite and positive throughout. No drift mechanism exists.

### ⚠️ COULD NOT VERIFY (stated, not buried)
**E5's complex has exactly ONE filled triangle, so exactly one τ_f exists.** A complex with several
triangles *sharing edges* could in principle couple their τ_f's; nothing here tests that and
nothing here claims it. That is the honest limit of this run.

> **⇒ V7 CLOSED. `τ_f` is a derived quantity with exact day-one degradation, certified
> non-load-bearing for E5 and demonstrably load-bearing for curvature.**

## 5an. ✅ FIX-16 CLOSED — and it immediately found two real bugs (2026-08-01)

The test could not diagnose its own failure, so **three** situations produced one opaque abort:
no server (should pass), reachable but 401/429 (should *skip* — an environment fact), and a 2xx we
cannot parse (should *fail* — our defect). Only the third is a defect, and it was the one case the
test could not name.

**Root cause was in the kernel, not the test.** `http_post` **never queried the HTTP status** — it
returned the body whether that body was a completion or an error, so a 404 was parsed as if it were
a completion. Added `ColibriHttpException` carrying status and body as **structured fields**, with
`is_credential_or_quota()` so callers can separate "this environment cannot reach the provider"
from "our request is wrong". Two more copies of the same pathology followed from it:
`generate_thought` caught, logged, and returned an **empty thought**; the latent fetch was a bare
`catch(...)`. Both now propagate or report.

### 🚨 BUG 1 — THE ENGINE COULD NEVER REACH GROQ
`main.cpp` and the test both set `host = api.groq.com` **while leaving the OLLAMA routes in place**,
so every completion 404'd with *"Unknown request URL: POST /v1/chat/completions"*. Groq serves the
OpenAI-compatible API under an **`/openai`** prefix — which `python/router.py` had right all along.
**Nothing noticed, because the 404 body was parsed into an empty thought.** Added
`ColibriConfig::groq()` so the provider's URL shape is stated **once**; two call sites independently
getting it wrong is precisely how this happened. **The engine now gets real completions from Groq
for the first time** (measured: a 1641-char reasoning chain).

### 🚨 BUG 2 — THE TEST'S CONTRACT WAS WRONG, AND THAT IS WHAT MADE IT PERMANENTLY RED
It required a **non-empty latent**. But concept geometry is computed **locally in Python** and
carried across the adjunction boundary as the FlatBuffers `geometry` field — `kernel.cpp` says so
outright: *"Operators use this instead of fetching embeddings remotely."* A completions-only
provider has no embeddings for us (Groq rejects the Ollama default `nomic-embed-text` with a 404),
so **an empty latent is CORRECT**, and downstream it means the organ stays **IDLE** rather than
zero-filled. The test now checks what it is actually for — the completions path returns 2xx with a
usable reasoning chain — and exercises curation only when geometry actually arrived, rather than
testing the zero-fill path the architecture deliberately refuses to have.

**Skips are counted separately from passes**, so a run that never exercises the live path cannot be
mistaken for one that did.

> ### ⭐ THE SUITE IS 22/22 WITH ZERO RED — the first time in the project's history.

## 5al. ⭐ HANDOFF — STATE AT END OF 2026-07-31. READ THIS FIRST IN A NEW CHAT.

**§7's run sheet is STALE (written 2026-07-27, Phase 0 is done). Read this section instead.**
Charbel is forking to a new conversation to introduce *"two heavily drastic claims"* — those are
not yet recorded anywhere and are not in this logbook. **This logbook is the shared state
(§5r); both threads must read here before acting and append here after.**

### WHAT SHIPPED THIS SESSION (7 commits, branch `fix-11-13-and-curvature-decisions`)
| | what | where |
|---|---|---|
| ✅ **FIX-11** | read-only nodes no longer poison the operad slice; foliation extracted to the testable `select_commuting_slice`; 3 slices → 1 | §5ae |
| ✅ **FIX-13** | stalk floor `O(1/d)`; **E4 epistemic 229.76 → 0**; W₂ no longer inert (0 → 0.206); `1e-9` clamp → derived `t_max = 4(1+√(eps·d))` | §5ae |
| ✅ **Q5 derived** | Forman's coefficient 3 = 1+2 from the "not both" clause; **weights must be `π_e`, NOT `w(σ,t)`** | §5ac |
| ✅ **Q6 answered** | `w_floor` was patching a forward-Euler artefact; replaced by exponential integration + a control-barrier / soft-bound certificate. **Q8 dissolves with it** | §5ad |
| ✅ **π_e derived** | `1/(D_u+D_v+s_e)` from the PC free energy; ρ **bit-identical** on uniform floors | `edge_precision.py`, §5ag |
| ✅ **τ_f derived** | harmonic mean of edge precisions; reduces to 1 so `F_MOS` reproduces `4−deg u−deg v+3m` | `derived_scales.py`, §5ag |
| ✅ **δ derived** | equal-error crossing of within/between distributions, **no hand labels**, with an identifiability flag | `derived_scales.py`, §5ag |
| ✅ **E7** | assembly recording, re-scoped off dead Ext¹ onto δ𝔇 promotion | `assembly_log.py` |
| ✅ **D̃** | `δ_eff = √(δ²+σ_dir²)`; caught that **thresholding D̃ is vacuous** | `merge_score.py`, §5ai |
| ✅ **π_v v2** | v1 restricted to the dominant mode; **refutes multi-modality as V6's cause** | `pi_v.py`, §5aj |
| 🚨 **V6 / V6b** | **§5z's closeness claim does NOT survive real text** | §5ah, §5ak |
| 🔵 **Construction 4** | organs as an overlapping cover, coarse complex as its nerve — **proposed, not built**; **AMENDED same day: filtration→zigzag, granularity claim downgraded** | §3 |
| 🔵 **Construction 5** | **the cover element DERIVED** — organs as latent causes of co-activation (noisy-OR), `F(K)` supplies the optimum σ_dir could not, the gain knob dissolves into a τ-filtration. **Re-bases C4's cover half. 16 tests in 4 gated tiers. Phase-2 item 9, PARALLEL to the main chain, blocked only on E7** | §3 |

**Questionnaire closed:** F10 dissolved · Q9 retracted (antisymmetric contract normative) · Q16 derived
· Q4/Q19/Q21/Q25 defaults adopted · Q5/Q6 answered · Q8 dissolved. **All eight Phase-2 items now have
their blocking questions answered.**

### 🚨 THE BIG NEGATIVE RESULT, STATED PLAINLY
**σ_dir/δ measures 0.32 on real text against a simulated 0.09** ⇒ merge agreement ~62%, not the
claimed 87%. Cause is **organ SEPARATION, not spread** (V1c calibrated within-organ spread and never
calibrated between-organ separation). **Three fixes tried, none rescues it:** (a) D̃ — a defensible
construction whose benefit is **still unmeasured**; (b) π_v v2 — mechanism real (−29% conditional)
but prevalence 1/11, so **refuted as the cause**; (c) organ definition — **bounded at −23% even in a
deliberately circular best case, and the TAIL WORSENS** (max 0.396 → 0.466).
**Also found: no privileged granularity exists in this corpus** — the k-sweep is monotone with no
optimum, which undercuts *every* partition-based organ definition and argues for the cover.
**Scope of damage is smaller than it looks: Cone–Bures is NOT wired into the engine.** `coherence.py`
(ω, ρ, contradiction detection) has **zero** Bures references. V6 falsifies a *proposed upgrade*.

> **RECOMMENDATION ON THE TABLE, NOT YET ACCEPTED:** re-base the §5z claim rather than defend it.
> Cone–Bures keeps everything that earned it a place under A17 — bounded, genuine metric, derived
> length scale, deletes a hand-set threshold — with HK agreement **monitored, not claimed**.

## 5ao. 🔓 PHASE 3 STAGES 0–3 BUILT (2026-08-01). Q(t) HAS LEFT ZERO.

Charbel: *"do all the stages for me, no mistake."* All four stages shipped, suite 25/25 green.
**The headline: the consolidation loop is closed and `Q(t)` moved off zero for the first time** —
0 → 4.9e-4 → 2.0e-3 → 4.4e-3 → 7.8e-3 across four ticks, monotone, and **exactly** 0 when nothing
is verified. Q = 0 is the constant sheaf, so this is the first evidence the engine consolidates
rather than merely runs.

### ⚠️ FIRST, A NAMING HAZARD: "PHASE 3" MEANT THREE DIFFERENT THINGS
| where | what it called Phase 3 |
|---|---|
| §5an NEXT (live) | **Composition** — wire the nine items into a tick |
| bottom-of-file PHASE 0–3 plan | **Test and benchmark** (E8–E14, B1–B4, T1) |
| the 6-phase plan of 2026-07-22 | **Neurogenesis** (δ𝔇, microneurons) |
The live one was the first. **The other two must be renumbered before anyone reads this file cold** —
per the file's own lesson, a superseded NEXT line is worse than no line.

### 🔑 THE ROOT CAUSE: ONE MISSING WIRE, THREE CONSUMERS
`gamma_nu` takes a **`Verdict`**, not a number. `VerifyOp::apply` computed VERIFIED/REFUTED/
UNVERIFIABLE, acted on the obstruction, and **discarded which of the three it saw.** So there was no
verdict → no γ → `i_shriek` unreachable → nothing crystallised → Q pinned at 0 → and E7's `verified`
column NULL. The same value is also the promotion gate for operator-algebra growth. **One wire
blocked the entire consolidation loop, and nothing failed loudly while it did.**

### 📐 FOUR FINDINGS THE DERIVATIONS DID NOT HAVE
1. **⚠️ E7 CONTAINED NO ASSEMBLIES AT ALL.** `cover.py` claimed *"this is exactly what E7's assembly
   log yields"*. **False.** `NodeRecord::support` is a foliation-scheduling constant — every
   implementation returns a hard-coded `{0}`, `{1}` or `{}` — with no concept identity in it. No
   amount of accumulation would have produced a T×N matrix. Fixed by recording **`retrieved`**
   (KB concepts pulled in by SearchOp's Wasserstein query — the real co-activation, overlapping
   across ticks) and **`grown`** separately. Growth is degenerate as activation: each concept is
   grown exactly once, so a cover fitted to it measures growth order.
2. **⚠️ T1's PASS CRITERION WAS BIASED TOWARD ITS OWN CONCLUSION.** `margin > 0` is only fair if the
   classes are level when neither is true. Measured, N=24 K=3 (nats/tick, + favours cover):

   | generator | T=300 | T=450 | T=700 | T=1200 |
   |---|---|---|---|---|
   | cover θ=0.20 | +0.212 | +0.182 | +0.128 | +0.127 |
   | cover θ=0.12 | +0.267 | +0.112 | +0.049 | +0.023 |
   | partition p=0.20 | +0.305 | +0.082 | −0.027 | −0.089 |
   | **partition p=0.12** | **+0.489** | **+0.291** | **+0.123** | **+0.015** |
   | permuted null | +0.062 | +0.037 | +0.021 | +0.000 |

   A **partition** at p=0.12 scores higher than a genuine cover of equal strength. Run as specified
   on a weak real corpus, **T1 would have returned COVER and confirmed Constructions 4 and 5 by
   artefact.** Not an EM local optimum: 1 → 12 restarts moved it +0.137 → +0.128, i.e. nothing. It
   is structural — at K=3 the noisy-OR marginalises 2³=8 latent configurations against the mixture's
   3 at the same parameter count. **Fixed** by `calibrated_compare`: fit the mixture, simulate from
   it, push each draw through the identical pipeline. False positives on weak partitions **1.00 →
   0.12**; power on strong cover **1.00 → 1.00**. The failure mode changed from *confidently wrong*
   to *honestly inconclusive*.
   **The calibration detail that matters: the null generator is fitted on the TRAINING FOLD ONLY.**
   Fitting it on all of X lets it see the held-out rows, the null sits too low, and the test
   over-rejects — that first attempt ran 25% false positives at a nominal 5%.
3. **⚠️ A GROWING STORE BIASES θ DOWNWARD FOR LATE CONCEPTS.** Construction 5 assumes fixed N; MOS
   grows concepts. Unmasked, every tick before a concept was born contributes a "stayed silent"
   term, so the model must explain the silence of something that did not exist. Measured on
   identical-truth data with half the concepts born halfway: apparent early-vs-late θ gap **+0.1197
   unmasked, −0.0128 masked**. **The bias mimics "organs stopped recruiting" exactly.** Fixed via
   `alive_mask`; the M-step denominator had to become per-(concept, organ), not per-organ.
4. **⚠️ THE TICK BUDGET WAS NEVER THE CONSTRAINT.** Embeddings are computed locally (bge-small,
   384-d, ONNX); only `ReasonOp::generate_thought` reaches Groq. **A SEARCH-only accumulation run
   costs ZERO API calls** — ~12 min of CPU for 1500 ticks. The "47 events/day" ceiling is the
   quadratic *pairwise judgement* cost, which Tier 0 does not need. **The real constraint is the
   supply of distinct tasks**, and `accumulate.py` refuses to hide it: cycling 6 tasks over 1500
   ticks is warned about explicitly, because effective sample size is then nearer 6 than 1500.

### 🧱 WHAT WAS BUILT
- **`verdict.hpp`** — `Verdict` lifted out of `two_complex.hpp` (which drags in Eigen) so
  `CognitiveState` can carry one. `combine` takes the **weakest** verdict: one refutation survives
  any number of passing checks, or a single pass could launder a contradiction into the store.
- **`CognitiveState`** — atomic `tick_verdict_` (lock-free CAS; several operators in one foliation
  slice may verify), plus `retrieved`/`grown`/geometry accumulators under their own mutex.
  **`nullopt` ≠ `UNVERIFIABLE`** and both are kept: "no oracle ran" is not "the oracle could not
  decide". E7 stores the first as NULL, the second as the string.
- **`concept_store.hpp/cpp`** — the bridge. `HodgeVertex` **is** `std::string`, so concept *names*
  are the vertex identity: no index map, and an identity that does not drift as the store grows.
  Edges are co-activation, the fine-level mirror of `CoarseComplex::co_activate`. No triangles —
  nothing yet earns a 2-simplex, and guessing would move b₁.
- **`align_map`** — the learning rule. **It must have EVEN parity.** One reflection aligns two unit
  vectors (`w = (a−b)/‖a−b‖`) but has det = −1, landing in the *other component* of O(d) from the
  identity the store starts at — `crystallise` then correctly refuses, the learned map never
  reaches 𝕂, and **Q stays 0 while every test passes.** Built instead as `R = H_p H_w` with
  `p ⊥ span{a,b}`: det = +1, `R a = b`. Antipodal and d=2 cases handled explicitly.
- **`execute_dag`** — the spine, closed: retrieved set → `i_star` → learn `R^W` → `W.touch` → ν →
  `gamma_nu` → `i_shriek` → `Q()`.
- **`accumulate.py`** — the driver, with a provenance manifest written even on interrupt.

### 🐛 THREE BUGS THE TESTS CAUGHT DURING THE BUILD
- **`Store`'s constructor pre-fills every edge with an identity, and `emplace` does not overwrite.**
  So the carried-over learned maps were silently dropped on every rebuild and the store reset to
  the constant sheaf whenever a concept was added. Nothing threw; Q just returned to 0.
  → `insert_or_assign`.
- **`last_verdict_` was harvested at step 5b, after the loop needed it at 4c**, so each tick would
  have crystallised on the *previous* tick's evidence — visibly wrong only on the tick after a
  refutation.
- **`accumulate.py`'s DAG dict was flat** (`op_type`/`payload`) where the serialiser wants
  `{"operator": {...}}`. Not rejected — **silently serialised as an UNKNOWN op with empty payload
  and no geometry**: a valid 80-byte DAG that runs, retrieves nothing, and logs blank assemblies.
  An accumulation run would have produced thousands of empty rows. `verify_dag` now parses the
  buffer back and asserts type, payload and 384-d geometry.

### 📋 WHAT PHASE 3 DOES *NOT* CLAIM
- **Tier 0 has still not been run on MOS's corpus.** The instrument is now trustworthy and the
  pipeline that feeds it exists; no accumulation run has been executed.
- **Q rising is not correctness.** It says the wiring left the constant sheaf, nothing more.
  Coherence ≠ correctness still stands (Construction 3).
- **`crystallise_unverified = true` is a DECISION, not a derivation.** γ(ν) is defined on three
  verdicts and "no VerifyOp in the DAG" is a fourth state it says nothing about. Default treats it
  as UNVERIFIABLE (γ = ε·γ₀) so the loop can learn in ordinary operation; `false` gives γ = 0 and,
  with VerifyOp rare, leaves 𝕂 at the constant sheaf almost always. **Charbel should rule on this.**
- **The consolidation loop is not yet PPR-instantiated.** `i_star` is seeded with the raw retrieved
  set; Phase-2 item 4's sweep-cut is not in the path. The seed is honest but unrefined.
- **Power at the realistic weak effect size is still short.** At θ=0.12, calibrated power is 0.17 at
  T=700 and 0.75 at T=1500 (FP 0.12). Larger T measured separately.

## 5ap. 🔬 THE CORPUS BLOCKER, AND A RETRIEVAL THRESHOLD THAT CANNOT WORK (2026-08-03)

Phase 3 shipped a pipeline with nothing to run through it. Three findings, one self-inflicted.

### ⚠️ 1. THE KNOWLEDGE BASE WAS EMPTY — AND EVERYTHING DOWNSTREAM WAS UNTESTABLE
`mos_brain.db` held **one** concept, of **dimension 2** — a stale test artefact that the engine's
fast dimension rejection silently skips. So `get_relevant_concepts` returned nothing, every tick's
assembly was empty, Construction 5 had no matrix, and the consolidation loop had no edges. The
retrieval half of the engine had never been exercised against real content. **This was the real
Tier-0 blocker, not task supply** — and it is invisible from the test suite, which builds its own
fixtures.

### 🔴 2. THE RELEVANCE THRESHOLD IS A NEAR-DUPLICATE FILTER, NOT A RELEVANCE FILTER
`SearchOp` sets `relevance_threshold = max(0.1, 1/dim)` and `derived_variance = ||q||`, and
`KnowledgeBase` keeps a concept when **squared** Bures-Wasserstein ≤ that. Two consequences, both
measured rather than argued:

- `max(0.1, 1/dim)` = **0.1 for every dim > 10**. The `1/dim` branch is dead; the threshold does not
  adapt to dimension at all despite looking like it does.
- bge-small returns **unit** vectors, so `‖Δμ‖² = 2(1 − cos)` and `≤ 0.1` means **cos ≥ 0.95**.

Measured on real embeddings: near-duplicate phrasings score `0.0245` ✓; genuinely related
mathematics ("sheaf cohomology of a simplicial complex" vs "Hodge decomposition on graphs") scores
`0.5214` ✗ — **rejected by 5×**. So retrieval admits paraphrases and nothing else. Almost every tick
returns ≤1 concept, **which yields no co-activation pair at all**, and a 3000-tick run would produce
a matrix Construction 5 cannot fit. `measure_retrieval.py` and cell 5 of the Colab notebook print
the size distribution across ε so the threshold is set from data rather than left at a default that
happens to be a duplicate filter.

**A second coupling, load-bearing and easy to break:** the Bures epistemic term is
`d·(√D₁ − √D₂)²` with `D₁ = ‖q‖ = 1`. A concept stored with the usual fresh floor
`stalk_floor(384, n_eff=1) = O(1/d)` sits **≈346 away on variance alone**, so nothing is ever
retrieved however well the means align. `ingest_corpus.py` therefore stores `D = 1.0` — not a tuning
choice, the only value at which the semantic term decides relevance. Verified against
`wasserstein_2_terms` (`semantic_skill.cpp:234`): at rank 0 the epistemic term reduces to that
identity exactly.

### 💥 3. A SELF-INFLICTED FAILURE WORTH RECORDING: THE INGEST MELTED THE MACHINE
The first `ingest_corpus.py` embedded all 1126 chunks in **one** `embed_batch` call, held every
vector in memory, and wrote to SQLite **once at the end**. fastembed/ONNX takes every core by
default. It pegged the laptop for 10+ minutes, was killed, and left **zero rows** — the entire run
lost. Three errors, all avoidable: no thread cap, no checkpointing, no progress output.
**Lesson: a long job whose partial progress is worth nothing is a bug in the job.** Now capped to 2
threads (set *before* import — ONNX reads those at session creation, so setting them afterwards does
nothing), committed every 50 concepts, and resumable by content hash.

### 🌐 THE CORPUS DECISION: arXiv, NOT THE PROJECT DOCS
Embedding moved to Colab (`colab_prepare_corpus.ipynb`), and the corpus changed with it. `DOCS/` was
rejected on two grounds: it would have to be **uploaded to Google**, and it is self-referential —
a Tier-0 verdict from it describes TATIANA's own documents. arXiv abstracts across six deliberately
**overlapping** categories (math.AT, math.DG, math-ph, quant-ph, math.PR, stat.ML) are public, and
carry a property that matters:

> **arXiv cross-listing IS real-world overlap.** A paper filed under both `math.AT` and `math.DG` is
> literally one concept claimed by two topics. So the corpus plausibly *has* cover structure, which
> makes a NEGATIVE Tier-0 result informative rather than merely underpowered.

Six disjoint fields would have planted a partition and rigged the question. **Cross-listing is
never shown to the model** — it is recorded for inspection only, not used as ground truth.

**Cost, measured:** precomputing geometry on Colab drops the local build cost from **0.476 s/tick to
0.001 s/tick** (476×). The engine tick itself was never the bottleneck; embedding was.

**Stated limit, carried in the manifest:** queries are sentences drawn from the same abstracts that
became concepts. That inflates *how much* is retrieved. It does not decide the *shape* of what is
retrieved, which is what Tier 0 asks — but it belongs beside any verdict.

### 📋 NEXT, DEPENDENCY-ORDERED (supersedes every earlier "NEXT" in this file)

> ## ✅ ALL FOUR PRE-PHASE-2 BLOCKERS CLOSED (2026-07-31, later same day). §5am has the detail.
> **Phase 2 is unblocked. Items 1–4 below are DONE and kept only for the record.**

1. ✅ **E7 at engine level — DONE.** `AssemblyLog` ported to C++ (`assembly_log.{hpp,cpp}`),
   recording bracketed around `Operad::run` inside `execute_dag`. `canonical_signature` is
   byte-identical to the Python across 6 shared cases (`check_signature_parity.py`).
   **No tick loses assembly data any more.**
2. ✅ **ε rename — DONE.** `ε_ρ` everywhere (`eps_rho`), 9 files, zero stale references.
   `ε_flow` has no name left to collide with when the curvature controller lands.
3. ✅ **FIX-12 propagation — DONE.** `MOS_FINALIZATION.md` D.3 carries the normative correction;
   Q10/Q11 re-specified to `{u, v, sub_claim, push_u, push_v, confidence}`; the stale **Q2b 🔴**
   and §5t's *"CHOOSE THE CATEGORY"* NEXT line are both retracted in place.
4. ✅ **Confidence → π_e — DONE.** `edge_precision.py` ported to C++; `CoarseComplex` stores
   precisions in their own map and **no longer reads the coupling weight as π_e**. A regression
   test asserts that `use_precision` with no π_e set changes nothing — which is precisely what
   the type error used to violate.

**Phase 2 proper — ✅ ALL NINE ITEMS SHIPPED 2026-08-01. See §5an for the close-out.**
5. ✅ Householder maps (m=4) → ✅ LSQR Hodge split → ✅ `F_MOS` + barrier → ✅ PPR instantiation
   → ✅ 𝕂/W split → ✅ γ(ν) → ✅ coning → ✅ rank-k SPD stalks in C++.
6. ✅ **Phase-2 item 9 — Construction 5's instrument** (`cover.py`), validated on known ground truth
   in both directions. **Its verdict about THIS corpus is still owed** and needs accumulated E7
   records; the tick only began producing them on 2026-07-31.

~~**NEXT IS PHASE 3, AND IT IS COMPOSITION, NOT CONSTRUCTION.**~~ — **BUILT 2026-08-01, see §5ao.**
The consolidation spine is wired into `execute_dag` and Q(t) has left zero. What that section did
NOT do, and what is now next:
1. **Run the accumulation.** `python accumulate.py --tasks <file> --ticks 1500` — zero API calls,
   ~12 min CPU. **Needs ≥1500 DISTINCT tasks**; cycling a short list inflates confidence.
2. **Run Tier 0 with `calibrated_compare`, never `compare_model_classes`** — the latter's `margin>0`
   rule returns COVER on weak partitions at rates up to 1.00 (§5ao finding 2).
3. **Rule on `crystallise_unverified`** (§5ao) — what an unchecked tick is worth.
4. **Renumber the two stale "Phase 3"s** at the bottom of this file and in the 6-phase plan.
5. **Put PPR/sweep-cut in front of `i_star`** — currently seeded with the raw retrieved set.

**Owed, not blocking:**
FIX-7/8/9 (docs) · FIX-15 (E5 significance overstated ~4×; fix before quoting the p-value) ·
FIX-16 (colibri test cannot diagnose its own failure — the only red in the suite) ·
**V7 (τ_f — Charbel refused to let it die; τ_f=1 is a WORKING value, not a closure)** ·
E5b at b₁≥2 · V2/E14 (**needs Charbel's ~50 labelled pairs**) · V3 · V5 ·
**V6c: a NON-CIRCULAR organ test (co-activation lens)** · **D̃ vs exact HK at the cutoff** ·
**V6d: the k-sweep against a structureless null** — without it "no privileged granularity" is
reading off k-means' own monotonicity (§5ak amendment). **⭐ NOW ABSORBED INTO Construction 5's T4,
which answers it properly with a non-monotone instrument — do not build V6d separately.**
~~**Construction 4's membership prior**~~ — **DISCHARGED by Construction 5's Beta-per-pair prior (§3).**

### ⚠️ FOUR THINGS THE NEXT THREAD MUST NOT RE-LITIGATE
1. **τ_f is NOT circular.** The Hodge split is provably independent of `W₂` (invertible ⇒ image
   unchanged), verified to 8.4e-16. I claimed otherwise and was wrong; the test lives in
   `derived_scales.py` §0 so it cannot silently un-retract.
2. **F10 is dissolved** and was already dissolved on 2026-07-27 in `MEMORY_MODEL_TWO_COMPLEX.md`.
   A stale "NEXT — blocking" line made it *look* open. **Lesson: a superseded NEXT line is worse
   than no line.**
3. **`w(σ,t)` and `π_e` are different objects.** Coupling capped on [0,1]; precision uncapped.
   Conflating them already caused one divergence bug (§5q).
4. **coarse/fine ≠ 𝕂/W.** Stratification vs store-cache. Two axes, a 2×2 (see Construction 4).

### 🧭 STRATEGIC POSITION (the honest read, for a cold start)
**Converging on internal validity, untested on external validity.** ~12 hand-set constants have been
converted to derived or measured, the architecture has survived every measurement so far, and the
theory keeps anticipating its own failure modes. **But nothing has yet tested the actual bet:**
Λ(t) unmeasured, T1 unrun, no slope observed. Every measured effect so far is **real but smaller
than hoped** (E5 weak PASS at 15% of planted level; V6 62% not 87%) — characteristic of a true but
modest theory, not a false one. **The formalism is ahead of the evidence and has been for a while.**
Marginal value of more theory is now below the marginal value of getting Phase 2 into the engine and
watching a number move.
**Engine state:** a one-shot planner-executor with memory and a coherence score. It remembers and it
notices disagreement. It does **not** yet grow, consolidate or restructure — all of that is Phase 2.
**Costs:** compute is free (µs/tick; the one trap is the Hodge pseudo-inverse, 10¹¹ flops → use LSQR,
10⁷). Space ceiling is real: 𝕂 at 100K concepts ≈ 735 MB fits in 5.9 GB, **1M ≈ 7.3 GB does not**.
**LLM is the binding wall** — the quadratic judgement cost (n=7 ⇒ 21 calls ⇒ 47 events/day) makes
batching, W-only judging and conflict-gating **mandatory, not optional**.

## 5ar. 🔍 GAP AUDIT — γ(∅) DERIVED AND SHIPPED · GAP 5 DISSOLVED · CONE–BURES RE-BASED ·
## TWO STALE MARKERS RETRACTED (2026-08-03)

Charbel asked whether the mathematical theory is complete without a Construction 6. **It is not**,
but the holes are small, local, and — the point of this section — **all closable with what is
already here**. No new mathematics is required by any of them. Full audit below, then the three
that got closed today. **Suite 25/25, zero errors.**

### 📋 THE ROSTER — FOUR OPEN GAPS, NOT FIVE OR SIX
The count drifted twice while auditing (once by miscounting a closed item as open, once by
renumbering mid-explanation and promoting a *pending decision* to a *gap*). Recorded because it is
the file's own recurring failure, and it happened again while writing about it.

| # | gap | status after today |
|---|---|---|
| 1 | `b₁` swamped by clique artifacts | **open** — §5ap records it BACKWARDS, corrected below |
| 2 | no criterion for when a 2-simplex exists | **open — same fix as #1** |
| 3 | γ(ν) defined on 3 verdicts, applied to 4 states | ✅ **CLOSED TODAY** |
| 4 | epoch length unmeasured (T13) | ✅ **DISSOLVED TODAY** |

**Not gaps, and should not be counted as such:** the 2-cochain inner product (**closed** by τ_f,
see below) · Cone–Bures (a pending decision, ruled today) · Forman's `w_α` prefactor placement
(a caveat correctly scoped to publication, §5ac).

### 🚨 CORRECTION TO §5ap — THE `b₁` CLAIM IS BACKWARDS
§5ap line: *"No triangles ⇒ `b₁` is structurally 0 in the fine store, so the harmonic/growth-address
half of the machinery cannot fire there yet."* **False, and inverted.**

For a 1-dimensional complex `b₁ = E − V + b₀`. With no 2-cells `δ¹ = 0`, so the curl subspace is
trivial and **harmonic = (im δ⁰)^⊥, of dimension exactly b₁**. No triangles does not zero `b₁` — it
**maximises** it. §7's own formula has this right (`b₁ = E − V + b₀ − F`, so `F = 0` is the max), and
`hodge.hpp:16` says it outright: *"harmonic: inconsistency around an UNFILLED cycle."*

**And the consequence is worse than the one recorded.** `concept_store.cpp:142` inserts each tick's
assembly as a **clique**, and `b₁(K_n) = (n−1)(n−2)/2` — a single 20-concept assembly contributes
**171** independent cycles, every one an artifact of inserting a clique and refusing to fill it.
> **The growth address at the fine level is not BLOCKED by `b₁ = 0`. It is SWAMPED by `b₁ ≫ 0` of
> purely artifactual origin.** Wire `harmonic_support()` to the fine store today and it returns
> confident addresses that are clique artifacts. **This is §5x's finding one level down.**

**The fix closes gap #2 with the same rule, and it introduces no knob:** fill `{a,b,c}` exactly when
all three co-fired in one assembly — *the edge rule, one dimension up*. Three facts line up:
1. the 2-skeleton of a simplex is simply connected ⇒ **within-assembly cycles all die; no
   tetrahedra needed**;
2. `H₁` depends only on the 2-skeleton ⇒ `b₁(filled) = b₁(⋃ₜ Δ(Aₜ))`;
3. `{Δ(Aₜ)}` is a **good cover** — simplices are contractible and `⋂_{t∈S} Δ(Aₜ) = Δ(⋂_S Aₜ)` is a
   simplex or empty — so the **nerve lemma applies with its hypotheses verified exactly**, unlike
   Construction 4's caveat (ii). Hence `⋃ₜ Δ(Aₜ) ≃ N({Aₜ})`.

> ⇒ **`b₁`(fine complex) = `b₁`(assembly nerve).** Surviving cycles are CROSS-assembly — genuine
> holes. And the fine store and Construction 5 stop measuring different objects.

**⚠️ TWO COSTS, STATED BEFORE ANYONE BUILDS IT.** (i) triangle count is `Σₜ C(|Aₜ|,3)`: ~1.7M at
1500 ticks × |A|=20 (≈20 MB, fine), but ~29M at |A|=50 (≈350 MB, not fine) — **decide against the
§5s cell budget first**, or enumerate from the assembly log instead of storing. (ii) **It creates
exactly the configuration V7 flagged as untested**: *"E5's complex has exactly ONE filled triangle…
several triangles SHARING EDGES could couple their τ_f's; nothing here tests that."* Filling
assembly triangles produces massively edge-sharing triangles. **A V7 follow-up on coupled τ_f is a
precondition, not a nicety.**

### ⚠️ STALE MARKER RETRACTED — §5ac's 2-cochain gap was closed by τ_f and never marked
§5ac (2026-07-30) raised *"MOS has no 2-cochain inner product… τ_f has no existing referent"* and
offered (a) `τ_f ≡ 1` declared, or (b) derive it from the 3-way residual, recommending (b).
**§5ag/V7 did exactly (b)** — τ_f = precision of the triangle circulation, the same derivation as
π_e one dimension up — and `curvature.hpp:56` now says so in as many words: *"tau_f: the 2-cochain
weight on face f, derived (logbook 5ag)."* **The ⚠️ at §5ac is stale. The gap is closed.**
**Fourth occurrence** of this exact failure (F10, Q2b, the Phase-3 numbering, now this). The
*residual* — Forman's `w_α` prefactor placement, taken from literature and not re-derived — stands,
correctly scoped by §5ac to "before any published claim rests on `F_MOS`".

### ✅ GAP 3 CLOSED — γ(∅) IS DERIVED, NOT DECIDED. SHIPPED.
`gamma_nu` is a function on **three** verdicts. `kernel.cpp` was applying it to **four** states via
`nu = last_verdict_ ? *last_verdict_ : Verdict::Unverifiable` — a partial function used as a total
one, erasing a distinction `CognitiveState` and E7 both take care to keep. §5ao flagged it as *"a
DECISION, not a derivation"* and asked for a ruling. **Charbel ruled: derive it.**

**The derivation.** "No test ran" is an *absence* of evidence, not a failed test, so the honest rate
is what a test would have licensed. Since `γ(Refuted) = 0` contributes nothing:

> `γ(∅) = E_P[γ(V)] = γ₀·[ P(V) + ε·P(U) ]`

with `P` estimated from verdicts actually observed and shrunk toward a prior of strength `κ` — the
**same Beta shrinkage Construction 5 uses for organ membership**, the third use of that idiom:

> `γ(∅) = γ₀ · [ (n_V + κπ⁰_V) + ε(n_U + κπ⁰_U) ] / (n_total + κ)`

**Day-one degradation is EXACT.** With `π⁰ = (V=0, U=1, R=0)` and `n=0` this returns precisely
`ε·γ₀` — the old value. **The hand-set decision becomes the PRIOR, and evidence moves it.** Same
pattern as τ_f → 1 at unit π. (Bit-exact for power-of-two `κ`; the default is 8. Stated, not hidden.)

**Measured, wired end to end:** 24 VERIFIED in the log ⇒ `γ(∅)` moves **0.005 → 0.03875** of
`γ₀ = 0.05`, matching `0.05·[24/32 + 0.1·8/32]` exactly.

| what shipped | where |
|---|---|
| `VerdictCounts` (counts, `observe`, `total`) | `verdict.hpp` — no Eigen, so `CognitiveState` can hold it |
| `gamma_no_verdict(counts, γ₀, ε, κ, π⁰)` | `two_complex.{hpp,cpp}`, beside `gamma_nu` |
| `AssemblyLog::scan_verdict_counts(path)` | `assembly_log.{hpp,cpp}` — **the log's only reader** |
| kernel seeds from the log, observes live, uses the derived rate | `kernel.{hpp,cpp}` |
| 4 estimator tests + 3 replay/wiring tests | `test_two_complex.cpp`, `test_assembly_log.cpp` |

**🚨 THE KNOB THIS INTRODUCES, STATED — the §5t pattern, not hidden.** It deletes the hand-set
`γ(∅)` and introduces `κ` (prior strength, in observations). That is a *better* knob — it has a
stated meaning ("how many real verdicts before data outvotes the prior"), a derived day-one value,
and it is **the same object as Construction 5's κ, so the two should be set together** — but it is a
knob and pretending otherwise would be the exact self-deception §0.8 exists to prevent.

**⚠️ THE LIMITATION, STATED NOT BURIED: the estimate is CONDITIONAL ON A CHECK HAVING HAPPENED.**
Ticks that ran VerifyOp may not resemble ticks that did not, so `P` is a conditional distribution
used as a marginal. This is real selection bias. It is **testable** (compare tick features across
the two populations) and still strictly better than a constant. **Do not quote `γ(∅)` as unbiased.**

**Design decisions worth not re-litigating:**
- **NULL is skipped by the scan, never counted.** NULL ticks are the population being extrapolated
  *to*; folding them in conditions on the thing being estimated.
- **`crystallise_unverified = false` still pins γ to EXACTLY 0.** That is a policy, not an estimate,
  so no amount of good history may move it.
- **Refutations dilute, never negate.** They enter only through the denominator, so `γ(∅)` stays in
  `[0, γ₀]` — asserted over 343 histories. Leaving that range would mean transferring more on **no
  evidence** than a VERIFIED session does.
- **`κ = 0` throws.** A zero-strength prior with no observations is `0/0`, not an uninformative
  prior, and a NaN would reach `i_shriek` and poison the store silently.
- **A truncated final line is skipped, not thrown on** — it is the normal residue of an interrupted
  accumulation run, and refusing to start over one lost verdict is worse than losing it.

### ✅ GAP 4 DISSOLVED — the epoch fix has no subject
**I said measuring T13 would be "free, a byproduct of the accumulation run". That was wrong.**
`cover.py`'s entire API is `assemblies_to_matrix · alive_mask · NoisyOr · Mixture · fit_noisy_or ·
fit_mixture · block_split · compare_model_classes · calibrated_compare · free_energy · sweep_K ·
interior_optimum · overlap_fraction · membership_prior · generate_* · permuted_null`.

> **There are no structural ops. No `split`, no `merge`, no `birth`, no `decay`. The cover is a
> BATCH EM FIT, not a grown object.** So A4-1's zigzag concerns operations that do not exist, and
> T13 counts ticks between events nothing emits. **Epoch length is not unmeasured — it is
> UNDEFINED**, and no accumulation run will produce it.

**It dissolves rather than closes**, on a decision already taken: *"(τ,t) is a bi-filtration and we
are not going there. Use the τ-barcode at fixed t; read time as a SEQUENCE of barcodes."* If PH
never runs along time, epochs never matter. τ is monotone by Construction 5's proof, so the primary
persistence claim never depended on the time axis. **Third dissolution in the project's history
(F10, Q8, now this).**
> **🔓 RE-OPEN TRIGGER, so this is not a permanent burial: the day typed structural ops land on the
> cover, T13 becomes live again.**

**⚠️ AND THE FINDING UNDERNEATH IT.** `membership_prior(n_ci, m_i, pi0, kappa)` exists — the
accumulating sufficient statistics are there — but **nothing converts accumulation into structure
change.** The cover currently **accumulates without restructuring**, which is verbatim T11's stated
failure mode: *"it is the hand-set list with extra steps."* That is a Tier-3 concern correctly gated
behind Tier 0, so it is not wrong — **but it must be written down before someone reads
`membership_prior` and concludes the cover grows.**

### ✅ CONE–BURES — THE RE-BASE IS ACCEPTED (Charbel, 2026-08-03)
Pending since 2026-07-31. **Ruled: accept the re-base.**
- **KEEP** Cone–Bures as a metric. Everything that earned it a place under A17 survives: genuine
  metric (20k triples, zero violation), bounded (kills the E4 runaway), derived length scale,
  deletes a hand-set threshold.
- **DROP** the §5z closeness claim — *"tracks true HK to under 1% / ~87% merge agreement"*. It does
  **not** survive real text (V6: σ_dir/δ = 0.32, agreement ~62%), and three rescues failed (D̃,
  π_v v2, organ redefinition bounded at −23% with a worsening tail).
- **MONITOR, NEVER CLAIM.** σ_dir/δ goes in telemetry as an observable.
- **Not to be re-litigated:** the damage was always smaller than it looked — `coherence.py` has
  **zero** Bures references. V6 falsified a *proposed upgrade*, not anything wired into the engine.

### 📋 WHAT THIS SECTION DOES *NOT* CLAIM
- **γ(∅) rising is not correctness.** It says the store transfers more on unchecked ticks because
  checked ticks have been passing. Coherence ≠ correctness still stands (Construction 3).
- **No accumulation run has been executed**, so the live `VerdictCounts` is empty and γ(∅) sits at
  its prior. The estimator is wired and tested; it has no history to learn from yet.
- **The b₁ fix is NOT implemented** — only diagnosed, with its two costs and its V7 precondition.

### 📋 NEXT (unchanged in order, updated in content)
1. **Run the accumulation.** `python accumulate.py --tasks <file> --ticks 1500` — zero API calls,
   ~12 min CPU. Now also supplies γ(∅)'s first real history. **Needs ≥1500 DISTINCT tasks.**
2. **Run Tier 0 with `calibrated_compare`**, never `compare_model_classes`.
3. ~~**Rule on `crystallise_unverified`**~~ — **DONE, derived (above).**
4. **Renumber the two stale "Phase 3"s.**
5. **Put PPR/sweep-cut in front of `i_star`.**
6. ~~**⭐ NEW — decide the b₁ fix**~~ — **DONE 2026-08-03, see §5as.** Both preconditions run;
   cap derived at 30; τ_f coupling discharged. **Two follow-ups it created:** re-calibrate
   `κ_hi`/`κ_lo` after the first accumulation (F_MOS scale moved), and read
   `widest_assembly_seen()` on that run to find out whether the cap ever fires.

## 5as. ✅ GAPS 1+3 CLOSED — THE TRIANGLE RULE, ITS TWO PRECONDITIONS DISCHARGED,
## AND A TEST THAT COULD NOT FAIL (2026-08-03)

§5ar diagnosed that §5ap's *"no triangles ⇒ b₁ = 0"* is backwards and that the growth address is
**swamped by clique artifacts, not blocked**. Both gaps it left open — the `b₁` contamination and
the missing 2-simplex criterion — close with **one rule and no new constant**. Both preconditions
§5ar attached were run first, and **one of them changed the design.** Suite **25/25, zero red**.

### ★ THE RULE — the edge rule, one dimension up
> **A 2-simplex `{a,b,c}` is recorded exactly when its three concepts co-fired in ONE assembly.**

Same signal as the edges (`concept_store.cpp` already inserts each assembly as a clique), same
signal Construction 5 fits its latent causes to. **No threshold, no new knob.** Three facts make it
the right rule and not merely a cheap one:
1. **The 2-skeleton of a simplex is simply connected** ⇒ every WITHIN-assembly cycle dies.
   **No tetrahedra are needed** — a real cost saving, not an approximation.
2. **`H₁` depends only on the 2-skeleton** ⇒ `b₁(filled) = b₁(⋃ₜ Δ(Aₜ))`.
3. **`{Δ(Aₜ)}` is a GOOD COVER** — simplices are contractible and `⋂_{t∈S}Δ(Aₜ) = Δ(⋂_S Aₜ)` is a
   simplex or empty — so the **nerve lemma applies with its hypotheses verified EXACTLY.** Unlike
   Construction 4's caveat (ii), nothing is borrowed here.

> ⇒ **`b₁`(fine complex) = `b₁`(assembly nerve).** The store and Construction 5 stop measuring
> different objects. Surviving cycles are CROSS-assembly — holes no single assembly covers.

**MEASURED, not cited** (`test_concept_store.cpp`, b₁ from RANKS):

| | n=3 | n=5 | n=7 | n=10 | 3-assembly necklace |
|---|---|---|---|---|---|
| b₁ unfilled (artifacts) | 1 | 6 | 15 | 36 | — |
| **b₁ filled** | **0** | **0** | **0** | **0** | **1** ← the real hole SURVIVES |

### ✅ P1 — COST. The cap is MANDATORY, and it is derived
`python/validate_triangles.py`. Triangles grow as `C(n,3)` while edges grow as `C(n,2)`, so their
ratio is `(n−2)/3` — **linear in assembly size, with no n beyond which the count stops mattering.**

| assembly n | triangles/tick | at 1500 ticks | store |
|---|---|---|---|
| 20 | 1,140 | 1.7 M | 82–164 MB ✅ |
| **30** | **4,060** | **6.1 M** | **292–585 MB ✅ (the cap)** |
| 50 | 19,600 | 29.4 M | 1.4–2.8 GB ❌ |
| 1000 | 166,167,000 | 249 G | ❌❌ |

**`max_assembly_for_triangles = 30`** is the largest that fits a tenth of the 5.9 GB machine —
**derived from the budget, not picked.**

> 🚨 **AND THE CAP IS NOT PRUDENCE, IT IS NECESSARY.** `KnowledgeBase::get_relevant_concepts(mu, D,
> epsilon)` is a **threshold scan with NO LIMIT** — `while (sqlite3_step(stmt) == SQLITE_ROW)` over
> the whole store. **|A| is bounded by the relevance threshold and the corpus size, not by any
> constant.** One wide tick at |A|=1000 would want 166 million triangles.

**The cap is COUNTED, never silent** (`skipped_wide_assemblies()`, `widest_assembly_seen()`). A
skipped assembly keeps its edges but not its 2-cells, so its `(n−1)(n−2)/2` cycles survive as
harmonic mass **indistinguishable from a real hole** — the exact artifact the rule removes
elsewhere. A nonzero counter means **b₁ is contaminated and the reader must know.** Pinned by test:
cap=4 on an 8-assembly ⇒ 0 triangles, 28 edges, skip count 1, and b₁ = 21 = (8−1)(8−2)/2.

### ✅ P2 — COUPLED τ_f. V7's stated limit, discharged
V7: *"E5's complex has exactly ONE filled triangle… several triangles SHARING EDGES could couple
their τ_f's; nothing here tests that."* The rule makes that configuration the normal one.

Measured on a **necklace of 4 filled assemblies** (V=24, E=84, F=140, **5 cofaces per edge**,
140 distinct τ_f where V7 had 1), π_e spanning V7's measured range:

| | |
|---|---|
| corr(τ_f, τ_f′) over 840 **edge-sharing** pairs | **+0.29 — the coupling is REAL** |
| W₂=I vs W₂=diag(τ_f), worst fraction Δ | 2.11e-15 |
| **the harmonic vector (the growth address)** | **1.67e-14** |
| positive control (perturb W₁) | **2.84e-02** ← the harness CAN detect movement |

**⇒ DISCHARGED.** V7's analytic argument (W₂ invertible ⇒ image unchanged) never depended on the
triangle count, and it survives the coupling.

> ### 🚨 THE TEST COULD NOT FAIL, AND THE POSITIVE CONTROL IS THE ONLY REASON WE KNOW
> The first version ran on a **filled K₇** — the obvious "many shared edges" object. But a filled
> clique is **contractible**, so `b₁ = 0` and the harmonic space is **identically zero**. It was
> asking whether W₂ moves a vector that is always the zero vector. **Unfailable, therefore
> worthless** — and it would have printed a confident 1e-15 PASS. The control returned **1.5e-29**
> instead of something large, which is what exposed it. Rebuilt on a **necklace**, which has the
> edge-sharing AND a real `b₁ = 1`.
> **This is §5v's lesson recurring: always compute what the statistic does when the effect is
> ABSENT, before reading it when the effect is present.** Third time.

> ### 🚨 A SECOND TRAP, WORTH RECORDING — the Euler count is WRONG once triangles share edges
> `b₁ = E − V + b₀ − F` assumes δ¹ has full row rank. **A filled K₇ has F = 35 but rank(δ¹) = 15,
> and the Euler expression returns −20** — a negative Betti number, i.e. a broken instrument rather
> than a broken complex. **Both the C++ test and the Python validator compute b₁ from RANKS**
> (`E − rank δ¹ − rank δ⁰`). Anyone reusing §7's E5 formula on the fine store will hit this.

### ⚠️ THE CONSEQUENCE NOBODY ASKED FOR — F_MOS's scale moves, so κ's thresholds are STALE
`F_MOS`'s coface term is `π_e²·Σ_{f>e} 1/τ_f`, and that sum now has `n−2` terms instead of 1:

| cofaces/edge | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| F_MOS(e) | 300 | 600 | 900 | 1200 | 1500 | 1800 |

**Exactly linear.** This is not a bug — it is the curvature of a genuinely denser complex — but
**any `κ_hi`/`κ_lo` calibrated when every edge had one coface is now wrong**, and §5t's rule (take a
quantile of the observed distribution) must be re-run after the first accumulation.

### 🧱 WHAT SHIPPED
- `concept_store.{hpp,cpp}` — triangle recording, sorted keys (a triple has ONE key however
  retrieval ordered it), the derived cap, and the skip/width counters.
- `python/validate_triangles.py` — both preconditions, with the positive control.
- 4 tests in `test_concept_store.cpp`, including the b₁ table above and the cap contract.
- The stale rationale in `concept_store.hpp` (*"no triangles… until something earns the triangle"*)
  **replaced in place** with why the premise was backwards.

### 📋 WHAT THIS DOES *NOT* CLAIM
- **`b₁ > 0` is not a growth address yet.** It says a cross-assembly hole exists. Nothing yet reads
  `harmonic_support()` in the tick, and §5x's warning stands: at `b₁ = 1` the address carries zero
  bits. **E5b at b₁ ≥ 2 is still owed.**
- **Not measured on a real corpus.** Every number above is from constructed complexes; no
  accumulation run has happened, so the true `|Aₜ|` distribution — and therefore whether the cap
  ever fires — is **unknown**. `widest_assembly_seen()` exists to answer that on the first run.
- **The cap is a real loss when it fires.** Wide ticks keep their artifacts by design.

## 5at. 🛑 HANDOFF (2026-08-03) — THE CORPUS EXISTS, RETRIEVAL PRODUCES ZERO PAIRS,
## AND COLAB IS THE WRONG TOOL FOR WHAT'S LEFT

Charbel: *"Colab is giving me a hard time... log everything so I can start a new chat... mention
alternatives to Colab."* Written as a cold-start brief — read this section alone and know exactly
where things stand.

### ✅ WHAT IS DONE AND WORKING
- **Corpus built and embedded, on real data, numbers in hand:** 1115 arXiv abstracts across six
  deliberately overlapping categories (math.AT, math.DG, math-ph, quant-ph, math.PR, stat.ML),
  **74% cross-listed** — real overlap structure, not planted. 3000 distinct query sentences, no
  cycling. `bge-small`, 384-d, unit-norm confirmed (`norms in [1.0000, 1.0000]`).
- **`gamma_no_verdict` shipped and tested** — the fourth verdict state (no oracle ran) is now a
  derivation, not a hand-set collapse onto Unverifiable. Suite 25/25.
- **The triangle rule shipped and tested** — see §5as immediately below this one. Independent of
  the corpus work; not blocked by anything in this section.
- **Three commits pushed** to `fix-11-13-and-curvature-decisions` (public repo,
  `BelSonOfOm/TATIANA`): `189fe25` (γ(∅)), `b719485` (corpus pipeline + the threshold finding
  below), `419de88` (Colab clone cell pointed at this branch, not `main`).

### 🔴 THE BLOCKER — MEASURED ON THE REAL CORPUS, NOT HYPOTHETICAL
`SearchOp`'s retrieval rule (`relevance_threshold = max(0.1, 1/dim)` against **squared**
Bures–Wasserstein) produces **zero usable co-activation** on real embeddings:

| ε | cos ≥ | mean concepts/tick | % ticks with a pair | % ticks empty |
|---|---|---|---|---|
| **0.10 (engine default)** | **0.95** | **0.07** | **0.0%** | **93.4%** |
| 0.20 | 0.90 | 0.28 | 0.2% | 71.8% |
| 0.30 | 0.85 | 0.63 | 8.1% | 50.5% |
| 0.40 | 0.80 | 6.34 | 48.0% | 31.8% |
| 0.50 | 0.75 | 58.75 | 70.9% | 21.0% |
| 0.60 | 0.70 | 193.98 | 82.6% | 12.2% |
| 0.80 | 0.60 | 627.44 | 97.0% | 1.8% |

**At the engine's own default: not "too sparse" — literally zero ticks retrieve a pair.**
Construction 5 has no matrix; `ConceptStore` gets no edges; `Q(t)` cannot move.

**Why no single threshold fixes it — embedding anisotropy, not a tuning miss.** Mean/tick jumps
**6.3 → 194** between cos 0.80 and cos 0.70. Every pair of unrelated English sentences under
`bge-small` scores cos ≈ 0.6–0.8 regardless of topic — a large common-mode offset that swamps the
topical signal. An absolute-distance threshold is measuring mostly the offset: below the band it
returns nothing, above it it returns a sixth of the corpus. No ε sits in a stable, well-behaved
middle, because there isn't one.

### 📐 THREE FIXES ON THE TABLE — NOT YET DECIDED, NOT YET MEASURED AGAINST EACH OTHER
**A. Fix ε = 0.40 and accept the skew.** Mean 6.3/tick, 48% of ticks usable (~1440 of 3000) — inside
   the calibrated test's power=0.75 range at T=1500. Cheapest: no new code, just a config change.
   **Weakness:** median is 1, not 6 — a handful of dense ticks would dominate the fit while half the
   ticks contribute nothing.
**B. k-NN retrieval instead of an ε-ball.** Top-k regardless of absolute distance; standard in RAG,
   robust to anisotropy by construction. **Real interaction to resolve, not just an implementation
   detail:** fixed k means fixed row sums, while `calibrated_compare`'s bootstrap null simulates
   *variable*-size rows from a fitted mixture. That size-distribution mismatch could inflate the
   apparent cover signal for reasons having nothing to do with latent structure. Fixable (sample k
   per tick, or use k as a cap not a fixed count) but has to be handled, not ignored.
**C. Centre and renormalise the embeddings** (subtract the corpus mean, project back to the unit
   sphere — "all-but-the-top"). Kills the common-mode offset at the source, most mathematically
   principled of the three. **Most invasive:** changes the geometry the WHOLE engine reads off —
   Bures distances, `π_v` fusion, every stalk position — not just retrieval.

**My prior going in, stated so it can be checked rather than deferred to authority: B or C over A.**
A's median of 1 means roughly half the accumulation is wasted before Tier 0 ever sees it. Untested.

### 📁 EXACT FILE STATE — WHAT EXISTS WHERE, RIGHT NOW
- **On Colab:** `concepts.npz` (2.01 MB), `queries.npz` (4.33 MB), `corpus_manifest.json` — all
  generated successfully, per the session's own reported cell output.
- **Locally: NONE of the three exist anywhere on disk.** Checked `MOS/python/` and `~/Downloads`
  directly — empty. **The browser download step is the last confirmed-working point; whether it
  completed is unknown.**
- **`mos_brain.db` still holds its one stale dim-2 concept.** No ingest has run.
- **No accumulation has run. No Tier 0 has run.** Nothing downstream of the threshold decision has
  been attempted, because the threshold decision was still open when Colab started failing.
- **What broke in Colab is NOT CAPTURED.** Charbel reported friction but not an error message,
  traceback, or which cell. **The next thread's first move must be getting that detail** — do not
  guess a Colab failure mode and build a fix for it; ask what actually happened (disconnect?
  timeout? runtime crash? quota?).

### 🌐 ALTERNATIVES TO COLAB, FOR THE NEXT THREAD TO WEIGH
Every problem this session hit — files "not found," missing dependencies on upload, browser
downloads landing nowhere — was friction from **hand-carrying files across two separate
environments** (Colab's browser sandbox and the local machine), not from the compute itself. That
should weight the comparison:

1. **GitHub Codespaces.** Free tier ~60 CPU-hours/month. A real Linux VM with the actual repo
   already checked out — no notebook cells, no npz hand-off, no browser-download step at all. Since
   the corpus is fetched from arXiv over the network (not from `DOCS/`), the exact same fetch+embed
   logic runs there unchanged; the file explorer's download is a single click, not Colab's
   multi-file dance. **Probably the strongest alternative given what actually broke this session** —
   it removes the failure surface, not just relocates it. Does NOT solve running `mos.exe` itself
   (still Windows-compiled), same as Colab.
2. **Local, throttled, overnight.** `ingest_corpus.py`'s local path already got the fix from
   the earlier machine-meltdown incident — 2-thread cap set before ONNX import, commits every 50
   concepts, resumable by content hash. No new infrastructure, zero upload/download friction, only
   cost is wall-clock time while asleep. The corpus would need to be arXiv abstracts fetched by a
   local script rather than DOCS/, to keep the privacy property Colab was chosen for.
3. **Kaggle Notebooks.** Free CPU, ~30h/week quota, similar shape to Colab. Worth trying only if
   Codespaces turns out to have its own friction — otherwise it inherits the same "notebook + manual
   file hand-off" pattern that caused the problems here.

### ⚠️ A PROBLEM THIS SESSION MADE WORSE, FLAGGED HONESTLY
§5aq (below) already diagnosed **duplicate section numbers** as a hazard and named it explicitly:
*"a superseded NEXT line is worse than no line."* This session's own commits (`b719485`) added a
**second** `§5ao` and a **second** `§5ap` without noticing the first pair — `§5an`, `§5ao`, `§5ap`
now each occur **twice** in this file (verify: `grep -n "^## 5a[nop]\."`). **Not fixed here** —
renumbering under time pressure during an urgent handoff risks a third collision. Still owed, and
now slightly worse than when §5aq first raised it.

### 📋 NEXT, DEPENDENCY-ORDERED (supersedes every earlier NEXT line in this file, including the
### stale one above 5ar that still lists "renumber the two stale Phase 3s" as item 4 — it's three now)
1. **Get the actual Colab error before doing anything else.** Screenshot, error text, or "which
   cell" — not a guess.
2. **Confirm whether `concepts.npz`/`queries.npz`/`corpus_manifest.json` exist anywhere** (Colab's
   `/content/`, Drive if mounted, Downloads, browser download history). If genuinely lost, the
   arXiv fetch + embed is cheap to redo (~5 min) wherever it runs next.
3. **Decide A vs B vs C on the retrieval threshold** — ideally by measuring, not arguing further.
   All three are cheap to prototype against the already-fetched corpus once the files are in hand.
4. **Pick where corpus-prep + Tier-0-fitting run next** — Codespaces, throttled-local, or retry
   Colab once the actual failure is known.
5. Then: ingest → accumulate (local only, needs `mos.exe`) → `run_tier0.py` with
   `calibrated_compare`, reading `retrieved` not `grown`.

## 5au. ✅ THE RETRIEVAL BLOCKER IS CLOSED — BY LABELS, AND THEY OVERTURNED THE PLAN (2026-08-04)

§5at left A/B/C undecided because relatedness had **one** hand-checked label. Built
`extract_refs.py` (a paper's own `\label`/`\ref` graph IS a relatedness label) → **71 papers, 2468
blocks, 2266 ground-truth positives**, no hand-annotation, no LLM budget. Then
`measure_reference_recall.py` ranked every candidate rule against them. Full detail:
`DOCS/THE_RETRIEVAL_PROBLEM.md` §10.

**MEASURED, and it inverted my own recommendation:**
- Pedestal `‖μ̄‖² = 0.671` (I had INFERRED 0.60 — right phenomenon, 12% low). Separation `z = 1.92`
  (I had INFERRED 1.3–1.5 — **the signal is better than feared**).
- The engine's `ε = 0.10` admits **0.31%** of true dependencies. Blocker reproduced on labelled data.
- **The pedestal was never a ranking problem, only a thresholding problem.** For fixed `q`, `‖μ̄‖²`
  and `⟨μ̄,r_q⟩` are constant in `k` and cannot affect rank order. So centering/ABTT is worth
  **+4.3 points** while abandoning the absolute threshold is worth **0.3% → 44.2%, ~140×.**
  **The whole A-vs-B-vs-C argument was about a 4-point effect.**
- At equal width (~25): rank-based **46.6%** vs ε-ball **37.5%**, and rank kills the variance
  (no empty ticks, no over-cap ticks).
- **R1 (diffusion / the "heat map" metric) REFUTED** — 12 configs (α×t), none beats raw, monotone
  degradation in `t`. Mechanism: a near-constant kernel ⇒ near-uniform walk ⇒ diffusion distance
  dominated by the stationary distribution. **It amplifies hubness rather than removing it**;
  Coifman–Lafon's α-normalisation corrects sampling *density*, not a rank-1 ambient offset.
- My own two-stage coarse→fine idea **did not pay** (48.4 vs 47.9).

**DECISION: top-`k` retrieval, `k = 24`, on `abtt-10` vectors.** `k` is **derived, not chosen** —
§5as budgeted 6.1M triangles and `C(24,3)×3000 = 6.07M`. This **deletes ε** *and* **deletes
`max_assembly_for_triangles` as a separate knob**: retrieval width IS the cap, so no assembly is
ever skipped and **b₁ is uncontaminated by construction** rather than by a warning counter. Two
hand-set constants collapse into one number from the memory budget (A17 satisfied).

**R3 (max-entropy null) is PROMOTED from option to prerequisite.** Top-`k` gives every row of the
co-activation matrix **exactly** `k` ones, and `cover.py:479`'s `_simulate_mixture` provably cannot
generate constant row sums. **The retrieval decision breaks the existing null**, so the fixed-margin
max-entropy ensemble is now blocking for any Tier-0 verdict. **R2 (Fisher local metric) DEFERRED** —
every local/spectral competitor measured moves recall by at most ±4 points, and `Σ_q` is estimated
from the already-wrong neighbourhood it is meant to rescue; it survives only as a *theory* bet on
context-dependence, to be judged by what it does to the cover, not by recall.

**⚠️ Limits:** measured on blocks-within-papers, **not** the 1115-abstract corpus — qualitative
findings transfer, recall figures do not. 100% of ref-edges are within-paper. `bge-small` is now
quantified as adequate-but-mediocre; a better embedder is the largest unpulled lever.

**Lesson (the same one as §5v, a fourth time):** the argument ran for three sessions on one data
point. The measurement took two hours and reversed the conclusion. **Build the labelled set first.**

---

## 5av. 🚨 THE OLD NULL PRODUCES A FALSE POSITIVE — MEASURED, NOT ARGUED (2026-08-04)

Tier 0 was run twice on **identical data** (3000 ticks × 1074 concepts, top-24 retrieval, K=6,
B=99), changing **only the null**:

| null | median | excess | p | verdict |
|---|---|---|---|---|
| **legacy** (free margins, independent Bernoulli) | −2.1538 | **+0.2329** | **0.0200** | **COVER** |
| **margin-matched** (R3, fixed row sums) | −1.9275 | +0.0065 | 0.4500 | no evidence |

Observed margin −1.9210 in both. **The verdict flips from a significant positive to nothing.**

**Mechanism.** Real rows have **exactly** 24 ones (sd 0.00); the legacy null emits Binomial row
sums (sd 3.08). On null data the mixture can spend components capturing row-size variation — an
advantage it does not have on real fixed-width data — so the null distribution shifts down and the
observed value looks anomalously high. Textbook **Type I error inflation**, and exactly what
Gotelli's survey of ecological null models reports: *"the three models that maintain fixed row sums
are invulnerable to Type I errors."* See `DOCS/PRIOR_ART_AND_THE_REPLAN.md` §1.

> 🚨 **HAD TIER 0 RUN AS PLANNED IN §5at, IT WOULD HAVE RETURNED `COVER at K=6, p=0.0200` AND WE
> WOULD HAVE BELIEVED IT.** R3 was promoted from "option" to "prerequisite" on a logical argument
> (top-k forces constant row sums, `_simulate_mixture` cannot produce them). That argument is now
> **measured**, and it caught a false positive worth the whole thread.

**⚠️ NEITHER VERDICT IS ABOUT MOS.** Both ran on the single-centre-tick protocol, where each tick is
a top-k ball around ONE query point — one cause by construction. That fixes the answer to
"partition" before any data is seen (the Modifiable Areal Unit Problem; §5aw below). **Two
independent bugs: a broken null, now fixed and demonstrated; a broken protocol, diagnosed and open.**

## 5aw. THE TICK WAS THE BUG, AND THE INSTRUMENT WAS BLIND (2026-08-04)

**Prior art searched** (`DOCS/PRIOR_ART_AND_THE_REPLAN.md`): our problems are all named elsewhere —
ecology's fixed-margin null debate (Connor–Simberloff, curveball), geography's **MAUP** (the tick is
the areal unit; results "vary artifactually with chosen aggregations"), **IBP vs DP mixture** (our
cover-vs-partition test, and it infers K so our guessed K=6 is removable), OSLOM, and TDA's
**Lattice Effect** — the documented name for §4.3's "the nerve captures the geometry of the cover
itself." **Cover detection is not novel; MOS's contribution is the sheaf over it, the growth law,
and the accumulating engine — infrastructure should be borrowed, not invented.**

**Phase A shipped:** `curveball_randomize` in `cover.py` (row AND column sums exact, 25.1% of cells
moved), pinned by test. Documented that it does **not** repair `_simulate_mixture_margin`'s sampling
bias — that needs conditional-Bernoulli draws; measured deviation stays 0.985. **A2 (EM convergence
measurement) still owed.**

**Phase B — the concept-side reframe.** A cover is overlapping patches, and *overlapping* means an
ELEMENT lies in two patches. So ask per concept, not per tick: collect every tick a concept fired
in, and test whether those neighbourhoods split. **Multi-cause structure lives ACROSS ticks, not
within one — so the broken single-centre ticks are adequate for this question.**
Result: **AUC 0.514–0.550 against cross-listing labels, inside the noise floor** (geometric null
scores 0.523–0.529 on meaningless labels; 1 SE ≈ 0.029 at 115 positives). **No signal.**

> ★ **THE POSITIVE CONTROL IS WHAT MADE THAT READABLE, AND IT NEARLY DIDN'T RUN.** Planted
> two-cluster data scored **0.0209 against a one-blob null of 0.0199** — the first Phase-B run was
> measuring *nothing*, because 67 points in 384-d have concentrated distances so every 2-means split
> scores alike. Per-concept PCA restores power, but only above ~40% of neighbourhood radius.
> **Without the control, "AUC 0.50, no cover structure" would have been reported as a finding — a
> second protocol artifact, one step after diagnosing the first.** §5v's lesson, fifth occurrence.

**Most likely cause of the null result, and it is a labelling problem:** `\ref` labels worked (2266
positives, decisive) because they are **semantic** — an author asserting a dependency. **arXiv
cross-listing is administrative**; a math.DG/math.AP filing need not bridge anything. Next test
should use the `\ref` block corpus, where a block cited from two distant sections is a genuine
bridging element. Not distinguishable yet from the instrument's 40% floor or from real absence.

---

## 5ax. PHASE B AGAINST SEMANTIC LABELS — SECOND NULL, AND THE REASON IS MEASURABLE (2026-08-04)

§5aw blamed the null result on the label (arXiv cross-listing is administrative, not semantic). So
Phase B was rerun against a **structural** label built from the `\ref` graph — non-circular by
construction, since it is computed from **character offsets in the LaTeX source** and never touches
the embeddings:

```
citer_span(v) = (max_pos(citers) − min_pos(citers)) / doclen
```
"a lemma invoked in §2 and again in §9 serves two parts of the argument."
538 blocks with ≥2 citers, 212 labelled bridging.

| | bimodality AUC | separation AUC | spearman vs span |
|---|---|---|---|
| real | **0.4932** | 0.5210 | −0.005 / +0.045 |
| geometric null | 0.5171 | 0.5181 | +0.057 / +0.023 |

**The real AUCs sit at or below the geometric null's. Zero signal, second labelled attempt.**

**⚠️ A confound I introduced and caught mid-run.** The raw span is predicted by **in-degree alone at
AUC 0.748** — the range of *n* points widens with *n* whether or not anything bridges. Dividing by
the expected range `(n−1)/(n+1)` cut it to 0.636. The score's AUC did not move, so the conclusion
stands, but as first written the label was measuring popularity.

**★ WHY IT FAILED, AND THE NUMBER WAS ALREADY IN HAND.** The label is **logical/argumentative** ("this
lemma is invoked over there"); the score is **similarity-geometric** ("this block's neighbourhoods
split"). A lemma can be invoked from §9 without resembling §9's prose. `THE_RETRIEVAL_PROBLEM.md`
§10 already measured the disagreement: **recall@30 = 44–48%**, i.e. more than half of cited blocks
never appear in their citer's top-30 neighbourhood. Validating a neighbourhood statistic with
citation labels was therefore expected to fail at roughly the observed rate. **That number was
measured days earlier and not connected before the run.**

**Not nothing:** real neighbourhoods score bimodality **0.445** vs the geometric null's **0.397**,
against a positive control where a clean 4σ split scores 0.631 and structure-free scores 0.357. Real
data carries ~a quarter of a clean split's structure — but it is **not concentrated in the blocks
either label calls bridging**. It reads as generic topic clustering, not specific multi-context
concepts.

### 🛑 THE PATTERN, STATED BECAUSE IT IS THE REAL FINDING OF THE DAY
**Three design mismatches in a row, each caught only by a control, none by the headline number:**
1. **single-centre ticks** — one cause by construction, answer baked in before data (MAUP);
2. **blind instrument + administrative label** — planted clusters scored 0.0209 vs a 0.0199 null;
3. **citation label vs similarity score** — different relations, disagreement already quantified.

Every measurement so far has described **our setup**, not the data. That is not bad luck: it is what
happens when an experiment is built before deciding precisely **what observation would distinguish a
cover from a partition in MOS.** **Next action is that definition, not another score.**

**Standing rule earned today: no measurement is reportable without a positive control.** It caught
items 2 and 3, and in both cases the artifact looked exactly like a result.

---

## 5ay. 🔧 SELF-AUDIT — THREE CLAIMS WEAKENED, AND AN EPISTEMIC-STATUS CONVENTION (2026-08-04)

Charbel reviewed the write-ups and identified over-reliance on a thin evidence base. On audit he was
**too generous**; three claims in §5au–§5ax were overstated and are corrected here. All three
corrections **weaken** conclusions written earlier the same day.

**C1 — the effective sample size is ~71, not 2266.** Every `\ref` label comes from one of 71 papers,
and blocks inside a paper share topic, author and overlapping neighbourhoods. Confidence intervals
computed from label counts are **too narrow**. Consequence: Phase B's AUC floor is nearer **±0.04**
than the ±0.029 quoted in §5aw, so the most suggestive figure (0.5495) is ~1.2 SE, not 1.75. **The
negatives are weaker than reported; the instrument had less power than claimed.** Future
significance claims must cluster by paper.

**C2 — `abtt-10` was argmax on a flat sweep.** abtt-1 → 48.3%, abtt-5 → 48.3%, abtt-10 → 48.5% are
indistinguishable under C1. §5au reported 10 as "best" and the decision adopted it on that basis.
Correct reading: removing the mean plus a *small* number of principal directions is worth ~+4 points
**[MEASURED]**; `r = 1` **[ENGINEERING CHOICE]**, for simplicity. **This is precisely the error §5aj
identified in the k-sweep — reading an optimum off a flat curve — repeated in a document that cites
§5aj.**

**C3 — `k = 24` is an ENGINEERING CHOICE, not "derived".** §5au and §5aw both said "derived, not
chosen." Three faults: §5as's 6.1M triangle budget is itself an unmeasured flop/memory estimate
(the logbook's own standing reminder covers this); recall rises monotonically in `k` (35.5% at k=10
→ 53.4% at k=50), so 24 is where a cost constraint bites, not where quality peaks; and two
independent constraints landing on the same number is exactly the tidiness motivated reasoning
produces. **[OPEN HYPOTHESIS]** that retrieval width should equal the topology budget — testing it
means varying `k` against `b₁`, never run.

**⭐ THE CONVENTION, NOW STANDING.** Every load-bearing claim in `THE_RETRIEVAL_PROBLEM.md`,
`THE_COVER_QUESTION.md` and this logbook carries one of:
`[MEASURED]` · `[DERIVED]` · `[INFERRED]` · `[ENGINEERING CHOICE]` · `[OPEN HYPOTHESIS]` ·
`[SPECULATION]`.

**Why it earns its place (A17):** the failure mode this week was never bad statistics — it was
**good numbers attached to conclusions they do not support**. C2 and C3 are both that failure, and
both were invisible until the claim and its evidence were forced next to each other. The tag makes
that adjacency mandatory rather than optional.

**What survives all three corrections:** rank-based retrieval over the ε-ball (0.31% → 46.6%,
**[MEASURED]**, large), and the fixed-margin null catching a false positive (p = 0.02 → 0.45,
**[MEASURED]**, direct). Those are the two results to keep if everything else here is wrong.

---

## 5az. 🏁 TIER 0 CLOSED — INCONCLUSIVE, WITH EVERY FAILURE UNDERSTOOD (2026-08-05)

Attempt 4 ran the operational reframe Charbel specified: not "is the topology a cover?" but
**"what observation would force us to believe overlap is NECESSARY?"** — measured as a per-concept
**transitivity deficit** (open triangles) against the fixed-margin `curveball` null. He supplied the
essential caution, which the design honours: an open triangle is **not** evidence of a cover, since
co-activation is sampled and A–B, B–C, no A–C can arise with perfectly transitive latent structure;
only **excess relative to a margin-preserving null** licenses any claim.

**Controls were run BEFORE the corpus, per the standing rule. The result is a verdict on the
instrument:**

| setting | synth partition | synth cover | geometric balls | real corpus |
|---|---|---|---|---|
| `w=1` | z −175, tail 0 ✅ | **+9.24 sd, recovers 60/60 planted bridges ✅** | **100% z>2 ❌** | 99.6% z>2 |
| `w=3` | z −130 ✅ | **−1.81 sd ❌ INVERTED** | z −1.0 ✅ | 91.8% z>2 |
| `w=5` | z −55 ✅ | **−7.13 sd ❌ INVERTED** | z −2.9 ✅ | 94.0% z>2 |
| `top-m=30` | z −29 ✅ | **−6.25 sd ❌ INVERTED** | z −4.7 ✅ | 87.8% z>2 |

**There is NO parameterisation where the cover control and the geometric control both pass.** At
`w=1` the statistic recovers planted bridges exactly — and calls a structureless Gaussian cloud a
cover for 100% of its concepts. Wherever the geometric control is clean, **planted bridges score on
the wrong side.** `min_weight` is a frequency filter and bridges have higher frequency; the
degree-controlled fix (`top-m`) repaired the geometric control but not the inversion.

> **★ THE METHODOLOGICAL WIN: this artifact was caught BEFORE interpretation, not after.** The real
> column shows 87.8% of concepts at z>2 against a geometric control at 0.1%. Without the cover
> control that would have been reported as a decisive positive. It is the fourth artifact this week
> and the first one that never reached a conclusion.

**[MEASURED] and unexplained, worth keeping:** the corpus has a large transitivity deficit that is
reproduced by *neither* the margin-preserving null *nor* ball geometry. **[SPECULATION]** its shape
(near-universal rather than a minority of concepts) looks more like a continuum than K discrete
patches — but the instrument that produced it fails its own control, so this is a hunch, not a
finding.

### 🏁 TIER 0: FOUR ATTEMPTS, ALL INCONCLUSIVE, EACH FAILURE DIAGNOSED
| # | instrument | outcome | cause |
|---|---|---|---|
| 1 | global likelihood margin (noisy-OR vs mixture) | inconclusive | single-centre ticks ⇒ single-cause by construction (MAUP); **and the null manufactured a false positive** |
| 2 | per-concept bimodality × arXiv cross-listing | inconclusive | instrument blind below ~40% separation; label administrative |
| 3 | per-concept bimodality × citation span | inconclusive | construct mismatch — logical vs geometric relation; recall@30 = 44–48% already quantified it |
| 4 | transitivity deficit × curveball null | **instrument refuted** | no setting passes both controls |

**ESTABLISHED [MEASURED]:** retrieval was broken (0.31% → 46.6%) and is fixed; the legacy null
manufactured a cover at p = 0.02 and is fixed; the corpus carries a real, unexplained transitivity
deficit.
**NOT ESTABLISHED:** anything about whether MOS's memory has a cover. **Four failures to reject the
partition are not evidence that the partition is true.**

**ACCEPTANCE CRITERION FOR ANY FUTURE TIER-0 INSTRUMENT, earned the hard way:** it must pass a
synthetic partition, a synthetic cover **with planted bridges recovered in the right direction**,
and a structure-free geometric control — **at one shared parameter setting** — before it is pointed
at the corpus. None of the four met it.

### ➡️ AND THE BOTTLENECK IS NO LONGER THE STATISTIC
Charbel's call, and it is right: every attempt has asked *"given these retrieval events, what shape
do they have?"* when the question a brain model owes is *"why did these retrieval events happen?"*
**MOS has no generative model of cognition.** The retrieval work's real result is that **the geometry
of a static embedding is not a sufficient foundation for a cognitive architecture** — which locates
the next layer precisely: not in a better similarity metric, but in the rules that generate thought
over time. See `DOCS/THE_GENERATIVE_THOUGHT_MODEL.md`.

---

## 5ba. 🛑 CHAPTER CLOSE — COLD-START HANDOFF FOR THE GENERATIVE PHASE (2026-08-05)

**Read this section alone and know exactly where the project stands.** The retrieval-and-Tier-0
chapter is closed. The next chapter builds a generative model of cognition. Written as a brief for a
new conversation with no memory of this one.

### 📍 REPO STATE
Branch `fix-11-13-and-curvature-decisions`, public repo `BelSonOfOm/TATIANA`. Three commits close
this chapter:
- `a8a608a` — retrieval fix + labelled evaluation + the false-positive null
- `7781e1a` — Tier 0 closed, four instruments, the calibration battery
- `5b9823d` — the generative-phase workflow

**Uncommitted and NOT ours** (pre-existing, left alone): `concept_store.hpp/.cpp`,
`test_concept_store.cpp`, `mos_brain.db`, deleted `DOCS/*.pdf`, and untracked
`simulate_retrieval.py` / `validate_triangles.py`. **`simulate_retrieval.py` is referenced by the
docs and is still untracked — decide whether it goes in.**

### ✅ SETTLED — [MEASURED], survives every caveat
| finding | number |
|---|---|
| the engine's `ε = 0.10` was a near-duplicate filter | admits **0.31%** of true dependencies |
| rank-based retrieval beats it at the same width | **46.6%** vs 37.5% |
| the embedding pedestal is real and large | `‖μ̄‖² = 0.671`, unrelated pairs cos ≈ 0.669 |
| semantic signal is real but mediocre | `z = 1.92`; recall@30 ≈ 44–48% |
| **the legacy null manufactured a cover** | p = **0.0200** → p = **0.4500** on identical data |
| diffusion/heat-kernel retrieval | refuted, 12 configurations, none beats raw |
| citation and similarity are different relations | they agree only ~47% |

### ❌ REFUTED / CORRECTED
- **R1 (diffusion metric)** — dead.
- **R2 (Fisher local metric)** — deferred; bootstrapping flaw stands (`Σ_q` is estimated from the
  neighbourhood it is meant to fix).
- **`abtt-10` "best"** — argmax on a flat sweep; `r = 1` is equivalent. **[ENGINEERING CHOICE]**
- **`k = 24` "derived"** — **[ENGINEERING CHOICE]**, not derived; its budget input is unmeasured.
- **Noise floors** — computed assuming independence; effective *n* is ~71 papers, not 2266 labels,
  so every quoted interval was too narrow and the negatives are **weaker** than reported.

### 🔓 OPEN — and these are the questions for the next chat
1. **What is the input stream?** A brain model needs something to think *about*. `\ref` chains?
   paper sequences? task streams? **UNDECIDED, and it will shape everything downstream exactly the
   way the tick definition silently determined four Tier-0 results.** Decide it deliberately.
2. **Directed edges.** Temporal succession is asymmetric, so `W` becomes non-symmetric and the
   existing cohomology changes meaning. Real theoretical work.
3. **Whether the 𝕂/W sheaf adjunction is a new formalisation of CLS** (§4.3 of the workflow) — if
   so, that is the paper, not "we invented a two-store memory."
4. **The unexplained transitivity deficit** — real, not margin-explained, not geometry-explained,
   currently uninterpretable. **[SPECULATION]** it looks like a continuum rather than K patches.
5. **Whether `bge-small` is adequate** — never compared against a stronger embedder.
6. **A2 (EM convergence measurement)** and **exact conditional-Bernoulli sampling** — both still owed.

### 🧰 BUILT AND WORKING
`build_corpus.py` (local corpus, Colab dead) · `extract_refs.py` (2266 free semantic labels) ·
`make_assemblies.py` (top-k + abtt + geometric null) · `measure_reference_recall.py` ·
`measure_multicontext.py` / `_refs.py` · `tier0_parallel.py` · `measure_open_triangles.py`
(refuted as an instrument, **reusable as the calibration harness**) · `cover.py` gains
`_simulate_mixture_margin` and `curveball_randomize`, both tested.

### 📏 THE DISCIPLINE, PAID FOR IN FULL THIS CHAPTER
1. **No measurement without a positive control.** Four artifacts caught; the fourth before it became
   a result.
2. **Any cover instrument must pass synthetic partition + synthetic cover (bridges in the RIGHT
   direction) + structure-free geometric — at ONE shared setting** — before touching real data.
3. **Every claim carries an epistemic-status tag** (`[MEASURED]`…`[SPECULATION]`).
4. **Effective sample size, not label count.**
5. **Never read an optimum off a flat sweep.** Done twice; the second time in a document citing the
   first.
6. **Time one complete unit of work before extrapolating.** A 15-minute estimate became 90 by
   multiplying two draws.
7. **Checkpoint long jobs.** A job whose partial progress is worth nothing is a bug in the job.
8. **Prior art before implementation.**

### ➡️ FIRST ACTIONS IN THE NEXT CHAT
1. Read `DOCS/WHY_A_MODEL_OF_COGNITION.md` (the case) then
   `DOCS/THE_GENERATIVE_THOUGHT_MODEL.md` (the workflow).
2. **Build the lag-CRP test harness BEFORE the simulator** (§12 of the workflow). It is the gate
   that decides viability, and building the test first makes it impossible to tune the model to the
   test without noticing.
3. Then G0's skeleton on a synthetic graph with planted structure. **Gate: it must recover a
   structure it was given.**
4. Answer open question 1 (the input stream) before G4.

### ⚠️ THE ONE THING THE NEXT CHAT MUST NOT FORGET
**A simulator produces the topology its rules imply.** The inversion from "assume a cover, test it"
to "simulate cognition, observe topology" is stronger — and is also Attempt 1's failure at ten times
the scale, harder to catch because a simulator is complicated enough to hide its own assumptions.
**No topology claim before the behavioural battery passes.** That rule is the whole reason the
workflow has the shape it does.

---

## 5bb. 🧭 THE SHEAF BECOMES LOAD-BEARING — AND FOUR THINGS ALREADY BUILT THAT WE RE-DERIVED (2026-08-08)

**Session character: no code written, one measurement spec produced, three literature gates run,
and four discoveries that the codebase already contained what was being designed.** Charbel opened
by setting a standing rule for this phase: *nothing is implemented until he demonstrably understands
it, and claiming to understand is not sufficient — it must be tested.* That rule was applied and
it caught a real gap (see "The gate that fired", below).

### 🔀 THE FORK, RESOLVED
`THE_GENERATIVE_THOUGHT_MODEL.md` left open whether the sheaf is load-bearing or decorative.
`PRECILLA/draft.md` answered it by **default** — it classified the sheaf as "AUXILIARY, for
topological reading", which is the decorative branch, without flagging that a choice had been made.

**Decided: LOAD-BEARING.** The activation is a 0-cochain, the spreading operator is built from the
sheaf Laplacian, `ρ` constrains the dynamics rather than describing them afterwards. The draft's
classification is retracted.

### 🧮 THE DUALITY — `J ↔ (C, F, η)` up to gauge
**[DERIVED]** The coupling matrix is not primitive; it is read off from `M = (C, F, s)`:

```
    J  =  (D − L_F)   +   η
          symmetric      antisymmetric
          = the sheaf    = a 1-cochain
```

- sparsity pattern ← 1-skeleton of `C`; symmetric part ← restriction maps; antisymmetric part ← `η`.
- The transport reading: the only canonical route `v → u` is push into the edge stalk, pull back —
  `F_{u⊴e}* F_{v⊴e}`, which IS the off-diagonal block of `L_F`.
- **Varying stalk dimension is native.** So is non-flatness (nontrivial holonomy round cycles).
- **The diagonal stops being free** — determined by the same restriction maps. One hand-set decision
  deleted, A17 satisfied without argument.
- **Gauge:** `J` fixes `F` only up to `∏_e O(d_e)`. **`Π_{O(d)}` in the consolidation formula is
  exactly a gauge fixing** — written months earlier for an unrelated reason.
- `s` is not part of `J`. `J` is structure, `a` is what it acts on, `s` is `a` when coherent.

### ☠️ PERFECT COHERENCE IS DEATH — `ρ` IS A LYAPUNOV FUNCTION
**[DERIVED]** `L_F = δ*δ` ⇒ self-adjoint and PSD ⇒ under `ȧ = −L_F a`, `dV/dt = −‖L_F a‖² ≤ 0` for
`V = ½‖δa‖²`. So `a(t) → P_{H⁰}a(0)` exponentially at the sheaf spectral gap. **Fatal four ways:**
the thought freezes; cue↦thought becomes a linear projection (Stage 1 with extra steps); generically
`H⁰ = 0` so `a → 0`; and a fixed point has no transitions, so the lag-CRP is *undefined*, not failed.

**A thought is `a* = L_F⁺(q − φ)`** — the least-incoherent state compatible with the drive. Never a
section, always an approximation to one.

**Only `φ` (fatigue) can prevent the collapse.** `σ` makes it worse (Banach contraction ⇒ unique
globally attracting fixed point); `λ` is a rank-one uniform shift that moves the fixed point without
removing it; `x_t` is disqualified (the model must run with empty input); `c` freezes when `A` does.
**This upgrades the fatigue ablation from a guess to a theorem.**

⚠️ **Honest limit.** Linearising the fast/slow pair on an `L_F`-eigenmode gives trace `< 0` and
determinant `> 0` — **a stable spiral. Linear fatigue buys damped oscillation, not a limit cycle.**
Sustained motion requires slow `J` learning (already present), noise (added, below), or a nonlinear
limit cycle (**[OPEN HYPOTHESIS]** — a finding to look for, never to design in).

**New observable:** `ρ(t)` should be a **sawtooth** — falling as the thought coheres, jumping when
fatigue ejects it. If it decays monotonically to a floor, the model is dead and one plot shows it.

### ✅ THE THREE OPEN ITEMS, ALL CLOSED
1. **Primacy** — `[SEARCHED]` start-list context reinstatement, not rehearsal, not a learning-rate
   gradient. The CMR literature already ran that comparison. **Costs one parameter and NO new state
   variable.** What was called "blocks G1, needs a design session" was one search.
2. **Noise** — **[DERIVED]** `τ² = 1/π_e`. Precision *is* inverse variance; `π_e` already exists and
   commit `2f6d64b` already established it as a genuine inverse variance rather than a score.
   `[SEARCHED]` — this is exactly active inference's construction (precision = inverse temperature
   in the softmax). **Claim no novelty.** And a noisy threshold unit IS a sigmoid unit, so fixing `τ`
   also fixes the gain — **a hidden hand-set constant inside the bare symbol `σ`.**
   ⚠️ Exact for **probit**, off by ≈1.6 for logistic. **Probit chosen.**
   → Revised ledger: **three knobs deleted (`k`, the leak, the gain), zero added.** The earlier
   "two deleted, one added" was wrong in our favour and is retracted.
3. **Input stream** — decided. **G0** synthetic planted structures · **G1** standard word lists ·
   **G4** `\ref` dependency chains. Rejected: random walks on the concept graph (circular by
   construction) and paper-reading order (no authored structure).
   ⚠️ **The guard that makes it non-circular:** Spec A's subset is never G4's input (50/50 split),
   and **the shuffle comparison is the experiment, not a control** — run citation order vs shuffled
   order and report what *differs*. What survives shuffling is dynamics; what doesn't is input.

### 📚 LITERATURE GATE PROTOCOL — ADOPTED
Rule 9 was written down and under-applied; tagging a claim ⚠️ *unsearched* flags a risk without
discharging it. Operational form: **at each gate, before building, one specific question, 2–4
searches batched, stop when either a standard answer exists or none does, record the verdict.**

**First round, 2026-08-08 — three searches, three changes to the spec:**
- **Primacy** → mechanism adopted (above).
- **Directed cohomology** → **the Alexandrov proposal is RETRACTED.** Sheaves on a preorder are
  constant on each strongly connected component, and a dense recurrent `J` is one giant SCC, so its
  cohomology is trivial *by construction*. Replaced by **GLMY path homology** (arXiv:1207.2834),
  which has persistent versions (arXiv:1701.00565) and — decisively — **an efficient algorithm for
  1-dimensional persistent path homology** (SoCG 2020), exactly the dimension the growth address
  lives in. Reachability homology (IMRN 2025) addresses the reachability question directly.
- **Precision→noise** → confirmed standard, novelty disclaimed.

**Second round, same day — concept formation:** DreamCoder (Roy. Soc. 2023), predicate invention in
ILP, chunking-as-compression/MDL. See "the growth law needs a cost side", below.

### 🔍 FOUR THINGS THE CODEBASE ALREADY CONTAINED
This session re-derived work that exists. **Recording it as a process failure, not a footnote: the
code was not read before the design was written.**

1. **`concept_store.hpp` already contains the growth-address story AND a fix we did not know about.**
   Its header: with no 2-cells `δ₁ = 0`, so harmonic `= (im δ₀)^⊥` of dimension `b₁ = E − V + b₀`;
   and since `observe` inserts each assembly as a **clique**, one assembly of size `n` contributes
   `(n−1)(n−2)/2` cycles alone — **171 for a 20-concept tick.**
   > **"The growth address was never blocked. It was SWAMPED, by artifacts of inserting cliques and
   > refusing to fill them."**
   The fix: a 2-simplex is recorded exactly when its three concepts co-fired in ONE assembly — the
   edge rule one dimension up, no new constant. Justified by the **nerve lemma with hypotheses
   verified exactly** (assembly simplices are contractible and their intersections are simplices),
   giving `b₁(fine complex) = b₁(assembly nerve)`. Validated in `validate_triangles.py`.
   **Consequence for Spec A:** the store's triangle rule is *co-firing*, NOT the clique complex.
   The clique complex remains right for the **citation** graph (no assemblies there, so no
   co-firing rule is available) — but the two graphs use different rules and the spec must say why.
   There is also a **cap** (`max_assembly_for_triangles_ = 30`, derived from the 5.9 GB budget) and
   `skipped_wide_assemblies()` is exposed **because a skipped assembly's cycles look exactly like a
   structural hole**. MUST be read before interpreting `b₁`.
2. **`HodgeSplit::harmonic_support` exists in `src/core/hodge.cpp:287`.** The harmonic extraction is
   already in C++.
3. **`cone_bures.py` exists** — the HK/WFR cone metric with `δ` = *"the distance beyond which two
   concepts stop being one thing that moved and become two different things"*. The concept-identity
   operator. Plus commit `8a4529e`, "coning off cycles, with the chord comparison measured."
   So **the where** (harmonic class) and **the how to attach** (cone) both exist.
4. **The Stage-1 retrieval fix never reached the engine.** `src/operators/primitives.cpp:58` still
   computes a *threshold* and calls `get_relevant_concepts(..., relevance_threshold)`, and
   `concept_store.hpp:138` confirms it is *"a THRESHOLD SCAN WITH NO LIMIT over the whole store."*
   **This is the measured 0.31%-of-true-dependencies bug, still live in the C++ engine.** See §7.

### 🧬 CONCEPT FORMATION — WHAT THE GROWTH LAW STILL LACKS
Charbel asked whether concepts "reproduce and evolve like bacteria to humans", with a DNA-like
structure permitting mutation.

**Position taken, and it is a substantive one:** variation-and-selection needs randomness *because
it has no address*. Natural selection cannot inspect an organism and say "you need a wing here."
**MOS computes an address.** Adding random mutation would discard the architecture's main asset.
Memetics specifically is a metaphor with little predictive content and is not a foundation.

But the *structural* half is sound, and MOS already has it: the inheritable content is the **stalk**
plus the **attachment**, and the genetic operators are `bind` / `collapse` / `cone`, already in `𝔇`.
**Directed surgery, not random mutation.**

**⚠️ THE REAL GAP THE LITERATURE EXPOSES.** `[SEARCHED]` DreamCoder, predicate invention and
chunking **all use compression (MDL) as the criterion**; we use "kill an obstruction". Coning a
cycle of length `k` **costs** 1 vertex + `k` edges + `k` triangles + a stalk, and **buys** `b₁ − 1`.

> **Our growth law has no cost side.** Applied literally it fills every hole — and the store's own
> header already warns `b₁` gets swamped. A criterion with no cost over-generates concepts.

**Proposed law, strictly better than the current one:** *attach a concept over a cycle that RECURS,
and only when the recurrence pays for the attachment.* This is DreamCoder's rule (it extracts
**common** sub-expressions, not any sub-expression). It also answers a question we had not asked —
which of several holes to fill first — and **deletes that decision rather than handing it to a
human. A17.**

**[OPEN HYPOTHESIS]** whether obstruction-killing *is* compression. Plausible (fewer independent
cycles ⇒ shorter description) but unproven, and the cost side suggests they come apart. **If true we
inherit forty years of MDL results; if false we must say which criterion we use and why.**

### 🎯 THE GATE THAT FIRED
Charbel's rule was applied to three questions on the new formalism. Two were answered by quoting the
explanation back verbatim — **retrieval, not understanding** — and were rejected. The third
("what does a zero growth address mean about concepts?") was re-taught in plain language with a
three-exercise worksheet (a rankable triangle; an unrankable *filled* triangle; an unrankable
*unfilled* 4-cycle) and **he then produced the right answer independently: "add a new concept in the
middle connecting all four" — which is the cone.**

**The rule works. Keep it.** Also recorded: two explicit complaints that the explanations were
over-technical and *"clouding everything with technicalities"*. The correction that landed was
plain-language-first, math-second, with a worked example before any symbol.

### ❌ CORRECTIONS TO `PRECILLA/draft.md`
| # | correction |
|---|---|
| 1 | **Type error.** `q_t = αx_t + βc_{t−1} + γ_g g_t` is added to `Ja ∈ ℝ^N`, but `c ∈ ℝ^d`. Requires `V ∈ ℝ^{N×384}`: `q_t = αx_t + βVc_{t−1} + γ_g Vg_t`. **Forces `d = 384`**, not the claimed `d ≈ 100` |
| 2 | **`W` → `J`.** The draft overwrote the symbol for the working complex. Also colliding: `d`, `γ`, `ρ` (**vs the coherence functional**), `φ` |
| 3 | **No noise anywhere**, yet §6 computes recall *probabilities* and silently introduces a Luce rule absent from §3 |
| 4 | **D6 is wrong by one nonlinearity.** `P ∝ exp(a_j)` with `a_j = σ(h_j)` gives a ratio capped at `e ≈ 2.72` regardless of `w₃`. Needs softmax on the **pre-activation** |
| 5 | **D7 is a category error.** Precision-weighting fuses several noisy estimates of ONE latent; `x_t`, `c`, `g` are different quantities in different spaces being *composed*, not fused |
| 6 | **§10.2 is wrong.** Uniqueness of the assembly-size fixed point is two lines: `f` is strictly decreasing, `g = f − k` strictly decreasing with `g(0) > 0 > g(N)`. Exactly one root. The *real* problem is that `μ, σ_h` depend on `k`, so the equation **is not closed** — closing it gives `√k(λ − m) = s·Φ⁻¹(1 − k/N)`, i.e. what controls width is the **excess inhibition `λ − m`**, with `k* ∼ (λ−m)^{-2}` |
| 7 | **§7.8's "not fitted" is self-deception.** An upper-triangular SR was installed and forward asymmetry derived from it. **The asymmetry was inserted.** G1 criterion replaced: (a) `γ`, `ρ` learned from the input stream never fitted to the CRP, (b) magnitude in the human 1.5–2× range, (c) long-range and across-list contiguity, which an upper-triangular `M₃` does **not** install |
| 8 | **§7.1's defence may be void.** `M₁` and `M₄` are collinear by construction (PMI is computed from co-activation, which is driven by semantic similarity), so `w₁` may not be **identifiable** and cannot be "read off". **Report the 5×5 Gram matrix and its condition number BEFORE learning anything** |
| 9 | **§7.5 Alexandrov** — retracted, see above |

### 📄 ARTEFACT
`DOCS/SPEC_GROWTH_ADDRESS_AND_DYNAMICS.md` — Spec A (the growth-address measurement, no simulator,
runs on existing data, five controls with numeric pass criteria) and Spec B (the dynamics, with
every decision stated). **Pre-registered before any run: clique complex on the citation graph, raw
count difference `η(i→j) = #(i cites j) − #(j cites i)`, 50/50 split, probit.**

### 🔓 STILL OPEN AFTER THIS SESSION
1. **[OPEN HYPOTHESIS]** Does the sigmoid support a sustained limit cycle, or are noise and slow
   learning the only sources of ongoing motion?
2. **[OPEN]** **Cover/partition is not well-posed as stated.** "Do the supports of a basis of `H⁰`
   overlap?" is basis-dependent. Krull–Schmidt makes the indecomposable decomposition canonical
   (cellular sheaves on a finite complex are modules over a finite-dimensional algebra), so
   *partition ⟺ indecomposable summands have disjoint supports* is rigorous — but computing it is
   potentially wild-quiver-hard, and the practical proxy (small-eigenvalue eigenvectors of `L_F`)
   reintroduces the basis problem. **Real gap.**
3. **[OPEN HYPOTHESIS]** Is obstruction-killing the same as MDL compression?
4. **[OPEN]** What rule sets a newly-coned concept's **stalk**? Barycentre — in which geometry?
5. **[OPEN]** A new concept needs a **label**, which is not derivable from a cycle. The one place an
   LLM is genuinely required and real novelty enters rather than being computed.
6. **[OPEN]** Growth is **sequential** — filling one hole changes the others. Order matters.
7. **[UNVERIFIED]** Is every symmetric matrix realisable as `D − L_F`? Freedom exists at rank 1;
   higher-rank stalks unchecked.
8. Carried from §5ba: `bge-small` never compared against a stronger embedder; A2 (EM convergence);
   exact conditional-Bernoulli sampling.

---

## 7. 🚀 THE ROAD TO A FIRST PROTOTYPE (written 2026-08-08)

**The single most important observation in this section: there are TWO tracks and they are
separable. Conflating them has been costing time.**

| | Track A — MOS as a working research tool | Track B — MOS as a model of cognition |
|---|---|---|
| serves | goal 1 (a free tool for the masters) | goals 2–3 (thesis, the science) |
| needs the generative model? | **NO** | yes, it *is* the generative model |
| status | plumbing mostly built, **one measured bug live** | design complete, nothing built |
| distance to a demo | **short** | months |

**A prototype of MOS solving a problem does not require the generative cognitive model.** It
requires the plumbing to be finished and one already-measured bug to be fixed.

### ✅ DONE AND VERIFIED ON DISK
- `MOS/build/Debug/mos.exe` builds (2026-08-03).
- `CognitiveState` `M = (C,F,s)` dual-track; `OSKernel` executing FlatBuffer Operad DAGs over stdin
  IPC with CRC32; `Operad` foliating DAGs into commuting slices via a ThreadPool.
- `ConceptStore` = **𝕂 over concepts** — the growing co-activation graph plus its sheaf, keyed by
  name so identity does not drift as the store grows. Edges = co-retrieval in one tick; triangles =
  co-firing in one assembly; cap at 30 with skipped-count exposed.
- `Complex2` / `HodgeSplit` including `harmonic_support`. Householder restriction maps, matrix-free
  LSQR, rank-`k` SPD stalks.
- The consolidation loop is closed (`test_consolidation_loop.cpp`), `Q(t)` instrumented.
- `SemanticEmbedding` with Woodbury low-rank and genuine Bures–Wasserstein; `cone_bures.py`.
- Python organ layer, all migrated to `ModuleVertex`; `coherence.py` (authoritative `ρ`);
  `precision.py`; `router.py` (tiered Groq, 8B triage → 70B reasoning, both free).
- Stage-1 measurement suite and the calibration harness.

### 🔴 BLOCKING A PROTOTYPE — in priority order

**P0 — Port the retrieval fix into the C++ engine.** `src/operators/primitives.cpp:58` still computes
a relevance *threshold*; `concept_store.hpp:138` confirms it is a threshold scan with no limit.
**[MEASURED]** that scheme admits **0.31%** of true dependencies; rank-based at the same width gets
**46.6%**. This is the largest single defect in the system, it is already diagnosed, and the fix is
known. **Everything downstream of retrieval is currently being fed near-noise.**
*Side benefit:* a rank rule bounds `|A|`, which is exactly what `max_assembly_for_triangles`
currently has to defend against.

**P1 — `support` name→vertex-id resolution.** `π` is currently told to emit `support: []`, so DAG
nodes cannot name the concepts they act on. Without it the operad cannot be pointed at anything
specific.

**P2 — Hook `VerifyOp` to a real checker.** `VerifyOp` exists and returns a three-valued verdict `ν`
that gates consolidation via `γ(ν)`, but it is not connected to a prover or a sandbox. Until it is,
**`γ(ν)` is gated on an unearned judgement** and the crystallised store can absorb errors.

**P3 — Confirm `Q(t)` moves.** Commit `1e7fc88` closed the loop with *"Q(t) left zero"*. Consolidation
that never accumulates is consolidation in name only. One run with the fixed retrieval should be
enough to tell.

**P4 — One end-to-end demo on a real question.** The reference problem is on record: eigenvalues of
the Hodge–Laplacian on differential forms of `ℂℙ³`. Ingest → retrieve → reason → verify → respond,
with the assembly log and `ρ(t)` recorded.

### 🟡 NOT BLOCKING, BUT NEXT
- Gram matrix of the five `M_k` (minutes; can invalidate the draft's central defence).
- Spec A controls 1–4, then the null, then the real run.
- `semantic_skill.cpp` fused-covariance exactness, still unverified.

### 📊 THE TEST THAT COUNTS, UNCHANGED
**T1 — three arms, SAME LLM: bare | plain-RAG | MOS.** Primary measure is the **gap as a function of
accumulated experience — a derivative, not a level.** Not valid: MOS vs a frontier model
single-shot; unequal call budgets; `Δρ` as an outcome (coherence ≠ correctness); `κ` capacity.

---

## 6. Failures & dead ends (so we don't repeat them)

- ❌ **2026-07-27 — FCA / Formal Concept Analysis as the memory substrate.** Proposed to make the
  complex's shape canonical by computing it from an object×attribute context (Galois connection ⇒
  a unique complete concept lattice, no parameters, no seed, no encoder). **Rejected by Charbel on
  the correct ground:** it is data-determined, and its canonicity comes precisely from discarding
  the history that makes a memory a memory. MOS must GROW (history-determined), not be RECOMPUTED.
  Also carries an exponential-lattice-size risk. *Salvage: possibly useful as a local FOLDING move
  during consolidation. Not the foundation.* **Lesson: canonicity and growth are in tension; we
  want growth, and the audit's "choose a category" problem (F10) is dissolved by the two-complex
  model rather than solved.**
- ⚠️ **[SUPERSEDED — the entry below was written from §5v and is RETRACTED. See §5w (why the
  statistic could not support it) and §5x (run 2: weak PASS). Kept as the record of the error,
  which was real and instructive: a verdict declared on a statistic that had never been shown
  to discriminate a known positive.]**
- ❌ **2026-07-29 — the cohomological growth law, on the evidence available: NOT SUPPORTED.**
  E5 ran (§5v). Measured η is *significantly more gradient-like than isotropic noise*
  (0.209 vs null 0.400, z=−2.19, p=0.014). One potential per organ largely explains the
  pairwise judgements ⇒ H¹ has little to find ⇒ **the growth law still has no address.**
  Filed here per §7's own instruction, but filed as **SUSPENDED, not dead**: (a) the pilot uses
  SIMULATED organs, all from one model in one call, which biases *toward* this outcome;
  (b) the controls behaved correctly and contested scored 3.4× them, so the instrument does
  track real disagreement; (c) one repeat produced 65% harmonic mass localised exactly on the
  unfilled cycle. **Lesson that outlives the result: the PASS criterion as originally written
  ("a non-trivial fraction") would have passed pure noise, because the isotropic null already
  puts 0.400 of the energy in curl+harmonic. Always compute the null of a projection-based
  statistic BEFORE reading the statistic.** Second lesson: check the TYPE of a measurement
  against the object it is meant to be — a symmetric "agreement" score can never be an
  antisymmetric 1-cochain, and no amount of care downstream repairs that.
- ❌ **2026-07-27 — reading the growth address off H¹ of a DERIVED cochain.** §5p's growth law
  ("the obstruction cocycle names the cell to attach") cannot fire from δx: [δx]=0 in H¹ always.
  Needs a MEASURED η. Kept as a dead end because the mechanism is still wanted — only its input
  was wrong.
- ❌ **2026-07-30 — the K₀ / Jordan–Hölder canonical memory schema (audit F10). DROPPED.**
  The proposal was to give every memory a canonical identity as a Jordan–Hölder class in K₀ of a
  suitable abelian category. It dies on the choice of category, and **both** candidates the book
  offers fail for opposite reasons: `Hol(𝒟)` makes every Gaussian concept a *simple* module
  (k[x] is simple over the Weyl algebra in char 0), so JH length is 1 and the class carries no
  information beyond identity; `Rep(Q)` makes the class the *dimension vector*, which collides
  catastrophically as a retrieval index. §29–32 of the book argue in one category, §33–37 in the
  other, §47 in neither. **Lesson: Jordan–Hölder gives canonicity GIVEN a category — it cannot
  pick the atoms, and no amount of downstream care supplies them.** Dissolved rather than solved:
  the two-complex 𝕂/W model already supplies memory identity through growth history. Same
  tension as the FCA rejection above — canonicity vs growth — resolved the same way, for growth.
  *Salvage: none claimed. Q24's default (keep the D-module/Koszul/quiver chapters out of every
  paper) now has a second independent reason behind it.*

---

### Session log

- **2026-08-03 (latest, handoff)** — **Corpus built (1115 arXiv abstracts, 74% cross-listed; 3000
  tasks), but retrieval as shipped produces ZERO co-activation pairs at the engine's own default
  threshold** (measured on the real corpus: 0.0% of ticks, 93.4% empty) — an embedding-anisotropy
  problem (mean/tick jumps 6.3→194 between cos 0.80 and 0.70), not a tuning miss. Three fixes on
  the table (fixed ε=0.40 / k-NN / centre-and-renormalise), none yet decided or measured against
  each other. Colab then became unreliable mid-session with the specific failure UNCAPTURED — next
  thread's first move is getting that detail, not guessing it. concepts.npz/queries.npz reported
  generated on Colab but confirmed ABSENT locally (Downloads and MOS/python/ both checked, empty).
  Alternatives to Colab logged (GitHub Codespaces recommended first, since this session's actual
  failures were all file hand-off friction between two environments, not compute). Also: this
  session's own commits added a SECOND §5ao and §5ap without noticing the first pair — §5an/ao/ap
  each now appear twice, worse than when §5aq first flagged duplicate numbering. Full brief: §5at.
- **2026-08-03 (later)** — **GAPS 1+3 CLOSED — the triangle rule.** A 2-simplex is recorded exactly
  when its three concepts co-fired in one assembly: the edge rule one dimension up, **no new
  constant**. Measured: filled cliques go from `b₁ = (n−1)(n−2)/2` to **0** at n=3,5,7,10, while a
  3-assembly necklace keeps **b₁ = 1** — the cross-assembly hole survives, exactly as the nerve
  lemma predicts. Both of §5ar's preconditions run first, and **both paid**: (P1) the cap is
  MANDATORY, not prudent, because `get_relevant_concepts` is an unlimited threshold scan — |A| is
  bounded by the corpus, not a constant, and one tick at |A|=1000 wants 166M triangles; cap **derived
  at 30** from the 5.9 GB budget, and **counted rather than silent** because a skipped assembly
  keeps its artifacts. (P2) V7's untested coupled-τ_f configuration is **discharged** (corr +0.29
  over 840 edge-sharing pairs, split moves 1.7e-14). **Two traps caught, both worth remembering:**
  my first P2 test ran on a filled K₇, which is **contractible**, so it asked whether W₂ moves a
  vector that is identically zero — **unfailable, and only the positive control (1.5e-29 instead of
  large) exposed it**, §5v's lesson a third time; and `b₁ = E−V+b₀−F` is **wrong** once triangles
  share edges (filled K₇: F=35, rank δ¹=15, Euler returns **−20**), so both the C++ and Python
  paths compute b₁ from ranks. **Uninvited consequence: F_MOS scales linearly with cofaces/edge,
  so every κ_hi/κ_lo calibrated at one coface is now stale.** Suite 25/25. See §5as.
- **2026-08-03** — **Gap audit** on Charbel's question *"is the theory complete?"* Answer: **no, but
  the four remaining holes need no new mathematics.** Closed three things and corrected two.
  **γ(∅) DERIVED AND SHIPPED** — `gamma_nu` was a function on three verdicts being applied to four
  states; it now estimates what an unchecked tick is worth from the verdicts actually observed,
  `γ₀·[(n_V+κπ⁰_V)+ε(n_U+κπ⁰_U)]/(n+κ)`, shrunk by the same Beta prior Construction 5 uses, with
  **exact day-one degradation** to the old `ε·γ₀` (measured: 24 passes move it 0.005 → 0.03875).
  Persisted across sessions by `AssemblyLog::scan_verdict_counts`, the append-only log's first
  reader. Stated openly: it introduces `κ` and the estimate is **conditional on a check having
  happened** (selection bias, testable, not unbiased). **GAP 5 DISSOLVED** — and I had costed it
  wrong: `cover.py` has **no structural ops at all**, so epoch length is *undefined*, not
  unmeasured, and A4-1's zigzag concerns operations that do not exist; it dissolves on the standing
  τ-axis-only decision, with a re-open trigger. Underneath it: the cover **accumulates without
  restructuring** — T11's failure mode verbatim. **CONE–BURES RE-BASE ACCEPTED** by Charbel: keep
  the metric, drop the §5z closeness claim, monitor σ_dir/δ rather than claim it. **Two stale
  markers retracted:** §5ac's 2-cochain gap was closed by τ_f back on 07-31 (fourth occurrence of
  that failure), and **§5ap's `b₁` claim is BACKWARDS** — no triangles *maximises* `b₁`, and since
  assemblies are inserted as cliques the growth address is **swamped by artifacts, not blocked**;
  the fix (fill within-assembly triangles) also closes the 2-simplex gap and makes
  `b₁`(fine) = `b₁`(assembly nerve) by a nerve lemma whose hypotheses are met *exactly*. Suite
  **25/25, zero errors**. See §5ar.
- **2026-07-31 (later)** — Implemented **D̃** (`merge_score.py`) and **caught that my own
  recommendation was a category error**: thresholding D̃ is VACUOUS (D is bounded by w₀+w₁ and
  D̃ ≤ D, so the test always passes; max D̃² = 1.7987 vs bound 2.0 over 3000 pairs). *Multiplying a
  score and its threshold by the same number cannot change a decision.* The real correction is a
  **length scale**: `δ_eff = √(δ² + σ_dir²)` — spread adds to the identity scale in quadrature.
  Triangle violations are **worse** with measured σ_dir (+1.29 at δ=0.3 vs §5z's +1.08), so the
  D/D̃ dispatch is mandatory. **The motivating claim is still unmeasured** — §5z's agreement table
  was never computed for D̃. Then, on Charbel's push that "organs = documents" is a relic: clarified
  the coarse/fine vs 𝕂/W confusion and wrote **Construction 4** (organs as an overlapping cover,
  coarse complex as its Čech nerve; cover is the state, nerve the observable; functional modules as
  a κ-weighted prior; overlap pinned by criticality σ≈1; four stated ways to fail). See §5ai, §3.
  Then **π_v v2** (`pi_v.py`, 45 tests): caught that Construction 2's "v2 = top principal
  component" is **type-defective** (v1 returns a position, a PC is a direction) and resolved it as
  *v1 restricted to the dominant mode*; found the eigengap is **not** a valid multi-modality test
  (an elongated cigar scores 49.8 vs a truly bimodal 12.2) and replaced it with BIC ∧ Ashman's D;
  fixed a basin-of-attraction bug that falsely called concentric core+halo clouds bimodal 60% of
  the time. **Result: v2 does NOT fix V6** — conditional effect −29.1% but prevalence only 1/11
  organs, so the median moves −3.1% and the worst pair not at all. **This ELIMINATES model
  misspecification as the explanation and confirms §5ah's separation diagnosis from the other
  side. V6's bad result stands.** Construction 4's multi-modality argument is correspondingly
  weakened and must not be reused. See §5aj.
- **2026-07-31** — **Charbel overturned my τ_f circularity claim and was right.** The Hodge split
  is provably independent of `W₂` (an invertible map cannot change an image), verified to 8.4e-16
  — so there was never any circularity and E5 was never at risk. **τ_f, π_e and δ are now all
  DERIVED and implemented** (`derived_scales.py`, `edge_precision.py`): τ_f = harmonic mean of the
  edge precisions (reduces to 1 in the unit case, so `F_MOS` reproduces `4−deg u−deg v+3m`
  exactly); π_e = 1/(D_u+D_v+s_e) from the PC free energy, which is finally where Q9's confidence
  belongs and is dimensionally safe there (ρ verified **bit-identical** on uniform floors); δ from
  the equal-error crossing of the within/between distance distributions, no hand labels, with an
  identifiability flag. Also shipped **E7** (`assembly_log.py`, re-scoped off the dead Ext¹ purpose
  onto δ𝔇 promotion) and **V6** (`measure_sigma_dir.py`). **V6 is a bad result and it stands:
  σ_dir/δ measures 0.32–0.42 against a simulated 0.084–0.100, so §5z's "tracks true HK to under
  1%" does NOT survive real text** — the cause is not σ_dir but organ SEPARATION (V1c calibrated
  within-organ spread and never calibrated between-organ separation). Cone–Bures survives as a
  metric; the closeness claim does not. Caught one of my own errors mid-run (δ from ‖Δμ‖ while the
  column said d_BW, overstating the ratio 2.4×). See §5ag, §5ah.
- **2026-07-30** — Status review before building. Confirmed against source that **FIX-11 and
  FIX-13 are both still open** (`operad.cpp:66` sets `slice_is_global_mutation` for *any*
  empty-support node, poisoning the slice even after the READ_ONLY guard admits it;
  `cognitive_state.cpp:224` and `curator.cpp:20` still build stalks with `empty_U(dim,0)` and a
  1.0 prior, so **C++ W₂ is still Euclidean and every C++ entropy identical** — `belief.py`'s fix
  is not ported). Then closed the finalization questionnaire: **F10 dissolved** (K₀/JH schema
  dropped, see §6), **Q9 retracted and the antisymmetric organ contract made normative**,
  **Q16 moved to the derived scale**, **Q4/Q19/Q21/Q25 defaults adopted**. Charbel held **Q5/Q6
  (curvature)** open for discussion — correct, it is the only default that moves weight. Also
  caught that `MOS_FINALIZATION.md` still lists **Q2b as 🔴** though §5t resolved it and §5y
  collapsed Q2c. See §5aa, §5ab.
  **Then, same session:** Charbel sent Q5 back to be derived rather than imported — which
  **closed C5-2** (the coefficient 3 is `1 + 2` from Forman's "not both" clause, verified by hand)
  and produced the real finding: **Forman's weights define the inner product for the Bochner
  decomposition, so they are fixed by the Laplacian the engine already uses — Π and the stalk
  precisions, NOT the Hebbian coupling w(σ,t).** Using w would compute the curvature of the wrong
  operator. Exposed a genuine gap: **MOS has no inner product on 2-cochains**, which augmented
  Forman needs. See §5ac. On Q6 he rejected the signal-only probation outright; the answer turned
  out to be that **`w_floor` is the wrong mechanism** — the exact flow is multiplicative and
  cannot sever, so the floor was patching a forward-Euler artefact. Replaced by exponential
  integration plus a **control-barrier / soft-bound certificate**, which is the same object the
  brain implements as weight-dependent plasticity. **Q8 dissolves with the floor.** See §5ad.
  **Shipped:** FIX-11 and FIX-13 both closed, with a new 16-assertion test file; E4's epistemic
  term measured at **229.76 → 0**, W₂ no longer inert (0 → 0.206 on rank), the 1e-9 confidence
  clamp replaced by the derived `t_max = 4(1+√(eps·d))`, and foliation extracted to a testable
  seam (3 slices → 1). Full suite: **13/14 C++ (the one red is pre-existing, proven by stash) and
  4/4 Python.** Raised FIX-16. See §5ae.
- **2026-07-22** — Read all of DOCS + full MOS architecture. Established the two-level decision, killed "Pachner", drafted Construction 1, opened the fix registry, created this logbook. Charbel flagged: (a) wants brain-like *growth*; (b) wants this log; (c) fix everything but he's on a tight token budget — warn before expensive tasks.
- **[TOMORROW'S PLAN IS AT THE END OF THIS FILE — §7]**
- **2026-07-27** — Audited the two incoming external documents (scrutiny + book) hostile-referee style; proofs checked by hand. Produced `AUDIT_SCRUTINY_AND_BOOK.md` (F1–F14) and `MEMORY_MODEL_TWO_COMPLEX.md`. Key findings: the ρ splitting and Prop 8.2 are real and load-bearing; Prop 8.2 **blocks §5p's growth law**; the `.tex` is stale vs the engine (F1); four technical errors in the incoming docs (F2, F7, F9, F13); the K₀ memory schema is vacuous (F10). Charbel rejected FCA as substrate and specified the two-complex (crystallized 𝕂 / working W) architecture, which was formalised via the sheaf adjunction ι_! ⊣ ι* ⊣ ι_*. Steps 1–4 branched to a separate chat — **this logbook is the shared state.** Adopted the "must change a number the engine prints" test for future formalism. See §5r.
- **2026-07-29 (branched thread)** — E1 + E4 shipped, E3 partially run, `.tex` resynced, FIX-6 and FIX-10 closed. See §5u. Raised FIX-11.
- **2026-07-29 (main thread, run 4)** — Charbel refused to lose δ. Built the **Cone–Bures metric** (`cone_bures.py`): the cone construction applied over Bures–Wasserstein rather than ℝᵈ, with mass = the Hebbian weight. Genuine metric (20k triples, zero violation), 5.45 ms/tick, exact day-one degradation, bounded (kills E4 runaway). Then validated: **V1** measured the gap with an exact HK solver — empirical law `HK²≈D²/(1+σ²/δ²)`; the correction it suggests **breaks the triangle inequality** and was rejected. **V4: not novel** (prior art — cite, don't claim). **V1c corrected two of my own errors**: an over-alarmed solver caveat (it was iteration budget, δ=20 → 1.0003 at 60k iters), and reading MOS's regime off ‖U‖_F instead of the spread along the separation direction — the real σ_dir ≈ 0.04, so **σ_dir/δ ≈ 0.09, agreement with true HK under 1% in value and ~87% on the merge decision. δ is recovered and usable.** New owed item V6: measure σ_dir on the real corpus and put σ_dir/δ in telemetry. See §5z.
- **2026-07-29 (main thread, run 3)** — Retracted §5v's FAIL (§5w). Built `belief.py`: sheaf-theoretic uncertainty (Λ = blockdiag(Σ_v⁻¹) + L), **solved blocker 2 (D=1.0) and closed E4's dimensional bug**, `sharpening` as a measured "whole > parts". **E15 answered NO** — WFR/HK has no Bures analogue between Gaussians (citations SEARCHED, one new paper found); **Q2c collapses, merge metric stays Bures**. Built F(M1) vs F(M0); found that **no restriction-map parameterisation is affordable on one tick**, which forces γ₀ ≪ 1 from evidence and gives **Q16 a derived route**. Raised FIX-13. See §5y.
- **2026-07-29 (main thread, run 2)** — Closed FIX-14; reran E5 with 12 contested questions, probe-calibrated |L₂|, questions as the independent unit. **PASS, weakly** (0.41 vs 0.26 null, p ≈ 0.02–0.08, 15% of the planted-cycle level). Caught that the apparent "consistent growth address" is a **b₁=1 artifact** carrying zero bits ⇒ next configuration needs b₁ ≥ 2. Raised FIX-15 (calibration treated as exact). 32 calls; 54 today. See §5x.
- **2026-07-29 (main thread)** — ~~**Ran E5, the gate. It FAILS.**~~ *(retracted — see §5w, §5x)* Built `hodge.py` and `experiment_e5.py`; derived the exact null distributions in closed form and caught that the run sheet's PASS criterion would have passed pure noise; caught that the specified organ contract is symmetric and therefore cannot be a 1-cochain (FIX-12); reformulated E5 as an Abramsky–Brandenburger contextuality test. Two elicitation designs failed informatively before the third worked. **Per §7's own FAIL action: the Φ_∞ rule, the aiming 2×2 and §5p's growth law are NOT to be written up as settled.** See §5v. 16 Groq calls.

---
---

# 7. ~~TOMORROW — THE RUN SHEET~~ ⛔ **SUPERSEDED (written 2026-07-27). GO TO §5al.**

> **⛔ DO NOT PLAN FROM THIS SECTION.** Phase 0 is DONE (E5 ran ×2 → weak PASS §5x; E15 answered
> NO §5y; E3 partially run §5u). Phase 1's questionnaire is CLOSED (§5aa, §5ac, §5ad). Several
> "NEXT — blocking" lines below and in §5s/§5t are **stale and were already superseded when
> written down**, which cost us real time on F10: a stale blocker re-blocks work that was already
> unblocked. **The live plan is §5al (HANDOFF).** This section is kept only as the record of what
> was planned on 2026-07-27, and for the still-valid *procedures* (E5's configuration, E3's
> read/write-set method, the not-valid-tests list), never for its ordering or its status marks.

**Order is deliberate.** Phase 0 first, always: three cheap things that can invalidate the work
of Phases 1–3. Do NOT write theory before Phase 0 returns.

---

## PHASE 0 — THE THREE GATES (do these before anything else)

### ⭐ E5 — THE GATE. Does a measured η have curl or harmonic mass?
> **✅ RUN ×2, 2026-07-29 — VERDICT: PASS, weakly. See §5x.** (§5v's FAIL was retracted in §5w.)
> Everything below is superseded on three counts: the PASS criterion is UNSAFE as written
> (isotropic noise scores 0.400, not 0, and the *fraction* cannot discriminate a planted cycle
> at all — use probe-calibrated |L₂|); the organ contract in step 2 is symmetric and therefore
> not a 1-cochain (FIX-12); and **b₁ = 1 makes the growth ADDRESS uninformative, so the next
> configuration needs b₁ ≥ 2.** Read §5v → §5w → §5x, not this.

**Why first:** the growth law, the aiming 2×2 (§5s), the Φ_∞ stopping rule, and half of Paper B
all assume a measured η is NOT pure gradient. Untested. If it fails, a large part of what we
would write tomorrow is wrong.

**⚠️ TEST DESIGN CORRECTION (caught 2026-07-27).** The originally-specified "one filled triangle"
**cannot detect harmonic mass at all**: a filled triangle has b₁ = 0, so
dim C¹ = 3 = 2 (gradient) + 1 (curl) + **0 (harmonic)**. You would measure curl and learn nothing
about the component that carries the growth address.

**Correct minimal configuration — 4 organs, 5 edges, 1 filled triangle:**

```
  organs:   A, B, C, D
  edges:    AB, BC, CA, CD, DA          (5 edges)
  filled:   triangle {A,B,C}            (1 two-simplex)
  unfilled: cycle A-C-D-A               ← this is where harmonic mass can live

  dim C¹ = 5  =  3 (gradient)  +  1 (curl)  +  1 (harmonic)
  check:  b₁ = E − V + b₀ − F = 5 − 4 + 1 − 1 = 1   ✓ one independent unfilled cycle
```

**Procedure:**
1. Pick one real question the 4 organs can all speak to.
2. **ONE batched LLM call** (mandatory, per A14): return JSON
   `[{u, v, agreement ∈ [−1,1], confidence ∈ [0,1]}, ...]` for the 5 edges. (Q9 contract.)
3. Assemble η ∈ ℝ⁵ from the agreements. Orient edges consistently.
4. Build δ⁰ (5×4) and δ¹ (1×5, the signed sum around ABC).
5. Split: `grad = δ⁰(δ⁰)⁺η` · `curl = (δ¹)ᵀ((δ¹)(δ¹)ᵀ)⁺δ¹η` · `harm = η − grad − curl`.
6. Report `‖grad‖², ‖curl‖², ‖harm‖²` and their fractions of `‖η‖²`.

**PASS:** `‖harm‖² + ‖curl‖²` is a non-trivial fraction of `‖η‖²` on at least some questions.
**FAIL:** η is essentially pure gradient every time ⇒ organs are implicitly consistent, there is
nothing for H¹ to find, and **the entire cohomological growth story needs rethinking.** Say so in
§6 and stop before building on it.

**Cost:** ~1–5 LLM calls. About an hour. Repeat on 3–5 different questions before concluding.

---

### E15 — Does WFR / Hellinger–Kantorovich have a closed form between Gaussians?

**Why:** everything in Q2c is contingent on this. Literature check, ~30 min, no code.
- **YES** ⇒ WFR is available as the merge/distance metric, δ = the concept-identity scale.
- **NO** ⇒ needs an optimisation solve per distance evaluation, is dead on the per-tick path,
  Q2c collapses to theory, and **the merge metric stays plain Bures–Wasserstein.**

Refs to check: Chizat–Peyré–Schmitzer–Vialard (2018); Liero–Mielke–Savaré (2018); and any
"Gaussian Hellinger–Kantorovich" / "unbalanced OT between Gaussians" follow-ups.

---

### E3 — The independence relation on the REAL operator set

**Why:** decides whether the book's entire Part II (Foata, Gröbner, Koszul, Cartier–Foata,
capacity κ, Anick, HH¹/HH²) is mathematics or bookkeeping.

**Procedure:**
1. For each of `SearchOp, ComputeOp, ReasonOp, ContextOp, VerifyOp` (+ RESPOND), read the
   implementation and write down its **read set** and **write set**.
2. **Include the shared state**, which is where this probably dies: `CognitiveState`, the SQLite
   store, the obstruction counter Ω, the mutation history, and the coarse stalks that
   `compute_pi_v` overwrites after execution (§5o).
3. `I = {(i,j) : write(gᵢ) ∩ (read(gⱼ) ∪ write(gⱼ)) = ∅ and symmetrically}`.
4. Count k-cliques `c_k`; form `μ(z) = Σ(−1)^k c_k z^k`; find the least positive root; `κ = 1/r`.

**FAIL:** `I = ∅` (or nearly) ⇒ A is the free algebra, `μ(z) = 1 − rz`, and Part II is counting
DAGs. Record it in §6 and drop those chapters from all papers (Q24 default already says drop).

**Cost:** one afternoon, no LLM calls.

---

## PHASE 1 — ANSWER THE OPEN QUESTIONS + FINALIZE THEORY

Open 🔴: **Q4** (Householder m) · **Q5/Q6** (Forman vs Ollivier; κ signal-only vs live flow) ·
**Q10/Q11** (which pairs judged; batched schema) · **Q16** (γ₀) · **Q19** (what leaves 𝕂) ·
**Q21** (Refuted handling) · **Q25** (θ for the growth trigger — *new, see §5t; recommend a
quantile of observed Φ_∞/‖η‖², same trick as ε and κ_hi/κ_lo*).

All have recommended defaults in `MOS_FINALIZATION.md` §D. "Defaults, except X" is a valid answer.

**Then:** write the **consolidated formal spec** — one document, the thing implementation builds
from and Paper A is drafted from. **It must be written AFTER Phase 0**, so it records what E5/E15/E3
actually returned rather than what we hoped.

**Also in this phase (cheap, independent, do not defer):**
- **FIX-6** — resync the `.tex` with §5q. Highest-priority correctness item; everything inherits it.
- **Point the other chat at §5r–§5t.** It has not seen any of this and may be building against the
  stale `.tex`, the wrong α claim (F12), or without the ‖R‖≤1 hypothesis (F2).

---

## PHASE 2 — IMPLEMENT

**Realistic scope: days, not hours.** Dependency-ordered:

1. Householder restriction maps (6 KB, orthogonal by construction — fixes F2 for free)
2. LSQR/CG Hodge split (never form the pseudo-inverse — 10¹¹ flops vs 10⁷)
3. Augmented Forman curvature `F(e) = 4 − deg u − deg v + 3·#{2-simplices ∋ e}`
4. PPR + sweep-cut instantiation, with CUT WEIGHT reported
5. The 𝕂 / W split as distinct objects; `ι*` instantiate, `ι_!` write-back
6. γ(ν) consolidation rule
7. Coning attachment operator
8. Rank-k SPD stalks + tangent-space (Wasserstein) linearisation

**Free instrumentation to land alongside, all independent of the above:**
**E1** (log α, ρ̃, window) · **E4** (split W₂ terms) · **E7** (record assembly at composition time —
*unrecoverable later, start immediately*) · **Q(t)** (mean ‖R − I‖²_F).

---

## PHASE 4 — TEST AND BENCHMARK

> **⚠️ RENUMBERED 2026-08-01 (§5aq). This was headed "PHASE 3" and collided with the real Phase 3,
> which is COMPOSITION (§5an, §5ap).** It cannot run earlier than composition anyway: **T1 measures
> the gap as a function of accumulated experience**, and there is no accumulated experience until
> the tick consolidates — which it only began doing on 2026-08-01.

Per `BUDGET_AND_TEST_PLAN.md`:
- **Mechanism validation (all free):** E8 (Φ_∞ predicts residual) · E9 (PPR vs k-NN) ·
  E10 (Householder expressiveness) · E11 (curvature distribution) · E12 (curved vs flat) ·
  E13 (consolidation replay) · E14 (δ sweep — *needs ~50 hand-labelled pairs, ~1 hour*)
- **Comparative (~1 week of LLM budget):** B1 error-catching · B2 multi-hop retrieval ·
  B3 retrieval scaling · B4 formal math (miniF2F/ProofNet, needs Lean)
- **T1 — THE MAIN TEST:** three arms, **SAME LLM** (bare | plain-RAG | MOS). Primary measure is
  the **GAP as a function of accumulated experience** — a derivative, not a level.

**⚠️ Not valid tests:** MOS vs a frontier model single-shot · unequal call budgets · Δρ as an
outcome (coherence ≠ correctness) · κ capacity (gameable).

---

## STANDING REMINDERS

- **Log to this file AS decisions land, not at session end.** §5r was written retrospectively and
  nearly lost the FCA reasoning and the Prop-8.2-blocks-growth connection.
- **All ⚠️ citations are from model knowledge and were NOT searched.** Verify before any bibliography.
- **Wall-clock estimates are inferred from flop counts, not measured.** Measure before trusting.
- **Discipline test (A17):** new mathematics earns its place only if it changes a number the engine
  prints, or deletes a decision a human was making by hand.
