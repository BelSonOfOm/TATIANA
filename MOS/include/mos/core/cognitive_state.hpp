#pragma once

#include "mos/topology/complex.hpp"
#include <Eigen/Sparse>
#include <atomic>
#include <map>
#include <memory>
#include <optional>
#include <shared_mutex>
#include <string>
#include <vector>

namespace mos {
namespace core {

class SemanticEmbedding; // defined in semantic_skill.hpp

/// @brief Represents a generic procedural skill attached to the topology.
class ProceduralSkill {
public:
  virtual ~ProceduralSkill() = default;

  [[nodiscard]] virtual std::string description() const = 0;

  /// @brief Merges another skill into this one when simplices collapse.
  /// @param other The other skill to merge.
  virtual void merge_with(const ProceduralSkill &other) = 0;
};

/// @brief The procedural layer (F).
/// Attaches procedural data or functions to the simplices of C.
class Sheaf {
public:
  /// @brief Default constructor.
  Sheaf() = default;

  /// @brief Attach a skill to a simplex.
  /// @param s The simplex.
  /// @param skill Shared pointer to the skill.
  void attach(const topology::Simplex &s,
              std::shared_ptr<ProceduralSkill> skill);

  /// @brief Retrieve a skill for a simplex.
  /// @param s The simplex.
  /// @return Shared pointer to the skill, or nullptr if not found.
  [[nodiscard]] std::shared_ptr<ProceduralSkill>
  get_skill(const topology::Simplex &s) const;

  /// @brief Removes the stalk (skill) attached to a simplex.
  void remove_stalk(const topology::Simplex &s);

  /// @brief Merge stalks when a vertex is contracted.
  /// Moves any procedural data attached to the removed vertex (or simplices
  /// containing it) to the corresponding simplices containing the kept vertex.
  /// @param keep_v The vertex ID to keep.
  /// @param remove_v The vertex ID to remove.
  void merge_stalks(topology::VertexID keep_v, topology::VertexID remove_v);

private:
  mutable std::mutex mutex_;
  std::map<topology::Simplex, std::shared_ptr<ProceduralSkill>> stalks_;
};

/// @brief Represents a specific active instantiation (state trace) over the
/// complex.
class GlobalSection {
public:
  /// @brief Check if the current section is stable (attractor reached).
  /// @return True if obstruction is exactly 0.0.
  [[nodiscard]] bool is_stable() const noexcept;

  /// @brief Set the current obstruction measure.
  /// @param measure The calculated obstruction.
  void set_obstruction(double measure) noexcept;

  /// @brief Get the current obstruction measure.
  /// @return The obstruction value.
  [[nodiscard]] double get_obstruction() const noexcept;

private:
  std::atomic<double> obstruction_measure_{1.0};
};

/// @brief The Cognitive State Space (C, F, s).
/// This is the evolving geometric object representing the intelligence runtime.
class CognitiveState {
public:
  CognitiveState() = default;

  /// @brief Get the underlying mathematical simplicial complex (C_math).
  /// @return Reference to the complex.
  [[nodiscard]] topology::SimplicialComplex &get_math_complex() noexcept;
  [[nodiscard]] const topology::SimplicialComplex &
  get_math_complex() const noexcept;

  /// @brief Get the procedural sheaf (F_math).
  /// @return Reference to the sheaf.
  [[nodiscard]] Sheaf &get_math_sheaf() noexcept;
  [[nodiscard]] const Sheaf &get_math_sheaf() const noexcept;

  // Convenience aliases
  [[nodiscard]] topology::SimplicialComplex &get_complex() noexcept {
    return math_complex_;
  }
  [[nodiscard]] const topology::SimplicialComplex &
  get_complex() const noexcept {
    return math_complex_;
  }
  [[nodiscard]] Sheaf &get_sheaf() noexcept { return math_sheaf_; }
  [[nodiscard]] const Sheaf &get_sheaf() const noexcept { return math_sheaf_; }

  /// @brief Get the chat simplicial complex.
  [[nodiscard]] topology::SimplicialComplex &get_chat_complex() noexcept {
    return chat_complex_;
  }
  [[nodiscard]] const topology::SimplicialComplex &
  get_chat_complex() const noexcept {
    return chat_complex_;
  }

  /// @brief Get the chat procedural sheaf.
  [[nodiscard]] Sheaf &get_chat_sheaf() noexcept { return chat_sheaf_; }
  [[nodiscard]] const Sheaf &get_chat_sheaf() const noexcept {
    return chat_sheaf_;
  }

  /// @brief Get the global section (s).
  /// @brief Retrieve the global section corresponding to this state
  GlobalSection &get_section() { return section_; }

  /// @brief Check if the topological geometry has collapsed
  bool is_collapsed() const { return is_collapsed_; }

  /// @brief Injects a temporary axiom as a geometric boundary condition.
  /// @param payload The binary or string representation of the axiom.
  /// @param is_rigid If true, applies as a hard subspace projection P. If
  /// false, applies as a penalty potential V.
  /// @param geometry The dense geometry vector representing the diagonal mask
  /// (for RIGID) or gradient vector (for FLUID).
  /// @param organ Which organ this axiom belongs to (for pi_v); empty => untagged.
  void inject_temporary_axiom(const std::string &payload, bool is_rigid,
                              const std::vector<float> &geometry,
                              const std::string &organ = "");

  /// @brief Removes a temporary axiom to restore pristine mathematical state.
  /// @param payload The payload to remove.
  void remove_temporary_axiom(const std::string &payload);

