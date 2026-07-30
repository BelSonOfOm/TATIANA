#include "mos/core/coarse_complex.hpp"

#include <algorithm>
#include <cmath>
#include <functional>
#include <iostream>
#include <set>
#include <sstream>
#include <stdexcept>
#include <unordered_map>
#include <utility>

namespace mos {
namespace core {

// ---------------------------------------------------------------- report ---

std::optional<CoarseEdge> CoherenceReport::worst_edge(double tol) const {
  if (per_edge.empty()) {
    return std::nullopt;
  }
  auto it = std::max_element(
      per_edge.begin(), per_edge.end(),
      [](const auto &a, const auto &b) { return a.second < b.second; });
  if (it->second <= tol) {
    // Perfect coherence: there is no guilty coalition to point at.
    return std::nullopt;
  }
  return it->first;
}

std::optional<double> CoherenceReport::mode_position() const {
  if (!rho_tilde.has_value() || !window.has_value()) {
    return std::nullopt;
  }
  const double lo = window->first, hi = window->second;
  if (hi - lo <= 1e-15) {
    return std::nullopt; // degenerate spectrum: "position" would be meaningless
  }
  return (*rho_tilde - lo) / (hi - lo);
}

std::string CoherenceReport::split_summary() const {
  std::ostringstream os;
  os.setf(std::ios::fixed);
  os.precision(4);
  if (!alpha.has_value()) {
    os << "split=UNAVAILABLE (" << split_status << ")";
    return os.str();
  }
  if (!rho_tilde.has_value()) {
    os << "alpha=" << *alpha << "  rho_tilde=UNDEFINED (perfect consensus)";
    return os.str();
  }
  os << "alpha=" << *alpha << "  rho_tilde=" << *rho_tilde;
  if (window.has_value()) {
    os << "  window=[" << window->first << "," << window->second << "]";
  }
  const auto pos = mode_position();
  os << "  position=";
  if (pos.has_value()) {
    os << *pos;
  } else {
    os << "n/a";
  }
  return os.str();
}

std::string CoherenceReport::summary() const {
  std::ostringstream os;
  os.setf(std::ios::fixed);
  os.precision(4);
  if (!rho.has_value()) {
    os << "rho=UNKNOWN (" << status << "); V=" << n_vertices
       << " E=" << n_edges << " b0=" << b0;
    return os.str();
  }
  os << "rho=" << *rho << " confidence=" << *confidence << " omega=" << omega
     << " V=" << n_vertices << " E=" << n_edges << " b0=" << b0;
  if (is_fragmented()) {
    os << "  [FRAGMENTED]";
  }
  return os.str();
}

// --------------------------------------------------------------- complex ---

CoarseComplex::CoarseComplex(double bind_threshold, double decay)
    : bind_threshold_(bind_threshold), decay_rate_(decay) {}

CoarseEdge CoarseComplex::make_key(const ModuleId &u, const ModuleId &v) {
  return (u <= v) ? CoarseEdge{u, v} : CoarseEdge{v, u};
}

void CoarseComplex::register_module(const ModuleId &id) {
  if (stalks_.find(id) == stalks_.end()) {
    stalks_[id] = std::nullopt; // registered but idle
    order_.push_back(id);
    mutation_log_.push_back("register " + id);
  }
}

void CoarseComplex::set_stalk(const ModuleId &id, const Eigen::VectorXd &v) {
  auto it = stalks_.find(id);
  if (it == stalks_.end()) {
    throw std::invalid_argument("set_stalk: unknown module '" + id + "'");
  }
  // Enforce a homogeneous geometry. Mixing dimensions is meaningless, and
  // padding/truncating to paper over it silently corrupts every distance.
  for (const auto &kv : stalks_) {
    if (kv.second.has_value() && kv.second->size() != v.size()) {
      throw std::invalid_argument(
          "set_stalk: dimension mismatch for '" + id + "' (" +
          std::to_string(v.size()) + " vs " +
          std::to_string(kv.second->size()) +
          "). Refusing to pad or truncate geometry.");
    }
  }
  it->second = v;
}

void CoarseComplex::clear_stalk(const ModuleId &id) {
  auto it = stalks_.find(id);
  if (it != stalks_.end()) {
    it->second = std::nullopt;
  }
}

void CoarseComplex::co_activate(const ModuleId &u, const ModuleId &v,
                                double amount) {
  if (u == v || stalks_.find(u) == stalks_.end() ||
      stalks_.find(v) == stalks_.end()) {
    return;
  }
  const CoarseEdge k = make_key(u, v);
  const bool was_bound = is_bound(u, v);
  weights_[k] += amount;
  if (!was_bound && weights_[k] >= bind_threshold_) {
    std::ostringstream os;
    os.setf(std::ios::fixed);
    os.precision(2);
    os << "bind " << k.first << "~" << k.second << " (w=" << weights_[k] << ")";
    mutation_log_.push_back(os.str());
  }
}

void CoarseComplex::tick_decay() {
  for (auto it = weights_.begin(); it != weights_.end();) {
    const bool was_bound = it->second >= bind_threshold_;
    it->second -= decay_rate_;
    if (it->second <= 0.0) {
      if (was_bound) {
        mutation_log_.push_back("collapse " + it->first.first + "~" +
                                it->first.second);
      }
      // The edge is gone, so its precision goes with it. Leaving it behind
      // would let a future re-bind silently inherit a stale confidence from a
      // coalition that has since collapsed.
      precisions_.erase(it->first);
      it = weights_.erase(it);
    } else {
      if (was_bound && it->second < bind_threshold_) {
        mutation_log_.push_back("unbind " + it->first.first + "~" +
                                it->first.second);
      }
      ++it;
    }
  }
}

void CoarseComplex::set_precision(const ModuleId &u, const ModuleId &v,
                                  double pi) {
  if (!std::isfinite(pi) || pi <= 0.0) {
    throw std::invalid_argument(
        "[CoarseComplex::set_precision] pi_e must be finite and > 0, got " +
        std::to_string(pi) +
        ". It is an inverse variance; 0 would delete the edge from the inner "
        "product without deleting it from the complex.");
  }
  precisions_[make_key(u, v)] = pi;
}

std::optional<double> CoarseComplex::precision(const ModuleId &u,
                                               const ModuleId &v) const {
  auto it = precisions_.find(make_key(u, v));
  if (it == precisions_.end()) return std::nullopt;
  return it->second;
}

void CoarseComplex::clear_precision(const ModuleId &u, const ModuleId &v) {
  precisions_.erase(make_key(u, v));
}

std::size_t CoarseComplex::calibrated_edge_count() const {
  std::size_t n = 0;
  for (const auto &e : edges()) {
    if (precisions_.count(e)) ++n;
  }
  return n;
}

bool CoarseComplex::is_bound(const ModuleId &u, const ModuleId &v) const {
  auto it = weights_.find(make_key(u, v));
  return it != weights_.end() && it->second >= bind_threshold_;
}

std::vector<CoarseEdge> CoarseComplex::edges() const {
  std::vector<CoarseEdge> out;
  for (const auto &kv : weights_) {
    if (kv.second >= bind_threshold_) {
      out.push_back(kv.first);
    }
  }
  return out;
}

void CoarseComplex::set_restriction(const ModuleId &u, const ModuleId &v,
                                    const Eigen::MatrixXd &R_u,
                                    const Eigen::MatrixXd &R_v) {
  if (R_u.rows() != R_v.rows()) {
    throw std::invalid_argument(
        "set_restriction: R_u and R_v must map into the SAME edge stalk "
        "(equal row counts).");
  }
  restriction_[make_key(u, v)] = {R_u, R_v};
}

CoherenceReport CoarseComplex::report() const {
  CoherenceReport rep;

  // Only organs that actually hold a position participate.
  std::vector<ModuleId> active;
  for (const auto &id : order_) {
    auto it = stalks_.find(id);
    if (it != stalks_.end() && it->second.has_value()) {
      active.push_back(id);
    }
  }
  rep.n_vertices = static_cast<int>(active.size());

  if (active.empty()) {
    rep.status = "empty";
    rep.b0 = 0;
    return rep;
  }

  // Edges whose BOTH endpoints are active: an idle organ cannot agree or disagree.
  std::vector<CoarseEdge> live;
  for (const auto &e : edges()) {
    const bool a_ok = stalks_.at(e.first).has_value();
    const bool b_ok = stalks_.at(e.second).has_value();
    if (a_ok && b_ok) {
      live.push_back(e);
    }
  }
  rep.n_edges = static_cast<int>(live.size());

  // --- b0 by union-find over the ACTIVE vertices --------------------------
  std::unordered_map<ModuleId, ModuleId> parent;
  for (const auto &id : active) {
    parent[id] = id;
  }
  std::function<ModuleId(ModuleId)> find = [&](ModuleId a) -> ModuleId {
    while (parent[a] != a) {
      parent[a] = parent[parent[a]];
      a = parent[a];
    }
    return a;
  };
  for (const auto &e : live) {
    ModuleId ra = find(e.first), rb = find(e.second);
    if (ra != rb) {
      parent[ra] = rb;
    }
  }
  std::set<ModuleId> roots;
  for (const auto &id : active) {
    roots.insert(find(id));
  }
  rep.b0 = static_cast<int>(roots.size());

  // --- omega and the per-edge breakdown -----------------------------------
  // (5p mechanism 1) precision-weighted predictive-coding free energy:
  //   omega = sum_e pi_e || R_u x_u - R_v x_v ||^2.
  // With no maps set and use_precision_ false (defaults) this is exactly the
  // pre-5p  sum ||x_u - x_v||^2  -- the parity test depends on that identity.
  // 5ah: reads precisions_, NOT weights_. See set_use_precision's note -- using
  // the Hebbian coupling here measured the wrong operator. An edge with no
  // measured precision is UNCALIBRATED and contributes pi=1; it is not treated
  // as strongly-coupled just because it is strongly bound.
  auto pi_of = [&](const CoarseEdge &e) -> double {
    if (!use_precision_) return 1.0;
    auto it = precisions_.find(e);
    return (it != precisions_.end()) ? it->second : 1.0;
  };
  double omega = 0.0;
  for (const auto &e : live) {
    const Eigen::VectorXd &xu = *stalks_.at(e.first);
    const Eigen::VectorXd &xv = *stalks_.at(e.second);
    Eigen::VectorXd eps;
    auto rit = restriction_.find(e);
    if (rit != restriction_.end()) {
      eps = rit->second.first * xu - rit->second.second * xv;
    } else {
      eps = xu - xv;
    }
    const double d = pi_of(e) * eps.squaredNorm();
    rep.per_edge[e] = d;
    omega += d;
  }
  rep.omega = omega;

  // --- GUARD: nobody is talking -------------------------------------------
  if (live.empty()) {
    rep.status = "no_edges";
    return rep; // rho stays empty == UNKNOWN, NOT confidence 1
  }

  // --- GUARD: zero state (Rayleigh quotient is 0/0) ------------------------
  double norm_f2 = 0.0;
  for (const auto &id : active) {
    norm_f2 += stalks_.at(id)->squaredNorm();
  }
  if (norm_f2 <= 0.0) {
    rep.status = "zero_state";
    return rep;
  }

  // --- normalisation: precision-weighted Anderson-Morley bound ------------
  // d_pi(v) = sum of pi_e over edges incident to v; B = max_e (d_pi(u)+d_pi(v)).
  // At uniform pi=1 this is the integer max(deg_u+deg_v) exactly (parity).
  std::map<ModuleId, double> dpi;
  for (const auto &id : active) {
    dpi[id] = 0.0;
  }
  for (const auto &e : live) {
    const double p = pi_of(e);
    dpi[e.first] += p;
    dpi[e.second] += p;
  }
  double B = 0.0;
  for (const auto &e : live) {
    B = std::max(B, dpi[e.first] + dpi[e.second]);
  }

  double rho_raw = omega / (B * norm_f2);
  if (rho_raw > 1.0 + 1e-9) {
    // Only reachable with non-orthogonal restriction maps (||R||>1): the
    // Anderson-Morley bound assumed orthogonality. Do not hide it (mirrors
    // coherence.py's stderr warning).
    std::cerr << "[coarse_complex] WARNING: rho_raw=" << rho_raw
              << " > 1 - restriction maps violated the orthogonality contract; "
                 "the Anderson-Morley bound no longer holds. Clamping.\n";
  }
  double rho = std::min(std::max(rho_raw, 0.0), 1.0); // clamp vs FP drift / contract break

  rep.rho = rho;
  rep.confidence = 1.0 - rho;
  rep.status = "ok";

  // --- E1: split rho into (alpha, rho_tilde) and compute the window --------
  // Ports coherence.py exactly. EXACT ONLY FOR IDENTITY RESTRICTION MAPS: with
  // non-identity maps ker L is not the per-component constants and there is no
  // n x n matrix carrying L's spectrum. We then report the split as unavailable
  // rather than compute something wrong -- rho itself stays exact either way.
  bool any_map = false;
  for (const auto &e : live) {
    if (restriction_.find(e) != restriction_.end()) {
      any_map = true;
      break;
    }
  }
  if (any_map) {
    rep.split_status = "non_identity_maps";
    return rep;
  }

  // Edges with pi_e == 0 contribute nothing to L: they neither raise omega nor
  // join two components as far as ker L is concerned.
  std::vector<CoarseEdge> kernel_edges;
  for (const auto &e : live) {
    if (pi_of(e) > 0.0) kernel_edges.push_back(e);
  }

  // x_perp = x - P_{ker L} x. For identity maps ker(L_K (x) I) is the set of
  // assignments CONSTANT ON EACH COMPONENT, so the projection subtracts the
  // PER-COMPONENT mean -- not the global mean. With b0 > 1 the global mean would
  // score between-component separation as dissent when it actually lies IN the
  // kernel. That is a correctness point, not a refinement.
  std::unordered_map<ModuleId, ModuleId> kparent;
  for (const auto &id : active) kparent[id] = id;
  std::function<ModuleId(ModuleId)> kfind = [&](ModuleId a) -> ModuleId {
    while (kparent[a] != a) {
      kparent[a] = kparent[kparent[a]];
      a = kparent[a];
    }
    return a;
  };
  for (const auto &e : kernel_edges) {
    ModuleId ra = kfind(e.first), rb = kfind(e.second);
    if (ra != rb) kparent[ra] = rb;
  }
  std::map<ModuleId, Eigen::VectorXd> comp_sum;
  std::map<ModuleId, int> comp_count;
  for (const auto &id : active) {
    const ModuleId r = kfind(id);
    const Eigen::VectorXd &xv = *stalks_.at(id);
    auto it = comp_sum.find(r);
    if (it == comp_sum.end()) {
      comp_sum.emplace(r, xv);
    } else {
      it->second += xv;
    }
    comp_count[r] += 1;
  }
  double perp_f2 = 0.0;
  for (const auto &id : active) {
    const ModuleId r = kfind(id);
    const Eigen::VectorXd mean = comp_sum.at(r) / static_cast<double>(comp_count.at(r));
    perp_f2 += (*stalks_.at(id) - mean).squaredNorm();
  }

  // Window endpoints from the SCALAR n x n weighted graph Laplacian: with
  // identity maps L = L_{K,pi} (x) I_d, so spec(L) = spec(L_{K,pi}) with
  // multiplicity d. At n = 7 this eigendecomposition is microseconds, and it is
  // only needed when the topology changes.
  const int n = static_cast<int>(active.size());
  std::map<ModuleId, int> vidx;
  for (int i = 0; i < n; ++i) vidx[active[i]] = i;
  Eigen::MatrixXd LK = Eigen::MatrixXd::Zero(n, n);
  for (const auto &e : kernel_edges) {
    const double p = pi_of(e);
    const int i = vidx.at(e.first), j = vidx.at(e.second);
    LK(i, i) += p;
    LK(j, j) += p;
    LK(i, j) -= p;
    LK(j, i) -= p;
  }
  Eigen::SelfAdjointEigenSolver<Eigen::MatrixXd> es(LK, Eigen::EigenvaluesOnly);
  const Eigen::VectorXd evals = es.eigenvalues();
  const double lam_max = evals.size() ? evals.maxCoeff() : 0.0;
  const double zero_tol = std::max(1e-9, 1e-9 * std::abs(lam_max));
  double lam_min_plus = 0.0;
  bool has_nonzero = false;
  for (int i = 0; i < evals.size(); ++i) {
    if (evals(i) > zero_tol && (!has_nonzero || evals(i) < lam_min_plus)) {
      lam_min_plus = evals(i);
      has_nonzero = true;
    }
  }

  if (perp_f2 <= 1e-12 * norm_f2) {
    // Perfect consensus has NO mode. rho_tilde must be UNKNOWN, not 0 -- zero
    // would assert "the most global mode possible", a measurement we did not make.
    rep.alpha = 0.0;
    rep.split_status = "consensus";
    if (has_nonzero) rep.window = std::make_pair(lam_min_plus / B, lam_max / B);
  } else if (!has_nonzero) {
    rep.alpha = perp_f2 / norm_f2;
    rep.split_status = "n/a"; // no bound pair carries weight
  } else {
    rep.alpha = perp_f2 / norm_f2;
    rep.rho_tilde = omega / (B * perp_f2);
    rep.window = std::make_pair(lam_min_plus / B, lam_max / B);
    rep.split_status = "ok";
  }
  return rep;
}

} // namespace core
} // namespace mos
