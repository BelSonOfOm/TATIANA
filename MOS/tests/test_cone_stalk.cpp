// THE GROWTH LAW'S COST SIDE — DOCS/DERIVATION_MDL_GROWTH_LAW.md §2.1, §5.10a, §5.11.
//
// Every assertion here is a claim from that document, so a failure localises to a
// section number. The C++ mirror of MOS/python/validate_growth_law.py, which
// carries the derivations these numbers came from.
//
// ⚠️ CHECK() RATHER THAN assert(). assert() is compiled out under NDEBUG, so a
// Release build of an assert-based suite reports success without testing
// anything. This one is built in both configurations, so it must hold in both.
//
// The controls are not optional. Without K1 the propagation check would pass for
// a store that has learned nothing at all, and without K2 the saving would be
// measuring the coder rather than the recurrence.

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <functional>
#include <iostream>
#include <random>
#include <stdexcept>
#include <vector>

#include "mos/core/cone_stalk.hpp"

using namespace mos::core;

namespace {

constexpr int kD = 8;

#define CHECK(cond)                                                                \
    do {                                                                           \
        if (!(cond)) {                                                             \
            std::fflush(stdout);                                                   \
            std::fprintf(stderr, "\nFAILED: %s\n  at %s:%d\n", #cond, __FILE__,    \
                         __LINE__);                                                \
            std::abort();                                                          \
        }                                                                          \
    } while (false)

Complex2 ring(int n) {
    std::vector<HodgeVertex> vs;
    for (int i = 0; i < n; ++i) vs.push_back("v" + std::to_string(i));
    std::vector<HodgeEdge> es;
    for (int i = 0; i < n; ++i) es.push_back({vs[i], vs[(i + 1) % n]});
    return Complex2(vs, es);
}

std::vector<HodgeVertex> ring_cycle(int n) {
    std::vector<HodgeVertex> c;
    for (int i = 0; i < n; ++i) c.push_back("v" + std::to_string(i));
    return c;
}

/// The cycle rotated to start at position `r`. Same loop, different base vertex.
std::vector<HodgeVertex> rotate_cycle(const std::vector<HodgeVertex>& c, int r) {
    std::vector<HodgeVertex> out;
    for (std::size_t i = 0; i < c.size(); ++i) {
        out.push_back(c[(static_cast<std::size_t>(r) + i) % c.size()]);
    }
    return out;
}

/// A single Householder reflection in direction e_j.
HouseholderMap reflect(int d, int j) {
    Eigen::VectorXd v = Eigen::VectorXd::Zero(d);
    v(j) = 1.0;
    return HouseholderMap(d, {v});
}

bool close(double a, double b, double tol) { return std::abs(a - b) <= tol; }

bool threw_invalid_argument(const std::function<void()>& f) {
    try {
        f();
    } catch (const std::invalid_argument&) {
        return true;
    } catch (...) {
        return false;
    }
    return false;
}

}  // namespace

