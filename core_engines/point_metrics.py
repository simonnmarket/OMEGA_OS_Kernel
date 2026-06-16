"""
OMEGA v4.0 — Point Metric Engine
==================================
OMEGA-EXEC-20260526-TECH | CEO Mandate Gate G2

Centraliza TODA a lógica de medição de distância/PnL em PONTOS MT5 nativos.
USD é calculado APENAS para reconciliação final — NUNCA como unidade de distância.

Regra CEO: 95%+ dos logs de distância devem usar "pts". Qualquer "USD" como
distância é FAIL no gate de auditoria.

Auditoria: cada evento é gravado em JSONL com campo "unit": "points".
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger("OMEGA.PointMetrics")

# ── Paths de auditoria ──────────────────────────────────────────────────────────
_AUDIT_DIR = Path(os.getenv("OMEGA_AUDIT_DIR", "audit/paper"))
_POINT_LOG = _AUDIT_DIR / "point_metrics_trace.jsonl"

# ── Epsilon ─────────────────────────────────────────────────────────────────────
_EPSILON = 1e-12


class PointMetricEngine:
    """
    Motor de métricas em pontos MT5.

    Todos os métodos são STATELESS (classmethods/staticmethods).
    Instanciar apenas para configurar path de auditoria customizado.

    CRITICAL: Nenhum método desta classe retorna "distância em USD".
    USD aparece apenas em usd_context (campo separado, jamais "dist").
    """

    def __init__(self, audit_path: Optional[Path] = None) -> None:
        self._audit_path = audit_path or _POINT_LOG
        self._audit_path.parent.mkdir(parents=True, exist_ok=True)

    # ── Conversão de preço para pontos ─────────────────────────────────────────

    @staticmethod
    def price_to_points(price_diff: float, symbol: str) -> float:
        """
        Converte diferença de preço para PONTOS MT5.

        Args:
            price_diff: Diferença absoluta de preço (ex: 0.00150 para EURUSD)
            symbol: Símbolo MT5 para obter .point

        Returns:
            float: Distância em pontos MT5 (ex: 150.0 para EURUSD 5-digit)
        """
        try:
            import MetaTrader5 as mt5
            info = mt5.symbol_info(symbol)
            if info is None:
                log.warning("[%s] price_to_points: symbol_info None — usando epsilon", symbol)
                return round(price_diff / _EPSILON, 1)
            point = max(info.point, _EPSILON)
            return round(price_diff / point, 1)
        except ImportError:
            # CI/test: retorna valor raw dividido por ponto padrão por classe
            return _fallback_price_to_points(price_diff, symbol)

    @staticmethod
    def points_to_price(points: float, symbol: str) -> float:
        """Converte pontos MT5 para diferença de preço absoluta."""
        try:
            import MetaTrader5 as mt5
            info = mt5.symbol_info(symbol)
            if info is None:
                return 0.0
            return round(points * info.point, 8)
        except ImportError:
            return _fallback_points_to_price(points, symbol)

    @staticmethod
    def unrealized_points(position_ticket: int, symbol: str, direction: int) -> float:
        """
        Calcula PnL não realizado em PONTOS para posição aberta.

        Args:
            position_ticket: ticket MT5 da posição
            symbol: símbolo da posição
            direction: +1 (BUY) ou -1 (SELL)

        Returns:
            float: PnL em pontos (positivo = lucro, negativo = prejuízo)
        """
        try:
            import MetaTrader5 as mt5
            positions = mt5.positions_get(ticket=position_ticket)
            if not positions:
                return 0.0
            pos = positions[0]
            info = mt5.symbol_info(symbol)
            if info is None:
                return 0.0
            point = max(info.point, _EPSILON)
            bid = mt5.symbol_info_tick(symbol).bid
            ask = mt5.symbol_info_tick(symbol).ask
            current_price = bid if direction == 1 else ask
            diff = (current_price - pos.price_open) * direction
            return round(diff / point, 1)
        except Exception as exc:
            log.debug("unrealized_points error: %s", exc)
            return 0.0

    # ── Logging de eventos (STRICTLY POINTS) ───────────────────────────────────

    def log_position_event(
        self,
        ticket: int,
        symbol: str,
        action: str,
        points: float,
        reason: str,
        usd_context: Optional[float] = None,
    ) -> None:
        """
        Loga evento de posição em PONTOS. USD é contexto, não unidade de distância.

        Format: [SYMBOL #ticket] ACTION | Dist: +150.0 pts | Reason: PEAK_DRAWDOWN

        Args:
            ticket: ticket MT5 da posição
            symbol: símbolo
            action: OPEN / CLOSE / PARTIAL / TRAILING / FLIP
            points: distância em PONTOS (positivo = favor, negativo = contra)
            reason: motivo do evento
            usd_context: PnL em USD para reconciliação (opcional, não é distância)
        """
        usd_suffix = f" | USD_ctx: ${usd_context:+.2f}" if usd_context is not None else ""
        msg = (
            f"[{symbol} #{ticket}] {action} | "
            f"Dist: {points:+.1f} pts | "
            f"Reason: {reason}{usd_suffix}"
        )
        log.info(msg)
        self._write_audit(ticket, symbol, action, points, reason, usd_context)

    def log_sl_tp_event(
        self,
        ticket: int,
        symbol: str,
        sl_pts: float,
        tp_pts: float,
        reason: str,
    ) -> None:
        """Loga SL/TP em pontos. Nunca em USD."""
        msg = (
            f"[{symbol} #{ticket}] SL/TP_SET | "
            f"SL: {sl_pts:.1f} pts | TP: {tp_pts:.1f} pts | "
            f"Reason: {reason}"
        )
        log.info(msg)
        self._write_audit(ticket, symbol, "SL_TP_SET", (sl_pts + tp_pts) / 2, reason)

    def log_trailing_event(
        self,
        ticket: int,
        symbol: str,
        trail_pts: float,
        peak_pts: float,
        current_pts: float,
    ) -> None:
        """Loga trailing stop em pontos."""
        msg = (
            f"[{symbol} #{ticket}] TRAILING | "
            f"Trail: {trail_pts:.1f} pts | "
            f"Peak: {peak_pts:+.1f} pts | "
            f"Current: {current_pts:+.1f} pts"
        )
        log.info(msg)
        self._write_audit(ticket, symbol, "TRAILING", current_pts, "TRAIL_UPDATE")

    # ── Auditoria JSONL ─────────────────────────────────────────────────────────

    def _write_audit(
        self,
        ticket: int,
        symbol: str,
        action: str,
        points: float,
        reason: str,
        usd_context: Optional[float] = None,
    ) -> None:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "ticket": ticket,
            "symbol": symbol,
            "action": action,
            "dist": round(points, 1),
            "unit": "points",          # NUNCA "usd" como unit de distância
            "reason": reason,
        }
        if usd_context is not None:
            record["usd_ctx"] = round(usd_context, 4)   # contexto — campo separado
        try:
            with open(self._audit_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(record) + "\n")
        except OSError as exc:
            log.warning("PointMetrics audit write error: %s", exc)


# ── Fallback sem MT5 (para CI/testes) ──────────────────────────────────────────

_FALLBACK_POINTS = {
    "EURUSD": 1e-5, "GBPUSD": 1e-5, "USDJPY": 1e-3, "XAUUSD": 1e-2,
    "ETHUSD": 1e-2, "BTCUSD": 1e-2, "XRPUSD": 1e-5, "SOLUSD": 1e-3,
    "US500":  1e-2, "DOGUSD": 1e-5,
}
_DEFAULT_POINT = 1e-5


def _fallback_price_to_points(price_diff: float, symbol: str) -> float:
    point = _FALLBACK_POINTS.get(symbol, _DEFAULT_POINT)
    return round(abs(price_diff) / max(point, _EPSILON), 1)


def _fallback_points_to_price(points: float, symbol: str) -> float:
    point = _FALLBACK_POINTS.get(symbol, _DEFAULT_POINT)
    return round(points * point, 8)
