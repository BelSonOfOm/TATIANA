# TATIANA V1 — IDENTITY MAP

*Opened 2026-08-13. Branch `fix-11-13-and-curvature-decisions`, on top of logbook §5bb.*

**What this is.** A *semantic* identity map: what TATIANA is, what it must never
become, and which laws are allowed to change it. "Identity" here means the sense in
which a thing remains itself — not the mathematical `id` morphism. Where the
distinction matters the document says **invariant** for the mathematical object and
**identity** for the design commitment.

**What this is not.** Not a result. Nothing below has been run except the Spec A
controls in §9, which are reported with their outcome.

Epistemic tags per §5ay: `[MEASURED]` · `[DERIVED]` · `[INFERRED]` ·
`[ENGINEERING CHOICE]` · `[OPEN HYPOTHESIS]` · `[SPECULATION]`

**Supersedes.** §7's Track A / Track B split. Track A (LLM router, three-arm T1) is
retired. TATIANA is Track B and nothing else.

---

## 1. THE ONE-SENTENCE COMMITMENT

> **TATIANA is a cellular sheaf on a stratified 2-complex whose section relaxes,
> whose restriction maps mold, and whose complex grows and prunes — under a
> two-phase law that conserves a stated invariant exactly while awake and
> projectively while offline.**

Read the clauses as constraints, not description. Each one forbids something.

| clause | forbids |
|---|---|
| cellular sheaf on a **2-complex** | dropping to a graph (§4.3) |
| section **relaxes** | treating `s` as stored data rather than a dynamical variable |
| restriction maps **mold** | freezing `F`, which makes the sheaf decorative |
| complex **grows and prunes** | growth-only architectures that inflate without bound |
| **two-phase** | trading all costs against each other on every tick |
| **stated invariant** | "identity" as a vibe rather than a number that can be printed |

---

## 2. WHAT TATIANA IS NOT

Recorded because each was a live position in this repo at some point.

1. **Not an LLM wrapper.** No router, no retrieval-augmented arm, no "memory layer
   for a chat model." An LLM may appear later as an *encoder* producing `o_t`, or as
   the `𝓛` lift in verification. It is never the thing that reasons.
2. **Not a knowledge graph.** A knowledge graph has no dynamics and no obstruction
   theory. If a proposed feature would work identically on a labelled graph, it does
   not belong in TATIANA.
3. **Not a cognitive-science model.** TATIANA borrows *mechanisms* from
   neuroscience as design constraints. It makes no claim to explain brains and must
   not be evaluated against neural data.
4. **Not the Free Energy Principle.** `[Retained from the 2026-08 note, §14]` The
   two-phase objective in §6 contains structural and stability terms that are our
   construction. Calling it free energy imports authority we have not earned. Call it
   the **maintenance cost** and nothing else.
5. **Not a system that must be conscious, agentic, or "alive."** Reproduction in §5
   is a morphism. No further reading is claimed.

---

## 3. THE INVARIANT — WHAT SURVIVES

Identity is carried by the **crystallized store `𝕂`**, not by the working complex
`W`. `W` is allowed to be destroyed at the end of every session. This is the whole
point of `MEMORY_MODEL_TWO_COMPLEX.md` and it is now promoted from an architectural
convenience to the definition of identity.

### 3.1 Level 0 — the exact invariant `[DERIVED]`

$$\mathrm{K}(\mathbb{K}) \;=\; \big(\dim \mathcal{F}_\mathbb{K}(\sigma)\big)_{\sigma \in \mathcal{C}_\mathbb{K}}$$

the dimension vector — a `K₀` class. Under the consolidation rule

$$R^\mathbb{K} \leftarrow \Pi_{O(d)}\big(R^\mathbb{K} + \gamma(\nu)(R^W - R^\mathbb{K})\big)$$

`K(𝕂)` is **exactly conserved**. `Π_{O(d)}` cannot change a dimension; molding
cannot change a dimension; state relaxation cannot change a dimension.

It changes only under growth, and then by a **derived** amount: Construction 6 sets
`F(w) := lim D_γ`, so `dim F(w) = dim H⁰(γ; F|_γ)`. Nothing is hand-set.

> **This is the theorem shape V1 is built to have:** two of three timescales
> conserve the invariant exactly; the third changes it computably.

### 3.2 Level 1 — the projective invariant `[INFERRED from SHY, §7.2]`

