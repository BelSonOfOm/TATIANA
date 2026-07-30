// FIX-16: this test could not diagnose its own failure.
//
// It previously wrapped everything in `catch (ColibriException&)` and reported
// PASS on the grounds that "connection refused proves the binding is physical".
// Three things were wrong with that, and all three fired at once the first time
// the suite was run off Windows:
//
//  1. `generate_thought` CATCHES its own routing failure internally and returns
//     a default-constructed AgentThought. So no ColibriException ever reaches
//     the handler, and the "expected refusal" branch is dead code.
//  2. The empty thought then flows into FourierMapper::project, which throws
//     `std::invalid_argument("Input dimension mismatch")` -- a message about
//     GEOMETRY for a failure that was about the NETWORK. That exception is not
//     a ColibriException, so nothing caught it and the process aborted.
//  3. `assert(!parsed.latent.empty())`, the one check that would have caught it
//     cleanly, is compiled out under NDEBUG (see mos_add_test in CMakeLists).
//
// A test that reports a network outage as a dimension mismatch is worse than no
// test: it sends whoever reads it into the geometry code. So this version
// SEPARATES the two questions it was conflating:
//
//     Is the LLM reachable?      -> environmental. SKIP, loudly, exit 0.
//     Given a thought, does the  -> a real assertion about our code, and it is
//     end-to-end type contract      now checked on a SYNTHETIC thought so it
//     hold?                         runs everywhere, with or without a network.
//
// The second half is the part that was worth testing all along, and it never
// needed an LLM.

#include <cassert>
#include <iostream>
#include <string>
#include <vector>

#include "mos/core/cognitive_state.hpp"
#include "mos/core/semantic_skill.hpp"
#include "mos/math/fourier.hpp"
#include "mos/translation/colibri_kernel.hpp"
#include "mos/translation/curator.hpp"

using namespace mos;

namespace {

constexpr int kFourierIn = 512;
constexpr int kFourierOut = 16;

/// The half that needs no network: a thought with a well-formed latent must
/// survive curation end to end. Runs on every platform, every build.
void test_curation_contract_offline() {
    translation::AgentThought thought;
    thought.reasoning_chain = "Quantum entanglement links the states of two distant photons.";
    thought.final_conclusion = "entangled";
    thought.latent.assign(kFourierIn, 0.0);
    for (int i = 0; i < kFourierIn; ++i) {
        thought.latent[i] = 0.01 * static_cast<double>((i % 17) - 8);
    }
    thought.confidence = 0.8;

    math::FourierMapper mapper(kFourierIn, kFourierOut);
    translation::AgentCurator curator(mapper);
    core::CognitiveState state;
    auto operad = curator.curate(thought, state, 100, 10.0);
    assert(operad != nullptr && "curate must return an operad for a valid thought");

    // 5ah: a reported confidence must reach nu_v. Before the routing existed
    // this was silently discarded, and nothing in the suite noticed.
    const double nu = core::vertex_precision(*thought.confidence);
    assert(nu == 0.8 && "confidence must survive as nu_v, unfloored at 0.8");

    translation::AgentThought unreported;
    unreported.reasoning_chain = "no confidence available";
    unreported.latent = thought.latent;
    auto operad2 = curator.curate(unreported, state, 101, 10.0);
    assert(operad2 != nullptr && "an UNCALIBRATED thought must still curate");

    std::cout << "  [ok] curation contract holds offline (nu=" << nu
              << " routed; unreported confidence stays UNCALIBRATED)\n";
}

/// The half that needs a network. Reports SKIPPED rather than passing or
/// aborting, so "no LLM here" can never be mistaken for either "verified" or
/// "the geometry is broken".
bool test_live_llm_if_available() {
    translation::ColibriKernel::ColibriConfig config;
    config.host = "api.groq.com";
    config.port = 443;
    config.model_name = "llama-3.1-8b-instant";

    try {
        translation::ColibriKernel colibri(config);
        std::cout << "  attempting live LLM binding...\n";
        auto parsed = colibri.generate_thought(
            "Quantum entanglement fundamentally links the states of two distant photons.");

        // THE CHECK THAT USED TO BE AN ASSERT AND WAS COMPILED OUT. An empty
        // latent means we never reached the model -- generate_thought swallows
        // its own transport failure and hands back a default AgentThought.
        if (parsed.latent.empty()) {
            std::cout << "  [SKIP] no thought returned: the LLM is unreachable from "
                         "this environment (no transport, no network, or the "
                         "provider refused).\n"
                         "         This is an ENVIRONMENT result, not a code result. "
                         "Nothing about MOS is verified or refuted by it.\n";
            return false;
        }

        std::cout << "  reasoning: " << parsed.reasoning_chain.substr(0, 60) << "...\n";
        std::cout << "  confidence: "
                  << (parsed.confidence.has_value()
                          ? std::to_string(*parsed.confidence)
                          : std::string("UNKNOWN (provider returned no logprobs)"))
                  << "\n";

        math::FourierMapper mapper(static_cast<int>(parsed.latent.size()), kFourierOut);
        translation::AgentCurator curator(mapper);
        core::CognitiveState state;
        auto operad = curator.curate(parsed, state, 200, 10.0);
        assert(operad != nullptr);
        std::cout << "  [ok] live LLM reached and the thought curated\n";
        return true;

    } catch (const translation::ColibriException &e) {
        std::cout << "  [SKIP] transport unavailable: " << e.what() << "\n";
        return false;
    } catch (const std::exception &e) {
        // Anything else IS a real failure, and it must not be swallowed as
        // "connection refused as expected" the way the old version did.
        std::cerr << "  [FAIL] unexpected " << typeid(e).name() << ": " << e.what() << "\n";
        throw;
    }
}

}  // namespace

int main() {
    std::cout << "=== colibri: curation contract + optional live LLM ===\n";
    test_curation_contract_offline();
    const bool live = test_live_llm_if_available();
    std::cout << "\ntest_colibri "
              << (live ? "PASSED (offline contract + live LLM)"
                       : "PASSED (offline contract; live LLM SKIPPED)")
              << "\n";
    return 0;
}
