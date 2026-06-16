"""
GATE G3 — Sem Travas de Ativo (Dynamic Scaling)
=================================================
OMEGA-PSA-EXEC-20260526 | CEO Criterion 3

Critério CEO: O limite fixo de 1 ou 2 ordens por ativo FOI EXTINTO.
O sistema deve escalar baseado no ATR/Risco (RiskBudgetManager).

Testes:
  G3-A: RiskBudgetManager calcula slots > 1 quando volatilidade é baixa
  G3-B: Em alta volatilidade (ATR grande), sistema reduz slots automaticamente
  G3-C: Hard cap OMEGA_RISK_BUDGET_HARD_CAP nunca é excedido
  G3-D: OMEGA_MAX_POS_PER_ASSET já NÃO existe no run_omega_24x7.ps1
  G3-E: Com OMEGA_USE_RISK_BUDGET=1, slots ≥ 3 num regime de baixa volatilidade
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))


class TestDynamicScalingNoAssetLock:

    def test_risk_budget_calculates_multiple_slots_low_volatility(self, mock_mt5):
        """
        G3-A: Baixa volatilidade → RiskBudgetManager permite > 1 slot.
        equity=10000, max_dd=2%, risk/pos=0.5%, ATR=50pts, tick_val=1.0, lot=0.10
        risk/pos_usd = 50 × 1.0 × 0.10 = $5.0
        allowed_risk = $200 (2% de $10000)
        max_by_dd = floor(200/5) = 40
        risk_budget_per_pos = $50 (0.5% de $10000)
        max_by_pos_budget = floor(50/5) = 10
        resultado = min(40, 10, HARD_CAP=8) = 8 slots
        """
        os.environ["OMEGA_USE_RISK_BUDGET"] = "1"
        os.environ["OMEGA_RISK_MAX_DD_PCT"] = "0.02"
        os.environ["OMEGA_RISK_PER_POS_PCT"] = "0.005"
        os.environ["OMEGA_RISK_BUDGET_HARD_CAP"] = "8"
        os.environ["OMEGA_LOT_BASE"] = "0.10"

        from core_engines.risk_budget import RiskBudgetManager, RiskBudgetConfig
        cfg = RiskBudgetConfig(max_drawdown_pct=0.02, risk_per_position_pct=0.005, default_lot=0.10)
        mgr = RiskBudgetManager(cfg=cfg)
        mgr.update_atr("EURUSD", 50.0)   # baixa volatilidade

        slots = mgr.available_slots("EURUSD", current_positions=0, atr_override_pts=50.0)
        print(f"\n[G3-A] ATR=50pts: slots disponíveis = {slots}")
        assert slots >= 3, (
            f"GATE G3 FAIL: slots={slots} com ATR baixo, esperado ≥ 3. "
            f"Sistema ainda tem trava fixar arbitrária."
        )

    def test_risk_budget_reduces_slots_high_volatility(self, mock_mt5):
        """
        G3-B: Alta volatilidade (ATR=1000pts) → menos slots disponíveis.
        risk/pos_usd = 1000 × 1.0 × 0.10 = $100
        max_by_dd = floor(200/100) = 2
        Resultado: slots < slots com ATR=50
        """
        os.environ["OMEGA_USE_RISK_BUDGET"] = "1"

        from core_engines.risk_budget import RiskBudgetManager, RiskBudgetConfig
        cfg = RiskBudgetConfig(max_drawdown_pct=0.02, risk_per_position_pct=0.005, default_lot=0.10)
        mgr = RiskBudgetManager(cfg=cfg)

        slots_low_vol  = mgr.available_slots("EURUSD", 0, atr_override_pts=50.0)
        slots_high_vol = mgr.available_slots("EURUSD", 0, atr_override_pts=1000.0)

        print(f"\n[G3-B] ATR=50pts: {slots_low_vol} slots | ATR=1000pts: {slots_high_vol} slots")
        assert slots_high_vol <= slots_low_vol, (
            "GATE G3 FAIL: alta volatilidade deve reduzir slots disponíveis"
        )

    def test_hard_cap_never_exceeded(self, mock_mt5):
        """
        G3-C: Hard cap NUNCA é excedido, independentemente do ATR.
        """
        os.environ["OMEGA_USE_RISK_BUDGET"] = "1"

        from core_engines.risk_budget import RiskBudgetManager, RiskBudgetConfig
        cfg = RiskBudgetConfig(
            max_drawdown_pct=0.50, risk_per_position_pct=0.50,
            default_lot=0.10, hard_cap=4,
        )
        mgr = RiskBudgetManager(cfg=cfg)

        # ATR muito baixo → sem hard cap poderia dar centenas de slots
        slots = mgr.available_slots("EURUSD", 0, atr_override_pts=0.1)
        print(f"\n[G3-C] Slots com ATR mínimo (hard_cap=4): {slots}")
        assert slots <= 4, (
            f"GATE G3 FAIL: hard cap violado — slots={slots} > hard_cap=4"
        )

    def test_max_pos_per_asset_removed_from_ps1(self):
        """
        G3-D: OMEGA_MAX_POS_PER_ASSET DEVE ter sido removido do run_omega_24x7.ps1.
        (Substituído por OMEGA_USE_RISK_BUDGET)
        """
        ps1_path = ROOT / "scripts" / "run_omega_24x7.ps1"
        assert ps1_path.exists(), "run_omega_24x7.ps1 não encontrado"

        content = ps1_path.read_text(encoding="utf-8")

        # Linha de atribuição directa (não comentada) não deve existir
        lines = content.splitlines()
        violations = [
            (i + 1, line.strip())
            for i, line in enumerate(lines)
            if "OMEGA_MAX_POS_PER_ASSET" in line
            and not line.strip().startswith("#")
            and "=" in line
        ]

        print(f"\n[G3-D] Linhas activas com OMEGA_MAX_POS_PER_ASSET: {violations}")
        assert not violations, (
            f"GATE G3 FAIL: OMEGA_MAX_POS_PER_ASSET ainda activo em run_omega_24x7.ps1:\n"
            + "\n".join(f"  L{l}: {v}" for l, v in violations)
        )

    def test_risk_budget_env_vars_present_in_ps1(self):
        """
        G3-E: Novas env vars de RiskBudget devem estar presentes no PS1.
        """
        ps1_path = ROOT / "scripts" / "run_omega_24x7.ps1"
        content = ps1_path.read_text(encoding="utf-8")

        required_vars = [
            "OMEGA_USE_RISK_BUDGET",
            "OMEGA_RISK_MAX_DD_PCT",
            "OMEGA_RISK_PER_POS_PCT",
            "OMEGA_USE_FASTLOOP",
            "OMEGA_LOG_UNIT",
        ]
        missing = [v for v in required_vars if v not in content]

        print(f"\n[G3-E] Vars encontradas no PS1: {[v for v in required_vars if v in content]}")
        assert not missing, (
            f"GATE G3 FAIL: vars obrigatórias não encontradas no PS1: {missing}"
        )

    def test_slots_decrease_with_existing_positions(self, mock_mt5):
        """
        G3-F: Slots disponíveis diminuem quando já existem posições abertas.
        """
        os.environ["OMEGA_USE_RISK_BUDGET"] = "1"
        os.environ["OMEGA_RISK_BUDGET_HARD_CAP"] = "8"

        from core_engines.risk_budget import RiskBudgetManager, RiskBudgetConfig
        cfg = RiskBudgetConfig(max_drawdown_pct=0.02, risk_per_position_pct=0.005, default_lot=0.10)
        mgr = RiskBudgetManager(cfg=cfg)

        slots_0 = mgr.available_slots("EURUSD", 0, atr_override_pts=50.0)
        slots_3 = mgr.available_slots("EURUSD", 3, atr_override_pts=50.0)

        print(f"\n[G3-F] 0 posições: {slots_0} slots | 3 posições: {slots_3} slots")
        assert slots_3 == max(0, slots_0 - 3), (
            f"GATE G3 FAIL: slots com 3 posições existentes ({slots_3}) "
            f"!= {max(0, slots_0-3)} (esperado)"
        )
