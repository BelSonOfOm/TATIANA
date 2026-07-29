#pragma once

#include "mos/topology/complex.hpp"
#include <vector>

namespace mos {
namespace dormant {

/// @brief Computes topological invariants (Betti numbers) for a given simplicial complex.
class HomologyComputer {
public:
    /// @brief Computes the k-th Betti number of the complex.
    /// \beta_k = dim(ker d_k) - dim(im d_{k+1})
    /// @param complex The simplicial complex to analyze.
    /// @param k The dimension.
    /// @return The integer Betti number.
    [[nodiscard]] static int betti_number(const topology::SimplicialComplex& complex, int k);

    /// @brief Computes the total obstruction measure of the complex.
    /// A simple heuristic measure summing \beta_k for k > 0.
    /// @param complex The simplicial complex.
    /// @return The sum of higher-order Betti numbers.
    [[nodiscard]] static int compute_obstruction(const topology::SimplicialComplex& complex);
};

} // namespace dormant
} // namespace mos
