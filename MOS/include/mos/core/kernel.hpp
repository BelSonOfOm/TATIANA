#pragma once

#include "mos/core/coarse_complex.hpp"
#include "mos/core/cognitive_state.hpp"
#include "mos/core/operad.hpp"
#include "mos/core/reflection.hpp"
#include "mos/core/thread_pool.hpp"
#include "mos/translation/knowledge_base.hpp"
#include "mos/translation/llm_interface.hpp"
#include <memory>
#include <functional>
#include <cstdint>

namespace mos {
namespace core {

/// @brief Configuration for the OS Kernel.
struct KernelConfig {
    unsigned int num_threads = 0; // 0 triggers auto-detect
    unsigned int fallback_threads = 4;
    float compute_dt = 0.05f;
    float compute_lambda = 2.0f;
    double conflict_threshold = 100.0;

    /// @brief eps_rho: the discord threshold for the RESOLVE/EXPLORE gate.
    /// (Named per C6-2; see plasticity.hpp THE THREE EPSILONS. This is the
    /// STATIC default -- CriticalityMonitor::epsilon_rho() supersedes it once
    /// enough rho history exists.)
    /// Because rho is dimensionless and bounded in [0,1], this is a portable
    /// number rather than one that drifts with embedding scale or graph size.
    /// Calibrated empirically on real 384-d embeddings: agreement ~0.00,
    /// related-but-distinct ~0.06, off-topic ~0.14. Hence 0.10 sits between
    /// "different facets of the same problem" and "genuinely incoherent".
    double rho_threshold = 0.10;
};

/// @brief The two-mode controller driven by discord over K.
enum class CognitiveMode {
    EXPLORE, ///< internally coherent: free to build, abstract, search outward
    RESOLVE, ///< discord above threshold: only reconcile, do not expand
    UNKNOWN  ///< discord undefined (no bound organs, or no geometry) - do NOT
             ///< guess a mode from a measurement that does not exist
};

[[nodiscard]] const char* to_string(CognitiveMode m) noexcept;

/// @brief The Orchestration Layer of the Mathematical Operating System.
/// Routes the cognitive state through Operadic DAGs based on its conflict score.
class OSKernel {
public:
    /// @brief Initialize the Operating System Kernel.
    /// @param initial_state The starting Cognitive State.
    /// @param config Configuration for the kernel.
    explicit OSKernel(CognitiveState& initial_state, const KernelConfig& config = KernelConfig());

    /// @brief Set the Reflection Engine for state distillation.
    void set_reflection_engine(std::shared_ptr<ReflectionEngine> reflection_engine);

    /// @brief Set the Knowledge Base for primitives to use.
    void set_knowledge_base(std::shared_ptr<translation::KnowledgeBase> kb);

    /// @brief Set the Language Kernel for primitives to use.
    void set_llm(std::shared_ptr<translation::LanguageKernel> llm);

    /// @brief Execute a serialized Operad DAG (FlatBuffers binary).
    /// @param buffer Pointer to the binary FlatBuffers payload.
    /// @param size Size of the payload.
    /// @return True if successful and valid, false if malformed or empty.
    bool execute_dag(const uint8_t* buffer, size_t size);

    /// @brief Runs a single tick (loop) of the OS Kernel (Legacy or periodic maintenance).
    bool tick();

    /// @brief Get the current cognitive state.
    [[nodiscard]] CognitiveState& get_state() noexcept;

    /// @brief The coarse complex K of operator-organs.
    /// Each OpType present in a DAG is an organ; its stalk is that operator's
    /// payload geometry (embedded locally in Python). Operators adjacent in the
    /// DAG co-activate, so cooperating organs bind. rho over K therefore measures
    /// whether the parts of a single reasoning act are semantically coherent.
    [[nodiscard]] CoarseComplex& get_coarse_complex() noexcept { return coarse_; }
    [[nodiscard]] const CoarseComplex& get_coarse_complex() const noexcept {
        return coarse_;
    }

    /// @brief Discord measured over K after the most recent execute_dag().
    [[nodiscard]] const CoherenceReport& last_coherence() const noexcept {
        return last_coherence_;
    }

    /// @brief The mode selected by the most recent coherence measurement.
    /// UNKNOWN when rho is undefined — the controller refuses to invent a mode
    /// from a measurement that does not exist.
    [[nodiscard]] CognitiveMode current_mode() const noexcept { return mode_; }

    /// @brief Set a halt condition for the kernel.
    void set_halt_condition(std::function<bool(const CognitiveState&)> condition);

private:
    CognitiveState& state_;
    std::shared_ptr<ReflectionEngine> reflection_engine_;
    std::shared_ptr<translation::KnowledgeBase> kb_;
    std::shared_ptr<translation::LanguageKernel> llm_;
    std::function<bool(const CognitiveState&)> halt_condition_;
    std::shared_ptr<ThreadPool> thread_pool_;
    KernelConfig config_;
    CoarseComplex coarse_;
    CoherenceReport last_coherence_;
    CognitiveMode mode_{CognitiveMode::UNKNOWN};
};

} // namespace core
} // namespace mos
