# TATIANA — Presentation & Poster Plan

**Venue:** local undergraduate mathematics conference day.
**Goal:** get people, researchers, and potential collaborators interested — NOT to claim a finished result or a novel theorem. The honest pitch is *"a working realization of ideas that recent papers only proposed, built on ~zero budget, with an open invitation to build on it."*

> ⚠️ **Reference verification status.** Citations below are tagged **[VERIFIED]** (confirmed via live web search on 2026-07-22) or **[FROM MEMORY — VERIFY BEFORE PRINTING]** (stated from training knowledge; searches were rate-limited before I could confirm arXiv ids/years). Do NOT print a memory-tagged citation without checking it first. A wrong citation on a poster at a math venue is exactly the kind of easy takedown we've spent this project avoiding.

---

## 1. The core decision: which demo

**DECISION: Option A — demo the coherence mechanism, fully pre-computed.**

| | Option A (chosen) | Option B (rejected for Friday) |
|---|---|---|
| What it shows | ρ measuring module (dis)agreement on real content; the complex evolving; conflict localized to the guilty edge | TATIANA solving FIRST DRAFT end-to-end |
| Status | **already works** (`integration_demo.py`, ρ 0.00→0.06→0.14) | multiple known gaps (ρ not in C++, no support name→id, VerifyOp unhooked) |
| Risk by Friday | low — polish only | high — likely half-works, worse than nothing at a poster |

**Hard rule for the venue: NO live API calls in the demo path.** Groq free tier is 30 RPM / 6k TPM — a curious crowd rate-limits you in minutes; conference wifi is unreliable; the machine is 4c/5.9 GB with a slow embedding cold-start. **Everything is pre-computed and offline.** The self-contained `complex_real.html` (opens in any browser, arrow-keys through the evolution) IS the demo. A live run is an *optional* party trick attempted only if conditions are good.

---

## 2. Poster strategy — two layers on purpose

The audience is mostly **undergraduates**, with a few researchers. The sheaf Laplacian is above the median attendee. So the poster is layered:

- **Entry layer (10-second hook, for everyone):** the orchestra analogy.
  > *Each module is a musician. **ω** is how out-of-tune they are with each other. **ρ** is that on a 0–1 scale that doesn't change when they play louder or when you add musicians.*
- **Core layer (for researchers):** the actual formalism (cellular sheaf Laplacian, Rayleigh normalization, the Anderson–Morley bound), sitting underneath the hook.

Undergrads get the top; researchers drop to the core; both stop walking. **The visualization is the magnet** — the ρ spike with the red dashed "guilty edge" is what makes people point.

**Put the limitations on the poster.** "Here's what works, here's what doesn't yet, here's where I want help" reads as maturity at a research venue and is precisely what recruits collaborators. Overclaiming is what makes researchers walk away.

---

## 3. Poster layout (recommend A0 portrait, 3 columns)

*(Format still to confirm — see §8. Layout below adapts to A0/A1.)*

```
┌───────────────────────────────────────────────────────────────┐
│  TITLE + one-line subtitle + your name / affiliation / QR      │
├───────────────┬───────────────────┬───────────────────────────┤
│ COL 1         │ COL 2             │ COL 3                     │
│ 1. The problem│ 4. ω and ρ        │ 7. Results (the money):   │
│    (amnesia,  │    (the orchestra │    ρ 0.00→0.06→0.14 on    │
│    hidden     │    + the boxed    │    real content + the     │
│    state)     │    formula)       │    visualization image    │
│               │                   │                           │
│ 2. M=(C,F,s)  │ 5. The uncertainty│ 8. What works / what's    │
│    the two-   │    stack (ρ, ρ̂,   │    next (honest table)    │
│    level idea │    Betti, Verify) │                           │
│               │                   │ 9. The quantum direction  │
│ 3. The        │ 6. Zero-budget    │    (contextuality = H¹)   │
│    adjunction │    architecture   │                           │
│    S→π→U→Φ→B  │    (split brain)  │ 10. References + QR to repo│
└───────────────┴───────────────────┴───────────────────────────┘
```

**The one boxed equation** (undergrads can admire it, researchers can read it):
$$\rho(x)=\frac{\sum_{\{u,v\}\in E}\lVert x_u-x_v\rVert^2}{B\,\lVert X\rVert_F^2}\in[0,1],\qquad B=\max_{\{u,v\}\in E}(d_u+d_v)$$
with the plain-language gloss directly beneath it.

---

## 4. The narrative arc (how to talk to someone at the poster, 60s)

