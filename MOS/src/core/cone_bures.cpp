#include "mos/core/cone_bures.hpp"

#include <algorithm>
#include <cmath>
#include <sstream>
#include <stdexcept>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace mos {
namespace core {

namespace {

/// Percentile with numpy's 'linear' interpolation, so the C++ and Python
/// monitors report the same p50/p95 on the same data. Sorting a copy is fine:
/// this runs once per report, not per observation.
double percentile_linear(std::vector<double> v, double q) {
  if (v.empty()) return std::nan("");
  std::sort(v.begin(), v.end());
  const double pos = (q / 100.0) * static_cast<double>(v.size() - 1);
  const std::size_t lo = static_cast<std::size_t>(std::floor(pos));
  const std::size_t hi = static_cast<std::size_t>(std::ceil(pos));
  if (lo == hi) return v[lo];
  const double frac = pos - static_cast<double>(lo);
  return v[lo] * (1.0 - frac) + v[hi] * frac;
}

/// eps + ||u^T U||^2 -- the spread of one stalk along the unit direction u.
double dir_var(const Eigen::VectorXd &u, const Eigen::MatrixXd &U, double eps) {
  double v = eps;
  if (U.size() != 0 && U.cols() > 0) {
    const Eigen::VectorXd p = U.transpose() * u;   // (k,)
    v += p.squaredNorm();
  }
  return v;
}

}  // namespace

// --------------------------------------------------------------------------
// Bures-Wasserstein, rank-k vs rank-k
// --------------------------------------------------------------------------

double bures_w2_sq_general(const Eigen::VectorXd &mu0, const Eigen::MatrixXd &U0,
                           double eps0, const Eigen::VectorXd &mu1,
                           const Eigen::MatrixXd &U1, double eps1) {
  const Eigen::Index d = mu0.size();
  if (mu1.size() != d) {
    throw std::invalid_argument(
        "bures_w2_sq_general: mean dimensions disagree (" +
        std::to_string(d) + " vs " + std::to_string(mu1.size()) +
        "). Refusing to pad or truncate.");
  }
  if (!(eps0 > 0.0) || !(eps1 > 0.0)) {
    throw std::invalid_argument(
        "bures_w2_sq_general: the isotropic floors must be > 0; a zero floor "
        "makes the covariance singular and the Bures square root undefined.");
  }

  const double mean_term = (mu0 - mu1).squaredNorm();
  const double dd = static_cast<double>(d);

  const bool has0 = (U0.size() != 0 && U0.cols() > 0);
  const bool has1 = (U1.size() != 0 && U1.cols() > 0);

  const double tr0 = (has0 ? U0.squaredNorm() : 0.0) + dd * eps0;
  const double tr1 = (has1 ? U1.squaredNorm() : 0.0) + dd * eps1;

  if (!has0 && !has1) {
    // Both isotropic: the cross term is exactly d*sqrt(eps0*eps1).
    const double cross = dd * std::sqrt(eps0 * eps1);
    return std::max(mean_term + tr0 + tr1 - 2.0 * cross, 0.0);
  }

  // Orthonormal basis B of W = span(U0) + span(U1).
  Eigen::MatrixXd M(d, (has0 ? U0.cols() : 0) + (has1 ? U1.cols() : 0));
  Eigen::Index c = 0;
  if (has0) { M.middleCols(c, U0.cols()) = U0; c += U0.cols(); }
  if (has1) { M.middleCols(c, U1.cols()) = U1; }

  Eigen::HouseholderQR<Eigen::MatrixXd> qr(M);
  Eigen::MatrixXd Q = qr.householderQ() * Eigen::MatrixXd::Identity(d, M.cols());

  // Drop numerically null directions, matching cone_bures.py's `keep` mask.
  std::vector<Eigen::Index> keep;
  const Eigen::MatrixXd QtM = Q.transpose() * M;
  for (Eigen::Index j = 0; j < Q.cols(); ++j) {
    if (QtM.row(j).norm() > 1e-12) keep.push_back(j);
  }
  Eigen::MatrixXd B(d, static_cast<Eigen::Index>(keep.size()));
  for (std::size_t j = 0; j < keep.size(); ++j) B.col(static_cast<Eigen::Index>(j)) = Q.col(keep[j]);
  const Eigen::Index p = B.cols();

  if (p == 0) {
    const double cross = dd * std::sqrt(eps0 * eps1);
    return std::max(mean_term + tr0 + tr1 - 2.0 * cross, 0.0);
  }

  // Sigma restricted to W, in the B basis.
  Eigen::MatrixXd S0 = eps0 * Eigen::MatrixXd::Identity(p, p);
  if (has0) { const Eigen::MatrixXd A0 = U0.transpose() * B; S0 += A0.transpose() * A0; }
  Eigen::MatrixXd S1 = eps1 * Eigen::MatrixXd::Identity(p, p);
  if (has1) { const Eigen::MatrixXd A1 = U1.transpose() * B; S1 += A1.transpose() * A1; }

  // Sigma0^{1/2} on W.
  Eigen::SelfAdjointEigenSolver<Eigen::MatrixXd> es0(S0);
  Eigen::VectorXd w0 = es0.eigenvalues().cwiseMax(0.0);
  const Eigen::MatrixXd S0h =
      es0.eigenvectors() * w0.cwiseSqrt().asDiagonal() * es0.eigenvectors().transpose();

  Eigen::SelfAdjointEigenSolver<Eigen::MatrixXd> esm(S0h * S1 * S0h);
  const Eigen::VectorXd wm = esm.eigenvalues().cwiseMax(0.0);

  const double cross =
      wm.cwiseSqrt().sum() + (dd - static_cast<double>(p)) * std::sqrt(eps0 * eps1);

  return std::max(mean_term + tr0 + tr1 - 2.0 * cross, 0.0);
}

// --------------------------------------------------------------------------
// ConeBures
// --------------------------------------------------------------------------

ConeBures::ConeBures(double delta) : delta_(delta) {
  if (!(delta > 0.0) || !std::isfinite(delta)) {
    throw std::invalid_argument(
        "ConeBures: delta must be finite and > 0 (it is a length scale), got " +
        std::to_string(delta));
  }
}

double ConeBures::base_angle(double d_bw) const noexcept {
  return std::min(d_bw / (2.0 * delta_), M_PI / 2.0);
}

double ConeBures::distance_sq(const Eigen::VectorXd &mu0, const Eigen::MatrixXd &U0,
                              double eps0, const Eigen::VectorXd &mu1,
                              const Eigen::MatrixXd &U1, double eps1, double w0,
                              double w1) const {
  if (w0 < 0.0 || w1 < 0.0) {
    throw std::invalid_argument("ConeBures: masses must be >= 0");
  }
  const double d_bw = std::sqrt(bures_w2_sq_general(mu0, U0, eps0, mu1, U1, eps1));
  const double theta = base_angle(d_bw);
  return std::max(w0 + w1 - 2.0 * std::sqrt(w0 * w1) * std::cos(theta), 0.0);
}

bool ConeBures::is_same_concept(const Eigen::VectorXd &mu0, const Eigen::MatrixXd &U0,
                                double eps0, const Eigen::VectorXd &mu1,
                                const Eigen::MatrixXd &U1, double eps1) const {
  const double d_bw = std::sqrt(bures_w2_sq_general(mu0, U0, eps0, mu1, U1, eps1));
  return d_bw < M_PI * delta_;
}

double ConeBures::sigma_dir_sq(const Eigen::VectorXd &mu0, const Eigen::MatrixXd &U0,
                               double eps0, const Eigen::VectorXd &mu1,
                               const Eigen::MatrixXd &U1, double eps1) const {
  const Eigen::VectorXd dmu = mu0 - mu1;
  const double nd = dmu.norm();
  if (!(nd > 0.0)) {
    throw std::invalid_argument(
        "sigma_dir is undefined for coincident means: there is no separation "
        "direction to project onto. Refusing to pick one.");
  }
  const Eigen::VectorXd u = dmu / nd;
  return 0.5 * (dir_var(u, U0, eps0) + dir_var(u, U1, eps1));
}

double ConeBures::regime_ratio(const Eigen::VectorXd &mu0, const Eigen::MatrixXd &U0,
                               double eps0, const Eigen::VectorXd &mu1,
                               const Eigen::MatrixXd &U1, double eps1) const {
  return std::sqrt(sigma_dir_sq(mu0, U0, eps0, mu1, U1, eps1)) / delta_;
}

double ConeBures::implied_gap(const Eigen::VectorXd &mu0, const Eigen::MatrixXd &U0,
                              double eps0, const Eigen::VectorXd &mu1,
                              const Eigen::MatrixXd &U1, double eps1) const {
  const double r = regime_ratio(mu0, U0, eps0, mu1, U1, eps1);
  return 1.0 + r * r;
}

// --------------------------------------------------------------------------
// RegimeMonitor
// --------------------------------------------------------------------------

std::string RegimeReport::report() const {
  if (status == "empty") return "[regime] no observations";
  std::ostringstream os;
  os.setf(std::ios::fixed);
  os.precision(4);
  os << "[regime] n=" << n << " sigma_dir/delta mean=" << mean << " p50=" << p50
     << " p95=" << p95 << " worst=" << worst
     << " | implied D^2/HK^2=" << mean_implied_gap;
  os.precision(1);
  os << " | " << frac_above_warn * 100.0 << "% >= " << REGIME_WARN << ", "
     << frac_above_chance * 100.0 << "% >= " << REGIME_CHANCE << " => ";
  std::string up = status;
  for (auto &ch : up) ch = static_cast<char>(std::toupper(ch));
  os << up;
  return os.str();
}

RegimeMonitor::RegimeMonitor(std::size_t window) : window_(window) {
  if (window == 0) throw std::invalid_argument("RegimeMonitor: window must be > 0");
}

void RegimeMonitor::observe_ratio(double ratio) {
  if (!std::isfinite(ratio) || ratio < 0.0) {
    throw std::invalid_argument(
        "sigma_dir/delta must be finite and >= 0, got " + std::to_string(ratio));
  }
  ratios_.push_back(ratio);
  while (ratios_.size() > window_) ratios_.pop_front();
}

std::optional<double> RegimeMonitor::observe(const ConeBures &metric,
                                             const Eigen::VectorXd &mu0,
                                             const Eigen::MatrixXd &U0, double eps0,
                                             const Eigen::VectorXd &mu1,
                                             const Eigen::MatrixXd &U1, double eps1) {
  try {
    const double r = metric.regime_ratio(mu0, U0, eps0, mu1, U1, eps1);
    observe_ratio(r);
    return r;
  } catch (const std::invalid_argument &) {
    return std::nullopt;   // coincident means: not evidence either way
  }
}

RegimeReport RegimeMonitor::report() const {
  RegimeReport out;
  if (ratios_.empty()) {
    const double nan = std::nan("");
    out = {0, nan, nan, nan, nan, nan, nan, nan, "empty"};
    return out;
  }
  const std::vector<double> v(ratios_.begin(), ratios_.end());
  const double n = static_cast<double>(v.size());

  double sum = 0.0, gap = 0.0, worst = 0.0;
  std::size_t above_warn = 0, above_chance = 0;
  for (double r : v) {
    sum += r;
    gap += 1.0 + r * r;
    worst = std::max(worst, r);
    if (r >= REGIME_WARN) ++above_warn;
    if (r >= REGIME_CHANCE) ++above_chance;
  }

  out.n = v.size();
  out.mean = sum / n;
  out.p50 = percentile_linear(v, 50.0);
  out.p95 = percentile_linear(v, 95.0);
  out.worst = worst;
  out.mean_implied_gap = gap / n;
  out.frac_above_warn = static_cast<double>(above_warn) / n;
  out.frac_above_chance = static_cast<double>(above_chance) / n;

  // Fractions, not the mean and not a percentile -- see the class docstring.
  if (out.frac_above_chance >= RegimeMonitor::kBadFraction) out.status = "chance";
  else if (out.frac_above_warn >= RegimeMonitor::kBadFraction) out.status = "degrading";
  else out.status = "ok";
  return out;
}

} // namespace core
} // namespace mos
