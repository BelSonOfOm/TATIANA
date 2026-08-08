# Adversarial fixture draft — NOT a real derivation

Every block below is planted. This file is the positive control for
`precilla check`: an instrument that cannot separate these has not earned the
right to gate a real draft. Same discipline as `cite/fixtures.json`.

## §4 DERIVATIONS

**EQ-1** Fatigue accumulates geometrically: after three ticks of constant drive
`a` with decay `kappa`, the accumulated fatigue has a closed form. *(planted:
TRUE — must PASS)*

```python
# EQ-1
kappa, a = symbols('kappa a')
lhs = a * (1 - kappa**3) / (1 - kappa)
rhs = a * (1 + kappa + kappa**2)
assert simplify(lhs - rhs) == 0
```

**EQ-2** Renormalising the context vector `c_t = rho*c + beta*f` requires the
squared norm. *(planted: FALSE — the cross term is dropped, which is the single
commonest algebra slip in this derivation. Must FAIL with a counterexample.)*

```python
# EQ-2
rho, beta = symbols('rho beta')
lhs = (rho + beta)**2
rhs = rho**2 + beta**2
assert simplify(lhs - rhs) == 0
```

**EQ-3** Inhibition strength enters the width equation through its magnitude.
*(planted: TRUE ONLY UNDER AN UNSTATED ASSUMPTION — `lam` is positive, but the
symbol is never declared positive. Must come back SUSPECT, not PASS and not
FAIL.)*

```python
# EQ-3
lam = symbols('lam')
lhs = sqrt(lam**2)
rhs = lam
assert simplify(lhs - rhs) == 0
```

**EQ-4** Loading the measured co-activation matrix. *(planted: MALICIOUS — must
be REFUSED by the static screen and never executed.)*

```python
# EQ-4
import os
os.system("echo pwned > /tmp/precilla_pwned")
lhs = 1
rhs = 1
```

**EQ-5** The k-WTA fixed point is stable. *(planted: the block asserts
something true but defines no `lhs`/`rhs`, so nothing can be verified
independently of its own claim. Must come back UNCHECKABLE.)*

```python
# EQ-5
x = symbols('x')
assert True
```

**EQ-6** The directed-graph cohomology term. *(planted: honestly declared
unmechanisable. Must be reported, not silently skipped.)*

```python
# EQ-6  [UNCHECKED]
# The sheaf coboundary on an asymmetric W has no closed form here.
```

**EQ-7** By the same argument, the base-level activation `B_i` follows a power
law rather than an exponential. *(planted: asserted in prose with NO block at
all. This is the important one — an unmechanised step is where the error
lives, and the gate must FAIL on it.)*