1. *"Plain LLMs forget, and hide when they're unsure."*
2. *"We give a group of reasoning modules an explicit shared geometry — a shape you can compute with."*
3. *"This number ρ measures whether the modules actually agree, and it points at exactly which two disagree."* → **show the visualization**
4. *"It runs free, on a laptop that can't even host a language model, because the geometry is local and only the reasoning is remote."*
5. *"Most of the math is borrowed — Hansen–Ghrist, Abramsky–Brandenburger. What's ours is making it all interlock and actually run, and I'd love people to build on it."*

That last line is the collaboration hook. Deliver it deliberately.

---

## 5. Detailed references — organized by role in the project

### A. The load-bearing prior work (cite prominently; these define our honesty)
- **[VERIFIED]** Hansen, J. & Ghrist, R. — *Opinion Dynamics on Discourse Sheaves.* arXiv:2005.12798 (SIAM J. Appl. Math, 2021). **This is the source of the sheaf Laplacian we use for ρ.** Our coherence measure is their construction applied to LLM modules — cite it as the origin, not as background.
- **[VERIFIED]** *Applied Sheaf Theory For Multi-agent AI (Reinforcement Learning) Systems: A Prospectus.* arXiv:2504.17700 (Apr 2025). Proposes sheaf theory for multi-agent AI **without building it**. We are a working instance of the prospectus.
- **[VERIFIED]** *Prospects for inconsistency detection using large language models and sheaves.* arXiv:2401.16713 (Jan 2024). LLM consistency ratings lifted via sheaves — closest in spirit to our conflict score; theirs targets claims/hypertext, ours targets cooperating modules.

### B. The uncertainty / calibration context (position against these)
- **[VERIFIED]** *When Planning Fails Despite Correct Execution: On Epistemic Calibration for LLM-Based Multi-Agent Systems.* arXiv:2605.23414.
- **[VERIFIED]** *Uncertainty Quantification in LLM Agents: Foundations, Emerging Challenges, and Opportunities.* arXiv:2602.05073.
- **[VERIFIED]** *Calibration of Structured Ignorance Certificates for Diagnosing Unknown Unknowns in Reasoning Models.* arXiv:2606.08571. (Uses the "known/unknown unknowns" framing that parallels our KNOWN_IGNORANCE verdict.)

### C. Adjacent sheaf/multi-agent work (shows the field is active — a reason to move, and to collaborate)
- **[VERIFIED]** *Learning Multi-Agent Coordination via Sheaf-ADMM.* arXiv:2605.31005.
- **[VERIFIED]** *Sheaf-Theoretic Planning: A Categorical Foundation for Resilient Multi-Agent Autonomous Systems.* arXiv:2605.01879.
- **[VERIFIED]** *Nonlinear Sheaf Diffusion in Graph Neural Networks.* arXiv:2403.00337.

### D. The quantum-information bridge (for the "future direction" panel)
- **[FROM MEMORY — VERIFY BEFORE PRINTING]** Abramsky, S. & Brandenburger, A. — *The sheaf-theoretic structure of non-locality and contextuality.* New J. Phys. 13 (2011). **Claim to verify:** quantum contextuality = local sections that cannot glue into a global section = our ρ / H¹≠0.
- **[FROM MEMORY — VERIFY]** Abramsky, Barbosa, Mansfield — cohomology of contextuality (~2015–2017). Verify exact title/venue.
- **[FROM MEMORY — reliable but confirm]** The **Bures metric** is the quantum-fidelity metric on density matrices; Fubini–Study is the pure-state metric tied to **quantum Fisher information**. (Standard QI facts; phrase carefully.)

### E. The mathematical toolkit (standard results — cite lightly, mainly to show grounding)
- **[reliable]** Anderson & Morley bound: $\lambda_{\max}(L_G)\le\max_{\{u,v\}\in E}(d_u+d_v)$ — gives our cheap, eigendecomposition-free normalization.
- **[reliable]** Woodbury matrix identity + Matrix Determinant Lemma — tractable low-rank Bayesian fusion (`semantic_skill.cpp`).
- **[reliable]** Bures–Wasserstein / 2-Wasserstein between Gaussians (`knowledge_base.cpp`).
- **[FROM MEMORY — VERIFY]** Curry, J. — *Sheaves, Cosheaves and Applications* (thesis, ~2014) for cellular sheaves; Leinster / May for operads; Friston for the free-energy / predictive-coding analogy behind Expected Precision.

### F. Systems context (name-check so researchers see you know the landscape)
- **[FROM MEMORY — reliable existence, confirm ids]** MemGPT (memory-augmented LLM), AutoGen / MetaGPT / LangGraph (multi-agent orchestration frameworks). We differ by having an explicit *geometric* coordination signal rather than prompt-based coordination.

---

## 6. Ideas we took, and how we organized them (provenance table)

