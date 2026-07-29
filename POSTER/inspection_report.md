# MOS Codebase — Full Structural Inspection Report

Complete file-by-file audit of all 30+ source and header files. Findings are categorized as:
- 🔧 **FIXED** — Applied immediately during this session
- ⚠️ **OPEN** — Requires design decision or further work
- 📝 **NOTED** — Architectural observation, not necessarily a defect

---

## 1. `src/main.cpp`

| # | Finding | Status |
|---|---------|--------|
| 1.1 | Missing `NOMINMAX` before `#include <Windows.h>` — would cause `std::max` macro collision | 🔧 FIXED |
| 1.2 | When run without `--ipc-server`, the binary does nothing but print a one-liner and exit. No REPL, no test harness, no help text | ⚠️ OPEN |
| 1.3 | No payload size upper-bound validation feedback — silently skips invalid sizes via `continue` without logging count of rejected payloads | 📝 NOTED |
| 1.4 | IPC loop reads raw binary from stdin with no framing checksum or version header. If the Python side sends a partial write (e.g., process killed mid-stream), the C++ engine will either block forever or read corrupt data | ⚠️ OPEN |

---

## 2. `src/core/kernel.cpp` + `include/mos/core/kernel.hpp`

| # | Finding | Status |
|---|---------|--------|
| 2.1 | `OperatorFactory` was a local struct inside `execute_dag`, now properly extracted as a class | 🔧 FIXED (previous session) |
| 2.2 | Hardcoded `dt=0.05f`, `lambda=2.0f` in `ComputeOp` creation — now driven by `KernelConfig` | 🔧 FIXED (previous session) |
| 2.3 | Thread fallback was hardcoded `2`, now uses `config_.fallback_threads` (default 4) | 🔧 FIXED (previous session) |
| 2.4 | `tick()` only calls `distill()` — no autonomous conflict-resolution loop. It checks `is_attractor_reached()` but has no mechanism to actually route a new DAG when conflict is high. The "Orchestrator" is passive | ⚠️ OPEN |
| 2.5 | `execute_dag` does not catch exceptions from `Operad::run`. If a topological collapse `std::runtime_error` propagates through the thread pool, the kernel crashes | ⚠️ OPEN — see 8.1 for partial mitigation |

---

## 3. `src/core/cognitive_state.cpp` + `include/mos/core/cognitive_state.hpp`

