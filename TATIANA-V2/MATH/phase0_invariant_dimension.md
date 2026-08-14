# Phase 0 — the invariant `K(𝕂)` under wake/sleep, and why `k_w = dim ker(H−I)`

**Extends**: `DOCS/TATIANA_V1_IDENTITY_MAP.md` §3.1 (the exact invariant), §12.3 (Kill-Test 3);
`DOCS/MATH_TOOLBOX.md` III.3 (Construction 6), III.4 (holonomy propagation), II.2 (`γ(ν)`
consolidation).

**Status**: the drift claim is `[MEASURED]` on synthetic complexes. The dimension formula is
`[DERIVED]` below and `[MEASURED]` two independent ways. Everything in §4 is `[OPEN]`.

**Experiment**: `../EXPERIMENTS/phase0_invariant/` (C++20, no dependencies, ~1s).

---

## 1. The falsifier, written before the code

Identity map §12.3: *"Run wake+sleep for many cycles on synthetic input. If `K(𝕂)` drifts
monotonically, or the sheaf collapses to a trivial summand, TATIANA does not have identity and
this document is refuted."*

Sharpened into something a program can fail:

> `K(𝕂)` restricted to **pre-existing** cells must be **exactly** unchanged, every tick, under
> arbitrarily much molding and consolidation — bit-identical integers, not "small drift." It may
> change **only** by the appearance of a new cell under growth, and that new cell's dimension must
> equal a quantity derived *before* the growth decision, never a hand-set or gradually-accumulated
> one.

Note this is stronger than §12.3 as written: §12.3 says "drifts *monotonically*", which a random
walk in dimension would technically survive. The check implemented is exact conservation, which
also catches non-monotone drift.

## 2. Why the dimension is `dim ker(H−I)`, and why that's checkable two ways

Construction 6 sets `F(w) := lim D_γ`, so `dim F(w) = dim H⁰(γ; F|_γ)` — the *compatible part* of
the cycle, not a summary of it (`MATH_TOOLBOX.md` III.3). Two independent routes to that number:

**Route 1 — cochain space.** `H⁰(γ;F|γ) = ker δ⁰`, and on a 1-complex with no 2-cells the harmonic
space *is* `H¹`, with `dim H¹ = dim H⁰` on a cycle with equal vertex/edge stalk dimensions (the
Euler-characteristic argument in `MATH_TOOLBOX.md` III.3 — `χ = 0` since `dim C⁰ = dim C¹`).
Computed here as `dim ker(δ⁰(δ⁰)ᵀ)` via a Jacobi eigensolve.

**Route 2 — holonomy.** `lim D_γ ≅ ker(H − I)` where `H` is the round-trip holonomy
(`MATH_TOOLBOX.md` III.4, the fix that removed the growth law's factor-of-`k` overcount: since
restriction maps are orthogonal hence invertible, only the first leg needs describing, the rest are
determined). Computed here from the transports directly.

For the eigen-test in Route 2, note `H` is real orthogonal, so for a unit `v`:
`vᵀ(H + Hᵀ)v = 2⟨v, Hv⟩ ≤ 2‖v‖‖Hv‖ = 2`, with equality iff `Hv = v`. So `H + Hᵀ` — real symmetric,
Jacobi-diagonalisable — has eigenvalue exactly `2` precisely on `ker(H−I)`, and strictly less
elsewhere. Counting eigenvalues at `2` gives the dimension without forming a kernel basis.

**`d` is odd on purpose.** Every element of `SO(odd)` has eigenvalue 1 (`MATH_TOOLBOX.md` III.3's
"structural surprise": a generic rotation fixes nothing is *false* in odd dimensions). At `d=3` the
cycle therefore always has something consistent to name, so a growth address is reachable by
construction rather than by luck — and correspondingly `k_w = 1` is the *expected* answer here, not
a surprise. At even `d` the degenerate `H⁰=0` case becomes reachable; untested.

## 3. What was measured

Three runs at one shared parameter setting (`N_TICKS=500`, `γ₀=0.05`, `lr_mold=0.02`,
`stall_tol=0.3`), per the standing rule that no measurement is reportable without a positive
control, a null, and a structure-free control:

| run | complex | input | growth | pre-existing `K(𝕂)` |
|---|---|---|---|---|
| **A** (null) | 3-cycle, `d=3` | exact/pure-gradient only | never fired | **untouched, 500 ticks** |
| **B** (positive) | 3-cycle, `d=3` | planted harmonic, `‖c‖=1` | fired once, tick 0 | **untouched, 500 ticks** |
| **C** (structure-free) | path, `b₁=0`, `d=3` | harmonic *attempted* | never fired | **untouched, 500 ticks** |

