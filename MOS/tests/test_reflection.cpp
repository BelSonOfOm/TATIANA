#include <iostream>
#include <cassert>
#include <memory>
#include "mos/core/cognitive_state.hpp"
#include "mos/core/reflection.hpp"
#include "mos/translation/knowledge_base.hpp"
#include "mos/core/semantic_skill.hpp"
#include "mos/topology/simplex.hpp"

using namespace mos;

void test_reflection_engine() {
    core::CognitiveState state;
    
    // Create a KnowledgeBase and ReflectionEngine
    auto kb = std::make_shared<translation::KnowledgeBase>();
    core::ReflectionEngine reflection(kb, 0.5); // Threshold = 0.5
    
    // Concept 1: Crystallized (Variance = 0.1)
    Eigen::VectorXd mu1(2);
    mu1 << 1.0, 1.0;
    Eigen::MatrixXd U1 = Eigen::MatrixXd::Zero(2, 2);
    double D1 = 0.1;
    auto skill1 = std::make_shared<core::SemanticEmbedding>(mu1, U1, D1, "Crystallized Concept");
    
    topology::Simplex v1({10});
    state.get_complex().insert(v1);
    state.get_sheaf().attach(v1, skill1);
    
    // Concept 2: High Variance Noise (Variance = 2.0)
    Eigen::VectorXd mu2(2);
    mu2 << -1.0, -1.0;
    Eigen::MatrixXd U2 = Eigen::MatrixXd::Zero(2, 2);
    double D2 = 2.0;
    auto skill2 = std::make_shared<core::SemanticEmbedding>(mu2, U2, D2, "Noisy Concept");
    
    topology::Simplex v2({20});
    state.get_complex().insert(v2);
    state.get_sheaf().attach(v2, skill2);
    
    // Concept 3: Edge linking them
    topology::Simplex edge({10, 20});
    state.get_complex().insert(edge);
    
    // Ensure topology has 2 vertices and 1 edge initially
    assert(state.get_complex().get_simplices().at(0).size() == 2);
    assert(state.get_complex().get_simplices().at(1).size() == 1);
    
    // Distill the state
    reflection.distill(state);
    
    // Verify Knowledge Base extracted only Concept 1
    auto concepts = kb->get_all_concepts();
    assert(concepts.size() == 1);
    assert(concepts[0]->get_name() == "Crystallized Concept");
    
    // Verify Topology Pruning:
    // v2 (Noise) should be deleted
    // v1 (Anchor) should remain
    // edge should be deleted (because it contains v2)
    const auto& all_simplices = state.get_complex().get_simplices();
    auto v_it = all_simplices.find(0);
    assert(v_it != all_simplices.end());
    assert(v_it->second.size() == 1);
    assert(*v_it->second.begin() == v1);
    
    auto e_it = all_simplices.find(1);
    assert(e_it == all_simplices.end() || e_it->second.empty()); // Edge was deleted
    
    std::cout << "test_reflection_engine passed.\n";
}

int main() {
    test_reflection_engine();
    return 0;
}
