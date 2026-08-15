# SPEC — THE GROWTH ADDRESS, AND THE SHEAF DYNAMICS

*Opened 2026-08-08. Supersedes the framework-selection draft in `PRECILLA/draft.md` on the points
listed in §6. This is a **specification**, not a result. Nothing in it has been run.*

Epistemic tags per §5ay: `[MEASURED]` · `[DERIVED]` · `[INFERRED]` · `[ENGINEERING CHOICE]` ·
`[OPEN HYPOTHESIS]` · `[SPECULATION]`.

⚠️ **Citations are from model knowledge and were NOT searched, EXCEPT the three gates searched
2026-08-08 and recorded in §9.** Everything else is named so it can be found, not quoted as
authority.

---

## 0. THE DECISION THIS SESSION MADE

The fork left open by `THE_GENERATIVE_THOUGHT_MODEL.md` — *is the sheaf load-bearing or
decorative?* — is **resolved in favour of load-bearing.** The activation is a 0-cochain on the
complex, the spreading operator is built from the sheaf Laplacian, and `ρ` constrains the dynamics
rather than describing it after the fact.

`PRECILLA/draft.md` answered this by default rather than by decision (it classified the sheaf as
"AUXILIARY — for topological reading", which is the decorative branch). That classification is
retracted.

---

## 1. THE DUALITY — WHAT `J` IS

**[DERIVED]** The coupling matrix is not a primitive object. It is read off from `M = (C, F, s)`:

$$J \;=\; \underbrace{\big(D - L_F\big)}_{\text{symmetric}} \;+\; \underbrace{\eta}_{\text{antisymmetric}}$$

where `L_F = δ*δ` is the sheaf Laplacian, `D` its diagonal, and `η ∈ C¹(C;F)` a 1-cochain.

| structure in `J` | structure in `M` | timescale |
|---|---|---|
| sparsity pattern | 1-skeleton of `C` | very slow (cell attachment) |
| symmetric part | the sheaf `F` (restriction maps) | slow (Hebbian) |
| antisymmetric part | a 1-cochain `η` | slow (TD on succession) |
| the vector acted on | `a ∈ C⁰(C;F)` | every tick |
| the diagonal | **forced by `F`, not free** | — |

**Why the symmetric part is the sheaf Laplacian.** For an edge `e = {u,v}` the sheaf provides
`F(u) → F(e) ← F(v)`. The only canonical way to move activation from `v` to `u` is push-then-pull,
`F_{u⊴e}* F_{v⊴e}` — which is exactly the off-diagonal block of `L_F`, sign-flipped.

**Three consequences.** **[DERIVED]**

1. Stalk dimensions may vary per vertex. `dim F(u) ≠ dim F(v)` is native, not a workaround.
2. Non-flatness (nontrivial holonomy of the restriction maps around cycles) is the signal, not a
   defect: nonzero holonomy ⟺ global sections die ⟺ the harmonic space is nonempty.
3. **The diagonal is determined by the same restriction maps that give the off-diagonal.** The
   leak/self-inhibition term stops being a free parameter. One hand-set decision deleted — A17.

**Gauge.** `J` determines `F` only up to `∏_e O(d_e)`: replacing `F_{v⊴e} ↦ O_e F_{v⊴e}` leaves every
block `F_u* O_e* O_e F_v = F_u* F_v` unchanged. **[DERIVED]**

> Note: `Π_{O(d)}` already appears in the consolidation formula
> `R^𝕂 ← Π_{O(d)}(R^𝕂 + γ(ν)(R^W − R^𝕂))`. **It is a gauge fixing.** Written months earlier for an
> unrelated reason; the convergence is worth recording.

**Symbol correction, load-bearing.** The draft calls the coupling matrix `W`. In MOS `W` is the
**working complex**. Coupling matrix is `J` throughout. Further collisions to fix in any derived
work: `d` (context dim vs base-level decay exponent), `γ` (SR discount vs goal mixing), `ρ`
(context drift vs **the coherence functional**), `φ` (fatigue vs normal pdf).

---

## 2. WHY PERFECT COHERENCE IS DEATH

**[DERIVED]** Set `V(a) = ½⟨a, L_F a⟩ = ½‖δa‖²`. Since `L_F = δ*δ` is self-adjoint and PSD, under
the linear flow `ȧ = −L_F a`:

