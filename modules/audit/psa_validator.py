import pandas as pd
import numpy as np
import os
import hashlib
from datetime import datetime

# =============================================================================
# OMEGA PSA EVIDENCE & BENCHMARK VALIDATOR V5.4.4 (ASCII ONLY)
# =============================================================================

def validate_evidence():
    csv_path = r"C:\OMEGA_PROJETO\PROJETO OMEGA QUANTITATIVE FUND\AUDIT_EVIDÊNCIA_CIENTÍFICA\FULL_HISTORICAL_AUDIT_V546_FINAL.csv"
    if not os.path.exists(csv_path):
        print("Error: Evidence CSV not found.")
        return

    df = pd.read_csv(csv_path)
    
    sha256 = hashlib.sha256(open(csv_path, 'rb').read()).hexdigest()
    
    # Baseline comparison
    start_price = df['PRICE'].iloc[0]
    end_price = df['PRICE'].iloc[-1]
    bh_return = ((end_price / start_price) - 1) * 100
    omega_return = ((df['BALANCE'].iloc[-1] / 10000.0) - 1) * 100
    
    # Risk Metrics
    mdd = df['DRAWDOWN'].max()
    b_diff = df['BALANCE'].diff().dropna()
    trades = b_diff[b_diff != 0]
    
    pf = 0
    if not trades.empty:
        pos = trades[trades > 0].sum()
        neg = abs(trades[trades < 0].sum())
        pf = pos / neg if neg > 0 else float('inf')
    
    print("-" * 60)
    print("OMEGA PSA EVIDENCE VALIDATION REPORT")
    print("-" * 60)
    print(f"File: {os.path.basename(csv_path)}")
    print(f"SHA256: {sha256}")
    print("-" * 60)
    print(f"BENCHMARK COMPARISON:")
    print(f"BUY & HOLD (XAUUSD): {bh_return:+.2f}%")
    print(f"OMEGA V5.4.4 (PSA):  {omega_return:+.2f}%")
    print(f"ALPHA:               {omega_return - bh_return:+.2f}%")
    print("-" * 60)
    print(f"RISK KPIs:")
    print(f"Max Drawdown (MDD): {mdd:.2f}%")
    print(f"Profit Factor:      {pf:.2f}")
    print(f"Final Balance:      ${df['BALANCE'].iloc[-1]:,.2f}")
    print("-" * 60)
    
    # Execution Proof
    non_zero = df[df['PNL'] != 0].copy()
    if not non_zero.empty:
        print("EXECUTION PROOF (LATEST TRADES):")
        print(non_zero.tail(5)[['TS', 'PRICE', 'BALANCE', 'EQUITY', 'PNL']].to_string(index=False))
    
    # SEI Calculation
    df['event_id'] = (df['LAUNCH'] != df['LAUNCH'].shift()).cumsum()
    events = df[df['LAUNCH'] == 1].groupby('event_id')
    sei_list = []
    for _, group in events:
        if len(group) < 2: continue
        amp = group['PRICE'].max() - group['PRICE'].min()
        captured = abs(group['PRICE'].iloc[-1] - group['PRICE'].iloc[0])
        if amp > 0: sei_list.append(captured / amp)
            
    avg_sei = np.mean(sei_list) * 100 if sei_list else 0
    print("-" * 60)
    print(f"SEI EVENT ANALYSIS: {avg_sei:.2f}% (Average per Event)")
    print("-" * 60)

if __name__ == "__main__":
    validate_evidence()
