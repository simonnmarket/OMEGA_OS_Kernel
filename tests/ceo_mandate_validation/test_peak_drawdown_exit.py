"""
GATE G5 — Protecção de Pico (Peak Drawdown Exit)
==================================================
OMEGA-PSA-EXEC-20260526 | CEO Criterion 5

Critério CEO: Simular entrada → +900 pts → queda para +300 pts.
O sistema DEVE fechar (parcial ou total) por "Peak Drawdown" ANTES de
tocar o Stop Loss original do broker.

Cenário de referência CEO:
  Entry: XAUUSD @ 2000.0 (BUY)
  SL original: -200 pts (1998.0)
  Pico atingido: +900 pts (2009.0)
  Queda: retracção para +300 pts (2003.0)
  Retracção do pico: 900 - 300 = 600 pts ≥ threshold (500 pts)
  Resultado esperado: CLOSE antes de o preço tocar 1998.0

Testes:
  G5-A: PositionPeak detecta pico e calcula retracção correctamente
  G5-B: Peak close threshold triggerado após retracção ≥ 500 pts
  G5-C: Peak partial (50%) triggerado antes do close total
  G5-D: Cenário CEO completo: +900 → +300 → CLOSE_FULL sem tocar SL
  G5-E: Min peak activation protege contra falsos triggers em lucros pequenos
  G5-F: PeakTrackerRegistry thread-safe com múltiplos updates simultâneos
"""
from __future__ import annotations

import sys
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))


