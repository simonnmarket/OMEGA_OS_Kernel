
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# =============================================================================
# OMEGA ECM — MARKET CARDIOGRAM (FORENSIC RHYTHM VISION)
# =============================================================================

def generate_market_cardiogram():
    path = 'C:/OMEGA_PROJETO/OHLCV_DATA/XAUUSD_M15.csv'
    df = pd.read_csv(path)
    df['time'] = pd.to_datetime(df['time'])
    
    # Foco no período crítico de Março/2026
    df = df[df['time'] >= '2026-03-09'].copy()
    
    # --- METRICAS CARDIACAS ---
    # Velocity (BPM) - Mudança de preço por barra
    df['bpm'] = df['close'].diff().abs()
    
    # Acceleration (Pulse Strength) - Mudança na velocidade
    df['pulse'] = df['bpm'].diff()
    
    # Rhythm (Arrhythmia) - Desvio padrão da velocidade (Estabilidade vs Caos)
    df['rhythm'] = df['bpm'].rolling(window=10).std()
    
    # Flow (Blood Pressure) - Volume relativo
    df['pressure'] = (df['tick_volume'] - df['tick_volume'].rolling(50).mean()) / df['tick_volume'].rolling(50).std()

    print(f"🩺 SCANNER OMEGA ECM — RELATÓRIO DE RITMO (MARÇO/2026)")
    print("="*100)
    print(f"{'TIME':<20} | {'PRICE':<8} | {'BPM (Batimento)':<15} | {'PULSE (Aceleração)':<18} | {'STATE (Diagnóstico Médico)'}")
    print("-"*100)

    for i in range(50, 80): # Amostra do dia 09/03
        row = df.iloc[i]
        
        # Diagnóstico de Estado
        state = "ESTÁVEL (Normal)"
        if row['bpm'] > 5000: # Se mover mais de 5k pontos em 15min
            state = "🚀 TAQUICARDIA (EXPLOSÃO)"
        elif row['rhythm'] > 3000:
            state = "⚠️ ARRITMIA (VOLATILIDADE)"
        elif row['bpm'] < 500:
            state = "💤 BRADICARDIA (SEM FLUXO)"
            
        print(f"{str(row['time']):<20} | {row['close']:<8.2f} | {row['bpm']:<15.2f} | {row['pulse']:<18.2f} | {state}")

if __name__ == "__main__":
    generate_market_cardiogram()
