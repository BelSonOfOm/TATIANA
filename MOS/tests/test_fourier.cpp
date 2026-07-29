#include "mos/math/fourier.hpp"
#include <iostream>
#include <cassert>
#include <cmath>

using namespace mos;

void test_fourier_mapper() {
    size_t input_dim = 3;
    size_t fourier_dim = 16;
    
    math::FourierMapper mapper(input_dim, fourier_dim, 1.0);
    
    std::vector<double> x1 = {0.5, -0.2, 0.8};
    std::vector<double> phi1 = mapper.project(x1);
    
    assert(phi1.size() == 2 * fourier_dim);
    
    // Test shift invariance / norm approx
    // The squared norm of phi1 should be exactly 1.0 because cos^2 + sin^2 = 1
    // Sum(1/d * (cos^2 + sin^2)) = Sum(1/d * 1) = 1.0
    double norm_sq = 0.0;
    for (size_t i = 0; i < phi1.size(); ++i) {
        norm_sq += phi1[i] * phi1[i];
    }
    
    assert(std::abs(norm_sq - 1.0) < 1e-6);
    
    std::cout << "test_fourier_mapper passed.\n";
}

int main() {
    test_fourier_mapper();
    return 0;
}
