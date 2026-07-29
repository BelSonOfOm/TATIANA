#include "mos/translation/colibri_kernel.hpp"
#include "json.hpp"
#include <cmath>
#include <iostream>
#include <map>

#define NOMINMAX
#include <windows.h>
#include <winhttp.h>

#pragma comment(lib, "winhttp.lib")

namespace mos {
namespace translation {

class WinHttpHandle {
public:
  HINTERNET h;
  explicit WinHttpHandle(HINTERNET handle) : h(handle) {}
  ~WinHttpHandle() {
    if (h)
      WinHttpCloseHandle(h);
  }
  operator HINTERNET() const { return h; }
};

ColibriKernel::ColibriKernel(const ColibriConfig &config) : config_(config) {
  std::wstring whost = std::wstring(config_.host.begin(), config_.host.end());
  HINTERNET hSession = WinHttpOpen(L"Colibri/1.0", WINHTTP_ACCESS_TYPE_DEFAULT_PROXY, WINHTTP_NO_PROXY_NAME, WINHTTP_NO_PROXY_BYPASS, 0);
  if (!hSession) throw ColibriException("WinHttpOpen failed.");
  session_ = hSession;

  HINTERNET hConnect = WinHttpConnect(hSession, whost.c_str(), config_.port, 0);
  if (!hConnect) {
      WinHttpCloseHandle(hSession);
      throw ColibriException("WinHttpConnect failed.");
  }
  connection_ = hConnect;
}

ColibriKernel::~ColibriKernel() {
  if (connection_) WinHttpCloseHandle(static_cast<HINTERNET>(connection_));
  if (session_) WinHttpCloseHandle(static_cast<HINTERNET>(session_));
}

std::string ColibriKernel::http_post(const std::string &endpoint,
                                     const std::string &json_payload) const {
  std::wstring wEndpoint(endpoint.begin(), endpoint.end());

  HINTERNET hConnect = static_cast<HINTERNET>(connection_);

  DWORD dwFlags =
      (config_.port == INTERNET_DEFAULT_HTTPS_PORT) ? WINHTTP_FLAG_SECURE : 0;
  WinHttpHandle hRequest(WinHttpOpenRequest(
      hConnect, L"POST", wEndpoint.c_str(), NULL, WINHTTP_NO_REFERER,
      WINHTTP_DEFAULT_ACCEPT_TYPES, dwFlags));
  if (!hRequest.h)
    throw ColibriException("WinHttpOpenRequest failed.");

  std::wstring headers = L"Content-Type: application/json\r\n";

  const char *env_key = std::getenv("GROQ_API_KEY");
  if (env_key) {
    std::string auth = "Authorization: Bearer " + std::string(env_key) + "\r\n";
    headers += std::wstring(auth.begin(), auth.end());
  }

  if (!WinHttpSendRequest(
          hRequest, headers.c_str(), (DWORD)-1, (LPVOID)json_payload.c_str(),
          (DWORD)json_payload.size(), (DWORD)json_payload.size(), 0)) {
    throw ColibriException("WinHttpSendRequest failed.");
  }

  if (!WinHttpReceiveResponse(hRequest, NULL)) {
    throw ColibriException("WinHttpReceiveResponse failed.");
  }

  std::string response;
  DWORD dwSize = 0;
  DWORD dwDownloaded = 0;
  do {
    WinHttpQueryDataAvailable(hRequest, &dwSize);
    if (dwSize == 0)
      break;
    std::vector<char> buffer(dwSize + 1, 0);
    WinHttpReadData(hRequest, (LPVOID)buffer.data(), dwSize, &dwDownloaded);
    response.append(buffer.data(), dwDownloaded);
  } while (dwSize > 0);

  return response;
}

std::string ColibriKernel::extract_json_value(const std::string &json,
                                              const std::string &key) const {
  try {
    nlohmann::json j = nlohmann::json::parse(json);

    // Structured API Check (e.g. OpenAI choices[0].message)
    if (j.contains("choices") && j["choices"].is_array() &&
        !j["choices"].empty()) {
      if (j["choices"][0].contains("message") &&
          j["choices"][0]["message"].contains(key)) {
        return j["choices"][0]["message"][key].get<std::string>();
      }
    }

    // Flat API Check (e.g. Local models)
    if (j.contains(key) && j[key].is_string()) {
      return j[key].get<std::string>();
    }
  } catch (const nlohmann::json::exception &e) {
    std::cerr << "[ColibriKernel] JSON Exception in extract_json_value: "
              << e.what() << "\n";
  }
  return "";
}

std::vector<double>
ColibriKernel::extract_json_array(const std::string &json,
                                  const std::string &key) const {
  std::vector<double> result;
  try {
    nlohmann::json j = nlohmann::json::parse(json);

    // Standard payload: data array
    if (j.contains("data") && j["data"].is_array() && !j["data"].empty()) {
      if (j["data"][0].contains(key) && j["data"][0][key].is_array()) {
        for (const auto &val : j["data"][0][key]) {
          result.push_back(val.get<double>());
        }
        return result;
      }
    }

    // Root array access payload
    if (j.contains(key) && j[key].is_array()) {
      for (const auto &val : j[key]) {
        result.push_back(val.get<double>());
      }
    }
  } catch (const nlohmann::json::exception &e) {
    std::cerr << "[ColibriKernel] JSON Array Exception: " << e.what() << "\n";
  }

  return result;
}

std::vector<double>
ColibriKernel::fetch_embedding(const std::string &text) const {
  nlohmann::json req;
  req["model"] = config_.embedding_model;
  req["input"] = text;
  std::string payload = req.dump();

  std::string response;
  try {
    response = http_post(config_.embeddings_route, payload);
  } catch (const std::exception &e) {
    throw ColibriException("Embedding fetch failed: " + std::string(e.what()));
  }

  std::vector<double> embedding = extract_json_array(response, "embedding");
  if (embedding.empty()) {
    throw ColibriException("Failed to extract embedding array from response.");
  }

  return embedding;
}

AgentThought ColibriKernel::generate_thought(const std::string &prompt) const {
  AgentThought thought;
  nlohmann::json req;
  req["model"] = config_.model_name;
  req["temperature"] = config_.temperature;
  // NOT requesting logprobs: verified empirically (2026-07-22) that Groq's
  // llama-3.1-8b-instant returns a HARD 400 error ("logprobs is not supported
  // with this model") rather than silently omitting them. Unconditionally
  // setting this to true would have broken every single call to this model.
  // Confidence is therefore always UNKNOWN from this provider/model pair; see
  // AgentThought::confidence and Construction 2b (rho replaces self-reported
  // confidence as the primary signal for exactly this reason).

  nlohmann::json message;
  message["role"] = "user";
  message["content"] = prompt;

  req["messages"] = nlohmann::json::array({message});
  std::string payload = req.dump();

  std::string response;
  try {
    response = http_post(config_.completions_route, payload);
  } catch (const std::exception &e) {
    std::cerr << "[ColibriKernel] Engine routing failed: " << e.what() << "\n";
    return thought;
  }

  try {
    nlohmann::json j = nlohmann::json::parse(response);
    if (j.contains("choices") && !j["choices"].empty()) {
      auto &choice = j["choices"][0];
      if (choice.contains("message") && choice["message"].contains("content")) {
        std::string text_output =
            choice["message"]["content"].get<std::string>();

        try {
          nlohmann::json parsed = nlohmann::json::parse(text_output);
          if (parsed.contains("reasoning") && parsed.contains("conclusion")) {
            thought.reasoning_chain = parsed["reasoning"].get<std::string>();
            thought.final_conclusion = parsed["conclusion"].get<std::string>();
          } else {
            thought.reasoning_chain = text_output;
            thought.final_conclusion = text_output;
          }
        } catch (const nlohmann::json::exception &) {
          thought.reasoning_chain = text_output;
          thought.final_conclusion = text_output;
        }
      }

      if (choice.contains("logprobs") && !choice["logprobs"].is_null()) {
        auto &logprobs_obj = choice["logprobs"];
        if (logprobs_obj.contains("content") &&
            logprobs_obj["content"].is_array()) {
          double total_entropy = 0.0;
          size_t count = 0;
          for (const auto &token_obj : logprobs_obj["content"]) {
            if (token_obj.contains("logprob")) {
              double logp = token_obj["logprob"].get<double>();
              double p = std::exp(logp);
              total_entropy += (-p * logp);
              count++;
            }
          }
          if (count > 0) {
            double avg_entropy = total_entropy / count;
            thought.confidence = std::max(0.0, 1.0 - avg_entropy);
          }
        }
      } else {
        // The provider returned no logprobs, so confidence is genuinely UNKNOWN.
        // We leave it EMPTY rather than inventing a number. The previous code set
        // a hardcoded 0.5 here; because this branch is the one that actually runs
        // against Groq, that constant propagated into compute_variance() and gave
        // EVERY stored concept the same noise floor D = -ln(0.5), silently turning
        // the Bures-Wasserstein geometry into a constant.
        thought.confidence.reset();
      }
    }
  } catch (const nlohmann::json::exception &e) {
    std::cerr << "[ColibriKernel] generate_thought JSON parse error: "
              << e.what() << "\n";
  }

  // Validate empty latent mapping fallback
  try {
    thought.latent = fetch_embedding(thought.reasoning_chain);
  } catch (...) {
    thought.latent = std::vector<double>();
  }
  return thought;
}

std::vector<double> ColibriKernel::generate_embedding(const std::string &text) {
  return fetch_embedding(text);
}

} // namespace translation
} // namespace mos