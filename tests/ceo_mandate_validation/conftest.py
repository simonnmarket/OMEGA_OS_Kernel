"""
OMEGA CEO Mandate Validation — Conftest
========================================
OMEGA-PSA-EXEC-20260526 | Fixtures partilhadas pelos 5 gates.

Todos os testes desta suite são ISOLADOS do MT5 real (mock completo).
Validação live com MT5 activo é responsabilidade da sessão de runner.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── Garantir que source_code está no path ───────────────────────────────────────
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

# ── Suprimir imports MT5 em CI ──────────────────────────────────────────────────
_MT5_MOCK = MagicMock()

# Símbolo de referência para testes
TEST_SYMBOLS = ["EURUSD", "XAUUSD", "ETHUSD", "GBPUSD", "USDJPY"]


@pytest.fixture(autouse=True)
def mock_mt5(monkeypatch):
    """Mock global de MetaTrader5 para todos os testes."""
    mock = MagicMock()

    # account_info
    account = MagicMock()
    account.equity = 10000.0
    account.balance = 10000.0
    account.profit = 121.23
    mock.account_info.return_value = account

    # symbol_info
    def _sym_info(symbol):
        m = MagicMock()
        m.point = {"EURUSD": 1e-5, "XAUUSD": 0.01, "ETHUSD": 0.01,
                   "GBPUSD": 1e-5, "USDJPY": 1e-3}.get(symbol, 1e-5)
        m.trade_tick_value = 1.0
        m.volume_min = 0.01
        return m
    mock.symbol_info.side_effect = _sym_info

    # copy_rates_from_pos
    import numpy as np
    rates = np.zeros(15, dtype=[
        ("time", "i8"), ("open", "f8"), ("high", "f8"),
        ("low", "f8"), ("close", "f8"), ("tick_volume", "i8"),
        ("spread", "i4"), ("real_volume", "i8"),
    ])
    rates["high"] = 1.1100 + np.random.uniform(0, 0.002, 15)
    rates["low"]  = 1.1050 - np.random.uniform(0, 0.002, 15)
    rates["close"] = 1.1075 + np.random.uniform(-0.001, 0.001, 15)
    mock.copy_rates_from_pos.return_value = rates

    # positions_get
    mock.positions_get.return_value = []

    # symbol_info_tick
    tick = MagicMock()
    tick.bid = 1.10750
    tick.ask = 1.10760
    mock.symbol_info_tick.return_value = tick

    # TIMEFRAME
    mock.TIMEFRAME_H4 = 16408

    monkeypatch.setitem(sys.modules, "MetaTrader5", mock)
    return mock


@pytest.fixture
def evidence_dir(tmp_path):
    """Pasta de evidências para cada teste."""
    ev = tmp_path / "ceo_mandate_72h_evidence"
    ev.mkdir(parents=True, exist_ok=True)
    return ev


@pytest.fixture
def sample_ledger():
    """Ledger de PnL simulado para teste de reconciliação."""
    return [
        {"ticket": 100001, "symbol": "EURUSD", "realized_pnl": 12.50, "swap": -0.20, "commission": -0.60},
        {"ticket": 100002, "symbol": "XAUUSD", "realized_pnl": -8.30, "swap":  0.00, "commission": -1.20},
        {"ticket": 100003, "symbol": "ETHUSD", "realized_pnl":  5.75, "swap": -0.10, "commission": -0.80},
    ]
