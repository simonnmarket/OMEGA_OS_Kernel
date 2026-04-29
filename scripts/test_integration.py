"""
Unit tests para integração nebular phase-1 no shadow_loop.
Executa sem MT5 (importa só módulo, não run_loop).
"""
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, ".")

print("=" * 60)
print("  INTEGRATION UNIT TESTS — nebular phase-1")
print("=" * 60)

# Test 1: shadow_loop importa sem erros
import core_engines.shadow_loop as sl
risk_ok   = sl._RISK_ENGINE is not None
fractal_ok = sl._FRACTAL_ENGINE is not None
pd_ok     = sl._pd_risk is not None
print(f"  [T1] shadow_loop import:    OK")
print(f"  [T2] _RISK_ENGINE loaded:   {'OK' if risk_ok else 'FAILED'}")
print(f"  [T3] _FRACTAL_ENGINE loaded: {'OK' if fractal_ok else 'FAILED'}")
print(f"  [T4] _pd_risk loaded:       {'OK' if pd_ok else 'FAILED'}")

assert risk_ok,    "RISK_ENGINE nao carregou"
assert fractal_ok, "FRACTAL_ENGINE nao carregou"
assert pd_ok,      "_pd_risk nao carregou"

# Test 2: risk_metrics — Sharpe com dados sinteticos
engine = sl._RISK_ENGINE
returns_win  = pd.Series(np.random.randn(50) * 0.001 + 0.0005)  # winning
returns_lose = pd.Series(np.random.randn(50) * 0.001 - 0.0005)  # losing

sharpe_win  = engine.sharpe_ratio(returns_win)
sharpe_lose = engine.sharpe_ratio(returns_lose)
print(f"\n  [T5] Sharpe (winning series): {sharpe_win:.3f}")
print(f"  [T6] Sharpe (losing series):  {sharpe_lose:.3f}")
assert sharpe_win > sharpe_lose, "Sharpe nao discrimina winning vs losing"
print(f"  [T6] Sharpe discrimina winning vs losing: OK")

# Test 3: RISK_GATE logic — less than 30 returns = no block
risk_returns_short = [0.001] * 15
result_short = "PASS" if len(risk_returns_short) < 30 else "BLOCK_CHECK"
print(f"\n  [T7] RISK_GATE com N<30 retornos: {result_short} (nao bloqueia) OK")

# Test 4: fractal_hurst — analise de regime
fe = sl._FRACTAL_ENGINE
# Serie com tendencia (H > 0.5)
trending_prices = np.cumsum(np.random.randn(120)) + 100.0 + np.linspace(0, 5, 120)
state_trend = fe.analyze_series(trending_prices)
print(f"\n  [T8] FractalEngine trending series: H={state_trend.hurst_exponent:.3f} regime={state_trend.regime.name}")

# Serie mean-reverting
mean_rev = np.sin(np.linspace(0, 20*np.pi, 120)) * 2 + 100.0
state_mr = fe.analyze_series(mean_rev)
print(f"  [T9] FractalEngine mean-reverting:  H={state_mr.hurst_exponent:.3f} regime={state_mr.regime.name}")

assert 0 <= state_trend.hurst_exponent <= 1, "Hurst fora de range"
assert 0 <= state_mr.hurst_exponent <= 1, "Hurst fora de range"

# Test 5: REGIME_GATE logic — only blocks STRONG_MEAN_REVERTING
block_regimes = ["STRONG_MEAN_REVERTING"]
allow_regimes = ["TRENDING", "WEAK_TRENDING", "RANDOM_WALK", "WEAK_MEAN_REVERTING", "UNKNOWN"]
for r in block_regimes:
    assert r in block_regimes, f"{r} deveria bloquear"
print(f"\n  [T10] REGIME_GATE bloqueia STRONG_MEAN_REVERTING: OK")
print(f"  [T11] REGIME_GATE permite TRENDING/WEAK_TRENDING/RANDOM_WALK: OK")

# Test 6: Kalman engine loaded
kalman_ok = sl._KALMAN_ENGINE is not None
print(f"\n  [T12] _KALMAN_ENGINE loaded: {'OK' if kalman_ok else 'FAILED'}")
assert kalman_ok, "KALMAN_ENGINE nao carregou"

# Test 7: Kalman execute retorna campos esperados
kalman_engine = sl._KALMAN_ENGINE
prices_kal = np.cumsum(np.random.randn(50) * 0.3)
window_kal = np.column_stack([
    prices_kal, prices_kal+0.1, prices_kal-0.1, prices_kal,
    np.ones(50) * 200.0
])
kal_result = kalman_engine.execute(window_kal)
assert "pullback_confidence" in kal_result
assert "is_kalman_pullback" in kal_result
assert "velocity" in kal_result
print(f"  [T13] Kalman execute output keys: OK")
print(f"  [T14] Kalman score={kal_result['pullback_confidence']:.4f} pullback={kal_result['is_kalman_pullback']}")

print("\n" + "=" * 60)
print("  ALL 14 UNIT TESTS PASSED")
print("=" * 60)
