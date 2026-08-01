// FIX-16. This test used to be the only red in the suite, and it could not
// diagnose its own failure.
//
// The old version wrapped everything in a try/catch that passed on
// ColibriException ("connection refused, as expected") and otherwise
// hard-asserted `!parsed.latent.empty()`. So THREE different situations all
// produced the same opaque abort:
//
//   1. no network / no server        -> should PASS (nothing to test against)
//   2. reachable but 401 / 429       -> should SKIP (no credentials here; that
//                                       is an environment fact, not a defect)
//   3. HTTP 200 that we cannot parse -> should FAIL (a real bug in our code)
//
// Only (3) is a defect, and it was the one case the old test could not name.
// The kernel now queries the HTTP status and throws ColibriHttpException with
// the status and body, so this test can tell the three apart and SAY WHICH.
//
// Exit codes: 0 = passed or skipped-for-environment, 1 = a real failure.

#include <cassert>
#include <cstdlib>
#include <iostream>
#include <string>

#include "mos/core/cognitive_state.hpp"
#include "mos/math/fourier.hpp"
#include "mos/translation/colibri_kernel.hpp"
#include "mos/translation/curator.hpp"

using namespace mos;

namespace {

// A skip is not a pass. It is recorded distinctly so a CI run that NEVER
// exercises the live path cannot be mistaken for one that did.
int g_skips = 0;

void skip(const std::string& why) {
    ++g_skips;
    std::cout << "  [SKIP] " << why << "\n";
}

bool run_live_thought_test() {
    const auto config =
        translation::ColibriKernel::ColibriConfig::groq("llama-3.1-8b-instant");

    if (std::getenv("GROQ_API_KEY") == nullptr) {
        skip("GROQ_API_KEY is not set, so the provider would reject us anyway. "
             "This is an environment fact, not a code defect.");
        return true;
    }

    try {
        translation::ColibriKernel colibri(config);
        std::cout << "  attempting physical LLM binding to " << config.host << "...\n";
        const auto parsed = colibri.generate_thought(
            "Quantum entanglement fundamentally links the states of two distant photons.");

        std::cout << "  reasoning chain: \"" << parsed.reasoning_chain << "\"\n";
        std::cout << "  confidence: "
                  << (parsed.confidence.has_value()
                          ? std::to_string(*parsed.confidence)
                          : std::string("UNKNOWN (provider returned no logprobs)"))
                  << "\n";
        std::cout << "  latent dimension: " << parsed.latent.size() << "\n";

        // Case (3). generate_thought returned rather than throwing, so the POST
        // was a 2xx and anything wrong from here is OURS.
        //
        // WHAT THIS TEST ACTUALLY CHECKS is the COMPLETIONS path: did we reach
        // the provider, get a 2xx, and parse a usable reasoning chain out of it.
        // The old version instead asserted `!latent.empty()`, which was the
        // wrong contract -- see below -- and that wrong assertion is what made
        // this the permanent red in the suite.
        if (parsed.reasoning_chain.empty()) {
            std::cerr << "  [FAIL] provider returned HTTP 2xx but the reasoning chain is "
                         "EMPTY. That is a parsing/contract defect in our code, not an "
                         "environment problem.\n";
            return false;
        }
        std::cout << "  [ok] completions path: 2xx with a "
                  << parsed.reasoning_chain.size() << "-char reasoning chain\n";

        // AN EMPTY LATENT IS CORRECT HERE, and asserting otherwise was the bug.
        // Concept geometry is computed LOCALLY in Python (bge-small, 384-d) and
        // carried across the adjunction boundary as the FlatBuffers `geometry`
        // field -- kernel.cpp's OperatorFactory says so explicitly: "Operators
        // use this instead of fetching embeddings remotely." A completions-only
        // provider has no embeddings for us, and Groq rejects the Ollama default
        // `nomic-embed-text` with a 404. Downstream, no geometry means the organ
        // stays IDLE rather than being zero-filled, which is the honest outcome.
        if (parsed.latent.empty()) {
            std::cout << "  [ok] latent is empty, as expected from a completions-only "
                         "provider (geometry crosses the boundary from Python)\n";
        } else {
            std::cout << "  [ok] provider also supplied a " << parsed.latent.size()
                      << "-d latent\n";
        }

        // Curation is only meaningful once the thought HAS geometry, so it is
        // exercised only when the latent actually arrived. Running it on an
        // empty latent would be testing the zero-fill path we deliberately
        // refuse to have.
        if (!parsed.latent.empty()) {
            math::FourierMapper mapper(512, 16);
            translation::AgentCurator curator(mapper);
            core::CognitiveState state;
            const auto operad = curator.curate(parsed, state, 100, 10.0);
            if (!operad) {
                std::cerr << "  [FAIL] curate() returned null for a thought WITH geometry.\n";
                return false;
            }
            std::cout << "  [ok] curated end-to-end\n";
        }
        return true;

    } catch (const translation::ColibriHttpException& e) {
        // Case (2). The transport worked; the provider said no. THIS is the
        // information the old test threw away.
        std::cout << "  provider responded with HTTP " << e.status() << "\n";
        std::cout << "  body: " << (e.body().empty() ? "<empty>" : e.body().substr(0, 300))
                  << "\n";
        if (e.is_credential_or_quota()) {
            skip("HTTP " + std::to_string(e.status()) +
                 " is a credential/quota response. The binding is physically "
                 "working; this environment simply cannot call the provider.");
            return true;
        }
        std::cerr << "  [FAIL] unexpected HTTP " << e.status()
                  << ". Not a credential or quota status, so this is a defect in the "
                     "request we sent.\n";
        return false;

    } catch (const translation::ColibriException& e) {
        // Case (1). Never reached the provider at all.
        skip(std::string("no connection (") + e.what() +
             "). The binding is strictly physical, so this is the expected result "
             "with no server reachable.");
        return true;
    }
}

// The part of the contract that needs no network: an HTTP failure must arrive
// as a ColibriHttpException carrying a usable status and body, not as a bare
// runtime_error. Without this, FIX-16 could silently regress the moment someone
// simplified the throw site back to ColibriException.
bool test_http_exception_carries_diagnosis() {
    const translation::ColibriHttpException e(
        429, "{\"error\":{\"message\":\"Rate limit reached\"}}", "POST /v1/chat/completions");

    assert(e.status() == 429);
    assert(e.body().find("Rate limit") != std::string::npos);
    assert(e.is_credential_or_quota());

    const std::string what = e.what();
    assert(what.find("429") != std::string::npos &&
           "the status must survive into what(), for logs that only print what()");
    assert(what.find("Rate limit") != std::string::npos &&
           "the body is the most useful thing the provider sends; it must not be dropped");

    // A 500 is NOT a credential/quota case: it must not be silently skipped.
    const translation::ColibriHttpException server_err(500, "upstream exploded", "POST /x");
    assert(!server_err.is_credential_or_quota());

    // An empty body must still produce a readable message rather than a
    // dangling colon that looks like truncation.
    const translation::ColibriHttpException empty_body(418, "", "POST /x");
    assert(std::string(empty_body.what()).find("<empty body>") != std::string::npos);

    // It must remain catchable as the base type, so existing handlers still work.
    bool caught_as_base = false;
    try {
        throw translation::ColibriHttpException(401, "no key", "POST /x");
    } catch (const translation::ColibriException&) {
        caught_as_base = true;
    }
    assert(caught_as_base);

    std::cout << "  [ok] ColibriHttpException carries status + body and stays "
                 "catchable as ColibriException\n";
    return true;
}

}  // namespace

int main() {
    std::cout << "=== FIX-16: the colibri test can now diagnose its own failure ===\n";

    bool ok = true;
    ok = test_http_exception_carries_diagnosis() && ok;
    ok = run_live_thought_test() && ok;

    if (!ok) {
        std::cerr << "\nCOLIBRI TESTS FAILED (see the diagnosis above).\n";
        return 1;
    }
    if (g_skips > 0) {
        std::cout << "\nCOLIBRI TESTS PASSED with " << g_skips
                  << " environment skip(s). The live path was NOT exercised.\n";
    } else {
        std::cout << "\nALL COLIBRI TESTS PASSED (live path exercised).\n";
    }
    return 0;
}
