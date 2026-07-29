#include "mos/math/algebra.hpp"
#include <cmath>
#include <algorithm>
#include <stdexcept>
#include <Eigen/Dense>

namespace mos {
namespace math {

Matrix::Matrix(size_t rows, size_t cols) : rows_(rows), cols_(cols), data_(rows * cols, 0.0) {}

double& Matrix::at(size_t r, size_t c) noexcept {
    return data_[r * cols_ + c];
}

double Matrix::at(size_t r, size_t c) const noexcept {
    return data_[r * cols_ + c];
}

size_t Matrix::rows() const noexcept { return rows_; }
size_t Matrix::cols() const noexcept { return cols_; }

std::vector<double> compute_eigenspectrum(const Eigen::MatrixXd& mat) {
    const size_t N = mat.rows();
    if (N != static_cast<size_t>(mat.cols())) {
        throw std::invalid_argument("Matrix must be square for Eigenvalue Algorithm.");
    }
    if (N == 0) return {};

    // Hardware accelerated SIMD eigensolver
    Eigen::SelfAdjointEigenSolver<Eigen::MatrixXd> solver(mat);
    if (solver.info() != Eigen::Success) {
        throw std::runtime_error("Eigen::SelfAdjointEigenSolver failed to converge.");
    }

    Eigen::VectorXd evals = solver.eigenvalues();
    std::vector<double> eigenvalues(N);
    for (size_t i = 0; i < N; ++i) {
        eigenvalues[i] = evals(i);
    }
    
    // Sort descending so the principal components are first
    std::sort(eigenvalues.begin(), eigenvalues.end(), std::greater<double>());
    
    return eigenvalues;
}

size_t compute_rank(const Matrix& mat, double tolerance) {
    const size_t R = mat.rows();
    const size_t C = mat.cols();
    if (R == 0 || C == 0) return 0;

    Eigen::MatrixXd eigen_mat(R, C);
    for (size_t i = 0; i < R; ++i) {
        for (size_t j = 0; j < C; ++j) {
            eigen_mat(i, j) = mat.at(i, j);
        }
    }

    Eigen::JacobiSVD<Eigen::MatrixXd> svd(eigen_mat);
    const auto& singular_values = svd.singularValues();
    size_t rank = 0;
    for (int i = 0; i < singular_values.size(); ++i) {
        if (singular_values(i) > tolerance) {
            rank++;
        }
    }
    return rank;
}

} // namespace math
} // namespace mos
