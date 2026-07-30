// The confidence -> nu_v -> pi_e -> tau_f routing, and the w(sigma,t) / pi_e
// separation that had to happen first.
//
// WHY THESE ARE THE ASSERTIONS
// -----------------------------
// Before this, `use_precision` read the HEBBIAN COUPLING as pi_e. That is the
// conflation 5ac and 5af both ruled out in writing -- w(sigma,t) is a
// normalised bind indicator on [0,1], pi_e is an unbounded inverse variance --
// and 5q had already eaten a divergence bug from it. It was also encoded as a
// REQUIREMENT by the old test_coarse_complex case, which is why it survived two
// audits: the test asserted the bug.
//
// Separately, confidence was being discarded outright (`(void)confidence` in
// curator.cpp) after FIX-13 correctly removed it from the stalk variance but
// left it with nowhere to go. With nothing feeding pi_e, every weight in the
// cell-weight tower is 1, tau_f == 1, and F_MOS silently degenerates to the
// unit-weight Forman formula -- so the 5ac derivation would have been inert in
// the engine no matter how correct it was.

#include <cassert>
#include <cmath>
#include <iostream>
#include <stdexcept>

#include "mos/core/coarse_complex.hpp"
#include "mos/core/semantic_skill.hpp"

using namespace mos;

