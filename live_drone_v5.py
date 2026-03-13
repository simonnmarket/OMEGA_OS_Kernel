import MetaTrader5 as mt5
import time
import sys
import numpy as np
import socket
import os
from datetime import datetime

from run_aic_v5_master import OmegaAICControllerV5
from modules.v_flow_microstructure import MacroBias

import logging

# Configuração de Log Persistente para a Madrugada (PSA TIER-0)
log_file = "omega_overnight_log.txt"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='a', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("OMEGA")

def log_print(msg):
    logger.info(msg)

def singleton_lock(port=50051):
    """
    TRAVA DE INSTÂNCIA ÚNICA (SINGLETON LOCK)
    Garante que o Terminal ID não seja duplicado via Socket.
    """
    try:
        lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lock_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        lock_socket.bind(('127.0.0.1', port))
        # Mantém o socket aberto durante a execução
        return lock_socket
    except socket.error:
        print(f"\n[🚫] ERRO CRÍTICO: OMEGA já está rodando em outra instância!")
        print(f"[🚫] O mesmo Terminal ID não aceita duplicidade. Abortando.")
        sys.exit()

def live_aerospace_deploy_multi():
    # Ativa trava de segurança imediata
    global _lock_instance
    _lock_instance = singleton_lock()
    
    log_print("=" * 80)
    log_print("🚀 OMEGA V5.1-AEROSPACE: KERNEL MASTER (SINGLE-INSTANCE ISO)")
    log_print("🚀 INTEGRADO COM METATRADER 5 (HFT Execution Mode)")
    log_print("=" * 80)
    
    if not mt5.initialize():
        log_print("[-] Falha Crítica: MT5 Offline ou inacessível.")
        sys.exit()

    # Define the list of target symbols (Metals + Majors)
    raw_symbols = ["XAUUSD", "XAGUSD", "EURUSD", "GBPUSD", "USDJPY"]
    active_symbols = []
    
    all_symbols = [s.name for s in mt5.symbols_get()]
    
    for sym in raw_symbols:
        # Tenta achar o simbolo exato ou com sufixo (ex: XAUUSD.a)
        found = False
        if mt5.symbol_select(sym, True):
            active_symbols.append(sym)
            found = True
        else:
            # Tentar achar equivalente
            for s in all_symbols:
                if sym in s:
                    if mt5.symbol_select(s, True):
                        active_symbols.append(s)
                        found = True
                        break
        if found:
            log_print(f"[+] Ativo Habilitado e Conectado: {active_symbols[-1]}")
        else:
            log_print(f"[-] Ativo Incompatível na Corretora Ignorado: {sym}")
            
    if not active_symbols:
        log_print("[-] Nenhum ativo operável encontrado. Fechando o sistema.")
        mt5.shutdown()
        sys.exit()

    log_print(f"\n[+] Total de Ativos em Monitoramento HFT: {len(active_symbols)}")
    
    # Instantiate a separate controller for each symbol to avoid state contamination
    controllers = {sym: OmegaAICControllerV5() for sym in active_symbols}
    
    # Parâmetros de risco fiduciário
    base_lot = 0.05
    magic_number = 500500 # V5 Aerospace ID
    
    log_print("\n[*] LUZ VERDE RECEBIDA DA DIRETORIA. OMEGA INICIANDO SCAM DE MICROESTRUTURA...")
    
    try:
        while True:
            for symbol in active_symbols:
                controller = controllers[symbol]
                
                # 1. Puxar 150 candles M1 (Micro - 'Small Hole')
                rates_m1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 150)
                if rates_m1 is None or len(rates_m1) < 150:
                    continue
                
                # 2. Puxar 500 candles M15 (Macro - 'Análise de Correlação')
                rates_m15 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 500)
                if rates_m15 is None or len(rates_m15) < 100:
                    continue
                
                # Formatação [close, high, low, tick_volume]
                window_data = np.array([[r['close'], r['high'], r['low'], float(r['tick_volume'])] for r in rates_m1])
                macro_window = np.array([[r['close'], r['high'], r['low'], float(r['tick_volume'])] for r in rates_m15])
                
                latest_bar = rates_m1[-1]
                candle_dict = {
                    'open': latest_bar['open'],
                    'high': latest_bar['high'],
                    'low': latest_bar['low'],
                    'close': latest_bar['close'],
                    'volume': float(latest_bar['tick_volume'])
                }
                
                # 3. Computar MacroBias Real (Fractal Hurst + Kalman Trend)
                # Usamos M15 para o 'Skeleton' do mercado
                hurst_state = controller.fractal_engine.analyze_series(macro_window[:, 0])
                kalman_macro = controller.kalman_engine.execute(macro_window)
                
                macro_bias = MacroBias(
                    hurst=hurst_state.hurst_exponent,
                    kalman_trend=1 if kalman_macro['velocity'] > 0 else -1,
                    horizon="MACRO_M15",
                    strength=hurst_state.regime_confidence
                )
                
                # Thrust Calculation (Injeção de Macro no Micro)
                thrust = controller.get_thrust_vector(window_data, candle_dict, macro_bias)
                
                # Checar posições abertas do ativo
                positions = mt5.positions_get(symbol=symbol)
                open_positions = [p for p in positions if p.magic == magic_number] if positions else []
                
                # Display Dashboard Verboso (PSA TIER-0)
                vfr_signal = controller.vfr_engine.vfr_core(window_data[-1], window_data)
                current_time = datetime.now().strftime('%H:%M:%S')
                log_print(f"[{current_time}] {symbol}={latest_bar['close']} | Score: {thrust['thrust_score']:.1f} | Trigger: {thrust.get('trigger_type', 'NONE')}")
                log_print(f"   => [DEBUG] Z-Price: {vfr_signal.z_price:+.2f} | Z-Vol: {vfr_signal.z_volume:.2f} | Wick: {vfr_signal.absorption_ratio*100:.0f}% | Δ: {vfr_signal.delta_imbalance:+.2f}")
                
                if not thrust["launch"]:
                    reason = "Score insuficiente (threshold 60)."
                    if thrust["kalman_break"]: reason = "KALMAN STRUCTURAL BREAK - Alta Volatilidade."
                    log_print(f"   => [REJECTED] {reason}")
                
                # Ejection Logic (Kalman Structural Break)
                if thrust["kalman_break"] and open_positions:
                    log_print(f"\n[⚠️] STRUCTURAL BREAK DETECTADO EM {symbol}! EJETANDO {len(open_positions)} POSIÇÕES...")
                    for pos in open_positions:
                        order_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
                        request = {
                            "action": mt5.TRADE_ACTION_DEAL,
                            "symbol": symbol,
                            "volume": pos.volume,
                            "type": order_type,
                            "position": pos.ticket,
                            "price": mt5.symbol_info_tick(symbol).bid if order_type == mt5.ORDER_TYPE_SELL else mt5.symbol_info_tick(symbol).ask,
                            "deviation": 20,
                            "magic": magic_number,
                            "comment": "OMEGA EMERGENCY EJECT",
                            "type_time": mt5.ORDER_TIME_GTC,
                            "type_filling": mt5.ORDER_FILLING_IOC,
                        }
                        mt5.order_send(request)
                
                elif thrust["launch"] and thrust["direction"] != 0:
                    # Disparo de ordem M5
                    # Limite de pyramiding aéreo. Não abre se tiver no sentido oposto e espera eject.
                    has_opposite = any(p.type != (mt5.ORDER_TYPE_BUY if thrust["direction"] == 1 else mt5.ORDER_TYPE_SELL) for p in open_positions)
                    
                    # Restrição para RANGE_DIAGONAL: Não abrir dezenas de ordens no mesmo candle se bater no Range do chefe
                    if thrust.get("trigger_type") == "RANGE_DIAGONAL":
                        max_orders_allowed = 1 # Apenas um tiro de Sniper no range limite
                    else:
                        max_orders_allowed = int(min(18, thrust["thrust_score"] / 5))
                    
                    if not has_opposite and len(open_positions) < max_orders_allowed:
                        dir_str = "BUY" if thrust["direction"] == 1 else "SELL"
                        log_print(f"\n[🚀] IGNICAO DE EMPUXO AUTORIZADA PARA {symbol}! DIREÇÃO: {dir_str}")
                        
                        price = mt5.symbol_info_tick(symbol).ask if thrust["direction"] == 1 else mt5.symbol_info_tick(symbol).bid
                        order_type = mt5.ORDER_TYPE_BUY if thrust["direction"] == 1 else mt5.ORDER_TYPE_SELL
                        
                        # Calcular lote e arredondar
                        lots = base_lot * thrust["squeeze_boost"]
                        lots = round(lots, 2)
                        
                        # Stop Loss 'Small Hole' (Barato e Oportuno)
                        # Em M1, usamos uma distância mínima técnica para não ser pego pelo spread, 
                        # mas mantendo o 'abismo' como apenas um 'buraco'.
                        point = mt5.symbol_info(symbol).point
                        sl_dist = 120 * point # Reduzido para ser um 'salto' curto
                        tp_dist = 400 * point # Alvo mais curto para aproveitar o candle
                        
                        sl = price - sl_dist if thrust["direction"] == 1 else price + sl_dist
                        tp = price + tp_dist if thrust["direction"] == 1 else price - tp_dist
                        
                        request_ioc = {
                            "action": mt5.TRADE_ACTION_DEAL,
                            "symbol": symbol,
                            "volume": lots,
                            "type": order_type,
                            "price": price,
                            "sl": sl,
                            "tp": tp,
                            "deviation": 20,
                            "magic": magic_number,
                            "comment": f"V5_{dir_str}_{thrust['thrust_score']:.0f}",
                            "type_time": mt5.ORDER_TIME_GTC,
                            "type_filling": mt5.ORDER_FILLING_IOC,
                        }
                        
                        result = mt5.order_send(request_ioc)
                        if result.retcode != mt5.TRADE_RETCODE_DONE:
                            # Fallback 1: FOK (Extremamente rígido, preenche ou mata, code 10030 common fix)
                            request_ioc["type_filling"] = mt5.ORDER_FILLING_FOK
                            result = mt5.order_send(request_ioc)
                            if result.retcode != mt5.TRADE_RETCODE_DONE:
                                # Fallback 2: RETURN
                                request_ioc["type_filling"] = mt5.ORDER_FILLING_RETURN
                                result = mt5.order_send(request_ioc)
                        
                        if result.retcode == mt5.TRADE_RETCODE_DONE:
                            log_print(f"[+] TRADE ABERTO EM {symbol}! {dir_str} {lots}x - Preço: {price} - Ticket: {result.order}")
                        else:
                            log_print(f"[-] FALHA NA ABERTURA ({symbol}). Code: {result.retcode}")
                            
                    elif has_opposite:
                        log_print(f"   => [REJECTED] Inversão de empuxo detectada sem Kalman Break. Aguardando resolução da ordem oposta.")

                            
            # Loop do robô - Varredura a cada 30 segundos
            log_print("-" * 60)
            time.sleep(30)
            
    except KeyboardInterrupt:
        log_print("\n[!] OMEGA V5 Halted Pelo Comandante. Encerrando conexões MT5 multi-ativos.")
        mt5.shutdown()

if __name__ == "__main__":
    live_aerospace_deploy_multi()
