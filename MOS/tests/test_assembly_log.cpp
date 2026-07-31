// E7 assembly recording (engine level).
//
// THE POINT OF THIS FILE. `canonical_signature` is the key the recurrence
// analysis groups on. If the C++ and Python implementations disagree about the
// signature of the same composite, every recurrence count is wrong and NOTHING
// fails — the counts just quietly split across two keys. So the cases below are
// duplicated verbatim in `python/check_signature_parity.py`, with the SAME
// expected strings hard-coded on both sides. Change one, and the other fails.
//
// The expected strings were derived from the Python implementation, which is
// authoritative: it existed first and the analysis functions were written
// against it.

#include <algorithm>
#include <cassert>
#include <cstdio>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#include "json.hpp"
#include "operad_generated.h"
#include "mos/core/assembly_log.hpp"
#include "mos/core/cognitive_state.hpp"
#include "mos/core/kernel.hpp"

using namespace mos;
using core::AssemblyLog;
using core::NodeRecord;
using core::canonical_signature;

namespace {

NodeRecord nr(const std::string& op_type, std::vector<int> support, bool read_only) {
    NodeRecord r;
    r.op_type = op_type;
    r.support = std::move(support);
    r.read_only = read_only;
    return r;
}

void expect_signature(const std::string& label,
                      const std::vector<NodeRecord>& nodes,
                      const std::vector<std::pair<int, int>>& edges,
                      const std::string& expected) {
    const std::string got = canonical_signature(nodes, edges);
    if (got != expected) {
        std::cerr << "  [FAIL] " << label << "\n    expected: " << expected
                  << "\n    got:      " << got << "\n";
        assert(false);
    }
    std::cout << "  [ok] " << label << " -> " << got << "\n";
}

// ---------------------------------------------------------------------------
// canonical_signature — shared with python/check_signature_parity.py
// ---------------------------------------------------------------------------

void test_single_node() {
    expect_signature("single read-only global node",
                     {nr("SEARCH", {}, true)}, {}, "SEARCH::r#");
}

void test_chain() {
    expect_signature("COMPUTE -> VERIFY",
                     {nr("COMPUTE", {1, 2}, false), nr("VERIFY", {}, true)},
                     {{0, 1}},
                     "COMPUTE:1,2:w|VERIFY::r#0>1");
}

void test_order_independence() {
    // THE property the signature exists for: the same composite presented with
    // its nodes in a different order must sign identically, or recurrence
    // counting splits one generator into several.
    const std::string a = canonical_signature(
        {nr("COMPUTE", {1, 2}, false), nr("VERIFY", {}, true)}, {{0, 1}});
    const std::string b = canonical_signature(
        {nr("VERIFY", {}, true), nr("COMPUTE", {1, 2}, false)}, {{1, 0}});
    assert(a == b);
    assert(a == "COMPUTE:1,2:w|VERIFY::r#0>1");
    std::cout << "  [ok] node order does not change the signature\n";
}

void test_tie_break_is_by_key_not_index() {
    // Two independent nodes: canonical order is by (op_type, support,
    // read_only), so COMPUTE sorts ahead of SEARCH regardless of input order.
    expect_signature("independent nodes sort by key",
                     {nr("SEARCH", {}, true), nr("COMPUTE", {}, true)}, {},
                     "COMPUTE::r|SEARCH::r#");
}

void test_edge_sort_is_lexicographic() {
    // Python sorts the edge strings, not the index pairs, so "0>10" precedes
    // "0>2". Getting this wrong only shows up once a composite has >10 nodes,
    // which is exactly when nobody is looking.
    std::vector<NodeRecord> nodes;
    for (int i = 0; i < 11; ++i) {
        char buf[8];
        std::snprintf(buf, sizeof(buf), "A%02d", i);
        nodes.push_back(nr(buf, {}, true));
    }
    std::string expected;
    for (int i = 0; i < 11; ++i) {
        char buf[8];
        std::snprintf(buf, sizeof(buf), "A%02d", i);
        if (i) expected += "|";
        expected += std::string(buf) + "::r";
    }
    expected += "#0>10;0>2";
    expect_signature("edge strings sort lexicographically", nodes, {{0, 2}, {0, 10}},
                     expected);
}

void test_cycle_is_refused() {
    bool threw = false;
    try {
        (void)canonical_signature({nr("A", {}, true), nr("B", {}, true)},
                                  {{0, 1}, {1, 0}});
    } catch (const std::invalid_argument&) {
        threw = true;
    }
    assert(threw);
    std::cout << "  [ok] a cyclic composite is refused, not serialised around\n";
}

void test_out_of_range_edge_is_refused() {
    bool threw = false;
    try {
        (void)canonical_signature({nr("A", {}, true)}, {{0, 5}});
    } catch (const std::invalid_argument&) {
        threw = true;
    }
    assert(threw);
    std::cout << "  [ok] an out-of-range dependency is refused\n";
}

// ---------------------------------------------------------------------------
// AssemblyLog round-trip
// ---------------------------------------------------------------------------

std::string temp_path(const char* name) {
    return std::string("assembly_test_") + name + ".jsonl";
}

std::vector<nlohmann::json> read_lines(const std::string& path) {
    std::vector<nlohmann::json> out;
    std::ifstream in(path);
    std::string line;
    while (std::getline(in, line)) {
        if (!line.empty()) out.push_back(nlohmann::json::parse(line));
    }
    return out;
}

void test_close_writes_one_line_with_delta_rho() {
    const std::string path = temp_path("close");
    std::remove(path.c_str());
    {
        AssemblyLog log(path);
        const int h = log.record({nr("COMPUTE", {1}, false), nr("VERIFY", {}, true)},
                                 {{0, 1}}, {{0}, {1}}, /*tick=*/7, /*rho_before=*/0.40);
        assert(log.open_count() == 1);
        log.close(h, /*rho_after=*/0.25);
        assert(log.open_count() == 0);
    }
    const auto lines = read_lines(path);
    assert(lines.size() == 1);
    const auto& j = lines[0];
    assert(j["tick"] == 7);
    assert(j["closed"] == true);
    assert(j["signature"] == "COMPUTE:1:w|VERIFY::r#0>1");
    assert(j["nodes"].size() == 2);
    assert(j["nodes"][0]["op_type"] == "COMPUTE");
    assert(j["nodes"][0]["support"][0] == 1);
    assert(j["nodes"][0]["read_only"] == false);
    assert(j["edges"][0][0] == 0 && j["edges"][0][1] == 1);
    assert(j["slices"].size() == 2);
    assert(j["verified"].is_null());  // never inferred from rho
    const double d = j["delta_rho"].get<double>();
    assert(d < -0.149 && d > -0.151);
    std::cout << "  [ok] close() writes one line, delta_rho = " << d << "\n";
    std::remove(path.c_str());
}

void test_missing_rho_stays_null_not_zero() {
    // "No measurement" must not become "no change". A 0.0 here would show up in
    // the promotion evidence as a composite that reliably did nothing.
    const std::string path = temp_path("null");
    std::remove(path.c_str());
    {
        AssemblyLog log(path);
        const int h = log.record({nr("SEARCH", {}, true)}, {}, {{0}}, 1, std::nullopt);
        log.close(h, std::nullopt);
    }
    const auto lines = read_lines(path);
    assert(lines.size() == 1);
    assert(lines[0]["rho_before"].is_null());
    assert(lines[0]["rho_after"].is_null());
    assert(lines[0]["delta_rho"].is_null());
    std::cout << "  [ok] absent rho serialises as null, never 0.0\n";
    std::remove(path.c_str());
}

void test_abandon_records_the_unknown_outcome() {
    const std::string path = temp_path("abandon");
    std::remove(path.c_str());
    {
        AssemblyLog log(path);
        const int h = log.record({nr("REASON", {3}, false)}, {}, {{0}}, 2, 0.1);
        log.abandon(h, "operad run threw");
    }
    const auto lines = read_lines(path);
    assert(lines.size() == 1);
    assert(lines[0]["closed"] == false);
    assert(lines[0]["note"] == "operad run threw");
    assert(lines[0]["rho_after"].is_null());
    std::cout << "  [ok] abandon() records the composite whose outcome is unknown\n";
    std::remove(path.c_str());
}

void test_appends_rather_than_truncates() {
    const std::string path = temp_path("append");
    std::remove(path.c_str());
    {
        AssemblyLog log(path);
        for (int i = 0; i < 3; ++i) {
            const int h = log.record({nr("SEARCH", {}, true)}, {}, {{0}},
                                     static_cast<std::uint64_t>(i), 0.2);
            log.close(h, 0.1);
        }
    }
    {  // a second log object on the same path must not clobber the first's lines
        AssemblyLog log(path);
        const int h = log.record({nr("VERIFY", {}, true)}, {}, {{0}}, 99, 0.2);
        log.close(h, 0.1);
    }
    const auto lines = read_lines(path);
    assert(lines.size() == 4);
    assert(lines[3]["tick"] == 99);
    std::cout << "  [ok] the log is append-only across writer lifetimes\n";
    std::remove(path.c_str());
}

// ---------------------------------------------------------------------------
// END-TO-END: does OSKernel::execute_dag actually record?
//
// The library tests above prove AssemblyLog works. They say nothing about
// whether the tick calls it, which is the part that was missing and the part
// that loses data every time it runs unwired. This drives a real FlatBuffers
// DAG through the real kernel and reads the file back.
//
// CONTEXT and VERIFY are used because their operators need neither a
// KnowledgeBase nor a LanguageKernel, so the test needs no network and no key.
// ---------------------------------------------------------------------------

void test_kernel_records_a_real_dag() {
    const std::string path = temp_path("e2e");
    std::remove(path.c_str());

    flatbuffers::FlatBufferBuilder fbb;

    const std::vector<float> geom_a = {1.0f, 0.0f, 0.0f, 0.0f};
    const std::vector<float> geom_b = {0.0f, 1.0f, 0.0f, 0.0f};

    auto op_ctx = mos::fbs::CreateOperator(
        fbb, mos::fbs::OpType_CONTEXT, fbb.CreateString("ctx"), 0, 0,
        fbb.CreateVector(geom_a));
    auto node_ctx = mos::fbs::CreateOperadNode(fbb, /*id=*/0, op_ctx,
                                               fbb.CreateVector<int>({1}));

    auto op_vfy = mos::fbs::CreateOperator(
        fbb, mos::fbs::OpType_VERIFY, fbb.CreateString("vfy"), 0, 0,
        fbb.CreateVector(geom_b));
    auto node_vfy = mos::fbs::CreateOperadNode(fbb, /*id=*/1, op_vfy, 0);

    auto dag = mos::fbs::CreateOperadDAG(
        fbb, fbb.CreateVector<flatbuffers::Offset<mos::fbs::OperadNode>>(
                 {node_ctx, node_vfy}));
    fbb.Finish(dag);

    {
        core::KernelConfig cfg;
        cfg.assembly_log_path = path;
        core::CognitiveState state;
        core::OSKernel kernel(state, cfg);

        assert(kernel.tick_count() == 0);
        const bool ok = kernel.execute_dag(fbb.GetBufferPointer(), fbb.GetSize());
        assert(ok);
        assert(kernel.tick_count() == 1);
        // Every recorded event must be closed or abandoned by the time the tick
        // returns; a leak here means events silently never reach disk.
        assert(kernel.assembly_log() != nullptr);
        assert(kernel.assembly_log()->open_count() == 0);
    }

    const auto lines = read_lines(path);
    assert(lines.size() == 1);
    const auto& j = lines[0];

    assert(j["tick"] == 1);
    assert(j["closed"] == true);
    assert(j["nodes"].size() == 2);
    // op_type must be the OpType (which organ acted), not READ_ONLY/MUTATION.
    std::vector<std::string> op_types;
    for (const auto& n : j["nodes"]) op_types.push_back(n["op_type"].get<std::string>());
    const bool has_ctx =
        std::find(op_types.begin(), op_types.end(), "CONTEXT") != op_types.end();
    const bool has_vfy =
        std::find(op_types.begin(), op_types.end(), "VERIFY") != op_types.end();
    assert(has_ctx && has_vfy);

    // The dependency CONTEXT -> VERIFY must survive into the record.
    assert(j["edges"].size() == 1);
    // rho_before is null on the first tick: nothing had been measured yet. That
    // is honest, not a defect -- it must NOT have been defaulted to a number.
    assert(j["rho_before"].is_null());
    assert(j["delta_rho"].is_null());
    // No foliation mismatch on a DAG whose supports are stable.
    assert(j["note"].get<std::string>().find("MISMATCH") == std::string::npos);

    std::cout << "  [ok] execute_dag recorded a real DAG: sig="
              << j["signature"].get<std::string>() << "\n";
    std::remove(path.c_str());
}

void test_recording_can_be_disabled() {
    core::KernelConfig cfg;
    cfg.assembly_log_path = "";  // the explicit opt-out
    core::CognitiveState state;
    core::OSKernel kernel(state, cfg);
    assert(kernel.assembly_log() == nullptr);
    std::cout << "  [ok] an empty path disables recording explicitly\n";
}

}  // namespace

int main() {
    std::cout << "=== canonical_signature (parity cases) ===\n";
    test_single_node();
    test_chain();
    test_order_independence();
    test_tie_break_is_by_key_not_index();
    test_edge_sort_is_lexicographic();
    test_cycle_is_refused();
    test_out_of_range_edge_is_refused();

    std::cout << "=== AssemblyLog round-trip ===\n";
    test_close_writes_one_line_with_delta_rho();
    test_missing_rho_stays_null_not_zero();
    test_abandon_records_the_unknown_outcome();
    test_appends_rather_than_truncates();

    std::cout << "=== E7 wired into the tick ===\n";
    test_kernel_records_a_real_dag();
    test_recording_can_be_disabled();

    std::cout << "\nALL ASSEMBLY LOG TESTS PASSED\n";
    return 0;
}
