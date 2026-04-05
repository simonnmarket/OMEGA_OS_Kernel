"""
VaR / CVaR histórico — sem simulação Monte Carlo aleatória.

Implementação determinística: quantis empíricos sobre série de retornos/PnL.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def var_historical(
    series: pd.Series | np.ndarray,
    *,
    alpha: float = 0.05,
    side: str = "loss",
) -> float:
    """
    VaR histórico ao nível alpha (ex.: 0.05 = 5% cauda).

    side='loss': retorna o quantil inferior (perdas); valores em unidades da série de entrada.
    """
    if not (0 < alpha < 0.5):
        raise ValueError("alpha deve estar em (0, 0.5)")
    x = np.asarray(pd.Series(series).dropna(), dtype=float)
    if x.size < 2:
        return float("nan")
    q = np.quantile(x, alpha)
    if side == "loss":
        return float(q)
    if side == "gain":
        return float(np.quantile(x, 1.0 - alpha))
    raise ValueError("side deve ser 'loss' ou 'gain'")


def cvar_historical(
    series: pd.Series | np.ndarray,
    *,
    alpha: float = 0.05,
    side: str = "loss",
) -> float:
    """CVaR (Expected Shortfall) histórico — média da cauda além do VaR."""
    if not (0 < alpha < 0.5):
        raise ValueError("alpha deve estar em (0, 0.5)")
    x = np.asarray(pd.Series(series).dropna(), dtype=float)
    if x.size < 2:
        return float("nan")
    q = np.quantile(x, alpha)
    if side == "loss":
        tail = x[x <= q]
        return float(np.mean(tail)) if tail.size else float(q)
    if side == "gain":
        q_up = np.quantile(x, 1.0 - alpha)
        tail = x[x >= q_up]
        return float(np.mean(tail)) if tail.size else float(q_up)
    raise ValueError("side deve ser 'loss' ou 'gain'")
