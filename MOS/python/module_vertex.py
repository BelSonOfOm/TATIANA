"""
TATIANA — ModuleVertex: the migration substrate (Phase 5 / D3).

This is what "the Python scripts become subcomplexes of the OS" actually means.

A legacy script does not get rewritten; it gets COORDINATES. Each module becomes a
vertex of the coarse complex K, carrying:

  * a STALK  F(v) in R^384  - its current position in meaning-space, obtained by
                              coarse-graining its own fine complex of concepts
                              via pi_v (v1 = weight-weighted centroid)
  * OPERATORS it induces    - the actions it contributes to the algebra D
  * a fine complex          - the concepts it is actively holding

Bound pairs of modules are the 1-simplices of K. Their coupling weight w(sigma,t)
rises on co-activation (Hebbian: fire together -> wire together) and decays when
idle; crossing thresholds triggers bind/collapse. That is learning-as-topology.

The discord rho over K is then computed by coherence.py, and the whole thing can
be watched evolving with visualize.py.

WHY A CENTROID FOR pi_v
-----------------------
Construction 2 fixes pi_v as the weighted centroid of a module's active concept
embeddings. It is the cheapest honest summary that lives in the SAME space as
every other module's summary, which is exactly what makes cross-module distance
meaningful. It is deliberately v1: the top principal component is the upgrade
path, and we only take it if implementation forces it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from coherence import CoherenceReport, coherence
from embeddings import EMBED_DIM
from predictive_coding import RestrictionMapLearner

Edge = Tuple[str, str]


@dataclass
class Concept:
    """One element of a module's FINE complex."""
    label: str
    vector: np.ndarray
    weight: float = 1.0


class ModuleVertex(ABC):
    """A cognitive organ occupying one vertex of the coarse complex K."""

    def __init__(self, name: str):
        self.name = name
        self._concepts: List[Concept] = []

    # --- the fine level -----------------------------------------------------
    def hold(self, label: str, vector: Sequence[float], weight: float = 1.0) -> None:
        """Bring a concept into this module's active fine complex."""
        v = np.asarray(vector, dtype=float).ravel()
        if v.size != EMBED_DIM:
            raise ValueError(
                f"{self.name}: concept '{label}' has dim {v.size}, expected {EMBED_DIM}. "
                "Refusing to pad or truncate.")
        self._concepts.append(Concept(label, v, weight))

    def release(self) -> None:
        """Drop the active concepts (end of a reasoning turn)."""
        self._concepts.clear()

    @property
    def concepts(self) -> List[Concept]:
        return list(self._concepts)

    # --- the coarse-graining map pi_v ---------------------------------------
    def stalk(self) -> Optional[np.ndarray]:
        """pi_v : fine complex -> F(v) in R^384. None when the module is idle.

        Returning None (rather than a zero vector) is deliberate: an idle module
        has no position, and a zero vector would silently drag every distance
        toward the origin and fake a measurement.
        """
        if not self._concepts:
            return None
        W = np.array([c.weight for c in self._concepts], dtype=float)
        if W.sum() <= 0:
            return None
        M = np.stack([c.vector for c in self._concepts])
        return (W[:, None] * M).sum(axis=0) / W.sum()

    def stalk_gaussian(self, prior_factor: Optional[np.ndarray] = None,
                       kappa: float = 1.0,
                       rank: Optional[int] = None) -> Optional["belief.Gaussian"]:
        """pi_v upgraded: the organ's PRIOR as a Gaussian, not just a point.

        Same mean as stalk() by construction, plus a low-rank covariance read off
        the spread of the concepts this organ is actually holding -- a tight
        cluster is a focused organ, a scattered one is a vague organ.

        This is a PRIOR, not the organ's uncertainty. The uncertainty the system
        actually has about x_v is the posterior marginal [Lambda^-1]_vv, which
        depends on the whole complex (see belief.SystemBelief). Computing a local
        covariance and stopping would be a local estimate wearing sheaf
        vocabulary.

        Kept SEPARATE from stalk() rather than replacing it: stalk() is byte-for-
        byte load-bearing for the C++ parity test (logbook 5j) and for the ρ
        calibration in 5h.
        """
        import belief
        if not self._concepts:
            return None
        return belief.stalk_gaussian(
            [c.vector for c in self._concepts],
            [c.weight for c in self._concepts],
            prior_factor=prior_factor, kappa=kappa, rank=rank)

    # --- what this organ contributes to the algebra D -----------------------
    @abstractmethod
    def operators(self) -> List[str]:
        """Names of the operators this vertex induces (its share of D)."""

    def __repr__(self) -> str:
        return f"<{type(self).__name__} '{self.name}' concepts={len(self._concepts)}>"


