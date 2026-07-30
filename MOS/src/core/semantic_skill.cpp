#include "mos/core/semantic_skill.hpp"
#include <algorithm>
#include <stdexcept>
#include <sstream>
#include <iostream>
#include <cmath>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#ifndef M_E
#define M_E 2.71828182845904523536
#endif

namespace mos {
namespace core {

/// Fraction of spectral energy we are willing to discard when truncating the
/// low-rank covariance basis U. Smaller => more rank retained => more rigor,
/// more compute. Named so the tolerance is explicit and tunable.
static constexpr double SPECTRAL_TRUNCATION_EPSILON = 0.05;

SemanticEmbedding::SemanticEmbedding(Eigen::VectorXd mu, Eigen::MatrixXd U, double D, std::string name)
    : mu_(std::move(mu)), U_(std::move(U)), D_(D), name_(std::move(name)) {
    if (U_.rows() > 0 && mu_.size() != U_.rows()) {
        throw std::invalid_argument("Mean vector and U matrix must have compatible dimensions");
    }
    if (D_ <= 0.0) {
        throw std::invalid_argument("Noise floor D must be strictly positive");
    }
}

std::string SemanticEmbedding::description() const {
    std::stringstream ss;
    ss << "SemanticEmbedding(Name: " << name_ << ", Dim: " << mu_.size() << ", Rank: " << U_.cols() << ")";
    return ss.str();
}

void SemanticEmbedding::merge_with(const ProceduralSkill& other) {
    const auto* other_embedding = dynamic_cast<const SemanticEmbedding*>(&other);
    if (!other_embedding) {
        throw std::invalid_argument("Cannot merge SemanticEmbedding with a different ProceduralSkill type");
    }

    if (mu_.size() != other_embedding->get_mu().size()) {
        throw std::invalid_argument("Cannot merge embeddings of different dimensions");
    }

    // 1. Woodbury Low-Rank Bayesian Fusion
    double D1 = D_;
    double D2 = other_embedding->get_D();
    double D_new = (D1 * D2) / (D1 + D2);
    double c = 1.0 / D1 + 1.0 / D2;

    int N = mu_.size();
    int k1 = U_.cols();
    int k2 = other_embedding->get_U().cols();
    
    // Compute P1 * mu1
    Eigen::VectorXd y1 = mu_ / D1;
    Eigen::MatrixXd M1_inv(k1, k1);
    Eigen::MatrixXd M1(k1, k1);
    if (k1 > 0) {
        Eigen::MatrixXd UtU = U_.transpose() * U_;
        M1_inv = -D1 * D1 * Eigen::MatrixXd::Identity(k1, k1) - D1 * UtU;
        // Tikhonov regularization to prevent singularity
        double reg1 = std::numeric_limits<double>::epsilon() * M1_inv.norm();
        M1 = (M1_inv + reg1 * Eigen::MatrixXd::Identity(k1, k1)).inverse();
        y1 += U_ * (M1 * (U_.transpose() * mu_));
    }

    // Compute P2 * mu2
    Eigen::VectorXd y2 = other_embedding->get_mu() / D2;
    Eigen::MatrixXd M2_inv(k2, k2);
    Eigen::MatrixXd M2(k2, k2);
    if (k2 > 0) {
        Eigen::MatrixXd UtU = other_embedding->get_U().transpose() * other_embedding->get_U();
        M2_inv = -D2 * D2 * Eigen::MatrixXd::Identity(k2, k2) - D2 * UtU;
        // Tikhonov regularization to prevent singularity
        double reg2 = std::numeric_limits<double>::epsilon() * M2_inv.norm();
        M2 = (M2_inv + reg2 * Eigen::MatrixXd::Identity(k2, k2)).inverse();
        y2 += other_embedding->get_U() * (M2 * (other_embedding->get_U().transpose() * other_embedding->get_mu()));
    }

    Eigen::VectorXd y = y1 + y2;

    // Compute Exact Rank Subspace U_exact
    Eigen::MatrixXd U_exact(N, 0);
    if (k1 + k2 > 0) {
        Eigen::MatrixXd V(N, k1 + k2);
        if (k1 > 0) V.leftCols(k1) = U_;
        if (k2 > 0) V.rightCols(k2) = other_embedding->get_U();

        Eigen::MatrixXd M_inv = Eigen::MatrixXd::Zero(k1 + k2, k1 + k2);
        if (k1 > 0) M_inv.topLeftCorner(k1, k1) = M1_inv;
        if (k2 > 0) M_inv.bottomRightCorner(k2, k2) = M2_inv;

        Eigen::MatrixXd VtV = V.transpose() * V;
        Eigen::MatrixXd K = M_inv + (1.0 / c) * VtV;
        // Tikhonov regularization for K inversion
        double reg_k = std::numeric_limits<double>::epsilon() * K.norm();
        Eigen::MatrixXd W = - (1.0 / (c * c)) * (K + reg_k * Eigen::MatrixXd::Identity(K.rows(), K.cols())).inverse();

        // W is symmetric positive semi-definite
        Eigen::SelfAdjointEigenSolver<Eigen::MatrixXd> es(W);
        Eigen::MatrixXd A = es.eigenvectors() * es.eigenvalues().cwiseMax(0.0).cwiseSqrt().asDiagonal();
        
        U_exact = V * A;
    }

    // Exact Woodbury Mean
    Eigen::VectorXd mu_new = D_new * y;
    if (U_exact.cols() > 0) {
        mu_new += U_exact * (U_exact.transpose() * y);
    }

    // Dynamic SVD Truncation based on cumulative energy
    Eigen::MatrixXd U_new = U_exact;
    if (U_new.cols() > 0) {
        Eigen::JacobiSVD<Eigen::MatrixXd> svd(U_new, Eigen::ComputeThinU | Eigen::ComputeThinV);
        Eigen::VectorXd singular_values = svd.singularValues();
        
        double total_variance = singular_values.array().square().sum();
        double current_variance = 0.0;
        int dynamic_k = 0;

        // Error-driven dynamic rank: keep the smallest k whose retained spectral
        // energy exceeds (1 - SPECTRAL_TRUNCATION_EPSILON). The threshold is NAMED
        // rather than a bare 0.95 literal so the discarded-energy tolerance is an
        // explicit, tunable parameter instead of a hidden magic number.
        for (int i = 0; i < singular_values.size(); ++i) {
            current_variance += singular_values(i) * singular_values(i);
            dynamic_k++;
            if (current_variance / total_variance >= 1.0 - SPECTRAL_TRUNCATION_EPSILON) {
                break;
            }
        }
        
        U_new = svd.matrixU().leftCols(dynamic_k) * singular_values.head(dynamic_k).asDiagonal();
    }

    mu_ = std::move(mu_new);
    U_ = std::move(U_new);
    D_ = D_new;
    name_ += " & " + other_embedding->get_name();
}

double SemanticEmbedding::calculate_entropy() const {
    double N = static_cast<double>(mu_.size());
    int k = U_.cols();
    
    // Matrix Determinant Lemma: det(D*I + U*U^T) = det(D*I) * det(I_k + U^T * (D*I)^{-1} * U)
    // = D^{N} * det(I_k + U^T U / D)
    // det = D^{N-k} * det(D*I_k + U^T U)
    
    double h = (N - k) * std::log(2.0 * M_PI * M_E * D_);
    
    if (k > 0) {
        Eigen::MatrixXd UtU = U_.transpose() * U_;
        Eigen::SelfAdjointEigenSolver<Eigen::MatrixXd> es(UtU);
        for (int i = 0; i < k; ++i) {
            h += std::log(2.0 * M_PI * M_E * (D_ + std::max(0.0, es.eigenvalues()(i))));
        }
    }
    return 0.5 * h;
}

Eigen::VectorXd fuse_concept_means(
    const std::vector<std::shared_ptr<const SemanticEmbedding>> &concepts,
    double d_floor) {
  if (concepts.empty()) {
    throw std::invalid_argument("fuse_concept_means: no concepts to fuse");
  }
  const Eigen::Index d = concepts.front()->get_mu().size();
  for (const auto &c : concepts) {
    if (c->get_mu().size() != d) {
      throw std::invalid_argument(
          "fuse_concept_means: inconsistent concept dimensions");
    }
  }

  // Is every concept isotropic (rank 0)? Then the exact answer needs no inversion.
  bool all_isotropic = true;
  for (const auto &c : concepts) {
    if (c->get_U().cols() > 0) {
      all_isotropic = false;
      break;
    }
  }

  if (all_isotropic) {
    // Scalar precision-weighted average: mu* = (sum p_i mu_i) / (sum p_i),
    // p_i = 1 / max(D_i, d_floor). Exact for isotropic Sigma_i = D_i I.
    double precision_sum = 0.0;
    Eigen::VectorXd y = Eigen::VectorXd::Zero(d);
    for (const auto &c : concepts) {
      const double p = 1.0 / std::max(c->get_D(), d_floor);
      precision_sum += p;
      y.noalias() += p * c->get_mu();
    }
    return y / precision_sum;
  }

  // General case (EXACT): accumulate the dense information matrix
  //   Lambda = sum_i Sigma_i^{-1},   y = sum_i Sigma_i^{-1} mu_i
  // with Sigma_i^{-1} obtained via Woodbury for the low-rank-plus-diagonal form:
  //   (U U^T + D I)^{-1} = D^{-1} I - D^{-1} U (I_k + U^T U / D)^{-1} U^T D^{-1}.
  Eigen::MatrixXd Lambda = Eigen::MatrixXd::Zero(d, d);
  Eigen::VectorXd y = Eigen::VectorXd::Zero(d);
  for (const auto &c : concepts) {
    const double D = std::max(c->get_D(), d_floor);
    const Eigen::MatrixXd &U = c->get_U();
    const Eigen::Index k = U.cols();

    Eigen::MatrixXd Sinv = (1.0 / D) * Eigen::MatrixXd::Identity(d, d);
    if (k > 0) {
      Eigen::MatrixXd M =
          Eigen::MatrixXd::Identity(k, k) + (U.transpose() * U) / D;
      // U M^{-1} U^T, solved rather than inverted for stability.
      Eigen::MatrixXd UMUt = U * M.ldlt().solve(U.transpose());
      Sinv.noalias() -= (1.0 / (D * D)) * UMUt;
    }
    Lambda.noalias() += Sinv;
    y.noalias() += Sinv * c->get_mu();
  }
  return Lambda.ldlt().solve(y);
}

// --------------------------------------------------------------------------
// E4: W_2^2 in its two parts. Single source of truth -- knowledge_base.cpp and
// curator.cpp previously carried byte-identical private copies of this formula.
// --------------------------------------------------------------------------
WassersteinTerms wasserstein_2_terms(const Eigen::VectorXd &mu1, double D1,
                                     const Eigen::VectorXd &mu2,
                                     const Eigen::MatrixXd &U2, double D2) {
  if (mu1.size() != mu2.size()) {
    throw std::invalid_argument(
        "wasserstein_2_terms: mean dimensions disagree (" +
        std::to_string(mu1.size()) + " vs " + std::to_string(mu2.size()) +
        "). Refusing to pad or truncate.");
  }

  WassersteinTerms out;

  // --- semantic: WHAT the two concepts say. d-intensive. -------------------
  out.semantic = (mu1 - mu2).squaredNorm();

  // --- epistemic: HOW SURE they are. The squared Bures distance between the
  // covariances, d-extensive. Exact for isotropic Sigma1 = D1*I:
  //   Sigma1^{1/2} Sigma2 Sigma1^{1/2} = D1 * Sigma2,  so
  //   tr[(Sigma1^{1/2} Sigma2 Sigma1^{1/2})^{1/2}] = sqrt(D1) * tr(Sigma2^{1/2}).
  // The eigenvalues of Sigma2 = U2 U2^T + D2*I are (sigma_j^2 + D2) on im(U2)
  // -- the nonzero eigenvalues of U2 U2^T equal those of U2^T U2 -- and D2 with
  // multiplicity (d - k) on ker(U2^T). Hence only a k x k eigendecomposition.
  const double d = static_cast<double>(mu1.size());
  const int k = static_cast<int>(U2.cols());

  double trace_Sigma1 = d * D1;
  double trace_Sigma2 = d * D2;
  double trace_Sigma2_sqrt = (d - static_cast<double>(k)) * std::sqrt(D2);
  if (k > 0) {
    const Eigen::MatrixXd UtU = U2.transpose() * U2;
    trace_Sigma2 += UtU.trace();
    Eigen::SelfAdjointEigenSolver<Eigen::MatrixXd> es(UtU);
    for (int i = 0; i < k; ++i) {
      trace_Sigma2_sqrt += std::sqrt(D2 + std::max(0.0, es.eigenvalues()(i)));
    }
  }
  const double cross = std::sqrt(D1) * trace_Sigma2_sqrt;

  // Mathematically >= 0 (it is a squared Bures distance). A negative value here
  // is float cancellation between three O(d*D) terms, not a real quantity -- so
  // clamp, but never clamp the semantic term, which cannot go negative.
  out.epistemic = std::max(0.0, trace_Sigma1 + trace_Sigma2 - 2.0 * cross);

  return out;
}

// --- FIX-13: the stalk noise-floor contract (see semantic_skill.hpp) --------

double stalk_floor(int d, double n_eff, double kappa) {
  if (d <= 0) {
    throw std::invalid_argument(
        "[stalk_floor] embedding dimension must be positive, got " +
        std::to_string(d));
  }
  if (n_eff < 1.0) {
    throw std::invalid_argument(
        "[stalk_floor] n_eff must be at least 1 (one observation is one "
        "observation), got " + std::to_string(n_eff));
  }
  if (kappa <= 0.0) {
    throw std::invalid_argument(
        "[stalk_floor] prior pseudo-count kappa must be positive, got " +
        std::to_string(kappa));
  }
  // Sigma_0 = (1/d) I has trace 1, so its contribution to the floor is
  // kappa / (d * (n_eff + kappa)) -- O(1/d), which is what keeps trace O(1).
  return EPS_FLOOR + kappa / (static_cast<double>(d) * (n_eff + kappa));
}

double max_epistemic_trace(int d, double eps) {
  if (d <= 0) {
    throw std::invalid_argument(
        "[max_epistemic_trace] embedding dimension must be positive, got " +
        std::to_string(d));
  }
  if (eps <= 0.0) {
    throw std::invalid_argument(
        "[max_epistemic_trace] floor must be positive, got " +
        std::to_string(eps));
  }
  // Exact solution of d*(sqrt(eps + t/d) - sqrt(eps))^2 = 4 for t.
  // MAX_SEMANTIC_DISTANCE_SQ = 4 is not a tuning knob: it is the largest
  // possible ||mu1 - mu2||^2 between two unit-norm embeddings (antipodal).
  constexpr double MAX_SEMANTIC_DISTANCE_SQ = 4.0;
  const double root = std::sqrt(MAX_SEMANTIC_DISTANCE_SQ);
  return MAX_SEMANTIC_DISTANCE_SQ +
         2.0 * root * std::sqrt(eps * static_cast<double>(d));
}

void assert_e4_budget(int d, double D_lo, double D_hi) {
  if (d <= 0) {
    throw std::invalid_argument(
        "[assert_e4_budget] embedding dimension must be positive, got " +
        std::to_string(d));
  }
  if (D_lo <= 0.0 || D_hi <= 0.0) {
    throw std::invalid_argument(
        "[assert_e4_budget] stalk floors must be positive");
  }
  if (D_hi < D_lo) {
    std::swap(D_lo, D_hi);
  }
  const double bures =
      static_cast<double>(d) * std::pow(std::sqrt(D_hi) - std::sqrt(D_lo), 2.0);
  if (bures > 4.0) {
    std::ostringstream oss;
    oss << "[assert_e4_budget] Stalk floors span [" << D_lo << ", " << D_hi
        << "], giving an epistemic Bures term of " << bures << " at d=" << d
        << ". That exceeds the maximum possible semantic distance (4), so "
           "confidence would outweigh meaning -- exactly the E4 failure. "
           "Floors must be O(1/d).";
    throw std::invalid_argument(oss.str());
  }
}

} // namespace core
} // namespace mos
