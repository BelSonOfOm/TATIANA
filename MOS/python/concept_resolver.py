"""P1 — the resolution layer at the Python/C++ boundary.

WHAT WAS BROKEN. `communicator.py` used to tell the planner:

    "'support' MUST be an array of integers (internal vertex ids) or omitted
     entirely. You do not know the internal vertex ids, so ALWAYS output []."

The planner knows concept NAMES -- that is what it reasons about -- and the
schema wanted INTEGERS, so the prompt resolved the mismatch by discarding the
information. An empty support means GLOBAL MUTATION to `select_commuting_slice`,
so no two nodes ever commuted, the operad's parallelism was dead code, and no
operator could be told which concepts it was about (which is why P2's VerifyOp
had nothing to verify against).

THE FIX IS TWO-SIDED, and the Python half alone would have changed nothing:
`OperatorFactory::create` never read the `support` field either, and every
primitive's `get_support()` returned a hard-coded constant. Both halves landed
together; see the P1 note in `include/mos/core/operator.hpp`.

------------------------------------------------------------------------------
THE ID SPACE, AND WHY IT IS NOT ConceptStore INSERTION ORDER
------------------------------------------------------------------------------

SPEC_P1_TO_P4 flagged this as "the one thing in P1 that could be wrong in a way
tests would not catch", and asked for it to be confirmed before any code was
written. It was, and the answer changed the design:

  * `ConceptStore::concepts()` is insertion-ordered and the header argues that a
    concept's NAME is its stable identity. True, but the store is built from what
    ticks RETRIEVE -- it is created lazily, lives inside the C++ process, holds
    only concepts already pulled in, and grows as the run proceeds. Python cannot
    see it, and an index into it means something different at tick 10 and tick
    900 because the vector it indexes has grown in between.

  * `EdgeContractionOp` / `EdgeExpansionOp` return `topology::VertexID`s over the
    simplicial complex. That IS a different numbering -- and it is a third one,
    not the same as either of the above.

  * The planner-facing operators (Search/Compute/Reason/Respond/Verify/Context)
    turned out to have NO id space at all. Their supports were the literals {},
    {0} and {1}, which `cognitive_state.hpp` itself calls "a scheduling artefact
    [that] carries no concept identity". There was nothing to be consistent with.

So the id space is chosen rather than inherited, and the choice is
`distilled_theorems.id` in the KnowledgeBase SQLite file:

  1. STABLE. `INTEGER PRIMARY KEY AUTOINCREMENT` is never reused or renumbered,
     so id 42 means the same concept at tick 900 as at tick 10 -- the property
     `concept_store.hpp` wanted, actually delivered.
  2. SHARED. Both sides can read the same file. No IPC round-trip per tick.
  3. TOTAL. It covers every concept in the corpus, not only the retrieved ones.
  4. DISJOINT FROM THE LEGACY TOKENS. AUTOINCREMENT starts at 1, so no real id
     is 0. The legacy {0} sentinel can never alias a resolved concept. (id 1 and
     the legacy ReasonOp {1} could in principle alias, but a DAG-built operator
     now always takes the resolved path, so the legacy constants are unreachable
     from a DAG at all.)

------------------------------------------------------------------------------
UNRESOLVABLE NAMES ARE AN EVENT, NOT A SILENCE
------------------------------------------------------------------------------

A name the store has never seen is INFORMATION: the planner is reasoning about
something not yet in memory. Dropping it would reintroduce the original defect
invisibly, so it never happens. Instead the name gets a PROVISIONAL id: a stable
negative integer derived from the name itself.

Negative ids cannot collide with KB rowids, and the provisional space preserves
the only thing support is actually used for -- set intersection within a tick:

  * two nodes naming the SAME unseen concept get the SAME provisional id, so
    they correctly do NOT commute;
  * two nodes naming DIFFERENT unseen concepts get different ids, so they
    correctly DO commute.

Dropping unresolved names instead would collapse both cases to "empty support"
= global mutation, which is safe but throws away exactly the parallelism P1
exists to recover. Every provisional assignment is reported in
`Resolution.unresolved` and logged by the caller.
"""

