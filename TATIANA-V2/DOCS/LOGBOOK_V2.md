# TATIANA V2 LOGBOOK

Append-as-you-go, same rule as `TATIANA_LOGBOOK.md`: log decisions when they land, not at session
end. An early V0 retrospective write-up nearly lost load-bearing reasoning this way — don't repeat
it.

## Standing discipline (combined checklist, `MATH_TOOLBOX.md` Part IX + identity map §8)

- A17 — new math earns its place only if it changes a number a program prints, or deletes a
  decision a human was making by hand.
- No measurement is reportable without a positive control, a null, and a structure-free control,
  at one shared parameter setting, before it touches anything real.
- Epistemic tags on every load-bearing claim: `[MEASURED]` `[DERIVED]` `[INFERRED]`
  `[ENGINEERING CHOICE]` `[OPEN HYPOTHESIS]` `[SPECULATION]`.
- Name the invariant a change affects, and whether it conserves `K(𝕂)`.
- New cost terms belong in the sleep phase only. Never add a second λ.
- Derive triggers; never threshold them.
- Write the falsifier before the implementation.
- Effective sample size, not label/observation count, for any confidence interval.
- Never read an optimum off a flat sweep.
- Always compute what a statistic does when the effect is absent, before reading it when present.
- A superseded "blocking" line is worse than no line — renumber/retract stale planning immediately.

## Provenance — what V2 inherits, from where

| V2 object | source | status at handoff |
|---|---|---|
| `M=(C,F,s)`, sheaf Laplacian, `ρ=α·ρ̃` | `MATH_TOOLBOX.md` I.1–I.2 | ✅ verified, carried forward as-is |
| SPD/density-matrix stalks, CPTP/Householder restriction maps | `MATH_TOOLBOX.md` I.4 | ✅ derived, shipped in V0 C++ |
| `K(𝕂)` invariant (dimension vector, exact under consolidation) | identity map §3.1 | `[DERIVED]`, Level 1 (projective) `[INFERRED]` — not yet measured |
| Two-phase WAKE/SLEEP law, Hodge routing | identity map §4 | `[DERIVED]`, partially measured (Spec A) |
| `𝕂`/`W` two-complex, `ι_! ⊣ ι* ⊣ ι_*` adjunction, `γ(ν)` consolidation | `MATH_TOOLBOX.md` II.2 | ✅ measured end-to-end in V0 |
| Construction 6 (coning, growth) | `MATH_TOOLBOX.md` III.3 | ✅ most-verified new construction in V0 |
| Construction 7 (MDL growth law) | `MATH_TOOLBOX.md` III.4 | ✅ measured, not wired into any engine |
| Curvature controller (Forman-Ricci, FOLD/EXPAND) | `MATH_TOOLBOX.md` I.7 | ✅ derived, unit-tested, never wired — low-precision sign-flip risk flagged, unresolved |
| VerifyOp trichotomy | `MATH_TOOLBOX.md` I.8 | ✅ fixed epistemically, not connected to a real checker |
| Spec A (growth-address instrument) | identity map §9, `SPEC_GROWTH_ADDRESS_AND_DYNAMICS.md` | ✅ run, real numbers on record; script location unresolved (see entry below) |
| Six-term λ energy functional | `Phase I — Understand the Geometry o.txt` (second half) | 🔴 refused, identity map §8 DON'T 1 / §13 — do not reintroduce |
| Pachner moves, FCA substrate, K₀/Jordan–Hölder atoms, trained geometry-blend weight, WFR closed form, diffusion retrieval, random-mutation growth | `MATH_TOOLBOX.md` Part VIII | 🔴/❌ dead-end registry — do not re-propose without reading why they died |

## Entries

