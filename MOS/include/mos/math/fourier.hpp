#pragma once

#include <vector>
#include <random>

namespace mos {
namespace math {

/// @brief Generates Fourier Feature Embeddings from low-dimensional inputs.
/// Implements Bochner's theorem by projecting inputs into a high-dimensional
/// spectral space using a fixed random Gaussian frequency matrix.
class FourierMapper {
public:
    /// @brief Construct a Fourier Mapper.
    /// @param input_dim The dimensionality of the raw input vector x.
    /// @param fourier_dim The number of frequency components (d). Output vector size will be 2 * d.
    /// @param scale The standard deviation of the Gaussian frequency matrix W.
    FourierMapper(size_t input_dim, size_t fourier_dim, double scale = 1.0);

    /// @brief Project the input vector into the Fourier feature space.
    /// @param x The raw low-dimensional input vector.
    /// @return The high-dimensional spectral representation: 1/sqrt(d) * [cos(Wx), sin(Wx)]
    [[nodiscard]] std::vector<double> project(const std::vector<double>& x) const;

private:
    size_t input_dim_;
    size_t fourier_dim_;
    
    // The frequency matrix W of size (fourier_dim_ x input_dim_)
    // Stored as a flat vector for cache locality: row-major format.
    std::vector<double> W_;
};

} // namespace math
} // namespace mos
