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

private:
    math::FourierMapper fourier_mapper_;
    
    /// @brief Isotropic noise floor D from confidence: sigma^2 = -ln(c).
    /// Accepts an EMPTY optional meaning "confidence unknown", in which case an
    /// explicitly-named, warned, transitional prior is used instead of a silent
    /// fabricated value. See UNCALIBRATED_VARIANCE_PRIOR in curator.cpp.
    double compute_variance(std::optional<double> confidence) const;

    // Helper to calculate the true Bures-Wasserstein trace distance squared between isotropic thought and low-rank semantic embedding
    double calculate_wasserstein_2_sq(const Eigen::VectorXd& mu1, double D1,
                                      const Eigen::VectorXd& mu2, const Eigen::MatrixXd& U2, double D2) const;
};

} // namespace translation
} // namespace mos
