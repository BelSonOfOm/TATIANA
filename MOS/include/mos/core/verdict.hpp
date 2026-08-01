#pragma once

// THE PROMOTION VERDICT, ON ITS OWN, SO THE TICK CAN CARRY IT.
//
// Verdict used to live in two_complex.hpp, which pulls in Eigen via hodge.hpp
// and householder.hpp. CognitiveState needs to carry a verdict and has no other
// reason to know about Eigen dense algebra, so the enum moves here and
// two_complex.hpp includes this. Nothing else changes: same namespace, same
// name, same to_string, defined where it always was in two_complex.cpp.
//
// WHY THIS MATTERS MORE THAN IT LOOKS. gamma_nu takes a Verdict, not a number.
// Until VerifyOp's outcome reaches the kernel there is no verdict, so there is
// no gamma, so i_shriek can never be called, so nothing crystallises and Q(t)
// stays pinned at zero -- the constant sheaf, i.e. nothing learned. The same
// value is also the NULL `verified` column in E7 and the promotion gate for
// operator-algebra growth. One wire, three consumers.

namespace mos {
namespace core {

/// @brief The promotion verdict that sets the transfer rate.
///
/// ORDERED BY HOW MUCH CRYSTALLISATION THEY PERMIT, least first. `combine`
/// relies on that order, so do not reorder these without reading it.
enum class Verdict {
    Refuted = 0,       ///< checked, and FALSE. gamma = 0 exactly.
    Unverifiable = 1,  ///< checked, and the oracle could not decide. gamma = eps*gamma0.
    Verified = 2       ///< checked, and it holds. gamma = gamma0.
};

[[nodiscard]] const char* to_string(Verdict v) noexcept;

/// @brief The verdict of a tick that ran SEVERAL checks: the weakest one.
///
/// A composite is only as verified as its least-verified check. Any refutation
/// makes the whole session refuted, however many other checks passed -- taking
/// the max instead would let one passing check launder a contradiction into the
/// store, which is precisely what the promotion gate exists to prevent.
[[nodiscard]] constexpr Verdict combine(Verdict a, Verdict b) noexcept {
    return (static_cast<int>(a) < static_cast<int>(b)) ? a : b;
}

} // namespace core
} // namespace mos
