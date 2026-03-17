import MetaTrader5 as mt5
import psutil
import time

# 1. KILL ALL RUNNING main.py PROCESSES TO STOP THE BLEEDING
killed_count = 0
for p in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        cmd = p.info.get('cmdline') or []
        cmd_str = ' '.join(cmd).lower()
        if 'python' in p.info.get('name', '').lower() and 'main.py' in cmd_str:
            print(f"[*] MATANDO INTEGRADOR DESCONTROLADO (PID: {p.info['pid']})")
            p.kill()
            killed_count += 1
    except Exception as e:
        pass

if killed_count > 0:
    print(f"[-] {killed_count} instâncias do Orquestrador mortas com sucesso.")
    time.sleep(2) # Give it time to die before we hit MT5 API

# 2. EMERGENCY CLOSE ALL POSITIONS
if not mt5.initialize():
    print("[-] FALHA AO INICIAR MT5 PARA ABORTO EMERGENCIAL!")
else:
    positions = mt5.positions_get()
    if positions is None or len(positions) == 0:
        print("[+] Nenhuma posição aberta encontrada no mercado.")
    else:
        print(f"[*] ALERTA VERMELHO: Fechando {len(positions)} posições abertas agora!")
        
        for p in positions:
            tick = mt5.symbol_info_tick(p.symbol)
            if tick is None:
                print(f"[-] Falha ao obter tick para {p.symbol}")
                continue
                
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
                "comment": "EMERGENCY_KILL",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            res = mt5.order_send(req)
            if res.retcode != mt5.TRADE_RETCODE_DONE:
                req["type_filling"] = mt5.ORDER_FILLING_FOK
                res2 = mt5.order_send(req)
                if res2.retcode != mt5.TRADE_RETCODE_DONE:
                    req["type_filling"] = mt5.ORDER_FILLING_RETURN
                    res3 = mt5.order_send(req)
                    if res3.retcode != mt5.TRADE_RETCODE_DONE:
                        print(f"[-] FALHA CRÍTICA ao fechar TICKET {p.ticket} / {p.symbol}. Código Erro: {res3.retcode} - {res3.comment}")
                    else:
                        print(f"[+] Posição de {p.symbol} ({p.ticket}) fechada com sucesso (RETURN).")
                else:
                    print(f"[+] Posição de {p.symbol} ({p.ticket}) fechada com sucesso (FOK).")
            else:
                 print(f"[+] Posição de {p.symbol} ({p.ticket}) fechada com sucesso (IOC).")
                 
    mt5.shutdown()