class CoarseComplex:
    """The complex K: module-vertices plus their bound coalitions.

    Holds the weights w(sigma,t) and the typed structural operations. Note we use
    bind/collapse/split/merge — NOT "Pachner moves", which would borrow a
    manifold-preservation guarantee that does not transfer to this object.
    """

    def __init__(self, bind_threshold: float = 1.0, decay: float = 0.1):
        self.vertices: Dict[str, ModuleVertex] = {}
        self.weights: Dict[Edge, float] = {}
        self.bind_threshold = bind_threshold
        self.decay_rate = decay
        self.mutation_log: List[str] = []
        # --- 5p mechanism (1): predictive-coding restriction maps -----------
        # Cold start = identity + uniform precision => report() is byte-identical
        # to the pre-5p measure (calibration + C++ parity preserved). Flip these
        # on once the maps are trained / to weight discord by coalition strength.
        self.learner = RestrictionMapLearner(EMBED_DIM)
        self.use_learned_maps: bool = False
        self.use_precision: bool = False
        # pi_e, stored SEPARATELY from self.weights by contract (5ah). Missing
        # key => UNCALIBRATED => pi = 1. Mirrors CoarseComplex::precisions_.
        self.precisions: Dict[Edge, float] = {}

    # --- membership ---------------------------------------------------------
    def register(self, vertex: ModuleVertex) -> None:
        self.vertices[vertex.name] = vertex
        self.mutation_log.append(f"register {vertex.name}")

    @staticmethod
    def _key(u: str, v: str) -> Edge:
        return (u, v) if u <= v else (v, u)

    # --- Hebbian dynamics: fire together -> wire together -------------------
    def co_activate(self, u: str, v: str, amount: float = 0.5) -> None:
        """Reinforce a pair that just worked together."""
        if u == v or u not in self.vertices or v not in self.vertices:
            return
        k = self._key(u, v)
        was_bound = self.is_bound(*k)
        self.weights[k] = self.weights.get(k, 0.0) + amount
        if not was_bound and self.is_bound(*k):
            self.mutation_log.append(f"bind {k[0]}~{k[1]} (w={self.weights[k]:.2f})")

    def tick_decay(self) -> None:
        """Idle decay; coalitions that fall to zero collapse (garbage collection)."""
        for k in list(self.weights):
            was_bound = self.is_bound(*k)
            self.weights[k] -= self.decay_rate
            if self.weights[k] <= 0.0:
                del self.weights[k]
                if was_bound:
                    self.mutation_log.append(f"collapse {k[0]}~{k[1]}")
            elif was_bound and not self.is_bound(*k):
                self.mutation_log.append(f"unbind {k[0]}~{k[1]}")

    def is_bound(self, u: str, v: str) -> bool:
        return self.weights.get(self._key(u, v), 0.0) >= self.bind_threshold

    def edges(self) -> List[Edge]:
        """The 1-simplices: pairs whose coupling has crossed the bind threshold."""
        return [k for k, w in self.weights.items() if w >= self.bind_threshold]

    # --- the bridge to coherence -------------------------------------------
    def states(self) -> Dict[str, np.ndarray]:
        """Coarse-grained positions of every ACTIVE module (idle ones excluded)."""
        out = {}
        for name, vx in self.vertices.items():
            s = vx.stalk()
            if s is not None:
                out[name] = s
        return out

    def report(self) -> CoherenceReport:
        """Current discord over K. Edges touching idle modules are dropped, since
        a module with no position cannot meaningfully agree or disagree.

        With use_learned_maps / use_precision on, this is the precision-weighted
        predictive-coding free energy (5p mechanism 1); with both off (default)
        it is the identity-map graph-Laplacian discord, numerically unchanged."""
        st = self.states()
        live = [(u, v) for (u, v) in self.edges() if u in st and v in st]
        restriction = self.learner.as_restriction_dict(live) if self.use_learned_maps else None
        # 5ah: pi_e comes from `precisions`, NOT from `weights`. This line used to
        # read self.weights -- the Hebbian coupling -- which is the conflation
        # 5ac and 5af both ruled out: w(sigma,t) is a normalised bind indicator
        # on [0,1], pi_e is an unbounded inverse variance, and using the former
        # computes the free energy of a different operator than the one we print
        # rho from. An edge nobody calibrated is pi=1 (UNCALIBRATED), not
        # "as trusted as it is bound".
        precision = ({e: self.precisions.get(self._key(*e), 1.0) for e in live}
                     if self.use_precision else None)
        return coherence(st, live, restriction=restriction, precision=precision)

    def learn_coherent_pairs(self, max_edge_discord: float = 0.05) -> int:
        """Predictive-coding learning (5p mechanism 1): nudge the restriction maps
        toward agreement on currently-bound pairs that ALREADY roughly agree
        (per-edge discord <= max_edge_discord). Learning only from coherent pairs
        is deliberate - training on a contradiction would teach the maps to HIDE
        it. Precision = coupling weight (a more-bound coalition is trusted more).
        Returns the number of pairs learned from."""
        st = self.states()
        rep = self.report()
        n = 0
        for (u, v) in self.edges():
            if u not in st or v not in st:
                continue
            d = rep.per_edge.get((u, v), rep.per_edge.get((v, u)))
            if d is None or d > max_edge_discord:
                continue
            self.learner.update(u, v, st[u], st[v],
                                precision=self.weights[self._key(u, v)])
            n += 1
        return n

    def snapshot(self, label: str, note: str = ""):
        """A frame for visualize.render(). Imported lazily to keep this module
        usable in headless contexts."""
        from visualize import Snapshot
        st = self.states()
        live = [(u, v) for (u, v) in self.edges() if u in st and v in st]
        return Snapshot(label=label, states=st, edges=live, note=note)


