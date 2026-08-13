#include "mos/core/cone_stalk.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <set>
#include <stdexcept>
#include <string>

namespace mos {
namespace core {
namespace {

constexpr double kTwoPiE = 2.0 * 3.14159265358979323846 * 2.71828182845904523536;

std::string pair_str(const HodgeVertex& u, const HodgeVertex& v) {
    return "(" + u + ", " + v + ")";
}

/// The transport along the edge from `u` to `v`, as a lookup plus a direction.
/// `forward` is true when (u, v) matches the edge's stored orientation, in which
/// case the stored map applies; otherwise its transpose does, which for an
/// orthogonal map is the inverse EXACTLY.
struct Transport {
    const HouseholderMap* R;
    bool forward;

    [[nodiscard]] Eigen::VectorXd operator()(const Eigen::VectorXd& x) const {
        return forward ? R->apply(x) : R->apply_transpose(x);
    }
};

Transport transport(const Store& K, const HodgeVertex& u, const HodgeVertex& v) {
    const auto [idx, sign] = K.complex.edge_index(u, v);   // throws if not an edge
    const HodgeEdge& e = K.complex.edges()[static_cast<std::size_t>(idx)];
    const auto it = K.restriction.find(e);
    if (it == K.restriction.end()) {
        throw std::invalid_argument(
            "cone_stalk: edge " + pair_str(e.first, e.second) +
            " carries no restriction map. A missing map is a missing measurement, "
            "not an identity.");
    }
    return Transport{&it->second, sign > 0.0};
}

void validate_cycle(const Store& K, const std::vector<HodgeVertex>& cycle) {
    if (cycle.size() < 3) {
        throw std::invalid_argument("cone_stalk: a cycle needs at least 3 vertices, got " +
                                    std::to_string(cycle.size()));
    }
    const std::set<HodgeVertex> distinct(cycle.begin(), cycle.end());
    if (distinct.size() != cycle.size()) {
        throw std::invalid_argument("cone_stalk: the cycle repeats a vertex");
    }
    for (std::size_t i = 0; i < cycle.size(); ++i) {
        (void)transport(K, cycle[i], cycle[(i + 1) % cycle.size()]);
    }
}

}  // namespace

Eigen::MatrixXd cycle_holonomy(const Store& K, const std::vector<HodgeVertex>& cycle) {
    validate_cycle(K, cycle);
    const int d = K.dim();

    // Build H column by column. Applying the transports to the columns of I keeps
    // every intermediate in the matrix-free representation: no per-edge dense map
    // is ever formed, only the single accumulating d x d result.
    Eigen::MatrixXd H = Eigen::MatrixXd::Identity(d, d);
    for (std::size_t i = 0; i < cycle.size(); ++i) {
        const Transport T = transport(K, cycle[i], cycle[(i + 1) % cycle.size()]);
        for (int c = 0; c < d; ++c) H.col(c) = T(H.col(c).eval());
    }
    return H;
}

ConeStalk cone_stalk(const Store& K, const std::vector<HodgeVertex>& cycle, double tol) {
    if (!(tol >= 0.0)) {
        throw std::invalid_argument("cone_stalk: tol must be >= 0");
    }
    const int d = K.dim();
    const Eigen::MatrixXd A = cycle_holonomy(K, cycle) - Eigen::MatrixXd::Identity(d, d);

    Eigen::BDCSVD<Eigen::MatrixXd> svd(A, Eigen::ComputeFullV);
    const Eigen::VectorXd& s = svd.singularValues();

    ConeStalk out;
    out.tol = tol;
    // Ascending, so the near-fixed directions read first. V's columns are ordered
    // by DESCENDING singular value, so the nullspace is the tail of V.
    out.spectrum = s.reverse();

    int kept = 0;
    for (int i = 0; i < s.size(); ++i) {
        if (s(i) <= tol) ++kept;
    }
    // A is d x d, so s has d entries and the last `kept` columns of V span ker A.
    out.leg = svd.matrixV().rightCols(kept);
    return out;
}

std::vector<Eigen::MatrixXd> propagate_legs(const Store& K,
                                            const std::vector<HodgeVertex>& cycle,
                                            const Eigen::MatrixXd& leg) {
    validate_cycle(K, cycle);
    if (leg.rows() != K.dim()) {
        throw std::invalid_argument("propagate_legs: leg has " + std::to_string(leg.rows()) +
                                    " rows, expected d = " + std::to_string(K.dim()));
    }
    std::vector<Eigen::MatrixXd> legs;
    legs.reserve(cycle.size());

    Eigen::MatrixXd cur = leg;
    for (std::size_t i = 0; i < cycle.size(); ++i) {
        legs.push_back(cur);
        const Transport T = transport(K, cycle[i], cycle[(i + 1) % cycle.size()]);
        Eigen::MatrixXd next(cur.rows(), cur.cols());
        for (int c = 0; c < cur.cols(); ++c) next.col(c) = T(cur.col(c).eval());
        cur = std::move(next);
    }
    return legs;
}

Eigen::VectorXd read_direction(const std::vector<Eigen::MatrixXd>& legs,
                               int col,
                               const std::vector<Eigen::VectorXd>& x) {
    if (legs.size() != x.size() || legs.empty()) {
        throw std::invalid_argument("read_direction: one observation per leg is required");
    }
    Eigen::VectorXd a(static_cast<Eigen::Index>(legs.size()));
    for (std::size_t i = 0; i < legs.size(); ++i) {
        if (col < 0 || col >= legs[i].cols()) {
            throw std::invalid_argument("read_direction: column " + std::to_string(col) +
                                        " is out of range for leg " + std::to_string(i));
        }
        const Eigen::VectorXd u = legs[i].col(col);
        const double n2 = u.squaredNorm();
        if (n2 <= 0.0) {
            throw std::invalid_argument("read_direction: leg " + std::to_string(i) +
                                        " has a zero column; it names no direction");
        }
        a(static_cast<Eigen::Index>(i)) = u.dot(x[i]) / n2;
    }
    return a;
}

DirectionVerdict score_direction(const Eigen::MatrixXd& readings, double model_bits) {
    const Eigen::Index n = readings.rows();
    const Eigen::Index k = readings.cols();
    if (n < 1 || k < 2) {
        throw std::invalid_argument(
            "score_direction: need at least one traversal and at least 2 readings; a "
            "single reading cannot disagree with itself");
    }

    const Eigen::VectorXd s_hat = readings.rowwise().mean();       // MLE of the concept's value
    const Eigen::MatrixXd resid = readings.colwise() - s_hat;

    const double mean_s = s_hat.mean();
    const double var_b = (s_hat.array() - mean_s).square().sum() / static_cast<double>(n);
    const double var_w = resid.array().square().sum() / static_cast<double>(n * k);

    DirectionVerdict v;
    if (var_b + var_w <= 0.0) {
        // Every reading identical at every traversal. Nothing varies, so nothing is
        // coded and nothing is saved.
        v.n_required = std::numeric_limits<double>::infinity();
        return v;
    }
    v.rho2_hat = var_b / (var_b + var_w);

    // §5.11.5: the plug-in ICC is inflated by exactly (1 - rho^2)/k, so pure noise
    // reads 1/k -- 0.20 at k = 5, which an uncorrected threshold would find
    // encouraging. Unbias before anyone compares this to the reliability floor.
    const double inv_k = 1.0 / static_cast<double>(k);
    v.rho2 = std::max(0.0, (v.rho2_hat - inv_k) / (1.0 - inv_k));

    // §5.11.3. The +1 inside b_s is what keeps a code length non-negative: the
    // high-rate form goes negative when sigma_b < sigma_w, and then the "saving"
    // diverges to +infinity exactly where the direction explains nothing.
    const double r = std::min(v.rho2_hat, 1.0 - 1e-15);
    const double b_s = 0.5 * std::log2(1.0 + kTwoPiE * r / (1.0 - r));
    v.delta_c = 0.5 * static_cast<double>(k) * std::log2(1.0 / (1.0 - r)) - b_s;

    v.n_required = v.delta_c > 0.0 ? model_bits / v.delta_c
                                   : std::numeric_limits<double>::infinity();
    return v;
}

double model_bits_per_direction(int d_v, int k_w, double bits_per_real) {
    if (d_v <= 0 || k_w < 0) {
        throw std::invalid_argument("model_bits_per_direction: d_v > 0 and k_w >= 0 required");
    }
    if (!(bits_per_real > 0.0)) {
        throw std::invalid_argument(
            "model_bits_per_direction: bits_per_real must be > 0. b = 0 makes the model "
            "free and every one-off traversal pay -- see derivation §6.4.");
    }
    return bits_per_real * (static_cast<double>(d_v) + static_cast<double>(k_w) + 1.0);
}

}  // namespace core
}  // namespace mos
