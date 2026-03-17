import numpy as np
import pandas as pd
from scipy import stats

def hfd_test(series):
    n = len(series)
    k_max = 6
    lk = []
    for k in range(1, k_max + 1):
        lm = []
        for m in range(k):
            idx = np.arange(m, n, k)
            if len(idx) < 2: continue
            norm = (n - 1) / (int((n - 1 - m) / k) * k)
            l_m = np.sum(np.abs(np.diff(series[idx]))) * norm / k
            lm.append(l_m)
        if lm: lk.append(np.mean(lm))
    
    x = np.log(np.arange(1, len(lk) + 1))
    y = np.log(lk)
    slope, _, r2, _, _ = stats.linregress(x, y)
    return slope, 2.0 + slope, r2

df = pd.read_csv(r"C:\OMEGA_PROJETO\OHLCV_DATA\XAUUSD_H4.csv").fillna(method='ffill')
prices = df['close'].values[500:560] # 60 points
s, h, r = hfd_test(prices)
print(f"Slope: {s:.4f} | HFD: {h:.4f} | R2: {r:.4f}")

# Test with random walk
rw = np.cumsum(np.random.normal(0, 1, 60))
s2, h2, r2 = hfd_test(rw)
print(f"RW Slope: {s2:.4f} | RW HFD: {h2:.4f} | RW R2: {r2:.4f}")
