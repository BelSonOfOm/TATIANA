#include "mos/core/plasticity.hpp"

#include <algorithm>
#include <cmath>
#include <numeric>
#include <set>
#include <utility>

namespace mos {
namespace core {

// -------------------------------------------------------------- Homeostat ---

Homeostat::Homeostat(double setpoint, double leak)
    : setpoint_(setpoint), leak_(leak) {}

void Homeostat::observe(const std::map<ModuleId, double> &per_organ_discord) {
  // Every organ we already track, plus any newly seen this frame. Organs absent
  // from this observation contribute discord 0 (they are not disagreeing now).
  std::set<ModuleId> keys;
  for (const auto &kv : integral_)
    keys.insert(kv.first);
  for (const auto &kv : per_organ_discord)
    keys.insert(kv.first);

  for (const auto &k : keys) {
    double d = 0.0;
    auto it = per_organ_discord.find(k);
    if (it != per_organ_discord.end())
      d = it->second;
    const double prev = integral_.count(k) ? integral_[k] : 0.0;
    integral_[k] = (1.0 - leak_) * prev + leak_ * d;
  }
}

double Homeostat::error(const ModuleId &organ) const {
  auto it = integral_.find(organ);
  return (it != integral_.end() ? it->second : 0.0) - setpoint_;
}

std::vector<ModuleId> Homeostat::organs_needing_growth() const {
  std::vector<std::pair<ModuleId, double>> hot;
  for (const auto &kv : integral_)
    if (kv.second > setpoint_)
      hot.push_back(kv);
  std::sort(hot.begin(), hot.end(),
            [](const auto &a, const auto &b) { return a.second > b.second; });
  std::vector<ModuleId> out;
  out.reserve(hot.size());
  for (const auto &p : hot)
    out.push_back(p.first);
  return out;
}

std::map<ModuleId, double>
Homeostat::per_organ_discord(const std::map<CoarseEdge, double> &per_edge) {
  std::map<ModuleId, double> out;
  for (const auto &kv : per_edge) {
    out[kv.first.first] += kv.second;
    out[kv.first.second] += kv.second;
  }
  return out;
}

// ------------------------------------------------------ CriticalityMonitor ---

CriticalityMonitor::CriticalityMonitor(double default_epsilon,
                                       std::size_t min_history, double quantile,
                                       std::size_t window)
    : default_epsilon_(default_epsilon), min_history_(min_history),
      quantile_(quantile), window_(window) {}

void CriticalityMonitor::record_rho(double rho) {
  rho_history_.push_back(rho);
  while (rho_history_.size() > window_)
    rho_history_.pop_front();
}

double CriticalityMonitor::epsilon() const {
  if (rho_history_.size() < min_history_)
    return default_epsilon_;
  std::vector<double> s(rho_history_.begin(), rho_history_.end());
  std::sort(s.begin(), s.end());
  // numpy default 'linear' quantile: position = q*(n-1), interpolate.
  const double pos = quantile_ * (static_cast<double>(s.size()) - 1.0);
  const std::size_t lo = static_cast<std::size_t>(std::floor(pos));
  const std::size_t hi = static_cast<std::size_t>(std::ceil(pos));
  const double frac = pos - static_cast<double>(lo);
  return s[lo] + frac * (s[hi] - s[lo]);
}

void CriticalityMonitor::record_avalanche(int n_binds) {
  avalanches_.push_back(n_binds);
  while (avalanches_.size() > window_)
    avalanches_.pop_front();
}

std::optional<double> CriticalityMonitor::branching_ratio() const {
  if (avalanches_.empty())
    return std::nullopt;
  const double s =
      std::accumulate(avalanches_.begin(), avalanches_.end(), 0.0);
  return s / static_cast<double>(avalanches_.size());
}

double CriticalityMonitor::suggest_decay(double current_decay,
                                         double target_sigma,
                                         double gain) const {
  const auto sigma = branching_ratio();
  if (!sigma)
    return current_decay;
  const double adjusted = current_decay + gain * (*sigma - target_sigma);
  return std::max(adjusted, 1e-3);
}

} // namespace core
} // namespace mos