$$\frac{dV}{dt} = \langle L_F a, -L_F a\rangle = -\|L_F a\|^2 \le 0$$

So `ρ` is a Lyapunov function for the fast subsystem, and `a(t) → P_{H⁰} a(0)` exponentially at rate
`λ₂`, the sheaf spectral gap.

**That limit is fatal, four ways:**

1. The thought stops. `A(t) = A(t+1) = …` forever — assemblies become snapshots again, the exact
   failure `WHY_A_MODEL_OF_COGNITION` §4① forbids.
2. The map cue ↦ final state is a **linear projection**. The generative process has collapsed back
   into a function. That is Stage 1 with extra steps.
3. Generically `H⁰ = 0`, so `a → 0` and the system thinks nothing at all.
4. A fixed point has no transitions, so the lag-CRP is not failed but **undefined**.

**With a drive present, a thought is** `a* = L_F⁺(q − φ)` — the least-incoherent state compatible
with the current drive. A regularised solve, matrix-free via the existing LSQR path. **A thought is
an approximation to a section, never a section.**

**Which variable prevents the collapse.** **[DERIVED]**

| candidate | verdict |
|---|---|
| `σ` (sigmoid) | **no — worsens it.** Under `‖J‖₂ < 4` it is a Banach contraction with a *unique globally attracting* fixed point |
| `λ` (inhibition) | **no.** Rank-one uniform shift; moves the fixed point, does not remove it |
| `x_t` (input) | **disqualified.** The architecture must run with `x_t = ∅`; tracking is not thinking |
| `c` (context) | **no.** Driven by `A(t)`; if `A` is constant then `c → β_c f(A)/(1−ρ)` and freezes |
| **`φ` (fatigue)** | **the only candidate** |

This upgrades the ablation prediction from a guess to a theorem: **with `φ = 0` the linear flow
provably converges to `P_{H⁰}a(0)` and freezes.**

**Honest limit.** **[DERIVED]** Linearising the coupled fast/slow pair on an `L_F`-eigenmode with
eigenvalue `μ` gives the matrix `[[−μ, −1], [1, −(1−κ)]]`: trace `< 0`, determinant `> 0`. Both
eigenvalues have negative real part. **Linear fatigue yields a stable spiral — damped oscillation,
not a limit cycle.** The system rings, then still dies.

Sustained motion needs one of three, and they are not equally optional:

- **slow learning of `J`** — already present (Hebbian), keeps deforming the landscape. Not a choice.
- **noise** — forced empirically, not logically (see §4). Add it.
- **a nonlinear limit cycle** (winnerless competition / heteroclinic sequences, Rabinovich et al.) —
  **[OPEN HYPOTHESIS]**. This is a finding to *look for*, never to design in; designing it in is the
  §2 circularity trap.

---

## 3. SPEC A — THE GROWTH-ADDRESS MEASUREMENT

**No simulator. Runs on data that exists. Cost: seconds.**

### 3.1 The question, in plain terms

Given one-way arrows between concepts (`i` cites `j`), ask: *is there a single ranking of concepts
that explains every arrow?* Split the answer into three parts that sum to 100%.

| part | plain meaning |
|---|---|
| **ranking** | explained by one global ordering |
| **local tangles** | loops around groups the complex already treats as a unit |
| **holes** | loops nothing explains — **the growth addresses** |

### 3.2 Why this is not circular — the Prop 8.2 escape

**[DERIVED]** Prop 8.2 blocked growth because the engine's only 1-cochain was `δx` for a global
state `x`, so `[δx] = 0` in `H¹` identically. Here `η` is built from **observed succession**, not
differentiated from any global state. It is not the coboundary of anything, so its harmonic
component may be nonzero.

**[OPEN HYPOTHESIS]** that it actually is. This spec exists to decide that.

### 3.3 Objects

- `C⁰ = ℝ^V` — functions on concepts
- `C¹` — antisymmetric functions on edges, `η(i,j) = −η(j,i)`
- `C²` — alternating functions on filled triangles

$$(\delta_0\psi)(i,j) = \psi(j) - \psi(i), \qquad (\delta_1\eta)(i,j,k) = \eta(i,j)+\eta(j,k)+\eta(k,i)$$

`δ₁δ₀ = 0` by telescoping. Hodge: `C¹ = im δ₀ ⊕ ker Δ₁ ⊕ im δ₁*`, an **orthogonal** decomposition.

