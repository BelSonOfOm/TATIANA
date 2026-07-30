#pragma once

#include <Eigen/Dense>
#include <cstddef>
#include <map>
#include <optional>
#include <string>
#include <utility>
#include <vector>

namespace mos {
namespace core {

/// Identifier of a cognitive organ occupying a vertex of the coarse complex K.
using ModuleId = std::string;

/// A bound pair of organs: the 1-simplices of K. Always stored canonically
/// ordered so (a,b) and (b,a) are the same edge.
using CoarseEdge = std::pair<ModuleId, ModuleId>;

/// @brief Result of measuring discord over K.
///
/// `rho` is EMPTY when discord is genuinely undefined — not zero, not one.
/// See CoarseComplex::report() for the two cases where that happens.
struct CoherenceReport {
  std::optional<double> rho;        ///< normalised discord in [0,1]; empty = UNKNOWN
  std::optional<double> confidence; ///< 1 - rho; empty = UNKNOWN
  double omega{0.0};                ///< raw (unnormalised) discord
  std::map<CoarseEdge, double> per_edge; ///< per-coalition breakdown
  int b0{0};                        ///< connected components => fragmentation
  int n_vertices{0};
  int n_edges{0};
  std::string status{"empty"};      ///< ok | no_edges | zero_state | empty

  // --- E1: the rho = alpha * rho_tilde split (audit 2026-07-27) -------------
  // rho tangles two independent questions. omega is blind to consensus (it IS
  // ker L), but ||X||_F^2 is not. Splitting x = x_0 + x_perp orthogonally gives
  // the EXACT factorisation rho = alpha * rho_tilde, where
  //   alpha     = ||x_perp||^2 / ||X||_F^2   -- HOW MUCH of the state dissents
  //   rho_tilde = omega / (B ||x_perp||^2)   -- WHICH MODE the dissent occupies
  // They call for opposite remedies: high alpha + low rho_tilde is a two-camp
  // split wanting `split`/`bind`; low alpha + high rho_tilde is one outlier organ
  // wanting edge repair. rho alone cannot tell them apart.
  std::optional<double> alpha;      ///< dissent fraction; empty = not computed
  std::optional<double> rho_tilde;  ///< mode index; empty = UNKNOWN (see split_status)
  /// Achievable range of rho_tilde: [lambda_min_plus(L_K,pi)/B, lambda_max/B].
  /// BOTH ENDPOINTS ARE GRAPH INVARIANTS, known before any data is seen, and
  /// need recomputing only when bind/collapse changes the topology.
  std::optional<std::pair<double, double>> window;
  /// ok | consensus | non_identity_maps | n/a | not_computed
  std::string split_status{"not_computed"};

  /// More than one component: any global coherence claim is only local.
  [[nodiscard]] bool is_fragmented() const noexcept { return b0 > 1; }

  /// @brief Where rho_tilde sits inside its achievable window, in [0,1].
  /// 0 = lowest (most global) mode the topology admits; 1 = highest (most local).
  /// This is the scale on which a topology-calibrated threshold should be set,
  /// because it is the only one comparable across rewirings. Empty when the
  /// window is degenerate or the split was not computed.
  [[nodiscard]] std::optional<double> mode_position() const;

  /// @brief The E1 diagnostic line (alpha, rho_tilde, window, position).
  [[nodiscard]] std::string split_summary() const;

  /// @brief The guilty coalition — where RESOLVE should be aimed.
  /// Returns empty when there is no actual disagreement: a bare max() would
  /// return an arbitrary edge even with every omega_e == 0, pointing RESOLVE at
  /// a conflict that does not exist.
  [[nodiscard]] std::optional<CoarseEdge> worst_edge(double tol = 1e-12) const;

  [[nodiscard]] std::string summary() const;
};

/// @brief The coarse complex K: cognitive organs as vertices, coalitions as edges.
///
/// This is the C++ port of python/coherence.py + python/module_vertex.py, which
/// remain the authoritative reference implementation and test-bed.
///
/// THE MEASURE
/// -----------
/// Each organ holds a position (its stalk) in a shared meaning-space. For every
/// bound pair we measure how far apart the two positions are:
///
///     omega = sum over bound pairs {u,v} of || x_u - x_v ||^2
///
/// omega is not scale-invariant (it grows if vectors merely get longer, or if
/// more organs are added), so we normalise by an upper bound on the Laplacian
/// spectrum. With identity restriction maps the sheaf Laplacian is L_G (x) I, and
/// the Anderson-Morley bound gives lambda_max(L_G) <= max over edges of
/// (deg u + deg v) =: B. Hence
///
///     rho = omega / (B * ||X||_F^2)   in [0,1]   -- guaranteed, no eigensolver
///     confidence = 1 - rho
///
/// THE GUARDS (both are load-bearing)
/// ----------------------------------
///  * no edges  -> rho is UNKNOWN. Nobody disagrees because nobody is talking;
///                 reporting confidence = 1 for a silent, fragmented system would
///                 be the most dangerous failure this design could have.
///  * zero state-> rho is UNKNOWN (the Rayleigh quotient is 0/0).
/// b0 is always reported: a LARGE kernel means fragmentation, not harmony.
class CoarseComplex {
public:
  /// @param bind_threshold Coupling weight at which a pair becomes a 1-simplex.
  /// @param decay Amount subtracted from every coupling on each idle tick.
  explicit CoarseComplex(double bind_threshold = 1.0, double decay = 0.1);

  /// @brief Add an organ as a vertex of K.
  void register_module(const ModuleId &id);

  /// @brief Set an organ's position (the coarse-graining map pi_v applied).
  /// @throws std::invalid_argument if the dimension disagrees with other organs;
  ///         geometry is never padded or truncated to fit.
  void set_stalk(const ModuleId &id, const Eigen::VectorXd &v);

