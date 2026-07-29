#include <iostream>
#include <cassert>
#include <memory>
#include "mos/core/cognitive_state.hpp"
#include "mos/core/operad.hpp"
#include "mos/core/kernel.hpp"
#include "mos/core/semantic_skill.hpp"
#include "mos/operators/edge_contraction.hpp"
#include "mos/operators/expansion.hpp"

using namespace mos;

void test_foliation_and_kernel() {
    // 1. Setup a Cognitive State with high conflict (divergent embeddings)
    core::CognitiveState state;
    
    // Concept A
    Eigen::VectorXd muA(2);
    muA << 1.0, 0.0;
    Eigen::MatrixXd UA = Eigen::MatrixXd::Zero(2, 2);
    double DA = 1.0;
    auto skillA = std::make_shared<core::SemanticEmbedding>(muA, UA, DA, "Concept A");
    topology::Simplex s1({1});
    state.get_complex().insert(s1);
    state.get_sheaf().attach(s1, skillA);
    
    // Concept B
    Eigen::VectorXd muB(2);
    muB << -1.0, 0.0;
    Eigen::MatrixXd UB = Eigen::MatrixXd::Zero(2, 2);
    double DB = 1.0;
    auto skillB = std::make_shared<core::SemanticEmbedding>(muB, UB, DB, "Concept B");
    topology::Simplex s2({2});
    state.get_complex().insert(s2);
    state.get_sheaf().attach(s2, skillB);
    
    // The conflict score should be high (variance of 1.0 and -1.0 is ~2.0 > 0.01)
    assert(state.is_attractor_reached() == false);
    
    // The conflict score should be high (variance of 1.0 and -1.0 is ~2.0 > 0.01)
    assert(state.is_attractor_reached() == false);
    
    // 4. Initialize the OS Kernel
    core::OSKernel kernel(state);
    
    // We cannot run ResolveOperad or ExploreOperad manually via setters anymore.
    // In production, these are passed via FlatBuffers DAGs.
    
    std::cout << "test_foliation_and_kernel passed (setup only, DAG execution tested elsewhere).\n";
}

int main() {
    std::cout << "Running MOS Operad Kernel Tests...\n";
    test_foliation_and_kernel();
    std::cout << "All Operad Kernel tests passed successfully!\n";
    return 0;
}
