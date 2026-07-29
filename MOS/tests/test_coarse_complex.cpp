// Parity test: the C++ CoarseComplex must reproduce python/coherence.py exactly.
// If these two ever disagree, the Python reference is authoritative and the C++
// is wrong — that is the whole point of keeping a tested reference implementation.

#include "mos/core/coarse_complex.hpp"

#include <cassert>
#include <cmath>
#include <iostream>

using namespace mos::core;

static bool close(double a, double b, double tol = 1e-9) {
  return std::fabs(a - b) < tol;
}

int main() {
  std::cout << "=== C++ CoarseComplex parity tests ===\n\n";

  // Four organs, 8-dimensional positions, mirroring the Python self-test shape.
  const int d = 8;
  Eigen::VectorXd base(d);
  base << 1.0, -0.5, 0.25, 2.0, -1.5, 0.75, 0.1, -0.9;

  // ---- 1. perfect agreement --------------------------------------------
  {
    CoarseComplex K(1.0, 0.25);
    for (const auto &m : {"planner", "search", "reason", "verify"}) {
      K.register_module(m);
      K.set_stalk(m, base);
    }
    K.co_activate("planner", "search", 1.0);
    K.co_activate("search", "reason", 1.0);
    K.co_activate("reason", "verify", 1.0);

    auto r = K.report();
    std::cout << "1. all identical      -> " << r.summary() << "\n";
    assert(r.rho.has_value());
    assert(close(*r.rho, 0.0));
    assert(r.b0 == 1);
    assert(!r.worst_edge().has_value() && "no disagreement => no guilty edge");
  }

  // ---- 2. one organ disagrees ------------------------------------------
  {
    CoarseComplex K(1.0, 0.25);
    for (const auto &m : {"planner", "search", "reason", "verify"}) {
      K.register_module(m);
      K.set_stalk(m, base);
    }
    K.set_stalk("verify", -base);
    K.co_activate("planner", "search", 1.0);
    K.co_activate("search", "reason", 1.0);
    K.co_activate("reason", "verify", 1.0);

    auto r = K.report();
    std::cout << "2. verify disagrees   -> " << r.summary() << "\n";
    assert(r.rho.has_value() && *r.rho > 0.0);
    auto w = r.worst_edge();
    assert(w.has_value());
    std::cout << "   guilty coalition   -> (" << w->first << ", " << w->second
              << ")\n";
    assert(w->first == "reason" && w->second == "verify");

    // Python reference: rho == 0.25 for this exact configuration
    // (omega = |2*base|^2 = 4*|base|^2 ; B = 4 ; ||X||_F^2 = 4*|base|^2).
    assert(close(*r.rho, 0.25, 1e-9) && "must match python/coherence.py");
    std::cout << "   matches python reference rho=0.2500 \n";
  }

  // ---- 3. THE TRAP: no edges -------------------------------------------
  {
    CoarseComplex K;
    for (const auto &m : {"a", "b", "c"}) {
      K.register_module(m);
      K.set_stalk(m, base);
    }
    auto r = K.report();
    std::cout << "3. no edges           -> " << r.summary() << "\n";
    assert(!r.rho.has_value() && "must be UNKNOWN, never confidence=1");
    assert(r.status == "no_edges");
    assert(r.b0 == 3);
  }

  // ---- 4. fragmentation is visible -------------------------------------
  {
    CoarseComplex K;
    for (const auto &m : {"a", "b", "c", "d"}) {
      K.register_module(m);
      K.set_stalk(m, base);
    }
    K.co_activate("a", "b", 1.0);
    K.co_activate("c", "d", 1.0);
    auto r = K.report();
    std::cout << "4. two disjoint pairs -> " << r.summary() << "\n";
    assert(r.b0 == 2 && r.is_fragmented());
  }

  // ---- 5. idle organs are excluded, not zero-filled ---------------------
  {
    CoarseComplex K;
    K.register_module("a");
    K.register_module("b");
    K.set_stalk("a", base);
    K.co_activate("a", "b", 1.0); // b never got a position
    auto r = K.report();
    std::cout << "5. one organ idle     -> " << r.summary() << "\n";
    assert(r.n_vertices == 1 && r.n_edges == 0);
    assert(!r.rho.has_value() && "idle organ must not be treated as a zero vector");
  }

  // ---- 6. dimension mismatch is refused --------------------------------
  {
    CoarseComplex K;
    K.register_module("a");
    K.register_module("b");
    K.set_stalk("a", base);
    bool threw = false;
    try {
      K.set_stalk("b", Eigen::VectorXd::Zero(d + 3));
    } catch (const std::invalid_argument &) {
      threw = true;
    }
    std::cout << "6. dim mismatch       -> "
              << (threw ? "correctly REFUSED" : "ACCEPTED (BUG)") << "\n";
    assert(threw && "geometry must never be padded or truncated");
  }

  // ---- 7. decay collapses coalitions -----------------------------------
  {
    CoarseComplex K(1.0, 0.5);
    K.register_module("a");
    K.register_module("b");
    K.set_stalk("a", base);
    K.set_stalk("b", base);
    K.co_activate("a", "b", 1.0);
    assert(K.is_bound("a", "b"));
    for (int i = 0; i < 3; ++i) {
      K.tick_decay();
    }
    auto r = K.report();
    std::cout << "7. after decay        -> " << r.summary() << "\n";
    assert(!K.is_bound("a", "b"));
    assert(!r.rho.has_value() && r.status == "no_edges");

    std::cout << "   mutation log:\n";
    for (const auto &m : K.mutation_log()) {
      std::cout << "     " << m << "\n";
    }
  }

  // ---- 8. rho stays within [0,1] under randomised states ----------------
  {
    double worst = 0.0;
    for (int trial = 0; trial < 500; ++trial) {
      CoarseComplex K;
      const char *names[] = {"a", "b", "c", "d", "e"};
      for (const auto &m : names) {
        K.register_module(m);
        K.set_stalk(m, Eigen::VectorXd::Random(d));
      }
      K.co_activate("a", "b", 1.0);
      K.co_activate("b", "c", 1.0);
      K.co_activate("c", "d", 1.0);
      K.co_activate("d", "e", 1.0);
      K.co_activate("e", "a", 1.0);
      auto r = K.report();
      assert(r.rho.has_value());
      assert(*r.rho >= 0.0 && *r.rho <= 1.0);
      worst = std::max(worst, *r.rho);
    }
    std::cout << "8. 500 random trials  -> all rho in [0,1], max = " << worst
              << "\n";
  }

  // ---- 9. (5p mechanism 1) precision + restriction maps -----------------
  {
    const int dd = 8;
    Eigen::VectorXd a = Eigen::VectorXd::Zero(dd); a(0) = 1.0;
    Eigen::VectorXd b = a; b(1) = 0.2;   // ||a-b||^2 = 0.04
    Eigen::VectorXd c = b; c(2) = 1.0;   // ||b-c||^2 = 1.00
    CoarseComplex K(1.0, 0.25);
    for (const auto &m : {"a", "b", "c"}) K.register_module(m);
    K.set_stalk("a", a); K.set_stalk("b", b); K.set_stalk("c", c);
    K.co_activate("a", "b", 100.0);   // coupling (= precision when enabled) 100
    K.co_activate("b", "c", 1.0);     // coupling 1

    // uniform pi: the big raw gap (b,c) is the guilty edge
    auto flat = K.report();
    auto wf = flat.worst_edge();
    assert(wf.has_value() && wf->first == "b" && wf->second == "c");

    // precision on: 100*0.04=4.0 outweighs 1*1.0 -> blame moves to (a,b)
    K.set_use_precision(true);
    auto ww = K.report().worst_edge();
    std::cout << "9. precision reweight -> worst (" << ww->first << ", "
              << ww->second << ")\n";
    assert(ww.has_value() && ww->first == "a" && ww->second == "b"
           && "precision must move blame to the trusted-but-disagreeing edge");

    // identity restriction maps must reproduce the no-map discord EXACTLY
    K.set_use_precision(false);
    double rho_plain = *K.report().rho;
    Eigen::MatrixXd I = Eigen::MatrixXd::Identity(dd, dd);
    K.set_restriction("a", "b", I, I);
    K.set_restriction("b", "c", I, I);
    double rho_ident = *K.report().rho;
    std::cout << "   identity maps rho=" << rho_ident << " == plain rho="
              << rho_plain << "\n";
    assert(close(rho_plain, rho_ident, 1e-12) && "identity maps must be a no-op");
  }

  // --- 10. E1: rho factors EXACTLY as alpha * rho_tilde ---------------------
  {
    const int dd = 6;
    CoarseComplex K(1.0, 0.25);
    for (const auto &m : {"a", "b", "c", "d"}) K.register_module(m);
    Eigen::VectorXd xa(dd), xb(dd), xc(dd), xd(dd);
    xa << 1, 0, 0, 0, 0, 0;
    xb << 0, 1, 0, 0, 0, 0;
    xc << 0, 0, 1, 0, 0, 0;
    xd << 0, 0, 0, 1, 0, 0;
    K.set_stalk("a", xa); K.set_stalk("b", xb);
    K.set_stalk("c", xc); K.set_stalk("d", xd);
    K.co_activate("a", "b", 1.0);
    K.co_activate("b", "c", 1.0);
    K.co_activate("c", "d", 1.0);

    auto r = K.report();
    assert(r.split_status == "ok" && "connected identity-map case must split");
    assert(r.alpha.has_value() && r.rho_tilde.has_value() && r.window.has_value());
    const double prod = *r.alpha * *r.rho_tilde;
    std::cout << "10. " << r.split_summary() << "\n";
    std::cout << "    alpha*rho_tilde=" << prod << " == rho=" << *r.rho << "\n";
    assert(close(prod, *r.rho, 1e-12) && "rho MUST equal alpha * rho_tilde exactly");

    // Courant-Fischer: the mode index cannot leave its graph-invariant window.
    assert(*r.rho_tilde >= r.window->first - 1e-12 &&
           *r.rho_tilde <= r.window->second + 1e-12 &&
           "rho_tilde must lie inside [lambda_min_plus/B, lambda_max/B]");
    auto pos = r.mode_position();
    assert(pos.has_value() && *pos >= -1e-12 && *pos <= 1.0 + 1e-12);
  }

  // --- 11. E1: FRAGMENTED uses PER-COMPONENT means, not the global mean -----
  {
    const int dd = 4;
    CoarseComplex K(1.0, 0.25);
    for (const auto &m : {"p", "q", "r", "s"}) K.register_module(m);
    Eigen::VectorXd camp(dd); camp << 1, 0, 0, 0;
    Eigen::VectorXd far(dd);  far  << 0, 50, 0, 0;
    K.set_stalk("p", camp);       K.set_stalk("q", camp);
    K.set_stalk("r", camp + far); K.set_stalk("s", camp + far);
    K.co_activate("p", "q", 1.0);
    K.co_activate("r", "s", 1.0);   // two disconnected camps, far apart

    auto r = K.report();
    assert(r.b0 == 2 && "two components expected");
    // Between-component separation lies IN ker L and is NOT dissent. A global-mean
    // projection would report alpha ~ 1 here; the correct one reports ~ 0.
    assert(r.alpha.has_value() && *r.alpha < 1e-12);
    std::cout << "11. fragmented b0=" << r.b0 << " alpha=" << *r.alpha
              << " (~0: each camp agrees internally)\n";
  }

  // --- 12. E1: consensus has no mode; non-identity maps refuse the split ----
  {
    const int dd = 4;
    Eigen::VectorXd v(dd); v << 1, 2, 3, 4;
    CoarseComplex K(1.0, 0.25);
    for (const auto &m : {"a", "b"}) K.register_module(m);
    K.set_stalk("a", v); K.set_stalk("b", v);      // identical => consensus
    K.co_activate("a", "b", 1.0);
    auto r = K.report();
    assert(r.split_status == "consensus");
    assert(r.alpha.has_value() && *r.alpha == 0.0);
    assert(!r.rho_tilde.has_value() && "perfect consensus has NO mode: must be UNKNOWN, not 0");
    std::cout << "12. " << r.split_summary() << "\n";

    // A genuinely non-identity map must make the split refuse, leaving rho exact.
    Eigen::MatrixXd R = Eigen::MatrixXd::Identity(dd, dd);
    R(0, 0) = 0.0; R(0, 1) = 1.0; R(1, 0) = 1.0; R(1, 1) = 0.0;  // a swap: orthogonal
    K.set_restriction("a", "b", R, Eigen::MatrixXd::Identity(dd, dd));
    auto r2 = K.report();
    assert(r2.split_status == "non_identity_maps");
    assert(!r2.alpha.has_value() && r2.rho.has_value() &&
           "split refuses, but rho itself stays exact");
    std::cout << "    " << r2.split_summary() << " (rho still exact: " << *r2.rho << ")\n";
  }

  std::cout << "\nALL COARSE COMPLEX TESTS PASSED\n";
  return 0;
}