namespace {

bool close(double a, double b, double tol = 1e-12) {
  return std::fabs(a - b) <= tol * std::max(1.0, std::max(std::fabs(a), std::fabs(b)));
}

void test_pi_is_not_the_coupling() {
  core::CoarseComplex K(1.0, 0.1);
  K.register_module("a");
  K.register_module("b");
  Eigen::VectorXd x(3); x << 1.0, 0.0, 0.0;
  Eigen::VectorXd y(3); y << 0.0, 1.0, 0.0;
  K.set_stalk("a", x);
  K.set_stalk("b", y);
  K.co_activate("a", "b", 50.0);            // strongly BOUND
  K.set_use_precision(true);

  assert(!K.precision("a", "b").has_value() && "coupling must not create a precision");
  assert(K.calibrated_edge_count() == 0);

  const double uncalibrated = K.report().omega;
  K.set_precision("a", "b", 50.0);
  const double calibrated = K.report().omega;

  assert(close(uncalibrated * 50.0, calibrated) &&
         "omega must scale with the MEASURED precision, not the coupling");
  std::cout << "  [ok] a coupling of 50 leaves pi=1 (omega " << uncalibrated
            << "); stating pi=50 gives omega " << calibrated << "\n";
}

void test_precision_survives_and_dies_with_the_edge() {
  core::CoarseComplex K(1.0, 0.6);
  K.register_module("a");
  K.register_module("b");
  Eigen::VectorXd x(2); x << 1.0, 0.0;
  K.set_stalk("a", x);
  K.set_stalk("b", x);
  K.co_activate("a", "b", 1.0);
  K.set_precision("a", "b", 7.0);
  assert(close(*K.precision("a", "b"), 7.0));

  K.tick_decay();                       // 1.0 -> 0.4, unbound but alive
  assert(K.precision("a", "b").has_value() && "an unbound edge keeps its precision");
  K.tick_decay();                       // 0.4 -> -0.2, collapses
  assert(!K.precision("a", "b").has_value() &&
         "a collapsed edge must not leave a stale precision behind");
  std::cout << "  [ok] precision outlives an unbind but dies with a collapse\n";
}

void test_precision_contract() {
  core::CoarseComplex K;
  K.register_module("a");
  K.register_module("b");
  for (double bad : {0.0, -1.0, std::nan(""), std::numeric_limits<double>::infinity()}) {
    bool threw = false;
    try {
      K.set_precision("a", "b", bad);
    } catch (const std::invalid_argument &) {
      threw = true;
    }
    assert(threw && "pi_e must be finite and > 0");
  }
  std::cout << "  [ok] set_precision refuses 0, negative, NaN and inf\n";
}

void test_the_cell_weight_tower() {
  // Level 0 -> 1: pi_e is the harmonic mean of its two vertex-faces.
  assert(close(core::edge_precision(1.0, 1.0), 1.0));
  assert(close(core::edge_precision(2.0, 6.0), 3.0));      // 2/(1/2+1/6) = 3
  // Dominated by the WORST face: one unreliable endpoint discredits the pair.
  const double lopsided = core::edge_precision(1000.0, 0.5);
  assert(lopsided < 1.0 && "a confident organ cannot rescue an unreliable one");
  std::cout << "  [ok] pi_e(1000, 0.5) = " << lopsided
            << " -- the worst face dominates, as a harmonic mean must\n";

  // The rule is uniform across levels: same function, three edge-faces.
  const double tau = core::harmonic_cell_weight({1.0, 1.0, 1.0});
  assert(close(tau, 1.0) && "unit precisions must give tau = 1 (day-one degradation)");
  assert(close(core::harmonic_cell_weight({2.0, 3.0, 6.0}), 3.0));  // 3/(1/2+1/3+1/6)

  // Bounded by its faces, always.
  for (double a : {0.01, 1.0, 50.0}) {
    for (double b : {0.02, 2.0, 90.0}) {
      const double w = core::edge_precision(a, b);
      assert(w >= std::min(a, b) - 1e-12 && w <= std::max(a, b) + 1e-12);
    }
  }
  std::cout << "  [ok] harmonic_cell_weight: unit -> 1, and min(faces) <= w <= max(faces)\n";
}

void test_tower_contract() {
  bool threw = false;
  try {
    core::harmonic_cell_weight({});
  } catch (const std::invalid_argument &) {
    threw = true;
  }
  assert(threw && "a cell with no faces has no weight");
  threw = false;
  try {
    core::harmonic_cell_weight({1.0, 0.0});
  } catch (const std::invalid_argument &) {
    threw = true;
  }
  assert(threw && "a zero face weight is degenerate, not a default");
  std::cout << "  [ok] the tower refuses empty face sets and non-positive weights\n";
}

void test_confidence_becomes_nu() {
  assert(close(core::vertex_precision(0.9), 0.9));
  // Floored, matching experiment_e5.py's max(confidence, 1e-3).
  assert(close(core::vertex_precision(0.0), core::EPS_FLOOR));
  assert(close(core::vertex_precision(-5.0), core::EPS_FLOOR));
  assert(close(core::vertex_precision(std::nan("")), core::EPS_FLOOR) &&
         "an unparsed confidence must floor, not poison the tower with NaN");
  std::cout << "  [ok] confidence -> nu_v, floored at EPS_FLOOR = " << core::EPS_FLOOR
            << " (matches belief.py / experiment_e5.py)\n";
}

void test_nu_rides_on_the_embedding() {
  Eigen::VectorXd mu(3); mu << 1.0, 0.0, 0.0;
  Eigen::MatrixXd U(3, 0);
  core::SemanticEmbedding uncalibrated(mu, U, 0.1, "no confidence reported");
  assert(close(uncalibrated.get_nu(), 1.0) &&
         "an unreported confidence is UNCALIBRATED (nu=1), never invented");

  core::SemanticEmbedding confident(mu, U, 0.1, "confident", core::vertex_precision(0.95));
  assert(close(confident.get_nu(), 0.95));

  // nu is a precision and is validated as one.
  bool threw = false;
  try {
    confident.set_nu(0.0);
  } catch (const std::invalid_argument &) {
    threw = true;
  }
  assert(threw);

  // The edge the curator would build between them.
  const double pi_e = core::edge_precision(uncalibrated.get_nu(), confident.get_nu());
  assert(pi_e < 1.0 && pi_e > 0.9);
  std::cout << "  [ok] nu travels on SemanticEmbedding; edge between nu=1.0 and "
               "nu=0.95 gets pi_e=" << pi_e << "\n";
}

void test_degeneracy_warning_is_real() {
  // The reason this routing was promoted ahead of the rest of Phase 2: with no
  // confidence anywhere, every level of the tower is 1 and the curvature
  // machinery cannot distinguish anything. Assert the degeneracy explicitly so
  // nobody has to rediscover it.
  const double nu = 1.0;
  const double pi = core::edge_precision(nu, nu);
  const double tau = core::harmonic_cell_weight({pi, pi, pi});
  assert(close(pi, 1.0) && close(tau, 1.0));
  std::cout << "  [ok] with NO confidence reported: nu=pi=tau=1 exactly, so F_MOS\n"
               "       collapses to 4 - deg u - deg v + 3m and Pi is inert.\n"
               "       The tower is only worth having once something reports.\n";
}

}  // namespace

int main() {
  std::cout << "=== confidence -> nu -> pi_e -> tau_f, and the w/pi separation ===\n";
  test_pi_is_not_the_coupling();
  test_precision_survives_and_dies_with_the_edge();
  test_precision_contract();
  test_the_cell_weight_tower();
  test_tower_contract();
  test_confidence_becomes_nu();
  test_nu_rides_on_the_embedding();
  test_degeneracy_warning_is_real();
  std::cout << "\nAll precision-routing tests passed.\n";
  return 0;
}
