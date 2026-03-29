"""Referência V8.2.1: OLS na janela [i-w, i) e Z com EWMA.shift(1)."""

import numpy as np
import pandas as pd

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from v821_batch import rolling_ols_spread, causal_z_ewma_shift1, v821_causal_spread_and_z


def test_rolling_spread_uses_only_past_window():
    n = 30
    window = 10
    y = np.arange(n, dtype=float)
    x = np.ones(n)
    sp = rolling_ols_spread(y, x, window)
    assert np.isnan(sp[:window]).all()
    i = window
    wy = y[i - window : i]
    wx = x[i - window : i]
    X = np.column_stack([np.ones(window), wx])
    theta, _, _, _ = np.linalg.lstsq(X, wy, rcond=None)
    manual = y[i] - (theta[0] + theta[1] * x[i])
    np.testing.assert_allclose(sp[i], manual)


def test_causal_z_matches_explicit_shift1_formula():
    """Z deve coincidir com (s - ewm_mean.shift(1)) / (ewm_std.shift(1) + eps)."""
    spread = np.array([0.0, 1.0, -0.5, 2.0, 1.5, 0.2, -1.0, 3.0], dtype=float)
    span = 4
    eps = 1e-10
    s = pd.Series(spread)
    ewm = s.ewm(span=span, adjust=False)
    mu_s = ewm.mean().shift(1)
    sig_s = ewm.std().shift(1)
    expected = ((s - mu_s) / (sig_s + eps)).values
    got = causal_z_ewma_shift1(spread, ewma_span=span, eps=eps)
    np.testing.assert_allclose(got, expected, rtol=1e-12, atol=1e-12, equal_nan=True)


def test_z_differs_from_contemporaneous_ewma_when_series_moves():
    """Com shift(1), Z não coincide com normalização pela média EWMA do mesmo instante."""
    spread = np.linspace(0.0, 10.0, 40)
    span = 8
    eps = 1e-10
    z_causal = causal_z_ewma_shift1(spread, ewma_span=span, eps=eps)
    s = pd.Series(spread)
    ewm = s.ewm(span=span, adjust=False)
    z_contemp = ((s - ewm.mean()) / (ewm.std() + eps)).values
    ok = np.isfinite(z_causal) & np.isfinite(z_contemp)
    assert ok.sum() > 5
    assert not np.allclose(z_causal[ok], z_contemp[ok], rtol=1e-2, atol=1e-2)


def test_v821_pipeline_matches_components():
    rng = np.random.default_rng(1)
    n = 120
    y = rng.normal(size=n)
    x = rng.normal(size=n)
    w, span = 25, 15
    spread, z = v821_causal_spread_and_z(y, x, window_ols=w, ewma_span=span)
    sp2 = rolling_ols_spread(y, x, w)
    z2 = causal_z_ewma_shift1(sp2, ewma_span=span)
    np.testing.assert_allclose(spread, sp2, rtol=0, atol=0, equal_nan=True)
    np.testing.assert_allclose(z, z2, rtol=0, atol=0, equal_nan=True)