if __name__ == "__main__":
    class Dummy(ModuleVertex):
        def operators(self):
            return ["noop"]

    rng = np.random.default_rng(3)
    base = rng.normal(size=EMBED_DIM)

    K = CoarseComplex(bind_threshold=1.0, decay=0.25)
    for n in ["Librarian", "Canonicalizer", "Curator", "WorkingMemory"]:
        K.register(Dummy(n))

    print("--- idle: no module holds anything ---")
    print("   ", K.report().summary(), " <- no positions at all")

    for n in K.vertices:
        K.vertices[n].hold(f"{n}-concept", base + rng.normal(scale=0.01, size=EMBED_DIM))
    print("\n--- active but unbound ---")
    print("   ", K.report().summary(), " <- UNKNOWN: nobody is talking")

    K.co_activate("Librarian", "Canonicalizer", 1.0)
    K.co_activate("Canonicalizer", "Curator", 1.0)
    print("\n--- after two binds ---")
    print("   ", K.report().summary())

    K.vertices["Curator"].release()
    K.vertices["Curator"].hold("contradiction", -base)
    print("\n--- Curator now disagrees sharply ---")
    r = K.report()
    print("   ", r.summary())
    print("    worst edge:", r.worst_edge())

    for _ in range(6):
        K.tick_decay()
    print("\n--- after idle decay ---")
    print("   ", K.report().summary())
    print("\nmutation log:")
    for m in K.mutation_log:
        print("   ", m)
