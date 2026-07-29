#include <iostream>
#include <cassert>
#include "mos/topology/simplex.hpp"
#include "mos/topology/chain.hpp"
#include "mos/topology/complex.hpp"
#include "mos/core/cognitive_state.hpp"
#include "mos/operators/edge_contraction.hpp"

using namespace mos;

void test_simplex_and_chain() {
    topology::Simplex s1({3, 1, 2}); // Will be sorted to 1, 2, 3
    assert(s1.dimension() == 2);
    assert(s1.get_vertices()[0] == 1);
    
    topology::Chain c;
    c.add(s1, 1);
    assert(c.get_elements().size() == 1);
    
    topology::Chain c2;
    c2.add(s1, -1);
    c.add(c2);
    assert(c.get_elements().empty()); // 1 + (-1) = 0, should be erased
    
    std::cout << "test_simplex_and_chain passed.\n";
}

void test_complex_boundary() {
    topology::Simplex triangle({1, 2, 3});
    topology::Chain boundary = topology::SimplicialComplex::boundary(triangle);
    
    // [1,2,3] boundary should be [2,3] - [1,3] + [1,2]
    const auto& elements = boundary.get_elements();
    assert(elements.size() == 3);
    assert(elements.at(topology::Simplex({2, 3})) == 1);
    assert(elements.at(topology::Simplex({1, 3})) == -1);
    assert(elements.at(topology::Simplex({1, 2})) == 1);

    std::cout << "test_complex_boundary passed.\n";
}

void test_edge_contraction() {
    core::CognitiveState state;
    topology::Simplex edge1({1, 2});
    topology::Simplex edge2({2, 3});
    
    state.get_complex().insert(edge1);
    state.get_complex().insert(edge2);
    
    assert(state.get_complex().contains(topology::Simplex({2})));
    
    // Contract vertex 2 into vertex 1
    operators::EdgeContractionOperator op(1, 2);
    bool mutated = op.apply(state);
    
    assert(mutated);
    
    // Vertex 2 should be gone.
    assert(!state.get_complex().contains(topology::Simplex({2})));
    
    // Edge {2,3} should have become {1,3}
    assert(state.get_complex().contains(topology::Simplex({1, 3})));
    
    // Edge {1,2} should have collapsed to {1}
    assert(state.get_complex().contains(topology::Simplex({1})));
    
    std::cout << "test_edge_contraction passed.\n";
}

void test_boundary_of_boundary() {
    // The fundamental lemma of homology: d_{n-1} o d_n = 0
    topology::Simplex tetra({1, 2, 3, 4}); // 3-simplex
    
    topology::Chain b1 = topology::SimplicialComplex::boundary(tetra);
    topology::Chain b2 = topology::SimplicialComplex::boundary(b1);
    
    assert(b2.is_empty());
    std::cout << "test_boundary_of_boundary (d^2 = 0) passed.\n";
}

int main() {
    std::cout << "Running MOS Core Tests...\n";
    test_simplex_and_chain();
    test_complex_boundary();
    test_edge_contraction();
    test_boundary_of_boundary();
    std::cout << "All tests passed successfully!\n";
    return 0;
}
