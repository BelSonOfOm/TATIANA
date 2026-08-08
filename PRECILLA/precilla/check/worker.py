"""
PRECILLA / check / worker.py

Runs ONE block, in its own process, and reports what it found.

Invoked as:  python3 -m precilla.check.worker  < block source on stdin >

Why a subprocess: SymPy's `simplify` can hang or blow memory on a bad
expression, and a model-authored block can loop forever. A crashed or timed-out
worker must degrade to TIMEOUT, not take the whole run down.

THE CENTRAL RULE OF THIS FILE
    The block's own `assert` is evidence, not proof. A model can write
    `assert simplify(lhs - rhs) == 0` against an lhs and rhs it has quietly
    defined to be the same object, and the assert passes while proving nothing.
    So after running the block, this worker RE-DERIVES the identity itself from
    the `lhs` and `rhs` left in the namespace, symbolically and then
    numerically. Agreement between those two independent routes is the result;
    the model's assert is only a tiebreaker signal.
"""

from __future__ import annotations

import ast
import json
import random
import signal
import sys


class _Timeout(Exception):
    pass


def _alarm(seconds):
    def handler(signum, frame):
        raise _Timeout()
    try:
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(seconds)
        return True
    except (ValueError, AttributeError):
        return False          # no SIGALRM (Windows); rely on parent timeout


def _cancel():
    try:
        signal.alarm(0)
    except (ValueError, AttributeError):
        pass


# Calls that only NORMALISE an expression. Unwrapping them is what makes the
# re-derivation independent: `assert simplify(M - expected) == zeros` compares
# an already-simplified result, so evaluating it as written would just re-run
# the model's own computation. Unwrapping to `M - expected` recovers the RAW
# claim, which this worker then simplifies and substitutes itself.
_UNWRAP = {"simplify", "expand", "factor", "together", "cancel", "radsimp",
           "trigsimp", "nsimplify", "powsimp", "logcombine", "expand_trig",
           "doit", "ratsimp", "signsimp"}


def _unwrap(node):
    changed = True
    while changed:
        changed = False
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in _UNWRAP and node.args):
            node, changed = node.args[0], True
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
              and node.func.attr in _UNWRAP):
            node, changed = node.func.value, True
    return node


def extract_claims(src):
    """
    Every equality the block ASSERTS, as (left_src, right_src) pairs.

    This is the generalisation of the old `lhs`/`rhs` requirement, which found
    1 of 5 real blocks in the first live draft because the model sensibly named
    its variables after the mathematics (`M`, `expected`) instead of after this
    tool's convention.
    """
    out = []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assert):
            continue
        t = node.test
        if not (isinstance(t, ast.Compare) and len(t.ops) == 1
                and isinstance(t.ops[0], ast.Eq)):
            continue
        lo, ro = _unwrap(t.left), _unwrap(t.comparators[0])
        try:
            out.append((ast.unparse(lo), ast.unparse(ro)))
        except AttributeError:          # py<3.9
            pass
    return out


def as_scalars(x):
    """Flatten a Matrix (or scalar) into a list of sympy expressions."""
    import sympy as sp
    if x is None:
        return []
    if isinstance(x, sp.MatrixBase):
        return list(x)
    if isinstance(x, (list, tuple)):
        outs = []
        for e in x:
            outs.extend(as_scalars(e))
        return outs
    return [sp.sympify(x)]


def symbolic_zero(expr, seconds=20):
    """Is expr identically zero? -> (verdict, detail)"""
    import sympy as sp
    _alarm(seconds)
    try:
        s = sp.simplify(expr)
        _cancel()
        if s == 0:
            return "ZERO", "simplify -> 0"
        s2 = sp.simplify(sp.expand(sp.together(s)))
        if s2 == 0:
            return "ZERO", "expand/together -> 0"
        return "NONZERO", "simplify -> %s" % str(s2)[:200]
    except _Timeout:
        return "TIMEOUT", "simplify exceeded %ds" % seconds
    except Exception as e:
        return "ERROR", "%s: %s" % (type(e).__name__, e)
    finally:
        _cancel()