`K(𝕂)` is coarse. It cannot distinguish two stores with the same dimensions and
different maps. The finer statement is that **relative structure is preserved while
absolute magnitude is not**:

$$\mathcal{F}_\mathbb{K} \;\sim\; \lambda \mathcal{F}_\mathbb{K}, \qquad \lambda > 0.$$

`Π_{O(d)}` already implements exactly this — it is the polar retraction `R ↦ UVᵀ`,
which discards scale and keeps direction. **Written months ago as a gauge fixing;
it is also the identity-preservation mechanism, and that coincidence is the reason
to trust it.** `[INFERRED]`

### 3.3 Level 2 — explicitly out of scope `[DERIVED]`

The full isomorphism class of `𝓕_𝕂`. A cellular sheaf on a graph is a
representation of the incidence quiver, whose underlying graph is the subdivision of
the 1-skeleton. Anything richer than a single cycle is of wild representation type.
Krull–Schmidt guarantees the decomposition into indecomposables is *unique*; it does
not make it *computable*.

**Do not chase the full iso class.** V1 reports levels 0 and 1.

---

## 4. THE TWO-PHASE LAW

The central structural commitment. TATIANA does not minimise a six-term functional
on every tick. It alternates.

| | **WAKE** | **SLEEP** |
|---|---|---|
| drive | `q_t ≠ 0` | `q_t = 0` |
| what moves | `s` (fast), `F` (slow), `C` grows | `F` renormalizes, `C` prunes |
| objective | discharge discord | pay down maintenance cost |
| invariant `K(𝕂)` | conserved exactly | may decrease (pruning) |
| relative structure | changes | **preserved** |

`[INFERRED]` Both phases are forced, not chosen. §5bb disqualified `x_t` as the
anti-collapse mechanism on the grounds that *the model must run with empty input* —
that argument already establishes an offline phase; this document names it.

### 4.1 Wake — the Hodge routing law `[DERIVED]`

On the 2-complex, `C¹ = im δ⁰ ⊕ H¹ ⊕ im (δ¹)*`, orthogonally. The discord `δs`
decomposes, and **each summand can be discharged by exactly one layer**:

| component | removable by changing `s`? | handled by | timescale |
|---|---|---|---|
| `im δ⁰` | yes | `ṡ = −L_F s + drive` | every tick |
| `H¹` (harmonic) | **no** — this is holonomy of `F` around a cycle | mold `F`, or grow | slow |
| `im (δ¹)*` | no | flags a bad 2-cell | slow |

The fast flow provably drives the `im δ⁰` part to zero (`L_F` is PSD; §5bb's Lyapunov
argument). **What survives is by definition harmonic.** `harmonic_support` is already
implemented in `Complex2` / `HodgeSplit`.

**The handoff is a stall condition, not a threshold.** `[DERIVED]` When the
constrained descent has converged and `ρ > 0`, it is *proven* that no further motion
at that level helps. That is the growth trigger. It is derived from the geometry, not
declared.

`[ENGINEERING CHOICE]` The numerical tolerance on "converged" is a free parameter.
State it; do not hide it inside a λ.

### 4.2 Sleep — renormalization and down-selection `[INFERRED from SHY]`

With `q_t = 0` the network runs on its own dynamics. Two things happen:

1. **Renormalize.** Apply `Π_{O(d)}` globally. Scale drops, relative structure
   survives (§3.2).
2. **Down-select.** Consult the MDL cost of `DERIVATION_MDL_GROWTH_LAW.md` and prune
   structure that does not pay for itself. Weak cells go; the strongest are left
   unscaled.

**This is where energy lives, and it lives nowhere else.** One term, one phase.
Growth (wake) adds; pruning (sleep) removes; they never bid against each other
inside a single tick. That is the whole answer to the six-λ objection.

### 4.3 Why the 2-cells are load-bearing `[MEASURED 2026-08-08]`

On a **graph**, `δ¹δ⁰ = 0` is vacuous — every assignment of stalks and maps is a
sheaf, molding is unconstrained, and nothing intrinsic can ever stall. On a
**2-complex** it is a real algebraic condition: an arbitrary `F(w)` gives
`|δ¹δ⁰|_max = 1.756`; the limit gives `4.4e-16`.

So the triangles are what make molding *obstructible*, hence what makes growth
*derivable*. This is TATIANA's defence against the negative results in §11 —
those concern graphs.

