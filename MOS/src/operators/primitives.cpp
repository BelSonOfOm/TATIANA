#include "mos/operators/primitives.hpp"
#include "mos/core/semantic_skill.hpp"
#include <cmath>
#include <iostream>
#include <algorithm>
#ifdef _WIN32
#define NOMINMAX
#include <windows.h>
#endif
#include "json.hpp"

namespace mos {
namespace operators {

// --- SearchOp ---

SearchOp::SearchOp(std::string query,
                   std::shared_ptr<translation::KnowledgeBase> kb,
                   std::shared_ptr<translation::LanguageKernel> llm,
                   std::vector<double> geometry, std::string organ)
    : query_(std::move(query)), kb_(std::move(kb)), llm_(std::move(llm)),
      geometry_(std::move(geometry)), organ_(std::move(organ)) {}

bool SearchOp::apply(core::CognitiveState &state) {
  std::cout << "[SearchOp] Searching for: " << query_ << "\n";
  if (kb_) {
    // Prefer the locally-computed geometry carried in the payload; only fall back
    // to a remote embedding call if none was supplied (see ComputeOp for why that
    // fallback fails against Groq).
    std::vector<double> query_embedding = geometry_;
    if (query_embedding.empty()) {
      if (!llm_) {
        std::cerr << "[SearchOp] No geometry and no LanguageKernel; cannot search.\n";
        return true;
      }
      try {
        query_embedding = llm_->generate_embedding(query_);
      } catch (const std::exception &e) {
        std::cerr << "[SearchOp] No geometry in payload and remote embedding "
                     "failed: " << e.what() << "\n";
        return true;
      }
    }
    if (query_embedding.empty()) {
      std::cerr << "[SearchOp] Empty query geometry; skipping retrieval.\n";
      return true;
    }

    // P0 -- RANK, DO NOT THRESHOLD. Spec: DOCS/SPEC_P0_RETRIEVAL_FIX.md.
    //
    // Two computations stood here and both are gone rather than kept:
    //
    //   * a "dynamic relevance threshold", max(0.1, 1/d), which at d = 384 is
    //     0.1 for every query the system will ever see. MEASUREMENT: that policy
    //     admits 0.31% of author-asserted true dependencies, against 46.6% for
    //     rank-based retrieval at the same width.
    //
    //   * a "derived variance" set to the query's NORM -- a quantity with no
    //     derivation behind it. It fed only the epistemic term, which the new
    //     ranking does not use, so removing the threshold removed this too.
    //
    // Width now comes from KnowledgeBase::kDefaultRetrievalWidth, which is
    // BOUNDED ABOVE by ConceptStore::max_assembly_for_triangles_ so that a tick
    // can never produce an assembly whose triangles get skipped -- skipped
    // triangles leave within-assembly cycles that look exactly like structural
    // holes in b1.
    auto concepts = kb_->get_top_k_concepts(
        Eigen::Map<Eigen::VectorXd>(query_embedding.data(),
                                    query_embedding.size()));
    std::cout << "[SearchOp] Retrieved " << concepts.size()
              << " nearest concepts.\n";

    // Inject retrieved concepts into the cognitive state as new boundary
    // conditions
    for (const auto &concept : concepts) {
      std::vector<float> geometry(concept->get_mu().size());
      for (int i = 0; i < concept->get_mu().size(); ++i) {
        geometry[i] = static_cast<float>(concept->get_mu()(i));
      }
      state.inject_temporary_axiom(concept->get_name(), false, geometry, organ_);
      // E7: THIS is the co-activation event Construction 5 is fitted to. One
      // Wasserstein query returns a SET of stored concepts, and overlapping sets
      // across ticks are exactly the structure a latent-cause model explains.
      // Recorded here rather than inside inject_temporary_axiom because that
      // method also serves hand-injected axioms, which are not retrievals.
      state.note_retrieved(concept->get_name(), concept->get_mu());
    }

    // NEUROGENESIS: the query itself becomes a permanent concept vertex,
    // regardless of whether the knowledge base had any matches. Without this,
    // an empty-KB search (the common case before anything has been consolidated)
    // leaves NO trace of "the system was actively pursuing this topic" — the
    // fine complex would stay exactly as empty as before the search ran.
    try {
      state.grow_concept(query_, query_embedding, organ_);
    } catch (const std::invalid_argument &e) {
      std::cerr << "[SearchOp] " << e.what() << "\n";
    }
  } else {
    std::cout << "[SearchOp] Error: Execution context missing KB or LLM.\n";
  }
  return true;
}

core::OperatorType SearchOp::get_type() const noexcept {
  return core::OperatorType::READ_ONLY;
}

std::set<int> SearchOp::get_support() const {
  // P1. The planner's resolved concepts when it named any; otherwise the legacy
  // token. Empty is the right unscoped answer here either way -- a search reads
  // the whole store, and READ_ONLY empty-support nodes co-schedule freely.
  if (explicit_support_) return *explicit_support_;
  return {}; // Global read
}

// --- ComputeOp ---

ComputeOp::ComputeOp(std::string logic_code,
                     std::shared_ptr<translation::LanguageKernel> llm, float dt,
                     float lambda, std::vector<double> geometry,
                     std::string organ)
    : logic_code_(std::move(logic_code)), llm_(std::move(llm)), dt_(dt),
      lambda_(lambda), geometry_(std::move(geometry)),
      organ_(std::move(organ)) {}

bool ComputeOp::apply(core::CognitiveState &state) {
  if (!llm_)
    return false;

  // Calculate current structural strain
  double initial_conflict = state.calculate_conflict_score();

  nlohmann::json out;
  out["operator"] = "Compute";
  out["initial_strain"] = initial_conflict;
  out["logic"] = logic_code_;
  std::cout << out.dump(2) << "\n";

  // 1. Obtain the deduction direction.
  // NORMAL PATH: use the geometry embedded LOCALLY on the Python side and carried
  // across the adjunction boundary in the FlatBuffer. The engine deliberately does
  // NOT fetch embeddings remotely: the configured provider (Groq) has no
  // /v1/embeddings endpoint, so that call fails 100% of the time — which used to
  // make this operator `return false` and silently do nothing at all.
  std::vector<double> latent_direction = geometry_;

  if (latent_direction.empty()) {
    // Legacy fallback, kept only for LanguageKernels that genuinely serve
    // embeddings. Failure here is reported and the operator aborts honestly
    // rather than pretending to have applied a flow.
    if (!llm_) {
      std::cerr << "[ComputeOp] No geometry supplied and no LanguageKernel; "
                   "cannot compute a deduction direction.\n";
      return false;
    }
    try {
      latent_direction = llm_->generate_embedding(logic_code_);
    } catch (const std::exception &e) {
      std::cerr << "[ComputeOp] No geometry in payload and remote embedding "
                   "failed: "
                << e.what()
                << ". (Expected against Groq: it serves no embeddings. Python "
                   "should attach operator geometry.)\n";
      return false;
    }
  }

  if (latent_direction.empty()) {
    std::cerr << "[ComputeOp] Empty deduction direction; refusing to apply a "
                 "zero flow that would look like work.\n";
    return false;
  }

  // 2. NEUROGENESIS: this computation becomes a new concept vertex in C_math.
  // Without this, apply_flow() below has nothing to act on beyond whatever
  // CONTEXT axioms happen to already exist, and calculate_conflict_score()
  // needs at least TWO concepts to report anything but a trivial 0 — so a
  // ComputeOp following a single CONTEXT node would always measure zero strain
  // change, even though real computation occurred.
  try {
    state.grow_concept(logic_code_, latent_direction, organ_);
  } catch (const std::invalid_argument &e) {
    std::cerr << "[ComputeOp] " << e.what() << "\n";
    return false;
  }

  // 3. Convert to float vector (F_deduce)
  Eigen::VectorXf F_deduce(latent_direction.size());
  for (size_t i = 0; i < latent_direction.size(); ++i) {
    F_deduce(i) = static_cast<float>(latent_direction[i]);
  }

  // 4. Apply physical flow using configured integration parameters
  state.apply_flow(F_deduce, dt_, lambda_);

  double final_conflict = state.calculate_conflict_score();

  nlohmann::json success;
  success["status"] = "Compute_Success";
  success["delta_strain"] = (final_conflict - initial_conflict);
  std::cout << success.dump(2) << "\n";

  return true;
}

core::OperatorType ComputeOp::get_type() const noexcept {
  return core::OperatorType::MUTATION;
}

std::set<int> ComputeOp::get_support() const {
  if (explicit_support_) return *explicit_support_;
  return {0}; // Touches fundamental vertices
}

// --- ReasonOp ---

ReasonOp::ReasonOp(std::string premise,
                   std::shared_ptr<translation::LanguageKernel> llm,
                   std::vector<double> geometry, std::string organ)
    : premise_(std::move(premise)), llm_(std::move(llm)),
      geometry_(std::move(geometry)), organ_(std::move(organ)) {}

bool ReasonOp::apply(core::CognitiveState &state) {
  double initial_conflict = state.calculate_conflict_score();
  nlohmann::json out;
  out["operator"] = "Reason";
  out["initial_strain"] = initial_conflict;
  out["premise"] = premise_;
  std::cout << out.dump(2) << "\n";

  // ReasonOp evaluates the principal component PCA stress (algebraic eigenvalue
  // gap) to measure the structural contradiction inside the active cognitive
  // state.
  Eigen::VectorXf stress_vec = state.get_principal_stress_vector();
  double conflict = state.calculate_conflict_score();

  // Convert mathematical tension into LLM context
  std::string internal_prompt = "PREMISE: " + premise_ + "\n";
  internal_prompt +=
      "TOPOLOGICAL CONFLICT SCORE: " + std::to_string(conflict) + "\n";
  internal_prompt += "Evaluate the truth value and mathematical consistency of "
                     "the premise against the current state.";

  translation::AgentThought thought;
  try {
    thought = llm_->generate_thought(internal_prompt);
  } catch (const std::exception &e) {
    std::cerr << "[ReasonOp] LLM evaluation failed: " << e.what() << "\n";
    return false;
  }

  nlohmann::json success;
  success["status"] = "Reason_Analyzed";
  success["premise"] = premise_;
  success["topological_obstruction"] = conflict;
  success["reasoning"] = thought.reasoning_chain;
  std::cout << success.dump(2) << "\n";

  // NEUROGENESIS: the premise this operator just reasoned about becomes a
  // permanent concept vertex. Prefer the locally-computed payload geometry
  // (crosses the boundary for free); fall back to thought.latent only if the
  // LanguageKernel genuinely populated it, since the configured provider (Groq)
  // serves no embeddings and that field is typically empty.
  const std::vector<double> &grow_geometry =
      !geometry_.empty() ? geometry_ : thought.latent;
  try {
    state.grow_concept(premise_, grow_geometry, organ_);
  } catch (const std::invalid_argument &e) {
    std::cerr << "[ReasonOp] " << e.what() << "\n";
  }

  // Store in global section for resolution
  state.get_section().set_obstruction(conflict);

  return true;
}

core::OperatorType ReasonOp::get_type() const noexcept {
  return core::OperatorType::MUTATION;
}

std::set<int> ReasonOp::get_support() const {
  if (explicit_support_) return *explicit_support_;
  return {1}; // Touches specific reasoning vertices
}

// --- RespondOp ---

RespondOp::RespondOp(std::string response_context)
    : response_context_(std::move(response_context)) {}

bool RespondOp::apply(core::CognitiveState &state) {
  // The actual text is now printed by ComputeOp/ReasonOp when they fetch it
  // from the LLM, so RespondOp just finalizes the state update.
  std::cout << "[RespondOp] Topological alignment complete.\n";
  return true;
}

core::OperatorType RespondOp::get_type() const noexcept {
  return core::OperatorType::READ_ONLY;
}

std::set<int> RespondOp::get_support() const {
  if (explicit_support_) return *explicit_support_;
  return {}; // Read only
}

// --- VerifyOp ---

VerifyOp::VerifyOp(std::string command) : command_(std::move(command)) {}

bool VerifyOp::apply(core::CognitiveState &state) {
  std::cout << "[VerifyOp] Attempting objective verification tool: " << command_
            << "\n";

  // SECURITY WHITELIST
  // For this MVP, we strictly only allow the python executable and basic flags.
  // If we detect any shell operators (&, |, ;, >, <, `), we instantly reject.
  // EVERY SECURITY BLOCK BELOW IS **UNVERIFIABLE**, NOT REFUTED.
  // The block is a fact about the COMMAND, not about the CLAIM: the oracle was
  // never allowed to run, so nothing was learned about whether the mathematics
  // holds. Recording these as Refuted would set gamma = 0 and, worse, would
  // teach the store that a malformed verification command is evidence of a false
  // claim. The severe obstruction penalty is a separate mechanism and is left
  // exactly as it was -- it punishes the attempted break-out, which is right.
  if (command_.find_first_of("&|;><`") != std::string::npos) {
    std::cerr
        << "[VerifyOp] SECURITY BLOCK: Metacharacters detected in command: "
        << command_ << "\n";
    state.note_verdict(core::Verdict::Unverifiable);
    state.get_section().set_obstruction(
        10000.0); // Severe penalty for trying to break out
    return true;
  }

  // Ensure command starts with an approved executable
  if (command_.find("python ") != 0 && command_.find("lean ") != 0) {
    std::cerr << "[VerifyOp] SECURITY BLOCK: Unapproved executable. Only "
                 "'python' and 'lean' are allowed.\n";
    state.note_verdict(core::Verdict::Unverifiable);
    state.get_section().set_obstruction(10000.0);
    return true;
  }

  // Ban the '-c' flag entirely for python
  if (command_.find(" -c") != std::string::npos ||
      command_.find(" -c ") != std::string::npos) {
    std::cerr << "[VerifyOp] SECURITY BLOCK: Inline code execution (-c) is "
                 "banned. Must use absolute file paths.\n";
    state.note_verdict(core::Verdict::Unverifiable);
    state.get_section().set_obstruction(10000.0);
    return true;
  }

  std::cout << "[VerifyOp] Command passed security whitelist. Executing...\n";

  std::string result = "";
  int exit_code = -1;

#ifdef _WIN32
  // Secure process execution bypassing the shell, capturing stdout/stderr via
  // CreatePipe
  HANDLE hStdOutRead = NULL;
  HANDLE hStdOutWrite = NULL;

  SECURITY_ATTRIBUTES saAttr;
  saAttr.nLength = sizeof(SECURITY_ATTRIBUTES);
  saAttr.bInheritHandle = TRUE;
  saAttr.lpSecurityDescriptor = NULL;

  if (!CreatePipe(&hStdOutRead, &hStdOutWrite, &saAttr, 0)) {
    std::cerr << "[VerifyOp] CreatePipe failed. Error: " << GetLastError()
              << "\n";
    state.get_section().set_obstruction(10000.0);
    return true;
  }

  SetHandleInformation(hStdOutRead, HANDLE_FLAG_INHERIT, 0);

  STARTUPINFOA si;
  PROCESS_INFORMATION pi;
  ZeroMemory(&si, sizeof(si));
  si.cb = sizeof(si);
  si.hStdError = hStdOutWrite;
  si.hStdOutput = hStdOutWrite;
  si.dwFlags |= STARTF_USESTDHANDLES;

  ZeroMemory(&pi, sizeof(pi));

  // Must copy string because CreateProcessA may modify it
  std::string cmd = command_;
  if (CreateProcessA(NULL, &cmd[0], NULL, NULL, TRUE, 0, NULL, NULL, &si,
                     &pi)) {
    // Close the write end of the pipe in the parent process so we can read from
    // it
    CloseHandle(hStdOutWrite);
    hStdOutWrite = NULL;

    DWORD dwRead;
    CHAR chBuf[4096];
    BOOL bSuccess = FALSE;

    for (;;) {
      bSuccess = ReadFile(hStdOutRead, chBuf, 4096, &dwRead, NULL);
      if (!bSuccess || dwRead == 0)
        break;
      result.append(chBuf, dwRead);
    }

    WaitForSingleObject(pi.hProcess, INFINITE);
    DWORD dwExitCode = 0;
    GetExitCodeProcess(pi.hProcess, &dwExitCode);
    exit_code = static_cast<int>(dwExitCode);

    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
  } else {
    std::cerr << "[VerifyOp] CreateProcess failed. Error: " << GetLastError()
              << "\n";
    CloseHandle(hStdOutWrite);
  }
  CloseHandle(hStdOutRead);
#else
  // POSIX fallback if needed, but assuming Windows based on OS kernel
  exit_code = std::system(command_.c_str());
#endif

  std::cout << "[VerifyOp] Execution complete. Exit Code: " << exit_code
            << "\n";
  if (!result.empty()) {
    std::cout << "[VerifyOp] Output: \n" << result << "\n";
  }

  // THREE outcomes, not two. The oracle (verify/check.py) distinguishes:
  //   0 = VERIFIED      the claim was checked and holds
  //   1 = REFUTED       the claim was checked and is FALSE
  //   2 = UNVERIFIABLE  the checker could not decide
  //
  // Collapsing 1 and 2 together — as this code previously did by treating every
  // nonzero exit as failure — is a real epistemic error: INABILITY TO CHECK IS
  // NOT EVIDENCE OF FALSEHOOD. Spiking conflict on UNVERIFIABLE would make the
  // system distrust perfectly good mathematics merely because the oracle is
  // limited, and would lock it in RESOLVE mode over its own blind spots.
  constexpr int VERIFY_VERIFIED = 0;
  constexpr int VERIFY_REFUTED = 1;
  constexpr int VERIFY_UNVERIFIABLE = 2;

  // The verdict is now PUBLISHED as well as acted on. Until this call existed
  // the three-way distinction above changed the obstruction and was then thrown
  // away, so gamma_nu -- which takes a Verdict, not a number -- had no input and
  // i_shriek could never run. Same value fills E7's `verified` column.
  if (exit_code == VERIFY_VERIFIED) {
    std::cout << "[VerifyOp] VERIFIED. Obstruction cleared.\n";
    // Externally grounded: the state may crystallize.
    state.note_verdict(core::Verdict::Verified);
    state.get_section().set_obstruction(0.0);
  } else if (exit_code == VERIFY_REFUTED) {
    std::cout << "[VerifyOp] REFUTED. Spiking global conflict measure.\n";
    // A genuine contradiction with external reality: force RESOLVE mode.
    state.note_verdict(core::Verdict::Refuted);
    double current_conflict = state.calculate_conflict_score();
    state.get_section().set_obstruction(current_conflict + 1000.0);
  } else {
    state.note_verdict(core::Verdict::Unverifiable);
    // UNVERIFIABLE (2) or any unexpected exit code. We learned nothing, so we
    // change nothing: leave the obstruction exactly as the topology computed it.
    std::cout << "[VerifyOp] UNVERIFIABLE (exit " << exit_code
              << "). Claim NOT checked; leaving obstruction untouched. "
                 "Absence of proof is not proof of absence.\n";
  }

  return true;
}

core::OperatorType VerifyOp::get_type() const noexcept {
  return core::OperatorType::MUTATION;
}

std::set<int> VerifyOp::get_support() const {
  // P2 depends on this one specifically: a verifier that cannot be told WHICH
  // concepts it is checking has nothing to check them against.
  if (explicit_support_) return *explicit_support_;
  return {0};
}

// --- ContextOp ---

ContextOp::ContextOp(std::string payload, std::vector<Constraint> constraints,
                     std::string organ)
    : payload_(std::move(payload)), constraints_(std::move(constraints)),
      organ_(std::move(organ)) {}

bool ContextOp::apply(core::CognitiveState &state) {
  std::cout << "[ContextOp] Injecting Temporary Axiom: " << payload_ << "\n";
  if (constraints_.empty()) {
    std::cout << "[ContextOp] Error: Missing strict geometric constraints. "
                 "Injection rejected.\n";
    return false;
  } else {
    for (const auto &c : constraints_) {
      if (c.geometry.empty()) {
        std::cout << "[ContextOp] Error: Empty constraint geometry. Injection "
                     "rejected.\n";
        return false;
      }
      state.inject_temporary_axiom(payload_, c.is_rigid, c.geometry, organ_);
    }
  }
  return true;
}

core::OperatorType ContextOp::get_type() const noexcept {
  return core::OperatorType::MUTATION;
}

std::set<int> ContextOp::get_support() const {
  if (explicit_support_) return *explicit_support_;
  // 0-simplices are fundamental constructs
  return {0};
}

} // namespace operators
} // namespace mos
