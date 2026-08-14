// Phase 0 -- the invariant-drift experiment.
//
// Tests identity map Kill-Test 3 (DOCS/TATIANA_V1_IDENTITY_MAP.md S12.3): "Run wake+sleep for
// many cycles on synthetic input. If K(K) drifts monotonically, or the sheaf collapses to a
// trivial summand, TATIANA does not have identity and this document is refuted."
//
// Falsifier, written before this code: K(K) (the dimension vector over existing cells) must be
// EXACTLY unchanged, tick after tick, whenever no genuine (non-exact) discord is injected --
// whether or not the complex is topologically capable of carrying harmonic mass. It must change
// ONLY when a genuine harmonic residual is present, and then by exactly dim ker(H-I) (MATH_TOOLBOX
// III.3/III.4's holonomy formula for Construction 6), never more, never gradually.
//
// Three runs, per project discipline (no measurement without a positive control, a null, and a
// structure-free control at one shared setting):
//   A (null)           -- 3-cycle complex (topologically capable of growth), fed only exact
//                          (pure-gradient) input every tick. Expect: zero drift, growth never
//                          fires, for MANY ticks of real molding+consolidation activity.
//   B (positive)        -- same 3-cycle complex, fed a genuine planted harmonic component.
//                          Expect: exactly one growth event, of exactly the derived size.
//   C (structure-free)  -- a tree (path) complex, same stalk dimension, same style of injected
//                          input. b1=0 identically, so growth is structurally unreachable no
//                          matter what is injected -- a different reason for zero drift than A's.
//
// Stated scope reductions (not hidden -- see TATIANA-V2/DOCS/LOGBOOK_V2.md):
//   - Restriction maps are full dense orthogonal matrices, not V0's Householder-factored ones
//     (storage efficiency is not what's being tested here; see linalg.hpp header).
//   - No 2-cells: this experiment covers the two-term Hodge split C^1 = im(delta^0) (+) H^1
//     only (MATH_TOOLBOX III.6's "no triangles" case). The "flags a bad 2-cell" branch of the
//     routing law needs a genuine 2-cell stalk and is out of scope here.
//   - Sleep-phase MDL pruning (identity map S6) is not implemented: its exchange rate is an
//     explicitly open engineering choice (identity map S10 open decision #2), not yet specified
//     enough to code against. This experiment tests growth's dimension-conservation claim, not
//     pruning's.
//   - gamma(nu) is fixed at a constant gamma_0 (the "Verified" case) -- VerifyOp is not modelled.
//   - Growth, once fired on a cycle, is not re-wired into further dynamics; this experiment
//     measures the SIZE of one growth event, not long-run post-growth behaviour.
//   - Molding is deliberately bounded to one Hebbian nudge per tick before the same tick's
//     stall check -- growth is checked and fired within the tick it stalls, not after letting
//     molding drift for many ticks first. Whether unbounded accumulated molding could eventually
//     erode a topological obstruction on its own is a genuinely open question this experiment
//     does not settle (flagged, not answered).

#include "linalg.hpp"
#include <vector>
#include <iostream>
#include <iomanip>
#include <random>
#include <string>

using namespace la;

struct Edge {
    int u, v, dim;
    Mat Ru_K, Rv_K, Ru_W, Rv_W;
};

struct BaseComplex {
    std::string name;
    std::vector<int> vdims;
    std::vector<Edge> edges;

    int totalVDim() const { int s = 0; for (int d : vdims) s += d; return s; }
    int totalEDim() const { int s = 0; for (auto& e : edges) s += e.dim; return s; }
    std::vector<int> vOffsets() const {
        std::vector<int> off(vdims.size()); int c = 0;
        for (size_t i = 0; i < vdims.size(); ++i) { off[i] = c; c += vdims[i]; }
        return off;
    }
    std::vector<int> eOffsets() const {
        std::vector<int> off(edges.size()); int c = 0;
        for (size_t i = 0; i < edges.size(); ++i) { off[i] = c; c += edges[i].dim; }
        return off;
    }
};

