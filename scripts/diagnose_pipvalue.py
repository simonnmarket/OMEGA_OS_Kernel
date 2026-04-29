import MetaTrader5 as mt5
mt5.initialize()

for sym_name in ['GBPJPY', 'USDJPY', 'AUDJPY', 'XAUUSD', 'BTCUSD']:
    s = mt5.symbol_info(sym_name)
    if not s:
        print(f"{sym_name}: nao encontrado")
        continue

    wrong_pv   = s.point * s.trade_contract_size
    tick_size  = s.trade_tick_size if s.trade_tick_size > 0 else s.point
    correct_pv = s.trade_tick_value * (s.point / tick_size)

    sl_pts = 80
    lot    = 0.05
    risk_wrong   = sl_pts * wrong_pv   * lot
    risk_correct = sl_pts * correct_pv * lot
    tp_pts_rr215 = sl_pts * (2.8 / 1.3)
    tp_pts_rr30  = sl_pts * 3.0
    rew_215 = tp_pts_rr215 * correct_pv * lot
    rew_30  = tp_pts_rr30  * correct_pv * lot

    print(f"\n{sym_name}")
    print(f"  point={s.point}  contract={s.trade_contract_size}  tick_val={s.trade_tick_value:.6f}  tick_sz={s.trade_tick_size}")
    print(f"  pip_value BUGADO : ${wrong_pv:.6f}/pt/lot  -> SL risco(0.05lot): ${risk_wrong:.4f}")
    print(f"  pip_value CORRETO: ${correct_pv:.6f}/pt/lot  -> SL risco(0.05lot): ${risk_correct:.4f}")
    print(f"  TP(R:R 2.15): {tp_pts_rr215:.0f}pts reward=${rew_215:.2f}  (net apos $3fee: ${rew_215-3:.2f})")
    print(f"  TP(R:R 3.00): {tp_pts_rr30:.0f}pts reward=${rew_30:.2f}  (net apos $3fee: ${rew_30-3:.2f})")
    print(f"  lot CORRETO para $10 risco, SL=80pts: {10/(80*correct_pv):.3f}")

mt5.shutdown()
