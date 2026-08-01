#pragma once

// PHASE-2 ITEM 2 — the Hodge split, solved by LSQR rather than a pseudo-inverse.
//
// WHY LSQR (5s budget finding 2). With IDENTITY restriction maps delta^0
// factors as delta_K (x) I_d and the split is 21x7 scalar work -- free. With
// REAL maps it does not factor, and a pseudo-inverse of the resulting
// 8064 x 2688 operator is ~10^11 flops: minutes per tick. LSQR needs ~50
// matrix-vector products, ~1.3x10^7 flops, milliseconds. So this file never
// forms delta^0, delta^1, or any inverse -- it applies them.
//
// WHAT THE SPLIT MEANS (python/hodge.py, authoritative):
//   gradient : eta is explained by a per-organ potential. Everyone is
//              consistently offset; there is no disagreement to repair.
//   curl     : inconsistency around a FILLED triangle. Local repair.
//   harmonic : inconsistency around an UNFILLED cycle that no potential and no
//              face can explain. THIS is the growth address -- the hole.
//
// Pythagoras is a THEOREM here, not a hope: the three pieces are orthogonal
// projections in the pi-weighted inner product, so
// ||eta||^2 = ||grad||^2 + ||curl||^2 + ||harm||^2 exactly. `hodge_split`
// REFUSES to return if that fails, because every number downstream of a broken
// decomposition is meaningless.

#include <Eigen/Dense>
#include <functional>
#include <map>
#include <optional>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

namespace mos {
namespace core {

using HodgeVertex = std::string;
using HodgeEdge = std::pair<HodgeVertex, HodgeVertex>;
using HodgeTriangle = std::tuple<HodgeVertex, HodgeVertex, HodgeVertex>;

/// @brief An oriented 2-dimensional simplicial complex.
///
/// Downward closure is ENFORCED, not assumed: a triangle whose faces are not all
/// present is not a simplex, and silently inserting the missing edges would
/// change b1 -- the very number the harmonic part is meant to expose -- behind
/// the caller's back.
class Complex2 {
public:
    Complex2(std::vector<HodgeVertex> vertices,
             const std::vector<HodgeEdge>& edges,
             const std::vector<HodgeTriangle>& triangles = {});

    [[nodiscard]] int num_vertices() const noexcept { return static_cast<int>(vertices_.size()); }
    [[nodiscard]] int num_edges() const noexcept { return static_cast<int>(edges_.size()); }
    [[nodiscard]] int num_triangles() const noexcept { return static_cast<int>(triangles_.size()); }

    [[nodiscard]] const std::vector<HodgeVertex>& vertices() const noexcept { return vertices_; }
    [[nodiscard]] const std::vector<HodgeEdge>& edges() const noexcept { return edges_; }
    [[nodiscard]] const std::vector<HodgeTriangle>& triangles() const noexcept { return triangles_; }

    /// @brief (row index, +1 if (u,v) matches the stored orientation else -1).
    [[nodiscard]] std::pair<int, double> edge_index(const HodgeVertex& u,
                                                    const HodgeVertex& v) const;

    // --- matrix-free coboundaries ------------------------------------------
    // (delta^0 f)_(u,v) = f(v) - f(u)
    [[nodiscard]] Eigen::VectorXd apply_delta0(const Eigen::VectorXd& f) const;
    [[nodiscard]] Eigen::VectorXd apply_delta0T(const Eigen::VectorXd& x) const;
    // (delta^1 eta)_(a,b,c) = eta_(b,c) - eta_(a,c) + eta_(a,b)
    [[nodiscard]] Eigen::VectorXd apply_delta1(const Eigen::VectorXd& x) const;
    [[nodiscard]] Eigen::VectorXd apply_delta1T(const Eigen::VectorXd& y) const;

    /// @brief Connected components of the 1-skeleton. b0 > 1 means the split's
    /// gradient dimension is V - b0, not V - 1.
    [[nodiscard]] int b0() const;