class TestPeakDrawdownExit:

    def test_peak_recorded_correctly(self):
        """
        G5-A: PositionPeak regista pico máximo e calcula retracção.
        """
        from core_engines.peak_tracker import PositionPeak

        peak = PositionPeak(
            ticket=600001, symbol="XAUUSD", direction=1,
            entry_price=2000.0,
            peak_close_threshold_pts=500.0,
            peak_partial_threshold_pts=600.0,
            min_peak_activation_pts=100.0,
        )

        peak.update(300.0)
        peak.update(600.0)
        peak.update(900.0)  # PICO MÁXIMO
        peak.update(700.0)  # queda
        peak.update(300.0)  # retracção 600 pts

        assert peak.highest_unrealized_pts == 900.0, (
            f"Pico máximo incorrecto: {peak.highest_unrealized_pts} != 900.0"
        )
        assert peak.current_unrealized_pts == 300.0
        assert peak.retraced_from_peak_points == 600.0, (
            f"Retracção incorrecta: {peak.retraced_from_peak_points} != 600.0"
        )
        print(f"\n[G5-A] Pico=+900pts, Actual=+300pts, Retracção=600pts ✓")

    def test_peak_close_threshold_triggered(self):
        """
        G5-B: Retracção ≥ 500 pts (close threshold) activa is_peak_close_triggered.
        """
        from core_engines.peak_tracker import PositionPeak

        peak = PositionPeak(
            ticket=600002, symbol="XAUUSD", direction=1,
            entry_price=2000.0,
            peak_close_threshold_pts=500.0,
            peak_partial_threshold_pts=600.0,
            min_peak_activation_pts=100.0,
        )

        # Antes do threshold
        peak.update(900.0)
        peak.update(500.0)   # retracção = 400 pts < 500 → NÃO activa

        assert not peak.is_peak_close_triggered, (
            "Close threshold não deve activar com retracção 400 < 500 pts"
        )

        # Atingir threshold
        peak.update(300.0)   # retracção = 600 pts ≥ 500 → ACTIVA

        assert peak.is_peak_close_triggered, (
            f"GATE G5 FAIL: is_peak_close_triggered=False apesar de retracção="
            f"{peak.retraced_from_peak_points}pts ≥ threshold=500pts"
        )
        print(f"\n[G5-B] Threshold activado: retracção={peak.retraced_from_peak_points}pts ≥ 500pts ✓")

    def test_peak_partial_triggered_before_close(self):
        """
        G5-C: Partial (50%) activa com retracção ≥ 600 pts, antes do close total.
        Nota: threshold_partial (600) > threshold_close (500)? CEO definiu:
        peak_close_pts=500 (total), peak_partial_pts=600 (50%??)
        → Aqui interpretamos: partial com threshold menor que close é o correcto.
        Usamos partial=300 (retracção moderada) e close=500 (retracção severa).
        """
        from core_engines.peak_tracker import PositionPeak

        peak = PositionPeak(
            ticket=600003, symbol="XAUUSD", direction=1,
            entry_price=2000.0,
            peak_close_threshold_pts=500.0,    # retracção 500 → fechar tudo
            peak_partial_threshold_pts=300.0,  # retracção 300 → fechar 50%
            min_peak_activation_pts=100.0,
        )

        peak.update(900.0)  # pico
        peak.update(580.0)  # retracção = 320 pts ≥ 300 → PARTIAL activa, mas < 500 → close NÃO

        assert peak.is_peak_partial_triggered, (
            f"GATE G5 FAIL: partial não activado com retracção=320pts ≥ 300pts"
        )
        assert not peak.is_peak_close_triggered, (
            "Close total não deve activar com retracção=320pts < 500pts"
        )

        peak.mark_partial_executed()
        assert not peak.is_peak_partial_triggered, (
            "Partial não deve re-activar após mark_partial_executed()"
        )
        print(f"\n[G5-C] Partial 50% activado @ retracção=320pts, close ainda inactivo ✓")

    def test_ceo_scenario_900_to_300_closes_before_sl(self):
        """
        G5-D: CENÁRIO CEO — entrada → +900 → +300 → CLOSE_FULL (via FastLoop).
        Sistema fecha ANTES de tocar SL original (-200 pts = 1998.0).
        """
        import asyncio
        import queue
        from core_engines.peak_tracker import PeakTrackerRegistry, PositionPeak
        from core_engines.async_position_orchestrator import AsyncPositionOrchestrator

        registry = PeakTrackerRegistry()

        # XAUUSD BUY @ 2000.0, SL em 1998.0 (-200 pts)
        peak = PositionPeak(
            ticket=600004, symbol="XAUUSD", direction=1,
            entry_price=2000.0,
            peak_close_threshold_pts=500.0,  # CEO: fechar se retracção ≥ 500 pts
            peak_partial_threshold_pts=800.0, # desactivado para este cenário
            min_peak_activation_pts=100.0,
        )
        registry.register(peak)

        # Subida para +900 pts
        for pts in [200.0, 400.0, 600.0, 750.0, 900.0]:
            peak.update(pts)

        # Queda para +300 pts (retracção = 600 pts ≥ 500 pts threshold)
        peak.update(300.0)

        sig_queue: queue.Queue = queue.Queue()
        orch = AsyncPositionOrchestrator(signal_queue=sig_queue, check_interval=2.0)

        async def run():
            with patch("core_engines.async_position_orchestrator.PEAK_REGISTRY", registry):
                await orch._evaluate_position(600004)

        asyncio.run(run())

        # Verificar signal de close
        assert not sig_queue.empty(), (
            "GATE G5 FAIL: sistema NÃO fechou posição apesar de retracção=600pts ≥ 500pts. "
            "Posição teria atingido o SL original."
        )

        sig = sig_queue.get_nowait()
        assert sig.action == "CLOSE_FULL", f"Acção incorrecta: {sig.action}"
        assert sig.reason == "PEAK_DRAWDOWN", f"Razão incorrecta: {sig.reason}"
        assert sig.points_context == 300.0, f"PnL actual incorrecto: {sig.points_context}"

        # Confirmar: price actual (+300) ainda longe do SL (-200)
        # Sistema fechou com +300pts de lucro — SL em -200 nunca tocado
        print(f"\n[G5-D] CEO CENÁRIO:")
        print(f"  Pico atingido:  +{peak.highest_unrealized_pts:.0f} pts")
        print(f"  Retracção:      {peak.retraced_from_peak_points:.0f} pts")
        print(f"  Preço de close: +{sig.points_context:.0f} pts (SL original em -200 pts)")
        print(f"  Signal emitido: {sig.action} | {sig.reason}")
        print(f"  SL BROKER: NÃO TOCADO ✓")
        assert sig.points_context > 0, (
            "GATE G5 FAIL: posição fechada em prejuízo — sistema deveria ter actuado antes"
        )

    def test_min_peak_activation_prevents_false_triggers(self):
        """
        G5-E: Sem pico mínimo atingido, peak protection não activa.
        Evita fechar posições com lucros muito pequenos (ruído de mercado).
        """
        from core_engines.peak_tracker import PositionPeak

        peak = PositionPeak(
            ticket=600005, symbol="EURUSD", direction=1,
            entry_price=1.1000,
            peak_close_threshold_pts=50.0,   # threshold pequeno
            peak_partial_threshold_pts=30.0,
            min_peak_activation_pts=100.0,   # PICO MÍNIMO: 100 pts
        )

        # Pico de apenas 80 pts (< 100 pts mínimo de activação)
        peak.update(80.0)
        peak.update(10.0)  # retracção de 70 pts ≥ 50 pts threshold
        # MAS pico foi 80 < 100 min_activation → NÃO deve activar

        assert not peak.is_peak_close_triggered, (
            f"GATE G5 FAIL: peak protection activou com pico={peak.highest_unrealized_pts}pts "
            f"< min_activation={peak.min_peak_activation_pts}pts"
        )
        print(f"\n[G5-E] Pico=80pts < min_activation=100pts → sem trigger ✓")

    def test_peak_registry_thread_safe(self):
        """
        G5-F: PeakTrackerRegistry é thread-safe com 50 threads em simultâneo.
        """
        from core_engines.peak_tracker import PeakTrackerRegistry, PositionPeak

        registry = PeakTrackerRegistry()
        errors = []

        def worker(tid: int):
            try:
                peak = PositionPeak(
                    ticket=700000 + tid, symbol="EURUSD", direction=1,
                    entry_price=1.1000,
                    peak_close_threshold_pts=500.0,
                    peak_partial_threshold_pts=600.0,
                    min_peak_activation_pts=100.0,
                )
                registry.register(peak)
                for pts in [50.0, 100.0, 200.0, 150.0, 80.0]:
                    peak.update(pts)
                    time.sleep(0.001)
                registry.remove(700000 + tid)
            except Exception as exc:
                errors.append(f"Thread {tid}: {exc}")

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10.0)

        print(f"\n[G5-F] 50 threads concorrentes: {len(errors)} erros")
        assert not errors, (
            f"GATE G5 FAIL: erros de thread safety:\n" + "\n".join(errors)
        )
        assert len(registry) == 0, "Registry deve estar vazio após todos removerem"
        print(f"[G5-F] Registry thread-safe verificado ✓")

    def test_peak_to_dict_serialization(self):
        """
        G5-G: PositionPeak.to_dict() serializa correctamente para JSONL.
        """
        from core_engines.peak_tracker import PositionPeak

        peak = PositionPeak(
            ticket=800001, symbol="ETHUSD", direction=-1,
            entry_price=3000.0,
            peak_close_threshold_pts=500.0,
            peak_partial_threshold_pts=600.0,
            min_peak_activation_pts=100.0,
        )
        peak.update(400.0)  # SELL em lucro (já inverso)
        peak.update(200.0)  # retracção

        d = peak.to_dict()
        assert d["ticket"] == 800001
        assert d["symbol"] == "ETHUSD"
        assert d["highest_pts"] == 400.0
        assert d["current_pts"] == 200.0
        assert d["retraced_pts"] == 200.0
        assert isinstance(d["holding_min"], float)
        print(f"\n[G5-G] Serialização: {d}")
