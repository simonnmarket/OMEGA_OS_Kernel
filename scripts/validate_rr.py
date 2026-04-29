import sys
sys.path.insert(0, ".")
from core_engines.shadow_loop import ASSET_PROFILES, _MAX_SL_PTS
import MetaTrader5 as mt5

mt5.initialize()

BROKER_FEE = 4.0  # USD round-trip estimado (spread + comissao)
EQUITY     = 10_000.0
RISK_PCT   = 0.001  # 0.1%
RISK_USD   = EQUITY * RISK_PCT

print(f"{'ATIVO':<10} {'regime':<11} {'R:R':>5} | {'SL$':>7} {'TP$':>7} {'Net$':>7} | {'lot':>5} | {'VIAVEL':>7}")
print("-" * 75)

for sym in ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY", "XAUUSD", "BTCUSD", "ETHUSD"]:
    prof = ASSET_PROFILES.get(sym)
    if not prof:
        continue
    s = mt5.symbol_info(sym)
    if not s:
        print(f"{sym}: nao encontrado no MT5")
        continue

    ts  = s.trade_tick_size if s.trade_tick_size > 0 else s.point
    pv  = s.trade_tick_value * (s.point / ts)  # USD por ponto por 1 lote

    sl_mult  = prof["sl_atr_mult"]
    tp_mult  = prof["tp_atr_mult"]
    rr       = tp_mult / sl_mult
    max_sl   = _MAX_SL_PTS.get(prof["regime"], _MAX_SL_PTS["generic"])

    # Simular ATR=80 pontos (valor tipico M3)
    atr_pts  = 80
    sl_pts   = min(atr_pts * sl_mult, max_sl)
    tp_pts   = sl_pts * rr

    # Lot correto para $RISK_USD de risco
    lot_raw  = RISK_USD / max(sl_pts * pv, 1e-6)
    lot      = min(round(lot_raw, 2), prof["lot_cap"])
    lot      = max(lot, s.volume_min if hasattr(s, "volume_min") else 0.01)

    risk_usd = sl_pts * pv * lot
    rew_usd  = tp_pts * pv * lot
    net_usd  = rew_usd - BROKER_FEE
    viavel   = "SIM" if net_usd > risk_usd * 0.8 else ("MARGINAL" if net_usd > 0 else "NAO")

    print(f"{sym:<10} {prof['regime']:<11} 1:{rr:.1f} | ${risk_usd:>6.2f} ${rew_usd:>6.2f} ${net_usd:>6.2f} | {lot:>5.2f} | {viavel}")

mt5.shutdown()
