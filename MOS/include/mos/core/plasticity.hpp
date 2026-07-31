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
class CriticalityMonitor {
public:
  CriticalityMonitor(double default_eps_rho = 0.10, std::size_t min_history = 20,
                     double quantile = 0.75, std::size_t window = 500);

  void record_rho(double rho);

  /// eps_rho: the RESOLVE/EXPLORE THRESHOLD on rho. The q-quantile of observed
  /// rho, or the documented default below min_history (never a guess from
  /// noise). numpy-'linear' interpolation.
  ///
  /// NAMED eps_rho, NOT epsilon (C6-2). The second epsilon in MOS is eps_flow,
  /// the STEP SIZE in the curvature flow `w <- w*exp(eps_flow*kappa)` (5ad).
  /// A threshold is compared against a measurement; a step size multiplies a
  /// rate. They share only a Greek letter, and the prose conflated them once
  /// already. The flow is not in the engine yet, so this rename is preventive.
  [[nodiscard]] double eps_rho() const;

  void record_avalanche(int n_binds);
  [[nodiscard]] std::optional<double> branching_ratio() const;

  /// Push sigma toward 1: supercritical => decay faster, subcritical => slower.
  [[nodiscard]] double suggest_decay(double current_decay,
                                     double target_sigma = 1.0,
                                     double gain = 0.1) const;

private:
  double default_eps_rho_;
  std::size_t min_history_;
  double quantile_;
  std::size_t window_;
  std::deque<double> rho_history_;
  std::deque<int> avalanches_;
};

} // namespace core
} // namespace mos
