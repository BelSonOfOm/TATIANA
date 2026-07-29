#include "mos/core/reflection.hpp"
#include <vector>
#include <algorithm>

namespace mos {
namespace core {

ReflectionEngine::ReflectionEngine(std::shared_ptr<translation::KnowledgeBase> kb, double variance_threshold)
    : kb_(std::move(kb)), variance_threshold_(variance_threshold) {}

void ReflectionEngine::distill(CognitiveState& state) const {
    auto& complex = state.get_complex();
    auto& sheaf = state.get_sheaf();
    
    const auto& all_simplices = complex.get_simplices();
    auto it = all_simplices.find(0);
    if (it == all_simplices.end()) {
        return; // No vertices to distill
    }
    
    // Copy the set of vertices because we might modify the complex while iterating
    std::vector<topology::Simplex> vertices(it->second.begin(), it->second.end());
    
    for (const auto& v : vertices) {
        auto skill = sheaf.get_skill(v);
        if (auto semantic = std::dynamic_pointer_cast<SemanticEmbedding>(skill)) {
            const auto& U = semantic->get_U();
            double D = semantic->get_D();
            double N = static_cast<double>(semantic->get_mu().size());
            
            double trace = N * D;
            if (U.cols() > 0) {
                trace += (U.transpose() * U).trace();
            }
            
            // Check if crystallized (average variance below threshold)
            bool is_crystallized = true;
            if (N > 0 && (trace / N) >= variance_threshold_) {
                is_crystallized = false;
            }
            
            if (is_crystallized) {
                // Anchor: Commit to Knowledge Base, leave in complex
                if (kb_) {
                    kb_->commit_concept(semantic);
                }
            } else {
                // Prune from rigorous logic but PRESERVE in the ghost section
                std::vector<float> residual_geometry(semantic->get_mu().size());
                for(size_t i=0; i < residual_geometry.size(); ++i) {
                    residual_geometry[i] = static_cast<float>(semantic->get_mu()(i));
                }
                
                // Inject into the fluid chat geometry
                state.inject_chat_memory("RESIDUAL: " + semantic->get_name(), residual_geometry);
                
                // Safely remove from the strict mathematical complex
                complex.remove(v);
            }
        }
    }
}

} // namespace core
} // namespace mos
