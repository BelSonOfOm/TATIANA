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
        std::vector<std::shared_ptr<OperadNode>> slice;
        std::vector<std::shared_ptr<OperadNode>> next_ready_queue;
        std::set<int> current_slice_support;
        bool slice_is_global_mutation = false;
        
        for (auto& node : ready_queue) {
            auto support = node->get_support();
            
            // Empty support means global mutation. Must run isolated unless READ_ONLY.
            bool intersects = false;
            bool is_read_only = (node->get_type() == OperatorType::READ_ONLY);
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
                // Add to current slice
                slice.push_back(node);
                if (support.empty()) {
                    slice_is_global_mutation = true; // Mark slice as globally locked
                } else {
                    for (int v : support) {
                        current_slice_support.insert(v);
                    }
                }
            } else {
                // Push back to next ready queue to be evaluated in a future slice
                next_ready_queue.push_back(node);
            }
        }
        
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
