#pragma once

#include <Eigen/Dense>
#include <cstddef>
#include <deque>
#include <optional>
#include <string>
#include <vector>

namespace mos {
namespace core {

/// @brief Phase-2 item 9: the CONE-BURES metric in the engine.
///
/// C++ port of `python/cone_bures.py`, which stays AUTHORITATIVE -- the parity
/// test compares this against numbers generated there, the same discipline
/// `coherence.py` holds over `CoarseComplex`.
///
/// WHY THIS EXISTS (logbook 5y, 5z)
/// ---------------------------------
/// The merge question needs a distance that interpolates between MOVING mass
/// (transport) and DESTROYING-and-RECREATING it, governed by a length scale
///
///     delta = the distance beyond which two concepts stop being "one thing
///             that moved" and become "two different things".
///
/// E15 asked whether Wasserstein-Fisher-Rao has a Bures-style closed form
/// between Gaussians. Answer: NO, structurally -- HK's cone cost is not
/// quadratic, so the Gaussian family is not preserved. 5z's move was to stop
/// attacking the cost and attack WHAT IS BEING TRANSPORTED: build the cone over
/// (Gaussian space, Bures-Wasserstein) rather than over R^d, using the Hebbian
/// weight as mass. For stalks g = (mu, Sigma, w):
///
///     D_delta(g0,g1)^2 = w0 + w1
///                        - 2 sqrt(w0 w1) cos( min( d_BW/(2 delta), pi/2 ) )
///
/// WHAT IT IS AND IS NOT -- stated, not buried
/// --------------------------------------------
/// IS: a genuine metric (20k randomised triangle-inequality trials in the
///     Python self-test, zero violations), with a length scale, hard
///     saturation, exact day-one degradation to weighted Bures as
///     delta -> infinity, and a cost of one Bures evaluation plus a cosine.
///
/// IS NOT: the true Hellinger-Kantorovich distance between Gaussian measures.
///     Restricting the competitor class raises an infimum, so D >= HK_true --
///     an UPPER BOUND. It is HK-TYPE, not HK, and calling it "WFR between
///     Gaussians" would be false. It is also NOT NOVEL (V4): weighted
///     Wasserstein-Bures / conic formulations are prior art and must be cited,
///     not claimed.
///
/// ⚠️ ITS ACCURACY IS CONDITIONAL, WHICH IS WHY RegimeMonitor SHIPS WITH IT.
/// 5z's agreement with true HK (under 1% in value, ~87% on the merge decision)
/// holds only because MOS's stalks are concentrated along the separation
/// direction, at a measured sigma_dir/delta ~ 0.09. 5z's own closing line is
/// "sigma_dir/delta must be MONITORED, NOT ASSUMED". See RegimeMonitor.
class ConeBures {
public:
  /// @param delta The concept-identity length scale. Must be > 0.
  /// @throws std::invalid_argument if delta <= 0.
  explicit ConeBures(double delta);

  [[nodiscard]] double delta() const noexcept { return delta_; }

  /// @brief theta = min(d_BW/(2 delta), pi/2). The CAPPED base metric.
  [[nodiscard]] double base_angle(double d_bw) const noexcept;

  /// @brief D_delta^2 for stalks with masses w0, w1.
  [[nodiscard]] double distance_sq(const Eigen::VectorXd &mu0,
                                   const Eigen::MatrixXd &U0, double eps0,
                                   const Eigen::VectorXd &mu1,
                                   const Eigen::MatrixXd &U1, double eps1,
                                   double w0 = 1.0, double w1 = 1.0) const;

  /// @brief THE MERGE PREDICATE, and the reason delta is worth having.
  ///
  /// True iff d_BW < pi*delta, i.e. iff the cosine has not saturated. Beyond
  /// that cutoff transport is abandoned entirely and creating-then-destroying
  /// is cheaper than moving, so the two stalks are "different things". This is
  /// a STRUCTURAL statement about the geometry, not a tuned threshold on a
  /// distance -- which is the whole argument for the construction (5z).
  [[nodiscard]] bool is_same_concept(const Eigen::VectorXd &mu0,
                                     const Eigen::MatrixXd &U0, double eps0,
                                     const Eigen::VectorXd &mu1,
                                     const Eigen::MatrixXd &U1,
                                     double eps1) const;

  // --- V6: the regime this metric's accuracy is conditional on -------------

  /// @brief sigma_dir^2 = u^T Sigma u along u = (mu0-mu1)/||mu0-mu1||, averaged
  /// over the pair. THE governing spread (V1c).
  ///
  /// NOT the d-averaged variance: that aggregates over directions the transport
  /// problem never sees, and reading the regime off it is the documented V1c
  /// error (it was 142x off on an orthogonal spread).
  ///
  /// @throws std::invalid_argument if the means coincide -- there is then no
  ///         separation direction, and inventing one fabricates the number V6
  ///         exists to watch.
  [[nodiscard]] double sigma_dir_sq(const Eigen::VectorXd &mu0,
                                    const Eigen::MatrixXd &U0, double eps0,
                                    const Eigen::VectorXd &mu1,
                                    const Eigen::MatrixXd &U1,
                                    double eps1) const;

