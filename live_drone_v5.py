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
log_file = "omega_v5.3_audit.log"
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
# EXECUTOR HFT (Protocolo CFO/SRE - FASE A SANDBOX REFINADO)
# =============================================================================
class HFTExecutor:
    def __init__(self, base_lot: float = 0.05, magic: int = 500500):
        self.base_lot = base_lot
        self.magic = magic
        self.daily_drawdown_limit = 0.015
        self.start_day_balance = None
        self.last_day = None

    def _sync_daily_balance(self):
        """Monitora o balanço de abertura do dia real."""
        now = datetime.now()
        if self.last_day != now.day:
            acc = mt5.account_info()
            if acc:
                self.start_day_balance = acc.balance
                self.last_day = now.day
                log_print(f"📅 Novo Dia Detectado. Balanço Inicial: ${self.start_day_balance:,.2f}")

    def check_circuit_breaker(self, symbol: str, atr: float) -> bool:
        self._sync_daily_balance()
        account = mt5.account_info()
        if not account or self.start_day_balance is None: return False
        
        # 1. Check Drawdown Diário Real
        equity_change = (account.equity - self.start_day_balance) / self.start_day_balance
        if equity_change < -self.daily_drawdown_limit:
            log_print(f"🚨 CIRCUIT BREAKER: DD DIÁRIO {equity_change*100:.2f}% > LIMIT {self.daily_drawdown_limit*100:.2f}%.")
            self.hft_order_close_all(symbol)
            return False
            
        # 2. Check Gap Protection
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 1, 1)
        if rates is None or len(rates) == 0: return False
        
        tick = mt5.symbol_info_tick(symbol)
        last_price = rates[0]['close']
        gap = abs(tick.bid - last_price)
        if gap > 3 * max(atr, 0.0001):
            log_print(f"⚠️ GAP PROTECTION: Gap {gap:.4f} > 3x ATR. Bloqueando.")
            return False
            
        return True

    def check_exposure(self, symbol: str, lot: float, direction: int, atr: float) -> bool:
        account = mt5.account_info()
        info = mt5.symbol_info(symbol)
        if not account or not info: return False
        
        # 1. Spread Filter
        spread_pts = info.spread * info.point
        spread_atr_ratio = spread_pts / (atr + 1e-10)
        if spread_atr_ratio > 0.10:
            log_print(f"⚠️ SPREAD FILTER: Ratio {spread_atr_ratio:.2f} > 0.10. Abortando.")
            return False

        # 2. Notional com Posições + Ordens Pendentes (CQO Fix)
        total_notional = 0
        positions = mt5.positions_get(symbol=symbol, magic=self.magic)
        orders = mt5.orders_get(symbol=symbol, magic=self.magic)
        
        contract_size = info.trade_contract_size
        
        if positions:
            for p in positions:
                total_notional += p.volume * p.price_open * contract_size
        
        if orders:
            for o in orders:
                total_notional += o.volume_initial * o.price_open * contract_size
        
        tick = mt5.symbol_info_tick(symbol)
        price = tick.ask if direction > 0 else tick.bid
        new_notional = lot * price * contract_size
        leverage = (total_notional + new_notional) / account.equity
        
        if leverage > 5.0:
            log_print(f"⚠️ LEVERAGE CAP: {leverage:.2f}x Excedido em {symbol}.")
            return False
        return True

    def execute_hft_order(self, symbol: str, direction: int, lot: float, sl: float, tp: float, label: str, atr: float):
        if not self.check_circuit_breaker(symbol, atr): return False

        tick = mt5.symbol_info_tick(symbol)
        price = tick.ask if direction > 0 else tick.bid
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": mt5.ORDER_TYPE_BUY if direction > 0 else mt5.ORDER_TYPE_SELL,
            "price": price,
            "sl": round(sl, 2),
            "tp": round(tp, 2),
            "deviation": 20,
            "magic": self.magic,
            "comment": f"V5.3_{label}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        res = mt5.order_send(request)
        if res is None or res.retcode != mt5.TRADE_RETCODE_DONE:
            log_print(f"❌ ORDER FAIL: {symbol} | Code: {getattr(res, 'retcode', 'UNKNOWN')} | {getattr(res, 'comment', 'NOVAL')}")
            return False
        
        log_print(f"✅ ORDER EXECUTED: {symbol} {label} | Ticket: {res.order}")
        return True

    def hft_order_close_all(self, symbol: str):
        positions = mt5.positions_get(symbol=symbol, magic=self.magic)
        if not positions: return
        for p in positions:
            order_type = mt5.ORDER_TYPE_SELL if p.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
            tick = mt5.symbol_info_tick(symbol)
            price = tick.bid if order_type == mt5.ORDER_TYPE_SELL else tick.ask
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": p.volume,
                "type": order_type,
                "position": p.ticket,
                "price": price,
                "deviation": 20,
                "magic": self.magic,
                "comment": "EJECT_ALL",
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            mt5.order_send(request)

# =============================================================================
# DEPLOY PRINCIPAL
# =============================================================================
def live_deploy_sandbox():
    with SingletonLock(port=50051):
        log_print("🚀 OMEGA V5.3 FASE A: SANDBOX ATIVO (ATOMIC UPGRADE)")
        
        if not mt5.initialize():
            log_print("💥 FALHA MT5")
            sys.exit(1)

        active_symbols = ["XAUUSD"]
        controllers = {s: OmegaAICControllerV5() for s in active_symbols}
        executor = HFTExecutor(base_lot=0.01)
        
        try:
            while True:
                if not mt5.terminal_info().connected:
                    time.sleep(5); continue

                for symbol in active_symbols:
                    try:
                        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 150)
                        if rates is None or len(rates) < 150: continue
                        
                        ohlcv = np.array([[r['open'], r['high'], r['low'], r['close'], float(r['tick_volume'])] for r in rates])
                        if np.any(np.isnan(ohlcv)): continue

                        # AIC Controller (Atomic PARR-F)
                        ctrl = controllers[symbol]
                        latest = rates[-1]
                        thrust = ctrl.get_thrust_vector(ohlcv, latest, None)
                        
                        curr_atr = thrust.get('atr', 0.1)
                        
                        # Monitoramento de Posições
                        my_pos = mt5.positions_get(symbol=symbol, magic=executor.magic) or []
                        
                        # Entry Logic
                        if thrust['launch'] and len(my_pos) < 18:
                            dir = thrust['direction']
                            if executor.check_exposure(symbol, 0.01, dir, curr_atr):
                                sl = latest['close'] - (curr_atr * 2.0 * dir)
                                tp = latest['close'] + (curr_atr * 5.0 * dir)
                                executor.execute_hft_order(symbol, dir, 0.01, sl, tp, "ATOMIC", curr_atr)
                                
                    except Exception as e:
                        log_print(f"❌ Erro {symbol}: {e}")
                
                if int(time.time()) % 60 < 10:
                    log_print(f"🛰️ CFOSandbox | Equity: {mt5.account_info().equity:.2f} | P: {len(mt5.positions_get())}")
                time.sleep(1)
                
        except KeyboardInterrupt:
            log_print("🛑 Shutdown Manual.")
        finally:
            mt5.shutdown()

if __name__ == "__main__":
    live_deploy_sandbox()
