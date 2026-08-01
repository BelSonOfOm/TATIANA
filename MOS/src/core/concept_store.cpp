#include "mos/core/concept_store.hpp"

#include <algorithm>
#include <stdexcept>
#include <utility>

namespace mos {
namespace core {

namespace {

/// Edges are undirected, so (u,v) and (v,u) must be ONE key. Sorting the pair
/// makes that structural instead of a convention every call site has to
/// remember -- and a forgotten one would create a parallel edge with its own
/// restriction map, silently halving the evidence behind both.
HodgeEdge canonical(const std::string& a, const std::string& b) {
    return (a < b) ? HodgeEdge{a, b} : HodgeEdge{b, a};
}

constexpr double kNormFloor = 1e-12;

}  // namespace

HouseholderMap align_map(const Eigen::VectorXd& from, const Eigen::VectorXd& to) {
    if (from.size() != to.size()) {
        throw std::invalid_argument(
            "align_map: dimension mismatch (" + std::to_string(from.size()) +
            " vs " + std::to_string(to.size()) + "). Refusing to pad or truncate.");
    }
    const int d = static_cast<int>(from.size());
    if (d <= 0) throw std::invalid_argument("align_map: empty vectors.");

    const double nf = from.norm(), nt = to.norm();
    if (nf < kNormFloor || nt < kNormFloor) {
        throw std::invalid_argument(
            "align_map: a vector too small to normalise has no direction to "
            "align. Treating it as the identity would hide the caller's bug.");
    }

    const Eigen::VectorXd a = from / nf;
    const Eigen::VectorXd b = to / nt;

    // Already aligned: nothing was learned on this edge, and the identity says
    // exactly that. Returning a spurious rotation would make Q(t) rise on edges
    // where the two stalks already agreed.
    const Eigen::VectorXd diff = a - b;
    if (diff.norm() < kNormFloor) {
        return HouseholderMap::identity(d);
    }

    // ANTIPODAL CASE. a = -b makes span{a,b} one-dimensional, so "orthogonal to
    // the span" is underdetermined and the generic construction below would pick
    // a direction by accident. Handled explicitly: any p perpendicular to a
    // gives H_p H_w with H_w = -reflection through a. Rather than reason about
    // which, note that a rotation by pi in ANY plane containing a maps a to -a,
    // so pick an arbitrary unit q perpendicular to a and rotate in span{a,q}.
    const double cos_ab = a.dot(b);
    Eigen::VectorXd w = diff.normalized();
    Eigen::VectorXd p;

    if (cos_ab < -1.0 + 1e-9) {
        if (d < 2) {
            throw std::invalid_argument(
                "align_map: cannot rotate a 1-dimensional vector onto its "
                "negation with an even number of reflections -- no such map "
                "exists in O(1). Refusing rather than returning a near-miss.");
        }
        // Build q perpendicular to a by removing a's component from the
        // coordinate axis least parallel to it, which is numerically safest.
        int axis = 0;
        for (int i = 1; i < d; ++i) {
            if (std::abs(a(i)) < std::abs(a(axis))) axis = i;
        }
        Eigen::VectorXd e = Eigen::VectorXd::Zero(d);
        e(axis) = 1.0;
        Eigen::VectorXd q = e - a.dot(e) * a;
        q.normalize();
        // A pi-rotation in span{a,q} is H_q H_a: reflect through a, then q.
        return HouseholderMap(d, {q, a});
    }

    // GENERIC CASE. H_w carries a to b. p is any unit vector orthogonal to
    // span{a,b}, so H_p fixes b and R = H_p H_w still sends a to b -- with
    // det = +1, which is the whole point.
    if (d >= 3) {
        int axis = 0;
        double best = 2.0;
        for (int i = 0; i < d; ++i) {
            const double load = std::abs(a(i)) + std::abs(b(i));
            if (load < best) { best = load; axis = i; }
        }
        Eigen::VectorXd e = Eigen::VectorXd::Zero(d);
        e(axis) = 1.0;
        p = e - e.dot(a) * a;
        const Eigen::VectorXd b_perp = (b - b.dot(a) * a).normalized();
        p -= p.dot(b_perp) * b_perp;          // now orthogonal to span{a,b}
        if (p.norm() < kNormFloor) {
            // The chosen axis lay inside span{a,b}; fall back to a search.
            for (int i = 0; i < d && p.norm() < kNormFloor; ++i) {
                Eigen::VectorXd f = Eigen::VectorXd::Zero(d);
                f(i) = 1.0;
                p = f - f.dot(a) * a;
                p -= p.dot(b_perp) * b_perp;
            }
        }
        p.normalize();
        return HouseholderMap(d, {p, w});
    }

    // d == 2: span{a,b} is the whole space, so no p exists outside it. The
    // rotation taking a to b is still a product of two reflections -- through a
    // itself, then through the bisector.
    return HouseholderMap(d, {w, a});
}

// ---------------------------------------------------------------------------

ConceptStore::ConceptStore(int d) : d_(d) {
    if (d <= 0) {
        throw std::invalid_argument("ConceptStore: embedding dimension must be positive.");
    }
}

void ConceptStore::observe(const std::vector<std::string>& coactive) {
    // Deduplicate without disturbing order: a repeated name in one tick is one
    // concept, and pairing it with itself would create a self-loop that
    // Complex2's downward closure has no meaning for.
    std::vector<std::string> uniq;
    uniq.reserve(coactive.size());
    for (const auto& c : coactive) {
        if (c.empty()) continue;
        if (std::find(uniq.begin(), uniq.end(), c) == uniq.end()) uniq.push_back(c);
    }

    for (const auto& c : uniq) {
        if (vertices_.insert(c).second) {
            order_.push_back(c);
            dirty_ = true;
        }
    }

    for (std::size_t i = 0; i < uniq.size(); ++i) {
        for (std::size_t j = i + 1; j < uniq.size(); ++j) {
            const HodgeEdge e = canonical(uniq[i], uniq[j]);
            if (coactivation_.find(e) == coactivation_.end()) dirty_ = true;
            ++coactivation_[e];
        }
    }
}

int ConceptStore::coactivation_count(const std::string& u,
                                     const std::string& v) const {
    auto it = coactivation_.find(canonical(u, v));
    return (it == coactivation_.end()) ? 0 : it->second;
}

Store& ConceptStore::store() {
    if (!dirty_ && store_) return *store_;

    // Carry the learned sheaf across the rebuild. Keys are (name, name), so a
    // map learned before the store grew still refers to the same edge -- this
    // is the reason vertices are names and not indices.
    std::map<HodgeEdge, HouseholderMap> kept_restriction;
    std::map<HodgeEdge, double> kept_coupling;
    if (store_) {
        kept_restriction = std::move(store_->restriction);
        kept_coupling = std::move(store_->coupling);
    }

    std::vector<HodgeVertex> vs(order_.begin(), order_.end());
    std::vector<HodgeEdge> es;
    es.reserve(coactivation_.size());
    for (const auto& [e, count] : coactivation_) es.push_back(e);

    Store rebuilt(Complex2(std::move(vs), es), d_);

    for (const auto& e : es) {
        auto old = kept_restriction.find(e);
        // A NEW edge starts at the identity, which is the honest prior: nothing
        // has been learned about how meaning transports along it yet. Q(t) = 0
        // is exactly "the constant sheaf", so a new edge contributes nothing to
        // Q until a session actually moves it.
        //
        // insert_or_assign, NOT emplace. Store's constructor has ALREADY filled
        // every edge with an identity, and emplace on an existing key does
        // nothing at all -- so the carried-over learned maps were silently
        // dropped and every rebuild reset the store to the constant sheaf.
        // Nothing threw; Q simply returned to zero whenever a concept was added.
        rebuilt.restriction.insert_or_assign(
            e, old != kept_restriction.end() ? old->second
                                             : HouseholderMap::identity(d_));
        auto oldw = kept_coupling.find(e);
        // The coupling is DERIVED from how often the pair co-activated, not
        // remembered separately, so it cannot drift out of step with the
        // evidence. w(sigma,t) is capped at 1 -- it is not pi_e, and conflating
        // the two already caused one divergence bug (logbook 5q).
        const double derived = static_cast<double>(coactivation_.at(e));
        rebuilt.coupling[e] = oldw != kept_coupling.end()
                                  ? std::max(oldw->second, std::min(1.0, derived / 10.0))
                                  : std::min(1.0, derived / 10.0);
    }

    store_ = std::move(rebuilt);
    dirty_ = false;
    return *store_;
}

}  // namespace core
}  // namespace mos
