#include "mos/core/kernel.hpp"
#include "operad_generated.h"
#include "mos/operators/primitives.hpp"
#include <iostream>

namespace mos {
namespace core {

class OperatorFactory {
public:
    static std::shared_ptr<mos::core::CognitiveOperator> create(
        const mos::fbs::Operator* op_data, 
        std::shared_ptr<translation::KnowledgeBase> kb, 
        std::shared_ptr<translation::LanguageKernel> llm,
        const KernelConfig& config) 
    {
        if (!op_data) return nullptr;
        std::string payload = op_data->payload() ? op_data->payload()->str() : "";

        // Payload geometry, embedded LOCALLY in Python and carried across the
        // boundary. Operators use this instead of fetching embeddings remotely.
        std::vector<double> geometry;
        if (op_data->geometry()) {
            geometry.assign(op_data->geometry()->begin(), op_data->geometry()->end());
        }

        switch (op_data->type()) {
            case mos::fbs::OpType_CONTEXT: {
                std::vector<mos::operators::ContextOp::Constraint> c_list;
                if (op_data->constraints()) {
                    for (const auto* fbs_c : *op_data->constraints()) {
                        mos::operators::ContextOp::Constraint c;
                        c.is_rigid = (fbs_c->type() == mos::fbs::ConstraintType_RIGID);
                        if (fbs_c->geometry()) {
                            c.geometry.assign(fbs_c->geometry()->begin(), fbs_c->geometry()->end());
                        }
                        c_list.push_back(c);
                    }
                }
                return std::make_shared<mos::operators::ContextOp>(payload, c_list);
            }
            case mos::fbs::OpType_SEARCH:
                return std::make_shared<mos::operators::SearchOp>(payload, kb, llm, geometry);
            case mos::fbs::OpType_COMPUTE:
                return std::make_shared<mos::operators::ComputeOp>(
                    payload, llm, config.compute_dt, config.compute_lambda, geometry
                );
            case mos::fbs::OpType_VERIFY:
                return std::make_shared<mos::operators::VerifyOp>(payload);
            case mos::fbs::OpType_REASON:
                return std::make_shared<mos::operators::ReasonOp>(payload, llm, geometry);
            case mos::fbs::OpType_RESPOND:
                return std::make_shared<mos::operators::RespondOp>(payload);
            default:
                return nullptr;
        }
    }
};

OSKernel::OSKernel(CognitiveState& initial_state, const KernelConfig& config)
    : state_(initial_state), config_(config) {
    unsigned int threads = config_.num_threads;
    if (threads == 0) {
        threads = std::thread::hardware_concurrency();
        if (threads == 0) threads = config_.fallback_threads;
    }
    thread_pool_ = std::make_shared<ThreadPool>(threads);

    // E7. An empty path is the explicit opt-out; anything else records.
    if (!config_.assembly_log_path.empty()) {
        assembly_log_ = std::make_unique<AssemblyLog>(config_.assembly_log_path);
        // Seed the verdict history from the log so gamma_no_verdict ACCUMULATES
        // across sessions. Without this the estimator would reset to its prior
        // on every process start, and "learns what an unchecked tick is worth"
        // would be true only within a single run.
        verdict_counts_ = AssemblyLog::scan_verdict_counts(config_.assembly_log_path);
    }
}

double OSKernel::gamma_for_unchecked() const {
    if (!config_.crystallise_unverified) return 0.0;
    return gamma_no_verdict(verdict_counts_, config_.gamma0, config_.gamma_eps,
                            config_.gamma_kappa, config_.gamma_prior_verified,
                            config_.gamma_prior_unverifiable);
}

void OSKernel::set_reflection_engine(std::shared_ptr<ReflectionEngine> reflection_engine) {
    reflection_engine_ = std::move(reflection_engine);
}

void OSKernel::set_knowledge_base(std::shared_ptr<translation::KnowledgeBase> kb) {
    kb_ = std::move(kb);
}

void OSKernel::set_llm(std::shared_ptr<translation::LanguageKernel> llm) {
    llm_ = std::move(llm);
}

void OSKernel::set_halt_condition(std::function<bool(const CognitiveState&)> condition) {
    halt_condition_ = std::move(condition);
}

std::optional<double> OSKernel::store_Q() const {
    // nullopt, not 0.0: "no store yet" and "a store that has learned nothing"
    // are different states, and collapsing them would make an engine that never
    // consolidated indistinguishable from one that never ran.
    if (!concept_store_) return std::nullopt;
    return const_cast<ConceptStore&>(*concept_store_).store().Q();
}

CognitiveState& OSKernel::get_state() noexcept {
    return state_;
}

bool OSKernel::execute_dag(const uint8_t* buffer, size_t size) {
    if (!buffer || size == 0) return false;

    // 1. Validate the buffer using FlatBuffers verifier
    flatbuffers::Verifier verifier(buffer, size);
    if (!mos::fbs::VerifyOperadDAGBuffer(verifier)) {
        std::cerr << "[OSKernel] FATAL: Invalid Operad DAG binary payload. Boundary rejected.\n";
        return false;
    }

    // 2. Access the DAG
    auto dag = mos::fbs::GetOperadDAG(buffer);
    if (!dag || !dag->nodes() || dag->nodes()->size() == 0) {
        std::cerr << "[OSKernel] Warning: Empty Operad DAG received. No operations to execute.\n";
        return true; 
    }

    // 3. Reconstruct the C++ Operad and Operators
    mos::core::Operad cpp_operad;
    // Map of id -> OperadNode
    std::map<int, std::shared_ptr<mos::core::OperadNode>> node_map;
    // Map of node id -> the organ (OpType) it belongs to, for the coarse complex.
    std::map<int, ModuleId> node_organ;
    // Same OpType name keyed by node pointer, for the E7 record. The operad
    // knows only READ_ONLY/MUTATION; the OpType lives on the FlatBuffers side,
    // so it has to be carried across here or the record loses which organ acted.
    std::map<const OperadNode*, std::string> node_op_type;

    // First pass: create all nodes and their operators
    for (const auto* node : *dag->nodes()) {
        auto cpp_op = OperatorFactory::create(node->operator_(), kb_, llm_, config_);

        // Even if op is null, we create the DAG node to maintain structure
        auto cpp_node = std::make_shared<mos::core::OperadNode>(cpp_op);
        node_map[node->id()] = cpp_node;
        cpp_operad.add_node(cpp_node);

        // --- populate the coarse complex K ---------------------------------
        // Each OpType is a cognitive organ. Its stalk is the operator's payload
        // geometry, embedded locally on the Python side so the engine never has
        // to derive meaning from a string (the adjunction boundary holds).
        const auto* op = node->operator_();
        if (op) {
            const ModuleId organ =
                mos::fbs::EnumNameOpType(op->type()) ? mos::fbs::EnumNameOpType(op->type())
                                                     : "UNKNOWN";
            node_organ[node->id()] = organ;
            node_op_type[cpp_node.get()] = organ;
            coarse_.register_module(organ);

            if (op->geometry() && op->geometry()->size() > 0) {
                Eigen::VectorXd v(op->geometry()->size());
                for (flatbuffers::uoffset_t i = 0; i < op->geometry()->size(); ++i) {
                    v(static_cast<Eigen::Index>(i)) =
                        static_cast<double>(op->geometry()->Get(i));
                }
                try {
                    coarse_.set_stalk(organ, v);
                } catch (const std::invalid_argument& e) {
                    // Dimension disagreement is a real fault, not something to
                    // paper over by reshaping the geometry.
                    std::cerr << "[OSKernel] coarse stalk rejected: " << e.what() << "\n";
                }
            }
            // No geometry => the organ stays IDLE (no position). It is then
            // excluded from rho, which is correct: an organ with no position
            // cannot meaningfully agree or disagree with anything.
        }
    }

    // Second pass: establish dependencies
    for (const auto* node : *dag->nodes()) {
        auto parent = node_map[node->id()];
        if (node->children_ids()) {
            for (auto child_id : *node->children_ids()) {
                auto child = node_map[child_id];
                if (child) {
                    cpp_operad.add_dependency(parent, child);

                    // Adjacency in the DAG IS cooperation: these two organs are
                    // working together on this reasoning act, so they co-activate
                    // (Hebbian: fire together -> wire together). Repeated
                    // cooperation is what eventually binds them into a coalition.
                    auto pit = node_organ.find(node->id());
                    auto cit = node_organ.find(child_id);
                    if (pit != node_organ.end() && cit != node_organ.end()) {
                        coarse_.co_activate(pit->second, cit->second, 1.0);
                    }
                }
            }
        }
    }

    // 3b. E7 — RECORD THE ASSEMBLY, BEFORE IT RUNS.
    // This has to happen here and not after: `rho_before` is only knowable
    // before the composite mutates the state, and the registry says assembly
    // data is impossible to recover later. The event is held open and closed at
    // step 5b once rho has been re-measured.
    ++tick_count_;

    // THE TICK BOUNDARY. Both of these are per-tick accumulators written by
    // operators during the run, so they must be reset here — before the run and
    // after the previous tick has been closed — or tick t would inherit tick
    // t-1's verdict and retrievals. Resetting after the run instead would race
    // with reading them.
    state_.clear_tick_verdict();
    state_.clear_tick_activation();

    int assembly_handle = -1;
    Foliation planned;
    std::map<const OperadNode*, int> node_index;
    if (assembly_log_) {
        const auto& ordered = cpp_operad.nodes();
        for (std::size_t i = 0; i < ordered.size(); ++i) {
            node_index[ordered[i].get()] = static_cast<int>(i);
        }

        std::vector<NodeRecord> records;
        records.reserve(ordered.size());
        for (const auto& node : ordered) {
            NodeRecord rec;
            // An operator-less node still has structure worth signing; naming it
            // UNKNOWN keeps the composite's shape honest instead of dropping it.
            // OperadNode::get_type/get_support dereference op_ unconditionally,
            // so the null check is load-bearing, not defensive noise.
            if (node->op_) {
                auto it = node_op_type.find(node.get());
                rec.op_type = (it != node_op_type.end()) ? it->second : "UNKNOWN";
                const auto support = node->get_support();
                rec.support.assign(support.begin(), support.end());
                rec.read_only = (node->get_type() == OperatorType::READ_ONLY);
            } else {
                rec.op_type = "UNKNOWN";
                rec.read_only = true;
            }
            records.push_back(std::move(rec));
        }

        std::vector<std::pair<int, int>> record_edges;
        for (const auto& node : ordered) {
            const int p = node_index[node.get()];
            for (const auto& child : node->children) {
                auto it = node_index.find(child.get());
                if (it != node_index.end()) record_edges.emplace_back(p, it->second);
            }
        }

        planned = plan_foliation(ordered);
        std::vector<std::vector<int>> slice_indices;
        slice_indices.reserve(planned.size());
        for (const auto& slice : planned) {
            std::vector<int> idx;
            idx.reserve(slice.size());
            for (const auto& node : slice) idx.push_back(node_index[node.get()]);
            slice_indices.push_back(std::move(idx));
        }

        try {
            assembly_handle = assembly_log_->record(
                std::move(records), std::move(record_edges), std::move(slice_indices),
                tick_count_, last_coherence_.rho);
        } catch (const std::exception& e) {
            // A composite we cannot sign (cycle, bad edge) is a bug worth
            // surfacing, but it must not take the tick down with it.
            std::cerr << "[OSKernel] E7 record failed: " << e.what() << "\n";
            assembly_handle = -1;
        }
    }

    // 4. Execute the Operad DAG on the cognitive state
    Foliation executed;
    try {
        executed = cpp_operad.run(state_, *thread_pool_);
    } catch (...) {
        // "We assembled this and never learned the outcome" is itself data, so
        // the event is abandoned rather than left dangling or silently dropped.
        if (assembly_log_ && assembly_handle >= 0) {
            try {
                assembly_log_->abandon(assembly_handle, "operad run threw");
            } catch (const std::exception& e) {
                std::cerr << "[OSKernel] E7 abandon failed: " << e.what() << "\n";
            }
        }
        throw;
    }

    // 4b. TWO-LEVEL BRIDGE (Construction 2, pi_v).
    // Now that operators have grown their concepts, replace each organ's COARSE
    // position with pi_v: the precision-weighted fusion of that organ's OWN fine
    // complex. Before this step the coarse stalk was a raw copy of the operator's
    // payload embedding; after it, coarse discord (rho over K) and the fine-level
    // concept geometry are the SAME measurement at two resolutions, which is the
    // whole point of the stratified complex. Organs that grew no concepts keep
    // their payload-derived position from the first pass.
    for (const auto& organ : node_organ) {
        if (auto pi_v = state_.compute_pi_v(organ.second)) {
            try {
                coarse_.set_stalk(organ.second, *pi_v);
            } catch (const std::invalid_argument& e) {
                std::cerr << "[OSKernel] pi_v stalk rejected for '" << organ.second
                          << "': " << e.what() << "\n";
            }
        }
    }

    // 4c. THE CONSOLIDATION LOOP (Phase 3). The spine, closed:
    //
    //     retrieved set --> i^*  --> W --> learn R^W --> nu --> gamma --> i_!
    //
    // Every piece of this existed and was unit-tested; none of it was reachable
    // from a tick, because gamma_nu takes a Verdict and no verdict was published.
    // With VerifyOp routed (step 5b) the chain closes and Q(t) can leave zero.
    //
    // ORDER MATTERS: this runs AFTER the operators (they are what retrieves) and
    // BEFORE E7 closes, so the number of crystallised edges reaches the record.
    //
    // The verdict is harvested HERE, not at 5b where it is written to E7. Read
    // any later and `last_verdict_` would still hold the PREVIOUS tick's value
    // at the moment gamma is computed, so this tick would crystallise on the
    // last one's evidence -- silently, and only visibly wrong on the tick after
    // a refutation.
    last_verdict_ = state_.tick_verdict();
    // Count it BEFORE gamma is computed below, so this tick's own verdict is in
    // the history the next unchecked tick extrapolates from. Only real verdicts
    // are counted: a nullopt tick contributes nothing, because it is the
    // population being extrapolated TO.
    if (last_verdict_) verdict_counts_.observe(*last_verdict_);
    last_crystallised_ = 0;
    {
        const auto coactive = state_.tick_retrieved();
        const auto geometry = state_.tick_geometry();

        if (!coactive.empty() && !geometry.empty()) {
            if (!concept_store_) {
                // The dimension is fixed for the store's life, so it is taken
                // from the first real geometry rather than guessed at construction.
                concept_store_.emplace(
                    static_cast<int>(geometry.begin()->second.size()));
            }
            try {
                concept_store_->observe(coactive);
                Store& K = concept_store_->store();

                // i^*: instantiate the working complex over exactly what this
                // tick touched. Downward closure is applied inside i_star.
                Working W = i_star(K, std::vector<HodgeVertex>(coactive.begin(),
                                                               coactive.end()));

                // THE LEARNING. For each edge of W whose two concepts both
                // carry geometry, R^W_e is the orthogonal map transporting u's
                // stalk onto v's -- the sheaf-consistency condition the edge is
                // supposed to satisfy. An edge is TOUCHED only when it was
                // actually learned; untouched edges are extended by zero and
                // stay bit-identical in the store.
                int learned = 0;
                for (const auto& e : W.complex.edges()) {
                    const auto u = geometry.find(e.first);
                    const auto v = geometry.find(e.second);
                    if (u == geometry.end() || v == geometry.end()) continue;
                    if (u->second.size() != v->second.size()) continue;
                    try {
                        W.restriction.insert_or_assign(
                            e, align_map(u->second, v->second));
                        W.touch(e);
                        ++learned;
                    } catch (const std::invalid_argument&) {
                        // Degenerate geometry on this edge (zero vector, or a
                        // dimension the store does not share). Skipping ONE edge
                        // is right; failing the tick over it is not.
                    }
                }

                // nu -> gamma. THE FOURTH STATE IS NO LONGER COLLAPSED.
                // gamma_nu is a function on three verdicts; "no VerifyOp was in
                // the DAG" is a fourth state it says nothing about, and applying
                // it there anyway was a partial function used as a total one.
                // With a real verdict we use gamma_nu unchanged. Without one we
                // use the DERIVED rate: what a check would have licensed, given
                // every check this store has ever seen. `crystallise_unverified
                // = false` still forces exactly 0 -- only checked sessions move
                // the store -- because that is a policy, not an estimate.
                const double gamma =
                    last_verdict_
                        ? gamma_nu(*last_verdict_, config_.gamma0, config_.gamma_eps)
                        : gamma_for_unchecked();

                last_crystallised_ = i_shriek(K, W, gamma);
                if (learned > 0) {
                    std::cerr << "[OSKernel] consolidation: learned " << learned
                              << " edge(s), gamma=" << gamma << " ("
                              << (last_verdict_ ? to_string(*last_verdict_)
                                                : "no oracle")
                              << "), crystallised " << last_crystallised_
                              << ", Q=" << K.Q() << "\n";
                }
            } catch (const std::exception& e) {
                // Consolidation is not allowed to take the tick down. A store
                // that failed to update is a lost session, not a lost answer.
                std::cerr << "[OSKernel] consolidation failed: " << e.what() << "\n";
            }
        }
    }

    // 5. Measure discord over the coarse complex K.
    // This is the real control signal: it asks whether the organs that just
    // cooperated on this reasoning act were working on semantically coherent
    // material. rho is reported as UNKNOWN when it genuinely is (no bound pairs,
    // or no organ carried geometry) rather than being defaulted to a number.
    last_coherence_ = coarse_.report();
    std::cerr << "[OSKernel] coherence: " << last_coherence_.summary() << "\n";

    // 5b. E7 — CLOSE THE EVENT now that rho_after exists.
    //
    // `verified` is STILL never inferred from rho — Construction 3 is explicit
    // that coherence is not correctness, and guessing here would fabricate the
    // promotion gate's own evidence. What changed is that it no longer has to be
    // guessed: VerifyOp publishes its real outcome via CognitiveState, so this
    // is the measured verdict or NULL when no oracle ran. Those two remain
    // different, and NULL still means exactly "not checked".
    // (last_verdict_ was harvested at 4c, where gamma needed it.)
    if (assembly_log_ && assembly_handle >= 0) {
        std::string note;
        // The record carries the PLANNED foliation because it is written before
        // the run. If the executed one differs, some operator's get_support()
        // changed under apply() and the recorded slices are wrong — say so in
        // the record rather than letting it quietly disagree with reality.
        std::vector<std::vector<int>> executed_indices;
        executed_indices.reserve(executed.size());
        for (const auto& slice : executed) {
            std::vector<int> idx;
            idx.reserve(slice.size());
            for (const auto& node : slice) {
                auto it = node_index.find(node.get());
                idx.push_back(it != node_index.end() ? it->second : -1);
            }
            executed_indices.push_back(std::move(idx));
        }
        std::vector<std::vector<int>> planned_indices;
        planned_indices.reserve(planned.size());
        for (const auto& slice : planned) {
            std::vector<int> idx;
            idx.reserve(slice.size());
            for (const auto& node : slice) idx.push_back(node_index[node.get()]);
            planned_indices.push_back(std::move(idx));
        }
        if (planned_indices != executed_indices) {
            note = "FOLIATION MISMATCH: planned != executed; recorded slices are the plan";
            std::cerr << "[OSKernel] E7 WARNING: " << note << "\n";
        }

        std::optional<std::string> verified;
        if (last_verdict_) verified = to_string(*last_verdict_);

        try {
            // The co-activation record is attached before close() because
            // close() flushes: anything set afterwards would never reach disk.
            assembly_log_->set_activation(assembly_handle,
                                          state_.tick_retrieved(),
                                          state_.tick_grown());
            assembly_log_->close(assembly_handle, last_coherence_.rho,
                                 verified, note);
        } catch (const std::exception& e) {
            std::cerr << "[OSKernel] E7 close failed: " << e.what() << "\n";
        }
    }

    // 6. THE TWO-MODE CONTROLLER.
    // rho now DRIVES behaviour rather than merely being logged. Note the three
    // outcomes: when discord is undefined we do NOT default to EXPLORE, because
    // "no measurement" is not "everything is fine" — that conflation is exactly
    // the failure mode the |E|=0 guard exists to prevent.
    if (!last_coherence_.rho.has_value()) {
        mode_ = CognitiveMode::UNKNOWN;
        std::cerr << "[OSKernel] mode=UNKNOWN (discord undefined: "
                  << last_coherence_.status
                  << "). Refusing to infer a mode from a missing measurement.\n";
    } else if (*last_coherence_.rho > config_.eps_rho) {
        mode_ = CognitiveMode::RESOLVE;
        std::cerr << "[OSKernel] mode=RESOLVE (rho=" << *last_coherence_.rho
                  << " > eps_rho=" << config_.eps_rho
                  << "): organs disagree; reconcile before expanding.\n";
        if (auto guilty = last_coherence_.worst_edge()) {
            std::cerr << "[OSKernel]   aim resolution at '" << guilty->first
                      << "' <-> '" << guilty->second << "' (omega_e="
                      << last_coherence_.per_edge.at(*guilty) << ")\n";
        }
    } else {
        mode_ = CognitiveMode::EXPLORE;
        std::cerr << "[OSKernel] mode=EXPLORE (rho=" << *last_coherence_.rho
                  << " <= eps_rho=" << config_.eps_rho
                  << "): internally coherent; free to build outward.\n";
    }

    if (last_coherence_.rho.has_value() && last_coherence_.is_fragmented()) {
        std::cerr << "[OSKernel] WARNING: complex is fragmented (b0="
                  << last_coherence_.b0
                  << "); this coherence claim is only LOCAL, not global.\n";
    }

    return true;
}

const char* to_string(CognitiveMode m) noexcept {
    switch (m) {
        case CognitiveMode::EXPLORE: return "EXPLORE";
        case CognitiveMode::RESOLVE: return "RESOLVE";
        default:                     return "UNKNOWN";
    }
}

bool OSKernel::tick() {
    if (halt_condition_ && halt_condition_(state_)) {
        return false;
    }

    // Update atomic attractor flag (IDE cache refresh trigger)
    bool attractor = state_.is_attractor_reached();
    state_.notify_attractor_state(attractor);

    if (attractor) {
        // Distill the stable state BEFORE exploring further
        if (reflection_engine_) {
            reflection_engine_->distill(state_);
        }
    } else {
        // Active conflict resolution
        double conflict = state_.calculate_conflict_score();
        if (conflict > config_.conflict_threshold && kb_ && llm_) {
            // Auto-generate a SEARCH DAG to pull missing axioms
            auto search_op = std::make_shared<mos::operators::SearchOp>(
                "RESOLVE: structural conflict " + std::to_string(conflict), kb_, llm_);
            auto node = std::make_shared<OperadNode>(search_op);
            Operad resolve_dag;
            resolve_dag.add_node(node);
            resolve_dag.run(state_, *thread_pool_);
        }
    }
    
    return true; // Successfully ran a maintenance cycle
}

} // namespace core
} // namespace mos
