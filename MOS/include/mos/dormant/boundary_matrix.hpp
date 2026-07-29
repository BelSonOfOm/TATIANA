#pragma once

#include "mos/topology/complex.hpp"
#include "mos/math/algebra.hpp"

namespace mos {
namespace dormant {

/// @brief Generates boundary matrices for homology calculations.
class BoundaryMatrixGenerator {
public:
    /// @brief Generates the boundary matrix D_k for a given simplicial complex and dimension k.
    /// The matrix represents the boundary map from k-simplices to (k-1)-simplices.
    /// @param complex The simplicial complex.
    /// @param k The dimension of simplices to take the boundary of.
    /// @return A dense matrix representing D_k.
    [[nodiscard]] static math::Matrix generate(const topology::SimplicialComplex& complex, int k);
};

} // namespace dormant
} // namespace mos
