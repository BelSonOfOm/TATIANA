#include "mos/dormant/boundary_matrix.hpp"
#include <vector>
#include <map>

namespace mos {
namespace dormant {

math::Matrix BoundaryMatrixGenerator::generate(const topology::SimplicialComplex& complex, int k) {
    const auto& all_simplices = complex.get_simplices();
    
    // If there are no k-simplices, the matrix has 0 columns.
    auto it_k = all_simplices.find(k);
    if (it_k == all_simplices.end() || it_k->second.empty()) {
        return math::Matrix(0, 0); // Rank is 0
    }
    
    // If there are k-simplices but no (k-1)-simplices, this shouldn't happen in a valid complex,
    // but we can return a 0xN matrix.
    auto it_k_minus_1 = all_simplices.find(k - 1);
    if (it_k_minus_1 == all_simplices.end() || it_k_minus_1->second.empty()) {
        return math::Matrix(0, it_k->second.size());
    }
    
    const auto& k_simplices = it_k->second;
    const auto& km1_simplices = it_k_minus_1->second;
    
    size_t cols = k_simplices.size();
    size_t rows = km1_simplices.size();
    
    math::Matrix D(rows, cols);
    
    // We need a stable indexing for (k-1)-simplices to map them to rows
    std::map<topology::Simplex, size_t> row_index_map;
    size_t r = 0;
    for (const auto& face : km1_simplices) {
        row_index_map[face] = r++;
    }
    
    size_t c = 0;
    for (const auto& s : k_simplices) {
        // Calculate boundary of this k-simplex
        topology::Chain bnd = topology::SimplicialComplex::boundary(s);
        
        // Populate the column for this simplex
        for (const auto& [face, coeff] : bnd.get_elements()) {
            auto face_it = row_index_map.find(face);
            if (face_it != row_index_map.end()) {
                D.at(face_it->second, c) = static_cast<double>(coeff);
            }
        }
        c++;
    }
    
    return D;
}

} // namespace dormant
} // namespace mos
