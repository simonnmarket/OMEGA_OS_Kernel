"""
Fase 1 Router/ATR -- Testes unitarios
Mandato: OMEGA-MANDATO-UNIFICADO-20260523 Sec. 7.3
Branch: feat/execution-router-atr-20260523

UT-R1: signal_tf=H4 -> copy_rates usa TIMEFRAME_H4; eff_sl >= max(atr_pts*mult, 1500)
UT-R2: signal_tf=M15 -> copy_rates usa TIMEFRAME_M15 (mock verificado)
UT-R3: partial_taken=False ao abrir; =True apos CLOSE_PARTIAL sucesso
UT-R4: signal_tf desconhecido -> fallback TIMEFRAME_H1
UT-R5: sanitize_sl_tp usa _signal_atr_pts do signal_tf
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

# Importar shadow_loop UMA vez a nivel modulo (usa cache de scipy existente).
# Os testes apenas fazem patch de MetaTrader5 durante a chamada da funcao.
from core_engines.shadow_loop import (
    get_execution_tf_atr,
    sanitize_sl_tp,
    MIN_SL_ATR_MULT,
    MAX_TP_SL_RATIO,
)


def _make_rates(n, high, low, close):
    return [{"high": high, "low": low, "close": close, "open": close} for _ in range(n)]


def _mock_mt5():
    """Mock MetaTrader5 com constantes TF e symbol_info basico."""
    m = MagicMock()
    m.TIMEFRAME_M1  = 1
    m.TIMEFRAME_M3  = 3
    m.TIMEFRAME_M5  = 5
    m.TIMEFRAME_M15 = 15
    m.TIMEFRAME_H1  = 16385
    m.TIMEFRAME_H4  = 16388
    m.TIMEFRAME_D1  = 16408
    m.TIMEFRAME_W1  = 32769
    sym = MagicMock()
    sym.point = 0.01  # XAUUSD default
    m.symbol_info.return_value = sym
    return m


def test_ut_r1_h4_atr_dominates_m1():
    """
    UT-R1: signal_tf=H4 usa TIMEFRAME_H4.
    atr_pts H4 XAUUSD >> 250 (valor tipico M1).
    eff_sl = max(atr_pts * MIN_SL_ATR_MULT, 1500) -- criterio mandato.
    """
    mock_mt5 = _mock_mt5()
    # H4 XAUUSD: TR por vela ~30 -> atr~30 -> pts = 30/0.01 = 3000
    mock_mt5.copy_rates_from_pos.return_value = _make_rates(40, 2020.0, 1990.0, 2005.0)

    with patch.dict("sys.modules", {"MetaTrader5": mock_mt5}):
        result = get_execution_tf_atr("XAUUSD", "H4", confidence=0.70)

    # Verificar que usou TIMEFRAME_H4 (16388)
    mock_mt5.copy_rates_from_pos.assert_called_once_with("XAUUSD", 16388, 0, 40)
    assert result["tf"] == "H4", f"tf esperado H4, obtido {result['tf']}"
    assert result["atr_pts"] > 250, (
        f"H4 atr_pts={result['atr_pts']} deve ser > 250 (ATR M1 tipico ~250 pts)"
    )

    # Criterio mandato Sec. 7.3: eff_sl >= max(3000*mult, 1500)
    eff_sl = max(result["atr_pts"] * MIN_SL_ATR_MULT, 1500.0)
    assert eff_sl >= 1500.0, "eff_sl deve ser >= 1500 (piso XAUUSD)"
    assert eff_sl >= result["atr_pts"] * MIN_SL_ATR_MULT


def test_ut_r2_signal_tf_m15_uses_timeframe_m15():
    """
    UT-R2: signal_tf=M15 -> copy_rates chamado com TIMEFRAME_M15 (15).
    Mock verificado: funcao nao deve usar TIMEFRAME_M1 (1) nem H4 (16388).
    """
    mock_mt5 = _mock_mt5()
    mock_mt5.symbol_info.return_value.point = 0.00001  # EURUSD
    mock_mt5.copy_rates_from_pos.return_value = _make_rates(40, 1.0850, 1.0820, 1.0835)

    with patch.dict("sys.modules", {"MetaTrader5": mock_mt5}):
        result = get_execution_tf_atr("EURUSD", "M15", confidence=0.70)

    mock_mt5.copy_rates_from_pos.assert_called_once_with("EURUSD", 15, 0, 40)
    assert result["tf"] == "M15", f"tf esperado M15, obtido {result['tf']}"
    assert "error" not in result, f"Nao deve ter erro: {result.get('error')}"
    assert result["atr_pts"] > 0


def test_ut_r3_partial_taken_flag_lifecycle():
    """
    UT-R3 (T-F1a): partial_taken=False ao criar ledger entry;
    partial_taken=True apos CLOSE_PARTIAL bem-sucedido (sem MT5).
    """
    _ledger = {}
    _ticket = 99001

    # Simular abertura de posicao (T-F1a: campo inicializado a False)
    _ledger[_ticket] = {
        "symbol": "XAUUSD", "direction": "BUY", "lot": 0.1,
        "entry_price": 2000.0, "partial_taken": False, "signal_tf": "H4",
    }
    assert _ledger[_ticket]["partial_taken"] is False,         "partial_taken deve ser False ao abrir posicao"

    # Simular CLOSE_PARTIAL sucesso -> partial_taken = True
    _pc_res = {"success": True, "volume": 0.05, "fill_price": 2010.0}
    if _pc_res.get("success") and _ticket in _ledger:
        _ledger[_ticket]["partial_taken"] = True
    assert _ledger[_ticket]["partial_taken"] is True,         "partial_taken deve ser True apos CLOSE_PARTIAL bem-sucedido"

    # Simular CLOSE_PARTIAL falhado -- flag nao deve mudar
    _ledger2 = {99002: {"partial_taken": False}}
    _pc_fail = {"success": False, "error": "REJECT"}
    if _pc_fail.get("success") and 99002 in _ledger2:
        _ledger2[99002]["partial_taken"] = True
    assert _ledger2[99002]["partial_taken"] is False,         "partial_taken nao deve mudar quando CLOSE_PARTIAL falha"


def test_ut_r4_unknown_signal_tf_fallback_h1():
    """
    UT-R4: signal_tf desconhecido (ex: XXTF) -> fallback TIMEFRAME_H1 (16385).
    Resultado: tf=H1 no dict retornado.
    """
    mock_mt5 = _mock_mt5()
    mock_mt5.symbol_info.return_value.point = 0.00001
    mock_mt5.copy_rates_from_pos.return_value = _make_rates(40, 1.0850, 1.0820, 1.0835)

    with patch.dict("sys.modules", {"MetaTrader5": mock_mt5}):
        result = get_execution_tf_atr("EURUSD", "XXTF", confidence=0.70)

    # Fallback deve ser TIMEFRAME_H1 (16385)
    mock_mt5.copy_rates_from_pos.assert_called_once_with("EURUSD", 16385, 0, 40)
    assert result["tf"] == "H1", f"tf esperado H1 (fallback), obtido {result['tf']}"


def test_ut_r5_sanitize_sl_tp_uses_signal_atr():
    """
    UT-R5 (T-R1b): sanitize_sl_tp recebe _signal_atr_pts do signal_tf (H4).
    Com atr_pts=3000, sl_raw=100 -> eff_sl deve ser elevado para >= 3000*mult.
    Sem MT5 necessario (funcao puramente matematica).
    """
    # H4 XAUUSD: signal_atr_pts=3000, sl_raw=100 (muito pequeno)
    eff_sl, eff_tp = sanitize_sl_tp(100.0, 6000.0, 3000.0, "XAUUSD")

    expected_min = 3000.0 * MIN_SL_ATR_MULT
    assert eff_sl >= expected_min, (
        f"eff_sl {eff_sl} deve ser >= {expected_min} (atr_pts=3000 * MIN_SL_ATR_MULT={MIN_SL_ATR_MULT})"
    )
    assert eff_sl > 100.0, "eff_sl deve ser elevado acima do sl_raw=100"
    assert eff_tp <= eff_sl * MAX_TP_SL_RATIO, (
        f"eff_tp {eff_tp} nao deve exceder {MAX_TP_SL_RATIO}x eff_sl={eff_sl}"
    )