---

## 5. GROWTH, MOLDING, REPRODUCTION — ONE NETWORK

They are not three mechanisms. They are one descent, at three levels of the
structure, each handing off when it stalls.

```
        input  o_t
          │
          ▼
   ṡ = −L_F s + drive          ← discharges im δ⁰            (every tick)
          │
      residual harmonic?
          │ yes
          ▼
   mold F within the sheaf variety   ← δ¹δ⁰ = 0 constrains it  (slow)
          │
      still stalled?
          │ yes
          ▼
   grow: cone the cycle carrying the harmonic mass            (rare)
          │  dim F(w) = dim H⁰(γ; F|_γ)     ← Construction 6
          ▼
   ═══════ SLEEP ═══════
   renormalize (Π_{O(d)}) · down-select by MDL cost
```

**Reproduction** is a morphism, not a copy. `[SPECULATION]` The natural candidate is
the adjoint pair already in the repo: `ι* ` instantiates a subcomplex, `ι_!` writes
back only what was touched, and `ι*ι_! ≅ id` guarantees the round trip does not
corrupt the fragment. A "reproduced" TATIANA is a downward-closed subcomplex plus
its pullback sheaf, carrying a sub-invariant of `K(𝕂)`. **This is the weakest part
of the document.** No claim is made that the offspring is viable, only that the
morphism is canonical.

---

## 6. THE MAINTENANCE COST

One functional, consulted only during sleep.

$$\mathcal{U}(\mathbb{K}) \;=\; L(\text{structure}) \;+\; L(\text{observations} \mid \text{structure})$$

`[DERIVED — from DERIVATION_MDL_GROWTH_LAW.md]` The description-length form is
already derived in the repo. Nothing new is introduced here except its *placement*.

`[ENGINEERING CHOICE — the one real free parameter]` The exchange rate between "cost
of a deformation" and "cost of a new cell." MDL needs both in the same units.
**State it in the open. If it acquires siblings, the design has regressed.**

Neuroscientific warrant, for the record and not as authority: SHY holds that stronger
synapses cost more energy and saturate learning, creating the need for
renormalization — "sleep is the price we pay for plasticity" (Tononi & Cirelli 2003,
2014). It is contested; see §11.

---

## 7. WHAT IS BORROWED FROM NEUROSCIENCE, AND WHAT IS NOT

### 7.1 Borrowed

| mechanism | source | TATIANA's form | status |
|---|---|---|---|
| Complementary Learning Systems | McClelland, McNaughton & O'Reilly 1995; Kumaran et al. 2016 | `𝕂`/`W` split, `γ₀ ≪ 1` | **built** |
| Truth-gated consolidation | project's own | `γ(Refuted) = 0` | **built** |
| Synaptic homeostasis (SHY) | Tononi & Cirelli 2003, 2014 | sleep phase: `Π_{O(d)}` + MDL prune | **specified, not built** |
| Offline reactivation | SWR replay literature | tick with `q_t = 0` | **specified, not built** |
| Memory allocation / tagging | Silva et al., *Nat Rev Neurosci* 15:157 (2014); Frey & Morris 1997 | harmonic support names the site | **instrument built (§9)** |
| Co- vs dis-allocation | Josselyn & Frankland; Rashid et al. 2016 | cone the cycle vs separate it | **OPEN — §10** |

### 7.2 The one that does real work

<u>Renormalization preserves relative strength while discarding magnitude.</u> Weak
connections are eliminated; the relative strength of the survivors is preserved. That
sentence is the neuroscientific statement of §3.2, and it is why identity survives
mutation at all. Consolidation explains how memory *stabilises*; renormalization
explains how it *stays itself while changing*. The first document in this series had
only the former, and that was the gap.

### 7.3 Not borrowed

- No spiking, no biophysics, no neuromodulators.
- No claim that `ρ` corresponds to any measured neural quantity.
- No fitting to human behavioural data as validation. `[Standing rule]` The lag-CRP
  test regains force only under the three conditions of §4.4 of the growth spec; it
  is not a headline result.

---

## 8. DOS AND DON'TS

The register to check a proposed change against. If a change violates one of these,
it needs an explicit retraction in the logbook, not a quiet merge.

### DO

1. **Name the invariant a change affects, and whether it conserves it.** Every
   operator declares its effect on `K(𝕂)`.
