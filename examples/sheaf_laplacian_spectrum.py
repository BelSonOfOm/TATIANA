"""Build a small complex, assemble its Hodge Laplacians, print the spectra.

Run:  python examples/sheaf_laplacian_spectrum.py
Needs: numpy only.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "MOS", "python"))

import numpy as np
from hodge import e5_complex, hodge_split

def spec(M):
    w = np.linalg.eigvalsh(M)
    w[np.abs(w) < 1e-12] = 0.0
    return np.round(w, 4)

cx = e5_complex()                      # 4 vertices, 5 edges, 1 filled triangle
d0, d1 = cx.delta0(), cx.delta1()      # coboundaries: (E x V) and (F x E)

L0 = d0.T @ d0                         # 0-Laplacian
L1 = d0 @ d0.T + d1.T @ d1             # 1-Laplacian (Hodge)

print("complex   :", cx.describe())
print("spec L0   :", spec(L0))
print("spec L1   :", spec(L1))
print("dim ker L0:", int(np.sum(np.linalg.eigvalsh(L0) < 1e-10)), "= b0 (connected components)")
print("dim ker L1:", int(np.sum(np.linalg.eigvalsh(L1) < 1e-10)), "= b1 (independent unfilled cycles)")

# The harmonic component of a measured 1-cochain is the growth address.
eta = np.array([0.0, 1.0, -1.0, 0.0, 1.0])
s = hodge_split(cx, eta)
print("\neta       :", eta)
print("gradient  : %.4f   curl: %.4f   harmonic: %.4f  (fractions of ||eta||^2)"
      % (s.grad2 / s.norm2, s.curl2 / s.norm2, s.harm2 / s.norm2))
