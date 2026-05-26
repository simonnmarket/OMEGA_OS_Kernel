"""
OMEGA v4.0 — Market Data Cache (Thread-Safe)
=============================================
OMEGA-PSA-EXEC-20260526 | Fase A: Thread Safety Fix

Resolve o risco crítico de MT5 thread-safety identificado pelo CQO:
  "Se o FastLoop chamar mt5.copy_rates_from_pos() em paralelo com o
   shadow_loop, o terminal MT5 pode travar ou corromper estado."

Solução Producer-Consumer:
  PRODUCER: shadow_loop (thread principal) — chama MT5 e popula este cache
  CONSUMER: AsyncPositionOrchestrator (daemon thread) — lê do cache (zero MT5)

O cache é o único canal de dados de mercado entre as duas threads.
Todas as operações são protegidas por RLock.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import logging

log = logging.getLogger("OMEGA.MarketDataCache")

_CACHE_TTL_SEC = 120.0   # dados expiram após 2 minutos sem actualização


@dataclass
class SymbolSnapshot:
    """Snapshot de dados de mercado para um símbolo em momento T."""
    symbol: str
    rates: Optional[List[dict]]      # OHLCV recentes (ex: H4, 14 barras)
    bid: float = 0.0
    ask: float = 0.0
    spread_pts: float = 0.0
    atr_pts: float = 0.0            # ATR pré-calculado pelo shadow_loop
    unrealized_pts: Dict[int, float] = field(default_factory=dict)  # ticket → pts
    ts: float = field(default_factory=time.time)


class MarketDataCache:
    """
    Cache de dados de mercado partilhado entre shadow_loop e FastLoop.

    REGRA ABSOLUTA:
      - Só a thread principal (shadow_loop) chama métodos update_*()
      - FastLoop só chama get_*() — nunca actualiza
      - Qualquer tentativa de MT5 fora da thread principal é um bug

    Usage:
        # shadow_loop (a cada ciclo, thread principal):
        MARKET_CACHE.update_snapshot("EURUSD", rates, bid=1.1075, ask=1.1076, atr_pts=120.0)
        MARKET_CACHE.update_unrealized("EURUSD", {100001: 320.5, 100002: -45.0})

        # FastLoop (daemon thread, NUNCA toca MT5):
        snap = MARKET_CACHE.get("EURUSD")
        if snap:
            current_pts = snap.unrealized_pts.get(ticket, 0.0)
    """

    def __init__(self) -> None:
        self._cache: Dict[str, SymbolSnapshot] = {}
        self._lock = threading.RLock()

    # ── API do Producer (shadow_loop — thread principal) ───────────────────────

    def update_snapshot(
        self,
        symbol: str,
        rates: Optional[List[dict]] = None,
        bid: float = 0.0,
        ask: float = 0.0,
        atr_pts: float = 0.0,
    ) -> None:
        """Actualiza dados de mercado de um símbolo. Chamado pelo shadow_loop."""
        with self._lock:
            existing = self._cache.get(symbol)
            self._cache[symbol] = SymbolSnapshot(
                symbol=symbol,
                rates=rates,
                bid=bid,
                ask=ask,
                spread_pts=round((ask - bid) / max(bid, 1e-10) * 10000, 2) if bid > 0 else 0.0,
                atr_pts=atr_pts,
                unrealized_pts=existing.unrealized_pts if existing else {},
                ts=time.time(),
            )

    def update_unrealized(self, symbol: str, ticket_pts_map: Dict[int, float]) -> None:
        """
        Actualiza PnL não realizado (em pontos) por ticket.
        Chamado pelo shadow_loop após mt5.positions_get().
        """
        with self._lock:
            if symbol not in self._cache:
                self._cache[symbol] = SymbolSnapshot(
                    symbol=symbol, rates=None, unrealized_pts=ticket_pts_map
                )
            else:
                self._cache[symbol].unrealized_pts.update(ticket_pts_map)
                self._cache[symbol].ts = time.time()

    def remove_ticket(self, ticket: int) -> None:
        """Remove ticket do cache de PnL (posição fechada)."""
        with self._lock:
            for snap in self._cache.values():
                snap.unrealized_pts.pop(ticket, None)

    # ── API do Consumer (FastLoop — zero MT5) ──────────────────────────────────

    def get(self, symbol: str) -> Optional[SymbolSnapshot]:
        """Retorna snapshot mais recente. None se expirado ou inexistente."""
        with self._lock:
            snap = self._cache.get(symbol)
            if snap is None:
                return None
            if time.time() - snap.ts > _CACHE_TTL_SEC:
                log.warning("[%s] MarketDataCache: snapshot expirado (%.0fs)", symbol,
                            time.time() - snap.ts)
                return None
            return snap

    def get_unrealized_pts(self, ticket: int, symbol: str) -> float:
        """PnL não realizado em pontos para um ticket. 0.0 se não disponível."""
        with self._lock:
            snap = self._cache.get(symbol)
            if snap is None:
                return 0.0
            return snap.unrealized_pts.get(ticket, 0.0)

    def get_all_unrealized(self) -> Dict[int, float]:
        """Retorna mapa global ticket → pts de todos os símbolos."""
        result: Dict[int, float] = {}
        with self._lock:
            for snap in self._cache.values():
                result.update(snap.unrealized_pts)
        return result

    def symbols(self) -> List[str]:
        """Lista de símbolos no cache."""
        with self._lock:
            return list(self._cache.keys())


# ── Singleton global ─────────────────────────────────────────────────────────
MARKET_CACHE = MarketDataCache()
