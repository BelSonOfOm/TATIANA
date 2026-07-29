#include "mos/topology/chain.hpp"

namespace mos {
namespace topology {

void Chain::add(const Simplex& s, int coeff) {
    elements_[s] += coeff;
    if (elements_[s] == 0) {
        elements_.erase(s); // Canonical form: no zero coefficients
    }
}

void Chain::add(const Chain& other) {
    for (const auto& [s, coeff] : other.elements_) {
        add(s, coeff);
    }
}

bool Chain::is_empty() const noexcept {
    return elements_.empty();
}

void Chain::scale(int scalar) {
    if (scalar == 0) {
        elements_.clear();
        return;
    }
    for (auto& [s, coeff] : elements_) {
        coeff *= scalar;
    }
}

const std::map<Simplex, int>& Chain::get_elements() const noexcept {
    return elements_;
}

} // namespace topology
} // namespace mos
