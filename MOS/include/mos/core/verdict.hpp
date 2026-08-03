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

/// @brief How many times each verdict has been OBSERVED -- i.e. how often an
///        oracle actually ran and returned each of the three.
///
/// WHAT THIS IS FOR. gamma_nu is defined on three verdicts, but most ticks are
/// in a FOURTH state -- no VerifyOp was in the DAG, so no oracle ran and
/// `last_verdict_` is nullopt. Collapsing that into Unverifiable is a decision,
/// not a derivation (it was flagged as such in KernelConfig). These counters are
/// what lets it become a derivation instead: "no test ran" is an ABSENCE of
/// evidence, so the honest rate is the expected rate under the historical
/// distribution of verdicts. See `gamma_no_verdict` in two_complex.hpp.
///
/// COUNTS ONLY TICKS WHERE AN ORACLE RAN. A tick with no VerifyOp contributes
/// nothing here -- including it would be conditioning on the very thing being
/// estimated. The distribution is therefore conditional on a check happening,
/// which is a real limitation and is stated at the estimator.
struct VerdictCounts {
    long long verified = 0;
    long long unverifiable = 0;
    long long refuted = 0;

    [[nodiscard]] constexpr long long total() const noexcept {
        return verified + unverifiable + refuted;
    }

    constexpr void observe(Verdict v) noexcept {
        switch (v) {
            case Verdict::Verified:     ++verified; break;
            case Verdict::Unverifiable: ++unverifiable; break;
            case Verdict::Refuted:      ++refuted; break;
        }
    }
};

} // namespace core
} // namespace mos
