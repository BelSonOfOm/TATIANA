#pragma once

// THE GROWTH LAW'S COST SIDE — DOCS/DERIVATION_MDL_GROWTH_LAW.md §2.1, §5.10a, §5.11.
//
// coning.hpp cones the COMPLEX. It decides WHERE a concept goes and proves the
// homology class dies. It carries no sheaf data, so it cannot say WHAT the
// concept is, nor WHETHER it is worth having. This file supplies both.
//
// ============== WHY THE HOLONOMY, AND NOT A NULLSPACE AT k*d ================
//
// Construction 6 sets F(w) = lim D_gamma, the sections of F over the cycle.
// Written directly that is the nullspace of delta^0 restricted to gamma: an
// operator on k*d = 1920 dimensions at k = 5, d = 384.
//
// It is not needed. The restriction maps are EXACTLY orthogonal (HouseholderMap),
// hence invertible, so a section is determined by its value at ONE vertex and
// propagated by maps the store already holds. Going once round the loop,
//
//     x_1 = H x_1,     H = T_k ... T_1     (the HOLONOMY of gamma)
//
// with T_i the transport along the i-th edge. Therefore
//
//     lim D_gamma  =  ker(H - I),   inside the SINGLE stalk F(v_1).
//
// Two consequences beyond the speed, and both are load-bearing in the derivation:
//
//   * k-1 OF THE k LEGS ARE FREE. They are propagated, not described, so the MDL
//     model term is b*d_w*(d_v + k_w + 1), NOT b*d_w*(1 + k*d_v). At k = 5,
//     d = 384 that is a 4.98x overcount removed (derivation §2.1), which moves
//     the recurrence threshold from ~2000 traversals to ~300.
//
//   * d_w = dim H(gamma) -- the concept is exactly as large as the hole it fills
//     (derivation §5.10a). So the whole model term is known BEFORE the decision.
//
// ========== WHY THIS FILE MATERIALISES ONE DENSE d x d MATRIX ==============
//
// householder.hpp marks dense() "FOR TESTS AND ORACLES ONLY", and it is right:
// the representation exists so that 2000 EDGES need not hold 576 KB each. This
// file materialises ONE TRANSIENT holonomy per attachment decision, built by
// applying the maps column-wise so no per-edge dense matrix is ever formed, and
// drops it immediately. That is not the cost the warning is about. The
// alternative -- matrix-free Lanczos for an eigenspace of unknown dimension --
// is more code for a millisecond.
//
// ⚠️ WHAT IS NOT SETTLED, stated here rather than discovered later:
//
//   (1) EXACT SECTIONS ARE MEASURE ZERO. In a learned sheaf ker(H - I) is
//       generically {0} at any strict tolerance: a direction turned by 1e-5
//       radians is not a section. `spectrum` is returned in full so the caller
//       can see the near-fixed directions rather than only the exact ones, and
//       score_direction() is what prices "nearly". Do not read dim() as the
//       whole answer.
//   (2) score_direction() fits sigma_b and sigma_w to the same readings it then
//       codes, so its saving is optimistic by the usual two-parameter amount.
//       That is what `bits_per_real` is meant to charge for, and derivation §6.4
//       has not settled it.

#include <Eigen/Dense>
#include <vector>

#include "mos/core/two_complex.hpp"

namespace mos {
namespace core {

/// @brief F(w) for a cycle, as a subspace of the first vertex's stalk.
struct ConeStalk {
    Eigen::MatrixXd leg;        ///< d x d_w, orthonormal columns. This is p_1.
    Eigen::VectorXd spectrum;   ///< singular values of (H - I), ASCENDING, length d.
    double tol = 0.0;           ///< the threshold that produced `leg`.

