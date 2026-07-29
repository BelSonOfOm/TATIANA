#include <iostream>
#include <cassert>
#include "mos/core/semantic_skill.hpp"
#include <cmath>

using namespace mos;

void test_bayesian_update() {
    // Vertex A: high variance (uncertainty)
    Eigen::VectorXd mu_A(2);
    mu_A << 1.0, -1.0;
    Eigen::MatrixXd U_A = Eigen::MatrixXd::Zero(2, 2);
    double D_A = 2.0;
    core::SemanticEmbedding A(mu_A, U_A, D_A, "Agent A");

    // Vertex B: low variance (high certainty)
    Eigen::VectorXd mu_B(2);
    mu_B << 0.0, 0.5;
    Eigen::MatrixXd U_B = Eigen::MatrixXd::Zero(2, 2);
    double D_B = 0.1;
    core::SemanticEmbedding B(mu_B, U_B, D_B, "Agent B");

    // Merge B into A
    A.merge_with(B);

    const auto& mu_new = A.get_mu();
    double var_new = A.get_D();

    // Mathematically, the new mean should be very close to B's mean (0.0, 0.5)
    // For x: (1.0 * 0.1 + 0.0 * 2.0) / 2.1 = 0.1 / 2.1 = 0.0476
    // For y: (-1.0 * 0.1 + 0.5 * 2.0) / 2.1 = 0.9 / 2.1 = 0.4285
    assert(std::abs(mu_new[0] - 0.0476) < 1e-3);
    assert(std::abs(mu_new[1] - 0.4285) < 1e-3);

    // The new variance should be smaller than both
    // (2.0 * 0.1) / 2.1 = 0.2 / 2.1 = 0.0952
    assert(std::abs(var_new - 0.0952) < 1e-3);
    assert(var_new < D_A);
    assert(var_new < D_B);

    std::cout << "test_bayesian_update passed.\n";
}

int main() {
    test_bayesian_update();
    return 0;
}
