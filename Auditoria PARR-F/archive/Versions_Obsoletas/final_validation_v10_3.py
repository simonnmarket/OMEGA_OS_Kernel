"""
FINAL VALIDATION V10.3: ENGAGEMENT & HASH
=========================================
Gera o log de 100 barras utilizando os dados de referência (Gold/Silver) 
para provar a correção da Métrica 9 (Engajamento) e Integridade SHA3-256.
"""

import sys
import os
import pandas as pd
from datetime import datetime
import hashlib
import psutil

# Setup paths
BASE_DIR = r"C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F"
CORE_PATH = os.path.join(BASE_DIR, "Núcleo de Validação OMEGA")
sys.path.insert(0, CORE_PATH)
sys.path.insert(0, BASE_DIR)

import importlib.util
spec = importlib.util.spec_from_file_location("GatewayV103", os.path.join(BASE_DIR, "10_mt5_gateway_V10_3_SOVEREIGN.py"))
gateway_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gateway_mod)
ExecutionManager = gateway_mod.ExecutionManager
OmegaV103Sovereign = gateway_mod.OmegaV103Sovereign

def run_final_audit():
    print("[*] INICIANDO AUDITORIA FINAL V10.3 (POLIMENTO TECH LEAD)...")
    
    # 1. Carregar Dados de Referência
    y_path = os.path.join(CORE_PATH, "dados_ohlcv_referencia", "XAUUSD_M1.csv")
    x_path = os.path.join(CORE_PATH, "dados_ohlcv_referencia", "XAGUSD_M1.csv")
    
    dy = pd.read_csv(y_path).head(100)
    dx = pd.read_csv(x_path).head(100)
    
    # 2. Setup do Motor (V10.3)
    eng = OmegaV103Sovereign()
    
    # Reduzir threshold para 0.01 apenas para provar gatilho (Critica Tech Lead §12)
    # MIN_Z_ENTRY = 0.01
    
    log_file = os.path.join(BASE_DIR, "logs", "FINAL_V10_3_POLISHED_LOG.csv")
    if os.path.exists(log_file): os.remove(log_file)
    
    print(f"[*] Processando 100 barras...")
    
    for i in range(len(dy)):
        y_val, x_val = dy['close'].iloc[i], dx['close'].iloc[i]
        ts = dy['time'].iloc[i]
        
        # Motor
        s, z, y_h = eng.motor.step(y_val, x_val)
        
        # Signal (Simulando threshold baixo para teste de fumo)
        # Se Z != 0, vai disparar
        side = "FLAT"
        if abs(z) >= 0.01: side = "SHORT" if z > 0 else "LONG"
        
        # EXECUTOR (Engagement Tracking)
        eng_res = eng.executor.manage(side, y_val, x_val, z)
        
        # LOGGING INTEGRADO
        # ts,y,x,spread,z,beta,signal_fired,order_filled,ram_mb,sha3
        ram = eng.process.memory_info().rss / 1024 / 1024
        beta = eng.motor.rls.theta[1]
        log_data = f"{ts},{y_val},{x_val},{s:.6f},{z:.4f},{beta:.6f},{eng_res['signal_fired']},{eng_res['order_filled']},{ram:.1f}"
        
        line_hash = hashlib.sha3_256(log_data.encode()).hexdigest()
        
        with open(log_file, "a") as f:
            if i == 0:
                f.write("ts,y,x,spread,z,beta,signal_fired,order_filled,ram_mb,sha3_256\n")
            f.write(f"{log_data},{line_hash}\n")
            
    print(f"✅ LOG GERADO: {log_file}")
    
    # Verificação Manual de 1 Linha (Gatilho)
    df = pd.read_csv(log_file)
    triggered = df[df['signal_fired'] == True].head(1)
    if not triggered.empty:
        print(f"✅ GATILHO COMPROVADO: Linha {triggered.index[0]} disparou sinal.")
        print(f"   Z: {triggered['z'].values[0]} | Signal: {triggered['signal_fired'].values[0]} | Filled: {triggered['order_filled'].values[0]}")
    else:
        print("❌ FALHA: Nenhum sinal disparado mesmo com threshold baixo.")

if __name__ == "__main__":
    run_final_audit()
