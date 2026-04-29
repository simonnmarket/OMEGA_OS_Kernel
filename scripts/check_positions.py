import MetaTrader5 as mt5

mt5.initialize()
positions = mt5.positions_get(magic=234001)
if positions:
    print(f"{len(positions)} posicoes abertas (magic=234001):")
    for p in positions:
        info = mt5.symbol_info(p.symbol)
        pt = info.point if info else 0.001
        tp_dist = abs(p.tp - p.price_open) / pt if p.tp > 0 else 0
        sl_dist = abs(p.sl - p.price_open) / pt if p.sl > 0 else 0
        rr = round(tp_dist / sl_dist, 2) if sl_dist > 0 else 0
        direction = "BUY" if p.type == 0 else "SELL"
        print(f"  #{p.ticket} {p.symbol} {direction} lot={p.volume} entry={p.price_open:.3f} "
              f"SL={p.sl:.3f}({sl_dist:.0f}pts) TP={p.tp:.3f}({tp_dist:.0f}pts) "
              f"R:R=1:{rr}  pnl=${p.profit:.2f}")
else:
    print("Nenhuma posicao aberta")
mt5.shutdown()
