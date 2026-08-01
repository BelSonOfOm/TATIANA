// Phase-2 item 3: F_MOS and the barrier controller.
//
// Two properties carry this file:
//   * F_MOS must degrade EXACTLY to 4 - deg u - deg v + 3m at unit weights. If
//     it does not, the derivation that justified it disagrees with the formula
//     shipped, and the "3" stops being derived.
//   * The barrier must make severing STRUCTURALLY impossible, at any step size
//     and any curvature. The forward-Euler step it replaces is included here
//     purely so the sign flip at eps*kappa < -1 can be demonstrated rather than
//     asserted in a comment.

#include <cassert>
#include <cmath>
#include <iostream>
#include <random>
#include <stdexcept>
#include <vector>

#include "mos/core/curvature.hpp"

using namespace mos::core;

namespace {

bool close(double a, double b, double tol = 1e-12) {
    return std::fabs(a - b) <= tol * std::max(1.0, std::max(std::fabs(a), std::fabs(b)));
}

// 4 organs, 5 edges, 1 filled triangle -- the E5 configuration.
Complex2 e5_complex() {
    return Complex2({"A", "B", "C", "D"},
                    {{"A", "B"}, {"B", "C"}, {"A", "C"}, {"A", "D"}, {"C", "D"}},
                    {{"A", "B", "C"}});
}

// ---------------------------------------------------------------- tau_f -----

void test_tau_is_the_harmonic_mean() {
    assert(close(tau_face({1.0, 1.0, 1.0}), 1.0));
    // 3 / (1/2 + 1/4 + 1/4) = 3 / 1 = 3
    assert(close(tau_face({2.0, 4.0, 4.0}), 3.0));
    // The |f| factor is the whole point: without it, unit precisions would give
    // 1/3 and F_MOS would not degrade to the combinatorial formula.
    assert(close(tau_face({1.0, 1.0, 1.0}), 1.0) && "all pi=1 MUST give tau=1");

    bool threw = false;
    try { (void)tau_face({}); } catch (const std::invalid_argument&) { threw = true; }
    assert(threw);
    threw = false;
    try { (void)tau_face({1.0, 0.0, 1.0}); } catch (const std::invalid_argument&) { threw = true; }
    assert(threw && "a zero precision must be refused, not treated as a default");
    std::cout << "  [ok] tau_f is the harmonic mean; all pi=1 => tau=1\n";
}

// ------------------------------------------------- the 'not both' clause ----

void test_parallel_excludes_triangle_edges() {
    const Complex2 cx = e5_complex();
    // Edge (A,B) lies in triangle (A,B,C). Its triangle-mates (A,C) and (B,C)
    // share a vertex AND a coface, so the "not both" clause excludes them.
    const auto [ab, orient_ab] = cx.edge_index("A", "B");
    (void)orient_ab;
    const auto par = parallel_edges(cx, ab);

    for (const auto& [j, gamma] : par) {
        (void)gamma;
        const HodgeEdge& f = cx.edges()[j];
        const bool is_ac = (f == HodgeEdge{"A", "C"});
        const bool is_bc = (f == HodgeEdge{"B", "C"});
        assert(!is_ac && !is_bc && "triangle-mates must NOT count as parallel");
    }
    // What remains: (A,D) only. deg A = 3, deg B = 2, m = 1
    // => deg u + deg v - 2 - 2m = 3 + 2 - 2 - 2 = 1.
    assert(par.size() == 1);
    assert(cx.edges()[par[0].first] == (HodgeEdge{"A", "D"}));
    std::cout << "  [ok] parallel set obeys 'share a face or a coface, not both'\n";
}

// -------------------------------------------------- exact degradation -------

void test_unit_weights_reproduce_the_combinatorial_formula() {
    const Complex2 cx = e5_complex();
    const auto w = CurvatureWeights::unit(cx);
    for (int i = 0; i < cx.num_edges(); ++i) {
        const double general = forman_mos(cx, i, w);
        const double combinatorial = forman_combinatorial(cx, i);
        if (!close(general, combinatorial)) {
            std::cerr << "  [FAIL] edge " << i << ": F_MOS=" << general
                      << " but 4-du-dv+3m=" << combinatorial << "\n";
            assert(false);
        }
    }
    // Spot-check one by hand so the test does not merely compare two bugs.
    // (A,B): deg A = 3, deg B = 2, m = 1  =>  4 - 3 - 2 + 3 = 2.
    const auto [ab, o] = cx.edge_index("A", "B");
    (void)o;
    assert(close(forman_combinatorial(cx, ab), 2.0));
    assert(close(forman_mos(cx, ab, w), 2.0));
    std::cout << "  [ok] pi=nu=tau=1 reproduces 4-deg u-deg v+3m on every edge\n";
}

void test_degradation_holds_on_random_complexes() {
    // A triangulated fan plus a dangling path, so degrees and m vary.
    const Complex2 cx({"P", "Q", "R", "S", "T"},
                      {{"P", "Q"}, {"Q", "R"}, {"P", "R"}, {"R", "S"}, {"P", "S"}, {"S", "T"}},
                      {{"P", "Q", "R"}, {"P", "R", "S"}});
    const auto w = CurvatureWeights::unit(cx);
    for (int i = 0; i < cx.num_edges(); ++i) {
        assert(close(forman_mos(cx, i, w), forman_combinatorial(cx, i)));
    }
    // (P,R) is in BOTH triangles: m = 2.
    // deg P = |{PQ, PR, PS}| = 3, deg R = |{QR, PR, RS}| = 3.
    // => 4 - 3 - 3 + 3*2 = 4. A doubly-filled edge is strongly POSITIVE, which
    // is the whole point: filled cycles are locally repairable, so curvature
    // should push toward contraction there.
    const auto [pr, o] = cx.edge_index("P", "R");
    (void)o;
    assert(close(forman_combinatorial(cx, pr), 4.0));
    // And the dangling edge (S,T) is the opposite extreme:
    // deg S = 3, deg T = 1, m = 0  =>  4 - 3 - 1 + 0 = 0.
    const auto [st, o2] = cx.edge_index("S", "T");
    (void)o2;
    assert(close(forman_combinatorial(cx, st), 0.0));
    std::cout << "  [ok] degradation holds on a two-triangle complex (shared edge m=2)\n";
}

// ------------------------------------------------------ weighted behaviour --

void test_weights_move_the_number() {
    // A formula that ignored its weights would still pass the degradation test,
    // so assert the weights actually do something -- and assert WHICH ones,
    // because one of them provably cancels here.
    const Complex2 cx = e5_complex();          // vertices A,B,C,D in that order
    auto w = CurvatureWeights::unit(cx);
    const auto [ab, o] = cx.edge_index("A", "B");
    (void)o;
    const double base = forman_mos(cx, ab, w);

    // nu_A CANCELS on this edge, and that is structure, not a defect. The only
    // edge parallel to (A,B) is (A,D), whose shared vertex is A, so the face
    // term contributes +nu_A and the penalty contributes -nu_A * sqrt(1) exactly.
    w.nu[0] = 3.0;
    assert(close(forman_mos(cx, ab, w), base) &&
           "nu at a vertex with exactly one parallel edge must cancel");

    // nu_B does NOT cancel: deg B = 2 and its other edge (B,C) is a triangle-mate,
    // excluded by the 'not both' clause, so B contributes no penalty term.
    w = CurvatureWeights::unit(cx);
    w.nu[1] = 3.0;
    const double raised = forman_mos(cx, ab, w);
    assert(close(raised, base + 2.0) && "nu_B must enter linearly, +1 per unit");

    w = CurvatureWeights::unit(cx);
    w.pi[static_cast<std::size_t>(ab)] = 4.0;
    assert(forman_mos(cx, ab, w) != base && "pi must enter the result");
    std::cout << "  [ok] nu_A cancels (one parallel edge through A), nu_B and pi move it\n";
}

void test_low_precision_prediction_confirmed_and_it_is_a_worry() {
    // 5ac flags a PREDICTION, explicitly "to test, not a claim": as pi_e -> 0 the
    // coface term dies like pi_e^2 and the penalty like sqrt(pi_e), while
    // (nu_u + nu_v) is untouched -- so a low-precision edge drifts POSITIVE,
    // i.e. toward CONTRACT/FOLD. 5ac says that "would be backwards".
    //
    // Tested on the BRIDGE (A,D), which is the case the worry is about: no
    // triangles, so no coface term, and three parallel edges (A,B),(A,C),(C,D).
    //   F(pi) = (nu_A + nu_D) - 3*sqrt(pi) = 2 - 3*sqrt(pi)
    const Complex2 cx = e5_complex();
    auto w = CurvatureWeights::unit(cx);
    const auto [ad, o] = cx.edge_index("A", "D");
    (void)o;

    assert(close(forman_mos(cx, ad, w), -1.0));      // 2 - 3 = -1, a bridge
    assert(close(forman_combinatorial(cx, ad), -1.0));

    double prev = -1e300;
    for (const double p : {1.0, 0.1, 0.01, 1e-4, 1e-8}) {
        w.pi[static_cast<std::size_t>(ad)] = p;
        const double f = forman_mos(cx, ad, w);
        assert(close(f, 2.0 - 3.0 * std::sqrt(p)) && "closed form for this edge");
        assert(f > prev && "on a bridge the drift IS monotone in pi");
        prev = f;
    }
    // CONFIRMED, and it is the unwelcome direction: a bridge at pi -> 0 goes
    // from -1 (EXPAND, correctly) to +2 (CONTRACT). An edge we know nothing
    // about would be folded away for being uninformative.
    assert(prev > 1.99 && "the limit is nu_u + nu_v = 2");
    std::cout << "  [ok] 5ac's prediction CONFIRMED on a bridge: F goes -1 -> "
              << prev << " as pi->0.\n"
              << "       This is the BACKWARDS direction 5ac feared; recorded, not endorsed.\n";

    // NOTE the approach is NOT monotone in general. On (A,B), which has a coface
    // term, F dips below its unit value before returning to nu_u + nu_v. 5ac
    // predicts the LIMIT, not the path, and only the limit is asserted here.
    auto w2 = CurvatureWeights::unit(cx);
    const auto [ab, o2] = cx.edge_index("A", "B");
    (void)o2;
    const double f1 = forman_mos(cx, ab, w2);
    w2.pi[static_cast<std::size_t>(ab)] = 0.1;
    const double f01 = forman_mos(cx, ab, w2);
    assert(f01 < f1 && "on a filled edge the path dips first -- not monotone");
    std::cout << "       (on a filled edge the path is non-monotone: " << f1
              << " -> " << f01 << " -> 2)\n";
}

void test_forman_refusals() {
    const Complex2 cx = e5_complex();
    bool threw = false;
    try {
        CurvatureWeights bad;
        bad.pi.assign(2, 1.0);
        bad.nu.assign(4, 1.0);
        (void)forman_mos(cx, 0, bad);
    } catch (const std::invalid_argument&) { threw = true; }
    assert(threw && "a pi vector of the wrong length must be refused");

    threw = false;
    try {
        auto bad = CurvatureWeights::unit(cx);
        bad.pi[1] = 0.0;
        (void)forman_mos(cx, 0, bad);
    } catch (const std::invalid_argument&) { threw = true; }
    assert(threw && "pi = 0 must be refused");
    std::cout << "  [ok] size mismatches and zero weights are refused\n";
}

// ------------------------------------------------------ barrier controller --

void test_euler_severs_and_that_is_the_bug() {
    // The motivating failure, demonstrated rather than described: at
    // eps*kappa < -1 forward Euler sends a positive weight NEGATIVE.
    const double w = 0.5, kappa = -30.0, eps = 0.05;   // eps*kappa = -1.5
    const double euler = euler_step_unsafe(w, kappa, eps);
    assert(euler < 0.0 && "this is the artefact w_floor was patching");

    // The exact flow never changes SIGN, at any step size.
    for (const double k : {-1e3, -1e2, -10.0, -1.0}) {
        for (const double e : {0.01, 0.5, 5.0, 100.0}) {
            assert(exponential_step(w, k, e) >= 0.0);
        }
    }
    std::cout << "  [ok] Euler flips sign at eps*kappa=-1.5 (" << euler
              << "); the exact flow never changes sign\n";
}

void test_exponential_positivity_does_not_survive_floating_point() {
    // 5ad says exponential integration makes positivity "structural rather than
    // clipped". That is true in EXACT ARITHMETIC and false in double: exp
    // underflows to exactly 0 below about -745, so a sufficiently negative
    // eps*kappa severs the edge after all -- silently, and to exactly zero
    // rather than to something negative anyone would notice.
    const double severed = exponential_step(0.5, -1e3, 100.0);   // exp(-1e5)
    assert(severed == 0.0 && "underflow, not a sign flip -- and still severed");

    // The barrier does NOT have this failure mode, and the reason is structural:
    // it ADDS the floor rather than multiplying, so an underflowed decay yields
    // theta_safe exactly, never below it.
    BarrierConfig cfg;
    cfg.eps_flow = 100.0;
    cfg.theta_safe = 1e-3;
    cfg.w_max = 1.0;
    const double barriered = barrier_step(0.5, -1e3, cfg);
    assert(barriered == cfg.theta_safe && "underflow lands ON the floor");
    assert(barriered > 0.0 && "and the floor is strictly above collapse");

    std::cout << "  [ok] exp underflows to " << severed
              << " (SEVERED) where the barrier lands on theta_safe = "
              << barriered << "\n"
              << "       => bare exponential integration is NOT sufficient; the\n"
              << "          barrier's guarantee is the one that survives float.\n";
}

void test_barrier_is_forward_invariant() {
    BarrierConfig cfg;
    cfg.eps_flow = 0.05;
    cfg.theta_safe = 1e-3;
    cfg.w_max = 1.0;

    std::mt19937 gen(17);
    std::uniform_real_distribution<double> w0(cfg.theta_safe, cfg.w_max);
    std::uniform_real_distribution<double> kap(-500.0, 500.0);

    for (int trial = 0; trial < 2000; ++trial) {
        double w = w0(gen);
        for (int step = 0; step < 200; ++step) {
            w = barrier_step(w, kap(gen), cfg);
            // The vector field vanishes at the boundary, so a trajectory that
            // starts inside approaches but never crosses. In exact arithmetic
            // this is strict; in double, an underflowed decay can land exactly
            // ON a boundary. Either way it NEVER leaves the band, which is the
            // property that matters -- theta_safe sits strictly above collapse.
            assert(w >= cfg.theta_safe && w <= cfg.w_max);
            assert(std::isfinite(w));
        }
    }
    std::cout << "  [ok] 400k steps, kappa in [-500,500]: never left (theta_safe, w_max)\n";
}

void test_barrier_never_severs_under_relentless_depression() {
    // The bridge-severing case C.4 actually cares about: maximum depression,
    // forever. Under w_floor this would park exactly AT the collapse point.
    BarrierConfig cfg;
    cfg.eps_flow = 0.5;
    cfg.theta_safe = 1e-3;
    cfg.w_max = 1.0;

    double w = 1.0;
    for (int i = 0; i < 100000; ++i) w = barrier_step(w, -100.0, cfg);
    // At eps*|kappa| = 50 the decay underflows within ~35 steps, so w lands
    // exactly ON theta_safe rather than merely near it. It is still not severed:
    // theta_safe is strictly above the collapse trigger by construction, which
    // is the whole reason the barrier replaced w_floor (which sat AT collapse).
    assert(w >= cfg.theta_safe && "never below the floor");
    assert(w - cfg.theta_safe < 1e-9 && "and it converges all the way down to it");
    assert(w > 0.0 && "and the floor itself is strictly positive");
    std::cout << "  [ok] 100k maximal-depression steps: w = " << w
              << " (== theta_safe, never below, never zero)\n";
}

void test_barrier_matches_the_closed_form() {
    // The step is EXACT, not an approximation, so assert it against the
    // closed-form solution of the constrained ODE rather than a tolerance band.
    BarrierConfig cfg;
    cfg.eps_flow = 0.07;
    cfg.theta_safe = 0.01;
    cfg.w_max = 2.0;

    const double w = 0.9;
    const double kd = -3.0, kp = 3.0;
    assert(close(barrier_step(w, kd, cfg),
                 cfg.theta_safe + (w - cfg.theta_safe) * std::exp(-cfg.eps_flow * 3.0)));
    assert(close(barrier_step(w, kp, cfg),
                 cfg.w_max - (cfg.w_max - w) * std::exp(-cfg.eps_flow * 3.0)));
    assert(barrier_step(w, 0.0, cfg) == w && "kappa = 0 must be an exact no-op");
    std::cout << "  [ok] the step matches the constrained ODE's closed form exactly\n";
}

void test_barrier_sign_convention() {
    // C6-4: the sign convention gets a TEST, not a comment.
    // kappa > 0 must potentiate, kappa < 0 must depress. A flipped sign here
    // would make the controller strengthen exactly what it should weaken.
    BarrierConfig cfg;
    const double w = 0.5;
    assert(barrier_step(w, +5.0, cfg) > w && "positive curvature must potentiate");
    assert(barrier_step(w, -5.0, cfg) < w && "negative curvature must depress");
    std::cout << "  [ok] sign convention: kappa>0 potentiates, kappa<0 depresses\n";
}

void test_barrier_refusals() {
    bool threw = false;
    BarrierConfig bad;
    bad.theta_safe = 1.0;
    bad.w_max = 1.0;                    // empty band
    try { (void)barrier_step(1.0, 1.0, bad); }
    catch (const std::invalid_argument&) { threw = true; }
    assert(threw);

    threw = false;
    BarrierConfig cfg;
    try { (void)barrier_step(5.0, 1.0, cfg); }   // starts outside
    catch (const std::invalid_argument&) { threw = true; }
    assert(threw && "forward invariance cannot rescue a trajectory starting outside");
    std::cout << "  [ok] empty band and out-of-band starts are refused\n";
}

}  // namespace

int main() {
    std::cout << "=== F_MOS (Q5, logbook 5ac) ===\n";
    test_tau_is_the_harmonic_mean();
    test_parallel_excludes_triangle_edges();
    test_unit_weights_reproduce_the_combinatorial_formula();
    test_degradation_holds_on_random_complexes();
    test_weights_move_the_number();
    test_low_precision_prediction_confirmed_and_it_is_a_worry();
    test_forman_refusals();

    std::cout << "=== the barrier controller (Q6, logbook 5ad) ===\n";
    test_euler_severs_and_that_is_the_bug();
    test_exponential_positivity_does_not_survive_floating_point();
    test_barrier_matches_the_closed_form();
    test_barrier_sign_convention();
    test_barrier_is_forward_invariant();
    test_barrier_never_severs_under_relentless_depression();
    test_barrier_refusals();

    std::cout << "\nALL CURVATURE TESTS PASSED\n";
    return 0;
}
