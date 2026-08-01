#pragma once

// PHASE-2 ITEM 3 — F_MOS (augmented Forman curvature) and the barrier controller.
//
// ============================ F_MOS (Q5, logbook 5ac) ======================
//
//   F_MOS(e) = pi_e^2 * sum_{f > e} 1/tau_f  +  (nu_u + nu_v)
//                                            -  sum_{e' || e} nu_gamma * sqrt(pi_e / pi_e')
//
// with gamma(e,e') the shared vertex. Two things are load-bearing:
//
// (1) THE WEIGHTS ARE Pi AND nu, NOT w(sigma,t). Forman's cell weights are not
//     decorative masses -- they define the inner product in which the
//     combinatorial Laplacian is self-adjoint, which is the only reason a Ricci
//     term exists at all. MOS's Laplacian is L = delta^T Pi delta, so the edge
//     weight IS pi_e. Using the Hebbian coupling would compute the curvature of
//     a DIFFERENT Laplacian than the one the engine prints omega and rho from --
//     a consistent-looking number about the wrong operator.
//
// (2) THE "NOT BOTH" CLAUSE. e' is parallel to e when they share a face OR a
//     coface but NOT BOTH. For edges that means: share a vertex, and lie in no
//     common triangle. The 2m edges closing e's triangles are therefore EXCLUDED
//     from the penalty, which is where the 3 in 4 - deg u - deg v + 3m comes
//     from: 3 = 1 (coface sum) + 2 (the pair removed from the penalty). It is a
//     consequence of the clause, not a tuning knob.
//
// Setting pi = nu = tau = 1 returns 4 - deg u - deg v + 3m exactly, so the
// combinatorial formula is a DERIVED special case, not an imported one.
//
// ==================== The barrier controller (Q6, logbook 5ad) =============
//
// w <- (1 + eps*kappa)*w is forward Euler on wdot = eps*kappa*w. The continuous
// flow is multiplicative, so w(t) = w(0)*exp(eps*int kappa) is strictly positive
// for all finite time: THE EXACT FLOW CAN NEVER SEVER ANYTHING. What severs is
// the discretisation -- if eps*kappa < -1 then (1 + eps*kappa) < 0 and the
// weight flips sign. w_floor was patching a numerical artefact of Euler and was
// misdiagnosed as a plasticity-safety mechanism. It is DELETED here, not tuned.
//
// Positivity alone is not enough: exponential decay still crosses a collapse
// threshold in finite time. Control barrier functions (Ames et al.) give
// forward invariance of C = {h >= 0} iff hdot >= -alpha(h) for a class-K alpha.
// With h(w) = w - theta_safe and alpha(h) = eps*|kappa|*h the 1-D QP is
// closed-form AND exactly integrable, and it coincides with weight-dependent
// plasticity's soft bound (van Rossum; Gutig) -- the neuroscience and the
// control theory are the same object, so we inherit both the invariance
// certificate and the biological precedent.

#include <string>
#include <vector>

#include "mos/core/hodge.hpp"

namespace mos {
namespace core {

/// @brief tau_f: the 2-cochain weight on face f, derived (logbook 5ag).
///
/// tau_f = |f| / sum_{e in f} (1/pi_e) -- the HARMONIC MEAN of the face's edge
/// precisions. The |f| factor is a stated choice, not cosmetic: it takes tau to
/// be the precision of the MEAN circulation per edge rather than of the total,
/// which keeps tau dimensionally comparable to pi (so pi_e^2/tau_f in F_MOS is a
/// pure number) and gives exact day-one degradation -- all pi_e = 1 => tau_f = 1.
/// Without it the derived curvature would silently disagree with the derivation
/// that justified it.
///
/// @throws std::invalid_argument on an empty face or a non-positive precision.
[[nodiscard]] double tau_face(const std::vector<double>& edge_precisions);

/// @brief Per-edge inputs to F_MOS. Absent entries are NOT defaulted.
struct CurvatureWeights {
    std::vector<double> pi;   ///< pi_e per edge, in cx.edges() order. All > 0.
    std::vector<double> nu;   ///< nu_v per vertex, in cx.vertices() order. All > 0.

