"""
TATIANA — Expected Precision (Construction 3, layer 2 of the uncertainty stack).

THE CAPABILITY THIS BUYS
------------------------
coherence.rho answers "are my modules agreeing RIGHT NOW?".
This module answers the harder, meta question: "did I KNOW IN ADVANCE whether
they would agree?" — which is what lets the system say

    "I am confident that I do not know algebraic topology."

That sentence is not low confidence. It is a HIGH-confidence prediction of high
disagreement — exactly the distinction between aleatoric uncertainty (noise) and
EPISTEMIC uncertainty (ignorance of the model itself).

HOW — WITHOUT TRAINING ANYTHING
-------------------------------
No model is trained here, and no API is called. Every completed run already
produces one pair (query_embedding, actual rho). To predict rho for a NEW query,
take a similarity-weighted average of rho over its k nearest past queries in the
same 384-d embedding space we already build for free.

    "I don't know algebraic topology"
      == "queries near this one have historically produced high rho"

It costs nothing today and it silently gets better as history accumulates —
the slope-not-intercept thesis, made concrete.

COLD START IS REPORTED, NEVER GUESSED
-------------------------------------
With little or no history, predict() returns None (UNKNOWN). We do not
manufacture a number. That is the whole point of this project.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Sequence

DEFAULT_STORE = os.path.join(os.path.dirname(__file__), "precision_history.json")


class SelfKnowledge(str, Enum):
    """The confusion matrix for self-knowledge."""
    COMPETENCE = "competence"                  # predicted agree, did agree
    KNOWN_IGNORANCE = "known_ignorance"        # predicted disagree, did disagree  <- the prize
    HALLUCINATION_RISK = "hallucination_risk"  # predicted agree, DID NOT          <- alarm
    UNDERESTIMATED = "underestimated"          # predicted disagree, actually fine
    COLD_START = "cold_start"                  # not enough history to predict


@dataclass
class PrecisionAssessment:
    predicted_rho: Optional[float]
    actual_rho: Optional[float]
    verdict: SelfKnowledge
    calibration_error: Optional[float]   # |predicted - actual|
    n_neighbours: int

    def summary(self) -> str:
        p = "None" if self.predicted_rho is None else f"{self.predicted_rho:.3f}"
        a = "None" if self.actual_rho is None else f"{self.actual_rho:.3f}"
        err = "n/a" if self.calibration_error is None else f"{self.calibration_error:.3f}"
        return (f"predicted={p} actual={a} err={err} "
                f"neighbours={self.n_neighbours} -> {self.verdict.value}")


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


class PrecisionStore:
    """Persistent history of (query_embedding, observed rho) pairs."""

    def __init__(self, path: str = DEFAULT_STORE, min_neighbours: int = 3):
        self.path = path
        self.min_neighbours = min_neighbours
        self.entries: List[dict] = []
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as fh:
                    self.entries = json.load(fh)
            except (json.JSONDecodeError, OSError) as e:
                print(f"[PrecisionStore] Could not read history ({e}); starting empty.")
                self.entries = []

    def save(self) -> None:
        try:
            with open(self.path, "w", encoding="utf-8") as fh:
                json.dump(self.entries, fh)
        except OSError as e:
            print(f"[PrecisionStore] FAILED to persist history: {e}")

    def record(self, query_vec: Sequence[float], rho: Optional[float],
               label: str = "", persist: bool = True) -> None:
        """Log one completed run. rho=None (UNKNOWN) is NOT recorded: an
        undefined coherence teaches us nothing about expected coherence."""
        if rho is None:
            return
        self.entries.append({"v": [float(x) for x in query_vec],
                             "rho": float(rho),
                             "label": label})
        if persist:
            self.save()

    def predict(self, query_vec: Sequence[float], k: int = 5) -> tuple[Optional[float], int]:
        """Similarity-weighted k-NN estimate of rho. Returns (rho_hat, n_used).

        Returns (None, n) when history is too thin — cold start is reported,
        never guessed.
        """
        if len(self.entries) < self.min_neighbours:
            return None, len(self.entries)

        sims = [(_cosine(query_vec, e["v"]), e["rho"]) for e in self.entries]
        sims.sort(key=lambda t: t[0], reverse=True)
        top = sims[:k]

        # Only similarities above zero carry information about this query.
        weights = [max(s, 0.0) for s, _ in top]
        total = sum(weights)
        if total <= 0.0:
            return None, len(top)
        rho_hat = sum(w * r for w, (_, r) in zip(weights, top)) / total
        return rho_hat, len(top)

    def assess(self, query_vec: Sequence[float], actual_rho: Optional[float],
               threshold: float = 0.5, k: int = 5) -> PrecisionAssessment:
        """Compare prediction against outcome and classify the self-knowledge."""
        predicted, n = self.predict(query_vec, k=k)

        if predicted is None or actual_rho is None:
            return PrecisionAssessment(predicted, actual_rho,
                                       SelfKnowledge.COLD_START, None, n)

        pred_high = predicted > threshold
        act_high = actual_rho > threshold
        if not pred_high and not act_high:
            verdict = SelfKnowledge.COMPETENCE
        elif pred_high and act_high:
            verdict = SelfKnowledge.KNOWN_IGNORANCE
        elif not pred_high and act_high:
            verdict = SelfKnowledge.HALLUCINATION_RISK
        else:
            verdict = SelfKnowledge.UNDERESTIMATED

        return PrecisionAssessment(predicted, actual_rho, verdict,
                                   abs(predicted - actual_rho), n)


if __name__ == "__main__":
    import tempfile

    tmp = os.path.join(tempfile.gettempdir(), "tatiana_precision_selftest.json")
    if os.path.exists(tmp):
        os.remove(tmp)
    store = PrecisionStore(path=tmp)

    # Crude 4-d stand-ins for embeddings: axis 0 = "topology-ish", axis 1 = "algebra-ish"
    topo = [1.0, 0.0, 0.0, 0.0]
    alg = [0.0, 1.0, 0.0, 0.0]

    print("=== Cold start: no history ===")
    print("   ", store.assess(topo, 0.2).summary(), "<- must be COLD_START, not a guess")

    # History: topology queries always went badly; algebra queries always went well.
    for i in range(6):
        store.record([1.0, 0.05 * i, 0.0, 0.0], rho=0.85, label="topology", persist=False)
        store.record([0.05 * i, 1.0, 0.0, 0.0], rho=0.10, label="algebra", persist=False)

    print("\n=== After history ===")
    a = store.assess(topo, 0.88)
    print("    topology, went badly :", a.summary(), "<- KNOWN IGNORANCE ('I knew I don't know this')")
    b = store.assess(alg, 0.12)
    print("    algebra,  went well  :", b.summary(), "<- COMPETENCE")
    c = store.assess(alg, 0.91)
    print("    algebra, unexpectedly bad:", c.summary(), "<- HALLUCINATION RISK (alarm!)")

    if os.path.exists(tmp):
        os.remove(tmp)
