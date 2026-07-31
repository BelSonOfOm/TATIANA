#include "mos/core/edge_precision.hpp"

#include <cmath>
#include <stdexcept>

namespace mos {
namespace core {

double report_variance(std::optional<double> confidence, int d) {
    if (d <= 0) {
        throw std::invalid_argument("embedding dimension must be positive, got " +
                                    std::to_string(d));
    }
    if (!confidence.has_value()) return 0.0;
    const double c = *confidence;
    if (!(c > 0.0 && c <= 1.0)) {
        throw std::invalid_argument(
            "confidence " + std::to_string(c) +
            " outside (0, 1]. Zero confidence is not a measurement and >1 is a "
            "caller bug; refusing to clamp.");
    }
    return -std::log(c) / static_cast<double>(d);
}

std::map<CoarseEdge, double> edge_precision(
    const std::vector<CoarseEdge>& edges,
    const std::map<ModuleId, double>& stalk_floor,
    int d,
    const std::map<CoarseEdge, double>& confidence) {
    std::map<CoarseEdge, double> out;

    for (const auto& e : edges) {
        for (const ModuleId& endpoint : {e.first, e.second}) {
            if (stalk_floor.find(endpoint) == stalk_floor.end()) {
                throw std::invalid_argument(
                    "No stalk floor for organ '" + endpoint + "' on edge (" +
                    e.first + ", " + e.second +
                    "). Refusing to default silently -- a missing floor is a "
                    "missing measurement, not a floor of 1.");
            }
        }
        const double D_u = stalk_floor.at(e.first);
        const double D_v = stalk_floor.at(e.second);
        if (D_u <= 0.0 || D_v <= 0.0) {
            throw std::invalid_argument(
                "Stalk floors must be strictly positive; got D[" + e.first +
                "]=" + std::to_string(D_u) + ", D[" + e.second +
                "]=" + std::to_string(D_v) + ". A zero floor is infinite precision.");
        }

        // Look the confidence up under either orientation, as the Python does.
        std::optional<double> c;
        auto it = confidence.find(e);
        if (it == confidence.end()) it = confidence.find({e.second, e.first});
        if (it != confidence.end()) c = it->second;

        const double total = D_u + D_v + report_variance(c, d);
        if (total < MIN_TOTAL_VARIANCE) {
            throw std::invalid_argument(
                "Edge (" + e.first + ", " + e.second + ") has total error variance " +
                std::to_string(total) +
                ", which would give an effectively infinite precision. Check the "
                "stalk floors -- they should be O(1/d), not O(1/d^2).");
        }
        out[e] = 1.0 / total;
    }
    return out;
}

bool is_uniform(const std::map<CoarseEdge, double>& pi, double rel_tol) {
    if (pi.size() <= 1) return true;
    const double first = pi.begin()->second;
    for (const auto& kv : pi) {
        const double scale = std::max(1.0, std::max(std::fabs(first), std::fabs(kv.second)));
        if (std::fabs(kv.second - first) > rel_tol * scale) return false;
    }
    return true;
}

}  // namespace core
}  // namespace mos
