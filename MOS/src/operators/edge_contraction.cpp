#include "mos/operators/edge_contraction.hpp"
#include "mos/core/cognitive_state.hpp"
#include <vector>
#include <algorithm>
#include <iostream>
#include <shared_mutex>

namespace mos {
namespace operators {

EdgeContractionOperator::EdgeContractionOperator(topology::VertexID keep_vertex, topology::VertexID remove_vertex)
    : v_keep_(keep_vertex), v_remove_(remove_vertex) {}

bool EdgeContractionOperator::apply(core::CognitiveState& state) {
    std::unique_lock<std::shared_mutex> lock(state.get_mutex());
    topology::SimplicialComplex& complex = state.get_complex();
    
    // MATHEMATICAL NOTE: The Link Condition
    // In discrete topology, an edge contraction preserves the homotopy type if and only if:
    // Lk(v_keep) \cap Lk(v_remove) = Lk([v_keep, v_remove])
    // If this operator is intended to preserve cohomology, we must verify this condition first.
    
    const auto& all_simplices = complex.get_simplices();
    
    // Verify Link Condition: For every simplex sigma where sigma U {u} and sigma U {v} are in K,
    // sigma U {u, v} must also be in K.
    for (const auto& [dim, simplex_set] : all_simplices) {
        for (const auto& sigma : simplex_set) {
            const auto& verts = sigma.get_vertices();
            if (std::find(verts.begin(), verts.end(), v_keep_) == verts.end() &&
                std::find(verts.begin(), verts.end(), v_remove_) == verts.end()) {
                
                // Construct sigma U {u}
                std::vector<topology::VertexID> s_u = verts;
                s_u.push_back(v_keep_);
                topology::Simplex sim_u(s_u);
                
                // Construct sigma U {v}
                std::vector<topology::VertexID> s_v = verts;
                s_v.push_back(v_remove_);
                topology::Simplex sim_v(s_v);
                
                if (complex.contains(sim_u) && complex.contains(sim_v)) {
                    // Check if sigma U {u, v} is in K
                    std::vector<topology::VertexID> s_uv = verts;
                    s_uv.push_back(v_keep_);
                    s_uv.push_back(v_remove_);
                    topology::Simplex sim_uv(s_uv);
                    if (!complex.contains(sim_uv)) {
                        std::cout << "[EdgeContraction] Link Condition failed. Contraction rejected.\n";
                        return false;
                    }
                }
            }
        }
    }
    
    std::vector<topology::Simplex> to_remove;
    std::vector<topology::Simplex> to_add;

    for (const auto& [dim, simplex_set] : all_simplices) {
        for (const auto& s : simplex_set) {
            const auto& verts = s.get_vertices();
            if (std::find(verts.begin(), verts.end(), v_remove_) != verts.end()) {
                to_remove.push_back(s);
                
                // Create the contracted simplex
                std::vector<topology::VertexID> new_verts;
                new_verts.reserve(verts.size());
                for (auto v : verts) {
                    if (v == v_remove_) {
                        if (std::find(verts.begin(), verts.end(), v_keep_) == verts.end()) {
                            new_verts.push_back(v_keep_); // Replace v_remove_ with v_keep_
                        }
                    } else {
                        new_verts.push_back(v);
                    }
                }
                
                // Note: The Simplex constructor automatically calls std::sort(verts.begin(), verts.end()) 
                // ensuring the canonical orientation is strictly preserved for the boundary operator.
                if (new_verts.size() > 0) {
                    to_add.emplace_back(std::move(new_verts));
                }
            }
        }
    }

    if (to_remove.empty()) {
        return false;
    }

    // Apply the topological surgery
    for (const auto& s : to_remove) {
        complex.remove(s);
    }
    for (const auto& s : to_add) {
        complex.insert(s);
    }

    // Update the Sheaf (F) to maintain a valid global section (s)
    state.get_sheaf().merge_stalks(v_keep_, v_remove_);

    return true;
}

} // namespace operators
} // namespace mos
