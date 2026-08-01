// Tests for FIX-11 (operad co-schedulability) and FIX-13 (the stalk noise floor).
//
// Both fixes are about things that were SILENTLY wrong: FIX-11 lost parallelism
// depending on node order, FIX-13 made every C++ entropy identical and every C++
// W_2 Euclidean. Neither showed up as a failure, which is exactly why they need
// tests that assert the property rather than the symptom.

#include <cassert>
#include <cmath>
#include <iostream>
#include <stdexcept>

#include "mos/core/cognitive_state.hpp"
#include "mos/core/edge_precision.hpp"
#include "mos/core/operad.hpp"
#include "mos/core/semantic_skill.hpp"
#include "mos/translation/curator.hpp"

using namespace mos;

namespace {

constexpr int kDeployedDim = 384;  // bge-small-en-v1.5, per FIX-1's contract
constexpr double kPythonEpsFloor = 1e-3;  // must match belief.py EPS_FLOOR

bool close(double a, double b, double tol = 1e-12) {
  return std::fabs(a - b) <= tol * std::max(1.0, std::max(std::fabs(a), std::fabs(b)));
}

// ---------------------------------------------------------------------------
// FIX-13
// ---------------------------------------------------------------------------

void test_eps_floor_matches_python() {
  // If these drift apart, the C++/Python parity tests compare different objects
  // and the comparison is meaningless while still passing.
  assert(close(core::EPS_FLOOR, kPythonEpsFloor));
  std::cout << "  [ok] EPS_FLOOR agrees with python/belief.py (" << core::EPS_FLOOR << ")\n";
}

void test_stalk_floor_is_order_one_over_d() {
  // The invariant is NOT "one shared eps" but "floor is O(1/d)", i.e. the
  // covariance carries trace O(1). Assert the trace, which is the real thing.
  const double D = core::stalk_floor(kDeployedDim, /*n_eff=*/1.0, /*kappa=*/1.0);

  // Closed form: eps + kappa/(d*(n_eff+kappa)) = 1e-3 + 1/(384*2).
  const double expected = kPythonEpsFloor + 1.0 / (384.0 * 2.0);
  assert(close(D, expected, 1e-9));

  const double trace = kDeployedDim * D;
  // trace = 384*1e-3 + 0.5 = 0.8842. O(1), and in particular <= 4 (the largest
  // possible semantic distance), so epistemic cannot dwarf meaning.
  assert(trace > 0.0 && trace < 4.0);
  std::cout << "  [ok] stalk_floor(384) = " << D << ", trace = " << trace
            << " -- O(1), not O(d)\n";
}

void test_floor_broadens_with_fewer_observations() {
  // A concept seen ONCE must be BROADER than one seen many times. The old engine
  // had this backwards: empty U plus D = 1.0 gave maximum confidence from a
  // single sighting.
  const double once = core::stalk_floor(kDeployedDim, /*n_eff=*/1.0);
  const double often = core::stalk_floor(kDeployedDim, /*n_eff=*/50.0);
  assert(once > often);
  // And it tends to the bare floor as evidence accumulates.
  const double many = core::stalk_floor(kDeployedDim, /*n_eff=*/1e6);
  assert(many > core::EPS_FLOOR && close(many, core::EPS_FLOOR, 1e-6));
  std::cout << "  [ok] n_eff 1 -> " << once << " broader than n_eff 50 -> " << often
            << ", -> EPS_FLOOR as n_eff grows\n";
}

void test_e4_blowup_is_actually_gone() {
  // THE REGRESSION TEST FOR FIX-13. Reproduce E4's number with the old constants,
  // then show the new floor kills it. Both use the real Bures formula, not a proxy.
  Eigen::VectorXd mu1 = Eigen::VectorXd::Zero(kDeployedDim);
  Eigen::VectorXd mu2 = Eigen::VectorXd::Zero(kDeployedDim);
  mu1(0) = 1.0;
  mu2(0) = -1.0;  // antipodal: the LARGEST possible semantic distance, = 4
  const Eigen::MatrixXd no_U(kDeployedDim, 0);

  // OLD: D1 = 1.0 (uncalibrated prior), D2 = -ln(0.95) (a confident concept).
  const double old_D1 = 1.0;
  const double old_D2 = -std::log(0.95);
  auto old_terms = core::wasserstein_2_terms(mu1, old_D1, mu2, no_U, old_D2);
  assert(close(old_terms.semantic, 4.0, 1e-9));
  // The documented ~230. Assert it exceeds the entire semantic budget many times
  // over -- that is the defect, stated as an inequality rather than a magic value.
  assert(old_terms.epistemic > 50.0 * old_terms.semantic);

  // NEW: both stalks get the shared shrinkage floor.
  const double new_D = core::stalk_floor(kDeployedDim, 1.0);
  auto new_terms = core::wasserstein_2_terms(mu1, new_D, mu2, no_U, new_D);
  assert(close(new_terms.semantic, 4.0, 1e-9));
  // Identical floors => the d-extensive term vanishes IDENTICALLY, not "is small".
  assert(new_terms.epistemic < 1e-9);

  std::cout << "  [ok] E4: epistemic was " << old_terms.epistemic << " (vs semantic 4), now "
            << new_terms.epistemic << "\n";
}

void test_w2_is_no_longer_euclidean_when_ranks_differ() {
  // FIX-13's complaint was that W_2 "remains Euclidean". With a shared floor the
  // ISOTROPIC part vanishes by construction (above), and the epistemic term must
  // now come from real directional structure in U -- which is the point.
  Eigen::VectorXd mu = Eigen::VectorXd::Zero(kDeployedDim);
  mu(0) = 1.0;
  const double D = core::stalk_floor(kDeployedDim, 1.0);

  Eigen::MatrixXd U(kDeployedDim, 1);
  U.setZero();
  U(1, 0) = 0.5;  // spread in ONE direction, orthogonal to the mean

  auto flat = core::wasserstein_2_terms(mu, D, mu, Eigen::MatrixXd(kDeployedDim, 0), D);
  auto structured = core::wasserstein_2_terms(mu, D, mu, U, D);

  assert(close(flat.semantic, 0.0, 1e-12) && flat.epistemic < 1e-9);
  assert(structured.epistemic > 1e-6);  // directional uncertainty IS measured
  std::cout << "  [ok] same mean, rank-0 vs rank-1: epistemic " << flat.epistemic
            << " -> " << structured.epistemic << " (geometry is live, not inert)\n";
}

void test_max_epistemic_trace_closed_form() {
  // t_max solves d*(sqrt(eps + t/d) - sqrt(eps))^2 = 4 exactly. Verify by
  // substituting the returned value back into the equation it claims to solve --
  // an independent check, not a restatement of the formula.
  for (int d : {2, 16, 384, 4096}) {
    const double eps = core::EPS_FLOOR;
    const double t = core::max_epistemic_trace(d, eps);
    const double D_hi = eps + t / static_cast<double>(d);
    const double bures = d * std::pow(std::sqrt(D_hi) - std::sqrt(eps), 2.0);
    assert(close(bures, 4.0, 1e-9));
  }
  const double t384 = core::max_epistemic_trace(kDeployedDim);
  std::cout << "  [ok] max_epistemic_trace closed form verified at d=2,16,384,4096"
            << " (d=384: t_max = " << t384 << ")\n";
}

void test_derived_clamp_beats_the_old_1e9_clamp() {
  // The old clamp was min confidence 1e-9, purely to dodge log(0). Show that it
  // admits an epistemic term far outside the budget, while the derived bound is
  // exactly at it. This is the "magic number replaced by a consequence" claim,
  // tested rather than asserted in a comment.
  const double t_from_old_clamp = -std::log(1e-9);   // 20.72
  const double t_max = core::max_epistemic_trace(kDeployedDim);
  assert(t_from_old_clamp > t_max);

  const double D_old = core::EPS_FLOOR + t_from_old_clamp / kDeployedDim;
  const double bures_old =
      kDeployedDim * std::pow(std::sqrt(D_old) - std::sqrt(core::EPS_FLOOR), 2.0);
  assert(bures_old > 4.0);  // over budget: confidence would outweigh meaning

  std::cout << "  [ok] old 1e-9 clamp allows t = " << t_from_old_clamp << " (Bures "
            << bures_old << " > 4); derived bound is t_max = " << t_max << "\n";
}

void test_e4_guard_refuses_the_old_configuration() {
  // The guard must FIRE on the exact configuration that caused E4, and stay quiet
  // on the fixed one. A guard that never fires is not a guard.
  bool threw = false;
  try {
    core::assert_e4_budget(kDeployedDim, core::EPS_FLOOR, 1.0);  // the old D = 1.0
  } catch (const std::invalid_argument &) {
    threw = true;
  }
  assert(threw);

  const double D = core::stalk_floor(kDeployedDim, 1.0);
  core::assert_e4_budget(kDeployedDim, D, D);  // must not throw

  // Argument order must not matter.
  core::assert_e4_budget(kDeployedDim, D, core::EPS_FLOOR);
  core::assert_e4_budget(kDeployedDim, core::EPS_FLOOR, D);

  // And it must reject nonsense rather than silently computing with it.
  bool bad_dim = false;
  try {
    volatile double sink = core::stalk_floor(0);
    (void)sink;
  } catch (const std::invalid_argument &) {
    bad_dim = true;
  }
  assert(bad_dim);

  std::cout << "  [ok] E4 guard fires on D=1.0, passes the shrinkage floor, "
               "order-independent, rejects d=0\n";
}

void test_grown_concept_uses_the_floor() {
  // End-to-end: the value cognitive_state.cpp actually attaches.
  core::CognitiveState state;
  std::vector<double> geometry(kDeployedDim, 0.0);
  geometry[0] = 1.0;
  state.grow_concept("test_concept", geometry, "Reasoning");

  const auto &complex = state.get_complex();
  assert(!complex.get_simplices().empty());

  // Read the attached stalk back and assert its floor is the derived one, not 1.0.
  bool found = false;
  for (const auto &s : complex.get_simplices().at(0)) {
    auto skill = state.get_sheaf().get_skill(s);
    if (!skill) continue;
    auto emb = std::dynamic_pointer_cast<const core::SemanticEmbedding>(skill);
    if (!emb || emb->get_name() != "test_concept") continue;
    found = true;
    const double expected = core::stalk_floor(kDeployedDim, 1.0);
    assert(close(emb->get_D(), expected, 1e-12));
    assert(emb->get_U().cols() == 0);  // one observation => genuinely rank 0
    assert(emb->get_D() < 1.0);        // the defect this fix closes
  }
  assert(found);
  std::cout << "  [ok] grow_concept attaches the shrinkage floor, not D = 1.0\n";
}

// ---------------------------------------------------------------------------
// FIX-11
// ---------------------------------------------------------------------------

/// Minimal operator with a settable support and type. `apply` is never called --
/// these tests exercise the co-schedulability RULE, not execution.
class StubOp : public core::CognitiveOperator {
 public:
  StubOp(std::set<int> support, core::OperatorType type)
      : support_(std::move(support)), type_(type) {}

