"""Métricas determinísticas (risco, PnL, regimes, clustering, institucionais)."""

from omega_dos.metrics.clustering import cluster_feature_matrix, default_feature_columns
from omega_dos.metrics.institutional import Tier0Metrics
from omega_dos.metrics.pnl import equity_from_returns, pnl_series_from_prices
from omega_dos.metrics.regimes import volatility_regime_labels
from omega_dos.metrics.risk import cvar_historical, var_historical

__all__ = [
    "var_historical",
    "cvar_historical",
    "pnl_series_from_prices",
    "equity_from_returns",
    "volatility_regime_labels",
    "cluster_feature_matrix",
    "default_feature_columns",
    "Tier0Metrics",
]
