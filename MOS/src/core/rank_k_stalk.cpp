#include "mos/core/rank_k_stalk.hpp"

#include <cmath>
#include <stdexcept>

namespace mos {
namespace core {

RankKStalk::RankKStalk(Eigen::VectorXd mu, Eigen::MatrixXd U, double D, double n_eff)
    : mu_(std::move(mu)), U_(std::move(U)), D_(D), n_eff_(n_eff) {
    if (mu_.size() == 0) {
        throw std::invalid_argument("RankKStalk: mu must be non-empty.");
    }
    if (U_.size() != 0 && U_.rows() != mu_.size()) {
        throw std::invalid_argument(
            "RankKStalk: U has " + std::to_string(U_.rows()) + " rows but mu has " +
            std::to_string(mu_.size()) + ".");
    }
    if (U_.size() == 0) U_ = Eigen::MatrixXd::Zero(mu_.size(), 0);
    if (!(D_ > 0.0)) {
        throw std::invalid_argument(
            "RankKStalk: the floor D must be strictly positive (got " +
            std::to_string(D_) + "). A zero floor is INFINITE confidence in every "
            "direction U does not span.");
    }
}

RankKStalk RankKStalk::isotropic(const Eigen::VectorXd& mu, double D, double n_eff) {
    return RankKStalk(mu, Eigen::MatrixXd::Zero(mu.size(), 0), D, n_eff);
}

RankKStalk RankKStalk::from_observations(const std::vector<Eigen::VectorXd>& vectors,
                                         double kappa,
                                         double eps) {
    if (vectors.empty()) {
        throw std::invalid_argument(
            "from_observations: no observations. An organ that grew nothing has no "
            "stalk; returning an isotropic prior would assert a position it never took.");
    }
    const Eigen::Index d = vectors.front().size();
    if (d <= 0) throw std::invalid_argument("from_observations: zero-dimensional observation.");
    for (const auto& v : vectors) {
        if (v.size() != d) {
            throw std::invalid_argument("from_observations: ragged observation dimensions.");
        }
    }

    const double n = static_cast<double>(vectors.size());
    Eigen::VectorXd mu = Eigen::VectorXd::Zero(d);
    for (const auto& v : vectors) mu += v;
    mu /= n;

    // Centred deviations. The scatter has rank <= n-1 < d, which is exactly why
    // the low-rank form is what the data supports rather than a compression.
    Eigen::MatrixXd Xc(d, vectors.size());
    for (std::size_t i = 0; i < vectors.size(); ++i) Xc.col(static_cast<Eigen::Index>(i)) = vectors[i] - mu;

    // Sigma = (S + kappa*Sigma_0)/(n + kappa) + eps I with Sigma_0 = (1/d) I.
    // The isotropic parts collect into the FLOOR, not into U -- folding them in
    // would make k = d and destroy the low-rank economy.
    const double n_eff = n;
    const double floor = stalk_floor(static_cast<int>(d), n_eff, kappa);
    Eigen::MatrixXd U = Xc / std::sqrt(n_eff + kappa);

    // Drop numerically-zero columns so a repeated observation does not inflate k.
    std::vector<Eigen::Index> keep;
    for (Eigen::Index j = 0; j < U.cols(); ++j) {
        if (U.col(j).norm() > 1e-12) keep.push_back(j);
    }
    Eigen::MatrixXd Uk(d, static_cast<Eigen::Index>(keep.size()));
    for (std::size_t j = 0; j < keep.size(); ++j) Uk.col(static_cast<Eigen::Index>(j)) = U.col(keep[j]);

    return RankKStalk(std::move(mu), std::move(Uk), floor, n_eff);
}

double RankKStalk::trace() const {
    return U_.squaredNorm() + static_cast<double>(d()) * D_;
}

double RankKStalk::log_det() const {
    // log det(U U^T + D I) = (d-k) log D + sum_i log(D + sigma_i^2), with sigma_i
    // the singular values of U. Only the k non-trivial directions need the SVD.
    if (k() == 0) return static_cast<double>(d()) * std::log(D_);
    const Eigen::VectorXd sv = U_.jacobiSvd().singularValues();
    double total = static_cast<double>(d() - sv.size()) * std::log(D_);
    for (Eigen::Index i = 0; i < sv.size(); ++i) total += std::log(D_ + sv(i) * sv(i));
    return total;
}

Eigen::VectorXd RankKStalk::covariance_apply(const Eigen::VectorXd& x) const {
    if (x.size() != mu_.size()) {
        throw std::invalid_argument("covariance_apply: dimension mismatch.");
    }
    if (k() == 0) return D_ * x;
    return U_ * (U_.transpose() * x) + D_ * x;
}

Eigen::VectorXd RankKStalk::precision_apply(const Eigen::VectorXd& x) const {
    if (x.size() != mu_.size()) {
        throw std::invalid_argument("precision_apply: dimension mismatch.");
    }
    // Woodbury: (U U^T + D I)^-1 = (1/D)(I - U (D I + U^T U)^-1 U^T).
    // The only inverse taken is k x k.
    if (k() == 0) return x / D_;
    const Eigen::MatrixXd UtU = U_.transpose() * U_;
    const Eigen::MatrixXd M = (D_ * Eigen::MatrixXd::Identity(k(), k()) + UtU);
    const Eigen::VectorXd inner = M.ldlt().solve(U_.transpose() * x);
    return (x - U_ * inner) / D_;
}

Eigen::MatrixXd RankKStalk::dense_covariance() const {
    Eigen::MatrixXd S = D_ * Eigen::MatrixXd::Identity(d(), d());
    if (k() > 0) S += U_ * U_.transpose();
    return S;
}

Eigen::MatrixXd RankKStalk::density_matrix() const {
    return dense_covariance() / trace();
}

RankKStalk RankKStalk::congruence(const HouseholderMap& R) const {
    if (R.dim() != d()) {
        throw std::invalid_argument("congruence: the map's dimension must match the stalk's.");
    }
    // R Sigma R^T = (R U)(R U)^T + D (R R^T) = (R U)(R U)^T + D I.
    // The floor is untouched because R is EXACTLY orthogonal (Phase-2 item 1),
    // so the rank-k form is preserved rather than approximately preserved.
    Eigen::MatrixXd RU(d(), k());
    for (int j = 0; j < k(); ++j) RU.col(j) = R.apply(U_.col(j));
    return RankKStalk(R.apply(mu_), std::move(RU), D_, n_eff_);
}

}  // namespace core
}  // namespace mos
