#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
risk_circuit_breaker.py — Circuit breaker intradiário (P-01 / Conselho OMEGA)

Objetivo:
    Interromper novas operações quando a perda acumulada desde o *anchor* da sessão
    atingir um limiar (default: -3.5% do equity de abertura do dia/sessão).

Escopo:
    Biblioteca reutilizável para integração no motor de execução (RT). NÃO substitui
    política de risco completa (ex.: limites por posição, margem, reconciliação broker).

Limitações conhecidas:
    - Não modela depósitos/saques intraday (exige equity ajustado upstream ou reset manual).
    - Threshold aplicado sobre equity de conta (não sobre PnL não realizado isolado).
    - Thread-safety: usar um lock externo se o mesmo objeto for partilhado entre threads.

Referência: PARECER_TECNICO_CONSELHO_DEMO_20260322.md (P-01)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "CLOSED"  # Operação permitida (breaker não disparou)
    OPEN = "OPEN"  # Operação bloqueada (disparo)


@dataclass
class CircuitBreakerConfig:
    """Configuração do limiar intradiário."""

    threshold_loss_pct: float = 3.5
    """Perda máxima permitida desde o equity de ancoragem, em percentagem (valor positivo, ex.: 3.5)."""

    use_utc_date: bool = True
    """Se True, o 'dia' para reset automático segue a data UTC."""

    timezone: Optional[Any] = None
    """Opcional: tzinfo (ex. ZoneInfo) para definir 'dia' de negociação; se definido, substitui use_utc_date."""


@dataclass
class TripEvent:
    """Registo de disparo (auditoria / alertas)."""

    at: datetime
    anchor_equity: float
    equity_at_trip: float
    loss_pct: float
    message: str


