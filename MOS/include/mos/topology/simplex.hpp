#pragma once

#include <vector>
#include <cstdint>
#include <initializer_list>

namespace mos {
namespace topology {

/// @brief Type alias for a unique vertex identifier.
using VertexID = uint64_t;

/// @brief Represents an oriented n-simplex in a discrete simplicial complex.
/// A simplex is uniquely identified by its canonically sorted sequence of vertices.
class Simplex {
public:
    /// @brief Construct a simplex from an initializer list of vertices.
    /// @param init The list of vertex IDs.
    Simplex(std::initializer_list<VertexID> init);

    /// @brief Construct a simplex from a vector of vertices (move semantics).
    /// @param v The vector of vertex IDs.
    explicit Simplex(std::vector<VertexID> v);

    /// @brief Default constructor (empty simplex).
    Simplex() = default;

    /// @brief Get the dimension of the simplex (number of vertices - 1).
    /// @return The dimension.
    [[nodiscard]] int dimension() const noexcept;

    /// @brief Get the vertices defining this simplex.
    /// @return A const reference to the sorted vertices.
    [[nodiscard]] const std::vector<VertexID>& get_vertices() const noexcept;

    /// @brief Equality operator.
    bool operator==(const Simplex& other) const noexcept;

    /// @brief Less-than operator for ordering in sets/maps.
    bool operator<(const Simplex& other) const noexcept;

private:
    std::vector<VertexID> vertices_;
};

} // namespace topology
} // namespace mos
