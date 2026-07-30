#pragma once

#include <set>

namespace mos {
namespace core {

class CognitiveState;

/// @brief Defines the threat level/concurrency mode of an operator.
enum class OperatorType {
    READ_ONLY, // Acquires std::shared_lock
    MUTATION   // Acquires std::unique_lock
};

/// @brief Abstract base class for any operation that transforms the cognitive state.
class CognitiveOperator {
public:
    virtual ~CognitiveOperator() = default;

    /// @brief Executes the operator on the given state.
    /// @param state The cognitive state to mutate or read.
    virtual bool apply(CognitiveState& state) = 0;

    /// @brief Returns the type of the operator for concurrency lock resolution.
    virtual OperatorType get_type() const noexcept = 0;

    /// @brief Returns the topological support (the set of vertices this operator touches).
    /// Used by the Operad engine to calculate disjoint commuting slices (Foliation).
    virtual std::set<int> get_support() const = 0;

    /// @brief Stable identity of this operator KIND, e.g. "SearchOp".
    ///
    /// E7 needs this and `get_type()` cannot supply it: OperatorType is a
    /// concurrency mode (READ_ONLY / MUTATION), so keying the assembly record on
    /// it would collapse every operator into one of two buckets and answer
    /// nothing. F4's open question is about the independence relation on the
    /// REAL operator set — {SearchOp, ComputeOp, ReasonOp, ContextOp, VerifyOp}
    /// — which requires distinguishing them by kind.
    ///
    /// Defaulted rather than pure so that adding E7 does not break every
    /// existing subclass, including ones in tests. "<unnamed>" is deliberately
    /// ugly: an unnamed operator showing up in the assembly record is a missing
    /// override, and should look like one rather than blending in.
    [[nodiscard]] virtual const char *name() const noexcept { return "<unnamed>"; }
};

} // namespace core
} // namespace mos
