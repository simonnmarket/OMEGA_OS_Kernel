import MetaTrader5 as mt5
import time
import sys
import numpy as np
import pandas as pd
import os
import logging
import socket
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Importar Módulos da Blindagem V5.5.0
from cost_oracle_v550 import CostOracle, CostSnapshot
from omega_parr_f_engine import OmegaParrFEngine

# =============================================================================
# CONFIGURAÇÃO DE MISSÃO (MULTI-TIMEFRAME PLAYBOOK V5.5.0)
# =============================================================================
PROFILES = {
    "M1_INTRADAY": {
        'SYMBOL': "XAUUSD",
        'MAGIC': 550551,
        'TIMEFRAME': mt5.TIMEFRAME_M1,
        'TIMEFRAME_STR': "M1",
        'BASE_LOT': 0.03,        
        'ENTRY_SCORE': 55.0,     # Reduzido para capturar o fluxo de tendência maciça sem exigência extrema 
        'EXIT_SCORE': 45.0,      
        'Z_GUARD': 1.0,          
        'HOLD_LOCK_S': 300,      # Apenas 5 minutos de espera mínima
        'DEBOUNCE_S': 60,        # Apenas 60s de bloqueio para permitir re-entradas com fluxo claro
        'HARD_SL_PTS': 500,      # SL mantido na proporção M1 (500 pts = -$15.00 a 0.03 lots)
        'TP_PTS': 2000,          # Adicionado Take Profit Massivo intraday (2000 pts)
        'LOOP_SLEEP_S': 1.0,
        'MAX_RETRIES': 5,
        'Z_PRICE_T': 1.6,        # Thrust normalizado (ignorar ultra ruído que previne momentum de deslize lento)
        'PORT': 55555            
    },
    "H1_SWING": {
        'SYMBOL': "XAUUSD",
        'MAGIC': 550552,
        'TIMEFRAME': mt5.TIMEFRAME_H1,
        'TIMEFRAME_STR': "H1",
        'BASE_LOT': 0.05,        # Aumentado o aproveitamento do longo prazo
        'ENTRY_SCORE': 55.0,     # Aberto para absorção de Macro Lento
        'EXIT_SCORE': 45.0,      
        'Z_GUARD': 0.8,          
        'HOLD_LOCK_S': 3600,     # Hold lock mínimo (1 hora)
        'DEBOUNCE_S': 60,        # Apenas 60s para reagrupar capital e tentar no próximo recuo
        'HARD_SL_PTS': 2000,     # Espaço amplo
        'TP_PTS': 6000,          # Take profit para Swing H1 massivo de 6000 pts
        'LOOP_SLEEP_S': 5.0,
        'MAX_RETRIES': 5,
        'Z_PRICE_T': 1.6,        
        'PORT': 55556            
    }
}

