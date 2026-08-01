#pragma once

// PHASE-2 ITEM 7 — attachment by CONING OFF THE CYCLE (Q13).
//
// The growth operator: given a cycle that carries harmonic mass -- i.e. an
// inconsistency no potential and no filled face can explain, which is exactly
// what the Hodge split's harmonic part addresses -- add ONE new vertex joined to
// every vertex of that cycle, together with the triangles that make the cone.
//
// WHY CONING AND NOT A CHORD. The cone over a cycle is a disk, so the cycle
// BOUNDS and its homology class dies: dim H^1 drops by exactly 1. A chord
// instead SPLITS the cycle into two, and unless both halves are filled it
// RELOCATES the class rather than killing it -- it can even raise b1. That is
// why the growth loop cannot spin under coning: every attachment strictly
// reduces the number of holes, so the loop terminates in at most dim H^1 steps.
// Both behaviours are measured in the tests rather than asserted in prose.
//
// The new vertex is the cell an aimed LLM sample fills: coning decides WHERE the
// missing concept goes, and the sample decides WHAT it is.

#include <string>
#include <vector>

#include "mos/core/hodge.hpp"

namespace mos {
namespace core {

/// @brief dim H^1 of a 2-complex: E - (V - b0) - rank(delta^1).
///
/// This is the same decomposition `hodge_split` reports as dim_harm, computed
/// directly so the growth loop can ask "how many holes are left?" without
/// needing a measured cochain to split.
[[nodiscard]] int betti1(const Complex2& cx);

/// @brief The result of an attachment.
struct ConeResult {
    Complex2 complex;
    HodgeVertex apex;          ///< the new vertex -- the cell to be filled
    int betti1_before = 0;
    int betti1_after = 0;

    [[nodiscard]] int classes_killed() const noexcept { return betti1_before - betti1_after; }
};

/// @brief Cone off `cycle`: add `apex`, the edges apex-v for every v in the
/// cycle, and the triangles (apex, v_i, v_{i+1}) that fill it.
///
/// @param cycle vertices in cyclic order. Consecutive pairs (and the wrap-around
///        pair) must already be edges of `cx` -- a "cycle" whose consecutive
///        vertices are not joined is not a cycle, and inventing the missing edge
///        would change the topology being repaired.
/// @param apex  name for the new vertex; must not already exist.
///
/// @throws std::invalid_argument if the cycle is shorter than 3, repeats a
///         vertex, names an unknown vertex, is not actually a cycle in `cx`, or
///         if `apex` collides with an existing vertex.
[[nodiscard]] ConeResult cone_off_cycle(const Complex2& cx,
                                        const std::vector<HodgeVertex>& cycle,
                                        const HodgeVertex& apex);

/// @brief The CHORD alternative, provided for comparison only.
///
/// Adds a single edge between two non-adjacent cycle vertices and fills nothing.
/// This is what Q13 rejected: it splits one cycle into two and RAISES b1 rather
/// than lowering it. Shipping it would make the growth loop spin.
[[nodiscard]] ConeResult chord_cycle(const Complex2& cx,
                                     const HodgeVertex& u,
                                     const HodgeVertex& v);

}  // namespace core
}  // namespace mos
