import os
import sys
import pandas as pd
import numpy as np
import time

MY_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_VAL_DIR = os.path.join(MY_DIR, "..", "..", "omega_core_validation")
sys.path.insert(0, os.path.abspath(CORE_VAL_DIR))
from online_rls_ewma import OnlineRLSEWMACausalZ

BASE_DIR = MY_DIR
RAW_Y = os.path.join(BASE_DIR, "01_raw_mt5", "XAUUSD_M1_RAW.csv")
RAW_X = os.path.join(BASE_DIR, "01_raw_mt5", "XAGUSD_M1_RAW.csv")
OUT_DIR = os.path.join(BASE_DIR, "02_logs_execucao")

def main():
    print("Iniciando Pipeline de Stress Histórico Completo v10.5")
    df_y = pd.read_csv(RAW_Y)
    df_x = pd.read_csv(RAW_X)
    df = pd.merge(df_y, df_x, on='time', suffixes=('_y', '_x')).sort_values('time')
    
    # Política de Truncagem: Nenhuma. 100% da base RAW.
    y_prices = df['close_y'].values
    x_prices = df['close_x'].values
    times = df['time'].values

    # Parâmetros Oficiais V10.5 SWING TRADE
    lam = 0.9998
    span = 500
    z_threshold = 2.0
    
    motor = OnlineRLSEWMACausalZ(forgetting=lam, ewma_span=span)
    
    # Arrays de métricas
    out_z = np.zeros(len(y_prices))
    out_s = np.zeros(len(y_prices))
    out_yh = np.zeros(len(y_prices))
    out_signal = np.zeros(len(y_prices), dtype=bool)
    
    # Execução
    in_position = False
    
    for i in range(len(y_prices)):
        s, z, y_h = motor.step(y_prices[i], x_prices[i])
        out_z[i] = z
        out_s[i] = s
        out_yh[i] = y_h
        
        # Detector de Crosses (Sinal Explícito C3)
        if not in_position and abs(z) >= z_threshold:
            out_signal[i] = True
            in_position = True
        elif in_position and abs(z) < z_threshold * 0.5: # Simple exit logic cool-down
            in_position = False
            
    df['z_score'] = out_z
    df['spread'] = out_s
    df['y_hat'] = out_yh
    df['signal_fired'] = out_signal
    
    print(f"Total de Sinais Disparados (|Z| > {z_threshold}): {np.sum(out_signal)}")
    
    out_file = os.path.join(OUT_DIR, "STRESS_V10_5_SWING_TRADE.csv")
    df.to_csv(out_file, index=False)
    print(f"Execução terminada. Salvo em {out_file}.")

if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"Tempo total: {time.time() - t0:.2f}s")
