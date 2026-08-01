#include "mos/core/instantiate.hpp"

#include <Eigen/Dense>
#include <algorithm>
#include <cmath>
#include <deque>
#include <numeric>
#include <set>
#include <stdexcept>

namespace mos {
namespace core {

namespace {

/// Weighted adjacency of the 1-skeleton: vertex -> [(neighbour, weight)].
std::vector<std::vector<std::pair<int, double>>> adjacency(const Complex2& cx,
                                                           const SkeletonWeights& weights) {
    if (static_cast<int>(weights.w.size()) != cx.num_edges()) {
        throw std::invalid_argument(
            "SkeletonWeights has " + std::to_string(weights.w.size()) +
            " entries, expected " + std::to_string(cx.num_edges()) + " (one per edge).");
    }
    std::map<HodgeVertex, int> vidx;
    for (int i = 0; i < cx.num_vertices(); ++i) vidx[cx.vertices()[static_cast<std::size_t>(i)]] = i;

    std::vector<std::vector<std::pair<int, double>>> adj(static_cast<std::size_t>(cx.num_vertices()));
    for (int e = 0; e < cx.num_edges(); ++e) {
        const double w = weights.w[static_cast<std::size_t>(e)];
        if (!(w > 0.0)) {
            throw std::invalid_argument(
                "Edge weight " + std::to_string(w) + " on edge " + std::to_string(e) +
                " must be strictly positive. A zero coupling is an edge that is not "
                "there; delete it from the complex rather than weighting it away.");
        }
        const int u = vidx.at(cx.edges()[static_cast<std::size_t>(e)].first);
        const int v = vidx.at(cx.edges()[static_cast<std::size_t>(e)].second);
        adj[static_cast<std::size_t>(u)].emplace_back(v, w);
        adj[static_cast<std::size_t>(v)].emplace_back(u, w);
    }
    return adj;
}

std::vector<double> degrees(const std::vector<std::vector<std::pair<int, double>>>& adj) {
    std::vector<double> d(adj.size(), 0.0);
    for (std::size_t u = 0; u < adj.size(); ++u) {
        for (const auto& [v, w] : adj[u]) { (void)v; d[u] += w; }
    }
    return d;
}

std::map<int, double> normalise_seeds(const std::map<int, double>& seeds, int n) {
    double total = 0.0;
    for (const auto& [v, m] : seeds) {
        if (v < 0 || v >= n) {
            throw std::invalid_argument("Seed vertex " + std::to_string(v) + " out of range.");
        }
        if (m < 0.0) throw std::invalid_argument("Negative seed mass.");
        total += m;
    }
    if (!(total > 0.0)) {
        throw std::invalid_argument(
            "Empty or all-zero seed. Refusing to return an empty instantiation for "
            "what is almost certainly a caller bug -- 'retrieve nothing' should be "
            "an explicit decision, not the result of a dropped seed.");
    }
    std::map<int, double> out;
    for (const auto& [v, m] : seeds) {
        if (m > 0.0) out[v] = m / total;
    }
    return out;
}

}  // namespace

SkeletonWeights SkeletonWeights::unit(const Complex2& cx) {
    SkeletonWeights s;
    s.w.assign(static_cast<std::size_t>(cx.num_edges()), 1.0);
    return s;
}

double PPRResult::mass(int v) const {
    auto it = p.find(v);
    return it == p.end() ? 0.0 : it->second;
}

PPRResult approximate_ppr(const Complex2& cx,
                          const SkeletonWeights& weights,
                          const std::map<int, double>& seeds,
                          double alpha,
                          double eps,
                          int max_pushes) {
    if (!(alpha > 0.0 && alpha < 1.0)) {
        throw std::invalid_argument("alpha must lie in (0,1); got " + std::to_string(alpha));
    }
    if (!(eps > 0.0 && eps <= 1.0)) {
        throw std::invalid_argument("eps must lie in (0,1]; got " + std::to_string(eps));
    }

    const auto adj = adjacency(cx, weights);
    const auto deg = degrees(adj);
    const auto seed = normalise_seeds(seeds, cx.num_vertices());

    // ACL's bound on the number of pushes for a unit seed. Used as the default
    // budget so the O(1/(alpha*eps)) claim is enforced by the code, not merely
    // hoped for; a little slack absorbs floating-point boundary cases.
    const int acl_bound = static_cast<int>(std::ceil(1.0 / (alpha * eps)));
    if (max_pushes <= 0) max_pushes = acl_bound + 16;

    PPRResult res;
    for (const auto& [v, m] : seed) res.r[v] = m;

    // Queue of vertices whose residual may exceed the threshold.
    std::deque<int> queue;
    std::set<int> queued;
    const auto ready = [&](int v) {
        auto it = res.r.find(v);
        if (it == res.r.end()) return false;
        const double d = deg[static_cast<std::size_t>(v)];
        // An isolated vertex has degree 0 and can never be pushed onward; its
        // mass simply stays put rather than being silently discarded.
        return d > 0.0 && it->second >= eps * d;
    };
    for (const auto& [v, m] : seed) { (void)m; if (ready(v)) { queue.push_back(v); queued.insert(v); } }

    while (!queue.empty()) {
        if (res.pushes >= max_pushes) { res.budget_exhausted = true; break; }
        const int u = queue.front();
        queue.pop_front();
        queued.erase(u);
        if (!ready(u)) continue;

        const double ru = res.r[u];
        const double du = deg[static_cast<std::size_t>(u)];

        // ACL lazy-walk push.
        res.p[u] += alpha * ru;
        res.r[u] = (1.0 - alpha) * ru / 2.0;
        const double spread = (1.0 - alpha) * ru / (2.0 * du);
        for (const auto& [v, w] : adj[static_cast<std::size_t>(u)]) {
            res.r[v] += spread * w;
            if (!queued.count(v) && ready(v)) { queue.push_back(v); queued.insert(v); }
        }
        if (!queued.count(u) && ready(u)) { queue.push_back(u); queued.insert(u); }
        ++res.pushes;
    }
    return res;
}

std::vector<double> exact_ppr(const Complex2& cx,
                              const SkeletonWeights& weights,
                              const std::map<int, double>& seeds,
                              double alpha) {
    const auto adj = adjacency(cx, weights);
    const auto deg = degrees(adj);
    const auto seed = normalise_seeds(seeds, cx.num_vertices());
    const int n = cx.num_vertices();

    // pr = alpha*s + (1-alpha)*pr*M with M the LAZY walk (I + D^-1 A)/2,
    // matching the push procedure above. Solving (I - (1-alpha) M^T) pr = alpha s.
    Eigen::MatrixXd M = Eigen::MatrixXd::Zero(n, n);
    for (int u = 0; u < n; ++u) {
        M(u, u) += 0.5;
        const double du = deg[static_cast<std::size_t>(u)];
        if (du > 0.0) {
            for (const auto& [v, w] : adj[static_cast<std::size_t>(u)]) {
                M(u, v) += 0.5 * w / du;
            }
        } else {
            M(u, u) += 0.5;   // isolated: the walk stays put
        }
    }
    Eigen::VectorXd s = Eigen::VectorXd::Zero(n);
    for (const auto& [v, m] : seed) s(v) = m;

    const Eigen::MatrixXd A =
        Eigen::MatrixXd::Identity(n, n) - (1.0 - alpha) * M.transpose();
    const Eigen::VectorXd pr = A.colPivHouseholderQr().solve(alpha * s);
    return std::vector<double>(pr.data(), pr.data() + n);
}

SweepCut sweep_cut(const Complex2& cx,
                   const SkeletonWeights& weights,
                   const PPRResult& ppr) {
    const auto adj = adjacency(cx, weights);
    const auto deg = degrees(adj);

    // Order by p(u)/d(u) descending -- the degree normalisation is what makes
    // this a conductance sweep rather than a popularity ranking.
    std::vector<int> order;
    for (const auto& [v, m] : ppr.p) {
        if (m > 0.0 && deg[static_cast<std::size_t>(v)] > 0.0) order.push_back(v);
    }
    std::stable_sort(order.begin(), order.end(), [&](int a, int b) {
        return ppr.mass(a) / deg[static_cast<std::size_t>(a)] >
               ppr.mass(b) / deg[static_cast<std::size_t>(b)];
    });

    double total_vol = 0.0;
    for (const double d : deg) total_vol += d;

    SweepCut best;
    std::set<int> inside;
    double vol = 0.0, cut = 0.0;

    for (const int u : order) {
        inside.insert(u);
        vol += deg[static_cast<std::size_t>(u)];
        // Adding u: its edges to outside vertices join the cut, its edges to
        // already-inside vertices leave it.
        for (const auto& [v, w] : adj[static_cast<std::size_t>(u)]) {
            if (inside.count(v)) cut -= w;
            else cut += w;
        }
        const double other = total_vol - vol;
        const double denom = std::min(vol, other);
        if (denom <= 0.0) continue;   // the whole graph is not a cut
        const double phi = cut / denom;
        if (best.vertices.empty() || phi < best.conductance) {
            best.vertices.assign(inside.begin(), inside.end());
            best.conductance = phi;
            best.volume = vol;
            best.cut = cut;
        }
    }
    if (best.vertices.empty() && !order.empty()) {
        // Degenerate: a single component with no proper cut. Return the whole
        // support rather than nothing, and let conductance say it is trivial.
        best.vertices = order;
        best.conductance = 0.0;
        best.volume = total_vol;
        best.cut = 0.0;
    }
    std::sort(best.vertices.begin(), best.vertices.end());
    return best;
}

Instantiation instantiate(const Complex2& cx,
                          const SkeletonWeights& weights,
                          const std::map<int, double>& seeds,
                          double alpha,
                          double eps) {
    const PPRResult ppr = approximate_ppr(cx, weights, seeds, alpha, eps);
    const SweepCut sc = sweep_cut(cx, weights, ppr);

    std::map<HodgeVertex, int> vidx;
    for (int i = 0; i < cx.num_vertices(); ++i) vidx[cx.vertices()[static_cast<std::size_t>(i)]] = i;

    const std::set<int> inside(sc.vertices.begin(), sc.vertices.end());

    Instantiation out;
    out.vertices = sc.vertices;
    out.conductance = sc.conductance;

    // DOWNWARD CLOSURE: keep a simplex only when EVERY vertex is inside.
    for (int e = 0; e < cx.num_edges(); ++e) {
        const int u = vidx.at(cx.edges()[static_cast<std::size_t>(e)].first);
        const int v = vidx.at(cx.edges()[static_cast<std::size_t>(e)].second);
        const int n_in = static_cast<int>(inside.count(u)) + static_cast<int>(inside.count(v));
        if (n_in == 2) {
            out.edges.push_back(e);
        } else if (n_in == 1) {
            out.cut_weight += weights.w[static_cast<std::size_t>(e)];
        }
    }

    for (int t = 0; t < cx.num_triangles(); ++t) {
        const auto& tri = cx.triangles()[static_cast<std::size_t>(t)];
        const int a = vidx.at(std::get<0>(tri));
        const int b = vidx.at(std::get<1>(tri));
        const int c = vidx.at(std::get<2>(tri));
        const int n_in = static_cast<int>(inside.count(a)) + static_cast<int>(inside.count(b)) +
                         static_cast<int>(inside.count(c));
        if (n_in == 3) {
            out.triangles.push_back(t);
        } else if (n_in > 0) {
            // A 3-way binding with 1 or 2 vertices retrieved is DROPPED, because
            // returning 2 of a jointly-bound 3 is a type error. Its coupling
            // mass is charged to the cut so the loss is visible.
            ++out.sliced_triangles;
            for (const auto& face : {HodgeEdge{std::get<0>(tri), std::get<1>(tri)},
                                     HodgeEdge{std::get<0>(tri), std::get<2>(tri)},
                                     HodgeEdge{std::get<1>(tri), std::get<2>(tri)}}) {
                const auto [j, orient] = cx.edge_index(face.first, face.second);
                (void)orient;
                out.cut_weight += weights.w[static_cast<std::size_t>(j)];
            }
        }
    }
    return out;
}

}  // namespace core
}  // namespace mos