### 3.4 Inputs

- Citation pairs from `extract_refs.py` (~2266 author-asserted dependencies) **[MEASURED]**
- Vertices = concepts, `N ≈ 1074`

### 3.5 Construction

1. **Undirected graph.** Edge `{i,j}` whenever a citation runs either way.
2. **The flow.** `η(i→j) = #(i cites j) − #(j cites i)`. Antisymmetric by construction.
3. **Triangles: CLIQUE COMPLEX.** `[ENGINEERING CHOICE, pre-registered 2026-08-08]` Fill every
   triangle all three of whose edges exist. This is the **conservative** setting: it maximises the
   local-tangle space and therefore *minimises* the holes. If holes survive here, the result is
   strong.

   ⚠️ **This is NOT the rule `ConceptStore` uses, and the difference is deliberate.** The store
   fills a 2-simplex exactly when its three concepts **co-fired in one assembly** — the edge rule one
   dimension up, justified by the nerve lemma with hypotheses verified rather than assumed
   (`concept_store.hpp`, logbook §5as). That rule is unavailable here because the citation graph has
   no assemblies. The clique complex is the closest conservative substitute. **Two graphs, two rules,
   stated rather than silently reconciled.**

   ⚠️ **When Spec A is later pointed at the co-activation graph instead**, read
   `skipped_wide_assemblies()` FIRST. A capped assembly keeps its edges but not its 2-cells, so its
   `(n−1)(n−2)/2` within-assembly cycles survive as harmonic mass **that looks exactly like a
   structural hole**. Nonzero count ⇒ `b₁` is contaminated by precisely the artifact the triangle
   rule exists to remove.
4. **Best ranking.** `ψ* = argmin ‖η − δ₀ψ‖²` via LSQR. Gradient part `= δ₀ψ*`.
5. **Residual.** `r = η − δ₀ψ*`, orthogonal to `im δ₀` by least squares.
6. **Curl.** `Φ* = argmin ‖r − δ₁*Φ‖²` via LSQR. Curl part `= δ₁*Φ*`.
7. **Harmonic.** `harm = r − δ₁*Φ*`.

### 3.6 Reported quantities

- the three energies as fractions of `‖η‖²`
- `b₁ = |E| − (|V| − c) − rank δ₁` — the number of independent holes
- `ψ*` — a global prerequisite-depth ranking of every concept **(useful regardless of outcome)**
- the specific concept cycles carrying the largest harmonic mass

**Built-in self-test:** orthogonality forces `‖η‖² = ‖grad‖² + ‖curl‖² + ‖harm‖²`. Assert to
tolerance; failure means the solver did not converge.

### 3.7 Controls — mandatory, ALL at one shared setting

Per the standing rule: an instrument that does not clear every control at a *single* parameter
setting is not used.

| # | control | required result | catches |
|---|---|---|---|
| 1 | directed path / tree | holes = 0 (`< 1e-8`) | a broken decomposition |
| 2 | directed 4-cycle, no triangles | holes = 100% (`> 0.999`) | insensitivity |
| 3 | directed triangle, filled | curl = 100%, holes = 0 | **curl/harmonic leakage — the crucial one** |
| 4 | planted gradient `η = δ₀ψ` on the real graph, random `ψ` | ranking = 100%, holes = 0 | leakage between parts |
| 5 | direction-randomised null, 1000 draws | null distribution of holes% | **makes the headline number readable** |

Control 5 is the analogue of `curveball` and is not optional. Without it "18% holes" means nothing.

### 3.8 Outcomes and what each forces

| result | meaning | next |
|---|---|---|
| ranking dominates, holes ≈ null | citations are a clean prerequisite hierarchy | **the growth story needs a different data source.** §3.2's hypothesis is dead — record it and move |
| holes above null, few | a handful of real addresses | inspect by hand; each names specific concepts |
| holes well above null, many | growth has material to work with | connects Attempt 4's transitivity deficit to a mechanism (§6) |

### 3.9 Cost

`|V| ≈ 1074`, `|E| ≈ 2266`. `δ₀` is sparse with 2 nonzeros/row, `δ₁` with 3. LSQR is already
implemented matrix-free. **Seconds, not minutes.** 1000 null draws remain trivial.

---

