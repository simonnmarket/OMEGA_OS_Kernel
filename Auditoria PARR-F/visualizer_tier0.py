import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# PATHS
BASE_DIR = r"C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F"
LOGS_DIR = os.path.join(BASE_DIR, "logs")
ASSETS_DIR = os.path.join(BASE_DIR, "Declaracoes", "Assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

def analyze_profile(name):
    print(f"[*] Analisando Perfil: {name}...")
    file_path = os.path.join(LOGS_DIR, f"STRESS_2Y_{name}.csv")
    df = pd.read_csv(file_path)
    
    # 1. Cálculo de PnL Simulado (Spread Arbitrage)
    # y = long, x = short (ou vice-versa). 
    # Para simplificar: PnL em pontos do Spread.
    df['diff_spread'] = df['spread'].diff()
    df['equity_pts'] = 0.0
    
    # Simulação Simplificada de Equity (Points)
    # Se order_filled e signal_fired: entramos.
    # Se order_filled muda de True para False: saímos.
    equity = 0.0
    pos = 0 # 0=flat, 1=long_spread, -1=short_spread
    entry_s = 0.0
    
    equities = []
    
    # Logic: 
    # Long Spread (Z < -3.75): Compra Y, Vende X. Ganha se Spread (Y-betaX) SOBE.
    # Short Spread (Z > 3.75): Vende Y, Compra X. Ganha se Spread (Y-betaX) CAI.
    
    for i, row in df.iterrows():
        fired = row['signal_fired']
        filled = row['order_filled']
        z = row['z']
        s = row['spread']
        
        if pos == 0:
            if filled:
                if z <= -3.75: pos = 1; entry_s = s
                elif z >= 3.75: pos = -1; entry_s = s
        else:
            # Saída na reversão (Z=0)
            if (pos == 1 and z >= 0) or (pos == -1 and z <= 0):
                pnl = (s - entry_s) if pos == 1 else (entry_s - s)
                equity += pnl
                pos = 0
        
        equities.append(equity)
    
    df['equity_curve'] = equities
    
    # 2. Plotagem - Equity Curve
    plt.figure(figsize=(12, 6))
    plt.plot(df['equity_curve'], label=f'Equity {name}', color='cyan' if name=="SCALPING" else 'gold')
    plt.title(f"OMEGA V10.4 OMNIPRESENT - EQUITY CURVE: {name}")
    plt.xlabel("Barras (M1)")
    plt.ylabel("Acumulado (Pontos)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.savefig(os.path.join(ASSETS_DIR, f"EQUITY_{name}.png"))
    plt.close()
    
    # 3. Métricas Tier-0
    total_pnl = df['equity_curve'].iloc[-1]
    max_dd = (df['equity_curve'].cummax() - df['equity_curve']).max()
    
    return {
        'Profile': name,
        'Final_PnL_Pts': f"{total_pnl:.2f}",
        'Max_Drawdown_Pts': f"{max_dd:.2f}",
        'Bars_Processed': len(df)
    }

if __name__ == "__main__":
    results = []
    for p in ["SCALPING", "DAY_TRADE", "SWING_TRADE"]:
        results.append(analyze_profile(p))
    
    # Gerar Resumo
    res_df = pd.DataFrame(results)
    res_df.to_markdown(os.path.join(BASE_DIR, "Declaracoes", "STRESS_TEST_METRICS.md"), index=False)
    print("\n[OK] MÉTRICAS E GRÁFICOS GERADOS EM Declaracoes/Assets/")