  /// @brief Grows the fine complex C_math by one permanent concept vertex.
  ///
  /// This is the organic-growth path ("neurogenesis"): SearchOp, ComputeOp and
  /// ReasonOp call this with the operator's payload geometry so that a reasoning
  /// act actually leaves a trace in the state space, rather than merely reading
  /// it. Distinct from inject_temporary_axiom(), which represents a transient
  /// BOUNDARY CONDITION (dropped when the turn ends) and perturbs the rigid/fluid
  /// projection; a grown concept is a permanent addition to C_math and does not
  /// touch P_/fluid_center_.
  ///
  /// Without this, apply_flow() and calculate_conflict_score() have nothing to
  /// act on: both require concept vertices to already exist in math_complex_, and
  /// conflict specifically requires at least two to compare.
  ///
  /// @param label Human-readable name for the concept (becomes the skill name).
  /// @param geometry The concept's position (locally-computed embedding).
  /// @param organ Which cognitive organ grew this concept (OpType name). Used to
  ///        compute that organ's coarse position pi_v; empty => untagged.
  /// @throws std::invalid_argument if geometry's dimension disagrees with the
  ///         space's established embedding_dimension_ — never silently reshaped.
  void grow_concept(const std::string &label, const std::vector<double> &geometry,
                    const std::string &organ = "");

  /// @brief pi_v: an organ's coarse position, fused from its OWN fine complex.
  ///
  /// This is the two-level bridge of Construction 2: rather than the coarse organ
  /// borrowing a raw payload embedding, its position is the precision-weighted
  /// fusion (fuse_concept_means) of every concept that organ has grown. So coarse
  /// discord (rho over K) and the fine-level concept geometry become the SAME
  /// measurement at two resolutions, instead of two loosely-correlated numbers.
  ///
  /// @return The fused mean, or empty if the organ has grown no concepts (in which
  ///         case the organ has no position and is excluded from rho — correct:
  ///         an organ that has done nothing cannot agree or disagree).
  [[nodiscard]] std::optional<Eigen::VectorXd>
  compute_pi_v(const std::string &organ) const;

  /// @brief Every organ that currently has at least one grown concept.
  [[nodiscard]] std::vector<std::string> active_organs() const;

  /// @brief Injects a casual chat memory directly into the isolated chat
  /// topology.
  /// @param payload The string content of the chat.
  /// @param geometry The dense geometry vector from the embedding model.
  void inject_chat_memory(const std::string &payload,
                          const std::vector<float> &geometry);

  /// @brief Evolves the underlying semantic stalks directly according to the
  /// Projected Lagrangian Flow.
  /// @param F_deduce The deductive logic vector.
  /// @param dt Time step.
  /// @param lambda Penalty multiplier for fluid constraints.
  void apply_flow(const Eigen::VectorXf &F_deduce, float dt = 1e-2f,
                  float lambda = 1.0f);

  /// @brief Calculates the conflict score using PCA/SVD on embeddings
  /// (structural conflict).
  /// @return The dominant variance.
  [[nodiscard]] double calculate_conflict_score() const;

  /// @brief Extracts the current unified state vector from the active
  /// embeddings.
  [[nodiscard]] Eigen::VectorXf get_current_state_vector() const;

  /// @brief Calculates the principal eigenvector of the structural covariance
  /// matrix.
  [[nodiscard]] Eigen::VectorXf get_principal_stress_vector() const;

  /// @brief Calculates the total differential entropy of the global section.
  /// Used to determine if the state has crystallized into an attractor.
  [[nodiscard]] double calculate_differential_entropy() const;

  /// @brief Checks if the current state has reached a zero-obstruction
  /// attractor. Evaluates if the differential entropy is below a strict
  /// threshold.
  /// @return True if stable.
  [[nodiscard]] bool is_attractor_reached() const;

  /// @brief Set the atomic attractor flag.
  void notify_attractor_state(bool is_attractor) noexcept {
    attractor_flag_.store(is_attractor, std::memory_order_release);
  }

  /// @brief Check the atomic attractor flag.
  [[nodiscard]] bool check_attractor_flag() const noexcept {
    return attractor_flag_.load(std::memory_order_acquire);
  }

  /// @brief Get the thread-safe mutex for operad locking.
  std::shared_mutex &get_mutex() const { return math_mutex_; }

  // Raw un-locked internal access for callers who already own the lock
  [[nodiscard]] double calculate_conflict_score_internal() const;
  [[nodiscard]] Eigen::VectorXf get_current_state_vector_internal() const;
  [[nodiscard]] Eigen::VectorXf get_principal_stress_internal() const;
  [[nodiscard]] double calculate_differential_entropy_internal() const;

private:
  topology::SimplicialComplex math_complex_;
  Sheaf math_sheaf_;

  // Dual-track architecture: isolated from mathematical reasoning
  topology::SimplicialComplex chat_complex_;
  Sheaf chat_sheaf_;

  // Concepts grouped by the organ that grew them, for pi_v fusion. Holds the same
  // shared SemanticEmbedding objects that live in math_sheaf_ (no duplication of
  // the vectors themselves).
  std::map<std::string, std::vector<std::shared_ptr<const SemanticEmbedding>>>
      organ_concepts_;

  // Enforces homogeneous geometry spaces
  size_t embedding_dimension_{0};

  // Indicates severe topological breakdown (PCA singularity)
  mutable bool is_collapsed_{false};

  GlobalSection section_;
  // Projected Lagrangian Flow Data
  Eigen::SparseMatrix<float> P_; // Rigid algebraic projection mask
  Eigen::VectorXf fluid_center_; // Fluid penalty potential center (attractor)
  // Mutable so locks can be acquired in const methods (e.g. read_only)
  mutable std::shared_mutex math_mutex_;
  mutable std::shared_mutex chat_mutex_;
  std::atomic<int> next_vertex_id_{0};
  std::atomic<bool> attractor_flag_{false};
};

} // namespace core
} // namespace mos