## 4. SPEC B — THE DYNAMICS

### 4.1 One tick

$$\begin{aligned}
\text{cue:}\quad & q_t = \alpha x_t + \beta\,Vc_{t-1} + \gamma_g\,Vg_t \\
\text{drive:}\quad & h = J a + q_t + B - \lambda\textstyle\sum_i a_i - \varphi_{t-1} + \varepsilon_t,
\qquad \varepsilon_t \sim \mathcal N(0,\tau^2 I) \\
\text{settle:}\quad & a \leftarrow \sigma(h)\ \text{ iterated to fixed point} \\
\text{read:}\quad & A(t) = \{i : a_i > \theta\} \\
\text{update:}\quad & \varphi,\ c,\ \mathrm{WM},\ B
\end{aligned}$$

`V ∈ ℝ^{N×384}` is the matrix of concept vectors, so `(Vc)_i = ⟨v_i, c⟩`.

> **Type correction.** The draft writes `q_t = αx_t + βc_{t−1} + γ_g g_t` and adds the result to
> `Ja ∈ ℝ^N`. But `c ∈ ℝ^d`. **An `ℝ^d` vector cannot be added to an `ℝ^N` one.** The `V` is
> required, and it forces `d = 384` (the embedding dimension) — not the `d ≈ 100`
> `[ENGINEERING CHOICE]` the draft claims.

### 4.2 Decisions

| decision | choice | why |
|---|---|---|
| noise | additive Gaussian, pre-sigmoid, size `τ` | **forced empirically, not logically:** the same list recalled twice gives different orders, and a deterministic model predicts zero of that variability. A CRP could in principle come from across-list variation alone — so this is an empirical necessity, not a theorem |
| dials | `τ` (and optionally `λ`) from the precision estimate | RESOLVE = low `τ`, EXPLORE = high `τ`. Not human-set |
| freezing | dials set once per run, never mid-run | closes the tuning loophole |
| inner iterations | run to convergence, not a fixed count | `‖J − λ11ᵀ‖₂ < 4` makes the map a Banach contraction (`σ` is `¼`-Lipschitz) with a unique fixed point, so `K` stops being a parameter **[DERIVED]** |
| diagonal / leak | determined by `F` | one knob deleted (§1) |
| symbols | `J`, never `W` | §1 |

**Consequence:** with noise the tick is a Markov kernel `𝒮 → 𝒫(𝒮)`, not a map. The draft's §2
declared a measure without a kernel for it to belong to; this fixes that inconsistency.

### 4.3 What gets logged every tick

Stage 1 discarded all of this. It is the actual product.

- `A(t)` — the full assembly **trajectory**
- `ρ(t)` — **predicted to be a sawtooth**: falls as the thought coheres, jumps when fatigue ejects
  it. If it decays monotonically to a floor, the model is dead and one plot shows it. **[DERIVED
  from §2]**
- `|A(t)|` — should stabilise without being set
- successive pairs `(A(t), A(t+1))` — these feed `η`, which feeds Spec A

### 4.4 Gates

- **G0** — plant a known structure; the simulator must recover it. If it cannot recover what it was
  handed, nothing later is interpretable.
- **G1** — lag-CRP with forward asymmetry **and** serial position. Both.

**On the lag-CRP's evidential value.** `[CORRECTION to PRECILLA/draft.md §7.8]` The draft installs
an upper-triangular successor matrix and then derives forward asymmetry from it. **The asymmetry was
inserted, not predicted.** The test regains force only if:

1. `γ` and `ρ` are learned from the input stream and never fitted to the CRP;
2. the **magnitude** matches (human forward/backward ≈ 1.5–2× at lag 1; a model giving 50× has
   failed even with the right sign);
3. long-range and across-list contiguity are reproduced — which an upper-triangular `M₃` does
   **not** install.

Replace "asymmetry ratio > 1" with those three as the G1 criterion.

### 4.5 The three open items — RESOLVED 2026-08-08

**① Primacy — resolved by literature, at zero cost in state.** `[DERIVED from searched prior art,
§9.1]`

The mechanism is **start-list context reinstatement**, not a rehearsal buffer and not a learning-rate
gradient. The CMR literature has already compared these: models with start-list context reinstatement
fit the primacy effect better than models with the learning-rate gradient alone.

At retrieval, mix the start-of-list context back into the cue:

