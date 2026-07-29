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

/// Transitional prior used ONLY when confidence is unknown. Deliberately more
/// humble than the old hidden 0.5 (this corresponds to c = e^-1 ~ 0.368), and
/// deliberately NAMED so it is visible in the code rather than buried as a magic
/// literal. This goes away once coherence-based confidence (rho, Construction 2b)
/// is wired in: rho is measured from actual module agreement, not self-reported.
static constexpr double UNCALIBRATED_VARIANCE_PRIOR = 1.0;

double AgentCurator::compute_variance(std::optional<double> confidence) const {
    // True epistemic variance based on information theory: \sigma^2 = -\ln(c)
    if (!confidence.has_value()) {
        // HONESTY: we do not manufacture a measurement. Warn once, loudly.
        static bool warned = false;
        if (!warned) {
            std::cerr << "[Curator] WARNING: thought confidence is UNAVAILABLE "
                         "(provider returned no logprobs). Using the explicit "
                         "UNCALIBRATED_VARIANCE_PRIOR for the noise floor D. Concept "
                         "variances are NOT measured until coherence-based (rho) "
                         "confidence is wired in.\n";
            warned = true;
        }
        return UNCALIBRATED_VARIANCE_PRIOR;
    }
    // Confidence is [0, 1]. Clamp strictly to avoid log(0).
    double clamped_conf = std::max(1e-9, std::min(0.999999, *confidence));
    return -std::log(clamped_conf);
}

double AgentCurator::calculate_wasserstein_2_sq(const Eigen::VectorXd& mu1, double D1,
                                                const Eigen::VectorXd& mu2, const Eigen::MatrixXd& U2, double D2) const {
    // E4: delegates to core::wasserstein_2_terms (single source of truth). This
    // function previously duplicated knowledge_base.cpp's copy of the formula
    // verbatim; two independent copies of a load-bearing metric is how they
    // silently drift apart.
    return core::wasserstein_2_terms(mu1, D1, mu2, U2, D2).total();
}

std::shared_ptr<core::Operad> AgentCurator::curate(const AgentThought& new_thought, const core::CognitiveState& state, size_t new_vertex_id, double epsilon, core::ThreadPool* pool) {
    auto operad = std::make_shared<core::Operad>();
    
    // 1. Process the new AgentThought (Agent -> 0-simplex)
    std::vector<double> mu_vec = fourier_mapper_.project(new_thought.latent);
    Eigen::VectorXd thought_mu = Eigen::Map<Eigen::VectorXd>(mu_vec.data(), mu_vec.size());
    double thought_D = compute_variance(new_thought.confidence);
    Eigen::MatrixXd thought_U(thought_mu.size(), 0);
    
    auto thought_skill = std::make_shared<core::SemanticEmbedding>(thought_mu, thought_U, thought_D, new_thought.reasoning_chain);
    
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
                    
                    if (w2_sq <= epsilon) {
                        // They mathematically intersect! Draw a 1-simplex between them.
                        int existing_id = existing_v.get_vertices()[0];
                        
                        // Midpoint geometry for the edge
                        Eigen::VectorXd edge_mu = 0.5 * (thought_mu + existing_semantic->get_mu());
                        // Blended variance
                        double edge_D = 0.5 * (thought_D + existing_semantic->get_D());
                        Eigen::MatrixXd edge_U(edge_mu.size(), 0);
                        
                        auto edge_skill = std::make_shared<core::SemanticEmbedding>(edge_mu, edge_U, edge_D, "Vietoris-Rips Intersection");
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
