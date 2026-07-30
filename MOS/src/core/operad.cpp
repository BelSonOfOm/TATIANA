#include "mos/core/operad.hpp"
#include "mos/core/cognitive_state.hpp"
#include "mos/core/thread_pool.hpp"
#include <queue>
#include <future>
#include <algorithm>
#include <iostream>

namespace mos {
namespace core {

void Operad::add_node(std::shared_ptr<OperadNode> node) {
    nodes_.push_back(std::move(node));
}

void Operad::add_dependency(std::shared_ptr<OperadNode> parent, std::shared_ptr<OperadNode> child) {
    parent->children.push_back(child);
    child->in_degree++;
}

std::vector<std::shared_ptr<OperadNode>> select_commuting_slice(
    const std::vector<std::shared_ptr<OperadNode>>& ready,
    std::vector<std::shared_ptr<OperadNode>>& deferred) {
    std::vector<std::shared_ptr<OperadNode>> slice;
    std::set<int> current_slice_support;
    bool slice_is_global_mutation = false;

    for (const auto& node : ready) {
        auto support = node->get_support();

        // Empty support means global. Must run isolated unless READ_ONLY.
        bool intersects = false;
        const bool is_read_only = (node->get_type() == OperatorType::READ_ONLY);
        if (support.empty()) {
            if (is_read_only) {
                intersects = slice_is_global_mutation;
            } else {
                intersects = !slice.empty(); // If slice has items, it intersects with them.
            }
        } else {
            if (slice_is_global_mutation) {
                intersects = true;
            } else {
                for (int v : support) {
                    if (current_slice_support.find(v) != current_slice_support.end()) {
                        intersects = true;
                        break;
                    }
                }
            }
        }

        if (!intersects) {
            slice.push_back(node);
            if (support.empty() && !is_read_only) {
                // FIX-11. Only a WRITING global node locks the slice. The guard
                // above already lets a READ_ONLY empty-support node (SearchOp,
                // RespondOp) join, but this line used to set the flag for ANY
                // empty-support node — so the first read-only node poisoned the
                // slice for everything evaluated after it. That made
                // co-schedulability depend on insertion order and silently threw
                // away the parallelism the read-only guard exists to permit. A
                // read-only node writes nothing, so nothing can conflict with it.
                slice_is_global_mutation = true; // Mark slice as globally locked
            } else if (!support.empty()) {
                for (int v : support) {
                    current_slice_support.insert(v);
                }
            }
        } else {
            // Defer to a future slice.
            deferred.push_back(node);
        }
    }
    return slice;
}

void Operad::run(CognitiveState& state, ThreadPool& pool) {
    // 1. Find all initial ready nodes (in_degree == 0)
    std::vector<std::shared_ptr<OperadNode>> ready_queue;
    for (auto& node : nodes_) {
        if (node->in_degree == 0) {
            ready_queue.push_back(node);
        }
    }

    // 2. Loop until the DAG is exhausted
    while (!ready_queue.empty()) {
        std::vector<std::shared_ptr<OperadNode>> next_ready_queue;
        auto slice = select_commuting_slice(ready_queue, next_ready_queue);

        // 3. Execute the slice concurrently using the persistent ThreadPool
        std::vector<std::future<void>> futures;
        for (auto& node : slice) {
            futures.push_back(pool.enqueue([&node, &state]() {
                // Lock pushing is delegated to CognitiveState modifiers.
                node->execute(state);
            }));
        }
        
        // Wait for slice to complete
        for (auto& f : futures) {
            f.wait();
        }
        
        // 4. Resolve dependencies of completed nodes
        for (auto& node : slice) {
            for (auto& child : node->children) {
                if (--child->in_degree == 0) {
                    next_ready_queue.push_back(child);
                }
            }
        }
        
        // Swap ready queues for the next foliation round
        ready_queue = std::move(next_ready_queue);
    }
}

} // namespace core
} // namespace mos
