"""
Referência batch para especificação OMEGA V8.2.1 (spread causal por janela OLS + Z com EWMA shift(1)).

- Para cada índice i >= window: β, α estimados só com dados [i-window, i) (exclui i).
- Spread_i = y_i - (α + β x_i).
- μ_i, σ_i = EWMA(span) sobre série de spreads; Z_i = (spread_i - μ_{i|i-1}) / (σ_{i|i-1}+ε)
  com μ_{i|i-1} = ewma_mean.shift(1), idem std (pandas adjust=False alinha com motor documentado).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def rolling_ols_spread(
    y: np.ndarray,
    x: np.ndarray,
    window: int,
) -> np.ndarray:
    y = np.asarray(y, dtype=float).ravel()
    x = np.asarray(x, dtype=float).ravel()
    n = len(y)
    spread = np.full(n, np.nan)
    for i in range(window, n):
        wy = y[i - window : i]
        wx = x[i - window : i]
        X = np.column_stack([np.ones(window), wx])
        theta, _, _, _ = np.linalg.lstsq(X, wy, rcond=None)
        alpha, beta = theta[0], theta[1]
        spread[i] = y[i] - (alpha + beta * x[i])
    return spread


def causal_z_ewma_shift1(spread: np.ndarray, ewma_span: int, eps: float = 1e-10) -> np.ndarray:
    s = pd.Series(spread)
    ewm = s.ewm(span=ewma_span, adjust=False)
    mu_t1 = ewm.mean().shift(1)
    sig_t1 = ewm.std().shift(1)
    z = (s - mu_t1) / (sig_t1 + eps)
    return z.values


def v821_causal_spread_and_z(
    y: np.ndarray,
    x: np.ndarray,
    window_ols: int = 500,
    ewma_span: int = 100,
    eps: float = 1e-10,
) -> tuple[np.ndarray, np.ndarray]:
    spread = rolling_ols_spread(y, x, window_ols)
    z = causal_z_ewma_shift1(spread, ewma_span, eps=eps)
    return spread, z
