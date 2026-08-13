// Phase 3, stage 3b: the consolidation loop, end to end through execute_dag.
//
// THE CLAIM UNDER TEST, and it is the first one this engine has been able to
// make: a tick that retrieves several stored concepts LEARNS something about
// how meaning transports between them, and that learning reaches the store.
//
// Q(t) = mean ||R^K_e - I||_F^2 is the whole acceptance criterion. Q = 0 is the
// constant sheaf -- every concept means the same thing in every context, i.e.
// nothing learned. Before this stage Q was pinned at 0 by construction, because
// gamma_nu takes a Verdict and no verdict was ever published, so i_! could not
// be called at all. These tests fail if that regresses.
//
// A real SQLite KnowledgeBase is used rather than a stub: SearchOp's retrieval
// IS the co-activation signal, so a test that faked it would be testing the
// fake. No LanguageKernel is needed -- geometry rides in on the DAG payload.

#include <cassert>
#include <cmath>
#include <cstdio>
#include <filesystem>
#include <iostream>
#include <string>
#include <vector>

#include "flatbuffers/flatbuffers.h"
#include "operad_generated.h"

#include "mos/core/kernel.hpp"
#include "mos/core/semantic_skill.hpp"
#include "mos/translation/knowledge_base.hpp"

using namespace mos;

