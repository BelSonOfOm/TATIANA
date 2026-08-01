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

/// @brief FIX-16. Thrown when the transport SUCCEEDED but the provider returned
/// a non-2xx status.
///
/// This distinction is the whole point. Before this existed, `http_post` never
/// asked for the status code and returned the body regardless, so a 401 (bad
/// key), a 429 (quota) and a 200-with-unexpected-shape all flowed onward
/// identically, parsed into an empty thought, and surfaced as one opaque
/// `assert(!parsed.latent.empty())` abort that said nothing about which had
/// happened.
///
/// Carrying the status and body as STRUCTURED FIELDS rather than only in
/// `what()` lets callers discriminate programmatically — a test can treat 401 as
/// "no credentials in this environment, skip" while still failing hard on a 200
/// it could not parse, which is a real defect in our code.
class ColibriHttpException : public ColibriException {
public:
    ColibriHttpException(int status, std::string body, const std::string& context)
        : ColibriException(context + " HTTP " + std::to_string(status) + ": " +
                           (body.empty() ? std::string("<empty body>")
                                         : body.substr(0, 400))),
          status_(status), body_(std::move(body)) {}

    /// @brief The HTTP status code. 0 means it could not be queried.
    [[nodiscard]] int status() const noexcept { return status_; }

    /// @brief The full response body, untruncated (what() truncates for display).
    [[nodiscard]] const std::string& body() const noexcept { return body_; }

    /// @brief True for the statuses that mean "this environment cannot reach the
    /// provider", as opposed to "our request or parsing is wrong".
    [[nodiscard]] bool is_credential_or_quota() const noexcept {
        return status_ == 401 || status_ == 403 || status_ == 429;
    }

private:
    int status_;
    std::string body_;
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
        // Defaults are OLLAMA-shaped, matching the default host/port above.
        std::string completions_route{"/v1/chat/completions"};
        std::string embeddings_route{"/v1/embeddings"};

        /// @brief Groq's OpenAI-compatible endpoints, which live under an
        /// `/openai` prefix.
        ///
        /// FIX-16 found that `main.cpp` and the colibri test both set
        /// `host = api.groq.com` while leaving the OLLAMA routes in place, so
        /// every request 404'd with "Unknown request URL". Nothing noticed,
        /// because the 404 body was parsed as if it were a completion and became
        /// an empty thought. `python/router.py` had the correct URL all along
        /// (`https://api.groq.com/openai/v1/chat/completions`); the C++ side
        /// simply never matched it.
        ///
        /// Exists so the provider's URL shape is stated ONCE. Two call sites
        /// independently getting it wrong is how this bug happened.
        [[nodiscard]] static ColibriConfig groq(std::string model) {
            ColibriConfig c;
            c.host = "api.groq.com";
            c.port = 443;
            c.model_name = std::move(model);
            c.completions_route = "/openai/v1/chat/completions";
            c.embeddings_route = "/openai/v1/embeddings";
            return c;
        }
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