  /// @brief sigma_dir/delta -- the monitored ratio.
  [[nodiscard]] double regime_ratio(const Eigen::VectorXd &mu0,
                                    const Eigen::MatrixXd &U0, double eps0,
                                    const Eigen::VectorXd &mu1,
                                    const Eigen::MatrixXd &U1,
                                    double eps1) const;

  /// @brief 1 + (sigma_dir/delta)^2 -- V1's empirical law for D^2/HK_true^2,
  /// i.e. the factor by which this pair's squared distance OVERSTATES true HK.
  /// Tracks V1's measured points to under 0.6% over a 10x spread range.
  [[nodiscard]] double implied_gap(const Eigen::VectorXd &mu0,
                                   const Eigen::MatrixXd &U0, double eps0,
                                   const Eigen::VectorXd &mu1,
                                   const Eigen::MatrixXd &U1,
                                   double eps1) const;

private:
  double delta_;
};

/// @brief Exact Bures-Wasserstein W2^2 between two RANK-k-plus-floor Gaussians.
///
/// `wasserstein_2_terms` in semantic_skill.hpp cannot do this: it requires side
/// one to be ISOTROPIC (it exploits Sigma0^{1/2} Sigma1 Sigma0^{1/2} =
/// D0 * Sigma1), which is exactly the assumption Cone-Bures cannot make. This
/// is the general case, ported from `python/cone_bures.py::bures_w2_sq`.
///
/// THE RANK-k REDUCTION, which is what makes it affordable at d = 384. Let
/// W = span(U0) + span(U1), dim p <= 2k. Both Sigma0^{1/2} and Sigma1 preserve
/// W, and on W^perp they act as sqrt(eps0) and eps1, so the product acts as
/// eps0*eps1 there. Hence only a p x p matrix square root is ever formed:
/// O(d k^2 + k^3) rather than O(d^3).
[[nodiscard]] double bures_w2_sq_general(const Eigen::VectorXd &mu0,
                                         const Eigen::MatrixXd &U0, double eps0,
                                         const Eigen::VectorXd &mu1,
                                         const Eigen::MatrixXd &U1, double eps1);

// --- V6 telemetry ---------------------------------------------------------
//
// Thresholds are read off 5z's own measurements, not chosen:
//   0.10  the measured regime (V1c: 0.084-0.100), ~87% agreement, <1% gap
//   0.30  5z's stated degradation point; agreement falls to ~63%
//   0.60  agreement hits 50% -- chance. The predicate carries no information.
inline constexpr double REGIME_OK = 0.10;
inline constexpr double REGIME_WARN = 0.30;
inline constexpr double REGIME_CHANCE = 0.60;

struct RegimeReport {
  std::size_t n{};
  double mean{};
  double p50{};
  double p95{};
  double worst{};
  double mean_implied_gap{};
  double frac_above_warn{};
  double frac_above_chance{};
  std::string status;  ///< "ok" | "degrading" | "chance" | "empty"

  [[nodiscard]] std::string report() const;
};

/// @brief V6: watch sigma_dir/delta so 5z's verdict is checked, not assumed.
///
/// STATUS IS SET BY THE FRACTION OF BAD PAIRS, NOT THE MEAN OR A PERCENTILE.
/// A merge decision is made per PAIR, so the meaningful question is what share
/// of decisions happen in the degraded regime. The mean hides that outright:
/// 95% of pairs at 0.05 with 5% at 0.90 has mean 0.09, indistinguishable from
/// MOS's healthy regime, while one merge in twenty is a coin flip.
///
/// A percentile is not good enough either, and the Python self-test is what
/// caught it: with EXACTLY 5% bad pairs, p95 lands on the boundary and
/// interpolates back into the healthy population, reporting OK for the very
/// distribution it was chosen to detect. Fractions have no such blind spot.
///
/// `kBadFraction` is a POLICY threshold, not a derived one -- it states how
/// many coin-flip merges we tolerate before calling the metric degraded.
class RegimeMonitor {
public:
  static constexpr double kBadFraction = 0.01;

  explicit RegimeMonitor(std::size_t window = 500);

  /// @brief Record one ratio. @throws std::invalid_argument if not finite / < 0.
  void observe_ratio(double ratio);

  /// @brief Record one pair; returns the ratio, or nullopt for coincident means
  /// (which carry no separation direction and are not evidence either way).
  std::optional<double> observe(const ConeBures &metric,
                                const Eigen::VectorXd &mu0,
                                const Eigen::MatrixXd &U0, double eps0,
                                const Eigen::VectorXd &mu1,
                                const Eigen::MatrixXd &U1, double eps1);

  [[nodiscard]] std::size_t size() const noexcept { return ratios_.size(); }
  [[nodiscard]] RegimeReport report() const;
  void clear() noexcept { ratios_.clear(); }

private:
  std::size_t window_;
  std::deque<double> ratios_;
};

} // namespace core
} // namespace mos
