#pragma once

#include <string>
#include <vector>

namespace mos {
namespace core {

/// @brief (5p mechanism 4) Edelman selectionism - verify-first fitness.
/// Header-only C++ port of python/selection.py. Encodes the rho-vs-truth order:
/// truth (VERIFIED) is promoted even if it raised discord; coherence (delta_rho)
/// alone never promotes past a possible verification.
enum class VerifyOutcome { REFUTED = 0, UNVERIFIABLE = 1, VERIFIED = 2 };

struct Candidate {
  std::string payload;
  double delta_rho; ///< rho_after - rho_before  (negative == reduced discord)
  VerifyOutcome verify;
  std::string source;
};

struct Selection {
  int winner_index; ///< -1 if nothing qualifies
  std::string reason;
};

/// Rules (see python/selection.py):
///  1. REFUTED candidates are discarded, always.
///  2. VERIFIED beats UNVERIFIABLE; a VERIFIED candidate is promotable even if it
///     RAISED discord (truth trumps coherence).
///  3. Within a tier, the biggest discord drop (most negative delta_rho) wins.
///  4. An UNVERIFIABLE candidate promotes only if it reduced discord (< 0).
[[nodiscard]] inline Selection select_best(const std::vector<Candidate> &cands) {
  if (cands.empty())
    return {-1, "no candidates were generated"};

  int best = -1;
  for (int i = 0; i < static_cast<int>(cands.size()); ++i) {
    if (cands[i].verify == VerifyOutcome::REFUTED)
      continue;
    if (best < 0) {
      best = i;
      continue;
    }
    const int tb = static_cast<int>(cands[best].verify);
    const int ti = static_cast<int>(cands[i].verify);
    if (ti > tb || (ti == tb && cands[i].delta_rho < cands[best].delta_rho))
      best = i;
  }

  if (best < 0)
    return {-1, "all candidates were REFUTED by the oracle"};
  if (cands[best].verify == VerifyOutcome::VERIFIED)
    return {best, "VERIFIED by oracle; truth promoted even if it raised discord"};
  if (cands[best].delta_rho < 0.0)
    return {best, "UNVERIFIABLE but reduced discord; weak, revocable promotion"};
  return {-1, "best candidate is UNVERIFIABLE and did not reduce discord; "
              "refusing to crystallise a coherent-but-unproven mediator"};
}

} // namespace core
} // namespace mos