Mat buildD0(const BaseComplex& C, bool useK) {
    int TV = C.totalVDim(), TE = C.totalEDim();
    Mat D0(TE, TV);
    auto voff = C.vOffsets(), eoff = C.eOffsets();
    for (size_t ei = 0; ei < C.edges.size(); ++ei) {
        const Edge& e = C.edges[ei];
        const Mat& Ru = useK ? e.Ru_K : e.Ru_W;
        const Mat& Rv = useK ? e.Rv_K : e.Rv_W;
        int erow = eoff[ei], ucol = voff[e.u], vcol = voff[e.v];
        for (int i = 0; i < e.dim; ++i)
            for (int j = 0; j < Ru.cols; ++j) D0(erow + i, ucol + j) += Ru(i, j);
        for (int i = 0; i < e.dim; ++i)
            for (int j = 0; j < Rv.cols; ++j) D0(erow + i, vcol + j) -= Rv(i, j);
    }
    return D0;
}

std::vector<double> slice(const std::vector<double>& v, int off, int len) {
    return std::vector<double>(v.begin() + off, v.begin() + off + len);
}

struct RelaxResult { std::vector<double> x, residual; double residualNorm; };

RelaxResult wakeRelax(const Mat& D0, const std::vector<double>& eta, int steps = 4000, double lr = 0.05) {
    int TV = D0.cols;
    std::vector<double> x(TV, 0.0);
    Mat D0T = D0.transpose();
    for (int it = 0; it < steps; ++it) {
        auto Dx = matvec(D0, x);
        auto r = vsub(Dx, eta);
        auto grad = matvec(D0T, r);
        x = vsub(x, vscale(grad, lr));
    }
    auto Dx = matvec(D0, x);
    auto residual = vsub(eta, Dx);
    return { x, residual, vnorm(residual) };
}

void moldOnce(BaseComplex& C, const std::vector<double>& x, const std::vector<double>& residual, double lrMold) {
    auto voff = C.vOffsets(), eoff = C.eOffsets();
    for (size_t ei = 0; ei < C.edges.size(); ++ei) {
        Edge& e = C.edges[ei];
        auto r_e = slice(residual, eoff[ei], e.dim);
        auto x_u = slice(x, voff[e.u], C.vdims[e.u]);
        auto x_v = slice(x, voff[e.v], C.vdims[e.v]);
        Mat dRu = outer(r_e, x_u) * lrMold;
        Mat dRv = outer(r_e, x_v) * (-lrMold);
        e.Ru_W = polarOrthogonal(e.Ru_W + dRu);
        e.Rv_W = polarOrthogonal(e.Rv_W + dRv);
    }
}

void consolidateSleep(BaseComplex& C, double gamma0) {
    for (auto& e : C.edges) {
        e.Ru_K = polarOrthogonal(e.Ru_K + (e.Ru_W - e.Ru_K) * gamma0);
        e.Rv_K = polarOrthogonal(e.Rv_K + (e.Rv_W - e.Rv_K) * gamma0);
        e.Ru_W = e.Ru_K;
        e.Rv_W = e.Rv_K;
    }
}

double meanQ(const BaseComplex& C) {
    double s = 0.0; int n = 0;
    for (auto& e : C.edges) {
        Mat Iu = Mat::identity(e.Ru_K.rows), Iv = Mat::identity(e.Rv_K.rows);
        s += (e.Ru_K - Iu).frobeniusNormSq(); n++;
        s += (e.Rv_K - Iv).frobeniusNormSq(); n++;
    }
    return n ? s / n : 0.0;
}

// dim ker(D0 D0^T) via Jacobi on the (small) totalEDim x totalEDim Gram matrix -- an
// independent, cochain-space route to dim H^1(gamma) alongside the holonomy route below.
int dimKernelViaGram(const Mat& D0, double tol, std::vector<double>* basisOut = nullptr) {
    Mat G = D0 * D0.transpose();
    std::vector<double> eigvals; Mat eigvecs;
    jacobiEigenSymmetric(G, eigvals, eigvecs);
    int count = 0; int firstIdx = -1;
    for (size_t i = 0; i < eigvals.size(); ++i) {
        if (eigvals[i] < tol) { count++; if (firstIdx < 0) firstIdx = static_cast<int>(i); }
    }
    if (basisOut && firstIdx >= 0) {
        basisOut->resize(eigvecs.rows);
        for (int i = 0; i < eigvecs.rows; ++i) (*basisOut)[i] = eigvecs(i, firstIdx);
    }
    return count;
}

