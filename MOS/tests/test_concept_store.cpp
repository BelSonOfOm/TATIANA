// Phase 3, stage 3a: the bridge, and the learning rule that makes the
// consolidation loop capable of moving anything.
//
// THE TEST THIS FILE EXISTS FOR is test_learned_map_survives_crystallise.
// align_map could be perfectly correct as geometry and still be useless: if it
// returns an ODD number of reflections it lands in the other component of O(d)
// from the identity the store starts at, crystallise refuses to interpolate
// across that gap, and the learned map never reaches K. Q(t) would sit at zero
// forever while every other test in the suite passed. That failure is invisible
// from anywhere except here.

#include <cassert>
#include <cmath>
#include <iostream>
#include <string>
#include <vector>

#include "mos/core/concept_store.hpp"
#include "mos/core/two_complex.hpp"

using namespace mos::core;

namespace {

constexpr int kD = 16;

Eigen::VectorXd unit(int d, unsigned seed) {
    Eigen::VectorXd v(d);
    unsigned s = seed * 2654435761u + 1u;
    for (int i = 0; i < d; ++i) {
        s = s * 1664525u + 1013904223u;
        v(i) = (static_cast<double>(s % 2000u) / 1000.0) - 1.0;
    }
    if (v.norm() < 1e-9) v(0) = 1.0;
    return v.normalized();
}

void test_align_map_actually_aligns() {
    for (unsigned s = 0; s < 25; ++s) {
        const Eigen::VectorXd a = unit(kD, s * 2 + 1);
        const Eigen::VectorXd b = unit(kD, s * 2 + 2);
        const HouseholderMap R = align_map(a, b);
        const Eigen::VectorXd got = R.apply(a);
        assert((got - b).norm() < 1e-9);
    }
    std::cout << "  align_map carries a onto b, 25/25 random pairs\n";
}

void test_align_map_is_orthogonal() {
    // A restriction map that is not orthogonal breaks the ||R|| <= 1 hypothesis
    // the whole Hodge argument rests on (logbook F2).
    const Eigen::VectorXd a = unit(kD, 11), b = unit(kD, 12);
    const Eigen::MatrixXd D = align_map(a, b).dense();
    const Eigen::MatrixXd I = Eigen::MatrixXd::Identity(kD, kD);
    assert((D.transpose() * D - I).norm() < 1e-9);
    assert((D * D.transpose() - I).norm() < 1e-9);
    std::cout << "  align_map is exactly orthogonal (R^T R = I)\n";
}

void test_align_map_has_even_parity() {
    // det = (-1)^m. Even m keeps the learned map in the identity's component,
    // which is what makes it crystallisable at all.
    for (unsigned s = 0; s < 12; ++s) {
        const HouseholderMap R = align_map(unit(kD, s + 40), unit(kD, s + 80));
        assert(R.m() % 2 == 0);
        const double det = R.dense().determinant();
        assert(std::abs(det - 1.0) < 1e-9);
    }
    std::cout << "  align_map always has even reflection count, det = +1\n";
}

void test_learned_map_survives_crystallise() {
    // THE ONE THAT MATTERS. Learn a map, blend it into an identity store by
    // gamma, and require that the store MOVED -- and moved partway, not all the
    // way, because gamma < 1.
    const Eigen::VectorXd a = unit(kD, 3), b = unit(kD, 4);
    const HouseholderMap learned = align_map(a, b);
    const HouseholderMap start = HouseholderMap::identity(kD);

    const double gamma = gamma_nu(Verdict::Verified);   // 0.05
    const HouseholderMap blended = crystallise(start, learned, gamma);

    const double moved = (blended.dense() - start.dense()).norm();
    const double remaining = (blended.dense() - learned.dense()).norm();
    const double total = (learned.dense() - start.dense()).norm();

    assert(total > 1e-6);        // there was something to learn
    assert(moved > 1e-9);        // the store actually moved
    assert(remaining > 1e-9);    // but not all the way, since gamma < 1
    assert(moved < total);
    std::cout << "  learned map crystallises: moved " << moved
              << " of " << total << " at gamma=" << gamma << "\n";
}

void test_refuted_leaves_the_store_bit_identical() {
    ConceptStore cs(kD);
    cs.observe({"alpha", "beta"});
    Store& K = cs.store();

    const HodgeEdge e{"alpha", "beta"};
    Working W = i_star(K, {"alpha", "beta"});
    W.restriction.insert_or_assign(e, align_map(unit(kD, 5), unit(kD, 6)));
    W.touch(e);

    const Eigen::MatrixXd before = K.restriction.at(e).dense();
    const int modified = i_shriek(K, W, gamma_nu(Verdict::Refuted));
    const Eigen::MatrixXd after = K.restriction.at(e).dense();

    assert(modified == 0);
    assert((before - after).norm() == 0.0);   // EXACTLY, not approximately
    std::cout << "  a refuted session leaves K bit-identical\n";
}

void test_Q_rises_off_zero_only_after_learning() {
    // Q = 0 IS the constant sheaf: every concept means the same in every
    // context, i.e. nothing learned. This is the engine-level acceptance test
    // for the whole consolidation loop.
    ConceptStore cs(kD);
    cs.observe({"ring", "ideal", "module"});
    Store& K = cs.store();
    assert(K.Q() == 0.0);          // fresh edges are identities

    Working W = i_star(K, {"ring", "ideal", "module"});
    int learned = 0;
    for (const auto& e : W.complex.edges()) {
        W.restriction.insert_or_assign(
            e, align_map(unit(kD, 100 + learned), unit(kD, 200 + learned)));
        W.touch(e);
        ++learned;
    }
    assert(learned > 0);

    const int modified = i_shriek(K, W, gamma_nu(Verdict::Verified));
    assert(modified == learned);
    assert(K.Q() > 0.0);
    std::cout << "  Q rose off zero after a verified session: Q=" << K.Q()
              << " over " << modified << " edges\n";
}

void test_untouched_edges_never_move() {
    ConceptStore cs(kD);
    cs.observe({"p", "q", "r"});
    Store& K = cs.store();

    Working W = i_star(K, {"p", "q", "r"});
    const HodgeEdge touched = W.complex.edges().front();
    W.restriction.insert_or_assign(touched, align_map(unit(kD, 7), unit(kD, 8)));
    W.touch(touched);

    std::map<HodgeEdge, Eigen::MatrixXd> before;
    for (const auto& [e, R] : K.restriction) before[e] = R.dense();

    i_shriek(K, W, gamma_nu(Verdict::Verified));

    for (const auto& [e, R] : K.restriction) {
        const double moved = (R.dense() - before.at(e)).norm();
        if (e == touched) assert(moved > 1e-9);
        else assert(moved == 0.0);   // extension by ZERO, bit-identical
    }
    std::cout << "  i_! moved only the touched edge; the rest are bit-identical\n";
}

void test_store_grows_and_keeps_what_it_learned() {
    ConceptStore cs(kD);
    cs.observe({"a", "b"});
    Store& K1 = cs.store();
    const HodgeEdge ab{"a", "b"};

    Working W = i_star(K1, {"a", "b"});
    W.restriction.insert_or_assign(ab, align_map(unit(kD, 21), unit(kD, 22)));
    W.touch(ab);
    i_shriek(K1, W, gamma_nu(Verdict::Verified));
    const Eigen::MatrixXd learned = K1.restriction.at(ab).dense();
    assert((learned - Eigen::MatrixXd::Identity(kD, kD)).norm() > 1e-9);

    // Now the store GROWS. The rebuilt Complex2 must not discard the sheaf.
    cs.observe({"b", "c", "d"});
    Store& K2 = cs.store();
    assert(cs.num_concepts() == 4);
    assert((K2.restriction.at(ab).dense() - learned).norm() == 0.0);
    std::cout << "  growing the store preserves already-learned edges exactly\n";
}

void test_coactivation_is_symmetric_and_counted() {
    ConceptStore cs(kD);
    cs.observe({"x", "y"});
    cs.observe({"y", "x"});          // same pair, opposite order
    assert(cs.coactivation_count("x", "y") == 2);
    assert(cs.coactivation_count("y", "x") == 2);
    assert(cs.num_edges() == 1);      // ONE edge, not two
    std::cout << "  (u,v) and (v,u) are one edge with a shared count\n";
}

void test_single_concept_tick_makes_no_edge() {
    ConceptStore cs(kD);
    cs.observe({"lonely"});
    assert(cs.num_concepts() == 1);
    assert(cs.num_edges() == 0);   // one concept co-activates with nothing
    cs.observe({});
    assert(cs.num_concepts() == 1);
    std::cout << "  a one-concept tick adds a vertex and no edge\n";
}

void test_degenerate_inputs_are_refused() {
    bool threw = false;
    try { (void)align_map(Eigen::VectorXd::Zero(kD), unit(kD, 1)); }
    catch (const std::invalid_argument&) { threw = true; }
    assert(threw);

    threw = false;
    try { (void)align_map(unit(kD, 1), unit(8, 2)); }
    catch (const std::invalid_argument&) { threw = true; }
    assert(threw);

    // Identical directions: nothing to learn, so the identity, not a throw.
    const Eigen::VectorXd a = unit(kD, 9);
    assert(align_map(a, a * 3.0).m() == 0);
    std::cout << "  zero and mismatched vectors are refused; a==b is the identity\n";
}

void test_antipodal_pair_is_handled() {
    const Eigen::VectorXd a = unit(kD, 33);
    const HouseholderMap R = align_map(a, -a);
    assert((R.apply(a) + a).norm() < 1e-9);
    assert(R.m() % 2 == 0);
    assert(std::abs(R.dense().determinant() - 1.0) < 1e-9);
    std::cout << "  the antipodal case rotates rather than picking a direction by accident\n";
}

}  // namespace

int main() {
    std::cout << "test_concept_store\n";
    test_align_map_actually_aligns();
    test_align_map_is_orthogonal();
    test_align_map_has_even_parity();
    test_antipodal_pair_is_handled();
    test_degenerate_inputs_are_refused();
    test_learned_map_survives_crystallise();
    test_refuted_leaves_the_store_bit_identical();
    test_untouched_edges_never_move();
    test_Q_rises_off_zero_only_after_learning();
    test_store_grows_and_keeps_what_it_learned();
    test_coactivation_is_symmetric_and_counted();
    test_single_concept_tick_makes_no_edge();
    std::cout << "all concept-store tests passed\n";
    return 0;
}
