#pragma once

#include "mos/core/operator.hpp"
#include <memory>
#include <vector>
#include <atomic>
#include <set>
#include <stdexcept>

namespace mos {
namespace core {

class CognitiveState;
class ThreadPool;

/// @brief A node in the Operad Directed Acyclic Graph (DAG).
class OperadNode {
public:
    OperadNode(std::shared_ptr<CognitiveOperator> op) : op_(std::move(op)), in_degree(0) {}

    [[nodiscard]] OperatorType get_type() const noexcept {
        return op_->get_type();
    }

    [[nodiscard]] std::set<int> get_support() const {
        return op_->get_support();
    }

    bool execute(CognitiveState& state) {
        if (!op_) return false;
        try {
            return op_->apply(state);
        } catch (const std::exception& e) {
            // Topological collapse or other operator failure — signal to the DAG
            return false;
        }
    }

    std::shared_ptr<CognitiveOperator> op_;
    std::vector<std::shared_ptr<OperadNode>> children;
    std::atomic<int> in_degree;
};

/// @brief Selects the maximal commuting slice from a ready queue (the "foliation"
/// step), returning the co-schedulable nodes and moving the rest into `deferred`.
///
/// Extracted from Operad::run so the co-schedulability RULE can be tested without
/// standing up a ThreadPool and a live CognitiveState. FIX-11 was an
/// order-dependence bug in exactly this rule, and it was invisible for as long as
/// the rule had no seam to test it at.
///
/// The rule, in full:
///   * disjoint non-empty supports co-schedule;
///   * an empty support means GLOBAL. A global MUTATION must run isolated, and it
///     locks the slice against everything evaluated after it;
///   * a global READ_ONLY node writes nothing, so it joins any slice that is not
///     already locked by a global mutation, and it does NOT lock the slice itself.
///
/// @param ready    Nodes whose dependencies are satisfied, in evaluation order.
/// @param deferred Appended to with the nodes that did not fit this slice.
[[nodiscard]] std::vector<std::shared_ptr<OperadNode>> select_commuting_slice(
    const std::vector<std::shared_ptr<OperadNode>> &ready,
    std::vector<std::shared_ptr<OperadNode>> &deferred);

/// @brief The Orchestration DAG that routes operators to the CognitiveState.
class Operad {
public:
    /// @brief Adds a node to the operad.
    void add_node(std::shared_ptr<OperadNode> node);

    /// @brief Adds a directed dependency: parent must complete before child starts.
    void add_dependency(std::shared_ptr<OperadNode> parent, std::shared_ptr<OperadNode> child);

    /// @brief Executes the Operad, foliating the DAG into maximal commuting slices.
    void run(CognitiveState& state, ThreadPool& pool);

private:
    std::vector<std::shared_ptr<OperadNode>> nodes_;
};

} // namespace core
} // namespace mos
