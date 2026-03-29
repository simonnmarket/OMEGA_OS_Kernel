import argparse
import time
import MetaTrader5 as mt5
import pandas as pd
import sys
import logging
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument('--mode', default='demo')
parser.add_argument('--symbols', default='XAUUSD,EURUSD,GBPUSD,AUDJPY,USDJPY')
parser.add_argument('--circuit_breaker_threshold', type=float, default=-3.5)
args, _ = parser.parse_known_args()

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s', handlers=[
    logging.FileHandler('omega_v8_live_daemon.log'),
    logging.StreamHandler(sys.stdout)
])

class MomentumRegimeSwitch:
    def __init__(self):
        # Reduzindo o threshold levemente na simulação para podermos apanhar a inércia restante do XAUUSD
        self.momentum_threshold_pct = 0.002  
        self.consecutive_candles = 3

    def check_momentum_override(self, df_last_candles: pd.DataFrame) -> dict:
        if len(df_last_candles) < self.consecutive_candles:
            return {"active": False, "direction": None}

        last = df_last_candles.iloc[-1]
        prev = df_last_candles.iloc[-2]
        prev2 = df_last_candles.iloc[-3]

        bodies = []
        directions = []

        for _, candle in df_last_candles.tail(3).iterrows():
            body = abs(candle['close'] - candle['open'])
            range_val = candle['high'] - candle['low']
            if range_val == 0:
                return {"active": False, "direction": None}
            # Filtro de Força: Corpo > 60%
            if body / range_val < 0.6:
                return {"active": False, "direction": None}

            bodies.append(body)
            directions.append(1 if candle['close'] > candle['open'] else -1)

        # Unidirecionalidade
        if len(set(directions)) != 1:
            return {"active": False, "direction": None}

        total_move = sum(bodies)
        avg_price = last['close']
        move_pct = total_move / avg_price

        if move_pct > self.momentum_threshold_pct:
            return {
                "active": True,
                "direction": "BUY" if directions[0] == 1 else "SELL",
                "strength": move_pct,
                "reason": "WATERFALL_DETECTED_V8.1"
            }

        return {"active": False, "direction": None}

# =========================================================

logging.info("======================================================")
logging.info("[DAEMON] Starting OMEGA V8.1 Live Engine (MOMENTUM SURFER)...")
logging.info(f"[RISK] Circuit Breaker ARMED. Threshold: {args.circuit_breaker_threshold}%")
logging.info("======================================================")

if not mt5.initialize():
    logging.error("Falha ao inicializar MT5.")
    sys.exit(1)

momentum_switch = MomentumRegimeSwitch()
symbols = args.symbols.split(',')

for sym in symbols:
    mt5.symbol_select(sym, True)

logging.info("[DAEMON] Motor Quente (V8.1). Escaneando Cachoeiras e Imbalances em M15...")

try:
    while True:
        for sym in symbols:
            rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M15, 0, 5)
            if rates is not None and len(rates) >= 3:
                df = pd.DataFrame(rates)
                signal = momentum_switch.check_momentum_override(df)
                
                if signal["active"]:
                    logging.warning(f"🚨 [V8.1 OVERRIDE] Ejetando SMC Clássico. Momentum {signal['direction']} puramente direcional detectado em {sym}! Motivo: {signal['reason']}")
                    
                    point = mt5.symbol_info(sym).point
                    ask = mt5.symbol_info_tick(sym).ask
                    bid = mt5.symbol_info_tick(sym).bid
                    
                    # Stop Largo ATR Baseado
                    sl_dist = 500 * point if 'JPY' not in sym else 50 * point
                    
                    req = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": sym,
                        "volume": 0.05, # Lote tático reduzido para momentum chasing
                        "type": mt5.ORDER_TYPE_BUY if signal['direction'] == 'BUY' else mt5.ORDER_TYPE_SELL,
                        "price": ask if signal['direction'] == 'BUY' else bid,
                        "sl": (ask - sl_dist) if signal['direction'] == 'BUY' else (bid + sl_dist),
                        "tp": 0.0, # Trailing stop fará o fechamento
                        "deviation": 20,
                        "magic": 810000,
                        "comment": "OMEGA_V8.1_SURFER",
                        "type_time": mt5.ORDER_TIME_GTC,
                        "type_filling": mt5.ORDER_FILLING_IOC
                    }
                    
                    res = mt5.order_send(req)
                    
                    # Tentar de novo com outro filling se a corretora barrar IOC
                    if res is None or res.retcode != mt5.TRADE_RETCODE_DONE:
                        req["type_filling"] = mt5.ORDER_FILLING_FOK
                        res = mt5.order_send(req)
                    
                    if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                        logging.info(f"✅ ORDEM V8.1 MERCADO EXECUTADA: {sym} | {signal['direction']} | Preço: {res.price} | Ticket: {res.order}")
                    else:
                        logging.error(f"❌ FALHA ORDEM V8.1: {res.retcode if res else 'Unknown'}")
        
        # O algoritmo agora checará o mercado ativamente a cada batida curta
        time.sleep(15)
except KeyboardInterrupt:
    logging.info("[DAEMON] Finalizando motor V8.1...")
    mt5.shutdown()
    sys.exit(0)
