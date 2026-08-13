#pragma once

#include <optional>
#include <set>
#include <utility>

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

    // ------------------------------------------------------------- P1 --
    //
    // THE SUPPORT THE PLANNER NAMED, resolved to ids on the Python side.
    //
    // Before P1 the `support` field of the FlatBuffer was parsed by nobody:
    // `OperatorFactory::create` never read it, and every primitive's
    // `get_support()` returned a HARD-CODED CONSTANT -- {} for SearchOp and
    // RespondOp, {0} for ComputeOp/VerifyOp/ContextOp, {1} for ReasonOp. Those
    // constants carry no concept identity (cognitive_state.hpp says so
    // outright); they exist only to make the foliation serialise mutations.
    //
    // So the support field crossed the adjunction boundary and was DISCARDED,
    // and a Python-side fix alone would have changed nothing observable. This
    // member is the other half: the resolved ids are stored here and returned
    // by `get_support()`, so a DAG that names disjoint concept sets can finally
    // foliate into more than one slice.
    //
    // THE ID SPACE is `distilled_theorems.id` in the KnowledgeBase -- see
    // `python/concept_resolver.py` for why that table and not ConceptStore
    // insertion order.
    //
    // nullopt is NOT the same as an empty set, and the difference is load
    // bearing. Empty means "the planner named concepts and none of them
    // resolved", which reads as a global mutation -- the conservative answer.
    // nullopt means "nobody ever set a support", which is how every operator
    // built outside a DAG arrives, and those keep their legacy constant so this
    // change stays confined to the boundary it is about.

    /// @brief Scope this operator to the concepts the planner named.
    /// @param support Resolved vertex ids. May be empty: "named, none resolved"
    ///        is a real answer and is not the same as never having been asked.
    void set_support(std::set<int> support) {
        explicit_support_ = std::move(support);
    }

    /// @brief Whether a DAG ever scoped this operator.
    [[nodiscard]] bool has_explicit_support() const noexcept {
        return explicit_support_.has_value();
    }

protected:
    /// @brief The resolved support, or nullopt when this operator was never
    /// scoped. Read by the primitives' `get_support()`.
    ///
    /// NOT read by EdgeContractionOp / EdgeExpansionOp / ExpansionOp: their
    /// supports are `topology::VertexID`s over the simplicial complex, which is
    /// a DIFFERENT id space from the concept ids resolved here. They are never
    /// constructed from a DAG, so the two spaces never meet -- but they would
    /// silently alias if those operators started honouring this member.
    std::optional<std::set<int>> explicit_support_;
};

} // namespace core
} // namespace mos
