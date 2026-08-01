#pragma once

// PHASE-2 ITEMS 5 & 6 — the K/W store-cache split, and gamma(nu) crystallisation.
//
// These are one object, not two: gamma(nu) IS the coefficient in the write-back,
// so splitting them would mean shipping an adjunction with no way to close the
// loop.
//
// ============================== THE TWO COMPLEXES ==========================
//
//   K = (C_K, F_K, w)   the crystallised store. CARRIES NO SECTION -- it is
//                       structure, not a thought.
//   W = (C_W, F_W, s_W) the working complex: a DOWNWARD-CLOSED subcomplex of K
//                       that does carry a state.
//
// They communicate by a genuine adjunction (Curry ch.4-6), not by the .tex's
// unverified L -| M:  i_! -| i^* -| i_*  for the poset inclusion i : W -> K.
//
//   i^* = INSTANTIATE   (store -> cache)
//   i_! = EXTENSION BY ZERO = write back ONLY what was touched
//
// Theorem: i^* i_! = id. The load / work / store round trip is FAITHFUL, and it
// is asserted in the tests rather than cited.
//
// i_! and NOT i_*: the cache must assert nothing about cells it never touched.
// i_* would extend by the terminal object, i.e. it would make a claim about
// untouched cells; i_! extends by zero, which is the sheaf-theoretic form of the
// bottom invariant used everywhere else in MOS.
//
// ADAPTATION IS THE SHEAF CEASING TO BE CONSTANT. Store maps say how concepts
// relate IN GENERAL; cache maps say how they relate IN THIS PROBLEM. The
// session's learning is exactly  dR = R^W - i^* R^K.
//
// ========================= gamma(nu) CRYSTALLISATION =======================
//
//   R^K_e  <-  Pi_O(d)( R^K_e + gamma(nu) * (R^W_e - R^K_e) )
//
// with gamma = gamma0 (Verified) / eps*gamma0 (Unverifiable) / 0 (Refuted).
// gamma0 << 1 is slow transfer, which IS the anti-catastrophic-interference
// property -- not a tuning knob to make learning "feel right".
//
// s_W IS NEVER WRITTEN BACK. Content and wiring persist; the episode does not.
//
// ⚠️ A CLOSURE PROBLEM THE FORMULA HIDES, STATED HERE BECAUSE IT CHANGED THE
// IMPLEMENTATION. The m=4 Householder family is NOT closed under this update: a
// convex combination of two products-of-4-reflections is not orthogonal, and
// projecting it back with an SVD yields a general orthogonal matrix needing up
// to d-1 reflections, not 4. So the literal formula cannot be applied in the
// representation Phase-2 item 1 ships. Two retractions onto O(d) are provided:
//
//   * crystallise_dense   -- the literal Pi_O(d) via SVD. Correct, O(d^3), and
//                            it does NOT stay in the m=4 family.
//   * crystallise         -- interpolation in the REFLECTION VECTORS (slerp on
//                            the unit sphere), which is exactly orthogonal by
//                            construction, stays at m=4, and costs O(md).
//
// They agree at gamma=0 and gamma=1 and differ on the path between. That is a
// real modelling choice, not an approximation of one by the other, and it is
// asserted in the tests so nobody mistakes them for the same map.

#include <map>
#include <optional>
#include <string>
#include <vector>

#include <Eigen/Dense>

#include "mos/core/householder.hpp"
#include "mos/core/hodge.hpp"