# =============================================================================
# LOGGING BLINDADO COM AUDITORIA
# =============================================================================
logging.basicConfig(
    filename='omega_v550_realtime.log',
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

def log_print(msg):
    print(msg)
    logging.info(msg)

# =============================================================================
# TRAVA DE HARDWARE (ATOMIC SINGLETON)
# =============================================================================
class SingletonLock:
    """ Trava de socket atômica para impedir ordens fantasmas de processos zumbis """
    def __init__(self, port):
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
    def __enter__(self):
        try:
            self.sock.bind(('127.0.0.1', self.port))
            return self
        except socket.error:
            print(f"🚫 OMEGA V5.5.0: OUTRA INSTÂNCIA DETECTADA NA PORTA {self.port}. ABORTANDO.")
            logging.error(f"Tentativa de concorrência detectada. Abortado pelo SingletonLock na porta {self.port}.")
            sys.exit(1)
            
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sock.close()

# =============================================================================
# EXECUTOR ATÔMICO
# =============================================================================
class AtomicExecutorV550:
    def __init__(self, oracle: CostOracle, config: Dict):
        self.oracle = oracle
        self.cfg = config
        self.last_exit_time = datetime(2000, 1, 1)
        self.is_busy = False # Trava de Software para Race Conditions intra-processo

    def get_my_positions(self):
        pos = mt5.positions_get(symbol=self.cfg['SYMBOL'])
        if pos is None: return []
        return [p for p in pos if p.magic == self.cfg['MAGIC']]

    def evaluate_exit(self, position, score: float, z_price: float, duration_s: float) -> Tuple[bool, str]:
        raw_pnl_usd = position.profit
        
        # Calcular os custos reais usando CostOracle
        direction = 'buy' if position.type == mt5.ORDER_TYPE_BUY else 'sell'
        costs = self.oracle.effective_cost(self.cfg['SYMBOL'], direction, position.volume, duration_s / 86400.0)
        total_cost_usd = costs['total_cost']
        net_profit_usd = raw_pnl_usd - total_cost_usd
        
        # Opcional: Ejetar se custo ultrapassou 35% do valor do trade em intraday (Monitoramento contínuo)
        # Alpha Ejection Logic (Saída antes do SL)
        if duration_s >= self.cfg['HOLD_LOCK_S'] and score < self.cfg['EXIT_SCORE']:
            reversing = (position.type == mt5.ORDER_TYPE_BUY and z_price < -self.cfg['Z_GUARD']) or \
                        (position.type == mt5.ORDER_TYPE_SELL and z_price > self.cfg['Z_GUARD'])
                        
            # Exige que saia se a lógica virou, preferencialmente sem arcar com lucros engolidos pelo custo
            if reversing or net_profit_usd > (0.4 * self.cfg['BASE_LOT'] * 100): 
                return True, f"ALPHA_EJECT [NET_PROFIT: ${net_profit_usd:.2f}]"
        
        # Stop de Fricção (Abortar se a fricção corrói excessivamente a viabilidade sem engatar movimento)
        # Se raw profit for negativo mas custo for mais de 2x a perda real no spread.
        return False, ""

    def execute_trade(self, direction: str):
        tick = mt5.symbol_info_tick(self.cfg['SYMBOL'])
        if not tick: return False
        
        # Trava spread largo removida para absorção de mega fluxos. Correlacionando custo ao Potencial.
        # spread_pts = (tick.ask - tick.bid)/0.01
        # if spread_pts > 40.0:
        #     log_print(f"⚠️ SPREAD EXCESSO ({spread_pts:.1f} pts) - Abortando entrada {direction.upper()}")
        #     return False

        self.is_busy = True # Trava instantânea
        
        if direction == 'buy':
            order_type = mt5.ORDER_TYPE_BUY
            price = tick.ask
            sl = tick.ask - (self.cfg['HARD_SL_PTS'] * 0.01)
            tp = tick.ask + (self.cfg.get('TP_PTS', 3000) * 0.01)
        else:
            order_type = mt5.ORDER_TYPE_SELL
            price = tick.bid
            sl = tick.bid + (self.cfg['HARD_SL_PTS'] * 0.01)
            tp = tick.bid - (self.cfg.get('TP_PTS', 3000) * 0.01)
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.cfg['SYMBOL'],
            "volume": self.cfg['BASE_LOT'],
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "magic": self.cfg['MAGIC'],
            "comment": f"OE_V5_{self.cfg['TIMEFRAME_STR']}_{direction.upper()}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        res = mt5.order_send(request)
        if res.retcode == mt5.TRADE_RETCODE_DONE:
            log_print(f"📥 ABERTA [{direction.upper()}]: {self.cfg['SYMBOL']} @ {price} | SL: {sl} | ID: {res.order} | Ret: {res.retcode}")
            return True
        
        # Fallback para FOK
        request["type_filling"] = mt5.ORDER_FILLING_FOK
        res = mt5.order_send(request)
        if res.retcode == mt5.TRADE_RETCODE_DONE:
            slippage = abs(res.price - price) / 0.01
            log_print(f"📥 ABERTA FOK [{direction.upper()}]: {self.cfg['SYMBOL']} @ {res.price} | Escorregamento: {slippage:.1f}pts | ID: {res.order}")
            return True

        self.is_busy = False # Libera se falhar
        log_print(f"❌ FALHA ENTRADA {direction.upper()} | RetCode: {res.retcode} | {res.comment}")
        return False

    def execute_close(self, position, reason: str):
        tick = mt5.symbol_info_tick(self.cfg['SYMBOL'])
        order_type_close = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        price = tick.bid if position.type == mt5.ORDER_TYPE_BUY else tick.ask
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.cfg['SYMBOL'],
            "volume": position.volume,
            "type": order_type_close,
            "position": position.ticket,
            "price": price,
            "deviation": 20,
            "magic": self.cfg['MAGIC'],
            "comment": f"OE_V5_EXIT_{self.cfg['TIMEFRAME_STR']}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        res = mt5.order_send(request)
        if res.retcode == mt5.TRADE_RETCODE_DONE:
            log_print(f"📤 SAÍDA [{reason}]: {self.cfg['SYMBOL']} Gross ${position.profit:.2f} | ID: {res.order}")
            self.last_exit_time = datetime.now()
            self.is_busy = False
            return True

        # Retry FOK
        request["type_filling"] = mt5.ORDER_FILLING_FOK
        res = mt5.order_send(request)
        if res.retcode == mt5.TRADE_RETCODE_DONE:
            slippage = abs(res.price - price) / 0.01
            log_print(f"📤 SAÍDA FOK [{reason}]: Gross ${position.profit:.2f} | Escorregamento: {slippage:.1f}pts | ID: {res.order}")
            self.last_exit_time = datetime.now()
            self.is_busy = False
            return True
            
        log_print(f"❌ FALHA SAÍDA: RetCode: {res.retcode} | {res.comment}")
        return False

# =============================================================================
# LIVE DEPLOY V5.5.0 REALTIME (XAUUSD DEMO - MULTI-PROFILE)
# =============================================================================
def run_live_realtime(profile_name: str):
    cfg = PROFILES[profile_name]
    log_print(f"🛰️ OMEGA V5.5.0 MTF: INICIANDO CONEXÃO REALTIME | PERFIL: {profile_name} ({cfg['TIMEFRAME_STR']})")
    
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
    symbol_info = mt5.symbol_info(cfg['SYMBOL'])
    if not symbol_info:
        log_print(f"💥 ERRO CRÍTICO: Símbolo {cfg['SYMBOL']} não encontrado.")
        mt5.shutdown()
        return
    if not symbol_info.visible:
        mt5.symbol_select(cfg['SYMBOL'], True)

    # Setup Oráculo
    oracle = CostOracle()
    oracle.set_snapshot(CostSnapshot(
        symbol=cfg['SYMBOL'], spread_points=25, slippage_points=5,
        commission_per_lot=7, swap_long_per_day=-15, swap_short_per_day=5,
        pip_value=1.0, lot_size=100
    ))
    
    engine = OmegaParrFEngine()
    engine.cfg['z_price_threshold'] = cfg['Z_PRICE_T']
    
    executor = AtomicExecutorV550(oracle, cfg)
    
    try:
        while True:
            # Heartbeat de Conexão
            if not mt5.terminal_info().connected:
                log_print("🚨 TERMINAL DESCONECTADO. Aguardando...")
                time.sleep(5)
                continue

            # 1. Obter Dados Baseados no Profile
            rates = mt5.copy_rates_from_pos(cfg['SYMBOL'], cfg['TIMEFRAME'], 0, 300)
            if rates is None or len(rates) < 210:
                time.sleep(1)
                continue
                
            df_rates = pd.DataFrame(rates)
            df_rates['time'] = pd.to_datetime(df_rates['time'], unit='s')
            
            # 2. Rodar Auditoria Forensic
            results = engine.execute_audit(df_rates) 
            current_metrics = results[-1]
            score = current_metrics['score_final']
            zp = current_metrics['z_price']
            signal = current_metrics['signal']

            # 3. Trava de Unicidade
            my_pos = executor.get_my_positions()
            log_print(f"💎 [{profile_name}] Eq: {mt5.account_info().equity:.2f} | Score: {score:.1f} | ZP: {zp:.2f} | Sig: {signal.upper()} | Pos: {len(my_pos)}")
            
            if len(my_pos) > 0:
                pos = my_pos[0]
                duration_s = (datetime.now().timestamp() - pos.time)
                should_exit, reason = executor.evaluate_exit(pos, score, zp, duration_s)
                if should_exit:
                    executor.execute_close(pos, reason)
            else:
                # Entrada
                if not executor.is_busy:
                    time_since_exit = (datetime.now() - executor.last_exit_time).total_seconds()
                    
                    if time_since_exit >= cfg['DEBOUNCE_S']:
                        if score >= cfg['ENTRY_SCORE']:
                            if signal == 'buy':
                                executor.execute_trade('buy')
                            elif signal == 'sell':
                                executor.execute_trade('sell')

            time.sleep(cfg['LOOP_SLEEP_S'])

    except KeyboardInterrupt:
        log_print(f"⏹️ INTERRUPÇÃO MANUAL. ENCERRANDO PERFIL {profile_name}...")
    except Exception as e:
        log_print(f"💥 FATAL EXCEPTION no Perfil {profile_name}: {e}")
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='OMEGA V5.5.0 Multi-Timeframe Executor')
    parser.add_argument('--profile', type=str, choices=['M1_INTRADAY', 'H1_SWING'], default='H1_SWING',
                        help='Perfil de execução (default: H1_SWING)')
    args = parser.parse_args()

    # Inicia com o Singleton Lock restrito à porta daquele Profile
    # Assim podemos rodar o M1 em uma porta e o H1 simultaneamente numa porta diferente
    port_for_lock = PROFILES[args.profile]['PORT']
    with SingletonLock(port=port_for_lock):
        run_live_realtime(args.profile)
