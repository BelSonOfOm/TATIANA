"""
E5, explained in the one quantity that makes it legible: THE LOOP SUM.

A 1-cochain eta is a GRADIENT (= a coboundary, = delta^0 f for some potential f)
IF AND ONLY IF its sum around every closed loop is zero. That is the whole of the
discrete Poincare lemma, and it is the honest translation of "H^1 has nothing to
find".

The E5 complex has exactly TWO independent loops:

    L1 = Reason -> Search -> Verify -> Reason      (the FILLED triangle)
         sum = eta_RS + eta_SV - eta_RV            -> failure here is CURL

    L2 = Reason -> Verify -> Context -> Reason     (the UNFILLED cycle)
         sum = eta_RV + eta_VC - eta_RC            -> failure here is HARMONIC

So the entire experiment reduces to: ARE THESE TWO NUMBERS NONZERO?

A nonzero loop sum is a Condorcet cycle among the organs: Verify pushes the claim
further than Reason, Context further than Verify, and Reason further than Context.
No single ranking of the organs can explain that. A zero loop sum means the organs
CAN be consistently ordered, one number each, and then there is no obstruction --
nothing for the growth law to aim at.

This script prints the loop sums for every recorded measurement, then works one
gradient case and one harmonic case all the way through by hand.
"""

from __future__ import annotations

import json
import numpy as np

import console
import hodge
from experiment_e5 import e5_complex, QUESTIONS, Elicitation

console.setup()

CX = e5_complex()
IDX = {e: i for i, e in enumerate(CX.edges)}
R, S, V, C = "Reason", "Search", "Verify", "Context"

# (edge, sign) lists for the two independent loops
L1 = [((R, S), +1), ((S, V), +1), ((R, V), -1)]      # filled triangle
L2 = [((R, V), +1), ((V, C), +1), ((R, C), -1)]      # unfilled cycle


def loop_sum(eta, loop):
    return float(sum(sgn * eta[IDX[e]] for e, sgn in loop))


def load():
    out = []
    by_qid = {q.qid: q for q in QUESTIONS}
    for line in open("e5_elicitations.jsonl", encoding="utf-8"):
        rec = json.loads(line)
        if "pairs" not in rec:
            continue
        push = {(p["u"], p["v"]): (float(p["push_u"]), float(p["push_v"]))
                for p in rec["pairs"]}
        conf = {(p["u"], p["v"]): float(p.get("confidence") or 0.0) for p in rec["pairs"]}
        claim = {(p["u"], p["v"]): p.get("sub_claim", "") for p in rec["pairs"]}
        el = Elicitation(rec["qid"], int(rec["repeat"]), "", push, conf, claim,
                         rec.get("positions") or {})
        eta, pi = el.to_cochain(CX)
        if np.sum(eta ** 2) <= 1e-12:
            continue
        out.append((by_qid[rec["qid"]], el, eta, pi))
    return out


rows = load()

print("=" * 79)
print("PART 1 - THE TWO LOOP SUMS, FOR EVERY MEASUREMENT")
print("=" * 79)
print("A gradient has BOTH loop sums = 0. That is the definition, not an approximation.")
print()
print(f"{'question':16s} {'r':>2s} {'||eta||':>8s} {'L1 filled':>10s} {'L2 unfilled':>12s} "
      f"{'|L1|+|L2|':>10s}  {'as % of ||eta||':>15s}")
print("-" * 79)
for q, el, eta, pi in rows:
    a, b = loop_sum(eta, L1), loop_sum(eta, L2)
    n = float(np.linalg.norm(eta))
    print(f"{q.qid:16s} {el.repeat:2d} {n:8.3f} {a:10.3f} {b:12.3f} "
          f"{abs(a) + abs(b):10.3f}  {100 * (abs(a) + abs(b)) / n:14.1f}%")

print()
print("READ THIS COLUMN: L2 is the one that matters. It is the sum around the")
print("UNFILLED cycle, and it is the ONLY thing in this complex that can carry a")
print("growth address. When it is ~0, the growth law has nothing to fire at.")

print()
print("=" * 79)
print("PART 2 - A GRADIENT CASE, WORKED BY HAND")
print("=" * 79)
# pick the most gradient-like measurement
best = min(rows, key=lambda t: hodge.hodge_split(CX, t[2], precision=t[3]).phi_ratio)
q, el, eta, pi = best
sp = hodge.hodge_split(CX, eta, precision=pi)
print(f"{q.qid} repeat {el.repeat}   (the most gradient-like measurement recorded)")
print()
print("the organs' pushes, pair by pair:")
for e in CX.edges:
    pu, pv = el.push[e]
    print(f"   {e[0]:8s} {pu:+.2f}   vs   {e[1]:8s} {pv:+.2f}    "
          f"eta = {pv - pu:+.2f}    on '{el.sub_claim[e]}'")
