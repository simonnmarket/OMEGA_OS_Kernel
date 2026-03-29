"""
OMEGA V10.1 INTEGRATED GATEWAY - PSA DEPLOY
===========================================
Engenharia: MACE-MAX (ANTIGRAVITY) | Auditoria Tier-0
Data: 29 de Março de 2026
Status: ✅ INTEGRAÇÃO COM NÚCLEO V1.1 CONCLUÍDA
        ✅ MOTOR RLS/EWMA CAUSAL OFICIAL

Este gateway utiliza o código auditado do 'Núcleo de Validação OMEGA' 
como fonte única de verdade para o sinal de Z-Score.
"""

import MetaTrader5 as mt5
import numpy as np
import time
import os
import sys
import psutil
from datetime import datetime

# 1. SETUP DE PATHS (Vincular ao Núcleo de Validação)
BASE_DIR = r"C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F"
CORE_PATH = os.path.join(BASE_DIR, "Núcleo de Validação OMEGA")
if CORE_PATH not in sys.path:
    sys.path.insert(0, CORE_PATH)

try:
    from online_rls_ewma import OnlineRLSEWMACausalZ
except ImportError:
    print(f"[ERRO] Falha ao importar Núcleo de Validação de: {CORE_PATH}")
    sys.exit(1)

# CONFIGURAÇÕES OPERACIONAIS
ASSET_Y, ASSET_X = "XAUUSD", "XAGUSD"
MAGIC_NUMBER = 100100
MIN_Z_ENTRY = 3.75
INTEGRATION_LOG = os.path.join(BASE_DIR, "logs", "integration_smoke_test.csv")

class OmegaV101Integrated:
    def __init__(self):
        # Instanciar o Motor do Padrão Ouro
        self.motor = OnlineRLSEWMACausalZ(forgetting=0.98, ewma_span=100)
        self.last_bar_t = 0
        self.process = psutil.Process(os.getpid())
        
        if not os.path.exists(os.path.dirname(INTEGRATION_LOG)):
            os.makedirs(os.path.dirname(INTEGRATION_LOG))

    def connect(self):
        if not mt5.initialize():
            print("Falha ao iniciar MT5")
            return False
        print(f"[*] OMEGA V10.1 INICIADO. MOTOR: OnlineRLSEWMACausalZ")
        return True

    def run_reactive(self):
        while True:
            # Sincronização por Barra M1 (Reactive)
            rates = mt5.copy_rates_from_pos(ASSET_Y, mt5.TIMEFRAME_M1, 0, 1)
            if rates and rates[0][0] != self.last_bar_t:
                # Ingestão do par
                ry = mt5.copy_rates_from_pos(ASSET_Y, mt5.TIMEFRAME_M1, 0, 1)
                rx = mt5.copy_rates_from_pos(ASSET_X, mt5.TIMEFRAME_M1, 0, 1)
                
                if ry and rx:
                    y_val, x_val = ry[0][4], rx[0][4]
                    
                    # PROCESSAMENTO VIA NÚCLEO V1.1
                    # s: spread, z: z_score, y_hat: predição
                    s, z, y_hat = self.motor.step(y_val, x_val)
                    
                    # Telemetria & Log
                    ts = datetime.now().isoformat()
                    ram = self.process.memory_info().rss / 1024 / 1024
                    
                    print(f"\r[V10.1] TS: {ts} | Z: {z:.4f} | RLS_Beta: {self.motor.rls.theta[1]:.4f} | RAM: {ram:.1f}MB", end="")
                    
                    with open(INTEGRATION_LOG, "a") as f:
                        if os.path.getsize(INTEGRATION_LOG) == 0:
                            f.write("ts,y,x,spread,z,beta,ram\n")
                        f.write(f"{ts},{y_val},{x_val},{s},{z},{self.motor.rls.theta[1]},{ram}\n")

                    # Lógica de Execução (Placeholder Simples p/ Teste de Fumo)
                    if abs(z) >= MIN_Z_ENTRY:
                        print(f"\n[SINAL] Z={z:.2f} atingiu threshold. Próximo passo: Validação de Regime.")

                self.last_bar_t = rates[0][0]
            
            time.sleep(0.1)

if __name__ == "__main__":
    eng = OmegaV101Integrated()
    if eng.connect():
        eng.run_reactive()
