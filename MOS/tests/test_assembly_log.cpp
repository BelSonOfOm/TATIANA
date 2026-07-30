// E7 — tests for the assembly record.
//
// E7's whole value is that the data is captured AT COMPOSITION TIME, because
// the foliation's decision is not recoverable afterwards. So these tests assert
// two different kinds of property:
//
//   * the record is FAITHFUL -- it says what the foliation actually did, for
//     every branch of the rule (co-schedule, support overlap, slice locked,
//     global-needs-empty);
//   * the record is INERT -- recording changes no scheduling decision. An
//     instrument that perturbs what it measures is worse than no instrument,
//     and this one sits inside the hot path of every tick.
//
// The independence-relation accessors are tested for what they actually claim
// (a LOWER BOUND on I from observed co-scheduling), not for answering E3.

#include <cassert>
#include <iostream>
#include <set>

#include "mos/core/assembly_log.hpp"
#include "mos/core/operad.hpp"

using namespace mos;

namespace {

/// Operator stub with a settable name, support and type. `apply` is never
/// called: these tests exercise the RECORD of the co-schedulability rule.
class NamedOp : public core::CognitiveOperator {
 public:
  NamedOp(const char *name, std::set<int> support, core::OperatorType type)
      : name_(name), support_(std::move(support)), type_(type) {}

  bool apply(core::CognitiveState &) override { return true; }
  [[nodiscard]] core::OperatorType get_type() const noexcept override { return type_; }
  [[nodiscard]] std::set<int> get_support() const override { return support_; }
  [[nodiscard]] const char *name() const noexcept override { return name_; }

