import pandas as pd
import numpy as np

def summarize_audit():
    path = r"C:\OMEGA_PROJETO\PROJETO OMEGA QUANTITATIVE FUND\AUDIT_EVIDÊNCIA_CIENTÍFICA\FULL_HISTORICAL_AUDIT_V542.csv"
    df = pd.read_csv(path)
    
    total_launches = df['LAUNCH'].sum()
    final_balance = df['BALANCE'].iloc[-1]
    regime_mode = df['REGIME'].mode()[0]
    avg_score = df['SCORE'].mean()
    
    # Simulação de SEI Global
    p_max = df['PRICE'].max()
    p_min = df['PRICE'].min()
    amplitude = p_max - p_min
    df['price_diff'] = df['PRICE'].diff().abs()
    captured = df[df['LAUNCH'] == 1]['price_diff'].sum()
    sei = (captured / amplitude) * 100
    
    # Filtros de Regimes
    regimes = df['REGIME'].value_counts(normalize=True) * 100

    print(f"--- SYNTHESIS REPORT (FULL HISTORY) ---")
    print(f"Total Bars: {len(df)}")
    print(f"Total Launches: {total_launches}")
    print(f"Final Balance: ${final_balance:,.2f} (+{((final_balance/10000)-1)*100:.2f}%)")
    print(f"Global SEI: {sei:.2f}%")
    print(f"Average Score: {avg_score:.2f}")
    print(f"Regime Distribution:")
    for regime, perc in regimes.items():
        print(f"  - {regime}: {perc:.2f}%")
    print(f"----------------------------------------")

if __name__ == "__main__":
    summarize_audit()
