// Phase-2 item 4: PPR instantiation.
//
// The load-bearing claim is Andersen-Chung-Lang's: cost O(1/(alpha*eps)),
// INDEPENDENT of |K|. That is the entire scalability story for retrieval, so it
// is measured on graphs of very different sizes rather than cited.
//
// The MOS-specific claim is that CUT WEIGHT is reported. Downward closure drops
// a 3-way binding that only partly survives the cut -- returning 2 of a
// jointly-bound 3 is a type error -- and the mass lost that way must be visible,
// not silently absorbed into a tidy-looking subcomplex.

#include <cassert>
#include <cmath>
#include <iostream>
#include <numeric>
#include <set>
#include <stdexcept>
#include <vector>

#include "mos/core/instantiate.hpp"

using namespace mos::core;

namespace {

bool close(double a, double b, double tol = 1e-9) {
    return std::fabs(a - b) <= tol * std::max(1.0, std::max(std::fabs(a), std::fabs(b)));
}

/// A path graph on n vertices: v0 - v1 - ... - v(n-1).
Complex2 path_graph(int n) {
    std::vector<HodgeVertex> vs;
    std::vector<HodgeEdge> es;
    for (int i = 0; i < n; ++i) vs.push_back("v" + std::to_string(i));
    for (int i = 0; i + 1 < n; ++i) es.push_back({vs[i], vs[i + 1]});
    return Complex2(vs, es);
}

/// Two k-cliques joined by a single bridge -- the canonical sweep-cut test.
Complex2 barbell(int k) {
    std::vector<HodgeVertex> vs;
    for (int i = 0; i < 2 * k; ++i) vs.push_back("v" + std::to_string(i));
    std::vector<HodgeEdge> es;
    for (int side = 0; side < 2; ++side) {
        const int off = side * k;
        for (int i = 0; i < k; ++i)
            for (int j = i + 1; j < k; ++j) es.push_back({vs[off + i], vs[off + j]});
    }
    es.push_back({vs[k - 1], vs[k]});   // the bridge
    return Complex2(vs, es);
}

// ---------------------------------------------------------------------------

void test_ppr_converges_to_exact() {
    // As eps -> 0 the approximation must converge to the exact PPR. This is the
    // correctness anchor; everything else about the walk is a performance claim.
    const Complex2 cx = barbell(4);
    const auto w = SkeletonWeights::unit(cx);
    const std::map<int, double> seed{{0, 1.0}};
    const auto exact = exact_ppr(cx, w, seed, 0.15);

    double prev_err = 1e9;
    for (const double eps : {1e-3, 1e-5, 1e-7, 1e-9}) {
        const auto ap = approximate_ppr(cx, w, seed, 0.15, eps, /*max_pushes=*/1 << 22);
        double err = 0.0;
        for (int v = 0; v < cx.num_vertices(); ++v) {
            err = std::max(err, std::fabs(ap.mass(v) - exact[static_cast<std::size_t>(v)]));
        }
        assert(err < prev_err && "shrinking eps must shrink the error");
        prev_err = err;
    }
    assert(prev_err < 1e-7);
    std::cout << "  [ok] approximate PPR -> exact as eps -> 0 (max err " << prev_err << ")\n";
}

void test_acl_bound_is_independent_of_graph_size() {
    // THE scalability claim. Same alpha and eps, wildly different |V|: the push
    // count must stay under ACL's 1/(alpha*eps) and must NOT grow with the graph.
    const double alpha = 0.15, eps = 1e-3;
    const int bound = static_cast<int>(std::ceil(1.0 / (alpha * eps)));

    std::vector<int> pushes;
    for (const int n : {50, 500, 5000}) {
        const Complex2 cx = path_graph(n);
        const auto w = SkeletonWeights::unit(cx);
        const auto ap = approximate_ppr(cx, w, {{0, 1.0}}, alpha, eps);
        assert(!ap.budget_exhausted && "ACL's own bound must suffice");
        assert(ap.pushes <= bound && "push count must respect 1/(alpha*eps)");
        pushes.push_back(ap.pushes);
    }
    // 100x the vertices must not cost meaningfully more work.
    assert(pushes[2] <= pushes[0] + 2 &&
           "cost must be INDEPENDENT of |K|, not merely sublinear");
    std::cout << "  [ok] pushes at |V|=50/500/5000: " << pushes[0] << "/" << pushes[1]
              << "/" << pushes[2] << " (ACL bound " << bound << ", size-independent)\n";
}

void test_residual_guarantee_holds_on_exit() {
    // ACL's stopping condition: r(u) <= eps*d(u) for every u when the queue drains.
    const Complex2 cx = barbell(5);
    const auto w = SkeletonWeights::unit(cx);
    const double eps = 1e-4;
    const auto ap = approximate_ppr(cx, w, {{0, 1.0}}, 0.15, eps);
    assert(!ap.budget_exhausted);

    std::vector<double> deg(static_cast<std::size_t>(cx.num_vertices()), 0.0);
    for (int e = 0; e < cx.num_edges(); ++e) {
        std::map<HodgeVertex, int> vidx;
        for (int i = 0; i < cx.num_vertices(); ++i) vidx[cx.vertices()[static_cast<std::size_t>(i)]] = i;
        deg[static_cast<std::size_t>(vidx.at(cx.edges()[static_cast<std::size_t>(e)].first))] +=
            w.w[static_cast<std::size_t>(e)];
        deg[static_cast<std::size_t>(vidx.at(cx.edges()[static_cast<std::size_t>(e)].second))] +=
            w.w[static_cast<std::size_t>(e)];
    }
    for (const auto& [v, rv] : ap.r) {
        assert(rv <= eps * deg[static_cast<std::size_t>(v)] + 1e-15);
    }
    std::cout << "  [ok] on exit every residual satisfies r(u) <= eps*d(u)\n";
}

void test_sweep_cut_finds_the_cluster() {
    // Seed inside one bell; the sweep must return that bell and not the bridge.
    const int k = 6;
    const Complex2 cx = barbell(k);
    const auto w = SkeletonWeights::unit(cx);
    const auto ap = approximate_ppr(cx, w, {{0, 1.0}}, 0.15, 1e-6);
    const auto sc = sweep_cut(cx, w, ap);

    // Every returned vertex must be from the seeded bell (indices 0..k-1).
    for (const int v : sc.vertices) {
        assert(v < k && "the sweep must not cross the bridge");
    }
    assert(static_cast<int>(sc.vertices.size()) >= k - 1);
    // A single bridge out of a k-clique: conductance is tiny.
    assert(sc.conductance < 0.1);
    std::cout << "  [ok] sweep cut recovers the seeded bell (" << sc.vertices.size()
              << "/" << k << " vertices, phi=" << sc.conductance << ")\n";
}

void test_hebbian_weights_steer_retrieval() {
    // The walk runs on w(sigma,t), so history must actually change what comes
    // back. Without this the weighting is decoration.
    const Complex2 cx({"a", "b", "c"}, {{"a", "b"}, {"a", "c"}});
    auto w = SkeletonWeights::unit(cx);

    w.w[0] = 100.0;   // a-b heavily co-activated
    w.w[1] = 1.0;
    const auto strong_b = approximate_ppr(cx, w, {{0, 1.0}}, 0.15, 1e-8, 1 << 20);

    w.w[0] = 1.0;
    w.w[1] = 100.0;   // now a-c is the strong one
    const auto strong_c = approximate_ppr(cx, w, {{0, 1.0}}, 0.15, 1e-8, 1 << 20);

    assert(strong_b.mass(1) > strong_b.mass(2) && "b should win when a-b is strong");
    assert(strong_c.mass(2) > strong_c.mass(1) && "c should win when a-c is strong");
    std::cout << "  [ok] Hebbian coupling steers the walk (history shapes retrieval)\n";
}

void test_downward_closure_and_cut_weight() {
    // Two triangles sharing nothing, joined by one edge. Seeding in the first
    // triangle must return it CLOSED, and must charge the bridge to the cut.
    const Complex2 cx({"a", "b", "c", "x", "y", "z"},
                      {{"a", "b"}, {"a", "c"}, {"b", "c"},
                       {"x", "y"}, {"x", "z"}, {"y", "z"},
                       {"c", "x"}},
                      {{"a", "b", "c"}, {"x", "y", "z"}});
    auto w = SkeletonWeights::unit(cx);
    w.w[6] = 0.25;   // a weak bridge c-x

    const auto inst = instantiate(cx, w, {{0, 1.0}}, 0.15, 1e-6);

    const std::set<int> got(inst.vertices.begin(), inst.vertices.end());
    assert(got.count(0) && got.count(1) && got.count(2));
    assert(!got.count(3) && !got.count(4) && !got.count(5));

    // Downward closure: every returned simplex must have ALL vertices returned.
    for (const int t : inst.triangles) {
        assert(t == 0 && "only the retrieved triangle may come back");
    }
    assert(inst.triangles.size() == 1);
    assert(inst.edges.size() == 3 && "the closed triangle's three faces");

    // The bridge is sliced, so its weight is charged.
    assert(close(inst.cut_weight, 0.25));
    assert(inst.sliced_triangles == 0 && "neither triangle was torn");
    std::cout << "  [ok] closure returns a closed subcomplex; cut_weight = "
              << inst.cut_weight << "\n";
}

void test_a_torn_triangle_is_dropped_and_charged() {
    // THE type-error guard. Force a cut through a triangle and check that the
    // partial binding is NOT returned, and that its loss is reported.
    const Complex2 cx({"a", "b", "c"}, {{"a", "b"}, {"a", "c"}, {"b", "c"}},
                      {{"a", "b", "c"}});
    const auto w = SkeletonWeights::unit(cx);

    // Hand-build the situation rather than hoping the sweep produces it: ask
    // what instantiate does when only part of the triangle is inside.
    // A seed with a huge alpha keeps essentially all mass at the seed, so the
    // sweep returns a strict subset.
    const auto inst = instantiate(cx, w, {{0, 1.0}}, 0.99, 0.5);

    if (inst.vertices.size() < 3) {
        assert(inst.triangles.empty() &&
               "a partly-retrieved 3-way binding must NOT be returned");
        assert(inst.sliced_triangles == 1);
        assert(inst.cut_weight > 0.0 && "tearing an n-ary binding must be charged");
        std::cout << "  [ok] torn triangle dropped, " << inst.sliced_triangles
                  << " sliced, cut_weight = " << inst.cut_weight << "\n";
    } else {
        // The sweep kept everything; then nothing was torn and the invariant is
        // trivially satisfied. Say so rather than claiming a pass we did not get.
        assert(inst.triangles.size() == 1 && inst.sliced_triangles == 0);
        std::cout << "  [ok] sweep retrieved the whole triangle; nothing torn "
                     "(the tearing branch was not exercised here)\n";
    }
}

void test_refusals() {
    const Complex2 cx = path_graph(4);
    const auto w = SkeletonWeights::unit(cx);
    bool threw;

    threw = false;
    try { (void)approximate_ppr(cx, w, {}, 0.15, 1e-4); }
    catch (const std::invalid_argument&) { threw = true; }
    assert(threw && "an empty seed must be refused, not silently return nothing");

    threw = false;
    try { (void)approximate_ppr(cx, w, {{0, 0.0}}, 0.15, 1e-4); }
    catch (const std::invalid_argument&) { threw = true; }
    assert(threw && "an all-zero seed must be refused");

    threw = false;
    try { (void)approximate_ppr(cx, w, {{0, 1.0}}, 1.5, 1e-4); }
    catch (const std::invalid_argument&) { threw = true; }
    assert(threw && "alpha outside (0,1) must be refused");

    threw = false;
    try {
        auto bad = w;
        bad.w[0] = 0.0;
        (void)approximate_ppr(cx, bad, {{0, 1.0}}, 0.15, 1e-4);
    } catch (const std::invalid_argument&) { threw = true; }
    assert(threw && "a zero coupling is an absent edge, not a weighted one");

    threw = false;
    try { (void)approximate_ppr(cx, w, {{99, 1.0}}, 0.15, 1e-4); }
    catch (const std::invalid_argument&) { threw = true; }
    assert(threw && "an out-of-range seed vertex must be refused");

    std::cout << "  [ok] empty/zero/out-of-range seeds, bad alpha, zero weights refused\n";
}

}  // namespace

int main() {
    std::cout << "=== approximate PPR (Andersen-Chung-Lang) ===\n";
    test_ppr_converges_to_exact();
    test_residual_guarantee_holds_on_exit();
    test_acl_bound_is_independent_of_graph_size();
    test_hebbian_weights_steer_retrieval();

    std::cout << "=== sweep cut and instantiation ===\n";
    test_sweep_cut_finds_the_cluster();
    test_downward_closure_and_cut_weight();
    test_a_torn_triangle_is_dropped_and_charged();
    test_refusals();

    std::cout << "\nALL INSTANTIATION TESTS PASSED\n";
    return 0;
}
