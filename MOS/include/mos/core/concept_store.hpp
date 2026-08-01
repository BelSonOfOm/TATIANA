#pragma once

// PHASE 3, STAGE 3a: THE BRIDGE.
//
// The tick's operators act on CognitiveState, which holds a
// topology::SimplicialComplex plus a Sheaf of SemanticEmbeddings. Every Phase-2
// item is built on hodge::Complex2 with HodgeVertex/HodgeEdge, and
// cognitive_state.hpp contained zero references to Complex2, Store or Working.
// Two parallel representations of "the complex", with nothing joining them --
// which is why nine finished items could sit unit-tested and unreachable.
//
// The join turns out to be cheap, because HodgeVertex IS std::string and
// concepts already have names. No index map, no renumbering, and no identity
// that drifts as the store grows: a concept's name means the same thing at tick
// 900 as at tick 10, which an integer index assigned on first sight would not.
//
// WHAT THE EDGES ARE, STATED RATHER THAN ASSUMED.
// An edge joins two concepts RETRIEVED IN THE SAME TICK. This is the fine-level
// mirror of CoarseComplex::co_activate, which already binds organs that
// cooperate in one DAG, and it is the same co-activation relation Construction 5
// fits its latent causes to -- so the store's wiring and the cover model are
// built from one signal, not two loosely-related ones.
//
// WHAT IS DELIBERATELY NOT HERE: no triangles. Complex2 supports them and b1
// needs them, but nothing in the engine yet decides when three concepts form a
// 2-simplex rather than three edges, and inserting them on a guess would move
// b1 -- the number the harmonic part exists to expose -- for a reason no one
// could later reconstruct. Edges only, until something earns the triangle.

#include <map>
#include <optional>
#include <set>
#include <string>
#include <vector>

#include <Eigen/Dense>

#include "mos/core/householder.hpp"
#include "mos/core/two_complex.hpp"

namespace mos {
namespace core {

/// @brief An orthogonal map carrying `from`'s direction onto `to`'s, as an EVEN
/// number of Householder reflections.
///
/// WHY EVEN, AND WHY THIS IS NOT A STYLE CHOICE. One reflection suffices to
/// align two unit vectors: with w = (a - b)/||a - b||, H_w a = b exactly. But
/// det(H_w) = -1, so a one-reflection map lies in the OTHER component of O(d)
/// from the identity the store starts at, and `crystallise` correctly REFUSES to
/// interpolate across that gap -- no continuous path joins them, so any blend
/// would be a jump, not a transfer. The learned map would then never reach the
/// store and Q(t) would stay at zero while every test passed.
///
/// So the alignment is built as a product of TWO reflections, det = +1:
///
///     R = H_p H_w,   w = (a - b)/||a - b||,   p orthogonal to span{a, b}
///
/// H_w carries a to b, and H_p fixes b because p is perpendicular to it, so
/// R a = b while the parity matches the identity. The construction degenerates
/// gracefully: when a and b already point the same way there is nothing to
/// learn and the identity is returned.
///
/// @param from,to Non-zero vectors of equal dimension. Only DIRECTIONS matter --
///        an orthogonal map cannot change length, so magnitudes are ignored
///        rather than silently discarded.
/// @throws std::invalid_argument on dimension mismatch or a vector too small to
///         normalise. A zero vector has no direction to align.
[[nodiscard]] HouseholderMap align_map(const Eigen::VectorXd& from,
                                       const Eigen::VectorXd& to);

/// @brief K over concepts: the growing co-activation graph plus its sheaf.
///
/// Complex2 is immutable once built, so the graph is accumulated here and the
/// Store is rebuilt when it changes. Restriction and coupling survive a rebuild
/// because they are keyed by (name, name) rather than by position.
class ConceptStore {
public:
    /// @param d embedding dimension. Fixed for the store's life: a restriction
    ///        map cannot span two dimensions, and padding one to fit is the kind
    ///        of silent reshape CognitiveState already refuses for geometry.
    explicit ConceptStore(int d);

    /// @brief Record one tick's co-activation. Adds any unseen concept as a
    /// vertex and joins every pair with an edge, incrementing its weight.
    ///
    /// ALL PAIRS, not a chain: co-activation is symmetric and unordered, and a
    /// spanning path would impose an arbitrary order on a set. k is the number
    /// of concepts one query retrieves -- single digits -- so k(k-1)/2 is small.
    /// A tick retrieving fewer than two concepts creates no edge, which is
    /// correct: one concept alone co-activates with nothing.
    void observe(const std::vector<std::string>& coactive);

    /// @brief The store, rebuilt if `observe` changed the graph since last call.
    [[nodiscard]] Store& store();

    /// @brief Vertices present, in insertion order.
    [[nodiscard]] const std::vector<std::string>& concepts() const noexcept {
        return order_;
    }

    [[nodiscard]] bool contains(const std::string& name) const {
        return weight_.count(name) > 0 || vertices_.count(name) > 0;
    }

    [[nodiscard]] std::size_t num_concepts() const noexcept { return vertices_.size(); }
    [[nodiscard]] std::size_t num_edges() const noexcept { return coactivation_.size(); }
    [[nodiscard]] int dim() const noexcept { return d_; }

    /// @brief How many ticks co-activated this pair. The raw evidence behind an
    /// edge, kept so the coupling weight is derived rather than remembered.
    [[nodiscard]] int coactivation_count(const std::string& u,
                                         const std::string& v) const;

private:
    int d_;
    std::set<std::string> vertices_;
    std::vector<std::string> order_;               ///< insertion order, for stability
    std::map<HodgeEdge, int> coactivation_;        ///< canonical (min, max) key
    std::map<std::string, int> weight_;            ///< reserved: per-concept counts
    std::optional<Store> store_;
    bool dirty_ = true;
};

}  // namespace core
}  // namespace mos
