"""
TATIANA — the external oracle behind VerifyOp.

Coherence (rho) tells you the organs AGREE. It cannot tell you they are RIGHT.
Only grounding against something outside the system can do that. This harness is
that grounding: a sandboxed symbolic checker invoked by VerifyOp.

INVOCATION (matches VerifyOp's security whitelist: `python <abs-path> <arg>`,
no -c, no shell metacharacters)

    python check.py <spec.json>

THREE OUTCOMES, NOT TWO
-----------------------
    exit 0  VERIFIED     the claim was checked and holds
    exit 1  REFUTED      the claim was checked and is FALSE
    exit 2  UNVERIFIABLE could not be decided by this checker

The third is essential and is the thing naive verifiers get wrong: *inability to
check is not evidence of falsehood*. Treating "I couldn't determine this" the
same as "this is false" would make the system distrust perfectly good mathematics
merely because the checker is limited. VerifyOp handles these three distinctly.

SPEC FORMAT
-----------
    {"kind": "symbolic_equal", "lhs": "sin(x)**2 + cos(x)**2", "rhs": "1",
     "symbols": ["x"]}
    {"kind": "simplify_zero",  "expr": "(x+1)**2 - x**2 - 2*x - 1", "symbols": ["x"]}
    {"kind": "eigenvalues",    "matrix": [[2,0],[0,3]], "expected": [2,3]}
    {"kind": "limit",          "expr": "sin(x)/x", "var": "x", "to": "0", "expected": "1"}
    {"kind": "derivative",     "expr": "x**3", "var": "x", "expected": "3*x**2"}
    {"kind": "citation",       "src": "2608.01080v1:thm:main", "dst": "2608.01080v1:lem:key",
     "refs": "refs_corpus.json"}
"""

from __future__ import annotations

import json
import sys

EXIT_VERIFIED = 0
EXIT_REFUTED = 1
EXIT_UNVERIFIABLE = 2


def _symbols(names):
    import sympy
    return {n: sympy.Symbol(n) for n in (names or [])}


def check_symbolic_equal(spec) -> tuple[int, str]:
    import sympy
    loc = _symbols(spec.get("symbols"))
    lhs = sympy.sympify(spec["lhs"], locals=loc)
    rhs = sympy.sympify(spec["rhs"], locals=loc)
    diff = sympy.simplify(lhs - rhs)
    if diff == 0:
        return EXIT_VERIFIED, f"{spec['lhs']} == {spec['rhs']}"
    # A nonzero simplification is only a refutation if it is genuinely nonzero.
    try:
        if sympy.simplify(sympy.nsimplify(diff)) == 0:
            return EXIT_VERIFIED, "equal after nsimplify"
    except Exception:
        pass
    return EXIT_REFUTED, f"difference does not vanish: {diff}"


def check_simplify_zero(spec) -> tuple[int, str]:
    import sympy
    loc = _symbols(spec.get("symbols"))
    expr = sympy.sympify(spec["expr"], locals=loc)
    s = sympy.simplify(expr)
    if s == 0:
        return EXIT_VERIFIED, "expression simplifies to 0"
    return EXIT_REFUTED, f"simplifies to {s}, not 0"


def check_eigenvalues(spec) -> tuple[int, str]:
    import sympy
    M = sympy.Matrix(spec["matrix"])
    if M.rows != M.cols:
        return EXIT_UNVERIFIABLE, "matrix is not square"
    got = sorted(sympy.nsimplify(v) for v in M.eigenvals().keys())
    expected = sorted(sympy.sympify(v) for v in spec["expected"])
    if len(got) != len(expected):
        return EXIT_REFUTED, f"eigenvalue count {len(got)} != expected {len(expected)}"
    for a, b in zip(got, expected):
        if sympy.simplify(a - b) != 0:
            return EXIT_REFUTED, f"eigenvalues {got} != expected {expected}"
    return EXIT_VERIFIED, f"eigenvalues {got}"


def check_limit(spec) -> tuple[int, str]:
    import sympy
    loc = _symbols([spec["var"]])
    var = loc[spec["var"]]
    expr = sympy.sympify(spec["expr"], locals=loc)
    target = sympy.sympify(spec["to"], locals=loc)
    got = sympy.limit(expr, var, target)
    expected = sympy.sympify(spec["expected"], locals=loc)
    if sympy.simplify(got - expected) == 0:
        return EXIT_VERIFIED, f"limit = {got}"
    return EXIT_REFUTED, f"limit = {got}, expected {expected}"


def check_derivative(spec) -> tuple[int, str]:
    import sympy
    loc = _symbols([spec["var"]])
    var = loc[spec["var"]]
    expr = sympy.sympify(spec["expr"], locals=loc)
    got = sympy.diff(expr, var)
    expected = sympy.sympify(spec["expected"], locals=loc)
    if sympy.simplify(got - expected) == 0:
        return EXIT_VERIFIED, f"d/d{spec['var']} = {got}"
    return EXIT_REFUTED, f"d/d{spec['var']} = {got}, expected {expected}"