print()
print(f"   loop L1 (filled)   = {loop_sum(eta, L1):+.4f}")
print(f"   loop L2 (unfilled) = {loop_sum(eta, L2):+.4f}")
print("   both ~0  =>  a single number per organ explains all five comparisons.")
print()
print("   the fitted potential f (one number per organ, up to a constant):")
for v, val in zip(CX.vertices, sp.potential):
    print(f"      f({v:8s}) = {val:+.3f}")
print()
print("   check: does f(v) - f(u) reproduce the measured eta?")
d0 = CX.delta0()
pred = d0 @ sp.potential
for i, e in enumerate(CX.edges):
    print(f"      {str(e):32s} measured {eta[i]:+.3f}   from f {pred[i]:+.3f}   "
          f"error {eta[i] - pred[i]:+.3f}")
print(f"\n   {sp.report('gradient case')}")
print("   => the organs are simply RANKED. There is no contradiction to localise.")

print()
print("=" * 79)
print("PART 3 - THE ONE HARMONIC CASE, WORKED BY HAND")
print("=" * 79)
worst = max(rows, key=lambda t: hodge.hodge_split(CX, t[2], precision=t[3]).harm2 /
            hodge.hodge_split(CX, t[2], precision=t[3]).norm2)
q, el, eta, pi = worst
sp = hodge.hodge_split(CX, eta, precision=pi)
print(f"{q.qid} repeat {el.repeat}   (the only measurement with real harmonic mass)")
print()
for e in CX.edges:
    pu, pv = el.push[e]
    print(f"   {e[0]:8s} {pu:+.2f}   vs   {e[1]:8s} {pv:+.2f}    "
          f"eta = {pv - pu:+.2f}    on '{el.sub_claim[e]}'")
print()
a, b = loop_sum(eta, L1), loop_sum(eta, L2)
print(f"   loop L1 (filled)   = {a:+.4f}")
print(f"   loop L2 (unfilled) = {b:+.4f}   <-- THIS is the obstruction")
print()
print("   spelling L2 out as a Condorcet cycle:")
print(f"      Verify  pushes its claim with Reason  {eta[IDX[(R, V)]]:+.2f} further than Reason")
print(f"      Context pushes its claim with Verify  {eta[IDX[(V, C)]]:+.2f} further than Verify")
print(f"      Reason  pushes its claim with Context {-eta[IDX[(R, C)]]:+.2f} further than Context")
print(f"      going round the loop you gain {b:+.2f} instead of returning to 0.")
print("      No ranking of the three organs can produce that.")
print()
print("   the best-fit potential, and what it CANNOT explain:")
pred = d0 @ sp.potential
for i, e in enumerate(CX.edges):
    print(f"      {str(e):32s} measured {eta[i]:+.3f}   from f {pred[i]:+.3f}   "
          f"UNEXPLAINED {eta[i] - pred[i]:+.3f}")
print(f"\n   {sp.report('harmonic case')}")
print("   harmonic support (where the growth law would attach a cell):")
for e, val in sp.harmonic_support(3):
    print(f"      {str(e):32s} {val:+.3f}")

print()
print("=" * 79)
print("PART 4 - WHY THE BASELINE IS 0.400 AND NOT 0")
print("=" * 79)
print("eta lives in a 5-dimensional space (one number per edge). That space splits")
print("into three orthogonal pieces, of dimensions 3 + 1 + 1:")
print("     gradient  3 dims   (4 organs, minus 1 for the additive constant)")
print("     curl      1 dim    (one filled triangle)")
print("     harmonic  1 dim    (one unfilled cycle)")
print()
print("Project a RANDOM vector onto orthogonal subspaces and the energy splits in")
print("proportion to dimension. So pure noise scores grad 3/5, curl 1/5, harm 1/5:")
rg = np.random.default_rng(3)
fr = np.array([hodge.hodge_split(CX, rg.normal(size=5)).frac for _ in range(30000)])
print(f"     30000 random etas: grad={fr[:,0].mean():.3f} curl={fr[:,1].mean():.3f} "
      f"harm={fr[:,2].mean():.3f}   -> non-gradient {fr[:,1:].sum(1).mean():.3f}")
print()
obs = [sum(hodge.hodge_split(CX, e, precision=p).frac[1:]) for q, el, e, p in rows
       if q.kind == "contested"]
print(f"     our contested measurements:                        -> non-gradient "
      f"{np.mean(obs):.3f}")
print()
print("So the measured judgements are not merely 'not very harmonic'. They are")
print("MORE CONSISTENT THAN RANDOM NUMBERS WOULD BE - about half the non-gradient")
print("content you would get by rolling dice. That is a positive finding about the")
print("organs, and it is the finding that kills the growth law as currently stated.")
