import MetaTrader5 as mt5
import time
import pandas as pd
import numpy as np
import logging
import sys
import os
from datetime import datetime

# Assegurar que os caminhos estão carregados
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Fallback Inline caso o Python Path não resolva a importação do diretório que começa com numero
class MLAdaptiveBivariateAgent:
    def __init__(self, name):
        self.name = name
        self.learning_rate = 0.01 
        self.transition_table = {"horizontal_weight": 0.5, "vertical_weight": 0.5, "trap_recognition_bias": 0.0}
        
    def read_bivariate_tape(self, time_evolution, cost_structure, detected_symbol):
        score = (time_evolution * self.transition_table["horizontal_weight"]) + \
                (cost_structure * self.transition_table["vertical_weight"]) + \
                self.transition_table["trap_recognition_bias"]
        return score

    def bivariate_feedback_loop(self, previous_symbol, real_outcome, prediction_error):
        if real_outcome == -1: 
            self.transition_table["trap_recognition_bias"] -= self.learning_rate
            self.transition_table["horizontal_weight"] -= (self.learning_rate * 2)
            self.transition_table["vertical_weight"] += self.learning_rate
        elif real_outcome == 1: 
            self.transition_table["horizontal_weight"] += self.learning_rate
            self.transition_table["trap_recognition_bias"] += (self.learning_rate / 2)
        total_w = abs(self.transition_table["horizontal_weight"]) + abs(self.transition_table["vertical_weight"])
        if total_w == 0: total_w = 1
        self.transition_table["horizontal_weight"] /= total_w
        self.transition_table["vertical_weight"] /= total_w

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')

def init_mt5():
    if not mt5.initialize():
        logging.error("Falha ao inicializar o MT5")
        mt5.shutdown()
        return False
    return True

def get_live_data(symbol="XAUUSD", timeframe=mt5.TIMEFRAME_M5, num_bars=100):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, num_bars)
    if rates is None: return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def send_market_order(symbol, order_type, lots, magic=777777, sl_pts=2000, tp_pts=3000):
    point = mt5.symbol_info(symbol).point
    price = mt5.symbol_info_tick(symbol).ask if order_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).bid
    
    sl_price = price - (sl_pts * point) if order_type == mt5.ORDER_TYPE_BUY else price + (sl_pts * point)
    tp_price = price + (tp_pts * point) if order_type == mt5.ORDER_TYPE_BUY else price - (tp_pts * point)
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL, "symbol": symbol, "volume": lots,
        "type": order_type, "price": price, "sl": sl_price, "tp": tp_price,
        "deviation": 20, "magic": magic, "comment": "Turing_Bivariate",
        "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_FOK,
    }
    
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logging.error(f"Erro ao abrir Ordem. Retcode: {result.retcode}")
        # Retentativa relaxando filling
        request["type_filling"] = mt5.ORDER_FILLING_IOC
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE: return None
    
    logging.info(f"Ordem Executada: {result.deal} no preço {result.price}")
    return result

