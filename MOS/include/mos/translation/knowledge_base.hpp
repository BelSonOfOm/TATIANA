#pragma once

#include "mos/core/semantic_skill.hpp"
#include <vector>
#include <memory>
#include <mutex>
#include <Eigen/Dense>

// Forward declaration of SQLite handle
struct sqlite3;

namespace mos {
namespace translation {

/// @brief A persistent memory store for crystallized theorems and concepts.
/// Stores the Woodbury low-rank (U, D) representation natively.
class KnowledgeBase {
public:
    /// @brief Default constructor. Opens or creates the SQLite database.
    KnowledgeBase(const std::string& db_path = "mos_brain.db");

    /// @brief Destructor. Closes the SQLite database.
    ~KnowledgeBase();

    // Delete copy/move to prevent accidental DB closures
    KnowledgeBase(const KnowledgeBase&) = delete;
    KnowledgeBase& operator=(const KnowledgeBase&) = delete;

    /// @brief Saves a distilled semantic embedding to the knowledge base (SQLite BLOB).
    /// @param concept The crystallized concept to store.
    void commit_concept(std::shared_ptr<const core::SemanticEmbedding> concept);

    /// @brief Retrieves all committed concepts.
    /// @return A vector of the stored concepts.
    [[nodiscard]] std::vector<std::shared_ptr<const core::SemanticEmbedding>> get_all_concepts() const;

    /// @brief Retrieves only the concepts that fall within the Wasserstein distance of the current thought.
    /// @param thought_mu The Fourier-projected mean of the current thought.
    /// @param thought_D The isotropic variance (noise floor) of the current thought.
    /// @param epsilon_w2 The maximum 2-Wasserstein distance (SQUARED).
    ///        Renamed per C6-2; see plasticity.hpp THE THREE EPSILONS.
    /// @return A vector of geometrically relevant axioms.
    [[nodiscard]] std::vector<std::shared_ptr<const core::SemanticEmbedding>> get_relevant_concepts(
        const Eigen::VectorXd& thought_mu, 
        double thought_D, 
        double epsilon_w2) const;

private:
    /// Helper to calculate the O(k^3) Bures-Wasserstein distance between isotropic and low-rank Gaussians
    double calculate_wasserstein_2_sq(const Eigen::VectorXd& mu1, double D1,
                                      const Eigen::VectorXd& mu2, const Eigen::MatrixXd& U2, double D2) const;

    mutable std::mutex mutex_;
    struct sqlite3* db_;
};

} // namespace translation
} // namespace mos
