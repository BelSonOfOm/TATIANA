// Tests for pi_v: precision-weighted Gaussian fusion of concept means.
// Verifies the mathematical properties claimed in the design:
//   1. equal-precision fusion == plain mean
//   2. unequal precision pulls toward the MORE CERTAIN concept
//   3. order-independence (fusion is a commutative/associative accumulation)
//   4. the D-floor keeps a near-certain axiom from numerically swamping everything
//   5. the general low-rank (Woodbury) path agrees with a dense ground-truth solve

#include "mos/core/semantic_skill.hpp"

#include <cassert>
#include <cmath>
#include <iostream>
#include <memory>
#include <vector>

using namespace mos::core;

static std::shared_ptr<const SemanticEmbedding>
iso(const Eigen::VectorXd& mu, double D) {
  return std::make_shared<SemanticEmbedding>(mu, Eigen::MatrixXd(mu.size(), 0), D,
                                             "c");
}

static bool close(const Eigen::VectorXd& a, const Eigen::VectorXd& b,
                  double tol = 1e-9) {
  return (a - b).cwiseAbs().maxCoeff() < tol;
}

int main() {
  std::cout << "=== pi_v fusion tests ===\n\n";

  Eigen::VectorXd a(3);
  a << 1.0, 0.0, 0.0;
  Eigen::VectorXd b(3);
  b << 0.0, 1.0, 0.0;
  Eigen::VectorXd c(3);
  c << 0.0, 0.0, 1.0;

  // 1. equal precision -> plain mean
  {
    std::vector<std::shared_ptr<const SemanticEmbedding>> cs = {
        iso(a, 1.0), iso(b, 1.0), iso(c, 1.0)};
    Eigen::VectorXd got = fuse_concept_means(cs);
    Eigen::VectorXd expected = (a + b + c) / 3.0;
    std::cout << "1. equal precision   -> [" << got.transpose() << "]\n";
    assert(close(got, expected));
  }

  // 2. unequal precision pulls toward the more certain concept
  {
    // a has 9x the precision of b (D = 1/9 vs 1) -> weights 0.9 : 0.1
    std::vector<std::shared_ptr<const SemanticEmbedding>> cs = {iso(a, 1.0 / 9.0),
                                                                iso(b, 1.0)};
    Eigen::VectorXd got = fuse_concept_means(cs);
    Eigen::VectorXd expected = 0.9 * a + 0.1 * b;
    std::cout << "2. 9:1 precision     -> [" << got.transpose()
              << "]  (should sit near a)\n";
    assert(close(got, expected));
    assert(got(0) > 0.8 && "must be pulled toward the certain concept a");
  }

  // 3. order-independence
  {
    std::vector<std::shared_ptr<const SemanticEmbedding>> fwd = {
        iso(a, 0.5), iso(b, 2.0), iso(c, 1.0)};
    std::vector<std::shared_ptr<const SemanticEmbedding>> rev = {
        iso(c, 1.0), iso(b, 2.0), iso(a, 0.5)};
    Eigen::VectorXd g1 = fuse_concept_means(fwd);
    Eigen::VectorXd g2 = fuse_concept_means(rev);
    std::cout << "3. order-independent -> maxdiff = "
              << (g1 - g2).cwiseAbs().maxCoeff() << "\n";
    assert(close(g1, g2));
  }

  // 4. D-floor: a near-zero-D axiom dominates but does not explode
  {
    std::vector<std::shared_ptr<const SemanticEmbedding>> cs = {
        iso(a, 1e-300), iso(b, 1.0)};
    Eigen::VectorXd got = fuse_concept_means(cs);  // default d_floor = 1e-6
    std::cout << "4. near-certain axiom-> [" << got.transpose()
              << "]  (finite, ~a)\n";
    assert(std::isfinite(got(0)) && std::isfinite(got(1)));
    assert(got(0) > 0.999 && "near-certain axiom should dominate pi_v");
  }

  // 5. general low-rank path agrees with a dense ground-truth information solve
  {
    Eigen::VectorXd mu1(3);
    mu1 << 1.0, 2.0, 3.0;
    Eigen::VectorXd mu2(3);
    mu2 << -1.0, 0.5, 1.0;
    Eigen::MatrixXd U1(3, 1);
    U1 << 0.5, 0.2, -0.1;
    Eigen::MatrixXd U2(3, 2);
    U2 << 0.3, 0.0, -0.2, 0.4, 0.1, 0.1;
    double D1 = 0.7, D2 = 1.3;

    auto e1 = std::make_shared<SemanticEmbedding>(mu1, U1, D1, "e1");
    auto e2 = std::make_shared<SemanticEmbedding>(mu2, U2, D2, "e2");
    Eigen::VectorXd got = fuse_concept_means({e1, e2});

    // Dense ground truth: Lambda = S1^-1 + S2^-1, mu* = Lambda^-1 (S1^-1 mu1 + S2^-1 mu2)
    Eigen::MatrixXd S1 = U1 * U1.transpose() + D1 * Eigen::MatrixXd::Identity(3, 3);
    Eigen::MatrixXd S2 = U2 * U2.transpose() + D2 * Eigen::MatrixXd::Identity(3, 3);
    Eigen::MatrixXd S1i = S1.inverse();
    Eigen::MatrixXd S2i = S2.inverse();
    Eigen::VectorXd truth = (S1i + S2i).inverse() * (S1i * mu1 + S2i * mu2);

    std::cout << "5. low-rank Woodbury -> maxdiff vs dense = "
              << (got - truth).cwiseAbs().maxCoeff() << "\n";
    assert(close(got, truth, 1e-8) &&
           "Woodbury fast path must equal the dense information solve");
  }

  // --- E4: W_2^2 split into semantic + epistemic --------------------------
  {
    const int d = 384;                       // the deployed embedding dimension
    Eigen::VectorXd p = Eigen::VectorXd::Zero(d); p(0) = 1.0;   // unit-normalised
    Eigen::VectorXd q = Eigen::VectorXd::Zero(d); q(1) = 1.0;   // orthogonal to p
    Eigen::MatrixXd noU(d, 0);

    // (a) TODAY'S REGIME. Every grown concept carries GROWN_CONCEPT_VARIANCE_PRIOR
    // = 1.0 with empty U, so the covariances are identical and the epistemic term
    // vanishes EXACTLY: the whole optimal-transport apparatus degenerates to
    // squared Euclidean distance. Not wrong -- just currently doing nothing.
    auto today = wasserstein_2_terms(p, 1.0, q, noU, 1.0);
    std::cout << "6. today (D1=D2=1.0, no U): semantic=" << today.semantic
              << " epistemic=" << today.epistemic << "\n";
    assert(std::abs(today.epistemic) < 1e-9 &&
           "equal isotropic covariances must give exactly zero epistemic distance");
    assert(std::abs(today.semantic - (p - q).squaredNorm()) < 1e-12);
    assert(std::abs(today.total() - (p - q).squaredNorm()) < 1e-9 &&
           "W_2^2 must degenerate to squared Euclidean distance in this regime");

    // (b) THE LATENT BUG, which switches on when calibration is FIXED. An
    // uncalibrated prior D1 = 1.0 against a confident concept c = 0.95
    // (D2 = -ln 0.95) makes the epistemic term d*(sqrt(D1)-sqrt(D2))^2 ~= 230,
    // while semantic is bounded by 4. Merge decisions would then be driven almost
    // entirely by a self-reported confidence the architecture declines to trust.
    const double D2 = -std::log(0.95);
    auto tomorrow = wasserstein_2_terms(p, 1.0, q, noU, D2);
    const double closed_form = d * std::pow(1.0 - std::sqrt(D2), 2.0);
    std::cout << "   tomorrow (D1=1.0, D2=-ln0.95): semantic=" << tomorrow.semantic
              << " epistemic=" << tomorrow.epistemic
              << "  ratio=" << (tomorrow.epistemic / tomorrow.semantic) << ":1\n";
    assert(std::abs(tomorrow.epistemic - closed_form) < 1e-6 &&
           "isotropic epistemic term must equal d*(sqrt(D1)-sqrt(D2))^2 exactly");
    assert(tomorrow.epistemic > 50.0 * tomorrow.semantic &&
           "this is the hazard: certainty outweighs meaning by ~57x at d=384");
    // The semantic term is UNCHANGED by the confidence shift -- which is exactly
    // the point of separating them.
    assert(std::abs(tomorrow.semantic - today.semantic) < 1e-12 &&
           "semantic distance must not move when only confidence changes");

    // (c) Both terms non-negative, and the split agrees with the scalar total.
    Eigen::MatrixXd U2(d, 2);
    U2.setZero(); U2(0, 0) = 0.7; U2(3, 1) = 0.4;
    auto lr = wasserstein_2_terms(p, 0.5, q, U2, 0.2);
    assert(lr.semantic >= 0.0 && lr.epistemic >= 0.0);
    assert(std::abs(lr.total() - (lr.semantic + lr.epistemic)) < 1e-12);
    std::cout << "   low-rank k=2: semantic=" << lr.semantic
              << " epistemic=" << lr.epistemic << " total=" << lr.total() << "\n";
  }

  std::cout << "\nALL PI_V FUSION TESTS PASSED\n";
  return 0;
}