namespace mos {
namespace core {

/// @brief The promotion verdict that sets the transfer rate.
enum class Verdict { Verified, Unverifiable, Refuted };

[[nodiscard]] const char* to_string(Verdict v) noexcept;

/// @brief gamma(nu): how much of the session's learning crystallises.
///
/// Verified -> gamma0; Unverifiable -> eps*gamma0; Refuted -> 0 EXACTLY.
/// Zero is not "very small": a refuted session must leave the store bit-identical,
/// or repeated refutations would still drift it.
///
/// @throws std::invalid_argument unless 0 < gamma0 <= 1 and 0 <= eps <= 1.
///         gamma0 > 1 would overshoot past the cache map, which is not a slower
///         or faster transfer but a different one.
[[nodiscard]] double gamma_nu(Verdict verdict, double gamma0 = 0.05, double eps = 0.1);

// ---------------------------------------------------------------------------

/// @brief K: the crystallised store. Structure and wiring, no section.
struct Store {
    Complex2 complex;
    std::map<HodgeEdge, HouseholderMap> restriction;   ///< R^K_e, exactly orthogonal
    std::map<HodgeEdge, double> coupling;              ///< w(sigma,t)

    Store(Complex2 cx, int d);

    /// @brief Q(t) = (1/|E|) sum_e ||R^K_e - I||_F^2.
    ///
    /// Q = 0 is the CONSTANT sheaf: every concept means the same thing in every
    /// context, i.e. nothing has been learned about the wiring. Departure from
    /// constancy is the learning signal, so this is the metric that says whether
    /// crystallisation is doing anything at all.
    [[nodiscard]] double Q() const;

    [[nodiscard]] int dim() const noexcept { return d_; }

private:
    int d_;
};

/// @brief W: a downward-closed subcomplex of K, carrying a section.
struct Working {
    Complex2 complex;
    std::map<HodgeEdge, HouseholderMap> restriction;    ///< R^W_e
    std::map<HodgeVertex, Eigen::VectorXd> section;     ///< s_W -- NEVER written back
    std::vector<HodgeEdge> touched;                     ///< the support of i_!

    /// @brief Mark an edge as touched, so i_! writes it back. An edge that is
    /// never touched is never crystallised, however long the session ran.
    void touch(const HodgeEdge& e);
    [[nodiscard]] bool was_touched(const HodgeEdge& e) const;
};

/// @brief i^*: instantiate a working complex from the store.
///
/// @param vertices the retrieved vertex set -- typically the output of Phase-2
///        item 4's `instantiate`. Downward closure is applied here: an edge or
///        triangle is included only when ALL its vertices are present.
/// @throws std::invalid_argument if a vertex is not in the store.
[[nodiscard]] Working i_star(const Store& store, const std::vector<HodgeVertex>& vertices);

/// @brief i_!: write back ONLY the touched edges, crystallising by gamma.
///
/// Extension by zero, not by the terminal object: untouched edges are left
/// bit-identical, because the cache asserts nothing about cells it never saw.
/// s_W is not written back at all.
///
/// @returns the number of edges actually modified.
int i_shriek(Store& store, const Working& working, double gamma);

/// @brief dR = R^W - i^* R^K, the session's learning, as a per-edge Frobenius
/// norm. Zero on every edge means the session learned nothing about the wiring.
[[nodiscard]] std::map<HodgeEdge, double> delta_R(const Store& store, const Working& working);

// ---------------------------------------------------------------------------

/// @brief The literal Pi_O(d)( A + gamma(B - A) ) by SVD. O(d^3).
/// Does NOT preserve the m=4 Householder family -- see the header note.
[[nodiscard]] Eigen::MatrixXd crystallise_dense(const Eigen::MatrixXd& A,
                                                const Eigen::MatrixXd& B,
                                                double gamma);

/// @brief Crystallisation in the REFLECTION VECTORS: slerp each Householder
/// vector of A toward B's by gamma. Exactly orthogonal by construction (a
/// product of reflections always is), stays at m = max(m_A, m_B), and costs
/// O(md) with no d x d matrix ever formed.
///
/// @throws std::invalid_argument on a dimension mismatch or gamma outside [0,1].
[[nodiscard]] HouseholderMap crystallise(const HouseholderMap& A,
                                         const HouseholderMap& B,
                                         double gamma);

}  // namespace core
}  // namespace mos
