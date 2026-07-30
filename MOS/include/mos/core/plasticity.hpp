#pragma once

#include "mos/core/coarse_complex.hpp" // ModuleId, CoarseEdge

#include <cstddef>
#include <deque>
#include <map>
#include <optional>
#include <string>
#include <vector>

namespace mos {
namespace core {

/// @brief (5p mechanism 3) Butz-van Ooyen homeostatic structural plasticity.
/// Per-organ leaky integrator of local discord vs a setpoint. Growth is driven
/// by SUSTAINED deviation, not an instantaneous spike (thrash-proof). C++ port of
/// python/plasticity.py Homeostat - if they disagree, the Python is authoritative.
class Homeostat {
public:
  explicit Homeostat(double setpoint, double leak = 0.25);

  /// Fold one measurement in. Organs absent from this observation relax to 0.
  void observe(const std::map<ModuleId, double> &per_organ_discord);

  /// Integrated deviation from setpoint (positive => grow here).
  [[nodiscard]] double error(const ModuleId &organ) const;

  /// Organs whose PERSISTENT local discord crossed the setpoint, worst first.
  [[nodiscard]] std::vector<ModuleId> organs_needing_growth() const;

  [[nodiscard]] double setpoint() const noexcept { return setpoint_; }

  /// Aggregate a report's per-edge discord into per-organ local discord.
  [[nodiscard]] static std::map<ModuleId, double>
  per_organ_discord(const std::map<CoarseEdge, double> &per_edge);

private:
  double setpoint_;
  double leak_;
  std::map<ModuleId, double> integral_;
};

/// @brief (5p mechanism 2) Beggs-Plenz self-organised criticality.
/// Auto-calibrates the RESOLVE gate eps_rho as a quantile of observed rho (kills
/// the hardcoded 0.10), and nudges decay toward branching ratio sigma ~ 1.
/// C++ port of python/plasticity.py CriticalityMonitor.
///
/// THE THREE EPSILONS (C6-2, and there are three not two)
/// -------------------------------------------------------
/// C6-2 flagged that two different epsilons were about to collide and required
/// a rename before the curvature controller is implemented. Enumerating the
/// actual uses found THREE distinct quantities that were all called `epsilon`:
///
///   eps_rho   THIS ONE. The RESOLVE/EXPLORE gate on discord rho. Dimensionless
///             and bounded in [0,1] because rho is. Auto-calibrated here as a
///             quantile; `KernelConfig::rho_threshold` is its static default.
///   eps_w2    The 2-Wasserstein BALL RADIUS for edge formation and concept
///             retrieval (curator.hpp, knowledge_base.hpp). A SQUARED DISTANCE
///             in embedding space -- not bounded, not dimensionless, and not
///             comparable to eps_rho in any way.
///   eps_flow  The curvature controller's step size in w <- w*exp(eps_flow*kappa)
///             (5ad). **Does not exist yet** -- Phase-2 work. Named here so it
///             cannot be introduced as a bare `epsilon` and silently collide
///             with either of the above, which is exactly what C6-2 predicted.
///
/// Renaming eps_rho and eps_w2 was the cheap half; keeping eps_flow out of the
/// bare namespace is the half that was actually at risk.
class CriticalityMonitor {
public:
  CriticalityMonitor(double default_epsilon_rho = 0.10, std::size_t min_history = 20,
                     double quantile = 0.75, std::size_t window = 500);

  void record_rho(double rho);

  /// The gate: q-quantile of observed rho, or the documented default below
  /// min_history (never a guess from noise). numpy-'linear' interpolation.
  [[nodiscard]] double epsilon_rho() const;

  void record_avalanche(int n_binds);
  [[nodiscard]] std::optional<double> branching_ratio() const;

  /// Push sigma toward 1: supercritical => decay faster, subcritical => slower.
  [[nodiscard]] double suggest_decay(double current_decay,
                                     double target_sigma = 1.0,
                                     double gain = 0.1) const;

private:
  double default_epsilon_rho_;
  std::size_t min_history_;
  double quantile_;
  std::size_t window_;
  std::deque<double> rho_history_;
  std::deque<int> avalanches_;
};

} // namespace core
} // namespace mos
