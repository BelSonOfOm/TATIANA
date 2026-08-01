// Phase 3, stage 0: the two things a tick must publish but used to discard.
//
// WHAT THIS PINS, AND WHY EACH ONE WOULD ROT SILENTLY.
//
//   * combine() takes the WEAKEST verdict. If it ever took the strongest, one
//     passing check could launder a refutation into the store and gamma would
//     be positive for a session that contained a contradiction. Nothing would
//     crash; the store would just quietly absorb false wiring.
//
//   * NO VERDICT is not UNVERIFIABLE. nullopt means no oracle ran; the enum
//     value means one ran and could not decide. Collapsing them would make
//     "we never checked" indistinguishable from "we checked and learned
//     nothing" in every downstream count.
//
//   * retrieved and grown are DIFFERENT SETS. A cover model fitted to `grown`
//     is fitted to growth order, because a concept is grown exactly once. The
//     test asserts they can disagree, so nobody can quietly alias one to the
//     other and still pass.
//
//   * clear_* actually clears. Without a tick boundary, tick t inherits tick
//     t-1's activation and the assembly matrix accumulates instead of sampling.

#include <cassert>
#include <iostream>
#include <optional>
#include <string>
#include <vector>

#include "mos/core/cognitive_state.hpp"
#include "mos/core/verdict.hpp"

using namespace mos::core;

