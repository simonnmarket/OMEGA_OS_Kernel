"""
Métricas institucionais Tier-0 (VaR/CVaR/RAROC/Sortino/Omega/Sharpe/Calmar).
Alinhado à especificação `metrics_tier0.py` do documento Conselho; implementação
determinística (sem bootstrap aleatório por defeito).
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd


class Tier0Metrics:
    """Métricas sobre série de retornos (ex.: retornos log ou simples por período)."""

    def __init__(self, returns: pd.Series, exposure: float = 1_000_000.0) -> None:
        self.returns = pd.to_numeric(returns, errors="coerce").dropna()
        self.exposure = float(exposure)
        self.risk_free = 0.04 / 252.0

    def var_historical(self, confidence: float = 0.95) -> Dict[str, float]:
        """VaR em USD (perda na cauda esquerda) com base no quantil empírico."""
        if self.returns.empty:
            return {"var_pct": 0.0, "var_usd": 0.0}
        q = (1.0 - confidence) * 100.0
        var_pct = float(-np.percentile(self.returns.to_numpy(dtype=float), q))
        return {"var_pct": var_pct, "var_usd": var_pct * self.exposure}

    def cvar_historical(self, confidence: float = 0.95) -> float:
        """CVaR (expected shortfall) em USD na cauda esquerda."""
        if self.returns.empty:
            return 0.0
        r = self.returns.to_numpy(dtype=float)
        q = (1.0 - confidence) * 100.0
        var_threshold = float(-np.percentile(r, q))
        tail = self.returns[self.returns <= -var_threshold]
        if tail.empty:
            return 0.0
        return float(-tail.mean() * self.exposure)

    def raroc_adjusted(self, beta: float = 1.0) -> float:
        """RAROC simplificado: excesso de retorno anualizado / capital de risco."""
        if self.returns.empty:
            return 0.0
        excess_return = (float(self.returns.mean()) - self.risk_free) * 252.0
        risk_capital = self.exposure * (0.08 + float(beta) * 0.02)
        if risk_capital <= 0:
            return 0.0
        return excess_return / risk_capital * 100.0

    def sortino_ratio(self, target_return: float = 0.0) -> float:
        downside = self.returns[self.returns < target_return]
        if downside.empty:
            return 0.0
        downside_std = float(downside.std(ddof=1)) * np.sqrt(252.0) if len(downside) > 1 else 0.0
        if downside_std <= 0:
            return 0.0
        return (float(self.returns.mean()) * 252.0 - target_return) / downside_std

    def omega_ratio(self, threshold: float = 0.0) -> float:
        up = self.returns[self.returns > threshold]
        down = self.returns[self.returns < threshold]
        if up.empty or down.empty:
            return 0.0
        upside = float(up.mean())
        downside = abs(float(down.mean()))
        if downside <= 0:
            return float("inf")
        return upside / downside

    def full_analysis(self, beta: float = 1.0) -> Dict[str, Any]:
        r = self.returns
        sharpe = 0.0
        if not r.empty and float(r.std(ddof=1)) > 0:
            sharpe = (float(r.mean()) - self.risk_free) / float(r.std(ddof=1)) * np.sqrt(252.0)
        calmar = 0.0
        if not r.empty:
            eq = (1.0 + r).cumprod()
            roll_max = eq.cummax()
            dd = (eq / roll_max - 1.0).min()
            mdd = abs(float(dd)) if pd.notna(dd) else 0.0
            ann_ret = float(r.mean()) * 252.0
            if mdd > 1e-12:
                calmar = ann_ret / mdd

        return {
            "var_95": self.var_historical(0.95),
            "var_99": self.var_historical(0.99),
            "cvar_95": self.cvar_historical(0.95),
            "raroc_pct": self.raroc_adjusted(beta),
            "sortino": self.sortino_ratio(),
            "omega": self.omega_ratio(),
            "sharpe": float(sharpe),
            "calmar": float(calmar),
        }
