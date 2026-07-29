#include "mos/core/knowledge_curator.hpp"
#include <iostream>
#include <chrono>

namespace mos {
namespace core {

KnowledgeCurator::KnowledgeCurator(CognitiveState& state, std::shared_ptr<translation::KnowledgeBase> kb) 
    : state_(state), kb_(std::move(kb)) {}

KnowledgeCurator::~KnowledgeCurator() {
    stop();
}

void KnowledgeCurator::start() {
    if (running_) return;
    running_ = true;
    background_thread_ = std::thread(&KnowledgeCurator::rem_loop, this);
}

void KnowledgeCurator::stop() {
    if (!running_) return;
    running_ = false;
    cv_.notify_all();
    if (background_thread_.joinable()) {
        background_thread_.join();
    }
}

void KnowledgeCurator::trigger_rem_cycle() {
    {
        std::lock_guard<std::mutex> lock(cv_m_);
        manual_trigger_ = true;
    }
    cv_.notify_one();
}

void KnowledgeCurator::rem_loop() {
    while (running_) {
        std::unique_lock<std::mutex> lock(cv_m_);
        
        // Wait dynamically until the Orchestrator flags a stable mathematical attractor
        cv_.wait(lock, [this] {
            return !running_ || state_.check_attractor_flag() || manual_trigger_;
        });

        if (!running_) break;
        manual_trigger_ = false;

        digest_memory();
        
        // Temporarily reset attractor logic to prevent immediate re-triggering
        // until new axioms are injected.
        state_.get_section().set_obstruction(1.0); 
    }
}

void KnowledgeCurator::digest_memory() {
    // 1. Acquire read-only lock on the mathematical state
    std::shared_lock<std::shared_mutex> state_lock(state_.get_mutex());
    
    std::cout << "[KnowledgeCurator] Initiating asynchronous REM digestion phase...\n";
    
    // 2. Get the principal stress direction — the eigenvector of maximum structural variance
    Eigen::VectorXf stress = state_.get_principal_stress_internal();
    if (stress.size() == 0) {
        std::cout << "[KnowledgeCurator] No structural stress detected. Skipping digestion.\n";
        return;
    }
    
    // 3. Selectively persist only vertices with high projection onto the principal eigenvector.
    // High projection = the concept contributes significantly to the dominant structural truth.
    const auto& all_simplices = state_.get_math_complex().get_simplices();
    auto it = all_simplices.find(0);
    if (it == all_simplices.end()) return;
    
    int migrated = 0;
    for (const auto& s : it->second) {
        auto skill = state_.get_math_sheaf().get_skill(s);
        if (auto sem = std::dynamic_pointer_cast<SemanticEmbedding>(skill)) {
            // Compute the mean-centered projection of this vertex onto the stress direction
            Eigen::VectorXf mu_f = sem->get_mu().cast<float>();
            float projection = std::abs(mu_f.dot(stress));
            
            // Only persist vertices whose projection exceeds the average variance (noise floor)
            double avg_var = sem->get_D();
            if (projection > static_cast<float>(avg_var) && kb_) {
                kb_->commit_concept(sem);
                migrated++;
            }
        }
    }
    
    std::cout << "[KnowledgeCurator] Selectively migrated " << migrated << " high-projection simplices to KnowledgeBase.\n";
}

} // namespace core
} // namespace mos
