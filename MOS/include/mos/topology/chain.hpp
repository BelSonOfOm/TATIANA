#pragma once

#include "mos/topology/simplex.hpp"
#include <map>

namespace mos {
namespace topology {

/// @brief Represents a formal linear combination of simplices over integers (Z).
/// This forms the basis for chain complexes and homology.
class Chain {
public:
    /// @brief Default constructor.
    Chain() = default;

    /// @brief Add a simplex to the chain with a given coefficient.
    /// @param s The simplex.
    /// @param coeff The integer coefficient (default 1).
    void add(const Simplex& s, int coeff = 1);

    /// @brief Add another chain to this chain (linear combination).
    /// @param other The other chain to add.
    void add(const Chain& other);

    /// @brief Check if the chain is a zero-chain (empty). O(1) cycle detection.
    /// @return True if empty.
    [[nodiscard]] bool is_empty() const noexcept;

    /// @brief Multiply the chain by a scalar.
    /// @param scalar The integer scalar.
    void scale(int scalar);

    /// @brief Get the underlying elements map.
    /// @return Const reference to the map of simplices to coefficients.
    [[nodiscard]] const std::map<Simplex, int>& get_elements() const noexcept;

private:
    std::map<Simplex, int> elements_;
};

} // namespace topology
} // namespace mos
