#include "mos/core/cognitive_state.hpp"
#include "mos/core/semantic_skill.hpp"
#include <Eigen/Dense>
#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>

namespace mos {
namespace core {

void Sheaf::attach(const topology::Simplex &s,
                   std::shared_ptr<ProceduralSkill> skill) {
  std::lock_guard<std::mutex> lock(mutex_);
  stalks_[s] = std::move(skill);
}

std::shared_ptr<ProceduralSkill>
Sheaf::get_skill(const topology::Simplex &s) const {
  std::lock_guard<std::mutex> lock(mutex_);
  auto it = stalks_.find(s);
  if (it != stalks_.end()) {
    return it->second;
  }
  return nullptr;
}

void Sheaf::remove_stalk(const topology::Simplex &s) {
  std::lock_guard<std::mutex> lock(mutex_);
  stalks_.erase(s);
}

void Sheaf::merge_stalks(topology::VertexID keep_v,
                         topology::VertexID remove_v) {
  std::lock_guard<std::mutex> lock(mutex_);
  std::map<topology::Simplex, std::shared_ptr<ProceduralSkill>> updated_stalks;

  for (auto it = stalks_.begin(); it != stalks_.end();) {
    const auto &s = it->first;
    const auto &verts = s.get_vertices();

    if (std::find(verts.begin(), verts.end(), remove_v) != verts.end()) {
      std::vector<topology::VertexID> new_verts;
      new_verts.reserve(verts.size());
      for (auto v : verts) {
        if (v == remove_v) {
          if (std::find(verts.begin(), verts.end(), keep_v) == verts.end()) {
            new_verts.push_back(keep_v);
          }
        } else {
          new_verts.push_back(v);
        }
      }

      if (!new_verts.empty()) {
        topology::Simplex new_s(std::move(new_verts));
        if (updated_stalks.find(new_s) != updated_stalks.end()) {
          updated_stalks[new_s]->merge_with(*(it->second));
        } else {
          updated_stalks[new_s] = std::move(it->second);
        }
      }
      it = stalks_.erase(it);
    } else {
      ++it;
    }
  }

  for (auto &[new_s, skill] : updated_stalks) {
    if (stalks_.find(new_s) != stalks_.end()) {
      stalks_[new_s]->merge_with(*skill);
    } else {
      stalks_[new_s] = std::move(skill);
    }
  }
}

bool GlobalSection::is_stable() const noexcept {
  return std::abs(obstruction_measure_.load()) < 1e-9;
}

void GlobalSection::set_obstruction(double measure) noexcept {
  obstruction_measure_ = measure;
}

double GlobalSection::get_obstruction() const noexcept {
  return obstruction_measure_;
}

const topology::SimplicialComplex &
CognitiveState::get_math_complex() const noexcept {
  return math_complex_;
}
topology::SimplicialComplex &CognitiveState::get_math_complex() noexcept {
  return math_complex_;
}

const Sheaf &CognitiveState::get_math_sheaf() const noexcept {
  return math_sheaf_;
}
Sheaf &CognitiveState::get_math_sheaf() noexcept { return math_sheaf_; }


void CognitiveState::inject_temporary_axiom(
    const std::string &payload, bool is_rigid,
    const std::vector<float> &geometry, const std::string &organ) {
  std::lock_guard<std::shared_mutex> lock(math_mutex_);

  topology::VertexID v = next_vertex_id_++;
  topology::Simplex boundary_simplex({v});
  math_complex_.insert(boundary_simplex);

  int dim = static_cast<int>(geometry.size());

  if (embedding_dimension_ == 0) {
    embedding_dimension_ = dim;
  } else if (static_cast<size_t>(dim) != embedding_dimension_) {
    // Enforce strict memory bounds
    throw std::invalid_argument(
        "[CognitiveState] Dimension mismatch in temporary axiom. Expected " +
        std::to_string(embedding_dimension_) + ", got " + std::to_string(dim) +
        ".");
  }

  Eigen::VectorXd true_geometry = Eigen::VectorXd::Zero(dim);
  for (size_t i = 0; i < geometry.size(); ++i) {
    true_geometry(i) = geometry[i];
  }

  double near_zero_D = std::numeric_limits<double>::epsilon();
  Eigen::MatrixXd empty_U(dim, 0);
  auto skill = std::make_shared<SemanticEmbedding>(true_geometry, empty_U,
                                                   near_zero_D, payload);
  math_sheaf_.attach(boundary_simplex, skill);

  if (!organ.empty()) {
    // An axiom is a near-certain belief (tiny D); fuse_concept_means floors D so
    // it strongly — but not infinitely — pins the organ's pi_v.
    organ_concepts_[organ].push_back(skill);
  }

  if (dim > 0) {
    if (is_rigid) {
      if (P_.rows() != dim) {
        P_.resize(dim, dim);
        P_.setIdentity();
      }
      for (size_t i = 0; i < geometry.size(); ++i) {
        if (geometry[i] == 0.0f) {
          P_.coeffRef(i, i) = 0.0f;
        }
      }
      P_.makeCompressed();
    } else {
      if (fluid_center_.size() != dim) {
        fluid_center_ = Eigen::VectorXf::Zero(dim);
      }
      for (size_t i = 0; i < dim; ++i) {
        fluid_center_(i) += geometry[i];
      }
    }
  }
  
  is_collapsed_ = false;
}

void CognitiveState::remove_temporary_axiom(const std::string &payload) {
  std::lock_guard<std::shared_mutex> lock(math_mutex_);

  const auto &simplices = math_complex_.get_simplices();
  auto it_0 = simplices.find(0);
  if (it_0 == simplices.end())
    return;

  std::vector<topology::Simplex> to_remove;
  for (const auto &s : it_0->second) {
    auto skill = math_sheaf_.get_skill(s);
    if (auto sem = std::dynamic_pointer_cast<SemanticEmbedding>(skill)) {
      if (sem->get_name() == payload) {
        to_remove.push_back(s);
      }
    }
  }

  for (const auto &s : to_remove) {
    math_sheaf_.remove_stalk(s);
    math_complex_.remove(s);
  }
}

void CognitiveState::grow_concept(const std::string &label,
                                  const std::vector<double> &geometry,
                                  const std::string &organ) {
  if (geometry.empty()) {
    // No geometry, nothing to grow. Silently doing nothing is correct here
    // (contrast: a *wrong* dimension below still throws).
    return;
  }

  std::unique_lock<std::shared_mutex> lock(math_mutex_);

  const int dim = static_cast<int>(geometry.size());
  if (embedding_dimension_ == 0) {
    embedding_dimension_ = dim;
  } else if (static_cast<size_t>(dim) != embedding_dimension_) {
    throw std::invalid_argument(
        "[CognitiveState] Dimension mismatch growing concept '" + label +
        "'. Expected " + std::to_string(embedding_dimension_) + ", got " +
        std::to_string(dim) + ". Refusing to pad or truncate.");
  }

  topology::VertexID v = next_vertex_id_++;
  topology::Simplex s({v});
  math_complex_.insert(s);

  Eigen::VectorXd mu(dim);
  for (int i = 0; i < dim; ++i) {
    mu(i) = geometry[static_cast<size_t>(i)];
  }

  // A freshly-grown concept starts with no established covariance structure
  // (rank 0) and an explicit, named prior variance rather than a fabricated
  // near-zero "certain axiom" value — this concept was inferred, not stated.
  constexpr double GROWN_CONCEPT_VARIANCE_PRIOR = 1.0;
  Eigen::MatrixXd empty_U(dim, 0);
  auto skill = std::make_shared<SemanticEmbedding>(
      mu, empty_U, GROWN_CONCEPT_VARIANCE_PRIOR, label);
  math_sheaf_.attach(s, skill);

  if (!organ.empty()) {
    organ_concepts_[organ].push_back(skill);
  }

  is_collapsed_ = false;
}

std::optional<Eigen::VectorXd>
CognitiveState::compute_pi_v(const std::string &organ) const {
  std::shared_lock<std::shared_mutex> lock(math_mutex_);
  auto it = organ_concepts_.find(organ);
  if (it == organ_concepts_.end() || it->second.empty()) {
    return std::nullopt;
  }
  return fuse_concept_means(it->second);
}

std::vector<std::string> CognitiveState::active_organs() const {
  std::shared_lock<std::shared_mutex> lock(math_mutex_);
  std::vector<std::string> out;
  out.reserve(organ_concepts_.size());
  for (const auto &kv : organ_concepts_) {
    if (!kv.second.empty()) {
      out.push_back(kv.first);
    }
  }
  return out;
}

void CognitiveState::inject_chat_memory(const std::string &payload,
                                        const std::vector<float> &geometry) {
  std::lock_guard<std::shared_mutex> lock(chat_mutex_);

  topology::VertexID v = next_vertex_id_++;
  topology::Simplex chat_simplex({v});
  chat_complex_.insert(chat_simplex);

  int dim = static_cast<int>(geometry.size());

  if (embedding_dimension_ == 0) {
    embedding_dimension_ = dim;
  } else if (static_cast<size_t>(dim) != embedding_dimension_) {
    // Enforce strict memory bounds
    throw std::invalid_argument(
        "[CognitiveState] Dimension mismatch in chat memory. Expected " +
        std::to_string(embedding_dimension_) + ", got " + std::to_string(dim) +
        ".");
  }

  Eigen::VectorXd mu(dim);
  double norm_sq = 0.0;
  for (int i = 0; i < dim; ++i) {
    mu(i) = static_cast<double>(geometry[i]);
    norm_sq += mu(i) * mu(i);
  }

  double D = std::sqrt(norm_sq) + std::numeric_limits<double>::epsilon();

  Eigen::MatrixXd U(dim, 1);
  if (D > std::numeric_limits<double>::epsilon() * 2) {
    U.col(0) = mu / D;
  } else {
    U.col(0) = Eigen::VectorXd::Zero(dim);
  }

  auto embedding = std::make_shared<SemanticEmbedding>(mu, U, D, payload);
  chat_sheaf_.attach(chat_simplex, embedding);
}

void CognitiveState::apply_flow(const Eigen::VectorXf &F_deduce, float dt,
                                float lambda) {
  std::unique_lock<std::shared_mutex> lock(math_mutex_);

  const auto &simplices = math_complex_.get_simplices();
  auto it_0 = simplices.find(0);
  if (it_0 == simplices.end() || it_0->second.empty())
    return;

  size_t dim = 0;
  for (const auto &s : it_0->second) {
    if (auto sem = std::dynamic_pointer_cast<SemanticEmbedding>(
            math_sheaf_.get_skill(s))) {
      dim = sem->get_mu().size();
      break;
    }
  }
  if (dim == 0)
    return;

  Eigen::VectorXf center = (fluid_center_.size() == static_cast<int>(dim))
                               ? fluid_center_
                               : Eigen::VectorXf::Zero(dim);

  auto compute_flow = [&](const Eigen::VectorXf &state_val) -> Eigen::VectorXf {
    Eigen::VectorXf s_minus_c = state_val - center;
    float dist_sq = s_minus_c.squaredNorm();
    Eigen::VectorXf dynamic_grad = 4.0f * lambda * dist_sq * s_minus_c;

    Eigen::VectorXf f = F_deduce - dynamic_grad;

    if (P_.rows() == state_val.size()) {
      f = P_ * f;
    }
    return f;
  };

  for (const auto &s : it_0->second) {
    if (auto sem = std::dynamic_pointer_cast<SemanticEmbedding>(
            math_sheaf_.get_skill(s))) {
      Eigen::VectorXd mu_d = sem->get_mu();
      Eigen::VectorXf state_val = mu_d.cast<float>();

      Eigen::VectorXf k1 = dt * compute_flow(state_val);
      Eigen::VectorXf k2 = dt * compute_flow(state_val + 0.5f * k1);
      Eigen::VectorXf k3 = dt * compute_flow(state_val + 0.5f * k2);
      Eigen::VectorXf k4 = dt * compute_flow(state_val + k3);

      state_val += (k1 + 2.0f * k2 + 2.0f * k3 + k4) / 6.0f;
      sem->set_mu(state_val.cast<double>());
    }
  }
}

double CognitiveState::calculate_conflict_score() const {
  std::shared_lock<std::shared_mutex> lock(math_mutex_);
  return calculate_conflict_score_internal();
}

double CognitiveState::calculate_conflict_score_internal() const {
  std::vector<Eigen::VectorXd> embeddings;

  const auto &simplices = math_complex_.get_simplices();
  auto it_0 = simplices.find(0);
  if (it_0 != simplices.end()) {
    for (const auto &s : it_0->second) {
      auto skill = math_sheaf_.get_skill(s);
      if (skill) {
        if (auto sem = std::dynamic_pointer_cast<SemanticEmbedding>(skill)) {
          embeddings.push_back(sem->get_mu());
        }
      }
    }
  }

  if (embeddings.size() <= 1)
    return 0.0;

  size_t M = embeddings.size();
  size_t D = embeddings[0].size();

  for (const auto &vec : embeddings) {
    if (vec.size() != D)
      return 0.0;
  }

  Eigen::MatrixXf X(M, D);
  for (size_t i = 0; i < M; ++i) {
    for (size_t j = 0; j < D; ++j) {
      X(i, j) = static_cast<float>(embeddings[i][j]);
    }
  }

  Eigen::RowVectorXf mean = X.colwise().mean();
  X.rowwise() -= mean;

  Eigen::MatrixXf G = (X * X.transpose()) / static_cast<float>(M - 1);

  Eigen::SelfAdjointEigenSolver<Eigen::MatrixXd> solver(G.cast<double>());
  if (solver.info() != Eigen::Success) {
    // Prevent silent failure logic
    is_collapsed_ = true;
    return 0.0;
  }

  Eigen::VectorXd eigenvalues = solver.eigenvalues();

  if (eigenvalues.size() > 0) {
    return static_cast<double>(eigenvalues(eigenvalues.size() - 1));
  }

  return 0.0;
}

Eigen::VectorXf CognitiveState::get_current_state_vector() const {
  std::shared_lock<std::shared_mutex> lock(math_mutex_);
  return get_current_state_vector_internal();
}

Eigen::VectorXf CognitiveState::get_current_state_vector_internal() const {
  std::vector<Eigen::VectorXd> embeddings;
  const auto &simplices = math_complex_.get_simplices();
  auto it_0 = simplices.find(0);
  if (it_0 != simplices.end()) {
    for (const auto &s : it_0->second) {
      auto skill = math_sheaf_.get_skill(s);
      if (skill) {
        if (auto sem = std::dynamic_pointer_cast<SemanticEmbedding>(skill)) {
          embeddings.push_back(sem->get_mu());
        }
      }
    }
  }

  if (embeddings.empty())
    return Eigen::VectorXf(0);

  size_t M = embeddings.size();
  size_t D = embeddings[0].size();
  size_t N = M;

  Eigen::MatrixXd centered(N, D);
  Eigen::VectorXd mean = Eigen::VectorXd::Zero(D);
  for (size_t i = 0; i < N; ++i) {
    for (size_t j = 0; j < D; ++j) {
      centered(i, j) = embeddings[i](j);
      mean(j) += embeddings[i](j);
    }
  }
  mean /= static_cast<double>(N);
  centered.rowwise() -= mean.transpose();

  Eigen::MatrixXd G = centered * centered.transpose() / (N - 1.0);

  Eigen::SelfAdjointEigenSolver<Eigen::MatrixXd> solver(G);
  if (solver.info() != Eigen::Success) {
    is_collapsed_ = true;
    return mean.cast<float>();
  }

  Eigen::VectorXd principal_stress = solver.eigenvectors().col(N - 1);

  Eigen::VectorXf state_vector = Eigen::VectorXf::Zero(D);
  double total_weight = 0.0;

  for (size_t i = 0; i < N; ++i) {
    double weight = std::abs(centered.row(i).dot(principal_stress));
    total_weight += weight;

    Eigen::VectorXd vec_i(D);
    for (size_t j = 0; j < D; ++j) {
      vec_i(j) = embeddings[i](j);
    }
    state_vector += (weight * vec_i).cast<float>();
  }

  if (total_weight > 0.0) {
    state_vector /= static_cast<float>(total_weight);
  }

  return state_vector;
}

Eigen::VectorXf CognitiveState::get_principal_stress_vector() const {
  std::shared_lock<std::shared_mutex> lock(math_mutex_);
  return get_principal_stress_internal();
}

Eigen::VectorXf CognitiveState::get_principal_stress_internal() const {
  std::vector<Eigen::VectorXd> embeddings;
  const auto &simplices = math_complex_.get_simplices();
  auto it_0 = simplices.find(0);
  if (it_0 != simplices.end()) {
    for (const auto &s : it_0->second) {
      auto skill = math_sheaf_.get_skill(s);
      if (skill) {
        if (auto sem = std::dynamic_pointer_cast<SemanticEmbedding>(skill)) {
          embeddings.push_back(sem->get_mu());
        }
      }
    }
  }

  if (embeddings.size() <= 1)
    return Eigen::VectorXf(0);

  size_t M = embeddings.size();
  size_t D = embeddings[0].size();

  Eigen::MatrixXf X(M, D);
  for (size_t i = 0; i < M; ++i) {
    for (size_t j = 0; j < D; ++j) {
      X(i, j) = static_cast<float>(embeddings[i](j));
    }
  }

  Eigen::RowVectorXf mean = X.colwise().mean();
  X.rowwise() -= mean;

  Eigen::MatrixXf G = (X * X.transpose()) / static_cast<float>(M - 1);

  Eigen::SelfAdjointEigenSolver<Eigen::MatrixXd> solver(G.cast<double>());
  if (solver.info() != Eigen::Success) {
    is_collapsed_ = true;
    return Eigen::VectorXf::Zero(D);
  }

  Eigen::VectorXf v = solver.eigenvectors().col(M - 1).cast<float>();

  Eigen::VectorXf stress_vec = X.transpose() * v;
  if (stress_vec.norm() > 1e-6f) {
    stress_vec.normalize();
  } else {
    stress_vec = Eigen::VectorXf::Zero(D);
  }
  return stress_vec;
}

double CognitiveState::calculate_differential_entropy() const {
  std::shared_lock<std::shared_mutex> lock(math_mutex_);
  return calculate_differential_entropy_internal();
}

double CognitiveState::calculate_differential_entropy_internal() const {

  const auto &all_simplices = math_complex_.get_simplices();
  auto it = all_simplices.find(0);
  if (it == all_simplices.end()) {
    return 0.0;
  }
  const auto &vertices = it->second;

  double total_entropy = 0.0;

  for (const auto &s : vertices) {
    auto skill = math_sheaf_.get_skill(s);
    if (auto semantic = std::dynamic_pointer_cast<SemanticEmbedding>(skill)) {
      total_entropy += semantic->calculate_entropy();
    }
  }

  return total_entropy;
}

bool CognitiveState::is_attractor_reached() const {
  double H = calculate_differential_entropy();

  const auto &all_simplices = math_complex_.get_simplices();
  auto it = all_simplices.find(0);
  size_t num_vertices = 0;
  if (it != all_simplices.end()) {
    num_vertices = it->second.size();
  }
  if (num_vertices == 0)
    return false;

  if (embedding_dimension_ == 0)
    return false;

  double threshold = -1.0 * static_cast<double>(embedding_dimension_) *
                     static_cast<double>(num_vertices);

  return H < threshold;
}

} // namespace core
} // namespace mos