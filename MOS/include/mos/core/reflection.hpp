#pragma once

#include "mos/core/cognitive_state.hpp"
#include "mos/translation/knowledge_base.hpp"
#include <memory>

namespace mos {
namespace core {

/// @brief The memory consolidation subsystem that distills stable topological states.
class ReflectionEngine {
public:
    /// @brief Construct the reflection engine with a target knowledge base.
    /// @param kb The persistent memory store to save crystallized concepts.
    /// @param variance_threshold The variance threshold below which a concept is considered "crystallized".
    ReflectionEngine(std::shared_ptr<translation::KnowledgeBase> kb, double variance_threshold = 0.5);

    /// @brief Distills the current cognitive state.
    /// Extracts low-variance 0-simplices into the knowledge base (anchors).
    /// Prunes high-variance 0-simplices from the complex (noise).
    /// @param state The cognitive state to distill.
    void distill(CognitiveState& state) const;

private:
    std::shared_ptr<translation::KnowledgeBase> kb_;
    double variance_threshold_;
};

} // namespace core
} // namespace mos