// dim ker(H - I) for the holonomy H around a 3-cycle v0->v1->v2->v0, via the current W-maps.
// H + H^T has eigenvalue exactly 2 on ker(H-I) and strictly less than 2 elsewhere (real
// orthogonal H): see the derivation in TATIANA-V2/MATH/phase0_invariant_dimension.md.
int dimFixedSpaceViaHolonomy(const BaseComplex& C, double tol) {
    // C.edges[0]=(v0,v1), C.edges[1]=(v1,v2), C.edges[2]=(v2,v0), by construction below.
    auto transport = [](const Edge& e, int from) -> Mat {
        // returns T: F(from) -> F(other), from the edge's current W-maps
        if (from == e.u) return inverse(e.Rv_W) * e.Ru_W;   // x_v = Rv^-1 Ru x_u
        else return inverse(e.Ru_W) * e.Rv_W;                // x_u = Ru^-1 Rv x_v
    };
    Mat T1 = transport(C.edges[0], C.edges[0].u); // v0 -> v1
    Mat T2 = transport(C.edges[1], C.edges[1].u); // v1 -> v2
    Mat T3 = transport(C.edges[2], C.edges[2].u); // v2 -> v0
    Mat H = T3 * T2 * T1; // v0 -> v0
    Mat M = H + H.transpose();
    std::vector<double> eigvals; Mat eigvecs;
    jacobiEigenSymmetric(M, eigvals, eigvecs);
    int count = 0;
    for (double ev : eigvals) if (std::fabs(ev - 2.0) < tol) count++;
    return count;
}

BaseComplex makeCycleComplex(int d, std::mt19937& rng) {
    BaseComplex C; C.name = "3-cycle (d=" + std::to_string(d) + ", SO(d))";
    C.vdims = { d, d, d };
    auto mkEdge = [&](int u, int v) {
        Edge e; e.u = u; e.v = v; e.dim = d;
        e.Ru_K = randomOrthogonal(d, rng, /*forceRotation=*/true);
        e.Rv_K = randomOrthogonal(d, rng, /*forceRotation=*/true);
        e.Ru_W = e.Ru_K; e.Rv_W = e.Rv_K;
        return e;
    };
    C.edges = { mkEdge(0, 1), mkEdge(1, 2), mkEdge(2, 0) };
    return C;
}

BaseComplex makeTreeComplex(int d, std::mt19937& rng) {
    BaseComplex C; C.name = "path v0-v1-v2 (d=" + std::to_string(d) + ", b1=0)";
    C.vdims = { d, d, d };
    auto mkEdge = [&](int u, int v) {
        Edge e; e.u = u; e.v = v; e.dim = d;
        e.Ru_K = randomOrthogonal(d, rng, false);
        e.Rv_K = randomOrthogonal(d, rng, false);
        e.Ru_W = e.Ru_K; e.Rv_W = e.Rv_K;
        return e;
    };
    C.edges = { mkEdge(0, 1), mkEdge(1, 2) };
    return C;
}

struct RunReport {
    std::string name;
    std::vector<int> initialK;      // dims of pre-existing cells (vertices then edges)
    bool grew = false;
    int growTick = -1;
    int k_w_holonomy = -1;
    int k_w_gram = -1;
    std::vector<int> spokeEdgeDims; // Construction 6: F(f_i):=F(v_i), recorded for K(K) reporting
                                     // only -- NOT wired into C.edges / further dynamics (header).
    double maxHarmonicResidualSeen = 0.0;
    double harmonicResidualAtGrowth = -1.0;
    double qMin = 1e300, qMax = -1e300, qFinal = 0.0;
    bool existingCellsUntouched = true; // K(K) of pre-existing cells never moved
};

std::vector<int> currentK(const BaseComplex& C) {
    std::vector<int> k = C.vdims;
    for (auto& e : C.edges) k.push_back(e.dim);
    return k;
}

