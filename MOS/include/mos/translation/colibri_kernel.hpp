#pragma once

#include "mos/translation/llm_interface.hpp"
#include <string>
#include <stdexcept>

namespace mos {
namespace translation {

/// @brief Exception thrown when Colibri fails to connect or parse.
class ColibriException : public std::runtime_error {
public:
    explicit ColibriException(const std::string& msg) : std::runtime_error(msg) {}
};

/// @brief The final, physical C++ binding for the local Colibri (LLM) engine.
/// Connects to a local inference server via HTTP POST, parses text into triples,
/// and fetches the semantic embedding vectors natively.
class ColibriKernel : public LanguageKernel {
public:
    struct ColibriConfig {
        std::string host{"127.0.0.1"};
        int port{11434};
        std::string model_name{"gpt-4o"};
        std::string embedding_model{"nomic-embed-text"};
        float temperature{0.2f};
        std::string completions_route{"/v1/chat/completions"};
        std::string embeddings_route{"/v1/embeddings"};
    };

    /// @brief Construct the Colibri Kernel connection.
    /// @param config The full configuration parameters.
    explicit ColibriKernel(const ColibriConfig& config);
    
    ~ColibriKernel() override;

    /// @brief Generates a full reasoning chain using the LLM.
    [[nodiscard]] AgentThought generate_thought(const std::string& prompt) const override;
    
    std::vector<double> generate_embedding(const std::string& text) override;

private:
    ColibriConfig config_;
    void* session_{nullptr};
    void* connection_{nullptr};

    /// @brief Internal helper to send a raw HTTP POST and return the body.
    [[nodiscard]] std::string http_post(const std::string& endpoint, const std::string& json_payload) const;

    /// @brief Fetches the embedding vector for a given word.
    [[nodiscard]] std::vector<double> fetch_embedding(const std::string& text) const;

    /// @brief Minimal string parser to extract value from JSON.
    [[nodiscard]] std::string extract_json_value(const std::string& json, const std::string& key) const;
    
    /// @brief Minimal array parser to extract vector of doubles from JSON.
    [[nodiscard]] std::vector<double> extract_json_array(const std::string& json, const std::string& key) const;
};

} // namespace translation
} // namespace mos
