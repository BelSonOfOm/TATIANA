#pragma once

#include "mos/topology/simplex.hpp"
#include "mos/topology/chain.hpp"
#include <map>
#include <set>

namespace mos {
namespace topology {

/// @brief A discrete Simplicial Complex storing simplices organized by dimension.
class SimplicialComplex {
public:
    /// @brief Default constructor.
    SimplicialComplex() = default;

    /// @brief Insert a simplex and all its faces recursively.
    /// @param s The simplex to insert.
    void insert(const Simplex& s);

    /// @brief Remove a simplex and all co-faces (simplices that contain it).
    /// @param s The simplex to remove.
    void remove(const Simplex& s);

    /// @brief Check if a simplex exists in the complex.
    /// @param s The simplex to check.
    /// @return True if present, false otherwise.
    [[nodiscard]] bool contains(const Simplex& s) const noexcept;

    /// @brief Calculate the boundary of a single simplex.
    /// @param s The simplex.
    /// @return The resulting chain representing the boundary d_n(s).
    [[nodiscard]] static Chain boundary(const Simplex& s);

    /// @brief Calculate the boundary of a chain.
    /// @param c The chain.
    /// @return The resulting boundary chain.
    [[nodiscard]] static Chain boundary(const Chain& c);

    /// @brief Get the underlying simplices map.
    /// @return Const reference to the map of dimensions to sets of simplices.
    [[nodiscard]] const std::map<int, std::set<Simplex>>& get_simplices() const noexcept;

private:
    std::map<int, std::set<Simplex>> simplices_;
};

} // namespace topology
} // namespace mos