$$c^{\text{cue}} = (1-\omega)\,c_t + \omega\,c_0$$

**This adds no new state variable** — `c` already exists, and `c_0` is a stored copy. One parameter
`ω`. Early-list items are cued by a context they are uniquely close to, which lifts them.

> The earlier claim that this "blocks G1 and needs a decision on paper" was correct that a mechanism
> was missing and wrong that it needed inventing. **One search, not a design session.** This is rule 9
> working.

**② The noise map — derived, and it deletes knobs rather than adding one.** `[DERIVED]`

Precision *is* inverse variance, by definition. Sampling from a belief with variance `σ²` means
adding noise of that variance:

$$\tau^2 = \frac{1}{\pi_e}$$

`π_e` already exists in the engine, and commit `2f6d64b` ("*Derive pi_e in the engine; stop reading a
Hebbian count as an inverse variance*") already established it as a genuine inverse variance rather
than a score. **Nothing to invent.** `[CONFIRMED against prior art, §9.3]` — this is precisely how
active inference does it: precision is the inverse temperature in the softmax and controls the
stochasticity of selection.

**And the gain is not independent of it.** A threshold unit with additive Gaussian noise is the same
object as a smooth sigmoid unit:

$$P(h + \varepsilon > \theta) = \Phi\!\big((h-\theta)/\tau\big)$$

So fixing `τ` from `π_e` also fixes the sigmoid gain, which was a **hidden hand-set constant** sitting
inside the bare symbol `σ` in the draft.

⚠️ **The approximation, stated:** this identity is *exact* for a **probit** and only approximate for
the **logistic** — they differ by a scale factor of ≈1.6. **Use probit and it is exact.** If logistic
is used for any reason, carry the 1.6 explicitly and never silently.

> Revised ledger for §4.2: **three knobs deleted (`k`, the leak, the gain), zero added.** The earlier
> "two deleted, one added" was wrong in our favour and is retracted.

**③ The input stream — decided. Three streams, because the gates need different things.**
`[ENGINEERING CHOICE]`

| gate | stream | why |
|---|---|---|
| **G0** | synthetic sequences over planted structures | must be able to check the simulator recovers what it was handed |
| **G1** | standard word lists; categorised lists for clustering | non-negotiable — the human data is *defined* on this paradigm |
| **G4** | `\ref` dependency chains | externally authored, real, 2266 of them, carrying structure someone else decided |

**Rejected:** random walks on the concept graph (input generated from the object under study —
circular by construction); paper-reading order (the sequence carries no authored structure).

⚠️ **The circularity this creates, and the two guards that are mandatory.** Spec A measures the
harmonic content of the citation graph. If the simulator is then *driven* by citation chains and we
read topology off its output, the topology found is the citation graph's, laundered through a
simulator. **That is Attempt 1's failure at a third scale.**

1. **Disjoint split.** The subset used for Spec A is never used as G4 input.
2. **The shuffle comparison is the experiment, not a control.** Run the same corpus twice — citation
   order and shuffled order — and report what *differs*. **What survives shuffling is the dynamics;
   what does not is the input's structure.** Same logic as commitment 5 of
   `WHY_A_MODEL_OF_COGNITION` (shuffled embedding), applied to the stream instead of the geometry.

### 4.6 Cost

`Ja` ≈ 1.2 M flops, Hebbian update ≈ 1.2 M ⇒ **2–3 ms/tick** in numpy ⇒ 10⁶ ticks in under an hour.
Checkpoint every N ticks; resumable by construction. `jobs = 2`, never 4.

---

## 5. IDENTIFIABILITY — RUN THIS BEFORE ANYTHING IS LEARNED

**[DERIVED]** The five-term edge model `J = Σ w_k M_k` learns the `w_k` by projecting a gradient onto
each `M_k`. The `M_k` are **not orthogonal**: `M₄` (PMI) is computed from co-activation, which is
driven by `M₁` (semantic), and `M₂` (Hebbian) tracks `M₄` almost by definition.

If `⟨M₁, M₄⟩` is large, `w₁` and `w₄` trade off freely and **`w₁` is not identifiable** — which
destroys the draft's §7.1 defence that the formalism makes circularity visible by letting you read
off `w₁`.

**Required, and it costs nothing:** report the `5×5` Gram matrix `G_{kl} = ⟨M_k, M_l⟩_F` and its
condition number **before** learning anything. If ill-conditioned, orthogonalise (residualise `M₄`
against `M₁`) so the weights mean something.

---

## 6. WHAT THIS AMENDS FROM TIER 0

| Tier-0 hole | amendment |
|---|---|
| **1. top-k ball ⇒ single-cause by construction** | the assembly is a superlevel set of a 0-cochain under (driven, noisy) sheaf heat flow. Not a ball, not centred anywhere |
| **2. logical vs geometric relations disagree (47%)** **[MEASURED]** | structurally separated: geometric → the sheaf (symmetric); logical/dependency → `η` (antisymmetric). Different pieces of one decomposition, not competing entries in one matrix |
| **3. co-activation graph carries non-geometric structure** **[MEASURED]** | that structure now has a name: `η`'s harmonic and curl parts |
| **4. generative null inverted p from 0.02 to 0.45** **[MEASURED]** | the generative process is the model, explicit and controllable |
| **5. Prop 8.2 — growth has no address** | `η` is not `δ` of anything; its harmonic part is the address (§3.2) |

**[SPECULATION]** — the connection worth checking. Attempt 4's unexplained transitivity deficit means
fewer filled triangles than any null predicts. Fewer triangles ⇒ smaller `rank δ₁` ⇒ **larger
harmonic space**. Stage 1's one unexplained positive finding is precisely the condition under which
the growth law has the most room to fire. Spec A tests this directly: `b₁` is reported.

---

## 7. ORDER OF WORK

1. Gram matrix of the five `M_k` (§5). Costs nothing, can invalidate §7.1 of the draft immediately.
2. Spec A controls 1–4. **If any fails, stop** — the instrument is broken and no result from it
   counts.
3. Spec A control 5 (null distribution), then Spec A on the real citation graph.
4. ~~Resolve Spec B's primacy question~~ — **done 2026-08-08 by literature, §4.5.①.**
5. Only then, G0.

**Nothing in §4 is built until §3 has returned an answer.**

---

## 8. WHAT IS STILL UNRESOLVED

- **[OPEN]** Whether the sigmoid's nonlinearity supports a sustained limit cycle, or whether noise
  and slow learning are the only sources of ongoing motion (§2).
- **[OPEN]** Whether the cover/partition question is well-posed in this language. "Do the supports of
  a basis of `H⁰` overlap?" is basis-dependent and therefore not well-posed. Krull–Schmidt makes the
  indecomposable decomposition canonical (cellular sheaves on a finite complex are modules over a
  finite-dimensional algebra), so *partition ⟺ the indecomposable summands have disjoint supports* is
  rigorous — but computing it is potentially wild-quiver-hard, and the practical proxy
  (small-eigenvalue eigenvectors of `L_F`) reintroduces the basis problem. **Real gap.**
- **[UNVERIFIED]** Whether every symmetric matrix is realisable as `D − L_F` for some sheaf. There is
  freedom at rank 1; higher-rank stalks unchecked.
- ~~The input stream~~ — **resolved, §4.5.③.**
- ~~Directed cohomology via the Alexandrov topology~~ — **superseded, §9.2.** The Alexandrov
  proposal in `PRECILLA/draft.md` §7.5 is retracted: sheaves on a preorder are constant on each
  strongly connected component, and a dense recurrent `J` is one giant SCC, so its cohomology is
  trivial by construction. **Use path homology (GLMY) instead.**

---

## 9. LITERATURE GATE PROTOCOL, AND THE 2026-08-08 RECORD

**Adopted 2026-08-08.** Rule 9 of `THE_GENERATIVE_THOUGHT_MODEL.md` §10 ("prior art before
implementation") was written down and then under-applied — tagging a claim ⚠️ *unsearched* flags the
risk without discharging it. Operational form, budget-shaped:

| step | rule |
|---|---|
| when | at each gate, **before** building |
| scope | one specific question, not a survey |
| budget | 2–4 searches per gate, batched into one round |
| stop | either a standard answer exists (use and cite it) or none does (proceed, and record that) |
| record | logbook entry with date, query, and verdict |

### 9.1 Primacy — **standard answer exists, adopted**

Start-list context reinstatement fits primacy better than a learning-rate gradient alone; sCMR (the
serial variant) additionally accounts for dissociations between serial-position curves and temporal
clustering. Adopted in §4.5.①. Costs one parameter and no new state.

- <https://collaborate.princeton.edu/en/publications/a-context-maintenance-and-retrieval-model-of-organizational-proce/>
- <https://d-nb.info/135447953X/34>
- <https://pmc.ncbi.nlm.nih.gov/articles/PMC5358688/>

### 9.2 Directed cohomology — **standard answer exists, replaces our proposal**

**GLMY path homology** (Grigor'yan–Lin–Muranov–Yau, arXiv:1207.2834) is the developed theory for
digraph topology: homotopy invariance, Eilenberg–Steenrod analogues, Künneth for box product and
join. Persistent versions exist (arXiv:1701.00565), and — the operationally decisive fact — **there
is an efficient algorithm for 1-dimensional persistent path homology** (SoCG 2020), which is exactly
the dimension the growth address lives in. Reachability homology (IMRN 2025) addresses the
reachability question directly.

**[DERIVED]** This is what §7.5 of the draft should have proposed. Our Alexandrov construction is
not merely weaker — it is degenerate on the graphs we actually have.

- <https://arxiv.org/abs/1207.2834>
- <https://arxiv.org/abs/1701.00565>
- <https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.SoCG.2020.36>
- <https://academic.oup.com/imrn/article/2025/3/rnae280/7978245>

### 9.3 Precision → noise — **our derivation matches the field; claim no novelty**

In predictive coding, precision is by definition the inverse variance. In active inference the
precision of beliefs about policies is the **inverse temperature in the softmax** and controls
selection stochasticity; high values recover winner-take-all. `τ² = 1/π_e` is therefore the standard
construction, not an invention — borrow it and cite it.

- <https://www.sciencedirect.com/science/article/pii/S0022249620300857>
- <https://activeinference.github.io/papers/process_theory.pdf>
- <https://arxiv.org/pdf/1909.10863>

### 9.5 Concept formation — the growth law needs a cost side `[SEARCHED 2026-08-08]`

The address says *where*. It does not say *whether*. Coning a cycle of length `k` **costs** one
vertex + `k` edges + `k` triangles + a stalk, and **buys** `b₁ − 1`.

**Our growth law has no cost side.** Applied literally it fills every hole — and
`concept_store.hpp` already warns that `b₁` gets swamped by clique artifacts. A criterion with no
cost over-generates concepts.

The literature is unanimous and uses a criterion we do not: **compression (MDL)**.

- **DreamCoder** — wake phase solves tasks with the current library; **sleep phase extracts common
  sub-expressions and adds them as new primitives if they reduce total description length.** Note
  MOS already has a sleep phase (`KnowledgeCurator`), arrived at independently.
- **Predicate invention** (ILP) — invent a new predicate when the vocabulary cannot express the
  theory. The field's verdict: *"without predicate invention, learning always will be shallow."*
- **Chunking as compression** — a chunk is *"a unit in a maximally compressed code"*, formalised
  via MDL.

**Proposed law, strictly better than the current one:**

> **Attach a concept over a cycle that RECURS, and only when the recurrence pays for the
> attachment.**

This is DreamCoder's rule — it extracts *common* sub-expressions, not any sub-expression. It also
answers a question we had not asked (which of several holes to fill first) and **deletes that
decision rather than handing it to a human. A17.**

**[OPEN HYPOTHESIS]** whether obstruction-killing *is* MDL compression. Plausible — fewer independent
cycles means a shorter description — but unproven, and the cost side above suggests they come apart.

**On evolution/mutation:** rejected as a mechanism. Variation-and-selection needs randomness
*because it has no address*; MOS computes one. The inheritable content of a concept is its **stalk**
plus its **attachment**, and the operators are `bind`/`collapse`/`cone`, already in `𝔇` — directed
surgery, not random mutation.

- <https://royalsocietypublishing.org/rsta/article/381/2251/20220050/112456/DreamCoder-growing-generalizable-interpretable>
- <https://arxiv.org/pdf/2008.07912>
- <https://www.sciencedirect.com/science/article/abs/pii/S0010027716301470>

### 9.4 Score

Three searches, three gates, **three changes to the spec** — one mechanism adopted, one construction
retracted, one derivation confirmed as standard. Cost: minutes. The Alexandrov retraction alone would
have been weeks of building a degenerate object.
