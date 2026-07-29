#include "mos/math/fourier.hpp"
#include <cmath>
#include <stdexcept>

namespace mos {
namespace math {

FourierMapper::FourierMapper(size_t input_dim, size_t fourier_dim, double scale)
    : input_dim_(input_dim), fourier_dim_(fourier_dim) {
    
    W_.resize(fourier_dim_ * input_dim_);
    
    // Deterministic seed for cross-session geometric stability.
    // The same projection matrix W_ must be used across restarts, otherwise
    // concepts persisted to the KnowledgeBase will have incompatible geometry.
    std::mt19937 gen(42); 
    std::normal_distribution<double> dist(0.0, scale);
    
    for (size_t i = 0; i < W_.size(); ++i) {
        W_[i] = dist(gen);
    }
}

std::vector<double> FourierMapper::project(const std::vector<double>& x) const {
    if (x.size() != input_dim_) {
        throw std::invalid_argument("Input dimension mismatch in FourierMapper::project");
    }
    
    std::vector<double> out(2 * fourier_dim_);
    double scale_factor = 1.0 / std::sqrt(static_cast<double>(fourier_dim_));
    
    // Compute W * x
    for (size_t i = 0; i < fourier_dim_; ++i) {
        double dot_product = 0.0;
        for (size_t j = 0; j < input_dim_; ++j) {
            dot_product += W_[i * input_dim_ + j] * x[j];
        }
        
        // Populate cos and sin parts
        out[i] = scale_factor * std::cos(dot_product);
        out[fourier_dim_ + i] = scale_factor * std::sin(dot_product);
    }
    
    return out;
}

} // namespace math
} // namespace mos