# --------------------------------------------------------------------------
# P2 TIER 2 — CITATION GROUNDING
# --------------------------------------------------------------------------
#
# A claim that block A depends on block B is checked against the author-asserted
# dependency graph that `python/extract_refs.py` extracts from arXiv LaTeX
# sources: when a proof writes "by Lemma 3.2", the author has asserted that this
# block depends on that one.
#
# WHAT MAY AND MAY NOT BE CONCLUDED. extract_refs.py is explicit that its edges
# are "excellent POSITIVES and unusable NEGATIVES" -- high precision, low recall,
# because most real dependencies are implicit and never get a \ref. So:
#
#   A -> B present in the record      => VERIFIED. The author asserted it.
#   B -> A present, A -> B absent     => REFUTED. Not silence: the record
#                                        asserts the OPPOSITE direction, and a
#                                        dependency cannot run both ways.
#   neither present                   => UNVERIFIABLE, always.
#
# THE THIRD CASE IS THE WHOLE POINT AND IS THE EASIEST TO GET WRONG. Treating "no
# edge in the record" as a refutation would convert the corpus's LOW RECALL into
# confident falsehoods, and would refute most true dependencies in mathematics.
# The docstring of extract_refs.py warns against exactly this, so the rule here
# is the narrowest one that can still ever fire: only a recorded edge in the
# opposite direction refutes.

_REFS_CACHE = {}


def _load_refs(path):
    """Load and index the \\ref record once per process."""
    if path in _REFS_CACHE:
        return _REFS_CACHE[path]
    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    edges = set()
    for e in payload.get("edges", []):
        src, dst = e.get("src"), e.get("dst")
        if src is not None and dst is not None:
            edges.add((str(src), str(dst)))
    blocks = {str(b.get("id")) for b in payload.get("blocks", [])}
    _REFS_CACHE[path] = (edges, blocks)
    return edges, blocks


def check_citation(spec) -> "tuple[int, str]":
    """Ground an asserted dependency against the author-asserted \\ref graph."""
    path = spec.get("refs", "refs_corpus.json")
    src, dst = spec.get("src"), spec.get("dst")
    if not src or not dst:
        return EXIT_UNVERIFIABLE, "citation check needs both 'src' and 'dst'"

    try:
        edges, blocks = _load_refs(path)
    except (OSError, json.JSONDecodeError) as e:
        return EXIT_UNVERIFIABLE, f"cannot read ref corpus {path!r}: {e}"

    src, dst = str(src), str(dst)

    # A block the corpus has never heard of cannot corroborate OR contradict.
    if src not in blocks or dst not in blocks:
        missing = [b for b in (src, dst) if b not in blocks]
        return EXIT_UNVERIFIABLE, f"block(s) not in the ref corpus: {missing}"

    if (src, dst) in edges:
        return EXIT_VERIFIED, f"author asserted {src} -> {dst}"

    if (dst, src) in edges:
        return EXIT_REFUTED, (f"record asserts the OPPOSITE direction "
                              f"({dst} -> {src}); a dependency cannot run both ways")

    # Silence. NOT a refutation -- see the note above.
    return EXIT_UNVERIFIABLE, (f"no \\ref edge either way between {src} and {dst}; "
                               f"the record has low recall, so absence proves nothing")


CHECKS = {
    "symbolic_equal": check_symbolic_equal,
    "simplify_zero": check_simplify_zero,
    "eigenvalues": check_eigenvalues,
    "limit": check_limit,
    "derivative": check_derivative,
    "citation": check_citation,
}


def main(argv) -> int:
    if len(argv) < 2:
        print("VERDICT=UNVERIFIABLE reason=no spec file given")
        return EXIT_UNVERIFIABLE

    try:
        with open(argv[1], "r", encoding="utf-8") as fh:
            spec = json.load(fh)
    except (OSError, json.JSONDecodeError) as e:
        print(f"VERDICT=UNVERIFIABLE reason=cannot read spec: {e}")
        return EXIT_UNVERIFIABLE

    kind = spec.get("kind")
    fn = CHECKS.get(kind)
    if fn is None:
        print(f"VERDICT=UNVERIFIABLE reason=unknown check kind {kind!r}; "
              f"known: {sorted(CHECKS)}")
        return EXIT_UNVERIFIABLE

    # Only the SYMBOLIC checks need sympy. Gating every kind on it would make
    # citation grounding -- which is pure set lookup against the \ref record --
    # report UNVERIFIABLE on a machine without sympy, i.e. turn a missing
    # optional dependency into a fabricated epistemic state.
    if kind != "citation":
        try:
            import sympy  # noqa: F401
        except ImportError:
            print("VERDICT=UNVERIFIABLE reason=sympy not installed")
            return EXIT_UNVERIFIABLE

    try:
        code, detail = fn(spec)
    except Exception as e:
        # A checker crash means we do NOT know. It is not a refutation.
        print(f"VERDICT=UNVERIFIABLE reason={type(e).__name__}: {e}")
        return EXIT_UNVERIFIABLE

    verdict = {EXIT_VERIFIED: "VERIFIED",
               EXIT_REFUTED: "REFUTED",
               EXIT_UNVERIFIABLE: "UNVERIFIABLE"}[code]
    print(f"VERDICT={verdict} detail={detail}")
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