  bool apply(core::CognitiveState &) override { return true; }
  [[nodiscard]] core::OperatorType get_type() const noexcept override { return type_; }
  [[nodiscard]] std::set<int> get_support() const override { return support_; }

 private:
  std::set<int> support_;
  core::OperatorType type_;
};

std::shared_ptr<core::OperadNode> node(std::set<int> support, core::OperatorType type) {
  return std::make_shared<core::OperadNode>(
      std::make_shared<StubOp>(std::move(support), type));
}

/// Foliate a whole ready queue into slices, the way Operad::run does, but without
/// executing anything.
std::vector<std::vector<std::shared_ptr<core::OperadNode>>> foliate_all(
    std::vector<std::shared_ptr<core::OperadNode>> ready) {
  std::vector<std::vector<std::shared_ptr<core::OperadNode>>> slices;
  while (!ready.empty()) {
    std::vector<std::shared_ptr<core::OperadNode>> deferred;
    auto slice = core::select_commuting_slice(ready, deferred);
    // A slice must always make progress, or this loop would not terminate.
    assert(!slice.empty());
    slices.push_back(std::move(slice));
    ready = std::move(deferred);
  }
  return slices;
}

void test_read_only_node_does_not_poison_the_slice() {
  // THE FIX-11 REGRESSION. A READ_ONLY empty-support node (SearchOp, RespondOp)
  // writes nothing, so it cannot conflict with anything and must not lock the
  // slice for nodes evaluated AFTER it. Reader FIRST is the order that used to
  // poison everything behind it: pre-fix this gave slices of 1, 1, 1.
  auto slices = foliate_all({
      node({}, core::OperatorType::READ_ONLY),
      node({1}, core::OperatorType::MUTATION),
      node({2}, core::OperatorType::MUTATION),
  });
  assert(slices.size() == 1);
  assert(slices.front().size() == 3);
  std::cout << "  [ok] read-only-first: 3 nodes in 1 slice (pre-fix: 3 slices)\n";
}

void test_co_schedulability_is_order_independent() {
  // The defect was ORDER-DEPENDENCE, so test that property directly rather than
  // any single ordering's outcome.
  auto reader_first = foliate_all({
      node({}, core::OperatorType::READ_ONLY),
      node({7}, core::OperatorType::MUTATION),
  });
  auto worker_first = foliate_all({
      node({7}, core::OperatorType::MUTATION),
      node({}, core::OperatorType::READ_ONLY),
  });
  assert(reader_first.size() == worker_first.size());
  assert(reader_first.size() == 1);
  std::cout << "  [ok] slice count is insertion-order independent (1 either way)\n";
}

void test_two_read_only_globals_share_a_slice() {
  // Several read-only global nodes must all fit together -- pre-fix the first one
  // locked out the second.
  auto slices = foliate_all({
      node({}, core::OperatorType::READ_ONLY),
      node({}, core::OperatorType::READ_ONLY),
      node({4}, core::OperatorType::MUTATION),
  });
  assert(slices.size() == 1 && slices.front().size() == 3);
  std::cout << "  [ok] two read-only globals + a worker co-schedule\n";
}

void test_writing_global_node_still_isolates() {
  // The safety property must SURVIVE the fix: a MUTATION empty-support node still
  // runs alone. Loosening FIX-11 too far would be worse than the bug it fixes.
  auto slices = foliate_all({
      node({}, core::OperatorType::MUTATION),
      node({3}, core::OperatorType::MUTATION),
  });
  assert(slices.size() == 2);
  assert(slices.front().size() == 1);
  std::cout << "  [ok] a MUTATION global node still runs isolated\n";
}

void test_global_mutation_locks_a_later_read_only() {
  // The other direction of the safety property: once a global MUTATION actually
  // HOLDS the slice, a read-only node evaluated after it must be locked out.
  //
  // The global mutation must come first for this to be the property under test. An
  // earlier draft of this test put a worker first, which DEFERS the global mutation
  // (it cannot join a non-empty slice) so the flag is never set and the read-only
  // node legitimately joins the worker. That is correct behaviour, not a leak —
  // the mutation is not in that slice at all — but it tests a different thing.
  auto slices = foliate_all({
      node({}, core::OperatorType::MUTATION),
      node({}, core::OperatorType::READ_ONLY),
  });
  assert(slices.size() == 2);
  assert(slices.front().size() == 1);  // the global mutation, isolated
  assert(slices.back().size() == 1);   // the read-only node, deferred
  std::cout << "  [ok] a global MUTATION holding the slice locks out a later read-only\n";
}

void test_deferred_global_mutation_does_not_leak_its_lock() {
  // The companion case to the above, asserted rather than left implicit: a global
  // MUTATION that is DEFERRED must not lock the slice it failed to enter.
  auto slices = foliate_all({
      node({5}, core::OperatorType::MUTATION),
      node({}, core::OperatorType::MUTATION),   // deferred: slice is non-empty
      node({}, core::OperatorType::READ_ONLY),  // must still be free to join
  });
  assert(slices.size() == 2);
  assert(slices.front().size() == 2);  // worker + read-only co-schedule
  assert(slices.back().size() == 1);   // the global mutation, alone, later
  std::cout << "  [ok] a DEFERRED global mutation does not lock the slice it missed\n";
}

void test_overlapping_supports_still_serialise() {
  // Baseline sanity: the ordinary disjointness rule is untouched by FIX-11.
  auto slices = foliate_all({
      node({1, 2}, core::OperatorType::MUTATION),
      node({2, 3}, core::OperatorType::MUTATION),
  });
  assert(slices.size() == 2);
  std::cout << "  [ok] overlapping supports still serialise\n";
}

// ---------------------------------------------------------------------------
// FIX-17. FIX-13 removed `D = -ln c` and UNCALIBRATED_VARIANCE_PRIOR = 1.0 from
// AgentCurator::compute_variance, but nothing PINNED that. The contract was held
// by a comment, and a comment is exactly what regresses -- the `.tex` had already
// drifted back to describing the old behaviour for four days without anything
// failing. These tests make the contract executable.
// ---------------------------------------------------------------------------

void test_curator_floor_ignores_confidence() {
  const translation::AgentCurator curator{math::FourierMapper(8, 8)};

  // The SAME floor for every confidence, including none at all. If a future
  // edit routes confidence back into the stalk geometry, this fails.
  const double none = curator.compute_variance(std::nullopt, kDeployedDim);
  const double sure = curator.compute_variance(0.99, kDeployedDim);
  const double unsure = curator.compute_variance(0.05, kDeployedDim);

  assert(none == sure && sure == unsure &&
         "confidence must NOT reach the stalk floor -- per Q9 its home is pi_e");
  assert(close(none, core::stalk_floor(kDeployedDim, 1.0)) &&
         "the floor must be the shared shrinkage floor, not a bespoke constant");
  std::cout << "  [ok] compute_variance is identical for c=none/0.99/0.05 (" << none << ")\n";
}

void test_curator_floor_is_order_one_over_d() {
  // The FIX-13 invariant, asserted where the OLD code violated it: the isotropic
  // trace d*D must stay O(1). The retired D = -ln(0.95) = 0.0513 gives a trace of
  // 19.7 at d = 384, and the retired prior D = 1.0 gives 384 -- against a
  // semantic budget of 4. Both are what made the epistemic term swamp meaning.
  const translation::AgentCurator curator{math::FourierMapper(8, 8)};
  for (const int d : {12, 128, kDeployedDim}) {
    const double D = curator.compute_variance(0.95, d);
    const double trace = static_cast<double>(d) * D;
    assert(trace < 2.0 && "isotropic trace must be O(1), not O(d)");
  }
  const double retired_lnc = -std::log(0.95) * kDeployedDim;
  const double retired_prior = 1.0 * kDeployedDim;
  assert(retired_lnc > 19.0 && retired_prior > 383.0);
  std::cout << "  [ok] trace O(1) at d=12/128/384; the retired forms gave "
            << retired_lnc << " and " << retired_prior << "\n";
}

void test_confidence_lives_in_pi_e_with_the_1_over_d() {
  // The other half of FIX-17: confidence is not discarded, it is RELOCATED.
  // s_e = -ln(c)/d, so the TRACE contribution is -ln(c) = O(1) -- the same
  // scaling discipline the stalk floor follows, in the place Q9 puts it.
  const double c = 0.95;
  const double s_e = core::report_variance(c, kDeployedDim);
  assert(close(s_e, -std::log(c) / kDeployedDim));
  const double trace_contribution = s_e * kDeployedDim;
  assert(close(trace_contribution, -std::log(c)) && trace_contribution < 1.0);
  // And an ABSENT confidence contributes no noise at all.
  assert(core::report_variance(std::nullopt, kDeployedDim) == 0.0);
  std::cout << "  [ok] confidence relocated to pi_e: s_e*d = -ln(c) = "
            << trace_contribution << " (O(1))\n";
}

}  // namespace

