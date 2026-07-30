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

**NEXT — blocking, and it is a modelling decision, not a computation: CHOOSE THE
CATEGORY** (audit F10). Both candidates the book offers fail: in Hol(𝒟) every Gaussian
concept is a *simple* module (k[x] is simple over the Weyl algebra in char 0), so
JH(M)={[M]}, length 1, and the K₀ class says no more than "which memory is this"; in
Rep(Q) the K₀ class *is* the dimension vector, which collides catastrophically as a
retrieval index. §29–32 of the book argue in one category, §33–37 in the other, §47 in
neither. Jordan–Hölder guarantees canonicity **given** the category; it cannot pick the
atoms. Discuss before any more memory-schema work.

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
growth. This unblocks 𝕂/W implementation (Phase 2 item 5), which had been waiting on a category
it turns out not to need. Filed as a dead end in §6.

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

### ⚠️ THE GAP THE DERIVATION EXPOSED — MOS has no 2-cochain inner product.
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

# 7. TOMORROW — THE RUN SHEET (written 2026-07-27 for 2026-07-28)

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

## PHASE 3 — TEST AND BENCHMARK

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
