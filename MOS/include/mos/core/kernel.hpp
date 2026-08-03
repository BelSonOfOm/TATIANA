#pragma once

#include "mos/core/assembly_log.hpp"
#include "mos/core/coarse_complex.hpp"
#include "mos/core/cognitive_state.hpp"
#include "mos/core/concept_store.hpp"
#include "mos/core/operad.hpp"
#include "mos/core/reflection.hpp"
#include "mos/core/thread_pool.hpp"
#include "mos/translation/knowledge_base.hpp"
#include "mos/translation/llm_interface.hpp"
#include <memory>
#include <functional>
#include <cstdint>
#include <optional>
#include <string>

namespace mos {
namespace core {

/// @brief Configuration for the OS Kernel.
struct KernelConfig {
    unsigned int num_threads = 0; // 0 triggers auto-detect
    unsigned int fallback_threads = 4;
    float compute_dt = 0.05f;
    float compute_lambda = 2.0f;
    double conflict_threshold = 100.0;

    /// @brief eps_rho: the discord THRESHOLD for the RESOLVE/EXPLORE gate,
    /// `rho > eps_rho => RESOLVE`.
    ///
    /// Because rho is dimensionless and bounded in [0,1], this is a portable
    /// number rather than one that drifts with embedding scale or graph size.
    /// Calibrated empirically on real 384-d embeddings: agreement ~0.00,
    /// related-but-distinct ~0.06, off-topic ~0.14. Hence 0.10 sits between
    /// "different facets of the same problem" and "genuinely incoherent".
    ///
    /// NAMED eps_rho (C6-2). MOS's other epsilon is eps_flow, the STEP SIZE in
    /// the curvature flow `w <- w*exp(eps_flow*kappa)` (5ad) — not yet in the
    /// engine. One is compared against a measurement, the other multiplies a
    /// rate; nothing but a Greek letter is shared. Renamed BEFORE the flow
    /// lands, so there is no name left for it to collide with.
    ///
    /// `CriticalityMonitor::eps_rho()` is the auto-calibrated replacement for
    /// this constant; this remains the cold-start value.
    double eps_rho = 0.10;

    /// @brief gamma0: how much of a VERIFIED session's learning crystallises.
    double gamma0 = 0.05;

    /// @brief eps: the UNVERIFIABLE discount, so gamma = eps*gamma0.
    double gamma_eps = 0.1;

    /// @brief What gamma to use when NO oracle ran at all.
    ///
    /// A DECISION, NOT A DERIVATION -- flagged here rather than buried.
    /// gamma_nu is defined on three verdicts, and "no VerifyOp was in the DAG"
    /// is a fourth state it says nothing about. Most ticks are in that state,
    /// so the choice matters more than it looks:
    ///
    ///   true  (default) -- treat it as UNVERIFIABLE, gamma = eps*gamma0.
    ///       Epistemically these agree: in both cases there is no external
    ///       grounding, and the store crystallises slowly rather than not at
    ///       all. This is what makes the loop able to learn during ordinary
    ///       operation.
    ///   false -- treat it as gamma = 0, so ONLY externally checked sessions
    ///       ever move the store. Safer and much stricter; with VerifyOp rare,
    ///       it means K stays at the constant sheaf almost always.
    ///
    /// E7 records the two cases DIFFERENTLY regardless of this flag: NULL for
    /// "no oracle ran", the string "UNVERIFIABLE" for "one ran and could not
    /// decide". The distinction is never lost in the data, only in gamma.
    ///
    /// ⚠️ UPDATED: the `true` branch is NO LONGER a collapse onto Unverifiable.
    /// It now calls `gamma_no_verdict`, which DERIVES the rate from the verdicts
    /// actually observed (see below). The flag keeps its original meaning as the
    /// hard opt-out -- `false` still means gamma = 0, only checked sessions move
    /// the store -- but `true` is a measurement rather than a decision.
    bool crystallise_unverified = true;

