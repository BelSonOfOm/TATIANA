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
        
        Eigen::VectorXd query_mu(4);
        query_mu << 0.11, 0.21, 0.31, 0.41;

        auto nearest = kb.get_top_k_concepts(query_mu, 5);
        assert(nearest.size() == 1);  // min(k, |store|), not k
        assert(nearest[0]->get_mu()[1] == 0.2);

        assert(kb.get_top_k_concepts(query_mu, 0).empty());
    }

    std::remove(db_path.c_str());
    std::cout << "test_knowledge_base passed (SQLite persistence and rank retrieval verified).\n";
}

/// @brief P0 REGRESSION. Pins the defect measured in the Tier-0 chapter: an
/// absolute Wasserstein cutoff of 0.1 returns NOTHING for a genuinely related
/// query, because the embedding pedestal puts even unrelated pairs at
/// cos ~ 0.669, i.e. semantic ~ 0.66 -- six times above the cutoff.
///
/// The store below is built so the old policy provably returns zero: every
/// stored concept sits further than 0.1 (squared) from the query, while still
/// being ordered by genuine similarity. A rank query MUST return them, nearest
/// first. If this test ever passes with an empty result, the epsilon-ball has
/// come back.
void test_p0_rank_beats_threshold() {
    const std::string db_path = "test_mos_p0.db";
    std::remove(db_path.c_str());

    const int d = 8;
    Eigen::VectorXd query = Eigen::VectorXd::Zero(d);
    query(0) = 1.0;

    // Offsets chosen so ||query - mu||^2 = offset^2 * (d-1) > 0.1 for all three,
    // and strictly increasing, so the correct order is unambiguous.
    const std::vector<double> offsets = {0.20, 0.35, 0.50};
    {
        translation::KnowledgeBase kb(db_path);
        for (std::size_t i = 0; i < offsets.size(); ++i) {
            Eigen::VectorXd mu = query;
            for (int j = 1; j < d; ++j) mu(j) += offsets[i];
            kb.commit_concept(std::make_shared<core::SemanticEmbedding>(
                mu, Eigen::MatrixXd::Zero(d, 0), 0.01,
                "concept_" + std::to_string(i)));
        }
    }

    {
        translation::KnowledgeBase kb(db_path);

        // Every stored concept is beyond the old 0.1 cutoff...
        for (double off : offsets) {
            assert(off * off * (d - 1) > 0.1);
        }

        // ...yet rank retrieval returns them, nearest first.
        auto top = kb.get_top_k_concepts(query, 3);
        assert(top.size() == 3);
        assert(top[0]->get_name() == "concept_0");
        assert(top[1]->get_name() == "concept_1");
        assert(top[2]->get_name() == "concept_2");

        // Width is respected, and truncation keeps the NEAREST, not the first
        // rows the scan happened to touch.
        auto top1 = kb.get_top_k_concepts(query, 1);
        assert(top1.size() == 1);
        assert(top1[0]->get_name() == "concept_0");

        // Descending COSINE is the contract, not an accident of insertion.
        double prev = 2.0;
        for (const auto& c : top) {
            const Eigen::VectorXd& m = c->get_mu();
            double cos = query.dot(m) / (query.norm() * m.norm());
            assert(cos <= prev);
            prev = cos;
        }
    }

    // THE LENGTH-BIAS REGRESSION. Ranking on ||mu_q - mu_i||^2 instead of cosine
    // is correct only if stored means are unit-norm, and pi_v's centroids are
    // not. This store contains a concept pointing EXACTLY at the query but with
    // a large norm, and one pointing further off-axis with a small norm. Cosine
    // must prefer the aligned one; squared distance would prefer the short one
    // purely because it is short.
    {
        translation::KnowledgeBase kb(db_path);
        Eigen::VectorXd aligned_long = query * 3.0;        // cos = 1, far in L2
        Eigen::VectorXd skew_short = Eigen::VectorXd::Zero(d);
        skew_short(0) = 0.30;
        skew_short(1) = 0.30;                              // cos ~ 0.707, near in L2
        kb.commit_concept(std::make_shared<core::SemanticEmbedding>(
            aligned_long, Eigen::MatrixXd::Zero(d, 0), 0.01, "aligned_long"));
        kb.commit_concept(std::make_shared<core::SemanticEmbedding>(
            skew_short, Eigen::MatrixXd::Zero(d, 0), 0.01, "skew_short"));

        // The trap this pins: L2 says skew_short wins, cosine says aligned_long.
        assert((query - skew_short).squaredNorm() < (query - aligned_long).squaredNorm());

        auto top = kb.get_top_k_concepts(query, 1);
        assert(top.size() == 1);
        assert(top[0]->get_name() == "aligned_long");
    }

    std::remove(db_path.c_str());
    std::cout << "test_p0_rank_beats_threshold passed (0.31% epsilon-ball defect pinned).\n";
}

int main() {
    test_knowledge_base_persistence();
    test_p0_rank_beats_threshold();
    return 0;
}
