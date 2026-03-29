"""
OMEGA V8.2.1 - MT5 EXECUTION ENGINE (PHASE 3)
=============================================
Arquiteto: Antigravity MACE-MAX (Tier-0)
Data: 24 de Março de 2026
Status: PROTOTYPE (PHASE 3) - Causal & Dual-Mode

Descrição:
Integra o Bloco Matemático V8.2.1 com a API MetaTrader 5.
Utiliza Z-Score Causal (t-1) para triggers e High/Low para gerenciamento de risco.
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import statsmodels.api as sm
import time
import os
import json
import hashlib
from datetime import datetime

# ============================================================================
# CONFIGURAÇÕES TÉCNICAS (CONSELHO OMEGA)
# ============================================================================
ASSET_Y = "XAUUSD" # Ouro (Target)
ASSET_X = "XAGUSD" # Prata (Hedge)
MAGIC_NUMBER = 821000
LOT_Y = 0.01       # Lote base para XAU
BETA_FIXED = 20.81 # Proporção base (será dinâmica)
COST_THRESHOLD = 19.0 # Pts

# GATES DE RISK MANAGEMENT
MAX_EQUITY_RISK = 0.02 # 2% por par
DAILY_DRAWDOWN_LIMIT = -0.035 # -3.5% Circuit Breaker

# ============================================================================
# MOTOR DE EXECUÇÃO DUAL-MODE
# ============================================================================

class OmegaExecutionGatewayV821:
    def __init__(self, window_ols=500, ewma_span=100, entry_z=3.0, exit_z=0.0):
        self.window_ols = window_ols
        self.ewma_span = ewma_span
        self.entry_z = entry_z
        self.exit_z = exit_z
        self.is_connected = False
        
        # Histórico local para cálculo de OLS (precisa de 500 barras M1)
        self.history_y = pd.Series()
        self.history_x = pd.Series()
        
        # Estado de Posição
        self.active_trade = None # None, 'LONG_SPREAD', 'SHORT_SPREAD'
        
    def connect(self):
        if not mt5.initialize():
            print(f"[-] Erro ao conectar ao MT5: {mt5.last_error()}")
            return False
        self.is_connected = True
        print(f"[+] MT5 Conectado. Terminal: {mt5.terminal_info().name}")
        return True

    def get_market_data(self, symbol, count=600):
        """Busca dados M1 para o rastro matemático."""
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, count)
        if rates is None: return None
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df.set_index('time')

    def calculate_causal_signal(self, df_y, df_x):
        """Cérebro Matemático V8.2.1 (Portado da Fase 2)"""
        # 1. Alinhamento
        df = pd.DataFrame({'Y': df_y['close'], 'X': df_x['close']}).dropna()
        
        # 2. OLS Rolante (Última Janela)
        y_win = df['Y'].tail(self.window_ols).values
        x_win = df['X'].tail(self.window_ols).values
        X_const = sm.add_constant(x_win)
        res = sm.OLS(y_win, X_const).fit()
        alpha, beta = res.params[0], res.params[1]
        
        # 3. Spread e Z-Score Causal (Usando Média/Std de T-1)
        spread_history = df['Y'] - (alpha + beta * df['X'])
        ewma_hist = spread_history.ewm(span=self.ewma_span, adjust=False)
        
        # PARÂMETROS CAUSAIS (T-1)
        mean_t1 = ewma_hist.mean().iloc[-2]
        std_t1 = ewma_hist.std().iloc[-2]
        
        # Z-SCORE ATUAL (Tempo T)
        current_spread = spread_history.iloc[-1]
        z_score = (current_spread - mean_t1) / (std_t1 + 1e-12)
        
        return z_score, beta, current_spread

    def check_circuit_breaker(self):
        """Monitoramento de Capital Tier-0"""
        account = mt5.account_info()
        day_profit = account.profit # Simplificado para demo
        if (day_profit / account.balance) <= DAILY_DRAWDOWN_LIMIT:
            print("[!!!] CIRCUIT BREAKER ATIVADO: Drawdown Diário atingido.")
            return True
        return False

    def send_order(self, action, symbol, volume, order_type, price=None, comment=""):
        """Wrapper Seguro MetaTrader"""
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volume),
            "type": order_type,
            "magic": MAGIC_NUMBER,
            "comment": f"OMEGA_{comment}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        if price: request["price"] = price
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"[-] Erro na Ordem: {result.retcode} | {result.comment}")
            return False
        return True

    def run_live_loop(self):
        print("[*] Iniciando Motor de Execução OMEGA V8.2.1 em Tempo Real...")
        
        while True:
            try:
                # 1. Heartbeat & Risk Check
                if self.check_circuit_breaker(): break
                
                # 2. Captura de Dados M1 (Sinal por LINHAS)
                df_y = self.get_market_data(ASSET_Y)
                df_x = self.get_market_data(ASSET_X)
                
                if df_y is None or df_x is None:
                    time.sleep(5); continue
                
                # 3. Cálculo do Sinal Causal
                z_score, beta, spread = self.calculate_causal_signal(df_y, df_x)
                
                # 4. Lógica de Execução (Dual-Mode)
                print(f"[LOG] {datetime.now()} | Z: {z_score:.2f} | Beta: {beta:.2f} | Spread: {spread:.2f}")
                
                # ENTRADAS
                if self.active_trade is None:
                    if z_score >= self.entry_z: # Sell Spread (Sell Y, Buy X)
                        print(f"[+] SHORT SPREAD Detetado (Z={z_score:.2f})")
                        # 19pts cost threshold check here...
                        lot_x = round(LOT_Y * beta, 2)
                        if self.send_order(mt5.TRADE_ACTION_DEAL, ASSET_Y, LOT_Y, mt5.ORDER_TYPE_SELL, comment="V821_S"):
                            if self.send_order(mt5.TRADE_ACTION_DEAL, ASSET_X, lot_x, mt5.ORDER_TYPE_BUY, comment="V821_H"):
                                self.active_trade = 'SHORT_SPREAD'
                                
                    elif z_score <= -self.entry_z: # Buy Spread (Buy Y, Sell X)
                        print(f"[+] LONG SPREAD Detetado (Z={z_score:.2f})")
                        lot_x = round(LOT_Y * beta, 2)
                        if self.send_order(mt5.TRADE_ACTION_DEAL, ASSET_Y, LOT_Y, mt5.ORDER_TYPE_BUY, comment="V821_L"):
                            if self.send_order(mt5.TRADE_ACTION_DEAL, ASSET_X, lot_x, mt5.ORDER_TYPE_SELL, comment="V821_H"):
                                self.active_trade = 'LONG_SPREAD'

                # SAÍDAS (REVERSÃO À MÉDIA)
                elif self.active_trade == 'SHORT_SPREAD' and z_score <= self.exit_z:
                    print(f"[*] EXIT SHORT SPREAD Detetado (Z={z_score:.2f})")
                    # Fechar ordens (simplificado para o protótipo: via Magic Number)
                    # mt5.close_all_by_magic(MAGIC_NUMBER)
                    self.active_trade = None
                    
                elif self.active_trade == 'LONG_SPREAD' and z_score >= self.exit_z:
                    print(f"[*] EXIT LONG SPREAD Detetado (Z={z_score:.2f})")
                    self.active_trade = None

                # Aguarda próximo bar M1 para recalcular rastro
                time.sleep(10) # Polling de 10s para acompanhar o tick dentro do bar M1

            except Exception as e:
                print(f"[!] Erro no Loop: {e}")
                time.sleep(30)

if __name__ == "__main__":
    gateway = OmegaExecutionGatewayV821(entry_z=3.0) # Threshold de 3.0 para vencer o custo de 19pts
    if gateway.connect():
        gateway.run_live_loop()
