import os
import pandas as pd
import numpy as np

MY_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(MY_DIR, "02_logs_execucao", "STRESS_V10_5_SWING_TRADE.csv")

def run_qa():
    print(f"Lendo base custodiada: {CSV_FILE}")
    df = pd.read_csv(CSV_FILE)
    
    total_bars = len(df)
    total_signals = df['signal_fired'].sum()
    
    # Z-Score absolute percentiles
    z_abs = np.abs(df['z_score'].dropna())
    p50 = np.percentile(z_abs, 50)
    p95 = np.percentile(z_abs, 95)
    p99 = np.percentile(z_abs, 99)
    
    print("-" * 50)
    print("MÉTRICAS QA INDEPENDENTE - V10.5")
    print("-" * 50)
    print(f"Total de Linhas (Barras): {total_bars}")
    print(f"Sinais Válidos ('True'):  {total_signals}")
    print("\n[Percentis Absolutos do Z-Score]")
    print(f"P50 (Mediana):  {p50:.4f}")
    print(f"P95 (Distorção): {p95:.4f}")
    print(f"P99 (Extremos):  {p99:.4f}")
    print("-" * 50)
    
    assert total_bars == 100000, "Falha de QA: Faltam barras no CSV de stress."
    print("Status Analítico Independente: APROVADO.")

if __name__ == "__main__":
    run_qa()
