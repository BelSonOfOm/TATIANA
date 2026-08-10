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

    /// @brief Default retrieval width. See `get_top_k_concepts` for why 24, and
    ///        why the ceiling is 30 rather than a matter of taste.
    static constexpr std::size_t kDefaultRetrievalWidth = 24;

    /// @brief The k stored concepts nearest the current thought, nearest first.
    ///
    /// P0 (spec: `DOCS/SPEC_P0_RETRIEVAL_FIX.md`, logbook 5bb/§7). This REPLACES
    /// `get_relevant_concepts`, an absolute-threshold epsilon-ball scan that
    /// MEASUREMENT showed admits **0.31%** of author-asserted true dependencies,
    /// against **46.6%** for rank-based retrieval at the same width. It is
    /// removed rather than deprecated: a deprecated landmine is exactly how the
    /// old policy survived long enough to be measured.
    ///
    /// THREE THINGS WERE WRONG, AND THEY COMPOUNDED.
    ///
    ///  1. THE THRESHOLD WAS NOT DYNAMIC. The caller computed
    ///     `max(0.1, 1/d)`, which at d = 384 is 0.1 for every query the system
    ///     will ever see. The dimension-dependence was decorative.
    ///
    ///  2. AN ABSOLUTE CUTOFF CANNOT WORK AGAINST THE PEDESTAL. For unit-norm
    ///     means, semantic = ||mu1 - mu2||^2 = 2(1 - cos), so a cutoff of 0.1
    ///     demands cos >= 0.95. Two UNRELATED abstracts already score
    ///     cos ~ 0.669 (||mu_bar||^2 = 0.671), so the cutoff sat six times below
    ///     where unrelated pairs live: a near-duplicate filter, derived here and
    ///     measured independently in the Tier-0 chapter. The pedestal is a
    ///     THRESHOLDING problem, never a RANKING one -- for a fixed query it is
    ///     a constant and cannot reorder anything.
    ///
    ///  3. IT SELECTED ON AN UNINTERPRETABLE SUM. `WassersteinTerms::total()`
    ///     adds a d-INTENSIVE term (semantic, <= 4) to a d-EXTENSIVE one
    ///     (epistemic), and `semantic_skill.hpp:120` already warns against it.
    ///     At d = 384 the extensive term dominates, so the engine was selecting
    ///     by EPISTEMIC BREADTH rather than semantic relevance.
    ///
    /// So ranking is on `semantic` alone, computed directly as
    /// `(thought_mu - mu).squaredNorm()`. That is the SAME formula as
    /// `WassersteinTerms::semantic`, not an approximation of it.
    ///
    /// A CONSEQUENCE WORTH NAMING. `thought_D` is gone from the signature. It
    /// fed only the epistemic term, and its caller derived it as the query's
    /// NORM used as a VARIANCE -- a quantity with no derivation behind it.
    /// Ranking on `semantic` makes it inert, so one fix removes two problems.
    ///
    /// @param thought_mu Mean of the current thought. Must match stored dim.
    /// @param k Width. Rows whose dimension differs are skipped, so fewer than
    ///        k may be returned; never more.
    /// @return Up to k concepts, sorted ASCENDING by ||mu_q - mu_i||^2.
    [[nodiscard]] std::vector<std::shared_ptr<const core::SemanticEmbedding>> get_top_k_concepts(
        const Eigen::VectorXd& thought_mu,
        std::size_t k = kDefaultRetrievalWidth) const;

private:
    /// Helper to calculate the O(k^3) Bures-Wasserstein distance between isotropic and low-rank Gaussians
    double calculate_wasserstein_2_sq(const Eigen::VectorXd& mu1, double D1,
                                      const Eigen::VectorXd& mu2, const Eigen::MatrixXd& U2, double D2) const;

    mutable std::mutex mutex_;
    struct sqlite3* db_;
};

} // namespace translation
} // namespace mos
