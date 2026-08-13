// P1 — `support` RESOLUTION: LET THE DAG NAME WHAT IT ACTS ON.
//
// THE OBSERVABLE THAT PROVES THE FIX LANDED, stated in SPEC_P1_TO_P4 before any
// code was written: "A DAG whose nodes name disjoint concept sets foliates into
// more than one slice. Today it cannot."
//
// These tests use the REAL primitives rather than a stub operator, and that is
// the entire point. `test_stalk_floor.cpp` already covers the co-schedulability
// RULE with a `StubOp` whose support is settable -- and it passed throughout,
// because the rule was never the broken part. What was broken is that the real
// operators never reached that rule with anything to say: `SearchOp` returned
// {}, `ComputeOp`/`VerifyOp`/`ContextOp` returned {0}, `ReasonOp` returned {1},
// hard-coded, regardless of what the planner had named. A stub cannot detect
// that, which is why the defect survived a passing foliation suite.

#include "mos/core/operad.hpp"
#include "mos/operators/primitives.hpp"

#include <cassert>
#include <iostream>
#include <memory>
#include <set>
#include <vector>

using namespace mos;

namespace {

std::vector<std::vector<std::shared_ptr<core::OperadNode>>> foliate_all(
    std::vector<std::shared_ptr<core::OperadNode>> ready) {
  std::vector<std::vector<std::shared_ptr<core::OperadNode>>> slices;
  while (!ready.empty()) {
    std::vector<std::shared_ptr<core::OperadNode>> deferred;
    auto slice = core::select_commuting_slice(ready, deferred);
    assert(!slice.empty() && "a slice must make progress or this loop spins");
    slices.push_back(std::move(slice));
    ready = std::move(deferred);
  }
  return slices;
}

/// A ComputeOp scoped to the concepts the planner named. `apply` is never
/// called here, so the null LanguageKernel is never dereferenced -- these tests
/// are about `get_support()` and the foliation it feeds.
std::shared_ptr<core::OperadNode> compute_on(std::set<int> support) {
  auto op = std::make_shared<operators::ComputeOp>("payload", nullptr);
  op->set_support(std::move(support));
  return std::make_shared<core::OperadNode>(op);
}

std::shared_ptr<core::OperadNode> reason_on(std::set<int> support) {
  auto op = std::make_shared<operators::ReasonOp>("premise", nullptr);
  op->set_support(std::move(support));
  return std::make_shared<core::OperadNode>(op);
}

std::size_t total_nodes(
    const std::vector<std::vector<std::shared_ptr<core::OperadNode>>>& slices) {
  std::size_t n = 0;
  for (const auto& s : slices) n += s.size();
  return n;
}

// -----------------------------------------------------------------------------

void test_disjoint_supports_foliate_into_one_parallel_slice() {
  // Three mutations on pairwise-disjoint concept sets. Nothing they touch
  // overlaps, so all three commute and belong in ONE slice -- i.e. they run in
  // parallel, which is what the ThreadPool exists for.
  //
  // BEFORE P1 all three returned {0} and this was three slices of one.
  auto slices = foliate_all({
      compute_on({10, 11}),
      compute_on({20, 21}),
      compute_on({30, 31}),
  });

  assert(slices.size() == 1);
  assert(slices[0].size() == 3);
  std::cout << "  [ok] three disjoint supports co-schedule in ONE slice\n";
}

void test_overlapping_supports_still_serialise() {
  // The safety property must survive the fix. These two share concept 11, so
  // they genuinely conflict and must NOT be co-scheduled.
  auto slices = foliate_all({
      compute_on({10, 11}),
      compute_on({11, 12}),
  });

  assert(slices.size() == 2);
  assert(slices[0].size() == 1);
  assert(slices[1].size() == 1);
  std::cout << "  [ok] overlapping supports still serialise\n";
}

void test_mixed_operator_types_commute_on_disjoint_concepts() {
  // Scoping is a property of the SUPPORT, not of the OpType. A ComputeOp and a
  // ReasonOp on disjoint concepts commute; before P1 they commuted only by the
  // accident that their hard-coded constants happened to be {0} and {1}, and
  // two ComputeOps never did.
  auto slices = foliate_all({
      compute_on({100}),
      reason_on({200}),
      compute_on({300}),
  });

  assert(slices.size() == 1);
  assert(slices[0].size() == 3);
  std::cout << "  [ok] different OpTypes commute on disjoint concepts\n";
}

void test_the_regression_this_fix_is_about() {
  // THE DEFECT, PINNED. Unscoped mutations report the legacy constant {0}, so
  // they all collide and the foliation degenerates to one node per slice. This
  // is what EVERY DAG looked like before P1, whatever the planner intended.
  auto a = std::make_shared<core::OperadNode>(
      std::make_shared<operators::ComputeOp>("a", nullptr));
  auto b = std::make_shared<core::OperadNode>(
      std::make_shared<operators::ComputeOp>("b", nullptr));
  auto c = std::make_shared<core::OperadNode>(
      std::make_shared<operators::ComputeOp>("c", nullptr));

  auto unscoped = foliate_all({a, b, c});
  assert(unscoped.size() == 3 && "unscoped mutations must still serialise");

  // The same three nodes, scoped: one slice. Same operators, same rule, and the
  // only thing that changed is that they can now say what they act on.
  auto scoped = foliate_all({compute_on({1}), compute_on({2}), compute_on({3})});
  assert(scoped.size() == 1);

  std::cout << "  [ok] unscoped: " << unscoped.size() << " slices; "
            << "scoped: " << scoped.size() << " slice -- the P1 observable\n";
}

void test_empty_resolved_support_is_a_global_mutation() {
  // "The planner named concepts and none of them resolved" is NOT the same as
  // "the planner named nothing", but both read as global at the scheduler: an
  // operator that cannot say what it touches might touch anything. That is the
  // conservative answer and it is deliberately preserved -- P1 removes the
  // silence, not the safety.
  auto op = std::make_shared<operators::ComputeOp>("payload", nullptr);
  op->set_support({});
  assert(op->has_explicit_support());
  assert(op->get_support().empty());

  auto slices = foliate_all({
      std::make_shared<core::OperadNode>(op),
      compute_on({7}),
  });
  assert(slices.size() == 2 && "a global mutation must run isolated");
  std::cout << "  [ok] empty resolved support still means global mutation\n";
}

void test_unscoped_operators_keep_their_legacy_support() {
  // Operators built outside a DAG (kernel.tick()'s auto-SearchOp, and every
  // existing test) never call set_support, and must behave exactly as before.
  operators::SearchOp search("q", nullptr, nullptr);
  operators::ComputeOp compute("c", nullptr);
  operators::ReasonOp reason("r", nullptr);
  operators::RespondOp respond("resp");
  operators::VerifyOp verify("python check.py");
  operators::ContextOp context("ctx", {});

  assert(!search.has_explicit_support());
  assert(search.get_support() == std::set<int>({}));
  assert(compute.get_support() == std::set<int>({0}));
  assert(reason.get_support() == std::set<int>({1}));
  assert(respond.get_support() == std::set<int>({}));
  assert(verify.get_support() == std::set<int>({0}));
  assert(context.get_support() == std::set<int>({0}));
  std::cout << "  [ok] unscoped operators keep their legacy constants\n";
}

void test_provisional_negative_ids_scope_correctly() {
  // Concepts the store has never seen get STABLE NEGATIVE ids on the Python
  // side (concept_resolver.provisional_id), so they cannot alias a real rowid
  // -- AUTOINCREMENT starts at 1 -- while still supporting set intersection.
  //
  // Two nodes about the same unseen concept must conflict; two about different
  // unseen concepts must not. Dropping unresolved names instead would collapse
  // both to an empty support and lose the distinction entirely.
  auto same = foliate_all({compute_on({-42}), compute_on({-42})});
  assert(same.size() == 2 && "same unseen concept => must not co-schedule");

  auto different = foliate_all({compute_on({-42}), compute_on({-99})});
  assert(different.size() == 1 && "different unseen concepts => co-schedule");

  // And a provisional id never collides with a resolved one.
  auto mixed = foliate_all({compute_on({-42}), compute_on({42})});
  assert(mixed.size() == 1);
  assert(total_nodes(mixed) == 2);
  std::cout << "  [ok] provisional negative ids scope without aliasing\n";
}

}  // namespace

int main() {
  std::cout << "== P1: the DAG can name what it acts on ==\n";
  test_disjoint_supports_foliate_into_one_parallel_slice();
  test_overlapping_supports_still_serialise();
  test_mixed_operator_types_commute_on_disjoint_concepts();
  test_the_regression_this_fix_is_about();
  test_empty_resolved_support_is_a_global_mutation();
  test_unscoped_operators_keep_their_legacy_support();
  test_provisional_negative_ids_scope_correctly();
  std::cout << "ALL P1 SUPPORT TESTS PASSED\n";
  return 0;
}
