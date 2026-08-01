#include "mos/core/assembly_log.hpp"

#include "json.hpp"

#include <algorithm>
#include <chrono>
#include <fstream>
#include <stdexcept>

namespace mos {
namespace core {

namespace {

/// Comparator over node INDICES by the canonical key. Python sorts by
/// `nodes[i].key()`, a tuple; NodeRecord::operator< reproduces that ordering.
struct ByKey {
    const std::vector<NodeRecord>& nodes;
    bool operator()(int a, int b) const { return nodes[a] < nodes[b]; }
};

std::string join_support(const std::vector<int>& support) {
    std::string out;
    for (std::size_t i = 0; i < support.size(); ++i) {
        if (i) out += ',';
        out += std::to_string(support[i]);
    }
    return out;
}

double now_seconds() {
    const auto d = std::chrono::system_clock::now().time_since_epoch();
    return std::chrono::duration<double>(d).count();
}

}  // namespace

std::string canonical_signature(const std::vector<NodeRecord>& nodes,
                                const std::vector<std::pair<int, int>>& edges) {
    const int n = static_cast<int>(nodes.size());

    std::map<int, std::vector<int>> children;
    for (int i = 0; i < n; ++i) children[i] = {};
    std::vector<int> indeg(static_cast<std::size_t>(n), 0);

    for (const auto& e : edges) {
        const int p = e.first;
        const int c = e.second;
        if (!(0 <= p && p < n && 0 <= c && c < n)) {
            throw std::invalid_argument(
                "dependency (" + std::to_string(p) + "," + std::to_string(c) +
                ") out of range for " + std::to_string(n) + " nodes");
        }
        children[p].push_back(c);
        indeg[static_cast<std::size_t>(c)] += 1;
    }

    const ByKey by_key{nodes};

    // Python: sorted(i for i in range(n) if indeg[i] == 0). The generator yields
    // in increasing i, and sorted() is stable, so pushing in increasing i and
    // then stable_sort reproduces it exactly.
    std::vector<int> ready;
    for (int i = 0; i < n; ++i) {
        if (indeg[static_cast<std::size_t>(i)] == 0) ready.push_back(i);
    }
    std::stable_sort(ready.begin(), ready.end(), by_key);

    std::vector<int> order;
    order.reserve(static_cast<std::size_t>(n));
    while (!ready.empty()) {
        // Python pops from the FRONT, appends newly-ready children at the BACK,
        // then re-sorts the whole list with a stable sort. Ties therefore keep
        // already-present nodes ahead of newly-appended ones. Replicated here
        // because the resulting index map feeds the edge part of the signature,
        // so a different tie-break is a different signature.
        const int i = ready.front();
        ready.erase(ready.begin());
        order.push_back(i);

        for (const int c : children[i]) {
            if (--indeg[static_cast<std::size_t>(c)] == 0) ready.push_back(c);
        }
        std::stable_sort(ready.begin(), ready.end(), by_key);
    }

    if (static_cast<int>(order.size()) != n) {
        throw std::invalid_argument("composite DAG contains a cycle; refusing to sign it");
    }

    std::map<int, int> pos;
    for (std::size_t k = 0; k < order.size(); ++k) pos[order[k]] = static_cast<int>(k);

    std::string node_part;
    for (std::size_t k = 0; k < order.size(); ++k) {
        if (k) node_part += '|';
        const NodeRecord& nd = nodes[static_cast<std::size_t>(order[k])];
        node_part += nd.op_type;
        node_part += ':';
        node_part += join_support(nd.support);
        node_part += ':';
        node_part += (nd.read_only ? 'r' : 'w');
    }

    std::vector<std::string> edge_strings;
    edge_strings.reserve(edges.size());
    for (const auto& e : edges) {
        edge_strings.push_back(std::to_string(pos[e.first]) + ">" +
                               std::to_string(pos[e.second]));
    }
    // Python `sorted()` on str is lexicographic by code point; std::sort on
    // std::string is lexicographic by char. Identical over ASCII digits and '>'.
    std::sort(edge_strings.begin(), edge_strings.end());

    std::string edge_part;
    for (std::size_t k = 0; k < edge_strings.size(); ++k) {
        if (k) edge_part += ';';
        edge_part += edge_strings[k];
    }

    return node_part + "#" + edge_part;
}

AssemblyLog::AssemblyLog(std::string path) : path_(std::move(path)) {}

int AssemblyLog::record(std::vector<NodeRecord> nodes,
                        std::vector<std::pair<int, int>> edges,
                        std::vector<std::vector<int>> slices,
                        std::uint64_t tick,
                        std::optional<double> rho_before,
                        std::string note) {
    AssemblyEvent ev;
    ev.signature = canonical_signature(nodes, edges);
    ev.nodes = std::move(nodes);
    ev.edges = std::move(edges);
    ev.slices = std::move(slices);
    ev.tick = tick;
    ev.wall_time = now_seconds();
    ev.rho_before = rho_before;
    ev.note = std::move(note);

    const int handle = next_handle_++;
    open_.emplace(handle, std::move(ev));
    return handle;
}

void AssemblyLog::close(int handle,
                        std::optional<double> rho_after,
                        std::optional<std::string> verified,
                        const std::string& extra_note) {
    auto it = open_.find(handle);
    if (it == open_.end()) {
        throw std::invalid_argument("AssemblyLog::close on unknown handle " +
                                    std::to_string(handle));
    }
    AssemblyEvent ev = std::move(it->second);
    open_.erase(it);

    ev.rho_after = rho_after;
    ev.verified = std::move(verified);
    ev.closed = true;
    if (!extra_note.empty()) {
        ev.note = ev.note.empty() ? extra_note : ev.note + "; " + extra_note;
    }
    flush(ev);
}

void AssemblyLog::set_activation(int handle,
                                 std::vector<std::string> retrieved,
                                 std::vector<std::string> grown) {
    auto it = open_.find(handle);
    if (it == open_.end()) {
        throw std::invalid_argument(
            "AssemblyLog::set_activation on unknown handle " +
            std::to_string(handle));
    }
    it->second.retrieved = std::move(retrieved);
    it->second.grown = std::move(grown);
}

void AssemblyLog::abandon(int handle, const std::string& note) {
    auto it = open_.find(handle);
    if (it == open_.end()) {
        throw std::invalid_argument("AssemblyLog::abandon on unknown handle " +
                                    std::to_string(handle));
    }
    AssemblyEvent ev = std::move(it->second);
    open_.erase(it);

    ev.closed = false;  // explicit: the outcome was never learned
    ev.note = ev.note.empty() ? note : ev.note + "; " + note;
    flush(ev);
}

void AssemblyLog::flush(const AssemblyEvent& ev) {
    nlohmann::json j;
    j["signature"] = ev.signature;

    nlohmann::json nodes = nlohmann::json::array();
    for (const auto& n : ev.nodes) {
        nodes.push_back({{"op_type", n.op_type},
                         {"support", n.support},
                         {"read_only", n.read_only}});
    }
    j["nodes"] = std::move(nodes);

    nlohmann::json edges = nlohmann::json::array();
    for (const auto& e : ev.edges) {
        edges.push_back(nlohmann::json::array({e.first, e.second}));
    }
    j["edges"] = std::move(edges);

    j["slices"] = ev.slices;
    j["tick"] = ev.tick;
    j["wall_time"] = ev.wall_time;
    // Always emitted, even when empty. An absent key and an empty list would be
    // indistinguishable to the reader, and "this tick retrieved nothing" is a
    // real observation that a cover model needs -- it is a row of zeros, not a
    // missing row.
    j["retrieved"] = ev.retrieved;
    j["grown"] = ev.grown;

    // Absent measurements serialise as null, never as 0.0.
    j["rho_before"] = ev.rho_before ? nlohmann::json(*ev.rho_before) : nlohmann::json(nullptr);
    j["rho_after"] = ev.rho_after ? nlohmann::json(*ev.rho_after) : nlohmann::json(nullptr);
    j["verified"] = ev.verified ? nlohmann::json(*ev.verified) : nlohmann::json(nullptr);
    j["closed"] = ev.closed;
    j["note"] = ev.note;
    const auto d = ev.delta_rho();
    j["delta_rho"] = d ? nlohmann::json(*d) : nlohmann::json(nullptr);

    std::ofstream out(path_, std::ios::app);
    if (!out) {
        // A failed write is data loss the registry calls unrecoverable, so it is
        // surfaced rather than swallowed. It is not fatal to the tick.
        throw std::runtime_error("AssemblyLog: cannot append to " + path_);
    }
    out << j.dump() << "\n";
}

}  // namespace core
}  // namespace mos
