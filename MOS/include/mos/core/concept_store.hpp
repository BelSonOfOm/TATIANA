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
// TRIANGLES: THE SAME RULE, ONE DIMENSION UP (added 2026-08-03, logbook 5as).
// This file previously said "no triangles ... until something earns the
// triangle", on the stated ground that b1 would move for an unreconstructable
// reason. THE PREMISE WAS BACKWARDS, and that is why the rule changed:
//
//   With no 2-cells delta1 = 0, so the curl subspace is trivial and
//   harmonic = (im delta0)^perp, of dimension b1 = E - V + b0. Leaving
//   triangles out does not zero b1 -- IT MAXIMISES IT. And since `observe`
//   inserts each assembly as a CLIQUE, one assembly of size n contributes
//   b1(K_n) = (n-1)(n-2)/2 cycles on its own: 171 for a 20-concept tick.
//   The growth address was never blocked. It was SWAMPED, by artifacts of
//   inserting cliques and refusing to fill them.
//
// So a 2-simplex is recorded exactly when its three concepts co-fired in ONE
// assembly -- the edge rule, one dimension up. It introduces no new constant,
// and it is the same co-activation signal Construction 5 fits its causes to.
// Three facts make it the right rule rather than merely a cheap one:
//
//   1. The 2-skeleton of a simplex is simply connected, so every
//      WITHIN-assembly cycle dies. No tetrahedra are needed.
//   2. H1 depends only on the 2-skeleton, so b1(filled) = b1(union of the
//      assembly simplices).
//   3. {Delta(A_t)} is a GOOD COVER -- simplices are contractible, and
//      intersect(Delta(A_t)) = Delta(intersect(A_t)) is a simplex or empty --
//      so the nerve lemma applies with its hypotheses verified EXACTLY, not
//      assumed. Hence b1(fine complex) = b1(assembly nerve).
//
// What survives is CROSS-assembly: a hole no single assembly covers. That is a
// real structural gap, and it is what the growth address was always meant to
// name. Verified numerically in `python/validate_triangles.py` (necklaces of
// k filled assemblies return b1 = 1 for every k, as the nerve lemma predicts).
//
// THE COST IS NOT FREE AND IS NOT HIDDEN: see max_assembly_for_triangles.

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
    ///
    /// AND EVERY TRIPLE GETS A TRIANGLE -- the same rule, one dimension up.
    /// See `max_assembly_for_triangles` for why that is not free.
    void observe(const std::vector<std::string>& coactive);

    /// @brief Largest assembly for which triangles are recorded. 0 disables
    ///        triangles entirely and restores the edges-only store.
    ///
    /// WHY A CAP EXISTS AT ALL. Triangles per assembly grow as C(n,3) while
    /// edges grow as C(n,2), so their ratio is (n-2)/3 -- LINEAR in assembly
    /// size, with no n beyond which the count stops mattering. Measured
    /// (`python/validate_triangles.py`), at 1500 ticks: n=20 costs 1.7M
    /// triangles (~82-164 MB), n=30 costs 6.1M (~292-585 MB), n=50 costs 29.4M
    /// (~1.4-2.8 GB) on a 5.9 GB machine. 30 is the largest that fits a tenth
    /// of the machine, so that is the default -- derived from the budget, not
    /// picked.
    ///
    /// AND THE CAP IS MANDATORY, not prudent: `KnowledgeBase::
    /// get_relevant_concepts` is a THRESHOLD SCAN WITH NO LIMIT over the whole
    /// store, so |A| is bounded by the relevance threshold and the corpus size
    /// rather than by any constant. At |A| = 1000 a single tick would want
    /// 166 million triangles.
    void set_max_assembly_for_triangles(std::size_t n) noexcept;
    [[nodiscard]] std::size_t max_assembly_for_triangles() const noexcept {
        return max_assembly_for_triangles_;
    }

    /// @brief Assemblies whose triangles were SKIPPED because they exceeded the
    ///        cap. MUST be read before interpreting b1.
    ///
    /// A skipped assembly keeps its edges but not its 2-cells, so its
    /// (n-1)(n-2)/2 within-assembly cycles survive as HARMONIC MASS that looks
    /// exactly like a structural hole. That is the artifact this whole change
    /// exists to remove, so a nonzero count here means b1 is contaminated by
    /// precisely the thing being fixed. Exposed rather than logged because a
    /// silent cap would move b1 -- the number the harmonic part exists to
    /// expose -- for a reason nobody could later reconstruct.
    [[nodiscard]] std::size_t skipped_wide_assemblies() const noexcept {
        return skipped_wide_;
    }

    /// @brief Concepts in the widest assembly seen, capped or not. Telemetry
    ///        for choosing the cap against a real corpus rather than a guess.
    [[nodiscard]] std::size_t widest_assembly_seen() const noexcept {
        return widest_seen_;
    }

    [[nodiscard]] std::size_t num_triangles() const noexcept {
        return triangles_.size();
    }

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
    std::set<HodgeTriangle> triangles_;            ///< sorted triple, so (a,b,c) is one key
    std::size_t max_assembly_for_triangles_ = 30;  ///< derived; see the setter's docs
    std::size_t skipped_wide_ = 0;
    std::size_t widest_seen_ = 0;
    std::map<std::string, int> weight_;            ///< reserved: per-concept counts
    std::optional<Store> store_;
    bool dirty_ = true;
};

}  // namespace core
}  // namespace mos
