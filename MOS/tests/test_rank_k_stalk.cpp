// Phase-2 item 8: rank-k SPD stalks in C++.
//
// Three claims carry this file, and all three are checked against a dense oracle
// rather than against themselves:
//   * Woodbury gives the exact precision without forming Sigma^-1.
//   * Orthogonal congruence PRESERVES the rank-k form, the trace and the
//     spectrum -- which is what makes 5t Q1's "restriction maps are unitary CPTP
//     channels" a fact rather than an analogy.
//   * The low-rank economy is real at the deployed d = 384.

#include <cassert>
#include <cmath>
#include <iostream>
#include <random>
#include <stdexcept>
#include <vector>

#include "mos/core/rank_k_stalk.hpp"

using namespace mos::core;

namespace {

constexpr int kDeployedDim = 384;   // bge-small-en-v1.5, FIX-1's contract

bool close(double a, double b, double tol = 1e-10) {
    return std::fabs(a - b) <= tol * std::max(1.0, std::max(std::fabs(a), std::fabs(b)));
}

std::vector<Eigen::VectorXd> random_observations(int d, int n, unsigned seed) {
    std::mt19937 gen(seed);
    std::normal_distribution<double> normal(0.0, 1.0);
    std::vector<Eigen::VectorXd> out;
    for (int i = 0; i < n; ++i) {
        Eigen::VectorXd v(d);
        for (int j = 0; j < d; ++j) v(j) = normal(gen);
        out.push_back(v.normalized());   // unit embeddings, per FIX-1's contract
    }
    return out;
}

// ---------------------------------------------------------------------------

void test_woodbury_is_exact() {
    // Sigma^-1 x by Woodbury vs a dense solve. The only inverse Woodbury takes is
    // k x k, so this is O(dk + k^3) against O(d^3).
    std::mt19937 gen(4);
    std::normal_distribution<double> normal(0.0, 1.0);
    for (const int d : {8, 32, 64}) {
        for (const int k : {0, 1, 3, 7}) {
            Eigen::MatrixXd U(d, k);
            for (int i = 0; i < d; ++i)
                for (int j = 0; j < k; ++j) U(i, j) = normal(gen);
            const RankKStalk s(Eigen::VectorXd::Zero(d), U, 0.05);

            Eigen::VectorXd x(d);
            for (int i = 0; i < d; ++i) x(i) = normal(gen);

            const Eigen::VectorXd got = s.precision_apply(x);
            const Eigen::VectorXd want = s.dense_covariance().ldlt().solve(x);
            assert((got - want).norm() < 1e-9 * std::max(1.0, want.norm()));

            // And Sigma * Sigma^-1 x == x, the round trip.
            assert((s.covariance_apply(got) - x).norm() < 1e-9 * std::max(1.0, x.norm()));
        }
    }
    std::cout << "  [ok] Woodbury precision matches a dense solve; Sigma Sigma^-1 = I\n";
}

void test_trace_and_logdet_match_the_dense_oracle() {
    std::mt19937 gen(9);
    std::normal_distribution<double> normal(0.0, 1.0);
    for (const int k : {0, 1, 5}) {
        const int d = 24;
        Eigen::MatrixXd U(d, k);
        for (int i = 0; i < d; ++i)
            for (int j = 0; j < k; ++j) U(i, j) = normal(gen);
        const RankKStalk s(Eigen::VectorXd::Zero(d), U, 0.03);

        const Eigen::MatrixXd S = s.dense_covariance();
        assert(close(s.trace(), S.trace()));
        // log det via the closed form vs an LDLT of the dense matrix.
        const Eigen::LDLT<Eigen::MatrixXd> ldlt(S);
        double dense_logdet = 0.0;
        for (Eigen::Index i = 0; i < ldlt.vectorD().size(); ++i) {
            dense_logdet += std::log(ldlt.vectorD()(i));
        }
        assert(close(s.log_det(), dense_logdet, 1e-8));
    }
    std::cout << "  [ok] trace and log_det agree with the dense covariance\n";
}

void test_congruence_is_a_unitary_channel() {
    // THE Q1 claim. R Sigma R^T must preserve the rank-k FORM (so the
    // representation is closed), the TRACE (so the density matrix is unchanged
    // as an object) and the SPECTRUM (so it is unitary, not merely trace-
    // preserving). Anything less and "CPTP channel" is decoration.
    const int d = 32, k = 5;
    std::mt19937 gen(15);
    std::normal_distribution<double> normal(0.0, 1.0);
    Eigen::MatrixXd U(d, k);
    for (int i = 0; i < d; ++i)
        for (int j = 0; j < k; ++j) U(i, j) = normal(gen);
    Eigen::VectorXd mu(d);
    for (int i = 0; i < d; ++i) mu(i) = normal(gen);

    const RankKStalk s(mu, U, 0.02);
    const auto R = HouseholderMap::random(d, HOUSEHOLDER_M_DEFAULT, 33);
    const RankKStalk t = s.congruence(R);

    assert(t.k() == s.k() && "the rank-k form must be PRESERVED, not approximated");
    assert(close(t.D(), s.D()) && "the floor is untouched: R (D I) R^T = D I exactly");
    assert(close(t.trace(), s.trace()) && "trace preserved => trace-preserving map");

    // Spectrum, to machine precision.
    const Eigen::VectorXd es = s.dense_covariance().selfadjointView<Eigen::Lower>().eigenvalues();
    const Eigen::VectorXd et = t.dense_covariance().selfadjointView<Eigen::Lower>().eigenvalues();
    assert((es - et).norm() < 1e-10 && "spectrum preserved => UNITARY channel");

    // And it really is the congruence, not something that merely looks like one.
    const Eigen::MatrixXd Rd = R.dense();
    assert((t.dense_covariance() - Rd * s.dense_covariance() * Rd.transpose()).norm() < 1e-10);
    std::cout << "  [ok] congruence preserves rank-k form, trace AND spectrum\n";
}

void test_density_matrix_has_trace_one() {
    const auto obs = random_observations(16, 5, 2);
    const RankKStalk s = RankKStalk::from_observations(obs);
    const Eigen::MatrixXd rho = s.density_matrix();
    assert(close(rho.trace(), 1.0));
    // SPD: every eigenvalue strictly positive, which the floor guarantees.
    const Eigen::VectorXd ev = rho.selfadjointView<Eigen::Lower>().eigenvalues();
    assert(ev.minCoeff() > 0.0 && "the floor makes Sigma strictly positive definite");
    std::cout << "  [ok] rho = Sigma/Tr Sigma has trace 1 and is SPD\n";
}

void test_low_rank_economy_at_the_deployed_dimension() {
    // 5 concepts at d = 384 must give k = 5, NOT 384. If the floor were folded
    // into U the rank would be d and the whole economy would be gone.
    const auto obs = random_observations(kDeployedDim, 5, 11);
    const RankKStalk s = RankKStalk::from_observations(obs);
    assert(s.d() == kDeployedDim);
    assert(s.k() <= 5 && "rank <= n, not d");

    const std::size_t dense_bytes =
        static_cast<std::size_t>(kDeployedDim) * kDeployedDim * sizeof(double);
    assert(s.storage_bytes() * 20 < dense_bytes && "must be far smaller than dense");
    std::cout << "  [ok] d=384, n=5 -> k=" << s.k() << "; " << s.storage_bytes()
              << " B vs " << dense_bytes << " B dense ("
              << (dense_bytes / s.storage_bytes()) << "x)\n";
}

void test_floor_is_the_fix13_contract() {
    // FIX-13: the floor must be O(1/d) so the covariance carries trace O(1).
    // A shared constant floor would make every C++ entropy identical and every
    // W_2 Euclidean -- silently.
    const auto obs = random_observations(kDeployedDim, 3, 5);
    const RankKStalk s = RankKStalk::from_observations(obs);
    const double expected = stalk_floor(kDeployedDim, 3.0, 1.0);
    assert(close(s.D(), expected) && "must use the shared stalk_floor, not a constant");

    // The isotropic part of the trace is d*D, which must stay O(1).
    const double isotropic_trace = static_cast<double>(kDeployedDim) * s.D();
    assert(isotropic_trace < 2.0 && "trace O(1), per FIX-13");
    std::cout << "  [ok] floor = stalk_floor(384, n, kappa) = " << s.D()
              << "; isotropic trace = " << isotropic_trace << " (O(1))\n";
}

void test_repeated_observations_do_not_inflate_rank() {
    // Five copies of one vector is ONE direction of evidence, not five.
    const int d = 16;
    Eigen::VectorXd v = Eigen::VectorXd::Ones(d).normalized();
    const std::vector<Eigen::VectorXd> same(5, v);
    const RankKStalk s = RankKStalk::from_observations(same);
    assert(s.k() == 0 && "identical observations have zero scatter");
    // With no learned directions the stalk is isotropic at the floor.
    assert(close(s.trace(), static_cast<double>(d) * s.D()));
    std::cout << "  [ok] 5 identical observations give k=0, not k=5\n";
}

void test_refusals() {
    bool threw = false;
    try { (void)RankKStalk(Eigen::VectorXd::Zero(4), Eigen::MatrixXd::Zero(4, 2), 0.0); }
    catch (const std::invalid_argument&) { threw = true; }
    assert(threw && "a zero floor is infinite confidence and must be refused");

    threw = false;
    try { (void)RankKStalk(Eigen::VectorXd::Zero(4), Eigen::MatrixXd::Zero(3, 2), 0.1); }
    catch (const std::invalid_argument&) { threw = true; }
    assert(threw && "U rows must match mu");

    threw = false;
    try { (void)RankKStalk::from_observations({}); }
    catch (const std::invalid_argument&) { threw = true; }
    assert(threw && "no observations must not silently produce an isotropic prior");

    threw = false;
    try {
        const RankKStalk s = RankKStalk::isotropic(Eigen::VectorXd::Zero(8), 0.1);
        (void)s.congruence(HouseholderMap::random(9, 4, 1));
    } catch (const std::invalid_argument&) { threw = true; }
    assert(threw && "a congruence of the wrong dimension must be refused");
    std::cout << "  [ok] zero floor, ragged U, empty observations, bad congruence refused\n";
}

}  // namespace

int main() {
    std::cout << "=== rank-k SPD stalks (Phase-2 item 8, Q1) ===\n";
    test_woodbury_is_exact();
    test_trace_and_logdet_match_the_dense_oracle();
    test_congruence_is_a_unitary_channel();
    test_density_matrix_has_trace_one();
    test_low_rank_economy_at_the_deployed_dimension();
    test_floor_is_the_fix13_contract();
    test_repeated_observations_do_not_inflate_rank();
    test_refusals();

    std::cout << "\nALL RANK-K STALK TESTS PASSED\n";
    return 0;
}
