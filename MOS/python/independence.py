"""
TATIANA - E3: the independence relation of the operator algebra D, and its
clique polynomial.

WHY THIS SCRIPT EXISTS
----------------------
The scrutiny document's Part II builds a large superstructure on the operator
algebra D: Foata normal form, a quadratic Groebner basis, Koszulity, the
Cartier-Foata clique polynomial, a "capacity" growth rate kappa, the Anick
resolution, and finally HH^1/HH^2 as the classification of genuine neurogenesis.

EVERY ONE of those rests on a single hypothesis:

    operators with DISJOINT SUPPORT COMMUTE,

so that I = {(i,j) : support(g_i) ^ support(g_j) = 0} is the independence
relation of a Mazurkiewicz trace monoid M(Sigma, I), whose algebra is quadratic,
PBW, and Koszul, with Hilbert series H(z) = 1/mu(z) for the clique polynomial mu.

That hypothesis was asserted and never checked against the engine. This script
checks it. It reads the ACTUAL declared supports from src/operators/primitives.cpp
and computes I, the clique numbers c_k, mu(z), and kappa = 1/r_min under both
readings of the support convention.

THE HEADLINE: three findings, in increasing order of severity.
See the printout, and DOCS/AUDIT_SCRUTINY_AND_BOOK.md finding F4.

Run:  python independence.py
"""

from __future__ import annotations

from itertools import combinations
from typing import Dict, FrozenSet, List, Sequence, Set, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# The operator set, transcribed verbatim from src/operators/primitives.cpp.
# (line numbers as of 2026-07-28)
# ---------------------------------------------------------------------------
#   SearchOp::get_support()   -> {}      // "Global read"                 READ_ONLY
#   ComputeOp::get_support()  -> {0}     // "Touches fundamental vertices" MUTATION
#   ReasonOp::get_support()   -> {1}     // "Touches specific reasoning vertices" MUTATION
#   RespondOp::get_support()  -> {}      // "Read only"                   READ_ONLY
#   VerifyOp::get_support()   -> {0}                                      MUTATION
#   ContextOp::get_support()  -> {0}     // "0-simplices are fundamental" MUTATION
OPERATORS: Dict[str, Tuple[FrozenSet[int], str]] = {
    "SearchOp":  (frozenset(),   "READ_ONLY"),
    "ComputeOp": (frozenset({0}), "MUTATION"),
    "ReasonOp":  (frozenset({1}), "MUTATION"),
    "RespondOp": (frozenset(),   "READ_ONLY"),
    "VerifyOp":  (frozenset({0}), "MUTATION"),
    "ContextOp": (frozenset({0}), "MUTATION"),
}


# ---------------------------------------------------------------------------
# Two competing readings of "disjoint support"
# ---------------------------------------------------------------------------
def independent_formalism(a: str, b: str) -> bool:
    """The trace-monoid reading: I = disjoint supports, treating {} as a SET.

    Under this reading the empty set is disjoint from everything, so a
    global-read operator is independent of every other operator. This is what
    the scrutiny document's Part II assumes.
    """
    return len(OPERATORS[a][0] & OPERATORS[b][0]) == 0


def can_coschedule(first: str, second: str) -> bool:
    """The CODE's reading, replaying src/core/operad.cpp's slice-packing loop.

    In the scheduler, an EMPTY support does NOT mean "touches nothing"; it means
    "touches EVERYTHING" (a global operation). Worse, any empty-support node --
    read-only or not -- sets `slice_is_global_mutation = true` once admitted, so
    the answer depends on which node the ready-queue reached first.

    We therefore have to ask the question in a specific ORDER, which is itself
    the finding: see check_symmetry().
    """
    sup1, ro1 = OPERATORS[first]
    sup2, ro2 = OPERATORS[second]
    ro1 = (ro1 == "READ_ONLY")
    ro2 = (ro2 == "READ_ONLY")

    # `first` always enters the empty slice.
    slice_support: Set[int] = set()
    slice_is_global = False
    if not sup1:
        slice_is_global = True          # set for READ_ONLY nodes too (operad.cpp)
    else:
        slice_support |= sup1

    # Can `second` join?
    if not sup2:
        intersects = slice_is_global if ro2 else True   # non-empty slice blocks a global mutation
    else:
        intersects = True if slice_is_global else bool(sup2 & slice_support)
    return not intersects


