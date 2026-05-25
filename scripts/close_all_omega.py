import MetaTrader5 as mt5

mt5.initialize()
positions = mt5.positions_get(magic=234001)
if not positions:
    print("Nenhuma posicao para fechar.")
    mt5.shutdown()
    exit()

print(f"Fechando {len(positions)} posicao(oes) OMEGA...")
for p in positions:
    tick = mt5.symbol_info_tick(p.symbol)
    if not tick:
        print(f"  #{p.ticket} ERRO: sem tick para {p.symbol}")
        continue
    order_type = mt5.ORDER_TYPE_SELL if p.type == 0 else mt5.ORDER_TYPE_BUY
    price = tick.bid if p.type == 0 else tick.ask
    req = {
        "action":      mt5.TRADE_ACTION_DEAL,
        "position":    p.ticket,
        "symbol":      p.symbol,
        "volume":      p.volume,
        "type":        order_type,
        "price":       price,
        "deviation":   50,
        "magic":       234001,
        "comment":     "OMEGA_CLOSE_FIX_SL_TP",
        "type_time":   mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    r = mt5.order_send(req)
    status = "OK" if r and r.retcode == 10009 else f"ERRO retcode={r.retcode if r else 'None'}"
    print(f"  #{p.ticket} {p.symbol} lot={p.volume} pnl=${p.profit:.2f} → {status}")

mt5.shutdown()
print("Concluido.")
