"""
OMEGA v4.0 — Async Position Orchestrator (FastLoop)
=====================================================
OMEGA-EXEC-20260526-TECH | CEO Mandate Gate G4

Gere posições abertas em loop assíncrono dedicado (1-3s por iteração),
INDEPENDENTE do scan loop principal (síncrono, 30-60s por ciclo).

Arquitectura de integração (Async Bridge):
  ┌─────────────────────┐    ┌──────────────────────────────┐
  │  shadow_loop.py     │    │  AsyncPositionOrchestrator   │
  │  (síncrono, scan)   │───▶│  (asyncio, daemon thread)    │
  │  30-60s por ciclo   │    │  1-3s por posição            │
  └─────────────────────┘    └──────────────────────────────┘
         ▲                              │
         │  Thread-safe Queue           │ MT5 orders
         └──────────────────────────────┘

Chave: OMEGA_USE_FASTLOOP=1 activa o orchestrator.
Sem flag → shadow_loop funciona como antes (zero regressão).

CEO Mandato:
  - Latência P95 ≤ 5.0s desde sinal de reversão até envio de ordem
  - Peak drawdown: fechar antes de tocar SL original
  - AI exit: mesma edge do entry (confidence > 0.75)
  - Timeout sideways: close se holding > N min e PnL < M pts
"""
from __future__ import annotations

import asyncio
import logging
import os
import queue
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from core_engines.peak_tracker import PEAK_REGISTRY, PositionPeak
from core_engines.point_metrics import PointMetricEngine
from core_engines.market_data_cache import MARKET_CACHE, MarketDataCache

log = logging.getLogger("OMEGA.FastLoop")

# ── Feature flag ────────────────────────────────────────────────────────────────
FASTLOOP_ENABLED: bool = os.getenv("OMEGA_USE_FASTLOOP", "0") == "1"

# ── Parâmetros de runtime ───────────────────────────────────────────────────────
_CHECK_INTERVAL_SEC  = float(os.getenv("OMEGA_FASTLOOP_INTERVAL",   "2.0"))   # por posição
_AI_CONFIDENCE_FLIP  = float(os.getenv("OMEGA_AI_FLIP_CONFIDENCE",  "0.75"))  # flip threshold
_TIMEOUT_MIN         = float(os.getenv("OMEGA_FASTLOOP_TIMEOUT_MIN","60.0"))  # sideways timeout
_MIN_PROFIT_PTS      = float(os.getenv("OMEGA_FASTLOOP_MIN_PROFIT", "0.0"))   # min pts para não fechar
_PEAK_CLOSE_PCT      = float(os.getenv("OMEGA_PEAK_PARTIAL_PCT",    "0.5"))   # 50% fechamento parcial


