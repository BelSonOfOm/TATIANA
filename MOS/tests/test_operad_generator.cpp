#include "mos/core/operad_generator.hpp"
#include "mos/translation/knowledge_base.hpp"
#include "mos/translation/colibri_kernel.hpp"
#include "mos/core/cognitive_state.hpp"
#include <iostream>
#include <cassert>

using namespace mos;

int main() {
    std::cout << "Testing OperadGenerator...\n";

    // Initialize mock dependencies
    auto kb = std::make_shared<translation::KnowledgeBase>("mos_brain_test_operad.db");
    auto llm = std::make_shared<translation::ColibriKernel>("127.0.0.1", 11434, "colibri");

    core::OperadGenerator generator(kb, llm);
    core::CognitiveState state;

    // Test 1: Resolve Mode (High Conflict)
    std::cout << "--- Test 1: RESOLVE Mode ---\n";
    auto resolve_operad = generator.generate_dag("What is an Operad?", 0.5, 0.1);
    assert(resolve_operad != nullptr);
    
    // Test 2: Explore Mode (Low Conflict)
    std::cout << "--- Test 2: EXPLORE Mode ---\n";
    auto explore_operad = generator.generate_dag("What is an Operad?", 0.05, 0.1);
    assert(explore_operad != nullptr);
    
    std::cout << "OperadGenerator passed!\n";
    return 0;
}
