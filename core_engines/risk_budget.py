"""
OMEGA v4.0 — Dynamic Risk Budget Manager
==========================================
OMEGA-EXEC-20260526-TECH | CEO Mandate Gate G3

Substitui OMEGA_MAX_POS_PER_ASSET (cap fixo arbitrário) por cálculo dinâmico
baseado em equity × max_dd_pct / (ATR_pts × tick_value × lot).

Fórmula institucional:
    max_positions = floor(allowed_risk_usd / risk_per_position_usd)
    risk_per_position_usd = atr_pts × tick_value_per_point × lot

Feature flag: OMEGA_USE_RISK_BUDGET=1 (sem flag → fallback legacy)

Padrão CQO: risco escala com volatilidade, não caps arbitrários.
"""
from __future__ import annotations

import logging
import math
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

log = logging.getLogger("OMEGA.RiskBudget")

# ── Feature flag ────────────────────────────────────────────────────────────────
RISK_BUDGET_ENABLED: bool = os.getenv("OMEGA_USE_RISK_BUDGET", "0") == "1"

# ── Constantes de segurança ─────────────────────────────────────────────────────
_EPSILON = 1e-12
_MAX_HARD_CAP = int(os.getenv("OMEGA_RISK_BUDGET_HARD_CAP", "8"))  # nunca excede


@dataclass
class RiskBudgetConfig:
    """Parâmetros do orçamento de risco — 100% configuráveis via env vars."""
    max_drawdown_pct: float = float(os.getenv("OMEGA_RISK_MAX_DD_PCT", "0.02"))      # 2% equity total
    risk_per_position_pct: float = float(os.getenv("OMEGA_RISK_PER_POS_PCT", "0.005"))  # 0.5% por posição
    default_lot: float = float(os.getenv("OMEGA_LOT_BASE", "0.10"))
    atr_lookback: int = int(os.getenv("OMEGA_ATR_LOOKBACK", "14"))
    min_positions: int = 1                                                              # garante pelo menos 1 slot
    hard_cap: int = int(os.getenv("OMEGA_RISK_BUDGET_HARD_CAP", "8"))                 # hard cap configurável


@dataclass
class SymbolRiskSnapshot:
    """Snapshot de risco calculado para um símbolo em momento T."""
    symbol: str
    equity: float
    atr_pts: float
    tick_value: float
    risk_per_pos_usd: float
    allowed_risk_usd: float
    max_new_positions: int
    existing_positions: int
    available_slots: int


