// Small dense linear algebra for Phase 0's invariant-drift experiment.
//
// Scope note (stated, not hidden): V0's engine represented restriction maps as products of
// m=4 Householder reflections for a 96x storage win at d=384 (MATH_TOOLBOX.md I.4). Here d is
// O(3-4) and storage is not the point being tested, so restriction maps are stored as plain
// dense orthogonal matrices instead. This is a scope reduction, stated once here, not a hidden
// approximation of the same claim.
#pragma once

#include <vector>
#include <cmath>
#include <random>
#include <stdexcept>
#include <algorithm>

namespace la {

struct Mat {
    int rows = 0, cols = 0;
    std::vector<double> a;

    Mat() = default;
    Mat(int r, int c, double fill = 0.0) : rows(r), cols(c), a(static_cast<size_t>(r) * c, fill) {}

    double& operator()(int i, int j) { return a[static_cast<size_t>(i) * cols + j]; }
    double operator()(int i, int j) const { return a[static_cast<size_t>(i) * cols + j]; }

    static Mat identity(int n) {
        Mat I(n, n);
        for (int i = 0; i < n; ++i) I(i, i) = 1.0;
        return I;
    }

    Mat transpose() const {
        Mat T(cols, rows);
        for (int i = 0; i < rows; ++i)
            for (int j = 0; j < cols; ++j)
                T(j, i) = (*this)(i, j);
        return T;
    }

    Mat operator*(const Mat& o) const {
        if (cols != o.rows) throw std::runtime_error("Mat* dim mismatch");
        Mat R(rows, o.cols);
        for (int i = 0; i < rows; ++i)
            for (int k = 0; k < cols; ++k) {
                double v = (*this)(i, k);
                if (v == 0.0) continue;
                for (int j = 0; j < o.cols; ++j)
                    R(i, j) += v * o(k, j);
            }
        return R;
    }

    Mat operator+(const Mat& o) const {
        Mat R(rows, cols);
        for (size_t i = 0; i < a.size(); ++i) R.a[i] = a[i] + o.a[i];
        return R;
    }
    Mat operator-(const Mat& o) const {
        Mat R(rows, cols);
        for (size_t i = 0; i < a.size(); ++i) R.a[i] = a[i] - o.a[i];
        return R;
    }
    Mat operator*(double s) const {
        Mat R(rows, cols);
        for (size_t i = 0; i < a.size(); ++i) R.a[i] = a[i] * s;
        return R;
    }

