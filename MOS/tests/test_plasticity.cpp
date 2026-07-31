// Parity test: C++ Homeostat/CriticalityMonitor/select_best vs python/plasticity.py
// and python/selection.py. Python is authoritative if they ever disagree.

#include "mos/core/plasticity.hpp"
#include "mos/core/selection.hpp"

#include <cassert>
#include <cmath>
#include <iostream>

using namespace mos::core;

static bool close(double a, double b, double t = 1e-9) {
  return std::fabs(a - b) < t;
}

int main() {
  std::cout << "=== plasticity + selection parity tests ===\n";

  // ---- 1. Homeostat: transient spike ignored, sustained triggers ----------
  {
    Homeostat h(0.30, 0.25);
    h.observe({{"Reason", 1.0}, {"Search", 0.0}});
    for (int i = 0; i < 5; ++i)
      h.observe({{"Reason", 0.0}, {"Search", 0.0}});
    assert(h.organs_needing_growth().empty() && "a single spike must not trigger");

    Homeostat h2(0.30, 0.25);
    for (int i = 0; i < 10; ++i)
      h2.observe({{"Reason", 0.5}, {"Search", 0.05}});
    auto g = h2.organs_needing_growth();
    assert(g.size() == 1 && g[0] == "Reason");
    std::cout << "1. homeostat: transient ignored, sustained -> " << g[0] << "\n";
  }

  // ---- 2. per-organ aggregation ------------------------------------------
  {
    std::map<CoarseEdge, double> pe{{{"A", "B"}, 0.2}, {{"B", "C"}, 0.5}};
    auto agg = Homeostat::per_organ_discord(pe);
    assert(close(agg["B"], 0.7) && close(agg["A"], 0.2));
    std::cout << "2. per-organ aggregation: B=" << agg["B"] << " A=" << agg["A"]
              << "\n";
  }

  // ---- 3. criticality epsilon: fallback + quantile ------------------------
  {
    CriticalityMonitor m(0.10, 5, 0.75);
    assert(close(m.eps_rho(), 0.10) && "cold start returns default");
    for (double v : {0.0, 0.1, 0.2, 0.3, 0.4})
      m.record_rho(v);
    // 75th percentile of {0,.1,.2,.3,.4}, numpy-linear: pos=0.75*4=3 -> 0.3
    std::cout << "3. criticality eps_rho = " << m.eps_rho() << " (expect 0.3)\n";
    assert(close(m.eps_rho(), 0.3));
  }

  // ---- 4. decay controller direction --------------------------------------
  {
    CriticalityMonitor sup;
    for (int i = 0; i < 4; ++i)
      sup.record_avalanche(3);
    const double up = sup.suggest_decay(0.10);
    CriticalityMonitor sub;
    for (int i = 0; i < 4; ++i)
      sub.record_avalanche(0);
    const double down = sub.suggest_decay(0.10);
    std::cout << "4. decay: supercritical->" << up << " subcritical->" << down
              << "\n";
    assert(up > 0.10 && down < 0.10);
  }

  // ---- 5. selection: truth > coherence ------------------------------------
  {
    std::vector<Candidate> c{
        {"false but tidy", -0.9, VerifyOutcome::REFUTED, "a"},
        {"true modest", +0.1, VerifyOutcome::VERIFIED, "b"},
        {"unproven guess", -0.2, VerifyOutcome::UNVERIFIABLE, "c"}};
    auto s = select_best(c);
    assert(s.winner_index == 1 && "VERIFIED wins over bigger unproven drop");
    std::cout << "5. selection winner = " << c[s.winner_index].source << "\n";

    assert(select_best({{"x", -1.0, VerifyOutcome::REFUTED, ""}}).winner_index ==
           -1);
    assert(select_best({{"y", +0.1, VerifyOutcome::UNVERIFIABLE, ""}})
               .winner_index == -1);
    std::cout << "6. refuted-only and unhelpful-unverifiable both refused\n";
  }

  std::cout << "\nALL PLASTICITY + SELECTION TESTS PASSED\n";
  return 0;
}
