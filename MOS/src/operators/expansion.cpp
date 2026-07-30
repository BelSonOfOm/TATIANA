#include "mos/operators/expansion.hpp"
#include "mos/core/cognitive_state.hpp"
#include <shared_mutex>
#include <mutex>
#include <shared_mutex>

namespace mos {
namespace operators {

ExpansionOperator::ExpansionOperator(topology::VertexID new_v, std::shared_ptr<core::ProceduralSkill> skill)
    : new_v_(new_v), skill_(std::move(skill)) {}

bool ExpansionOperator::apply(core::CognitiveState& state) {
    std::unique_lock<std::shared_mutex> lock(state.get_mutex());
    topology::Simplex s({new_v_});
    
    // Insert the vertex into the complex
    state.get_complex().insert(s);
    
    // Attach the skill to the sheaf
    if (skill_) {
        state.get_sheaf().attach(s, skill_);
    }
    
    return true;
}

} // namespace operators
} // namespace mos
