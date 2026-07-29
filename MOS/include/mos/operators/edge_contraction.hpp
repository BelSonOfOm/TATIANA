#pragma once

#include "mos/core/operator.hpp"
#include "mos/topology/simplex.hpp"

namespace mos {
namespace operators {

/// @brief Topological Surgery: Edge Contraction.
/// Merges two vertices in the complex, collapsing the edge between them.
class EdgeContractionOperator : public core::CognitiveOperator {
public:
    /// @brief Construct the operator to merge v2 into v1.
    /// @param keep_vertex The vertex to keep.
    /// @param remove_vertex The vertex to remove and merge into keep_vertex.
    EdgeContractionOperator(topology::VertexID keep_vertex, topology::VertexID remove_vertex);

    /// @brief Apply the edge contraction to the cognitive state's topology.
    /// @param state The cognitive state.
    /// @return True if the operation mutated the complex.
    bool apply(core::CognitiveState& state) override;

    [[nodiscard]] core::OperatorType get_type() const noexcept override {
        return core::OperatorType::MUTATION;
    }

    [[nodiscard]] std::set<int> get_support() const override {
        return {static_cast<int>(v_keep_), static_cast<int>(v_remove_)};
    }

private:
    topology::VertexID v_keep_;
    topology::VertexID v_remove_;
};

} // namespace operators
} // namespace mos