int main() {
  std::cout << "=== FIX-17: confidence is not a stalk geometry ===\n";
  test_curator_floor_ignores_confidence();
  test_curator_floor_is_order_one_over_d();
  test_confidence_lives_in_pi_e_with_the_1_over_d();

  std::cout << "\n=== FIX-13: the stalk noise-floor contract ===\n";
  test_eps_floor_matches_python();
  test_stalk_floor_is_order_one_over_d();
  test_floor_broadens_with_fewer_observations();
  test_e4_blowup_is_actually_gone();
  test_w2_is_no_longer_euclidean_when_ranks_differ();
  test_max_epistemic_trace_closed_form();
  test_derived_clamp_beats_the_old_1e9_clamp();
  test_e4_guard_refuses_the_old_configuration();
  test_grown_concept_uses_the_floor();

  std::cout << "\n=== FIX-11: operad co-schedulability ===\n";
  test_read_only_node_does_not_poison_the_slice();
  test_co_schedulability_is_order_independent();
  test_two_read_only_globals_share_a_slice();
  test_writing_global_node_still_isolates();
  test_global_mutation_locks_a_later_read_only();
  test_deferred_global_mutation_does_not_leak_its_lock();
  test_overlapping_supports_still_serialise();

  std::cout << "\nAll FIX-11 / FIX-13 tests passed.\n";
  return 0;
}
