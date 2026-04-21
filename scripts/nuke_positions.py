import MetaTrader5 as mt5
if not mt5.initialize():
    quit()
positions = mt5.positions_get()
if positions:
    print(f"Fechando {len(positions)} posicoes...")
    for p in positions:
        tick = mt5.symbol_info_tick(p.symbol)
        price = tick.bid if p.type == mt5.ORDER_TYPE_BUY else tick.ask
        request = {
            'action': mt5.TRADE_ACTION_DEAL,
            'symbol': p.symbol,
            'volume': p.volume,
            'type': mt5.ORDER_TYPE_SELL if p.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
            'position': p.ticket,
            'price': price,
            'deviation': 20,
            'magic': 234001,
            'type_time': mt5.ORDER_TIME_GTC,
            'type_filling': mt5.ORDER_FILLING_IOC,
        }
        res = mt5.order_send(request)
        if res and res.retcode != 10009:
            print(f"Erro ao fechar {p.ticket}: {res.comment}")
mt5.shutdown()
