import pandas as pd
import numpy as np
import os
from modules.omega_parr_f_engine import OmegaParrFEngine

# =============================================================================
# OMEGA FORENSIC SIMULATOR V5.4.1 ATÔMICO — CQO AUDIT EDITION
# =============================================================================

def run_forensic_simulation():
    data_path = r"C:\OMEGA_PROJETO\OHLCV_DATA\XAUUSD_H4.csv"
    if not os.path.exists(data_path):
        print(f"Erro: Arquivo não encontrado em {data_path}")
        return

    df = pd.read_csv(data_path)
    df['time'] = pd.to_datetime(df['time'])
    
    # Filtro Evento 50k (09-13/03/2026)
    mask = (df['time'] >= '2026-03-09 00:00:00') & (df['time'] <= '2026-03-14 23:59:00')
    event_df = df[mask].copy()
    
    if len(event_df) == 0:
        print("Erro: Dados do evento não encontrados no CSV.")
        return

    print(f"[*] Iniciando Auditoria Atômica V5.4.1 (CQO Edition): {len(event_df)} barras H4.")
    
    engine = OmegaParrFEngine()
    results = []
    
    # Colunas: open, high, low, close, volume (tick_volume)
    full_ohlcv = df[['open', 'high', 'low', 'close', 'tick_volume']].values
    event_indices = event_df.index
    
    for idx in event_indices:
        if idx < 150: continue 
        
        window = full_ohlcv[idx-150:idx+1]
        
        # Orquestração V5.4.1
        res = engine.execute_full_audit(window)
        
        layers = res['layers']
        
        results.append({
            'TS': df.iloc[idx]['time'],
            'PRICE': window[-1, 3],
            'ATR': res['atr'],
            'L0_HFD': layers['L0']['hfd'],
            'L0_R2': layers['L0']['r2'],
            'L0_STABILITY': layers['L0']['stability'],
            'L1_POC_LAG': layers['L1']['lag'],
            'L1_DENSITY': layers['L1']['density'],
            'L2_ZVOL_LOG': layers['L2']['z_vol_log'],
            'L2_WICK_NORM': layers['L2']['wick_norm'],
            'L3_HA_STRENGTH': layers['L3']['strength'],
            'L3_OK': int(layers['L3']['ok']),
            'SCORE': res['score'],
            'REGIME': res['regime'],
            'LAUNCH': int(res['launch']),
            'FLAGS': "|".join(res['flags'])
        })
        
    res_df = pd.DataFrame(results)
    output_dir = r"C:\OMEGA_PROJETO\PROJETO OMEGA QUANTITATIVE FUND\AUDIT_EVIDÊNCIA_CIENTÍFICA"
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    
    output_path = os.path.join(output_dir, "FORENSIC_50K_SIM_V5.4.1_ATOMIC.csv")
    res_df.to_csv(output_path, index=False)
    
    print(f"✅ AUDITORIA CONCLUÍDA. Arquivo: {output_path}")
    
    avg_score = res_df['SCORE'].mean()
    launches = res_df['LAUNCH'].sum()
    
    print(f"📊 MÉTRICAS CONSOLIDADAS:")
    print(f"   - Score Médio: {avg_score:.2f}")
    print(f"   - Total Launches: {launches}")
    print(f"   - Regime Dominante: {res_df['REGIME'].mode()[0]}")
    
    if launches > 0:
        print("\n🚀 PRIMEIRO TRIGGER DETECTADO (RESPOSTA AO ABISMO):")
        print(res_df[res_df['LAUNCH'] == 1].iloc[0])
    else:
        print("\n⚠️ AVISO: Sistema ainda em modo defensivo (SEI inferior). Review thresholds L0/L3.")

if __name__ == "__main__":
    run_forensic_simulation()
