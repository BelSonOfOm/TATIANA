"""
TATIANA - Selectionism (plan 5p, mechanism (4): Edelman / neural Darwinism).

When the system is STUCK at an obstruction (a persistent guilty edge), the
search-controller generates a POPULATION of candidate mediating cells - k aimed
LLM samples (or k paraphrase-perturbations for cheap variance) - and selection
keeps the survivors. This file is the selection operator: variation happens
upstream (costs Groq, budget-gated), selection here is free.

THE FITNESS ORDER (this encodes the rho-vs-truth distinction, load-bearing)
---------------------------------------------------------------------------
    1. REFUTED candidates are DISCARDED, always. A mediator the oracle proved
       false must never enter the scaffold, no matter how much it lowered discord.
    2. VERIFIED beats UNVERIFIABLE. A candidate the oracle CONFIRMED is
       promotable EVEN IF it raised discord (delta_rho >= 0): a true fact SHOULD
       increase disagreement with a wrong organ. Truth trumps coherence.
    3. Within a tier, the biggest discord DROP (most negative delta_rho) wins.
    4. An UNVERIFIABLE candidate is promotable ONLY if it reduced discord
       (delta_rho < 0) - a weak, revocable promotion, since coherence is the only
       (and fallible) evidence we have. delta_rho ALONE never promotes past a
       verification we could have done. This is the guard against a
       coherent-but-wrong mediator being crystallised as truth.

delta_rho = rho_after_injecting_this_candidate - rho_before  (negative == good).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

VERIFIED = "VERIFIED"
REFUTED = "REFUTED"
UNVERIFIABLE = "UNVERIFIABLE"

_TIER = {VERIFIED: 2, UNVERIFIABLE: 1, REFUTED: 0}


@dataclass
class Candidate:
    """One structural variant proposed under obstruction."""
    payload: str                 # the mediating concept/axiom the LLM produced
    delta_rho: float             # rho_after - rho_before  (negative == reduced discord)
    verify: str                  # VERIFIED | REFUTED | UNVERIFIABLE
    source: str = ""             # provenance (which sample / perturbation)

    def __post_init__(self):
        if self.verify not in _TIER:
            raise ValueError(f"unknown verify outcome {self.verify!r}; "
                             f"expected one of {sorted(_TIER)}")


@dataclass
class Selection:
    winner: Optional[Candidate]
    reason: str


def select_best(candidates: List[Candidate]) -> Selection:
    """Pick the survivor to promote, or None with a reason if none qualifies."""
    if not candidates:
        return Selection(None, "no candidates were generated")

    survivors = [c for c in candidates if c.verify != REFUTED]
    n_refuted = len(candidates) - len(survivors)
    if not survivors:
        return Selection(None, f"all {len(candidates)} candidates were REFUTED by the oracle")

    # sort: tier desc, then delta_rho asc (most negative = biggest discord drop)
    survivors.sort(key=lambda c: (-_TIER[c.verify], c.delta_rho))
    best = survivors[0]

    if best.verify == VERIFIED:
        why = (f"VERIFIED by oracle (delta_rho={best.delta_rho:+.4f}); "
               "truth is promoted even if it raised discord")
        return Selection(best, why)

    # best is UNVERIFIABLE: promote only if it actually reduced discord
    if best.delta_rho < 0:
        why = (f"UNVERIFIABLE but reduced discord (delta_rho={best.delta_rho:+.4f}); "
               "weak, revocable promotion - coherence is the only evidence")
        return Selection(best, why)

    return Selection(None,
                     f"best candidate is UNVERIFIABLE and did not reduce discord "
                     f"(delta_rho={best.delta_rho:+.4f}); refusing to crystallise a "
                     f"coherent-but-unproven mediator ({n_refuted} others were refuted)")


if __name__ == "__main__":
    print("=== 1. A REFUTED candidate is never chosen, even if it slashed discord ===")
    sel = select_best([
        Candidate("false but tidy", delta_rho=-0.90, verify=REFUTED),
        Candidate("true, modest", delta_rho=-0.05, verify=VERIFIED),
    ])
    assert sel.winner is not None and sel.winner.payload == "true, modest"
    print("   ", sel.reason)

    print("\n=== 2. VERIFIED truth wins even when it RAISED discord ===")
    sel = select_best([
        Candidate("coherent guess", delta_rho=-0.20, verify=UNVERIFIABLE),
        Candidate("hard truth", delta_rho=+0.10, verify=VERIFIED),
    ])
    assert sel.winner.payload == "hard truth"
    print("   ", sel.reason)

    print("\n=== 3. Among VERIFIED, biggest discord drop wins ===")
    sel = select_best([
        Candidate("true A", delta_rho=-0.02, verify=VERIFIED),
        Candidate("true B", delta_rho=-0.30, verify=VERIFIED),
    ])
    assert sel.winner.payload == "true B"
    print("   ", sel.reason)

    print("\n=== 4. UNVERIFIABLE + did-not-help => refuse to promote ===")
    sel = select_best([
        Candidate("neither proven nor helpful", delta_rho=+0.03, verify=UNVERIFIABLE),
    ])
    assert sel.winner is None
    print("   ", sel.reason)

    print("\n=== 5. UNVERIFIABLE but reduced discord => weak promotion ===")
    sel = select_best([
        Candidate("plausible, lowered discord", delta_rho=-0.12, verify=UNVERIFIABLE),
    ])
    assert sel.winner is not None
    print("   ", sel.reason)

    print("\n=== 6. all refuted => nothing, and say so ===")
    sel = select_best([
        Candidate("x", -0.5, REFUTED), Candidate("y", -0.3, REFUTED),
    ])
    assert sel.winner is None and "REFUTED" in sel.reason
    print("   ", sel.reason)

    print("\nALL SELECTION SELF-TESTS PASSED")