def numeric_zero(expr, trials=200, tol=1e-9, seconds=20):
    """
    Independent numeric spot-check: substitute random values for every free
    symbol and see whether the difference vanishes.

    This catches what `simplify` misses (it gives up on hard expressions) and,
    more usefully, catches an expression that simplifies to zero only under
    assumptions the model forgot to state.
    """
    import sympy as sp
    _alarm(seconds)
    rng = random.Random(20260806)
    try:
        syms = sorted(expr.free_symbols, key=lambda s: s.name)
        if not syms:
            v = complex(sp.N(expr))
            return ("ZERO" if abs(v) < tol else "NONZERO",
                    "constant expression = %s" % v, 1, 0)
        worst = 0.0
        evaluated = 0
        for _ in range(trials):
            subs = {}
            for s in syms:
                # Rationals near 1 avoid branch cuts, division by zero, and
                # overflow, while still being generic enough to be a real test.
                subs[s] = sp.Rational(rng.randint(1, 97), rng.randint(1, 53))
            try:
                v = complex(sp.N(expr.subs(subs), 30))
            except Exception:
                continue
            if v != v:                      # NaN
                continue
            evaluated += 1
            worst = max(worst, abs(v))
            if abs(v) > tol:
                # ESCALATE, do not accuse.
                #
                # A residual containing exp(h) with h ~ 500 loses every
                # significant digit at 30-digit precision: one term underflows
                # to ~1e-74 while its partner stays O(10), and the difference
                # looks exactly like a counterexample. That false positive was
                # observed on a real draft, against mathematics that was
                # correct. A disagreement between two methods is resolved by
                # strengthening the weaker one, not by loosening a tolerance.
                survived = True
                for prec in (60, 200, 500):
                    try:
                        hv = complex(sp.N(expr.subs(subs), prec))
                    except Exception:
                        break
                    if hv != hv:                     # NaN
                        break
                    if abs(hv) <= tol:
                        survived = False             # artefact of precision
                        break
                if not survived:
                    continue
                return ("NONZERO",
                        "counterexample at %s -> %s (survives 500-digit "
                        "re-evaluation)"
                        % ({str(k): str(v2) for k, v2 in list(subs.items())[:6]},
                           v), evaluated, worst)
        if evaluated == 0:
            return "INCONCLUSIVE", "no substitution evaluated", 0, 0.0
        return "ZERO", "%d/%d substitutions vanish" % (evaluated, trials), \
            evaluated, worst
    except _Timeout:
        return "TIMEOUT", "numeric check exceeded %ds" % seconds, 0, 0.0
    except Exception as e:
        return "ERROR", "%s: %s" % (type(e).__name__, e), 0, 0.0
    finally:
        _cancel()


