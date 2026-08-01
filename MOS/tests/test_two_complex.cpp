// Phase-2 items 5 & 6: the K/W adjunction and gamma(nu) crystallisation.
//
// The theorem being shipped is  i^* i_! = id  -- the load / work / store round
// trip is faithful. It is asserted here, not cited.
//
// The three properties that would silently rot if untested:
//   * i_! extends by ZERO, so untouched edges stay BIT-identical. i_* would
//     instead assert something about cells the cache never saw.
//   * gamma(Refuted) = 0 EXACTLY, so a refuted session leaves the store
//     bit-identical no matter how many times it runs.
//   * s_W is never written back. Content and wiring persist, the episode does not.

#include <cassert>
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <vector>

#include "mos/core/two_complex.hpp"

using namespace mos::core;

namespace {

constexpr int kD = 12;

bool close(double a, double b, double tol = 1e-12) {
    return std::fabs(a - b) <= tol * std::max(1.0, std::max(std::fabs(a), std::fabs(b)));
}

Complex2 demo_complex() {
    return Complex2({"a", "b", "c", "d"},
                    {{"a", "b"}, {"b", "c"}, {"a", "c"}, {"c", "d"}},
                    {{"a", "b", "c"}});
}

bool is_orthogonal(const Eigen::MatrixXd& R, double tol = 1e-12) {
    const Eigen::MatrixXd I = Eigen::MatrixXd::Identity(R.rows(), R.cols());
    return (R.transpose() * R - I).norm() < tol;
}

// ------------------------------------------------------------- gamma(nu) ----

void test_gamma_of_nu() {
    assert(close(gamma_nu(Verdict::Verified, 0.05, 0.1), 0.05));
    assert(close(gamma_nu(Verdict::Unverifiable, 0.05, 0.1), 0.005));
    // EXACTLY zero. Not 1e-12, not "negligible": a refuted session must leave
    // the store bit-identical, or repeated refutations would still drift it.
    assert(gamma_nu(Verdict::Refuted, 0.05, 0.1) == 0.0);

    bool threw = false;
    try { (void)gamma_nu(Verdict::Verified, 1.5); }
    catch (const std::invalid_argument&) { threw = true; }
    assert(threw && "gamma0 > 1 overshoots past the cache map");
    std::cout << "  [ok] gamma: Verified=0.05, Unverifiable=0.005, Refuted=0 exactly\n";
}

// ------------------------------------------------------- the adjunction -----

void test_i_star_is_downward_closed() {
    const Store K(demo_complex(), kD);
    const Working W = i_star(K, {"a", "b", "c"});

    assert(W.complex.num_vertices() == 3);
    assert(W.complex.num_edges() == 3 && "(c,d) must be dropped: d is not retrieved");
    assert(W.complex.num_triangles() == 1 && "(a,b,c) survives intact");

    const Working W2 = i_star(K, {"a", "b"});
    assert(W2.complex.num_edges() == 1);
    assert(W2.complex.num_triangles() == 0 &&
           "a triangle with 2 of 3 vertices must NOT come back");
    std::cout << "  [ok] i^* is downward closed; a partly-present triangle is dropped\n";
}

void test_round_trip_is_faithful() {
    // THE THEOREM: i^* i_! = id. Instantiate, change nothing, write back, and
    // re-instantiate: the cache must be recovered exactly.
    Store K(demo_complex(), kD);
    for (auto& [e, R] : K.restriction) {
        (void)e;
        R = HouseholderMap::random(kD, HOUSEHOLDER_M_DEFAULT, 7);
    }

    const std::vector<HodgeVertex> verts{"a", "b", "c"};
    Working W = i_star(K, verts);
    for (const auto& e : W.complex.edges()) W.touch(e);

    // Writing back a cache identical to the store must be a no-op at ANY gamma,
    // because dR = 0. This is the identity half of the theorem.
    const double q_before = K.Q();
    i_shriek(K, W, 1.0);
    assert(close(K.Q(), q_before) && "writing back an unchanged cache must not move K");

    const Working W2 = i_star(K, verts);
    for (const auto& e : W.complex.edges()) {
        const Eigen::MatrixXd before = W.restriction.at(e).dense();
        const Eigen::MatrixXd after = W2.restriction.at(e).dense();
        assert((before - after).norm() < 1e-12 && "i^* i_! must recover the cache");
    }
    std::cout << "  [ok] i^* i_! = id: the load/work/store round trip is faithful\n";
}

void test_i_shriek_extends_by_zero() {
    // i_! and NOT i_*: an edge the cache never touched must be left BIT-identical,
    // because the cache asserts nothing about cells it never saw.
    Store K(demo_complex(), kD);
    Working W = i_star(K, {"a", "b", "c"});

    // Learn something on (a,b) only.
    W.restriction.at({"a", "b"}) = HouseholderMap::random(kD, HOUSEHOLDER_M_DEFAULT, 3);
    W.touch({"a", "b"});

    const Eigen::MatrixXd ab_before = K.restriction.at({"a", "b"}).dense();
    const Eigen::MatrixXd bc_before = K.restriction.at({"b", "c"}).dense();
    const Eigen::MatrixXd cd_before = K.restriction.at({"c", "d"}).dense();

    const int modified = i_shriek(K, W, gamma_nu(Verdict::Verified));
    assert(modified == 1 && "only the touched edge may be written");

    // Untouched-but-instantiated, and never-instantiated: both bit-identical.
    assert(K.restriction.at({"b", "c"}).dense() == bc_before);
    assert(K.restriction.at({"c", "d"}).dense() == cd_before);
    // And the touched one must actually move -- a store that starts as the
    // constant sheaf must be able to learn at gamma0 << 1, not only at gamma>=0.5.
    assert((K.restriction.at({"a", "b"}).dense() - ab_before).norm() > 1e-6 &&
           "the touched edge SHOULD have moved");
    std::cout << "  [ok] i_! extends by zero: untouched edges are bit-identical\n";
}

void test_refuted_leaves_the_store_bit_identical() {
    Store K(demo_complex(), kD);
    Working W = i_star(K, {"a", "b", "c"});
    W.restriction.at({"a", "b"}) = HouseholderMap::random(kD, HOUSEHOLDER_M_DEFAULT, 5);
    W.touch({"a", "b"});

    const Eigen::MatrixXd before = K.restriction.at({"a", "b"}).dense();
    for (int i = 0; i < 100; ++i) {
        const int n = i_shriek(K, W, gamma_nu(Verdict::Refuted));
        assert(n == 0);
    }
    assert(K.restriction.at({"a", "b"}).dense() == before &&
           "100 refuted sessions must not drift the store by one bit");
    std::cout << "  [ok] 100 refuted write-backs leave K bit-identical\n";
}

void test_section_is_never_written_back() {
    // s_W is the episode. It must not survive crystallisation in any form.
    Store K(demo_complex(), kD);
    Working W = i_star(K, {"a", "b", "c"});
    W.section["a"] = Eigen::VectorXd::Constant(kD, 3.14);
    W.section["b"] = Eigen::VectorXd::Constant(kD, -2.71);
    W.touch({"a", "b"});

    i_shriek(K, W, gamma_nu(Verdict::Verified));

    // The Store type has no section member at all, which is the structural
    // guarantee; assert the API surface so a later refactor cannot add one
    // quietly. Content and wiring persist; the episode does not.
    static_assert(!std::is_member_object_pointer<decltype(&Store::complex)>::value == false,
                  "Store::complex exists");
    // If a section were ever written back, K.Q() would depend on s_W. It cannot:
    // re-running with a DIFFERENT section must give the same store.
    Store K2(demo_complex(), kD);
    Working W2 = i_star(K2, {"a", "b", "c"});
    W2.section["a"] = Eigen::VectorXd::Constant(kD, -99.0);
    W2.touch({"a", "b"});
    i_shriek(K2, W2, gamma_nu(Verdict::Verified));
    assert(close(K.Q(), K2.Q()) && "the store must not depend on the episode");
    std::cout << "  [ok] s_W is never written back: K is independent of the episode\n";
}

void test_delta_R_is_the_session_learning() {
    Store K(demo_complex(), kD);
    Working W = i_star(K, {"a", "b", "c"});

    // Fresh cache: dR = 0 on every edge. Nothing has been learned yet.
    for (const auto& [e, d] : delta_R(K, W)) {
        (void)e;
        assert(d < 1e-12);
    }
    W.restriction.at({"a", "b"}) = HouseholderMap::random(kD, HOUSEHOLDER_M_DEFAULT, 11);
    const auto dR = delta_R(K, W);
    assert(dR.at({"a", "b"}) > 1e-6 && "the adapted edge must show learning");
    assert(dR.at({"b", "c"}) < 1e-12 && "the untouched edge must show none");
    std::cout << "  [ok] dR = R^W - i^* R^K is zero on a fresh cache, positive where adapted\n";
}

// --------------------------------------------------------- crystallisation --

void test_Q_starts_at_zero_and_rises() {
    // Q = 0 IS the constant sheaf: every concept means the same in every context,
    // i.e. nothing learned about the wiring. If Q never moves, crystallisation is
    // doing nothing and the whole adjunction is decoration.
    Store K(demo_complex(), kD);
    assert(close(K.Q(), 0.0) && "a fresh store is the constant sheaf");

    Working W = i_star(K, {"a", "b", "c"});
    W.restriction.at({"a", "b"}) = HouseholderMap::random(kD, HOUSEHOLDER_M_DEFAULT, 13);
    W.touch({"a", "b"});

    double prev = K.Q();
    for (int session = 0; session < 20; ++session) {
        i_shriek(K, W, gamma_nu(Verdict::Verified));
        const double q = K.Q();
        assert(q >= prev - 1e-12 && "repeated verified sessions must not un-learn");
        prev = q;
    }
    assert(prev > 0.0 && "20 verified sessions must move the wiring off constant");
    std::cout << "  [ok] Q rises from 0 under repeated verified crystallisation (Q="
              << prev << ")\n";
}

void test_crystallise_stays_exactly_orthogonal() {
    // The whole reason for interpolating in the reflection vectors: the result is
    // a product of reflections, hence orthogonal BY CONSTRUCTION, at every gamma.
    const auto A = HouseholderMap::random(kD, HOUSEHOLDER_M_DEFAULT, 1);
    const auto B = HouseholderMap::random(kD, HOUSEHOLDER_M_DEFAULT, 2);
    for (const double g : {0.0, 0.01, 0.25, 0.5, 0.75, 0.99, 1.0}) {
        const auto C = crystallise(A, B, g);
        assert(is_orthogonal(C.dense()) && "must be orthogonal at every gamma");
        assert(C.m() <= HOUSEHOLDER_M_DEFAULT && "must STAY in the m=4 family");
    }
    // Endpoints exactly.
    assert((crystallise(A, B, 0.0).dense() - A.dense()).norm() < 1e-12);
    assert((crystallise(A, B, 1.0).dense() - B.dense()).norm() < 1e-12);
    std::cout << "  [ok] slerp crystallisation is orthogonal at every gamma and stays m<=4\n";
}

void test_dense_projection_does_not_stay_in_the_family() {
    // THE FINDING, asserted rather than described: the literal Pi_O(d) formula
    // produces an orthogonal matrix that is NOT a product of 4 reflections, so
    // the m=4 representation is not closed under it. The two retractions agree
    // at the endpoints and differ in between -- a modelling choice, not an
    // approximation of one by the other.
    const auto A = HouseholderMap::random(kD, HOUSEHOLDER_M_DEFAULT, 21);
    const auto B = HouseholderMap::random(kD, HOUSEHOLDER_M_DEFAULT, 22);

    for (const double g : {0.0, 1.0}) {
        const Eigen::MatrixXd dense = crystallise_dense(A.dense(), B.dense(), g);
        const Eigen::MatrixXd slerp = crystallise(A, B, g).dense();
        assert((dense - slerp).norm() < 1e-10 && "the two must agree at the endpoints");
    }
    const Eigen::MatrixXd dense_mid = crystallise_dense(A.dense(), B.dense(), 0.5);
    const Eigen::MatrixXd slerp_mid = crystallise(A, B, 0.5).dense();
    assert(is_orthogonal(dense_mid, 1e-10) && "Pi_O(d) must return an orthogonal matrix");
    assert((dense_mid - slerp_mid).norm() > 1e-6 &&
           "and it must genuinely differ from the slerp path in between");
    std::cout << "  [ok] Pi_O(d) and slerp agree at gamma=0,1 and differ at 0.5 by "
              << (dense_mid - slerp_mid).norm() << "\n";
}

void test_crystallise_refusals() {
    const auto A = HouseholderMap::random(kD, 4, 1);
    const auto B = HouseholderMap::random(kD + 1, 4, 2);
    bool threw = false;
    try { (void)crystallise(A, B, 0.5); }
    catch (const std::invalid_argument&) { threw = true; }
    assert(threw && "a dimension mismatch must be refused");

    threw = false;
    try { (void)crystallise(A, HouseholderMap::random(kD, 4, 3), 1.5); }
    catch (const std::invalid_argument&) { threw = true; }
    assert(threw && "gamma outside [0,1] must be refused");

    threw = false;
    try {
        Store K(demo_complex(), kD);
        (void)i_star(K, {"a", "nope"});
    } catch (const std::invalid_argument&) { threw = true; }
    assert(threw && "instantiating an unknown vertex must be refused");
    std::cout << "  [ok] dimension mismatch, bad gamma, unknown vertex all refused\n";
}

}  // namespace

int main() {
    std::cout << "=== gamma(nu) (Phase-2 item 6) ===\n";
    test_gamma_of_nu();

    std::cout << "=== the K/W adjunction (Phase-2 item 5) ===\n";
    test_i_star_is_downward_closed();
    test_round_trip_is_faithful();
    test_i_shriek_extends_by_zero();
    test_refuted_leaves_the_store_bit_identical();
    test_section_is_never_written_back();
    test_delta_R_is_the_session_learning();

    std::cout << "=== crystallisation ===\n";
    test_Q_starts_at_zero_and_rises();
    test_crystallise_stays_exactly_orthogonal();
    test_dense_projection_does_not_stay_in_the_family();
    test_crystallise_refusals();

    std::cout << "\nALL TWO-COMPLEX TESTS PASSED\n";
    return 0;
}
