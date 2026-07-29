#include "mos/operators/edge_expansion.hpp"
#include "mos/core/cognitive_state.hpp"
#include <shared_mutex>

namespace mos {
namespace operators {

EdgeExpansionOperator::EdgeExpansionOperator(topology::VertexID v1, topology::VertexID v2, std::shared_ptr<core::ProceduralSkill> skill)
    : v1_(v1), v2_(v2), skill_(std::move(skill)) {}

bool EdgeExpansionOperator::apply(core::CognitiveState& state) {
    std::unique_lock<std::shared_mutex> lock(state.get_mutex());
    // A 1-simplex (edge) containing v1 and v2
    // The Simplex constructor automatically sorts them for canonical orientation
    topology::Simplex edge({v1_, v2_});
    
    // Insert into the complex
    state.get_complex().insert(edge);
    
    // Attach the transitive verb skill to the sheaf
    if (skill_) {
        state.get_sheaf().attach(edge, skill_);
    }
    
    return true;
}

} // namespace operators
} // namespace mos
