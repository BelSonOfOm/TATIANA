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
