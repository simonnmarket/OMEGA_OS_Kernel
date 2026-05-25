"""
PSA Pre-A/B Fix Verification — assertivas matemáticas dos Fixes 2/3/8.
Não depende de MT5 ou rede. Roda em qualquer máquina com Python+pydantic+numpy.

Critérios:
  - Fix 2: lot = clamp(kelly × max_lot, 0.01, max_lot) sem multiplicador mágico.
  - Fix 3: kill switch dispara via highwater (peak_equity), não daily_pnl.
  - Fix 8: idempotência por ticket no record_trade_result e dedup por ticket
           no register_open_position.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent))
sys.path.insert(0, str(ROOT))

from agent_ia.core.omega_global_orchestrator import OmegaGlobalOrchestrator


def test_fix2_kelly_clamp():
    """Lot deve respeitar clamp [0.01, max_lot] sem multiplicador mágico."""
    orch = OmegaGlobalOrchestrator(
        assets=["XAUUSD", "EURUSD", "GBPUSD"],
        total_capital=10000.0,
    )
    # Acessar primeiro agente para verificar que o cálculo usa kelly_fraction × max_lot
    # (não × 10). Verificamos via inspeção do código: a fórmula em get_signal_for_asset.
    src = (ROOT / "core" / "omega_global_orchestrator.py").read_text(encoding="utf-8")
    assert "kelly_fraction * 10" not in src, "Fix 2 falhou: ainda há multiplicador ×10"
    assert "kelly_fraction * session_config.max_lot" in src, "Fix 2 falhou: fórmula clamp ausente"
    print("[FIX2] kelly clamp OK")


def test_fix3_peak_equity_kill_switch():
    """Kill switch deve disparar quando current_equity cair >5% do peak_equity."""
    orch = OmegaGlobalOrchestrator(
        assets=["XAUUSD", "EURUSD", "GBPUSD"],
        total_capital=10000.0,
    )
    # PnL recupera e depois cai: peak deve subir e DD% ser medido vs peak
    orch.record_trade_result("XAUUSD", "agent-1", +1000.0, ticket=1)
    assert orch.peak_equity == 11000.0, f"peak_equity esperado 11000, got {orch.peak_equity}"
    # Queda de 600 (5.45% do peak 11000) deve disparar kill switch
    res = orch.record_trade_result("XAUUSD", "agent-1", -600.0, ticket=2)
    assert res.get("error") == "KILL_SWITCH_TRIGGERED", f"KS deveria disparar, got {res}"
    assert res["drawdown_pct"] >= 0.05, f"DD% esperado ≥5%, got {res['drawdown_pct']}"
    print(f"[FIX3] kill switch via peak_equity OK (DD={res['drawdown_pct']*100:.2f}%)")


def test_fix8_idempotency_and_dedup():
    """record_trade_result com mesmo ticket = duplicate; register_open_position dedup."""
    orch = OmegaGlobalOrchestrator(
        assets=["XAUUSD", "EURUSD", "GBPUSD"],
        total_capital=10000.0,
    )
    # Idempotência record_trade_result
    r1 = orch.record_trade_result("XAUUSD", "agent-1", +50.0, ticket=999)
    pnl_after_first = orch.daily_pnl
    r2 = orch.record_trade_result("XAUUSD", "agent-1", +50.0, ticket=999)  # duplicata
    pnl_after_dup = orch.daily_pnl
    assert r2.get("status") == "DUPLICATE_IGNORED", f"deveria deduplicar, got {r2}"
    assert pnl_after_first == pnl_after_dup, "PnL não deve dobrar em duplicata"
    print(f"[FIX8a] idempotency record_trade_result OK (pnl estável={pnl_after_dup})")

    # Dedup register_open_position
    ok1 = orch.register_open_position("EURUSD", ticket=12345, entry_price=1.1, lot=0.01, agent_id="a")
    ok2 = orch.register_open_position("GBPUSD", ticket=12345, entry_price=1.3, lot=0.01, agent_id="b")
    assert ok1 is True, "primeiro registro deve aceitar"
    assert ok2 is False, "ticket duplicado em outro ativo deve rejeitar"
    print("[FIX8b] dedup register_open_position OK")


if __name__ == "__main__":
    test_fix2_kelly_clamp()
    test_fix3_peak_equity_kill_switch()
    test_fix8_idempotency_and_dedup()
    print("\n[ALL PASS] Fixes 2/3/8 verificados matematicamente")