- **2026-08-13** — V0 close-out committed (`70f0ca1`, branch `fix-11-13-and-curvature-decisions`):
  `DOCS/MATH_TOOLBOX.md` and `DOCS/TATIANA_V1_IDENTITY_MAP.md` land as the founding record and the
  binding identity document. Branch `tatiana-v2` created from that commit (not from `main`, which
  is 4 commits behind and missing essentially all V0 content — discovered when the original plan
  to branch from `main` was checked against `git log main`). `TATIANA-V2/` skeleton created
  (`MATH/`, `EXPERIMENTS/` — standalone CMake, no MOS dependency — `DOCS/LOGBOOK_V2.md`).
  Reformulation plan adopted with two amendments made during planning, both logged here rather
  than silently: (1) the six-term λ energy functional originally drafted from the predictive-coding
  half of `Phase I — Understand the Geometry o.txt` is **refused** — the identity map already
  replaced it with the two-phase law before this session started, and the plan was corrected to
  build on that instead of reintroducing what was already rejected. (2) Identity map §2.1's
  encoder/verification-lift allowance is narrowed but not closed: both roles stay required, neither
  is to be filled by a wrapped/pretrained LLM, and their own architecture is now an open research
  question (Phase IV of the plan) rather than an assumption either way. `MOS/python/Spec A.py`
  exists (space in filename) and is committed — the plan's concern about a missing/unreconstructable
  script was unfounded, just needed a repo-wide search. **Next**: Phase 0's invariant-drift
  experiment (identity map §12 Kill-Test 3) — not yet started.