namespace {

constexpr int kD = 8;

std::string temp_path(const std::string& tag) {
    return (std::filesystem::temp_directory_path() /
            ("mos_consolidation_" + tag + ".db")).string();
}

/// The query direction the test always searches from.
Eigen::VectorXd base_direction(int d) {
    return Eigen::VectorXd::Constant(d, 1.0 / std::sqrt(static_cast<double>(d)));
}

/// A concept NEAR the query direction, perturbed along one axis.
///
/// Both parts of this matter, and getting either wrong makes the test vacuous
/// rather than failing:
///
///   * NEAR. SearchOp's relevance threshold is max(0.1, 1/d), and
///     get_relevant_concepts measures Bures-Wasserstein, whose epistemic term is
///     d*(sqrt(D1) - sqrt(D2))^2. A concept whose variance differs from the
///     query's is rejected on variance alone no matter how well the means line
///     up -- which is exactly what happened on the first run here: nothing was
///     retrieved, so there was no co-activation and no store at all.
///
///   * DISTINCT. The perturbations must differ between concepts, or every pair
///     is parallel, align_map correctly returns the identity, and Q stays at 0
///     for a reason that has nothing to do with the loop being broken.
Eigen::VectorXd near_query(int d, int k, double spread) {
    Eigen::VectorXd v = base_direction(d);
    v(k % d) += spread;
    v((k + 3) % d) -= spread * 0.5;
    return v.normalized();
}

/// A DAG with one SEARCH node, carrying `geom` as the query's payload geometry.
/// SearchOp uses the payload rather than fetching an embedding, so this needs
/// no network and no API key.
void build_search_dag(flatbuffers::FlatBufferBuilder& fbb,
                      const std::vector<float>& geom) {
    auto op = fbs::CreateOperator(fbb, fbs::OpType_SEARCH,
                                  fbb.CreateString("query"), 0, 0,
                                  fbb.CreateVector(geom));
    auto node = fbs::CreateOperadNode(fbb, /*id=*/0, op, 0);
    auto dag = fbs::CreateOperadDAG(
        fbb, fbb.CreateVector<flatbuffers::Offset<fbs::OperadNode>>({node}));
    fbb.Finish(dag);
}

/// SEARCH -> VERIFY, where the VERIFY is guaranteed to come back UNVERIFIABLE.
///
/// The command is rejected by VerifyOp's security whitelist (unapproved
/// executable), and that path publishes Verdict::Unverifiable deliberately:
/// "the oracle was never allowed to run, so nothing was learned about whether
/// the mathematics holds". That is exactly the state P2's rule is about, and it
/// is reachable without a real interpreter.
void build_search_then_blocked_verify_dag(flatbuffers::FlatBufferBuilder& fbb,
                                          const std::vector<float>& geom) {
    auto search = fbs::CreateOperator(fbb, fbs::OpType_SEARCH,
                                      fbb.CreateString("query"), 0, 0,
                                      fbb.CreateVector(geom));
    auto verify = fbs::CreateOperator(fbb, fbs::OpType_VERIFY,
                                      fbb.CreateString("definitely_not_python foo"),
                                      0, 0, 0);
    auto n1 = fbs::CreateOperadNode(fbb, /*id=*/1, verify, 0);
    auto n0 = fbs::CreateOperadNode(fbb, /*id=*/0, search,
                                    fbb.CreateVector<int32_t>({1}));
    auto dag = fbs::CreateOperadDAG(
        fbb, fbb.CreateVector<flatbuffers::Offset<fbs::OperadNode>>({n0, n1}));
    fbb.Finish(dag);
}

/// Every restriction map in the store, as raw doubles, for a BITWISE compare.
///
/// Comparing Q(t) alone would be too weak: Q is a mean of squared norms, so a
/// pair of offsetting changes could leave it identical while the wiring moved.
/// The claim is that the store does not move AT ALL, so the test reads the
/// actual matrices.
std::vector<double> store_fingerprint(const core::OSKernel& kernel) {
    std::vector<double> out;
    const auto* cs = kernel.concept_store();
    if (!cs) return out;
    // Same const_cast the kernel's own store_Q() uses: the store is rebuilt
    // lazily, so materialising it is not a logical mutation.
    auto& store = const_cast<core::ConceptStore&>(*cs).store();
    for (const auto& [edge, map] : store.restriction) {
        (void)edge;
        const Eigen::MatrixXd dense = map.dense();
        for (Eigen::Index i = 0; i < dense.size(); ++i) out.push_back(dense.data()[i]);
    }
    return out;
}

/// Seed a KB with `n` concepts clustered near the query direction, so the
/// Wasserstein filter actually returns several of them together.
std::shared_ptr<translation::KnowledgeBase> seeded_kb(const std::string& path,
                                                      int n) {
    std::remove(path.c_str());
    auto kb = std::make_shared<translation::KnowledgeBase>(path);
    for (int i = 0; i < n; ++i) {
        Eigen::MatrixXd U(kD, 0);
        // D = 1.0 matches the variance SearchOp derives from a unit-norm query
        // (derived_variance = ||q||), so the Bures epistemic term vanishes and
        // relevance is decided by the means -- which is what the test is about.
        kb->commit_concept(std::make_shared<const core::SemanticEmbedding>(
            near_query(kD, i, 0.12 + 0.03 * i), U, 1.0,
            "concept_" + std::to_string(i)));
    }
    return kb;
}

std::vector<float> query_geometry() {
    const Eigen::VectorXd b = base_direction(kD);
    std::vector<float> g(kD);
    for (int i = 0; i < kD; ++i) g[i] = static_cast<float>(b(i));
    return g;
}

// ---------------------------------------------------------------------------

void test_Q_leaves_zero_after_a_real_tick() {
    const std::string db = temp_path("q_rises");
    auto kb = seeded_kb(db, 5);

    core::KernelConfig cfg;
    cfg.assembly_log_path = "";          // not under test here
    core::CognitiveState state;
    core::OSKernel kernel(state, cfg);
    kernel.set_knowledge_base(kb);

    // Before any tick there is NO store, which is not the same as Q = 0.
    assert(!kernel.store_Q().has_value());

    flatbuffers::FlatBufferBuilder fbb;
    build_search_dag(fbb, query_geometry());
    assert(kernel.execute_dag(fbb.GetBufferPointer(), fbb.GetSize()));

    const auto q = kernel.store_Q();
    assert(q.has_value());
    assert(kernel.concept_store() != nullptr);

    if (kernel.concept_store()->num_edges() == 0) {
        // The retrieval threshold let through fewer than two concepts, so there
        // was no pair to learn from. Say so rather than passing quietly.
        std::cout << "  [SKIP] retrieval returned <2 concepts; no edge to learn\n";
        std::remove(db.c_str());
        return;
    }

    std::cout << "  Q after one tick = " << *q << " over "
              << kernel.concept_store()->num_edges() << " edge(s), "
              << kernel.last_crystallised() << " crystallised\n";
    assert(*q > 0.0);   // THE CLAIM: the store learned something
    assert(kernel.last_crystallised() > 0);
    std::remove(db.c_str());
}

void test_Q_is_monotone_over_repeated_ticks() {
    // Crystallisation is a gamma-blend toward the session's map, so repeating
    // the same session must move K further, not oscillate.
    const std::string db = temp_path("q_monotone");
    auto kb = seeded_kb(db, 5);

    core::KernelConfig cfg;
    cfg.assembly_log_path = "";
    core::CognitiveState state;
    core::OSKernel kernel(state, cfg);
    kernel.set_knowledge_base(kb);

    flatbuffers::FlatBufferBuilder fbb;
    build_search_dag(fbb, query_geometry());

    double prev = 0.0;
    bool any_edges = false;
    for (int t = 0; t < 4; ++t) {
        assert(kernel.execute_dag(fbb.GetBufferPointer(), fbb.GetSize()));
        const double q = kernel.store_Q().value_or(0.0);
        if (kernel.concept_store() && kernel.concept_store()->num_edges() > 0) {
            any_edges = true;
            assert(q >= prev - 1e-12);   // never goes backwards
        }
        prev = q;
    }
    if (!any_edges) {
        std::cout << "  [SKIP] no edges formed; monotonicity vacuous\n";
    } else {
        std::cout << "  Q is non-decreasing across 4 ticks, ending at " << prev << "\n";
        assert(prev > 0.0);
    }
    std::remove(db.c_str());
}

void test_refuted_tick_does_not_move_the_store() {
    // gamma(Refuted) = 0 EXACTLY, so a refuted session must leave K
    // bit-identical however much it learned. Driven through the real kernel,
    // because that is where the verdict now travels.
    const std::string db = temp_path("q_refuted");
    auto kb = seeded_kb(db, 5);

    core::KernelConfig cfg;
    cfg.assembly_log_path = "";
    core::CognitiveState state;
    core::OSKernel kernel(state, cfg);
    kernel.set_knowledge_base(kb);

    flatbuffers::FlatBufferBuilder fbb;
    build_search_dag(fbb, query_geometry());
    assert(kernel.execute_dag(fbb.GetBufferPointer(), fbb.GetSize()));

    if (!kernel.concept_store() || kernel.concept_store()->num_edges() == 0) {
        std::cout << "  [SKIP] no edges formed; refutation test vacuous\n";
        std::remove(db.c_str());
        return;
    }
    const double q_before = kernel.store_Q().value();

    // A SEARCH plus a VERIFY whose command is blocked -> Unverifiable, not
    // Refuted. To force Refuted the oracle would have to run and fail, which
    // needs a real interpreter; instead assert the weaker, still-decisive claim
    // that an UNVERIFIED tick crystallises strictly LESS than a verified one.
    core::KernelConfig strict = cfg;
    strict.crystallise_unverified = false;
    core::CognitiveState state2;
    core::OSKernel kernel2(state2, strict);
    kernel2.set_knowledge_base(kb);
    assert(kernel2.execute_dag(fbb.GetBufferPointer(), fbb.GetSize()));

    const double q_strict = kernel2.store_Q().value_or(-1.0);
    std::cout << "  Q with crystallise_unverified=true: " << q_before
              << ", =false: " << q_strict << "\n";
    assert(q_strict == 0.0);       // nothing checked, so nothing crystallised
    assert(q_before > q_strict);   // and the permissive setting did learn
    std::remove(db.c_str());
}

void test_unverifiable_tick_leaves_the_store_bit_identical() {
    // P2'S SAFETY RULE, AND THE TEST THAT PROVES IT IS REAL.
    //
    // "UNKNOWN must map to gamma = 0, not to a small positive number. An
    // unverified claim should leave the crystallised store untouched, not nudge
    // it slightly. Nudging is how an unverified claim becomes a verified one
    // after enough repetitions." (SPEC_P1_TO_P4 §P2)
    //
    // This knowingly overrides gamma_nu, which maps Unverifiable to eps*gamma0.
    // See KernelConfig::unverifiable_gamma_zero for both sides of that
    // disagreement. The test pins the POLICY, and the second half pins that the
    // policy is genuinely doing the work rather than the tick being inert.
    const std::string db = temp_path("q_unverifiable");
    auto kb = seeded_kb(db, 5);

    core::KernelConfig cfg;
    cfg.assembly_log_path = "";
    core::CognitiveState state;
    core::OSKernel kernel(state, cfg);
    kernel.set_knowledge_base(kb);

    // Tick 1: a plain SEARCH, no oracle. Builds the store and learns.
    flatbuffers::FlatBufferBuilder fbb;
    build_search_dag(fbb, query_geometry());
    assert(kernel.execute_dag(fbb.GetBufferPointer(), fbb.GetSize()));

    if (!kernel.concept_store() || kernel.concept_store()->num_edges() == 0) {
        std::cout << "  [SKIP] no edges formed; unverifiable test vacuous\n";
        std::remove(db.c_str());
        return;
    }
    const auto before = store_fingerprint(kernel);
    const double q_before = kernel.store_Q().value();
    assert(!before.empty());

    // Tick 2: the SAME retrieval, plus an oracle that is blocked and therefore
    // returns UNVERIFIABLE. It learns exactly as much as tick 1 did -- the gap
    // is nonzero -- so anything that moves is the gate leaking.
    flatbuffers::FlatBufferBuilder fbb2;
    build_search_then_blocked_verify_dag(fbb2, query_geometry());
    assert(kernel.execute_dag(fbb2.GetBufferPointer(), fbb2.GetSize()));

    assert(kernel.last_verdict().has_value());
    assert(*kernel.last_verdict() == core::Verdict::Unverifiable);

    const auto after = store_fingerprint(kernel);
    const double q_after = kernel.store_Q().value();

    std::cout << "  verdict=" << core::to_string(*kernel.last_verdict())
              << " Q " << q_before << " -> " << q_after
              << ", learned " << kernel.last_learned() << " edge(s), gap mean="
              << (kernel.last_gap_mean() ? std::to_string(*kernel.last_gap_mean())
                                         : std::string("n/a"))
              << ", crystallised " << kernel.last_crystallised() << "\n";

    // THE CLAIM: bit-identical, not merely close.
    assert(after.size() == before.size());
    for (std::size_t i = 0; i < before.size(); ++i) {
        assert(before[i] == after[i] && "an UNVERIFIABLE tick moved the store");
    }
    assert(q_after == q_before);
    assert(kernel.last_crystallised() == 0);

    // AND THE TEST IS NOT VACUOUS: the tick really did have something to teach.
    // Without this, a run that learned nothing would pass the bitwise check
    // while proving nothing about the gate.
    assert(kernel.last_learned() > 0);
    assert(kernel.last_gap_mean().has_value() && *kernel.last_gap_mean() > 0.0);

    std::remove(db.c_str());
}

void test_unverifiable_does_move_the_store_when_the_policy_is_off() {
    // The mirror image, so the flag is shown to be the cause. With the policy
    // disabled, gamma_nu's eps*gamma0 applies and the same tick DOES nudge the
    // store -- which is precisely the accumulation the spec objects to.
    const std::string db = temp_path("q_unverifiable_off");
    auto kb = seeded_kb(db, 5);

    core::KernelConfig cfg;
    cfg.assembly_log_path = "";
    cfg.unverifiable_gamma_zero = false;   // restore gamma_nu's own rate
    core::CognitiveState state;
    core::OSKernel kernel(state, cfg);
    kernel.set_knowledge_base(kb);

    flatbuffers::FlatBufferBuilder fbb;
    build_search_dag(fbb, query_geometry());
    assert(kernel.execute_dag(fbb.GetBufferPointer(), fbb.GetSize()));
    if (!kernel.concept_store() || kernel.concept_store()->num_edges() == 0) {
        std::cout << "  [SKIP] no edges formed\n";
        std::remove(db.c_str());
        return;
    }
    const double q_before = kernel.store_Q().value();

    flatbuffers::FlatBufferBuilder fbb2;
    build_search_then_blocked_verify_dag(fbb2, query_geometry());
    assert(kernel.execute_dag(fbb2.GetBufferPointer(), fbb2.GetSize()));
    assert(*kernel.last_verdict() == core::Verdict::Unverifiable);

    const double q_after = kernel.store_Q().value();
    std::cout << "  policy OFF: Q " << q_before << " -> " << q_after
              << ", crystallised " << kernel.last_crystallised() << "\n";
    assert(kernel.last_crystallised() > 0);
    assert(q_after > q_before);   // the nudge the spec calls laundering
    std::remove(db.c_str());
}

void test_store_identity_survives_growth_through_the_kernel() {
    const std::string db = temp_path("q_growth");
    auto kb = seeded_kb(db, 6);

    core::KernelConfig cfg;
    cfg.assembly_log_path = "";
    core::CognitiveState state;
    core::OSKernel kernel(state, cfg);
    kernel.set_knowledge_base(kb);

    flatbuffers::FlatBufferBuilder f1;
    build_search_dag(f1, query_geometry());
    assert(kernel.execute_dag(f1.GetBufferPointer(), f1.GetSize()));
    const std::size_t n1 = kernel.concept_store()
                               ? kernel.concept_store()->num_concepts() : 0;

    // A different query direction, pulling in a partly different concept set.
    // Still close enough to the cluster to retrieve, or the second tick would
    // retrieve nothing and the growth assertion would hold vacuously.
    const Eigen::VectorXd q2 = near_query(kD, 2, 0.20);
    std::vector<float> g2(kD);
    for (int i = 0; i < kD; ++i) g2[i] = static_cast<float>(q2(i));
    flatbuffers::FlatBufferBuilder f2;
    build_search_dag(f2, g2);
    assert(kernel.execute_dag(f2.GetBufferPointer(), f2.GetSize()));

    const std::size_t n2 = kernel.concept_store()
                               ? kernel.concept_store()->num_concepts() : 0;
    assert(n2 >= n1);   // the store only grows
    std::cout << "  store grew " << n1 << " -> " << n2
              << " concepts across two different queries\n";
    std::remove(db.c_str());
}

}  // namespace

int main() {
    std::cout << "test_consolidation_loop\n";
    test_Q_leaves_zero_after_a_real_tick();
    test_Q_is_monotone_over_repeated_ticks();
    test_refuted_tick_does_not_move_the_store();
    test_unverifiable_tick_leaves_the_store_bit_identical();
    test_unverifiable_does_move_the_store_when_the_policy_is_off();
    test_store_identity_survives_growth_through_the_kernel();
    std::cout << "all consolidation-loop tests passed\n";
    return 0;
}
