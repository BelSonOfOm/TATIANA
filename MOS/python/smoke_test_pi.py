"""
TATIANA — smoke test for the pi morphism (S -> U).

Exercises the LEFT ADJOINT of the adjunction: natural language -> Operad DAG,
running against the real Groq endpoint. Does NOT launch the C++ engine; this
isolates pi so a failure here is unambiguously a pi failure.

Costs ~3 Groq calls (free tier: 30 RPM / 6k TPM / ~1k RPD).

Run:  python smoke_test_pi.py
"""

from __future__ import annotations

import json
import os
import sys

from communicator import Communicator

CASES = [
    ("PURE NOISE", "hi my name is charbel", "NOISE"),
    ("PURE MATH",
     "Solve the eigenvalue problem for the weighted Hodge-de Rham Laplacian on 1-forms over CP^3 "
     "with the Fubini-Study metric and a thermal weight e^{-beta E}.",
     "MATH"),
    ("HYBRID (math + joke)",
     "Decompose this PDF into steps and solve each step, then come here so we can make out.",
     "MATH"),
]


def main() -> int:
    if not os.environ.get("GROQ_API_KEY"):
        print("GROQ_API_KEY not set in this process. Aborting.")
        return 1

    # Build WITHOUT __init__ so no C++ subprocess is spawned: we are testing pi only.
    c = Communicator.__new__(Communicator)
    c.c_chat = []
    c.api_url = "https://api.groq.com/openai/v1/chat/completions"
    c.model = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
    c.api_key = os.environ["GROQ_API_KEY"]

    print(f"model: {c.model}\n")
    failures = 0

    for name, text, expected in CASES:
        print("=" * 70)
        print(f"CASE: {name}")
        print(f"input: {text[:80]}{'...' if len(text) > 80 else ''}")
        try:
            dag = c.invoke_pi_llm(text)
        except Exception as e:
            print(f"  !! pi RAISED: {type(e).__name__}: {e}")
            failures += 1
            continue

        got = dag.get("type", "<missing 'type'>")
        ok = (got == expected)
        print(f"  type: {got}   (expected {expected})  {'OK' if ok else 'MISMATCH'}")
        if not ok:
            failures += 1

        nodes = dag.get("nodes", [])
        if nodes:
            print(f"  nodes: {len(nodes)}")
            for n in nodes:
                op = n.get("operator", {})
                print(f"    - id={n.get('id')} type={op.get('type')} "
                      f"payload={str(op.get('payload'))[:60]!r} "
                      f"children={n.get('children_ids')}")
        else:
            print("  nodes: (none)")

        # Show anything unexpected in the schema so we can catch drift early.
        extra = set(dag.keys()) - {"type", "nodes"}
        if extra:
            print(f"  !! unexpected top-level keys: {sorted(extra)}")
        print()

    print("=" * 70)
    print(f"RESULT: {len(CASES) - failures}/{len(CASES)} cases behaved as expected.")
    return 0 if failures == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
