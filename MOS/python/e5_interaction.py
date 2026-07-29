"""
E5 STEP 0 - where the non-gradient content actually comes from. FREE, no API calls.

THE THEOREM THIS COMPUTES
-------------------------
The instrument records a push  p_u(e)  for each INCIDENCE (organ u, incident edge
e) -- 2|E| = 10 numbers. The cochain is eta_e = p_v(e) - p_u(e).

Decompose the push table the way one decomposes a two-way layout:

    p_u(e) = alpha_u + beta_e + gamma_u(e)
             organ     claim    INTERACTION

Then

    eta_e = (alpha_v - alpha_u) + (gamma_v(e) - gamma_u(e))
          =   (delta^0 alpha)_e  + (interaction contribution)

**beta_e cancels identically**, because both organs on an edge are scored against
the SAME sub-claim. The alpha term is a pure gradient. Therefore:

    the non-gradient content of eta = the non-gradient content of gamma, exactly.

Dimension check, which makes this an isomorphism and not just an inequality:
  incidences                       2|E|              = 10
  additive parameters              |V| + |E| - 1     =  8   (one redundancy:
                                                            alpha += c, beta -= c)
  interaction space                10 - 8            =  2
  non-gradient space of C^1        curl 1 + harm 1   =  2   <- same dimension

and the additive part maps ONTO the gradients while contributing nothing to the
non-gradient part, so

    gamma = 0   <=>   eta is a pure gradient.

An exact iff, in both directions. So "is the growth mechanism alive?" is literally
"is there an organ x claim interaction?" -- an ordinary, measurable quantity, not
a piece of topology one has to take on faith.

WHAT THIS SCRIPT ANSWERS
------------------------
Given the 15 recorded elicitations: was gamma small because the model produced an
ADDITIVE push table (each organ has one strength, each claim one difficulty), or
was gamma present but pointing mostly at curl rather than harmonic? Those are
different diagnoses with different fixes, and until now we could not tell them
apart.
"""

from __future__ import annotations

import json
import numpy as np

import console
import hodge
from experiment_e5 import e5_complex, QUESTIONS, Elicitation

console.setup()

CX = e5_complex()
EDGES = CX.edges
VERTS = CX.vertices
VI = {v: i for i, v in enumerate(VERTS)}
EI = {e: i for i, e in enumerate(EDGES)}
NV, NE = len(VERTS), len(EDGES)


def design_matrix():
    """Rows = incidences (u, e); columns = [alpha_1..alpha_V, beta_1..beta_E]."""
    rows, labels = [], []
    for e in EDGES:
        for u in e:
            r = np.zeros(NV + NE)
            r[VI[u]] = 1.0
            r[NV + EI[e]] = 1.0
            rows.append(r)
            labels.append((u, e))
    return np.array(rows), labels


A, LABELS = design_matrix()


def decompose(push):
    """Fit p = alpha + beta, return (alpha, beta, gamma, fractions)."""
    y = np.array([push[e][0 if u == e[0] else 1] for (u, e) in LABELS])
    theta, *_ = np.linalg.lstsq(A, y, rcond=None)
    fit = A @ theta
    gamma = y - fit
    alpha, beta = theta[:NV], theta[NV:]
    centred = y - y.mean()
    ss_tot = float(centred @ centred)
    ss_gam = float(gamma @ gamma)
    return alpha, beta, gamma, y, ss_gam, ss_tot


def load():
    by_qid = {q.qid: q for q in QUESTIONS}
    out = []
    for line in open("e5_elicitations.jsonl", encoding="utf-8"):
        rec = json.loads(line)
        if "pairs" not in rec:
            continue
        push = {(p["u"], p["v"]): (float(p["push_u"]), float(p["push_v"]))
                for p in rec["pairs"]}
        conf = {(p["u"], p["v"]): float(p.get("confidence") or 0.0) for p in rec["pairs"]}
        el = Elicitation(rec["qid"], int(rec["repeat"]), "", push, conf, {},
                         rec.get("positions") or {})
        eta, pi = el.to_cochain(CX)
        if np.sum(eta ** 2) <= 1e-12:
            continue
        out.append((by_qid[rec["qid"]], el, eta, pi, push))
    return out


print("=" * 79)
print("E5 STEP 0 - IS THERE AN ORGAN x CLAIM INTERACTION?")
print("=" * 79)
r = np.linalg.matrix_rank(A)
print(f"design matrix rank = {r} of {NV + NE} columns  =>  interaction space has "
      f"dimension {2 * NE - r}")
print(f"non-gradient space of C^1 has dimension "
      f"{NE - np.linalg.matrix_rank(CX.delta0())}")
print("equal, as the theorem requires: gamma = 0  <=>  eta is a pure gradient.\n")