    /// @brief d_w. Equals dim H(gamma) -- derivation §5.10a.
    [[nodiscard]] int dim() const noexcept { return static_cast<int>(leg.cols()); }
};

/// @brief The holonomy H of `cycle`, as a dense d x d matrix.
///
/// `cycle` is the vertices in cyclic order; the wrap-around pair closes it. Each
/// consecutive pair must already be an edge with a restriction map. Traversal
/// against an edge's stored orientation applies the transpose, which for an
/// orthogonal map is the inverse exactly, not approximately.
///
/// @throws std::invalid_argument if the cycle is shorter than 3, repeats a
///         vertex, names an unknown vertex, is not a cycle in the complex, or
///         reaches an edge carrying no restriction map. A missing map is a
///         missing measurement, not an identity.
[[nodiscard]] Eigen::MatrixXd cycle_holonomy(const Store& K,
                                             const std::vector<HodgeVertex>& cycle);

/// @brief Construction 6 by the holonomy route: F(w) = ker(H - I).
///
/// @param tol ABSOLUTE, not relative. For orthogonal H the singular values of
///        (H - I) are 2|sin(theta/2)| for the rotation angles theta, so `tol` is
///        read directly as "fixed to within this angle". See caveat (1) above.
[[nodiscard]] ConeStalk cone_stalk(const Store& K,
                                   const std::vector<HodgeVertex>& cycle,
                                   double tol = 1e-9);

/// @brief The remaining k-1 legs, propagated from `leg` by the transports.
///
/// Returns p_1 ... p_k, one d x d_w block per vertex of the cycle, in cycle
/// order. These are DERIVED, never stored -- that is the whole point of §2.1.
[[nodiscard]] std::vector<Eigen::MatrixXd> propagate_legs(
    const Store& K,
    const std::vector<HodgeVertex>& cycle,
    const Eigen::MatrixXd& leg);

/// @brief The k readings of one direction on one traversal (derivation §5.11.2):
///        a_i = <x_i, u_i> / ||u_i||^2, with u_i the `col`-th column of legs[i].
///
/// If the direction is a section and the record respects it, these k numbers are
/// ONE number seen k times. How nearly they are is the entire data term.
[[nodiscard]] Eigen::VectorXd read_direction(const std::vector<Eigen::MatrixXd>& legs,
                                             int col,
                                             const std::vector<Eigen::VectorXd>& x);

/// @brief What one direction of the limit is worth (derivation §5.11.3–5.11.5).
struct DirectionVerdict {
    double rho2_hat = 0.0;   ///< plug-in intraclass correlation of the readings
    double rho2 = 0.0;       ///< unbiased. PURE NOISE READS rho2_hat = 1/k, not 0.
    double delta_c = 0.0;    ///< bits saved per traversal
    double n_required = 0.0; ///< the recurrence threshold; infinity if it never pays

    [[nodiscard]] bool ever_pays() const noexcept { return delta_c > 0.0; }
};

/// @brief Score one direction from its readings.
///
/// @param readings n_traversals x k. Row t is one traversal's k readings.
/// @param model_bits the once-only cost of describing this direction; see
///        model_bits_per_direction().
///
/// delta_c is computed from rho2_hat, NOT from rho2, because rho2_hat is what the
/// coder actually achieves -- and it is still negative for pure noise, so this
/// gives away nothing. rho2 is reported for reading by a human, and it is the one
/// to compare against the reliability floor of derivation §5.11.4.
///
/// @throws std::invalid_argument if k < 2 or there are no traversals.
[[nodiscard]] DirectionVerdict score_direction(const Eigen::MatrixXd& readings,
                                               double model_bits);

/// @brief b * (d_v + k_w + 1) -- derivation §2.2.
///
/// @param bits_per_real b. NOT DEFAULTED, ON PURPOSE. Derivation §6.4 is open,
///        and the standard "1/2 log2 n bits per continuous parameter" answer
///        DEGENERATES at the small n this law lives at: it gives b = 0 at n = 1,
///        so a single traversal always pays, which is exactly the
///        over-generation the growth law exists to prevent. The caller must
///        decide and must be able to say which.
[[nodiscard]] double model_bits_per_direction(int d_v, int k_w, double bits_per_real);

}  // namespace core
}  // namespace mos
