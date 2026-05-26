#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMEGA v4.0 — Validate Live Gates
==================================
CEO Mandate 2026-05-26 | PSA Finding #7

Valida as 5 portas de prontidão para Demo Live.

Gates:
  G1 — RiskBudgetManager: import + instância + available_slots (modo legacy)
  G2 — PointMetricEngine: import + cálculo de pontos (sanidade)
  G3 — PeakTrackerRegistry: import + register + cleanup_closed_positions
  G4 — AsyncPositionOrchestrator: import + drain dedup + FASTLOOP_ENABLED flag
  G5 — AiCalibrationLog: import + record_prediction + compute_stats

Exit codes:
  0 — todas as portas PASS → GO para Demo
  1 — uma ou mais portas FAIL → NO-GO
"""
from __future__ import annotations

import sys
import os
import io
import traceback
from pathlib import Path

# Windows: forcar UTF-8 em stdout para evitar OSError [Errno 22]
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
except AttributeError:
    pass

# Garantir que o root do projecto está no PYTHONPATH
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# ── Utilitários de report ─────────────────────────────────────────────────────

PASS = "PASS"
FAIL = "FAIL"

results: list = []


def gate(name: str, fn) -> bool:
    """Executa uma função de gate e regista resultado."""
    try:
        fn()
        print(f"  [{PASS}] {name}")
        results.append((name, True, ""))
        return True
    except Exception as exc:
        msg = f"{type(exc).__name__}: {exc}"
        print(f"  [{FAIL}] {name} — {msg}")
        results.append((name, False, msg))
        return False


# ── Gate G1: RiskBudgetManager ────────────────────────────────────────────────

def _g1_risk_budget():
    from core_engines.risk_budget import RiskBudgetManager, RiskBudgetConfig, RISK_BUDGET_ENABLED
    cfg = RiskBudgetConfig(
        max_drawdown_pct=0.02,
        risk_per_position_pct=0.005,
        default_lot=0.10,
        hard_cap=8,
    )
    mgr = RiskBudgetManager(cfg=cfg)
    # Modo legacy (sem MT5): deve retornar 1 slot (cap=1) ou hard_cap
    os.environ.setdefault("OMEGA_MAX_POS_PER_ASSET", "1")
    slots = mgr.available_slots("EURUSD", current_positions=0)
    assert slots >= 0, f"available_slots retornou negativo: {slots}"
    # update_atr não deve lançar excepção
    mgr.update_atr("EURUSD", 500.0)
    mgr.update_atr("EURUSD", 480.0)


# ── Gate G2: PointMetricEngine ────────────────────────────────────────────────

def _g2_point_metrics():
    from core_engines.point_metrics import PointMetricEngine
    eng = PointMetricEngine()
    # Sanidade: cálculo de distância em pontos (CI fallback — sem MT5)
    pts = eng.price_to_points(price_diff=0.0010, symbol="EURUSD")
    assert pts > 0, f"price_to_points retornou <= 0: {pts}"
    # log_position_event não deve lançar
    eng.log_position_event(99999, "EURUSD", "TEST_EVENT", 200.0, "validate_gate")


# ── Gate G3: PeakTrackerRegistry ─────────────────────────────────────────────

def _g3_peak_tracker():
    from core_engines.peak_tracker import PeakTrackerRegistry, PositionPeak

    reg = PeakTrackerRegistry()
    peak = PositionPeak(
        ticket=12345,
        symbol="EURUSD",
        direction=1,
        entry_price=1.08500,
    )
    reg.register(peak)
    assert 12345 in reg.all_tickets()

    # Simular update de PnL
    reg.update_all({12345: 350.0})
    p = reg.get(12345)
    assert p is not None and p.highest_unrealized_pts == 350.0

    # Testar cleanup_closed_positions
    reg.cleanup_closed_positions(live_tickets=set())   # set vazio → tudo stale
    assert 12345 not in reg.all_tickets(), "cleanup não removeu ticket stale"


# ── Gate G4: AsyncPositionOrchestrator ───────────────────────────────────────

def _g4_orchestrator():
    import queue as _q
    from core_engines.async_position_orchestrator import (
        AsyncPositionOrchestrator, FastLoopSignal, dedup_signals,
    )
    from core_engines.market_data_cache import MarketDataCache

    # Verificar instância sem tocar em singletons de produção
    cache = MarketDataCache()
    orch = AsyncPositionOrchestrator(
        signal_queue=_q.Queue(maxsize=64),
        market_cache=cache,
    )
    assert not orch.is_alive(), "orchestrador nao devia estar activo sem start()"
    assert orch.p95_latency() == 0.0

    # Testar dedup_signals — função pura, zero efeitos laterais em produção
    sig_partial = FastLoopSignal(ticket=777, symbol="XAUUSD", action="CLOSE_PARTIAL",
                                  reason="PEAK_PARTIAL", points_context=400.0, partial_pct=0.5)
    sig_full    = FastLoopSignal(ticket=777, symbol="XAUUSD", action="CLOSE_FULL",
                                  reason="PEAK_DRAWDOWN", points_context=350.0, partial_pct=1.0)
    sig_other   = FastLoopSignal(ticket=888, symbol="EURUSD", action="CLOSE_FULL",
                                  reason="AI_REVERSAL", points_context=200.0)

    deduped = dedup_signals([sig_partial, sig_full, sig_other])
    ticket_map = {s.ticket: s for s in deduped}

    assert 777 in ticket_map, "ticket 777 ausente apos dedup"
    assert ticket_map[777].action == "CLOSE_FULL", \
        f"dedup falhou: {ticket_map[777].action} (esperado CLOSE_FULL)"
    assert 888 in ticket_map, "ticket 888 ausente apos dedup"
    assert len(deduped) == 2, f"esperado 2 sinais, obtido {len(deduped)}"


# ── Gate G5: AiCalibrationLog ─────────────────────────────────────────────────

def _g5_ai_calibration():
    import tempfile
    from pathlib import Path
    from core_engines.ai_calibration import AiCalibrationLog

    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test_calib.jsonl"
        calib = AiCalibrationLog(log_file=log_path)

        calib.record_prediction(
            ticket=555, symbol="GBPUSD",
            pred_direction=1, pred_confidence=0.82,
            actual_direction=1, reason="TEST",
        )
        calib.record_outcome(ticket=555, actual_pnl_pts=250.0, outcome="WIN")

        stats = calib.compute_stats()
        assert stats["total"] == 1, f"esperado total=1, obtido {stats['total']}"
        assert "bands" in stats
        assert log_path.exists(), "ficheiro JSONL não foi criado"


# ── Runner principal ──────────────────────────────────────────────────────────

def main() -> int:
    print("\n" + "-" * 60)
    print("  OMEGA v4.0 - validate_live_gates.py")
    print("  CEO Mandate 2026-05-26 | 5 Gates")
    print("-" * 60 + "\n")

    gate("G1 — RiskBudgetManager",           _g1_risk_budget)
    gate("G2 — PointMetricEngine",           _g2_point_metrics)
    gate("G3 — PeakTrackerRegistry cleanup", _g3_peak_tracker)
    gate("G4 — Orchestrator dedup+drain",    _g4_orchestrator)
    gate("G5 — AiCalibrationLog",            _g5_ai_calibration)

    passed = sum(1 for _, ok, _ in results if ok)
    total  = len(results)

    print("\n" + "-" * 60)
    if passed == total:
        print(f"  RESULTADO: {PASS} - {passed}/{total} gates OK  -> GO DEMO")
        print("-" * 60 + "\n")
        return 0
    else:
        failed = [(n, m) for n, ok, m in results if not ok]
        print(f"  RESULTADO: {FAIL} - {passed}/{total} gates OK  -> NO-GO")
        for n, m in failed:
            print(f"    FAIL  {n}: {m}")
        print("-" * 60 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
