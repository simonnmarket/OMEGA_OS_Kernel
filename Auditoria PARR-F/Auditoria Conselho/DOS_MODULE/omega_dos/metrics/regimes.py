"""
Regimes de volatilidade — labels determinísticos por quantis da vol rolling.

Sem cadeias de Markov estocásticas: `pd.qcut` em volatilidade rolling para buckets
aproximadamente equipopulados (reproduzível para a mesma série).
"""

from __future__ import annotations

import pandas as pd


def rolling_volatility(series: pd.Series, *, window: int = 20) -> pd.Series:
    """Volatilidade rolling dos retornos simples (std amostral, ddof=1)."""
    s = pd.to_numeric(series, errors="coerce").astype(float)
    r = s.pct_change()
    min_p = max(3, window // 4)
    return r.rolling(window, min_periods=min_p).std()


def volatility_regime_labels(
    price_or_level: pd.Series,
    *,
    window: int = 20,
    n_regimes: int = 3,
) -> pd.Series:
    """
    Atribui inteiros 0..K-1 com base em quantis da volatilidade rolling (baixo→alto).

    Usa `pd.qcut` quando possível; se dados repetidos impedem qcut, recorre a `pd.cut` linear.
    """
    if n_regimes < 2:
        raise ValueError("n_regimes deve ser >= 2")
    vol = rolling_volatility(price_or_level, window=window)
    v = vol.dropna()
    if v.empty or len(v) < n_regimes:
        return pd.Series(index=price_or_level.index, dtype="Int64")

    try:
        cats = pd.qcut(v, q=n_regimes, labels=False, duplicates="drop")
    except ValueError:
        cats = pd.cut(v, bins=n_regimes, labels=False, duplicates="drop")
    out = cats.astype("Int64")
    return out.reindex(price_or_level.index)
