#include "mos/core/householder.hpp"

#include <random>
#include <stdexcept>
#include <string>

namespace mos {
namespace core {

namespace {
/// Below this a vector does not define a reflection direction. Chosen well above
/// the double round-off floor so a near-degenerate vector is REPORTED rather
/// than silently normalised into noise.
constexpr double kMinReflectionNorm = 1e-12;
}  // namespace

HouseholderMap::HouseholderMap(int d, std::vector<Eigen::VectorXd> vectors)
    : d_(d) {
    if (d <= 0) {
        throw std::invalid_argument("HouseholderMap: dimension must be positive, got " +
                                    std::to_string(d));
    }
    v_.reserve(vectors.size());
    for (std::size_t i = 0; i < vectors.size(); ++i) {
        if (vectors[i].size() != d) {
            throw std::invalid_argument(
                "HouseholderMap: reflection vector " + std::to_string(i) + " has dimension " +
                std::to_string(vectors[i].size()) + ", expected " + std::to_string(d));
        }
        const double n = vectors[i].norm();
        if (n < kMinReflectionNorm) {
            throw std::invalid_argument(
                "HouseholderMap: reflection vector " + std::to_string(i) +
                " has norm " + std::to_string(n) +
                ", which does not define a reflection. Treating it as the identity "
                "would hide a caller bug; pass an empty list for the identity.");
        }
        v_.push_back(vectors[i] / n);
    }
}

HouseholderMap HouseholderMap::identity(int d) {
    return HouseholderMap(d, {});
}

HouseholderMap HouseholderMap::random(int d, int m, unsigned seed) {
    std::mt19937 gen(seed);
    std::normal_distribution<double> normal(0.0, 1.0);
    std::vector<Eigen::VectorXd> vs;
    vs.reserve(static_cast<std::size_t>(std::max(0, m)));
    for (int i = 0; i < m; ++i) {
        Eigen::VectorXd v(d);
        // Redraw rather than accept a degenerate direction. With a Gaussian in
        // d >= 1 dimensions this effectively never loops, but "effectively
        // never" is not "never" and the constructor would throw.
        do {
            for (int j = 0; j < d; ++j) v(j) = normal(gen);
        } while (v.norm() < kMinReflectionNorm);
        vs.push_back(std::move(v));
    }
    return HouseholderMap(d, std::move(vs));
}

Eigen::VectorXd HouseholderMap::apply(const Eigen::VectorXd& x) const {
    if (x.size() != d_) {
        throw std::invalid_argument("HouseholderMap::apply: vector has dimension " +
                                    std::to_string(x.size()) + ", expected " +
                                    std::to_string(d_));
    }
    // R = H_1 H_2 ... H_m, so H_m acts on x FIRST.
    Eigen::VectorXd y = x;
    for (auto it = v_.rbegin(); it != v_.rend(); ++it) {
        y.noalias() -= 2.0 * it->dot(y) * (*it);
    }
    return y;
}

Eigen::VectorXd HouseholderMap::apply_transpose(const Eigen::VectorXd& x) const {
    if (x.size() != d_) {
        throw std::invalid_argument("HouseholderMap::apply_transpose: vector has dimension " +
                                    std::to_string(x.size()) + ", expected " +
                                    std::to_string(d_));
    }
    // R^T = H_m ... H_1 because every H_i is symmetric: the same factors in the
    // opposite order. No transpose is ever formed.
    Eigen::VectorXd y = x;
    for (const auto& v : v_) {
        y.noalias() -= 2.0 * v.dot(y) * v;
    }
    return y;
}

Eigen::MatrixXd HouseholderMap::dense() const {
    Eigen::MatrixXd R(d_, d_);
    Eigen::VectorXd e = Eigen::VectorXd::Zero(d_);
    for (int j = 0; j < d_; ++j) {
        e.setZero();
        e(j) = 1.0;
        R.col(j) = apply(e);
    }
    return R;
}

}  // namespace core
}  // namespace mos
