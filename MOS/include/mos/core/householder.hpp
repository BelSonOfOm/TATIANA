#pragma once

// PHASE-2 ITEM 1 — restriction maps as products of Householder reflections.
//
// WHY (5s budget finding 1). A dense restriction map is 384^2 floats = 576 KB,
// two per edge => 2.3 GB at 2000 edges on a 5.9 GB machine. Dead on arrival.
// A product of m reflections stores m vectors instead of a d x d matrix:
//
//     R = H_1 H_2 ... H_m,    H_i = I - 2 v_i v_i^T   (v_i unit)
//
// Storage drops by d/m = 96x at d=384, m=4; application drops from O(d^2) to
// O(m d). (5s quotes "6 KB at m=4", which is the float32 figure -- Eigen here
// is double, so it is 12 KB against 1.15 MB. The 96x RATIO is exact either way,
// since it is d/m and independent of element size.)
//
// TWO PROPERTIES WE GET FOR FREE, AND BOTH ARE LOAD-BEARING.
//  * Each H_i is symmetric AND orthogonal (H^T = H, H^2 = I), so R is EXACTLY
//    orthogonal by construction -- not orthogonal-to-tolerance, and never in
//    need of re-orthogonalisation after an update. Audit F2's ||R|| <= 1
//    hypothesis therefore holds structurally rather than being asserted.
//  * Orthogonal congruence Sigma -> R Sigma R^T preserves the trace, so on
//    density matrices R is a unitary CPTP channel (5t Q1): level 1 of the
//    potency ladder, "same content, different basis" -- reversible and lossless.
//
// R^T IS FREE: since each H_i is symmetric,
//     R^T = (H_1 ... H_m)^T = H_m ... H_1,
// i.e. the same factors applied in the opposite order. No storage, no transpose.

#include <Eigen/Dense>
#include <vector>

namespace mos {
namespace core {

/// @brief An exactly-orthogonal d x d map stored as m Householder vectors.
class HouseholderMap {
public:
    /// @brief R = H_1 ... H_m from the given vectors, each normalised to unit
    /// length on construction. An empty list is the identity (m = 0).
    /// @throws std::invalid_argument if the vectors disagree in dimension, if
    ///         d <= 0, or if any vector has norm too small to normalise --
    ///         a zero Householder vector does not define a reflection, and
    ///         silently treating it as identity would hide a caller bug.
    HouseholderMap(int d, std::vector<Eigen::VectorXd> vectors);

    /// @brief The identity map, stored in zero bytes of reflection data.
    [[nodiscard]] static HouseholderMap identity(int d);

    /// @brief A reproducible pseudo-random orthogonal map, for tests and for
    /// seeding a learnable map before anything has been learned.
    [[nodiscard]] static HouseholderMap random(int d, int m, unsigned seed);

    /// @brief R x, in O(m d). Applies H_m first: R x = H_1(H_2(...(H_m x))).
    [[nodiscard]] Eigen::VectorXd apply(const Eigen::VectorXd& x) const;

    /// @brief R^T x, in O(m d). Same factors, opposite order.
    [[nodiscard]] Eigen::VectorXd apply_transpose(const Eigen::VectorXd& x) const;

    /// @brief The dense d x d matrix. FOR TESTS AND ORACLES ONLY -- materialising
    /// this is precisely the 576 KB/map cost the representation exists to avoid.
    [[nodiscard]] Eigen::MatrixXd dense() const;

    [[nodiscard]] int dim() const noexcept { return d_; }
    [[nodiscard]] int m() const noexcept { return static_cast<int>(v_.size()); }

    /// @brief Bytes of reflection data held (excluding object overhead).
    [[nodiscard]] std::size_t storage_bytes() const noexcept {
        return v_.size() * static_cast<std::size_t>(d_) * sizeof(double);
    }

    [[nodiscard]] const std::vector<Eigen::VectorXd>& vectors() const noexcept {
        return v_;
    }

private:
    int d_;
    std::vector<Eigen::VectorXd> v_;  ///< unit vectors, normalised at construction
};

/// @brief Default number of reflections per map (Q4). Four is enough to reach a
/// useful subgroup of O(d) while keeping a map at 12 KB rather than 1.15 MB.
inline constexpr int HOUSEHOLDER_M_DEFAULT = 4;

}  // namespace core
}  // namespace mos
