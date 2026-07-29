#include <iostream>
#include <cassert>
#include "mos/translation/curator.hpp"
#include "mos/math/fourier.hpp"
#include "mos/core/cognitive_state.hpp"
#include "mos/core/thread_pool.hpp"

using namespace mos;

void test_agent_curator() {
    math::FourierMapper mapper(512, 16);
    translation::AgentCurator curator(mapper);
    core::CognitiveState state;

    // Agent 1: The Solver
    translation::AgentThought solver_thought;
    solver_thought.reasoning_chain = "Let M be a Riemannian manifold with metric g...";
    solver_thought.latent = std::vector<double>(512, 0.5);
    solver_thought.confidence = 0.9;

    // Agent 2: The Critic (very similar thought, but lower confidence)
    translation::AgentThought critic_thought;
    critic_thought.reasoning_chain = "The metric g must be positive-definite, but I am unsure if it is here...";
    critic_thought.latent = std::vector<double>(512, 0.51); // Slight distance in latent space
    critic_thought.confidence = 0.4;

    // 1. Curate Solver (No edges will form because state is empty)
    auto operad1 = curator.curate(solver_thought, state, 100, 10.0);
    core::ThreadPool pool(2);
    operad1->run(state, pool);

    // Verify Solver is in the state
    assert(state.get_complex().get_simplices().at(0).size() == 1);

    // 2. Curate Critic
    // Epsilon = 100.0 is large enough to form the Vietoris-Rips edge
    auto operad2 = curator.curate(critic_thought, state, 101, 100.0);
    operad2->run(state, pool);

    // Verify Critic is in the state, AND an edge was formed between them!
    const auto& simplices = state.get_complex().get_simplices();
    assert(simplices.at(0).size() == 2); // 2 vertices
    assert(simplices.at(1).size() == 1); // 1 edge

    std::cout << "test_agent_curator passed (Vietoris-Rips formed successfully via Wasserstein distance).\n";
}

int main() {
    test_agent_curator();
    return 0;
}
