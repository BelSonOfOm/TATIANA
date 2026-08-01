// Phase-2 item 2: the Hodge split via LSQR.
//
// The expected numbers below were generated from python/hodge.py, which is
// authoritative. They are hard-coded rather than recomputed so that a change to
// either implementation breaks this test instead of both drifting together.
//
// The configuration is E5's: 4 organs, 5 edges, 1 FILLED triangle, giving
// dim C^1 = 5 = 3 (grad) + 1 (curl) + 1 (harm), i.e. b1 = 1. The original
// "one filled triangle" design had b1 = 0 and could detect NO harmonic mass at
// all -- which is why the dimension assertions here are not decoration.

#include <cassert>
#include <cmath>
#include <iostream>
#include <random>
#include <stdexcept>
#include <vector>

#include "mos/core/hodge.hpp"

using namespace mos::core;

namespace {

constexpr double kTol = 1e-12;

bool close(double a, double b, double tol = kTol) {
    return std::fabs(a - b) <= tol * std::max(1.0, std::max(std::fabs(a), std::fabs(b)));
}

void expect_vec(const char* label, const Eigen::VectorXd& got,
                const std::vector<double>& want, double tol = kTol) {
    assert(static_cast<std::size_t>(got.size()) == want.size());
    for (std::size_t i = 0; i < want.size(); ++i) {
        if (!close(got(static_cast<int>(i)), want[i], tol)) {
            std::cerr << "  [FAIL] " << label << "[" << i << "] expected " << want[i]
                      << " got " << got(static_cast<int>(i)) << "\n";
            assert(false);
        }
    }
}

Complex2 e5_complex() {
    return Complex2({"A", "B", "C", "D"},
                    {{"A", "B"}, {"B", "C"}, {"A", "C"}, {"A", "D"}, {"C", "D"}},
                    {{"A", "B", "C"}});
}

Eigen::VectorXd vec5(double a, double b, double c, double d, double e) {
    Eigen::VectorXd v(5);
    v << a, b, c, d, e;
    return v;
}

// --------------------------------------------------------------------------

void test_delta1_delta0_is_zero() {
    // delta^1 . delta^0 = 0 is THE cochain identity. If it fails, the signs or
    // the orientation handling are wrong and every split below is meaningless.
    const Complex2 cx = e5_complex();
    std::mt19937 gen(3);
    std::normal_distribution<double> normal(0.0, 1.0);
    for (int trial = 0; trial < 20; ++trial) {
        Eigen::VectorXd f(cx.num_vertices());
        for (int i = 0; i < f.size(); ++i) f(i) = normal(gen);
        const Eigen::VectorXd out = cx.apply_delta1(cx.apply_delta0(f));
        assert(out.norm() < 1e-14);
    }
    std::cout << "  [ok] delta^1 . delta^0 = 0 (signs and orientations agree)\n";
}

void test_adjoints_are_actual_adjoints() {
    // <A x, y> = <x, A^T y> for random x, y. A transpose that is not the
    // adjoint makes LSQR silently solve a different problem.
    const Complex2 cx = e5_complex();
    std::mt19937 gen(7);
    std::normal_distribution<double> normal(0.0, 1.0);
    for (int trial = 0; trial < 20; ++trial) {
        Eigen::VectorXd f(cx.num_vertices()), x(cx.num_edges()), y(cx.num_triangles());
        for (int i = 0; i < f.size(); ++i) f(i) = normal(gen);
        for (int i = 0; i < x.size(); ++i) x(i) = normal(gen);
        for (int i = 0; i < y.size(); ++i) y(i) = normal(gen);
        assert(close(cx.apply_delta0(f).dot(x), f.dot(cx.apply_delta0T(x))));
        assert(close(cx.apply_delta1(x).dot(y), x.dot(cx.apply_delta1T(y))));
    }
    std::cout << "  [ok] apply_delta0T / apply_delta1T are the true adjoints\n";
}

void test_uniform_split_matches_python() {
    const Complex2 cx = e5_complex();
    const HodgeSplit r = hodge_split(cx, vec5(0.7, -0.3, 0.45, 0.9, -0.15));

    assert(r.dim_grad == 3 && r.dim_curl == 1 && r.dim_harm == 1);
    expect_vec("grad", r.grad,
               {0.7937500000000002, -0.20624999999999993, 0.5875000000000002,
                0.6687500000000003, 0.08125000000000004});
    expect_vec("curl", r.curl,
               {-0.016666666666666708, -0.016666666666666708, 0.016666666666666708, 0.0, 0.0});
    expect_vec("harm", r.harm,
               {-0.07708333333333352, -0.07708333333333335, -0.15416666666666695,
                0.23124999999999973, -0.23125000000000004});
    assert(close(r.norm2, 1.615));
    assert(close(r.grad2, 1.4715625000000008));
    assert(close(r.curl2, 0.0008333333333333374));
    assert(close(r.harm2, 0.1426041666666667));
    std::cout << "  [ok] uniform split matches python/hodge.py to 1e-12\n";
}

void test_weighted_split_matches_python() {
    const Complex2 cx = e5_complex();
    const std::map<HodgeEdge, double> pi{
        {{"A", "B"}, 2.0}, {{"B", "C"}, 0.5}, {{"A", "C"}, 1.5},
        {{"A", "D"}, 3.0}, {{"C", "D"}, 0.25}};
    const HodgeSplit r = hodge_split(cx, vec5(0.7, -0.3, 0.45, 0.9, -0.15), pi);

    expect_vec("W-grad", r.grad,
               {0.721119133574007, -0.21552346570397113, 0.505595667870036,
                0.8581227436823102, 0.3525270758122742});
    expect_vec("W-harm", r.harm,
               {-0.013224396731901834, -0.05289758692760789, -0.06612198365950961,
                0.04187725631768979, -0.5025270758122742});
    assert(close(r.norm2, 3.7643750000000002));
    assert(close(r.grad2, 3.6868840252707562));
    assert(close(r.curl2, 0.00078947368421052229));
    assert(close(r.harm2, 0.076701501045031331));
    std::cout << "  [ok] pi-weighted split matches python/hodge.py to 1e-12\n";
}

void test_pure_gradient_has_no_harmonic_mass() {
    // The sharpest sanity check: eta = delta^0 f must be ALL gradient. If any
    // harmonic mass appears here, the instrument would report a hole where the
    // organs are merely consistently offset -- a fabricated growth address.
    const Complex2 cx = e5_complex();
    Eigen::VectorXd f(4);
    f << 0.1, -0.4, 0.9, 0.25;
    const HodgeSplit r = hodge_split(cx, cx.apply_delta0(f));

    assert(r.curl2 == 0.0 && "delta^1 delta^0 = 0, so the curl part is exactly zero");
    assert(r.harm2 < 1e-28);
    assert(close(r.grad2, 3.024999999999999));
    std::cout << "  [ok] a pure gradient splits as pure gradient (harm2 = "
              << r.harm2 << ")\n";
}

void test_null_fractions_are_the_number_to_beat() {
    // A COMPLETELY RANDOM instrument scores harm+curl = 0.40 in this
    // configuration, not 0. Quoting a raw 0.4 as success would be the single
    // easiest way to fool ourselves here.
    const Complex2 cx = e5_complex();
    const HodgeSplit r = hodge_split(cx, vec5(0.7, -0.3, 0.45, 0.9, -0.15));
    const auto [ng, nc, nh] = r.null_fractions();
    assert(close(ng, 0.6) && close(nc, 0.2) && close(nh, 0.2));

    const auto [g, c, h] = r.fractions();
    assert(close(g + c + h, 1.0));
    // This eta is MORE gradient-like than noise: excess must be negative.
    assert(r.excess_non_gradient() < 0.0);
    std::cout << "  [ok] null = (0.60, 0.20, 0.20); excess_non_gradient = "
              << r.excess_non_gradient() << " (negative => more gradient-like than noise)\n";
}

void test_harmonic_support_is_the_growth_address() {
    const Complex2 cx = e5_complex();
    const HodgeSplit r = hodge_split(cx, vec5(0.7, -0.3, 0.45, 0.9, -0.15));
    const auto top = r.harmonic_support(cx, 2);
    assert(top.size() == 2);
    // The unfilled cycle is A-D-C, so its edges must carry the harmonic mass --
    // NOT the edges of the filled triangle, whose inconsistency is curl.
    const bool ad = top[0].first == HodgeEdge{"A", "D"} || top[1].first == HodgeEdge{"A", "D"};
    const bool cd = top[0].first == HodgeEdge{"C", "D"} || top[1].first == HodgeEdge{"C", "D"};
    assert(ad && cd);
    std::cout << "  [ok] harmonic support points at the UNFILLED cycle (A,D),(C,D)\n";
}

void test_orthogonality_holds_on_random_complexes() {
    // Pythagoras across many random complexes and cochains, including weighted
    // inner products. This is what would break first if LSQR stopped early.
    std::mt19937 gen(11);
    std::normal_distribution<double> normal(0.0, 1.0);
    std::uniform_real_distribution<double> pos(0.25, 4.0);

    const Complex2 cx = e5_complex();
    for (int trial = 0; trial < 200; ++trial) {
        Eigen::VectorXd eta(cx.num_edges());
        for (int i = 0; i < eta.size(); ++i) eta(i) = normal(gen);

        std::map<HodgeEdge, double> pi;
        for (const auto& e : cx.edges()) pi[e] = pos(gen);

        for (int weighted = 0; weighted < 2; ++weighted) {
            const HodgeSplit r =
                weighted ? hodge_split(cx, eta, pi) : hodge_split(cx, eta);
            const double sum = r.grad2 + r.curl2 + r.harm2;
            assert(std::fabs(r.norm2 - sum) <= 1e-10 * std::max(1.0, r.norm2));
            // Cross terms must vanish too, in the SAME inner product.
            double gc = 0.0, gh = 0.0, ch = 0.0;
            for (int i = 0; i < cx.num_edges(); ++i) {
                const double w = weighted ? pi.at(cx.edges()[i]) : 1.0;
                gc += w * r.grad(i) * r.curl(i);
                gh += w * r.grad(i) * r.harm(i);
                ch += w * r.curl(i) * r.harm(i);
            }
            const double s = std::max(1.0, r.norm2);
            assert(std::fabs(gc) < 1e-9 * s && std::fabs(gh) < 1e-9 * s &&
                   std::fabs(ch) < 1e-9 * s);
        }
    }
    std::cout << "  [ok] Pythagoras AND pairwise orthogonality hold over 400 splits\n";
}

void test_lsqr_solves_a_known_least_squares_problem() {
    // LSQR against a dense reference, on an INCONSISTENT overdetermined system
    // (where testing ||r|| instead of ||A^T r|| would stop at the wrong place).
    const int m = 40, n = 12;
    std::mt19937 gen(21);
    std::normal_distribution<double> normal(0.0, 1.0);
    Eigen::MatrixXd A(m, n);
    Eigen::VectorXd b(m);
    for (int i = 0; i < m; ++i) {
        for (int j = 0; j < n; ++j) A(i, j) = normal(gen);
        b(i) = normal(gen);
    }
    const Eigen::VectorXd want = A.colPivHouseholderQr().solve(b);
    const LsqrResult got = lsqr([&](const Eigen::VectorXd& x) { return Eigen::VectorXd(A * x); },
                                [&](const Eigen::VectorXd& y) { return Eigen::VectorXd(A.transpose() * y); },
                                b, n);
    assert(got.converged);
    assert((got.x - want).norm() < 1e-9 * std::max(1.0, want.norm()));
    std::cout << "  [ok] LSQR matches a dense QR least-squares solve in "
              << got.iterations << " iterations (n=" << n << ")\n";
}

void test_rank_deficient_lsqr_gives_minimum_norm() {
    // delta^0 is ALWAYS rank-deficient (constants are in its kernel), so this is
    // the case that actually occurs, not a corner. numpy's lstsq returns the
    // minimum-norm solution and LSQR from x=0 must agree.
    const Complex2 cx = e5_complex();
    Eigen::VectorXd eta(5);
    eta << 0.7, -0.3, 0.45, 0.9, -0.15;
    const HodgeSplit r = hodge_split(cx, eta);
    // NON-TRIVIALITY FIRST. An earlier version of this test asserted only that
    // delta^0(potential) == grad, which BOTH SATISFY WHEN BOTH ARE ZERO -- and
    // that is exactly what happened while an Eigen dangling-temporary bug made
    // LSQR return garbage near 1e-124. The test passed and the split was wrong.
    assert(r.potential.norm() > 0.1 && "a zero potential would make this vacuous");
    assert(r.grad.norm() > 0.1 && "a zero gradient would make this vacuous");

    // Mean-zero is the canonical representative; assert it explicitly.
    assert(std::fabs(r.potential.mean()) < 1e-12);
    // And the potential must actually generate the gradient part.
    assert((cx.apply_delta0(r.potential) - r.grad).norm() < 1e-12);
    std::cout << "  [ok] potential is non-trivial, mean-zero, and reproduces grad\n";
}

void test_refusals() {
    const Complex2 cx = e5_complex();
    bool threw;

    // Downward closure: a triangle whose face is missing changes b1 silently.
    threw = false;
    try {
        Complex2 bad({"A", "B", "C"}, {{"A", "B"}, {"B", "C"}}, {{"A", "B", "C"}});
    } catch (const std::invalid_argument&) { threw = true; }
    assert(threw && "a triangle without all three faces must be refused");

    // A partial precision map is a missing measurement, not a weight of 1.
    threw = false;
    try {
        std::map<HodgeEdge, double> partial{{{"A", "B"}, 1.0}};
        (void)hodge_split(cx, vec5(1, 0, 0, 0, 0), partial);
    } catch (const std::invalid_argument&) { threw = true; }
    assert(threw && "a partial precision map must be refused");

    // pi_e = 0 would delete the edge from the inner product but not the complex.
    threw = false;
    try {
        std::map<HodgeEdge, double> zero{
            {{"A", "B"}, 0.0}, {{"B", "C"}, 1.0}, {{"A", "C"}, 1.0},
            {{"A", "D"}, 1.0}, {{"C", "D"}, 1.0}};
        (void)hodge_split(cx, vec5(1, 0, 0, 0, 0), zero);
    } catch (const std::invalid_argument&) { threw = true; }
    assert(threw && "pi_e = 0 must be refused");

    // Wrong-length eta.
    threw = false;
    try { (void)hodge_split(cx, Eigen::VectorXd::Zero(4)); }
    catch (const std::invalid_argument&) { threw = true; }
    assert(threw && "an eta of the wrong length must be refused");

    // Self-loop and duplicate edge.
    threw = false;
    try { Complex2 bad({"A"}, {{"A", "A"}}); }
    catch (const std::invalid_argument&) { threw = true; }
    assert(threw && "a self-loop is not a 1-simplex");

    std::cout << "  [ok] closure, partial/zero precision, bad shapes are all refused\n";
}

void test_disconnected_complex_uses_b0() {
    // dim(gradient) = V - b0, NOT V - 1. Two components means the constants are
    // two-dimensional, and getting this wrong shifts harmonic dimension -- i.e.
    // it would invent or destroy a hole.
    const Complex2 cx({"A", "B", "C", "D"}, {{"A", "B"}, {"C", "D"}});
    assert(cx.b0() == 2);
    Eigen::VectorXd eta(2);
    eta << 0.5, -0.25;
    const HodgeSplit r = hodge_split(cx, eta);
    assert(r.dim_grad == 2 && r.dim_curl == 0 && r.dim_harm == 0);
    // With no cycles and no triangles, everything is gradient.
    assert(close(r.grad2, r.norm2) && r.harm2 < 1e-24);
    std::cout << "  [ok] disconnected complex: dim_grad = V - b0 = 2, all gradient\n";
}

}  // namespace

int main() {
    std::cout << "=== Hodge split via LSQR (Phase-2 item 2) ===\n";
    test_delta1_delta0_is_zero();
    test_adjoints_are_actual_adjoints();
    test_lsqr_solves_a_known_least_squares_problem();
    test_rank_deficient_lsqr_gives_minimum_norm();

    std::cout << "=== parity with python/hodge.py ===\n";
    test_uniform_split_matches_python();
    test_weighted_split_matches_python();
    test_pure_gradient_has_no_harmonic_mass();

    std::cout << "=== the diagnostic ===\n";
    test_null_fractions_are_the_number_to_beat();
    test_harmonic_support_is_the_growth_address();
    test_orthogonality_holds_on_random_complexes();
    test_disconnected_complex_uses_b0();
    test_refusals();

    std::cout << "\nALL HODGE TESTS PASSED\n";
    return 0;
}
