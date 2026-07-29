#include <iostream>
#include <cassert>
#include <vector>
#include <memory>
#include <cstdio>
#include "mos/translation/knowledge_base.hpp"
#include "mos/core/semantic_skill.hpp"

using namespace mos;

void test_knowledge_base_persistence() {
    const std::string db_path = "test_mos_brain.db";
    std::remove(db_path.c_str()); // Ensure clean slate

    // Step 1: Initialize DB and write a crystallized theorem
    {
        translation::KnowledgeBase kb(db_path);
        Eigen::VectorXd mu(4);
        mu << 0.1, 0.2, 0.3, 0.4;
        Eigen::MatrixXd U = Eigen::MatrixXd::Zero(4, 4);
        double D = 0.01;
        std::string theorem = "The metric tensor determines the shortest path on the manifold.";
        
        auto concept = std::make_shared<core::SemanticEmbedding>(mu, U, D, theorem);
        kb.commit_concept(concept);
    }
    // kb goes out of scope, DB closes.

    // Step 2: Re-open DB and retrieve
    {
        translation::KnowledgeBase kb(db_path);
        auto concepts = kb.get_all_concepts();
        
        assert(concepts.size() == 1);
        assert(concepts[0]->get_name() == "The metric tensor determines the shortest path on the manifold.");
        assert(concepts[0]->get_mu().size() == 4);
        assert(concepts[0]->get_mu()[1] == 0.2);
        
        // Test Topological Filtration (Wasserstein)
        Eigen::VectorXd query_mu(4);
        query_mu << 0.11, 0.21, 0.31, 0.41;
        double query_D = 0.01;
        
        // Should find it with epsilon 0.1
        auto relevant = kb.get_relevant_concepts(query_mu, query_D, 0.1);
        assert(relevant.size() == 1);
        
        // Should NOT find it with very strict epsilon
        auto non_relevant = kb.get_relevant_concepts(query_mu, query_D, 0.0001);
        assert(non_relevant.empty());
    }

    std::remove(db_path.c_str());
    std::cout << "test_knowledge_base passed (SQLite persistence and Wasserstein filtration verified).\n";
}

int main() {
    test_knowledge_base_persistence();
    return 0;
}