namespace {

void test_combine_takes_the_weakest() {
    assert(combine(Verdict::Verified, Verdict::Refuted) == Verdict::Refuted);
    assert(combine(Verdict::Refuted, Verdict::Verified) == Verdict::Refuted);
    assert(combine(Verdict::Verified, Verdict::Unverifiable) == Verdict::Unverifiable);
    assert(combine(Verdict::Unverifiable, Verdict::Refuted) == Verdict::Refuted);
    assert(combine(Verdict::Verified, Verdict::Verified) == Verdict::Verified);

    // Commutative and associative, so the order operators happen to run in
    // inside a foliation slice cannot change the tick's verdict.
    const Verdict all[] = {Verdict::Verified, Verdict::Unverifiable, Verdict::Refuted};
    for (Verdict a : all) {
        for (Verdict b : all) {
            assert(combine(a, b) == combine(b, a));
            for (Verdict c : all) {
                assert(combine(combine(a, b), c) == combine(a, combine(b, c)));
            }
        }
    }
    std::cout << "  combine takes the weakest, commutatively and associatively\n";
}

void test_no_verdict_is_not_unverifiable() {
    CognitiveState s;
    assert(!s.tick_verdict().has_value());   // nothing ran

    s.note_verdict(Verdict::Unverifiable);
    assert(s.tick_verdict().has_value());
    assert(*s.tick_verdict() == Verdict::Unverifiable);

    s.clear_tick_verdict();
    assert(!s.tick_verdict().has_value());
    std::cout << "  nullopt (no oracle) stays distinct from UNVERIFIABLE\n";
}

void test_verdict_accumulates_weakest_regardless_of_order() {
    {
        CognitiveState s;
        s.note_verdict(Verdict::Verified);
        s.note_verdict(Verdict::Refuted);
        s.note_verdict(Verdict::Verified);
        assert(*s.tick_verdict() == Verdict::Refuted);
    }
    {
        CognitiveState s;   // same multiset, reversed order
        s.note_verdict(Verdict::Refuted);
        s.note_verdict(Verdict::Verified);
        s.note_verdict(Verdict::Verified);
        assert(*s.tick_verdict() == Verdict::Refuted);
    }
    std::cout << "  one refutation survives any number of passing checks\n";
}

void test_to_string_round_trips_every_value() {
    // E7 stores the STRING, so a wrong mapping here corrupts the column
    // silently -- every record still parses, just as the wrong verdict.
    assert(std::string(to_string(Verdict::Verified)) == "VERIFIED");
    assert(std::string(to_string(Verdict::Refuted)) == "REFUTED");
    assert(std::string(to_string(Verdict::Unverifiable)) == "UNVERIFIABLE");
    std::cout << "  to_string maps all three values correctly\n";
}

void test_retrieved_and_grown_are_separate_sets() {
    CognitiveState s;
    const std::vector<double> g(4, 0.5);

    s.note_retrieved("stored_concept_A");
    s.note_retrieved("stored_concept_B");
    s.grow_concept("fresh_concept", g, "SEARCH");

    const auto retrieved = s.tick_retrieved();
    const auto grown = s.tick_grown();

    assert(retrieved.size() == 2);
    assert(retrieved[0] == "stored_concept_A");
    assert(retrieved[1] == "stored_concept_B");

    assert(grown.size() == 1);
    assert(grown[0] == "fresh_concept");

    // The sets are disjoint here, which is the point: growth is not retrieval.
    for (const auto& r : retrieved) {
        for (const auto& gr : grown) assert(r != gr);
    }
    std::cout << "  retrieved and grown are recorded as separate sets\n";
}

void test_retrieval_is_deduplicated() {
    // Two SearchOps in one tick hitting the same stored concept is ONE
    // co-activation. The matrix is binary, so a duplicate would not change
    // x_tc -- but it would inflate any count taken off the record later.
    CognitiveState s;
    s.note_retrieved("same");
    s.note_retrieved("same");
    s.note_retrieved("other");
    s.note_retrieved("same");

    const auto r = s.tick_retrieved();
    assert(r.size() == 2);
    assert(r[0] == "same" && r[1] == "other");   // insertion order preserved
    std::cout << "  repeated retrieval of one concept counts once\n";
}

void test_empty_name_is_refused() {
    // An unnamed concept cannot be a column of the assembly matrix, so it must
    // not silently become one.
    CognitiveState s;
    s.note_retrieved("");
    assert(s.tick_retrieved().empty());
    std::cout << "  an unnamed retrieval is refused, not recorded blank\n";
}

void test_clear_resets_the_tick_boundary() {
    CognitiveState s;
    const std::vector<double> g(4, 0.5);
    s.note_retrieved("a");
    s.grow_concept("b", g, "SEARCH");
    assert(!s.tick_retrieved().empty() && !s.tick_grown().empty());

    s.clear_tick_activation();
    assert(s.tick_retrieved().empty());
    assert(s.tick_grown().empty());

    // And the state is reusable afterwards -- clear must not poison it.
    s.note_retrieved("c");
    assert(s.tick_retrieved().size() == 1);
    std::cout << "  clear_tick_activation resets both sets and stays usable\n";
}

void test_growth_records_even_without_an_organ() {
    // organ tagging drives pi_v fusion, not the birth register. A concept grown
    // untagged still exists, so alive_mask still needs its birth tick.
    CognitiveState s;
    const std::vector<double> g(4, 0.25);
    s.grow_concept("untagged", g, "");
    assert(s.tick_grown().size() == 1);
    assert(s.tick_grown()[0] == "untagged");
    std::cout << "  an untagged concept is still recorded as born\n";
}

void test_empty_geometry_grows_nothing() {
    // grow_concept returns early on empty geometry. It must not leave a birth
    // record for a concept it declined to create, or the mask would mark a
    // nonexistent concept alive.
    CognitiveState s;
    s.grow_concept("never_created", {}, "SEARCH");
    assert(s.tick_grown().empty());
    std::cout << "  a refused growth leaves no birth record\n";
}

}  // namespace

int main() {
    std::cout << "test_tick_record\n";
    test_combine_takes_the_weakest();
    test_no_verdict_is_not_unverifiable();
    test_verdict_accumulates_weakest_regardless_of_order();
    test_to_string_round_trips_every_value();
    test_retrieved_and_grown_are_separate_sets();
    test_retrieval_is_deduplicated();
    test_empty_name_is_refused();
    test_clear_resets_the_tick_boundary();
    test_growth_records_even_without_an_organ();
    test_empty_geometry_grows_nothing();
    std::cout << "all tick-record tests passed\n";
    return 0;
}
