import MetaTrader5 as mt5
import time
import sys
import numpy as np
import socket
import os
import logging
import atexit
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from run_aic_v5_master import OmegaAICControllerV5
from modules.v_flow_microstructure import MacroBias

# =============================================================================
# LOGGING INSTITUCIONAL (Audit Trail TIER-0)
# =============================================================================
log_file = "omega_v5.2_audit.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='a', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("OMEGA_TIER0")

def log_print(msg: str):
    logger.info(msg)

# =============================================================================
# SINGLETON LOCK ROBUSTO (CQO Issue #4/5)
# =============================================================================
class SingletonLock:
    def __init__(self, port: int = 50051):
        self.port = port
        self.sock = None

    def __enter__(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # REMOVIDO SO_REUSEADDR conforme diretriz CQO para evitar bypass
            self.sock.bind(('127.0.0.1', self.port))
            self.sock.listen(1)
            return self
        except socket.error:
            log_print(f"🚫 ERRO CRÍTICO: OMEGA já está rodando! Port {self.port} ocupado.")
            sys.exit(1)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.sock:
            self.sock.close()

# =============================================================================
# TACTICAL SCALER (Protocolo CQO/COO - Histerese + Progressão + Refractory)
# =============================================================================
class TacticalScaler:
    def __init__(self, h_low: float = 85.0, h_high: float = 95.0):
        self.scale_levels = {
            1: {"legs": 3, "wait_min": 0, "label": "RECON", "lot_mult": 0.5},
            2: {"legs": 6, "wait_min": 5, "label": "SQUAD", "lot_mult": 0.8},
            3: {"legs": 9, "wait_min": 10, "label": "PLATOON", "lot_mult": 1.0},
            4: {"legs": 12, "wait_min": 15, "label": "COMPANY", "lot_mult": 1.2},
            5: {"legs": 15, "wait_min": 20, "label": "BATTALION", "lot_mult": 1.5},
            6: {"legs": 18, "wait_min": 30, "label": "BRIGADE", "lot_mult": 2.0}
        }
        self.current_level = 0
        self.score_start_time = None
        self.h_low = h_low
        self.h_high = h_high
        self.refractory_end = None

    def update(self, score: float, now: datetime) -> Dict:
        # 1. Cooldown Anti-Loop (COO)
        if self.refractory_end and now < self.refractory_end:
            return {"legs": 0, "label": "REFRACTORY", "lot_mult": 0.0}

        # 2. Histerese de Reset (CQO Issue #1)
        if score < self.h_low:
            if self.current_level > 0:
                log_print(f"📉 Reset Scaler: Score {score:.1f} < Threshold {self.h_low}")
            self.score_start_time = None
            self.current_level = 0
            self.refractory_end = now + timedelta(minutes=5)
            return {"legs": 1, "label": "SINGLE_SHOT", "lot_mult": 0.3}

        # 3. Histerese de Ativação
        if self.score_start_time is None:
            if score >= self.h_high:
                self.score_start_time = now
                self.current_level = 1
                return self.scale_levels[1]
            return {"legs": 1, "label": "SINGLE_SHOT", "lot_mult": 0.3}

        # 4. Progressão Real Sem Jumping (CQO Issue #2)
        elapsed = (now - self.score_start_time).total_seconds() / 60.0
        max_next = min(self.current_level + 1, 6)
        
        if elapsed >= self.scale_levels[max_next]["wait_min"]:
            self.current_level = max_next
            log_print(f"📈 Level UP: {self.scale_levels[self.current_level]['label']} (Legs: {self.scale_levels[self.current_level]['legs']})")

        return self.scale_levels[self.current_level]

# =============================================================================
# EXECUTOR HFT (Protocolo COO/CFO - Fallback + Trailing + Profit Lock)
# =============================================================================
class HFTExecutor:
    def __init__(self, base_lot: float = 0.05, magic: int = 500500):
        self.base_lot = base_lot
        self.magic = magic

    def check_exposure(self, symbol: str, lot: float, direction: int, active_symbols: list) -> bool:
        """CQO Issue #7: Hard Cap Leverage 5.0x"""
        account = mt5.account_info()
        if not account: return False
        
        total_notional = 0
        all_pos = mt5.positions_get()
        if all_pos:
            for p in all_pos:
                if p.magic == self.magic:
                    # Nocional simplificado (vol * price * contract_size)
                    total_notional += p.volume * p.price_open * 100
        
        # Projeção nova ordem
        price = mt5.symbol_info_tick(symbol).ask if direction > 0 else mt5.symbol_info_tick(symbol).bid
        new_notional = lot * price * 100
        
        leverage = (total_notional + new_notional) / account.equity
        if leverage > 5.0:
            log_print(f"⚠️ LEVERAGE CAP: {leverage:.2f}x EXCEDIDO. BLOQUEANDO ORDEM.")
            return False
        return True

    def execute_hft_order(self, symbol: str, direction: int, lot: float, sl: float, tp: float, label: str):
        """COO: Triple Fallback (FOK -> IOC -> RETURN)"""
        price = mt5.symbol_info_tick(symbol).ask if direction > 0 else mt5.symbol_info_tick(symbol).bid
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": mt5.ORDER_TYPE_BUY if direction > 0 else mt5.ORDER_TYPE_SELL,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 10,
            "magic": self.magic,
            "comment": f"V5_{label}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK, # Primeira tentativa
        }

        # Fallback 1: FOK
        res = mt5.order_send(request)
        if res and res.retcode == mt5.TRADE_RETCODE_DONE: return True

        # Fallback 2: IOC
        request["type_filling"] = mt5.ORDER_FILLING_IOC
        res = mt5.order_send(request)
        if res and res.retcode == mt5.TRADE_RETCODE_DONE: return True

        # Fallback 3: RETURN (Padrão)
        request["type_filling"] = mt5.ORDER_FILLING_RETURN
        res = mt5.order_send(request)
        return res and res.retcode == mt5.TRADE_RETCODE_DONE

    def trailing_atr(self, symbol: str, atr: float):
        """CFO: Profit-Taking & Trailing"""
        positions = mt5.positions_get(symbol=symbol)
        if not positions: return
        
        tick = mt5.symbol_info_tick(symbol)
        for p in positions:
            if p.magic != self.magic: continue
            
            # Trailing Stop dinâmico
            dist = atr * 1.5
            if p.type == mt5.ORDER_TYPE_BUY:
                new_sl = tick.bid - dist
                if new_sl > p.sl + (atr * 0.1): # Update mínimo
                    mt5.order_send({"action": mt5.TRADE_ACTION_SLTP, "position": p.ticket, "sl": new_sl, "tp": p.tp})
            else:
                new_sl = tick.ask + dist
                if new_sl < p.sl - (atr * 0.1):
                    mt5.order_send({"action": mt5.TRADE_ACTION_SLTP, "position": p.ticket, "sl": new_sl, "tp": p.tp})

