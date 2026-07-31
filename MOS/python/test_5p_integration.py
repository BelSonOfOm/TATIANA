"""
TATIANA - 5p integration test: the four computational-neuroscience mechanisms
running together on one scenario. This is the "see how it works" for plan 5p.

SCENARIO (deliberately the hard case for identity maps)
-------------------------------------------------------
Three organs, all unit-norm (as bge embeddings are):
  * Reason and Search hold the SAME underlying concept but in DIFFERENT frames
    (Search's vector is a fixed rotation Q of Reason's). They SHOULD be judged
    coherent - different representations of the same thing.
  * Verify holds a genuinely off-topic vector (a real disagreement).

Identity maps (pre-5p) cannot tell these apart: the rotated-but-same pair looks
just as conflicted as the truly-off-topic one. The predictive-coding maps learn
the rotation and collapse the FALSE conflict while leaving the REAL one - which
is the whole "quality of connection" thesis, made measurable.
"""

from __future__ import annotations

import numpy as np

from coherence import coherence, sheaf_diffusion
from plasticity import Homeostat, CriticalityMonitor
from predictive_coding import RestrictionMapLearner
from selection import Candidate, select_best

rng = np.random.default_rng(7)
D = 64  # smaller than 384 for a fast test; the math is dimension-agnostic


def unit(v):
    return v / np.linalg.norm(v)


# a fixed hidden relation: Search sees Reason's content rotated by Q
Q, _ = np.linalg.qr(rng.normal(size=(D, D)))

concept = unit(rng.normal(size=D))
reason = concept
search = Q @ concept                      # SAME content, rotated frame
verify = unit(rng.normal(size=D))         # genuinely different

states = {"Reason": reason, "Search": search, "Verify": verify}
edges = [("Reason", "Search"), ("Reason", "Verify")]

print("=" * 68)
print("MECHANISM (1) PREDICTIVE CODING - maps separate false vs real conflict")
print("=" * 68)
r0 = coherence(states, edges)
print("  identity maps (pre-5p):")
print("   ", r0.summary())
print(f"    Reason-Search discord = {r0.per_edge[('Reason','Search')]:.3f}  "
      f"(FALSE conflict: same content, rotated)")
print(f"    Reason-Verify discord = {r0.per_edge[('Reason','Verify')]:.3f}  "
      f"(REAL conflict: off-topic)")

# learn the maps ONLY on the coherent pair (Reason<->Search), many small steps
learner = RestrictionMapLearner(D, learning_rate=0.1)
for _ in range(150):
    learner.update("Reason", "Search", reason, search, precision=1.0)

r1 = coherence(states, edges, restriction=learner.as_restriction_dict(edges))
print("\n  after predictive-coding learns the Reason-Search relation:")
print("   ", r1.summary())
rs0, rs1 = r0.per_edge[("Reason", "Search")], r1.per_edge[("Reason", "Search")]
rv0, rv1 = r0.per_edge[("Reason", "Verify")], r1.per_edge[("Reason", "Verify")]
print(f"    Reason-Search discord {rs0:.3f} -> {rs1:.4f}   (false conflict COLLAPSED)")
print(f"    Reason-Verify discord {rv0:.3f} -> {rv1:.3f}   (real conflict SURVIVES)")
assert rs1 < 0.2 * rs0, "PC should collapse the false (rotational) conflict"
assert rv1 > 0.5 * rv0, "PC must NOT erase the genuine disagreement"
print("  => the maps encode 'quality of connection': rotated-same is now coherent,")
print("     off-topic is still flagged. Identity maps could not do this.")

print("\n" + "=" * 68)
print("MECHANISM (3) HOMEOSTAT - only SUSTAINED discord triggers growth")
print("=" * 68)
# Verify keeps disagreeing over several ticks; Reason-Search is now coherent.
h = Homeostat(setpoint=0.15, leak=0.3)
for tick in range(8):
    rep = coherence(states, edges, restriction=learner.as_restriction_dict(edges))
    h.observe(Homeostat.per_organ_discord(rep.per_edge))
print(f"  Verify integrated discord = {h.integral['Verify']:.3f} (setpoint {h.setpoint})")
print(f"  Search integrated discord = {h.integral['Search']:.3f}")
print("  organs flagged for growth (aim an attachment here):",
      h.organs_needing_growth())
assert "Verify" in h.organs_needing_growth()
assert "Search" not in h.organs_needing_growth()

print("\n" + "=" * 68)
print("MECHANISM (2) CRITICALITY - the RESOLVE gate auto-calibrates")
print("=" * 68)
mon = CriticalityMonitor(default_eps_rho=0.10, min_history=20)
print(f"  cold start: eps_rho = {mon.eps_rho():.3f} (documented default, no guess)")
for _ in range(300):
    mon.record_rho(float(abs(rng.normal(0.05, 0.02))))
print(f"  after 300 rho observations: eps_rho = {mon.eps_rho():.4f} "
      f"(75th percentile of observed discord)")

print("\n" + "=" * 68)
print("MECHANISM (4) SELECTIONISM - pick the survivor under obstruction")
print("=" * 68)
# The homeostat aimed growth at Verify. Suppose the search-controller generated
# 3 candidate mediators (k=3 variation). Selection keeps the right one.
cands = [
    Candidate("tidy but false reconciliation", delta_rho=-0.30, verify="REFUTED", source="sample-1"),
    Candidate("true, modestly helpful bridge", delta_rho=-0.08, verify="VERIFIED", source="sample-2"),
    Candidate("plausible unproven guess", delta_rho=-0.20, verify="UNVERIFIABLE", source="sample-3"),
]
sel = select_best(cands)
print(f"  winner: {sel.winner.source} -> \"{sel.winner.payload}\"")
print(f"  reason: {sel.reason}")
assert sel.winner.source == "sample-2", "must prefer VERIFIED truth over a bigger unproven discord drop"

print("\n" + "=" * 68)
print("BONUS: sheaf diffusion RECONCILES (role-2: structure computes a state)")
print("=" * 68)
recon, traj = sheaf_diffusion(states, edges,
                              restriction=learner.as_restriction_dict(edges),
                              dt=0.05, steps=400)
w0, w1 = traj[0], traj[-1]
print(f"  omega {w0:.3f} -> {w1:.4f} over {len(traj)} steps "
      f"(a reconciled state no single organ held)")
assert w1 <= w0

print("\n" + "=" * 68)
print("ALL FOUR MECHANISMS COMPOSED AND PASSED")
print("=" * 68)
