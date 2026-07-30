// Phase-2 item 9: the Cone-Bures metric in C++ (logbook 5y, 5z, 5ak).
//
// python/cone_bures.py stays AUTHORITATIVE. The parity block below is generated
// from it, the same discipline coherence.py holds over CoarseComplex: two
// independent implementations of a load-bearing metric is how they silently
// drift apart, so one of them has to be the reference and the other has to be
// checked against it numerically.
//
// The properties asserted here are the ones 5z's verdict actually rests on:
// it is a METRIC (triangle inequality), it degrades to weighted Bures on day
// one, it SATURATES so distance is bounded (which is what killed the E4
// runaway), and its accuracy is conditional on a regime that is monitored.

#include <cassert>
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <vector>

#include <Eigen/Dense>

#include "mos/core/cone_bures.hpp"
#include "mos/core/semantic_skill.hpp"

using namespace mos;

namespace {

bool close(double a, double b, double tol = 1e-9) {
  return std::fabs(a - b) <= tol * std::max(1.0, std::max(std::fabs(a), std::fabs(b)));
}

Eigen::VectorXd vec(const std::vector<double> &v) {
  return Eigen::Map<const Eigen::VectorXd>(v.data(), static_cast<Eigen::Index>(v.size()));
}

/// Column-major, matching numpy's ravel(order='F') in the generator.
Eigen::MatrixXd mat(const std::vector<double> &v, int d, int k) {
  Eigen::MatrixXd M(d, k);
  for (int j = 0; j < k; ++j)
    for (int i = 0; i < d; ++i) M(i, j) = v[static_cast<std::size_t>(j) * d + i];
  return M;
}

// GENERATED from python/cone_bures.py -- the authoritative implementation.
// Regenerate if that file changes; do not hand-edit.
struct ParityCase { int d, k0, k1; std::vector<double> mu0, U0, mu1, U1;
                    double e0, e1, bures, dist_sq, sdir; bool same; };
static const std::vector<ParityCase> kParity = {
  { 6, 0, 1, {1.3515774962229512, 0.86639714275631174, 0.7743339492908542, -0.64842391401804045, 1.2392758742886434, -0.33558787415124036}, {},
    {0.24876898943181222, 0.87449208156291003, 1.546106784700563, -1.3294467354007948, -0.34664851700026661, 0.028631998543104279}, {0.32455122925411262, -0.067242662709346354, -0.72749721285991709, -0.60744498435832495, -0.73766759545273008, 0.061117530728616913}, 0.01, 0.02,
    6.2669774482041154, 2.1000000000000001, 0.062777576120279094, false },
  { 6, 1, 2, {2.2362146560214717, -0.3587678364312285, -0.58109165534675067, -0.35939814851937235, 0.33525096607568527, 0.44542978174049819}, {0.2458518479382811, -0.54411511290024783, -0.52574494966810625, -0.30151084410131507, -0.30806189997942279, 0.45813158291340816},
    {-0.95244749838726284, 0.55911704816255237, -0.059721964394052716, 0.7259308725872281, 1.0813394560462184, -1.0386451467719322}, {0.082081407627267025, -0.7098416512613096, 0.17478564791904849, -0.30453619926233011, -0.029356942022819285, 0.62024630634600919, 0.47497617390461749, -0.21759387830448157, 0.32149720954985028, -0.25790658335380484, -0.081177593295291423, 0.20296503632999441}, 0.060000000000000005, 0.050000000000000003,
    16.009973916397012, 2.1000000000000001, 0.61309224681382024, false },
  { 6, 2, 0, {1.0331839833600007, 0.70640125313356705, 1.1476631566432138, 0.069081127435425105, -0.73897750725889277, -0.72997042833308989}, {-0.26394675758954289, 0.84849896067300667, 0.21542996882077148, 0.45762503752471012, 0.65906322488479496, -0.67147586672704274, 0.19523504999876379, 0.68841446360156866, 0.4667224446760278, -0.1642221071162708, -0.46651495642287144, -0.30986089506851489},
    {-1.2241907194210531, -0.98273871161852466, -0.39530627896759707, -0.54743479485913316, 0.29891352659137382, 0.55073603529191384}, {}, 0.11, 0.080000000000000002,
    15.410872093749944, 2.1000000000000001, 0.5523363532619886, false },
  { 6, 0, 1, {-0.21191166301223857, -0.10526761253258828, 0.54865705585099811, -1.0380911599835232, 1.2070349361511075, 0.18939148381006848}, {},
    {1.7362530907861902, -0.35598344268724008, -0.15847541626256934, -1.3175051821511181, -0.80334021212771223, 0.78731648552135458}, {-0.039533740933663547, -0.36497577846967344, -0.39446127054884184, -0.12865751127287772, 0.11304418168895536, 0.17865605884055627}, 0.16000000000000003, 0.11,
    8.9368643696578314, 2.1000000000000001, 0.13747035458162238, false },
  { 6, 1, 2, {0.25654055654950808, -0.73287610953935756, -1.682177727653132, 1.9439673728529374, 0.27446113749731554, -0.06367415628364323}, {0.15425871820273526, -1.0815042286297103, 0.41444143077719053, 0.26536254361891337, -0.18504617097641474, 0.040662347386451053},
    {-0.49481892501127922, 0.96473637719799565, 0.6787490367583241, 0.34618219412526502, -0.48144765736451017, -1.9941450392910485}, {-0.15894698877345881, -0.82905356163472832, 0.38089218080785792, 0.060285032432914831, 0.68329814670285283, -0.17516772371560008, 0.71231472681410313, 0.18689006578023737, -0.33849868344157397, -0.1005169861588722, 0.069241419764209375, -0.15312818202636466}, 0.21000000000000002, 0.13999999999999999,
    16.832030072123626, 2.1000000000000001, 0.25694353944100479, false },
  { 6, 2, 0, {0.81573698535041506, -0.6571672413864782, -0.64954209316797762, -1.5138862679763447, 1.6100820272304719, 0.33169930444388762}, {-0.34796196430128673, -0.056490218134364889, -0.0055148320379002757, 0.0077088118388628007, 0.55929796538151955, -0.31826553219757631, -0.57257378622173083, -0.13391471524524987, -0.35987188955999505, 0.60966921923789952, 0.14732816339490393, 0.281855183266495},
    {-0.70976737111001953, -0.89368285818330084, -0.23357929242610032, 0.27160604054930954, -0.47498498329823025, 1.8316503011380272}, {}, 0.26000000000000001, 0.16999999999999998,
    13.092001407367265, 2.1000000000000001, 0.41852154365522976, false },
};

void test_parity_with_python() {
  std::cout << "=== 1. PARITY with python/cone_bures.py (the reference) ===\n";
  for (std::size_t i = 0; i < kParity.size(); ++i) {
    const auto &c = kParity[i];
    const Eigen::VectorXd m0 = vec(c.mu0), m1 = vec(c.mu1);
    const Eigen::MatrixXd U0 = mat(c.U0, c.d, c.k0), U1 = mat(c.U1, c.d, c.k1);

    const double b = core::bures_w2_sq_general(m0, U0, c.e0, m1, U1, c.e1);
    assert(close(b, c.bures, 1e-10) && "bures_w2_sq_general disagrees with Python");

    core::ConeBures cb(0.7);
    const double dsq = cb.distance_sq(m0, U0, c.e0, m1, U1, c.e1, 0.8, 1.3);
    assert(close(dsq, c.dist_sq, 1e-10) && "distance_sq disagrees with Python");
    assert(cb.is_same_concept(m0, U0, c.e0, m1, U1, c.e1) == c.same);
    assert(close(cb.sigma_dir_sq(m0, U0, c.e0, m1, U1, c.e1), c.sdir, 1e-10));

    std::cout << "  [ok] case " << i << " k=(" << c.k0 << "," << c.k1
              << ")  d_BW^2=" << b << "  D^2=" << dsq << "\n";
  }
}

void test_rank_k_vs_rank_k_is_the_new_capability() {
  std::cout << "\n=== 2. THE GAP THIS CLOSES: rank-k on BOTH sides ===\n";
  // wasserstein_2_terms requires side 1 ISOTROPIC -- it exploits
  // Sigma0^{1/2} Sigma1 Sigma0^{1/2} = D0 * Sigma1. Where that assumption
  // holds, the two must agree exactly; where it does not, only the general
  // routine is defined at all.
  const int d = 5;
  Eigen::VectorXd m0(d); m0 << 1, 0, 0, 0, 0;
  Eigen::VectorXd m1(d); m1 << 0, 1, 0, 0, 0;
  Eigen::MatrixXd none(d, 0);
  Eigen::MatrixXd U1(d, 2); U1.setZero(); U1(2, 0) = 0.5; U1(3, 1) = 0.3;

  const double general = core::bures_w2_sq_general(m0, none, 0.05, m1, U1, 0.02);
  const auto terms = core::wasserstein_2_terms(m0, 0.05, m1, U1, 0.02);
  std::cout << "  isotropic-vs-rank-k: general=" << general
            << "  wasserstein_2_terms=" << terms.total() << "\n";
  assert(close(general, terms.total(), 1e-9) &&
         "must agree exactly where the isotropic assumption holds");

  Eigen::MatrixXd U0(d, 2); U0.setZero(); U0(0, 0) = 0.4; U0(4, 1) = 0.6;
  const double both = core::bures_w2_sq_general(m0, U0, 0.05, m1, U1, 0.02);
  assert(both > 0.0 && std::isfinite(both));
  std::cout << "  rank-k-vs-rank-k:    general=" << both
            << "  (wasserstein_2_terms CANNOT express this)  OK\n";
}

void test_it_is_a_metric() {
  std::cout << "\n=== 3. TRIANGLE INEQUALITY (the property we cannot trade) ===\n";
  std::srand(7);
  const int d = 4;
  auto rnd = [&](double s) {
    Eigen::VectorXd v(d);
    for (int i = 0; i < d; ++i) v(i) = s * ((std::rand() / double(RAND_MAX)) - 0.5);
    return v;
  };
  double worst = 0.0;
  for (double delta : {0.05, 0.3, 1.0, 5.0}) {
    core::ConeBures cb(delta);
    Eigen::MatrixXd none(d, 0);
    for (int t = 0; t < 400; ++t) {
      const Eigen::VectorXd a = rnd(2.0), b = rnd(2.0), c = rnd(2.0);
      const double wa = 0.2 + std::rand() / double(RAND_MAX);
      const double wb = 0.2 + std::rand() / double(RAND_MAX);
      const double wc = 0.2 + std::rand() / double(RAND_MAX);
      const double ab = std::sqrt(cb.distance_sq(a, none, 0.01, b, none, 0.01, wa, wb));
      const double bc = std::sqrt(cb.distance_sq(b, none, 0.01, c, none, 0.01, wb, wc));
      const double ac = std::sqrt(cb.distance_sq(a, none, 0.01, c, none, 0.01, wa, wc));
      worst = std::max(worst, ac - (ab + bc));
    }
  }
  std::cout << "  1600 triples over 4 deltas: worst d(a,c)-[d(a,b)+d(b,c)] = "
            << worst << "\n";
  assert(worst < 1e-9 && "Cone-Bures must satisfy the triangle inequality");
  std::cout << "  [ok] it is a metric\n";
}

void test_the_three_limits() {
  std::cout << "\n=== 4. THE THREE LIMITS ===\n";
  const int d = 3;
  Eigen::VectorXd a(d); a << 0, 0, 0;
  Eigen::VectorXd b(d); b << 1, 0, 0;
  Eigen::MatrixXd none(d, 0);

  // (i) identical stalks => pure Hellinger on the masses.
  core::ConeBures cb(1.0);
  const double same = cb.distance_sq(a, none, 0.01, a, none, 0.01, 1.0, 0.25);
  const double hell = std::pow(std::sqrt(1.0) - std::sqrt(0.25), 2.0);
  assert(close(same, hell, 1e-12));
  std::cout << "  d_BW=0    -> D^2 = (sqrt(w0)-sqrt(w1))^2 = " << same << "  OK\n";

  // (ii) beyond the cutoff => CONSTANT w0+w1. This is what bounds the metric
  // and kills the E4 runaway, and it is also the merge predicate flipping.
  core::ConeBures tight(0.05);
  const double far = tight.distance_sq(a, none, 1e-6, b, none, 1e-6, 1.0, 1.0);
  assert(close(far, 2.0, 1e-9));
  assert(!tight.is_same_concept(a, none, 1e-6, b, none, 1e-6));
  std::cout << "  d_BW>pi*d -> D^2 = w0+w1 = " << far
            << " (saturated, BOUNDED) and is_same_concept=false  OK\n";

  // (iii) delta -> infinity => 4 delta^2 D^2 -> w * d_BW^2 (weighted Bures),
  // which is what the engine computes TODAY. Day-one degradation.
  const double d_bw_sq = core::bures_w2_sq_general(a, none, 1e-9, b, none, 1e-9);
  double prev_err = 1e9;
  for (double delta : {10.0, 100.0, 1000.0}) {
    core::ConeBures big(delta);
    const double scaled =
        4.0 * delta * delta * big.distance_sq(a, none, 1e-9, b, none, 1e-9, 1.0, 1.0);
    const double err = std::fabs(scaled - d_bw_sq) / d_bw_sq;
    assert(err < prev_err && "must converge to weighted Bures");
    prev_err = err;
  }
  std::cout << "  delta->inf-> 4 delta^2 D^2 -> w*d_BW^2, rel err falls to "
            << prev_err << "  OK\n";
}

void test_regime_monitor() {
  std::cout << "\n=== 5. V6: the monitor flags on the FRACTION ===\n";
  core::RegimeMonitor mon(1000);
  assert(mon.report().status == "empty");
  for (int i = 0; i < 950; ++i) mon.observe_ratio(0.05);
  for (int i = 0; i < 50; ++i) mon.observe_ratio(0.90);
  const auto rep = mon.report();
  std::cout << "  " << rep.report() << "\n";
  assert(rep.status == "chance");
  assert(rep.mean < core::REGIME_OK * 1.05 && "the mean reads HEALTHY -- that is the trap");
  assert(close(rep.p95, 0.0925, 1e-6) && "p95 also reads healthy at exactly 5% bad");
  std::cout << "  mean and p95 BOTH read healthy; the fraction does not.  OK\n";

  core::RegimeMonitor ok(500);
  for (int i = 0; i < 400; ++i) ok.observe_ratio(0.09 + 0.01 * (i % 3));
  const auto r2 = ok.report();
  assert(r2.status == "ok" && r2.mean_implied_gap < 1.02);
  std::cout << "  " << r2.report() << "\n";

  core::RegimeMonitor small(10);
  for (int i = 0; i < 1000; ++i) small.observe_ratio(0.1);
  assert(small.size() == 10 && "bounded history");
  std::cout << "  bounded window: 1000 observations -> 10 retained  OK\n";
}

void test_contracts() {
  std::cout << "\n=== 6. contracts ===\n";
  bool threw = false;
  try { core::ConeBures bad(0.0); } catch (const std::invalid_argument &) { threw = true; }
  assert(threw && "delta must be > 0");

  const int d = 3;
  Eigen::VectorXd a(d); a << 1, 2, 3;
  Eigen::MatrixXd none(d, 0);
  core::ConeBures cb(1.0);
  threw = false;
  try { cb.sigma_dir_sq(a, none, 0.1, a, none, 0.1); }
  catch (const std::invalid_argument &) { threw = true; }
  assert(threw && "coincident means have no separation direction");

  threw = false;
  try { core::bures_w2_sq_general(a, none, 0.0, a, none, 0.1); }
  catch (const std::invalid_argument &) { threw = true; }
  assert(threw && "a zero floor makes the Bures root undefined");

  // Dimension mismatch must be refused, never padded (embeddings.py contract 2).
  Eigen::VectorXd shortv(2); shortv << 1, 2;
  Eigen::MatrixXd none2(2, 0);
  threw = false;
  try { core::bures_w2_sq_general(a, none, 0.1, shortv, none2, 0.1); }
  catch (const std::invalid_argument &) { threw = true; }
  assert(threw && "dimension mismatch must be refused");
  std::cout << "  [ok] delta<=0, coincident means, zero floor, dim mismatch all refused\n";
}

}  // namespace

int main() {
  std::cout << "=== CONE-BURES (Phase-2 item 9) ===\n";
  test_parity_with_python();
  test_rank_k_vs_rank_k_is_the_new_capability();
  test_it_is_a_metric();
  test_the_three_limits();
  test_regime_monitor();
  test_contracts();
  std::cout << "\nAll Cone-Bures tests passed.\n";
  return 0;
}