# =============================================================================
# DEPLOY PRINCIPAL (Tech Lead Resiliência Loop)
# =============================================================================
def live_deploy_alfa_18():
    with SingletonLock(port=50051):
        log_print("🚀 OMEGA V5.2 ALFA-18: MOTOR INSTITUCIONAL ATIVO")
        
        if not mt5.initialize():
            log_print("💥 FALHA MT5")
            sys.exit(1)

        raw_list = ["XAUUSD", "XAGUSD", "EURUSD", "GBPUSD", "USDJPY"]
        active_symbols = []
        for s in raw_list:
            # CQO Issue #6: Match Exato
            if mt5.symbol_select(s, True):
                active_symbols.append(s)
                log_print(f"✅ ATIVO VALIDADO: {s}")
        
        controllers = {s: OmegaAICControllerV5() for s in active_symbols}
        scalers = {s: TacticalScaler() for s in active_symbols}
        executor = HFTExecutor(base_lot=0.05)
        
        try:
            while True:
                # CQO/CFO: Check Circuit Breaker (3% Max Drawdown Diário)
                acc = mt5.account_info()
                if acc and (acc.equity - acc.balance) / acc.balance < -0.03:
                    log_print("🚨 CIRCUIT BREAKER: DRAWDOWN DIÁRIO 3% EXCEDIDO. HALT GLOBAL.")
                    for s in active_symbols:
                        executor.hft_order_close_all(s) # Implementado no sensei
                    time.sleep(3600)
                    continue

                for symbol in active_symbols:
                    try: # Tech Lead: Isolamento de Erro por Símbolo
                        ctrl = controllers[symbol]
                        
                        # Data Fetch
                        rates_m1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 150)
                        rates_m15 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 500)
                        if rates_m1 is None or rates_m15 is None: continue
                        
                        ohlcv_m1 = np.array([[r['open'], r['high'], r['low'], r['close'], float(r['tick_volume'])] for r in rates_m1])
                        ohlcv_m15 = np.array([[r['open'], r['high'], r['low'], r['close'], float(r['tick_volume'])] for r in rates_m15])
                        
                        # Análise Kernel
                        macro_state = ctrl.omega_kernel.engine_step(ohlcv_m15)
                        bias = MacroBias(
                            hurst=macro_state.details.get('hfd', 0.5),
                            kalman_trend=1 if ctrl.kalman_engine.execute(ohlcv_m15)['velocity'] > 0 else -1,
                            strength=macro_state.signal_strength
                        )
                        
                        latest = rates_m1[-1]
                        thrust = ctrl.get_thrust_vector(ohlcv_m1, {'close': latest['close']}, bias)
                        
                        # Scaler Update
                        scaling = scalers[symbol].update(thrust['thrust_score'], datetime.now())
                        
                        # Execução - Filtro Spread (CIO)
                        info = mt5.symbol_info(symbol)
                        if info.spread > 50: 
                            continue
                        
                        # Entry Logic
                        positions = mt5.positions_get(symbol=symbol)
                        my_pos = [p for p in positions if p.magic == executor.magic] if positions else []
                        
                        if thrust['launch'] and len(my_pos) < scaling['legs']:
                            # Calculo SL/TP Dinâmico
                            atr = np.std(ohlcv_m1[:, 3][-20:]) * 4.0
                            direction = thrust['direction']
                            lot = executor.base_lot * scaling['lot_mult']
                            
                            if executor.check_exposure(symbol, lot, direction, active_symbols):
                                sl = latest['close'] - (atr * 1.2) if direction > 0 else latest['close'] + (atr * 1.2)
                                tp = latest['close'] + (atr * 3.0) if direction > 0 else latest['close'] - (atr * 3.0)
                                executor.execute_hft_order(symbol, direction, lot, sl, tp, scaling['label'])
                        
                        # Shadow/Trailing Logic
                        if my_pos:
                            executor.trailing_atr(symbol, np.std(ohlcv_m1[:, 3][-20:]))
                            
                    except Exception as e:
                        log_print(f"❌ Erro em {symbol}: {e}")
                        continue
                
                # Adaptive Sleep (Tech Lead Issue #9)
                time.sleep(10) # 10s para M1 HFT
                
        except KeyboardInterrupt:
            log_print("🛑 Shutdown.")
        finally:
            mt5.shutdown()

if __name__ == "__main__":
    live_deploy_alfa_18()
n()

if __name__ == "__main__":
    live_aerospace_deploy_multi()
