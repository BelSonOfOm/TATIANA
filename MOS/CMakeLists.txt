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
else()
    # Was `/std:c++17` -- MSVC syntax handed to GCC/Clang, which read it as a
    # source PATH. It broke configure before any of our code compiled (Eigen's
    # "Can't link to the standard math library" probe fails first), so the
    # project could not be built or tested on Linux at all. CMAKE_CXX_STANDARD 17
    # above already selects the standard on every compiler, so the correct
    # non-MSVC flag list is warnings only. The MSVC branch is untouched.
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra")
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
    src/core/plasticity.cpp
    src/core/semantic_skill.cpp
    src/core/thread_pool.cpp
    src/core/operad.cpp
    src/core/assembly_log.cpp
    src/core/cone_bures.cpp
    src/core/kernel.cpp
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
# winhttp exists only on Windows; the transport in colibri_kernel.cpp is guarded
# by #ifdef _WIN32 to match. Linking it unconditionally made every target
# unlinkable off Windows even after the source compiled.
if(WIN32)
    target_link_libraries(mos winhttp flatbuffers)
else()
    target_link_libraries(mos flatbuffers)
endif()
add_dependencies(mos fbs_headers)

# Create a static library for the core
add_library(mos_core STATIC ${SOURCES})
target_include_directories(mos_core PUBLIC include ${CMAKE_CURRENT_BINARY_DIR})
if(WIN32)
    target_link_libraries(mos_core PUBLIC winhttp flatbuffers)
else()
    target_link_libraries(mos_core PUBLIC flatbuffers)
endif()
add_dependencies(mos_core fbs_headers)


# --- TEST TARGETS: assertions must SURVIVE the build type -------------------
# Every test in tests/ states its expectations with assert(). CMake's Release
# and MinSizeRel configurations define NDEBUG, which compiles assert() to
# nothing -- so a Release build ran ~208 assertions as no-ops, printed its
# progress lines, exited 0, and reported PASS while verifying NOTHING. Any
# "the suite is green" claim made from a Release build was vacuous.
#
# mos_add_test undefines NDEBUG for test targets only (product code keeps the
# optimiser's NDEBUG). Use it for every new test target -- do not hand-roll
# add_executable/target_link_libraries, or the new test silently joins the
# stripped set.
function(mos_add_test target source)
    add_executable(${target} ${source})
    target_link_libraries(${target} PRIVATE mos_core)
    if(MSVC)
        target_compile_options(${target} PRIVATE /UNDEBUG)
    else()
        target_compile_options(${target} PRIVATE -UNDEBUG)
    endif()
endfunction()

# Tests
mos_add_test(mos_tests tests/test_topology.cpp)

mos_add_test(mos_homology_tests tests/test_dormant_homology.cpp)

mos_add_test(mos_algebra_tests tests/test_algebra.cpp)

mos_add_test(mos_kernel_tests tests/test_kernel.cpp)

mos_add_test(mos_fourier_tests tests/test_fourier.cpp)

mos_add_test(mos_probabilistic_tests tests/test_probabilistic.cpp)

mos_add_test(mos_curator_tests tests/test_curator.cpp)

mos_add_test(mos_reflection_tests tests/test_reflection.cpp)

mos_add_test(mos_colibri_tests tests/test_colibri.cpp)

mos_add_test(mos_knowledge_base_tests tests/test_knowledge_base.cpp)

# Parity tests: C++ CoarseComplex vs the authoritative python/coherence.py
mos_add_test(mos_coarse_complex_tests tests/test_coarse_complex.cpp)

# pi_v precision-weighted fusion (Construction 2, two-level bridge)
mos_add_test(mos_pi_fusion_tests tests/test_pi_fusion.cpp)

# 5p mechanisms (2)(3)(4): criticality, homeostasis, selectionism
mos_add_test(mos_plasticity_tests tests/test_plasticity.cpp)

# FIX-11 (operad co-schedulability) + FIX-13 (stalk noise-floor contract)
mos_add_test(mos_stalk_floor_tests tests/test_stalk_floor.cpp)

# E7: the assembly record, written at composition time
mos_add_test(mos_assembly_log_tests tests/test_assembly_log.cpp)

# confidence -> nu_v -> pi_e -> tau_f, and the w(sigma,t)/pi_e separation
mos_add_test(mos_precision_routing_tests tests/test_precision_routing.cpp)

# Phase-2 item 9: Cone-Bures (delta), with parity against python/cone_bures.py
mos_add_test(mos_cone_bures_tests tests/test_cone_bures.cpp)
