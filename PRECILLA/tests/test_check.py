"""
Positive control for `precilla check`.

Same rule as the cite instrument: the verifier is not used until it separates
planted classes at one shared setting. Here the classes are
TRUE / FALSE / SUSPECT / MALICIOUS / UNCHECKABLE / DECLARED / MISSING.

The FALSE and MALICIOUS rows are the ones that matter. A checker that passes
everything scores 100% on the true identities alone.

Run:  python3 tests/test_check.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from precilla.check import blocks as _blocks      # noqa: E402
from precilla.check.guard import screen           # noqa: E402
from precilla.check.run import check_file, check_text  # noqa: E402

FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "fixture_draft.md")
PWNED = "/tmp/precilla_pwned"
FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print("  ok   %s" % name)
    else:
        print("  FAIL %s   %s" % (name, detail))
        FAILURES.append(name)


EXPECTED = {
    "EQ-1": "PASS",                 # true identity
    "EQ-2": "FAIL",                 # dropped cross term
    "EQ-3": "SUSPECT",              # true only under an unstated assumption
    "EQ-4": "REFUSED",              # malicious
    "EQ-5": "UNCHECKABLE",          # no lhs/rhs to re-derive
    "EQ-6": "DECLARED_UNCHECKED",   # honestly declared
}


def test_guard():
    print("\n[1] static screen")
    cases = [
        ("import os", True),
        ("from subprocess import run", True),
        ("open('/etc/passwd')", True),
        ("eval('1+1')", True),
        ("().__class__.__bases__", True),
        ("with open('x') as f:\n    pass", True),
        ("from sympy import symbols\nlhs = symbols('x')\nrhs = lhs", False),
        ("import math\nlhs = math.pi\nrhs = math.pi", False),
    ]
    for src, should_flag in cases:
        flagged = bool(screen(src))
        check("%-38s -> %s" % (src.split("\n")[0][:38],
                               "refused" if should_flag else "allowed"),
              flagged == should_flag, str(screen(src)))


def test_blocks():
    print("\n[2] block extraction")
    with open(FIXTURE, encoding="utf-8") as fh:
        text = fh.read()
    aud = _blocks.audit(text)
    check("finds all 6 fenced blocks", aud["n_blocks"] == 6, aud["n_blocks"])
    check("sees 7 equations mentioned in prose", aud["n_mentioned"] == 7,
          aud["n_mentioned"])
    check("flags EQ-7 as having no block", aud["missing_block"] == ["EQ-7"],
          str(aud["missing_block"]))
    check("EQ-6 recorded as declared-unchecked",
          aud["declared_unchecked"] == ["EQ-6"], str(aud["declared_unchecked"]))


def test_verdicts():
    print("\n[3] per-equation verdicts (one shared setting)")
    if os.path.exists(PWNED):
        os.remove(PWNED)
    rep = check_file(FIXTURE, symbolic_seconds=8, numeric_seconds=8, trials=60)
    got = {r["eq"]: r["verdict"] for r in rep["results"]}
    for eq, want in EXPECTED.items():
        check("%s -> %s" % (eq, want), got.get(eq) == want,
              "got %s" % got.get(eq))

    check("the malicious block never executed", not os.path.exists(PWNED),
          "%s exists -- the screen was bypassed" % PWNED)
    # The fixture DOES contain a genuinely failing block (EQ-2), so the gate
    # must be FAIL, not merely INCOMPLETE. A wrong step outranks a missing one.
    check("a failing block outranks a missing one",
          rep["gate"] == "FAIL", rep["gate"])
    check("gate reason names the failing equation", "EQ-2" in rep["reason"],
          rep["reason"])

    fail = next(r for r in rep["results"] if r["eq"] == "EQ-2")
    check("EQ-2 failure carries an actual counterexample",
          "counterexample" in (fail.get("reason") or "").lower(),
          fail.get("reason", "")[:120])
    return rep


def test_missing_blocks_are_incomplete_not_failed():
    """
    Missing != wrong. Numbered DEFINITIONS have no identity to verify, so
    demanding a block for every label guaranteed FAIL and said nothing. A real
    draft came back FAIL at 8% coverage while every block it did contain
    passed -- which is INCOMPLETE, a different and more useful verdict.
    """
    print("\n[3b] INCOMPLETE vs FAIL")
    doc = """
EQ-1 defines the context update. EQ-2 is derived below.

```python
# EQ-2
x, y = symbols('x y')
lhs = (x + y)**2
rhs = x**2 + 2*x*y + y**2
assert simplify(lhs - rhs) == 0
```
"""
    rep = check_text(doc, symbolic_seconds=8, numeric_seconds=8, trials=40)
    check("all present blocks pass but one label lacks a block",
          rep["gate"] == "INCOMPLETE", "%s -- %s" % (rep["gate"], rep["reason"]))
    check("the unmechanised label is named", "EQ-1" in rep["reason"],
          rep["reason"])


def test_no_false_counterexample_on_stiff_expressions():
    """
    Regression for a live FALSE POSITIVE. A residual containing exp(h) with
    h ~ 500 loses every significant digit at 30-digit precision and looks like
    a counterexample. The mathematics was correct; the checker was not.
    """
    print("\n[3c] precision escalation, not accusation")
    stiff = """
