import MetaTrader5 as mt5
print('Iniciando limpeza de posições MT5...')
if not mt5.initialize():
    print('Falha ao conectar MT5.')
    quit()

positions = mt5.positions_get()
if positions is None or len(positions) == 0:
    print('Nenhuma posição em aberto. Mercado flat.')
else:
    for p in positions:
        tick = mt5.symbol_info_tick(p.symbol)
        req = {
            'action': mt5.TRADE_ACTION_DEAL,
            'symbol': p.symbol,
            'volume': p.volume,
            'type': mt5.ORDER_TYPE_SELL if p.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
            'position': p.ticket,
            'price': tick.bid if p.type == mt5.ORDER_TYPE_BUY else tick.ask,
            'deviation': 20,
            'magic': 999999,
            'comment': 'Emergency Cleanup',
            'type_time': mt5.ORDER_TIME_GTC,
            'type_filling': mt5.ORDER_FILLING_IOC,
        }
        res = mt5.order_send(req)
        if res.retcode == mt5.TRADE_RETCODE_DONE:
            print(f'Posição {p.ticket} fechada com sucesso.')
        else:
            print(f'Erro ao fechar {p.ticket}: {res.comment}')
mt5.shutdown()
print('Reset sistêmico finalizado.')
