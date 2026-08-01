#include "mos/core/coning.hpp"

#include <Eigen/Dense>
#include <algorithm>
#include <set>
#include <stdexcept>

namespace mos {
namespace core {

int betti1(const Complex2& cx) {
    int rank_d1 = 0;
    if (cx.num_triangles() > 0) {
        Eigen::ColPivHouseholderQR<Eigen::MatrixXd> qr(cx.dense_delta1_for_rank());
        qr.setThreshold(1e-10);
        rank_d1 = static_cast<int>(qr.rank());
    }
    return cx.num_edges() - (cx.num_vertices() - cx.b0()) - rank_d1;
}

namespace {

bool has_edge(const Complex2& cx, const HodgeVertex& u, const HodgeVertex& v) {
    try {
        (void)cx.edge_index(u, v);
        return true;
    } catch (const std::invalid_argument&) {
        return false;
    }
}

}  // namespace

ConeResult cone_off_cycle(const Complex2& cx,
                          const std::vector<HodgeVertex>& cycle,
                          const HodgeVertex& apex) {
    if (cycle.size() < 3) {
        throw std::invalid_argument(
            "cone_off_cycle: a cycle needs at least 3 vertices; got " +
            std::to_string(cycle.size()) + ".");
    }
    if (std::set<HodgeVertex>(cycle.begin(), cycle.end()).size() != cycle.size()) {
        throw std::invalid_argument("cone_off_cycle: the cycle repeats a vertex.");
    }

    const std::set<HodgeVertex> known(cx.vertices().begin(), cx.vertices().end());
    for (const auto& v : cycle) {
        if (!known.count(v)) {
            throw std::invalid_argument("cone_off_cycle: unknown vertex '" + v + "'.");
        }
    }
    if (known.count(apex)) {
        throw std::invalid_argument(
            "cone_off_cycle: apex '" + apex + "' already exists. The attachment must "
            "introduce a NEW cell, not overwrite one.");
    }

    // The consecutive pairs must already be edges. A "cycle" that is not one in
    // the complex would have us inventing edges, which changes the topology we
    // are trying to repair rather than repairing it.
    const std::size_t n = cycle.size();
    for (std::size_t i = 0; i < n; ++i) {
        const auto& u = cycle[i];
        const auto& v = cycle[(i + 1) % n];
        if (!has_edge(cx, u, v)) {
            throw std::invalid_argument(
                "cone_off_cycle: (" + u + ", " + v + ") is not an edge, so the given "
                "vertices do not form a cycle in this complex. Refusing to invent it.");
        }
    }

    std::vector<HodgeVertex> vertices = cx.vertices();
    vertices.push_back(apex);

    std::vector<HodgeEdge> edges = cx.edges();
    for (const auto& v : cycle) edges.push_back({apex, v});

    std::vector<HodgeTriangle> triangles = cx.triangles();
    for (std::size_t i = 0; i < n; ++i) {
        // The cone's faces. These are what make the cycle BOUND; adding the
        // spokes without them would leave the hole open (and add new ones).
        triangles.push_back({apex, cycle[i], cycle[(i + 1) % n]});
    }

    ConeResult r{Complex2(vertices, edges, triangles), apex, betti1(cx), 0};
    r.betti1_after = betti1(r.complex);
    return r;
}

ConeResult chord_cycle(const Complex2& cx, const HodgeVertex& u, const HodgeVertex& v) {
    const std::set<HodgeVertex> known(cx.vertices().begin(), cx.vertices().end());
    if (!known.count(u) || !known.count(v)) {
        throw std::invalid_argument("chord_cycle: unknown vertex.");
    }
    if (u == v) throw std::invalid_argument("chord_cycle: a self-loop is not a chord.");
    if (has_edge(cx, u, v)) {
        throw std::invalid_argument("chord_cycle: (" + u + ", " + v + ") already exists.");
    }

    std::vector<HodgeEdge> edges = cx.edges();
    edges.push_back({u, v});

    ConeResult r{Complex2(cx.vertices(), edges, cx.triangles()), "", betti1(cx), 0};
    r.betti1_after = betti1(r.complex);
    return r;
}

}  // namespace core
}  // namespace mos
