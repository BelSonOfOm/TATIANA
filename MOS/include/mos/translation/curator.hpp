#pragma once

#include "mos/core/operad.hpp"
#include "mos/core/thread_pool.hpp"
#include "mos/math/fourier.hpp"
#include "mos/translation/llm_interface.hpp"
#include <string>
#include <memory>
#include <vector>
#include <Eigen/Dense>

namespace mos {
namespace translation {

/// @brief Curates agent thoughts into topological Operads via a Vietoris-Rips complex using 2-Wasserstein Distance.
class AgentCurator {
public:
    /// @brief Initialize with a Fourier mapper for spectral embeddings.
    AgentCurator(math::FourierMapper mapper);

    /// @brief Projects a new AgentThought into the CognitiveState and forms edges via Wasserstein threshold.
    /// @param new_thought The parsed reasoning chain and latent from the agent.
    /// @param state The current global cognitive state.
    /// @param new_vertex_id The vertex ID to assign to the new thought.
    /// @param epsilon The 2-Wasserstein distance threshold for edge formation.
    /// @param pool Optional ThreadPool for parallelizing O(N^3) Wasserstein metric
    /// @return A populated Operad containing the vertex and its Vietoris-Rips edges.
    std::shared_ptr<core::Operad> curate(const AgentThought& new_thought, const core::CognitiveState& state, size_t new_vertex_id, double epsilon, core::ThreadPool* pool = nullptr);

    /// @brief The stalk noise floor D. Since FIX-13 this is the shared O(1/d)
    /// shrinkage floor `core::stalk_floor(d, n_eff=1)` and is **NOT a function of
    /// `confidence`** — an isotropic variance in d dimensions is the wrong
    /// destination for a scalar confidence, because the Bures term it feeds is
    /// d-EXTENSIVE while the semantic term is d-INTENSIVE and bounded by 4.
    /// Per Q9 a reported confidence belongs in the edge precision pi_e, where
    /// `core::report_variance` scales it by 1/d for the same reason.
    ///
    /// `confidence` stays in the signature because the caller still carries it
    /// onward toward pi_e; this function ignores it and warns once if it is
    /// absent.
    ///
    /// PUBLIC so `tests/test_stalk_floor.cpp` can pin the contract (FIX-17).
    /// It was held by a comment alone, and a comment is what regresses: the
    /// `.tex` drifted back to describing `D = -ln c` for four days with nothing
    /// failing. The invariant is now executable.
    ///
    /// @param d The embedding dimension; passed explicitly, never inferred.
    double compute_variance(std::optional<double> confidence, int d) const;

private:
    math::FourierMapper fourier_mapper_;

    // Helper to calculate the true Bures-Wasserstein trace distance squared between isotropic thought and low-rank semantic embedding
    double calculate_wasserstein_2_sq(const Eigen::VectorXd& mu1, double D1,
                                      const Eigen::VectorXd& mu2, const Eigen::MatrixXd& U2, double D2) const;
};

} // namespace translation
} // namespace mos
