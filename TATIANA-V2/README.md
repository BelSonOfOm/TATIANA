# TATIANA V2

**Read `DOCS/TATIANA_V1_IDENTITY_MAP.md` (repo root `DOCS/`, not copied here) before anything else
in this folder.** It is not V0 debris and it is not superseded by this folder's existence — it is
the binding identity document this stage builds forward from. Its one-sentence commitment:

> TATIANA is a cellular sheaf on a stratified 2-complex whose section relaxes, whose restriction
> maps mold, and whose complex grows and prunes — under a two-phase law that conserves a stated
> invariant exactly while awake and projectively while offline.

**Read `DOCS/MATH_TOOLBOX.md` (repo root `DOCS/`) second.** It is the full inventory of what the
V0 record (the organ-complex-around-an-LLM architecture, now retired) actually proved, measured,
and killed — every construction here should either extend something tagged ✅/🔵 there, or state
explicitly why it's reopening something tagged ❌/🔴.

## What this folder is

Math-first, C++-second. No production engine, no LLM-wrapper code, no LLM as reasoner under any
circumstance. C++ exists here solely to numerically test a theorem or claim.

```
MATH/           one file per construction, epistemic-tagged (✅🔵❌⚠️🔴), organized by the
                phases in the reformulation plan, not by session date
EXPERIMENTS/    standalone CMake project, no dependency on ../MOS/CMakeLists.txt
VIZ/            (deferred — see DOCS/LOGBOOK_V2.md 2026-08-13 entry) a fork of
                FutureAIGuru/BrainSimIII, modified to render TATIANA's complex state
                (dumped by EXPERIMENTS/ as JSON) instead of the UKS. Debugging/visualization
                tool only, not a dependency of the math. Not started until a math phase closes.
DOCS/
  LOGBOOK_V2.md   append-as-you-go decision record for this stage specifically
```

## Discipline (carried from `MATH_TOOLBOX.md` Part IX + identity map §8, one combined checklist)

- New math earns its place only if it changes a number a program prints, or deletes a decision a
  human was making by hand (A17).
- No measurement without a positive control, a null, and a structure-free control, at one shared
  setting, before it touches anything real.
- Every load-bearing claim gets an epistemic tag: `[MEASURED]` `[DERIVED]` `[INFERRED]`
  `[ENGINEERING CHOICE]` `[OPEN HYPOTHESIS]` `[SPECULATION]`.
- Name the invariant a change affects, and whether it conserves `K(𝕂)`.
- New cost terms belong in the sleep phase. **Never add a second λ** — the two-phase law replaced
  the six-term energy functional exactly to avoid this.
- Derive triggers; never threshold them.
- Write the falsifier before the implementation.
- Log decisions to `DOCS/LOGBOOK_V2.md` as they land, not at session end.