rows = load()

# --- the exact iff, verified numerically on real data ---------------------
print("VERIFYING THE THEOREM ON THE RECORDED DATA")
print("  (non-gradient energy of eta) vs (non-gradient energy of the gamma part alone)")
worst = 0.0
for q, el, eta, pi, push in rows:
    alpha, beta, gamma, y, *_ = decompose(push)
    eta_gam = np.array([gamma[2 * EI[e] + 1] - gamma[2 * EI[e]] for e in EDGES])
    s_full = hodge.hodge_split(CX, eta)
    s_gam = hodge.hodge_split(CX, eta_gam)
    d = abs((s_full.curl2 + s_full.harm2) - (s_gam.curl2 + s_gam.harm2))
    worst = max(worst, d)
print(f"  max discrepancy over {len(rows)} measurements: {worst:.2e}  "
      f"({'exact' if worst < 1e-9 else 'NOT EXACT - investigate'})\n")

print("=" * 79)
print("THE DECOMPOSITION, MEASUREMENT BY MEASUREMENT")
print("=" * 79)
print(f"{'question':15s} {'r':>2s} {'organ%':>7s} {'claim%':>7s} {'INTERACT%':>10s} "
      f"{'non-grad':>9s} {'curl':>6s} {'harm':>6s}")
print("-" * 79)
agg = []
for q, el, eta, pi, push in rows:
    alpha, beta, gamma, y, ss_gam, ss_tot = decompose(push)
    # organ vs claim share of the ADDITIVE part
    a_eff = np.array([alpha[VI[u]] for (u, e) in LABELS])
    b_eff = np.array([beta[EI[e]] for (u, e) in LABELS])
    a_eff = a_eff - a_eff.mean()
    b_eff = b_eff - b_eff.mean()
    ss_a, ss_b = float(a_eff @ a_eff), float(b_eff @ b_eff)
    tot = max(ss_tot, 1e-12)
    s = hodge.hodge_split(CX, eta, precision=pi)
    g, c, h = s.frac
    print(f"{q.qid:15s} {el.repeat:2d} {100*ss_a/tot:6.1f}% {100*ss_b/tot:6.1f}% "
          f"{100*ss_gam/tot:9.1f}% {c+h:9.3f} {c:6.3f} {h:6.3f}")
    agg.append((q.kind, ss_a / tot, ss_b / tot, ss_gam / tot, c + h, h))

print("-" * 79)
arr = np.array([[a, b, g, n, h] for _, a, b, g, n, h in agg])
print(f"{'ALL':15s} {'':2s} {100*arr[:,0].mean():6.1f}% {100*arr[:,1].mean():6.1f}% "
      f"{100*arr[:,2].mean():9.1f}% {arr[:,3].mean():9.3f} {'':6s} {arr[:,4].mean():6.3f}")
con = np.array([[a, b, g, n, h] for k, a, b, g, n, h in agg if k == "contested"])
ctl = np.array([[a, b, g, n, h] for k, a, b, g, n, h in agg if k.startswith("control")])
print(f"{'contested':15s} {'':2s} {100*con[:,0].mean():6.1f}% {100*con[:,1].mean():6.1f}% "
      f"{100*con[:,2].mean():9.1f}% {con[:,3].mean():9.3f} {'':6s} {con[:,4].mean():6.3f}")
print(f"{'control':15s} {'':2s} {100*ctl[:,0].mean():6.1f}% {100*ctl[:,1].mean():6.1f}% "
      f"{100*ctl[:,2].mean():9.1f}% {ctl[:,3].mean():9.3f} {'':6s} {ctl[:,4].mean():6.3f}")

print()
print("=" * 79)
print("DIAGNOSIS")
print("=" * 79)
print("organ%     = the push table is explained by 'this organ is strong/weak'")
print("             -> contributes ONLY gradient. Cannot ever produce an obstruction.")
print("claim%     = explained by 'this sub-claim is easy/hard'")
print("             -> CANCELS ENTIRELY in eta. Contributes nothing at all.")
print("INTERACT%  = 'this organ bears on THIS claim differently than on that one'")
print("             -> the ONLY source of curl and harmonic mass. This is the number")
print("                the whole growth story depends on.")
print()
mi = arr[:, 2].mean()
print(f"Observed interaction share: {100*mi:.1f}% of push-table variance.")
if mi < 0.15:
    print("=> The model produced a very nearly ADDITIVE push table: each organ has one")
    print("   strength, each claim one difficulty. That is a POTENTIAL FUNCTION, and it")
    print("   is a pure gradient by the theorem above -- not by any property of organs.")
    print("   Cause (a)/(b) is confirmed as the operative one: the elicitation form")
    print("   invited a ranking and got one.")
