import pandas as pd
import numpy as np

def calculate_sei():
    csv_path = r"C:\OMEGA_PROJETO\PROJETO OMEGA QUANTITATIVE FUND\AUDIT_EVIDÊNCIA_CIENTÍFICA\FORENSIC_50K_SIM_V5.4.1_ATOMIC.csv"
    df = pd.read_csv(csv_path)
    
    # Amplitude do Evento
    p_max = df['PRICE'].max()
    p_min = df['PRICE'].min()
    amplitude = p_max - p_min
    
    # Pontos Capturados (Simplificado: Mudança de preço em barras com LAUNCH=1)
    df['price_diff'] = df['PRICE'].diff().abs()
    captured = df[df['LAUNCH'] == 1]['price_diff'].sum()
    
    sei = (captured / amplitude) * 100 if amplitude > 0 else 0
    
    print(f"📊 RELATÓRIO DE EFICIÊNCIA DE RESSONÂNCIA (SEI V5.4.2):")
    print(f"   - Amplitude do Movimento: {amplitude:.2f} pts")
    print(f"   - Pontos Capturados (Ignition Active): {captured:.2f} pts")
    print(f"   - SEI (Success Efficiency Index): {sei:.2f}%")
    print(f"   - Status: {'✅ EXCELENTE (>15%)' if sei > 15 else '⚠️ MELHORAR'}")

if __name__ == "__main__":
    calculate_sei()
