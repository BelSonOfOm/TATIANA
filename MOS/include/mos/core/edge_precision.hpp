#pragma once

// pi_e DERIVED, ported from python/edge_precision.py (authoritative).
//
// THE TYPE ERROR THIS FIXES (5af). `CoarseComplex::set_use_precision(true)` used
// each edge's COUPLING WEIGHT as pi_e, on the reading "a more-bound coalition is
// trusted more". But the coupling weight is a Hebbian co-activation count and
// pi_e is an INVERSE VARIANCE. They are different quantities with different
// units pointing in different directions: coupling grows with how often two
// organs fired together, precision grows with how little noise their difference
// carries. Substituting one for the other is a type error that happens to
// produce plausible numbers, which is why it survived.
//
// THE DERIVATION. The predictive-coding free energy is
//
//     F = sum_e pi_e ||eps_e||^2,   eps_e = R_u x_u - R_v x_v
//
// With orthogonal restriction maps and isotropic stalk floors D_u, D_v,
//
//     Var(eps_e) = R_u Sigma_u R_u^T + R_v Sigma_v R_v^T = (D_u + D_v) I
//
// and a reported confidence c_e adds a per-component variance s_e, giving
//
//     pi_e = 1 / (D_u + D_v + s_e),     s_e = -ln(c_e) / d
//
// The 1/d keeps the TRACE contribution -ln(c) = O(1), commensurate with the
// semantic scale, exactly as belief.py's Sigma_0 = (1/d)I carries trace 1.

#include <map>
#include <optional>
#include <string>
#include <vector>

#include "mos/core/coarse_complex.hpp"

namespace mos {
namespace core {

/// @brief Below this, a total error variance would mean effectively infinite
/// precision. Must match python/edge_precision.py MIN_TOTAL_VARIANCE.
inline constexpr double MIN_TOTAL_VARIANCE = 1e-12;

/// @brief The per-component variance s_e contributed by a reported confidence.
///
/// Returns 0.0 for an ABSENT confidence: absence of a measurement is not
/// evidence of noise, and inventing one would be the failure mode this project
/// exists to avoid.
///
/// @throws std::invalid_argument for d <= 0, or c outside (0, 1]. A confidence
///         of 0 is not a confidence and one above 1 is a caller bug — neither
///         gets quietly clamped.
[[nodiscard]] double report_variance(std::optional<double> confidence, int d);

/// @brief Build the per-edge precision map pi_e = 1 / (D_u + D_v + s_e).
///
/// @param edges       the bound pairs of the coarse complex.
/// @param stalk_floor D_v per organ — `core::stalk_floor(d, n_eff)`, or
///                    belief.stalk_gaussian(...).eps. Strictly positive.
/// @param d           embedding dimension (384 deployed), for the s_e scaling.
/// @param confidence  optional c_e in (0, 1] per edge, from the Q9 judgement
///                    contract. Missing edges contribute no extra noise.
///
/// @throws std::invalid_argument on a missing or non-positive stalk floor. A
///         missing floor is a MISSING MEASUREMENT, not a floor of 1 — defaulting
///         it would silently manufacture a precision.
[[nodiscard]] std::map<CoarseEdge, double> edge_precision(
    const std::vector<CoarseEdge>& edges,
    const std::map<ModuleId, double>& stalk_floor,
    int d,
    const std::map<CoarseEdge, double>& confidence = {});

/// @brief True when every precision is the same to within rel_tol. An empty or
/// single-edge map is uniform. Used to assert the parity identity: uniform pi
/// must reproduce the pre-5p measure exactly.
[[nodiscard]] bool is_uniform(const std::map<CoarseEdge, double>& pi,
                              double rel_tol = 1e-12);

}  // namespace core
}  // namespace mos
