#pragma once

// PHASE-2 ITEM 8 — rank-k SPD stalks in C++ (Q1).
//
// The stalk stops being a POINT in R^d and becomes a GAUSSIAN over R^d:
//
//     Sigma = U U^T + D I,     U in R^{d x k},   k << d
//
// stored as (mu, U, D). Never as a d x d matrix: at d = 384 that is 1.15 MB per
// stalk, where (U, D) at k = 8 is 24 KB.
//
// ====================== WHY THE LOW-RANK FORM IS THE RIGHT ONE =============
//
// It is not a compression of something else -- it is what the data supports. A
// concept grown from n observations has a scatter matrix of rank <= n, and
// n << d always (5 concepts at d = 384 gives k = 5, not 384). Storing d x d
// would be storing mostly floor.
//
// Three things come for free and all three are load-bearing:
//
//   * WOODBURY. Sigma^-1 = (1/D)(I - U M U^T) with M = (D I + U^T U)^-1, a k x k
//     inverse. So precision-weighted operations cost O(dk + k^3), never O(d^3),
//     and Sigma^-1 is never formed either.
//
//   * CLOSURE UNDER ORTHOGONAL CONGRUENCE. R Sigma R^T = (RU)(RU)^T + D I,
//     because R (D I) R^T = D I exactly. So congruence is just U -> RU: the
//     rank-k-plus-floor FORM IS PRESERVED, and with a Householder R it costs
//     O(m d k) with no d x d matrix anywhere. This is what makes 5t's reading of
//     restriction maps as unitary CPTP channels operational rather than
//     analogical -- trace and spectrum are preserved exactly.
//
//   * THE TRACE SPLITS OFF. Sigma = (Tr Sigma) * (Sigma / Tr Sigma), so the
//     density matrix rho = Sigma/Tr Sigma is available for the quantum reading
//     while the engine keeps storing Sigma. The Bures-Wasserstein distance
//     already in knowledge_base.cpp, restricted to trace 1, IS the Bures metric
//     on density matrices.
//
// ⚠️ THE FLOOR IS NOT DECORATION. FIX-13 established D = O(1/d) so the
// covariance carries trace O(1). A rank-0 stalk (one observation, U empty) then
// has Sigma = D I with SMALL D, i.e. HIGH confidence from a single sighting --
// which is backwards, and is exactly what the shrinkage prior in
// `from_observations` exists to prevent. D is never a free parameter here.

#include <Eigen/Dense>
#include <vector>

#include "mos/core/householder.hpp"
#include "mos/core/semantic_skill.hpp"

namespace mos {
namespace core {

/// @brief N(mu, U U^T + D I). Low-rank by construction; d is never materialised.
class RankKStalk {
public:
    /// @param mu mean, length d.
    /// @param U  factor, d x k. k = 0 is allowed and means Sigma = D I.
    /// @param D  isotropic floor, strictly positive.
    /// @param n_eff effective sample size behind this stalk (provenance, not maths).
    /// @throws std::invalid_argument on a shape mismatch or D <= 0. A zero floor
    ///         is infinite confidence in the directions U does not span.
    RankKStalk(Eigen::VectorXd mu, Eigen::MatrixXd U, double D, double n_eff = 1.0);

    /// @brief An isotropic stalk with no learned directions: Sigma = D I.
    [[nodiscard]] static RankKStalk isotropic(const Eigen::VectorXd& mu, double D,
                                              double n_eff = 1.0);

    /// @brief Build from observations with the shrinkage prior, porting
    /// belief.stalk_gaussian: Sigma = (S + kappa*Sigma_0)/(n_eff + kappa) + eps I
    /// with Sigma_0 = (1/d) I, so the floor is
    /// `stalk_floor(d, n_eff, kappa)` = eps + kappa/(d(n_eff+kappa)).
    ///
    /// The floor is deliberately NOT folded into U: doing so would make k = d and
    /// destroy the entire low-rank economy.
    ///
    /// @throws std::invalid_argument if `vectors` is empty or ragged.
    [[nodiscard]] static RankKStalk from_observations(
        const std::vector<Eigen::VectorXd>& vectors,
        double kappa = 1.0,
        double eps = EPS_FLOOR);

    [[nodiscard]] int d() const noexcept { return static_cast<int>(mu_.size()); }
    [[nodiscard]] int k() const noexcept { return static_cast<int>(U_.cols()); }
    [[nodiscard]] const Eigen::VectorXd& mu() const noexcept { return mu_; }
    [[nodiscard]] const Eigen::MatrixXd& U() const noexcept { return U_; }
    [[nodiscard]] double D() const noexcept { return D_; }
    [[nodiscard]] double n_eff() const noexcept { return n_eff_; }

    /// @brief Tr(Sigma) = ||U||_F^2 + d*D.
    [[nodiscard]] double trace() const;

    /// @brief log det(U U^T + D I) = (d-k) log D + sum_i log(D + sigma_i^2).
    [[nodiscard]] double log_det() const;

    /// @brief Sigma^-1 x by Woodbury, in O(dk + k^3). Sigma^-1 is never formed.
    [[nodiscard]] Eigen::VectorXd precision_apply(const Eigen::VectorXd& x) const;

    /// @brief Sigma x, in O(dk). Sigma is never formed.
    [[nodiscard]] Eigen::VectorXd covariance_apply(const Eigen::VectorXd& x) const;

    /// @brief The dense Sigma. FOR TESTS AND ORACLES ONLY -- 1.15 MB at d=384.
    [[nodiscard]] Eigen::MatrixXd dense_covariance() const;

    /// @brief The density matrix rho = Sigma / Tr(Sigma), trace 1. Dense; theory
    /// side only. The engine stores Sigma and gets the trace for free.
    [[nodiscard]] Eigen::MatrixXd density_matrix() const;

    /// @brief R Sigma R^T with R orthogonal, i.e. U -> R U and mu -> R mu.
    /// EXACTLY preserves the rank-k form, the trace and the spectrum, so this is
    /// a unitary CPTP channel and not an approximation of one. O(m d k).
    [[nodiscard]] RankKStalk congruence(const HouseholderMap& R) const;

    /// @brief Bytes of stalk data held.
    [[nodiscard]] std::size_t storage_bytes() const noexcept {
        return (static_cast<std::size_t>(mu_.size()) +
                static_cast<std::size_t>(U_.size())) * sizeof(double) + sizeof(double);
    }

private:
    Eigen::VectorXd mu_;
    Eigen::MatrixXd U_;
    double D_;
    double n_eff_;
};

}  // namespace core
}  // namespace mos