class RiskBudgetManager:
    """
    Gestor de orçamento de risco dinâmico.

    Substitui MAX_POS_PER_ASSET (cap fixo) por limite calculado em função de:
      - Equity da conta em tempo real
      - ATR do símbolo (volatilidade actual)
      - tick_value do broker (valor monetário por ponto)

    Usage:
        mgr = RiskBudgetManager()
        slots = mgr.available_slots("EURUSD", current_open_count=2)
        if slots > 0:
            # abrir nova posição
    """

    def __init__(self, cfg: Optional[RiskBudgetConfig] = None) -> None:
        self._cfg = cfg or RiskBudgetConfig()
        self._atr_cache: Dict[str, List[float]] = {}   # symbol → lista ATR recente
        self._last_equity: float = 0.0

    # ── Interface pública ───────────────────────────────────────────────────────

    def available_slots(
        self,
        symbol: str,
        current_positions: int,
        atr_override_pts: Optional[float] = None,
    ) -> int:
        """
        Retorna número de slots disponíveis para NOVO trade no símbolo.

        Args:
            symbol: Símbolo MT5 (ex: "EURUSD")
            current_positions: Número de posições já abertas neste símbolo
            atr_override_pts: Se fornecido, usa este ATR (pts) em vez de calcular

        Returns:
            int: slots disponíveis (≥0). 0 = não abrir mais posições.
        """
        if not RISK_BUDGET_ENABLED:
            # Modo legado: lê OMEGA_MAX_POS_PER_ASSET ou ilimitado (0)
            legacy_cap = int(os.getenv("OMEGA_MAX_POS_PER_ASSET", "0"))
            if legacy_cap == 0:
                return _MAX_HARD_CAP
            return max(0, legacy_cap - current_positions)

        snapshot = self._compute_snapshot(symbol, current_positions, atr_override_pts)
        if snapshot is None:
            log.warning("[%s] RiskBudget: MT5 indisponível — fallback legacy cap=1", symbol)
            return max(0, 1 - current_positions)

        log.info(
            "[%s] RiskBudget: equity=%.2f atr=%.1fpts risk/pos=$%.2f "
            "allowed=$%.2f max_new=%d existing=%d slots=%d",
            symbol,
            snapshot.equity,
            snapshot.atr_pts,
            snapshot.risk_per_pos_usd,
            snapshot.allowed_risk_usd,
            snapshot.max_new_positions,
            snapshot.existing_positions,
            snapshot.available_slots,
        )
        return snapshot.available_slots

    def update_atr(self, symbol: str, atr_pts: float) -> None:
        """Actualiza cache de ATR para um símbolo. Chamado pelo shadow_loop a cada ciclo."""
        if symbol not in self._atr_cache:
            self._atr_cache[symbol] = []
        self._atr_cache[symbol].append(atr_pts)
        # manter apenas lookback recente
        if len(self._atr_cache[symbol]) > self._cfg.atr_lookback:
            self._atr_cache[symbol].pop(0)

    def get_snapshot(
        self,
        symbol: str,
        current_positions: int,
        atr_override_pts: Optional[float] = None,
    ) -> Optional[SymbolRiskSnapshot]:
        """Retorna snapshot completo para auditoria/log."""
        return self._compute_snapshot(symbol, current_positions, atr_override_pts)

    # ── Lógica interna ──────────────────────────────────────────────────────────

    def _compute_snapshot(
        self,
        symbol: str,
        current_positions: int,
        atr_override_pts: Optional[float],
    ) -> Optional[SymbolRiskSnapshot]:
        try:
            import MetaTrader5 as mt5  # import local — módulo não disponível em CI
        except ImportError:
            return None

        account = mt5.account_info()
        sym_info = mt5.symbol_info(symbol)
        if account is None or sym_info is None:
            return None

        equity = account.equity
        self._last_equity = equity

        # ATR em pontos
        atr_pts = atr_override_pts or self._get_atr_pts(symbol, sym_info)
        if atr_pts <= 0:
            log.warning("[%s] RiskBudget: ATR=0 — rejeitado", symbol)
            return None

        tick_value = sym_info.trade_tick_value   # USD por tick (1 pip / 1 ponto)
        lot = self._cfg.default_lot

        # Risco monetário por posição = ATR_pts × tick_value × (lot / min_lot)
        # Para lot=0.01 (min standard): pip_value = tick_value
        # Generalizamos: risco = atr_pts × tick_value × lot / sym_info.volume_min
        volume_min = max(sym_info.volume_min, 1e-4)
        risk_per_pos_usd = atr_pts * tick_value * (lot / volume_min) * volume_min
        # Simplificado para lot fixo:
        risk_per_pos_usd = atr_pts * tick_value * lot

        allowed_risk_usd = equity * self._cfg.max_drawdown_pct
        risk_budget_per_pos = equity * self._cfg.risk_per_position_pct

        if risk_per_pos_usd < _EPSILON:
            return None

        # Max posições pelo orçamento total
        max_by_dd = math.floor(allowed_risk_usd / risk_per_pos_usd)
        # Max posições pelo limite por posição individual
        max_by_pos_budget = math.floor(risk_budget_per_pos / risk_per_pos_usd)

        # Hard cap: usa config (permite override por teste/env var)
        hard_cap = self._cfg.hard_cap
        raw_max = min(max_by_dd, max_by_pos_budget)
        if raw_max > hard_cap:
            log.warning(
                "[%s] RiskBudget HARD_CAP aplicado: raw=%d → cap=%d "
                "(equity=%.0f atr=%.1fpts risk/pos=$%.2f)",
                symbol, raw_max, hard_cap, equity, atr_pts, risk_per_pos_usd,
            )
        max_positions = max(self._cfg.min_positions, min(raw_max, hard_cap))
        available = max(0, max_positions - current_positions)

        return SymbolRiskSnapshot(
            symbol=symbol,
            equity=equity,
            atr_pts=atr_pts,
            tick_value=tick_value,
            risk_per_pos_usd=round(risk_per_pos_usd, 4),
            allowed_risk_usd=round(allowed_risk_usd, 4),
            max_new_positions=max_positions,
            existing_positions=current_positions,
            available_slots=available,
        )

    def _get_atr_pts(self, symbol: str, sym_info) -> float:
        """Calcula ATR médio em pontos do cache ou via rates MT5."""
        # Usar cache se disponível
        if symbol in self._atr_cache and self._atr_cache[symbol]:
            return sum(self._atr_cache[symbol]) / len(self._atr_cache[symbol])

        # Fallback: calcular ATR simples via rates H4
        try:
            import MetaTrader5 as mt5
            import numpy as np
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, self._cfg.atr_lookback + 1)
            if rates is None or len(rates) < 2:
                return 0.0
            highs = rates["high"]
            lows = rates["low"]
            closes = rates["close"]
            tr_list = []
            for i in range(1, len(rates)):
                tr = max(
                    highs[i] - lows[i],
                    abs(highs[i] - closes[i - 1]),
                    abs(lows[i] - closes[i - 1]),
                )
                tr_list.append(tr)
            atr_price = sum(tr_list) / len(tr_list)
            point = max(sym_info.point, _EPSILON)
            atr_pts = atr_price / point
            # popular cache
            self._atr_cache[symbol] = [atr_pts]
            return atr_pts
        except Exception as exc:
            log.warning("[%s] RiskBudget ATR calc error: %s", symbol, exc)
            return 0.0