    double frobeniusNormSq() const {
        double s = 0.0;
        for (double v : a) s += v * v;
        return s;
    }
};

inline std::vector<double> matvec(const Mat& M, const std::vector<double>& x) {
    if (M.cols != static_cast<int>(x.size())) throw std::runtime_error("matvec dim mismatch");
    std::vector<double> y(M.rows, 0.0);
    for (int i = 0; i < M.rows; ++i) {
        double s = 0.0;
        for (int j = 0; j < M.cols; ++j) s += M(i, j) * x[j];
        y[i] = s;
    }
    return y;
}

inline std::vector<double> vadd(const std::vector<double>& a, const std::vector<double>& b) {
    std::vector<double> r(a.size());
    for (size_t i = 0; i < a.size(); ++i) r[i] = a[i] + b[i];
    return r;
}
inline std::vector<double> vsub(const std::vector<double>& a, const std::vector<double>& b) {
    std::vector<double> r(a.size());
    for (size_t i = 0; i < a.size(); ++i) r[i] = a[i] - b[i];
    return r;
}
inline std::vector<double> vscale(const std::vector<double>& a, double s) {
    std::vector<double> r(a.size());
    for (size_t i = 0; i < a.size(); ++i) r[i] = a[i] * s;
    return r;
}
inline double vdot(const std::vector<double>& a, const std::vector<double>& b) {
    double s = 0.0;
    for (size_t i = 0; i < a.size(); ++i) s += a[i] * b[i];
    return s;
}
inline double vnorm(const std::vector<double>& a) { return std::sqrt(vdot(a, a)); }

inline Mat outer(const std::vector<double>& a, const std::vector<double>& b) {
    Mat R(static_cast<int>(a.size()), static_cast<int>(b.size()));
    for (size_t i = 0; i < a.size(); ++i)
        for (size_t j = 0; j < b.size(); ++j)
            R(static_cast<int>(i), static_cast<int>(j)) = a[i] * b[j];
    return R;
}

// Gauss-Jordan inverse with partial pivoting. d is small (<=6) throughout this experiment.
inline Mat inverse(Mat M) {
    int n = M.rows;
    if (M.cols != n) throw std::runtime_error("inverse: not square");
    Mat A = M;
    Mat I = Mat::identity(n);
    for (int col = 0; col < n; ++col) {
        int piv = col;
        double best = std::fabs(A(col, col));
        for (int r = col + 1; r < n; ++r) {
            double v = std::fabs(A(r, col));
            if (v > best) { best = v; piv = r; }
        }
        if (best < 1e-14) throw std::runtime_error("inverse: singular to working precision");
        if (piv != col) {
            for (int j = 0; j < n; ++j) { std::swap(A(col, j), A(piv, j)); std::swap(I(col, j), I(piv, j)); }
        }
        double d = A(col, col);
        for (int j = 0; j < n; ++j) { A(col, j) /= d; I(col, j) /= d; }
        for (int r = 0; r < n; ++r) {
            if (r == col) continue;
            double f = A(r, col);
            if (f == 0.0) continue;
            for (int j = 0; j < n; ++j) { A(r, j) -= f * A(col, j); I(r, j) -= f * I(col, j); }
        }
    }
    return I;
}

// Polar decomposition's orthogonal factor via Newton's iteration: X_{k+1} = (X_k + (X_k^-1)^T)/2.
// Quadratically convergent; input here always starts within a small gamma_0 step of an
// already-orthogonal matrix (the consolidation blend), so ~20 iterations is generous headroom,
// not a tuned-for-this-run constant.
inline Mat polarOrthogonal(const Mat& M, int maxIters = 20, double tol = 1e-13) {
    Mat X = M;
    for (int it = 0; it < maxIters; ++it) {
        Mat Xinv = inverse(X);
        Mat Xnext = (X + Xinv.transpose()) * 0.5;
        double diff = (Xnext - X).frobeniusNormSq();
        X = Xnext;
        if (diff < tol * tol) break;
    }
    return X;
}

// Haar-ish random orthogonal matrix via Gram-Schmidt QR of a random Gaussian matrix.
// forceRotation=true flips the sign of the last column if det<0, forcing det=+1 (SO(d)) --
// used for the cycle whose stalks are odd-dimensional, so every element of SO(odd) has a fixed
// eigenvalue-1 axis (MATH_TOOLBOX.md III.3's "structural surprise"), making a genuine growth
// address reachable by construction rather than by luck.
inline Mat randomOrthogonal(int d, std::mt19937& rng, bool forceRotation = false) {
    std::normal_distribution<double> nd(0.0, 1.0);
    Mat G(d, d);
    for (auto& v : G.a) v = nd(rng);
    // Gram-Schmidt columns of G -> orthonormal columns Q
    Mat Q(d, d);
    for (int j = 0; j < d; ++j) {
        std::vector<double> v(d);
        for (int i = 0; i < d; ++i) v[i] = G(i, j);
        for (int k = 0; k < j; ++k) {
            std::vector<double> qk(d);
            for (int i = 0; i < d; ++i) qk[i] = Q(i, k);
            double proj = vdot(qk, v);
            for (int i = 0; i < d; ++i) v[i] -= proj * qk[i];
        }
        double n = vnorm(v);
        if (n < 1e-12) { v.assign(d, 0.0); v[j] = 1.0; n = 1.0; } // degenerate draw, replace with axis
        for (int i = 0; i < d; ++i) Q(i, j) = v[i] / n;
    }
    if (forceRotation) {
        // determinant sign via Gaussian elimination on a copy (small d, cheap)
        Mat A = Q;
        double det = 1.0;
        for (int col = 0; col < d; ++col) {
            int piv = col;
            double best = std::fabs(A(col, col));
            for (int r = col + 1; r < d; ++r) { double v = std::fabs(A(r, col)); if (v > best) { best = v; piv = r; } }
            if (piv != col) { for (int j = 0; j < d; ++j) std::swap(A(col, j), A(piv, j)); det = -det; }
            double dpiv = A(col, col);
            det *= dpiv;
            if (std::fabs(dpiv) < 1e-14) break;
            for (int r = col + 1; r < d; ++r) {
                double f = A(r, col) / dpiv;
                for (int j = 0; j < d; ++j) A(r, j) -= f * A(col, j);
            }
        }
        if (det < 0) for (int i = 0; i < d; ++i) Q(i, d - 1) = -Q(i, d - 1);
    }
    return Q;
}

// Classic cyclic Jacobi eigenvalue algorithm for a real symmetric matrix.
// Returns eigenvalues in `eigvals` and eigenvectors as columns of `eigvecs`.
inline void jacobiEigenSymmetric(Mat A, std::vector<double>& eigvals, Mat& eigvecs,
                                  int maxSweeps = 100, double tol = 1e-13) {
    int n = A.rows;
    Mat V = Mat::identity(n);
    for (int sweep = 0; sweep < maxSweeps; ++sweep) {
        double off = 0.0;
        for (int p = 0; p < n; ++p)
            for (int q = p + 1; q < n; ++q) off += A(p, q) * A(p, q);
        if (off < tol * tol) break;
        for (int p = 0; p < n; ++p) {
            for (int q = p + 1; q < n; ++q) {
                if (std::fabs(A(p, q)) < 1e-300) continue;
                double theta = (A(q, q) - A(p, p)) / (2.0 * A(p, q));
                double t = (theta >= 0 ? 1.0 : -1.0) / (std::fabs(theta) + std::sqrt(theta * theta + 1.0));
                double c = 1.0 / std::sqrt(t * t + 1.0);
                double s = t * c;
                double app = A(p, p), aqq = A(q, q), apq = A(p, q);
                A(p, p) = c * c * app - 2 * s * c * apq + s * s * aqq;
                A(q, q) = s * s * app + 2 * s * c * apq + c * c * aqq;
                A(p, q) = A(q, p) = 0.0;
                for (int i = 0; i < n; ++i) {
                    if (i == p || i == q) continue;
                    double aip = A(i, p), aiq = A(i, q);
                    A(i, p) = A(p, i) = c * aip - s * aiq;
                    A(i, q) = A(q, i) = s * aip + c * aiq;
                }
                for (int i = 0; i < n; ++i) {
                    double vip = V(i, p), viq = V(i, q);
                    V(i, p) = c * vip - s * viq;
                    V(i, q) = s * vip + c * viq;
                }
            }
        }
    }
    eigvals.resize(n);
    for (int i = 0; i < n; ++i) eigvals[i] = A(i, i);
    eigvecs = V;
}

} // namespace la
