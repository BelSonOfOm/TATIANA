#include "mos/dormant/homology.hpp"
#include "mos/dormant/boundary_matrix.hpp"
#include "mos/math/algebra.hpp"
#include <algorithm>

namespace mos {
namespace dormant {

int HomologyComputer::betti_number(const topology::SimplicialComplex& complex, int k) {
    if (k < 0) return 0;
    
    // Number of k-simplices
    const auto& simplices = complex.get_simplices();
    auto it_k = simplices.find(k);
    size_t num_k_simplices = (it_k != simplices.end()) ? it_k->second.size() : 0;
    
    if (num_k_simplices == 0) return 0;
    
    // Rank of D_k
    math::Matrix D_k = BoundaryMatrixGenerator::generate(complex, k);
    size_t rank_D_k = math::compute_rank(D_k);
    
    // Rank of D_{k+1}
    math::Matrix D_kp1 = BoundaryMatrixGenerator::generate(complex, k + 1);
    size_t rank_D_kp1 = math::compute_rank(D_kp1);
    
    // \beta_k = (number of k-simplices) - rank(D_k) - rank(D_{k+1})
    int betti = static_cast<int>(num_k_simplices) - static_cast<int>(rank_D_k) - static_cast<int>(rank_D_kp1);
    return std::max(0, betti);
}

int HomologyComputer::compute_obstruction(const topology::SimplicialComplex& complex) {
    int total_obstruction = 0;
    
    // Find the max dimension in the complex
    const auto& simplices = complex.get_simplices();
    if (simplices.empty()) return 0;
    
    int max_dim = simplices.rbegin()->first;
    
    // Sum Betti numbers for k > 0 (we ignore \beta_0 which is connected components)
    // A stable cognitive attractor should have no "holes" (loops of unresolved logic)
    for (int k = 1; k <= max_dim; ++k) {
        total_obstruction += betti_number(complex, k);
    }
    
    return total_obstruction;
}

} // namespace dormant
} // namespace mos