- **2026-08-14 (later)** — **The book is now V2-shaped, as a plan.** `tatiana-book/` moved into
  `TATIANA-V2/` (by Charbel) and restructured to be rewritten section by section rather than read
  as finished. Changes: (1) new opening chapter `parts/00_v2_reformulation.tex` — the commitment,
  what TATIANA is *not*, the six structural changes that force a rewrite rather than an edit, and
  the encoder/verification-lift position; (2) **every chapter now carries a disposition**
  (`KEEP`/`RECAST`/`RETIRE`/`NEW IN V2`) **and a work-plan box** stating goal, raw material, ordered
  steps, and a done-when condition — the plan is an *instruction*, deleted and replaced by prose
  when the chapter is written, so **a chapter still containing a work plan is a chapter that is not
  done**; (3) four new chapters, currently pure work plans: `11_identity` (the invariant — now the
  centre of the book), `12_twophase` (the wake/sleep law, plus the record of the refused six-λ
  functional), `13_reproduction`, `14_encoder`; (4) `main.tex` reordered so Identity and the
  Two-Phase Law sit immediately after the cohomology they depend on, rather than the V0 ordering
  which had no place for them; (5) frontmatter rewritten to say the book is mid-rewrite and how to
  read it that way. Compiles clean, 101 pages, no undefined references.
  **Dispositions assigned**: `KEEP` — sheaf, Laplacian, adjunction, cone (Construction 6), quantum;
  `RECAST` — base complex (its stratification was justified by organs and that ground is gone),
  coherence (ρ is a diagnostic and Lyapunov function, *never* an objective), semantic geometry,
  cohomology (largest change in *role*: the Hodge split becomes the wake phase's routing law),
  growth operators, MDL law (now explicitly the sleep phase's maintenance cost), retrieval,
  verification, limits, open problems. Nothing was assigned `RETIRE` except the six-λ energy
  functional, which is recorded as refused inside `12_twophase` rather than deleted.
  **Sharpest thing the pass surfaced**: the growth-address problem is now the book's ranked #1 open
  problem. V0 obtained its measured non-exact 1-cochain η from *organs disagreeing with each
  other*. V2 has no organs. Until a source of η exists for a single kernel, Prop 8.2 leaves growth
  with no address and the kernel cannot grow at all — this is flagged loudly in `04_cohomology`
  and `09_open_problems` rather than papered over.
  **Docs**: copied four inherited documents into `TATIANA-V2/DOCS/` that the book cites but did not
  have locally — `AUDIT_SCRUTINY_AND_BOOK.md` (the F1–F14 audit the epistemic-tag discipline
  descends from), `Phase I — Understand the Geometry o.txt`, `PRIOR_ART_AND_THE_REPLAN.md`,
  `MOS_FINALIZATION.md`. Wrote `TATIANA-V2/DOCS/README.md` recording what each inherited doc is for
  **and what was deliberately left behind** (V0 engine specs, the LLM budget plan, the dropped
  K₀/Jordan–Hölder schema, and the retrieval/cover sagas already condensed into `MATH_TOOLBOX.md`
  Parts V–VI) so the decision is visible and reversible.
- **2026-08-14** — **Phase 0 ran. Kill-Test 3 SURVIVES.** `EXPERIMENTS/phase0_invariant/`
  (C++20, no deps, ~1s); write-up in `MATH/phase0_invariant_dimension.md`. Three runs at one shared
  setting: **A (null)** 3-cycle fed exact/pure-gradient input only — growth never fires, residual
  `7.3e-15`; **B (positive)** same complex with a planted harmonic component — growth fires once,
  residual stalls at `9.8e-01`; **C (structure-free)** path with `b₁=0` — growth structurally
  unreachable, residual `5.9e-15`. A and C are zero for *different* reasons (untriggered vs.
  impossible), which is the point of running both. **Pre-existing `K(𝕂)` exactly untouched in all
  three runs across 500 ticks of real molding + consolidation**, and the one growth event's size
  came out `k_w = 1` via **two independent routes that agree** — holonomy `dim ker(H−I)` and
  cochain-space `dim ker(δ⁰(δ⁰)ᵀ)`. `Q(t)` moves in B (`4.910642→4.916937`) while dimensions stay
  pinned — §3.2's projective claim (relative structure changes, dimension doesn't) behaving as
  advertised. Reproduced across 4 RNG seeds, identical verdict and identical `k_w` each time.
  `[MEASURED]` — this converts identity map §3.1/§3.2 from `[DERIVED]`/`[INFERRED]` to measured,
  which is what Phase 0 existed to do.
  **Harness bug found and fixed mid-run, recorded not quietly corrected**: the first version
  compared `currentK()`'s vertices-then-edges concatenation index-by-index, so appending a grown
  vertex shifted the boundary and reported a false `DRIFT DETECTED` in run B. Underlying dimensions
  were never wrong. Caught **only** because run B's expected behaviour was written down before the
  code — exactly the failure mode the discipline warns about.
  **Does NOT establish** (all stated in the experiment header up front, not discovered later): no
  2-cells, so §4.3's "triangles make molding obstructible" is untested and the routing law's
  bad-2-cell branch is unexercised; **no sleep-phase MDL pruning**, so the "may decrease (pruning)"
  half of §4's invariant table is entirely untested — Kill-Test 3 survives, it is not passed in
  full; `γ(ν)` constant (VerifyOp unmodelled); post-growth dynamics unwired (measures one growth
  event's size, not repeated-growth stability); dense orthogonal restriction maps rather than
  Householder products; synthetic input only. **New open question raised, not answered**: molding
  is bounded to one nudge per tick before the same tick's stall check — whether unbounded
  accumulated molding could erode the very topological obstruction growth depends on is genuinely
  open.
- **2026-08-13 (same day)** — **Visualization strategy decided, work deferred.** Evaluated
  `FutureAIGuru/BrainSimIII` and `FutureAIGuru/BrainSimII` (both C#/WPF, MIT). BrainSimII is a
  spiking-neuron/embodied-agent simulator (vision/motor modules, a virtual agent "Sallie") — not a
  structural match, ruled out. BrainSimIII's core is the UKS: a plain labeled graph ("Things"/
  "Relationships") with a dedicated viewer (`ModuleShowGraphDlg.xaml`, `Network.cs`), the closer
  match, but its graph UI is tightly coupled to its own engine, not a separable renderer, and a
  plain node/edge graph has no notion of stalks, restriction maps, 2-cells, `ρ`/curvature, or
  harmonic residual — the parts of TATIANA's structure that are load-bearing, not decorative
  (identity map §4.3). **Decision (Charbel, overriding the lightweight-custom-viewer
  recommendation)**: fork BrainSimIII and modify it to render TATIANA's actual complex state
  instead of the UKS, for debugging/visualizing the C++ experiments only — it is tooling, never a
  dependency of the math itself. **Explicitly deferred**: no forking or modification starts now;
  this is picked up only once a specific math phase (Part B of the reformulation plan) is fully
  closed out on paper first. `TATIANA-V2/README.md` records the planned `VIZ/` location. Nothing
  created yet.