  /// @brief Mark an organ idle. An idle organ has NO position — deliberately not
  /// a zero vector, which would silently drag every distance toward the origin.
  void clear_stalk(const ModuleId &id);

  /// @brief Hebbian reinforcement: organs that fire together wire together.
  void co_activate(const ModuleId &u, const ModuleId &v, double amount = 0.5);

  /// @brief Idle decay; coalitions reaching zero collapse (garbage collection).
  void tick_decay();

  [[nodiscard]] bool is_bound(const ModuleId &u, const ModuleId &v) const;

  /// @brief The 1-simplices: pairs whose coupling passed the bind threshold.
  [[nodiscard]] std::vector<CoarseEdge> edges() const;

  // --- (5p mechanism 1) predictive-coding measure -------------------------
  // Ports python/coherence.py's precision-weighted form. With NO restriction
  // maps set and use_precision=false (the defaults), report() is byte-identical
  // to the pre-5p measure - the parity test relies on that.

  /// @brief Set an ORTHOGONAL restriction pair (R_u, R_v) for edge {u,v}, taking
  /// each vertex stalk into the edge stalk. eps_e = R_u x_u - R_v x_v is then the
  /// prediction error. Orthogonality is the caller's contract (the learner keeps
  /// it via polar retraction); non-orthogonal maps can break the rho<=1 bound and
  /// are warned at report() time, exactly as in coherence.py.
  void set_restriction(const ModuleId &u, const ModuleId &v,
                       const Eigen::MatrixXd &R_u, const Eigen::MatrixXd &R_v);

  /// @brief Master switch for precision weighting. Off by default => uniform
  /// pi=1, the pre-5p behaviour, which the parity test depends on.
  ///
  /// **CHANGED (5ah): this no longer means "use the coupling weight as pi_e".**
  /// It used to read `weights_`, i.e. the Hebbian coupling w(sigma,t), which is
  /// the exact conflation 5ac and 5af both ruled out:
  ///
  ///   > w(sigma,t) is a normalised coupling, capped on [0,1]. pi_e is a
  ///   > precision, uncapped. They are not the same variable and must never be
  ///   > substituted for one another.
  ///
  /// Using the coupling computed the curvature and the free energy of a
  /// DIFFERENT operator than the one the engine prints omega and rho from --
  /// a consistent-looking number about the wrong thing. 5q had already eaten a
  /// divergence bug from the same conflation ("raw coupling weight as precision
  /// made lr*precision huge"). pi_e now comes from `set_precision` only, and
  /// unset edges are pi=1 (UNCALIBRATED, not "trusted").
  void set_use_precision(bool on) noexcept { use_precision_ = on; }
  [[nodiscard]] bool use_precision() const noexcept { return use_precision_; }

  /// @brief Set the edge precision pi_e for {u,v} -- an inverse variance, and
  /// the ONLY home for a reported confidence (Q9, FIX-13).
  ///
  /// Stored separately from the Hebbian coupling and never derived from it. In
  /// the cell-weight tower (semantic_skill.hpp) this is the edge level; use
  /// `core::edge_precision(nu_u, nu_v)` to build it from two endpoint
  /// confidences, or pass a directly-measured pair confidence when one exists
  /// (python/experiment_e5.py elicits exactly that, and a direct measurement
  /// always beats a derivation).
  ///
  /// @throws std::invalid_argument if pi <= 0 or is not finite.
  void set_precision(const ModuleId &u, const ModuleId &v, double pi);

  /// @brief The stored pi_e, or nullopt if this edge was never calibrated.
  /// Deliberately distinguishable from 1.0: "nobody measured this" and "measured
  /// as exactly average" are different facts and the telemetry must not merge
  /// them.
  [[nodiscard]] std::optional<double> precision(const ModuleId &u,
                                                const ModuleId &v) const;

  /// @brief Forget an edge's precision (back to UNCALIBRATED).
  void clear_precision(const ModuleId &u, const ModuleId &v);

  /// @brief How many live edges carry a measured pi_e. Telemetry for the
  /// question "is Pi actually doing anything yet?" -- if this is 0 then
  /// tau_f == 1, F_MOS collapses to the unit-weight formula, and the whole
  /// derived-weight story is inert (5ah).
  [[nodiscard]] std::size_t calibrated_edge_count() const;

  /// @brief Measure discord over K. Edges touching an idle organ are ignored,
  /// since an organ with no position cannot meaningfully agree or disagree.
  [[nodiscard]] CoherenceReport report() const;

  /// @brief Audit trail of every typed structural operation (bind/collapse/...).
  [[nodiscard]] const std::vector<std::string> &mutation_log() const noexcept {
    return mutation_log_;
  }

  [[nodiscard]] const std::vector<ModuleId> &modules() const noexcept {
    return order_;
  }

private:
  static CoarseEdge make_key(const ModuleId &u, const ModuleId &v);

  double bind_threshold_;
  double decay_rate_;
  std::vector<ModuleId> order_; ///< registration order, for stable reporting
  std::map<ModuleId, std::optional<Eigen::VectorXd>> stalks_;
  std::map<CoarseEdge, double> weights_;   ///< w(sigma,t): Hebbian coupling, [0,1]-ish
  std::map<CoarseEdge, double> precisions_; ///< pi_e: inverse variance, UNCAPPED.
                                            ///< Separate from weights_ by contract (5ah).
  std::vector<std::string> mutation_log_;
  // (5p mechanism 1) per-edge restriction pair (R_u, R_v); absent => identity.
  std::map<CoarseEdge, std::pair<Eigen::MatrixXd, Eigen::MatrixXd>> restriction_;
  bool use_precision_{false};
};

} // namespace core
} // namespace mos
