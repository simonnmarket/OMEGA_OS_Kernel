import pandas as pd
import matplotlib.pyplot as plt
import os

def generate_plots(csv_path, output_title):
    df = pd.read_csv(csv_path)
    if len(df) == 0:
        print(f"Skipping empty file: {csv_path}")
        return
    
    # Simular Curva de Capital
    equity = 10000 + df['pnl_net'].cumsum()
    peak = equity.cummax()
    dd_pct = (peak - equity) / peak * 100
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    
    ax1.plot(equity, color='blue', label='Equity')
    ax1.set_title(f'Equity Curve: {output_title}')
    ax1.set_ylabel('Balance (USD)')
    ax1.grid(True)
    ax1.legend()
    
    ax2.fill_between(range(len(dd_pct)), dd_pct, color='red', alpha=0.3, label='Drawdown %')
    ax2.set_title(f'Drawdown %')
    ax2.set_ylabel('Drawdown %')
    ax2.set_xlabel('Trade Number')
    ax2.grid(True)
    ax2.legend()
    
    plt.tight_layout()
    plot_name = csv_path.replace('.csv', '_plot.png')
    plt.savefig(plot_name)
    print(f"✅ Gráfico gerado: {plot_name}")
    plt.close()

if __name__ == "__main__":
    generate_plots("./RIGOROUS_AUDIT_V550_BOSS_FINAL/REPLAY_STRUCTURAL_V550_RIGOROUS_augmented.csv", "STRUCTURAL (2019-2026)")
    generate_plots("./RIGOROUS_AUDIT_V550_BOSS_FINAL/REPLAY_FOCAL_V550_RIGOROUS_augmented.csv", "FOCAL (MARCH 2026)")