    /// @brief Dense delta^1, FOR RANK COUNTING ONLY. This is F x E with F the
    /// triangle count, which is small; it is not the operator LSQR applies and
    /// it is never inverted.
    [[nodiscard]] Eigen::MatrixXd dense_delta1_for_rank() const;

private:
    [[nodiscard]] HodgeEdge canon_edge(const HodgeVertex& u, const HodgeVertex& v) const;

    std::vector<HodgeVertex> vertices_;
    std::map<HodgeVertex, int> vidx_;
    std::vector<HodgeEdge> edges_;
    std::map<HodgeEdge, int> eidx_;
    std::vector<HodgeTriangle> triangles_;
};

/// @brief Matrix-free LSQR (Paige & Saunders 1982) for min ||A x - b||_2.
///
/// A is supplied only through its action: `apply(x) = A x` and
/// `apply_transpose(y) = A^T y`. Started from x = 0, LSQR converges to the
/// MINIMUM-NORM least-squares solution, which is what numpy's lstsq returns and
/// therefore what the Python parity target assumes.
struct LsqrResult {
    Eigen::VectorXd x;
    int iterations = 0;
    double residual_norm = 0.0;   ///< ||b - A x||
    double atr_norm = 0.0;        ///< ||A^T (b - A x)||, the optimality residual
    bool converged = false;
};

LsqrResult lsqr(const std::function<Eigen::VectorXd(const Eigen::VectorXd&)>& apply,
                const std::function<Eigen::VectorXd(const Eigen::VectorXd&)>& apply_transpose,
                const Eigen::VectorXd& b,
                int n,
                double tol = 1e-14,
                int max_iter = 0);

/// @brief The result of splitting a 1-cochain.
struct HodgeSplit {
    Eigen::VectorXd grad, curl, harm;
    double norm2 = 0.0, grad2 = 0.0, curl2 = 0.0, harm2 = 0.0;
    int dim_grad = 0, dim_curl = 0, dim_harm = 0;
    Eigen::VectorXd potential;   ///< the mean-zero f with grad = delta^0 f

    /// @brief Energy fractions (grad, curl, harm), summing to 1.
    [[nodiscard]] std::tuple<double, double, double> fractions() const;

    /// @brief harm2 + curl2 -- the non-gradient mass. The run sheet's quantity.
    [[nodiscard]] double non_gradient() const noexcept { return harm2 + curl2; }

    /// @brief Expected (grad, curl, harm) fractions for ISOTROPIC eta, i.e. what
    /// a COMPLETELY RANDOM instrument scores. In the E5 configuration this is
    /// (0.60, 0.20, 0.20), so harm+curl = 0.40 is the number to beat -- NOT 0.
    [[nodiscard]] std::tuple<double, double, double> null_fractions() const;

    /// @brief (non-gradient fraction) - (its null value). Positive means more
    /// non-gradient structure than noise alone would give.
    [[nodiscard]] double excess_non_gradient() const;

    /// @brief Edges carrying the most harmonic mass -- THE GROWTH ADDRESS.
    /// Meaningful only when harm2 is materially above the null.
    [[nodiscard]] std::vector<std::pair<HodgeEdge, double>> harmonic_support(
        const Complex2& cx, int top = 3) const;
};

/// @brief Split a measured 1-cochain into gradient + curl + harmonic.
///
/// @param eta       one value per edge, in `cx.edges()` order, SIGNED with the
///                  stored orientation (u -> v).
/// @param precision optional pi_e > 0 per edge. Supplying a partial map is an
///                  ERROR, not an invitation to default: a missing weight is a
///                  missing measurement, not a weight of 1.
///
/// @throws std::invalid_argument on a shape mismatch, a missing or non-positive
///         precision, or -- critically -- if the returned pieces fail Pythagoras.
[[nodiscard]] HodgeSplit hodge_split(
    const Complex2& cx,
    const Eigen::VectorXd& eta,
    const std::optional<std::map<HodgeEdge, double>>& precision = std::nullopt);

}  // namespace core
}  // namespace mos
