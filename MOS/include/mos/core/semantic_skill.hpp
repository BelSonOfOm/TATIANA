#pragma once

#include "mos/core/cognitive_state.hpp"
#include <vector>
#include <string>
#include <Eigen/Dense>

namespace mos {
namespace core {

/// @brief A fixed-dimension semantic embedding vector representing concept meaning.
/// @brief A specific implementation of a procedural skill that holds
/// a probabilistic semantic state (mean and variance).
class SemanticEmbedding : public ProceduralSkill {
public:
    /// @brief Constructs a new probabilistic semantic embedding.
    /// @param mu The mean vector (core semantic meaning or Fourier features).
    /// @param U The N x k basis matrix representing structured low-rank covariance.
    /// @param D The scalar noise floor (isotropic variance).
    /// @param name The human-readable name of the concept.
    SemanticEmbedding(Eigen::VectorXd mu, Eigen::MatrixXd U, double D, std::string name);

    /// @brief Gets the description of the embedding.
    [[nodiscard]] std::string description() const override;

    /// @brief Performs a Bayesian Update to merge this embedding with another.
    /// Mathematically pulls the mean towards the lower-variance embedding, and shrinks the total variance.
    void merge_with(const ProceduralSkill& other) override;

    /// @brief Gets the mean vector (mu).
    [[nodiscard]] const Eigen::VectorXd& get_mu() const noexcept { return mu_; }

    /// @brief Sets the mean vector (mu), used for explicit Lagrangian state flow mutations.
    void set_mu(Eigen::VectorXd new_mu) noexcept { mu_ = std::move(new_mu); }

    /// @brief Gets the low-rank basis matrix (U).
    [[nodiscard]] const Eigen::MatrixXd& get_U() const noexcept { return U_; }

    /// @brief Gets the scalar noise floor (D).
    [[nodiscard]] double get_D() const noexcept { return D_; }

    /// @brief Gets the name of the concept.
    [[nodiscard]] const std::string& get_name() const noexcept { return name_; }

    /// @brief Calculates the exact differential entropy using the Matrix Determinant Lemma without dense expansion.
    [[nodiscard]] double calculate_entropy() const;

private:
    Eigen::VectorXd mu_;
    Eigen::MatrixXd U_;
    double D_;
    std::string name_;
};

/// @brief Precision-weighted fusion of several concept means (Construction 2, pi_v).
///
/// Treats the given concepts as independent Gaussian estimates N(mu_i, Sigma_i),
/// Sigma_i = U_i U_i^T + D_i I, of one underlying quantity (an organ's position),
/// and returns the maximum-likelihood fused mean
///
///     mu* = (sum_i Sigma_i^{-1})^{-1} (sum_i Sigma_i^{-1} mu_i).
///
/// Each concept pulls mu* toward itself in proportion to its PRECISION, so a
/// certain concept (small D) dominates and an uncertain one barely moves it. This
/// is the n-way generalisation of what SemanticEmbedding::merge_with does pairwise
/// — but NON-DESTRUCTIVE: it reads the concepts and never mutates them.
///
///  * Fast path (EXACT): when every U_i is empty (rank 0), Sigma_i^{-1} = I/D_i and
///    the whole thing collapses to a scalar precision-weighted average, O(n*d),
///    no matrix inversion. This is the current reality of every grown concept.
///  * General path (EXACT): otherwise, accumulates the dense information matrix via
///    the Woodbury identity per term and solves once. O(n*d*k + d^3).
///
/// @param concepts Non-empty, homogeneous-dimension concept embeddings.
/// @param d_floor  Lower bound on each D_i, so a near-certain axiom (D ~ eps) cannot
///                 blow the precision up to ~1e16 and swamp everything numerically.
/// @throws std::invalid_argument if concepts is empty or dimensions disagree.
[[nodiscard]] Eigen::VectorXd fuse_concept_means(
    const std::vector<std::shared_ptr<const SemanticEmbedding>> &concepts,
    double d_floor = 1e-6);

// --------------------------------------------------------------------------
// E4 (audit 2026-07-27): the 2-Wasserstein distance, REPORTED IN ITS TWO PARTS
// --------------------------------------------------------------------------
/// @brief The two halves of W_2^2 between N(mu1, D1*I) and N(mu2, U2 U2^T + D2*I).
///
/// WHY THIS IS SPLIT, AND WHY SUMMING THEM IS A CATEGORY ERROR
/// -----------------------------------------------------------
/// W_2^2 = ||mu1 - mu2||^2  +  Bures^2(Sigma1, Sigma2)
///         \_____________/     \________________________/
///           `semantic`             `epistemic`
///        WHAT the concepts say   HOW SURE they are
///
/// These are not commensurable, and it is a dimensional fact, not a modelling
/// preference:
///   * `semantic` is d-INTENSIVE. For unit-normalised embeddings it is bounded
///     by 4 (attained only at antipodes) regardless of d.
///   * `epistemic` is d-EXTENSIVE. In the isotropic case it equals exactly
///     d * (sqrt(D1) - sqrt(D2))^2, so it grows linearly in the embedding
///     dimension for a FIXED disagreement about certainty.
///
/// At the deployed d = 384, an uncalibrated prior D1 = 1.0 against a confident
/// concept (c = 0.95 => D2 = -ln 0.95 = 0.0513) gives
///     epistemic = 384 * (1 - 0.2265)^2 ~= 230,   semantic <= 4.
/// The certainty term outweighs meaning by roughly 57 to 1, and it is driven by
/// a self-reported LLM confidence the architecture elsewhere declines to trust.
/// Adding them and thresholding the sum therefore makes merge/split decisions
/// almost entirely a function of confidence, not content.
///
/// THE LATENT-BUG PROPERTY. Today every grown concept carries D = 1.0 with empty
/// U, so `epistemic` is IDENTICALLY ZERO and W_2^2 degenerates exactly to squared
/// Euclidean distance -- the optimal-transport machinery is currently inert. The
/// hazard above switches on the moment calibration is fixed, i.e. it is worst
/// precisely when the system is improved. Reporting the terms separately is what
/// makes that visible before it fires.
///
/// Callers should threshold the two terms SEPARATELY: two concepts saying the
/// same thing with different confidence should merge; two concepts saying
/// different things with the same confidence should not.
struct WassersteinTerms {
  double semantic{0.0};   ///< ||mu1 - mu2||^2   (d-intensive; <= 4 if unit-norm)
  double epistemic{0.0};  ///< Bures^2 between the covariances (d-extensive)

  /// The classical scalar W_2^2. Retained for backward compatibility ONLY;
  /// prefer thresholding the two fields independently.
  [[nodiscard]] double total() const noexcept { return semantic + epistemic; }
};

/// @brief Exact Bures-Wasserstein between isotropic D1*I and low-rank
/// U2 U2^T + D2*I, returned as its two separately-meaningful parts.
///
/// Exact (not a diagonal approximation) and O(d k^2 + k^3): only the k x k
/// matrix U2^T U2 is eigendecomposed, never the d x d covariance. The epistemic
/// part is clamped at zero -- it is a squared Bures distance and so mathematically
/// non-negative; any negative value is floating-point cancellation in the
/// tr Sigma1 + tr Sigma2 - 2 tr(...) expression, not a real quantity.
[[nodiscard]] WassersteinTerms wasserstein_2_terms(const Eigen::VectorXd &mu1, double D1,
                                                   const Eigen::VectorXd &mu2,
                                                   const Eigen::MatrixXd &U2, double D2);

} // namespace core
} // namespace mos
