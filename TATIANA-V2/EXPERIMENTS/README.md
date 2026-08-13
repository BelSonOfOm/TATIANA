# EXPERIMENTS/

Standalone CMake project. **No dependency on `../../MOS/CMakeLists.txt`** or any MOS header —
V2 is a from-the-ground-up reconstruction, not an extension of the V0 engine. Where a V0 algorithm
is worth keeping (Householder restriction maps, sheaf Laplacian assembly, Bures–Wasserstein), it
gets re-written small here, not linked in.

One executable per theorem/claim, one subdirectory per phase (`phase0_invariant/`,
`phase1_killtests/`, ...), added to the root `CMakeLists.txt` as its phase begins — don't
pre-create empty phase directories before there's a claim to test.

Each experiment's `main.cpp` states in a header comment:
- what it's testing and its falsifier condition
- its positive control, null, and structure-free control (per project discipline — no
  measurement is reportable without all three)
- which `MATH/` file it backs