2. **Put new cost terms in the sleep phase.** If it cannot wait until offline, it is
   not a cost, it is a drive — and drives need §4.1 justification.
3. **Derive the trigger, don't threshold it.** Growth fires on a stall, not on
   `ρ > c`.
4. **Keep the ledger.** A new mathematical object must delete at least as many
   hand-set numbers as it adds. §5bb deleted three and added zero. That is the bar.
5. **Report the null, not the raw number.** See §9.
6. **Write the falsifier before the implementation.**

### DON'T

1. **Don't add a λ.** The exchange rate in §6 is the only one. A second means the
   two-phase separation has failed.
2. **Don't minimise `ρ`.** §5bb proved perfect coherence is death: the flow drives
   `a → P_{H⁰}a(0)`, and generically `a → 0`. `ρ` is a *diagnostic and a Lyapunov
   function*, never an objective. The 2026-08 note proposed exactly this and it must
   stay refused.
3. **Don't let `F` optimise freely.** Trivial restriction maps are the global minimum
   of the gluing term. This is the "cohomology vacuous under identity restrictions"
   bug from MOS. `Π_{O(d)}` plus the `δ¹δ⁰ = 0` constraint are what prevent it.
4. **Don't drop to a graph.** §4.3.
5. **Don't reintroduce the LLM as the reasoner.** §2.1.
6. **Don't call it free energy.** §2.4.
7. **Don't add a mechanism that would work identically on a labelled graph.**

---

## 9. SPEC A — BUILT, RUN, AND AMENDED

`spec_a.py` implements `SPEC_GROWTH_ADDRESS_AND_DYNAMICS.md` §3.3–3.7. Controls
1–4 pass at one shared setting. Two additions:

```
1  path/tree            holes=1.7e-31   PASS
2  4-cycle, unfilled    holes=1.000000  PASS
3  filled 3-cycle       curl=1.000000   PASS   [leakage — the crucial one]
4  planted gradient     rank=1.000000   PASS
4b QUANTISATION FLOOR   holes=1.4e-05   FLOOR  [new]
5b 12-cycle, chordless  holes=1.000000  PASS   [new]
```

### 9.1 Amendment — the quantisation floor `[MEASURED 2026-08-13]`

Control 4 as specified plants `η = δ₀ψ` exactly. Built the way real data arrives —
integer citation counts pointing down a potential — it **fails**, holes = 8.7e-05.
Integer counts cannot express an exact gradient. This is a floor the instrument can
never beat on real data and must be reported alongside any real holes%.

### 9.2 Amendment — §3.8's headline number is wrong `[DERIVED + MEASURED]`

Synthetic 300-concept corpus, mostly a prerequisite ranking, three chordless 9-cycles
planted:

```
V=327  E=927  T=35  b1=569
ranking 65.01%   tangles 1.67%   holes 33.31%
null (200 draws): mean 60.50%  sd 2.10%   z = −12.9
```

Observed holes are **twelve sigma BELOW the null.**

The null is analytic, no simulation needed: a direction-randomised flow is isotropic,
so expected energy in any subspace is its dimension fraction. `dim H¹ = b₁`, hence

$$\mathbb{E}[\text{holes}\%] \;=\; b_1 / |E| \;=\; 569/927 \;=\; 0.614$$

against a simulated `0.605`. `[DERIVED, confirmed to 1%]`

**Consequence.** On a sparse graph `b₁/|E|` is large, so a high holes% is the null
expectation, not evidence of growth material. §3.8's outcome table reads the wrong
quantity. Replace it:

| new headline | why |
|---|---|
| **ranking% vs null** | the planted structure showed as 65% against a 39% null |
| **per-cycle localisation of harmonic mass** | the planted cycles appeared in the top harmonic edges |

Localisation is the output Construction 6 actually consumes. It survives even when
the global fraction is uninformative. **That is the usable result.**

### 9.3 Still to run

Point `spec_a.py` at `extract_refs.py` output as `citing<TAB>cited`. `V ≈ 1074`,
`E ≈ 2266`. Seconds. When later pointed at the co-activation graph, read
`skipped_wide_assemblies()` first — a capped assembly keeps edges but not 2-cells,
and its within-assembly cycles look exactly like structural holes.

---

## 10. OPEN DECISIONS

Ranked. Everything else in this document has either a construction or a measurement.

