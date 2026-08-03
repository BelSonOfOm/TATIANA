#include "mos/core/two_complex.hpp"

#include <algorithm>
#include <cmath>
#include <set>
#include <stdexcept>

namespace mos {
namespace core {

const char* to_string(Verdict v) noexcept {
    switch (v) {
        case Verdict::Verified:     return "VERIFIED";
        case Verdict::Unverifiable: return "UNVERIFIABLE";
        default:                    return "REFUTED";
    }
}

double gamma_nu(Verdict verdict, double gamma0, double eps) {
    if (!(gamma0 > 0.0 && gamma0 <= 1.0)) {
        throw std::invalid_argument(
            "gamma0 must lie in (0,1]; got " + std::to_string(gamma0) +
            ". Above 1 the store would overshoot past the cache map, which is not "
            "a faster transfer but a different one.");
    }
    if (!(eps >= 0.0 && eps <= 1.0)) {
        throw std::invalid_argument("eps must lie in [0,1]; got " + std::to_string(eps));
    }
    switch (verdict) {
        case Verdict::Verified:     return gamma0;
        case Verdict::Unverifiable: return eps * gamma0;
        // EXACTLY zero, not merely small: a refuted session must leave the store
        // bit-identical, or repeated refutations would still drift it.
        default:                    return 0.0;
    }
}

double gamma_no_verdict(const VerdictCounts& counts, double gamma0, double eps,
                        double kappa, double prior_verified,
                        double prior_unverifiable) {
    if (!(gamma0 > 0.0 && gamma0 <= 1.0)) {
        throw std::invalid_argument(
            "gamma0 must lie in (0,1]; got " + std::to_string(gamma0));
    }
    if (!(eps >= 0.0 && eps <= 1.0)) {
        throw std::invalid_argument("eps must lie in [0,1]; got " + std::to_string(eps));
    }
    // Strictly positive: at kappa = 0 with no observations the estimator is 0/0.
    // A zero-strength prior is not "no prior", it is an undefined one.
    if (!(kappa > 0.0)) {
        throw std::invalid_argument(
            "kappa must be > 0; got " + std::to_string(kappa) +
            ". kappa = 0 with no observations is 0/0, not an uninformative prior.");
    }
    if (!(prior_verified >= 0.0 && prior_unverifiable >= 0.0 &&
          prior_verified + prior_unverifiable <= 1.0)) {
        throw std::invalid_argument(
            "prior_verified and prior_unverifiable must be non-negative and sum to "
            "at most 1; the remainder is prior_refuted.");
    }
    if (counts.verified < 0 || counts.unverifiable < 0 || counts.refuted < 0) {
        throw std::invalid_argument("verdict counts must be non-negative");
    }

    // gamma(Refuted) = 0, so refutations enter ONLY through the denominator --
    // they dilute the rate rather than subtract from it. That is the correct
    // behaviour: a history of refutations should make an unchecked tick worth
    // LESS, and it does, without ever driving gamma negative.
    const double num =
        (static_cast<double>(counts.verified) + kappa * prior_verified) +
        eps * (static_cast<double>(counts.unverifiable) + kappa * prior_unverifiable);
    const double den = static_cast<double>(counts.total()) + kappa;

    return gamma0 * (num / den);
}

// ------------------------------------------------------------------- Store --

Store::Store(Complex2 cx, int d) : complex(std::move(cx)), d_(d) {
    if (d <= 0) throw std::invalid_argument("Store: stalk dimension must be positive.");
    // The store starts as the CONSTANT sheaf: every restriction map is the
    // identity, so Q = 0 and nothing has yet been learned about the wiring.
    for (const auto& e : complex.edges()) {
        restriction.emplace(e, HouseholderMap::identity(d));
        coupling.emplace(e, 1.0);
    }
}

double Store::Q() const {
    if (complex.num_edges() == 0) return 0.0;
    double total = 0.0;
    const Eigen::MatrixXd I = Eigen::MatrixXd::Identity(d_, d_);
    for (const auto& e : complex.edges()) {
        const auto it = restriction.find(e);
        if (it == restriction.end()) continue;
        total += (it->second.dense() - I).squaredNorm();
    }
    return total / static_cast<double>(complex.num_edges());
}

// ----------------------------------------------------------------- Working --

void Working::touch(const HodgeEdge& e) {
    if (!was_touched(e)) touched.push_back(e);
}

bool Working::was_touched(const HodgeEdge& e) const {
    return std::find(touched.begin(), touched.end(), e) != touched.end();
}

// --------------------------------------------------------------- adjunction --

Working i_star(const Store& store, const std::vector<HodgeVertex>& vertices) {
    const std::set<HodgeVertex> keep(vertices.begin(), vertices.end());
    const std::set<HodgeVertex> known(store.complex.vertices().begin(),
                                      store.complex.vertices().end());
    for (const auto& v : keep) {
        if (!known.count(v)) {
            throw std::invalid_argument("i_star: vertex '" + v + "' is not in the store.");
        }
    }

    // DOWNWARD CLOSURE: a simplex survives only if every vertex does.
    std::vector<HodgeEdge> edges;
    for (const auto& e : store.complex.edges()) {
        if (keep.count(e.first) && keep.count(e.second)) edges.push_back(e);
    }
    std::vector<HodgeTriangle> triangles;
    for (const auto& t : store.complex.triangles()) {
        if (keep.count(std::get<0>(t)) && keep.count(std::get<1>(t)) &&
            keep.count(std::get<2>(t))) {
            triangles.push_back(t);
        }
    }

    std::vector<HodgeVertex> ordered;
    for (const auto& v : store.complex.vertices()) {
        if (keep.count(v)) ordered.push_back(v);
    }

    Working w{Complex2(ordered, edges, triangles), {}, {}, {}};
    for (const auto& e : edges) {
        // The cache STARTS as a copy of the store's wiring. Learning is the
        // departure from this, dR = R^W - i^* R^K, which is zero right here.
        w.restriction.emplace(e, store.restriction.at(e));
    }
    return w;
}

int i_shriek(Store& store, const Working& working, double gamma) {
    if (!(gamma >= 0.0 && gamma <= 1.0)) {
        throw std::invalid_argument("i_shriek: gamma must lie in [0,1].");
    }
    if (gamma == 0.0) return 0;   // Refuted: the store must not move at all.

    int modified = 0;
    for (const auto& e : working.touched) {
        auto ws = working.restriction.find(e);
        auto ks = store.restriction.find(e);
        if (ws == working.restriction.end() || ks == store.restriction.end()) {
            throw std::invalid_argument(
                "i_shriek: touched edge (" + e.first + ", " + e.second +
                ") is missing from the working or store sheaf.");
        }
        ks->second = crystallise(ks->second, ws->second, gamma);
        ++modified;
    }
    // NOTE what is NOT here: working.section is never consulted. Content and
    // wiring persist; the episode does not.
    return modified;
}

std::map<HodgeEdge, double> delta_R(const Store& store, const Working& working) {
    std::map<HodgeEdge, double> out;
    for (const auto& [e, rw] : working.restriction) {
        auto ks = store.restriction.find(e);
        if (ks == store.restriction.end()) continue;
        out[e] = (rw.dense() - ks->second.dense()).norm();
    }
    return out;
}

// ------------------------------------------------------------ crystallisation --

Eigen::MatrixXd crystallise_dense(const Eigen::MatrixXd& A,
                                  const Eigen::MatrixXd& B,
                                  double gamma) {
    if (A.rows() != B.rows() || A.cols() != B.cols()) {
        throw std::invalid_argument("crystallise_dense: shape mismatch.");
    }
    const Eigen::MatrixXd M = A + gamma * (B - A);
    // Pi_O(d)(M) = U V^T for M = U S V^T -- the nearest orthogonal matrix in
    // Frobenius norm (the orthogonal Procrustes solution).
    Eigen::JacobiSVD<Eigen::MatrixXd> svd(M, Eigen::ComputeFullU | Eigen::ComputeFullV);
    return svd.matrixU() * svd.matrixV().transpose();
}

HouseholderMap crystallise(const HouseholderMap& A, const HouseholderMap& B, double gamma) {
    if (A.dim() != B.dim()) {
        throw std::invalid_argument("crystallise: dimension mismatch.");
    }
    if (!(gamma >= 0.0 && gamma <= 1.0)) {
        throw std::invalid_argument("crystallise: gamma must lie in [0,1].");
    }
    const int d = A.dim();
    if (gamma == 0.0) return A;

    // ---- PARITY IS A TOPOLOGICAL OBSTRUCTION, NOT A CODING INCONVENIENCE ----
    // det(H_1...H_m) = (-1)^m, so maps with different reflection-count parity lie
    // in DIFFERENT COMPONENTS of O(d). No continuous path joins them, and any
    // "interpolation" between them would have to jump. Refuse rather than
    // silently produce a discontinuity. (m defaults to 4, i.e. SO(d), so the
    // store's identity and every learned map are in the same component.)
    if ((A.m() % 2) != (B.m() % 2)) {
        throw std::invalid_argument(
            "crystallise: reflection-count parity differs (m=" + std::to_string(A.m()) +
            " vs " + std::to_string(B.m()) + "), so det differs in sign and the two "
            "maps lie in different components of O(d). No continuous path exists; "
            "this is a topological obstruction, not a numerical one.");
    }

    // ---- PAD THE SHORTER MAP WITH CANCELLING PAIRS -------------------------
    // The identity has NO reflection vectors, so there is nothing to slerp from
    // -- which meant a store starting as the constant sheaf could never learn.
    // But H_v H_v = I, so the identity has many m-reflection representations.
    // Pad the shorter list with duplicated pairs drawn from the longer one: the
    // pairs cancel (so the padded map still equals the original exactly), and
    // every slot then has a partner to interpolate toward.
    auto padded = [](const std::vector<Eigen::VectorXd>& shorter,
                     const std::vector<Eigen::VectorXd>& longer) {
        std::vector<Eigen::VectorXd> out = shorter;
        for (std::size_t j = shorter.size(); j + 1 < longer.size() + 1 && out.size() < longer.size();
             j += 2) {
            out.push_back(longer[j]);
            if (out.size() < longer.size()) out.push_back(longer[j]);
        }
        return out;
    };

    std::vector<Eigen::VectorXd> av = A.vectors();
    std::vector<Eigen::VectorXd> bv = B.vectors();
    if (av.size() < bv.size())      av = padded(av, bv);
    else if (bv.size() < av.size()) bv = padded(bv, av);
    const std::size_t m = av.size();

    std::vector<Eigen::VectorXd> out;
    out.reserve(m);
    for (std::size_t i = 0; i < m; ++i) {
        const Eigen::VectorXd& a = av[i];
        Eigen::VectorXd b = bv[i];
        // A Householder vector and its negation give the SAME reflection, so pick
        // the representative on the near side of the sphere before interpolating;
        // otherwise slerp would take the long way round for no geometric reason.
        if (a.dot(b) < 0.0) b = -b;

        const double cos_theta = std::max(-1.0, std::min(1.0, a.dot(b)));
        const double theta = std::acos(cos_theta);
        Eigen::VectorXd v;
        if (theta < 1e-12) {
            v = a;                       // already aligned; slerp is degenerate
        } else {
            const double s = std::sin(theta);
            v = (std::sin((1.0 - gamma) * theta) / s) * a + (std::sin(gamma * theta) / s) * b;
        }
        const double n = v.norm();
        if (n > 1e-300) out.push_back(v / n);
    }
    return HouseholderMap(d, std::move(out));
}

}  // namespace core
}  // namespace mos
