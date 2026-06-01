"""Coleta métricas ao vivo para relatório do Conselho."""
import sys, json
sys.path.insert(0, ".")

from modules.mt5_position_tag import human_tag_line
import core_engines.shadow_loop as sl

modules = {
    "RISK_GATE (risk_metrics)":    sl._RISK_ENGINE is not None,
    "REGIME_GATE (fractal_hurst)": sl._FRACTAL_ENGINE is not None,
    "KALMAN (pullback scorer)":    sl._KALMAN_ENGINE is not None,
    "CIRCUIT_BREAKER":             sl._CIRCUIT_BREAKER is not None,
    "TAIL_RISK_HALT":              sl._TAIL_RISK_HALT is not None,
    "pandas (_pd_risk)":           sl._pd_risk is not None,
}

print("\n=== MODULE STATUS ===")
all_ok = True
for k, v in modules.items():
    status = "ACTIVE" if v else "FAILED"
    if not v: all_ok = False
    print(f"  [{status}] {k}")
print(f"  ALL MODULES: {'OK' if all_ok else 'DEGRADED'}")

print("\n=== RISK THRESHOLDS ===")
print(f"  RISK_PER_TRADE_PCT  = {sl.RISK_PER_TRADE_PCT * 100:.3f}%")
print(f"  DD_DAILY_MAX (KS)   = {sl.DD_DAILY_MAX * 100:.1f}%")
print(f"  CIRCUIT_BREAKER DD  = {sl._CB_DD_LIMIT:.1f}%  [OMEGA_DD_CIRCUIT_BREAK]")
print(f"  TAIL_RISK_HALT DD   = 3.0%  (intraday, per event)")
print(f"  REGIME_GATE         = BLOCK if STRONG_MEAN_REVERTING")
print(f"  RISK_GATE_SHARPE    = BLOCK if Sharpe < 0.3 (N >= 30)")
print(f"  KALMAN              = LOG-ONLY (not blocking)")
print(f"  MAX_POSITIONS       = {sl.MAX_POSITIONS}")
print(f"  MT5_TRACKING_TAG    = {human_tag_line()}")

print("\n=== GATE EXECUTION ORDER ===")
gates = [
    "1. GUARDRAIL (night window, regime)",
    "2. MOTOR HARMONICO (harmonic pattern engine)",
    "3. EDGE_GATE (ATR% + ADX min thresholds)",
    "4. [REGIME_GATE] fractal_hurst — Hurst exponent M15",
    "5. MTF_BIAS (multi-timeframe confirmation)",
    "6. CORRELATION_FILTER (JPY cross concentration)",
    "7. [CIRCUIT_BREAKER] daily DD gate — trip @ -3.5%",
    "8. [TAIL_RISK_HALT] intraday tail risk — trip @ -3.0%",
    "9. KILL_SWITCH (DD_DAILY_MAX + consec_fail)",
    "10. MIN_CONF (asset-specific min confidence)",
    "11. LOT_CALC v2 (4-factor adaptive sizing)",
    "12. [RISK_GATE] Sharpe rolling — block if < 0.3",
    "13. [KALMAN] entry timing scorer (log-only)",
    "14. mt5_send_order",
]
for g in gates: print(f"  {g}")

print(f"\n=== ASSET PROFILES ({len(sl.ASSET_PROFILES)} ativos) ===")
for sym, cfg in list(sl.ASSET_PROFILES.items()):
    print(f"  {sym:<12} regime={cfg.get('regime','?'):<12} lot_cap={cfg.get('lot_cap'):.2f}  R:R={cfg.get('tp_atr_mult', '?')}/{cfg.get('sl_atr_mult', '?')}")

print("\n=== SHA3 AUDIT TRAIL ===")
print("  pre-integration  : ef348b0710c7bc64eb4d41237a188023baf4a911f69e915498dfdcbd9b3ff044")
print("  post-RISK/REGIME : ab6ce6b43c540f585f166fa7537aef3f8504deb5966fae3cc6f0faf68f46800c")
try:
    current_sha3 = open("logs/pre_integration_sha3.txt").read().strip()
    print(f"  current          : {current_sha3}")
except Exception:
    pass
