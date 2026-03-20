import pandas as pd
import numpy as np

def summary():
    path = r"C:\OMEGA_PROJETO\PROJETO OMEGA QUANTITATIVE FUND\AUDIT_EVIDÊNCIA_CIENTÍFICA\FULL_HISTORICAL_AUDIT_V543_PSA.csv"
    df = pd.read_csv(path)
    
    print(f"--- PSA COMPLIANCE REPORT (V5.4.3) ---")
    print(f"Columns Found: {len(df.columns)}")
    print(f"Total Bars: {len(df)}")
    
    final_balance = df['BALANCE'].iloc[-1]
    net_return = ((final_balance/10000)-1)*100
    max_dd = df['DRAWDOWN'].max() * 100
    
    # Calculate Sharpe from Balance diffs
    b_diff = df['BALANCE'].diff().dropna()
    b_diff = b_diff[b_diff != 0] # only trade bars
    if len(b_diff) > 1:
        sharpe = (b_diff.mean() / b_diff.std()) * np.sqrt(252) # simplistic
    else:
        sharpe = 0
        
    print(f"Net Return: {net_return:.2f}%")
    print(f"Max Drawdown: {max_dd:.2f}%")
    print(f"Sharpe Ratio (Sim): {sharpe:.2f}")
    
    # Success Efficiency Index (SEI)
    p_max, p_min = df['PRICE'].max(), df['PRICE'].min()
    amplitude = p_max - p_min
    captured = df[df['LAUNCH'] == 1]['PRICE'].diff().abs().sum()
    sei = (captured / amplitude) * 100
    print(f"Global SEI: {sei:.2f}%")
    
    # Win Rate
    # In my sim, trades were stored in the sim object, but I can infer from BALANCE changes
    trades = b_diff.values
    wins = len(trades[trades > 0])
    total = len(trades)
    win_rate = (wins/total)*100 if total > 0 else 0
    print(f"Win Rate: {win_rate:.2f}%")
    
    print(f"---------------------------------------")

if __name__ == "__main__":
    summary()
