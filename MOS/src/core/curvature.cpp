#include "mos/core/curvature.hpp"

#include <algorithm>
#include <cmath>
#include <set>
#include <stdexcept>

namespace mos {
namespace core {

namespace {

std::set<HodgeVertex> edge_vertices(const HodgeEdge& e) { return {e.first, e.second}; }

/// True when both edges lie in a common triangle of cx.
bool share_a_triangle(const Complex2& cx, int a, int b) {
    const HodgeEdge& ea = cx.edges()[a];
    const HodgeEdge& eb = cx.edges()[b];
    for (const auto& t : cx.triangles()) {
        const std::set<HodgeVertex> tv{std::get<0>(t), std::get<1>(t), std::get<2>(t)};
        const bool has_a = tv.count(ea.first) && tv.count(ea.second);
        const bool has_b = tv.count(eb.first) && tv.count(eb.second);
        if (has_a && has_b) return true;
    }
    return false;
}

int degree_of(const Complex2& cx, const HodgeVertex& v) {
    int d = 0;
    for (const auto& e : cx.edges()) {
        if (e.first == v || e.second == v) ++d;
    }
    return d;
}

int triangles_containing(const Complex2& cx, int edge_i) {
    const HodgeEdge& e = cx.edges()[edge_i];
    int m = 0;
    for (const auto& t : cx.triangles()) {
        const std::set<HodgeVertex> tv{std::get<0>(t), std::get<1>(t), std::get<2>(t)};
        if (tv.count(e.first) && tv.count(e.second)) ++m;
    }
    return m;
}

void check_positive(const std::vector<double>& xs, const char* what) {
    for (std::size_t i = 0; i < xs.size(); ++i) {
        if (!(xs[i] > 0.0)) {
            throw std::invalid_argument(
                std::string(what) + "[" + std::to_string(i) +
                "] must be strictly positive; a zero weight is an infinitely noisy "
                "cell, which is a measurement to state explicitly, not a default.");
        }
    }
}

}  // namespace

double tau_face(const std::vector<double>& edge_precisions) {
    if (edge_precisions.empty()) {
        throw std::invalid_argument("tau_face: a face with no edges has no precision.");
    }
    check_positive(edge_precisions, "pi");
    double inv_sum = 0.0;
    for (const double p : edge_precisions) inv_sum += 1.0 / p;
    // |f| / sum(1/pi_e): the harmonic mean. The |f| factor is what makes all
    // pi_e = 1 give tau_f = 1, and hence F_MOS degrade exactly.
    return static_cast<double>(edge_precisions.size()) / inv_sum;
}

CurvatureWeights CurvatureWeights::unit(const Complex2& cx) {
    CurvatureWeights w;
    w.pi.assign(static_cast<std::size_t>(cx.num_edges()), 1.0);
    w.nu.assign(static_cast<std::size_t>(cx.num_vertices()), 1.0);
    return w;
}

std::vector<std::pair<int, int>> parallel_edges(const Complex2& cx, int edge_i) {
    if (edge_i < 0 || edge_i >= cx.num_edges()) {
        throw std::invalid_argument("parallel_edges: edge index out of range.");
    }
    const HodgeEdge& e = cx.edges()[edge_i];
    const std::set<HodgeVertex> ev = edge_vertices(e);

    std::vector<std::pair<int, int>> out;
    for (int j = 0; j < cx.num_edges(); ++j) {
        if (j == edge_i) continue;
        const HodgeEdge& f = cx.edges()[j];

        // Shared vertices. Edges in a simplicial complex share at most one.
        std::vector<HodgeVertex> shared;
        for (const auto& v : {f.first, f.second}) {
            if (ev.count(v)) shared.push_back(v);
        }
        if (shared.size() != 1) continue;   // no face in common

        // THE "NOT BOTH" CLAUSE. Sharing a vertex AND a triangle disqualifies.
        // These are exactly the 2m edges closing e's triangles, and removing
        // them from the penalty is where the coefficient 3 comes from.
        if (share_a_triangle(cx, edge_i, j)) continue;

        int vi = 0;
        for (int k = 0; k < cx.num_vertices(); ++k) {
            if (cx.vertices()[static_cast<std::size_t>(k)] == shared[0]) { vi = k; break; }
        }
        out.emplace_back(j, vi);
    }
    return out;
}

double forman_combinatorial(const Complex2& cx, int edge_i) {
    if (edge_i < 0 || edge_i >= cx.num_edges()) {
        throw std::invalid_argument("forman_combinatorial: edge index out of range.");
    }
    const HodgeEdge& e = cx.edges()[edge_i];
    const int du = degree_of(cx, e.first);
    const int dv = degree_of(cx, e.second);
    const int m = triangles_containing(cx, edge_i);
    return 4.0 - du - dv + 3.0 * m;
}

double forman_mos(const Complex2& cx, int edge_i, const CurvatureWeights& w) {
    if (edge_i < 0 || edge_i >= cx.num_edges()) {
        throw std::invalid_argument("forman_mos: edge index out of range.");
    }
    if (static_cast<int>(w.pi.size()) != cx.num_edges()) {
        throw std::invalid_argument(
            "forman_mos: pi has " + std::to_string(w.pi.size()) + " entries, expected " +
            std::to_string(cx.num_edges()) + " (one per edge).");
    }
    if (static_cast<int>(w.nu.size()) != cx.num_vertices()) {
        throw std::invalid_argument(
            "forman_mos: nu has " + std::to_string(w.nu.size()) + " entries, expected " +
            std::to_string(cx.num_vertices()) + " (one per vertex).");
    }
    check_positive(w.pi, "pi");
    check_positive(w.nu, "nu");

    const HodgeEdge& e = cx.edges()[edge_i];
    const double pi_e = w.pi[static_cast<std::size_t>(edge_i)];

    // --- coface term: pi_e^2 * sum_{f > e} 1/tau_f --------------------------
    double coface = 0.0;
    for (const auto& t : cx.triangles()) {
        const HodgeVertex& a = std::get<0>(t);
        const HodgeVertex& b = std::get<1>(t);
        const HodgeVertex& c = std::get<2>(t);
        const std::set<HodgeVertex> tv{a, b, c};
        if (!(tv.count(e.first) && tv.count(e.second))) continue;

        std::vector<double> face_pi;
        for (const auto& face : {HodgeEdge{a, b}, HodgeEdge{a, c}, HodgeEdge{b, c}}) {
            const auto [j, orient] = cx.edge_index(face.first, face.second);
            (void)orient;
            face_pi.push_back(w.pi[static_cast<std::size_t>(j)]);
        }
        coface += 1.0 / tau_face(face_pi);
    }
    coface *= pi_e * pi_e;

    // --- face term: nu_u + nu_v ---------------------------------------------
    int iu = 0, iv = 0;
    for (int k = 0; k < cx.num_vertices(); ++k) {
        if (cx.vertices()[static_cast<std::size_t>(k)] == e.first) iu = k;
        if (cx.vertices()[static_cast<std::size_t>(k)] == e.second) iv = k;
    }
    const double face_term = w.nu[static_cast<std::size_t>(iu)] + w.nu[static_cast<std::size_t>(iv)];

    // --- penalty: sum over parallel edges ------------------------------------
    double penalty = 0.0;
    for (const auto& [j, gamma] : parallel_edges(cx, edge_i)) {
        const double pi_other = w.pi[static_cast<std::size_t>(j)];
        penalty += w.nu[static_cast<std::size_t>(gamma)] * std::sqrt(pi_e / pi_other);
    }

    return coface + face_term - penalty;
}

std::vector<double> forman_mos_all(const Complex2& cx, const CurvatureWeights& w) {
    std::vector<double> out;
    out.reserve(static_cast<std::size_t>(cx.num_edges()));
    for (int i = 0; i < cx.num_edges(); ++i) out.push_back(forman_mos(cx, i, w));
    return out;
}

// ------------------------------------------------------- barrier controller --

double exponential_step(double w, double kappa, double eps_flow) {
    return w * std::exp(eps_flow * kappa);
}

double euler_step_unsafe(double w, double kappa, double eps_flow) {
    return w * (1.0 + eps_flow * kappa);
}

double barrier_step(double w, double kappa, const BarrierConfig& cfg) {
    if (!(cfg.theta_safe < cfg.w_max)) {
        throw std::invalid_argument(
            "barrier_step: empty safe band (theta_safe=" + std::to_string(cfg.theta_safe) +
            " >= w_max=" + std::to_string(cfg.w_max) + ").");
    }
    if (!(w >= cfg.theta_safe && w <= cfg.w_max)) {
        throw std::invalid_argument(
            "barrier_step: w=" + std::to_string(w) + " starts outside [" +
            std::to_string(cfg.theta_safe) + ", " + std::to_string(cfg.w_max) +
            "]. Forward invariance is a statement about trajectories that START "
            "inside; it cannot rescue one that begins outside.");
    }
    if (kappa == 0.0) return w;

    // alpha(h) = eps_flow*|kappa|*h makes the constrained flow exactly
    // integrable, and coincides with weight-dependent plasticity's soft bound.
    const double decay = std::exp(-cfg.eps_flow * std::fabs(kappa));

    if (kappa < 0.0) {
        // Depression: approach theta_safe asymptotically. The vector field
        // vanishes at the boundary, so the bound is never reached, let alone
        // crossed -- no clip is applied anywhere.
        return cfg.theta_safe + (w - cfg.theta_safe) * decay;
    }
    // Potentiation: the mirrored soft bound toward w_max.
    return cfg.w_max - (cfg.w_max - w) * decay;
}

}  // namespace core
}  // namespace mos
