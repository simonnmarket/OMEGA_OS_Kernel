import MetaTrader5 as mt5
import sys

def check_mt5():
    if not mt5.initialize():
        print("FALHA: MT5 não inicializado.")
        sys.exit(1)
    
    account_info = mt5.account_info()
    if account_info is None:
        print("FALHA: Não foi possível obter informações da conta.")
        mt5.shutdown()
        sys.exit(1)
    
    print(f"CONTA: {account_info.login}")
    print(f"SERVIDOR: {account_info.server}")
    print(f"BALANCE: {account_info.balance}")
    print(f"EQUITY: {account_info.equity}")
    print(f"TRADE_MODE: {account_info.trade_mode}")
    
    # 0 = DEMO, 1 = CONTEST, 2 = REAL
    if account_info.trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO:
        print("STATUS: CONTA DEMO CONFIRMADA.")
    elif account_info.trade_mode == mt5.ACCOUNT_TRADE_MODE_REAL:
        print("ALERTA: ESTA É UMA CONTA REAL! ABORTANDO POR SEGURANÇA.")
    else:
        print(f"STATUS: MODO DE TROCA {account_info.trade_mode}")

    mt5.shutdown()

if __name__ == "__main__":
    check_mt5()
