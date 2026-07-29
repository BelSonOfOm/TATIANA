#pragma once

#include <vector>
#include <cstddef>
#include <Eigen/Dense>

namespace mos {
namespace math {

/// @brief A lightweight, dense matrix class for topological and algebraic computations.
class Matrix {
public:
    /// @brief Constructor for an empty matrix.
    /// @param rows Number of rows.
    /// @param cols Number of columns.
    Matrix(size_t rows, size_t cols);

    /// @brief Access an element (mutable).
    /// @param r Row index.
    /// @param c Column index.
    /// @return Reference to the element.
    [[nodiscard]] double& at(size_t r, size_t c) noexcept;

    /// @brief Access an element (const).
    /// @param r Row index.
    /// @param c Column index.
    /// @return Value of the element.
    [[nodiscard]] double at(size_t r, size_t c) const noexcept;

    /// @brief Get number of rows.
    [[nodiscard]] size_t rows() const noexcept;

    /// @brief Get number of columns.
    [[nodiscard]] size_t cols() const noexcept;

private:
    size_t rows_;
    size_t cols_;
    std::vector<double> data_; // 1D contiguous array for cache locality
};


/// @brief Computes the eigenspectrum of a real symmetric matrix.
/// Uses Eigen's hardware-accelerated (SIMD) SelfAdjointEigenSolver. NOTE: this doc
/// comment previously claimed a hand-rolled Jacobi algorithm, which the code has
/// not used for some time — the comment was lying about the implementation.
/// @param symmetric_mat A square, real, symmetric matrix (e.g. a covariance matrix).
/// @return A std::vector of eigenvalues (variances), typically not strictly ordered.
[[nodiscard]] std::vector<double> compute_eigenspectrum(const Eigen::MatrixXd& symmetric_mat);

/// @brief Computes the numerical rank of a matrix via SVD.
/// @param mat The matrix to analyze.
/// @param tolerance The singular value threshold below which a dimension is considered zero.
/// @return The numerical rank.
[[nodiscard]] size_t compute_rank(const Matrix& mat, double tolerance = 1e-10);

} // namespace math
} // namespace mos