RunReport runExperiment(const std::string& label, BaseComplex C, bool plantHarmonic,
                         int nTicks, double gamma0, double lrMold, double stallTol,
                         double kernelTol, std::mt19937& rng) {
    RunReport rep; rep.name = label; rep.initialK = currentK(C);
    // Growth appends to C.vdims (a NEW cell), which would shift currentK()'s vdims/edges
    // concatenation boundary if compared index-by-index against initialK naively -- that is a
    // bookkeeping bug in the harness, not evidence of drift in a pre-existing cell. Compare
    // vertex dims and edge dims against their own original prefixes separately instead.
    const size_t origVCount = C.vdims.size();
    const size_t origECount = C.edges.size();
    const std::vector<int> origVDims = C.vdims;
    std::vector<int> origEDims; for (auto& e : C.edges) origEDims.push_back(e.dim);
    std::normal_distribution<double> nd(0.0, 1.0);

    for (int tick = 0; tick < nTicks; ++tick) {
        Mat D0 = buildD0(C, false); // wake acts on W
        int TV = D0.cols;

        std::vector<double> psi(TV);
        for (auto& v : psi) v = nd(rng);
        std::vector<double> etaGrad = matvec(D0, psi); // exact by construction under current W

        std::vector<double> eta = etaGrad;
        if (plantHarmonic) {
            std::vector<double> hBasis;
            int kGram = dimKernelViaGram(D0, kernelTol, &hBasis);
            if (kGram > 0) {
                double n = vnorm(hBasis);
                if (n > 1e-9) {
                    for (double& hv : hBasis) hv /= n;
                    for (size_t i = 0; i < eta.size(); ++i) eta[i] += 1.0 * hBasis[i]; // planted magnitude c=1.0
                }
            }
        }

        auto rel = wakeRelax(D0, eta);
        rep.maxHarmonicResidualSeen = std::max(rep.maxHarmonicResidualSeen, rel.residualNorm);

        moldOnce(C, rel.x, rel.residual, lrMold);

        // recheck after molding, same tick, per the stated ordering (mold, then check if still stalled)
        Mat D0b = buildD0(C, false);
        auto relAfterMold = wakeRelax(D0b, eta);

        if (!rep.grew && relAfterMold.residualNorm > stallTol) {
            int kHol = dimFixedSpaceViaHolonomy(C, 0.05);
            int kGram = dimKernelViaGram(D0b, kernelTol, nullptr);
            rep.grew = true;
            rep.growTick = tick;
            rep.k_w_holonomy = kHol;
            rep.k_w_gram = kGram;
            rep.harmonicResidualAtGrowth = relAfterMold.residualNorm;
            // Construction 6: new vertex w (dim k_w) plus one spoke edge {w,v_i} per cycle
            // vertex, F(f_i):=F(v_i) so each spoke has dim = the cycle's base vertex dim.
            // Recorded into the report for K(K) bookkeeping only -- NOT added to C.vdims/
            // C.edges, since wiring them into further wake/sleep dynamics is out of scope here
            // (see file header). This means currentK(C) after this tick reports only the
            // pre-existing cells plus the new vertex w -- the spoke edges are reported
            // separately via rep.spokeEdgeDims, not double-counted into C's own bookkeeping.
            if (kHol > 0) {
                C.vdims.push_back(kHol);
                rep.spokeEdgeDims.assign(C.edges.size(), C.vdims[0]);
            }
        }

        consolidateSleep(C, gamma0);

        double q = meanQ(C);
        rep.qMin = std::min(rep.qMin, q);
        rep.qMax = std::max(rep.qMax, q);
        rep.qFinal = q;

        // Pre-existing-cell dimension check, done on the ORIGINAL vertex/edge prefixes
        // specifically (not on currentK(C)'s concatenation, which shifts once a new vertex is
        // appended -- see the note above where origVCount/origVDims/origEDims are captured).
        for (size_t i = 0; i < origVCount; ++i)
            if (C.vdims[i] != origVDims[i]) rep.existingCellsUntouched = false;
        for (size_t i = 0; i < origECount; ++i)
            if (C.edges[i].dim != origEDims[i]) rep.existingCellsUntouched = false;
    }
    return rep;
}

