#pragma once

#include "mos/core/cognitive_state.hpp"
#include "mos/translation/knowledge_base.hpp"
#include <memory>
#include <thread>
#include <atomic>
#include <mutex>
#include <condition_variable>

namespace mos {
namespace core {

/// @brief The Asynchronous REM Protocol for Memory Consolidation.
/// Operates off the critical path, scanning episodic/temporary states
/// to distill persistent mathematical axioms (eigenvalues) into the Scaffold.
class KnowledgeCurator {
public:
    /// @brief Construct a curator attached to a specific cognitive state and knowledge base.
    /// @param state The state to monitor and distill.
    /// @param kb The persistent storage.
    KnowledgeCurator(CognitiveState& state, std::shared_ptr<translation::KnowledgeBase> kb);

    /// @brief Destructor ensures the background thread is cleanly joined.
    ~KnowledgeCurator();

    /// @brief Start the asynchronous REM digestion cycle.
    void start();

    /// @brief Stop the REM digestion cycle safely.
    void stop();

    /// @brief Wake the curator up immediately to perform a manual REM cycle.
    void trigger_rem_cycle();

private:
    /// @brief The main loop running on the background thread.
    void rem_loop();

    /// @brief Extracts topological cycles and performs SVD/PCA to find structural truths.
    void digest_memory();

    CognitiveState& state_;
    std::shared_ptr<translation::KnowledgeBase> kb_;
    
    std::thread background_thread_;
    std::atomic<bool> running_{false};
    
    std::mutex cv_m_;
    std::condition_variable cv_;
    bool manual_trigger_{false};
};

} // namespace core
} // namespace mos
