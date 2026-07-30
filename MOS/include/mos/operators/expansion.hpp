#pragma once

#include "mos/core/operator.hpp"
#include "mos/topology/simplex.hpp"
#include <memory>
#include <set>

namespace mos {
namespace core {
class ProceduralSkill; // Forward declaration
}

namespace operators {

/// @brief Expands the complex by inserting a new vertex equipped with a skill.
/// Represents an EXPLORE action when the cognitive state is stable.
class ExpansionOperator : public core::CognitiveOperator {
public:
    /// @brief Construct the operator.
    /// @param new_v The ID for the new vertex.
    /// @param skill The skill (e.g., SemanticEmbedding) to attach.
    ExpansionOperator(topology::VertexID new_v, std::shared_ptr<core::ProceduralSkill> skill);

    /// @brief Mutates the complex by adding the new vertex.
    bool apply(core::CognitiveState& state) override;

    [[nodiscard]] core::OperatorType get_type() const noexcept override {
        return core::OperatorType::MUTATION;
    }

    [[nodiscard]] std::set<int> get_support() const override {
        return {static_cast<int>(new_v_)};
    }

    /// E7: stable operator identity for the assembly record.
    [[nodiscard]] const char *name() const noexcept override { return "ExpansionOperator"; }

private:
    topology::VertexID new_v_;
    std::shared_ptr<core::ProceduralSkill> skill_;
};

} // namespace operators
} // namespace mos
