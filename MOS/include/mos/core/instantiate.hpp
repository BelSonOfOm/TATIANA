#pragma once

// PHASE-2 ITEM 4 — instantiation: pull a working subcomplex W out of the store K.
//
// THE PIPELINE (logbook 5s, gap (a)):
//   seed by embedding (LAST, not first)
//     -> approximate Personalized PageRank on the WEIGHTED 1-skeleton
//     -> sweep cut
//     -> downward closure
//     -> report CUT WEIGHT
//
// WHY PPR AND NOT k-NN. Andersen-Chung-Lang 2006 gives a local partitioning
// whose cost is O(1/(alpha*eps)) -- INDEPENDENT of |K|. That independence is the
// entire scalability claim for retrieval: the store can grow without retrieval
// getting slower. It is asserted in the tests, not assumed.
//
// WHY THE WEIGHTS MATTER. The walk runs on w(sigma,t), the Hebbian coupling, so
// what was co-activated in the past shapes what is retrieved now. Note this is
// the ONE place w(sigma,t) is the right weight -- it is a coupling strength here,
// not a precision. (Using it as pi_e was the 5af type error; see edge_precision.)
//
// WHY CUT WEIGHT IS REPORTED, NOT HIDDEN. Downward closure keeps a simplex only
// when ALL its vertices are retrieved. A 3-way binding with 2 vertices inside the
// cut is DROPPED, and returning 2 of a jointly-bound 3 would be a type error --
// so the mass lost that way is reported as a first-class number. A large cut
// weight means the retrieved complex is a torn piece of a larger structure, and
// the caller is entitled to know that rather than to receive a tidy-looking
// subcomplex that quietly lost its bindings.
//
// SCOPE, STATED: cluster on the 1-SKELETON. Higher-order simplicial Cheeger
// inequalities are much weaker and have known counterexamples, so conductance
// here is a diagnostic about the graph, never quoted as a bound on the complex.

#include <map>
#include <string>
#include <vector>

#include "mos/core/hodge.hpp"

namespace mos {
namespace core {

/// @brief A weighted 1-skeleton over a Complex2's vertices and edges.
/// Weights are w(sigma,t), the Hebbian coupling -- strictly positive.
struct SkeletonWeights {
    std::vector<double> w;   ///< one per edge, in cx.edges() order

    [[nodiscard]] static SkeletonWeights unit(const Complex2& cx);
};

/// @brief The result of an approximate Personalized PageRank run.
struct PPRResult {
    std::map<int, double> p;   ///< sparse rank vector, vertex index -> mass
    std::map<int, double> r;   ///< the residual left when the push queue drained
    int pushes = 0;            ///< push operations performed; ACL bounds this
    bool budget_exhausted = false;

    [[nodiscard]] double mass(int v) const;
};

/// @brief Approximate PPR by the Andersen-Chung-Lang push procedure.
///
/// Maintains (p, r) with p = 0, r = seed, and repeatedly pushes any vertex whose
/// residual exceeds eps * degree. On return every vertex satisfies
/// r(u) <= eps * d(u), which is the ACL stopping guarantee.
///
/// @param seeds   seed mass per vertex index. Normalised to sum 1 internally;
///                an empty or all-zero seed is an error, not an empty answer.
/// @param alpha   teleport probability in (0,1).
/// @param eps     residual tolerance in (0,1].
/// @param max_pushes 0 => use the ACL bound ceil(1/(alpha*eps)) + slack.
///
/// @throws std::invalid_argument on a bad parameter, a non-positive weight, or
///         an empty seed.
[[nodiscard]] PPRResult approximate_ppr(const Complex2& cx,
                                        const SkeletonWeights& weights,
                                        const std::map<int, double>& seeds,
                                        double alpha = 0.15,
                                        double eps = 1e-4,
                                        int max_pushes = 0);

/// @brief Exact PPR by a dense solve. REFERENCE ONLY -- O(V^3), used to check
/// the approximation. Never call this on the real store; that is the entire
/// reason approximate_ppr exists.
[[nodiscard]] std::vector<double> exact_ppr(const Complex2& cx,
                                            const SkeletonWeights& weights,
                                            const std::map<int, double>& seeds,
                                            double alpha = 0.15);

/// @brief The best prefix of the degree-normalised PPR ordering.
struct SweepCut {
    std::vector<int> vertices;   ///< the chosen set, in sweep order
    double conductance = 1.0;    ///< phi(S) = cut(S) / min(vol S, vol complement)
    double volume = 0.0;
    double cut = 0.0;
};

/// @brief Sweep cut: order vertices by p(u)/d(u) descending, and take the prefix
/// of least conductance. Only vertices with p > 0 are candidates.
[[nodiscard]] SweepCut sweep_cut(const Complex2& cx,
                                 const SkeletonWeights& weights,
                                 const PPRResult& ppr);

/// @brief The instantiated working subcomplex, plus what it cost to cut it out.
struct Instantiation {
    std::vector<int> vertices;
    std::vector<int> edges;        ///< indices into cx.edges()
    std::vector<int> triangles;    ///< indices into cx.triangles()

    double conductance = 1.0;

    /// @brief Total coupling weight on simplices SLICED by the cut -- edges with
    /// exactly one endpoint inside, and triangles with one or two vertices
    /// inside. NOT a diagnostic to skip: a jointly-bound k-simplex returned with
    /// k-1 of its vertices would be a type error, so those bindings are dropped,
    /// and this is the mass that was dropped.
    double cut_weight = 0.0;

    /// @brief How many higher simplices (triangles) were torn. Reported
    /// separately because losing an n-ary binding is qualitatively worse than
    /// losing a pairwise one.
    int sliced_triangles = 0;
};

/// @brief The full pipeline: PPR -> sweep cut -> downward closure -> cut weight.
///
/// Seeds are supplied by the caller because seeding is by EMBEDDING and that
/// happens LAST in the design order, not first: the graph structure decides the
/// neighbourhood, the embedding only decides where to start looking.
[[nodiscard]] Instantiation instantiate(const Complex2& cx,
                                        const SkeletonWeights& weights,
                                        const std::map<int, double>& seeds,
                                        double alpha = 0.15,
                                        double eps = 1e-4);

}  // namespace core
}  // namespace mos
