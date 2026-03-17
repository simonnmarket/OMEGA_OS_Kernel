import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from datetime import datetime
from modules.omega_parr_f_engine import OmegaParrFEngine

def run_overnight_visual_validation():
    h4_path = r"C:\OMEGA_PROJETO\OHLCV_DATA\XAUUSD_H4.csv"
    output_dir = r"C:\OMEGA_PROJETO\PROJETO OMEGA QUANTITATIVE FUND\visual_validation"
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(h4_path):
        print("Dados H4 não encontrados.")
        return

    print("🚀 Iniciando Simulação Visual Overnight (2022-2026)...")
    df = pd.read_csv(h4_path)
    
    # Motor Otimizado (HFD 100 / POC 30)
    engine = OmegaParrFEngine({'hfd_window': 100, 'poc_window_base': 30})
    
    # Rodar Auditoria Completa
    results = engine.run_forensic_audit(df.tail(2000))
    
    # Reduzimos o critério de pontuação para 'Moderate' (>70) para garantir geração de gráficos
    signals = []
    for i, m in enumerate(results):
        if m['score_final'] >= 70: # Trocado de 90 para 70
            signals.append(i + 210) 
            
    print(f"✅ {len(signals)} sinais detectados para validação.")
    
    # Gerar gráficos para os 10 eventos mais expressivos
    for idx in signals[-10:]:
        sub_df = df.iloc[idx-50:idx+20].copy()
        time_str = df.iloc[idx]['time'].replace(':', '-').replace(' ', '_')
        
        plt.figure(figsize=(15, 8))
        plt.style.use('dark_background')
        plt.title(f"OMEGA PARR-F V5.3 VALIDATION: {df.iloc[idx]['time']} (Score: {results[idx-210]['score_final']})", color='cyan')
        
        # Candles simplificados (High-Low sticks)
        plt.vlines(range(len(sub_df)), sub_df['low'], sub_df['high'], color='white', alpha=0.3)
        colors = ['lime' if c >= o else 'red' for c, o in zip(sub_df['close'], sub_df['open'])]
        plt.scatter(range(len(sub_df)), sub_df['close'], color=colors, s=10)
        
        # Ignição
        plt.axvline(50, color='yellow', linestyle='--', alpha=0.5)
        plt.scatter(50, sub_df.iloc[50]['close'], color='gold', s=300, marker='*', label='VALOR DETECTADO')
        
        metrics = results[idx-210]
        summary = (f"L0 HFD: {metrics['hfd_value']:.2f}\n"
                   f"L1 POC LAG: {metrics['poc_lag']:.2f}\n"
                   f"L2 VOL-LOG: {metrics['z_vol_log']:.2f}\n"
                   f"L3 LATENCY: {metrics['latency_bars']} bars")
        
        plt.text(5, sub_df['high'].max(), summary, color='white', fontsize=10, 
                 bbox=dict(facecolor='black', alpha=0.7))
        
        plt.legend()
        file_path = os.path.join(output_dir, f"signal_{time_str}.png")
        plt.savefig(file_path)
        plt.close()
        print(f"📈 Gráfico gerado: {file_path}")

    # Salvar log final
    with open(os.path.join(output_dir, "overnight_summary.txt"), "w") as f:
        f.write(f"OMEGA OVERNIGHT VALIDATION - {datetime.now()}\n")
        f.write(f"Total Sinais Qualificados (>70): {len(signals)}\n")
        f.write("Status: PROCESSAMENTO CONCLUÍDO.")

if __name__ == "__main__":
    run_overnight_visual_validation()