    /// @brief Prior strength for `gamma_no_verdict`, in observations.
    ///
    /// THE ONE KNOB THE DERIVATION INTRODUCES, stated rather than buried. It
    /// deleted the hand-set gamma-for-no-oracle and replaced it with "how many
    /// real verdicts before the data outvotes the prior". This is the same
    /// object as Construction 5's membership kappa and should be set
    /// consistently with it.
    ///
    /// Default 8: a power of two, so day-one degradation is bit-exact, and
    /// modest enough that a first session of real verdicts already moves it.
    double gamma_kappa = 8.0;

    /// @brief The prior verdict distribution for `gamma_no_verdict`.
    ///
    /// Default (V=0, U=1) reproduces the OLD constant eps*gamma0 exactly at
    /// n = 0, so the previous hand-set decision becomes the starting condition
    /// rather than a permanent one. Remaining mass is prior_refuted, which
    /// contributes 0 and is therefore implicit.
    double gamma_prior_verified = 0.0;
    double gamma_prior_unverifiable = 1.0;

    /// @brief Where E7 appends assembly events. Empty disables recording.
    ///
    /// CWD-relative by default, matching the `mos_brain_ipc.db` convention in
    /// main.cpp. Because `communicator.py` spawns the engine WITHOUT setting a
    /// cwd, the child inherits the caller's directory — so relying on that
    /// default would make the log land somewhere that depends on where the user
    /// happened to be standing. main.cpp therefore honours the
    /// `MOS_ASSEMBLY_LOG` environment variable, and `communicator.py` sets it to
    /// `assembly_log.DEFAULT_PATH`, so writer and reader agree by construction
    /// rather than by coincidence.
    std::string assembly_log_path = "assembly_events.jsonl";
};

/// @brief The two-mode controller driven by discord over K.
enum class CognitiveMode {
    EXPLORE, ///< internally coherent: free to build, abstract, search outward
    RESOLVE, ///< discord above threshold: only reconcile, do not expand
    UNKNOWN  ///< discord undefined (no bound organs, or no geometry) - do NOT
             ///< guess a mode from a measurement that does not exist
};

[[nodiscard]] const char* to_string(CognitiveMode m) noexcept;

/// @brief The Orchestration Layer of the Mathematical Operating System.
/// Routes the cognitive state through Operadic DAGs based on its conflict score.
class OSKernel {
public:
    /// @brief Initialize the Operating System Kernel.
    /// @param initial_state The starting Cognitive State.
    /// @param config Configuration for the kernel.
    explicit OSKernel(CognitiveState& initial_state, const KernelConfig& config = KernelConfig());

    /// @brief Set the Reflection Engine for state distillation.
    void set_reflection_engine(std::shared_ptr<ReflectionEngine> reflection_engine);

    /// @brief Set the Knowledge Base for primitives to use.
    void set_knowledge_base(std::shared_ptr<translation::KnowledgeBase> kb);

    /// @brief Set the Language Kernel for primitives to use.
    void set_llm(std::shared_ptr<translation::LanguageKernel> llm);

    /// @brief Execute a serialized Operad DAG (FlatBuffers binary).
    /// @param buffer Pointer to the binary FlatBuffers payload.
    /// @param size Size of the payload.
    /// @return True if successful and valid, false if malformed or empty.
    bool execute_dag(const uint8_t* buffer, size_t size);

    /// @brief Runs a single tick (loop) of the OS Kernel (Legacy or periodic maintenance).
    bool tick();

    /// @brief Get the current cognitive state.
    [[nodiscard]] CognitiveState& get_state() noexcept;

    /// @brief The coarse complex K of operator-organs.
    /// Each OpType present in a DAG is an organ; its stalk is that operator's
    /// payload geometry (embedded locally in Python). Operators adjacent in the
    /// DAG co-activate, so cooperating organs bind. rho over K therefore measures
    /// whether the parts of a single reasoning act are semantically coherent.
    [[nodiscard]] CoarseComplex& get_coarse_complex() noexcept { return coarse_; }
    [[nodiscard]] const CoarseComplex& get_coarse_complex() const noexcept {
        return coarse_;
    }