    /// @brief The unit-weight specialisation: pi = nu = 1 everywhere.
    /// F_MOS then reproduces 4 - deg u - deg v + 3m exactly.
    [[nodiscard]] static CurvatureWeights unit(const Complex2& cx);
};

/// @brief Edges parallel to `edge_i` in Forman's sense: sharing a vertex, and
/// lying in NO common triangle with it ("share a face or a coface, not both").
/// Returns (edge index, shared vertex index) pairs.
[[nodiscard]] std::vector<std::pair<int, int>> parallel_edges(const Complex2& cx, int edge_i);

/// @brief The combinatorial specialisation 4 - deg u - deg v + 3m. Exposed so
/// the general formula can be tested against it rather than against a comment.
[[nodiscard]] double forman_combinatorial(const Complex2& cx, int edge_i);

/// @brief F_MOS(e) for one edge. See the header comment for the formula.
/// @throws std::invalid_argument on a weight-vector size mismatch or a
///         non-positive weight (pi = 0 is an infinitely noisy edge, which is a
///         measurement to state explicitly, not a default to fall into).
[[nodiscard]] double forman_mos(const Complex2& cx, int edge_i,
                                const CurvatureWeights& w);

/// @brief F_MOS for every edge, in cx.edges() order.
[[nodiscard]] std::vector<double> forman_mos_all(const Complex2& cx,
                                                 const CurvatureWeights& w);

// ---------------------------------------------------------------------------

/// @brief The safe operating band for a coupling weight, and the flow step size.
struct BarrierConfig {
    /// @brief Integrator step size. NAMED eps_flow, never eps: the RESOLVE gate's
    /// eps_rho is a THRESHOLD compared against a measurement, this is a STEP SIZE
    /// multiplying a rate. C6-2.
    double eps_flow = 0.05;

    /// @brief Lower barrier. The flow approaches it asymptotically and NEVER
    /// reaches it, which is why it sits strictly above the collapse trigger by
    /// construction -- the earlier w_floor sat exactly AT the collapse point.
    double theta_safe = 1e-3;

    /// @brief Upper barrier. w is a bounded coupling, so the symmetric barrier is
    /// required rather than optional (logbook 5aj).
    double w_max = 1.0;
};

/// @brief One step of the barrier-constrained curvature flow.
///
/// The desired dynamics are wdot = eps_flow * kappa * w. With alpha(h) =
/// eps_flow*|kappa|*h the barrier-constrained flow is exactly integrable in both
/// branches, so this is an EXACT step, not an approximation:
///
///   kappa < 0:  w <- theta_safe + (w - theta_safe) * exp(-eps_flow*|kappa|)
///   kappa > 0:  w <- w_max      - (w_max - w)      * exp(-eps_flow*|kappa|)
///   kappa = 0:  unchanged
///
/// Both branches have a vector field that VANISHES at the boundary, so
/// [theta_safe, w_max] is forward invariant with no clip anywhere. Nothing here
/// can sever an edge, at any step size, for any curvature -- which is the
/// property forward Euler could not offer at eps*kappa < -1.
///
/// @throws std::invalid_argument if the band is empty or w starts outside it.
[[nodiscard]] double barrier_step(double w, double kappa, const BarrierConfig& cfg);

/// @brief The UNCONSTRAINED exact flow w * exp(eps_flow * kappa), for comparison
/// and for callers that genuinely want no barrier. Strictly positive for any
/// step size -- but it still crosses any fixed threshold in finite time, which
/// is precisely why barrier_step exists.
[[nodiscard]] double exponential_step(double w, double kappa, double eps_flow);

/// @brief The forward-Euler step this replaces: w * (1 + eps_flow*kappa).
/// Provided ONLY so the regression test can demonstrate the sign flip at
/// eps_flow*kappa < -1 that motivated the whole construction. Do not ship it.
[[nodiscard]] double euler_step_unsafe(double w, double kappa, double eps_flow);

}  // namespace core
}  // namespace mos
