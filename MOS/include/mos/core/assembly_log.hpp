#pragma once

// E7 AT ENGINE LEVEL — assembly recording, ported from python/assembly_log.py.
//
// WHY THIS IS A PORT AND NOT A BRIDGE. The tick is C++ and the analysis
// (`recurrence`, `promotion_evidence`) is Python. Rather than stand up an IPC
// path, the engine writes the SAME JSONL schema the Python reader already
// consumes. That keeps one format and one set of readers.
//
// THE ONE THING THAT MUST NOT DRIFT: `canonical_signature`. It is the key the
// recurrence analysis groups on, so if C++ and Python disagree about the
// signature of the same composite, every recurrence count is silently wrong
// while every test still passes. `tests/test_assembly_log.cpp` asserts the two
// implementations agree on fixed cases, and `python/check_signature_parity.py`
// asserts it from the other side against these same cases.
//
// RECORD AT ASSEMBLY, CLOSE AT JUDGEMENT. `record()` is called once the DAG is
// built and BEFORE it runs, because that is when `rho_before` is knowable.
// `close()` supplies `rho_after`. An event that never closes is `abandon`ed
// rather than dropped: "we assembled this and never learned the outcome" is
// itself data, per the Python docstring.

#include <cstdint>
#include <map>
#include <optional>
#include <string>
#include <utility>
#include <vector>

namespace mos {
namespace core {

/// @brief One operator occurrence inside a composite. Mirrors
/// `assembly_log.NodeRecord`.
struct NodeRecord {
    std::string op_type;
    std::vector<int> support;  ///< sorted; empty means GLOBAL
    bool read_only = false;

    /// @brief The sort key used by the canonical topological order. Matches
    /// Python's `NodeRecord.key()` tuple ordering exactly: op_type, then
    /// support elementwise, then read_only (false < true, as in Python).
    [[nodiscard]] bool operator<(const NodeRecord& o) const noexcept {
        if (op_type != o.op_type) return op_type < o.op_type;
        if (support != o.support) return support < o.support;
        return read_only < o.read_only;
    }
};

/// @brief One composition, recorded when assembled. Mirrors
/// `assembly_log.AssemblyEvent`.
struct AssemblyEvent {
    std::string signature;
    std::vector<NodeRecord> nodes;
    std::vector<std::pair<int, int>> edges;   ///< (parent_idx, child_idx)
    std::vector<std::vector<int>> slices;     ///< foliation: node indices per slice
    std::uint64_t tick = 0;
    double wall_time = 0.0;
    std::optional<double> rho_before;
    std::optional<double> rho_after;
    std::optional<std::string> verified;      ///< VERIFIED | REFUTED | UNVERIFIABLE

    /// @brief Stored concepts RETRIEVED this tick -- the co-activation event.
    ///
    /// This is the assembly Construction 5 is fitted to, and until it existed
    /// the log contained no assemblies at all. `NodeRecord::support` looks like
    /// it should be this and is not: it is a foliation-scheduling constant
    /// ({0}, {1}, {}) with no concept identity in it.
    ///
    /// Names, not indices, because the concept set GROWS. An index assigned at
    /// tick 10 would mean something different at tick 900; a name does not. The
    /// analysis side builds the index map once, over the whole accumulated log.
    std::vector<std::string> retrieved;

    /// @brief Concepts GROWN this tick (neurogenesis).
    ///
    /// Kept separate from `retrieved` and NOT interchangeable with it: a concept
    /// is grown exactly once, so a co-activation matrix built from this field
    /// has a single firing per column and measures growth order, not
    /// co-activation. Recorded because it is the birth register -- which is
    /// precisely what `cover.alive_mask` needs to stop scoring a concept's
    /// silence before it existed.
    std::vector<std::string> grown;

    bool closed = false;
    std::string note;

    /// @brief null unless BOTH rho values are present. Never defaulted to 0 —
    /// "no measurement" is not "no change".
    [[nodiscard]] std::optional<double> delta_rho() const noexcept {
        if (!rho_before || !rho_after) return std::nullopt;
        return *rho_after - *rho_before;
    }
};

/// @brief A complete, order-independent invariant of a composite's structure.
///
/// Topological sort with deterministic tie-breaking on (op_type, support,
/// read_only), then serialise the nodes AND the dependency edges rewritten in
/// the canonical index space.
///
/// @throws std::invalid_argument if an edge indexes out of range, or if the DAG
///         contains a cycle. A cycle in an operad DAG is a bug worth surfacing,
///         not something to serialise around.
[[nodiscard]] std::string canonical_signature(
    const std::vector<NodeRecord>& nodes,
    const std::vector<std::pair<int, int>>& edges);

/// @brief Append-only recorder. Nothing here rewrites or deletes a past line.
///
/// NOT thread-safe and not multi-process safe: one writer at a time. The engine
/// calls it from `execute_dag` on the orchestrating thread, never from inside a
/// foliation slice.
class AssemblyLog {
public:
    explicit AssemblyLog(std::string path);

    /// @brief Record a composition AT ASSEMBLY TIME. Returns a handle for close().
    /// Nothing is written to disk until close() or abandon().
    int record(std::vector<NodeRecord> nodes,
               std::vector<std::pair<int, int>> edges,
               std::vector<std::vector<int>> slices,
               std::uint64_t tick,
               std::optional<double> rho_before,
               std::string note = "");

    /// @brief Close an open event with its outcome and flush it.
    /// @param verified left empty when nothing actually verified the composite.
    ///        It is NOT inferred from rho: coherence is not correctness
    ///        (Construction 3), so guessing here would fabricate evidence.
    ///        NULL therefore keeps its exact meaning -- "no oracle ran" -- and is
    ///        distinct from the string "UNVERIFIABLE", which means one ran and
    ///        could not decide.
    void close(int handle,
               std::optional<double> rho_after,
               std::optional<std::string> verified = std::nullopt,
               const std::string& extra_note = "");

    /// @brief Attach this tick's co-activation record to an open event.
    ///
    /// Separate from record() because retrieval happens DURING the run, while
    /// record() fires before it. Called once, between run and close.
    void set_activation(int handle,
                        std::vector<std::string> retrieved,
                        std::vector<std::string> grown);

    /// @brief Flush an event whose outcome will never be known.
    void abandon(int handle, const std::string& note = "abandoned");

    /// @brief Number of events recorded but not yet closed or abandoned.
    [[nodiscard]] std::size_t open_count() const noexcept { return open_.size(); }

    [[nodiscard]] const std::string& path() const noexcept { return path_; }

private:
    void flush(const AssemblyEvent& ev);

    std::string path_;
    std::map<int, AssemblyEvent> open_;
    int next_handle_ = 0;
};

}  // namespace core
}  // namespace mos
