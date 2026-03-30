import os
import sys
import pandas as pd
import numpy as np
import time

# Adicionar omega_core_validation ao path para importar o motor RLS
MY_DIR = os.path.dirname(os.path.abspath(__file__))
# MY_DIR = evidencia_pre_demo
# we need to reach omega_core_validation: ../../omega_core_validation
CORE_VAL_DIR = os.path.join(MY_DIR, "..", "..", "omega_core_validation")
sys.path.insert(0, os.path.abspath(CORE_VAL_DIR))

from online_rls_ewma import OnlineRLSEWMACausalZ

BASE_DIR = MY_DIR
RAW_Y = os.path.join(BASE_DIR, "01_raw_mt5", "XAUUSD_M1_RAW.csv")
RAW_X = os.path.join(BASE_DIR, "01_raw_mt5", "XAGUSD_M1_RAW.csv")

def run_grid():
    print("Carregando bases brutas de Alta Frequencia...")
    df_y = pd.read_csv(RAW_Y)
    df_x = pd.read_csv(RAW_X)
    
    # Fazendo merge rápido. Assumimoms que as colunas essenciais contêm 'time', 'close'
    df = pd.merge(df_y, df_x, on='time', suffixes=('_y', '_x')).sort_values('time')
    
    if len(df) > 100000: # Limitando em 100k para um benchmark padrao
        df = df.iloc[:100000]

    y_prices = df['close_y'].values
    x_prices = df['close_x'].values

    # Grid params
    lambdas = [0.960, 0.985, 0.995, 0.9998, 0.99995]
    spans = [100, 200, 500]
    
    results = []

    print("| Lambda | Span EWMA | N (Mem. Efetiva) | Z P95 | Trades (|Z| > 1.5) | Trades (|Z| > 2.0) | Trades (|Z| > 3.0) |")
    print("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    
    for lam in lambdas:
        for span in spans:
            motor = OnlineRLSEWMACausalZ(forgetting=lam, ewma_span=span)
            z_vals = np.zeros(len(y_prices))
            
            for i in range(len(y_prices)):
                s, z, y_h = motor.step(y_prices[i], x_prices[i])
                z_vals[i] = z
                
            eff_mem = int(1 / (1 - lam))
            p95_z = np.percentile(np.abs(z_vals), 95)
            
            # Simulated trades naive (sem cooldown, conta crossing point)
            t_15 = np.sum(np.abs(z_vals) > 1.5)
            t_20 = np.sum(np.abs(z_vals) > 2.0)
            t_30 = np.sum(np.abs(z_vals) > 3.0)
            
            # Simple crossing detection (from within bands to outside bands)
            # Find points where abs(Z) crosses threshold
            def count_crosses(z_array, thresh):
                is_out = np.abs(z_array) > thresh
                # Diff > 0 -> went from inside (False/0) to outside (True/1)
                crosses = np.diff(is_out.astype(int)) > 0
                return np.sum(crosses)
                
            c_15 = count_crosses(z_vals, 1.5)
            c_20 = count_crosses(z_vals, 2.0)
            c_30 = count_crosses(z_vals, 3.0)
            
            # Formatting line for table
            res_line = f"| `{lam:.5f}` | `{span}` | {eff_mem} brs | **{p95_z:.2f} sigma** | {c_15} | {c_20} | {c_30} |"
            print(res_line)
            results.append((lam, span, eff_mem, p95_z, c_20))
            
if __name__ == "__main__":
    start = time.time()
    run_grid()
    print(f"\nGrid Search Completo em {time.time() - start:.2f}s")
