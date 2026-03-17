import pandas as pd
import numpy as np
import sys
sys.path.append(r"C:\OMEGA_PROJETO\PROJETO OMEGA QUANTITATIVE FUND")
from omega_parr_f_engine import OmegaParrFEngine

def debug_scores():
    m1_path = r"C:\OMEGA_PROJETO\OHLCV_DATA\XAUUSD_M1.csv"
    df = pd.read_csv(m1_path)
    df['time'] = pd.to_datetime(df['time'])
    
    mask = (df['time'] >= '2026-03-09') & (df['time'] <= '2026-03-11 23:59:59')
    df_calc = df.loc[mask].copy()
    
    engine = OmegaParrFEngine()
    results = engine.run_forensic_audit(df_calc)
    res_df = pd.DataFrame(results)
    
    print("--- SCORE DISTRIBUTION M1 (09-11/03) ---")
    print(res_df['score_final'].value_counts().sort_index())
    print(f"Max Score: {res_df['score_final'].max()}")
    print(f"Avg Score: {res_df['score_final'].mean():.2f}")

if __name__ == "__main__":
    debug_scores()