@dataclass
class IntradayCircuitBreaker:
    """
    Circuit breaker intradiário baseado em equity vs equity de ancoragem do dia.

    Semântica:
        loss_pct = (anchor_equity - current_equity) / anchor_equity * 100
        Dispara quando loss_pct >= threshold_loss_pct (ex. >= 3.5).
    """

    config: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    state: CircuitState = CircuitState.CLOSED
    _anchor_date: Optional[date] = None
    _anchor_equity: Optional[float] = None
    _last_equity: Optional[float] = None
    _last_trip: Optional[TripEvent] = None
    _on_trip: Optional[Callable[[TripEvent], None]] = None

    def set_trip_callback(self, fn: Optional[Callable[[TripEvent], None]]) -> None:
        """Callback opcional chamado uma vez por disparo (ex.: webhook / fila de alertas)."""
        self._on_trip = fn

    def _resolve_day(self, ts: datetime) -> date:
        if self.config.timezone is not None:
            return ts.astimezone(self.config.timezone).date()
        if self.config.use_utc_date:
            return ts.astimezone(timezone.utc).date()
        return ts.date()

    def reset_for_new_day(self, anchor_equity: float, ts: Optional[datetime] = None) -> None:
        """
        Ancoragem explícita (ex.: abertura de sessão ou primeiro tick do dia).
        """
        ts = ts or datetime.now(timezone.utc)
        self._anchor_date = self._resolve_day(ts)
        self._anchor_equity = float(anchor_equity)
        self._last_equity = self._anchor_equity
        self.state = CircuitState.CLOSED
        self._last_trip = None
        logger.info(
            "CircuitBreaker: reset day=%s anchor_equity=%.6f",
            self._anchor_date,
            self._anchor_equity,
        )

    def update(
        self,
        equity: float,
        ts: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Atualiza o estado com o equity atual. Devolve dicionário com flags e métricas.

        Se o dia mudar e ainda não houver anchor, ancora automaticamente no primeiro equity do novo dia.
        """
        ts = ts or datetime.now(timezone.utc)
        ts = ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
        day = self._resolve_day(ts)
        equity = float(equity)

        if self._anchor_date is None or day != self._anchor_date:
            self.reset_for_new_day(equity, ts=ts)

        assert self._anchor_equity is not None
        self._last_equity = equity

        if self.state == CircuitState.OPEN:
            return self._snapshot(ts, tripped=True)

        anchor = self._anchor_equity
        if anchor <= 0:
            logger.error("CircuitBreaker: anchor_equity <= 0; forcing OPEN.")
            self._trip(ts, anchor, equity, loss_pct=float("nan"))
            return self._snapshot(ts, tripped=True)

        loss_pct = (anchor - equity) / anchor * 100.0
        if loss_pct >= self.config.threshold_loss_pct:
            self._trip(ts, anchor, equity, loss_pct=loss_pct)
        return self._snapshot(ts, tripped=self.state == CircuitState.OPEN)

    def _trip(self, ts: datetime, anchor: float, equity: float, loss_pct: float) -> None:
        self.state = CircuitState.OPEN
        msg = (
            f"Circuit breaker OPEN: intraday loss {loss_pct:.4f}% >= "
            f"{self.config.threshold_loss_pct}% (anchor={anchor:.6f}, equity={equity:.6f})"
        )
        self._last_trip = TripEvent(
            at=ts,
            anchor_equity=anchor,
            equity_at_trip=equity,
            loss_pct=loss_pct,
            message=msg,
        )
        logger.critical(msg)
        if self._on_trip:
            try:
                self._on_trip(self._last_trip)
            except Exception as e:  # noqa: BLE001 — alertas não podem derrubar o motor
                logger.exception("CircuitBreaker: on_trip callback failed: %s", e)

    def _snapshot(self, ts: datetime, tripped: bool) -> Dict[str, Any]:
        anchor = self._anchor_equity
        last = self._last_equity
        loss_pct = None
        if anchor is not None and last is not None and anchor > 0:
            loss_pct = (anchor - last) / anchor * 100.0
        return {
            "timestamp": ts.isoformat(),
            "state": self.state.value,
            "anchor_date": str(self._anchor_date) if self._anchor_date else None,
            "anchor_equity": anchor,
            "last_equity": last,
            "intraday_loss_pct": None if loss_pct is None else round(loss_pct, 6),
            "threshold_loss_pct": self.config.threshold_loss_pct,
            "tripped": tripped,
            "last_trip": None
            if self._last_trip is None
            else {
                "at": self._last_trip.at.isoformat(),
                "loss_pct": round(self._last_trip.loss_pct, 6),
                "message": self._last_trip.message,
            },
        }

    def allow_new_orders(self) -> bool:
        """False quando OPEN — integrador deve bloquear envio de novas ordens."""
        return self.state == CircuitState.CLOSED

    def manual_reset_after_governance(self, anchor_equity: float, ts: Optional[datetime] = None) -> None:
        """
        Reset administrativo (ex.: após aprovação humana). Use com trilho de auditoria externo.
        """
        self.reset_for_new_day(anchor_equity, ts=ts)


def default_p01_breaker(
    on_trip: Optional[Callable[[TripEvent], None]] = None,
) -> IntradayCircuitBreaker:
    """Factory com limiar -3.5% (perda máxima 3.5% desde anchor)."""
    cfg = CircuitBreakerConfig(threshold_loss_pct=3.5)
    br = IntradayCircuitBreaker(config=cfg)
    br.set_trip_callback(on_trip)
    return br


if __name__ == "__main__":
    # Smoke test rápido (não substitui pytest no CI)
    logging.basicConfig(level=logging.INFO)

    def _alert(ev: TripEvent) -> None:
        print("[ALERT]", ev.message)

    cb = default_p01_breaker(on_trip=_alert)
    t0 = datetime(2026, 3, 22, 8, 0, tzinfo=timezone.utc)
    cb.update(100_000.0, ts=t0)
    r = cb.update(96_400.0, ts=t0)  # -3.6% desde 100k -> deve disparar
    print(r)
    assert cb.state == CircuitState.OPEN
    assert not cb.allow_new_orders()
    print("smoke OK")
