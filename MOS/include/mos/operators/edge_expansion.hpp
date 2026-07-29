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

/// @brief Expands the complex by inserting a 1-simplex (Edge) equipped with a skill.
/// Represents a Transitive Verb binding two Nouns in the DisCoCat formalism.
class EdgeExpansionOperator : public core::CognitiveOperator {
public:
    EdgeExpansionOperator(topology::VertexID v1, topology::VertexID v2, std::shared_ptr<core::ProceduralSkill> skill);

    bool apply(core::CognitiveState& state) override;

    [[nodiscard]] core::OperatorType get_type() const noexcept override {
        return core::OperatorType::MUTATION;
    }

    [[nodiscard]] std::set<int> get_support() const override {
        return {static_cast<int>(v1_), static_cast<int>(v2_)};
    }

private:
    topology::VertexID v1_;
    topology::VertexID v2_;
    std::shared_ptr<core::ProceduralSkill> skill_;
};

} // namespace operators
} // namespace mos