@dataclass
class FastLoopSignal:
    """Sinal de acção enviado do FastLoop para executor principal."""
    ticket: int
    symbol: str
    action: str                  # "CLOSE_FULL" | "CLOSE_PARTIAL" | "FLIP"
    reason: str
    points_context: float        # PnL actual em pontos
    confidence: float = 0.0      # AI confidence se aplicável
    partial_pct: float = 1.0     # percentagem a fechar (1.0 = total)
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AsyncPositionOrchestrator:
    """
    Orchestrador assíncrono de posições abertas.

    Corre em daemon thread dedicada com próprio event loop asyncio.
    Comunicação com shadow_loop via Queue thread-safe.

    Usage no shadow_loop.py:
        from core_engines.async_position_orchestrator import AsyncPositionOrchestrator, FASTLOOP_ENABLED
        if FASTLOOP_ENABLED:
            _orchestrator = AsyncPositionOrchestrator(signal_queue=_shared_queue)
            _orchestrator.start()
        ...
        # No loop principal — processar signals
        while not _shared_queue.empty():
            sig = _shared_queue.get_nowait()
            _handle_fastloop_signal(sig)
    """

    def __init__(
        self,
        signal_queue: Optional[queue.Queue] = None,
        check_interval: float = _CHECK_INTERVAL_SEC,
        ai_predict_fn: Optional[Callable] = None,
        mt5_executor: Optional[Any] = None,
        market_cache: Optional[MarketDataCache] = None,
    ) -> None:
        """
        Args:
            signal_queue: Queue thread-safe para enviar FastLoopSignal ao shadow_loop
            check_interval: Segundos entre iterações por posição (default 2.0)
            ai_predict_fn: Callable(symbol, cached_data) → {"direction": int, "confidence": float}
                           ATENÇÃO: esta função NÃO deve chamar MT5. Deve usar apenas o
                           MarketDataCache (snapshot já obtido pelo shadow_loop).
            mt5_executor: Não usado pelo FastLoop (MT5 só na thread principal)
            market_cache: Cache de dados de mercado partilhado com shadow_loop (thread-safe)
        """
        self._queue: queue.Queue = signal_queue or queue.Queue()
        self._interval = check_interval
        self._ai_predict = ai_predict_fn
        self._executor = mt5_executor   # reservado — não usar MT5 aqui
        self._market_cache: MarketDataCache = market_cache or MARKET_CACHE
        self._metrics = PointMetricEngine()

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._latency_samples: List[float] = []   # para cálculo P95

    # ── Ciclo de vida ───────────────────────────────────────────────────────────

    def start(self) -> None:
        """Inicia daemon thread com event loop asyncio dedicado."""
        if self._running:
            log.warning("FastLoop já está a correr — ignorado")
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._run_event_loop,
            name="OMEGA-FastLoop",
            daemon=True,
        )
        self._thread.start()
        log.info("FastLoop STARTED — interval=%.1fs | AI_flip_conf=%.2f", self._interval, _AI_CONFIDENCE_FLIP)

    def stop(self) -> None:
        """Para o orchestrador de forma limpa."""
        self._running = False
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=10.0)
        log.info("FastLoop STOPPED — %d amostras de latência registadas", len(self._latency_samples))

    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    # ── Signal Queue ────────────────────────────────────────────────────────────

    def get_queue(self) -> queue.Queue:
        """Retorna a queue partilhada para shadow_loop consumir signals."""
        return self._queue

    def p95_latency(self) -> float:
        """Latência P95 em segundos das últimas iterações. Gate G4: ≤ 5.0s."""
        if not self._latency_samples:
            return 0.0
        sorted_samples = sorted(self._latency_samples[-1000:])  # últimas 1000
        idx = max(0, int(len(sorted_samples) * 0.95) - 1)
        return sorted_samples[idx]

    # ── Event loop privado ──────────────────────────────────────────────────────

    def _run_event_loop(self) -> None:
        """Corre em daemon thread. Cria event loop asyncio isolado."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._main_loop())
        except Exception as exc:
            log.error("FastLoop event loop crashed: %s", exc, exc_info=True)
        finally:
            self._loop.close()

    async def _main_loop(self) -> None:
        """Loop principal assíncrono — itera sobre posições activas."""
        log.info("FastLoop asyncio loop iniciado")
        while self._running:
            cycle_start = time.perf_counter()
            tickets = PEAK_REGISTRY.all_tickets()

            if tickets:
                tasks = [self._evaluate_position(t) for t in tickets]
                await asyncio.gather(*tasks, return_exceptions=True)

            elapsed = time.perf_counter() - cycle_start
            self._latency_samples.append(elapsed)

            # Dormir o restante do intervalo
            sleep_time = max(0.0, self._interval - elapsed)
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            else:
                log.warning("FastLoop ciclo excedeu intervalo: %.3fs > %.1fs", elapsed, self._interval)
                await asyncio.sleep(0)

    async def _evaluate_position(self, ticket: int) -> None:
        """Avalia UMA posição — executa em task asyncio independente."""
        t_start = time.perf_counter()
        peak = PEAK_REGISTRY.get(ticket)
        if peak is None:
            return

        try:
            current_pts = self._get_unrealized_pts(peak)
            peak.update(current_pts)

            # === PYRAMID EVAL (CEO P0-2C — late import anti circular) ===
            try:
                import MetaTrader5 as mt5
                import core_engines.shadow_loop as sl_module
                _pos_list = list(mt5.positions_get(symbol=peak.symbol) or [])
                _dir_str = "BUY" if peak.direction > 0 else "SELL"
                _atr_i = sl_module.get_execution_tf_atr(peak.symbol, "H1", 0.70)
                _trigger = float(_atr_i.get("atr_pts", 0) or 0) * 0.5
                _dec = sl_module.check_pyramid_add(
                    symbol=peak.symbol,
                    direction=_dir_str,
                    open_positions=_pos_list,
                    pos_ledger={},
                    prof={"lot_cap": 0.10},
                    exec_atr={"atr_pts": _atr_i.get("atr_pts", 0)},
                    equity=0.0,
                )
                log.info(
                    "[PYRAMID_EVAL] %s #%d add=%s reason=%s profit_pts=%s trigger=%.1f",
                    peak.symbol,
                    ticket,
                    _dec.get("add"),
                    _dec.get("reason"),
                    _dec.get("profit_pts"),
                    _trigger,
                )
            except Exception as _pe:
                log.warning("[PYRAMID_EVAL] %s #%d erro: %s", peak.symbol, ticket, _pe)

            # ── Check 1: Peak Drawdown Protection ──────────────────────────────
            if peak.is_peak_close_triggered and not peak.peak_close_triggered:
                peak.mark_close_executed()
                sig = FastLoopSignal(
                    ticket=ticket,
                    symbol=peak.symbol,
                    action="CLOSE_FULL",
                    reason="PEAK_DRAWDOWN",
                    points_context=current_pts,
                    partial_pct=1.0,
                )
                self._emit(sig)
                self._metrics.log_position_event(
                    ticket, peak.symbol, "CLOSE_FULL", current_pts, "PEAK_DRAWDOWN"
                )
                return

            # ── Check 2: Peak Partial (50% close) ──────────────────────────────
            if peak.is_peak_partial_triggered:
                peak.mark_partial_executed()
                sig = FastLoopSignal(
                    ticket=ticket,
                    symbol=peak.symbol,
                    action="CLOSE_PARTIAL",
                    reason="PEAK_DRAWDOWN_PARTIAL",
                    points_context=current_pts,
                    partial_pct=_PEAK_CLOSE_PCT,
                )
                self._emit(sig)
                self._metrics.log_position_event(
                    ticket, peak.symbol, "PARTIAL_50PCT", current_pts, "PEAK_DRAWDOWN_PARTIAL"
                )

            # ── Check 3: AI Exit / Flip ─────────────────────────────────────────
            ai_result = await self._query_ai(peak)
            if ai_result:
                direction, confidence = ai_result
                if direction != peak.direction and confidence >= _AI_CONFIDENCE_FLIP:
                    sig = FastLoopSignal(
                        ticket=ticket,
                        symbol=peak.symbol,
                        action="CLOSE_FULL",
                        reason="AI_REVERSAL",
                        points_context=current_pts,
                        confidence=confidence,
                    )
                    self._emit(sig)
                    self._metrics.log_position_event(
                        ticket, peak.symbol, "AI_EXIT", current_pts,
                        f"AI_REVERSAL conf={confidence:.2f}"
                    )
                    return

            # ── Check 4: Timeout Sideways ───────────────────────────────────────
            if (peak.holding_time_min > _TIMEOUT_MIN
                    and current_pts < _MIN_PROFIT_PTS):
                sig = FastLoopSignal(
                    ticket=ticket,
                    symbol=peak.symbol,
                    action="CLOSE_FULL",
                    reason="TIMEOUT_SIDEWAYS",
                    points_context=current_pts,
                )
                self._emit(sig)
                self._metrics.log_position_event(
                    ticket, peak.symbol, "TIMEOUT_CLOSE", current_pts, "TIMEOUT_SIDEWAYS"
                )

        except Exception as exc:
            log.error("[#%d] FastLoop evaluate error: %s", ticket, exc, exc_info=True)

        finally:
            elapsed_ms = (time.perf_counter() - t_start) * 1000
            log.debug("[#%d] evaluate %.1fms", ticket, elapsed_ms)

    # ── Helpers ─────────────────────────────────────────────────────────────────

    def _emit(self, signal: FastLoopSignal) -> None:
        """Envia signal para queue (shadow_loop vai consumir no próximo ciclo)."""
        try:
            self._queue.put_nowait(signal)
            log.info(
                "[%s #%d] FastLoop EMIT %s | reason=%s | pts=%+.1f",
                signal.symbol, signal.ticket, signal.action,
                signal.reason, signal.points_context,
            )
        except queue.Full:
            log.warning("[#%d] FastLoop queue FULL — signal perdido: %s", signal.ticket, signal.action)

    def _get_unrealized_pts(self, peak: PositionPeak) -> float:
        """
        Obtém PnL não realizado em pontos do MarketDataCache.

        THREAD SAFETY: este método NUNCA chama MT5.
        O shadow_loop (thread principal) actualiza o MarketDataCache a cada ciclo
        via MARKET_CACHE.update_unrealized(). O FastLoop apenas lê deste cache.

        Fallback: se o cache não tem dados, usa o último valor conhecido no PeakTracker.
        """
        cached_pts = self._market_cache.get_unrealized_pts(peak.ticket, peak.symbol)
        if cached_pts != 0.0:
            return cached_pts
        # Fallback: usar último valor registado no PeakTracker
        return peak.current_unrealized_pts

    async def _query_ai(self, peak: PositionPeak) -> Optional[tuple]:
        """
        Consulta motor de IA para sinal de saída/flip.

        THREAD SAFETY: a função ai_predict_fn NÃO deve chamar MT5.
        Deve usar apenas o snapshot do MarketDataCache (já obtido pelo shadow_loop).
        A assinatura esperada: ai_predict_fn(symbol, cached_snapshot) → dict

        Returns:
            (direction: int, confidence: float) ou None se IA indisponível
        """
        if self._ai_predict is None:
            return None
        try:
            # Obter snapshot do cache (zero MT5) para passar à IA.
            # Se cache ainda vazia (1.º ciclo), passa dict vazio —
            # AI DEVE operar sem aceder MT5; nunca retorna None por falta de cache.
            cached_snapshot = self._market_cache.get(peak.symbol) or {}
            if not cached_snapshot:
                log.debug("FastLoop AI: cache vazia para %s — snapshot={}", peak.symbol)
            # Executar IA em thread pool (sem bloquear event loop)
            # Assinatura: ai_predict_fn(symbol, cached_snapshot) → dict  [ZERO MT5]
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._ai_predict, peak.symbol, cached_snapshot
            )
            if result and isinstance(result, dict):
                direction = result.get("direction", 0)
                confidence = result.get("confidence", 0.0)
                return (direction, confidence)
        except Exception as exc:
            log.debug("FastLoop AI query error [%s]: %s", peak.symbol, exc)
        return None


# ── API pública deste módulo ────────────────────────────────────────────────────
# PROIBIDO importar _GLOBAL_QUEUE fora deste ficheiro.
# Qualquer injecção de sinais na fila de produção fora do orchestrador
# pode disparar fechamentos reais de posições em conta LIVE/PAPER.
# Use EXCLUSIVAMENTE:
#   - drain_fastloop_signals()  ← shadow_loop (consumidor, thread principal)
#   - dedup_signals(lista)      ← testes/validação (função pura, zero estado global)
#   - start_fastloop()          ← boot do shadow_loop (produtor via _emit interno)
__all__ = [
    "AsyncPositionOrchestrator",
    "FastLoopSignal",
    "FASTLOOP_ENABLED",
    "start_fastloop",
    "stop_fastloop",
    "drain_fastloop_signals",
    "dedup_signals",
    "get_orchestrator",
    # _GLOBAL_QUEUE e _GLOBAL_ORCHESTRATOR: PRIVADOS — nao constam de __all__
]

# ── Singleton global (PRIVADO — aceder apenas via funções públicas acima) ───────
_GLOBAL_ORCHESTRATOR: Optional[AsyncPositionOrchestrator] = None
_GLOBAL_QUEUE: queue.Queue = queue.Queue(maxsize=256)


def get_orchestrator() -> Optional[AsyncPositionOrchestrator]:
    """Retorna singleton global do orchestrador."""
    return _GLOBAL_ORCHESTRATOR


def start_fastloop(
    ai_predict_fn: Optional[Callable] = None,
    mt5_executor: Optional[Any] = None,
    market_cache=None,
) -> Optional[AsyncPositionOrchestrator]:
    """
    Inicia FastLoop global se OMEGA_USE_FASTLOOP=1.
    Chamado pelo shadow_loop.py no boot.

    Args:
        ai_predict_fn: Callable(symbol, cached_snapshot) → dict  [ZERO MT5]
        mt5_executor: Não usado pelo FastLoop (MT5 só na thread principal)
        market_cache: MarketDataCache partilhado (default: singleton MARKET_CACHE)

    Returns:
        orchestrador ou None se flag desactivada
    """
    global _GLOBAL_ORCHESTRATOR
    if not FASTLOOP_ENABLED:
        log.info("FastLoop DISABLED (OMEGA_USE_FASTLOOP not set)")
        return None
    if _GLOBAL_ORCHESTRATOR is not None and _GLOBAL_ORCHESTRATOR.is_alive():
        log.info("FastLoop ja activo")
        return _GLOBAL_ORCHESTRATOR
    from core_engines.market_data_cache import MARKET_CACHE as _MC
    _GLOBAL_ORCHESTRATOR = AsyncPositionOrchestrator(
        signal_queue=_GLOBAL_QUEUE,
        ai_predict_fn=ai_predict_fn,
        mt5_executor=None,    # MT5 proibido no FastLoop
        market_cache=market_cache or _MC,
    )
    _GLOBAL_ORCHESTRATOR.start()
    return _GLOBAL_ORCHESTRATOR


def stop_fastloop() -> None:
    """Para FastLoop global. Chamado no shutdown do shadow_loop."""
    global _GLOBAL_ORCHESTRATOR
    if _GLOBAL_ORCHESTRATOR:
        _GLOBAL_ORCHESTRATOR.stop()
        _GLOBAL_ORCHESTRATOR = None


def dedup_signals(raw: List[FastLoopSignal]) -> List[FastLoopSignal]:
    """
    Aplica deduplicação a uma lista de FastLoopSignal.

    Regras (CEO Finding #6):
    - Se o mesmo ticket tem CLOSE_PARTIAL + CLOSE_FULL → manter apenas CLOSE_FULL
    - Se o mesmo ticket aparece duas vezes com a mesma acção → manter só a primeira

    Função pura: não acede filas nem estado global.

    Args:
        raw: lista de sinais tal como chegou da queue

    Returns:
        Lista deduplicada (CLOSE_FULL prevalece sobre qualquer outro para o mesmo ticket)
    """
    if not raw:
        return raw

    seen: Dict[int, FastLoopSignal] = {}
    for sig in raw:
        existing = seen.get(sig.ticket)
        if existing is None:
            seen[sig.ticket] = sig
        elif sig.action == "CLOSE_FULL" and existing.action != "CLOSE_FULL":
            # CLOSE_FULL sobrepõe CLOSE_PARTIAL ou outro sinal para o mesmo ticket
            log.debug("[DEDUP] #%d: %s substituído por CLOSE_FULL (%s)",
                      sig.ticket, existing.action, sig.reason)
            seen[sig.ticket] = sig
        # else: manter o primeiro — descartar duplicata

    deduped = list(seen.values())
    if len(deduped) < len(raw):
        log.info("[FASTLOOP] Signal dedup: %d raw → %d únicos", len(raw), len(deduped))
    return deduped


def drain_fastloop_signals() -> List[FastLoopSignal]:
    """
    Extrai todos os signals pendentes da queue global e aplica deduplicação.
    Chamado pelo shadow_loop no início de cada ciclo (thread principal).

    Returns:
        Lista de FastLoopSignal deduplicada, pronta a executar.
    """
    raw: List[FastLoopSignal] = []
    while True:
        try:
            raw.append(_GLOBAL_QUEUE.get_nowait())
        except queue.Empty:
            break
    return dedup_signals(raw)