int main() {
    // ================================================================ §2.1 [C]
    // CONTROL K1. A store whose every edge is the identity is the CONSTANT sheaf:
    // nothing has been learned about how meaning transports, so EVERY direction is
    // a section and dim lim = d. If a learned store below also reported d, this is
    // the number it would be reporting, and the test would prove nothing.
    {
        const int k = 5;
        Store K(ring(k), kD);
        const auto cyc = ring_cycle(k);

        const Eigen::MatrixXd H = cycle_holonomy(K, cyc);
        CHECK((H - Eigen::MatrixXd::Identity(kD, kD)).cwiseAbs().maxCoeff() < 1e-12);

        const ConeStalk cs = cone_stalk(K, cyc);
        CHECK(cs.dim() == kD);
        std::cout << "[K1] constant sheaf: holonomy = I, dim lim = " << cs.dim()
                  << " (= d, every direction is a section)\n";
    }

    // One reflection anywhere on the cycle turns exactly one direction, so the
    // fixed space drops by exactly 1 -- a number known in advance, against K1's d.
    {
        const int k = 5;
        Store K(ring(k), kD);
        K.restriction.at({"v1", "v2"}) = reflect(kD, 3);
        const auto cyc = ring_cycle(k);

        const ConeStalk cs = cone_stalk(K, cyc);
        CHECK(cs.dim() == kD - 1);
        // The turned direction is e_3, so no retained column may touch it.
        CHECK(cs.leg.row(3).cwiseAbs().maxCoeff() < 1e-9);
        std::cout << "[C] one reflection: dim lim = " << cs.dim()
                  << " (= d-1), and e_3 is excluded\n";

        // §2.1, the load-bearing claim: k-1 of the k legs are DETERMINED, not
        // stored. Propagating from any vertex of the cycle must reproduce the same
        // blocks, rotated -- which is delta^0 = 0 on every edge AND closure round
        // the loop, in one check.
        const auto legs = propagate_legs(K, cyc, cs.leg);
        CHECK(legs.size() == static_cast<std::size_t>(k));
        double worst = 0.0;
        for (int r = 1; r < k; ++r) {
            const auto from_r =
                propagate_legs(K, rotate_cycle(cyc, r), legs[static_cast<std::size_t>(r)]);
            for (int j = 0; j < k; ++j) {
                const auto& expect = legs[static_cast<std::size_t>((r + j) % k)];
                const double e =
                    (from_r[static_cast<std::size_t>(j)] - expect).cwiseAbs().maxCoeff();
                if (e > worst) worst = e;
            }
        }
        CHECK(worst < 1e-12);
        std::cout << "[C] legs propagate consistently from every base vertex, to " << worst
                  << "   -> k-1 legs are free, and the loop closes\n";
    }

    // Reversing the traversal inverts the holonomy, which fixes the same space. If
    // this failed, the orientation handling would be silently wrong and every
    // dimension above would be luck rather than arithmetic.
    {
        const int k = 4;
        Store K(ring(k), kD);
        K.restriction.at({"v0", "v1"}) = reflect(kD, 2);
        K.restriction.at({"v2", "v3"}) = reflect(kD, 5);
        const auto fwd = ring_cycle(k);
        const std::vector<HodgeVertex> rev(fwd.rbegin(), fwd.rend());

        const Eigen::MatrixXd Hf = cycle_holonomy(K, fwd);
        const Eigen::MatrixXd Hr = cycle_holonomy(K, rev);
        const Eigen::MatrixXd I = Eigen::MatrixXd::Identity(kD, kD);
        CHECK((Hf * Hf.transpose() - I).cwiseAbs().maxCoeff() < 1e-12);
        CHECK((Hr * Hr.transpose() - I).cwiseAbs().maxCoeff() < 1e-12);
        CHECK(cone_stalk(K, fwd).dim() == cone_stalk(K, rev).dim());
        CHECK(cone_stalk(K, fwd).dim() == kD - 2);
        std::cout << "[C] reversed traversal: dim lim = " << cone_stalk(K, rev).dim()
                  << " both ways, holonomy exactly orthogonal both ways\n";
    }

    // ============================================================ §5.11 [D,E,F]
    {
        const int k = 5;
        const int n = 40000;
        std::mt19937 gen(20260811);

        auto synth = [&](double rho2) {
            std::normal_distribution<double> nb(0.0, std::sqrt(rho2));
            std::normal_distribution<double> nw(0.0, std::sqrt(1.0 - rho2));
            Eigen::MatrixXd a(n, k);
            for (int t = 0; t < n; ++t) {
                const double s = (rho2 > 0.0) ? nb(gen) : 0.0;
                for (int i = 0; i < k; ++i) a(t, i) = s + nw(gen);
            }
            return a;
        };

        const double mb = model_bits_per_direction(384, 1, 4.0);

        // §5.11.5: rho2_hat = rho2 + (1 - rho2)/k, EXACTLY. Pure noise reads 1/k,
        // which is 0.20 at k = 5 -- inside the range an uncorrected threshold would
        // find encouraging.
        for (double rho2 : {0.9, 0.5, 0.0}) {
            const DirectionVerdict v = score_direction(synth(rho2), mb);
            const double predicted = rho2 + (1.0 - rho2) / k;
            CHECK(close(v.rho2_hat, predicted, 5e-3));
            CHECK(close(v.rho2, rho2, 8e-3));
            std::cout << "[F] true rho2 = " << rho2 << "   rho2_hat = " << v.rho2_hat
                      << " (predicted " << predicted << ")   unbiased = " << v.rho2 << "\n";
        }

        // §5.11.4: a reliable direction pays after a few hundred traversals.
        const DirectionVerdict good = score_direction(synth(0.9), mb);
        CHECK(good.ever_pays());
        CHECK(good.n_required > 100.0 && good.n_required < 1000.0);
        std::cout << "[D] rho2 = 0.90: " << good.delta_c
                  << " bits/traversal, n_required = " << good.n_required << "\n";

        // ...and pure noise NEVER pays, at any n. That half is what a frequency
        // threshold alone cannot express.
        const DirectionVerdict noise = score_direction(synth(0.0), mb);
        CHECK(!noise.ever_pays());
        CHECK(std::isinf(noise.n_required));
        std::cout << "[E] rho2 = 0.00: " << noise.delta_c
                  << " bits/traversal, n_required = infinity  -> no recurrence buys it\n";

        // ---- CONTROL K2: shuffle each vertex's readings independently. This
        // preserves every marginal and destroys only the co-occurrence. If the
        // saving survived it, the saving was never measuring the recurrence.
        Eigen::MatrixXd a = synth(0.9);
        for (int i = 0; i < k; ++i) {
            for (int t = n - 1; t > 0; --t) {
                std::uniform_int_distribution<int> pick(0, t);
                std::swap(a(t, i), a(pick(gen), i));
            }
        }
        const DirectionVerdict shuffled = score_direction(a, mb);
        CHECK(!shuffled.ever_pays());
        std::cout << "[K2] shuffled control: rho2_hat = " << shuffled.rho2_hat << ", "
                  << shuffled.delta_c
                  << " bits/traversal  -> the saving is the recurrence, not the coder\n";
    }

    // ================================================================= refusals
    {
        Store K(ring(5), kD);
        CHECK(threw_invalid_argument([&] { (void)cycle_holonomy(K, {"v0", "v1"}); }));
        CHECK(threw_invalid_argument([&] { (void)cycle_holonomy(K, {"v0", "v1", "v0"}); }));
        // v0-v2 is not an edge of a 5-ring: inventing it would change the topology
        // being repaired.
        CHECK(threw_invalid_argument([&] { (void)cycle_holonomy(K, {"v0", "v2", "v4"}); }));
        // b = 0 makes the model free, so every one-off traversal pays -- §6.4.
        CHECK(threw_invalid_argument([&] { (void)model_bits_per_direction(384, 1, 0.0); }));
        std::cout << "[refusals] short cycle, repeated vertex, non-edge and b = 0 all rejected\n";
    }

    std::cout << "\nALL ASSERTIONS PASSED.\n";
    return 0;
}
