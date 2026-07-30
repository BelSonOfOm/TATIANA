#include "mos/translation/curator.hpp"
#include "mos/core/semantic_skill.hpp"
#include "mos/operators/expansion.hpp"
#include "mos/operators/edge_expansion.hpp"
#include <cmath>
#include <iostream>
#include <optional>

namespace mos {
namespace translation {

AgentCurator::AgentCurator(math::FourierMapper mapper)
    : fourier_mapper_(std::move(mapper)) {}

/// FIX-13. This function used to return -ln(c) as an isotropic variance, and
/// UNCALIBRATED_VARIANCE_PRIOR = 1.0 when no confidence was available. Both are
/// now gone, for one reason: **an isotropic variance in d dimensions is the wrong
/// destination for a scalar confidence.**
///
/// The arithmetic (also documented at semantic_skill.hpp's WassersteinTerms): the
/// Bures term between two isotropic covariances is d*(sqrt(D1)-sqrt(D2))^2, which
/// grows with d, while the semantic term ||mu1-mu2||^2 <= 4 regardless of d. At
/// d = 384, D = 1.0 against a confident c = 0.95 gave epistemic ~= 230 vs
/// semantic <= 4 — a 57:1 ratio in favour of a self-reported LLM confidence the
/// architecture elsewhere explicitly declines to trust. The old 1e-9 confidence
/// clamp made this worse: it admits -ln(c) = 20.7, i.e. an epistemic term of
/// ~15.8, still four times the whole semantic budget.
///
/// Per Q9 (MOS_FINALIZATION.md) the correct home for a reported confidence is the
/// EDGE PRECISION pi_e in L = delta^T Pi delta, where it is dimensionally
/// harmless and actually load-bearing. This function's job is only to supply the
/// shared O(1/d) noise floor, and it no longer pretends a confidence is a
/// geometry.
///
/// **The routing now EXISTS (5ah).** `curate` sends the confidence to
/// `nu` on the SemanticEmbedding via `core::vertex_precision`, and the edge
/// skill's precision is `core::edge_precision(nu_new, nu_existing)` -- the
/// cell-weight tower. `confidence` stays in this signature because the caller
/// still needs it for that, not because this function uses it.
///
/// @param d The embedding dimension. Passed explicitly rather than inferred:
///          the floor is a function of d, and silently assuming a dimension is
///          precisely the class of bug FIX-1 was opened for.
double AgentCurator::compute_variance(std::optional<double> confidence, int d) const {
    (void)confidence;  // deliberately unused; see the note above and Q9.
    if (!confidence.has_value()) {
        static bool warned = false;
        if (!warned) {
            std::cerr << "[Curator] NOTE: thought confidence is UNAVAILABLE "
                         "(provider returned no logprobs). This no longer affects "
                         "the noise floor D, which is now the shared O(1/d) "
                         "shrinkage floor for every stalk (FIX-13). Confidence, "
                         "when present, is routed to nu_v and thence to pi_e "
                         "(5ah); with none available this concept stays "
                         "UNCALIBRATED at nu = 1.\n";
            warned = true;
        }
    }
    return core::stalk_floor(d, /*n_eff=*/1.0);
}

double AgentCurator::calculate_wasserstein_2_sq(const Eigen::VectorXd& mu1, double D1,
                                                const Eigen::VectorXd& mu2, const Eigen::MatrixXd& U2, double D2) const {
    // E4: delegates to core::wasserstein_2_terms (single source of truth). This
    // function previously duplicated knowledge_base.cpp's copy of the formula
    // verbatim; two independent copies of a load-bearing metric is how they
    // silently drift apart.
    return core::wasserstein_2_terms(mu1, D1, mu2, U2, D2).total();
}

std::shared_ptr<core::Operad> AgentCurator::curate(const AgentThought& new_thought, const core::CognitiveState& state, size_t new_vertex_id, double epsilon_w2, core::ThreadPool* pool) {
    auto operad = std::make_shared<core::Operad>();
    
    // 1. Process the new AgentThought (Agent -> 0-simplex)
    std::vector<double> mu_vec = fourier_mapper_.project(new_thought.latent);
    Eigen::VectorXd thought_mu = Eigen::Map<Eigen::VectorXd>(mu_vec.data(), mu_vec.size());
    double thought_D = compute_variance(new_thought.confidence,
                                        static_cast<int>(thought_mu.size()));
    Eigen::MatrixXd thought_U(thought_mu.size(), 0);

    // 5ah: confidence -> nu_v. This is the ONLY measured input to the whole
    // cell-weight tower (nu -> pi_e -> tau_f); with it absent every weight is 1,
    // tau_f == 1, and F_MOS silently collapses to the unit-weight Forman
    // formula. An absent confidence is UNCALIBRATED (nu = 1), never invented.
    const double thought_nu =
        new_thought.confidence.has_value()
            ? core::vertex_precision(*new_thought.confidence)
            : 1.0;

    auto thought_skill = std::make_shared<core::SemanticEmbedding>(
        thought_mu, thought_U, thought_D, new_thought.reasoning_chain, thought_nu);
    
    auto thought_op = std::make_shared<operators::ExpansionOperator>(new_vertex_id, thought_skill);
    auto thought_node = std::make_shared<core::OperadNode>(thought_op);
    operad->add_node(thought_node);
    
    // 2. Form the Vietoris-Rips Complex by measuring Wasserstein distance against existing thoughts
    const auto& complex = state.get_complex();
    const auto& sheaf = state.get_sheaf();
    
    const auto& simplices = complex.get_simplices();
    auto v_it = simplices.find(0);
    
    if (v_it != simplices.end()) {
        std::mutex operad_mutex; // Protect operad edge addition during parallel loop
        
        std::vector<std::future<void>> futures;
        
        for (const auto& existing_v : v_it->second) {
            auto task = [&, existing_v]() {
                auto skill = sheaf.get_skill(existing_v);
                if (auto existing_semantic = std::dynamic_pointer_cast<core::SemanticEmbedding>(skill)) {
                    
                    double w2_sq = calculate_wasserstein_2_sq(thought_mu, thought_D,
                                                              existing_semantic->get_mu(), existing_semantic->get_U(), existing_semantic->get_D());
                    
                    if (w2_sq <= epsilon_w2) {
                        // They mathematically intersect! Draw a 1-simplex between them.
                        int existing_id = existing_v.get_vertices()[0];
                        
                        // Midpoint geometry for the edge
                        Eigen::VectorXd edge_mu = 0.5 * (thought_mu + existing_semantic->get_mu());
                        // Blended variance
                        double edge_D = 0.5 * (thought_D + existing_semantic->get_D());
                        Eigen::MatrixXd edge_U(edge_mu.size(), 0);
                        
                        // 5ah, the edge level of the cell-weight tower: pi_e is
                        // the harmonic mean of its two vertex-faces, which is
                        // the error-propagation precision of a difference of
                        // two independent estimates. NOT the midpoint average
                        // used for the geometry above -- averaging precisions
                        // would let one confident endpoint mask an unreliable
                        // one, and the whole point of the harmonic mean is that
                        // the WORST face dominates.
                        const double edge_nu = core::edge_precision(
                            thought_nu, existing_semantic->get_nu());

                        auto edge_skill = std::make_shared<core::SemanticEmbedding>(
                            edge_mu, edge_U, edge_D, "Vietoris-Rips Intersection", edge_nu);
                        auto edge_op = std::make_shared<operators::EdgeExpansionOperator>(new_vertex_id, existing_id, edge_skill);
                        auto edge_node = std::make_shared<core::OperadNode>(edge_op);
                        
                        std::lock_guard<std::mutex> lock(operad_mutex);
                        operad->add_node(edge_node);
                        operad->add_dependency(thought_node, edge_node);
                    }
                }
            };
            
            if (pool) {
                futures.push_back(pool->enqueue(task));
            } else {
                task();
            }
        }
        
        // Wait for parallel solvers to complete
        for (auto& f : futures) {
            f.wait();
        }
    }
    
    return operad;
}

} // namespace translation
} // namespace mos
