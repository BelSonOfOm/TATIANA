#include "mos/core/hodge.hpp"

#include <algorithm>
#include <cmath>
#include <numeric>
#include <set>
#include <stdexcept>

namespace mos {
namespace core {

// ---------------------------------------------------------------- Complex2 --

Complex2::Complex2(std::vector<HodgeVertex> vertices,
                   const std::vector<HodgeEdge>& edges,
                   const std::vector<HodgeTriangle>& triangles)
    : vertices_(std::move(vertices)) {
    for (std::size_t i = 0; i < vertices_.size(); ++i) {
        if (!vidx_.emplace(vertices_[i], static_cast<int>(i)).second) {
            throw std::invalid_argument("Duplicate vertex: " + vertices_[i]);
        }
    }

    for (const auto& uv : edges) {
        const HodgeVertex& u = uv.first;
        const HodgeVertex& v = uv.second;
        if (u == v) {
            throw std::invalid_argument("Self-loop (" + u + ", " + v + "): not a 1-simplex.");
        }
        for (const HodgeVertex& w : {u, v}) {
            if (vidx_.find(w) == vidx_.end()) {
                throw std::invalid_argument("Edge (" + u + ", " + v +
                                            ") references unknown vertex " + w);
            }
        }
        const HodgeEdge e = canon_edge(u, v);
        if (eidx_.find(e) != eidx_.end()) {
            throw std::invalid_argument("Duplicate edge (" + e.first + ", " + e.second + ").");
        }
        eidx_.emplace(e, static_cast<int>(edges_.size()));
        edges_.push_back(e);
    }

    for (const auto& t : triangles) {
        std::vector<HodgeVertex> vs{std::get<0>(t), std::get<1>(t), std::get<2>(t)};
        if (std::set<HodgeVertex>(vs.begin(), vs.end()).size() != 3) {
            throw std::invalid_argument("Degenerate triangle.");
        }
        for (const auto& w : vs) {
            if (vidx_.find(w) == vidx_.end()) {
                throw std::invalid_argument("Triangle references unknown vertex " + w);
            }
        }
        // Sorted by VERTEX INDEX, matching python/hodge.py.
        std::sort(vs.begin(), vs.end(),
                  [&](const HodgeVertex& a, const HodgeVertex& b) {
                      return vidx_.at(a) < vidx_.at(b);
                  });
        const HodgeTriangle canon{vs[0], vs[1], vs[2]};

        // Downward closure, ENFORCED. Inventing the missing edge would change b1
        // -- exactly the number the harmonic part exists to expose.
        for (const auto& face : {HodgeEdge{vs[0], vs[1]}, HodgeEdge{vs[0], vs[2]},
                                 HodgeEdge{vs[1], vs[2]}}) {
            if (eidx_.find(canon_edge(face.first, face.second)) == eidx_.end()) {
                throw std::invalid_argument(
                    "Triangle (" + vs[0] + ", " + vs[1] + ", " + vs[2] + ") has face (" +
                    face.first + ", " + face.second +
                    ") that is not an edge. Downward closure is required; refusing to "
                    "invent the edge, because that would change b1 silently.");
            }
        }
        if (std::find(triangles_.begin(), triangles_.end(), canon) != triangles_.end()) {
            throw std::invalid_argument("Duplicate triangle.");
        }
        triangles_.push_back(canon);
    }
}

HodgeEdge Complex2::canon_edge(const HodgeVertex& u, const HodgeVertex& v) const {
    return vidx_.at(u) < vidx_.at(v) ? HodgeEdge{u, v} : HodgeEdge{v, u};
}

std::pair<int, double> Complex2::edge_index(const HodgeVertex& u,
                                            const HodgeVertex& v) const {
    const HodgeEdge e = canon_edge(u, v);
    auto it = eidx_.find(e);
    if (it == eidx_.end()) {
        throw std::invalid_argument("No such edge: (" + u + ", " + v + ")");
    }
    return {it->second, (e.first == u && e.second == v) ? 1.0 : -1.0};
}

Eigen::VectorXd Complex2::apply_delta0(const Eigen::VectorXd& f) const {
    if (f.size() != num_vertices()) {
        throw std::invalid_argument("apply_delta0: expected one value per vertex.");
    }
    Eigen::VectorXd out = Eigen::VectorXd::Zero(num_edges());
    for (int i = 0; i < num_edges(); ++i) {
        out(i) = f(vidx_.at(edges_[i].second)) - f(vidx_.at(edges_[i].first));
    }
    return out;
}

Eigen::VectorXd Complex2::apply_delta0T(const Eigen::VectorXd& x) const {
    if (x.size() != num_edges()) {
        throw std::invalid_argument("apply_delta0T: expected one value per edge.");
    }
    Eigen::VectorXd out = Eigen::VectorXd::Zero(num_vertices());
    for (int i = 0; i < num_edges(); ++i) {
        out(vidx_.at(edges_[i].first)) -= x(i);
        out(vidx_.at(edges_[i].second)) += x(i);
    }
    return out;
}

namespace {
// The three faces of (a,b,c) with delta^1's alternating signs:
//   (delta^1 eta)_(a,b,c) = eta_(b,c) - eta_(a,c) + eta_(a,b)
struct Face { int lo, hi; double sign; };
std::array<Face, 3> faces_of() { return {Face{1, 2, +1.0}, Face{0, 2, -1.0}, Face{0, 1, +1.0}}; }
}  // namespace

Eigen::VectorXd Complex2::apply_delta1(const Eigen::VectorXd& x) const {
    if (x.size() != num_edges()) {
        throw std::invalid_argument("apply_delta1: expected one value per edge.");
    }
    Eigen::VectorXd out = Eigen::VectorXd::Zero(num_triangles());
    for (int k = 0; k < num_triangles(); ++k) {
        const HodgeVertex* v[3] = {&std::get<0>(triangles_[k]), &std::get<1>(triangles_[k]),
                                   &std::get<2>(triangles_[k])};
        for (const auto& f : faces_of()) {
            const auto [j, orient] = edge_index(*v[f.lo], *v[f.hi]);
            out(k) += f.sign * orient * x(j);
        }
    }
    return out;
}

Eigen::VectorXd Complex2::apply_delta1T(const Eigen::VectorXd& y) const {
    if (y.size() != num_triangles()) {
        throw std::invalid_argument("apply_delta1T: expected one value per triangle.");
    }
    Eigen::VectorXd out = Eigen::VectorXd::Zero(num_edges());
    for (int k = 0; k < num_triangles(); ++k) {
        const HodgeVertex* v[3] = {&std::get<0>(triangles_[k]), &std::get<1>(triangles_[k]),
                                   &std::get<2>(triangles_[k])};
        for (const auto& f : faces_of()) {
            const auto [j, orient] = edge_index(*v[f.lo], *v[f.hi]);
            out(j) += f.sign * orient * y(k);
        }
    }
    return out;
}

int Complex2::b0() const {
    std::vector<int> parent(vertices_.size());
    std::iota(parent.begin(), parent.end(), 0);
    std::function<int(int)> find = [&](int a) {
        while (parent[a] != a) { parent[a] = parent[parent[a]]; a = parent[a]; }
        return a;
    };
    for (const auto& e : edges_) {
        const int ra = find(vidx_.at(e.first));
        const int rb = find(vidx_.at(e.second));
        if (ra != rb) parent[ra] = rb;
    }
    std::set<int> roots;
    for (std::size_t i = 0; i < vertices_.size(); ++i) roots.insert(find(static_cast<int>(i)));
    return static_cast<int>(roots.size());
}

Eigen::MatrixXd Complex2::dense_delta1_for_rank() const {
    Eigen::MatrixXd D = Eigen::MatrixXd::Zero(num_triangles(), num_edges());
    for (int k = 0; k < num_triangles(); ++k) {
        const HodgeVertex* v[3] = {&std::get<0>(triangles_[k]), &std::get<1>(triangles_[k]),
                                   &std::get<2>(triangles_[k])};
        for (const auto& f : faces_of()) {
            const auto [j, orient] = edge_index(*v[f.lo], *v[f.hi]);
            D(k, j) += f.sign * orient;
        }
    }
    return D;
}

// -------------------------------------------------------------------- LSQR --

LsqrResult lsqr(const std::function<Eigen::VectorXd(const Eigen::VectorXd&)>& apply,
                const std::function<Eigen::VectorXd(const Eigen::VectorXd&)>& apply_transpose,
                const Eigen::VectorXd& b,
                int n,
                double tol,
                int max_iter) {
    LsqrResult res;
    res.x = Eigen::VectorXd::Zero(n);

    const int m = static_cast<int>(b.size());
    if (max_iter <= 0) max_iter = 4 * std::min(m, n) + 100;

    // Golub-Kahan bidiagonalisation, started at x = 0 so the iterate stays in
    // the Krylov space of A^T b -- which is what makes the limit the
    // MINIMUM-NORM least-squares solution rather than an arbitrary one.
    Eigen::VectorXd u = b;
    double beta = u.norm();
    const double bnorm = beta;
    if (beta > 0.0) u /= beta;

    Eigen::VectorXd v = apply_transpose(u);
    double alpha = v.norm();
    if (alpha > 0.0) v /= alpha;

    Eigen::VectorXd w = v;
    double phibar = beta;
    double rhobar = alpha;
    double anorm = 0.0;

    res.residual_norm = bnorm;
    res.atr_norm = alpha * beta;
    const double atr0 = res.atr_norm;

    if (bnorm == 0.0 || atr0 == 0.0) {
        res.converged = true;      // x = 0 is already the answer
        return res;
    }

    for (int iter = 1; iter <= max_iter; ++iter) {
        // --- continue the bidiagonalisation ---
        u = apply(v) - alpha * u;
        beta = u.norm();
        if (beta > 0.0) u /= beta;

        v = apply_transpose(u) - beta * v;
        alpha = v.norm();
        if (alpha > 0.0) v /= alpha;

        anorm = std::sqrt(anorm * anorm + alpha * alpha + beta * beta);

        // --- Givens rotation to eliminate beta ---
        const double rho = std::hypot(rhobar, beta);
        const double c = rhobar / rho;
        const double s = beta / rho;
        const double theta = s * alpha;
        rhobar = -c * alpha;
        const double phi = c * phibar;
        phibar = s * phibar;

        // --- update the iterate ---
        res.x += (phi / rho) * w;
        w = v - (theta / rho) * w;

        res.iterations = iter;
        res.residual_norm = std::fabs(phibar);
        res.atr_norm = std::fabs(phibar * alpha * c);

        // Optimality for a least-squares problem is ||A^T r|| = 0, NOT ||r|| = 0
        // -- an inconsistent system has a large residual at the true optimum, so
        // testing ||r|| would stop this either far too late or never.
        if (res.atr_norm <= tol * std::max(anorm * res.residual_norm, atr0) ||
            res.residual_norm <= tol * bnorm) {
            res.converged = true;
            break;
        }
    }
    return res;
}

// -------------------------------------------------------------- hodge_split --

std::tuple<double, double, double> HodgeSplit::fractions() const {
    const double d = std::max(norm2, 1e-300);
    return {grad2 / d, curl2 / d, harm2 / d};
}

std::tuple<double, double, double> HodgeSplit::null_fractions() const {
    const double E = static_cast<double>(dim_grad + dim_curl + dim_harm);
    if (E <= 0.0) return {0.0, 0.0, 0.0};
    return {dim_grad / E, dim_curl / E, dim_harm / E};
}

double HodgeSplit::excess_non_gradient() const {
    const auto [ng, nc, nh] = null_fractions();
    (void)ng;
    const double d = std::max(norm2, 1e-300);
    return (curl2 + harm2) / d - (nc + nh);
}

std::vector<std::pair<HodgeEdge, double>> HodgeSplit::harmonic_support(const Complex2& cx,
                                                                      int top) const {
    std::vector<int> order(static_cast<std::size_t>(harm.size()));
    std::iota(order.begin(), order.end(), 0);
    std::stable_sort(order.begin(), order.end(),
                     [&](int a, int b) { return std::fabs(harm(a)) > std::fabs(harm(b)); });
    std::vector<std::pair<HodgeEdge, double>> out;
    const int n = std::min<int>(top, static_cast<int>(order.size()));
    for (int i = 0; i < n; ++i) out.emplace_back(cx.edges()[order[i]], harm(order[i]));
    return out;
}

HodgeSplit hodge_split(const Complex2& cx,
                       const Eigen::VectorXd& eta,
                       const std::optional<std::map<HodgeEdge, double>>& precision) {
    const int E = cx.num_edges();
    if (eta.size() != E) {
        throw std::invalid_argument(
            "eta has " + std::to_string(eta.size()) + " entries, expected " +
            std::to_string(E) + " -- one value per edge, in cx.edges() order.");
    }

    Eigen::VectorXd w = Eigen::VectorXd::Ones(E);
    if (precision.has_value()) {
        for (int i = 0; i < E; ++i) {
            const HodgeEdge& e = cx.edges()[i];
            auto it = precision->find(e);
            if (it == precision->end()) it = precision->find({e.second, e.first});
            if (it == precision->end()) {
                throw std::invalid_argument(
                    "No precision supplied for edge (" + e.first + ", " + e.second +
                    "). Refusing to default silently -- a missing weight is a missing "
                    "measurement, not a weight of 1.");
            }
            if (!(it->second > 0.0)) {
                throw std::invalid_argument(
                    "Precision on edge (" + e.first + ", " + e.second +
                    ") must be > 0 (it is 1/variance, and 0 would delete the edge from "
                    "the inner product without deleting it from the complex).");
            }
            w(i) = it->second;
        }
    }
    const Eigen::VectorXd S = w.array().sqrt();   // W = S^2, so ||x||^2_W = ||S x||^2
    const Eigen::VectorXd Se = S.cwiseProduct(eta);

    HodgeSplit out;

    // --- GRADIENT: argmin_f ||eta - delta^0 f||^2_W -------------------------
    // Whitened so it is ordinary least squares: M = S . delta^0, b = S . eta.
    // NOTE the explicit -> Eigen::VectorXd on every lambda below. Without it the
    // deduced return type is an Eigen EXPRESSION holding a reference to the
    // temporary returned by apply_delta0, which dies at the end of the return
    // statement. The result is silent garbage, not a crash.
    const auto grad_apply = [&](const Eigen::VectorXd& f) -> Eigen::VectorXd {
        return S.cwiseProduct(cx.apply_delta0(f));
    };
    const auto grad_applyT = [&](const Eigen::VectorXd& x) -> Eigen::VectorXd {
        return cx.apply_delta0T(S.cwiseProduct(x));
    };
    const LsqrResult gr = lsqr(grad_apply, grad_applyT, Se, cx.num_vertices());
    Eigen::VectorXd f = gr.x;
    if (f.size() > 0) f.array() -= f.mean();   // potentials live up to a constant
    out.potential = f;
    out.grad = cx.apply_delta0(f);

    // --- CURL: project onto im(delta^1 *), the W-adjoint image ---------------
    // delta^1* = W^{-1} delta^1^T, so  A g = (delta^1^T g) / w  and
    // A^T x = delta^1(x / w). Whitened the same way.
    if (cx.num_triangles() > 0) {
        const auto curl_apply = [&](const Eigen::VectorXd& g) -> Eigen::VectorXd {
            return S.cwiseProduct(cx.apply_delta1T(g).cwiseQuotient(w));
        };
        const auto curl_applyT = [&](const Eigen::VectorXd& x) -> Eigen::VectorXd {
            const Eigen::VectorXd scaled = S.cwiseProduct(x).cwiseQuotient(w);
            return cx.apply_delta1(scaled);
        };
        const LsqrResult cr = lsqr(curl_apply, curl_applyT, Se, cx.num_triangles());
        out.curl = cx.apply_delta1T(cr.x).cwiseQuotient(w);
    } else {
        out.curl = Eigen::VectorXd::Zero(E);
    }

    out.harm = eta - out.grad - out.curl;

    const auto n2 = [&](const Eigen::VectorXd& x) {
        return (w.array() * x.array() * x.array()).sum();
    };
    out.norm2 = n2(eta);
    out.grad2 = n2(out.grad);
    out.curl2 = n2(out.curl);
    out.harm2 = n2(out.harm);

    // The three pieces are ORTHOGONAL projections, so Pythagoras is a theorem,
    // not a hope. If it fails the decomposition is wrong and every number
    // downstream is meaningless -- refuse rather than report.
    const double residual = std::fabs(out.norm2 - (out.grad2 + out.curl2 + out.harm2));
    const double scale = std::max(out.norm2, 1e-30);
    if (residual / scale > 1e-8) {
        throw std::invalid_argument(
            "Hodge orthogonality violated: ||eta||^2=" + std::to_string(out.norm2) +
            " but grad+curl+harm=" + std::to_string(out.grad2 + out.curl2 + out.harm2) +
            " (rel. err " + std::to_string(residual / scale) + ").");
    }

    // Subspace dimensions. dim(grad) = V - b0 because delta^0's kernel is the
    // locally-constant functions, one per component.
    out.dim_grad = cx.num_vertices() - cx.b0();
    out.dim_curl = 0;
    if (cx.num_triangles() > 0) {
        const Eigen::MatrixXd D1 = cx.dense_delta1_for_rank();
        Eigen::ColPivHouseholderQR<Eigen::MatrixXd> qr(D1);
        qr.setThreshold(1e-10);
        out.dim_curl = static_cast<int>(qr.rank());
    }
    out.dim_harm = E - out.dim_grad - out.dim_curl;
    return out;
}

}  // namespace core
}  // namespace mos
