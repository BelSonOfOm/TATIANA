#pragma once

#include "mos/core/operator.hpp"

#include <cstddef>
#include <map>
#include <mutex>
#include <set>
#include <string>
#include <vector>

namespace mos {
namespace core {

/// @brief E7 — the assembly record, written AT COMPOSITION TIME.
///
/// WHY THIS EXISTS, AND WHY IT IS ALWAYS ON
/// -----------------------------------------
/// The logbook's experiment table says of E7: *"record Ext/assembly data AT
/// COMPOSITION TIME — cost: small — blocked by: nothing. **do it now,
/// impossible to recover later**"*, and §5r's fix registry repeats the
/// "impossible to recover later" verdict. It is the only owed item on the whole
/// pre-Phase-2 list that gets STRICTLY WORSE by waiting: every tick the engine
/// runs without it is data that cannot be reconstructed afterwards, because the
/// foliation decision — which operators were judged co-schedulable with which
/// others — exists only for the instant `select_commuting_slice` makes it and is
/// then thrown away. The DAG that remains afterwards does not record it.
///
/// WHAT IT IS FOR (F4 / E3)
/// -------------------------
/// The audit's F4 note: **all** of the book's Part II (Foata, Gröbner, Koszul,
/// Cartier–Foata, capacity κ, Anick, HH¹/HH²) rests on ONE unverified
/// hypothesis — that operators with disjoint node-support COMMUTE. The logbook
/// is blunt that in this engine they very likely do not, since every operator
/// touches shared state (CognitiveState, SQLite, Ω, the mutation history, the
/// coarse stalks). Nobody has computed the independence relation I for the real
/// operator set. **If I is empty, A is the free algebra, μ(z) = 1 − rz, and
/// Part II is counting DAGs.**
///
/// That question is answered by DATA, not argument: run the engine, record
/// every co-scheduling decision the foliation actually made, and read I off the
/// pairs that co-scheduled without incident. This class is the recorder. It
/// does not answer E3; it makes E3 answerable at all.
///
/// DESIGN CONSTRAINTS
/// ------------------
///  * **Always on.** A recorder you have to remember to enable is a recorder
///    that is off during the run you needed. There is no `enable()`.
///  * **Cheap.** One small struct per slice, a few set insertions. The engine
///    already builds these sets to make the decision; we keep them instead of
///    dropping them.
///  * **Thread-safe.** `Operad::run` hands slices to a ThreadPool. Recording
///    happens on the scheduling thread, before the slice is enqueued, but the
///    log is guarded anyway — a data race in the instrument would corrupt the
///    only copy of unrecoverable data.
///  * **Records the DECISION, not just the outcome.** Deferred nodes and the
///    reason they were deferred are the informative half: a pair that never
///    co-scheduled is evidence about I only if you know it was *offered* and
///    refused.
class AssemblyLog {
public:
  /// Why a node did not join the slice it was offered to.
  enum class Deferral {
    SupportOverlap,   ///< shares a vertex with a node already in the slice
    SliceLocked,      ///< a global MUTATION owns the slice
    GlobalNeedsEmpty, ///< this node is a global mutation; slice already non-empty
  };

  /// One operator as the foliation saw it.
  struct Participant {
    std::string name;      ///< operator KIND, e.g. "SearchOp" (CognitiveOperator::name)
    OperatorType type{};   ///< concurrency mode, kept because FIX-11 turned on it
    std::set<int> support; ///< the vertices it claimed; empty means GLOBAL
  };

  /// One foliation round: what was offered, what co-scheduled, what was pushed
  /// to a later slice and why.
  struct SliceRecord {
    std::size_t round{};                    ///< 0-based foliation round within one run
    std::size_t offered{};                  ///< nodes in the ready queue
    std::vector<Participant> co_scheduled;  ///< ran together, in slice order
    std::vector<std::pair<Participant, Deferral>> deferred; ///< and why
    bool slice_locked_by_global_mutation{}; ///< the FIX-11 flag, as it ended up
  };

  /// An unordered pair of operator kinds, canonically ordered.
  using Pair = std::pair<std::string, std::string>;

  /// @brief Record one foliation round. Called by `select_commuting_slice`.
  void record_slice(SliceRecord rec);

  /// @brief Mark the start of a new `Operad::run` (resets the round counter).
  void begin_run();

  [[nodiscard]] std::vector<SliceRecord> slices() const;
  [[nodiscard]] std::size_t run_count() const;

  /// @brief The empirical independence relation, so far.
  ///
  /// Every unordered pair of operator types observed co-scheduled in the same
  /// slice, with a count. **This is a LOWER BOUND on I and must not be read as
  /// I itself:** co-scheduling means the foliation's support rule permitted
  /// them, not that they commute as state transformers. F4's whole point is
  /// that those are different claims — shared state (SQLite, Ω, the mutation
  /// history) can make two disjoint-support operators non-commuting anyway.
  /// Deciding that needs a differential test (run both orders, compare states),
  /// which is E3's job and is deliberately NOT done here.
  [[nodiscard]] std::map<Pair, std::size_t> co_scheduling_counts() const;

  /// @brief Pairs that were offered in the same round but did NOT co-schedule.
  /// The other half of the evidence: a pair absent from
  /// `co_scheduling_counts` might simply never have been offered, and "never
  /// offered" says nothing about independence while "offered and refused" does.
  [[nodiscard]] std::map<Pair, std::size_t> refused_counts() const;

  /// @brief One line per slice, for the telemetry stream.
  [[nodiscard]] std::vector<std::string> format() const;

  /// @brief Drop everything. For tests only — in production the whole point is
  /// that this data is never discarded.
  void clear();

private:
  mutable std::mutex mu_;
  std::vector<SliceRecord> slices_;
  std::size_t runs_{0};
  std::size_t round_{0};
};

/// @brief Human-readable name of an operator type, for the assembly record.
[[nodiscard]] const char *operator_type_name(OperatorType t) noexcept;

/// @brief Human-readable deferral reason.
[[nodiscard]] const char *deferral_name(AssemblyLog::Deferral d) noexcept;

/// @brief The process-wide assembly log.
///
/// A global is the right call here and the reason is E7's own constraint: the
/// recorder must capture EVERY composition, including those in code paths that
/// were written before this file existed and do not thread a log through. A
/// log that only sees the call sites someone remembered to wire is exactly the
/// partial record E7 says is unrecoverable.
[[nodiscard]] AssemblyLog &assembly_log() noexcept;

} // namespace core
} // namespace mos
