"""Séries de retorno, PnL e equity a partir de preços (determinístico)."""

from __future__ import annotations

import numpy as np
import pandas as pd


def log_returns(prices: pd.Series) -> pd.Series:
    p = pd.to_numeric(prices, errors="coerce").astype(float)
    return np.log(p / p.shift(1)).replace([np.inf, -np.inf], np.nan)


def pnl_series_from_prices(
    prices: pd.Series,
    *,
    notional: float = 1.0,
    use_log_returns: bool = True,
) -> pd.Series:
    """
    PnL incremental por período (mesma frequência que `prices`), escala linear em `notional`.

    Se use_log_returns=True: PnL_t ≈ notional * (exp(r_t) - 1) com r_t = log-return.
    """
    if use_log_returns:
        r = log_returns(prices)
        pnl = notional * (np.exp(r) - 1.0)
    else:
        simple = prices.pct_change()
        pnl = notional * simple
    return pnl.fillna(0.0)


def equity_from_returns(returns: pd.Series, *, initial: float = 1.0) -> pd.Series:
    """Curva de equity multiplicativa: E_t = initial * cumprod(1 + r_t)."""
    r = pd.to_numeric(returns, errors="coerce").fillna(0.0).astype(float)
    return initial * (1.0 + r).cumprod()
