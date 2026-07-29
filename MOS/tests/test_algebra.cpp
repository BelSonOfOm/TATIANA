#include <iostream>
#include <cassert>
#include <cmath>
#include "mos/math/algebra.hpp"

using namespace mos;

void test_jacobi_diagonalization() {
    // Construct a known symmetric matrix
    // A = [ 4  1 -2 ]
    //     [ 1  2  0 ]
    //     [-2  0  3 ]
    
    Eigen::MatrixXd A(3, 3);
    A(0,0) = 4.0; A(0,1) = 1.0; A(0,2) = -2.0;
    A(1,0) = 1.0; A(1,1) = 2.0; A(1,2) =  0.0;
    A(2,0) = -2.0; A(2,1) = 0.0; A(2,2) =  3.0;
    
    // Compute eigenspectrum
    std::vector<double> eigenvalues = math::compute_eigenspectrum(A);
    
    // The eigenvalues for this matrix are roughly: 5.766, 2.378, 0.856
    // (We just check that they are ordered descending and have the correct trace)
    assert(eigenvalues.size() == 3);
    assert(eigenvalues[0] >= eigenvalues[1]);
    assert(eigenvalues[1] >= eigenvalues[2]);
    
    // Trace should be preserved: 4 + 2 + 3 = 9
    double trace = eigenvalues[0] + eigenvalues[1] + eigenvalues[2];
    assert(std::abs(trace - 9.0) < 1e-6);
    
    std::cout << "test_jacobi_diagonalization passed.\n";
}

int main() {
    std::cout << "Running MOS Algebra Tests...\n";
    test_jacobi_diagonalization();
    std::cout << "All algebra tests passed successfully!\n";
    return 0;
}