| Idea / tool | Source (borrowed) | What WE did with it |
|---|---|---|
| Sheaf Laplacian as disagreement measure | Hansen–Ghrist | Applied it to LLM *modules*; normalized to ρ∈[0,1]; made it the RESOLVE/EXPLORE gate |
| Anderson–Morley bound | spectral graph theory | Used it to make ρ cheap (no eigensolve in the fast path) |
| Contextuality = failure to glue | Abramsky–Brandenburger | Reinterpreted our conflict score as the same object; basis for the quantum direction |
| Bures–Wasserstein distance | quantum info geometry / OT | Concept-to-concept distance in the knowledge base |
| Woodbury + low-rank⊕diagonal Σ | numerical linear algebra | Scalable Bayesian fusion of concept embeddings |
| Operads → DAG | May/Leinster; category theory | Execution grammar; foliation into commuting slices |
| Persistent homology / Betti | Curry; TDA | Deciding what consolidates into permanent memory (b₀ fragmentation guard) |
| k-NN regression | classic ML | Training-free Expected Precision ("known ignorance") over logged (query, ρ) pairs |
| Predictive coding / expected precision | Friston (free-energy) | The *meta*-layer: predict ρ before computing it |
| Adjunction (left/right functors) | category theory | S→π→U→Φ→B: keep natural language out of the math engine |
| Simplicial complex / n-ary relations | algebraic topology | Knowledge as joint binding (a theorem + its prereq closure = a simplex), not pairwise edges |

**The organizing principle** (this is worth a sentence on the poster): *each borrowed piece answers one specific question, and they were assembled so the output of one is the input of the next — text → DAG → execution → geometry → coherence → consolidation.*

---

## 7. Where the novelty actually is (honest, tiered)

**NOT novel (say so, cite the owners):** the sheaf Laplacian, contextuality-as-obstruction, Bures–Wasserstein, Woodbury, operads, persistent homology. All borrowed. Claiming any as ours is an easy, embarrassing takedown.

**The genuine contribution, strongest first:**
1. **A working implementation validating "prospectus" papers.** The nearest prior work (2504.17700, 2401.16713) *proposes without building*. We built a running system. Validating a prospectus is a recognized contribution type.
2. **The specific integration.** Sheaf-Laplacian coherence *gating a RESOLVE/EXPLORE controller* inside an *operad-executed DAG engine* feeding a *persistent consolidation loop* — as one interlocking system. We did not find this exact combination, built, anywhere.
3. **Concrete engineering findings** other implementers would want: (a) the provider hard-400s on logprobs, so self-reported confidence is *structurally unavailable* → confidence must come from structural agreement (ρ); (b) a hidden constant confidence silently collapsed the entire covariance geometry to one value.
4. **Zero-budget / hardware-constrained design as a driver:** a coordination signal that runs on a 5.9 GB laptop with no local LLM, because geometry is local and only reasoning is remote.
5. **(Weaker, frame carefully)** the two-level stratification (coarse subsystems / fine concepts) as a specific modeling choice; the training-free k-NN "known ignorance" mechanism (calibration is a crowded field — position, don't claim).

**One-line novelty statement for the poster:**
> *"The mathematics is largely established; the contribution is a working, zero-budget system that makes these pieces interlock and coordinate LLM reasoning modules through an explicit, computable geometry — a running instance of what recent papers proposed."*

---

## 8. Guardrails — what to NOT put on the poster

- ❌ "A rigorous mathematical model of cognition" / "genuine simulation of intelligence" — overclaim; kills credibility.
- ❌ Any claim that the sheaf Laplacian, ρ, or contextuality-as-obstruction is *our* mathematics.
- ❌ Any memory-tagged citation that hasn't been verified.
- ❌ A demo that needs the internet.
- ✅ DO show a real number on real content, DO show the limitations table, DO credit the sources.

---

## 9. Open decisions (need Charbel's input)
1. **Poster format:** A0 or A1? Portrait (recommended) or landscape? — determines final layout.
2. **Output form:** printable HTML/PDF (I build it, you send to a print shop) or content to drop into your own PowerPoint/LaTeX?
3. **Repo public?** A QR code to a public GitHub repo (with README + the logbook) is a strong collaboration hook — but only if you're comfortable making it public.
4. **Name/affiliation/contact** block content.

## 10. Two-day execution plan
- **Day 1 (demo hardening, ~half day):** cache embeddings to disk (kill cold-start); make `integration_demo` deterministic + re-runnable; polish `visualize.py` (it's the money shot); verify `complex_real.html` opens standalone with no network.
- **Day 2 (poster + rehearsal):** build poster from this plan; verify every citation (untag the [VERIFY]s); print; rehearse the 60-second pitch (§4).
- **Cut without guilt (→ "future work" panel):** full FIRST DRAFT solve, ρ in C++, VerifyOp, dormant→consolidation, quantum implementation.
