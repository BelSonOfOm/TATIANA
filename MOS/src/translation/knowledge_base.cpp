#include "mos/translation/knowledge_base.hpp"
#include "mos/core/semantic_skill.hpp"
#include "sqlite3.h"
#include <algorithm>
#include <iostream>
#include <cmath>
#include <stdexcept>
#include <cstring>
#include <utility>
#include <vector>

namespace mos {
namespace translation {

KnowledgeBase::KnowledgeBase(const std::string& db_path) : db_(nullptr) {
    if (sqlite3_open(db_path.c_str(), &db_) != SQLITE_OK) {
        throw std::runtime_error("Failed to open SQLite database: " + db_path);
    }
    
    // Schema stores the Woodbury (U, D) structure natively:
    // mu_vector: BLOB of N doubles (the mean)
    // u_matrix: BLOB of N*k doubles (the low-rank basis, column-major)
    // noise_floor: REAL (the isotropic scalar D)
    // rank: INTEGER (k, the number of columns in U)
    const char* sql = "CREATE TABLE IF NOT EXISTS distilled_theorems ("
                      "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                      "content_hash TEXT UNIQUE, "
                      "reasoning_chain TEXT, "
                      "dimension INTEGER, "
                      "rank INTEGER DEFAULT 0, "
                      "mu_vector BLOB, "
                      "u_matrix BLOB, "
                      "noise_floor REAL DEFAULT 1.0, "
                      "timestamp DATETIME DEFAULT CURRENT_TIMESTAMP);";
                      
    char* err_msg = nullptr;
    if (sqlite3_exec(db_, sql, nullptr, nullptr, &err_msg) != SQLITE_OK) {
        std::string err = err_msg;
        sqlite3_free(err_msg);
        throw std::runtime_error("Failed to create table: " + err);
    }

    int version = 0;
    sqlite3_exec(db_, "PRAGMA user_version", [](void* data, int, char** vals, char**) -> int {
        if (vals[0]) *static_cast<int*>(data) = std::atoi(vals[0]); 
        return 0;
    }, &version, nullptr);

    if (version < 1) {
        sqlite3_exec(db_, "ALTER TABLE distilled_theorems ADD COLUMN content_hash TEXT UNIQUE", nullptr, nullptr, nullptr);
        sqlite3_exec(db_, "PRAGMA user_version = 1", nullptr, nullptr, nullptr);
    }
}

KnowledgeBase::~KnowledgeBase() {
    if (db_) {
        sqlite3_close(db_);
    }
}

void KnowledgeBase::commit_concept(std::shared_ptr<const core::SemanticEmbedding> concept) {
    if (!concept) return;
    std::lock_guard<std::mutex> lock(mutex_);
    
    const char* sql = "INSERT OR REPLACE INTO distilled_theorems (content_hash, reasoning_chain, dimension, rank, mu_vector, u_matrix, noise_floor) VALUES (?, ?, ?, ?, ?, ?, ?);";
    sqlite3_stmt* stmt = nullptr;
    
    if (sqlite3_prepare_v2(db_, sql, -1, &stmt, nullptr) != SQLITE_OK) {
        std::cerr << "Failed to prepare insert statement.\n";
        return;
    }
    
    const auto& mu = concept->get_mu();
    const auto& U = concept->get_U();
    double D = concept->get_D();
    int dim = static_cast<int>(mu.size());
    int rank = static_cast<int>(U.cols());
    
    std::string hash_str = std::to_string(std::hash<std::string>{}(concept->get_name()));
    sqlite3_bind_text(stmt, 1, hash_str.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 2, concept->get_name().c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_int(stmt, 3, dim);
    sqlite3_bind_int(stmt, 4, rank);
    sqlite3_bind_blob(stmt, 5, reinterpret_cast<const void*>(mu.data()), dim * sizeof(double), SQLITE_TRANSIENT);
    
    if (rank > 0) {
        // U is stored column-major by Eigen, so U.data() gives us N*k doubles contiguously
        sqlite3_bind_blob(stmt, 6, reinterpret_cast<const void*>(U.data()), dim * rank * sizeof(double), SQLITE_TRANSIENT);
    } else {
        sqlite3_bind_null(stmt, 6);
    }
    
    sqlite3_bind_double(stmt, 7, D);
    
    if (sqlite3_step(stmt) != SQLITE_DONE) {
        std::cerr << "Failed to execute insert statement.\n";
    }
    
    sqlite3_finalize(stmt);
}

std::vector<std::shared_ptr<const core::SemanticEmbedding>> KnowledgeBase::get_all_concepts() const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<std::shared_ptr<const core::SemanticEmbedding>> results;
    
    const char* sql = "SELECT reasoning_chain, dimension, rank, mu_vector, u_matrix, noise_floor FROM distilled_theorems;";
    sqlite3_stmt* stmt = nullptr;
    
    if (sqlite3_prepare_v2(db_, sql, -1, &stmt, nullptr) != SQLITE_OK) {
        return results;
    }
    
    while (sqlite3_step(stmt) == SQLITE_ROW) {
        std::string reasoning = reinterpret_cast<const char*>(sqlite3_column_text(stmt, 0));
        int stored_dim = sqlite3_column_int(stmt, 1);
        int stored_rank = sqlite3_column_int(stmt, 2);
        
        // Deserialize mu
        int mu_bytes = sqlite3_column_bytes(stmt, 3);
        const void* mu_blob = sqlite3_column_blob(stmt, 3);
        if (mu_bytes != stored_dim * static_cast<int>(sizeof(double))) continue;
        Eigen::VectorXd mu(stored_dim);
        std::memcpy(mu.data(), mu_blob, mu_bytes);
        
        // Deserialize U
        Eigen::MatrixXd U(stored_dim, stored_rank);
        if (stored_rank > 0) {
            int u_bytes = sqlite3_column_bytes(stmt, 4);
            const void* u_blob = sqlite3_column_blob(stmt, 4);
            if (u_bytes != stored_dim * stored_rank * static_cast<int>(sizeof(double))) continue;
            std::memcpy(U.data(), u_blob, u_bytes);
        }
        
        // Deserialize D
        double D = sqlite3_column_double(stmt, 5);
        if (D <= 0.0) D = 1e-9; // Clamp to prevent construction failure
        
        results.push_back(std::make_shared<core::SemanticEmbedding>(mu, U, D, reasoning));
    }
    
    sqlite3_finalize(stmt);
    return results;
}

double KnowledgeBase::calculate_wasserstein_2_sq(const Eigen::VectorXd& mu1, double D1,
                                                  const Eigen::VectorXd& mu2, const Eigen::MatrixXd& U2, double D2) const {
    // E4: delegates to core::wasserstein_2_terms, the single source of truth.
    // curator.cpp used to carry a byte-identical private copy of this formula.
    // Retained as a scalar for the existing epsilon-ball callers; prefer
    // wasserstein_2_terms() and threshold the two parts SEPARATELY -- see the
    // WassersteinTerms docs for why summing a d-intensive and a d-extensive
    // quantity makes the sum uninterpretable.
    return core::wasserstein_2_terms(mu1, D1, mu2, U2, D2).total();
}

std::vector<std::shared_ptr<const core::SemanticEmbedding>> KnowledgeBase::get_top_k_concepts(
        const Eigen::VectorXd& thought_mu,
        std::size_t k) const {

    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<std::shared_ptr<const core::SemanticEmbedding>> results;
    if (k == 0) return results;

    // A MAX-heap of the k BEST-SO-FAR. The largest score sits on top, so the
    // worst survivor is the one that gets evicted, and heap.front().first is the
    // admission price once the heap is full. Bounded at k, so memory does not
    // grow with the store the way the old unbounded threshold scan's did.
    using Scored = std::pair<double, std::shared_ptr<const core::SemanticEmbedding>>;
    const auto worse = [](const Scored& a, const Scored& b) { return a.first < b.first; };
    std::vector<Scored> heap;
    heap.reserve(k + 1);

    const char* sql = "SELECT reasoning_chain, dimension, rank, mu_vector, u_matrix, noise_floor FROM distilled_theorems;";
    sqlite3_stmt* stmt = nullptr;

    if (sqlite3_prepare_v2(db_, sql, -1, &stmt, nullptr) != SQLITE_OK) {
        return results;
    }

    while (sqlite3_step(stmt) == SQLITE_ROW) {
        int stored_dim = sqlite3_column_int(stmt, 1);

        // Fast dimension rejection
        if (stored_dim != static_cast<int>(thought_mu.size())) continue;

        int mu_bytes = sqlite3_column_bytes(stmt, 3);
        const void* mu_blob = sqlite3_column_blob(stmt, 3);
        if (mu_bytes != stored_dim * static_cast<int>(sizeof(double))) continue;
        Eigen::VectorXd mu(stored_dim);
        std::memcpy(mu.data(), mu_blob, mu_bytes);

        // THE SCORE IS NEGATIVE COSINE, AND THE CHOICE IS LOAD-BEARING.
        //
        // The obvious score is the d-intensive Wasserstein term,
        // semantic = ||mu_q - mu_i||^2. It is WRONG here, and only by an
        // assumption that does not hold:
        //
        //     ||mu_q - mu_i||^2 = ||mu_q||^2 - 2<mu_q, mu_i> + ||mu_i||^2
        //
        // For a fixed query ||mu_q||^2 is constant and drops out of the ranking,
        // but ||mu_i||^2 does NOT. Squared distance reproduces a cosine ranking
        // ONLY IF every stored mean is unit-norm -- and stored means are not.
        // pi_v is a WEIGHTED CENTROID of unit vectors (module_vertex.py,
        // Construction 2), whose norm falls below 1 and falls further the more
        // spread the concepts it summarises. The ||mu_i||^2 term would then act
        // as a per-concept penalty proportional to how BROAD a concept is,
        // pushing exactly the general concepts down the list for a reason that
        // has nothing to do with the query.
        //
        // recall@30 = 46.6% was MEASURED on a cosine ranking
        // (measure_reference_recall.py, transform `raw`). Ranking by cosine is
        // therefore provably the same ordering that was measured; ranking by
        // squared distance is a different ordering with an unmeasured bias.
        //
        // Degenerate norms cannot rank. A zero vector has no direction, so it is
        // dropped rather than given an arbitrary score -- the same refusal
        // embeddings.py makes rather than padding a short vector.
        const double q_norm = thought_mu.norm();
        const double mu_norm = mu.norm();
        if (q_norm <= 0.0 || mu_norm <= 0.0) continue;
        const double score = -thought_mu.dot(mu) / (q_norm * mu_norm);

        // Rows that cannot win are dropped BEFORE the expensive columns are
        // touched. U costs O(d * rank) to deserialise and the reasoning chain is
        // a whole string; neither is needed to know this row loses.
        if (heap.size() == k && score >= heap.front().first) continue;

        int stored_rank = sqlite3_column_int(stmt, 2);
        Eigen::MatrixXd U(stored_dim, stored_rank);
        if (stored_rank > 0) {
            int u_bytes = sqlite3_column_bytes(stmt, 4);
            const void* u_blob = sqlite3_column_blob(stmt, 4);
            if (u_bytes != stored_dim * stored_rank * static_cast<int>(sizeof(double))) continue;
            std::memcpy(U.data(), u_blob, u_bytes);
        }

        double D = sqlite3_column_double(stmt, 5);
        if (D <= 0.0) D = 1e-9;

        const unsigned char* reasoning_text = sqlite3_column_text(stmt, 0);
        std::string reasoning = reasoning_text ? reinterpret_cast<const char*>(reasoning_text) : "";

        heap.emplace_back(score, std::make_shared<core::SemanticEmbedding>(mu, U, D, reasoning));
        std::push_heap(heap.begin(), heap.end(), worse);
        if (heap.size() > k) {
            std::pop_heap(heap.begin(), heap.end(), worse);
            heap.pop_back();
        }
    }

    sqlite3_finalize(stmt);

    // sort_heap on a max-heap leaves ASCENDING order, which is nearest-first.
    std::sort_heap(heap.begin(), heap.end(), worse);
    results.reserve(heap.size());
    for (auto& scored : heap) results.push_back(std::move(scored.second));
    return results;
}

} // namespace translation
} // namespace mos
