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
};

} // namespace core
} // namespace mos
