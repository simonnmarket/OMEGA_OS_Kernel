
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Adiciona o kernel ao path
sys.path.append(str(Path.cwd()))
from modules.omega_parr_f_engine import OmegaParrFEngine

def run_multi_cycle_test():
    # Carrega dados
    h1_path = 'C:/OMEGA_PROJETO/OHLCV_DATA/XAUUSD_H1.csv'
    m15_path = 'C:/OMEGA_PROJETO/OHLCV_DATA/XAUUSD_M15.csv'
    
    df_h1 = pd.read_csv(h1_path)
    df_m15 = pd.read_csv(m15_path)
    
    df_h1['time'] = pd.to_datetime(df_h1['time'])
    df_m15['time'] = pd.to_datetime(df_m15['time'])
    
    # Filtra Março/2026
    df_h1 = df_h1[df_h1['time'] >= '2026-03-09'].copy()
    df_m15 = df_m15[df_m15['time'] >= '2026-03-09'].copy()
    
    engine = OmegaParrFEngine()
    
    events = []
    
    # Passo a passo no M15
    for i in range(20, len(df_m15)):
        m15_row = df_m15.iloc[i]
        ts = m15_row['time']
        
        # Busca contexto H1 (confluência)
        h1_context = df_h1[df_h1['time'] <= ts].tail(1)
        if h1_context.empty: continue
        
        # Análise M15 (Gatilho)
        data_m15 = df_m15.iloc[i-15:i][['open','high','low','close','tick_volume']].values
        res = engine.execute_audit(data_m15)
        
        if res['launch']:
            events.append({
                'TS': ts,
                'PRICE': m15_row['close'],
                'SCORE': res['score'],
                'STORM': res.get('storm', False)
            })
            
    return pd.DataFrame(events)

if __name__ == "__main__":
    results = run_multi_cycle_test()
    print("--- SNIPER CONFLUENCE TEST (MAR-2026) ---")
    if not results.empty:
        print(f"Total Gatilhos Capturados: {len(results)}")
        print(f"Exemplos de Captura (Início da Onda de 50k):")
        print(results.head(10).to_string())
    else:
        print("Nenhum gatilho detectado com a calibração atual.")