def independent_code(a: str, b: str) -> bool:
    """Conservative symmetrisation of the scheduler: independent only if the two
    operators can share a slice in BOTH orders. An 'independence relation' that
    depends on order is not one."""
    return can_coschedule(a, b) and can_coschedule(b, a)


# ---------------------------------------------------------------------------
# Clique polynomial machinery (Cartier-Foata)
# ---------------------------------------------------------------------------
def clique_numbers(gens: Sequence[str], indep) -> List[int]:
    """c_k = number of k-subsets that are PAIRWISE independent (k-cliques of I).

    c_0 = 1 by convention (the empty clique). Brute force is correct and instant
    at r = 6; the whole point is that this is a cheap computation nobody ran.
    """
    counts = [1]
    for k in range(1, len(gens) + 1):
        c = sum(1 for S in combinations(gens, k)
                if all(indep(x, y) for x, y in combinations(S, 2)))
        if c == 0:
            break
        counts.append(c)
    return counts


def mu_coefficients(c: Sequence[int]) -> List[float]:
    """mu(z) = sum_k (-1)^k c_k z^k, ascending powers."""
    return [((-1) ** k) * c[k] for k in range(len(c))]


def growth_rate(mu_asc: Sequence[float]) -> Tuple[float, float]:
    """kappa = 1/r_min, r_min the least positive real root of mu.

    H_A(z) = 1/mu(z) is the Hilbert series of the trace algebra, so the number of
    distinct m-step reasoning acts is [z^m] H_A(z) and its exponential growth rate
    is the reciprocal of the radius of convergence -- the least positive root of
    the denominator (Pringsheim: a series with non-negative coefficients has a
    singularity on the positive real axis at its radius of convergence).
    """
    roots = np.roots(list(mu_asc)[::-1])          # np.roots wants descending
    pos = [r.real for r in roots
           if abs(r.imag) < 1e-9 and r.real > 1e-12]
    if not pos:
        return float("nan"), float("nan")
    r_min = min(pos)
    return r_min, 1.0 / r_min


def poly_str(mu_asc: Sequence[float]) -> str:
    parts = []
    for k, a in enumerate(mu_asc):
        if abs(a) < 1e-12:
            continue
        sign = "-" if a < 0 else ("+" if k else "")
        mag = abs(a)
        mag_s = f"{mag:g}"
        term = mag_s if k == 0 else (f"{mag_s}z" if k == 1 else f"{mag_s}z^{k}")
        parts.append(f"{sign} {term}" if k else f"{sign}{term}")
    return " ".join(parts)


def check_symmetry() -> List[Tuple[str, str]]:
    """Pairs whose co-schedulability DEPENDS ON ORDER. Any such pair proves the
    scheduler's relation is not symmetric, hence not an independence relation,
    hence not a trace monoid."""
    bad = []
    for a, b in combinations(OPERATORS, 2):
        if can_coschedule(a, b) != can_coschedule(b, a):
            bad.append((a, b))
    return bad


def report(title: str, gens: Sequence[str], indep) -> None:
    c = clique_numbers(gens, indep)
    mu = mu_coefficients(c)
    r_min, kappa = growth_rate(mu)
    pairs = [(a, b) for a, b in combinations(gens, 2) if indep(a, b)]
    print(f"\n--- {title} ---")
    print(f"  |I| = {len(pairs)} independent pairs out of {len(gens)*(len(gens)-1)//2}")
    for a, b in pairs:
        print(f"      {a} || {b}")
    print(f"  clique numbers c_k = {c}")
    print(f"  mu(z) = {poly_str(mu)}")
    print(f"  least positive root r_min = {r_min:.6f}")
    print(f"  capacity kappa = 1/r_min = {kappa:.4f}   (free monoid on {len(gens)}: kappa = {len(gens)})")
    print(f"  => commutation buys {len(gens)} -> {kappa:.4f}, "
          f"a {100.0*(len(gens)-kappa)/len(gens):.1f}% reduction from free")


