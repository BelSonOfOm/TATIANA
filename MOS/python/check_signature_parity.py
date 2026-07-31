"""C++/Python parity for E7's canonical_signature.

WHY THIS FILE EXISTS
--------------------
`canonical_signature` is the key `AssemblyLog.recurrence` groups on. The engine
(C++, src/core/assembly_log.cpp) and the analysis (Python, assembly_log.py) each
compute it. If they disagree about the same composite, the recurrence counts
split silently across two keys: no test fails, no exception is raised, and the
promotion evidence is simply wrong. Nothing else in the pipeline would notice.

So the cases below are duplicated VERBATIM in tests/test_assembly_log.cpp with
the same expected strings hard-coded on both sides. Changing one implementation
breaks the other's test, which is the whole point.

Python is authoritative: it existed first, and `recurrence` /
`promotion_evidence` were written against it.

    python check_signature_parity.py
"""

from __future__ import annotations

import sys

from assembly_log import NodeRecord, canonical_signature

# (label, nodes, edges, expected) -- MUST match tests/test_assembly_log.cpp
CASES = [
    (
        "single read-only global node",
        [NodeRecord("SEARCH", (), True)],
        [],
        "SEARCH::r#",
    ),
    (
        "COMPUTE -> VERIFY",
        [NodeRecord("COMPUTE", (1, 2), False), NodeRecord("VERIFY", (), True)],
        [(0, 1)],
        "COMPUTE:1,2:w|VERIFY::r#0>1",
    ),
    (
        "same composite, nodes presented in the other order",
        [NodeRecord("VERIFY", (), True), NodeRecord("COMPUTE", (1, 2), False)],
        [(1, 0)],
        "COMPUTE:1,2:w|VERIFY::r#0>1",
    ),
    (
        "independent nodes sort by key, not by index",
        [NodeRecord("SEARCH", (), True), NodeRecord("COMPUTE", (), True)],
        [],
        "COMPUTE::r|SEARCH::r#",
    ),
    (
        "edge strings sort lexicographically ('0>10' before '0>2')",
        [NodeRecord("A%02d" % i, (), True) for i in range(11)],
        [(0, 2), (0, 10)],
        "|".join("A%02d::r" % i for i in range(11)) + "#0>10;0>2",
    ),
    (
        "the round-trip case from test_close_writes_one_line_with_delta_rho",
        [NodeRecord("COMPUTE", (1,), False), NodeRecord("VERIFY", (), True)],
        [(0, 1)],
        "COMPUTE:1:w|VERIFY::r#0>1",
    ),
]

REFUSAL_CASES = [
    ("a cycle", [NodeRecord("A", (), True), NodeRecord("B", (), True)], [(0, 1), (1, 0)]),
    ("an out-of-range dependency", [NodeRecord("A", (), True)], [(0, 5)]),
]


def main() -> int:
    failures = 0

    for label, nodes, edges, expected in CASES:
        got = canonical_signature(nodes, edges)
        if got != expected:
            print(f"  [FAIL] {label}\n    expected: {expected}\n    got:      {got}")
            failures += 1
        else:
            print(f"  [ok] {label} -> {got}")

    for label, nodes, edges in REFUSAL_CASES:
        try:
            canonical_signature(nodes, edges)
        except ValueError:
            print(f"  [ok] {label} is refused")
        else:
            print(f"  [FAIL] {label} was accepted; it must raise")
            failures += 1

    if failures:
        print(f"\n{failures} PARITY FAILURE(S). The C++ and Python signatures "
              f"have drifted -- recurrence counts are unreliable until this is fixed.")
        return 1

    print("\nSIGNATURE PARITY HOLDS (python side). "
          "Run mos_assembly_log_tests for the C++ side.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
