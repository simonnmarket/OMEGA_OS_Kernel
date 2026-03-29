import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
from scipy import stats
import hurst
from statsmodels.tsa.stattools import adfuller

print("[*] V8.1 AUDIT SCRIPT - COMPUTING C-LEVEL DEMANDED METRICS")

# 1. Loading renamed Parquet
os.makedirs("audit_packages", exist_ok=True)
parquet_path = "archive/failed_models/v8.1/XAUUSD_M1_Q1_2026.parquet"
df = pd.read_parquet(parquet_path)

# DADO 1: histogram_delta_time.csv
df['time'] = pd.to_datetime(df['time'])
deltas = df['time'].diff().dt.total_seconds().dropna()
hist = deltas.value_counts().reset_index()
hist.columns = ['delta_time_seconds', 'count']
hist.to_csv("audit_packages/histogram_delta_time.csv", index=False)
sys_bars = df[df['tick_volume'] <= 1].shape[0] # Usually zero or 1 vol means synthetic/gap

# Re-run the V8.1 optimized logic to get exact trades for MAE/MFE etc
opens = df['open'].values
highs = df['high'].values
lows = df['low'].values
closes = df['close'].values
vols = df['tick_volume'].values

ma20 = pd.Series(vols).rolling(20).mean().fillna(0).values

# Best vector according to Grid: theta_m=0.5, delta=0.1, lam=10.0
theta_m, delta, lam = 0.50, 0.10, 10.0

trades = []
in_pos = False
entry = 0.0
entry_idx = 0
trailing = 0.0

for i in range(20, len(closes)):
    o, h, l, c, v, m20 = opens[i], highs[i], lows[i], closes[i], vols[i], ma20[i]
    if in_pos:
        if h >= trailing:
            pnl = entry - trailing
            # MAE is min favorable (actually maximum adverse in short which is Highest High so far)
            highest_high = np.max(highs[entry_idx:i+1])
            lowest_low = np.min(lows[entry_idx:i+1])
            mae = (highest_high - entry)  # Because we are short, higher is adverse
            mfe = (entry - lowest_low)    # Because we are short, lower is favorable
            trades.append({
                'entry_idx': entry_idx, 'exit_idx': i,
                'pnl': pnl, 'mae': mae, 'mfe': mfe
            })
            in_pos = False
        else:
            nt = l + lam
            if nt < trailing:
                trailing = nt
    else:
        r = h - l
        if r <= 10.0: continue
        m = abs(c - o) / (r + 1e-5)
        if c < o and m >= (theta_m - delta) and v > m20 * 1.1:
            in_pos = True
            entry_idx = i
            entry = c
            trailing = c + lam

trades_df = pd.DataFrame(trades)
trades_df.to_csv("audit_packages/trades_full.csv", index=False)

# MAE / MFE Package
mae_p95 = np.percentile(trades_df['mae'], 95)
mfe_p95 = np.percentile(trades_df['mfe'], 95)

# PnL array
pnls = trades_df['pnl'].values
wins = pnls[pnls > 0]
losses = pnls[pnls < 0]
pf = wins.sum() / abs(losses.sum())

# Welch exact (compare against dummy array of 0s)
dummy = np.zeros(len(pnls))
t_stat, p_val = stats.ttest_ind(pnls, dummy, equal_var=False, alternative='greater')

# Check Ljung Box on PnL using statsmodels
from statsmodels.stats.diagnostic import acorr_ljungbox
ljung = acorr_ljungbox(pnls, lags=[5, 10, 20], return_df=True)
ljung.to_csv("audit_packages/ljung_box_pnl.csv")

# Random Walk tests on close prices
returns = pd.Series(closes).pct_change().dropna().values
H, c, data = hurst.compute_Hc(closes, kind='price', simplified=True)
adf = adfuller(closes)

rw_tests = {
    "hurst_exponent": {"value": H, "interpretation": "Random Walk / Anti-persistent" if H < 0.55 else "Trending"},
    "adf_test": {"statistic": adf[0], "p_value": adf[1]},
    "welch_exact": {"t_stat": t_stat, "p_value": p_val},
    "mae_p95": mae_p95,
    "mfe_p95": mfe_p95,
    "pf_observed": pf,
    "synthetic_bars_forward_filled": sys_bars
}

with open("audit_packages/random_walk_tests.json", "w") as f:
    json.dump(rw_tests, f, indent=4)

print("[+] ALL AUDIT PACKAGES GENERATED")