```python
# D-1
W, a, b = symbols('W a b')
h = W*a + b
sig = 1/(1 + exp(-h))
lhs = diff(-log(1 - sig), W)
rhs = a*sig
assert simplify(lhs - rhs) == 0
```
"""
    rep = check_text(stiff, symbolic_seconds=20, numeric_seconds=20, trials=60)
    r = rep["results"][0]
    check("a stiff-but-true identity is not called a counterexample",
          r["verdict"] == "PASS", "%s -- %s" % (r["verdict"], r["reason"][:120]))


def test_named_variables_other_than_lhs_rhs():
    """The first real draft named its variables after the mathematics."""
    print("\n[3d] claims recovered without lhs/rhs")
    matrixy = """
```python
# D-9
from sympy import Matrix, eye
g = symbols('g')
T = Matrix([[0,1,0],[0,0,1],[0,0,0]])
M = (eye(3) - g*T).inv()
expected = Matrix([[1,g,g**2],[0,1,g],[0,0,1]])
assert simplify(M - expected) == Matrix.zeros(3,3)
```
"""
    rep = check_text(matrixy, symbolic_seconds=15, numeric_seconds=15, trials=40)
    r = rep["results"][0]
    check("a matrix identity with no lhs/rhs still verifies",
          r["verdict"] == "PASS", "%s -- %s" % (r["verdict"], r["reason"][:110]))
    check("and it was re-derived, not taken on trust",
          "re-derived" in (r.get("claim_source") or ""), str(r.get("claim_source")))


def test_clean_draft_passes():
    print("\n[4] a clean draft must actually pass (guards against a checker "
          "that just says no)")
    clean = """
EQ-1 and EQ-2 hold.

```python
# EQ-1
x, y = symbols('x y')
lhs = (x + y)**2
rhs = x**2 + 2*x*y + y**2
assert simplify(lhs - rhs) == 0
```

```python
# EQ-2
g, t = symbols('g t')
lhs = (1 - g**4) / (1 - g)
rhs = 1 + g + g**2 + g**3
assert simplify(lhs - rhs) == 0
```
"""
    rep = check_text(clean, symbolic_seconds=8, numeric_seconds=8, trials=40)
    check("clean draft gates PASS", rep["gate"] == "PASS",
          "%s -- %s" % (rep["gate"], rep["reason"]))
    check("both blocks PASS",
          all(r["verdict"] == "PASS" for r in rep["results"]),
          str([(r["eq"], r["verdict"]) for r in rep["results"]]))


def test_self_consistent_lie():
    print("\n[5] the block's own assert is not trusted")
    # lhs and rhs are literally the same object: the assert passes and proves
    # nothing about the claim in the prose. The independent route agrees they
    # are equal -- correctly -- but the point is that the verdict comes from
    # the re-derivation, not from the model's assert.
    sneaky = """
```python
# EQ-1
x = symbols('x')
expr = sin(x)**2 + cos(x)**2
lhs = expr
rhs = expr
assert simplify(lhs - rhs) == 0
```
"""
    rep = check_text(sneaky, symbolic_seconds=8, numeric_seconds=8, trials=40)
    r = rep["results"][0]
    check("tautological block still reports its independent route",
          r.get("symbolic") == "ZERO" and r.get("numeric") == "ZERO",
          str((r.get("symbolic"), r.get("numeric"))))

    # And the converse: an assert that PASSES on a FALSE identity because the
    # model compared the wrong things.
    lying = """
```python
# EQ-1
x = symbols('x')
lhs = x + 1
rhs = x + 2
dummy = x
assert simplify(dummy - x) == 0
```
"""
    rep2 = check_text(lying, symbolic_seconds=8, numeric_seconds=8, trials=40)
    r2 = rep2["results"][0]
    check("passing assert does NOT rescue a false lhs/rhs",
          r2["verdict"] == "FAIL", "%s -- %s" % (r2["verdict"], r2["reason"][:90]))
    check("...and the block's own assert is recorded as having passed",
          r2.get("assert_passed") is True, str(r2.get("assert_passed")))


if __name__ == "__main__":
    test_guard()
    test_blocks()
    test_verdicts()
    test_missing_blocks_are_incomplete_not_failed()
    test_no_false_counterexample_on_stiff_expressions()
    test_named_variables_other_than_lhs_rhs()
    test_clean_draft_passes()
    test_self_consistent_lie()
    print("\n%s  %d failure(s)" % ("FAILED" if FAILURES else "PASSED",
                                   len(FAILURES)))
    if FAILURES:
        print("  " + "\n  ".join(FAILURES))
    sys.exit(1 if FAILURES else 0)
