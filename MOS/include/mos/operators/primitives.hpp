#pragma once

#include "mos/core/operator.hpp"
#include "mos/core/cognitive_state.hpp"
#include "mos/translation/knowledge_base.hpp"
#include "mos/translation/llm_interface.hpp"
#include <string>
#include <memory>
#include <iostream>

namespace mos {
namespace operators {

/// @brief SearchOp: Queries the KnowledgeBase for relevant mathematical truths.
class SearchOp : public core::CognitiveOperator {
public:
    /// @param geometry Locally-computed payload embedding from the FlatBuffer.
    /// Preferred over any remote embedding call (see ComputeOp for why).
    SearchOp(std::string query, std::shared_ptr<translation::KnowledgeBase> kb,
             std::shared_ptr<translation::LanguageKernel> llm,
             std::vector<double> geometry = {}, std::string organ = "SEARCH");

    bool apply(core::CognitiveState& state) override;
    core::OperatorType get_type() const noexcept override;
    std::set<int> get_support() const override;
    /// E7: stable operator identity for the assembly record.
    [[nodiscard]] const char *name() const noexcept override { return "SearchOp"; }

private:
    std::string query_;
    std::shared_ptr<translation::KnowledgeBase> kb_;
    std::shared_ptr<translation::LanguageKernel> llm_;
    std::vector<double> geometry_;
    std::string organ_;
};

/// @brief ComputeOp: A mutation operator that adds concrete mathematical calculations or structural logic.
class ComputeOp : public core::CognitiveOperator {
public:
    /// @param geometry The payload embedding computed LOCALLY on the Python side
    /// and carried in the FlatBuffer. Supplying it is the normal path: the engine
    /// must not fetch embeddings remotely (Groq has no /v1/embeddings endpoint, so
    /// every such call fails and ComputeOp becomes a silent no-op).
    ComputeOp(std::string logic_code, std::shared_ptr<translation::LanguageKernel> llm,
              float dt = 0.05f, float lambda = 2.0f,
              std::vector<double> geometry = {}, std::string organ = "COMPUTE");
    bool apply(core::CognitiveState& state) override;
    core::OperatorType get_type() const noexcept override;
    std::set<int> get_support() const override;
    /// E7: stable operator identity for the assembly record.
    [[nodiscard]] const char *name() const noexcept override { return "ComputeOp"; }

private:
    std::string logic_code_;
    std::shared_ptr<translation::LanguageKernel> llm_;
    float dt_;
    float lambda_;
    std::vector<double> geometry_;
    std::string organ_;
};

/// @brief ReasonOp: A mutation operator that invokes the LLM (Colibri) to reason over a premise.
class ReasonOp : public core::CognitiveOperator {
public:
    ReasonOp(std::string premise, std::shared_ptr<translation::LanguageKernel> llm,
             std::vector<double> geometry = {}, std::string organ = "REASON");

    bool apply(core::CognitiveState& state) override;
    core::OperatorType get_type() const noexcept override;
    std::set<int> get_support() const override;
    /// E7: stable operator identity for the assembly record.
    [[nodiscard]] const char *name() const noexcept override { return "ReasonOp"; }

private:
    std::string premise_;
    std::shared_ptr<translation::LanguageKernel> llm_;
    std::vector<double> geometry_;
    std::string organ_;
};

/// @brief RespondOp: A read-only operator that formats the active section to respond to the user.
class RespondOp : public core::CognitiveOperator {
public:
    RespondOp(std::string response_context);

    bool apply(core::CognitiveState& state) override;
    core::OperatorType get_type() const noexcept override;
    std::set<int> get_support() const override;
    /// E7: stable operator identity for the assembly record.
    [[nodiscard]] const char *name() const noexcept override { return "RespondOp"; }

private:
    std::string response_context_;
};

/// @brief VerifyOp: A mutation operator that executes external tools/terminal commands to objectively verify mathematical truths.
class VerifyOp : public core::CognitiveOperator {
public:
    VerifyOp(std::string command);

    bool apply(core::CognitiveState& state) override;
    core::OperatorType get_type() const noexcept override;
    std::set<int> get_support() const override;
    /// E7: stable operator identity for the assembly record.
    [[nodiscard]] const char *name() const noexcept override { return "VerifyOp"; }

private:
    std::string command_;
};

/// @brief ContextOp: A boundary condition operator that injects a Temporary Axiom into the topological space.
class ContextOp : public core::CognitiveOperator {
public:
    struct Constraint {
        bool is_rigid;
        std::vector<float> geometry;
    };

    ContextOp(std::string payload, std::vector<Constraint> constraints,
              std::string organ = "CONTEXT");

    bool apply(core::CognitiveState& state) override;
    core::OperatorType get_type() const noexcept override;
    std::set<int> get_support() const override;
    /// E7: stable operator identity for the assembly record.
    [[nodiscard]] const char *name() const noexcept override { return "ContextOp"; }

private:
    std::string payload_;
    std::vector<Constraint> constraints_;
    std::string organ_;
};

} // namespace operators
} // namespace mos
