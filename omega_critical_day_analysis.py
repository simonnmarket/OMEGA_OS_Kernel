
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Adiciona o kernel ao path
sys.path.append(str(Path.cwd()))
from modules.omega_parr_f_engine import OmegaParrFEngine

def run_critical_day_test():
    # Carrega M15 (mais granular)
    m15_path = 'C:/OMEGA_PROJETO/OHLCV_DATA/XAUUSD_M15.csv'
    df = pd.read_csv(m15_path)
    df['time'] = pd.to_datetime(df['time'])
    
    # Foca no dia 09/03/26
    df = df[(df['time'] >= '2026-03-09 00:00:00') & (df['time'] <= '2026-03-09 23:45:00')].copy()
    
    engine = OmegaParrFEngine()
    ohlcv = df[['open','high','low','close','tick_volume']].values
    
    results = []
    
    print(f"🚀 ANALISE CRITICA OMEGA V5.21.0 - DIA 09/03/2026")
    
    for i in range(15, len(ohlcv)):
        res = engine.execute_audit(ohlcv[i-15:i+1])
        if res['launch']:
            results.append({
                'TIME': df.iloc[i]['time'],
                'PRICE': ohlcv[i, 3],
                'BIAS': 'BUY' if res['bias'] > 0 else 'SELL',
                'Z_P': res['z_price'],
                'Z_V': res['z_vol']
            })
            
    res_df = pd.DataFrame(results)
    print("\n" + "="*80)
    if not res_df.empty:
        print(res_df.to_string())
    else:
        print("Nenhuma operacao encontrada.")
    print("="*80)

if __name__ == "__main__":
    run_critical_day_test()
