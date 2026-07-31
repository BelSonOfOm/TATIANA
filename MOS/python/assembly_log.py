"""
TATIANA — E7: record assembly AT COMPOSITION TIME, because it is unrecoverable later.

WHY THIS EXISTS, AND WHY ITS STATED PURPOSE CHANGED
---------------------------------------------------
E7 was specified (audit 3.3, book 48.3 item 5) as "record Ext^1 data when
composites are assembled". **That purpose is dead**: F10 is dissolved (logbook
5aa/5af), the K_0 / Jordan-Holder / Ext^1 memory schema is dropped, and there is
no longer any category in which to take an Ext group. Building an Ext recorder
now would be building for a theory we retired.

What survives, and is in fact the stronger reason, is the *instruction*:

    "record the raw assembly, decide what it means afterwards"
    "cheap now and impossible later"

because MOS's memory is **history-determined by construction** (the whole basis
for rejecting both FCA and canonical K_0 schemas). Two live mechanisms consume
assembly history and neither can reconstruct it after the fact:

  1. **delta-D promotion (Construction 3).** "A microneuron is a promoted operad
     sub-tree: when a composite DAG repeatedly resolves conflicts it is promoted
     from composite to first-class GENERATOR." That requires knowing which
     composites RECURRED and whether they actually resolved conflict. Both are
     composition-time facts.
  2. **Q(t) and Lambda(t).** Wiring-change and compression curves are time series;
     a gap in the series is permanent.

So this module records composition events, not extension classes. The
interpretation is deliberately left open, exactly as E7 instructed.

THE IDENTITY PROBLEM, AND WHY THE SIGNATURE IS A COMPLETE INVARIANT
--------------------------------------------------------------------
"Did this composite recur?" is only well-posed if composites have a well-defined
identity. Comparing DAGs is graph isomorphism in general, but ours are tiny and
TYPED, which collapses the difficulty: we serialise the dependency structure in a
canonical order obtained by topological sort with ties broken deterministically
on (op_type, sorted support).

That signature is a COMPLETE invariant for our purposes: two composites share a
signature exactly when they agree on every node's (type, support) AND on every
dependency edge between them -- which is precisely what it means to be the same
composite. Tie-breaking cannot conflate two genuinely different DAGs, because the
dependency edges are part of what is serialised, not just the node multiset.

APPEND-ONLY, AND WHY
--------------------
The file is opened in append mode and never rewritten. A consolidation pass may
later summarise it, but the raw record is the thing E7 says is unrecoverable, so
nothing in this module deletes or edits a past line. Same discipline as
e5_elicitations.jsonl, which already paid off once when E5's verdict thresholds
had to be replaced and the data could be re-scored at zero API cost (5v).
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "assembly_events.jsonl")


@dataclass(frozen=True)
class NodeRecord:
    """One operator occurrence inside a composite."""
    op_type: str
    support: Tuple[int, ...]          # sorted; () means global
    read_only: bool

    def key(self) -> Tuple[str, Tuple[int, ...], bool]:
        return (self.op_type, self.support, self.read_only)


@dataclass
class AssemblyEvent:
    """One composition, recorded when it is assembled -- not when it is judged.

    `rho_before` is known at assembly time. `rho_after`, `verified` and
    `delta_rho` are filled in by `close()` once the composite has run; an event
    that never closes is recorded as incomplete rather than silently dropped,
    because "we assembled this and never learned the outcome" is itself data.
    """
    signature: str
    nodes: List[NodeRecord]
    edges: List[Tuple[int, int]]      # dependency (parent_idx, child_idx)
    slices: List[List[int]]           # foliation: node indices per slice
    tick: int
    wall_time: float
    rho_before: Optional[float] = None
    rho_after: Optional[float] = None
    verified: Optional[str] = None    # "VERIFIED" | "REFUTED" | "UNVERIFIABLE"
    closed: bool = False
    note: str = ""

    @property
    def delta_rho(self) -> Optional[float]:
        if self.rho_before is None or self.rho_after is None:
            return None
        return self.rho_after - self.rho_before

    def to_json(self) -> Dict:
        d = asdict(self)
        d["nodes"] = [{"op_type": n.op_type,
                       "support": list(n.support),
                       "read_only": n.read_only} for n in self.nodes]
        d["edges"] = [list(e) for e in self.edges]
        d["delta_rho"] = self.delta_rho
        return d


def canonical_signature(nodes: Sequence[NodeRecord],
                        edges: Sequence[Tuple[int, int]]) -> str:
    """A complete, order-independent invariant of the composite's structure.

    Topological sort with deterministic tie-breaking on (op_type, support,
    read_only), then serialise nodes AND the dependency edges rewritten in the
    canonical index space. Raises on a cycle -- an operad DAG with a cycle is a
    bug worth surfacing, not something to serialise around.
    """
    n = len(nodes)
    children: Dict[int, List[int]] = {i: [] for i in range(n)}
    indeg = [0] * n
    for (p, c) in edges:
        if not (0 <= p < n and 0 <= c < n):
            raise ValueError(f"dependency ({p},{c}) out of range for {n} nodes")
        children[p].append(c)
        indeg[c] += 1

    ready = sorted((i for i in range(n) if indeg[i] == 0),
                   key=lambda i: nodes[i].key())
    order: List[int] = []
    while ready:
        i = ready.pop(0)
        order.append(i)
        for c in children[i]:
            indeg[c] -= 1
            if indeg[c] == 0:
                ready.append(c)
        ready.sort(key=lambda j: nodes[j].key())

    if len(order) != n:
        raise ValueError("composite DAG contains a cycle; refusing to sign it")

    pos = {orig: k for k, orig in enumerate(order)}
    node_part = "|".join(
        f"{nodes[i].op_type}:{','.join(map(str, nodes[i].support))}"
        f":{'r' if nodes[i].read_only else 'w'}" for i in order)
    edge_part = ";".join(sorted(f"{pos[p]}>{pos[c]}" for (p, c) in edges))
    return f"{node_part}#{edge_part}"


class AssemblyLog:
    """Append-only recorder. Nothing here rewrites or deletes a past line."""

    def __init__(self, path: str = DEFAULT_PATH):
        self.path = path
        self._open: Dict[int, AssemblyEvent] = {}
        self._next_handle = 0

    def record(self,
               nodes: Sequence[NodeRecord],
               edges: Sequence[Tuple[int, int]],
               slices: Sequence[Sequence[int]],
               tick: int,
               rho_before: Optional[float] = None,
               note: str = "") -> int:
        """Record a composition AT ASSEMBLY TIME. Returns a handle for close()."""
        ev = AssemblyEvent(
            signature=canonical_signature(nodes, edges),
            nodes=list(nodes),
            edges=[tuple(e) for e in edges],
            slices=[list(s) for s in slices],
            tick=tick,
            wall_time=time.time(),
            rho_before=rho_before,
            note=note,
        )
        h = self._next_handle
        self._next_handle += 1
        self._open[h] = ev
        return h

    def close(self, handle: int,
              rho_after: Optional[float] = None,
              verified: Optional[str] = None) -> AssemblyEvent:
        """Fill in the outcome and flush the event to disk."""
        if handle not in self._open:
            raise KeyError(f"unknown assembly handle {handle}")
        ev = self._open.pop(handle)
        ev.rho_after = rho_after
        ev.verified = verified
        ev.closed = True
        self._flush(ev)
        return ev

    def abandon(self, handle: int, note: str = "abandoned") -> AssemblyEvent:
        """Flush an event whose outcome was never learned.

        Recorded as closed=False. "We assembled this and never found out" is a
        fact about the run, and dropping it would bias any later analysis toward
        composites that happened to finish.
        """
        if handle not in self._open:
            raise KeyError(f"unknown assembly handle {handle}")
        ev = self._open.pop(handle)
        ev.note = (ev.note + " | " + note).strip(" |")
        self._flush(ev)
        return ev

    def _flush(self, ev: AssemblyEvent) -> None:
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(ev.to_json(), sort_keys=True) + "\n")

    # -- read side: what delta-D promotion will actually ask -------------------

    @staticmethod
    def load(path: str = DEFAULT_PATH) -> List[Dict]:
        if not os.path.exists(path):
            return []
        out: List[Dict] = []
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    @staticmethod
    def recurrence(events: Iterable[Dict]) -> Dict[str, int]:
        """signature -> how many times that composite has been assembled."""
        counts: Dict[str, int] = {}
        for e in events:
            counts[e["signature"]] = counts.get(e["signature"], 0) + 1
        return counts

    @staticmethod
    def promotion_evidence(events: Iterable[Dict]) -> Dict[str, Dict]:
        """Per signature: the evidence Construction 3's promotion gate needs.

        Deliberately returns EVIDENCE, not a decision. Per selection.py's rule,
        delta_rho alone must never promote (coherent-but-wrong), so the verify
        tallies are reported separately and the caller applies the gate.
        """
        acc: Dict[str, Dict] = {}
        for e in events:
            s = acc.setdefault(e["signature"], {
                "assembled": 0, "closed": 0, "verified": 0, "refuted": 0,
                "unverifiable": 0, "delta_rhos": []})
            s["assembled"] += 1
            if e.get("closed"):
                s["closed"] += 1
            v = e.get("verified")
            if v == "VERIFIED":
                s["verified"] += 1
            elif v == "REFUTED":
                s["refuted"] += 1
            elif v == "UNVERIFIABLE":
                s["unverifiable"] += 1
            if e.get("delta_rho") is not None:
                s["delta_rhos"].append(e["delta_rho"])
        return acc


# ---------------------------------------------------------------------------
# Self-tests. Run: python assembly_log.py
# ---------------------------------------------------------------------------

def _main() -> None:
    import tempfile

    ok = 0

    def check(name: str, cond: bool) -> None:
        nonlocal ok
        assert cond, f"FAILED: {name}"
        ok += 1
        print(f"  [ok] {name}")

    print("=== E7: assembly recording ===")

    A = NodeRecord("SearchOp", (), True)
    B = NodeRecord("ReasonOp", (1,), False)
    C = NodeRecord("VerifyOp", (2,), False)

    # 1. The signature is order-independent -- the same composite described with
    #    its nodes listed differently must sign identically, or "did this recur?"
    #    is meaningless.
    s1 = canonical_signature([A, B, C], [(0, 1), (1, 2)])
    s2 = canonical_signature([C, B, A], [(2, 1), (1, 0)])
    check("signature is independent of node listing order", s1 == s2)

    # 2. ... but it is NOT blind to structure: same nodes, different dependency
    #    edges must sign differently.
    s3 = canonical_signature([A, B, C], [(0, 1), (0, 2)])
    check("different dependency structure signs differently", s1 != s3)

    # 3. ... nor to support or type.
    s4 = canonical_signature([A, NodeRecord("ReasonOp", (9,), False), C],
                             [(0, 1), (1, 2)])
    check("different support signs differently", s1 != s4)
    s5 = canonical_signature([A, NodeRecord("ComputeOp", (1,), False), C],
                             [(0, 1), (1, 2)])
    check("different op type signs differently", s1 != s5)

    # 4. A cycle is a bug, not something to serialise around.
    try:
        canonical_signature([A, B], [(0, 1), (1, 0)])
        raise AssertionError("FAILED: cycle was not rejected")
    except ValueError:
        ok += 1
        print("  [ok] a cyclic 'DAG' is refused rather than signed")

    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "assembly.jsonl")
        log = AssemblyLog(path)

        # 5. Record at assembly time, close at outcome time.
        h = log.record([A, B, C], [(0, 1), (1, 2)], [[0], [1], [2]],
                       tick=1, rho_before=0.40)
        check("nothing is written before the outcome is known",
              not os.path.exists(path) or len(AssemblyLog.load(path)) == 0)
        ev = log.close(h, rho_after=0.12, verified="VERIFIED")
        check("delta_rho is computed, not stored twice",
              abs(ev.delta_rho - (0.12 - 0.40)) < 1e-12)
        check("one line on disk after close", len(AssemblyLog.load(path)) == 1)

        # 6. An abandoned composite is still recorded. Dropping it would bias
        #    later analysis toward composites that happened to finish.
        h2 = log.record([A, B], [(0, 1)], [[0, 1]], tick=2, rho_before=0.5)
        log.abandon(h2, "engine crashed")
        rows = AssemblyLog.load(path)
        check("an abandoned composite is recorded as closed=False",
              len(rows) == 2 and rows[1]["closed"] is False)
        check("and its delta_rho is None, not 0.0",
              rows[1]["delta_rho"] is None)

        # 7. Append-only: an existing file is added to, never rewritten.
        log2 = AssemblyLog(path)
        h3 = log2.record([A, B, C], [(0, 1), (1, 2)], [[0], [1], [2]],
                         tick=3, rho_before=0.33)
        log2.close(h3, rho_after=0.30, verified="UNVERIFIABLE")
        rows = AssemblyLog.load(path)
        check("a new AssemblyLog appends rather than truncating", len(rows) == 3)

        # 8. Recurrence -- the delta-D question. The tick-1 and tick-3 composites
        #    are structurally identical and must be counted together.
        counts = AssemblyLog.recurrence(rows)
        check("the recurring composite is counted twice", counts[s1] == 2)
        check("the one-off composite is counted once",
              sum(v for k, v in counts.items() if k != s1) == 1)

        # 9. Promotion EVIDENCE, not a promotion decision.
        ev_map = AssemblyLog.promotion_evidence(rows)
        e1 = ev_map[s1]
        check("verify outcomes are tallied separately from delta_rho",
              e1["verified"] == 1 and e1["unverifiable"] == 1
              and e1["refuted"] == 0)
        check("both delta_rhos are retained for the caller to gate on",
              len(e1["delta_rhos"]) == 2)

        # 10. Unknown handles are errors, not silent no-ops.
        try:
            log.close(999)
            raise AssertionError("FAILED: unknown handle accepted")
        except KeyError:
            ok += 1
            print("  [ok] closing an unknown handle raises")

    print(f"\nAll {ok} assembly-log tests passed.")


if __name__ == "__main__":
    _main()