1. **Co-allocation vs separation.** When the harmonic residual names a cycle, does
   TATIANA cone it (integrate) or separate it (keep the memories distinct)? The
   allocation literature says excitability history decides — which in this formalism
   means it depends on `w`, the coupling weights. **`w` is computed and never read.**
   That is the same bug as the MOS Hebbian weights, still open. Highest priority.
2. **The MDL exchange rate** (§6).
3. **The stall tolerance** (§4.1).
4. **Whether reproduction (§5) produces anything viable.** Currently a canonical
   morphism with no claim attached.
5. **Whether `Ext²` obstructions for incidence algebras of 2-complexes make §4.3
   into a theorem.** `[OPEN — CHECK]` Quiver categories are hereditary (`Ext² = 0`,
   no obstructions); poset categories with relations should have higher global
   dimension. **Unverified. Do not build on it.**

---

## 11. PRIOR ART AND LIVE THREATS

`[SEARCHED 2026-08-13]`

- **Oversmoothing as representation degeneracy in neural sheaf diffusion**
  (arXiv:2605.11178). Reads learned sheaves as incidence-quiver representations;
  oversmoothing becomes collapse toward trivial or low-complexity summands; connects
  to GIT stability and moment maps. Reports that when `d_v = d_e` the trivial summand
  sits on a stability wall, and **non-uniform stalk dimensions remove the
  obstruction** — TATIANA's varying stalk dimensions are already on the right side of
  this, for free. Their own verdict on moment-map regularisation is that it is a
  dataset-dependent bias, not a universal improvement. Don't over-buy.
- **arXiv:2607.25387 — the live threat.** Reports that identity maps replace learned
  sheaf Laplacians on a benchmark family, and that diffusion-limit behaviour need not
  predict trained performance. This is the strongest available evidence for the
  *decorative* branch, published after §5bb decided LOAD-BEARING. **It concerns
  graphs.** §4.3 is the defence and must appear in the paper before a reviewer
  raises it.
- **Frank, *Why I Am Not SHY*** (2013). Argues SHY's mechanisms are poorly defined and
  not cleanly separable from ordinary synaptic scaling. Cite SHY as a hypothesis.
- Hansen & Ghrist pose metrics on cellular sheaves from combinatorial data alone, and
  the moduli space of cellular sheaves, as open. Any `E_K`-style stability term is a
  research problem, not a notation choice.

`[CAUTION]` The two arXiv identifiers above are from search snippets and have not
been fetched. Verify before citing in the paper.

---

## 12. WHAT WOULD KILL V1

Written before implementation, per §8 DO 6.

1. **Routing fails.** Run the wake flow on a synthetic complex with planted holonomy.
   If `ρ` does not drop to a harmonic floor and stop, or `harmonic_support` does not
   name the planted cycle, the routing law of §4.1 is dead. Minutes, no C++.
2. **Localisation fails on real data.** If Spec A's top harmonic edges are noise —
   no interpretable concept pairs — the growth address has no referent and growth
   must be triggered some other way.
3. **The invariant does not survive.** Run wake+sleep for many cycles on synthetic
   input. If `K(𝕂)` drifts monotonically, or the sheaf collapses to a trivial
   summand, TATIANA does not have identity and this document is refuted.
4. **The sheaf is decorative after all.** If ablating to identity restriction maps
   changes nothing on TATIANA's own task, §5bb's decision reverses and arXiv:2607.25387
   was right.

Any of these fires, it goes in the logbook and in the Refuted Claims appendix. That
is the point of the instrument.

---

## 13. AMENDMENTS THIS DOCUMENT MAKES

| document | change |
|---|---|
| logbook §7 | Track A retired. TATIANA is Track B. |
| `SPEC_GROWTH_ADDRESS_AND_DYNAMICS.md` §3.7 | add control 4b (quantisation floor) and 5b (chordless cycle) |
| same, §3.8 | outcome table reads the wrong number; replace per §9.2 |
| same, §4 | the tick gains a phase flag; `q_t = 0` is a supported mode |
| `MEMORY_MODEL_TWO_COMPLEX.md` §4(IV)(b) | `Π_{O(d)}` is a gauge fixing **and** the projective identity mechanism |
| the 2026-08 energy note | §2–13 adopted in spirit, §2's six-λ functional refused; see §8 DON'T 1–2 |