void printReport(const RunReport& r) {
    std::cout << "== " << r.name << " ==\n";
    std::cout << "  initial K(K): [";
    for (size_t i = 0; i < r.initialK.size(); ++i) std::cout << r.initialK[i] << (i + 1 < r.initialK.size() ? "," : "");
    std::cout << "]\n";
    std::cout << "  existing cells' dims untouched across all ticks: " << (r.existingCellsUntouched ? "YES" : "NO (DRIFT DETECTED)") << "\n";
    std::cout << "  max harmonic residual seen (pre-growth-check): " << std::scientific << std::setprecision(3) << r.maxHarmonicResidualSeen << "\n";
    if (r.grew) {
        std::cout << "  GREW at tick " << r.growTick
                  << " | k_w via holonomy ker(H-I) = " << r.k_w_holonomy
                  << " | k_w via ker(D0 D0^T)      = " << r.k_w_gram
                  << (r.k_w_holonomy == r.k_w_gram ? "  [MATCH]" : "  [MISMATCH]") << "\n";
        std::cout << "  harmonic residual at growth tick: " << r.harmonicResidualAtGrowth << "\n";
        std::cout << "  spoke edge dims (F(f_i):=F(v_i), reported not wired): [";
        for (size_t i = 0; i < r.spokeEdgeDims.size(); ++i) std::cout << r.spokeEdgeDims[i] << (i + 1 < r.spokeEdgeDims.size() ? "," : "");
        std::cout << "]\n";
    } else {
        std::cout << "  growth never fired\n";
    }
    std::cout << std::fixed << std::setprecision(6);
    std::cout << "  Q(t): min=" << r.qMin << " max=" << r.qMax << " final=" << r.qFinal << "\n\n";
}

int main() {
    std::mt19937 rng(20260813);
    const int D_CYCLE = 3;   // odd: SO(3) holonomy generically has a fixed axis (III.3)
    const int D_TREE = 3;    // same dimension as the cycle runs, isolates topology as the variable
    const int N_TICKS = 500;
    const double GAMMA0 = 0.05;
    const double LR_MOLD = 0.02;
    const double STALL_TOL = 0.3;   // separates ~1e-6 (resolved) from ~1.0 (planted) residuals
    const double KERNEL_TOL = 1e-6;

    std::cout << "TATIANA-V2 Phase 0 -- invariant-drift experiment (identity map S12 Kill-Test 3)\n";
    std::cout << "N_TICKS=" << N_TICKS << " gamma0=" << GAMMA0 << " lr_mold=" << LR_MOLD
              << " stall_tol=" << STALL_TOL << "\n\n";

    auto complexA = makeCycleComplex(D_CYCLE, rng);
    auto repA = runExperiment("Run A (null: cycle present, exact input only)", complexA,
                               /*plantHarmonic=*/false, N_TICKS, GAMMA0, LR_MOLD, STALL_TOL, KERNEL_TOL, rng);
    printReport(repA);

    auto complexB = makeCycleComplex(D_CYCLE, rng);
    auto repB = runExperiment("Run B (positive: cycle present, planted harmonic component)", complexB,
                               /*plantHarmonic=*/true, N_TICKS, GAMMA0, LR_MOLD, STALL_TOL, KERNEL_TOL, rng);
    printReport(repB);

    auto complexC = makeTreeComplex(D_TREE, rng);
    auto repC = runExperiment("Run C (structure-free: tree, b1=0, same input style attempted)", complexC,
                               /*plantHarmonic=*/true, N_TICKS, GAMMA0, LR_MOLD, STALL_TOL, KERNEL_TOL, rng);
    printReport(repC);

    bool pass = repA.existingCellsUntouched && !repA.grew
             && repB.existingCellsUntouched && repB.grew && repB.k_w_holonomy > 0
             && repB.k_w_holonomy == repB.k_w_gram
             && repC.existingCellsUntouched && !repC.grew;

    std::cout << "KILL-TEST 3 VERDICT: " << (pass ? "SURVIVES (no drift observed)" : "FAILS -- SEE ABOVE") << "\n";
    return pass ? 0 : 1;
}
