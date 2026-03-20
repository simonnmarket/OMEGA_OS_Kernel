import MetaTrader5 as mt5
import time
import sys

def run_live_trade_test():
    print("=== TESTE DE EXECUÇÃO OMEGA TIER-0 NO METATRADER 5 ===")
    
    # 1. Pede conexão ao Terminal do MT5 Aberto
    if not mt5.initialize():
        print("[-] Falha ao inicializar o MT5")
        sys.exit()

    print(f"[+] Conectado ao Terminal! Versão: {mt5.version()}")
    
    # Vamos usar um ativo muito líquido
    symbol = "EURUSD" 
    
    # Se EURUSD não existir por conta do sufixo (ex: EURUSD.m), tentaremos adaptar.
    if not mt5.symbol_select(symbol, True):
        # Fallback: tentar apanhar o primeiro símbolo visível na janela do MT5
        symbols_get = mt5.symbols_get()
        if symbols_get:
            symbol = symbols_get[0].name
            mt5.symbol_select(symbol, True)
            print(f"[*] Alterando ativo para: {symbol}")
        else:
            print("[-] Nenhum ativo operável encontrado.")
            mt5.shutdown()
            sys.exit()

    print(f"[+] Ativo Alvo Selecionado: {symbol}")

    info = mt5.symbol_info(symbol)
    if info is None:
        print("[-] Falha ao obter dados do ativo.")
        mt5.shutdown()
        sys.exit()

    # Preço Ouro da Corretora
    ask_price = mt5.symbol_info_tick(symbol).ask
    bid_price = mt5.symbol_info_tick(symbol).bid
    
    # Risk Engine: Cálculo para um SL/TP muito simples de teste (10 pips/pontos base)
    point = info.point
    sl_points = 100 * point
    tp_points = 200 * point
    
    # Preparar Ação de Compra MT5 dict
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": 0.01,  # Lote mínimo 
        "type": mt5.ORDER_TYPE_BUY,
        "price": ask_price,
        "sl": ask_price - sl_points,
        "tp": ask_price + tp_points,
        "deviation": 20,
        "magic": 999999,  # O ID Institucional Omega
        "comment": "OMEGA TESTE REAL",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    print("\n[!] ENVIANDO ORDEM AO METATRADER 5...")
    result = mt5.order_send(request)
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"[-] Erro ao enviar a Ordem. RetCode: {result.retcode}")
        print(result)
        # Se falhou por causa do preçário ou modo de preenchimento, vamos tentar outro tipo de preenchimento.
        request["type_filling"] = mt5.ORDER_FILLING_RETURN
        print("[!] Tentando preenchimento_return...")
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"[-] Erro final. A tua conta pode requerer outros parâmetros.")
        else:
            print(f"[+] SUCESSO! Ticket do Trade Aberto: {result.order}")
    else:
        print(f"[+] SUCESSO! Ticket do Trade Aberto: {result.order}")
        print(f"[+] Volume: {result.volume} | Preço: {result.price}")
        print(f"(!!!) Vai à tua ABA DE TRADES / POSITIONS do MT5 para veres o Trade Ativo!")

    mt5.shutdown()

if __name__ == "__main__":
    run_live_trade_test()
