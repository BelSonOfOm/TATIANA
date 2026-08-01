// Phase-2 item 1: Householder restriction maps.
//
// The properties asserted here are the ones the rest of the design LEANS on:
// exact orthogonality (audit F2's ||R|| <= 1, and the CPTP reading of 5t Q1),
// R^T for free from symmetry of the factors, and the storage/apply costs that
// made the representation necessary in the first place (5s budget finding 1).

#include <algorithm>
#include <cassert>
#include <chrono>
#include <cmath>
#include <iostream>
#include <random>
#include <stdexcept>
#include <vector>

#include "mos/core/coarse_complex.hpp"
#include "mos/core/householder.hpp"

using namespace mos::core;

namespace {

constexpr int kDeployedDim = 384;  // bge-small-en-v1.5, FIX-1's contract

bool close(double a, double b, double tol = 1e-12) {
    return std::fabs(a - b) <= tol * std::max(1.0, std::max(std::fabs(a), std::fabs(b)));
}

void test_single_reflection_is_its_own_inverse() {
    // H = I - 2vv^T is symmetric and orthogonal, so H^2 = I. If this fails,
    // nothing else in the file means anything.
    Eigen::VectorXd v(3);
    v << 1.0, 2.0, -2.0;   // norm 3, normalised on construction
    HouseholderMap H(3, {v});

    Eigen::VectorXd x(3);
    x << 5.0, -1.0, 3.0;
    const Eigen::VectorXd once = H.apply(x);
    const Eigen::VectorXd twice = H.apply(once);
    assert((twice - x).norm() < 1e-13);

    // A vector ALONG v flips sign; a vector ORTHOGONAL to v is fixed. That is
    // what makes it a reflection rather than merely an orthogonal map.
    const Eigen::VectorXd vn = v.normalized();
    assert((H.apply(vn) + vn).norm() < 1e-13);
    Eigen::VectorXd perp(3);
    perp << 2.0, 0.0, 1.0;             // dot(perp, v) = 2 + 0 - 2 = 0
    assert(std::fabs(perp.dot(v)) < 1e-15);
    assert((H.apply(perp) - perp).norm() < 1e-13);
    std::cout << "  [ok] H^2 = I; v flips, v-perp is fixed\n";
}

void test_orthogonality_is_exact_at_deployed_dimension() {
    // Not "orthogonal to tolerance after re-orthogonalisation" -- orthogonal by
    // construction, at the dimension actually deployed.
    const HouseholderMap R = HouseholderMap::random(kDeployedDim, HOUSEHOLDER_M_DEFAULT, 12345);

    double worst_norm_err = 0.0;
    double worst_roundtrip = 0.0;
    std::mt19937 gen(999);
    std::normal_distribution<double> normal(0.0, 1.0);
    for (int trial = 0; trial < 50; ++trial) {
        Eigen::VectorXd x(kDeployedDim);
        for (int i = 0; i < kDeployedDim; ++i) x(i) = normal(gen);

        // Orthogonal => norm preserved exactly.
        const Eigen::VectorXd Rx = R.apply(x);
        worst_norm_err = std::max(worst_norm_err, std::fabs(Rx.norm() - x.norm()));

        // R^T R = I, tested through the free-transpose path.
        const Eigen::VectorXd back = R.apply_transpose(Rx);
        worst_roundtrip = std::max(worst_roundtrip, (back - x).norm() / x.norm());
    }
    std::cout << "  [ok] d=384, m=4: worst norm error " << worst_norm_err
              << ", worst R^T R roundtrip " << worst_roundtrip << "\n";
    assert(worst_norm_err < 1e-12);
    assert(worst_roundtrip < 1e-13);
}

void test_transpose_matches_the_dense_transpose() {
    // apply_transpose reverses the factor order rather than transposing anything.
    // Checked against the dense oracle so the reasoning is not merely asserted.
    const int d = 24;
    const HouseholderMap R = HouseholderMap::random(d, 5, 7);
    const Eigen::MatrixXd Rd = R.dense();

    std::mt19937 gen(3);
    std::normal_distribution<double> normal(0.0, 1.0);
    Eigen::VectorXd x(d);
    for (int i = 0; i < d; ++i) x(i) = normal(gen);

    assert((R.apply(x) - Rd * x).norm() < 1e-13);
    assert((R.apply_transpose(x) - Rd.transpose() * x).norm() < 1e-13);

    // And the dense matrix really is orthogonal.
    const Eigen::MatrixXd should_be_I = Rd.transpose() * Rd;
    assert((should_be_I - Eigen::MatrixXd::Identity(d, d)).norm() < 1e-12);
    std::cout << "  [ok] apply/apply_transpose agree with the dense oracle\n";
}

void test_identity_is_free_and_exact() {
    const HouseholderMap I = HouseholderMap::identity(kDeployedDim);
    assert(I.m() == 0);
    assert(I.storage_bytes() == 0);
    Eigen::VectorXd x = Eigen::VectorXd::Random(kDeployedDim);
    assert((I.apply(x) - x).norm() == 0.0);
    assert((I.apply_transpose(x) - x).norm() == 0.0);
    // This is the parity hook: identity maps must be BIT-identical to no maps,
    // which is what lets the pre-5p coherence tests keep passing unchanged.
    std::cout << "  [ok] identity is bit-exact and stores zero bytes\n";
}

void test_determinant_sign_tracks_reflection_count() {
    // det(H) = -1 for one reflection, so det(R) = (-1)^m. An even m gives a
    // ROTATION (SO(d)); an odd m gives an improper orthogonal map. Worth
    // knowing: m=4 lands in SO(d), which is the connected component containing
    // the identity, so a Householder map can be deformed continuously back to
    // "no translation at all". That is the right default for a potency ladder
    // whose level 0 is the identity.
    for (int m = 0; m <= 4; ++m) {
        const HouseholderMap R = HouseholderMap::random(9, m, 42u + static_cast<unsigned>(m));
        const double det = R.dense().determinant();
        const double expected = (m % 2 == 0) ? 1.0 : -1.0;
        assert(close(det, expected, 1e-10));
    }
    std::cout << "  [ok] det(R) = (-1)^m, so m=4 is a rotation in SO(d)\n";
}

void test_storage_and_apply_costs() {
    const HouseholderMap R = HouseholderMap::random(kDeployedDim, HOUSEHOLDER_M_DEFAULT, 1);
    const std::size_t dense_bytes =
        static_cast<std::size_t>(kDeployedDim) * kDeployedDim * sizeof(double);
    const std::size_t compact = R.storage_bytes();
    const double ratio = static_cast<double>(dense_bytes) / static_cast<double>(compact);

    std::cout << "  [ok] storage " << compact << " B vs dense " << dense_bytes
              << " B  => " << ratio << "x reduction\n";
    // The ratio is d/m exactly, independent of element size. 5s quotes 96x and
    // "6 KB", the latter being the float32 figure; in double it is 12 KB and
    // the ratio is unchanged.
    assert(close(ratio, static_cast<double>(kDeployedDim) / HOUSEHOLDER_M_DEFAULT, 1e-9));
    assert(compact == 4u * 384u * sizeof(double));

    // The point of the representation is that applying it never touches d^2
    // work. Compare against the dense product on the same map.
    const Eigen::MatrixXd Rd = R.dense();
    Eigen::VectorXd x = Eigen::VectorXd::Random(kDeployedDim);

    const auto t0 = std::chrono::steady_clock::now();
    for (int i = 0; i < 2000; ++i) { volatile double s = R.apply(x).sum(); (void)s; }
    const auto t1 = std::chrono::steady_clock::now();
    for (int i = 0; i < 2000; ++i) { volatile double s = (Rd * x).sum(); (void)s; }
    const auto t2 = std::chrono::steady_clock::now();

    const double compact_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    const double dense_ms = std::chrono::duration<double, std::milli>(t2 - t1).count();
    std::cout << "       apply x2000: compact " << compact_ms << " ms, dense "
              << dense_ms << " ms\n";
    // Deliberately NOT asserted. This is a debug build with bounds checking and
    // a timing assertion here would be a flaky test, not a real guarantee. The
    // O(md) vs O(d^2) claim is structural and is asserted by storage above.
}

void test_degenerate_inputs_are_refused() {
    bool threw = false;
    try {
        HouseholderMap(3, {Eigen::VectorXd::Zero(3)});
    } catch (const std::invalid_argument&) { threw = true; }
    assert(threw && "a zero reflection vector must not be silently treated as identity");

    threw = false;
    try {
        HouseholderMap(3, {Eigen::VectorXd::Ones(4)});
    } catch (const std::invalid_argument&) { threw = true; }
    assert(threw && "a dimension mismatch must be refused");

    threw = false;
    try {
        (void)HouseholderMap::identity(0);
    } catch (const std::invalid_argument&) { threw = true; }
    assert(threw && "d = 0 must be refused");
    std::cout << "  [ok] zero vectors, dimension mismatches and d=0 are refused\n";
}

void test_congruence_preserves_trace() {
    // 5t Q1: Sigma -> R Sigma R^T is a unitary CPTP channel, so it preserves the
    // trace and therefore maps density matrices to density matrices. That claim
    // is the whole basis for reading restriction maps as quantum channels, so it
    // gets a test rather than a footnote.
    const int d = 16;
    const HouseholderMap R = HouseholderMap::random(d, HOUSEHOLDER_M_DEFAULT, 2024);
    const Eigen::MatrixXd Rd = R.dense();

    Eigen::MatrixXd A = Eigen::MatrixXd::Random(d, d);
    const Eigen::MatrixXd Sigma = A * A.transpose();          // SPD
    const Eigen::MatrixXd pushed = Rd * Sigma * Rd.transpose();

    assert(close(pushed.trace(), Sigma.trace(), 1e-10));
    // Congruence by an orthogonal matrix is a similarity, so the SPECTRUM is
    // preserved too -- "same content, different basis", losslessly.
    Eigen::SelfAdjointEigenSolver<Eigen::MatrixXd> es1(Sigma), es2(pushed);
    assert((es1.eigenvalues() - es2.eigenvalues()).cwiseAbs().maxCoeff() < 1e-9);
    std::cout << "  [ok] congruence preserves trace AND spectrum (unitary channel)\n";
}

// ---------------------------------------------------------------------------
// Integration: the compact maps must be usable AS restriction maps, and must
// agree with the dense path they replace. A primitive nothing calls is not an
// implemented Phase-2 item.
// ---------------------------------------------------------------------------

void test_coarse_complex_compact_matches_dense() {
    const int d = 32;
    const HouseholderMap Ru = HouseholderMap::random(d, HOUSEHOLDER_M_DEFAULT, 11);
    const HouseholderMap Rv = HouseholderMap::random(d, HOUSEHOLDER_M_DEFAULT, 22);

    std::mt19937 gen(5);
    std::normal_distribution<double> normal(0.0, 1.0);
    Eigen::VectorXd xa(d), xb(d);
    for (int i = 0; i < d; ++i) { xa(i) = normal(gen); xb(i) = normal(gen); }

    auto build = [&](bool compact) {
        CoarseComplex K(1.0, 0.25);
        K.register_module("a");
        K.register_module("b");
        K.set_stalk("a", xa);
        K.set_stalk("b", xb);
        K.co_activate("a", "b", 2.0);
        if (compact) {
            K.set_restriction_householder("a", "b", Ru, Rv);
        } else {
            K.set_restriction("a", "b", Ru.dense(), Rv.dense());
        }
        return K.report();
    };

    const auto compact = build(true);
    const auto dense = build(false);

    assert(compact.rho.has_value() && dense.rho.has_value());
    assert(close(*compact.rho, *dense.rho, 1e-12));
    assert(close(compact.omega, dense.omega, 1e-12));
    // Both must equally disable the alpha/rho-tilde split: orthogonality does
    // not make ker L the per-component constants again.
    assert(compact.split_status == "non_identity_maps");
    assert(dense.split_status == "non_identity_maps");
    std::cout << "  [ok] compact restriction reproduces the dense rho exactly ("
              << *compact.rho << ")\n";
}

void test_identity_householder_is_a_no_op_in_the_complex() {
    // The parity hook again, now through CoarseComplex: an identity Householder
    // pair must leave rho bit-identical to having no maps at all, or every
    // pre-5p coherence number silently shifts the day maps are switched on.
    const int d = 16;
    std::mt19937 gen(8);
    std::normal_distribution<double> normal(0.0, 1.0);
    Eigen::VectorXd xa(d), xb(d);
    for (int i = 0; i < d; ++i) { xa(i) = normal(gen); xb(i) = normal(gen); }

    CoarseComplex K(1.0, 0.25);
    K.register_module("a");
    K.register_module("b");
    K.set_stalk("a", xa);
    K.set_stalk("b", xb);
    K.co_activate("a", "b", 2.0);

    const double rho_plain = *K.report().rho;
    assert(!K.has_restriction("a", "b"));

    K.set_restriction_householder("a", "b", HouseholderMap::identity(d),
                                  HouseholderMap::identity(d));
    assert(K.has_restriction("a", "b"));
    const double rho_ident = *K.report().rho;

    assert(rho_plain == rho_ident && "identity Householder must be BIT-identical");
    std::cout << "  [ok] identity Householder pair is bit-identical to no maps\n";
}

void test_edge_budget_at_scale() {
    // 5s's actual finding: 2 dense maps/edge at 2000 edges is 2.3 GB on a 5.9 GB
    // machine. State both numbers so the constraint stays visible in the code.
    const std::size_t edges = 2000;
    const std::size_t dense_per_edge =
        2u * static_cast<std::size_t>(kDeployedDim) * kDeployedDim * sizeof(float);
    const std::size_t compact_per_edge =
        2u * HOUSEHOLDER_M_DEFAULT * static_cast<std::size_t>(kDeployedDim) * sizeof(double);

    const double dense_gb = static_cast<double>(edges * dense_per_edge) / (1024.0 * 1024.0 * 1024.0);
    const double compact_mb = static_cast<double>(edges * compact_per_edge) / (1024.0 * 1024.0);
    std::cout << "  [ok] at 2000 edges: dense " << dense_gb << " GB (float32) vs compact "
              << compact_mb << " MB (float64)\n";
    assert(dense_gb > 2.0 && "5s's 2.3 GB finding must still reproduce");
    assert(compact_mb < 64.0 && "the compact form must comfortably fit");
}

}  // namespace

int main() {
    std::cout << "=== Householder restriction maps (Phase-2 item 1) ===\n";
    test_single_reflection_is_its_own_inverse();
    test_orthogonality_is_exact_at_deployed_dimension();
    test_transpose_matches_the_dense_transpose();
    test_identity_is_free_and_exact();
    test_determinant_sign_tracks_reflection_count();
    test_storage_and_apply_costs();
    test_degenerate_inputs_are_refused();
    test_congruence_preserves_trace();

    std::cout << "=== wired into CoarseComplex ===\n";
    test_coarse_complex_compact_matches_dense();
    test_identity_householder_is_a_no_op_in_the_complex();
    test_edge_budget_at_scale();

    std::cout << "\nALL HOUSEHOLDER TESTS PASSED\n";
    return 0;
}
