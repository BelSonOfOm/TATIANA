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