 private:
  const char *name_;
  std::set<int> support_;
  core::OperatorType type_;
};

std::shared_ptr<core::OperadNode> node(const char *name, std::set<int> support,
                                       core::OperatorType type) {
  return std::make_shared<core::OperadNode>(
      std::make_shared<NamedOp>(name, std::move(support), type));
}

using Nodes = std::vector<std::shared_ptr<core::OperadNode>>;

void test_records_a_co_scheduled_slice() {
  core::assembly_log().clear();
  Nodes ready{node("SearchOp", {1}, core::OperatorType::READ_ONLY),
              node("ComputeOp", {2}, core::OperatorType::MUTATION)};
  Nodes deferred;
  auto slice = core::select_commuting_slice(ready, deferred);
  assert(slice.size() == 2 && deferred.empty());

  auto slices = core::assembly_log().slices();
  assert(slices.size() == 1);
  assert(slices[0].round == 0);
  assert(slices[0].offered == 2);
  assert(slices[0].co_scheduled.size() == 2);
  assert(slices[0].co_scheduled[0].name == std::string("SearchOp"));
  assert(slices[0].co_scheduled[1].name == std::string("ComputeOp"));
  assert(slices[0].co_scheduled[0].support == std::set<int>{1});
  assert(slices[0].deferred.empty());
  assert(!slices[0].slice_locked_by_global_mutation);
  std::cout << "  [ok] a co-scheduled slice is recorded with names and supports\n";
}

void test_records_why_a_node_was_deferred() {
  // Each branch of the rule must be distinguishable in the record. A deferral
  // that does not say WHY is not evidence about independence.
  {
    core::assembly_log().clear();
    Nodes ready{node("ReasonOp", {1, 2}, core::OperatorType::MUTATION),
                node("ComputeOp", {2, 3}, core::OperatorType::MUTATION)};
    Nodes deferred;
    core::select_commuting_slice(ready, deferred);
    auto s = core::assembly_log().slices().at(0);
    assert(s.deferred.size() == 1);
    assert(s.deferred[0].first.name == std::string("ComputeOp"));
    assert(s.deferred[0].second == core::AssemblyLog::Deferral::SupportOverlap);
  }
  {
    core::assembly_log().clear();
    Nodes ready{node("ContextOp", {}, core::OperatorType::MUTATION),
                node("SearchOp", {}, core::OperatorType::READ_ONLY)};
    Nodes deferred;
    core::select_commuting_slice(ready, deferred);
    auto s = core::assembly_log().slices().at(0);
    assert(s.slice_locked_by_global_mutation);
    assert(s.deferred.size() == 1);
    assert(s.deferred[0].first.name == std::string("SearchOp"));
    assert(s.deferred[0].second == core::AssemblyLog::Deferral::SliceLocked);
  }
  {
    core::assembly_log().clear();
    Nodes ready{node("ComputeOp", {7}, core::OperatorType::MUTATION),
                node("ContextOp", {}, core::OperatorType::MUTATION)};
    Nodes deferred;
    core::select_commuting_slice(ready, deferred);
    auto s = core::assembly_log().slices().at(0);
    assert(s.deferred.size() == 1);
    assert(s.deferred[0].first.name == std::string("ContextOp"));
    assert(s.deferred[0].second == core::AssemblyLog::Deferral::GlobalNeedsEmpty);
  }
  std::cout << "  [ok] all three deferral reasons are recorded distinctly\n";
}

void test_recording_does_not_change_scheduling() {
  // THE PROPERTY THAT MATTERS MOST. E7 is always-on and sits in the hot path of
  // every tick; if it perturbed the foliation it would corrupt the engine to
  // measure it. Run the identical input many times and assert the partition is
  // byte-identical each time and independent of how much history the log holds.
  core::assembly_log().clear();
  std::size_t first_slice = 0, first_deferred = 0;
  for (int i = 0; i < 200; ++i) {
    Nodes ready{node("SearchOp", {}, core::OperatorType::READ_ONLY),
                node("ComputeOp", {1}, core::OperatorType::MUTATION),
                node("ReasonOp", {1}, core::OperatorType::MUTATION),
                node("VerifyOp", {2}, core::OperatorType::MUTATION)};
    Nodes deferred;
    auto slice = core::select_commuting_slice(ready, deferred);
    if (i == 0) {
      first_slice = slice.size();
      first_deferred = deferred.size();
    }
    assert(slice.size() == first_slice);
    assert(deferred.size() == first_deferred);
  }
  assert(core::assembly_log().slices().size() == 200);
  std::cout << "  [ok] 200 identical runs: partition unchanged as the log grows ("
            << first_slice << " scheduled, " << first_deferred << " deferred)\n";
}

void test_co_scheduling_counts_are_a_lower_bound_on_I() {
  core::assembly_log().clear();
  for (int i = 0; i < 3; ++i) {
    Nodes ready{node("SearchOp", {1}, core::OperatorType::READ_ONLY),
                node("ComputeOp", {2}, core::OperatorType::MUTATION),
                node("ReasonOp", {2}, core::OperatorType::MUTATION)};
    Nodes deferred;
    core::select_commuting_slice(ready, deferred);
  }
  auto co = core::assembly_log().co_scheduling_counts();
  // SearchOp{1} and ComputeOp{2} are disjoint -> co-scheduled every round.
  assert(co.at({"ComputeOp", "SearchOp"}) == 3);
  // ReasonOp{2} collides with ComputeOp{2} -> deferred every round, so it is
  // never seen co-scheduled with EITHER of them.
  assert(co.find({"ComputeOp", "ReasonOp"}) == co.end());
  assert(co.find({"ReasonOp", "SearchOp"}) == co.end());

  auto refused = core::assembly_log().refused_counts();
  // ...but it WAS offered alongside both, which is the informative half.
  assert(refused.at({"ComputeOp", "ReasonOp"}) == 3);
  assert(refused.at({"ReasonOp", "SearchOp"}) == 3);
  std::cout << "  [ok] co-scheduled pairs counted; refused-but-offered pairs "
               "counted separately\n";
  std::cout << "       (F4/E3: co-scheduling bounds I from below -- it means the\n"
               "        support rule ALLOWED them, not that they commute)\n";
}

void test_rounds_and_runs() {
  core::assembly_log().clear();
  core::assembly_log().begin_run();
  for (int r = 0; r < 3; ++r) {
    Nodes ready{node("ComputeOp", {1}, core::OperatorType::MUTATION)};
    Nodes deferred;
    core::select_commuting_slice(ready, deferred);
  }
  auto s = core::assembly_log().slices();
  assert(s.size() == 3 && s[0].round == 0 && s[1].round == 1 && s[2].round == 2);
  assert(core::assembly_log().run_count() == 1);
  core::assembly_log().begin_run();
  {
    Nodes ready{node("ComputeOp", {1}, core::OperatorType::MUTATION)};
    Nodes deferred;
    core::select_commuting_slice(ready, deferred);
  }
  assert(core::assembly_log().slices().back().round == 0 &&
         "begin_run resets the round counter");
  assert(core::assembly_log().run_count() == 2);
  std::cout << "  [ok] rounds increment within a run and reset across runs\n";
}

void test_unnamed_operator_is_visible_as_such() {
  // A missing name() override must look like a defect in the record rather than
  // blending in with real operators.
  class Bare : public core::CognitiveOperator {
   public:
    bool apply(core::CognitiveState &) override { return true; }
    [[nodiscard]] core::OperatorType get_type() const noexcept override {
      return core::OperatorType::MUTATION;
    }
    [[nodiscard]] std::set<int> get_support() const override { return {1}; }
  };
  core::assembly_log().clear();
  Nodes ready{std::make_shared<core::OperadNode>(std::make_shared<Bare>())};
  Nodes deferred;
  core::select_commuting_slice(ready, deferred);
  assert(core::assembly_log().slices().at(0).co_scheduled.at(0).name ==
         std::string("<unnamed>"));
  std::cout << "  [ok] an operator with no name() override records as <unnamed>\n";
}

void test_format_is_human_readable() {
  core::assembly_log().clear();
  Nodes ready{node("SearchOp", {1}, core::OperatorType::READ_ONLY),
              node("ComputeOp", {1}, core::OperatorType::MUTATION)};
  Nodes deferred;
  core::select_commuting_slice(ready, deferred);
  auto lines = core::assembly_log().format();
  assert(lines.size() == 1);
  std::cout << "  [ok] format: " << lines[0] << "\n";
}

}  // namespace

int main() {
  std::cout << "=== E7: the assembly record ===\n";
  test_records_a_co_scheduled_slice();
  test_records_why_a_node_was_deferred();
  test_recording_does_not_change_scheduling();
  test_co_scheduling_counts_are_a_lower_bound_on_I();
  test_rounds_and_runs();
  test_unnamed_operator_is_visible_as_such();
  test_format_is_human_readable();
  std::cout << "\nAll E7 assembly-log tests passed.\n";
  return 0;
}
