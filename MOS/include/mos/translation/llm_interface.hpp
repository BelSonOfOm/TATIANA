#pragma once

#include <optional>
#include <string>
#include <vector>

namespace mos {
namespace translation {

/// @brief Represents a full reasoning chain from an Agent (Colibri).
struct AgentThought {
    std::string reasoning_chain; // The full, unconstrained text output
    std::string final_conclusion; // The extracted final answer
    std::vector<double> latent;  // The physical embedding vector

    /// @brief Certainty of the thought, derived from token logprobs.
    /// EMPTY means genuinely UNKNOWN (the provider returned no logprobs) — it does
    /// NOT mean zero, and it must never be silently replaced by a made-up number.
    /// This field previously defaulted to a hardcoded 0.5, which flowed straight
    /// into the noise floor D of every stored concept (curator.cpp), making the
    /// entire Bures-Wasserstein geometry run on a constant variance.
    std::optional<double> confidence{};
};

/// @brief The pure virtual interface for the Language Kernel.
/// Abstract base class for any LLM endpoint connection.
class LanguageKernel {
public:
    virtual ~LanguageKernel() = default;

    /// @brief Generates a full mathematical thought from a prompt.
    /// @param prompt The input context or prompt for the agent.
    /// @return The AgentThought containing text, latent, and confidence.
    virtual AgentThought generate_thought(const std::string& prompt) const = 0;

    /// @brief Generate a true dense embedding vector from a mathematical query.
    virtual std::vector<double> generate_embedding(const std::string& text) = 0;
};

} // namespace translation
} // namespace mos
