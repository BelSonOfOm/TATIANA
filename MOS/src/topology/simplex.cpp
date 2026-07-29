#include "mos/topology/simplex.hpp"
#include <algorithm>
#include <utility>
#include <stdexcept>

namespace mos {
namespace topology {

Simplex::Simplex(std::initializer_list<VertexID> init) : vertices_(init) {
    std::sort(vertices_.begin(), vertices_.end());
    vertices_.erase(std::unique(vertices_.begin(), vertices_.end()), vertices_.end());
    if (vertices_.empty()) {
        throw std::invalid_argument("[Simplex] Cannot construct an empty or fully degenerate simplex.");
    }
}

Simplex::Simplex(std::vector<VertexID> v) : vertices_(std::move(v)) {
    std::sort(vertices_.begin(), vertices_.end());
    vertices_.erase(std::unique(vertices_.begin(), vertices_.end()), vertices_.end());
    if (vertices_.empty()) {
        throw std::invalid_argument("[Simplex] Cannot construct an empty or fully degenerate simplex.");
    }
}

int Simplex::dimension() const noexcept {
    return static_cast<int>(vertices_.size()) - 1;
}

const std::vector<VertexID>& Simplex::get_vertices() const noexcept {
    return vertices_;
}

bool Simplex::operator==(const Simplex& other) const noexcept {
    return vertices_ == other.vertices_;
}

bool Simplex::operator<(const Simplex& other) const noexcept {
    return vertices_ < other.vertices_;
}

} // namespace topology
} // namespace mos
