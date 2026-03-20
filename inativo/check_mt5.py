import MetaTrader5 as mt5

if not mt5.initialize():
    print("Falha ao conectar MT5.")
    quit()

positions = mt5.positions_get()
if positions is None or len(positions) == 0:
    print("[+] Conta limpa. Nenhuma posicao aberta.")
else:
    print(f"[-] AVISO: {len(positions)} posicoes em aberto. Forcando fecho Mestre...")
    for p in positions:
        tick = mt5.symbol_info_tick(p.symbol)
        if not tick: continue
        action_type = mt5.ORDER_TYPE_SELL if p.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        price = tick.bid if p.type == mt5.ORDER_TYPE_BUY else tick.ask
        
        req = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": p.ticket,
            "symbol": p.symbol,
            "volume": p.volume,
            "type": action_type,
            "price": price,
            "deviation": 50,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        res = mt5.order_send(req)
        if res and res.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"Fechado ticket {p.ticket}")
        else:
            req["type_filling"] = mt5.ORDER_FILLING_FOK
            res = mt5.order_send(req)
            if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                 print(f"Fechado ticket {p.ticket} (FOK)")
            else:
                 req["type_filling"] = mt5.ORDER_FILLING_RETURN
                 res = mt5.order_send(req)
                 print(f"Fechado ticket {p.ticket} (RETURN): code {res.retcode if res else 'none'}")

acc = mt5.account_info()
if acc:
    print(f"Estado da Conta:")
    print(f"Saldo: {acc.balance}")
    print(f"Equity: {acc.equity}")
    print(f"Flutuante (Profit): {acc.profit}")

mt5.shutdown()
