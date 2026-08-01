"""Tests for the alive-mask and the calibrated T1 threshold.

The mask tests are the ones that matter most, because a mask bug is silent: it
does not crash, it just shifts theta, and the shift looks exactly like the
finding it would be corrupting ("organs stopped recruiting new concepts").
"""
import sys, os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cover import (NoisyOr, Mixture, alive_mask, fit_noisy_or, fit_mixture,
                   generate_noisy_or, calibrated_compare, LEAK_RATE,
                   _noisy_or_row_loglik, _mixture_row_loglik)


def test_all_alive_mask_is_a_no_op():
    """An all-ones mask must reproduce the unmasked numbers EXACTLY, or every
    existing result silently changed meaning when the mask landed."""
    X, truth = generate_noisy_or(N=12, K=2, T=200, seed=1)
    ones = np.ones_like(X)

    assert np.allclose(_noisy_or_row_loglik(X, truth.theta, truth.pi),
                       _noisy_or_row_loglik(X, truth.theta, truth.pi, ones))
    mix = Mixture(p=np.full((12, 2), 0.3), w=np.array([0.5, 0.5]))
    assert np.allclose(_mixture_row_loglik(X, mix.p, mix.w),
                       _mixture_row_loglik(X, mix.p, mix.w, ones))

    a = fit_noisy_or(X, K=2, seed=0)
    b = fit_noisy_or(X, K=2, seed=0, mask=ones)
    assert np.allclose(a.theta, b.theta) and np.allclose(a.pi, b.pi)
    c = fit_mixture(X, K=2, seed=0)
    d = fit_mixture(X, K=2, seed=0, mask=ones)
    assert np.allclose(c.p, d.p) and np.allclose(c.w, d.w)
    print("  all-alive mask is exactly a no-op")


def test_dead_concept_contributes_nothing():
    """A column that is masked off everywhere must not move the likelihood."""
    rng = np.random.default_rng(0)
    X, truth = generate_noisy_or(N=12, K=2, T=150, seed=2)

    # Append a 13th concept that never existed, with arbitrary junk in its column.
    Xbig = np.concatenate([X, rng.integers(0, 2, size=(X.shape[0], 1)).astype(float)], axis=1)
    Mbig = np.ones_like(Xbig)
    Mbig[:, -1] = 0.0                       # never alive

    theta_big = np.vstack([truth.theta, rng.uniform(0.1, 0.9, size=(1, 2))])
    ll_small = _noisy_or_row_loglik(X, truth.theta, truth.pi)
    ll_big = _noisy_or_row_loglik(Xbig, theta_big, truth.pi, Mbig)
    assert np.allclose(ll_small, ll_big), np.abs(ll_small - ll_big).max()
    print("  a never-alive concept contributes exactly zero, whatever its theta")


def test_mask_removes_the_late_birth_bias():
    """THE POINT OF THE MASK.

    Build data where every concept has the SAME true recruitment rate, but half
    of them are born late. Unmasked, the late half must look weaker purely
    because their pre-birth silence is scored. Masked, the two halves must agree.
    """
    rng = np.random.default_rng(7)
    N, K, T = 16, 2, 1200
    theta = np.full((N, K), 0.35)          # identical for every concept
    pi = np.full(K, 0.4)

    Z = (rng.random((T, K)) < pi).astype(float)
    drive = LEAK_RATE + Z @ (-np.log1p(-theta)).T
    X = (rng.random((T, N)) < -np.expm1(-drive)).astype(float)

    birth = [0] * (N // 2) + [T // 2] * (N // 2)      # half born halfway through
    M = alive_mask(birth, T, N)
    X = X * M                                         # unborn concepts cannot fire

    early, late = slice(0, N // 2), slice(N // 2, N)

    naive = fit_noisy_or(X, K, seed=0).theta.mean(axis=1)
    masked = fit_noisy_or(X, K, seed=0, mask=M).theta.mean(axis=1)

    naive_gap = naive[early].mean() - naive[late].mean()
    masked_gap = masked[early].mean() - masked[late].mean()
    print(f"  early-vs-late theta gap: unmasked {naive_gap:+.4f}, masked {masked_gap:+.4f}")

    # Unmasked, late concepts look substantially weaker than identical early ones.
    assert naive_gap > 0.05, f"expected a clear unmasked bias, got {naive_gap:+.4f}"
    # Masked, the bias is largely removed.
    assert abs(masked_gap) < naive_gap / 2, (
        f"mask failed to remove the bias: {masked_gap:+.4f} vs {naive_gap:+.4f}")
    print("  mask removes the late-birth bias")


def test_alive_mask_shape_and_validation():
    M = alive_mask([0, 2, 5], T=6, n_concepts=3)
    assert M.shape == (6, 3)
    assert M[0].tolist() == [1.0, 0.0, 0.0]
    assert M[5].tolist() == [1.0, 1.0, 1.0]
    try:
        alive_mask([0, 1], T=4, n_concepts=3)
        raise AssertionError("should have refused a wrong-length birth_tick")
    except ValueError:
        pass
    print("  alive_mask builds and validates correctly")


def test_calibrated_p_value_bounds():
    """p is in (0, 1] and never exactly 0 -- B draws cannot support more."""
    X, _ = generate_noisy_or(N=12, K=2, T=250, seed=5)
    res = calibrated_compare(X, K=2, n_folds=4, B=9, seed=0)
    assert 0.0 < res.p_value <= 1.0
    assert res.p_value >= 1.0 / (1 + 9) - 1e-12
    assert len(res.null) == 9
    print(f"  calibrated_compare runs; p={res.p_value:.3f}, "
          f"excess={res.excess_over_null:+.4f}")


if __name__ == "__main__":
    for fn in (test_all_alive_mask_is_a_no_op,
               test_dead_concept_contributes_nothing,
               test_alive_mask_shape_and_validation,
               test_mask_removes_the_late_birth_bias,
               test_calibrated_p_value_bounds):
        print(fn.__name__)
        fn()
    print("\nall mask/calibration tests passed")
