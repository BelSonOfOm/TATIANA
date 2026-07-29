#include "mos/topology/complex.hpp"
#include <vector>
#include <algorithm>

namespace mos {
namespace topology {

void SimplicialComplex::insert(const Simplex& s) {
    int dim = s.dimension();
    simplices_[dim].insert(s);
    
    // Recursively insert faces if dimension > 0
    if (dim > 0) {
        Chain b = boundary(s);
        for (const auto& [face, coeff] : b.get_elements()) {
            insert(face);
        }
    }
}

void SimplicialComplex::remove(const Simplex& s) {
    // Basic implementation: remove the simplex
    int dim = s.dimension();
    simplices_[dim].erase(s);
    
    // Remove all co-faces (simplices containing 's' as a face)
    for (auto it = simplices_.upper_bound(dim); it != simplices_.end(); ++it) {
        auto& higher_dim_set = it->second;
        for (auto set_it = higher_dim_set.begin(); set_it != higher_dim_set.end(); ) {
            // Check if s is a subset of set_it->get_vertices()
            const auto& large_v = set_it->get_vertices();
            const auto& small_v = s.get_vertices();
            
            bool is_subset = std::includes(large_v.begin(), large_v.end(), small_v.begin(), small_v.end());
            
            if (is_subset) {
                set_it = higher_dim_set.erase(set_it);
            } else {
                ++set_it;
            }
        }
    }
}

bool SimplicialComplex::contains(const Simplex& s) const noexcept {
    int dim = s.dimension();
    auto it = simplices_.find(dim);
    if (it != simplices_.end()) {
        return it->second.find(s) != it->second.end();
    }
    return false;
}

Chain SimplicialComplex::boundary(const Simplex& s) {
    Chain result;
    int dim = s.dimension();
    if (dim == 0) {
        return result; // Boundary of a vertex is 0
    }

    const auto& verts = s.get_vertices();
    for (size_t i = 0; i < verts.size(); ++i) {
        std::vector<VertexID> face_vertices;
        face_vertices.reserve(verts.size() - 1);
        for (size_t j = 0; j < verts.size(); ++j) {
            if (i != j) {
                face_vertices.push_back(verts[j]);
            }
        }
        
        Simplex face(std::move(face_vertices));
        int coeff = (i % 2 == 0) ? 1 : -1;
        result.add(face, coeff);
    }
    
    return result;
}

Chain SimplicialComplex::boundary(const Chain& c) {
    Chain result;
    for (const auto& [s, coeff] : c.get_elements()) {
        Chain s_boundary = boundary(s);
        s_boundary.scale(coeff);
        result.add(s_boundary);
    }
    return result;
}

const std::map<int, std::set<Simplex>>& SimplicialComplex::get_simplices() const noexcept {
    return simplices_;
}

} // namespace topology
} // namespace mos