def main():
    payload = json.loads(sys.stdin.read())
    src = payload["source"]
    sym_s = int(payload.get("symbolic_seconds", 20))
    num_s = int(payload.get("numeric_seconds", 20))
    trials = int(payload.get("trials", 200))

    result = {"assert_passed": None, "assert_error": None,
              "symbolic": None, "symbolic_detail": None,
              "numeric": None, "numeric_detail": None,
              "have_lhs_rhs": False, "exec_error": None,
              "verdict": "ERROR", "reason": ""}

    import sympy as sp
    ns = {}
    exec("from sympy import *", ns)          # noqa: S102 -- screened by guard
    ns["__name__"] = "precilla_block"

    # 1. run the block. An AssertionError is informative, not fatal.
    try:
        _alarm(sym_s + num_s + 10)
        exec(src, ns)                        # noqa: S102 -- screened by guard
        _cancel()
        result["assert_passed"] = True
    except AssertionError as e:
        _cancel()
        result["assert_passed"] = False
        result["assert_error"] = str(e) or "assertion failed"
    except _Timeout:
        _cancel()
        result["exec_error"] = "block execution timed out"
        result["verdict"] = "TIMEOUT"
        result["reason"] = "the block itself did not finish"
        print(json.dumps(result))
        return
    except Exception as e:
        _cancel()
        result["exec_error"] = "%s: %s" % (type(e).__name__, e)
        result["verdict"] = "ERROR"
        result["reason"] = "block raised: " + result["exec_error"]
        print(json.dumps(result))
        return

    # 2. independent re-derivation from lhs/rhs
    # Preferred: explicit lhs/rhs. Fallback: re-derive whatever the block
    # asserted, with normalising calls stripped so we redo the work ourselves.
    residuals, source = [], None
    lhs, rhs = ns.get("lhs"), ns.get("rhs")
    if lhs is not None and rhs is not None:
        source = "lhs/rhs"
        try:
            residuals = [sp.sympify(lhs) - sp.sympify(rhs)]
        except Exception as e:
            result["verdict"] = "ERROR"
            result["reason"] = "lhs/rhs not sympifiable: %s" % e
            print(json.dumps(result))
            return
    else:
        claims = extract_claims(src)
        for lsrc, rsrc in claims:
            try:
                lv = eval(lsrc, ns)          # noqa: S307 -- screened by guard
                rv = eval(rsrc, ns)          # noqa: S307
                ls, rs = as_scalars(lv), as_scalars(rv)
                if len(ls) != len(rs):
                    continue
                residuals.extend([a - b for a, b in zip(ls, rs)])
                source = "asserted equality (re-derived)"
            except Exception:
                continue

    if not residuals:
        result["verdict"] = "UNCHECKABLE"
        result["reason"] = ("block ran, but no equality could be recovered "
                            "from it -- define `lhs`/`rhs`, or assert an "
                            "explicit `A == B`")
        print(json.dumps(result))
        return

    result["have_lhs_rhs"] = True
    result["claim_source"] = source
    result["n_residuals"] = len(residuals)
    diff = residuals[0] if len(residuals) == 1 else None

    # Every residual must vanish. One surviving entry falsifies the claim.
    sv, sd, nv, nd = "ZERO", "all residuals vanish", "ZERO", "all residuals vanish"
    for i, r in enumerate(residuals):
        v, d = symbolic_zero(r, sym_s)
        if v != "ZERO":
            sv, sd = v, "residual %d/%d: %s" % (i + 1, len(residuals), d)
            break
    for i, r in enumerate(residuals):
        v, d = numeric_zero(r, trials, seconds=num_s)[:2]
        if v != "ZERO":
            nv, nd = v, "residual %d/%d: %s" % (i + 1, len(residuals), d)
            break
    result["symbolic"], result["symbolic_detail"] = sv, sd
    result["numeric"], result["numeric_detail"] = nv, nd

    # 3. adjudicate. Disagreement between the two routes is itself a finding.
    if sv == "ZERO" and nv == "ZERO":
        result["verdict"] = "PASS"
        result["reason"] = "symbolic and numeric agree the identity holds"
    elif nv == "NONZERO":
        result["verdict"] = "FAIL"
        result["reason"] = "numeric counterexample: " + nd
    elif sv == "NONZERO" and nv == "ZERO":
        result["verdict"] = "SUSPECT"
        result["reason"] = ("simplify says nonzero but every substitution "
                            "vanishes -- usually a missing assumption "
                            "(positivity, realness, domain). " + sd)
    elif sv == "NONZERO":
        result["verdict"] = "FAIL"
        result["reason"] = "symbolic residual: " + sd
    elif "TIMEOUT" in (sv, nv):
        result["verdict"] = "TIMEOUT"
        result["reason"] = "symbolic=%s numeric=%s" % (sv, nv)
    else:
        result["verdict"] = "INCONCLUSIVE"
        result["reason"] = "symbolic=%s numeric=%s" % (sv, nv)

    if result["assert_passed"] is False and result["verdict"] == "PASS":
        result["verdict"] = "SUSPECT"
        result["reason"] = ("independent check passes but the block's own "
                            "assert failed -- the block and the identity "
                            "disagree about what is being claimed")

    print(json.dumps(result))


if __name__ == "__main__":
    main()
