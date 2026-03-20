import MetaTrader5 as mt5
from datetime import datetime

print("--- DIAGNÓSTICO MT5 LIVE ---")
if not mt5.initialize():
    print("Falha ao inicializar MT5")
else:
    t_info = mt5.terminal_info()
    if t_info:
        print(f"Terminal Trade Allowed: {t_info.trade_allowed}")
        print(f"Terminal Connected: {t_info.connected}")
    
    a_info = mt5.account_info()
    if a_info:
        print(f"Account Trade Allowed: {a_info.trade_allowed}")
        print(f"Account Balance: {a_info.balance}")
    
    s_info = mt5.symbol_info("XAUUSD")
    if s_info:
        print(f"Symbol Trade Mode: {s_info.trade_mode}")
        print(f"Symbol Spread: {s_info.spread}")
        print(f"Symbol Ask/Bid: {s_info.ask} / {s_info.bid}")
        print(f"Symbol Market Phase (Opcional): Tempo do Servidor: {datetime.utcfromtimestamp(s_info.time)}")

    mt5.shutdown()
