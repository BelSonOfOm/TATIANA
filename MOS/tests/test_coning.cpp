// Phase-2 item 7: coning off cycles (Q13).
//
// The claim being shipped is that coning drops dim H^1 by EXACTLY 1, so the
// growth loop terminates in at most b1 attachments and cannot spin. The chord
// alternative Q13 rejected is implemented alongside purely so the comparison is
// measured rather than asserted -- and it does not merely fail to help, it makes
// things worse.

#include <cassert>
#include <iostream>
#include <stdexcept>
#include <vector>

#include "mos/core/coning.hpp"

using namespace mos::core;

namespace {

/// An n-cycle with no filled faces: b1 = 1.
Complex2 ring(int n) {
    std::vector<HodgeVertex> vs;
    for (int i = 0; i < n; ++i) vs.push_back("v" + std::to_string(i));
    std::vector<HodgeEdge> es;
    for (int i = 0; i < n; ++i) es.push_back({vs[i], vs[(i + 1) % n]});
    return Complex2(vs, es);
}

/// Two 4-cycles sharing one vertex: b1 = 2.
Complex2 figure_eight() {
    return Complex2({"c", "a1", "a2", "a3", "b1", "b2", "b3"},
                    {{"c", "a1"}, {"a1", "a2"}, {"a2", "a3"}, {"a3", "c"},
                     {"c", "b1"}, {"b1", "b2"}, {"b2", "b3"}, {"b3", "c"}});
}

void test_betti1_counts_holes() {
    assert(betti1(ring(3)) == 1 && "an unfilled triangle is one hole");
    assert(betti1(ring(7)) == 1);
    assert(betti1(figure_eight()) == 2 && "two independent cycles");

    // A FILLED triangle has no hole -- this is the distinction E5's original
    // design got wrong (one filled triangle has b1 = 0 and can carry no
    // harmonic mass at all).
    const Complex2 filled({"a", "b", "c"}, {{"a", "b"}, {"b", "c"}, {"a", "c"}},
                          {{"a", "b", "c"}});
    assert(betti1(filled) == 0);

    // A tree has no cycles.
    assert(betti1(Complex2({"a", "b", "c"}, {{"a", "b"}, {"b", "c"}})) == 0);
    std::cout << "  [ok] betti1: ring=1, figure-eight=2, filled triangle=0, tree=0\n";
}

void test_coning_kills_exactly_one_class() {
    for (const int n : {3, 4, 5, 8}) {
        const Complex2 cx = ring(n);
        const ConeResult r = cone_off_cycle(cx, cx.vertices(), "apex");
        assert(r.betti1_before == 1);
        assert(r.betti1_after == 0 && "the cone makes the cycle bound");
        assert(r.classes_killed() == 1);
        // The cone adds n spokes and n faces plus one vertex.
        assert(r.complex.num_vertices() == n + 1);
        assert(r.complex.num_edges() == 2 * n);
        assert(r.complex.num_triangles() == n);
    }
    std::cout << "  [ok] coning an n-ring (n=3,4,5,8) drops b1 from 1 to 0\n";
}

void test_coning_kills_exactly_one_not_all() {
    // THE property that makes the growth loop terminate: each attachment removes
    // ONE class. If coning removed all of them the budget claim would be vacuous;
    // if it removed none the loop would spin.
    const Complex2 cx = figure_eight();
    const ConeResult r = cone_off_cycle(cx, {"c", "a1", "a2", "a3"}, "apex");
    assert(r.betti1_before == 2);
    assert(r.betti1_after == 1 && "the OTHER hole must survive");
    assert(r.classes_killed() == 1);

    // And a second attachment finishes the job -- b1 attachments suffice.
    const ConeResult r2 = cone_off_cycle(r.complex, {"c", "b1", "b2", "b3"}, "apex2");
    assert(r2.betti1_after == 0);
    std::cout << "  [ok] figure-eight: 2 -> 1 -> 0, exactly one class per attachment\n";
}

void test_chord_relocates_and_is_worse() {
    // Q13's stated reason for rejecting the chord, measured. On a 4-ring a chord
    // splits one cycle into two and fills neither, so b1 goes UP.
    const Complex2 cx = ring(4);
    const ConeResult r = chord_cycle(cx, "v0", "v2");
    assert(r.betti1_before == 1);
    assert(r.betti1_after == 2 && "a chord SPLITS the cycle; it does not kill it");
    assert(r.classes_killed() == -1 && "negative: the chord made it worse");

    // Coning the same ring does the opposite.
    const ConeResult c = cone_off_cycle(cx, cx.vertices(), "apex");
    assert(c.classes_killed() == 1);
    std::cout << "  [ok] chord: b1 1 -> 2 (WORSE). cone: 1 -> 0. Q13's decision holds.\n";
}

void test_growth_budget_is_bounded_by_b1() {
    // "<= dim H^1 attachments make W reconcilable" -- the growth budget computed
    // from shape, before any LLM call. Verified by exhausting it.
    Complex2 cx = figure_eight();
    const int budget = betti1(cx);
    assert(budget == 2);

    int attachments = 0;
    std::vector<std::vector<HodgeVertex>> cycles{{"c", "a1", "a2", "a3"},
                                                 {"c", "b1", "b2", "b3"}};
    for (const auto& cyc : cycles) {
        if (betti1(cx) == 0) break;
        cx = cone_off_cycle(cx, cyc, "apex" + std::to_string(attachments)).complex;
        ++attachments;
    }
    assert(betti1(cx) == 0);
    assert(attachments <= budget && "the shape-derived budget must not be exceeded");
    std::cout << "  [ok] " << attachments << " attachments cleared b1=" << budget
              << " -- growth budget known before any LLM call\n";
}

void test_cone_output_is_a_valid_complex() {
    // Complex2's constructor enforces downward closure, so a cone whose faces
    // referenced missing edges would throw. Assert the spokes are really there.
    const Complex2 cx = ring(5);
    const ConeResult r = cone_off_cycle(cx, cx.vertices(), "apex");
    for (const auto& v : cx.vertices()) {
        bool found = false;
        try { (void)r.complex.edge_index("apex", v); found = true; }
        catch (const std::invalid_argument&) {}
        assert(found && "every cycle vertex must be joined to the apex");
    }
    std::cout << "  [ok] the cone is a valid closed complex with all spokes present\n";
}

void test_refusals() {
    const Complex2 cx = ring(4);
    bool threw;

    threw = false;
    try { (void)cone_off_cycle(cx, {"v0", "v1"}, "apex"); }
    catch (const std::invalid_argument&) { threw = true; }
    assert(threw && "a 2-vertex 'cycle' must be refused");

    threw = false;
    try { (void)cone_off_cycle(cx, {"v0", "v1", "v0"}, "apex"); }
    catch (const std::invalid_argument&) { threw = true; }
    assert(threw && "a repeated vertex must be refused");

    // v0-v2 is not an edge of a 4-ring, so this is not a cycle in this complex.
    threw = false;
    try { (void)cone_off_cycle(cx, {"v0", "v2", "v1"}, "apex"); }
    catch (const std::invalid_argument&) { threw = true; }
    assert(threw && "a non-cycle must be refused, not silently completed");

    threw = false;
    try { (void)cone_off_cycle(cx, {"v0", "v1", "v2", "v3"}, "v0"); }
    catch (const std::invalid_argument&) { threw = true; }
    assert(threw && "the apex must be a NEW cell");

    threw = false;
    try { (void)cone_off_cycle(cx, {"v0", "v1", "nope"}, "apex"); }
    catch (const std::invalid_argument&) { threw = true; }
    assert(threw && "an unknown vertex must be refused");

    std::cout << "  [ok] short/repeating/non-cycles, colliding apex, unknown vertex refused\n";
}

}  // namespace

int main() {
    std::cout << "=== coning off cycles (Phase-2 item 7, Q13) ===\n";
    test_betti1_counts_holes();
    test_coning_kills_exactly_one_class();
    test_coning_kills_exactly_one_not_all();
    test_chord_relocates_and_is_worse();
    test_growth_budget_is_bounded_by_b1();
    test_cone_output_is_a_valid_complex();
    test_refusals();

    std::cout << "\nALL CONING TESTS PASSED\n";
    return 0;
}
