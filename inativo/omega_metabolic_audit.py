
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Adiciona o kernel ao path
sys.path.append(str(Path.cwd()))
from modules.omega_parr_f_engine import OmegaParrFEngine

def run_metabolic_history_audit():
    # PATHS
    m15_path = 'C:/OMEGA_PROJETO/OHLCV_DATA/XAUUSD_M15.csv'
    
    # LOAD
    df = pd.read_csv(m15_path)
    df['time'] = pd.to_datetime(df['time'])
    df.sort_values('time', inplace=True)
    
    engine = OmegaParrFEngine()
    
    # --- METRICAS DE AUDITORIA METABÓLICA ---
    states_count = {"REPOUSO": 0, "CAMINHADA": 0, "CORRIDA": 0, "ADRENALINA": 0}
    launches_per_state = {"REPOUSO": 0, "CAMINHADA": 0, "CORRIDA": 0, "ADRENALINA": 0}
    captured_points = 0.0
    
    # Configuração de Execução (Simples para verificação rítmica)
    ohlcv = df[['open','high','low','close','tick_volume']].values
    
    print(f"🩺 INICIANDO MAPEAMENTO METABÓLICO DE 2 ANOS (OECG)...")
    
    current_trade_points = 0.0
    in_position = False
    
    for i in range(20, len(ohlcv)):
        slice_data = ohlcv[i-19:i+1]
        res = engine.execute_audit(slice_data)
        
        state = res['state']
        states_count[state] += 1
        
        if res['launch']:
            launches_per_state[state] += 1
            if not in_position:
                in_position = True
                entry_price = ohlcv[i, 3]
                bias = res['bias']
            
        if in_position:
            # Pnl da vela atual
            price = ohlcv[i, 3]
            pnl = (price - ohlcv[i-1, 3]) * bias
            captured_points += pnl
            
            # Saída simplificada por exaustão de ritmo (volta ao Repouso)
            if state == "REPOUSO":
                in_position = False

    print("\n" + "🩺" * 25)
    print(f"📊 RELATÓRIO DE FISIOLOGIA DO MERCADO (2 ANOS)")
    print("🩺" * 25)
    print(f"📅 Período: {df.time.min()} ate {df.time.max()}")
    print(f"📏 Total de Pontos Capturados: {captured_points:,.2f}")
    print("\n--- DISTRIBUIÇÃO DE ESTADOS (Batimentos) ---")
    for s, c in states_count.items():
        pct = (c / len(ohlcv)) * 100
        print(f"[{s:<10}]: {c:>6} barras ({pct:>5.2f}%) | Gatilhos: {launches_per_state[s]}")
    
    print("\n" + "🏁" * 25)

if __name__ == "__main__":
    run_metabolic_history_audit()
