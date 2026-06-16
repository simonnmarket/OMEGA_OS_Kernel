"""
OMEGA v4.0 — Peak Tracker & Retracement Guard
===============================================
OMEGA-EXEC-20260526-TECH | CEO Mandate Gate G5

Rastreia o pico máximo de PnL não realizado (em PONTOS) por posição.
Detecta retracções do pico e dispara fechamento automático antes do SL.

Regra CEO: entrada → +900 pts → queda para +300 pts → sistema fecha/parcial
ANTES de tocar o Stop Loss original do broker.

Thread-safe: todas as operações de update são atómicas via lock por ticket.
"""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional

log = logging.getLogger("OMEGA.PeakTracker")

# ── Defaults configuráveis ──────────────────────────────────────────────────────
import os
_DEFAULT_PEAK_CLOSE_PTS   = float(os.getenv("OMEGA_PEAK_CLOSE_PTS", "500.0"))   # retracção para fechar
_DEFAULT_PEAK_PARTIAL_PTS = float(os.getenv("OMEGA_PEAK_PARTIAL_PTS", "600.0")) # retracção para parcial
_DEFAULT_MIN_PEAK_PTS     = float(os.getenv("OMEGA_MIN_PEAK_PTS", "100.0"))     # pico mínimo para activar


@dataclass
class PositionPeak:
    """
    Estado de pico para UMA posição aberta.

    Todos os valores em PONTOS MT5. USD nunca é usado aqui.
    Thread-safe via _lock interno.
    """
    ticket: int
    symbol: str
    direction: int                           # +1 BUY, -1 SELL
    entry_price: float                       # preço de entrada (para cálculo)
    open_time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Estado de pico (mutável — protegido por lock)
    highest_unrealized_pts: float = 0.0
    current_unrealized_pts: float = 0.0
    update_count: int = 0

    # Thresholds de acção
    peak_close_threshold_pts: float = _DEFAULT_PEAK_CLOSE_PTS
    peak_partial_threshold_pts: float = _DEFAULT_PEAK_PARTIAL_PTS
    min_peak_activation_pts: float = _DEFAULT_MIN_PEAK_PTS

    # Flags de estado
    peak_close_triggered: bool = False
    peak_partial_triggered: bool = False

    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)

    # ── Propriedades derivadas (thread-safe via cópia atómica) ─────────────────

    @property
    def retraced_from_peak_points(self) -> float:
        """Pontos de retracção desde o pico máximo (≥ 0)."""
        return max(0.0, self.highest_unrealized_pts - self.current_unrealized_pts)

    @property
    def is_peak_close_triggered(self) -> bool:
        """True se retracção ≥ peak_close_threshold E pico era significativo."""
        if self.highest_unrealized_pts < self.min_peak_activation_pts:
            return False
        return self.retraced_from_peak_points >= self.peak_close_threshold_pts

    @property
    def is_peak_partial_triggered(self) -> bool:
        """True se retracção ≥ peak_partial_threshold (fechamento parcial 50%)."""
        if self.highest_unrealized_pts < self.min_peak_activation_pts:
            return False
        if self.peak_partial_triggered:
            return False   # já executado
        return self.retraced_from_peak_points >= self.peak_partial_threshold_pts

    @property
    def holding_time_seconds(self) -> float:
        """Tempo em segundos desde abertura da posição."""
        try:
            opened = datetime.fromisoformat(self.open_time)
            now = datetime.now(timezone.utc)
            return (now - opened).total_seconds()
        except Exception:
            return 0.0

    @property
    def holding_time_min(self) -> float:
        return self.holding_time_seconds / 60.0

    # ── Actualização de estado (thread-safe) ───────────────────────────────────

    def update(self, current_unrealized_pts: float) -> None:
        """
        Actualiza PnL actual e pico máximo.

        Chamado pelo AsyncPositionOrchestrator a cada 1-3 segundos.

        Args:
            current_unrealized_pts: PnL actual em pontos (positivo = lucro)
        """
        with self._lock:
            self.current_unrealized_pts = current_unrealized_pts
            self.update_count += 1
            if current_unrealized_pts > self.highest_unrealized_pts:
                old_peak = self.highest_unrealized_pts
                self.highest_unrealized_pts = current_unrealized_pts
                if old_peak < self.min_peak_activation_pts <= current_unrealized_pts:
                    log.info(
                        "[%s #%d] PeakTracker ACTIVATED — pico %.1f pts atingido",
                        self.symbol, self.ticket, current_unrealized_pts
                    )

    def mark_partial_executed(self) -> None:
        """Marca que o fechamento parcial foi executado (evita duplicação)."""
        with self._lock:
            self.peak_partial_triggered = True

    def mark_close_executed(self) -> None:
        """Marca que o fechamento total por peak foi executado."""
        with self._lock:
            self.peak_close_triggered = True

    def to_dict(self) -> dict:
        """Serialização para JSONL de auditoria."""
        return {
            "ticket": self.ticket,
            "symbol": self.symbol,
            "direction": self.direction,
            "highest_pts": round(self.highest_unrealized_pts, 1),
            "current_pts": round(self.current_unrealized_pts, 1),
            "retraced_pts": round(self.retraced_from_peak_points, 1),
            "peak_close_triggered": self.is_peak_close_triggered,
            "peak_partial_triggered": self.is_peak_partial_triggered,
            "holding_min": round(self.holding_time_min, 1),
            "update_count": self.update_count,
        }


class PeakTrackerRegistry:
    """
    Registo global de PositionPeak por ticket.

    Singleton por sessão — partilhado entre shadow_loop e AsyncPositionOrchestrator.
    Thread-safe: operações de add/remove protegidas por RLock.
    """

    def __init__(self) -> None:
        self._registry: Dict[int, PositionPeak] = {}
        self._rlock = threading.RLock()

    def register(self, peak: PositionPeak) -> None:
        """Regista nova posição para rastreio de pico."""
        with self._rlock:
            self._registry[peak.ticket] = peak
            log.info(
                "[%s #%d] PeakTracker registered — dir=%+d entry=%.5f",
                peak.symbol, peak.ticket, peak.direction, peak.entry_price
            )

    def get(self, ticket: int) -> Optional[PositionPeak]:
        """Obtém peak tracker por ticket. None se não existe."""
        with self._rlock:
            return self._registry.get(ticket)

    def remove(self, ticket: int) -> None:
        """Remove posição fechada do registo."""
        with self._rlock:
            if ticket in self._registry:
                peak = self._registry.pop(ticket)
                log.info(
                    "[%s #%d] PeakTracker removed — peak=%.1f pts retraced=%.1f pts",
                    peak.symbol, ticket,
                    peak.highest_unrealized_pts,
                    peak.retraced_from_peak_points,
                )

    def update_all(self, ticket_pts_map: Dict[int, float]) -> None:
        """Actualiza múltiplos tickets em batch. ticket → current_unrealized_pts."""
        with self._rlock:
            for ticket, pts in ticket_pts_map.items():
                if ticket in self._registry:
                    self._registry[ticket].update(pts)

    def all_tickets(self) -> list:
        with self._rlock:
            return list(self._registry.keys())

    def snapshot(self) -> list:
        """Snapshot completo para auditoria."""
        with self._rlock:
            return [p.to_dict() for p in self._registry.values()]

    def __len__(self) -> int:
        with self._rlock:
            return len(self._registry)


# ── Singleton global (importável por shadow_loop e orchestrator) ────────────────
PEAK_REGISTRY = PeakTrackerRegistry()