from __future__ import annotations

import hashlib
import os
import re
import sqlite3
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

# The KB the IPC engine opens (main.cpp hardcodes this name, relative to the
# process working directory). Kept in one place so the resolver and the engine
# cannot drift onto different files.
DEFAULT_DB = os.environ.get("MOS_KB_PATH", "mos_brain_ipc.db")

# Provisional ids live in [-(2**31 - 1), -1]. Wide enough that a collision
# between two distinct names is not a practical concern, and narrow enough to
# fit the schema's int32 `support` vector.
_PROVISIONAL_MODULUS = 2**31 - 1


def normalise(name: str) -> str:
    """Fold the accidental differences between two spellings of one concept.

    Case, surrounding whitespace, internal runs of whitespace, and the
    apostrophe/quote zoo ("Stokes' theorem" vs "Stokes theorem" vs "Stokes`s
    theorem"). Deliberately NOT stemming or synonym expansion: those would turn
    a lookup into a guess, and a wrong resolution is worse than an honest miss
    because it silently scopes an operator to the wrong concepts.
    """
    s = name.strip().lower()
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = re.sub(r"['`\"]s\b", "", s)   # possessives: stokes's -> stokes
    s = re.sub(r"['`\"]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


def provisional_id(name: str) -> int:
    """A stable negative id for a concept memory has never seen.

    Stable ACROSS RUNS, not merely within one DAG: the same unseen name yields
    the same id every time, so E7's recorded supports stay comparable across
    ticks. blake2b rather than hash() because Python salts str hashing per
    process, which would make the ids differ between the planner and any later
    analysis of the same log.
    """
    digest = hashlib.blake2b(normalise(name).encode("utf-8"), digest_size=8).digest()
    return -(int.from_bytes(digest, "big") % _PROVISIONAL_MODULUS + 1)


@dataclass
class Resolution:
    """What one `resolve()` call produced.

    `ids` is what crosses the boundary. `resolved` and `unresolved` are the
    audit trail: which names hit the store, which were provisional, and by which
    rule each match was made.
    """

    ids: List[int] = field(default_factory=list)
    resolved: Dict[str, Tuple[int, str]] = field(default_factory=dict)
    unresolved: Dict[str, int] = field(default_factory=dict)

    @property
    def hit_rate(self) -> Optional[float]:
        total = len(self.resolved) + len(self.unresolved)
        if total == 0:
            return None
        return len(self.resolved) / total

    def summary(self) -> str:
        total = len(self.resolved) + len(self.unresolved)
        if total == 0:
            return "no names to resolve"
        return (f"{len(self.resolved)}/{total} names resolved to store ids, "
                f"{len(self.unresolved)} provisional")


class ConceptResolver:
    """name -> id against the live KnowledgeBase.

    Loads the (id, name) table ONCE per instance. The KB grows only by ingestion,
    which does not run concurrently with a reasoning session, so re-reading per
    tick would buy nothing; `reload()` is there for the cases that do.
    """

    def __init__(self, db_path: str = DEFAULT_DB):
        self.db_path = db_path
        self._by_exact: Dict[str, int] = {}
        self._by_head: Dict[str, int] = {}
        self._heads: List[Tuple[str, int]] = []
        self._ambiguous_heads: set = set()
        self.loaded = False
        self.load_error: Optional[str] = None
        self.reload()

    # ------------------------------------------------------------------ load --

    def reload(self) -> None:
        self._by_exact.clear()
        self._by_head.clear()
        self._heads.clear()
        self._ambiguous_heads.clear()
        self.loaded = False
        self.load_error = None

        if not os.path.exists(self.db_path):
            # NOT an exception. A missing KB means "nothing is in memory yet",
            # which is a legitimate cold-start state: every name then resolves
            # provisionally and the run still proceeds, loudly.
            self.load_error = f"knowledge base not found at {self.db_path!r}"
            return

        try:
            con = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
            try:
                rows = con.execute(
                    "SELECT id, reasoning_chain FROM distilled_theorems "
                    "WHERE reasoning_chain IS NOT NULL ORDER BY id"
                ).fetchall()
            finally:
                con.close()
        except sqlite3.Error as exc:
            self.load_error = f"{type(exc).__name__}: {exc}"
            return

        for row_id, chain in rows:
            full = normalise(str(chain))
            # First writer wins, so a duplicated name keeps its LOWEST id and the
            # mapping stays stable as the corpus grows.
            self._by_exact.setdefault(full, int(row_id))

            # ingest_corpus.concept_name() builds "src#0007: first nine words",
            # so the readable part is what a planner could plausibly name.
            head = normalise(_strip_provenance(str(chain)))
            if not head:
                continue
            if head in self._by_head and self._by_head[head] != int(row_id):
                # Two different concepts share a head. It is then not an
                # identifier, so it resolves nothing -- recorded rather than
                # arbitrarily assigned to whichever row was read first.
                self._ambiguous_heads.add(head)
            else:
                self._by_head.setdefault(head, int(row_id))
            self._heads.append((head, int(row_id)))

        for head in self._ambiguous_heads:
            self._by_head.pop(head, None)

        self.loaded = True

    @property
    def size(self) -> int:
        return len(self._by_exact)

    # --------------------------------------------------------------- resolve --

    def resolve_one(self, name: str) -> Tuple[int, str]:
        """Resolve a single name. Returns (id, rule).

        The rules are tried most-specific first and every one of them is exact
        in some sense; none is a similarity score. A near-miss is reported as a
        miss, because scoping an operator to the wrong concepts is a silent
        error and an honest provisional id is not.
        """
        key = normalise(name)
        if not key:
            return provisional_id(name), "empty"

        hit = self._by_exact.get(key)
        if hit is not None:
            return hit, "exact"

        hit = self._by_head.get(key)
        if hit is not None:
            return hit, "head"

        # Containment, but ONLY when exactly one concept contains the name.
        # Several matches means the name does not identify a concept, so it is
        # not a resolution -- the ambiguity is the finding.
        if len(key) >= 4:
            hits = {rid for head, rid in self._heads if key in head}
            if len(hits) == 1:
                return hits.pop(), "substring"

        return provisional_id(name), "provisional"

    def resolve(self, names: Iterable[str]) -> Resolution:
        """Resolve a support list. Order-preserving, duplicate-collapsing.

        NEVER returns an empty `ids` for a non-empty `names`: that is the exact
        failure this module exists to prevent. Every name yields an id, either
        from the store or provisional.
        """
        out = Resolution()
        seen: set = set()
        for raw in names:
            name = str(raw)
            rid, rule = self.resolve_one(name)
            if rule == "provisional" or rule == "empty":
                out.unresolved[name] = rid
            else:
                out.resolved[name] = (rid, rule)
            if rid not in seen:
                seen.add(rid)
                out.ids.append(rid)
        return out


def _strip_provenance(chain: str) -> str:
    """Drop ingest_corpus's "source#0007: " prefix, keeping the readable head.

    Matches the shape `concept_name()` writes -- a filename, '#', four digits,
    ': ' -- rather than splitting on the first colon, which would decapitate any
    concept whose text legitimately contains one.
    """
    m = re.match(r"^\S+#\d{3,}:\s*(.+)$", chain.strip(), flags=re.DOTALL)
    return m.group(1) if m else chain.strip()


__all__ = [
    "ConceptResolver",
    "Resolution",
    "DEFAULT_DB",
    "normalise",
    "provisional_id",
]
