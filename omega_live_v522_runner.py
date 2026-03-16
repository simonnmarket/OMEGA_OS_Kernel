
import MetaTrader5 as mt5
import time
import numpy as np
import sys
import logging
from datetime import datetime
from modules.omega_parr_f_engine import OmegaParrFEngine

# =============================================================================
# OMEGA LIVE RUNNER V5.22.0 — DEMO DEPLOYMENT
# =============================================================================
# Mandato: Execução em Tempo Real | XAUUSD | Metabolic Predator
# =============================================================================

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler("omega_live_v522.log", mode='a', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("OMEGA_LIVE")

def log_print(msg: str):
    logger.info(msg)

class OmegaLiveRunner:
    def __init__(self, symbol: str = "XAUUSD", lot_size: float = 1.0, magic: int = 20260316):
        self.symbol = symbol
        self.lot_size = lot_size
        self.magic = magic
        self.engine = OmegaParrFEngine()
        
    def initialize_mt5(self):
        if not mt5.initialize():
            log_print("[-] Falha ao inicializar MetaTrader 5")
            return False
        
        # Seleciona o símbolo (tenta com sufixos se necessário)
        if not mt5.symbol_select(self.symbol, True):
            log_print(f"[-] Símbolo {self.symbol} não encontrado. Tentando variações...")
            all_symbols = mt5.symbols_get()
            found = False
            for s in all_symbols:
                if self.symbol in s.name:
                    self.symbol = s.name
                    mt5.symbol_select(self.symbol, True)
                    log_print(f"[+] Símbolo alterado para: {self.symbol}")
                    found = True
                    break
            if not found:
                log_print("[-] Nenhum símbolo de Ouro compatível encontrado.")
                return False
        
        log_print(f"[+] Conectado ao MT5. Operando: {self.symbol}")
        return True

    def get_data(self, timeframe, count=50):
        rates = mt5.copy_rates_from_pos(self.symbol, timeframe, 0, count)
        if rates is None or len(rates) < count:
            return None
        return np.array([[r['open'], r['high'], r['low'], r['close'], float(r['tick_volume'])] for r in rates])

    def execute_order(self, direction: int, lot: float, comment: str):
        tick = mt5.symbol_info_tick(self.symbol)
        price = tick.ask if direction > 0 else tick.bid
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": lot,
            "type": mt5.ORDER_TYPE_BUY if direction > 0 else mt5.ORDER_TYPE_SELL,
            "price": price,
            "deviation": 20,
            "magic": self.magic,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            # Tenta preenchimento alternativo se falhar
            request["type_filling"] = mt5.ORDER_FILLING_RETURN
            result = mt5.order_send(request)
            
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            log_print(f"✅ ORDEM EXECUTADA: {self.symbol} | Dir: {direction} | Ticket: {result.order}")
            return True
        else:
            log_print(f"❌ FALHA NA ORDEM: {result.retcode} | {result.comment}")
            return False

    def close_all_positions(self):
        positions = mt5.positions_get(symbol=self.symbol, magic=self.magic)
        if not positions:
            return
        for p in positions:
            order_type = mt5.ORDER_TYPE_SELL if p.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
            tick = mt5.symbol_info_tick(self.symbol)
            price = tick.bid if order_type == mt5.ORDER_TYPE_SELL else tick.ask
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": p.volume,
                "type": order_type,
                "position": p.ticket,
                "price": price,
                "deviation": 20,
                "magic": self.magic,
                "comment": "WHALE_EXIT",
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            mt5.order_send(request)
            log_print(f"🚪 POSIÇÃO ENCERRADA: {p.ticket}")

    def run(self):
        if not self.initialize_mt5():
            return

        log_print("🚀 OMEGA V5.22.0 PREDATOR ATIVO EM CONTA DEMO")
        
        try:
            while True:
                # 1. Sync Data
                data_m15 = self.get_data(mt5.TIMEFRAME_M15, 20)
                data_h1 = self.get_data(mt5.TIMEFRAME_H1, 10)
                data_h4 = self.get_data(mt5.TIMEFRAME_H4, 10)
                
                if data_m15 is None or data_h1 is None or data_h4 is None:
                    time.sleep(10)
                    continue
                
                # 2. Audit OMEGA Engine (V5.22.0)
                audit = self.engine.execute_audit(data_m15)
                
                # 3. Confluência Hierárquica
                h4_dir = 1 if data_h4[-1, 3] > np.mean(data_h4[:, 3]) else -1
                h1_dir = 1 if data_h1[-1, 3] > data_h1[-2, 3] else -1
                
                # 4. Monitoramento de Posição Ativa
                current_pos = mt5.positions_get(symbol=self.symbol, magic=self.magic)
                
                if not current_pos:
                    # GATILHO DE ENTRADA SNIPER
                    if audit['launch'] and audit['bias'] == h4_dir and h1_dir == h4_dir:
                        log_print(f"🎯 ALVO DETECTADO: Estado {audit['state']} | Gatilho Atômico!")
                        self.execute_order(audit['bias'], self.lot_size, f"OMEGA_{audit['state']}")
                else:
                    # GESTÃO DE SAÍDA (OECG Vision)
                    p = current_pos[0]
                    # Se inércia H1 inverter ou estado voltar ao Repouso, sai do movimento.
                    if h1_dir != (1 if p.type == mt5.ORDER_TYPE_BUY else -1) or audit['state'] == "REPOUSO":
                        log_print("🌊 ONDA ENCERRADA: Reversão ou Repouso detectado.")
                        self.close_all_positions()

                # Telemetria a cada 10 segundos
                if int(time.time()) % 10 == 0:
                    status = "LIVE" if mt5.terminal_info().connected else "DISCONNECTED"
                    equity = mt5.account_info().equity
                    log_print(f"🛰️ STATUS: {status} | Equity: {equity:,.2f} | Pos: {len(current_pos)} | State: {audit['state']}")
                
                time.sleep(2)
                
        except KeyboardInterrupt:
            log_print("🛑 Shutdown Manual solicitado.")
        finally:
            mt5.shutdown()

if __name__ == "__main__":
    runner = OmegaLiveRunner(lot_size=1.0) # Iniciando com 1.0 Lote Demo
    runner.run()