def run_tesseract_live_loop():
    print("="*80)
    print(" 👁️  OMEGA TESSERACT LIVE - THE TURING MACHINE IS AWAKE 👁️ ")
    print(" (O Agente Bivariado está Lendo a Fita ao vivo - XAUUSD M5) ")
    print("="*80)
    
    if not init_mt5(): return
    
    agent = MLAdaptiveBivariateAgent("TURING_SNIPER_01")
    symbol = "XAUUSD"
    lots = 0.02
    
    # Sistema de Escalonamento (Pyramiding Máximo: 5 Ordens simultâneas)
    max_pyramid_legs = 5
    open_tickets = []
    base_trade_dir = 0
    trade_open_price = 0
    tracked_symbol = ""
    
    print("| Conectado à Hantec. Modo de Escalonamento Momentum (Pyramiding) Ativado...")
    print(f"| Pesos Iniciais - Hz: {agent.transition_table['horizontal_weight']:.2f} | Vt: {agent.transition_table['vertical_weight']:.2f}")
    
    while True:
        try:
            # Puxamos M5 (Micro) e H1 (Macro) para a Fita Bivariada
            df_m5 = get_live_data(symbol, mt5.TIMEFRAME_M5, 300)
            df_h1 = get_live_data(symbol, mt5.TIMEFRAME_H1, 50)
            
            if df_m5 is None or df_h1 is None:
                time.sleep(5)
                continue
                
            # 1. Leitura de Fuga Estrutural Instantânea (Sem Médias Atrasadas)
            # Ao invés de Médias que demoram 50 horas, lemos a quebra de fractais primários.
            current_px = df_m5['close'].iloc[-1]
            h1_accel = (df_h1['close'].iloc[-1] - df_h1['open'].iloc[-1]) / df_h1['open'].iloc[-1] * 10000
            m5_accel = (df_m5['close'].iloc[-1] - df_m5['open'].iloc[-1]) / df_m5['open'].iloc[-1] * 10000
            
            # HZ Momentum é a pura Aceleração Gravitacional Instantânea (não suavizada)
            hz_momentum = m5_accel + (h1_accel * 0.5) 
            
            # 2. Leitura de Volume Absoluto (Custo e Deslocamento)
            # Paramos de comparar com "a média dos 20" (O Cão correndo atrás do rabo).
            current_vol = df_m5['tick_volume'].iloc[-1]
            body_size = abs(df_m5['close'].iloc[-1] - df_m5['open'].iloc[-1])
            # Deslocamento por Volume (Eficiência Institucional)
            vt_cost = (current_vol / body_size) if body_size > 0 else current_vol 
            vt_cost = vt_cost / 100.0 # Standardização simples
            
            # Gestão de Múltiplas Posições Abertas (O Motor de Fat Tail)
            active_legs = 0
            if len(open_tickets) > 0:
                positions = mt5.positions_get(symbol=symbol)
                alive_tkts = []
                for tk in open_tickets:
                    found = False
                    for pos in (positions or []):
                        if pos.ticket == tk:
                            found = True
                            active_legs += 1
                            pnl_pts = (current_px - pos.price_open) if pos.type == mt5.ORDER_TYPE_BUY else (pos.price_open - current_px)
                            
                            # Trailing TP Dinâmico
                            limit_tp = 4000 if active_legs <= 2 else 8000
                            if pnl_pts > limit_tp or pnl_pts < -2000:
                                close_req = {
                                    "action": mt5.TRADE_ACTION_DEAL, "symbol": symbol, "volume": pos.volume,
                                    "type": mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                                    "position": pos.ticket, "price": mt5.symbol_info_tick(symbol).bid if pos.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).ask,
                                    "deviation": 20, "magic": 777777, "comment": "FatTail_Close", "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_IOC,
                                }
                                mt5.order_send(close_req)
                                real_outcome = 1 if pnl_pts > 0 else -1
                                err = abs(pnl_pts) / pos.price_open
                                agent.bivariate_feedback_loop(tracked_symbol, real_outcome, err)
                            else:
                                alive_tkts.append(tk)
                open_tickets = alive_tkts
                
            # GATILHO REATIVO CORRIGIDO: Se a vela desaba e tem aceleração, ele atira. Sem checar filtros atrasados do passado.
            if abs(hz_momentum) > 3.0: # Se o preço tem mais de 3.0 bps de aceleração na veia (Queda/Alta livre)
                tape_symbol = "FLASH_CRASH" if hz_momentum < 0 else "FLASH_SURGE"
                score = agent.read_bivariate_tape(hz_momentum, vt_cost, tape_symbol)
                
                if hz_momentum > 0 and score > -0.2: # Libera compras muito mais facil se o mercado derreteu pra cima
                    if len(open_tickets) == 0 or (trade_dir == 1 and len(open_tickets) < max_pyramid_legs and (current_px - trade_open_price > 800)):
                        logging.info(f"🟢 ENTRY BUY (VETOR DESTRUIDO | Leg: {len(open_tickets)+1} | Hz: {hz_momentum:.2f} | VT: {vt_cost:.1f})")
                        res = send_market_order(symbol, mt5.ORDER_TYPE_BUY, lots)
                        if res:
                            open_tickets.append(res.order)
                            trade_dir = 1
                            trade_open_price = res.price
                            tracked_symbol = tape_symbol
                            last_trade_time = time.time()
                            
                elif hz_momentum < 0 and score < 0.2: # Libera vendas na força da gravidade
                    if len(open_tickets) == 0 or (trade_dir == -1 and len(open_tickets) < max_pyramid_legs and (trade_open_price - current_px > 800)):
                        logging.info(f"🔴 ENTRY SELL (VETOR DESTRUIDO | Leg: {len(open_tickets)+1} | Hz: {hz_momentum:.2f} | VT: {vt_cost:.1f})")
                        res = send_market_order(symbol, mt5.ORDER_TYPE_SELL, lots)
                        if res:
                            open_tickets.append(res.order)
                            trade_dir = -1
                            trade_open_price = res.price
                            tracked_symbol = tape_symbol
                            last_trade_time = time.time()

            time.sleep(2) # Tick Rate
            
        except Exception as e:
            logging.error(f"Erro no loop Fat Tail Live: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_tesseract_live_loop()
