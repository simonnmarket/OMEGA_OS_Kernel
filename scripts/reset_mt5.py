import MetaTrader5 as mt5
mt5.initialize()
positions = mt5.positions_get()
if positions:
    for p in positions:
        req = {
            'action': mt5.TRADE_ACTION_DEAL,
            'symbol': p.symbol,
            'volume': p.volume,
            'type': mt5.ORDER_TYPE_SELL if p.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
            'position': p.ticket,
            'price': mt5.symbol_info_tick(p.symbol).bid if p.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(p.symbol).ask,
            'deviation': 20,
            'magic': 999999,
            'type_time': mt5.ORDER_TIME_GTC,
            'type_filling': mt5.ORDER_FILLING_IOC,
        }
        mt5.order_send(req)
mt5.shutdown()
