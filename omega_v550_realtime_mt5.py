import MetaTrader5 as mt5
import time
import sys
import numpy as np
import pandas as pd
import os
import logging
import socket
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Importar Módulos da Blindagem V5.5.0
from cost_oracle_v550 import CostOracle, CostSnapshot
from omega_parr_f_engine import OmegaParrFEngine

# =============================================================================
# CONFIGURAÇÃO DE MISSÃO (V5.5.0 ATOMIC)
# =============================================================================
CONFIG = {
    'SYMBOL': "XAUUSD",
    'MAGIC': 550550,
    'BASE_LOT': 0.01,
    'ENTRY_SCORE': 40.0,
    'Z_GUARD': 0.15,
    'HOLD_LOCK_S': 60,
    'DEBOUNCE_S': 60,
    'HARD_SL_PTS': 500,
    'LOOP_SLEEP_S': 1.0,
    'MAX_RETRIES': 5
}

# =============================================================================
# LOGGING REAL-TIME OMEGA V5.5.0
# =============================================================================
log_file = "omega_v550_realtime.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='a', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("OMEGA_V550")

def log_print(msg: str):
    logger.info(msg)

# =============================================================================
# SINGLETON LOCK (Proteção Anti-Fantasma)
# =============================================================================
class SingletonLock:
    def __init__(self, port: int = 55555):
        self.port = port
        self.sock = None

    def __enter__(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind(('127.0.0.1', self.port))
            self.sock.listen(1)
            return self
        except socket.error:
            print("🚫 OMEGA V5.5.0: OUTRA INSTÂNCIA DETECTADA. ABORTANDO.")
            sys.exit(1)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.sock: self.sock.close()

# =============================================================================
# ATOMIC CORE EXECUTOR (Blindagem NASA V5.5.0)
# =============================================================================
class AtomicExecutorV550:
    def __init__(self, oracle: CostOracle):
        self.oracle = oracle
        self.cfg = CONFIG
        self.last_exit_time = datetime(2010, 1, 1)
        self.is_busy = False # [1] Trava de Memória Local

    def check_entry(self, score: float, now: datetime) -> bool:
        if self.is_busy: return False
        if (now - self.last_exit_time).total_seconds() < self.cfg['DEBOUNCE_S']:
            return False
        return score >= self.cfg['ENTRY_SCORE']

    def check_exit(self, position, score: float, zp: float, now: datetime) -> tuple[bool, str]:
        duration = (now - datetime.fromtimestamp(position.time)).total_seconds()
        
        # 1. Hard SL Protection (Double check local)
        tick = mt5.symbol_info_tick(self.cfg['SYMBOL'])
        if position.type == mt5.ORDER_TYPE_BUY:
            pts_pnl = (tick.bid - position.price_open) * 100
        else:
            pts_pnl = (position.price_open - tick.ask) * 100
            
        if pts_pnl <= -self.cfg['HARD_SL_PTS']:
            return True, "STOP_LOSS"

        # 2. Alpha Eject + Hold Lock
        if duration < self.cfg['HOLD_LOCK_S']:
            return False, ""
            
        # Z-Guard Bypass (Only for profit)
        if position.profit > 0 and abs(zp) > self.cfg['Z_GUARD']:
            return False, ""
            
        # Cost Filter via Oracle
        costs = self.oracle.effective_cost(self.cfg['SYMBOL'], "buy", position.volume, duration/(24*3600))
        if position.profit > 0 and position.profit < costs['total_cost'] * 1.2:
            return False, ""
            
        if score < self.cfg['ENTRY_SCORE']:
            return True, "ALPHA_EJECT"
            
        return False, ""

    def execute_buy(self):
        tick = mt5.symbol_info_tick(self.cfg['SYMBOL'])
        if not tick: return False
        
        self.is_busy = True # Trava instantânea
        sl = tick.ask - (self.cfg['HARD_SL_PTS'] * 0.01)
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.cfg['SYMBOL'],
            "volume": self.cfg['BASE_LOT'],
            "type": mt5.ORDER_TYPE_BUY,
            "price": tick.ask,
            "sl": sl,
            "magic": self.cfg['MAGIC'],
            "comment": "OMEGA_V550_ALPHA",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        res = mt5.order_send(request)
        if res.retcode == mt5.TRADE_RETCODE_DONE:
            log_print(f"📥 POSIÇÃO ABERTA: {self.cfg['SYMBOL']} @ {tick.ask} | SL: {sl} | ID: {res.order}")
            return True
        
        # Fallback para FOK
        request["type_filling"] = mt5.ORDER_FILLING_FOK
        res = mt5.order_send(request)
        if res.retcode == mt5.TRADE_RETCODE_DONE:
            log_print(f"📥 POSIÇÃO ABERTA (FOK): {self.cfg['SYMBOL']} @ {tick.ask} | ID: {res.order}")
            return True

        self.is_busy = False # Libera se falhar
        log_print(f"❌ FALHA ENTRADA: {res.retcode} | {res.comment}")
        return False

    def execute_close(self, position, reason: str):
        tick = mt5.symbol_info_tick(self.cfg['SYMBOL'])
        order_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        price = tick.bid if position.type == mt5.ORDER_TYPE_BUY else tick.ask
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.cfg['SYMBOL'],
            "volume": position.volume,
            "type": order_type,
            "position": position.ticket,
            "price": price,
            "deviation": 20,
            "magic": self.cfg['MAGIC'],
            "comment": f"OMEGA_{reason}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        res = mt5.order_send(request)
        if res.retcode == mt5.TRADE_RETCODE_DONE:
            log_print(f"📤 SAÍDA [{reason}]: {self.cfg['SYMBOL']} Net ${position.profit:.2f}")
            self.last_exit_time = datetime.now()
            self.is_busy = False
            return True

        # Retry FOK
        request["type_filling"] = mt5.ORDER_FILLING_FOK
        res = mt5.order_send(request)
        if res.retcode == mt5.TRADE_RETCODE_DONE:
            log_print(f"📤 SAÍDA FOK [{reason}]: Net ${position.profit:.2f}")
            self.last_exit_time = datetime.now()
            self.is_busy = False
            return True
            
        log_print(f"❌ FALHA SAÍDA: {res.retcode} | {res.comment}")
        return False

# =============================================================================
# LIVE DEPLOY V5.5.0 REALTIME (XAUUSD DEMO)
# =============================================================================
def run_live_realtime():
    log_print("🛰️ OMEGA V5.5.0 ATOMIC: INICIANDO CONEXÃO REALTIME...")
    
    # Validação MT5
    if not mt5.initialize():
        log_print("💥 ERRO CRÍTICO: Falha ao inicializar MT5.")
        return

    # Check Account
    acc = mt5.account_info()
    if not acc:
        log_print("💥 ERRO CRÍTICO: Conta não encontrada.")
        mt5.shutdown()
        return
    log_print(f"✅ CONECTADO: Conta {acc.login} | Broker: {acc.company} | Equity: {acc.equity}")

    # Check Symbol
    symbol_info = mt5.symbol_info(CONFIG['SYMBOL'])
    if not symbol_info:
        log_print(f"💥 ERRO CRÍTICO: Símbolo {CONFIG['SYMBOL']} não encontrado.")
        mt5.shutdown()
        return
    if not symbol_info.visible:
        mt5.symbol_select(CONFIG['SYMBOL'], True)

    # Setup Oráculo
    oracle = CostOracle()
    oracle.set_snapshot(CostSnapshot(
        symbol=CONFIG['SYMBOL'], spread_points=25, slippage_points=5,
        commission_per_lot=7, swap_long_per_day=-15, swap_short_per_day=5,
        pip_value=1.0, lot_size=100
    ))
    
    engine = OmegaParrFEngine()
    executor = AtomicExecutorV550(oracle)
    
    try:
        while True:
            # Heartbeat de Conexão
            if not mt5.terminal_info().connected:
                log_print("🚨 TERMINAL DESCONECTADO. Aguardando...")
                time.sleep(5)
                continue

            # 1. Obter Dados M1 para o Kernel
            rates = mt5.copy_rates_from_pos(CONFIG['SYMBOL'], mt5.TIMEFRAME_M1, 0, 300)
            if rates is None or len(rates) < 210:
                time.sleep(1)
                continue
                
            df_rates = pd.DataFrame(rates)
            df_rates['time'] = pd.to_datetime(df_rates['time'], unit='s')
            
            # 2. Rodar Auditoria Forensic
            # results = engine.run_forensic_audit(df_rates) # Original
            results = engine.execute_audit(df_rates) # Alias Seguro
            current_metrics = results[-1]
            score = current_metrics['score_final']
            zp = current_metrics['z_vol_log']
            now = datetime.now()
            
            # 3. Gerenciamento de Posições (Apenas do nosso Magic)
            positions = mt5.positions_get(symbol=CONFIG['SYMBOL'])
            my_pos = [p for p in positions if p.magic == CONFIG['MAGIC']] if positions else []
            
            # [8] Trava de Unicidade de Posição
            if not my_pos:
                if executor.check_entry(score, now):
                    executor.execute_buy()
            else:
                # Gerenciar saída da posição ativa
                pos = my_pos[0] 
                should_exit, reason = executor.check_exit(pos, score, zp, now)
                if should_exit:
                    executor.execute_close(pos, reason)

            # Telemetria Periódica
            if int(time.time()) % 60 < 2:
                acc_now = mt5.account_info()
                log_print(f"💎 OMEGA V5.5 | Eq: {acc_now.equity:.2f} | Score: {score:.1f} | ZP: {zp:.2f} | P: {len(my_pos)}")

            time.sleep(CONFIG['LOOP_SLEEP_S'])
            
    except Exception as e:
        log_print(f"🚨 EXCEÇÃO EM RUNTIME: {str(e)}")
    except KeyboardInterrupt:
        log_print("🛑 SHUTDOWN SOLICITADO PELO COMANDANTE.")
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    with SingletonLock(port=55555):
        run_live_realtime()