    /// @brief Discord measured over K after the most recent execute_dag().
    [[nodiscard]] const CoherenceReport& last_coherence() const noexcept {
        return last_coherence_;
    }

    /// @brief The mode selected by the most recent coherence measurement.
    /// UNKNOWN when rho is undefined — the controller refuses to invent a mode
    /// from a measurement that does not exist.
    [[nodiscard]] CognitiveMode current_mode() const noexcept { return mode_; }

    /// @brief Set a halt condition for the kernel.
    void set_halt_condition(std::function<bool(const CognitiveState&)> condition);

    /// @brief How many composites this kernel has executed. Also the `tick`
    /// field of every E7 record, so it is the join key between the assembly log
    /// and anything else logged per tick.
    [[nodiscard]] std::uint64_t tick_count() const noexcept { return tick_count_; }

    /// @brief The E7 recorder, or nullptr when `assembly_log_path` is empty.
    [[nodiscard]] AssemblyLog* assembly_log() noexcept { return assembly_log_.get(); }

    /// @brief K over concepts: the growing co-activation store the tick
    /// crystallises into. Empty until the first tick that retrieves anything.
    [[nodiscard]] const ConceptStore* concept_store() const noexcept {
        return concept_store_ ? &*concept_store_ : nullptr;
    }

    /// @brief Q(t) = mean ||R^K_e - I||_F^2 over the concept store.
    ///
    /// THE ACCEPTANCE TEST FOR THE WHOLE CONSOLIDATION LOOP. Q = 0 is the
    /// constant sheaf -- every concept means the same thing in every context,
    /// i.e. nothing has been learned about the wiring. Q leaving zero is the
    /// first evidence the engine has ever produced that it consolidates.
    /// nullopt when no store exists yet, which is not the same as Q = 0.
    [[nodiscard]] std::optional<double> store_Q() const;

    /// @brief Edges crystallised by the most recent tick's i_!.
    [[nodiscard]] int last_crystallised() const noexcept { return last_crystallised_; }

    /// @brief nu for the most recent tick, or nullopt when NO check ran.
    ///
    /// This is gamma_nu's input, and it is the reason the consolidation loop
    /// could not previously close: with no verdict there is no gamma, so
    /// i_shriek is never called and Q(t) stays at zero.
    [[nodiscard]] std::optional<Verdict> last_verdict() const noexcept {
        return last_verdict_;
    }

    /// @brief Verdicts observed so far, seeded from the E7 log at construction
    ///        and incremented live. The input to `gamma_no_verdict`.
    ///
    /// Seeded rather than started empty because the estimator is meant to
    /// ACCUMULATE: resetting to the prior on every process start would make
    /// "learns what an unchecked tick is worth" true only within one session.
    [[nodiscard]] const VerdictCounts& verdict_counts() const noexcept {
        return verdict_counts_;
    }

    /// @brief gamma the NEXT unchecked tick would use. Exposed for telemetry:
    ///        this number moving is what "the prior is being outvoted" looks
    ///        like, and it is otherwise invisible inside one tick's log line.
    [[nodiscard]] double gamma_for_unchecked() const;

private:
    CognitiveState& state_;
    std::shared_ptr<ReflectionEngine> reflection_engine_;
    std::shared_ptr<translation::KnowledgeBase> kb_;
    std::shared_ptr<translation::LanguageKernel> llm_;
    std::function<bool(const CognitiveState&)> halt_condition_;
    std::shared_ptr<ThreadPool> thread_pool_;
    KernelConfig config_;
    CoarseComplex coarse_;
    CoherenceReport last_coherence_;
    CognitiveMode mode_{CognitiveMode::UNKNOWN};
    std::unique_ptr<AssemblyLog> assembly_log_;
    std::uint64_t tick_count_ = 0;
    std::optional<Verdict> last_verdict_;
    VerdictCounts verdict_counts_;

    // Created lazily: the store's dimension is fixed for its life and is only
    // knowable once a concept with geometry has actually been retrieved.
    std::optional<ConceptStore> concept_store_;
    int last_crystallised_ = 0;
};

} // namespace core
} // namespace mos
