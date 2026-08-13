cmake_minimum_required(VERSION 3.14)
project(MOS_TopologicalCore VERSION 1.0.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
set(VCPKG_APPLOCAL_DEPS OFF)
add_compile_definitions(NOMINMAX WIN32_LEAN_AND_MEAN)
if(MSVC)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /W4 /std:c++17 /permissive- /Zc:__cplusplus")
    # Suppress some verbose warnings in 3rd party code if needed
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /wd4127 /wd4505 /wd4714")
    # cone_stalk.cpp exceeds COFF's 65279-section limit in Debug: Eigen expands a
    # separate section per instantiated template, and Construction 6 instantiates
    # a lot of them. Not a size optimisation -- without this the object file
    # cannot be emitted at all (C1128), so mos_core and every test that links it
    # fail to build.
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /bigobj")
else()
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /std:c++17")
endif()

# Add include directories
include_directories(include)
include_directories(vendor/sqlite)
include_directories(vendor/nlohmann)

include(FetchContent)
FetchContent_Declare(
  flatbuffers
  GIT_REPOSITORY https://github.com/google/flatbuffers.git
  GIT_TAG        v23.5.26
)
# FlatBuffers options
set(FLATBUFFERS_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(FLATBUFFERS_BUILD_FLATC ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(flatbuffers)

# Fetch Eigen for SIMD vectorization
FetchContent_Declare(
  eigen
  GIT_REPOSITORY https://gitlab.com/libeigen/eigen.git
  GIT_TAG        3.4.0
)
FetchContent_MakeAvailable(eigen)
include_directories(${eigen_SOURCE_DIR})

# Generate C++ headers from FlatBuffers schema
set(FBS_FILES proto/operad.fbs)
build_flatbuffers("${FBS_FILES}" "" fbs_headers "" "" "" "")

# Include the generated headers directory
include_directories(${CMAKE_CURRENT_BINARY_DIR})

# Gather source files
set(SOURCES
    src/topology/simplex.cpp
    src/topology/chain.cpp
    src/topology/complex.cpp
    src/dormant/boundary_matrix.cpp
    src/dormant/homology.cpp
    src/math/algebra.cpp
    src/math/fourier.cpp
    src/core/cognitive_state.cpp
    src/core/coarse_complex.cpp
    src/core/edge_precision.cpp
    src/core/hodge.cpp
    src/core/curvature.cpp
    src/core/instantiate.cpp
    src/core/two_complex.cpp
    src/core/concept_store.cpp
    src/core/coning.cpp
    src/core/cone_stalk.cpp
    src/core/rank_k_stalk.cpp
    src/core/householder.cpp
    src/core/plasticity.cpp
    src/core/semantic_skill.cpp
    src/core/thread_pool.cpp
    src/core/operad.cpp
    src/core/kernel.cpp
    src/core/assembly_log.cpp
    src/core/reflection.cpp
    src/core/knowledge_curator.cpp
    src/operators/edge_contraction.cpp
    src/operators/expansion.cpp
    src/operators/edge_expansion.cpp
    src/operators/primitives.cpp
    src/translation/curator.cpp
    src/translation/knowledge_base.cpp
    src/translation/colibri_kernel.cpp
    vendor/sqlite/sqlite3.c
)

add_executable(mos src/main.cpp ${SOURCES})
target_include_directories(mos PUBLIC include ${CMAKE_CURRENT_BINARY_DIR})
target_link_libraries(mos winhttp flatbuffers)
add_dependencies(mos fbs_headers)

# Create a static library for the core
add_library(mos_core STATIC ${SOURCES})
target_include_directories(mos_core PUBLIC include ${CMAKE_CURRENT_BINARY_DIR})
target_link_libraries(mos_core PUBLIC winhttp flatbuffers)
add_dependencies(mos_core fbs_headers)

# Tests
add_executable(mos_tests tests/test_topology.cpp)
target_link_libraries(mos_tests PRIVATE mos_core)

add_executable(mos_homology_tests tests/test_dormant_homology.cpp)
target_link_libraries(mos_homology_tests PRIVATE mos_core)

add_executable(mos_algebra_tests tests/test_algebra.cpp)
target_link_libraries(mos_algebra_tests PRIVATE mos_core)

add_executable(mos_kernel_tests tests/test_kernel.cpp)
target_link_libraries(mos_kernel_tests PRIVATE mos_core)

add_executable(mos_fourier_tests tests/test_fourier.cpp)
target_link_libraries(mos_fourier_tests PRIVATE mos_core)

add_executable(mos_probabilistic_tests tests/test_probabilistic.cpp)
target_link_libraries(mos_probabilistic_tests PRIVATE mos_core)

add_executable(mos_curator_tests tests/test_curator.cpp)
target_link_libraries(mos_curator_tests PRIVATE mos_core)

add_executable(mos_reflection_tests tests/test_reflection.cpp)
target_link_libraries(mos_reflection_tests PRIVATE mos_core)

add_executable(mos_colibri_tests tests/test_colibri.cpp)
target_link_libraries(mos_colibri_tests PRIVATE mos_core)

add_executable(mos_knowledge_base_tests tests/test_knowledge_base.cpp)
target_link_libraries(mos_knowledge_base_tests PRIVATE mos_core)

# Parity tests: C++ CoarseComplex vs the authoritative python/coherence.py
add_executable(mos_coarse_complex_tests tests/test_coarse_complex.cpp)
target_link_libraries(mos_coarse_complex_tests PRIVATE mos_core)

# pi_v precision-weighted fusion (Construction 2, two-level bridge)
add_executable(mos_pi_fusion_tests tests/test_pi_fusion.cpp)
target_link_libraries(mos_pi_fusion_tests PRIVATE mos_core)

# 5p mechanisms (2)(3)(4): criticality, homeostasis, selectionism
add_executable(mos_plasticity_tests tests/test_plasticity.cpp)
target_link_libraries(mos_plasticity_tests PRIVATE mos_core)

# FIX-11 (operad co-schedulability) + FIX-13 (stalk noise-floor contract)
add_executable(mos_stalk_floor_tests tests/test_stalk_floor.cpp)
target_link_libraries(mos_stalk_floor_tests PRIVATE mos_core)

# P1: the DAG can name what it acts on. Uses the REAL primitives, not a stub --
# the co-schedulability rule was always correct, but the operators never reached
# it with anything to say, which a StubOp-based suite cannot detect.
add_executable(mos_p1_support_tests tests/test_p1_support.cpp)
target_link_libraries(mos_p1_support_tests PRIVATE mos_core)

# E7 assembly recording. The signature cases here are shared with
# python/check_signature_parity.py — if the two implementations drift, every
# recurrence count is silently wrong while every other test still passes.
# Phase-2 item 1: Householder restriction maps
# Phase-2 item 2: Hodge split via LSQR. Expected values are hard-coded from
# python/hodge.py so the two implementations cannot drift together.
add_executable(mos_hodge_tests tests/test_hodge.cpp)
target_link_libraries(mos_hodge_tests PRIVATE mos_core)

# Phase-2 item 8: rank-k SPD stalks. Checks Woodbury against a dense solve and
# that orthogonal congruence preserves form, trace and spectrum.
add_executable(mos_rank_k_stalk_tests tests/test_rank_k_stalk.cpp)
target_link_libraries(mos_rank_k_stalk_tests PRIVATE mos_core)

# Phase-2 item 7: coning off cycles. Measures that it kills exactly one class,
# and that the rejected chord alternative makes b1 WORSE.
add_executable(mos_coning_tests tests/test_coning.cpp)
target_link_libraries(mos_coning_tests PRIVATE mos_core)

# The growth law's COST side (DERIVATION_MDL_GROWTH_LAW.md 2.1, 5.10a, 5.11).
# F(w) = ker(Hol - I) by the holonomy route, the propagated legs that make k-1 of
# them free, and the per-direction MDL threshold. C++ mirror of
# python/validate_growth_law.py.
add_executable(mos_cone_stalk_tests tests/test_cone_stalk.cpp)
target_link_libraries(mos_cone_stalk_tests PRIVATE mos_core)

# Phase-2 items 5 & 6: the K/W adjunction (i^* i_! = id) and gamma(nu).
add_executable(mos_two_complex_tests tests/test_two_complex.cpp)
target_link_libraries(mos_two_complex_tests PRIVATE mos_core)

# Phase 3 stage 0: what a tick publishes -- nu for gamma_nu, and the
# co-activation record Construction 5 is fitted to. Both used to be discarded.
add_executable(mos_tick_record_tests tests/test_tick_record.cpp)
target_link_libraries(mos_tick_record_tests PRIVATE mos_core)

# Phase 3 stage 3a: the CognitiveState <-> Complex2 bridge, and the even-parity
# learning rule without which crystallise refuses and Q(t) never leaves zero.
add_executable(mos_concept_store_tests tests/test_concept_store.cpp)
target_link_libraries(mos_concept_store_tests PRIVATE mos_core)

# Phase 3 stage 3b: the loop closed end-to-end through execute_dag. Q(t) leaving
# zero is the first evidence the engine consolidates rather than merely runs.
add_executable(mos_consolidation_tests tests/test_consolidation_loop.cpp)
target_link_libraries(mos_consolidation_tests PRIVATE mos_core)

# Phase-2 item 4: PPR instantiation. The ACL size-independence claim is measured.
add_executable(mos_instantiate_tests tests/test_instantiate.cpp)
target_link_libraries(mos_instantiate_tests PRIVATE mos_core)

# Phase-2 item 3: F_MOS curvature + the control-barrier flow that replaces w_floor.
add_executable(mos_curvature_tests tests/test_curvature.cpp)
target_link_libraries(mos_curvature_tests PRIVATE mos_core)

add_executable(mos_householder_tests tests/test_householder.cpp)
target_link_libraries(mos_householder_tests PRIVATE mos_core)

add_executable(mos_assembly_log_tests tests/test_assembly_log.cpp)
target_link_libraries(mos_assembly_log_tests PRIVATE mos_core)
# The end-to-end case builds a real FlatBuffers DAG, so it needs the generated
# header rather than only what mos_core exposes.
add_dependencies(mos_assembly_log_tests fbs_headers)