if __name__ == "__main__":
    gens = list(OPERATORS)
    print("=" * 74)
    print("E3 - INDEPENDENCE RELATION OF THE OPERATOR ALGEBRA D")
    print("=" * 74)
    print("\nDeclared supports (verbatim from src/operators/primitives.cpp):")
    for g, (sup, ty) in OPERATORS.items():
        s = "{}" if not sup else "{" + ",".join(map(str, sorted(sup))) + "}"
        print(f"  {g:<11} support={s:<6} type={ty}")

    report("READING A: formalism (disjoint supports, {} is a set)",
           gens, independent_formalism)
    report("READING B: the code (operad.cpp slice packing, {} means GLOBAL)",
           gens, independent_code)

    asym = check_symmetry()

    print("\n" + "=" * 74)
    print("FINDINGS")
    print("=" * 74)

    print("""
F4.1  THE SUPPORTS ARE HARDCODED LITERALS, NOT COMPUTED.
      Every get_support() in primitives.cpp returns a constant -- {}, {0} or {1}
      -- with a comment ("Touches fundamental vertices") standing in for an
      actual analysis of what the operator reads and writes. Three of the six
      operators return the same literal {0}. These are placeholders.

      CONSEQUENCE: any clique polynomial computed from them -- including both of
      the ones printed above -- is a fact about six hardcoded constants, NOT
      about the system. Part II's capacity kappa currently measures nothing.""")

    print("""
F4.2  THE TWO READINGS OF {} ARE OPPOSITE, AND THE FORMALISM TOOK THE WRONG ONE.
      In operad.cpp an EMPTY support means GLOBAL -- the operator touches
      everything and must run isolated. In the trace-monoid formalism, {} is a
      set disjoint from every other set, so an empty-support operator is
      independent of EVERYTHING. The same symbol carries opposite meanings, and
      Part II silently assumes the one the engine does not implement.""")

    if asym:
        print(f"""
F4.3  *** THE SCHEDULER'S RELATION IS NOT SYMMETRIC. ***
      {len(asym)} pair(s) can share a slice in one order but not the other:""")
        for a, b in asym:
            print(f"        ({a}, {b}): {a} then {b} -> {can_coschedule(a, b)};  "
                  f"{b} then {a} -> {can_coschedule(b, a)}")
        print("""      Cause: in operad.cpp, admitting ANY empty-support node -- including a
      READ_ONLY one -- sets slice_is_global_mutation = true, which then blocks
      every later node. So whether two operators commute depends on the order the
      ready-queue happened to reach them.

      An independence relation is symmetric BY DEFINITION (Mazurkiewicz). A
      non-symmetric relation does not define a trace monoid, so there is no Foata
      normal form, no quadratic Groebner basis, no Koszul dual, and no
      Cartier-Foata Hilbert series to compute. Part II does not apply to the
      engine as written.

      This is also very likely an unintended scheduling behaviour worth fixing on
      its own merits, independent of any of the algebra.""")
    else:
        print("\nF4.3  Scheduler relation is symmetric (no order-dependent pairs found).")

    print("""
F4.4  THE TWO READINGS DISAGREE BY A FACTOR OF ~1.8 IN CAPACITY.
      Reading A (formalism) gives kappa = 3.00, a 50% reduction from free.
      Reading B (the code)  gives kappa = 5.45, a  9% reduction from free.
      So the number Part II calls "the system's procedural reach" depends almost
      entirely on which convention you pick for {} -- and the two conventions are
      contradictory (F4.2). Under the reading the ENGINE actually implements, the
      algebra is nearly free: with three of six operators sharing the single
      support {0}, the dependence graph is almost complete, and the trace
      structure is barely distinguishable from the free monoid.

      Koszulity, the PBW basis and the clique polynomial remain TRUE statements
      about whichever algebra you pick. They are simply not INFORMATIVE about the
      architecture, because they are computed from placeholder constants (F4.1)
      under a convention the code contradicts (F4.2), over a relation that is not
      even symmetric (F4.3).

VERDICT
      Part II of the scrutiny/book is not usable as written. To make it usable,
      in order:
        1. Fix operad.cpp so co-schedulability is symmetric (a genuine bug).
        2. Replace the hardcoded supports with real read/write sets derived from
           what each operator actually touches -- including the shared state the
           current model ignores entirely: the SQLite store, the obstruction
           counter Omega, the mutation log, and the coarse stalks that
           compute_pi_v overwrites after every DAG execution. Operators that all
           mutate Omega do NOT commute, whatever their vertex supports say.
        3. Only THEN recompute I. If it is still near-empty -- which the current
           evidence suggests -- Part II should be cut from the paper rather than
           defended.""")