| # | Finding | Status |
|---|---------|--------|
| 3.1 | `is_stable()` used hardcoded `1e-9` threshold — now uses `std::numeric_limits<double>::epsilon()` | 🔧 FIXED (previous session) |
| 3.2 | `apply_flow()` sampled dimension from first vertex — now uses enforced `embedding_dimension_` | 🔧 FIXED (previous session) |
| 3.3 | PCA solver failures returned mock zeroes — now throws `std::runtime_error` in all three locations ([calculate_conflict_score](file:///c:/Users/cdarg/Desktop/TATIANA/MOS/src/core/cognitive_state.cpp#L313), [get_current_state_vector](file:///c:/Users/cdarg/Desktop/TATIANA/MOS/src/core/cognitive_state.cpp#L365), [get_principal_stress_vector](file:///c:/Users/cdarg/Desktop/TATIANA/MOS/src/core/cognitive_state.cpp#L428)) | 🔧 FIXED (previous session) |
| 3.4 | Dead member variables `previous_entropy_` and `has_previous_entropy_` declared but never read/written anywhere | 🔧 FIXED — removed |
| 3.5 | `is_collapsed_` is set to `true` on PCA failure but **never reset** back to `false`. Once the state collapses, there is no recovery path. `is_collapsed()` accessor exists but nothing in the engine reads it | ⚠️ OPEN |
| 3.6 | `remove_temporary_axiom()` removes simplices from `math_complex_` but **does not clean up the corresponding sheaf stalks** — orphaned `ProceduralSkill` pointers remain in `math_sheaf_.stalks_` | ⚠️ OPEN |
| 3.7 | `inject_temporary_axiom()` uses `std::lock_guard<std::shared_mutex>` (exclusive lock). This is correct, but `inject_chat_memory()` also uses it, meaning chat injection blocks mathematical reasoning. These are independent topologies and could use independent mutexes | ⚠️ OPEN |
| 3.8 | `get_mutex()` exposes the internal mutex publicly. Any consumer can deadlock the system by holding the lock indefinitely (e.g., [knowledge_curator.cpp:60](file:///c:/Users/cdarg/Desktop/TATIANA/MOS/src/core/knowledge_curator.cpp#L60) acquires a read lock in `digest_memory` while holding the REM loop's own `cv_m_` lock) | ⚠️ OPEN |
| 3.9 | `calculate_conflict_score()` computes the Gram matrix as `X * X^T / (M-1)` — this is an M×M matrix, not the D×D covariance. For M ≪ D this is fine (kernel PCA), but the returned "conflict score" is the **largest eigenvalue of the Gram matrix**, which conflates sample spread with actual variance unless M is comparable to D | 📝 NOTED |

---

## 4. `src/core/semantic_skill.cpp` + `include/mos/core/semantic_skill.hpp`

| # | Finding | Status |
|---|---------|--------|
| 4.1 | Hardcoded SVD rank truncation at `k_max = 10` — now uses dynamic 95% energy threshold | 🔧 FIXED (previous session) |
| 4.2 | `merge_with()` performs two dense matrix inversions (`M1_inv.inverse()`, `M2_inv.inverse()`) without checking for singularity. If `U^T * U` is ill-conditioned, these inversions silently produce garbage | ⚠️ OPEN |
| 4.3 | The `M_PI` / `M_E` defines at the top of the file use `#ifndef` guards which is correct, but they duplicate the standard `<numbers>` header (C++20). Not a bug for C++17 | 📝 NOTED |

---

## 5. `src/core/reflection.cpp` + `include/mos/core/reflection.hpp`

| # | Finding | Status |
|---|---------|--------|
| 5.1 | `distill()` destructively deleted uncrystallized vertices — now preserves residuals in chat geometry via `inject_chat_memory()` | 🔧 FIXED (previous session) |
| 5.2 | `distill()` calls `state.get_complex()` and `state.get_sheaf()` (the convenience aliases) — these return `math_complex_` and `math_sheaf_`, which is correct. But it also calls `state.inject_chat_memory()` which acquires the `mutex_` — while `distill()` itself does **not** acquire any lock. If the kernel calls `distill()` while an operator is concurrently mutating state, this is a data race | ⚠️ OPEN |

---

## 6. `src/core/knowledge_curator.cpp` + `include/mos/core/knowledge_curator.hpp`

| # | Finding | Status |
|---|---------|--------|
| 6.1 | Hardcoded 1-hour sleep — now event-driven via `is_attractor_reached()` | 🔧 FIXED (previous session) |
| 6.2 | **Double-escaped newlines** (`\\n` instead of `\n`) in all three `std::cout` statements — prints literal backslash-n instead of newline | 🔧 FIXED |
| 6.3 | `digest_memory()` acquires a **shared (read) lock** on `state_.get_mutex()` via [line 60](file:///c:/Users/cdarg/Desktop/TATIANA/MOS/src/core/knowledge_curator.cpp#L60), then calls `get_principal_stress_vector()` which **also** acquires a shared lock on the same mutex. `std::shared_mutex` permits recursive shared locks on the same thread on most implementations, but this is **not guaranteed by the standard** — it is technically undefined behavior | ⚠️ OPEN |
| 6.4 | `rem_loop()` uses `cv_.wait()` which checks `is_attractor_reached()` — but `is_attractor_reached()` acquires `mutex_`, while the wait is under `cv_m_`. If `is_attractor_reached()` blocks (e.g., shared lock contention from an ongoing apply_flow), the condition variable's predicate becomes a blocking call, violating the expected non-blocking predicate semantics | ⚠️ OPEN |

---

## 7. `src/core/operad.cpp` + `include/mos/core/operad.hpp`

| # | Finding | Status |
|---|---------|--------|
| 7.1 | `OperadNode::execute()` had no exception handling — if an operator throws (as PCA collapse now does), the future's `.wait()` would rethrow and crash | 🔧 FIXED — wrapped in try-catch |
| 7.2 | Missing `<stdexcept>` header for `std::exception` | 🔧 FIXED |
| 7.3 | The foliation scheduler in `Operad::run()` checks `support.empty()` and treats it as "global mutation" that must run isolated. But `SearchOp` and `RespondOp` declare `READ_ONLY` type yet return empty support `{}` — the foliation logic ignores `OperatorType` entirely and only checks support sets. A `READ_ONLY` op with empty support is treated identically to a `MUTATION` op with empty support | ⚠️ OPEN |
| 7.4 | `OperadNode::op_` is `public` — exposes internal state. Should be `private` with a getter | 📝 NOTED |
| 7.5 | `in_degree` is a public `std::atomic<int>` modified by both `add_dependency` and the run loop — this is correct for thread safety but the public access allows external callers to corrupt the DAG state | 📝 NOTED |

---

## 8. `src/core/thread_pool.cpp` + `include/mos/core/thread_pool.hpp`

| # | Finding | Status |
|---|---------|--------|
| 8.1 | Worker threads catch **no exceptions**. If a task throws, `std::terminate()` is called. The `OperadNode::execute` fix (7.1) partially mitigates this for operator failures, but any other task enqueued to the pool is still vulnerable | ⚠️ OPEN |

---

## 9. `src/translation/colibri_kernel.cpp` + `include/mos/translation/colibri_kernel.hpp`

| # | Finding | Status |
|---|---------|--------|
| 9.1 | `confidence` hardcoded to `0.5` when logprobs are absent — now uses a sigmoid length-based heuristic | 🔧 FIXED |
| 9.2 | `http_post()` creates a **new WinHTTP session, connection, and request** for every single call. No connection pooling, no keep-alive. Every embedding fetch and every thought generation opens a new TCP+TLS handshake | ⚠️ OPEN |
| 9.3 | `generate_thought()` uses a fragile `---FINAL---` string delimiter to split reasoning from conclusion. If the LLM doesn't produce this exact marker, the entire response is dumped into `final_conclusion` with `reasoning_chain = "Raw Thought"` | ⚠️ OPEN |
| 9.4 | `generate_thought()` silently swallows HTTP exceptions and returns an **empty, default-constructed** `AgentThought` with empty latent, empty strings, and 0.0 confidence. Callers (e.g., `ReasonOp`) then operate on this empty state without checking | ⚠️ OPEN |
| 9.5 | `WinHttpQueryDataAvailable` return value is not checked — if it fails, `dwSize` is uninitialized | ⚠️ OPEN |
| 9.6 | The `GROQ_API_KEY` is read from environment via `std::getenv()` on **every single HTTP request**, not cached | 📝 NOTED |

---

## 10. `src/translation/knowledge_base.cpp` + `include/mos/translation/knowledge_base.hpp`

| # | Finding | Status |
|---|---------|--------|
| 10.1 | `calculate_wasserstein_2_sq()` is duplicated identically in both [knowledge_base.cpp](file:///c:/Users/cdarg/Desktop/TATIANA/MOS/src/translation/knowledge_base.cpp#L127) and [curator.cpp](file:///c:/Users/cdarg/Desktop/TATIANA/MOS/src/translation/curator.cpp#L20). Should be extracted into a shared math utility | ⚠️ OPEN |
| 10.2 | `get_relevant_concepts()` does a **full table scan** of all distilled theorems on every search query. No spatial index, no approximate nearest neighbor. For large knowledge bases this is O(N × k³) per query | ⚠️ OPEN |
| 10.3 | Noise floor clamping `if (D <= 0.0) D = 1e-9` appears in two locations ([L118](file:///c:/Users/cdarg/Desktop/TATIANA/MOS/src/translation/knowledge_base.cpp#L118), [L193](file:///c:/Users/cdarg/Desktop/TATIANA/MOS/src/translation/knowledge_base.cpp#L193)) — this silently masks corrupt database rows rather than flagging them | 📝 NOTED |
| 10.4 | `commit_concept()` does **INSERT only** — if the same concept is committed multiple times (e.g., re-distilled), it creates duplicate rows. There is no UPSERT or deduplication logic | ⚠️ OPEN |
| 10.5 | No database migration strategy. If the schema changes, existing `.db` files become incompatible with no error handling | ⚠️ OPEN |

---

## 11. `src/translation/curator.cpp` + `include/mos/translation/curator.hpp`

| # | Finding | Status |
|---|---------|--------|
| 11.1 | Duplicate Wasserstein implementation (see 10.1) | ⚠️ OPEN |
| 11.2 | `curate()` takes `new_vertex_id` as a `size_t` parameter but `VertexID` is `int` — implicit narrowing conversion | ⚠️ OPEN |
| 11.3 | Edge skills are created with the **thought's** geometry (`thought_mu, thought_U, thought_D`) rather than an interpolation or midpoint between the two vertices — the edge stalk doesn't encode the relationship, just a copy of one endpoint | ⚠️ OPEN |

---

## 12. `src/math/algebra.cpp` + `include/mos/math/algebra.hpp`

| # | Finding | Status |
|---|---------|--------|
| 12.1 | `compute_rank()` was missing — Betti number computation was dead code | 🔧 FIXED — implemented via JacobiSVD |
| 12.2 | `Matrix::at()` performs no bounds checking — out-of-bounds access is silent UB | 📝 NOTED |
| 12.3 | Comment says "Hardware accelerated SIMD eigensolver" but this is just Eigen's default `SelfAdjointEigenSolver` — Eigen will use SSE/AVX if available at compile time but there's no explicit SIMD control | 📝 NOTED |

---

## 13. `src/math/fourier.cpp` + `include/mos/math/fourier.hpp`

| # | Finding | Status |
|---|---------|--------|
| 13.1 | Random projection matrix `W_` uses hardcoded seed `42`. This is **intentional** for cross-session stability, but the comment should note that changing the seed invalidates all persisted knowledge base embeddings | 📝 NOTED |
| 13.2 | The `project()` output dimension is `2 * fourier_dim_` (cos + sin features). If the embedding model's output dimension doesn't match `input_dim_`, the curator will throw. There's no runtime validation that the LLM embedding dimension matches the mapper's `input_dim_` | ⚠️ OPEN |

---

## 14. `src/topology/` (simplex.cpp, chain.cpp, complex.cpp)

| # | Finding | Status |
|---|---------|--------|
| 14.1 | `SimplicialComplex::remove()` does cascading co-face deletion via `std::includes()` check. This is O(V × S) per removal where S is the number of higher-dimensional simplices. For large complexes this is expensive | 📝 NOTED |
| 14.2 | `Simplex` constructor does not check for duplicate vertex IDs. Passing `{1, 1, 2}` silently creates a degenerate simplex `{1, 1, 2}` → sorted as `{1, 1, 2}` — a non-standard simplex | ⚠️ OPEN |
| 14.3 | `Chain::scale(0)` clears the chain — correct. But `Chain::add()` auto-removes zero-coefficient entries, which could cause subtle issues if a consumer iterates while adding | 📝 NOTED |

---

## 15. `src/dormant/homology.cpp` + `boundary_matrix.cpp`

| # | Finding | Status |
|---|---------|--------|
| 15.1 | `betti_number()` was fully dead — commented out code returning hardcoded `0` | 🔧 FIXED — revived with `compute_rank()` |
| 15.2 | `compute_obstruction()` calls `betti_number()` in a loop — now actually functional | 🔧 FIXED (consequence of 15.1) |
| 15.3 | The dormant module has no callers in the active engine. `HomologyComputer` and `BoundaryMatrixGenerator` are built but never invoked by the kernel, reflection engine, or curator | ⚠️ OPEN — potential integration point for structural verification |

---

## 16. `src/operators/` (expansion.cpp, edge_expansion.cpp, edge_contraction.cpp)

| # | Finding | Status |
|---|---------|--------|
| 16.1 | `EdgeContractionOperator::apply()` does not implement `get_type()` or `get_support()` — it inherits directly from `CognitiveOperator` without providing these pure virtual implementations. **This file will not compile** as a standalone operator | ⚠️ OPEN |
| 16.2 | `ExpansionOperator` and `EdgeExpansionOperator` similarly lack `get_type()` and `get_support()` overrides | ⚠️ OPEN |
| 16.3 | All three operators call `state.get_complex()` and `state.get_sheaf()` (convenience aliases to `math_complex_` / `math_sheaf_`) — they bypass the locking mechanism entirely, performing direct mutation without acquiring `mutex_` | ⚠️ OPEN |

---

## 17. `src/operators/primitives.cpp`

| # | Finding | Status |
|---|---------|--------|
| 17.1 | Missing `NOMINMAX` before `<windows.h>` | 🔧 FIXED (earlier in this conversation) |
| 17.2 | `VerifyOp` security whitelist is bypassable — it only checks `command_.find("python ") == 0` but doesn't validate the path. An attacker could craft `python ../../evil.py` or use Python's `-m` flag to run arbitrary modules | ⚠️ OPEN |
| 17.3 | `VerifyOp` uses `CreateProcessA` with `NULL` as the application name — Windows resolves the executable from the command string using `PATH` search. An attacker could shadow `python.exe` with a malicious binary in a higher-priority PATH directory | ⚠️ OPEN |

---

## 18. `include/operator.hpp` (Top-level, outside `mos/` directory)

| # | Finding | Status |
|---|---------|--------|
| 18.1 | **Entirely stale legacy file.** Contains mock `EdgeContractionOperator` and `LanguageProjectionTrigger` classes with stub `apply()` methods that just `return true`. These use a different class hierarchy (`mos::CognitiveOperator` vs `mos::core::CognitiveOperator`), different namespace, and a non-existent include `"cognitive_state.hpp"`. This file is **not included by anything in the build** and should be deleted | ⚠️ OPEN — recommend deletion |

---

## 19. `include/mos/translation/llm_interface.hpp`

| # | Finding | Status |
|---|---------|--------|
| 19.1 | `AgentThought::confidence` was uninitialized (no default value) — would contain garbage if logprobs parsing fails before assignment | 🔧 FIXED — initialized to `0.0` |

---

## Summary Statistics

| Category | Count |
|----------|-------|
| 🔧 **Fixed this session** | 8 |
| 🔧 **Fixed previous session** | 7 |
| ⚠️ **Open issues** | 27 |
| 📝 **Noted observations** | 12 |

## Priority Open Issues (Recommended Next Actions)

> [!IMPORTANT]
> 1. **16.1–16.2**: `EdgeContractionOperator`, `ExpansionOperator`, `EdgeExpansionOperator` missing pure virtual overrides — will fail to compile if instantiated through the core `CognitiveOperator` interface
> 2. **16.3**: Operators bypass mutex locking — concurrent execution via the thread pool is a data race
> 3. **18.1**: Delete `include/operator.hpp` — fully stale mock file
> 4. **10.1/11.1**: Deduplicate Wasserstein computation into `mos::math::` utility
> 5. **8.1**: Thread pool workers need top-level exception handling
> 6. **2.4**: `tick()` is passive — the kernel has no autonomous conflict-resolution loop
