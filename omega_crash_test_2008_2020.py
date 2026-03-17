import os
import sys
import numpy as np
import pandas as pd
from run_aic_v5_master import OmegaAICControllerV5

# =============================================================================
# OMEGA CRASH-TEST (2008 & 2020) - RAW DATA DUMP
# =============================================================================

def run_historical_crash_test():
    h4_path = r"C:\OMEGA_PROJETO\OHLCV_DATA\XAUUSD_H4.csv"
    output_csv = r"C:\OMEGA_PROJETO\PROJETO OMEGA QUANTITATIVE FUND\AUDIT_EVIDÊNCIA_CIENTÍFICA\RAW_BACKTEST_2008_2020.csv"
    
    if not os.path.exists(h4_path):
        print("Dataset H4 não encontrado.")
        return

    df = pd.read_csv(h4_path)
    # Filtro para os períodos de stress extremo
    # Crise 2008 (Jan 2008 - Dez 2009) e Covid 2020 (Jan 2020 - Dez 2020)
    df['time'] = pd.to_datetime(df['time'])
    stress_df = df[((df['time'].dt.year >= 2008) & (df['time'].dt.year <= 2009)) | 
                   ((df['time'].dt.year == 2020))].copy()
    
    print(f"[*] Iniciando Crash-Test em {len(stress_df)} amostras (2008 & 2020)...")
    
    controller = OmegaAICControllerV5()
    raw_logs = []
    
    # Simulação simplificada de PnL no Kernel
    balance = 10000.0
    active_pos = None
    
    ohlcv = stress_df[['open', 'high', 'low', 'close', 'tick_volume']].values
    
    for i in range(150, len(ohlcv)):
        window = ohlcv[i-150:i]
        candle = ohlcv[i]
        
        # O motor PARR-F V5.3 agora está injetado no controlador
        res = controller.get_thrust_vector(window, None, None)
        
        log_entry = {
            'time': stress_df.iloc[i]['time'],
            'price': candle[3],
            'thrust_score': res['thrust_score'],
            'direction': res['direction'],
            'launch': res['launch'],
            'hfd': res['kernel_details']['hfd'],
            'poc_lag': res['kernel_details']['poc_lag'],
            'zvol': res['kernel_details']['zvol'],
            'balance': balance
        }
        
        # Simulação de trade básica
        if res['launch'] and not active_pos:
            active_pos = {'entry': candle[3], 'dir': res['direction']}
        elif active_pos and (res['kalman_break'] or res['direction'] != active_pos['dir']):
            # Fechamento
            profit = active_pos['dir'] * (candle[3] - active_pos['entry']) * 10 # Lote 0.1 simulado
            balance += profit
            active_pos = None
            
        raw_logs.append(log_entry)

    # Dump de dados brutos para auditoria do Comandante
    pd.DataFrame(raw_logs).to_csv(output_csv, index=False)
    print(f"✅ DUMP DE DADOS BRUTOS GERADO: {output_csv}")

if __name__ == "__main__":
    run_historical_crash_test()