Run B: `k_w = 1` via holonomy **and** `k_w = 1` via `ker(δ⁰(δ⁰)ᵀ)` — the two independent routes
agree. Spoke edges come out at `dim 3` each (`F(f_i) := F(v_i)`).

Residuals separate cleanly by ~14 orders of magnitude: A and C resolve to `7.3e-15` / `5.9e-15`
(machine precision — the fast flow provably kills `im δ⁰`, and there is nothing else present),
while B stalls at `9.8e-01` against a planted magnitude of `1.0`. There is no threshold-tuning
sensitivity here to worry about; `stall_tol=0.3` sits in an enormous empty gap.

**A and C are zero for different reasons, and that's the point of having both**: A's complex *can*
carry harmonic mass (`b₁=1`) and simply wasn't given any; C's *cannot* (`b₁=0`), so its zero is
structural. A instrument that only ran A could be measuring "growth never fires" rather than
"growth fires exactly when it should."

`Q(t)` (mean `‖R^𝕂−I‖²_F`) moves in B (`4.910642 → 4.916937`) and is **identically constant** in A
and C — molding does real work on the maps while dimensions stay pinned. That's §3.2's projective
claim behaving as advertised: relative structure changes, dimension doesn't.

**Reproduced across 4 RNG seeds** (`20260813, 7, 12345, 999999`) — identical verdict and identical
`k_w` every time.

**One harness bug found and fixed mid-run, recorded rather than quietly corrected**: the first
version compared `currentK()`'s vertices-then-edges concatenation index-by-index against its
initial value, so appending a new vertex shifted the vertex/edge boundary and reported a false
`DRIFT DETECTED` in run B. The underlying dimensions were never wrong. Fixed by comparing the
original vertex and edge prefixes separately. Worth noting because it is exactly the failure mode
the project's own discipline warns about — an instrument reporting a confident wrong answer — and
it was caught only because run B's *expected* behaviour was written down in advance.

## 4. What this does NOT establish — read before citing it

Scope reductions, all stated in the experiment's own header rather than discovered later:

- **No 2-cells.** Only the two-term split `C¹ = im δ⁰ ⊕ H¹` is exercised. The routing law's third
  branch ("flags a bad 2-cell", identity map §4.1) is untested, and §4.3's argument that 2-cells are
  what make molding *obstructible* is therefore **not** what's being confirmed here.
- **No sleep-phase MDL pruning.** Identity map §6's maintenance cost is not implemented — its
  exchange rate is still an open engineering choice (§10 open decision #2). So the "**may decrease**
  (pruning)" half of §4's invariant table is entirely untested; only the "conserved exactly" half is.
- **`γ(ν)` is a constant.** VerifyOp is not modelled; every tick consolidates as if VERIFIED.
- **Post-growth dynamics are not wired.** The new vertex `w` and its spokes are recorded for
  `K(𝕂)` bookkeeping; they do not participate in later ticks. This measures the *size* of one
  growth event, not long-run behaviour after growth — in particular **not** whether repeated growth
  is stable.
- **Molding is bounded to one nudge per tick before the same tick's stall check.** Whether
  unbounded accumulated molding could eventually erode a topological obstruction on its own is
  **open and not answered here** — it is a genuine question about whether the wake phase's slow
  layer can dissolve the very address the growth layer depends on.
- **Restriction maps are dense orthogonal matrices**, not V0's Householder products. Storage
  efficiency isn't under test; the `Π_{O(d)}` retraction's non-closure caveat
  (`MATH_TOOLBOX.md` I.4) doesn't bite here but *will* return when Householder factoring comes back.
- **Synthetic input only.** Nothing here touches real data, so it says nothing about identity map
  §12.2 (localisation on real data).

**What it does establish**: on the structures tested, `K(𝕂)` is exactly conserved by molding and
consolidation, changes only under growth, and the change is exactly the derived `dim ker(H−I)`,
confirmed two independent ways. Kill-Test 3 **survives**; it is not passed in full, because
pruning — the other half of §4's table — is not yet implemented.

## 5. Ledger (A17)

Deletes no hand-set number and adds none: the growth size `k_w` was already derived in V0, and this
gives it its first end-to-end measurement inside a wake/sleep loop. It earns its place under the
second clause of A17 rather than the first — it does not change a printed number, it **converts a
`[DERIVED]`/`[INFERRED]` identity claim into a `[MEASURED]` one**, which is what Phase 0 was for.
