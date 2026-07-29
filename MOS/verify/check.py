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


CHECKS = {
    "symbolic_equal": check_symbolic_equal,
    "simplify_zero": check_simplify_zero,
    "eigenvalues": check_eigenvalues,
    "limit": check_limit,
    "derivative": check_derivative,
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
